# AutoYes Quick Start

## Install (One Command)

```bash
make install
```

## Use (With Any Command)

```bash
autoyes <command> [args...]
```

Examples:
```bash
autoyes claude        # Claude with auto-approval
autoyes cursor        # Cursor with auto-approval
autoyes terraform apply    # Terraform with auto-approval
```

That's it! 🎉

## The Magic Toggle

AutoYes starts with auto-approval **ON** by default:

- **Starts ON** → Automatically approves "Do you want to proceed?" prompts
- **Press `Ctrl-Y`** → Toggle OFF (manual approval)
- **Press `Ctrl-Y` again** → Toggle back ON
- **Press `Ctrl-C`** → Exit

## What It Does

AutoYes is a transparent proxy that:
1. Runs any command in a real terminal (PTY)
2. Passes all input/output through
3. Watches for approval prompts
4. Auto-responds when enabled (default)

## Common Use Cases

### 🤖 AI Tools
```bash
autoyes claude        # Claude CLI
autoyes cursor        # Cursor
autoyes aider         # Aider
```

### ☁️ Infrastructure
```bash
autoyes terraform apply
autoyes pulumi up
autoyes kubectl apply -f config.yaml
```

### 📦 Package Management
```bash
autoyes apt upgrade
autoyes brew upgrade
autoyes npm install
```

### 🧹 Cleanup Operations
```bash
autoyes docker system prune
autoyes git clean -fdx
```

## Debug Mode

If auto-approval isn't working:

```bash
# Enable debug logging
AUTOYES_DEBUG=1 autoyes <command>

# In another terminal, watch the log
make log-tail
```

Check `~/.autoyes/autoyes.log` to see what AutoYes is detecting.

## After Installation

- **Command**: `autoyes <command>` (works with any command)
- **Location**: `~/.autoyes/`
- **Wrapper**: `~/.local/bin/autoyes`

## Need Help?

```bash
# Show all make targets
make help

# Test the installation
make test

# Uninstall everything
make uninstall
```

## PATH Not Set?

If `autoyes` command not found:

```bash
# Bash
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc

# Zsh
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc
```

## Safety Tips

⚠️ AutoYes automatically approves prompts! Always:
- Know what command you're running
- Test with safe commands first
- Use Ctrl-Y to disable for dangerous operations

---

**Pro Tip**: Set an alias for even faster access:

```bash
# Add to ~/.bashrc or ~/.zshrc
alias ay='autoyes'
```

Now just type `ay claude` or `ay terraform apply`! ⚡
