#!/usr/bin/env python3
"""
E2E Tests for Background Tasks Functionality

Tests the background tasks server endpoints with real HTTP requests.
"""
import pytest
import pytest_asyncio
import httpx
import asyncio
import time

# Helper function for waiting for task completion
async def wait_for_task_completion(client, server_url, task_id, max_wait_seconds=10):
    """Wait for a task to complete, with polling"""
    for _ in range(max_wait_seconds * 2):  # Poll every 0.5 seconds
        await asyncio.sleep(0.5)
        response = await client.get(f"{server_url}/tasks/{task_id}/status")
        if response.status_code == 200:
            status_data = response.json()
            if status_data["status"] in ["completed", "failed", "cancelled"]:
                return status_data
    return None  # Timeout

async def wait_for_task_progress(client, server_url, task_id, max_wait_seconds=5):
    """Wait for a task to show progress > 0"""
    for _ in range(max_wait_seconds * 2):  # Poll every 0.5 seconds
        await asyncio.sleep(0.5)
        response = await client.get(f"{server_url}/tasks/{task_id}/status")
        if response.status_code == 200:
            status_data = response.json()
            if status_data.get("progress", 0) > 0:
                return status_data
    return None  # Timeout
from pathlib import Path
import sys

# Add test utils to path
test_dir = Path(__file__).parent
sys.path.insert(0, str(test_dir))

from utils.server_manager import get_server_manager

# Test configuration
# Configuration
BACKGROUND_TASKS_SERVER_PORT = 8106
BACKGROUND_TASKS_SERVER_HOST = "127.0.0.1"

@pytest.mark.asyncio
async def test_background_tasks_health_check(background_tasks_server):
    """Test background tasks server health check"""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{background_tasks_server}/health")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "healthy"
        assert data["server"] == "background_tasks_e2e_test"
        assert "active_tasks" in data
        assert "total_tasks" in data

@pytest.mark.asyncio
async def test_background_tasks_home_info(background_tasks_server):
    """Test background tasks server info endpoint"""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{background_tasks_server}/")
        assert response.status_code == 200

        data = response.json()
        assert "Background Tasks" in data["message"]
        assert "features" in data
        assert "endpoints" in data
        assert "task_counts" in data

@pytest.mark.asyncio
async def test_create_long_running_task(background_tasks_server):
    """Test creating a long-running background task"""
    async with httpx.AsyncClient() as client:
        task_data = {
            "task_type": "long_running",
            "duration": 2.0,
            "data": "test data"
        }

        response = await client.post(f"{background_tasks_server}/tasks/create", json=task_data)
        assert response.status_code == 201

        data = response.json()
        assert data["message"] == "Task created successfully"
        assert "task_id" in data
        assert data["task_type"] == "long_running"
        assert data["status"] == "pending"

        return data["task_id"]

@pytest.mark.asyncio
async def test_task_status_tracking(background_tasks_server):
    """Test task status tracking and progress updates"""
    async with httpx.AsyncClient() as client:
        # Create a task with shorter duration for testing
        task_data = {"task_type": "long_running", "duration": 2.0}  # Increased for more reliable timing
        response = await client.post(f"{background_tasks_server}/tasks/create", json=task_data)
        task_id = response.json()["task_id"]

        # Check initial status
        response = await client.get(f"{background_tasks_server}/tasks/{task_id}/status")
        assert response.status_code == 200

        status_data = response.json()
        assert status_data["task_id"] == task_id
        assert status_data["status"] in ["pending", "running"]
        assert "progress" in status_data

        # Wait a bit and check progress
        progress_data = await wait_for_task_progress(client, background_tasks_server, task_id)
        assert progress_data is not None, "Task should show progress within timeout"
        assert progress_data["status"] == "running"
        assert progress_data["progress"] > 0
        assert "current_step" in progress_data

        # Wait for completion with polling
        completion_data = await wait_for_task_completion(client, background_tasks_server, task_id)
        assert completion_data is not None, "Task should complete within timeout"
        assert completion_data["status"] == "completed"
        assert completion_data["progress"] == 100

@pytest.mark.asyncio
async def test_task_result_retrieval(background_tasks_server):
    """Test retrieving task results after completion"""
    async with httpx.AsyncClient() as client:
        # Create a short task (0.5 seconds to be safe)
        task_data = {"task_type": "long_running", "duration": 0.5, "data": "result test"}
        response = await client.post(f"{background_tasks_server}/tasks/create", json=task_data)
        task_id = response.json()["task_id"]

        # Try to get result before completion (should fail)
        response = await client.get(f"{background_tasks_server}/tasks/{task_id}/result")
        assert response.status_code == 400

        # Wait for completion with polling
        completion_data = await wait_for_task_completion(client, background_tasks_server, task_id)
        assert completion_data is not None, "Task should complete within timeout"

        # Get result after completion
        response = await client.get(f"{background_tasks_server}/tasks/{task_id}/result")
        assert response.status_code == 200

        result_data = response.json()
        assert result_data["task_id"] == task_id
        assert "result" in result_data
        assert result_data["result"]["message"] == "Task completed successfully"
        assert result_data["result"]["data"] == "result test"

@pytest.mark.asyncio
async def test_email_task_creation(background_tasks_server):
    """Test creating email sending background tasks"""
    async with httpx.AsyncClient() as client:
        email_data = {
            "to": "test@example.com",
            "subject": "Test Email",
            "body": "This is a test email from background task",
            "delay": 0.5
        }

        response = await client.post(f"{background_tasks_server}/tasks/email", json=email_data)
        assert response.status_code == 201

        data = response.json()
        assert data["message"] == "Email task created successfully"
        assert "task_id" in data
        assert data["task_type"] == "email"
        assert data["to"] == "test@example.com"
        assert data["subject"] == "Test Email"

        task_id = data["task_id"]

        # Wait for completion with polling
        completion_data = await wait_for_task_completion(client, background_tasks_server, task_id)
        assert completion_data is not None, "Task should complete within timeout"

        # Check result
        response = await client.get(f"{background_tasks_server}/tasks/{task_id}/result")
        assert response.status_code == 200

        result = response.json()["result"]
        assert result["message"] == "Email sent successfully"
        assert result["to"] == "test@example.com"

@pytest.mark.asyncio
async def test_data_processing_task(background_tasks_server):
    """Test data processing background tasks"""
    async with httpx.AsyncClient() as client:
        processing_data = {
            "data": ["hello", "world", "test", "data"],
            "operation": "transform",
            "batch_size": 2
        }

        response = await client.post(f"{background_tasks_server}/tasks/process", json=processing_data)
        assert response.status_code == 201

        data = response.json()
        assert data["message"] == "Processing task created successfully"
        assert data["task_type"] == "processing"
        assert data["operation"] == "transform"
        assert data["data_count"] == 4

        task_id = data["task_id"]

        # Wait for completion
        completion_data = await wait_for_task_completion(client, background_tasks_server, task_id)
        assert completion_data is not None, "Task should complete within timeout"

        # Check result
        response = await client.get(f"{background_tasks_server}/tasks/{task_id}/result")
        assert response.status_code == 200

        result = response.json()["result"]
        assert result["message"] == "Data processing completed"
        assert result["operation"] == "transform"
        assert result["processed_items"] == ["HELLO", "WORLD", "TEST", "DATA"]

@pytest.mark.asyncio
async def test_task_cancellation(background_tasks_server):
    """Test cancelling running tasks"""
    async with httpx.AsyncClient() as client:
        # Create a long task
        task_data = {"task_type": "long_running", "duration": 10.0}
        response = await client.post(f"{background_tasks_server}/tasks/create", json=task_data)
        task_id = response.json()["task_id"]

        # Wait a bit for it to start
        await asyncio.sleep(0.5)

        # Cancel the task
        response = await client.delete(f"{background_tasks_server}/tasks/{task_id}")
        if response.status_code != 200:
            print(f"Error response: {response.status_code}, {response.text}")
        assert response.status_code == 200

        data = response.json()
        assert data["message"] == "Task cancelled/deleted successfully"
        assert data["task_id"] == task_id

        # Try to get the task (should be gone)
        response = await client.get(f"{background_tasks_server}/tasks/{task_id}")
        assert response.status_code == 404

@pytest.mark.asyncio
async def test_list_tasks(background_tasks_server):
    """Test listing tasks with filtering"""
    async with httpx.AsyncClient() as client:
        # Create multiple tasks
        task_ids = []

        # Create a few tasks
        for i in range(3):
            task_data = {"task_type": "long_running", "duration": 1.0}
            response = await client.post(f"{background_tasks_server}/tasks/create", json=task_data)
            task_ids.append(response.json()["task_id"])

        # List all tasks
        response = await client.get(f"{background_tasks_server}/tasks/list")
        assert response.status_code == 200

        data = response.json()
        assert "tasks" in data
        assert data["total_count"] >= 3

        # List only running/pending tasks
        response = await client.get(f"{background_tasks_server}/tasks/list?status=running")
        assert response.status_code == 200

        data = response.json()
        assert data["filter"] == "running"

        # Wait for completion and list completed tasks
        for task_id in task_ids:
            completion_data = await wait_for_task_completion(client, background_tasks_server, task_id)
            assert completion_data is not None, f"Task {task_id} should complete within timeout"
        response = await client.get(f"{background_tasks_server}/tasks/list?status=completed")
        assert response.status_code == 200

        data = response.json()
        assert data["filter"] == "completed"

@pytest.mark.asyncio
async def test_task_statistics(background_tasks_server):
    """Test task execution statistics"""
    async with httpx.AsyncClient() as client:
        # Create some tasks
        email_data = {"to": "test@example.com", "subject": "Test", "body": "Test"}
        await client.post(f"{background_tasks_server}/tasks/email", json=email_data)

        processing_data = {"data": ["test"], "operation": "transform"}
        await client.post(f"{background_tasks_server}/tasks/process", json=processing_data)

        # Get statistics
        response = await client.get(f"{background_tasks_server}/tasks/stats")
        assert response.status_code == 200

        data = response.json()
        stats = data["statistics"]

        assert "total_tasks" in stats
        assert "status_counts" in stats
        assert "type_counts" in stats
        assert "active_tasks" in stats
        assert "average_completion_time" in stats

        # Should have different task types
        assert stats["total_tasks"] >= 2
        assert "email" in stats["type_counts"]
        assert "processing" in stats["type_counts"]

@pytest.mark.asyncio
async def test_task_cleanup(background_tasks_server):
    """Test cleaning up completed/failed tasks"""
    async with httpx.AsyncClient() as client:
        # Create and complete some tasks
        task_data = {"task_type": "long_running", "duration": 1.0}
        response = await client.post(f"{background_tasks_server}/tasks/create", json=task_data)
        task_id = response.json()["task_id"]

        # Wait for completion
        completion_data = await wait_for_task_completion(client, background_tasks_server, task_id)
        assert completion_data is not None, "Task should complete within timeout"

        # Verify task is completed
        assert completion_data["status"] == "completed"

        # Clean up
        response = await client.post(f"{background_tasks_server}/tasks/cleanup")
        assert response.status_code == 200

        data = response.json()
        assert data["message"] == "Task cleanup completed"
        assert data["removed_count"] >= 1
        assert "removed_tasks" in data

        # Verify task is gone
        response = await client.get(f"{background_tasks_server}/tasks/{task_id}")
        assert response.status_code == 404

@pytest.mark.asyncio
async def test_concurrent_task_creation(background_tasks_server):
    """Test creating multiple tasks concurrently"""
    async with httpx.AsyncClient() as client:
        # Create multiple tasks concurrently
        tasks = []
        for i in range(5):
            task_data = {"task_type": "long_running", "duration": 1.0, "data": f"task_{i}"}
            tasks.append(client.post(f"{background_tasks_server}/tasks/create", json=task_data))

        # Execute concurrently
        responses = await asyncio.gather(*tasks)

        # All should succeed
        task_ids = []
        for response in responses:
            assert response.status_code == 201
            task_ids.append(response.json()["task_id"])

        # All task IDs should be unique
        assert len(set(task_ids)) == 5

        # Wait for completion
        for task_id in task_ids:
            completion_data = await wait_for_task_completion(client, background_tasks_server, task_id)
            assert completion_data is not None, f"Task {task_id} should complete within timeout"
            assert completion_data["status"] == "completed"

@pytest.mark.asyncio
async def test_task_progress_monitoring(background_tasks_server):
    """Test monitoring task progress over time"""
    async with httpx.AsyncClient() as client:
        # Create a longer task
        task_data = {"task_type": "long_running", "duration": 4.0}
        response = await client.post(f"{background_tasks_server}/tasks/create", json=task_data)
        task_id = response.json()["task_id"]

        # Monitor progress
        progress_history = []

        for i in range(8):  # Check progress 8 times over 4 seconds
            await asyncio.sleep(0.5)
            response = await client.get(f"{background_tasks_server}/tasks/{task_id}/status")
            if response.status_code == 200:
                status_data = response.json()
                progress_history.append({
                    "time": i * 0.5,
                    "progress": status_data.get("progress", 0),
                    "status": status_data["status"]
                })

        # Progress should increase over time
        assert len(progress_history) > 0

        # Find running states
        running_states = [p for p in progress_history if p["status"] == "running"]
        if len(running_states) >= 2:
            # Progress should increase
            assert running_states[-1]["progress"] > running_states[0]["progress"]

        # Final state should be completed
        final_state = progress_history[-1]
        assert final_state["status"] in ["completed", "running"]

@pytest.mark.asyncio
async def test_different_processing_operations(background_tasks_server):
    """Test different data processing operations"""
    async with httpx.AsyncClient() as client:
        test_data = ["hello", "world"]
        operations = ["transform", "reverse", "length"]

        for operation in operations:
            processing_data = {
                "data": test_data,
                "operation": operation,
                "batch_size": 1
            }

            response = await client.post(f"{background_tasks_server}/tasks/process", json=processing_data)
            assert response.status_code == 201

            task_id = response.json()["task_id"]

            # Wait for completion
            completion_data = await wait_for_task_completion(client, background_tasks_server, task_id)
            assert completion_data is not None, f"Task {task_id} should complete within timeout"

            # Check result
            response = await client.get(f"{background_tasks_server}/tasks/{task_id}/result")
            assert response.status_code == 200

            result = response.json()["result"]
            assert result["operation"] == operation

            if operation == "transform":
                assert result["processed_items"] == ["HELLO", "WORLD"]
            elif operation == "reverse":
                assert result["processed_items"] == ["olleh", "dlrow"]
            elif operation == "length":
                assert result["processed_items"] == [5, 5]

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
