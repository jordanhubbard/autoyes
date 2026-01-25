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
        self.idle_prompt_timeout = 0.75
        self.last_output_time = 0.0
        self.last_idle_snapshot = ""
        
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
        self.approval_patterns = [
            # Numbered menu format (Claude, many CLI tools): "1. Yes" / "2. No" (optional 3rd option)
            re.compile(r'(?:›\s*)?1[\.)]\s*Yes\s*\n\s*(?:›\s*)?2[\.)]\s*No(?:\s*\n\s*(?:›\s*)?3[\.)]\s*[^\n]+)?', re.IGNORECASE | re.MULTILINE),
            # "Do you want to proceed?" followed by "1. Yes"
            re.compile(r'Do you want to (?:proceed|continue)\?\s*\n\s*(?:›\s*)?1[\.)]\s*Yes', re.IGNORECASE | re.MULTILINE),
            # Generic approval prompts with yes/no options
            re.compile(r'(?:Do you want to|Continue|Proceed|Approve|Confirm)\s*\??\s*\(?\s*(?:yes?/no?|y/n)\s*\)?', re.IGNORECASE),
            # Terraform style: "Enter a value:"
            re.compile(r'Enter a value:\s*$', re.IGNORECASE | re.MULTILINE),
        ]
        self.relaxed_approval_patterns = [
            re.compile(r'\?\s*(?:\(|\[)?\s*(?:yes|y)\s*/\s*(?:no|n)(?:\s*/\s*[^\s\]\)]+)?\s*(?:\)|\])?', re.IGNORECASE),
            re.compile(r'\bYes\b\s*/\s*\bNo\b\s*/\s*[^\n]+', re.IGNORECASE),
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
    
    def print_status(self, message: str, color: str = RESET):
        """Print a status message to stderr"""
        sys.stderr.write(f"\r\n{color}{BOLD}[AutoYes]{RESET} {color}{message}{RESET}\r\n")
        sys.stderr.flush()
        if self.enable_logging:
            self.log(f"[STATUS] {message}\n")
        
    def toggle_auto_approve(self):
        """Toggle auto-approval mode"""
        self.auto_approve = not self.auto_approve
        if self.auto_approve:
            self.print_status("Auto-approve mode: ON", GREEN)
        else:
            self.print_status("Auto-approve mode: OFF", RED)
            
    def check_for_approval_prompt(self, text: str, relaxed: bool = False) -> bool:
        """Check if the text contains an approval prompt"""
        # Look at the last few lines of the buffer
        lines = text.split('\n')
        max_lines = 20 if relaxed else 10
        last_lines = '\n'.join(lines[-max_lines:])
        
        # Strip ANSI escape codes for cleaner pattern matching
        # Commands often add colors/formatting that can break patterns
        clean_text = ANSI_ESCAPE.sub('', last_lines)
        # Also normalize line endings
        clean_text = clean_text.replace('\r\n', '\n').replace('\r', '\n')
        
        if self.enable_logging:
            mode = "RELAXED" if relaxed else "STRICT"
            self.log(f"\n[PATTERN CHECK] Mode: {mode} | Buffer size: {len(self.buffer)} chars\n")
            self.log(f"[PATTERN CHECK] Last {max_lines} lines (raw):\n{repr(last_lines)}\n")
            self.log(f"[PATTERN CHECK] Last {max_lines} lines (clean):\n{repr(clean_text)}\n")
        
        patterns = self.approval_patterns + (self.relaxed_approval_patterns if relaxed else [])
        for i, pattern in enumerate(patterns):
            match = pattern.search(clean_text)
            if match:
                if self.enable_logging:
                    self.log(f"[PATTERN MATCH] Pattern #{i} matched: {pattern.pattern}\n")
                    self.log(f"[PATTERN MATCH] Matched text: {repr(match.group())}\n")
                return True
            elif self.enable_logging:
                self.log(f"[PATTERN CHECK] Pattern #{i} no match: {pattern.pattern}\n")
        
        return False
        
    def auto_respond_yes(self):
        """Send 'yes' response to command"""
        self.print_status("Auto-responding: YES (pressing Enter)", YELLOW)
        # Send Enter key to select default option (1. Yes)
        # In terminal/PTY, Enter key sends carriage return (\r), not newline (\n)
        os.write(self.master_fd, b'\r')
        if self.enable_logging:
            self.log(f"[AUTO_RESPOND] Sent carriage return (\\r) to select default option\n")
        
    def handle_user_input(self, data: bytes) -> bytes:
        """Process user input, intercepting Ctrl-Y"""
        self.log_data("USER_INPUT", data)
        
        # Ctrl-Y is ASCII 25 (0x19)
        if b'\x19' in data:
            self.toggle_auto_approve()
            # Remove Ctrl-Y from the data stream
            data = data.replace(b'\x19', b'')
        return data
        
    def handle_command_output(self, data: bytes) -> bool:
        """Process command output, checking for approval prompts
        
        Returns True if an approval prompt was detected (and will be auto-responded)
        """
        self.log_data("COMMAND_OUTPUT", data)
        
        # Add to buffer for pattern matching
        try:
            text = data.decode('utf-8', errors='replace')
            self.buffer += text
            
            # Keep buffer from growing too large
            if len(self.buffer) > self.buffer_limit:
                self.buffer = self.buffer[-self.buffer_limit:]
                
            # Check for approval prompt if auto-approve is on
            if self.auto_approve and self.check_for_approval_prompt(self.buffer):
                # Return True to signal that we should auto-respond
                # But don't respond yet - let the prompt be displayed first
                return True
        except Exception as e:
            # Don't let decoding errors break the proxy
            if self.enable_logging:
                self.log(f"[ERROR] Exception in handle_command_output: {e}\n")
            pass
        
        return False
            
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
                
                # Main I/O loop
                self.last_output_time = time.monotonic()

                while True:
                    # Use select to wait for I/O on stdin or master PTY
                    r, w, e = select.select([sys.stdin, self.master_fd], [], [], 0.1)

                    if not r:
                        now = time.monotonic()
                        if (
                            self.auto_approve
                            and self.buffer
                            and (now - self.last_output_time) >= self.idle_prompt_timeout
                        ):
                            snapshot = self.buffer[-512:]
                            if snapshot != self.last_idle_snapshot:
                                self.last_idle_snapshot = snapshot
                                if self.check_for_approval_prompt(self.buffer, relaxed=True):
                                    if self.enable_logging:
                                        self.log("[IDLE CHECK] Triggered relaxed approval check\n")
                                    self.auto_respond_yes()
                                    self.buffer = ""
                                    self.last_output_time = now
                        continue
                    
                    if sys.stdin in r:
                        # User input
                        try:
                            data = os.read(sys.stdin.fileno(), self.read_chunk_size)
                            if not data:
                                break
                                
                            # Process input (intercept Ctrl-Y)
                            data = self.handle_user_input(data)
                            
                            # Forward to command (if not empty after processing)
                            if data:
                                os.write(self.master_fd, data)
                        except OSError:
                            break
                            
                    if self.master_fd in r:
                        # Command output
                        try:
                            data = os.read(self.master_fd, self.read_chunk_size)
                            if not data:
                                break
                            self.last_output_time = time.monotonic()
                            self.last_idle_snapshot = ""
                                
                            # Process output (check for approval prompts)
                            should_auto_respond = self.handle_command_output(data)
                            
                            # Forward to user
                            os.write(sys.stdout.fileno(), data)
                            sys.stdout.flush()  # Ensure prompt is displayed
                            
                            # Now respond if we detected an approval prompt
                            if should_auto_respond:
                                time.sleep(0.15)  # Slightly longer delay for output to be visible
                                self.auto_respond_yes()
                                self.buffer = ""  # Clear buffer after responding
                        except OSError:
                            break
                            
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
    if enable_logging:
        log_path = Path.home() / ".autoyes" / "autoyes.log"
        print(f"[AutoYes] Debug logging enabled: {log_path}", file=sys.stderr)
    
    command = sys.argv[1:]
    
    proxy = AutoYes(command, enable_logging=enable_logging)
    proxy.run()


if __name__ == "__main__":
    main()
