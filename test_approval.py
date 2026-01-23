#!/usr/bin/env python3
"""
Test script to simulate approval prompts
Use this to test AutoYes's detection without running actual commands
"""

import sys
import time

def simulate_approval_prompt():
    """Simulate an approval prompt"""
    print("\nBash command")
    time.sleep(0.5)
    print("\nbd show horde-j82dc0")
    print("Get details for QEMU zombie processes bead")
    time.sleep(0.5)
    print("\nPermission rule Bash requires confirmation for this command.")
    time.sleep(0.5)
    print("\nDo you want to proceed?")
    print("› 1. Yes")
    print("  2. No")
    time.sleep(0.5)
    print("\nEsc to cancel · Tab to add additional instructions")
    
    # Wait for user input
    response = input()
    
    if response == "" or response == "1" or response.lower() == "yes":
        print("\n✓ Proceeding with command...")
        return True
    else:
        print("\n✗ Cancelled")
        return False

def main():
    print("=" * 60)
    print("Approval Prompt Simulator")
    print("=" * 60)
    print("\nThis simulates a typical approval prompt.")
    print("Use this with AutoYes to test auto-approval:")
    print("\n  ./autoyes.py python3 test_approval.py")
    print("\nThen press Ctrl-Y to enable auto-approval mode.")
    print("=" * 60)
    
    count = 1
    while True:
        print(f"\n\n--- Prompt #{count} ---")
        time.sleep(1)
        
        if simulate_approval_prompt():
            print("Continuing to next prompt in 2 seconds...")
            time.sleep(2)
            count += 1
        else:
            print("\nExiting...")
            break

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nInterrupted by user. Goodbye!")
        sys.exit(0)
