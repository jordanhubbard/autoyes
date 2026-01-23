#!/bin/bash
# Test script to verify debug logging works

echo "Testing AutoYes Debug Logging"
echo "================================="
echo ""

# Clear any existing log
make log-clear 2>/dev/null

# Run a quick test with debug enabled
echo "Running: AUTOYES_DEBUG=1 ./autoyes.py echo 'test'"
echo ""

AUTOYES_DEBUG=1 timeout 2s ./autoyes.py echo "test" 2>&1 | head -20 || true

echo ""
echo "Checking log file..."
echo ""

if [ -f ~/.autoyes/autoyes.log ]; then
    echo "✓ Log file created: ~/.autoyes/autoyes.log"
    echo ""
    echo "Log contents:"
    echo "-------------"
    head -20 ~/.autoyes/autoyes.log
    echo ""
    echo "✓ Debug logging is working!"
else
    echo "✗ Log file not created"
    echo "Something went wrong"
    exit 1
fi
