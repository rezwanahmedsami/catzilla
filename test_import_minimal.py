#!/usr/bin/env python3
"""
Minimal import test for debugging segfault on macOS x86_64
"""
import sys
import os

print(f"Python version: {sys.version}")
print(f"Platform: {sys.platform}")
print(f"Architecture: {os.uname().machine}")

# Try importing at the lowest level possible
print("1. Testing basic Python imports...")
import ctypes
print("   ✓ ctypes imported")

print("2. Testing sys.path...")
print(f"   sys.path contains: {len(sys.path)} entries")

print("3. Testing if the _catzilla module exists...")
try:
    import importlib.util
    spec = importlib.util.find_spec("catzilla._catzilla")
    if spec:
        print(f"   ✓ _catzilla module found at: {spec.origin}")
    else:
        print("   ✗ _catzilla module not found")
        sys.exit(1)
except Exception as e:
    print(f"   ✗ Error finding _catzilla: {e}")
    sys.exit(1)

print("4. Testing direct import of _catzilla...")
try:
    # This is where the segfault happens
    import catzilla._catzilla as _catzilla
    print("   ✓ _catzilla imported successfully!")
    print(f"   Module: {_catzilla}")
    print(f"   Version: {getattr(_catzilla, 'VERSION', 'unknown')}")
except Exception as e:
    print(f"   ✗ Error importing _catzilla: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("5. Testing Server class access...")
try:
    Server = _catzilla.Server
    print(f"   ✓ Server class found: {Server}")
except Exception as e:
    print(f"   ✗ Error accessing Server class: {e}")
    sys.exit(1)

print("6. All imports successful!")
