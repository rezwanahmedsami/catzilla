#!/usr/bin/env python3
"""
Test script to verify the event loop fix works with pytest-xdist.

This script simulates the exact conditions that cause the
"RuntimeError: There is no current event loop in thread 'MainThread'"
error in Ubuntu Python 3.8 CI environment.
"""

import pytest
import asyncio
import threading
import sys
import os

# Add the tests directory to path to import conftest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'tests', 'python'))

def test_sync_test():
    """Sync test should work fine"""
    assert True

@pytest.mark.asyncio
async def test_async_basic():
    """Basic async test"""
    await asyncio.sleep(0.001)
    assert True

@pytest.mark.asyncio
async def test_async_with_tasks():
    """Async test with task creation"""

    async def dummy_coroutine():
        await asyncio.sleep(0.001)
        return "success"

    # Create some tasks
    tasks = [asyncio.create_task(dummy_coroutine()) for _ in range(3)]
    results = await asyncio.gather(*tasks)

    assert all(r == "success" for r in results)

def test_mixed_scenario():
    """Sync test that checks event loop availability"""
    # This should not fail with our fix
    try:
        loop = asyncio.get_event_loop()
        assert loop is not None
        print(f"✅ Event loop available in sync test: {loop}")
    except RuntimeError as e:
        pytest.fail(f"Event loop not available in sync test: {e}")

class TestAsyncClass:
    """Test class with async methods"""

    @pytest.mark.asyncio
    async def test_class_async_method(self):
        """Async method in test class"""
        await asyncio.sleep(0.001)
        assert True

    def test_class_sync_method(self):
        """Sync method in test class"""
        assert True

if __name__ == "__main__":
    print("Testing event loop fix...")
    print(f"Python version: {sys.version}")
    print(f"Thread: {threading.current_thread().name}")
    print(f"Thread ID: {threading.get_ident()}")

    # Run with pytest-xdist to simulate CI environment
    exit_code = pytest.main([
        __file__,
        "-v",
        "-n", "2",  # Use 2 workers like CI
        "--dist", "worksteal",
        "--tb=short"
    ])

    if exit_code == 0:
        print("🎉 ALL TESTS PASSED - Event loop fix working!")
    else:
        print("❌ Tests failed - fix needs more work")

    sys.exit(exit_code)
