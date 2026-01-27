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
import threading
import queue
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
ANSI_ESCAPE = re.compile(r'\x1b\[[0-9;]*[a-zA-Z]')

class AutoYes:
    def __init__(self, command: list[str], enable_logging: bool = False):
        self.command = command
        self.auto_approve = True  # Start with auto-approve ON by default
        self.buffer = ""  # Buffer to detect approval prompts
        self.master_fd: Optional[int] = None
        self.original_tty = None
        self.buffer_limit = 16384
        self.read_chunk_size = 4096
        self.pty_read_chunk_size = 16384
        self.idle_prompt_timeout = 0.75
        self.response_delay = 0.15
        self.last_output_time = 0.0
        self.last_idle_snapshot = ""
        self.output_queue = queue.Queue()
        self.stop_event = threading.Event()
        self.state_lock = threading.Lock()
        self.status_lock = threading.Lock()
        self.use_status_line = sys.stderr.isatty() and os.environ.get("TERM") not in (None, "dumb")
        
        # Logging setup
        self.enable_logging = enable_logging
        self.log_file = None
        if self.enable_logging:
            log_dir = Path.home() / ".autoyes"
            log_dir.mkdir(exist_ok=True)
            log_path = log_dir / "autoyes.log"
            self.log_file = open(log_path, "a", encoding="utf-8", buffering=1)  # Line buffered
            self.log(f"\n{'='*80}\n")
            self.log(f"AutoYes session started: {datetime.now()}\n")
            self.log(f"Command: {' '.join(command)}\n")
            self.log(f"{'='*80}\n")
        
        # Patterns that indicate the command is asking for approval
        # These work with Claude, Terraform, kubectl, and many other tools
        menu_prefix = r'(?:[›❯>➤•*]\s*)?'
        self.approval_patterns: list[tuple[re.Pattern, bytes, str]] = [
            # Numbered menu format (Claude, many CLI tools): "1. Yes" / "2. No" (optional 3rd option)
            (re.compile(rf'{menu_prefix}1[\.)]\s*Yes\s+{menu_prefix}2[\.)]\s*No(?:\s+{menu_prefix}3[\.)]\s*[^\n]+)?', re.IGNORECASE | re.MULTILINE), b'\n', "pressing Enter"),
            # "Do you want to proceed?" followed by "1. Yes"
            (re.compile(rf'Do you want to (?:proceed|continue)\?\s+{menu_prefix}1[\.)]\s*Yes', re.IGNORECASE | re.MULTILINE), b'\n', "pressing Enter"),
            # Generic approval prompts with yes/no options
            (re.compile(r'(?:Do you want to|Continue|Proceed|Approve|Confirm|Are you sure)\b[^\n]*?\s*(?:\(|\[)?\s*(?:yes\s*/\s*no|y\s*/\s*n)\s*(?:\)|\])?', re.IGNORECASE), b'y\n', "sending 'y' + Enter"),
            # Terraform style: "Enter a value:"
            (re.compile(r'Enter a value:\s*$', re.IGNORECASE | re.MULTILINE), b'yes\n', "sending 'yes' + Enter"),
        ]
        self.relaxed_approval_patterns: list[tuple[re.Pattern, bytes, str]] = [
            (re.compile(r'\?\s*(?:\(|\[)?\s*(?:yes|y)\s*/\s*(?:no|n)(?:\s*/\s*[^\s\]\)]+)?\s*(?:\)|\])?', re.IGNORECASE), b'y\n', "sending 'y' + Enter (relaxed)"),
            (re.compile(r'\bYes\b\s*/\s*\bNo\b\s*/\s*[^\n]+', re.IGNORECASE), b'y\n', "sending 'y' + Enter (relaxed)"),
        ]
        
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
    
    def print_status(self, message: str, color: str = RESET, *, visible: bool = False):
        """Print a status message to stderr"""
        formatted = f"{color}{BOLD}[AutoYes]{RESET} {color}{message}{RESET}"
        if visible and self.use_status_line:
            with self.status_lock:
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
        with self.state_lock:
            self.auto_approve = not self.auto_approve
        if self.auto_approve:
            self.print_status("Auto-approve mode: ON", GREEN, visible=True)
        else:
            self.print_status("Auto-approve mode: OFF", RED, visible=True)
            
    def check_for_approval_prompt(self, text: str, relaxed: bool = False) -> Optional[tuple[bytes, str]]:
        """Check if the text contains an approval prompt"""
        # Look at the last few lines of the buffer
        normalized_text = text.replace('\r\n', '\n').replace('\r', '\n')
        lines = normalized_text.split('\n')
        max_lines = 20 if relaxed else 10
        last_lines = '\n'.join(lines[-max_lines:])
        
        # Strip ANSI escape codes for cleaner pattern matching
        # Commands often add colors/formatting that can break patterns
        clean_text = ANSI_ESCAPE.sub('', last_lines)
        # Also normalize line endings
        clean_text = clean_text.replace('\r\n', '\n').replace('\r', '\n')

        if self.enable_logging:
            mode = "RELAXED" if relaxed else "STRICT"
            self.log(f"\n[PATTERN CHECK] Mode: {mode} | Buffer size: {len(text)} chars\n")
            self.log(f"[PATTERN CHECK] Last {max_lines} lines (raw):\n{repr(last_lines)}\n")
            self.log(f"[PATTERN CHECK] Last {max_lines} lines (clean):\n{repr(clean_text)}\n")
        
        patterns = self.approval_patterns + (self.relaxed_approval_patterns if relaxed else [])
        for i, (pattern, response, response_label) in enumerate(patterns):
            match = pattern.search(clean_text)
            if match:
                if self.enable_logging:
                    self.log(f"[PATTERN MATCH] Pattern #{i} matched: {pattern.pattern}\n")
                    self.log(f"[PATTERN MATCH] Matched text: {repr(match.group())}\n")
                    self.log(f"[PATTERN MATCH] Response: {response_label} ({response!r})\n")
                return response, response_label
            elif self.enable_logging:
                self.log(f"[PATTERN CHECK] Pattern #{i} no match: {pattern.pattern}\n")
        
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
        
        # Add to buffer for pattern matching
        try:
            text = data.decode('utf-8', errors='replace')
            with self.state_lock:
                self.buffer += text
                if len(self.buffer) > self.buffer_limit:
                    self.buffer = self.buffer[-self.buffer_limit:]
                buffer_snapshot = self.buffer
                auto_approve = self.auto_approve

            if auto_approve:
                response = self.check_for_approval_prompt(buffer_snapshot)
                if response:
                    return response
        except Exception as e:
            # Don't let decoding errors break the proxy
            if self.enable_logging:
                self.log(f"[ERROR] Exception in handle_command_output: {e}\n")
            pass
        
        return None

    def clear_buffer(self):
        with self.state_lock:
            self.buffer = ""
            self.last_idle_snapshot = ""

    def pty_reader(self):
        while not self.stop_event.is_set():
            try:
                data = os.read(self.master_fd, self.pty_read_chunk_size)
                if not data:
                    self.output_queue.put(None)
                    return
                with self.state_lock:
                    self.last_output_time = time.monotonic()
                    self.last_idle_snapshot = ""
                response = self.handle_command_output(data)
                self.output_queue.put((data, response))
            except OSError:
                self.output_queue.put(None)
                return
            
    def setup_terminal(self):
        """Set terminal to raw mode"""
        self.original_tty = termios.tcgetattr(sys.stdin)
        tty.setraw(sys.stdin.fileno())
        
    def restore_terminal(self):
        """Restore terminal to original mode"""
        if self.original_tty:
            termios.tcsetattr(sys.stdin, termios.TCSAFLUSH, self.original_tty)
            
    def run(self):
        """Main event loop"""
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
                reader_thread = threading.Thread(target=self.pty_reader, daemon=True)
                reader_thread.start()

                while True:
                    r, _, _ = select.select([sys.stdin], [], [], 0.05)

                    if sys.stdin in r:
                        try:
                            data = os.read(sys.stdin.fileno(), self.read_chunk_size)
                            if not data:
                                break
                            data = self.handle_user_input(data)
                            if data:
                                os.write(self.master_fd, data)
                        except OSError:
                            break

                    while True:
                        try:
                            item = self.output_queue.get_nowait()
                        except queue.Empty:
                            break
                        if item is None:
                            return
                        data, response = item
                        os.write(sys.stdout.fileno(), data)
                        sys.stdout.flush()
                        if response:
                            time.sleep(self.response_delay)
                            self.auto_respond(response[0], response[1])
                            self.clear_buffer()

                    now = time.monotonic()
                    with self.state_lock:
                        auto_approve = self.auto_approve
                        buffer_snapshot = self.buffer
                        last_output_time = self.last_output_time
                        last_idle_snapshot = self.last_idle_snapshot

                    if auto_approve and buffer_snapshot and (now - last_output_time) >= self.idle_prompt_timeout:
                        snapshot = buffer_snapshot[-512:]
                        if snapshot != last_idle_snapshot:
                            response = self.check_for_approval_prompt(buffer_snapshot, relaxed=True)
                            if response:
                                if self.enable_logging:
                                    self.log("[IDLE CHECK] Triggered relaxed approval check\n")
                                self.auto_respond(response[0], response[1])
                                self.clear_buffer()
                                with self.state_lock:
                                    self.last_output_time = now
                                    self.last_idle_snapshot = ""
                            else:
                                with self.state_lock:
                                    self.last_idle_snapshot = snapshot
                            
            except KeyboardInterrupt:
                self.print_status("Interrupted by user", YELLOW)
            finally:
                self.stop_event.set()
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


def main():
    """Entry point"""
    # Handle version flag
    if len(sys.argv) == 2 and sys.argv[1] in ('--version', '-v'):
        print(f"AutoYes v{__version__}")
        sys.exit(0)
    
    # Handle help flag
    if len(sys.argv) == 2 and sys.argv[1] in ('--help', '-h'):
        print(f"AutoYes v{__version__} - Interactive PTY proxy with auto-approval")
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
