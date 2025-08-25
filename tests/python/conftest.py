"""
Shared pytest configuration and fixtures for Catzilla tests

This module provides common fixtures and configuration that can be used
across all test files, particularly for async test support and event loop management.
"""

import pytest
import asyncio
import warnings
import sys
from typing import Generator


@pytest.fixture(scope="function", autouse=True)
def ensure_event_loop():
    """
    Ensure there's always an event loop available for both sync and async tests.

    This fixture is designed to work with:
    - Python 3.8+ (including Ubuntu CI Python 3.8)
    - pytest-xdist parallel execution ([gw0], [gw1] workers)
    - Both sync and async test methods

    The key insight: Never use asyncio.get_event_loop() in worker threads,
    always use asyncio.new_event_loop() + asyncio.set_event_loop()
    """
    import asyncio
    import threading
    import sys

    # Critical: Always create a new event loop for worker threads
    # This avoids the "There is no current event loop in thread 'MainThread'" error
    # that occurs in pytest-xdist workers in Python 3.8

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

    yield

    # Minimal cleanup - let event_loop fixture handle the rest
    if needs_cleanup and loop and not loop.is_closed():
        try:
            # Cancel any pending tasks quickly
            pending = asyncio.all_tasks(loop)
            for task in pending:
                if not task.done():
                    task.cancel()
        except Exception:
            pass  # Ignore cleanup errors


@pytest.fixture(scope="function")
def event_loop():
    """
    Create an event loop for each test with bulletproof compatibility.

    This fixture handles:
    - Python 3.8+ compatibility (Ubuntu CI Python 3.8)
    - pytest-xdist worker thread isolation
    - Proper cleanup between tests
    - Mixed sync/async test scenarios
    """
    import sys
    import asyncio
    import threading

    # Aggressive cleanup of any existing event loop state
    try:
        # For Python 3.13+, handle running loops differently
        if sys.version_info >= (3, 13):
            try:
                existing_loop = asyncio.get_running_loop()
                if existing_loop and not existing_loop.is_closed():
                    existing_loop.close()
            except RuntimeError:
                pass  # No running loop

        # Clean up any existing loop (safe for all Python versions)
        try:
            # Only use get_event_loop on main thread for Python 3.8 compatibility
            if threading.current_thread() == threading.main_thread():
                existing_loop = asyncio.get_event_loop()
            else:
                # In worker threads, don't use get_event_loop (fails in Python 3.8)
                existing_loop = None

            if existing_loop and not existing_loop.is_closed():
                # Cancel all tasks before closing
                pending = asyncio.all_tasks(existing_loop)
                for task in pending:
                    if not task.done():
                        task.cancel()
                if pending:
                    try:
                        existing_loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
                    except Exception:
                        pass
                existing_loop.close()
        except RuntimeError:
            pass  # No existing loop, which is expected

        # Clear the event loop reference completely
        asyncio.set_event_loop(None)
    except Exception:
        pass  # Ignore any cleanup errors

    # Create a new event loop with explicit policy
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    try:
        yield loop
    finally:
        # Comprehensive cleanup
        try:
            # Cancel all remaining tasks
            pending = asyncio.all_tasks(loop)
            for task in pending:
                if not task.done():
                    task.cancel()

            # Wait for cancellation if there are pending tasks
            if pending:
                try:
                    loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
                except Exception:
                    pass

        except Exception:
            pass
        finally:
            # Close the loop
            try:
                if not loop.is_closed():
                    loop.close()
            except Exception:
                pass

            # Clear the event loop for compatibility
            try:
                asyncio.set_event_loop(None)
            except Exception:
                pass


@pytest.fixture(scope="function")
def catzilla_app():
    """
    Create a fresh Catzilla app instance for testing.

    This fixture provides a clean app instance with test-friendly configuration.

    Returns:
        Catzilla: A configured Catzilla app instance
    """
    from catzilla import Catzilla

    # Create app with test-friendly settings - use production=True to suppress debug messages
    app = Catzilla(
        auto_validation=True,
        memory_profiling=False,
        production=True,  # Suppress debug messages in tests
        show_banner=False,
        log_requests=False,
        enable_colors=False
    )

    return app
