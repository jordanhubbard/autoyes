# AutoClaude Usage Guide

## Quick Reference

### Installation
```bash
make install           # Install to ~/.autoclaude and ~/.local/bin
autoclaude            # Run it!
```

### Basic Usage
```bash
autoclaude                    # Run Claude with auto-approval capability
autoclaude --model sonnet     # Pass arguments to Claude
autoclaude --help             # Show help
```

### Controls
- **Ctrl-Y**: Toggle auto-approval OFF/ON (starts ON by default)
- **Ctrl-C**: Exit

### Debugging
```bash
AUTOCLAUDE_DEBUG=1 autoclaude     # Enable debug logging
make log-tail                     # Watch log in real-time
make log-view                     # View full log
make log-clear                    # Clear log
```

## Common Workflows

### Workflow 1: Enable Auto-Approve from Start

Perfect for batch operations:

```bash
autoclaude
# Press Ctrl-Y immediately
# Ask Claude to perform many operations
# All approvals happen automatically
```

### Workflow 2: Toggle as Needed

For selective approval:

```bash
autoclaude
# Work normally, approve manually
# When you see a trusted operation, press Ctrl-Y
# Auto-approve for that operation
# Press Ctrl-Y again to turn it back off
```

### Workflow 3: Debug Pattern Detection

If auto-approval isn't working:

```bash
# Terminal 1: Run with debug logging
AUTOCLAUDE_DEBUG=1 autoclaude

# Terminal 2: Watch the log
make log-tail

# In Terminal 1, press Ctrl-Y and trigger an approval prompt
# In Terminal 2, watch what AutoClaude sees
```

## Understanding the Log

### Key Log Sections

1. **USER_INPUT**: What you typed
2. **CLAUDE_OUTPUT**: What Claude sent (raw)
3. **PATTERN CHECK**: Pattern matching details
4. **PATTERN MATCH**: When a pattern matches
5. **STATUS**: Mode changes and actions

### Example Log Flow

```
[10:15:45.123] CLAUDE_OUTPUT: Do you want to proceed?\n
[10:15:45.156] CLAUDE_OUTPUT: \x1b[34m›\x1b[0m 1. Yes\n
[10:15:45.178] CLAUDE_OUTPUT:   2. No\n

[PATTERN CHECK] Buffer size: 234 chars
[PATTERN CHECK] Last 10 lines (raw):
'Do you want to proceed?\n\x1b[34m›\x1b[0m 1. Yes\n  2. No'

[PATTERN CHECK] Last 10 lines (clean):
'Do you want to proceed?\n› 1. Yes\n  2. No'

[PATTERN MATCH] Pattern #2 matched
[STATUS] Auto-responding: YES (pressing Enter)
```

Notice how:
- Raw output has ANSI codes (`\x1b[34m`)
- Clean text strips them out
- Pattern matches on clean text

## Troubleshooting

### Auto-Approval Not Working

**Symptom**: Press Ctrl-Y, mode shows ON, but approval prompt doesn't auto-respond.

**Solution**:

1. Enable debug mode:
   ```bash
   AUTOCLAUDE_DEBUG=1 autoclaude
   ```

2. Check the log:
   ```bash
   make log-view
   ```

3. Look for `[PATTERN CHECK]` entries near the approval prompt

4. Common issues:
   - **No pattern match**: Prompt format changed, need to update patterns
   - **ANSI codes**: Should be handled now, but verify in log
   - **Timing**: Prompt split across chunks (already handled)

### False Positives

**Symptom**: Auto-approval triggers on wrong text.

**Solution**: Check log for `[PATTERN MATCH]`, see what triggered it, refine patterns.

### Installation Issues

**Symptom**: `autoclaude: command not found`

**Solution**:
```bash
# Add to PATH
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc

# Or for zsh
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc
```

## Advanced Usage

### Custom Installation Path

Edit Makefile variables:
```makefile
AUTOCLAUDE_HOME := $(HOME)/.autoclaude
BIN_DIR := $(HOME)/.local/bin
```

### Testing Without Installing

```bash
make install-local          # Make scripts executable
./autoclaude.py claude      # Run from source directory
```

### Development Workflow

```bash
# Make changes to autoclaude.py
make install-local

# Test locally
AUTOCLAUDE_DEBUG=1 ./autoclaude.py claude

# When ready, install
make install
```

## Pattern Customization

Patterns are in `autoclaude.py`:

```python
self.approval_patterns = [
    # Add your own patterns here
    re.compile(r'Your custom pattern', re.IGNORECASE | re.MULTILINE),
]
```

After editing:
```bash
make install    # Reinstall with new patterns
```

## Performance Tips

- **Disable logging**: Only use `AUTOCLAUDE_DEBUG=1` when debugging
- **Clear logs**: `make log-clear` periodically to keep log file small
- **Minimal overhead**: When not debugging, AutoClaude adds < 1ms latency

## Security Notes

- All code runs locally
- No network access
- No external dependencies
- Source code is transparent
- Virtual environment isolated from system

## Getting Help

1. **Documentation**:
   - README.md - Overview
   - QUICKSTART.md - Quick start
   - INSTALL.md - Installation
   - DEBUG.md - Debugging
   - TESTING.md - Testing

2. **Debug First**: Enable `AUTOCLAUDE_DEBUG=1` to see what's happening

3. **Check Patterns**: View `autoclaude.py` to see current patterns

4. **Update**: `make install` to apply any changes

## Tips & Tricks

### Alias for Speed

Add to `~/.bashrc` or `~/.zshrc`:
```bash
alias c='autoclaude'
alias cd='AUTOCLAUDE_DEBUG=1 autoclaude'  # c with debug
```

Now:
```bash
c           # Quick launch
cd          # Launch with debug
```

### Log Monitoring

Keep a terminal open with log tail:
```bash
watch -n 1 tail -20 ~/.autoclaude/autoclaude.log
```

### Quick Pattern Test

```bash
# Search log for specific text
grep -i "do you want" ~/.autoclaude/autoclaude.log

# See last pattern check
grep "PATTERN CHECK" ~/.autoclaude/autoclaude.log | tail -1
```

## FAQ

**Q: Does AutoClaude modify Claude's behavior?**  
A: No, it only forwards I/O and automatically presses Enter when you toggle it on.

**Q: Can I use it with other commands?**  
A: Yes! `autoclaude bash`, `autoclaude python3`, etc.

**Q: How do I uninstall?**  
A: `make uninstall` removes everything.

**Q: Where are files stored?**  
A: `~/.autoclaude/` (main files) and `~/.local/bin/autoclaude` (wrapper)

**Q: Does it work on Windows?**  
A: No, requires Unix-like system with PTY support (Linux/macOS).

**Q: Can I have multiple sessions?**  
A: Yes, each terminal can run its own `autoclaude` session.

**Q: What if patterns don't match?**  
A: Enable debug mode, check the log, and adjust patterns in `autoclaude.py`.
