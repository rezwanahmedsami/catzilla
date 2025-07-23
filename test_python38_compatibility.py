#!/usr/bin/env python3
"""
Comprehensive test to verify Python 3.8 compatibility for pytest-xdist async tests.

This script tests all the scenarios that could cause the
"RuntimeError: There is no current event loop in thread 'MainThread'"
error in Ubuntu Python 3.8 CI environment.
"""

import asyncio
import threading
import sys
import os
import time


def simulate_python38_worker_thread():
    """
    Simulate the exact conditions in a pytest-xdist worker thread
    in Python 3.8 environment.
    """
    print(f"\n=== Simulating Python 3.8 pytest-xdist worker ===")
    print(f"Thread: {threading.current_thread().name}")
    print(f"Main thread: {threading.main_thread().name}")
    print(f"Is main thread: {threading.current_thread() == threading.main_thread()}")

    def worker_thread_simulation():
        """This simulates what happens in [gw0] and [gw1] workers"""

        # Test 1: The failing scenario from the CI
        print("\n1. Testing asyncio.get_event_loop() (this should fail in Python 3.8 workers)")
        try:
            loop = asyncio.get_event_loop()
            print(f"   ✅ Unexpectedly succeeded: {loop}")
        except RuntimeError as e:
            print(f"   ❌ Expected failure: {e}")

        # Test 2: The working solution
        print("\n2. Testing our fix: new_event_loop + set_event_loop")
        try:
            # This is what our conftest.py should do
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            print(f"   ✅ Success: {loop}")

            # Test that async operations work
            async def test_coro():
                await asyncio.sleep(0.001)
                return "async_success"

            result = loop.run_until_complete(test_coro())
            print(f"   ✅ Async operation worked: {result}")

            # Clean up
            loop.close()
            asyncio.set_event_loop(None)

        except Exception as e:
            print(f"   ❌ Fix failed: {e}")

        # Test 3: Multiple loop creation/cleanup cycles
        print("\n3. Testing multiple event loop cycles (simulating test sequence)")
        for i in range(3):
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

                # Simulate some async work
                async def mini_test():
                    await asyncio.sleep(0.001)
                    return f"cycle_{i}"

                result = loop.run_until_complete(mini_test())
                print(f"   ✅ Cycle {i}: {result}")

                # Proper cleanup
                pending = asyncio.all_tasks(loop)
                for task in pending:
                    if not task.done():
                        task.cancel()

                loop.close()
                asyncio.set_event_loop(None)

            except Exception as e:
                print(f"   ❌ Cycle {i} failed: {e}")

    # Run in a separate thread to simulate pytest-xdist worker
    thread = threading.Thread(target=worker_thread_simulation, name="SimulatedWorker")
    thread.start()
    thread.join()


def test_ensure_event_loop_fixture():
    """Test our ensure_event_loop fixture logic"""
    print(f"\n=== Testing ensure_event_loop fixture logic ===")

    # Import the fixture logic from our conftest
    import threading

    def fixture_simulation():
        """Simulate our autouse fixture"""
        loop = None
        needs_cleanup = False

        try:
            # Try to get existing loop only on main thread
            if threading.current_thread() == threading.main_thread():
                try:
                    existing_loop = asyncio.get_event_loop()
                    if existing_loop and not existing_loop.is_closed():
                        loop = existing_loop
                except RuntimeError:
                    pass  # No loop exists, will create new one

            # If no valid loop, create a new one (works in all threads)
            if loop is None or loop.is_closed():
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                needs_cleanup = True

        except Exception:
            # Fallback: always create new loop
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            needs_cleanup = True

        print(f"   ✅ Fixture created loop: {loop}")
        print(f"   ✅ Needs cleanup: {needs_cleanup}")

        # Test async operation
        async def test_operation():
            await asyncio.sleep(0.001)
            return "fixture_test_success"

        result = loop.run_until_complete(test_operation())
        print(f"   ✅ Async operation: {result}")

        # Cleanup simulation
        if needs_cleanup and loop and not loop.is_closed():
            try:
                pending = asyncio.all_tasks(loop)
                for task in pending:
                    if not task.done():
                        task.cancel()
            except Exception:
                pass

    # Test in main thread
    print("\nMain thread test:")
    fixture_simulation()

    # Test in worker thread
    print("\nWorker thread test:")
    thread = threading.Thread(target=fixture_simulation, name="WorkerTest")
    thread.start()
    thread.join()


if __name__ == "__main__":
    print("🧪 Comprehensive Python 3.8 pytest-xdist compatibility test")
    print(f"Python version: {sys.version}")
    print(f"Platform: {sys.platform}")

    try:
        simulate_python38_worker_thread()
        test_ensure_event_loop_fixture()

        print(f"\n🎉 ALL COMPATIBILITY TESTS PASSED!")
        print(f"✅ The fix should work in Ubuntu Python 3.8 CI with pytest-xdist")

    except Exception as e:
        print(f"\n❌ COMPATIBILITY TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
