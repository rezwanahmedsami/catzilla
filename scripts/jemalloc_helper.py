#!/usr/bin/env python3
"""
Catzilla Jemalloc Helper Script

This script helps detect and configure jemalloc preloading for your environment.
It can be used to launch Python applications with the correct jemalloc preloading settings.

Usage:
  ./jemalloc_helper.py [--detect] [--launch SCRIPT]

Examples:
  # Detect jemalloc and print configuration
  ./jemalloc_helper.py --detect

  # Launch a script with proper jemalloc preloading
  ./jemalloc_helper.py --launch my_catzilla_app.py
"""

import argparse
import os
import platform
import subprocess
import sys
from pathlib import Path
from typing import Optional, List, Tuple

# Import platform compatibility utilities
try:
    from platform_compat import safe_print, is_windows
except ImportError:
    # Define a simple fallback if module isn't available
    def is_windows():
        return platform.system() == "Windows"

    def safe_print(text):
        """Print text safely on any platform."""
        if is_windows():
            # Remove or replace emoji in Windows
            emoji_map = {
                "🚀": ">>", "⚠️": "!!", "✅": "OK", "❌": "XX",
                "🔍": ">>", "🧪": "[]", "🐛": "##"
            }
            for emoji, alt in emoji_map.items():
                text = text.replace(emoji, alt)

        try:
            print(text)
        except UnicodeEncodeError:
            # Fallback for severe encoding issues
            print(text.encode('ascii', 'replace').decode())


def find_jemalloc_library() -> Optional[str]:
    """Find jemalloc library path for the current platform."""
    system = platform.system()

    if system == "Linux":
        # Common locations for jemalloc on Linux
        possible_paths = [
            "/lib/x86_64-linux-gnu/libjemalloc.so.2",  # Ubuntu/Debian
            "/usr/lib64/libjemalloc.so.2",            # RHEL/CentOS/Fedora
            "/usr/lib/x86_64-linux-gnu/libjemalloc.so.2",  # Some Debian-based
            "/usr/local/lib/libjemalloc.so.2",        # Custom installations
        ]

        for path in possible_paths:
            if os.path.exists(path):
                return path

    elif system == "Darwin":  # macOS
        # Check for Intel and Apple Silicon paths
        possible_paths = [
            "/usr/local/lib/libjemalloc.dylib",      # Intel Mac (Homebrew)
            "/opt/homebrew/lib/libjemalloc.dylib",   # Apple Silicon (Homebrew)
        ]

        for path in possible_paths:
            if os.path.exists(path):
                return path

    return None


def platform_emoji(emoji, alt_text):
    """Return emoji character or text alternative based on platform support."""
    return alt_text if is_windows() else emoji


def setup_environment(jemalloc_path: str) -> None:
    """Set up the environment variables for jemalloc preloading."""
    system = platform.system()

    if system == "Linux":
        os.environ["LD_PRELOAD"] = f"{jemalloc_path}:{os.environ.get('LD_PRELOAD', '')}"
        safe_print(f"{platform_emoji('✅', '+')} Configured LD_PRELOAD={jemalloc_path}")

    elif system == "Darwin":  # macOS
        os.environ["DYLD_INSERT_LIBRARIES"] = f"{jemalloc_path}:{os.environ.get('DYLD_INSERT_LIBRARIES', '')}"
        safe_print(f"{platform_emoji('✅', '+')} Configured DYLD_INSERT_LIBRARIES={jemalloc_path}")


def detect_jemalloc() -> bool:
    """Detect jemalloc and print configuration information."""
    safe_print(f"{platform_emoji('🔍', '*')} Detecting jemalloc...")
    jemalloc_path = find_jemalloc_library()

    if jemalloc_path:
        safe_print(f"{platform_emoji('✅', '+')} Found jemalloc at: {jemalloc_path}")
        system = platform.system()

        safe_print(f"\n{platform_emoji('📋', '#')} Configuration Instructions:")
        if system == "Linux":
            safe_print(f"  export LD_PRELOAD={jemalloc_path}:$LD_PRELOAD")
        elif system == "Darwin":  # macOS
            safe_print(f"  export DYLD_INSERT_LIBRARIES={jemalloc_path}:$DYLD_INSERT_LIBRARIES")

        return True
    else:
        safe_print(f"{platform_emoji('❌', 'x')} Jemalloc not found on this system")
        safe_print(f"\n{platform_emoji('📋', '#')} Installation Instructions:")

        system = platform.system()
        if system == "Linux":
            safe_print("  # Ubuntu/Debian:")
            safe_print("  sudo apt-get update && sudo apt-get install -y libjemalloc-dev libjemalloc2")
            safe_print("\n  # RHEL/CentOS/Fedora:")
            safe_print("  sudo yum install -y jemalloc-devel")
        elif system == "Darwin":  # macOS
            safe_print("  # Using Homebrew:")
            safe_print("  brew install jemalloc")

        return False


def launch_script(script_path: str, script_args: List[str]) -> int:
    """Launch a Python script with jemalloc preloaded."""
    jemalloc_path = find_jemalloc_library()

    if not jemalloc_path:
        safe_print(f"{platform_emoji('❌', 'x')} Jemalloc library not found. Cannot preload.")
        return 1

    setup_environment(jemalloc_path)

    safe_print(f"{platform_emoji('🚀', '>>')} Launching: {script_path} with jemalloc preloaded")

    # Execute the script as a Python module
    cmd = [sys.executable, script_path] + script_args
    return subprocess.call(cmd)


def main():
    parser = argparse.ArgumentParser(description="Catzilla Jemalloc Helper")
    parser.add_argument("--detect", action="store_true", help="Detect jemalloc and print configuration")
    parser.add_argument("--launch", metavar="SCRIPT", help="Launch a Python script with jemalloc preloaded")
    parser.add_argument("script_args", nargs=argparse.REMAINDER, help="Arguments to pass to the script")

    args = parser.parse_args()

    if args.detect:
        detect_jemalloc()
        return 0

    if args.launch:
        script_path = args.launch
        return launch_script(script_path, args.script_args)

    # If no arguments provided, just detect jemalloc
    detect_jemalloc()
    return 0


if __name__ == "__main__":
    sys.exit(main())
