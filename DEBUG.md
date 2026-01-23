# AutoClaude Debugging Guide

## Enabling Debug Logging

AutoClaude includes comprehensive logging to help debug pattern detection issues.

### Enable Logging

```bash
# Set environment variable
AUTOCLAUDE_DEBUG=1 autoclaude

# Or for local development
AUTOCLAUDE_DEBUG=1 ./autoclaude.py claude
```

### Log Location

All debug logs are written to:
```
~/.autoclaude/autoclaude.log
```

## Viewing Logs

### Real-time Monitoring

```bash
# Tail the log in real-time
make log-tail

# Or manually
tail -f ~/.autoclaude/autoclaude.log
```

### View Entire Log

```bash
# View with less
make log-view

# Or manually
less ~/.autoclaude/autoclaude.log
cat ~/.autoclaude/autoclaude.log
```

### Clear Logs

```bash
# Clear the log file
make log-clear

# Or manually
rm ~/.autoclaude/autoclaude.log
```

## What Gets Logged

The log file contains:

### 1. Session Information
```
================================================================================
AutoClaude session started: 2026-01-23 10:15:32.123456
Command: claude
================================================================================
```

### 2. User Input
Every keystroke and input sequence:
```
[10:15:45.123] USER_INPUT: hello\n
[10:15:48.456] USER_INPUT: \x19  # Ctrl-Y
```

### 3. Claude Output
All output from Claude:
```
[10:15:45.234] CLAUDE_OUTPUT: Claude Code v2.1.17\n
[10:15:45.567] CLAUDE_OUTPUT: Welcome back!\n
```

### 4. Status Messages
Auto-approve toggles and actions:
```
[STATUS] Auto-approve mode: ON
[STATUS] Auto-responding: YES (pressing Enter)
```

### 5. Pattern Matching

Detailed pattern checking when auto-approve is ON:
```
[PATTERN CHECK] Buffer size: 1234 chars
[PATTERN CHECK] Last 10 lines:
'Do you want to proceed?\n› 1. Yes\n  2. No'

[PATTERN CHECK] Pattern #0 no match: Do you want to (?:proceed|continue)\?\s*\n\s*(?:›\s*)?1\.\s*Yes
[PATTERN CHECK] Pattern #1 no match: (?:Do you want to|Continue|Proceed...
[PATTERN MATCH] Pattern #2 matched: (?:›\s*)?1\.\s*Yes\s*\n\s*2\.\s*No
[PATTERN MATCH] Matched text: '› 1. Yes\n  2. No'
```

### 6. Session End
```
================================================================================
AutoClaude session ended: 2026-01-23 10:20:15.789012
================================================================================
```

## Common Debugging Scenarios

### Scenario 1: Auto-Approve Not Triggering

**Problem**: You press Ctrl-Y, auto-approve mode is ON, but Claude's approval prompt isn't being detected.

**Debug Steps**:

1. Enable debug logging:
   ```bash
   AUTOCLAUDE_DEBUG=1 autoclaude
   ```

2. Trigger the approval prompt

3. Check the log:
   ```bash
   make log-view
   ```

4. Look for:
   - `[CLAUDE_OUTPUT]` - What Claude actually sent
   - `[PATTERN CHECK]` - What patterns were tested
   - `[PATTERN MATCH]` or absence of it

5. Common issues:
   - **ANSI escape codes**: Claude might be sending color codes that break pattern matching
   - **Timing**: Prompt might be split across multiple output chunks
   - **Format differences**: Claude's prompt format might have changed

### Scenario 2: False Positives

**Problem**: Auto-approve triggers on non-approval text.

**Debug Steps**:

1. Check the log for `[PATTERN MATCH]` entries
2. See what text triggered the match
3. Refine the patterns in `autoclaude.py`

### Scenario 3: Pattern Analysis

**Example Log Analysis**:

If you see this in the log:
```
[10:15:45.234] CLAUDE_OUTPUT: Do you want to proceed?\r\n
[10:15:45.267] CLAUDE_OUTPUT: \x1b[32m›\x1b[0m 1. Yes\r\n
[10:15:45.289] CLAUDE_OUTPUT:   2. No\r\n

[PATTERN CHECK] Last 10 lines:
'Do you want to proceed?\r\n\x1b[32m›\x1b[0m 1. Yes\r\n  2. No'
[PATTERN CHECK] Pattern #0 no match
```

**Problem**: ANSI color codes (`\x1b[32m` and `\x1b[0m`) are breaking the pattern.

**Solution**: Strip ANSI codes before pattern matching (see fixes below).

## Log Output Examples

### Successful Detection

```
[10:15:45.123] CLAUDE_OUTPUT: Do you want to proceed?\n
[10:15:45.156] CLAUDE_OUTPUT: › 1. Yes\n
[10:15:45.178] CLAUDE_OUTPUT:   2. No\n

[PATTERN CHECK] Buffer size: 156 chars
[PATTERN CHECK] Last 10 lines:
'Do you want to proceed?\n› 1. Yes\n  2. No\nEsc to cancel'

[PATTERN MATCH] Pattern #2 matched: (?:›\s*)?1\.\s*Yes\s*\n\s*2\.\s*No
[PATTERN MATCH] Matched text: '› 1. Yes\n  2. No'
[STATUS] Auto-responding: YES (pressing Enter)
```

### Failed Detection (ANSI Codes)

```
[10:15:45.123] CLAUDE_OUTPUT: Do you want to proceed?\n
[10:15:45.156] CLAUDE_OUTPUT: \x1b[34m›\x1b[0m 1. Yes\n
[10:15:45.178] CLAUDE_OUTPUT:   2. No\n

[PATTERN CHECK] Buffer size: 178 chars
[PATTERN CHECK] Last 10 lines:
'Do you want to proceed?\n\x1b[34m›\x1b[0m 1. Yes\n  2. No'

[PATTERN CHECK] Pattern #0 no match
[PATTERN CHECK] Pattern #1 no match
[PATTERN CHECK] Pattern #2 no match
```

## Fixing Pattern Detection Issues

### Issue 1: ANSI Escape Codes

If you see escape sequences like `\x1b[32m` in the log, you need to strip them.

**Fix**: Add ANSI stripping to `check_for_approval_prompt()`:

```python
import re

ANSI_ESCAPE = re.compile(r'\x1b\[[0-9;]*m')

def check_for_approval_prompt(self, text: str) -> bool:
    # Strip ANSI codes
    clean_text = ANSI_ESCAPE.sub('', text)
    
    # Then do pattern matching on clean_text
    ...
```

### Issue 2: Carriage Returns

Windows-style line endings (`\r\n`) or carriage returns might cause issues.

**Fix**: Normalize line endings:

```python
# Normalize line endings
text = text.replace('\r\n', '\n').replace('\r', '\n')
```

### Issue 3: Buffering

Prompt might arrive in chunks.

**Fix**: Already handled - we check patterns on the accumulated buffer, not individual chunks.

## Advanced Debugging

### Inspect Raw Bytes

If text decoding is suspect:

```bash
# View log and search for specific output
grep "CLAUDE_OUTPUT" ~/.autoclaude/autoclaude.log | tail -20
```

### Test Patterns Manually

Create a test script:

```python
import re

# Copy patterns from autoclaude.py
pattern = re.compile(r'(?:›\s*)?1\.\s*Yes\s*\n\s*2\.\s*No', re.IGNORECASE | re.MULTILINE)

# Test with actual text from log
text = """Do you want to proceed?
› 1. Yes
  2. No"""

if pattern.search(text):
    print("MATCH!")
else:
    print("NO MATCH")
```

### Compare Expected vs Actual

1. Copy the `[PATTERN CHECK] Last 10 lines:` text from log
2. Copy the pattern that should match
3. Test them together in Python REPL

## Performance Monitoring

The log includes timestamps for every I/O operation:

```bash
# Check timing between prompt and response
grep -A 5 "Do you want to proceed" ~/.autoclaude/autoclaude.log
```

Should show ~100ms delay (configured in code).

## Reporting Issues

When reporting pattern detection issues, include:

1. **Log excerpt**: Show the relevant `[CLAUDE_OUTPUT]` and `[PATTERN CHECK]` entries
2. **Screenshot**: Visual of what Claude displayed
3. **Environment**: OS, terminal, Claude version
4. **Command**: What you asked Claude to do

Example report:
```
Pattern not matching Claude approval prompt.

Log shows:
[CLAUDE_OUTPUT] containing escape codes \x1b[34m

Screenshot attached showing blue arrow (›) before "1. Yes"

Environment: macOS 14, iTerm2, Claude CLI 2.1.17
Command: Asked Claude to run bash command
```

## Tips

- **Clear log between tests**: `make log-clear` before each test run
- **Use two terminals**: One running autoclaude, another tailing the log
- **Search efficiently**: `grep -i "pattern" ~/.autoclaude/autoclaude.log`
- **Keep logs small**: Log file grows quickly; clear it periodically

## Disabling Logging

Simply don't set `AUTOCLAUDE_DEBUG=1`. Logging is off by default for performance.
