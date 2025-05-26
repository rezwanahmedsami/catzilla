#!/usr/bin/env python3
"""
Debug script to isolate the import crash on macOS x86_64
"""

import sys
import traceback

def test_step(step_name, test_func):
    """Run a test step and report the result"""
    print(f"🔍 {step_name}...")
    try:
        test_func()
        print(f"✅ {step_name} successful")
        return True
    except Exception as e:
        print(f"❌ {step_name} failed: {e}")
        traceback.print_exc()
        return False

def test_basic_imports():
    """Test basic Python imports"""
    import os
    import sys
    import typing

def test_catzilla_module_discovery():
    """Test if catzilla module can be found"""
    import importlib.util
    spec = importlib.util.find_spec("catzilla")
    if spec is None:
        raise ImportError("catzilla module not found")
    print(f"   Module path: {spec.origin}")

def test_c_extension_file():
    """Test if the C extension file exists and is readable"""
    import importlib.util
    import os

    # Find the catzilla module
    spec = importlib.util.find_spec("catzilla")
    if spec is None:
        raise ImportError("catzilla module not found")

    # Look for the C extension
    module_dir = os.path.dirname(spec.origin)
    c_extension_candidates = [
        "_catzilla.cpython-310-darwin.so",
        "_catzilla.so",
        "_catzilla.dylib"
    ]

    for candidate in c_extension_candidates:
        c_ext_path = os.path.join(module_dir, candidate)
        if os.path.exists(c_ext_path):
            print(f"   Found C extension: {c_ext_path}")
            print(f"   File size: {os.path.getsize(c_ext_path)} bytes")
            break
    else:
        raise FileNotFoundError("C extension file not found")

def test_c_extension_import():
    """Test importing the C extension directly"""
    from catzilla import _catzilla

def test_catzilla_types_import():
    """Test importing catzilla.types module"""
    from catzilla import types

def test_catzilla_basic_import():
    """Test basic catzilla import"""
    import catzilla

def main():
    """Run all debug tests"""
    print("🐱 Catzilla Import Debug Tool")
    print("=" * 50)

    # Show Python and system info
    print(f"Python version: {sys.version}")
    print(f"Platform: {sys.platform}")
    print(f"Architecture: {sys.maxsize > 2**32 and '64-bit' or '32-bit'}")
    print()

    tests = [
        ("Basic Python imports", test_basic_imports),
        ("Catzilla module discovery", test_catzilla_module_discovery),
        ("C extension file check", test_c_extension_file),
        ("Catzilla types import", test_catzilla_types_import),
        ("C extension direct import", test_c_extension_import),
        ("Catzilla basic import", test_catzilla_basic_import),
    ]

    for step_name, test_func in tests:
        success = test_step(step_name, test_func)
        if not success:
            print(f"\n💥 Import failed at: {step_name}")
            print("This helps identify the root cause of the segmentation fault.")
            return 1

    print("\n🎉 All import tests passed!")
    return 0

if __name__ == "__main__":
    sys.exit(main())
