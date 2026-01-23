#!/bin/bash
# Example usage scenarios for AutoYes

echo "AutoYes - Example Usage"
echo "=========================="
echo ""

echo "After 'make install', use autoyes with any command:"
echo ""

# Basic usage
echo "1. With Claude:"
echo "   autoyes claude"
echo ""

echo "2. With Cursor:"
echo "   autoyes cursor"
echo ""

echo "3. With Terraform:"
echo "   autoyes terraform apply"
echo ""

echo "4. With kubectl:"
echo "   autoyes kubectl apply -f config.yaml"
echo ""

echo "5. With any command:"
echo "   autoyes <your-command> [args...]"
echo ""

echo "──────────────────────────────────────────────────"
echo ""
echo "For local development (before 'make install'):"
echo ""

echo "6. Using the Python script directly:"
echo "   ./autoyes.py <command>"
echo ""

echo "7. Test with bash:"
echo "   ./autoyes.py bash"
echo ""

echo "8. Test with Python REPL:"
echo "   ./autoyes.py python3"
echo ""

echo "──────────────────────────────────────────────────"
echo ""
echo "Interactive controls:"
echo "  - Auto-approval starts ON by default"
echo "  - Press Ctrl-Y to toggle auto-approval OFF/ON"
echo "  - Press Ctrl-C to exit"
echo ""
