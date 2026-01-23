#!/bin/bash
# Quick test to verify logging works

echo "Testing AutoYes Logging"
echo "=========================="
echo ""

# Clear any old log
rm -f ~/.autoyes/autoyes.log

echo "1. Running with AUTOYES_DEBUG=1"
echo "   Command: AUTOYES_DEBUG=1 autoyes echo 'hello'"
echo ""

# Run with debug (use perl to timeout since macOS doesn't have timeout)
(AUTOYES_DEBUG=1 autoyes echo "hello" &
PID=$!
sleep 2
kill $PID 2>/dev/null
wait $PID 2>/dev/null) 2>&1 | head -10

echo ""
echo "2. Checking for log file..."
echo ""

if [ -f ~/.autoyes/autoyes.log ]; then
    echo "✓ Log file exists: ~/.autoyes/autoyes.log"
    echo ""
    echo "3. Log file contents:"
    echo "---------------------"
    cat ~/.autoyes/autoyes.log
    echo "---------------------"
    echo ""
    echo "✓ Logging is working!"
else
    echo "✗ Log file was not created"
    echo ""
    echo "Troubleshooting:"
    echo "  1. Check if AUTOYES_DEBUG=1 is set"
    echo "  2. Check permissions on ~/.autoyes/"
    echo "  3. Run: AUTOYES_DEBUG=1 autoyes --version"
fi
