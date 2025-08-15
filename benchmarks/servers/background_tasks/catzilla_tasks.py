#!/usr/bin/env python3
"""
Catzilla Background Tasks Benchmark Server

High-performance background task processing benchmarks using Catzilla's optimized task system.
Tests task queuing, execution, scheduling, and monitoring capabilities.

Features:
- Optimized background task processing
- Task queue management with priority
- Scheduled task execution
- Task monitoring and status tracking
- Memory-efficient task processing
"""

import sys
import os
import json
import time
import argparse
import asyncio
import threading
from typing import Optional, List, Dict, Any, Callable
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor
import uuid

# Add the catzilla package to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', 'python'))

from catzilla import (
    Catzilla, BaseModel, Field,
    JSONResponse, Response, Query, Path as PathParam, Header, Form
)

# Import shared background task endpoints
# sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'shared'))
# from background_endpoints import get_background_endpoints


# =====================================================
# BACKGROUND TASK MODELS
# =====================================================

class TaskRequest(BaseModel):
    """Background task request model"""
    task_type: str = Field(regex=r'^(computation|io|network|data_processing|email|report)$')
    parameters: Dict[str, Any] = {}
    priority: int = Field(default=5, ge=1, le=10)
    delay_seconds: Optional[int] = Field(default=0, ge=0)

class TaskResponse(BaseModel):
    """Background task response model"""
    task_id: str
    task_type: str
    status: str
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

class BatchTaskRequest(BaseModel):
    """Batch background task request model"""
    tasks: List[TaskRequest] = Field(min_items=1, max_items=1000)
    execute_parallel: bool = True


# =====================================================
# TASK PROCESSING FUNCTIONS
# =====================================================

def computation_task(task_id: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
    """CPU-intensive computation task"""
    n = parameters.get("iterations", 1000)
    start_time = time.perf_counter()

    # Simulate computation
    result = 0
    for i in range(n):
        result += i ** 2

    processing_time = (time.perf_counter() - start_time) * 1000

    return {
        "task_id": task_id,
        "result": result,
        "iterations": n,
        "processing_time_ms": round(processing_time, 3),
        "completed": True
    }

def io_task(task_id: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
    """I/O intensive task simulation"""
    file_count = parameters.get("file_count", 10)
    file_size = parameters.get("file_size", 1024)  # bytes

    start_time = time.perf_counter()

    # Simulate file operations
    import tempfile
    files_created = []

    with tempfile.TemporaryDirectory() as temp_dir:
        for i in range(file_count):
            file_path = os.path.join(temp_dir, f"test_file_{i}.txt")
            with open(file_path, "w") as f:
                f.write("A" * file_size)
            files_created.append(file_path)

        # Read all files back
        total_bytes_read = 0
        for file_path in files_created:
            with open(file_path, "r") as f:
                content = f.read()
                total_bytes_read += len(content)

    processing_time = (time.perf_counter() - start_time) * 1000

    return {
        "task_id": task_id,
        "files_processed": file_count,
        "total_bytes": total_bytes_read,
        "processing_time_ms": round(processing_time, 3),
        "completed": True
    }

def network_task(task_id: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
    """Network operation simulation"""
    request_count = parameters.get("request_count", 5)
    delay_ms = parameters.get("delay_ms", 100)

    start_time = time.perf_counter()

    # Simulate network requests
    results = []
    for i in range(request_count):
        # Simulate network delay
        # Removed artificial delay for benchmarking
        results.append({
            "request_id": i,
            "status": "success",
            "response_time_ms": delay_ms
        })

    processing_time = (time.perf_counter() - start_time) * 1000

    return {
        "task_id": task_id,
        "requests_completed": request_count,
        "results": results,
        "processing_time_ms": round(processing_time, 3),
        "completed": True
    }

def data_processing_task(task_id: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
    """Data processing task simulation"""
    record_count = parameters.get("record_count", 1000)
    operation = parameters.get("operation", "aggregate")

    start_time = time.perf_counter()

    # Generate sample data
    data = [
        {
            "id": i,
            "value": i * 1.5,
            "category": f"cat_{i % 10}",
            "timestamp": time.time() - (i * 60)
        }
        for i in range(record_count)
    ]

    # Process data
    if operation == "aggregate":
        result = {
            "total_records": len(data),
            "sum_values": sum(record["value"] for record in data),
            "avg_value": sum(record["value"] for record in data) / len(data),
            "categories": len(set(record["category"] for record in data))
        }
    elif operation == "filter":
        threshold = parameters.get("threshold", 500)
        filtered = [record for record in data if record["value"] > threshold]
        result = {
            "total_records": len(data),
            "filtered_records": len(filtered),
            "threshold": threshold
        }
    else:
        result = {"total_records": len(data)}

    processing_time = (time.perf_counter() - start_time) * 1000

    return {
        "task_id": task_id,
        "operation": operation,
        "result": result,
        "processing_time_ms": round(processing_time, 3),
        "completed": True
    }

def email_task(task_id: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
    """Email sending simulation"""
    recipient_count = parameters.get("recipient_count", 10)
    template = parameters.get("template", "newsletter")

    start_time = time.perf_counter()

    # Simulate email processing
    emails_sent = []
    for i in range(recipient_count):
        # Simulate email processing delay
        # Removed artificial delay for benchmarking  # 10ms per email
        emails_sent.append({
            "recipient": f"user{i}@example.com",
            "template": template,
            "status": "sent",
            "send_time": time.time()
        })

    processing_time = (time.perf_counter() - start_time) * 1000

    return {
        "task_id": task_id,
        "emails_sent": len(emails_sent),
        "template": template,
        "processing_time_ms": round(processing_time, 3),
        "completed": True
    }

def report_task(task_id: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
    """Report generation simulation"""
    report_type = parameters.get("report_type", "summary")
    data_points = parameters.get("data_points", 1000)

    start_time = time.perf_counter()

    # Simulate report generation
    report_data = {
        "report_id": str(uuid.uuid4()),
        "type": report_type,
        "generated_at": datetime.now().isoformat(),
        "data_points": data_points,
        "summary": {
            "total_items": data_points,
            "processing_time": "calculated_below",
            "status": "completed"
        }
    }

    # Simulate report processing time
    # Removed artificial delay for benchmarking  # 100ms base processing time

    processing_time = (time.perf_counter() - start_time) * 1000
    report_data["summary"]["processing_time"] = f"{processing_time:.3f}ms"

    return {
        "task_id": task_id,
        "report": report_data,
        "processing_time_ms": round(processing_time, 3),
        "completed": True
    }


# Task registry
TASK_FUNCTIONS = {
    "computation": computation_task,
    "io": io_task,
    "network": network_task,
    "data_processing": data_processing_task,
    "email": email_task,
    "report": report_task
}


def create_catzilla_background_server():
    """Create Catzilla server optimized for background task processing"""

    app = Catzilla(
        production=True,
        use_jemalloc=True,           # Memory optimization
        auto_validation=True,        # Enable auto-validation
        memory_profiling=False,      # Disable for benchmarks
        auto_memory_tuning=True,     # Adaptive memory management
        show_banner=False
    )

    # Enable background task system
    app.enable_background_tasks(
        workers=4,
        enable_profiling=True,
        memory_pool_mb=500
    )

    # Task storage (in production, this would be a proper queue system)
    tasks_storage = {}
    task_queue = []
    executor = ThreadPoolExecutor(max_workers=10)

    # endpoints = get_background_endpoints()

    def execute_task(task_id: str, task_type: str, parameters: Dict[str, Any]) -> None:
        """Execute a background task"""
        try:
            # Update task status
            tasks_storage[task_id]["status"] = "running"
            tasks_storage[task_id]["started_at"] = datetime.now()

            # Execute task function
            if task_type in TASK_FUNCTIONS:
                result = TASK_FUNCTIONS[task_type](task_id, parameters)
                tasks_storage[task_id]["result"] = result
                tasks_storage[task_id]["status"] = "completed"
            else:
                tasks_storage[task_id]["error"] = f"Unknown task type: {task_type}"
                tasks_storage[task_id]["status"] = "failed"

            tasks_storage[task_id]["completed_at"] = datetime.now()

        except Exception as e:
            tasks_storage[task_id]["error"] = str(e)
            tasks_storage[task_id]["status"] = "failed"
            tasks_storage[task_id]["completed_at"] = datetime.now()

    # ==========================================
    # SINGLE TASK OPERATIONS
    # ==========================================

    @app.post("/tasks/create")
    def create_task(request, task_request: TaskRequest) -> Response:
        """Create a single background task"""
        task_id = str(uuid.uuid4())

        # Store task information
        task_info = {
            "task_id": task_id,
            "task_type": task_request.task_type,
            "parameters": task_request.parameters,
            "priority": task_request.priority,
            "status": "pending",
            "created_at": datetime.now(),
            "started_at": None,
            "completed_at": None,
            "result": None,
            "error": None
        }

        tasks_storage[task_id] = task_info

        # Schedule task execution with optional delay
        if task_request.delay_seconds > 0:
            # In a real implementation, this would use a proper scheduler
            def delayed_execution():
                # Removed artificial delay for benchmarking
                execute_task(task_id, task_request.task_type, task_request.parameters)

            executor.submit(delayed_execution)
        else:
            executor.submit(execute_task, task_id, task_request.task_type, task_request.parameters)

        return JSONResponse({
            "task_created": True,
            "task_id": task_id,
            "task_type": task_request.task_type,
            "status": "pending",
            "framework": "catzilla"
        })

    @app.get("/tasks/{task_id}")
    def get_task_status(request, task_id: str = PathParam(...)) -> Response:
        """Get task status and result"""
        if task_id not in tasks_storage:
            return JSONResponse({"error": "Task not found"}, status_code=404)

        task_info = tasks_storage[task_id]

        return JSONResponse({
            "task_id": task_id,
            "task_type": task_info["task_type"],
            "status": task_info["status"],
            "created_at": task_info["created_at"].isoformat(),
            "started_at": task_info["started_at"].isoformat() if task_info["started_at"] else None,
            "completed_at": task_info["completed_at"].isoformat() if task_info["completed_at"] else None,
            "result": task_info["result"],
            "error": task_info["error"],
            "framework": "catzilla"
        })

    @app.delete("/tasks/{task_id}")
    def cancel_task(request, task_id: str = PathParam(...)) -> Response:
        """Cancel a background task"""
        if task_id not in tasks_storage:
            return JSONResponse({"error": "Task not found"}, status_code=404)

        task_info = tasks_storage[task_id]

        if task_info["status"] in ["completed", "failed"]:
            return JSONResponse({
                "error": f"Cannot cancel task with status: {task_info['status']}"
            }, status_code=400)

        # Mark as cancelled
        task_info["status"] = "cancelled"
        task_info["completed_at"] = datetime.now()

        return JSONResponse({
            "task_cancelled": True,
            "task_id": task_id,
            "framework": "catzilla"
        })

    # ==========================================
    # BATCH TASK OPERATIONS
    # ==========================================

    @app.post("/tasks/batch")
    def create_batch_tasks(request, batch_request: BatchTaskRequest) -> Response:
        """Create multiple background tasks"""
        start_time = time.perf_counter()

        created_tasks = []

        for task_request in batch_request.tasks:
            task_id = str(uuid.uuid4())

            task_info = {
                "task_id": task_id,
                "task_type": task_request.task_type,
                "parameters": task_request.parameters,
                "priority": task_request.priority,
                "status": "pending",
                "created_at": datetime.now(),
                "started_at": None,
                "completed_at": None,
                "result": None,
                "error": None
            }

            tasks_storage[task_id] = task_info
            created_tasks.append(task_id)

            # Submit task for execution
            executor.submit(execute_task, task_id, task_request.task_type, task_request.parameters)

        creation_time = (time.perf_counter() - start_time) * 1000

        return JSONResponse({
            "batch_created": True,
            "task_count": len(created_tasks),
            "task_ids": created_tasks,
            "execute_parallel": batch_request.execute_parallel,
            "creation_time_ms": round(creation_time, 3),
            "framework": "catzilla"
        })

    @app.get("/tasks/batch/status")
    def get_batch_status(request, task_ids: str = Query(..., description="Comma-separated task IDs")) -> Response:
        """Get status of multiple tasks"""
        task_id_list = [tid.strip() for tid in task_ids.split(",")]

        batch_status = []
        for task_id in task_id_list:
            if task_id in tasks_storage:
                task_info = tasks_storage[task_id]
                batch_status.append({
                    "task_id": task_id,
                    "status": task_info["status"],
                    "task_type": task_info["task_type"],
                    "completed_at": task_info["completed_at"].isoformat() if task_info["completed_at"] else None
                })
            else:
                batch_status.append({
                    "task_id": task_id,
                    "status": "not_found"
                })

        # Calculate summary
        status_counts = {}
        for task in batch_status:
            status = task["status"]
            status_counts[status] = status_counts.get(status, 0) + 1

        return JSONResponse({
            "batch_status": batch_status,
            "summary": status_counts,
            "total_tasks": len(batch_status),
            "framework": "catzilla"
        })

    # ==========================================
    # TASK QUEUE MANAGEMENT
    # ==========================================

    @app.get("/tasks/queue/stats")
    def get_queue_stats(request) -> Response:
        """Get task queue statistics"""
        # Calculate statistics
        status_counts = {}
        total_tasks = len(tasks_storage)

        for task_info in tasks_storage.values():
            status = task_info["status"]
            status_counts[status] = status_counts.get(status, 0) + 1

        # Calculate processing times for completed tasks
        completed_tasks = [t for t in tasks_storage.values() if t["status"] == "completed"]
        processing_times = []

        for task in completed_tasks:
            if task["started_at"] and task["completed_at"]:
                duration = (task["completed_at"] - task["started_at"]).total_seconds() * 1000
                processing_times.append(duration)

        avg_processing_time = sum(processing_times) / len(processing_times) if processing_times else 0

        return JSONResponse({
            "total_tasks": total_tasks,
            "status_counts": status_counts,
            "completed_tasks": len(completed_tasks),
            "avg_processing_time_ms": round(avg_processing_time, 3),
            "queue_health": "healthy" if status_counts.get("failed", 0) < total_tasks * 0.1 else "degraded",
            "framework": "catzilla"
        })

    @app.delete("/tasks/queue/clear")
    def clear_completed_tasks(request) -> Response:
        """Clear completed and failed tasks from queue"""
        cleared_count = 0
        task_ids_to_remove = []

        for task_id, task_info in tasks_storage.items():
            if task_info["status"] in ["completed", "failed", "cancelled"]:
                task_ids_to_remove.append(task_id)
                cleared_count += 1

        for task_id in task_ids_to_remove:
            del tasks_storage[task_id]

        return JSONResponse({
            "cleared": True,
            "tasks_removed": cleared_count,
            "remaining_tasks": len(tasks_storage),
            "framework": "catzilla"
        })

    # ==========================================
    # SCHEDULED TASKS
    # ==========================================

    @app.post("/tasks/schedule")
    def schedule_task(
        request,
        task_request: TaskRequest,
        schedule_time: str = Query(..., description="ISO format datetime for scheduling")
    ) -> Response:
        """Schedule a task for future execution"""
        try:
            scheduled_datetime = datetime.fromisoformat(schedule_time.replace('Z', '+00:00'))
            current_time = datetime.now()

            if scheduled_datetime <= current_time:
                return JSONResponse({
                    "error": "Scheduled time must be in the future"
                }, status_code=400)

            delay_seconds = (scheduled_datetime - current_time).total_seconds()

            task_id = str(uuid.uuid4())

            task_info = {
                "task_id": task_id,
                "task_type": task_request.task_type,
                "parameters": task_request.parameters,
                "priority": task_request.priority,
                "status": "scheduled",
                "created_at": datetime.now(),
                "scheduled_at": scheduled_datetime,
                "started_at": None,
                "completed_at": None,
                "result": None,
                "error": None
            }

            tasks_storage[task_id] = task_info

            # Schedule execution
            def scheduled_execution():
                # Removed artificial delay for benchmarking
                execute_task(task_id, task_request.task_type, task_request.parameters)

            executor.submit(scheduled_execution)

            return JSONResponse({
                "task_scheduled": True,
                "task_id": task_id,
                "scheduled_at": scheduled_datetime.isoformat(),
                "delay_seconds": round(delay_seconds, 3),
                "framework": "catzilla"
            })

        except ValueError as e:
            return JSONResponse({
                "error": f"Invalid datetime format: {str(e)}"
            }, status_code=400)

    @app.get("/health")
    def health(request) -> Response:
        """Health check endpoint"""
        return JSONResponse({
            "status": "healthy",
            "framework": "catzilla",
            "background_tasks": "enabled",
            "memory_optimization": "jemalloc_enabled",
            "active_tasks": len([t for t in tasks_storage.values() if t["status"] in ["pending", "running"]]),
            "total_tasks": len(tasks_storage)
        })

    return app


def main():
    parser = argparse.ArgumentParser(description='Catzilla background tasks benchmark server')
    parser.add_argument('--host', default='127.0.0.1', help='Host to bind to')
    parser.add_argument('--port', type=int, default=8300, help='Port to bind to')
    parser.add_argument('--workers', type=int, default=1, help='Number of workers')

    args = parser.parse_args()

    app = create_catzilla_background_server()

    print(f"🚀 Starting Catzilla background tasks benchmark server on {args.host}:{args.port}")
    print("Background task endpoints:")
    print("  POST /tasks/create              - Create single task")
    print("  GET  /tasks/{task_id}           - Get task status")
    print("  DELETE /tasks/{task_id}         - Cancel task")
    print("  POST /tasks/batch               - Create batch tasks")
    print("  GET  /tasks/batch/status        - Get batch status")
    print("  GET  /tasks/queue/stats         - Queue statistics")
    print("  DELETE /tasks/queue/clear       - Clear completed tasks")
    print("  POST /tasks/schedule            - Schedule future task")
    print("  GET  /health                    - Health check")
    print()

    try:
        app.listen(args.port, args.host)
    except KeyboardInterrupt:
        print("\n👋 Catzilla background tasks benchmark server stopped")


if __name__ == "__main__":
    main()
