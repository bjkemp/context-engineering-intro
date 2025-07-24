#!/usr/bin/env python3
"""
Entry point script for the Adventure Generation Agent.

This script provides a simple way to run the CLI without installing the package.
"""

import sys
import os

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from adventure_agent.cli import main

if __name__ == "__main__":
    main()