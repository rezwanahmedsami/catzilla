#!/usr/bin/env python3
"""
Test script to verify psutil integration in Catzilla banner system.
"""

import sys
import os

# Add the python directory to the path so we can import catzilla
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'python'))

from catzilla.ui.collectors import SystemInfoCollector, ServerInfoCollector
from catzilla.ui.banner import BannerRenderer

def test_psutil_integration():
    """Test that psutil is properly integrated"""
    print("=== Testing psutil integration ===\n")

    # Test SystemInfoCollector methods
    collector = SystemInfoCollector()

    print(f"Memory usage: {collector.get_memory_usage()}")
    print(f"CPU usage: {collector.get_cpu_usage()}%")
    print(f"Worker count: {collector.get_worker_count()}")
    print(f"Python version: {collector.get_python_version()}")
    print(f"Platform: {collector.get_platform_info()}")
    print(f"Jemalloc available: {collector.check_jemalloc()}")

    # Test if psutil is available
    try:
        import psutil
        print(f"\npsutil version: {psutil.__version__}")
        print(f"psutil available: True")

        # Test some psutil functionality directly
        process = psutil.Process()
        print(f"Process PID: {process.pid}")
        print(f"Process memory: {process.memory_info().rss / 1024 / 1024:.1f} MB")
        print(f"CPU count: {psutil.cpu_count()}")

    except ImportError:
        print("psutil not available!")
        return False

    print("\n=== psutil integration test passed! ===")
    return True

if __name__ == "__main__":
    success = test_psutil_integration()
    if not success:
        sys.exit(1)
