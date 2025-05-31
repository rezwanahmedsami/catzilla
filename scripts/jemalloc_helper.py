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


def setup_environment(jemalloc_path: str) -> None:
    """Set up the environment variables for jemalloc preloading."""
    system = platform.system()

    if system == "Linux":
        os.environ["LD_PRELOAD"] = f"{jemalloc_path}:{os.environ.get('LD_PRELOAD', '')}"
        print(f"✅ Configured LD_PRELOAD={jemalloc_path}")

    elif system == "Darwin":  # macOS
        os.environ["DYLD_INSERT_LIBRARIES"] = f"{jemalloc_path}:{os.environ.get('DYLD_INSERT_LIBRARIES', '')}"
        print(f"✅ Configured DYLD_INSERT_LIBRARIES={jemalloc_path}")


def detect_jemalloc() -> bool:
    """Detect jemalloc and print configuration information."""
    print("🔍 Detecting jemalloc...")
    jemalloc_path = find_jemalloc_library()

    if jemalloc_path:
        print(f"✅ Found jemalloc at: {jemalloc_path}")
        system = platform.system()

        print("\n📋 Configuration Instructions:")
        if system == "Linux":
            print(f"  export LD_PRELOAD={jemalloc_path}:$LD_PRELOAD")
        elif system == "Darwin":  # macOS
            print(f"  export DYLD_INSERT_LIBRARIES={jemalloc_path}:$DYLD_INSERT_LIBRARIES")

        return True
    else:
        print("❌ Jemalloc not found on this system")
        print("\n📋 Installation Instructions:")

        system = platform.system()
        if system == "Linux":
            print("  # Ubuntu/Debian:")
            print("  sudo apt-get update && sudo apt-get install -y libjemalloc-dev libjemalloc2")
            print("\n  # RHEL/CentOS/Fedora:")
            print("  sudo yum install -y jemalloc-devel")
        elif system == "Darwin":  # macOS
            print("  # Using Homebrew:")
            print("  brew install jemalloc")

        return False


def launch_script(script_path: str, script_args: List[str]) -> int:
    """Launch a Python script with jemalloc preloaded."""
    jemalloc_path = find_jemalloc_library()

    if not jemalloc_path:
        print("❌ Jemalloc library not found. Cannot preload.")
        return 1

    setup_environment(jemalloc_path)

    print(f"🚀 Launching: {script_path} with jemalloc preloaded")

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
