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
from catzilla.background_tasks import TaskPriority
import time
import signal
import os
from datetime import datetime, timedelta
from typing import Dict, Any, List
import threading
import uuid

# Initialize Catzilla with monitoring enabled
app = Catzilla(
    production=False,
    show_banner=True,
    log_requests=True
)

# Enable background task system
app.enable_background_tasks(
    workers=4,
    enable_profiling=True,
    memory_pool_mb=500
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

# Global shutdown flag
shutdown_requested = False

def long_running_task(task_id: str, duration: int):
    """Simulate a long-running task for monitoring"""
    start_time = time.time()

    print(f"🔄 Starting long-running task {task_id} for {duration} seconds")

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
            if shutdown_requested:
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
        return f"Task {task_id} completed successfully"

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
        raise

def memory_intensive_task(task_id: str, memory_mb: int):
    """Simulate a memory-intensive task"""
    start_time = time.time()

    print(f"💾 Starting memory-intensive task {task_id} with {memory_mb}MB allocation")

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
        data_chunks = []
        chunk_size = 1024 * 1024  # 1MB chunks

        for i in range(memory_mb):
            if shutdown_requested:
                print(f"⏹️  Memory task {task_id} received shutdown signal, cleaning up...")
                break

            # Allocate 1MB chunk
            chunk = bytearray(chunk_size)
            data_chunks.append(chunk)

            # Update progress
            with metrics_lock:
                if task_id in active_tasks:
                    active_tasks[task_id]["progress"] = int(((i + 1) / memory_mb) * 100)

            print(f"💾 Task {task_id} allocated {i + 1}MB / {memory_mb}MB")
            time.sleep(0.1)  # Small delay to simulate work

        # Hold memory for a bit
        if not shutdown_requested:
            print(f"🔄 Task {task_id} holding {memory_mb}MB for 3 seconds...")
            time.sleep(3)

        # Release memory
        data_chunks.clear()

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
        return f"Memory task {task_id} completed with {memory_mb}MB allocation"

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
        raise

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
            if shutdown_requested:
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
    while not shutdown_requested:
        try:
            import resource
            # Get basic system metrics using resource module
            with metrics_lock:
                mem_usage = resource.getrusage(resource.RUSAGE_SELF)
                system_metrics["memory_usage"] = mem_usage.ru_maxrss / 1024  # KB to MB on Linux, already MB on macOS
                system_metrics["task_queue_size"] = len(active_tasks)
                # CPU usage not easily available without psutil, so we'll skip it

        except Exception as e:
            print(f"❌ Error updating system metrics: {e}")

        time.sleep(5)  # Update every 5 seconds

# Start system metrics monitoring in a separate thread
import threading
metrics_thread = threading.Thread(target=update_system_metrics, daemon=True)
metrics_thread.start()

# Signal handler for graceful shutdown
def signal_handler(signum, frame):
    """Handle shutdown signals"""
    global shutdown_requested
    print("🛑 Received shutdown signal, waiting for tasks to complete...")
    shutdown_requested = True

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

# Register signal handlers
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

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

        # Schedule the task using Catzilla's background task system
        task_result = app.add_task(
            long_running_task,
            task_id,
            duration,
            priority=TaskPriority.NORMAL
        )

        return JSONResponse({
            "message": "Long-running task started",
            "task_id": task_id,
            "catzilla_task_id": task_result.task_id,
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

        # Schedule the task using Catzilla's background task system
        task_result = app.add_task(
            memory_intensive_task,
            task_id,
            memory_mb,
            priority=TaskPriority.HIGH
        )

        return JSONResponse({
            "message": "Memory-intensive task started",
            "task_id": task_id,
            "catzilla_task_id": task_result.task_id,
            "memory_mb": memory_mb,
            "status": "scheduled"
        }, status_code=202)

    except Exception as e:
        return JSONResponse({
            "error": "Failed to start task",
            "details": str(e)
        }, status_code=400)

@app.get("/monitoring/catzilla-stats")
def get_catzilla_task_stats(request: Request) -> Response:
    """Get real-time Catzilla background task system statistics"""
    try:
        # Get stats from the actual Catzilla background task system
        stats = app.get_task_stats()

        return JSONResponse({
            "message": "Catzilla Background Task System Statistics",
            "engine_stats": {
                "queue_metrics": {
                    "critical_queue_size": stats.critical_queue_size,
                    "high_queue_size": stats.high_queue_size,
                    "normal_queue_size": stats.normal_queue_size,
                    "low_queue_size": stats.low_queue_size,
                    "total_queued": stats.total_queued,
                    "queue_pressure": stats.queue_pressure
                },
                "worker_metrics": {
                    "active_workers": stats.active_workers,
                    "idle_workers": stats.idle_workers,
                    "total_workers": stats.total_workers,
                    "avg_worker_utilization": stats.avg_worker_utilization,
                    "worker_cpu_usage": stats.worker_cpu_usage,
                    "worker_memory_usage": stats.worker_memory_usage
                },
                "performance_metrics": {
                    "tasks_per_second": stats.tasks_per_second,
                    "avg_execution_time_ms": stats.avg_execution_time_ms,
                    "p95_execution_time_ms": stats.p95_execution_time_ms,
                    "p99_execution_time_ms": stats.p99_execution_time_ms,
                    "memory_usage_mb": stats.memory_usage_mb,
                    "memory_efficiency": stats.memory_efficiency
                },
                "error_metrics": {
                    "failed_tasks": stats.failed_tasks,
                    "retry_count": stats.retry_count,
                    "timeout_count": stats.timeout_count,
                    "error_rate": stats.error_rate
                },
                "engine_metrics": {
                    "uptime_seconds": stats.uptime_seconds,
                    "total_tasks_processed": stats.total_tasks_processed,
                    "engine_cpu_usage": stats.engine_cpu_usage,
                    "engine_memory_usage": stats.engine_memory_usage
                }
            },
            "system_status": {
                "enabled": True,
                "configuration": {
                    "workers": 4,
                    "memory_pool_mb": 500,
                    "profiling_enabled": True
                }
            },
            "timestamp": datetime.now().isoformat()
        })

    except Exception as e:
        return JSONResponse({
            "error": "Failed to get Catzilla task stats",
            "details": str(e),
            "fallback_stats": {
                "local_monitoring": {
                    "active_tasks": len(active_tasks),
                    "completed_tasks": task_metrics["total_completed"],
                    "failed_tasks": task_metrics["total_failed"]
                }
            }
        }, status_code=500)

@app.get("/monitoring/tasks")
def get_task_monitoring(request: Request) -> Response:
    """Get real-time task monitoring data"""
    with metrics_lock:
        current_active = []
        for task_id, task_info in active_tasks.items():
            task_copy = task_info.copy()
            task_copy["running_time"] = time.time() - task_info["start_time"]
            current_active.append(task_copy)

        recent_completed = []
        for task_info in completed_tasks[-10:]:  # Last 10 completed tasks
            task_copy = task_info.copy()
            # Convert datetime objects to ISO strings
            if "completed_at" in task_copy and hasattr(task_copy["completed_at"], "isoformat"):
                task_copy["completed_at"] = task_copy["completed_at"].isoformat()
            if "failed_at" in task_copy and hasattr(task_copy["failed_at"], "isoformat"):
                task_copy["failed_at"] = task_copy["failed_at"].isoformat()
            recent_completed.append(task_copy)

        # Convert datetime in metrics to ISO string
        metrics_copy = task_metrics.copy()
        if "last_update" in metrics_copy and hasattr(metrics_copy["last_update"], "isoformat"):
            metrics_copy["last_update"] = metrics_copy["last_update"].isoformat()

        return JSONResponse({
            "metrics": metrics_copy,
            "active_tasks": current_active,
            "recent_completed": recent_completed,
            "system_metrics": system_metrics.copy(),
            "timestamp": datetime.now().isoformat()
        })

@app.get("/monitoring/system")
def get_system_monitoring(request: Request) -> Response:
    """Get system resource monitoring data"""
    try:
        import resource
        mem_usage = resource.getrusage(resource.RUSAGE_SELF)

        return JSONResponse({
            "system_resources": {
                "memory_mb": mem_usage.ru_maxrss / 1024,  # Convert to MB
                "num_threads": threading.active_count(),
                "uptime_seconds": time.time() - app.start_time if hasattr(app, 'start_time') else 0
            },
            "task_stats": {
                "active_count": len(active_tasks),
                "queue_size": len(active_tasks),
                "total_scheduled": task_metrics["total_scheduled"],
                "total_completed": task_metrics["total_completed"],
                "total_failed": task_metrics["total_failed"]
            },
            "background_task_system": {
                "enabled": app._task_system_enabled if hasattr(app, '_task_system_enabled') else False,
                "workers": 4,  # From our configuration
                "memory_pool_mb": 500  # From our configuration
            },
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
    global shutdown_requested
    shutdown_requested = True

    return JSONResponse({
        "message": "Graceful shutdown initiated",
        "active_tasks": len(active_tasks),
        "status": "shutting_down"
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
    print("   GET  /monitoring/catzilla-stats - Catzilla background task system stats")
    print("   GET  /monitoring/system        - System resource monitoring")
    print("   GET  /monitoring/health        - Task system health check")
    print("   POST /monitoring/shutdown      - Trigger graceful shutdown")
    print("   GET  /health                   - Health check")
    print()
    print("🎨 Features demonstrated:")
    print("   • Real-time task monitoring with metrics")
    print("   • Catzilla background task system integration")
    print("   • System resource usage tracking")
    print("   • Task health checking and failure detection")
    print("   • Graceful shutdown with task completion waiting")
    print("   • Performance metrics collection")
    print()
    print("🧪 Try these examples:")
    print("   curl -X POST http://localhost:8000/tasks/long-running \\")
    print("     -H 'Content-Type: application/json' -d '{\"duration\": 15}'")
    print("   curl http://localhost:8000/monitoring/catzilla-stats")
    print("   curl http://localhost:8000/monitoring/tasks")
    print("   curl http://localhost:8000/monitoring/system")
    print()

    # Set start time for uptime calculation
    app.start_time = time.time()
    app.listen(host="0.0.0.0", port=8000)
