#!/usr/bin/env python3
"""
AutoYes - Interactive PTY proxy with auto-approval mode

This program runs any command in a PTY, allowing interactive use while monitoring
I/O for approval prompts. Press Ctrl-Y to toggle auto-approval mode.

Works with any interactive command: claude, cursor, terraform, kubectl, etc.
"""

__version__ = "2.0.0"

import sys
import os
import pty
import select
import termios
import tty
import signal
import re
import time
from typing import Optional
from datetime import datetime
from pathlib import Path

# ANSI color codes for status messages
GREEN = '\033[92m'
YELLOW = '\033[93m'
RED = '\033[91m'
BLUE = '\033[94m'
RESET = '\033[0m'
BOLD = '\033[1m'

# Pattern to strip ANSI escape codes for pattern matching
# Handles standard CSI, DEC private mode (\x1b[?...), and OSC sequences (\x1b]...\x07)
ANSI_ESCAPE = re.compile(
    r'\x1b'                         # ESC
    r'(?:'
    r'\[[?!>]*[0-9;]*[a-zA-Z<>~]'   # CSI sequences (including DEC private mode)
    r'|'
    r'\][^\x07]*\x07'               # OSC sequences (terminated by BEL)
    r'|'
    r'\][^\x1b]*\x1b\\'             # OSC sequences (terminated by ST)
    r')'
)

def read_version() -> str:
    version_path = Path(__file__).resolve().with_name("VERSION")
    try:
        return version_path.read_text(encoding="utf-8").strip()
    except OSError:
        return __version__

class AutoYes:
    def __init__(self, command: list[str], enable_logging: bool = False):
        self.command = command
        self.auto_approve = True  # Start with auto-approve ON by default
        self.buffer = ""  # Buffer to detect approval prompts
        self.master_fd: Optional[int] = None
        self.original_tty = None
        self.buffer_limit = 16384
        self.read_chunk_size = 4096
        self.idle_prompt_timeout = 0.75
        self.response_delay = 0.3  # Increased delay for TUI to be ready for input
        self.last_output_time = 0.0
        self.last_idle_snapshot = ""
        self.pending_response = None  # Response waiting to be sent after TUI settles
        self.use_status_line = sys.stderr.isatty() and os.environ.get("TERM") not in (None, "dumb")
        
        # Logging setup
        self.enable_logging = enable_logging
        self.log_file = None
        self.stream_log_file = None
        self.stream_log_path: Optional[Path] = None
        log_dir = None
        try:
            log_dir = Path.home() / ".autoyes"
            log_dir.mkdir(exist_ok=True)
        except OSError:
            log_dir = None

        if log_dir:
            self.stream_log_path = log_dir / "stream.log"
            try:
                self.stream_log_file = open(self.stream_log_path, "ab", buffering=0)
            except OSError:
                self.stream_log_file = None

            if self.enable_logging:
                log_path = log_dir / "autoyes.log"
                self.log_file = open(log_path, "a", encoding="utf-8", buffering=1)  # Line buffered
                self.log(f"\n{'='*80}\n")
                self.log(f"AutoYes session started: {datetime.now()}\n")
                self.log(f"Command: {' '.join(command)}\n")
                self.log(f"{'='*80}\n")
        
        # Patterns that indicate the command is asking for approval
        # These work with Claude, Terraform, kubectl, and many other tools
        menu_prefix = r'(?:[›❯>➤•*]\s*)?'
        # NOTE: In raw terminal mode, Enter sends \r (carriage return), not \n (line feed)
        # TUIs expect \r for Enter key presses
        self.approval_patterns: list[tuple[re.Pattern, bytes, str]] = [
            # Numbered menu format (Claude, many CLI tools): "1. Yes" / "2. No" (optional 3rd option)
            # NOTE: Must require BOTH "1. Yes" AND "2. No" to avoid premature matching when
            # the menu is rendered incrementally (TUIs often send "1. Yes" before "2. No")
            (re.compile(rf'{menu_prefix}1[\.)]\s*Yes\s+{menu_prefix}2[\.)]\s*No(?:\s+{menu_prefix}3[\.)]\s*[^\n]+)?', re.IGNORECASE | re.MULTILINE), b'\r', "pressing Enter"),
            # Generic approval prompts with yes/no options (e.g., "Continue? (y/n)")
            (re.compile(r'(?:Do you want to|Continue|Proceed|Approve|Confirm|Are you sure)\b[^\n]*?\s*(?:\(|\[)?\s*(?:yes\s*/\s*no|y\s*/\s*n)\s*(?:\)|\])?', re.IGNORECASE), b'y\r', "sending 'y' + Enter"),
            # Terraform style: "Enter a value:"
            (re.compile(r'Enter a value:\s*$', re.IGNORECASE | re.MULTILINE), b'yes\r', "sending 'yes' + Enter"),
        ]
        self.relaxed_approval_patterns: list[tuple[re.Pattern, bytes, str]] = [
            (re.compile(r'\?\s*(?:\(|\[)?\s*(?:yes|y)\s*/\s*(?:no|n)(?:\s*/\s*[^\s\]\)]+)?\s*(?:\)|\])?', re.IGNORECASE), b'y\r', "sending 'y' + Enter (relaxed)"),
            (re.compile(r'\bYes\b\s*/\s*\bNo\b\s*/\s*[^\n]+', re.IGNORECASE), b'y\r', "sending 'y' + Enter (relaxed)"),
        ]
        self.numbered_menu_pattern = re.compile(r'^\s*[›❯>➤•*]?\s*(\d+)[\.)]\s*(Yes|No)\b', re.IGNORECASE)
        
    def log(self, message: str):
        """Write a message to the log file"""
        if self.log_file:
            self.log_file.write(message)
            self.log_file.flush()
    
    def log_data(self, direction: str, data: bytes):
        """Log raw data with timestamp and direction"""
        if not self.enable_logging:
            return
        
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        try:
            text = data.decode('utf-8', errors='replace')
            # Escape non-printable characters for clarity
            escaped = repr(text)[1:-1]  # Remove outer quotes
            self.log(f"[{timestamp}] {direction}: {escaped}\n")
        except Exception as e:
            self.log(f"[{timestamp}] {direction}: <decode error: {e}>\n")

    def log_stream_data(self, data: bytes):
        if self.stream_log_file:
            try:
                self.stream_log_file.write(data)
            except Exception as e:
                if self.enable_logging:
                    self.log(f"[ERROR] Failed to write stream log: {e}\n")
    
    def print_status(self, message: str, color: str = RESET, *, visible: bool = False):
        """Print a status message to stderr"""
        formatted = f"{color}{BOLD}[AutoYes]{RESET} {color}{message}{RESET}"
        if visible and self.use_status_line:
            sys.stderr.write("\0337")
            sys.stderr.write("\033[999B")
            sys.stderr.write("\r\033[2K")
            sys.stderr.write(formatted)
            sys.stderr.write("\0338")
            sys.stderr.flush()
        if self.enable_logging:
            self.log(f"[STATUS] {message}\n")
        
    def toggle_auto_approve(self):
        """Toggle auto-approval mode"""
        self.auto_approve = not self.auto_approve
        if self.auto_approve:
            self.print_status("Auto-approve mode: ON", GREEN, visible=True)
        else:
            self.print_status("Auto-approve mode: OFF", RED, visible=True)
            
    def check_for_approval_prompt(self, text: str, relaxed: bool = False) -> Optional[tuple[bytes, str]]:
        """Check if the text contains an approval prompt"""
        # Strip ANSI escape codes first for cleaner processing
        clean_text = ANSI_ESCAPE.sub('', text)
        # Normalize line endings
        clean_text = clean_text.replace('\r\n', '\n').replace('\r', '\n')
        
        # Filter out empty lines and spinner-only lines to handle TUI animations
        # that flood the buffer and push the actual prompt out of view
        all_lines = clean_text.split('\n')
        # Spinner characters commonly used by TUI apps
        spinner_chars = set('⏺⏹⏸⏵⏴●○◐◑◒◓◴◵◶◷⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏▁▂▃▄▅▆▇█✓✗✳✴✵')
        meaningful_lines = [
            line for line in all_lines 
            if line.strip() and not all(c in spinner_chars or c.isspace() for c in line)
        ]
        
        # Take last N meaningful lines (more lines in relaxed mode for idle check)
        max_lines = 50 if relaxed else 30
        last_lines = '\n'.join(meaningful_lines[-max_lines:])

        menu_response = self.match_numbered_menu(last_lines)
        if menu_response:
            return menu_response

        if self.enable_logging:
            mode = "RELAXED" if relaxed else "STRICT"
            self.log(f"\n[PATTERN CHECK] Mode: {mode} | Buffer size: {len(text)} chars\n")
            self.log(f"[PATTERN CHECK] Last {max_lines} non-empty lines:\n{repr(last_lines)}\n")
        
        patterns = self.approval_patterns + (self.relaxed_approval_patterns if relaxed else [])
        for i, (pattern, response, response_label) in enumerate(patterns):
            match = pattern.search(last_lines)
            if match:
                if self.enable_logging:
                    self.log(f"[PATTERN MATCH] Pattern #{i} matched: {pattern.pattern}\n")
                    self.log(f"[PATTERN MATCH] Matched text: {repr(match.group())}\n")
                    self.log(f"[PATTERN MATCH] Response: {response_label} ({response!r})\n")
                return response, response_label
            elif self.enable_logging:
                self.log(f"[PATTERN CHECK] Pattern #{i} no match: {pattern.pattern}\n")
        
        return None

    def match_numbered_menu(self, clean_text: str) -> Optional[tuple[bytes, str]]:
        options = {}
        for line in clean_text.splitlines():
            match = self.numbered_menu_pattern.match(line)
            if match:
                options[match.group(1)] = match.group(2).lower()

        if options.get("1") == "yes" and options.get("2") == "no":
            if self.enable_logging:
                self.log("[MENU MATCH] Detected numbered Yes/No menu\n")
                self.log(f"[MENU MATCH] Options: {options}\n")
            return b'\r', "pressing Enter"

        return None
        
    def auto_respond(self, response: bytes, response_label: str):
        """Send auto-approval response to command"""
        self.print_status(f"Auto-responding: YES ({response_label})", YELLOW)
        os.write(self.master_fd, response)
        if self.enable_logging:
            self.log(f"[AUTO_RESPOND] Sent {response_label} ({response!r})\n")
        
    def handle_user_input(self, data: bytes) -> bytes:
        """Process user input, intercepting Ctrl-Y"""
        self.log_data("USER_INPUT", data)
        
        # Ctrl-Y is ASCII 25 (0x19)
        if b'\x19' in data:
            self.toggle_auto_approve()
            # Remove Ctrl-Y from the data stream
            data = data.replace(b'\x19', b'')
        return data
        
    def handle_command_output(self, data: bytes) -> Optional[tuple[bytes, str]]:
        """Process command output, checking for approval prompts
        
        Returns a response tuple if an approval prompt was detected (and will be auto-responded)
        """
        self.log_data("COMMAND_OUTPUT", data)
        self.log_stream_data(data)
        
        # Add to buffer for pattern matching
        try:
            text = data.decode('utf-8', errors='replace')
            self.buffer += text
            if len(self.buffer) > self.buffer_limit:
                self.buffer = self.buffer[-self.buffer_limit:]

            if self.auto_approve:
                response = self.check_for_approval_prompt(self.buffer)
                if response:
                    return response
        except Exception as e:
            # Don't let decoding errors break the proxy
            if self.enable_logging:
                self.log(f"[ERROR] Exception in handle_command_output: {e}\n")
            pass
        
        return None

    def clear_buffer(self):
        self.buffer = ""
        self.last_idle_snapshot = ""
            
    def setup_terminal(self):
        """Set terminal to raw mode"""
        if not sys.stdin.isatty():
            return
        try:
            self.original_tty = termios.tcgetattr(sys.stdin)
        except termios.error:
            return
        tty.setraw(sys.stdin.fileno())
        
    def restore_terminal(self):
        """Restore terminal to original mode"""
        if self.original_tty:
            termios.tcsetattr(sys.stdin, termios.TCSAFLUSH, self.original_tty)
            
    def run(self):
        """Main event loop - single-threaded for reliable prompt detection"""
        # Print startup message
        self.print_status(f"Starting: {' '.join(self.command)}", BLUE)
        self.print_status("Auto-approval: ON (press Ctrl-Y to toggle)", GREEN)
        self.print_status("Press Ctrl-C to exit", BLUE)
        
        if self.enable_logging:
            log_path = Path.home() / ".autoyes" / "autoyes.log"
            self.print_status(f"Logging to: {log_path}", BLUE)
        
        # Spawn command in a PTY
        pid, self.master_fd = pty.fork()
        
        if pid == 0:  # Child process
            # Execute the command
            os.execvp(self.command[0], self.command)
        else:  # Parent process
            try:
                self.setup_terminal()
                self.last_output_time = time.monotonic()

                # Single-threaded I/O loop using select on both stdin and PTY
                while True:
                    # Wait for input from either user or command (with timeout for idle check)
                    r, _, _ = select.select([sys.stdin, self.master_fd], [], [], 0.1)

                    if sys.stdin in r:
                        # User input
                        try:
                            data = os.read(sys.stdin.fileno(), self.read_chunk_size)
                            if not data:
                                break
                            data = self.handle_user_input(data)
                            if data:
                                os.write(self.master_fd, data)
                        except OSError:
                            break

                    if self.master_fd in r:
                        # Command output - use smaller reads to catch prompts before spinner floods
                        try:
                            data = os.read(self.master_fd, 4096)
                            if not data:
                                break
                            
                            self.last_output_time = time.monotonic()
                            
                            # Check for approval prompt BEFORE adding to buffer
                            # This catches the prompt even if spinner data follows in same chunk
                            response = self.handle_command_output(data)
                            
                            # Forward output to user
                            os.write(sys.stdout.fileno(), data)
                            sys.stdout.flush()
                            
                            # Queue auto-response to be sent after TUI settles
                            if response and not self.pending_response:
                                self.pending_response = response
                                if self.enable_logging:
                                    self.log(f"[PENDING] Queued response: {response[1]}\n")
                                
                        except OSError:
                            break

                    # Check if we should send a pending response
                    # Wait for TUI to settle (no output for response_delay time)
                    now = time.monotonic()
                    if self.pending_response and (now - self.last_output_time) >= self.response_delay:
                        if self.enable_logging:
                            self.log(f"[SENDING] TUI settled, sending response: {self.pending_response[1]}\n")
                        sys.stdout.flush()
                        self.auto_respond(self.pending_response[0], self.pending_response[1])
                        self.clear_buffer()
                        self.pending_response = None
                        self.last_output_time = now
                    
                    # Idle check - if no output for a while, do a relaxed pattern check
                    elif self.auto_approve and self.buffer and not self.pending_response:
                        if (now - self.last_output_time) >= self.idle_prompt_timeout:
                            snapshot = self.buffer[-512:]
                            if snapshot != self.last_idle_snapshot:
                                response = self.check_for_approval_prompt(self.buffer, relaxed=True)
                                if response:
                                    if self.enable_logging:
                                        self.log("[IDLE CHECK] Triggered relaxed approval check\n")
                                    self.pending_response = response
                                else:
                                    self.last_idle_snapshot = snapshot
                            
            except KeyboardInterrupt:
                self.print_status("Interrupted by user", YELLOW)
            finally:
                self.restore_terminal()
                
                # Clean up
                try:
                    os.close(self.master_fd)
                except:
                    pass
                    
                # Wait for child process
                try:
                    os.waitpid(pid, 0)
                except:
                    pass
                    
                self.print_status("Session ended", BLUE)
                
                # Close log file
                if self.log_file:
                    self.log(f"\n{'='*80}\n")
                    self.log(f"AutoYes session ended: {datetime.now()}\n")
                    self.log(f"{'='*80}\n\n")
                    self.log_file.close()
                if self.stream_log_file:
                    try:
                        self.stream_log_file.close()
                    except Exception:
                        pass


def main():
    """Entry point"""
    version = read_version()
    # Handle version flag
    if len(sys.argv) == 2 and sys.argv[1] in ('--version', '-v'):
        print(f"AutoYes v{version}")
        sys.exit(0)
    
    # Handle help flag
    if len(sys.argv) == 2 and sys.argv[1] in ('--help', '-h'):
        print(f"AutoYes v{version} - Interactive PTY proxy with auto-approval")
        print("\nUsage: autoyes <command> [args...]")
        print("\nExamples:")
        print("  autoyes claude                        # Run Claude with auto-approval")
        print("  autoyes cursor                        # Run Cursor with auto-approval")
        print("  autoyes terraform apply               # Run Terraform with auto-approval")
        print("  autoyes kubectl apply -f config.yaml  # Run kubectl with auto-approval")
        print("\nControls:")
        print("  Ctrl-Y    Toggle auto-approval ON/OFF (starts ON)")
        print("  Ctrl-C    Exit")
        print("\nDebugging:")
        print("  AUTOYES_DEBUG=1 autoyes <command>     # Enable logging to ~/.autoyes/autoyes.log")
        print("\nDocumentation:")
        print("  https://github.com/yourusername/autoyes")
        sys.exit(0)
    
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <command> [args...]", file=sys.stderr)
        print(f"\nExamples:", file=sys.stderr)
        print(f"  {sys.argv[0]} claude", file=sys.stderr)
        print(f"  {sys.argv[0]} cursor", file=sys.stderr)
        print(f"  {sys.argv[0]} terraform apply", file=sys.stderr)
        print(f"\nRun '{sys.argv[0]} --help' for more information", file=sys.stderr)
        sys.exit(1)
    
    # Check for debug mode via environment variable
    enable_logging = os.environ.get('AUTOYES_DEBUG', '0') == '1'
    command = sys.argv[1:]
    
    proxy = AutoYes(command, enable_logging=enable_logging)
    proxy.run()


if __name__ == "__main__":
    main()
