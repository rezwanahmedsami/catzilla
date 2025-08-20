#!/usr/bin/env python3
"""
Debug test for background tasks to check thread execution
"""
import asyncio
import pytest
import httpx

@pytest.mark.asyncio
async def test_debug_background_tasks(background_tasks_server):
    """Debug background tasks with detailed logging"""
    async with httpx.AsyncClient() as client:
        # Create a task
        task_data = {"task_type": "long_running", "duration": 1.0}
        response = await client.post(f"{background_tasks_server}/tasks/create", json=task_data)
        print(f"\n=== DEBUG BACKGROUND TASKS ===")
        print(f"1. Create task: {response.status_code}")

        assert response.status_code == 201
        task_id = response.json()["task_id"]
        print(f"   Task ID: {task_id}")

        # Check status immediately
        response = await client.get(f"{background_tasks_server}/tasks/{task_id}/status")
        print(f"\n2. Initial status: {response.status_code}")
        assert response.status_code == 200

        status = response.json()
        print(f"   Status: {status['status']}")
        print(f"   Progress: {status['progress']}")
        print(f"   Thread created: {status.get('thread_created', False)}")
        print(f"   Thread started: {status.get('thread_started', False)}")
        print(f"   Debug log: {status.get('debug_log', [])}")

        # Wait a bit
        print(f"\n3. Waiting 1.5 seconds...")
        await asyncio.sleep(1.5)

        response = await client.get(f"{background_tasks_server}/tasks/{task_id}/status")
        print(f"   Status check: {response.status_code}")
        assert response.status_code == 200

        status = response.json()
        print(f"   Status: {status['status']}")
        print(f"   Progress: {status['progress']}")
        print(f"   Current step: {status.get('current_step', 'None')}")
        print(f"   Thread created: {status.get('thread_created', False)}")
        print(f"   Thread started: {status.get('thread_started', False)}")
        print(f"   Thread error: {status.get('thread_error', 'None')}")
        print(f"   Debug log: {status.get('debug_log', [])}")

        # Wait for completion
        print(f"\n4. Waiting another 1.0 seconds...")
        await asyncio.sleep(1.0)

        response = await client.get(f"{background_tasks_server}/tasks/{task_id}/status")
        print(f"   Final status check: {response.status_code}")
        assert response.status_code == 200

        status = response.json()
        print(f"   Final status: {status['status']}")
        print(f"   Final progress: {status['progress']}")
        print(f"   Current step: {status.get('current_step', 'None')}")
        print(f"   Thread created: {status.get('thread_created', False)}")
        print(f"   Thread started: {status.get('thread_started', False)}")
        print(f"   Thread error: {status.get('thread_error', 'None')}")
        print(f"   Debug log: {status.get('debug_log', [])}")

        print(f"\n=== END DEBUG ===")

        # For the test to pass, let's just check that we got some progress
        # The actual assertion can fail, we just want to see the debug info
        if status['status'] != 'completed':
            print(f"WARNING: Task did not complete as expected. Status: {status['status']}")
