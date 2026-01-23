.PHONY: help install install-local uninstall run test test-bash clean log-tail log-view log-clear

# Installation directories
AUTOYES_HOME := $(HOME)/.autoyes
VENV_DIR := $(AUTOYES_HOME)/venv
BIN_DIR := $(HOME)/.local/bin
LOG_FILE := $(AUTOYES_HOME)/autoyes.log

help:
	@echo "AutoYes - Interactive PTY Proxy with Auto-Approval"
	@echo ""
	@echo "Available targets:"
	@echo "  make install       - Install to ~/.autoyes and ~/.local/bin (recommended)"
	@echo "  make install-local - Make local scripts executable for development"
	@echo "  make uninstall     - Remove installed files from home directory"
	@echo "  make run           - Run AutoYes with echo (local test)"
	@echo "  make test          - Test auto-approval with simulated prompts"
	@echo "  make test-bash     - Test with bash shell"
	@echo "  make clean         - Remove temporary files"
	@echo ""
	@echo "Debugging targets:"
	@echo "  make log-tail      - Tail the debug log in real-time"
	@echo "  make log-view      - View the entire debug log"
	@echo "  make log-clear     - Clear the debug log"
	@echo ""
	@echo "After 'make install', just type: autoyes <command>"
	@echo ""
	@echo "Enable debug logging:"
	@echo "  AUTOYES_DEBUG=1 autoyes <command>"
	@echo ""
	@echo "Local development usage:"
	@echo "  ./autoyes.py <command> [args...]"
	@echo "  ./autoyes.py echo 'test'"

install:
	@echo "Installing AutoYes to your home directory..."
	@echo ""
	@# Create directory structure
	@mkdir -p "$(AUTOYES_HOME)"
	@mkdir -p "$(BIN_DIR)"
	@echo "✓ Created $(AUTOYES_HOME)"
	@# Create virtual environment
	@if [ ! -d "$(VENV_DIR)" ]; then \
		echo "✓ Creating virtual environment..."; \
		python3 -m venv "$(VENV_DIR)"; \
	else \
		echo "✓ Virtual environment already exists"; \
	fi
	@# Copy Python script
	@cp autoyes.py "$(AUTOYES_HOME)/autoyes.py"
	@chmod +x "$(AUTOYES_HOME)/autoyes.py"
	@echo "✓ Installed autoyes.py to $(AUTOYES_HOME)"
	@# Copy test script
	@cp test_approval.py "$(AUTOYES_HOME)/test_approval.py"
	@chmod +x "$(AUTOYES_HOME)/test_approval.py"
	@echo "✓ Installed test_approval.py to $(AUTOYES_HOME)"
	@# Install wrapper script
	@cp autoyes "$(BIN_DIR)/autoyes"
	@chmod +x "$(BIN_DIR)/autoyes"
	@echo "✓ Installed autoyes wrapper to $(BIN_DIR)"
	@echo ""
	@echo "╔════════════════════════════════════════════════════════════╗"
	@echo "║  Installation Complete!                                    ║"
	@echo "╚════════════════════════════════════════════════════════════╝"
	@echo ""
	@echo "AutoYes is now installed and ready to use!"
	@echo ""
	@echo "Location:  $(AUTOYES_HOME)"
	@echo "Wrapper:   $(BIN_DIR)/autoyes"
	@echo "Venv:      $(VENV_DIR)"
	@echo ""
	@echo "Usage:"
	@echo "  autoyes <command> [args...]   # Run any command with auto-approval"
	@echo ""
	@echo "Examples:"
	@echo "  autoyes claude                # AI assistant"
	@echo "  autoyes terraform apply       # Infrastructure as code"
	@echo ""
	@echo "Controls:"
	@echo "  Ctrl-Y    Toggle auto-approval ON/OFF (starts ON)"
	@echo "  Ctrl-C    Exit"
	@echo ""
	@# Check if ~/.local/bin is in PATH
	@if echo "$$PATH" | grep -q "$(BIN_DIR)"; then \
		echo "✓ $(BIN_DIR) is in your PATH"; \
	else \
		echo "⚠  $(BIN_DIR) is NOT in your PATH"; \
		echo ""; \
		echo "Add this to your ~/.bashrc or ~/.zshrc:"; \
		echo "  export PATH=\"\$$HOME/.local/bin:\$$PATH\""; \
		echo ""; \
		echo "Then run: source ~/.bashrc  (or source ~/.zshrc)"; \
	fi
	@echo ""

install-local:
	@echo "Making local scripts executable..."
	@chmod +x autoyes.py autoyes test_approval.py
	@echo "✓ Local scripts are now executable"
	@echo ""
	@echo "Run with: ./autoyes.py <command>"
	@echo "Or use:   ./autoyes <command> (wrapper script)"

uninstall:
	@echo "Uninstalling AutoYes..."
	@rm -rf "$(AUTOYES_HOME)"
	@rm -f "$(BIN_DIR)/autoyes"
	@echo "✓ Removed $(AUTOYES_HOME)"
	@echo "✓ Removed $(BIN_DIR)/autoyes"
	@echo ""
	@echo "AutoYes has been uninstalled."

run: install-local
	./autoyes.py echo "AutoYes is working!"

test: install-local
	@echo "Testing auto-approval with simulated prompts..."
	@echo "Press Ctrl-Y to toggle auto-approve mode"
	@echo "Watch it automatically select 'Yes' when enabled!"
	@echo ""
	./autoyes.py python3 test_approval.py

test-bash: install-local
	@echo "Testing with bash shell (exit with Ctrl-C)..."
	@echo "Auto-approval starts ON - press Ctrl-Y to toggle"
	./autoyes.py bash

clean:
	@echo "Cleaning up temporary files..."
	@find . -type f -name "*.pyc" -delete
	@find . -type d -name "__pycache__" -delete
	@echo "✓ Cleaned"

log-tail:
	@if [ -f "$(LOG_FILE)" ]; then \
		echo "Tailing $(LOG_FILE) (Ctrl-C to stop)..."; \
		tail -f "$(LOG_FILE)"; \
	else \
		echo "Log file does not exist: $(LOG_FILE)"; \
		echo "Run: AUTOYES_DEBUG=1 autoyes <command>"; \
	fi

log-view:
	@if [ -f "$(LOG_FILE)" ]; then \
		less "$(LOG_FILE)"; \
	else \
		echo "Log file does not exist: $(LOG_FILE)"; \
		echo "Run: AUTOYES_DEBUG=1 autoyes <command>"; \
	fi

log-clear:
	@if [ -f "$(LOG_FILE)" ]; then \
		rm "$(LOG_FILE)"; \
		echo "✓ Cleared $(LOG_FILE)"; \
	else \
		echo "Log file does not exist: $(LOG_FILE)"; \
	fi
