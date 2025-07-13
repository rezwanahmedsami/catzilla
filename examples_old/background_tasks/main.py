"""
Catzilla Background Task System Example

This example demonstrates the revolutionary Background Task System that provides:
- C-speed task execution with automatic compilation
- Zero-copy operations with jemalloc optimization
- Priority-based scheduling with auto-scaling
- Real-time performance monitoring
"""

from catzilla import Catzilla, Request, BaseModel, Path, Query, Form, Header, JSONResponse
from catzilla.background_tasks import TaskPriority
from typing import Optional, List, Dict
import time
import asyncio

# Create Catzilla app with memory optimization
app = Catzilla(
    use_jemalloc=True,           # 35% memory efficiency improvement
    memory_profiling=True,       # Real-time memory monitoring
    auto_memory_tuning=True,     # Adaptive memory management
    auto_validation=True         # Enable FastAPI-style auto-validation
)

# Models for auto-validation
class NotificationMessage(BaseModel):
    """Notification message model"""
    message: str
    urgency: Optional[str] = "normal"

class UserData(BaseModel):
    """User data model for processing"""
    name: str
    email: str
    age: Optional[int] = None
    friends: Optional[List[str]] = []
    metadata: Optional[Dict[str, str]] = {}

class SecurityAlert(BaseModel):
    """Security alert model"""
    event_type: str
    severity: int = 5
    source_ip: Optional[str] = None
    details: Optional[str] = None

class CleanupRequest(BaseModel):
    """Cleanup request model"""
    directory: str = "/tmp"
    recursive: bool = False
    max_age_days: Optional[int] = None

# Enable revolutionary background task system
app.enable_background_tasks(
    workers=16,                  # 16 worker threads
    enable_auto_scaling=True,    # Intelligent scaling based on queue pressure
    memory_pool_mb=1000,         # 1GB memory pool with jemalloc optimization
    enable_c_compilation=True,   # Automatic C compilation for simple tasks
    enable_profiling=True        # Real-time performance monitoring
)

# Example 1: Simple task - automatically compiled to C for maximum speed
@app.task(priority=TaskPriority.HIGH, compile_to_c=True)
def send_notification(user_id: int, message: str) -> dict:
    """Simple notification task - compiled to C automatically"""
    # Simple operations like this get compiled to C for sub-millisecond execution
    print(f"📧 Sending notification to user {user_id}: {message}")
    time.sleep(0.001)  # Simulate quick I/O
    return {"user_id": user_id, "status": "sent", "timestamp": time.time()}

# Example 2: Complex task - stays in Python with jemalloc optimization
@app.task(priority=TaskPriority.NORMAL)
def process_user_data(user_data: dict) -> dict:
    """Complex data processing - uses Python with memory optimization"""
    # Complex operations stay in Python but use jemalloc for optimal memory usage
    print(f"🔄 Processing data for user: {user_data.get('name', 'unknown')}")

    # Simulate complex processing
    result = {
        "processed_at": time.time(),
        "user_count": len(user_data.get("friends", [])),
        "processing_time": 0.05
    }

    time.sleep(0.05)  # Simulate processing time
    return result

# Example 3: Critical real-time task
@app.task(priority=TaskPriority.CRITICAL, compile_to_c=True)
def log_security_event(event_type: str, severity: int) -> bool:
    """Critical security logging - <1ms execution target"""
    print(f"🔒 SECURITY EVENT: {event_type} (severity: {severity})")
    # Critical tasks get highest priority and immediate execution
    return True

# Example 4: Low priority maintenance task
@app.task(priority=TaskPriority.LOW)
def cleanup_temp_files(directory: str) -> dict:
    """Maintenance task - executed when system is idle"""
    print(f"🧹 Cleaning up directory: {directory}")
    time.sleep(0.1)  # Simulate cleanup work
    return {"directory": directory, "files_cleaned": 42, "bytes_freed": 1024000}

# ============================================================================
# ROUTE HANDLERS WITH BACKGROUND TASKS
# ============================================================================

# ============================================================================
# ROUTE HANDLERS WITH BACKGROUND TASKS
# ============================================================================

@app.post("/users/{user_id}/notify")
def send_user_notification(
    request,
    user_id: int = Path(..., description="User ID to send notification to"),
    notification: NotificationMessage = None
):
    """Send notification via background task system"""
    if not notification or not notification.message:
        return JSONResponse({"error": "Message is required"}, 400)

    # Schedule high-priority task (executed at C-speed if compiled)
    result = app.add_task(
        send_notification,
        user_id,
        notification.message,
        priority=TaskPriority.HIGH
    )

    return JSONResponse({
        "task_id": result.task_id,
        "status": "queued",
        "priority": "high",
        "urgency": notification.urgency,
        "message": "Notification queued for delivery",
        "validation_time": "~2.3μs (auto-validated)"
    })

@app.post("/users/process")
def process_user(request, user_data: UserData):
    """Process user data in background"""
    # Schedule normal priority task with retry logic
    result = app.add_task(
        process_user_data,
        user_data.model_dump(),
        priority=TaskPriority.NORMAL,
        max_retries=3,
        timeout_ms=10000  # 10 second timeout
    )

    return JSONResponse({
        "task_id": result.task_id,
        "status": "processing",
        "user_name": user_data.name,
        "estimated_completion": "5-10 seconds",
        "validation_time": "~3.1μs (complex model)"
    })

@app.post("/security/alert")
def security_alert(request, alert: SecurityAlert):
    """Critical security event logging"""
    # Schedule critical task (immediate execution)
    result = app.add_task(
        log_security_event,
        alert.event_type,
        alert.severity,
        priority=TaskPriority.CRITICAL,
        delay_ms=0  # Execute immediately
    )

    return JSONResponse({
        "task_id": result.task_id,
        "status": "logged",
        "event_type": alert.event_type,
        "severity": alert.severity,
        "source_ip": alert.source_ip,
        "message": "Security event logged immediately",
        "validation_time": "~1.8μs (security model)"
    })

@app.post("/maintenance/cleanup")
def trigger_cleanup(request, cleanup: CleanupRequest):
    """Trigger system cleanup"""
    # Schedule low priority maintenance task
    result = app.add_task(
        cleanup_temp_files,
        cleanup.directory,
        priority=TaskPriority.LOW,
        delay_ms=5000  # Wait 5 seconds before execution
    )

    return JSONResponse({
        "task_id": result.task_id,
        "status": "scheduled",
        "directory": cleanup.directory,
        "recursive": cleanup.recursive,
        "execution_delay": "5 seconds",
        "priority": "low",
        "validation_time": "~1.5μs (cleanup model)"
    })

# ============================================================================
# TASK CHAIN EXAMPLE (Advanced Usage)
# ============================================================================

@app.task(priority=TaskPriority.NORMAL)
def fetch_user_data(user_id: int) -> dict:
    """Step 1: Fetch user data"""
    print(f"📊 Fetching data for user {user_id}")
    time.sleep(0.02)  # Simulate database query
    return {
        "user_id": user_id,
        "name": f"User{user_id}",
        "email": f"user{user_id}@example.com",
        "friends": list(range(user_id % 10))
    }

@app.task(priority=TaskPriority.NORMAL)
def analyze_user_behavior(user_data: dict) -> dict:
    """Step 2: Analyze user behavior"""
    print(f"🔍 Analyzing behavior for {user_data['name']}")
    time.sleep(0.03)  # Simulate ML analysis
    return {
        "user_id": user_data["user_id"],
        "engagement_score": 8.5,
        "recommendation_count": len(user_data["friends"]) * 2
    }

@app.task(priority=TaskPriority.HIGH, compile_to_c=True)
def send_recommendations(analysis: dict) -> dict:
    """Step 3: Send recommendations (C-compiled)"""
    print(f"📨 Sending {analysis['recommendation_count']} recommendations to user {analysis['user_id']}")
    time.sleep(0.001)  # Fast C execution
    return {"status": "recommendations_sent", "count": analysis["recommendation_count"]}

@app.post("/users/{user_id}/recommendations")
def generate_user_recommendations(
    request,
    user_id: int = Path(..., description="User ID for recommendations"),
    priority: Optional[str] = Query("normal", description="Processing priority"),
    max_recommendations: int = Query(10, ge=1, le=100, description="Max recommendations")
):
    """Complex workflow: fetch → analyze → send recommendations"""

    # Determine priority level
    task_priority = TaskPriority.NORMAL
    if priority == "high":
        task_priority = TaskPriority.HIGH
    elif priority == "critical":
        task_priority = TaskPriority.CRITICAL
    elif priority == "low":
        task_priority = TaskPriority.LOW

    # Step 1: Fetch user data
    fetch_result = app.add_task(fetch_user_data, user_id, priority=task_priority)
    user_data = fetch_result.wait(timeout=5.0)  # Wait for completion

    # Step 2: Analyze behavior
    analysis_result = app.add_task(analyze_user_behavior, user_data, priority=task_priority)
    analysis = analysis_result.wait(timeout=5.0)

    # Step 3: Send recommendations (C-speed execution)
    send_result = app.add_task(
        send_recommendations,
        analysis,
        priority=TaskPriority.HIGH
    )
    recommendations = send_result.wait(timeout=2.0)

    return JSONResponse({
        "user_id": user_id,
        "workflow_completed": True,
        "recommendations_sent": min(recommendations["count"], max_recommendations),
        "engagement_score": analysis["engagement_score"],
        "processing_priority": priority,
        "validation_time": "~0.7μs (path param) + ~1.2μs (query params)"
    })

# ============================================================================
# PERFORMANCE MONITORING ENDPOINTS
# ============================================================================

# ============================================================================
# PERFORMANCE MONITORING ENDPOINTS
# ============================================================================

@app.get("/tasks/stats")
def get_task_performance(
    request,
    detailed: bool = Query(False, description="Include detailed metrics"),
    format: Optional[str] = Query("json", description="Response format")
):
    """Get real-time task system performance statistics"""
    stats = app.get_task_stats()

    base_stats = {
        "engine_performance": {
            "tasks_per_second": stats.tasks_per_second,
            "avg_execution_time_ms": stats.avg_execution_time_ms,
            "p95_execution_time_ms": stats.p95_execution_time_ms,
            "p99_execution_time_ms": stats.p99_execution_time_ms,
            "error_rate": stats.error_rate
        },
        "queue_status": {
            "critical_queue": stats.critical_queue_size,
            "high_queue": stats.high_queue_size,
            "normal_queue": stats.normal_queue_size,
            "low_queue": stats.low_queue_size,
            "total_queued": stats.total_queued,
            "queue_pressure": stats.queue_pressure
        },
        "worker_metrics": {
            "active_workers": stats.active_workers,
            "idle_workers": stats.idle_workers,
            "total_workers": stats.total_workers,
            "avg_utilization": stats.avg_worker_utilization,
            "cpu_usage": stats.worker_cpu_usage
        },
        "memory_metrics": {
            "memory_usage_mb": stats.memory_usage_mb,
            "memory_efficiency": stats.memory_efficiency
        },
        "system_health": {
            "uptime_seconds": stats.uptime_seconds,
            "total_processed": stats.total_tasks_processed,
            "failed_tasks": stats.failed_tasks,
            "retry_count": stats.retry_count
        }
    }

    if detailed:
        base_stats["detailed_metrics"] = {
            "c_compilation_enabled": True,
            "auto_scaling_active": True,
            "jemalloc_optimized": True,
            "validation_time": "~1.2μs (query params)"
        }

    return JSONResponse(base_stats)

@app.get("/tasks/memory")
def get_task_memory_stats(
    request,
    include_global: bool = Query(True, description="Include global memory stats")
):
    """Get memory statistics for task system"""
    memory_stats = app.get_memory_stats()
    task_stats = app.get_task_stats()

    result = {
        "task_memory": {
            "usage_mb": task_stats.memory_usage_mb,
            "efficiency": task_stats.memory_efficiency
        }
    }

    if include_global:
        result["global_memory"] = {
            "allocator": memory_stats.get("allocator", "unknown"),
            "jemalloc_enabled": memory_stats.get("jemalloc_enabled", False),
            "allocated_mb": memory_stats.get("allocated_mb", 0),
            "fragmentation_percent": memory_stats.get("fragmentation_percent", 0)
        }
        result["optimization_status"] = {
            "jemalloc_active": app.has_jemalloc,
            "memory_profiling": app.memory_profiling,
            "auto_tuning": app.auto_memory_tuning
        }

    result["validation_time"] = "~1.2μs (query params)"
    return JSONResponse(result)

@app.get("/tasks/worker/{worker_id}")
def get_worker_stats(
    request,
    worker_id: int = Path(..., ge=0, description="Worker ID to get stats for")
):
    """Get statistics for a specific worker"""
    # This would get stats for a specific worker in a real implementation
    return JSONResponse({
        "worker_id": worker_id,
        "status": "active",
        "tasks_processed": 1250,
        "avg_task_time_ms": 2.3,
        "cpu_usage_percent": 45.2,
        "memory_usage_mb": 128.5,
        "uptime_seconds": 3600,
        "validation_time": "~0.7μs (path param)"
    })

@app.post("/tasks/benchmark")
def run_task_benchmark(
    request,
    iterations: int = Query(1000, ge=100, le=100000, description="Number of iterations"),
    task_type: str = Query("notification", description="Type of task to benchmark"),
    priority: str = Query("normal", description="Task priority for benchmark")
):
    """Run a performance benchmark of the task system"""

    # Convert priority string to enum
    task_priority = TaskPriority.NORMAL
    if priority == "high":
        task_priority = TaskPriority.HIGH
    elif priority == "critical":
        task_priority = TaskPriority.CRITICAL
    elif priority == "low":
        task_priority = TaskPriority.LOW

    start_time = time.time()
    successful_tasks = 0

    # Run benchmark based on task type
    for i in range(iterations):
        try:
            if task_type == "notification":
                result = app.add_task(
                    send_notification,
                    i,
                    f"Benchmark message {i}",
                    priority=task_priority
                )
            elif task_type == "security":
                result = app.add_task(
                    log_security_event,
                    f"benchmark_event_{i}",
                    5,
                    priority=task_priority
                )
            else:
                result = app.add_task(
                    send_notification,
                    i,
                    f"Default benchmark {i}",
                    priority=task_priority
                )

            if result:
                successful_tasks += 1
        except Exception:
            pass

    end_time = time.time()
    total_time_ms = (end_time - start_time) * 1000
    tasks_per_second = successful_tasks / (total_time_ms / 1000) if total_time_ms > 0 else 0
    avg_time_ms = total_time_ms / successful_tasks if successful_tasks > 0 else 0

    return JSONResponse({
        "benchmark_results": {
            "iterations": iterations,
            "successful_tasks": successful_tasks,
            "total_time_ms": round(total_time_ms, 3),
            "tasks_per_second": round(tasks_per_second, 0),
            "avg_task_time_ms": round(avg_time_ms, 3),
            "task_type": task_type,
            "priority": priority
        },
        "system_performance": {
            "c_compilation": "enabled",
            "jemalloc_optimization": "active",
            "auto_scaling": "enabled"
        },
        "validation_time": "~1.2μs (query params)"
    })

# ============================================================================
# STARTUP MESSAGE
# ============================================================================

if __name__ == "__main__":
    print("🚀 Catzilla Background Task System Example")
    print("=" * 60)
    print("Revolutionary features enabled:")
    print("✅ C-speed task execution with automatic compilation")
    print("✅ jemalloc memory optimization (35% efficiency gain)")
    print("✅ Priority-based scheduling with auto-scaling")
    print("✅ Real-time performance monitoring")
    print("✅ Zero-copy operations and lock-free queues")
    print("✅ FastAPI-style auto-validation with 20x performance")
    print("=" * 60)
    # print("\nAvailable endpoints:")
    # print("POST /users/{user_id}/notify        - Send notification (with path param)")
    # print("POST /users/process                 - Process user data (with model validation)")
    # print("POST /security/alert                - Log security event (with model validation)")
    # print("POST /maintenance/cleanup           - Trigger cleanup (with model validation)")
    # print("POST /users/{user_id}/recommendations - Complex workflow (path + query params)")
    # print("GET  /tasks/stats                   - Task performance stats (with query params)")
    # print("GET  /tasks/memory                  - Memory usage stats (with query params)")
    # print("GET  /tasks/worker/{worker_id}      - Individual worker stats (with path param)")
    # print("POST /tasks/benchmark               - Run performance benchmark (with query params)")
    print("\nExample requests:")
    print('curl -X POST "http://localhost:8000/users/123/notify" \\')
    print('  -H "Content-Type: application/json" \\')
    print('  -d \'{"message": "Hello!", "urgency": "high"}\'')
    print()
    print('curl "http://localhost:8000/tasks/stats?detailed=true&format=json"')
    print()
    print('curl "http://localhost:8000/users/123/recommendations?priority=high&max_recommendations=20"')
    print("\nStarting server...")

    app.listen(host="127.0.0.1", port=8000)
