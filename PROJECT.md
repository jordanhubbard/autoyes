# AutoClaude Project Structure

## Overview

AutoClaude is a PTY (pseudo-terminal) proxy for Claude that enables auto-approval of prompts via Ctrl-Y toggle.

## Project Files

### Core Files

| File | Purpose |
|------|---------|
| `autoclaude` | Shell wrapper script installed to `~/.local/bin` |
| `autoclaude.py` | Main Python program (PTY proxy implementation) |
| `test_approval.py` | Test script that simulates Claude approval prompts |

### Build & Configuration

| File | Purpose |
|------|---------|
| `Makefile` | Build automation (install, test, uninstall) |
| `requirements.txt` | Python dependencies (none - stdlib only) |
| `.gitignore` | Git ignore patterns |
| `VERSION` | Version number (1.0.0) |

### Documentation

| File | Purpose |
|------|---------|
| `README.md` | Main documentation |
| `QUICKSTART.md` | Quick start guide (TL;DR) |
| `INSTALL.md` | Detailed installation guide |
| `TESTING.md` | Testing and troubleshooting guide |
| `PROJECT.md` | This file - project structure |
| `examples.sh` | Usage examples script |

## Installation Layout

After `make install`, files are organized as follows:

```
$HOME/
├── .autoclaude/
│   ├── venv/                    # Python virtual environment
│   │   ├── bin/
│   │   │   └── python3         # Python interpreter
│   │   └── ...
│   ├── autoclaude.py           # Main script (copy)
│   └── test_approval.py        # Test script (copy)
│
└── .local/
    └── bin/
        └── autoclaude          # Shell wrapper
```

## Architecture

### Shell Wrapper (`autoclaude`)
- Entry point for users
- Checks for/creates venv on first run
- Validates installation
- Executes Python script with venv's Python
- Defaults to running `claude` if no args provided

### Python Script (`autoclaude.py`)
- Uses `pty.fork()` to create pseudo-terminal
- Spawns Claude (or other command) in child process
- Proxies I/O between user's terminal and Claude's PTY
- Monitors output stream for approval prompts
- Intercepts Ctrl-Y (ASCII 25) to toggle auto-approve
- Pattern matches for Claude's approval format
- Auto-responds by sending Enter key

### Test Script (`test_approval.py`)
- Simulates Claude's approval prompt format
- Useful for testing without running real Claude
- Accepts Enter or "1" or "yes" as approval
- Loops to test multiple approvals

## Key Technologies

- **PTY (Pseudo-Terminal)**: Python's `pty` module
- **Terminal Control**: `termios`, `tty` modules
- **I/O Multiplexing**: `select.select()`
- **Process Management**: `os.fork()`, `os.execvp()`
- **Pattern Matching**: Regular expressions (`re` module)

## Code Flow

1. **Startup**
   - Shell wrapper validates/creates venv
   - Executes Python script
   - Python script parses arguments

2. **PTY Creation**
   - Fork process with `pty.fork()`
   - Child executes Claude with `os.execvp()`
   - Parent enters I/O loop

3. **I/O Loop**
   - `select()` waits for stdin or PTY readable
   - User input: Check for Ctrl-Y, forward to PTY
   - PTY output: Check for approval prompts, forward to stdout
   - If auto-approve ON + prompt detected: send Enter

4. **Shutdown**
   - Restore terminal settings
   - Close PTY
   - Wait for child process
   - Exit

## Pattern Detection

AutoClaude detects these approval patterns:

1. **Claude-specific**: `"Do you want to proceed?\n› 1. Yes\n  2. No"`
2. **Generic**: `"Do you want to continue? (yes/no)"`
3. **Numbered menu**: `"› 1. Yes\n  2. No"`

Patterns use regex with MULTILINE and IGNORECASE flags.

## Auto-Response Mechanism

When approval prompt is detected:
1. Wait 0.1s for prompt to stabilize
2. Send `\n` (Enter key) to PTY
3. Print status message to stderr
4. Clear buffer

Enter key selects default option (1. Yes) in Claude's menu.

## State Management

- `auto_approve`: Boolean flag (toggles with Ctrl-Y)
- `buffer`: Last 4KB of output for pattern matching
- `master_fd`: File descriptor for PTY master
- `original_tty`: Original terminal settings (for restoration)

## Development Workflow

```bash
# Local development (no install)
make install-local    # Make scripts executable
./autoclaude.py claude

# Testing
make test            # Test with simulator
make test-bash       # Test with bash

# Installation
make install         # Install to home directory
autoclaude          # Use installed version

# Uninstall
make uninstall      # Remove all installed files
```

## Security Considerations

- No network access
- No external dependencies
- All code runs locally
- Venv isolation
- Source code is transparent
- No elevated privileges required

## Performance

- Minimal latency: < 1ms per I/O operation
- Pattern matching: O(n) where n = buffer size (4KB)
- Memory footprint: ~10-15 MB (including venv)
- CPU usage: Negligible (event-driven I/O)

## Compatibility

- **OS**: Unix-like systems (Linux, macOS, BSD)
- **Python**: 3.6+ (uses type hints, f-strings)
- **Terminal**: Any ANSI-compatible terminal
- **Shell**: Bash, Zsh, Fish, etc.

## Future Enhancements

Potential improvements:
- Configuration file for custom patterns
- Logging mode for debugging
- Session recording/playback
- Custom key bindings
- Multiple approval modes (always/never/ask)
- Integration with other Claude tools

## License

MIT License (implied - add LICENSE file if publishing)

## Version History

- **1.0.0** (2026-01-23): Initial release
  - PTY proxy implementation
  - Ctrl-Y toggle for auto-approval
  - Shell wrapper with auto-setup
  - Comprehensive documentation
