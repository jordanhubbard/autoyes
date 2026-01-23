# AutoYes Changelog

## [2.0.0] - 2026-01-23 - "The Universal Release"

### 🎉 Major Changes

**Project renamed from AutoClaude to AutoYes**

AutoYes is now a universal auto-approval tool that works with ANY interactive command, not just Claude.

### Breaking Changes

1. **Command argument now required**
   - Old: `autoclaude` (defaulted to "claude")
   - New: `autoyes <command>` (explicit command required)

2. **Binary renamed**
   - Old: `~/.local/bin/autoclaude`
   - New: `~/.local/bin/autoyes`

3. **Directory renamed**
   - Old: `~/.autoclaude/`
   - New: `~/.autoyes/`

4. **Environment variable renamed** (backward compatible)
   - Old: `AUTOCLAUDE_DEBUG=1`
   - New: `AUTOYES_DEBUG=1` (old name still works)

### New Features

1. **Universal Command Support**
   - Works with Claude, Cursor, Terraform, kubectl, and any interactive command
   - No longer hardcoded for Claude only

2. **Additional Approval Patterns**
   - Added Terraform "Enter a value:" detection
   - Improved generic yes/no pattern matching
   - More robust pattern detection

3. **Improved Code**
   - Renamed `AutoClaude` class → `AutoYes`
   - Renamed methods to be command-agnostic
   - Generic variable names throughout

4. **New Documentation**
   - **EXAMPLES-autoyes.md**: Comprehensive examples for many tools
   - **RENAMED-TO-AUTOYES.md**: Migration guide from AutoClaude
   - Updated all docs to reflect universal nature

### Usage Examples

```bash
# AI Tools
autoyes claude
autoyes cursor
autoyes aider

# Infrastructure
autoyes terraform apply
autoyes pulumi up

# Kubernetes
autoyes kubectl apply -f config.yaml
autoyes helm install myapp ./chart

# Package Managers
autoyes apt upgrade
autoyes brew upgrade

# Any command!
autoyes <your-command> [args...]
```

### Migration from AutoClaude

```bash
# 1. Uninstall old AutoClaude
cd /path/to/autoclaude
make uninstall

# 2. Install new AutoYes
cd /path/to/autoyes
make install

# 3. Update usage
# Old: autoclaude
# New: autoyes claude
```

### Technical Details

- Version: 2.0.0
- Python: 3.6+
- Platform: Unix-like systems (Linux, macOS)
- Installation: `~/.autoyes/` with venv
- Log file: `~/.autoyes/autoyes.log`

### Backward Compatibility

- Environment variable `AUTOCLAUDE_DEBUG=1` still works
- Can create alias: `alias autoclaude='autoyes claude'`
- Both directories can coexist temporarily

### Files Renamed

- `autoclaude.py` → `autoyes.py`
- `autoclaude` (wrapper) → `autoyes`
- `autoclaude.log` → `autoyes.log`
- All documentation updated

### What Didn't Change

- Auto-approval still ON by default
- Ctrl-Y toggle still works
- Pattern detection logic improved but compatible
- Same PTY proxy mechanism
- Same installation process (`make install`)

---

## Previous Versions (as AutoClaude)

### [1.0.3] - 2026-01-23
- Auto-approval ON by default
- Cleaner startup messages

### [1.0.2] - 2026-01-23
- Fixed Enter key (changed \n to \r)
- Fixed response timing
- Added ANSI code stripping
- Improved log formatting

### [1.0.1] - 2026-01-23
- Added debug logging
- ANSI escape code handling
- Comprehensive debugging

### [1.0.0] - 2026-01-23
- Initial release as AutoClaude
- PTY proxy for Claude
- Ctrl-Y toggle
- Pattern detection

---

## Upgrade Path

### From 1.0.x to 2.0.0

**Required changes:**
1. Change command: `autoclaude` → `autoyes claude`
2. Update scripts that use `autoclaude`
3. Reinstall: `make install`

**Optional changes:**
1. Update env var: `AUTOCLAUDE_DEBUG` → `AUTOYES_DEBUG`
2. Update aliases and wrappers

**No changes needed:**
- Ctrl-Y still toggles auto-approval
- Same behavior and features
- Same installation process

---

## Future Plans

- Configuration file support
- Custom pattern definitions
- Multiple response strategies
- Session recording/playback
- Integration with CI/CD tools

---

**Welcome to AutoYes v2.0.0!** 🎉

The universal auto-approval tool for any interactive command.
