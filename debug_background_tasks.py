#!/usr/bin/env python3
"""
Debug script for background tasks issues
"""
import asyncio
import httpx
import sys
import time

async def debug_background_tasks():
    """Debug background tasks by inspecting the server responses"""
    try:
        async with httpx.AsyncClient() as client:
            # Test server health first
            try:
                response = await client.get('http://127.0.0.1:8106/health')
                print(f"Health check: {response.status_code} - {response.json()}")
            except Exception as e:
                print(f"Health check failed: {e}")
                return

            # Create a task
            task_data = {"task_type": "long_running", "duration": 1.0}
            response = await client.post('http://127.0.0.1:8106/tasks/create', json=task_data)
            print(f"\n1. Create task: {response.status_code}")
            if response.status_code != 201:
                print(f"Failed to create task: {response.text}")
                return

            task_response = response.json()
            task_id = task_response["task_id"]
            print(f"   Task ID: {task_id}")
            print(f"   Response: {task_response}")

            # Check status immediately
            response = await client.get(f'http://127.0.0.1:8106/tasks/{task_id}/status')
            print(f"\n2. Initial status: {response.status_code}")
            if response.status_code == 200:
                status = response.json()
                print(f"   Status: {status['status']}")
                print(f"   Progress: {status['progress']}")
                print(f"   Debug log: {status.get('debug_log', 'None')}")
            else:
                print(f"   Error: {response.text}")

            # Wait and check again
            print("\n3. Waiting 1.5 seconds...")
            await asyncio.sleep(1.5)

            response = await client.get(f'http://127.0.0.1:8106/tasks/{task_id}/status')
            print(f"   Status after 1.5s: {response.status_code}")
            if response.status_code == 200:
                status = response.json()
                print(f"   Status: {status['status']}")
                print(f"   Progress: {status['progress']}")
                print(f"   Current step: {status.get('current_step', 'None')}")
                print(f"   Debug log: {status.get('debug_log', 'None')}")
            else:
                print(f"   Error: {response.text}")

            # Wait for completion
            print("\n4. Waiting another 1.0 seconds...")
            await asyncio.sleep(1.0)

            response = await client.get(f'http://127.0.0.1:8106/tasks/{task_id}/status')
            print(f"   Final status: {response.status_code}")
            if response.status_code == 200:
                status = response.json()
                print(f"   Status: {status['status']}")
                print(f"   Progress: {status['progress']}")
                print(f"   Current step: {status.get('current_step', 'None')}")
                print(f"   Debug log: {status.get('debug_log', 'None')}")

                # If completed, try to get result
                if status['status'] == 'completed':
                    response = await client.get(f'http://127.0.0.1:8106/tasks/{task_id}/result')
                    print(f"\n5. Result: {response.status_code}")
                    if response.status_code == 200:
                        print(f"   Result: {response.json()}")
                    else:
                        print(f"   Error: {response.text}")
            else:
                print(f"   Error: {response.text}")

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_background_tasks())
