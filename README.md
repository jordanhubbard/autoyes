# AutoYes - Interactive PTY Proxy with Auto-Approval

A universal "auto-yes" wrapper for any interactive command. Runs commands in a pseudo-terminal with automatic approval of prompts.

> **Quick Start**: Run `make install`, then type `autoyes <command>` anywhere. Auto-approval is ON by default!

📖 **Documentation**: [Quick Start](QUICKSTART.md) | [Installation](INSTALL.md) | [Examples](EXAMPLES.md)

## Features

- **Universal**: Works with any interactive command (Claude, Cursor, Terraform, kubectl, etc.)
- **Full PTY Support**: Commands think they're attached to a real terminal
- **Transparent Proxy**: All input and output passes through seamlessly
- **Auto-Approval ON by Default**: Automatically responds to approval prompts
- **Toggle Control**: Press Ctrl-Y to toggle auto-approval ON/OFF
- **Smart Detection**: Intelligently detects various approval prompt patterns
- **Visual Feedback**: Color-coded status messages

## Installation

### System-Wide Installation (Recommended)

Install AutoYes to `~/.autoyes` and `~/.local/bin`:

```bash
make install
```

This will:
- Create `~/.autoyes/` directory
- Set up a Python virtual environment in `~/.autoyes/venv`
- Install the Python script and wrapper
- Add `autoyes` command to `~/.local/bin`

After installation, ensure `~/.local/bin` is in your PATH:

```bash
# Add to ~/.bashrc or ~/.zshrc if needed:
export PATH="$HOME/.local/bin:$PATH"
```

## Usage

### Basic Usage

```bash
# Run Claude with auto-approval
autoyes claude

# Run Cursor with auto-approval
autoyes cursor

# Run Terraform with auto-approval
autoyes terraform apply

# Run kubectl with auto-approval
autoyes kubectl apply -f config.yaml

# Any interactive command works!
autoyes <your-command> [args...]
```

### Interactive Controls

- **Ctrl-Y**: Toggle auto-approval OFF/ON (starts ON by default)
- **Ctrl-C**: Exit the session

### Auto-Approval Mode

AutoYes starts with auto-approval ON by default. It will:

1. Monitor command output for approval prompts
2. Automatically detect patterns like:
   - Numbered menus: "1. Yes / 2. No"
   - "Do you want to proceed?" prompts
   - "(yes/no)" or "(y/n)" questions
   - Terraform "Enter a value:" prompts
3. Automatically press Enter or respond "yes"
4. Show a status message when auto-responding

Toggle it off by pressing Ctrl-Y if you want manual control.

## Example Session

```
$ autoyes claude

[AutoYes] Starting: claude
[AutoYes] Auto-approval: ON (press Ctrl-Y to toggle)
[AutoYes] Press Ctrl-C to exit

# Claude asks: "Do you want to proceed?" with "1. Yes / 2. No"
[AutoYes] Auto-responding: YES (pressing Enter)

# If you want manual control, press Ctrl-Y:
[AutoYes] Auto-approve mode: OFF

# Press Ctrl-Y again to turn it back on
[AutoYes] Auto-approve mode: ON

# Exit with Ctrl-C
[AutoYes] Session ended
```

## Debugging

If auto-approval isn't working, enable debug logging:

```bash
AUTOYES_DEBUG=1 autoyes <command>
```

This logs all I/O and pattern matching to `~/.autoyes/autoyes.log`.

View the log:
```bash
make log-view      # View entire log
make log-tail      # Tail in real-time
make log-clear     # Clear log
```

## Use Cases

### Claude / Cursor
```bash
autoyes claude
autoyes cursor
```

### Infrastructure as Code
```bash
autoyes terraform apply
autoyes terraform destroy
autoyes pulumi up
```

### Kubernetes
```bash
autoyes kubectl apply -f deployment.yaml
autoyes kubectl delete pod my-pod
autoyes helm install myapp ./mychart
```

### Package Managers
```bash
autoyes apt upgrade
autoyes brew upgrade
autoyes npm install
```

### Any Interactive Tool
```bash
autoyes docker system prune
autoyes git clean -fdx
autoyes rm -rf /path/to/important/stuff  # (be careful!)
```

## Approval Patterns Detected

AutoYes recognizes these common patterns:

- **Numbered menus**: `1. Yes` / `2. No`
- **"Do you want to proceed?"** prompts
- **Generic yes/no**: `(yes/no)`, `(y/n)`, `[Y/n]`
- **Terraform**: `Enter a value:` prompts
- And many other common approval formats

## Requirements

- Python 3.6+
- Unix-like system (Linux, macOS) with PTY support
- The command you want to run must be installed

## Uninstall

```bash
make uninstall
```

This removes all installed files from `~/.autoyes` and `~/.local/bin/autoyes`.

## Limitations

- Currently Unix/Linux/macOS only (requires PTY support)
- Auto-approval detection is pattern-based and may occasionally miss unusual prompts
- Ctrl-Y character is consumed and won't be sent to the command (this is intentional)

## Safety Note

⚠️ **Use with caution!** AutoYes automatically approves prompts, including destructive operations. Always:
- Know what command you're running
- Understand what it will do
- Use Ctrl-Y to disable auto-approval for dangerous operations
- Test with safe commands first

## Philosophy

AutoYes is a "yes | command" replacement that:
- Works with interactive commands that need a real TTY
- Lets you see the prompts before they're approved
- Gives you toggle control (Ctrl-Y) for selective approval
- Makes batch operations and CI/CD workflows easier

## Version

Current version: 2.0.0 (renamed from AutoClaude)

## License

MIT License - feel free to use and modify as needed.
