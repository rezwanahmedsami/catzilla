"""
Shared pytest configuration and fixtures for Catzilla tests

This module provides common fixtures and configuration that can be used
across all test files, particularly for async test support and event loop management.

Designed for compatibility with:
- pytest-asyncio plugin
- pytest-xdist parallel execution
- Python 3.9+ asyncio strictness
- Multiple Catzilla instances in tests
"""

import pytest
import asyncio
import warnings
import sys
import threading
from typing import Generator


@pytest.fixture(scope="function")
def event_loop():
    """
    Create an event loop for each test with pytest-asyncio compatibility.

    This fixture is compatible with pytest-asyncio plugin and handles:
    - Python 3.9+ asyncio strictness
    - pytest-xdist worker thread isolation
    - Proper cleanup between tests
    - Mixed sync/async test scenarios
    """
    # Use pytest-asyncio's recommended approach for custom event loop fixtures
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()

    # Set the loop for the current thread
    asyncio.set_event_loop(loop)

    try:
        yield loop
    finally:
        # Clean up pending tasks
        try:
            pending = asyncio.all_tasks(loop)
            for task in pending:
                if not task.done():
                    task.cancel()

            # Wait for cancellation with timeout
            if pending:
                try:
                    loop.run_until_complete(
                        asyncio.wait_for(
                            asyncio.gather(*pending, return_exceptions=True),
                            timeout=1.0
                        )
                    )
                except (asyncio.TimeoutError, Exception):
                    pass  # Ignore cleanup timeout/errors
        except Exception:
            pass  # Ignore any cleanup errors
        finally:
            # Close the loop
            try:
                if not loop.is_closed():
                    loop.close()
            except Exception:
                pass

            # Clear event loop for next test
            try:
                asyncio.set_event_loop(None)
            except Exception:
                pass


# Global memory system initialization tracking
_memory_system_initialized = False


@pytest.fixture(scope="function")
def catzilla_app():
    """
    Create a fresh Catzilla app instance for testing.

    This fixture provides a clean app instance with test-friendly configuration
    and prevents multiple memory system initialization issues.

    Returns:
        Catzilla: A configured Catzilla app instance
    """
    global _memory_system_initialized

    from catzilla import Catzilla

    # Prevent multiple memory system initialization in same process
    use_jemalloc = not _memory_system_initialized
    if not _memory_system_initialized:
        _memory_system_initialized = True

    # Create app with test-friendly settings
    app = Catzilla(
        auto_validation=True,
        memory_profiling=False,
        production=True,  # Suppress debug messages in tests
        show_banner=False,
        log_requests=False,
        enable_colors=False,
        use_jemalloc=use_jemalloc  # Only first instance uses jemalloc
    )

    return app


@pytest.fixture(scope="function", autouse=True)
def ensure_clean_asyncio_state():
    """
    Ensure clean asyncio state before and after each test.

    This fixture works alongside pytest-asyncio to ensure proper cleanup
    and is compatible with pytest-xdist worker threads.
    """
    # Before test: minimal setup
    pass

    yield

    # After test: clean up any remaining asyncio state
    try:
        # Only clean up if we're in the main thread or have an event loop
        if threading.current_thread() == threading.main_thread():
            try:
                loop = asyncio.get_event_loop()
                if loop and not loop.is_closed():
                    # Cancel remaining tasks quickly
                    pending = asyncio.all_tasks(loop)
                    for task in pending:
                        if not task.done():
                            task.cancel()
            except RuntimeError:
                pass  # No loop, which is fine
    except Exception:
        pass  # Ignore all cleanup errors
