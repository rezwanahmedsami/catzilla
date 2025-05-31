#!/usr/bin/env python3
"""
Verify the fixes for segmentation faults in CI environments.

This script runs the tests that previously caused segmentation faults
to ensure our fixes have resolved the issues.
"""

import os
import subprocess
import sys
import platform

def print_header(text):
    """Print a section header."""
    print("\n" + "=" * 60)
    print(text)
    print("=" * 60)

def detect_jemalloc_preloading():
    """Detect if jemalloc is properly preloaded."""
    system = platform.system()

    if system == "Linux":
        return "libjemalloc.so" in os.environ.get("LD_PRELOAD", "")
    elif system == "Darwin":  # macOS
        return "libjemalloc.dylib" in os.environ.get("DYLD_INSERT_LIBRARIES", "")
    return False

def run_test(test_path):
    """Run a specific test and return the result."""
    cmd = [sys.executable, "-m", "pytest", test_path, "-v"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.returncode == 0, result.stdout, result.stderr

def main():
    """Verify the fixes for segmentation faults in CI environments."""
    print_header("🚀 Catzilla Segmentation Fault Fix Verification")

    # Check for proper jemalloc preloading
    if not detect_jemalloc_preloading():
        print("⚠️  WARNING: Jemalloc is not properly preloaded!")
        print("The tests may still fail with segmentation faults.")
        print("See docs/jemalloc_troubleshooting.md for proper configuration.")

        # Try to find and use the helper script
        helper_script = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "scripts",
            "jemalloc_helper.py"
        )

        if os.path.exists(helper_script):
            print("\n🔧 Running jemalloc helper to configure environment...")
            subprocess.run([sys.executable, helper_script, "--detect"])
    else:
        print("✅ Jemalloc preloading detected!")

    print_header("🧪 Running Previously Failing Tests")

    tests = [
        "tests/python/test_validation_performance.py::TestPerformanceBenchmarks::test_memory_usage_during_validation",
        "tests/python/test_http_responses.py::TestComplexRoutingScenarios::test_special_characters_in_params",
        "tests/python/test_http_responses.py::TestComplexRoutingScenarios::test_nested_resource_routing"
    ]

    all_passed = True

    for test in tests:
        print(f"\n📋 Running test: {test}")
        passed, stdout, stderr = run_test(test)

        if passed:
            print(f"✅ PASSED: {test}")
        else:
            print(f"❌ FAILED: {test}")
            print("\nStdout:")
            print(stdout)
            print("\nStderr:")
            print(stderr)
            all_passed = False

    print_header("📊 Results Summary")

    if all_passed:
        print("✅ All tests passed! The segmentation fault issues have been fixed.")
    else:
        print("❌ Some tests failed. The fixes may need additional work.")

    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())
