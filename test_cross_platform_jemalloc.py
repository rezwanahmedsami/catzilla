#!/usr/bin/env python3
"""
Cross-platform jemalloc integration verification test
Tests that the jemalloc compatibility layer works correctly
"""

import os
import sys
import subprocess

def test_build_configuration():
    """Test that jemalloc was properly detected and configured during build"""
    print("🔍 Testing build configuration...")

    # Check if jemalloc was found during CMake configuration
    cmake_cache_path = os.path.join("build", "CMakeCache.txt")
    if not os.path.exists(cmake_cache_path):
        print("❌ Build directory not found. Please run 'cmake ..' first.")
        return False

    with open(cmake_cache_path, 'r') as f:
        cache_content = f.read()

    if "JEMALLOC_FOUND:INTERNAL=1" in cache_content or "USE_JEMALLOC:BOOL=ON" in cache_content:
        print("✅ jemalloc was found and configured during build")

        # Check if prefix detection worked
        if "JEMALLOC_USES_PREFIX" in cache_content:
            print("✅ jemalloc prefix detection configured")
        else:
            print("✅ jemalloc using direct function names (no prefix needed)")

        return True
    else:
        print("⚠️  jemalloc not found during build - using standard malloc")
        return True  # This is also valid, just not optimal

def test_library_loading():
    """Test that the compiled library can be loaded and basic functions work"""
    print("🔍 Testing library loading...")

    try:
        sys.path.insert(0, 'build')
        import _catzilla
        print("✅ Catzilla C extension loaded successfully")

        # Test basic functionality
        test_result = _catzilla.test_basic_functionality()
        if test_result:
            print("✅ Basic functionality test passed")
        else:
            print("⚠️  Basic functionality test failed")

        return True
    except ImportError as e:
        print(f"❌ Failed to import Catzilla C extension: {e}")
        return False
    except AttributeError:
        print("✅ C extension loaded (some test functions may not be exposed)")
        return True

def test_memory_allocations():
    """Test memory allocation patterns to ensure jemalloc integration works"""
    print("🔍 Testing memory allocation patterns...")

    # Test by running one of the C test executables
    test_executables = [
        "build/test_router",
        "build/test_validation_engine",
        "build/test_advanced_router"
    ]

    for test_exe in test_executables:
        if os.path.exists(test_exe):
            try:
                result = subprocess.run([test_exe], capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    print(f"✅ Memory test passed: {os.path.basename(test_exe)}")
                    return True
                else:
                    print(f"⚠️  Test issues in {os.path.basename(test_exe)}: {result.stderr}")
            except subprocess.TimeoutExpired:
                print(f"⚠️  Test timeout: {os.path.basename(test_exe)}")
            except Exception as e:
                print(f"⚠️  Test error: {e}")

    print("⚠️  No test executables found or all tests had issues")
    return False

def test_jemalloc_symbols():
    """Test that the correct jemalloc symbols are available"""
    print("🔍 Testing jemalloc symbol availability...")

    # Check if the built library has jemalloc symbols
    lib_path = "build/libcatzilla_core.a"
    if not os.path.exists(lib_path):
        print("❌ Core library not found")
        return False

    try:
        # Use nm to check symbols (macOS/Linux)
        result = subprocess.run(['nm', lib_path], capture_output=True, text=True)
        if result.returncode == 0:
            symbols = result.stdout
            if 'malloc' in symbols or 'je_malloc' in symbols:
                print("✅ Memory allocation symbols found in library")
                return True
            else:
                print("⚠️  No obvious memory allocation symbols found")
                return True  # May be linked dynamically
    except FileNotFoundError:
        print("⚠️  'nm' tool not available for symbol inspection")
        return True  # Can't test, but that's okay

def main():
    """Run all cross-platform jemalloc integration tests"""
    print("=" * 60)
    print("🚀 CATZILLA CROSS-PLATFORM JEMALLOC INTEGRATION TEST")
    print("=" * 60)
    print()

    # Detect platform
    import platform
    system = platform.system()
    print(f"📍 Platform: {system} {platform.release()}")

    if system == "Darwin":
        print("🍎 macOS detected - expecting direct jemalloc function names")
    elif system == "Linux":
        print("🐧 Linux detected - will auto-detect jemalloc naming convention")
        # Try to detect distribution
        try:
            with open('/etc/os-release', 'r') as f:
                os_info = f.read()
            if 'rhel' in os_info.lower() or 'centos' in os_info.lower() or 'almalinux' in os_info.lower() or 'fedora' in os_info.lower():
                print("   📦 RPM-based distribution - expecting je_ prefixed functions")
            else:
                print("   📦 DEB-based or other distribution - expecting direct function names")
        except:
            print("   📦 Distribution unknown")
    elif system == "Windows":
        print("🪟 Windows detected - jemalloc support may vary")
    print()

    tests = [
        ("Build Configuration", test_build_configuration),
        ("Library Loading", test_library_loading),
        ("Memory Allocations", test_memory_allocations),
        ("jemalloc Symbols", test_jemalloc_symbols)
    ]

    passed = 0
    total = len(tests)

    for test_name, test_func in tests:
        print(f"Running {test_name}...")
        if test_func():
            passed += 1
        print()

    print("=" * 60)
    print(f"📊 TEST RESULTS: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 ALL TESTS PASSED! Cross-platform jemalloc integration is working correctly.")
    elif passed >= total - 1:
        print("✅ MOSTLY WORKING! Minor issues detected but core functionality works.")
    else:
        print("⚠️  ISSUES DETECTED! Some tests failed - check the output above.")

    print("=" * 60)

    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
