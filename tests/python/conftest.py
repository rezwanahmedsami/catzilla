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
    """Ensure there's always an event loop available for both sync and async tests"""
    import asyncio

    # Check if we need to create an event loop
    try:
        loop = asyncio.get_event_loop()
        if loop.is_closed():
            raise RuntimeError("Loop is closed")
    except RuntimeError:
        # No loop or closed loop, create a new one
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    yield

    # No cleanup here, let the event_loop fixture handle it


@pytest.fixture(scope="function")
def event_loop():
    """Create an event loop for each test, with Python 3.13 compatibility and mixed test support"""
    import sys

    # Enhanced cleanup for any existing event loop state
    if sys.version_info >= (3, 13):
        # Python 3.13+ requires more explicit event loop management
        try:
            existing_loop = asyncio.get_running_loop()
            if existing_loop and not existing_loop.is_closed():
                existing_loop.close()
        except RuntimeError:
            pass  # No running loop, which is fine

        # Clear any existing event loop policy
        try:
            asyncio.set_event_loop(None)
        except RuntimeError:
            pass

    # More aggressive cleanup for mixed sync/async test scenarios
    try:
        # Try to get any existing loop and close it properly
        try:
            existing_loop = asyncio.get_event_loop()
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
            pass  # No existing loop, which is expected in mixed scenarios

        # Clear the event loop reference completely
        asyncio.set_event_loop(None)
    except Exception:
        pass  # Ignore any cleanup errors

    # Create a new event loop with explicit policy
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)


@pytest.fixture(scope="function")
def catzilla_app():
    """
    Create a fresh Catzilla app instance for testing.

    This fixture provides a clean app instance with test-friendly configuration.

    Returns:
        Catzilla: A configured Catzilla app instance
    """
    from catzilla import Catzilla

    # Create app with test-friendly settings
    app = Catzilla(
        auto_validation=True,
        memory_profiling=False,
        production=False,
        show_banner=False,
        log_requests=False,
        enable_colors=False
    )

    return app
