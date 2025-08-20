#!/usr/bin/env python3
"""
E2E Test Server for Background Tasks Functionality

This server mirrors examples/background_tasks/ for E2E testing.
It provides background task functionality to be tested via HTTP.
"""
import sys
import argparse
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from catzilla import Catzilla, Request, Response, JSONResponse, BaseModel, Path as PathParam
from typing import Optional, List, Dict
import time
import threading
import uuid
from datetime import datetime
import json

# Initialize Catzilla for E2E testing
app = Catzilla(
    production=False,
    show_banner=False,
    log_requests=False
)

# Task storage and management
task_storage: Dict[str, Dict] = {}
task_results: Dict[str, Dict] = {}
running_tasks: Dict[str, threading.Thread] = {}
cancelled_tasks: set = set()

# Pydantic models
class TaskCreate(BaseModel):
    """Task creation model"""
    task_type: str
    duration: float = 5.0  # seconds
    data: Optional[str] = None

class EmailTask(BaseModel):
    """Email task model"""
    to: str
    subject: str
    body: str
    delay: float = 0.0

class ProcessingTask(BaseModel):
    """Data processing task model"""
    data: List[str]
    operation: str = "transform"
    batch_size: int = 10

# ============================================================================
# BACKGROUND TASK FUNCTIONS
# ============================================================================

def long_running_task(task_id: str, duration: float, data: str = None):
    """Simulate a long-running background task"""
    try:
        # Update task status
        task_storage[task_id]["status"] = "running"
        task_storage[task_id]["started_at"] = time.time()

        # Simulate work with progress updates
        total_steps = int(duration * 2)  # Update every 0.5 seconds

        for step in range(total_steps):
            # Check for cancellation
            if task_id in cancelled_tasks:
                task_storage[task_id]["status"] = "cancelled"
                task_storage[task_id]["cancelled_at"] = time.time()
                if task_id in running_tasks:
                    del running_tasks[task_id]
                return

            time.sleep(0.5)
            progress = (step + 1) / total_steps * 100
            task_storage[task_id]["progress"] = progress
            task_storage[task_id]["current_step"] = f"Processing step {step + 1}/{total_steps}"

        # Complete task
        result = {
            "message": "Task completed successfully",
            "data": data,
            "duration": duration,
            "steps_completed": total_steps,
            "completed_at": time.time()
        }

        task_storage[task_id]["status"] = "completed"
        task_storage[task_id]["completed_at"] = time.time()
        task_storage[task_id]["progress"] = 100
        task_results[task_id] = result

        # Clean up thread reference
        if task_id in running_tasks:
            del running_tasks[task_id]

    except Exception as e:
        # Task failed
        import traceback
        task_storage[task_id]["status"] = "failed"
        task_storage[task_id]["error"] = str(e)
        task_storage[task_id]["failed_at"] = time.time()

        # Clean up thread reference
        if task_id in running_tasks:
            del running_tasks[task_id]

def email_sending_task(task_id: str, to: str, subject: str, body: str, delay: float = 0.0):
    """Simulate email sending background task"""
    try:
        task_storage[task_id]["status"] = "running"
        task_storage[task_id]["started_at"] = time.time()

        # Initial delay if specified
        if delay > 0:
            task_storage[task_id]["current_step"] = f"Waiting {delay} seconds before sending"
            time.sleep(delay)

        # Simulate email preparation
        task_storage[task_id]["current_step"] = "Preparing email"
        task_storage[task_id]["progress"] = 25
        time.sleep(1)

        # Simulate SMTP connection
        task_storage[task_id]["current_step"] = "Connecting to SMTP server"
        task_storage[task_id]["progress"] = 50
        time.sleep(1)

        # Simulate sending
        task_storage[task_id]["current_step"] = "Sending email"
        task_storage[task_id]["progress"] = 75
        time.sleep(1)

        # Complete
        result = {
            "message": "Email sent successfully",
            "to": to,
            "subject": subject,
            "body_length": len(body),
            "sent_at": time.time()
        }

        task_storage[task_id]["status"] = "completed"
        task_storage[task_id]["completed_at"] = time.time()
        task_storage[task_id]["progress"] = 100
        task_storage[task_id]["current_step"] = "Email sent"
        task_results[task_id] = result

    except Exception as e:
        task_storage[task_id]["status"] = "failed"
        task_storage[task_id]["error"] = str(e)
        task_storage[task_id]["failed_at"] = time.time()

def data_processing_task(task_id: str, data: List[str], operation: str, batch_size: int):
    """Simulate data processing background task"""
    try:
        task_storage[task_id]["status"] = "running"
        task_storage[task_id]["started_at"] = time.time()

        total_items = len(data)
        processed_items = []

        # Process in batches
        for i in range(0, total_items, batch_size):
            batch = data[i:i + batch_size]

            # Update progress
            progress = (i / total_items) * 100
            task_storage[task_id]["progress"] = progress
            task_storage[task_id]["current_step"] = f"Processing batch {i//batch_size + 1}"

            # Simulate processing each item in batch
            batch_results = []
            for item in batch:
                time.sleep(0.1)  # Simulate processing time

                if operation == "transform":
                    result = item.upper()
                elif operation == "reverse":
                    result = item[::-1]
                elif operation == "length":
                    result = len(item)
                else:
                    result = item

                batch_results.append(result)

            processed_items.extend(batch_results)

        # Complete
        result = {
            "message": "Data processing completed",
            "operation": operation,
            "total_items": total_items,
            "processed_items": processed_items,
            "batch_size": batch_size,
            "completed_at": time.time()
        }

        task_storage[task_id]["status"] = "completed"
        task_storage[task_id]["completed_at"] = time.time()
        task_storage[task_id]["progress"] = 100
        task_storage[task_id]["current_step"] = "Processing complete"
        task_results[task_id] = result

    except Exception as e:
        task_storage[task_id]["status"] = "failed"
        task_storage[task_id]["error"] = str(e)
        task_storage[task_id]["failed_at"] = time.time()

# ============================================================================
# ROUTES
# ============================================================================

# Health check
@app.get("/health")
def health_check(request: Request) -> Response:
    """Health check endpoint"""
    return JSONResponse({
        "status": "healthy",
        "server": "background_tasks_e2e_test",
        "timestamp": time.time(),
        "active_tasks": len(running_tasks),
        "total_tasks": len(task_storage)
    })

@app.post("/reset")
def reset_state(request: Request) -> Response:
    """Reset server state for testing"""
    global task_storage, task_results, running_tasks, cancelled_tasks

    # Cancel all running tasks
    for task_id, thread in running_tasks.items():
        cancelled_tasks.add(task_id)

    # Clear all storage
    task_storage.clear()
    task_results.clear()
    running_tasks.clear()
    cancelled_tasks.clear()

    return JSONResponse({
        "message": "Server state reset successfully",
        "timestamp": time.time()
    })

# Basic info
@app.get("/")
def home(request: Request) -> Response:
    """Background tasks test server info"""
    return JSONResponse({
        "message": "Catzilla E2E Background Tasks Test Server",
        "features": [
            "Long-running tasks",
            "Email sending tasks",
            "Data processing tasks",
            "Task monitoring",
            "Task cancellation",
            "Progress tracking"
        ],
        "endpoints": [
            "POST /tasks/create",
            "POST /tasks/email",
            "POST /tasks/process",
            "GET /tasks/{task_id}",
            "GET /tasks/{task_id}/status",
            "GET /tasks/{task_id}/result",
            "DELETE /tasks/{task_id}",
            "GET /tasks/list",
            "GET /tasks/stats"
        ],
        "task_counts": {
            "total": len(task_storage),
            "running": len([t for t in task_storage.values() if t["status"] == "running"]),
            "completed": len([t for t in task_storage.values() if t["status"] == "completed"]),
            "failed": len([t for t in task_storage.values() if t["status"] == "failed"])
        }
    })

# Create generic background task
@app.post("/tasks/create")
def create_task(request: Request) -> Response:
    """Create a new background task"""
    try:
        # Parse JSON data manually
        task_data = request.json()

        task_id = str(uuid.uuid4())

        # Store task info
        task_info = {
            "id": task_id,
            "type": task_data.get("task_type"),
            "status": "pending",
            "created_at": time.time(),
            "progress": 0,
            "current_step": "Task created"
        }
        task_storage[task_id] = task_info

        # Start the task in a separate thread since we can't use asyncio.create_task
        # from a sync function without an event loop
        if task_data.get("task_type") == "long_running":
            # Start task in thread
            def run_task():
                try:
                    long_running_task(task_id, task_data.get("duration", 1.0), task_data.get("data", ""))
                except Exception as e:
                    # Ensure task failure is recorded
                    task_storage[task_id]["status"] = "failed"
                    task_storage[task_id]["error"] = str(e)
                    task_storage[task_id]["failed_at"] = time.time()
                    if task_id in running_tasks:
                        del running_tasks[task_id]

            thread = threading.Thread(target=run_task)
            thread.daemon = True
            thread.start()
            running_tasks[task_id] = thread
        else:
            return JSONResponse({
                "error": "Unknown task type",
                "supported_types": ["long_running"]
            }, status_code=400)

        return JSONResponse({
            "message": "Task created successfully",
            "task_id": task_id,
            "task_type": task_data.get("task_type"),
            "status": "pending",
            "created_at": task_info["created_at"]
        }, status_code=201)

    except Exception as e:
        return JSONResponse({
            "error": "Failed to create task",
            "message": str(e)
        }, status_code=500)

# Create email task
@app.post("/tasks/email")
def create_email_task(request: Request) -> Response:
    """Create an email sending background task"""
    try:
        # Parse JSON data manually
        email_data = request.json()

        task_id = str(uuid.uuid4())

        # Store task info
        task_info = {
            "id": task_id,
            "type": "email",
            "status": "pending",
            "created_at": time.time(),
            "progress": 0,
            "current_step": "Email task created"
        }
        task_storage[task_id] = task_info

        # Start the email task in a separate thread
        def run_email_task():
            email_sending_task(
                task_id,
                email_data.get("to"),
                email_data.get("subject"),
                email_data.get("body"),
                email_data.get("delay", 0.0)
            )

        thread = threading.Thread(target=run_email_task)
        thread.daemon = True
        thread.start()
        running_tasks[task_id] = thread

        return JSONResponse({
            "message": "Email task created successfully",
            "task_id": task_id,
            "task_type": "email",
            "status": "pending",
            "to": email_data.get("to"),
            "subject": email_data.get("subject"),
            "created_at": task_info["created_at"]
        }, status_code=201)

    except Exception as e:
        return JSONResponse({
            "error": "Failed to create email task",
            "message": str(e)
        }, status_code=500)

# Create data processing task
@app.post("/tasks/process")
def create_processing_task(request: Request) -> Response:
    """Create a data processing background task"""
    try:
        # Parse JSON data manually
        processing_data = request.json()

        task_id = str(uuid.uuid4())

        # Store task info
        task_info = {
            "id": task_id,
            "type": "processing",
            "status": "pending",
            "created_at": time.time(),
            "progress": 0,
            "current_step": "Processing task created"
        }
        task_storage[task_id] = task_info

        # Start the processing task in a separate thread
        def run_processing_task():
            data_processing_task(
                task_id,
                processing_data.get("data", []),
                processing_data.get("operation", "transform"),
                processing_data.get("batch_size", 10)
            )

        thread = threading.Thread(target=run_processing_task)
        thread.daemon = True
        thread.start()
        running_tasks[task_id] = thread

        return JSONResponse({
            "message": "Processing task created successfully",
            "task_id": task_id,
            "task_type": "processing",
            "status": "pending",
            "operation": processing_data.get("operation"),
            "data_count": len(processing_data.get("data", [])),
            "created_at": task_info["created_at"]
        }, status_code=201)

    except Exception as e:
        return JSONResponse({
            "error": "Failed to create processing task",
            "message": str(e)
        }, status_code=500)

    # Store task info
    task_info = {
        "id": task_id,
        "type": "processing",
        "status": "pending",
        "created_at": time.time(),
        "progress": 0,
        "current_step": "Processing task created"
    }
    task_storage[task_id] = task_info

    # Start the processing task
    task = asyncio.create_task(
        data_processing_task(task_id, processing_data.data, processing_data.operation, processing_data.batch_size)
    )
    running_tasks[task_id] = task

    return JSONResponse({
        "message": "Processing task created successfully",
        "task_id": task_id,
        "task_type": "processing",
        "status": "pending",
        "operation": processing_data.operation,
        "data_count": len(processing_data.data),
        "batch_size": processing_data.batch_size,
        "created_at": task_info["created_at"]
    }, status_code=201)

# Get task details
@app.get("/tasks/{task_id}")
def get_task(request: Request, task_id: str = PathParam(..., description="Task ID")) -> Response:
    """Get complete task information"""
    try:
        if task_id not in task_storage:
            return JSONResponse({
                "error": "Task not found",
                "task_id": task_id
            }, status_code=404)

        task_info = task_storage[task_id].copy()

        # Add result if available
        if task_id in task_results:
            task_info["result"] = task_results[task_id]

        return JSONResponse({
            "task": task_info,
            "timestamp": time.time()
        })
    except Exception as e:
        import traceback
        return JSONResponse({
            "error": "Failed to get task",
            "task_id": task_id,
            "exception": str(e),
            "traceback": traceback.format_exc()
        }, status_code=500)

# Get task status only
@app.get("/tasks/{task_id}/status")
def get_task_status(request: Request, task_id: str = PathParam(..., description="Task ID")) -> Response:
    """Get task status and progress"""
    try:
        if task_id not in task_storage:
            return JSONResponse({
                "error": "Task not found",
                "task_id": task_id,
                "available_tasks": list(task_storage.keys())
            }, status_code=404)

        task_info = task_storage[task_id]

        return JSONResponse({
            "task_id": task_id,
            "status": task_info["status"],
            "progress": task_info.get("progress", 0),
            "current_step": task_info.get("current_step", "Unknown"),
            "created_at": task_info["created_at"],
            "started_at": task_info.get("started_at"),
            "completed_at": task_info.get("completed_at"),
            "failed_at": task_info.get("failed_at"),
            "error": task_info.get("error")
        })

    except Exception as e:
        return JSONResponse({
            "error": "Failed to get task status",
            "message": str(e)
        }, status_code=500)

# Get task result
@app.get("/tasks/{task_id}/result")
def get_task_result(request: Request, task_id: str = PathParam(..., description="Task ID")) -> Response:
    """Get task result (only if completed)"""
    if task_id not in task_storage:
        return JSONResponse({
            "error": "Task not found",
            "task_id": task_id
        }, status_code=404)

    task_info = task_storage[task_id]

    if task_info["status"] != "completed":
        return JSONResponse({
            "error": "Task not completed",
            "task_id": task_id,
            "status": task_info["status"]
        }, status_code=400)

    if task_id not in task_results:
        return JSONResponse({
            "error": "Task result not available",
            "task_id": task_id
        }, status_code=404)

    return JSONResponse({
        "task_id": task_id,
        "result": task_results[task_id],
        "timestamp": time.time()
    })

# Cancel/delete task
@app.delete("/tasks/{task_id}")
def cancel_task(request: Request, task_id: str = PathParam(..., description="Task ID")) -> Response:
    """Cancel a running task or delete a completed task"""
    try:
        if task_id not in task_storage:
            return JSONResponse({
                "error": "Task not found",
                "task_id": task_id
            }, status_code=404)

        task_info = task_storage[task_id].copy()  # Make a copy to avoid race conditions
        previous_status = task_info["status"]

        # Cancel running task
        if task_id in running_tasks:
            cancelled_tasks.add(task_id)  # Mark for cancellation
            # Wait briefly for thread to notice cancellation
            time.sleep(0.2)  # Increased wait time
            if task_id in running_tasks:  # Check again after wait
                del running_tasks[task_id]
            if task_id in task_storage:  # Check if still exists
                task_storage[task_id]["status"] = "cancelled"
                task_storage[task_id]["cancelled_at"] = time.time()
            previous_status = "cancelled"

        # Remove from storage (safely)
        if task_id in task_storage:
            del task_storage[task_id]
        if task_id in task_results:
            del task_results[task_id]
        if task_id in cancelled_tasks:
            cancelled_tasks.remove(task_id)

        return JSONResponse({
            "message": "Task cancelled/deleted successfully",
            "task_id": task_id,
            "previous_status": previous_status,
            "timestamp": time.time()
        })
    except Exception as e:
        import traceback
        return JSONResponse({
            "error": "Failed to cancel task",
            "task_id": task_id,
            "exception": str(e),
            "traceback": traceback.format_exc()
        }, status_code=500)

# List all tasks
@app.get("/tasks/list")
def list_tasks(request) -> Response:
    """List all tasks, optionally filtered by status"""
    status_filter = request.query_params.get("status")

    if status_filter:
        filtered_tasks = {
            task_id: task for task_id, task in task_storage.items()
            if task["status"] == status_filter
        }
        return Response(
            status_code=200,
            content_type="application/json",
            body=json.dumps({
                "tasks": filtered_tasks,
                "total_count": len(filtered_tasks),
                "filter": status_filter
            })
        )

    return Response(
        status_code=200,
        content_type="application/json",
        body=json.dumps({
            "tasks": task_storage,
            "total_count": len(task_storage)
        })
    )

# Task statistics
@app.get("/tasks/stats")
def get_task_stats(request: Request) -> Response:
    """Get task execution statistics"""
    stats = {
        "total_tasks": len(task_storage),
        "status_counts": {
            "pending": 0,
            "running": 0,
            "completed": 0,
            "failed": 0,
            "cancelled": 0
        },
        "type_counts": {},
        "active_tasks": len(running_tasks)
    }

    # Count by status and type
    for task_info in task_storage.values():
        status = task_info["status"]
        task_type = task_info["type"]

        stats["status_counts"][status] = stats["status_counts"].get(status, 0) + 1
        stats["type_counts"][task_type] = stats["type_counts"].get(task_type, 0) + 1

    # Calculate average completion time for completed tasks
    completed_tasks = [t for t in task_storage.values() if t["status"] == "completed" and "completed_at" in t and "started_at" in t]
    if completed_tasks:
        total_duration = sum(t["completed_at"] - t["started_at"] for t in completed_tasks)
        stats["average_completion_time"] = total_duration / len(completed_tasks)
    else:
        stats["average_completion_time"] = 0

    return JSONResponse({
        "statistics": stats,
        "timestamp": time.time()
    })

# Clear all completed/failed tasks
@app.post("/tasks/cleanup")
def cleanup_tasks(request: Request) -> Response:
    """Clean up completed and failed tasks"""
    removed_tasks = []

    # Remove completed and failed tasks
    to_remove = []
    for task_id, task_info in task_storage.items():
        if task_info["status"] in ["completed", "failed", "cancelled"]:
            to_remove.append(task_id)

    for task_id in to_remove:
        removed_tasks.append({
            "id": task_id,
            "status": task_storage[task_id]["status"],
            "type": task_storage[task_id]["type"]
        })
        del task_storage[task_id]
        if task_id in task_results:
            del task_results[task_id]

    return JSONResponse({
        "message": "Task cleanup completed",
        "removed_count": len(removed_tasks),
        "removed_tasks": removed_tasks,
        "remaining_tasks": len(task_storage),
        "timestamp": time.time()
    })

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Catzilla E2E Background Tasks Test Server")
    parser.add_argument("--port", type=int, default=8106, help="Port to run server on")
    parser.add_argument("--host", type=str, default="127.0.0.1", help="Host to bind to")

    args = parser.parse_args()

    print(f"🚀 Starting Catzilla E2E Background Tasks Test Server")
    print(f"📍 Server: http://{args.host}:{args.port}")
    print(f"🏥 Health: http://{args.host}:{args.port}/health")

    app.listen(port=args.port, host=args.host)
