#!/usr/bin/env python3
"""
Test script to verify that the jemalloc CI fix works properly.
This simulates the conditions that caused the CI failure on macOS.
"""

import os
import subprocess
import sys
from pathlib import Path

def run_command(cmd, capture_output=True):
    """Run a command and return the result."""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=capture_output, text=True)
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        return False, "", str(e)

def test_jemalloc_detection():
    """Test that jemalloc can be detected properly."""
    print("🔍 Testing jemalloc detection...")

    # Test pkg-config detection
    success, stdout, stderr = run_command("pkg-config --exists jemalloc")
    if success:
        print("✅ jemalloc found via pkg-config")

        # Get jemalloc info
        success, stdout, stderr = run_command("pkg-config --cflags --libs jemalloc")
        if success:
            print(f"📋 jemalloc flags: {stdout.strip()}")
        else:
            print(f"❌ Failed to get jemalloc flags: {stderr}")
    else:
        print("❌ jemalloc not found via pkg-config")

    # Test manual library detection
    potential_paths = [
        "/opt/homebrew/lib/libjemalloc.dylib",  # ARM64 macOS
        "/usr/local/lib/libjemalloc.dylib",     # Intel macOS
        "/usr/lib/x86_64-linux-gnu/libjemalloc.so",  # Ubuntu
    ]

    print("\n🔍 Testing manual library detection...")
    found_libs = []
    for path in potential_paths:
        if os.path.exists(path):
            found_libs.append(path)
            print(f"✅ Found: {path}")

    if not found_libs:
        print("❌ No jemalloc libraries found in standard locations")

    return len(found_libs) > 0

def test_cmake_configuration():
    """Test that CMake can properly configure with jemalloc."""
    print("\n🔍 Testing CMake jemalloc configuration...")

    # Create a temporary build directory for testing
    test_build_dir = Path("test_build_jemalloc")
    test_build_dir.mkdir(exist_ok=True)

    try:
        # Run CMake configuration
        cmd = f"cd {test_build_dir} && cmake .. -DUSE_JEMALLOC=ON"
        success, stdout, stderr = run_command(cmd)

        if success:
            print("✅ CMake configuration succeeded")

            # Check if jemalloc was found
            if "✅ jemalloc found:" in stdout:
                print("✅ jemalloc was properly detected by CMake")
                return True
            else:
                print("❌ jemalloc was not detected by CMake")
                print(f"CMake output: {stdout}")
                return False
        else:
            print(f"❌ CMake configuration failed: {stderr}")
            return False

    finally:
        # Clean up test build directory
        import shutil
        if test_build_dir.exists():
            shutil.rmtree(test_build_dir)

def test_build_without_global_linking():
    """Test that the build works without global jemalloc linking."""
    print("\n🔍 Testing build without global jemalloc linking...")

    # Clean any existing build
    success, _, _ = run_command("rm -rf build")

    # Run the build script
    success, stdout, stderr = run_command("./scripts/build.sh")

    if success:
        print("✅ Build completed successfully")

        # Check that expected outputs exist
        expected_files = [
            "build/_catzilla.so",
            "build/libcatzilla_core.a",
            "build/test_router",
            "build/test_memory"
        ]

        all_files_exist = True
        for file_path in expected_files:
            if os.path.exists(file_path):
                print(f"✅ Generated: {file_path}")
            else:
                print(f"❌ Missing: {file_path}")
                all_files_exist = False

        return all_files_exist
    else:
        print(f"❌ Build failed: {stderr}")
        return False

def main():
    """Run all tests."""
    print("🧪 Testing Catzilla jemalloc CI fix...")
    print("=" * 50)

    tests = [
        ("Jemalloc Detection", test_jemalloc_detection),
        ("CMake Configuration", test_cmake_configuration),
        ("Build Without Global Linking", test_build_without_global_linking),
    ]

    results = []
    for test_name, test_func in tests:
        print(f"\n📝 Running: {test_name}")
        print("-" * 30)
        try:
            result = test_func()
            results.append((test_name, result))
            status = "✅ PASSED" if result else "❌ FAILED"
            print(f"\n{status}: {test_name}")
        except Exception as e:
            print(f"\n💥 ERROR in {test_name}: {e}")
            results.append((test_name, False))

    print("\n" + "=" * 50)
    print("📊 Test Results Summary:")
    print("=" * 50)

    passed = 0
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{status}: {test_name}")
        if result:
            passed += 1

    print(f"\n🎯 Overall: {passed}/{len(results)} tests passed")

    if passed == len(results):
        print("🎉 All tests passed! The jemalloc CI fix should work.")
        return True
    else:
        print("⚠️  Some tests failed. The CI may still have issues.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
