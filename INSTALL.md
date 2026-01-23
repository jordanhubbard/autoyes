# AutoClaude Installation Guide

## Quick Install

```bash
cd /path/to/autoclaude
make install
```

That's it! Now you can type `autoclaude` from anywhere.

## What Gets Installed

### Directory Structure

```
~/.autoclaude/
├── venv/              # Python virtual environment
├── autoclaude.py      # Main Python script
└── test_approval.py   # Test script

~/.local/bin/
└── autoclaude         # Shell wrapper (in your PATH)
```

### Installation Steps (Automatic)

1. **Creates `~/.autoclaude` directory** - All AutoClaude files live here
2. **Creates Python venv** - Isolated environment in `~/.autoclaude/venv`
3. **Copies scripts** - Python files copied to `~/.autoclaude`
4. **Installs wrapper** - Shell script to `~/.local/bin/autoclaude`
5. **Sets permissions** - Makes everything executable

## Verify Installation

```bash
# Check if autoclaude is in your PATH
which autoclaude
# Should show: /Users/yourusername/.local/bin/autoclaude

# Run it
autoclaude --version  # or just: autoclaude
```

## PATH Setup

If `autoclaude` command is not found, add `~/.local/bin` to your PATH:

### For Bash (~/.bashrc)

```bash
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

### For Zsh (~/.zshrc)

```bash
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc
```

### For Fish (~/.config/fish/config.fish)

```fish
fish_add_path $HOME/.local/bin
```

## Usage After Installation

```bash
# Just type autoclaude (replaces 'claude')
autoclaude

# With arguments
autoclaude --model claude-3-5-sonnet-20241022
autoclaude --help

# Ctrl-Y to toggle auto-approval
# Ctrl-C to exit
```

## Update AutoClaude

To update to a new version:

```bash
cd /path/to/autoclaude
git pull  # or download new version
make install
```

This will overwrite the existing installation with the new version.

## Uninstall

```bash
cd /path/to/autoclaude
make uninstall
```

This removes:
- `~/.autoclaude/` directory (including venv)
- `~/.local/bin/autoclaude` wrapper

## Development Mode

If you're developing AutoClaude and want to test local changes:

```bash
# Make local scripts executable
make install-local

# Run from source directory
./autoclaude.py claude

# Or use the wrapper (still runs local version if you're in the dir)
./autoclaude
```

## Troubleshooting

### Command not found

**Problem:** `autoclaude: command not found`

**Solution:** Add `~/.local/bin` to your PATH (see PATH Setup above)

### Permission denied

**Problem:** Permission errors during installation

**Solution:** Make sure you have write access to `~/.autoclaude` and `~/.local/bin`

```bash
mkdir -p ~/.local/bin
chmod u+w ~/.local/bin
```

### Python version

**Problem:** `python3: command not found`

**Solution:** AutoClaude requires Python 3.6 or later. Install Python 3:

```bash
# macOS
brew install python3

# Ubuntu/Debian
sudo apt install python3 python3-venv

# Fedora/RHEL
sudo dnf install python3
```

### Virtual environment issues

**Problem:** Venv creation fails

**Solution:** Install python3-venv package:

```bash
# Ubuntu/Debian
sudo apt install python3-venv

# Or recreate manually:
rm -rf ~/.autoclaude/venv
python3 -m venv ~/.autoclaude/venv
```

## Files and Sizes

- `autoclaude.py`: ~8 KB (main program)
- `autoclaude`: ~1 KB (shell wrapper)
- `test_approval.py`: ~2 KB (test script)
- Virtual environment: ~15-20 MB

Total installation size: ~20-25 MB

## Security Notes

- All code runs locally on your machine
- No external dependencies beyond Python standard library
- Virtual environment is isolated from system Python
- Source code is transparent and auditable

## Advanced: Custom Installation Location

To install to a different location, edit the Makefile variables:

```makefile
AUTOCLAUDE_HOME := $(HOME)/.autoclaude  # Change this
BIN_DIR := $(HOME)/.local/bin           # And this
```

Then run `make install`.
