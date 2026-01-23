# AutoClaude v1.0.3 - Auto-Approval ON by Default

## The Change

Starting with v1.0.3, **auto-approval is ON by default** when you launch autoclaude.

## Why?

The whole point of AutoClaude is to auto-approve prompts. Having to press Ctrl-Y every time you start it defeated the purpose. Now it works the way you'd expect:

```bash
autoclaude
# It's already in auto-approve mode!
# Just use Claude normally, approvals happen automatically
```

## What Changed

### Before (v1.0.0 - v1.0.2)

```bash
$ autoclaude
[AutoClaude] Starting Claude: claude
[AutoClaude] Press Ctrl-Y to toggle auto-approval mode  ← Had to enable it
[AutoClaude] Press Ctrl-C to exit

# Press Ctrl-Y
[AutoClaude] Auto-approve mode: ON
```

### After (v1.0.3+)

```bash
$ autoclaude
[AutoClaude] Starting Claude: claude
[AutoClaude] Auto-approval: ON (press Ctrl-Y to toggle)  ← Already ON!
[AutoClaude] Press Ctrl-C to exit

# Just start working, approvals happen automatically
```

## Behavior

### Startup
- Auto-approval starts **ON**
- One-line message in green: "Auto-approval: ON (press Ctrl-Y to toggle)"
- No toggle spam unless you actively change it

### When You Press Ctrl-Y
- **First press**: Turns OFF → Shows "Auto-approve mode: OFF" (red)
- **Second press**: Turns ON → Shows "Auto-approve mode: ON" (green)
- **And so on...**

Only shows the toggle message when you actively change it.

## Use Cases

### Use Case 1: Batch Operations (Default)

Perfect - just launch and go:

```bash
autoclaude
# Ask Claude to do many things
# All approvals happen automatically
# No need to press Ctrl-Y
```

### Use Case 2: Selective Approval

Turn it off when you need manual control:

```bash
autoclaude
# Press Ctrl-Y to disable auto-approve
# Review each prompt manually
# Press Ctrl-Y again when ready for auto-approve
```

### Use Case 3: Long-Running Tasks

Already enabled - perfect for complex tasks:

```bash
autoclaude
# Ask Claude to refactor a large codebase
# Walk away, come back to completed work
# No need to babysit the approvals
```

## Controls

- **Start**: Auto-approval is ON
- **Ctrl-Y**: Toggle OFF → ON → OFF → ...
- **Ctrl-C**: Exit

## Code Changes

### Main Change

```python
# Before (v1.0.2)
def __init__(self, claude_command: list[str], enable_logging: bool = False):
    self.auto_approve = False  # Start OFF

# After (v1.0.3)
def __init__(self, claude_command: list[str], enable_logging: bool = False):
    self.auto_approve = True  # Start ON
```

### Startup Message

```python
# Before (v1.0.2)
self.print_status("Press Ctrl-Y to toggle auto-approval mode", BLUE)

# After (v1.0.3)
self.print_status("Auto-approval: ON (press Ctrl-Y to toggle)", GREEN)
```

## Migration

No action needed! Just:

```bash
make install
autoclaude
```

It will start in auto-approve mode automatically.

## For Users Who Want Manual Approval

If you prefer to start with auto-approve OFF:

**Option 1**: Press Ctrl-Y immediately after launch

```bash
autoclaude
# Immediately press Ctrl-Y
[AutoClaude] Auto-approve mode: OFF
```

**Option 2**: Create a wrapper script

```bash
# ~/bin/autoclaude-manual
#!/bin/bash
autoclaude "$@" &
PID=$!
sleep 0.5
# Send Ctrl-Y
kill -USR1 $PID  # or implement signal handling
wait $PID
```

**Option 3**: Feature request

If you want a `--no-auto-approve` flag, let me know and I can add it!

## Philosophy

AutoClaude is "tmux for Claude" - it's meant to run in the background and handle approvals automatically. Starting with auto-approve ON aligns with this philosophy:

- **Default behavior**: Auto-approve everything
- **Override when needed**: Ctrl-Y to disable temporarily
- **Principle of least surprise**: It does what the name suggests

## Documentation Updates

All documentation has been updated:

- ✅ README.md - Updated startup examples
- ✅ QUICKSTART.md - Updated use cases
- ✅ TESTING.md - Updated test scenarios
- ✅ USAGE_GUIDE.md - Updated controls
- ✅ CHANGELOG.md - Added v1.0.3 entry

## Upgrade

```bash
cd /path/to/autoclaude
make install
autoclaude --version  # Should show v1.0.3
```

## Feedback

This change makes AutoClaude more useful out of the box. If you have feedback or want configuration options, let me know!

## Summary

| Aspect | v1.0.2 | v1.0.3 |
|--------|--------|--------|
| Default state | OFF | **ON** |
| Startup action | Press Ctrl-Y | Nothing - already ON |
| Toggle behavior | Shows message | Only shows when you toggle |
| Message color | Blue | Green (ON) / Red (OFF) |
| Philosophy | Opt-in | Opt-out |

**Bottom line**: Launch autoclaude and it just works. No extra steps!
