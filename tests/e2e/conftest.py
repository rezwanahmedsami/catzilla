#!/usr/bin/env python3
"""
Shared fixtures for E2E tests
"""
import pytest
import pytest_asyncio
from pathlib import Path
import sys

# Add test utils to path
test_dir = Path(__file__).parent
sys.path.insert(0, str(test_dir))

from utils.server_manager import get_server_manager

# Background Tasks Server Configuration
BACKGROUND_TASKS_SERVER_PORT = 8106
BACKGROUND_TASKS_SERVER_HOST = "127.0.0.1"

@pytest_asyncio.fixture(scope="module")
async def background_tasks_server():
    """Start and manage background tasks E2E test server"""
    server_manager = get_server_manager()

    # Start the background tasks server
    success = await server_manager.start_server("background_tasks", BACKGROUND_TASKS_SERVER_PORT, BACKGROUND_TASKS_SERVER_HOST)
    if not success:
        pytest.fail("Failed to start background tasks test server")

    yield server_manager.get_server_url("background_tasks")

    # Cleanup
    await server_manager.stop_server("background_tasks")
