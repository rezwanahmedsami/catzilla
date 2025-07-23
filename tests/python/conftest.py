"""
Shared pytest configuration and fixtures for Catzilla tests

This module provides common fixtures and configuration that can be used
across all test files, particularly for async test support and event loop management.
"""

import pytest
import asyncio
import warnings
from typing import Generator


@pytest.fixture(scope="function")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """
    Create a fresh event loop for each test function.

    This fixture ensures that async tests have a clean event loop
    and properly handles event loop cleanup to prevent issues in CI environments.
    """
    # Create a new event loop
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    try:
        yield loop
    finally:
        # Clean up any remaining tasks
        try:
            # Get all pending tasks
            pending = asyncio.all_tasks(loop)

            # Cancel all pending tasks
            for task in pending:
                task.cancel()

            # Wait for cancellation to complete
            if pending:
                loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
        except Exception:
            # Ignore cleanup errors
            pass
        finally:
            # Close the event loop
            try:
                loop.close()
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
