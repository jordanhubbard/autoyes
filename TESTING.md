# Testing AutoClaude

## Quick Test (Simulated Prompts)

Test the auto-approval functionality without running actual Claude:

```bash
# From source directory (before install)
make test

# Or run directly
./autoclaude.py python3 test_approval.py

# After 'make install', the test script is also installed
autoclaude python3 ~/.autoclaude/test_approval.py
```

This will:
1. Show simulated Claude approval prompts
2. Let you test Ctrl-Y toggle
3. Demonstrate auto-approval in action

### Testing Steps:

1. Run the test command above
2. You'll see a simulated approval prompt
3. Auto-approval is already ON - it will automatically press Enter
4. Press **Ctrl-Y** to disable auto-approval mode
5. Next prompt will wait for your manual input
6. Press **Ctrl-Y** again to re-enable auto-approval

## Testing with Real Claude

```bash
# After 'make install'
autoclaude

# Or before install (from source directory)
./autoclaude.py claude
```

Then:
1. Ask Claude to run a bash command that requires approval
2. When you see "Do you want to proceed?", press **Ctrl-Y**
3. AutoClaude will automatically press Enter to approve
4. Toggle off with **Ctrl-Y** when you want manual control back

## Visual Indicators

When auto-approval is working, you'll see:

```
[AutoClaude] Auto-approve mode: ON          # Green - enabled
[AutoClaude] Auto-responding: YES (pressing Enter)  # Yellow - auto-responding
[AutoClaude] Auto-approve mode: OFF         # Red - disabled
```

## Common Test Scenarios

### Scenario 1: Rapid Approvals
Auto-approval is ON by default. Ask Claude to perform multiple operations that require approval. All will be auto-approved.

### Scenario 2: Selective Approval
Turn auto-approval OFF (Ctrl-Y), manually review each prompt, and re-enable (Ctrl-Y) for trusted operations.

### Scenario 3: Batch Processing
Auto-approval is already ON - perfect for long tasks with many approval steps. Disable (Ctrl-Y) when you need manual control.

## Troubleshooting

### Auto-approval not triggering?

1. **Check the buffer size**: The prompt must appear in the last 10 lines of output
2. **Check the format**: Works best with Claude's standard "Do you want to proceed?" format
3. **Timing**: There's a 0.1s delay to ensure the prompt is fully rendered

### False positives?

If auto-approval triggers on non-approval text:
- Check the patterns in `autoclaude.py`
- The patterns are designed to be specific to avoid false positives
- Open an issue if you encounter false triggers

## Advanced Testing

### Test with different shells
```bash
./autoclaude.py bash
./autoclaude.py zsh
./autoclaude.py fish
```

### Test with Python REPL
```bash
./autoclaude.py python3
```

### Test with other CLI tools
```bash
./autoclaude.py <any-interactive-command>
```

## Performance Notes

- PTY proxying adds minimal latency (< 1ms)
- Pattern matching is efficient even with large buffers
- Auto-response delay is 0.1s (100ms) to ensure prompt stability
