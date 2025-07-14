"""
Task Monitoring and Shutdown Example

This example demonstrates Catzilla's background task monitoring capabilities
and graceful shutdown handling for production environments.

Features demonstrated:
- Real-time task monitoring with metrics
- Graceful shutdown with task completion waiting
- Task health checking and failure recovery
- Resource usage monitoring
- Task queue management
"""

from catzilla import Catzilla, Request, Response, JSONResponse
import asyncio
import time
import signal
import os
import psutil
from datetime import datetime, timedelta
from typing import Dict, Any, List
import threading

# Initialize Catzilla with monitoring enabled
app = Catzilla(
    production=False,
    show_banner=True,
    log_requests=True,
    enable_background_tasks=True,
    graceful_shutdown_timeout=30  # Wait up to 30 seconds for tasks to complete
)

# Global task monitoring data
task_metrics = {
    "total_scheduled": 0,
    "total_completed": 0,
    "total_failed": 0,
    "current_running": 0,
    "longest_running_time": 0,
    "average_completion_time": 0,
    "last_update": datetime.now()
}

active_tasks: Dict[str, Dict[str, Any]] = {}
completed_tasks: List[Dict[str, Any]] = []
system_metrics = {
    "cpu_usage": 0.0,
    "memory_usage": 0.0,
    "task_queue_size": 0
}

# Task monitoring lock for thread safety
metrics_lock = threading.Lock()

def long_running_task(task_id: str, duration: int):
    """Simulate a long-running task for monitoring"""
    start_time = time.time()

    with metrics_lock:
        task_metrics["total_scheduled"] += 1
        task_metrics["current_running"] += 1
        active_tasks[task_id] = {
            "id": task_id,
            "type": "long_running",
            "status": "running",
            "start_time": start_time,
            "duration": duration,
            "progress": 0
        }

    try:
        for i in range(duration):
            # Check for shutdown signal
            if app.is_shutting_down:
                print(f"⏹️  Task {task_id} received shutdown signal, cleaning up...")
                break

            time.sleep(1)

            # Update progress
            with metrics_lock:
                if task_id in active_tasks:
                    active_tasks[task_id]["progress"] = int(((i + 1) / duration) * 100)

            print(f"🔄 Task {task_id} progress: {((i + 1) / duration) * 100:.1f}%")

        # Task completed
        completion_time = time.time() - start_time

        with metrics_lock:
            task_metrics["current_running"] -= 1
            task_metrics["total_completed"] += 1

            # Update average completion time
            if task_metrics["total_completed"] > 0:
                task_metrics["average_completion_time"] = (
                    (task_metrics["average_completion_time"] * (task_metrics["total_completed"] - 1) + completion_time) /
                    task_metrics["total_completed"]
                )

            # Update longest running time
            if completion_time > task_metrics["longest_running_time"]:
                task_metrics["longest_running_time"] = completion_time

            # Move to completed tasks
            if task_id in active_tasks:
                task_info = active_tasks[task_id]
                task_info["status"] = "completed"
                task_info["completion_time"] = completion_time
                task_info["completed_at"] = datetime.now()
                completed_tasks.append(task_info)
                del active_tasks[task_id]

            task_metrics["last_update"] = datetime.now()

        print(f"✅ Task {task_id} completed in {completion_time:.2f} seconds")

    except Exception as e:
        # Task failed
        with metrics_lock:
            task_metrics["current_running"] -= 1
            task_metrics["total_failed"] += 1

            if task_id in active_tasks:
                task_info = active_tasks[task_id]
                task_info["status"] = "failed"
                task_info["error"] = str(e)
                task_info["failed_at"] = datetime.now()
                completed_tasks.append(task_info)
                del active_tasks[task_id]

            task_metrics["last_update"] = datetime.now()

        print(f"❌ Task {task_id} failed: {e}")

def memory_intensive_task(task_id: str, memory_mb: int):
    """Simulate a memory-intensive task"""
    start_time = time.time()

    with metrics_lock:
        task_metrics["total_scheduled"] += 1
        task_metrics["current_running"] += 1
        active_tasks[task_id] = {
            "id": task_id,
            "type": "memory_intensive",
            "status": "running",
            "start_time": start_time,
            "memory_mb": memory_mb,
            "progress": 0
        }

    try:
        # Simulate memory allocation
        data = []
        chunk_size = memory_mb // 10  # Allocate in chunks

        for i in range(10):
            if app.is_shutting_down:
                break

            # Allocate memory chunk
            chunk = [0] * (chunk_size * 1024 * 256)  # Roughly chunk_size MB
            data.append(chunk)

            with metrics_lock:
                if task_id in active_tasks:
                    active_tasks[task_id]["progress"] = (i + 1) * 10

            time.sleep(0.5)
            print(f"💾 Task {task_id} allocated {(i + 1) * chunk_size}MB")

        # Hold memory for a bit
        time.sleep(2)

        # Clean up
        del data

        completion_time = time.time() - start_time

        with metrics_lock:
            task_metrics["current_running"] -= 1
            task_metrics["total_completed"] += 1

            if task_id in active_tasks:
                task_info = active_tasks[task_id]
                task_info["status"] = "completed"
                task_info["completion_time"] = completion_time
                task_info["completed_at"] = datetime.now()
                completed_tasks.append(task_info)
                del active_tasks[task_id]

            task_metrics["last_update"] = datetime.now()

        print(f"✅ Memory task {task_id} completed, memory released")

    except Exception as e:
        with metrics_lock:
            task_metrics["current_running"] -= 1
            task_metrics["total_failed"] += 1

            if task_id in active_tasks:
                task_info = active_tasks[task_id]
                task_info["status"] = "failed"
                task_info["error"] = str(e)
                task_info["failed_at"] = datetime.now()
                completed_tasks.append(task_info)
                del active_tasks[task_id]

            task_metrics["last_update"] = datetime.now()

        print(f"❌ Memory task {task_id} failed: {e}")

def update_system_metrics():
    """Update system metrics periodically"""
    while not app.is_shutting_down:
        try:
            process = psutil.Process(os.getpid())

            with metrics_lock:
                system_metrics["cpu_usage"] = process.cpu_percent()
                system_metrics["memory_usage"] = process.memory_info().rss / 1024 / 1024  # MB
                system_metrics["task_queue_size"] = len(active_tasks)

        except Exception as e:
            print(f"❌ Error updating system metrics: {e}")

        time.sleep(5)  # Update every 5 seconds

# Start system metrics monitoring
app.add_background_task(update_system_metrics)

# Graceful shutdown handler
def graceful_shutdown():
    """Handle graceful shutdown"""
    print("🛑 Received shutdown signal, waiting for tasks to complete...")

    start_time = time.time()
    timeout = 30  # 30 seconds timeout

    while active_tasks and (time.time() - start_time) < timeout:
        remaining_tasks = len(active_tasks)
        print(f"⏳ Waiting for {remaining_tasks} tasks to complete...")
        time.sleep(1)

    if active_tasks:
        print(f"⚠️  Timeout reached, {len(active_tasks)} tasks still running")
        # Force cleanup of remaining tasks
        with metrics_lock:
            for task_id, task_info in active_tasks.items():
                task_info["status"] = "interrupted"
                task_info["interrupted_at"] = datetime.now()
                completed_tasks.append(task_info)
            active_tasks.clear()
    else:
        print("✅ All tasks completed successfully")

# Register shutdown handler
app.add_shutdown_handler(graceful_shutdown)

@app.get("/")
def home(request: Request) -> Response:
    """Home endpoint with monitoring info"""
    return JSONResponse({
        "message": "Catzilla Task Monitoring Example",
        "features": [
            "Real-time task monitoring",
            "Graceful shutdown handling",
            "Resource usage tracking",
            "Task health checking",
            "Performance metrics"
        ],
        "monitoring": {
            "active_tasks": len(active_tasks),
            "completed_tasks": len(completed_tasks)
        }
    })

@app.post("/tasks/long-running")
def start_long_running_task(request: Request) -> Response:
    """Start a long-running task for monitoring"""
    try:
        data = request.json()
        duration = data.get("duration", 10)  # Default 10 seconds

        if duration > 300:  # Max 5 minutes
            return JSONResponse({
                "error": "Duration too long",
                "max_duration": 300
            }, status_code=400)

        task_id = f"long_{int(time.time())}_{len(active_tasks)}"

        # Schedule the task
        app.add_background_task(long_running_task, task_id, duration)

        return JSONResponse({
            "message": "Long-running task started",
            "task_id": task_id,
            "duration": duration,
            "status": "scheduled"
        }, status_code=202)

    except Exception as e:
        return JSONResponse({
            "error": "Failed to start task",
            "details": str(e)
        }, status_code=400)

@app.post("/tasks/memory-intensive")
def start_memory_intensive_task(request: Request) -> Response:
    """Start a memory-intensive task for monitoring"""
    try:
        data = request.json()
        memory_mb = data.get("memory_mb", 50)  # Default 50MB

        if memory_mb > 500:  # Max 500MB
            return JSONResponse({
                "error": "Memory allocation too large",
                "max_memory_mb": 500
            }, status_code=400)

        task_id = f"memory_{int(time.time())}_{len(active_tasks)}"

        # Schedule the task
        app.add_background_task(memory_intensive_task, task_id, memory_mb)

        return JSONResponse({
            "message": "Memory-intensive task started",
            "task_id": task_id,
            "memory_mb": memory_mb,
            "status": "scheduled"
        }, status_code=202)

    except Exception as e:
        return JSONResponse({
            "error": "Failed to start task",
            "details": str(e)
        }, status_code=400)

@app.get("/monitoring/tasks")
def get_task_monitoring(request: Request) -> Response:
    """Get real-time task monitoring data"""
    with metrics_lock:
        current_active = []
        for task_id, task_info in active_tasks.items():
            task_copy = task_info.copy()
            task_copy["running_time"] = time.time() - task_info["start_time"]
            current_active.append(task_copy)

        recent_completed = completed_tasks[-10:]  # Last 10 completed tasks

        return JSONResponse({
            "metrics": task_metrics.copy(),
            "active_tasks": current_active,
            "recent_completed": recent_completed,
            "system_metrics": system_metrics.copy(),
            "timestamp": datetime.now().isoformat()
        })

@app.get("/monitoring/system")
def get_system_monitoring(request: Request) -> Response:
    """Get system resource monitoring data"""
    try:
        process = psutil.Process(os.getpid())

        return JSONResponse({
            "system_resources": {
                "cpu_percent": process.cpu_percent(),
                "memory_mb": process.memory_info().rss / 1024 / 1024,
                "memory_percent": process.memory_percent(),
                "num_threads": process.num_threads(),
                "num_fds": process.num_fds() if hasattr(process, 'num_fds') else 0
            },
            "task_stats": {
                "active_count": len(active_tasks),
                "queue_size": len(active_tasks),
                "total_scheduled": task_metrics["total_scheduled"],
                "total_completed": task_metrics["total_completed"],
                "total_failed": task_metrics["total_failed"]
            },
            "uptime_seconds": time.time() - app.start_time if hasattr(app, 'start_time') else 0,
            "timestamp": datetime.now().isoformat()
        })

    except Exception as e:
        return JSONResponse({
            "error": "Failed to get system metrics",
            "details": str(e)
        }, status_code=500)

@app.get("/monitoring/health")
def get_task_health(request: Request) -> Response:
    """Get task system health status"""
    with metrics_lock:
        # Calculate health metrics
        success_rate = 0
        if task_metrics["total_completed"] + task_metrics["total_failed"] > 0:
            success_rate = task_metrics["total_completed"] / (task_metrics["total_completed"] + task_metrics["total_failed"]) * 100

        # Check for stuck tasks (running > 5 minutes)
        stuck_tasks = []
        current_time = time.time()
        for task_id, task_info in active_tasks.items():
            if current_time - task_info["start_time"] > 300:  # 5 minutes
                stuck_tasks.append(task_id)

        health_status = "healthy"
        if stuck_tasks:
            health_status = "warning"
        elif task_metrics["current_running"] > 10:
            health_status = "warning"
        elif success_rate < 90 and task_metrics["total_completed"] > 10:
            health_status = "warning"

        return JSONResponse({
            "health_status": health_status,
            "success_rate": round(success_rate, 2),
            "stuck_tasks": stuck_tasks,
            "recommendations": [
                "Monitor task completion times",
                "Check for memory leaks in long-running tasks",
                "Implement task timeouts for better reliability"
            ] if health_status == "warning" else [],
            "metrics_summary": {
                "active_tasks": task_metrics["current_running"],
                "success_rate": round(success_rate, 2),
                "average_completion_time": round(task_metrics["average_completion_time"], 2),
                "longest_running_time": round(task_metrics["longest_running_time"], 2)
            }
        })

@app.post("/monitoring/shutdown")
def trigger_graceful_shutdown(request: Request) -> Response:
    """Trigger graceful shutdown (for testing)"""
    app.add_background_task(graceful_shutdown)

    return JSONResponse({
        "message": "Graceful shutdown initiated",
        "active_tasks": len(active_tasks),
        "estimated_completion_time": "30 seconds"
    })

@app.get("/health")
def health_check(request: Request) -> Response:
    """Health check with task monitoring status"""
    return JSONResponse({
        "status": "healthy",
        "monitoring": "enabled",
        "framework": "Catzilla v0.2.0",
        "task_system": {
            "active": len(active_tasks),
            "completed": task_metrics["total_completed"],
            "failed": task_metrics["total_failed"]
        }
    })

if __name__ == "__main__":
    print("🚨 Starting Catzilla Task Monitoring Example")
    print("📝 Available endpoints:")
    print("   GET  /                         - Home with monitoring info")
    print("   POST /tasks/long-running       - Start long-running task")
    print("   POST /tasks/memory-intensive   - Start memory-intensive task")
    print("   GET  /monitoring/tasks         - Real-time task monitoring")
    print("   GET  /monitoring/system        - System resource monitoring")
    print("   GET  /monitoring/health        - Task system health check")
    print("   POST /monitoring/shutdown      - Trigger graceful shutdown")
    print("   GET  /health                   - Health check")
    print()
    print("🎨 Features demonstrated:")
    print("   • Real-time task monitoring with metrics")
    print("   • System resource usage tracking")
    print("   • Task health checking and failure detection")
    print("   • Graceful shutdown with task completion waiting")
    print("   • Performance metrics collection")
    print()
    print("🧪 Try these examples:")
    print("   curl -X POST http://localhost:8000/tasks/long-running \\")
    print("     -H 'Content-Type: application/json' -d '{\"duration\": 15}'")
    print("   curl http://localhost:8000/monitoring/tasks")
    print("   curl http://localhost:8000/monitoring/system")
    print()

    # Set start time for uptime calculation
    app.start_time = time.time()
    app.listen(host="0.0.0.0", port=8000)
