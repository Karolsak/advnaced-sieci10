#!/usr/bin/env python3
"""
Standalone launcher for Synchronous Generator Lab
Use this to avoid Jupyter notebook caching issues
"""

import sys
import os

# Ensure we're using the current directory's modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Clear any cached imports
if 'synchronous_generator_lab' in sys.modules:
    del sys.modules['synchronous_generator_lab']

# Now import and run
from synchronous_generator_lab import main

if __name__ == "__main__":
    print("="*70)
    print("Advanced Synchronous Generator Simulation Lab")
    print("Example 7.3 - Complete Solution with Multi-Physics Modeling")
    print("="*70)
    print("\nLaunching GUI application...")
    print("\nNOTE: If running from Jupyter, please restart the kernel first")
    print("      to ensure the latest code is loaded.\n")

    try:
        main()
    except KeyboardInterrupt:
        print("\n\nApplication closed by user.")
    except Exception as e:
        print(f"\n\nError: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
