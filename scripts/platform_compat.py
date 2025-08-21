#!/usr/bin/env python3
"""
Platform compatibility utilities for Catzilla project.
Ensures cross-platform compatibility for output formatting.
"""

import os
import platform
import sys
from typing import Dict

# Define emoji and their plain text alternatives
EMOJI_MAP: Dict[str, str] = {
    "🚀": ">>",  # Rocket
    "⚠️": "!!",  # Warning
    "✅": "OK",  # Checkmark
    "❌": "XX",  # Cross mark
    "🔍": ">>",  # Magnifying glass
    "🧪": "[]",  # Test tube
    "🐛": "##",  # Bug
    "🔧": "++",  # Wrench
    "🔥": "!!", # Fire
    "💡": "**", # Light bulb
}

def is_windows() -> bool:
    """Check if running on Windows"""
    return platform.system() == "Windows"

def is_windows_ci() -> bool:
    """Check if running on Windows CI environment"""
    # Common environment variables in CI systems that indicate Windows
    if is_windows():
        return any(env in os.environ for env in ["CI", "GITHUB_ACTIONS", "APPVEYOR", "TF_BUILD"])
    return False

def safe_print(text: str) -> None:
    """Print text, replacing emojis with alternative text on Windows"""
    if is_windows():
        for emoji, alt in EMOJI_MAP.items():
            text = text.replace(emoji, alt)

    try:
        print(text)
    except UnicodeEncodeError:
        # Fallback for severe encoding issues - strip all non-ASCII
        print(text.encode('ascii', 'replace').decode())

if __name__ == "__main__":
    # Test the function
    safe_print("🚀 Test message with emoji")
    safe_print("Normal text")
