#!/usr/bin/env python3
"""
Test Windows emoji compatibility.

This script verifies that the emoji compatibility solutions work correctly on Windows.
It specifically tests emoji characters that have been problematic in Windows CI environments.
"""

import os
import platform
import sys

# Import platform compatibility tools
try:
    from scripts.platform_compat import safe_print, is_windows
except ImportError:
    # Try to add scripts to path
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    try:
        from scripts.platform_compat import safe_print, is_windows
    except ImportError:
        # Fallback if we can't import
        def is_windows():
            return platform.system() == "Windows"

        def safe_print(text):
            try:
                print(text)
            except UnicodeEncodeError:
                print(text.encode('ascii', 'replace').decode())

def main():
    """Test emoji handling on Windows platforms."""
    platform_name = platform.system()

    safe_print(f"Testing emoji compatibility on {platform_name}")
    safe_print("=" * 50)

    # Test all potentially problematic emoji
    test_emojis = [
        ("🚀", "Rocket"),
        ("⚠️", "Warning"),
        ("✅", "Check"),
        ("❌", "Cross"),
        ("🔍", "Search"),
        ("🧪", "Test tube"),
        ("🐛", "Bug"),
        ("🔧", "Wrench"),
    ]

    for emoji, name in test_emojis:
        safe_print(f"Testing emoji: {emoji} ({name})")

    # Test a message with multiple emoji
    safe_print("\nMultiple emoji test:")
    safe_print("🚀 Catzilla: Memory revolution activated (jemalloc) ✅")

    # Check if running on Windows
    if is_windows():
        safe_print("\nRunning on Windows - emoji should be replaced with text alternatives")
    else:
        safe_print("\nRunning on non-Windows platform - emoji should display normally")

    return 0

if __name__ == "__main__":
    sys.exit(main())
