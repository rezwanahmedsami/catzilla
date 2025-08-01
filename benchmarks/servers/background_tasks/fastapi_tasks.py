#!/usr/bin/env python3
"""
FastAPI Background Tasks Benchmark Server

Comprehensive background task processing using FastAPI with Celery integration.
Tests async task execution, scheduling, and queue management performance.

Features:
- Task creation and queuing
- Multiple task types (computation, I/O, network)
- Task status monitoring and results
- Batch task processing
- Task scheduling and retry logic
- Real-time task progress tracking
"""

import sys
import os
import json
import time
import argparse
import uuid
import asyncio
from typing import Optional, List, Dict, Any, Union
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import random
import threading
from queue import Queue
from dataclasses import dataclass, asdict
from enum import Enum

# FastAPI imports
from fastapi import FastAPI, Query, Path as PathParam, Header, Form, Depends, BackgroundTasks
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn

# Import shared background task endpoints
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'shared'))
from background_endpoints import get_background_endpoints


# =====================================================
# TASK MODELS AND ENUMS
# =====================================================

class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    RETRYING = "retrying"

class TaskPriority(str, Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"

class TaskType(str, Enum):
    COMPUTATION = "computation"
    IO_OPERATION = "io_operation"
    NETWORK_REQUEST = "network_request"
    DATA_PROCESSING = "data_processing"
    EMAIL_SENDING = "email_sending"
    REPORT_GENERATION = "report_generation"

class TaskRequest(BaseModel):
    """Task creation request"""
    task_type: TaskType
    priority: TaskPriority = TaskPriority.NORMAL
    payload: Dict[str, Any]
    delay_seconds: Optional[int] = Field(None, ge=0, le=3600)
    max_retries: int = Field(3, ge=0, le=10)
    timeout_seconds: Optional[int] = Field(None, ge=1, le=3600)

class BatchTaskRequest(BaseModel):
    """Batch task creation request"""
    tasks: List[TaskRequest] = Field(min_items=1, max_items=100)
    execute_parallel: bool = True
    max_concurrent: int = Field(5, ge=1, le=20)

@dataclass
class Task:
    """Task data structure"""
    id: str
    task_type: str
    priority: str
    payload: Dict[str, Any]
    status: str = TaskStatus.PENDING
    created_at: str = ""
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    progress: float = 0.0
    result: Optional[Any] = None
    error: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3
    timeout_seconds: Optional[int] = None
    worker_id: Optional[str] = None


def create_fastapi_tasks_server():
    """Create FastAPI server with background task processing"""

    app = FastAPI(
        title="FastAPI Background Tasks Benchmark",
        description="Background task processing performance testing with FastAPI",
        version="1.0.0"
    )

    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Task execution infrastructure
    executor = ThreadPoolExecutor(max_workers=8)
    process_executor = ProcessPoolExecutor(max_workers=4)

    # Task storage and queues
    task_store = {
        "tasks": {},
        "queues": {
            "urgent": Queue(),
            "high": Queue(),
            "normal": Queue(),
            "low": Queue()
        },
        "workers": {},
        "stats": {
            "total_created": 0,
            "total_completed": 0,
            "total_failed": 0,
            "avg_execution_time": 0.0
        }
    }

    # Start background workers
    for i in range(4):
        worker_id = f"worker_{i}"
        worker_thread = threading.Thread(
            target=task_worker,
            args=(worker_id, task_store, executor),
            daemon=True
        )
        worker_thread.start()
        task_store["workers"][worker_id] = {
            "status": "running",
            "tasks_processed": 0,
            "current_task": None
        }

    endpoints = get_background_endpoints()

    # ==========================================
    # TASK CREATION ENDPOINTS
    # ==========================================

    @app.post("/tasks")
    async def create_task(
        background_tasks: BackgroundTasks,
        task_request: TaskRequest
    ):
        """Create a new background task"""
        start_time = time.perf_counter()

        # Generate task ID
        task_id = str(uuid.uuid4())

        # Create task
        task = Task(
            id=task_id,
            task_type=task_request.task_type.value,
            priority=task_request.priority.value,
            payload=task_request.payload,
            created_at=datetime.now().isoformat(),
            max_retries=task_request.max_retries,
            timeout_seconds=task_request.timeout_seconds
        )

        # Store task
        task_store["tasks"][task_id] = task
        task_store["stats"]["total_created"] += 1

        # Add to appropriate queue based on priority
        if task_request.delay_seconds:
            # Schedule delayed task
            background_tasks.add_task(
                schedule_delayed_task,
                task_id, task_request.delay_seconds, task_store
            )
        else:
            # Add to immediate execution queue
            priority_queue = task_store["queues"][task_request.priority.value]
            priority_queue.put(task_id)

        processing_time = (time.perf_counter() - start_time) * 1000

        return JSONResponse({
            "task_created": True,
            "task_id": task_id,
            "status": task.status,
            "priority": task.priority,
            "estimated_start": "immediate" if not task_request.delay_seconds else f"{task_request.delay_seconds}s",
            "processing_time_ms": round(processing_time, 3),
            "framework": "fastapi"
        })

    @app.post("/tasks/batch")
    async def create_batch_tasks(
        background_tasks: BackgroundTasks,
        batch_request: BatchTaskRequest
    ):
        """Create multiple tasks in batch"""
        start_time = time.perf_counter()

        created_tasks = []

        for task_request in batch_request.tasks:
            # Generate task ID
            task_id = str(uuid.uuid4())

            # Create task
            task = Task(
                id=task_id,
                task_type=task_request.task_type.value,
                priority=task_request.priority.value,
                payload=task_request.payload,
                created_at=datetime.now().isoformat(),
                max_retries=task_request.max_retries,
                timeout_seconds=task_request.timeout_seconds
            )

            # Store task
            task_store["tasks"][task_id] = task
            task_store["stats"]["total_created"] += 1

            # Add to queue
            priority_queue = task_store["queues"][task_request.priority.value]
            priority_queue.put(task_id)

            created_tasks.append({
                "task_id": task_id,
                "task_type": task.task_type,
                "priority": task.priority
            })

        # Schedule batch monitoring if needed
        if batch_request.execute_parallel:
            batch_id = str(uuid.uuid4())
            background_tasks.add_task(
                monitor_batch_execution,
                batch_id, [t["task_id"] for t in created_tasks], task_store
            )

        processing_time = (time.perf_counter() - start_time) * 1000

        return JSONResponse({
            "batch_created": True,
            "batch_size": len(created_tasks),
            "tasks": created_tasks,
            "parallel_execution": batch_request.execute_parallel,
            "processing_time_ms": round(processing_time, 3),
            "framework": "fastapi"
        })

    # ==========================================
    # TASK MONITORING ENDPOINTS
    # ==========================================

    @app.get("/tasks/{task_id}")
    async def get_task_status(task_id: str = PathParam(...)):
        """Get task status and details"""
        start_time = time.perf_counter()

        if task_id not in task_store["tasks"]:
            return JSONResponse({"error": "Task not found"}, status_code=404)

        task = task_store["tasks"][task_id]

        # Calculate runtime if running
        runtime_seconds = None
        if task.started_at:
            start_dt = datetime.fromisoformat(task.started_at)
            if task.completed_at:
                end_dt = datetime.fromisoformat(task.completed_at)
                runtime_seconds = (end_dt - start_dt).total_seconds()
            else:
                runtime_seconds = (datetime.now() - start_dt).total_seconds()

        processing_time = (time.perf_counter() - start_time) * 1000

        task_data = asdict(task)
        task_data["runtime_seconds"] = runtime_seconds

        return JSONResponse({
            "task": task_data,
            "processing_time_ms": round(processing_time, 3),
            "framework": "fastapi"
        })

    @app.get("/tasks")
    async def list_tasks(
        status: Optional[TaskStatus] = Query(None),
        task_type: Optional[TaskType] = Query(None),
        priority: Optional[TaskPriority] = Query(None),
        limit: int = Query(50, ge=1, le=1000),
        offset: int = Query(0, ge=0)
    ):
        """List tasks with filtering"""
        start_time = time.perf_counter()

        tasks = list(task_store["tasks"].values())

        # Apply filters
        if status:
            tasks = [t for t in tasks if t.status == status.value]
        if task_type:
            tasks = [t for t in tasks if t.task_type == task_type.value]
        if priority:
            tasks = [t for t in tasks if t.priority == priority.value]

        # Sort by created_at (newest first)
        tasks.sort(key=lambda x: x.created_at, reverse=True)

        # Apply pagination
        total_count = len(tasks)
        paginated_tasks = tasks[offset:offset + limit]

        # Convert to dict format
        task_list = [asdict(task) for task in paginated_tasks]

        processing_time = (time.perf_counter() - start_time) * 1000

        return JSONResponse({
            "tasks": task_list,
            "total": total_count,
            "limit": limit,
            "offset": offset,
            "filters": {
                "status": status.value if status else None,
                "task_type": task_type.value if task_type else None,
                "priority": priority.value if priority else None
            },
            "processing_time_ms": round(processing_time, 3),
            "framework": "fastapi"
        })

    @app.delete("/tasks/{task_id}")
    async def cancel_task(task_id: str = PathParam(...)):
        """Cancel a pending or running task"""
        start_time = time.perf_counter()

        if task_id not in task_store["tasks"]:
            return JSONResponse({"error": "Task not found"}, status_code=404)

        task = task_store["tasks"][task_id]

        if task.status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]:
            return JSONResponse({
                "error": f"Cannot cancel task in {task.status} status"
            }, status_code=400)

        # Mark task as cancelled
        task.status = TaskStatus.CANCELLED
        task.completed_at = datetime.now().isoformat()
        task.error = "Task was cancelled"

        processing_time = (time.perf_counter() - start_time) * 1000

        return JSONResponse({
            "task_cancelled": True,
            "task_id": task_id,
            "processing_time_ms": round(processing_time, 3),
            "framework": "fastapi"
        })

    # ==========================================
    # TASK EXECUTION ENDPOINTS
    # ==========================================

    @app.post("/tasks/{task_id}/retry")
    async def retry_task(task_id: str = PathParam(...)):
        """Retry a failed task"""
        start_time = time.perf_counter()

        if task_id not in task_store["tasks"]:
            return JSONResponse({"error": "Task not found"}, status_code=404)

        task = task_store["tasks"][task_id]

        if task.status != TaskStatus.FAILED:
            return JSONResponse({
                "error": f"Cannot retry task in {task.status} status"
            }, status_code=400)

        if task.retry_count >= task.max_retries:
            return JSONResponse({
                "error": "Maximum retry attempts exceeded"
            }, status_code=400)

        # Reset task for retry
        task.status = TaskStatus.PENDING
        task.started_at = None
        task.completed_at = None
        task.error = None
        task.result = None
        task.retry_count += 1
        task.progress = 0.0

        # Add back to queue
        priority_queue = task_store["queues"][task.priority]
        priority_queue.put(task_id)

        processing_time = (time.perf_counter() - start_time) * 1000

        return JSONResponse({
            "task_retried": True,
            "task_id": task_id,
            "retry_count": task.retry_count,
            "max_retries": task.max_retries,
            "processing_time_ms": round(processing_time, 3),
            "framework": "fastapi"
        })

    # ==========================================
    # SYSTEM MONITORING ENDPOINTS
    # ==========================================

    @app.get("/stats")
    async def get_system_stats():
        """Get system and task statistics"""
        start_time = time.perf_counter()

        # Count tasks by status
        status_counts = {}
        type_counts = {}
        priority_counts = {}

        for task in task_store["tasks"].values():
            status_counts[task.status] = status_counts.get(task.status, 0) + 1
            type_counts[task.task_type] = type_counts.get(task.task_type, 0) + 1
            priority_counts[task.priority] = priority_counts.get(task.priority, 0) + 1

        # Queue sizes
        queue_sizes = {
            priority: queue.qsize()
            for priority, queue in task_store["queues"].items()
        }

        # Worker stats
        worker_stats = {}
        for worker_id, worker_info in task_store["workers"].items():
            worker_stats[worker_id] = {
                "status": worker_info["status"],
                "tasks_processed": worker_info["tasks_processed"],
                "current_task": worker_info["current_task"]
            }

        processing_time = (time.perf_counter() - start_time) * 1000

        return JSONResponse({
            "system_stats": {
                "total_tasks": len(task_store["tasks"]),
                "status_breakdown": status_counts,
                "type_breakdown": type_counts,
                "priority_breakdown": priority_counts,
                "queue_sizes": queue_sizes,
                "worker_stats": worker_stats,
                "global_stats": task_store["stats"]
            },
            "processing_time_ms": round(processing_time, 3),
            "framework": "fastapi"
        })

    @app.get("/health")
    async def health():
        """Health check"""
        active_workers = sum(
            1 for worker in task_store["workers"].values()
            if worker["status"] == "running"
        )

        return JSONResponse({
            "status": "healthy",
            "framework": "fastapi",
            "features": ["background_tasks", "task_scheduling", "task_monitoring", "task_retry"],
            "active_workers": active_workers,
            "total_tasks": len(task_store["tasks"]),
            "pending_tasks": sum(q.qsize() for q in task_store["queues"].values())
        })

    return app


# =====================================================
# BACKGROUND TASK WORKERS AND PROCESSORS
# =====================================================

def task_worker(worker_id: str, task_store: Dict, executor: ThreadPoolExecutor):
    """Background worker that processes tasks from queues"""
    worker_info = task_store["workers"][worker_id]

    while True:
        try:
            # Check queues in priority order
            task_id = None
            for priority in ["urgent", "high", "normal", "low"]:
                queue = task_store["queues"][priority]
                if not queue.empty():
                    task_id = queue.get_nowait()
                    break

            if task_id and task_id in task_store["tasks"]:
                task = task_store["tasks"][task_id]

                # Skip cancelled tasks
                if task.status == TaskStatus.CANCELLED:
                    continue

                # Update worker status
                worker_info["current_task"] = task_id

                # Execute task
                execute_task(task, worker_id, task_store)

                # Update worker stats
                worker_info["tasks_processed"] += 1
                worker_info["current_task"] = None

            else:
                # No tasks available, sleep briefly
                time.sleep(0.1)

        except Exception as e:
            print(f"Worker {worker_id} error: {e}")
            time.sleep(1)

def execute_task(task: Task, worker_id: str, task_store: Dict):
    """Execute a single task"""
    try:
        # Update task status
        task.status = TaskStatus.RUNNING
        task.started_at = datetime.now().isoformat()
        task.worker_id = worker_id

        # Execute based on task type
        if task.task_type == TaskType.COMPUTATION:
            result = execute_computation_task(task)
        elif task.task_type == TaskType.IO_OPERATION:
            result = execute_io_task(task)
        elif task.task_type == TaskType.NETWORK_REQUEST:
            result = execute_network_task(task)
        elif task.task_type == TaskType.DATA_PROCESSING:
            result = execute_data_processing_task(task)
        elif task.task_type == TaskType.EMAIL_SENDING:
            result = execute_email_task(task)
        elif task.task_type == TaskType.REPORT_GENERATION:
            result = execute_report_task(task)
        else:
            result = {"message": "Unknown task type"}

        # Mark as completed
        task.status = TaskStatus.COMPLETED
        task.completed_at = datetime.now().isoformat()
        task.result = result
        task.progress = 100.0

        # Update global stats
        task_store["stats"]["total_completed"] += 1

    except Exception as e:
        # Mark as failed
        task.status = TaskStatus.FAILED
        task.completed_at = datetime.now().isoformat()
        task.error = str(e)
        task_store["stats"]["total_failed"] += 1

def execute_computation_task(task: Task) -> Dict[str, Any]:
    """Execute computation-intensive task"""
    payload = task.payload
    iterations = payload.get("iterations", 1000000)

    # Simulate CPU-intensive work
    start_time = time.perf_counter()
    result = 0

    for i in range(iterations):
        result += i * i
        if i % (iterations // 10) == 0:
            task.progress = (i / iterations) * 100

    execution_time = time.perf_counter() - start_time

    return {
        "result": result,
        "iterations": iterations,
        "execution_time": execution_time
    }

def execute_io_task(task: Task) -> Dict[str, Any]:
    """Execute I/O task"""
    payload = task.payload
    file_size = payload.get("file_size", 1024)

    # Simulate file I/O
    time.sleep(0.5)  # Simulate I/O wait
    task.progress = 50.0

    time.sleep(0.5)  # Simulate more I/O
    task.progress = 100.0

    return {
        "operation": "file_io",
        "file_size": file_size,
        "status": "completed"
    }

def execute_network_task(task: Task) -> Dict[str, Any]:
    """Execute network request task"""
    payload = task.payload
    url = payload.get("url", "https://example.com")

    # Simulate network request
    time.sleep(random.uniform(0.5, 2.0))  # Variable network delay
    task.progress = 100.0

    return {
        "url": url,
        "status_code": 200,
        "response_time": random.uniform(100, 500)
    }

def execute_data_processing_task(task: Task) -> Dict[str, Any]:
    """Execute data processing task"""
    payload = task.payload
    records = payload.get("records", 1000)

    # Simulate data processing
    for i in range(10):
        time.sleep(0.1)
        task.progress = (i + 1) * 10

    return {
        "records_processed": records,
        "status": "completed"
    }

def execute_email_task(task: Task) -> Dict[str, Any]:
    """Execute email sending task"""
    payload = task.payload
    recipients = payload.get("recipients", ["user@example.com"])

    # Simulate email sending
    time.sleep(1.0)
    task.progress = 100.0

    return {
        "recipients": recipients,
        "emails_sent": len(recipients),
        "status": "sent"
    }

def execute_report_task(task: Task) -> Dict[str, Any]:
    """Execute report generation task"""
    payload = task.payload
    report_type = payload.get("type", "summary")

    # Simulate report generation
    for i in range(5):
        time.sleep(0.5)
        task.progress = (i + 1) * 20

    return {
        "report_type": report_type,
        "report_id": str(uuid.uuid4()),
        "status": "generated"
    }

async def schedule_delayed_task(task_id: str, delay_seconds: int, task_store: Dict):
    """Schedule a task to run after a delay"""
    await asyncio.sleep(delay_seconds)

    if task_id in task_store["tasks"]:
        task = task_store["tasks"][task_id]
        if task.status == TaskStatus.PENDING:
            # Add to appropriate queue
            priority_queue = task_store["queues"][task.priority]
            priority_queue.put(task_id)

async def monitor_batch_execution(batch_id: str, task_ids: List[str], task_store: Dict):
    """Monitor execution of a batch of tasks"""
    print(f"Monitoring batch {batch_id} with {len(task_ids)} tasks")

    while True:
        completed_tasks = 0
        for task_id in task_ids:
            if task_id in task_store["tasks"]:
                task = task_store["tasks"][task_id]
                if task.status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]:
                    completed_tasks += 1

        if completed_tasks == len(task_ids):
            print(f"Batch {batch_id} completed: {completed_tasks}/{len(task_ids)} tasks")
            break

        await asyncio.sleep(1)


def main():
    parser = argparse.ArgumentParser(description='FastAPI background tasks benchmark server')
    parser.add_argument('--host', default='127.0.0.1', help='Host to bind to')
    parser.add_argument('--port', type=int, default=8201, help='Port to bind to')
    parser.add_argument('--workers', type=int, default=1, help='Number of workers')

    args = parser.parse_args()

    app = create_fastapi_tasks_server()

    print(f"🚀 Starting FastAPI background tasks benchmark server on {args.host}:{args.port}")
    print("Background task endpoints:")
    print("  POST /tasks                    - Create task")
    print("  POST /tasks/batch              - Create batch tasks")
    print("  GET  /tasks/{task_id}          - Get task status")
    print("  GET  /tasks                    - List tasks")
    print("  DELETE /tasks/{task_id}        - Cancel task")
    print("  POST /tasks/{task_id}/retry    - Retry failed task")
    print("  GET  /stats                    - System statistics")
    print("  GET  /health                   - Health check")
    print()

    uvicorn.run(app, host=args.host, port=args.port, workers=args.workers)


if __name__ == "__main__":
    main()
