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

    Yields:
        asyncio.AbstractEventLoop: A fresh event loop for the test
    """
    # Suppress DeprecationWarnings about get_event_loop in newer Python versions
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", DeprecationWarning)

        policy = asyncio.get_event_loop_policy()
        loop = policy.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            yield loop
        finally:
            # Clean up any remaining tasks
            try:
                tasks = [task for task in asyncio.all_tasks(loop) if not task.done()]
                for task in tasks:
                    task.cancel()
                if tasks:
                    # Wait briefly for cancellation to complete
                    loop.run_until_complete(
                        asyncio.gather(*tasks, return_exceptions=True)
                    )
            except Exception:
                # Ignore cleanup errors - we're already shutting down
                pass
            finally:
                try:
                    # Close the event loop
                    if not loop.is_closed():
                        loop.close()
                except Exception:
                    # Ignore close errors
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


# Configure asyncio mode for all tests
pytestmark = pytest.mark.asyncio


def pytest_configure(config):
    """Configure pytest with custom markers and settings."""
    config.addinivalue_line(
        "markers",
        "asyncio: Mark test as an async test that requires event loop"
    )
    config.addinivalue_line(
        "markers",
        "slow: Mark test as slow (may be skipped in fast test runs)"
    )
    config.addinivalue_line(
        "markers",
        "integration: Mark test as integration test"
    )


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add asyncio marker to async tests."""
    for item in items:
        if asyncio.iscoroutinefunction(item.function):
            item.add_marker(pytest.mark.asyncio)
