Background Tasks
================

Catzilla provides a powerful background task system for executing long-running operations without blocking your API responses. Schedule tasks, monitor their progress, and handle graceful shutdowns with ease.

Overview
--------

Catzilla's background task system provides:

- **Non-Blocking Execution** - Tasks run independently of HTTP requests
- **Task Scheduling** - Schedule tasks for immediate or delayed execution
- **Progress Monitoring** - Track task status and progress in real-time
- **Graceful Shutdown** - Clean task termination on application shutdown
- **Task Queues** - Priority-based task processing
- **Persistent Storage** - Task results and state persistence
- **Error Handling** - Robust error recovery and retry mechanisms

Quick Start
-----------

Basic Background Task
~~~~~~~~~~~~~~~~~~~~~

Execute a simple background task:

.. code-block:: python

   from catzilla import Catzilla, Request, Response, JSONResponse
   import time

   app = Catzilla()

   # Enable background task system
   app.enable_background_tasks(
       workers=4,
       enable_profiling=True,
       memory_pool_mb=500
   )

   def long_running_task():
       """Simulate a long-running operation"""
       for i in range(10):
           time.sleep(1)  # Simulate work
           print(f"Task progress: {i+1}/10")
       return {"result": "Task completed successfully"}

   @app.post("/start-task")
   def start_background_task(request: Request) -> Response:
       """Start a background task"""
       # Schedule the task using Catzilla's background task system
       task_result = app.add_task(long_running_task)

       return JSONResponse({
           "message": "Task started",
           "task_id": task_result.task_id,
           "status": "scheduled"
       })

   @app.get("/")
   def home(request: Request) -> Response:
       return JSONResponse({"message": "Hello with background tasks!"})

   if __name__ == "__main__":
       print("🚀 Starting Catzilla background tasks example...")
       print("Try: curl -X POST http://localhost:8000/start-task")
       app.listen(port=8000)

Async Background Tasks
~~~~~~~~~~~~~~~~~~~~~~

Background tasks with async operations:

.. code-block:: python

   from catzilla import Catzilla, Request, Response, JSONResponse
   import asyncio
   import time

   app = Catzilla()

   # Enable background task system
   app.enable_background_tasks(
       workers=4,
       enable_profiling=True,
       memory_pool_mb=500
   )

   async def fetch_from_api():
       """Fetch data from external API"""
       # Simulate multiple API calls
       results = []
       for i in range(5):
           await asyncio.sleep(0.5)  # Simulate API delay
           results.append(f"Data chunk {i+1}")

       return {"data": results, "total_items": len(results)}

   @app.post("/fetch-data")
   def fetch_external_data(request: Request) -> Response:
       """Start async background task"""
       task_result = app.add_task(fetch_from_api)

       return JSONResponse({
           "message": "Async task started",
           "task_id": task_result.task_id,
           "estimated_duration": "2-3 seconds"
       })

   if __name__ == "__main__":
       print("🚀 Starting async background tasks example...")
       print("Try: curl -X POST http://localhost:8000/fetch-data")
       app.listen(port=8000)

Task Scheduling
---------------

Delayed Execution
~~~~~~~~~~~~~~~~~

Schedule tasks for future execution:

.. code-block:: python

   from catzilla import Catzilla, Request, Response, JSONResponse
   from catzilla.background_tasks import TaskPriority
   from datetime import datetime, timedelta
   import time

   app = Catzilla()

   # Enable background task system
   app.enable_background_tasks(workers=4)

   def send_reminder():
       """Send reminder notification"""
       print("📧 Sending reminder email...")
       # Simulate email sending
       time.sleep(2)
       return {"notification": "Reminder sent", "timestamp": datetime.now().isoformat()}

   @app.post("/schedule-reminder")
   def schedule_reminder(request: Request) -> Response:
       """Schedule a reminder task"""
       # Schedule task with priority (immediate execution)
       task_result = app.add_task(send_reminder, priority=TaskPriority.NORMAL)

       return JSONResponse({
           "message": "Reminder scheduled",
           "task_id": task_result.task_id,
           "scheduled_for": datetime.now().isoformat()
       })

   if __name__ == "__main__":
       print("🚀 Starting task scheduling example...")
       print("Try: curl -X POST http://localhost:8000/schedule-reminder")
       app.listen(port=8000)

Recurring Tasks
~~~~~~~~~~~~~~~

Schedule periodic tasks:

.. code-block:: python

   from catzilla import Catzilla, Request, Response, JSONResponse
   from datetime import datetime
   import time

   app = Catzilla()

   # Enable background task system
   app.enable_background_tasks(workers=4)

   def check_system_health():
       """Monitor system health"""
       # Simulate system health check
       cpu_percent = 25.5  # Simulated CPU usage
       memory_percent = 60.2  # Simulated memory usage

       print(f"🖥️  System Health - CPU: {cpu_percent}%, Memory: {memory_percent}%")

       return {
           "cpu_percent": cpu_percent,
           "memory_percent": memory_percent,
           "timestamp": datetime.now().isoformat()
       }

   @app.post("/start-monitoring")
   def start_system_monitoring(request: Request) -> Response:
       """Start periodic system monitoring"""
       # Schedule recurring task
       task_result = app.add_task(check_system_health)

       return JSONResponse({
           "message": "System monitoring started",
           "task_id": task_result.task_id,
           "interval": "immediate",
           "note": "For periodic tasks, schedule multiple instances or use external schedulers"
       })

   if __name__ == "__main__":
       print("🚀 Starting recurring tasks example...")
       print("Try: curl -X POST http://localhost:8000/start-monitoring")
       app.listen(port=8000)

Task Monitoring
---------------

Progress Tracking
~~~~~~~~~~~~~~~~~

Track task progress with status updates:

.. code-block:: python

   from catzilla import Catzilla, Request, Response, JSONResponse, Path
   import time
   import uuid
   from datetime import datetime
   from typing import Dict, Any

   app = Catzilla()

   # Enable background task system
   app.enable_background_tasks(workers=4)

   # Task storage for tracking (in production, use Redis or database)
   task_storage: Dict[str, Dict[str, Any]] = {}

   def data_processing_task(task_id: str):
       """Process data with progress updates"""
       task_storage[task_id] = {
           "id": task_id,
           "status": "running",
           "progress": 0,
           "started_at": datetime.now().isoformat()
       }

       try:
           # Simulate data processing steps
           steps = [
               "Loading data...",
               "Validating records...",
               "Processing batch 1/3...",
               "Processing batch 2/3...",
               "Processing batch 3/3...",
               "Generating report...",
               "Saving results..."
           ]

           for i, step in enumerate(steps):
               progress = (i + 1) * 100 // len(steps)
               task_storage[task_id].update({
                   "progress": progress,
                   "current_step": step
               })
               print(f"📊 Task {task_id}: {step} ({progress}%)")
               time.sleep(1)  # Simulate processing time

           task_storage[task_id].update({
               "status": "completed",
               "completed_at": datetime.now().isoformat(),
               "result": {
                   "processed_records": 1000,
                   "generated_file": "report_2024.pdf",
                   "processing_time": f"{len(steps)} seconds"
               }
           })

       except Exception as e:
           task_storage[task_id].update({
               "status": "failed",
               "error": str(e),
               "failed_at": datetime.now().isoformat()
           })

   @app.post("/process-data")
   def process_large_dataset(request: Request) -> Response:
       """Process data with progress tracking"""
       task_id = f"data_{uuid.uuid4().hex[:8]}"

       # Schedule the background task
       task_result = app.add_task(data_processing_task, task_id)

       return JSONResponse({
           "message": "Data processing started",
           "task_id": task_id,
           "catzilla_task_id": task_result.task_id,
           "progress_available": True
       })

   @app.get("/task-progress/{task_id}")
   def get_task_progress(request: Request, task_id: str = Path(...)) -> Response:
       """Get detailed task progress"""
       if task_id not in task_storage:
           return JSONResponse({
               "error": "Task not found"
           }, status_code=404)

       progress_info = task_storage[task_id]

       return JSONResponse({
           "task_id": task_id,
           "progress_percent": progress_info.get("progress", 0),
           "current_step": progress_info.get("current_step", "Unknown"),
           "status": progress_info.get("status", "unknown"),
           "started_at": progress_info.get("started_at"),
           "result": progress_info.get("result")
       })

   if __name__ == "__main__":
       print("🚀 Starting task progress tracking example...")
       print("Try: curl -X POST http://localhost:8000/process-data")
       print("Try: curl http://localhost:8000/task-progress/{task_id}")
       app.listen(port=8000)

Real-Time Task Updates
~~~~~~~~~~~~~~~~~~~~~~

Get real-time task updates:

.. code-block:: python

   from catzilla import Catzilla, Request, Response, JSONResponse
   from typing import Dict, Any, List

   app = Catzilla()

   # Enable background task system
   app.enable_background_tasks(workers=4)

   # Task storage for tracking
   task_storage: Dict[str, Dict[str, Any]] = {}

   @app.get("/active-tasks")
   def list_active_tasks(request: Request) -> Response:
       """List all active tasks"""
       active_tasks = [
           task for task in task_storage.values()
           if task.get("status") == "running"
       ]

       return JSONResponse({
           "active_tasks": active_tasks,
           "total_count": len(active_tasks)
       })

   @app.get("/task-stats")
   def get_task_stats(request: Request) -> Response:
       """Get Catzilla background task system statistics"""
       try:
           # Get stats from the actual Catzilla background task system
           stats = app.get_task_stats()

           return JSONResponse({
               "catzilla_stats": {
                   "queue_metrics": {
                       "critical_queue_size": stats.critical_queue_size,
                       "high_queue_size": stats.high_queue_size,
                       "normal_queue_size": stats.normal_queue_size,
                       "low_queue_size": stats.low_queue_size,
                       "total_queued": stats.total_queued
                   },
                   "worker_metrics": {
                       "active_workers": stats.active_workers,
                       "idle_workers": stats.idle_workers,
                       "total_workers": stats.total_workers
                   },
                   "performance_metrics": {
                       "tasks_per_second": stats.tasks_per_second,
                       "avg_execution_time_ms": stats.avg_execution_time_ms,
                       "memory_usage_mb": stats.memory_usage_mb
                   }
               }
           })

       except Exception as e:
           return JSONResponse({
               "error": "Failed to get Catzilla task stats",
               "details": str(e)
           }, status_code=500)

   if __name__ == "__main__":
       print("🚀 Starting real-time task updates example...")
       print("Try: curl http://localhost:8000/active-tasks")
       print("Try: curl http://localhost:8000/task-stats")
       app.listen(port=8000)

Error Handling and Retry
-------------------------

Task Error Recovery
~~~~~~~~~~~~~~~~~~~

Handle task failures with proper error handling:

.. code-block:: python

   from catzilla import Catzilla, Request, Response, JSONResponse
   from catzilla.background_tasks import TaskPriority
   import time
   import random

   app = Catzilla()

   # Enable background task system
   app.enable_background_tasks(workers=4)

   def unreliable_operation():
       """Simulate an operation that might fail"""
       if random.random() < 0.3:  # 30% chance of failure
           raise Exception("Simulated network error")

       # Simulate successful operation
       time.sleep(2)
       return {"status": "success", "data": "Operation completed"}

   @app.post("/unreliable-task")
   def start_unreliable_task(request: Request) -> Response:
       """Start task that might fail"""
       # Schedule with higher priority for important tasks
       task_result = app.add_task(
           unreliable_operation,
           priority=TaskPriority.HIGH
       )

       return JSONResponse({
           "message": "Unreliable task started",
           "task_id": task_result.task_id,
           "note": "Task may succeed or fail randomly"
       })

   if __name__ == "__main__":
       print("🚀 Starting error handling example...")
       print("Try: curl -X POST http://localhost:8000/unreliable-task")
       app.listen(port=8000)

Custom Error Handlers
~~~~~~~~~~~~~~~~~~~~~

Define custom error handling strategies:

.. code-block:: python

   from catzilla import Catzilla, Request, Response, JSONResponse
   import random

   app = Catzilla()

   # Enable background task system
   app.enable_background_tasks(workers=4)

   def potentially_failing_task():
       """Simulate different types of errors"""
       error_type = random.choice(["connection", "validation", "success"])

       if error_type == "connection":
           raise ConnectionError("Failed to connect to external service")
       elif error_type == "validation":
           raise ValueError("Invalid data format")
       elif error_type == "success":
           return {"status": "success", "message": "Task completed successfully"}

   @app.post("/task-with-error-handling")
   def task_with_custom_errors(request: Request) -> Response:
       """Start task with error handling"""
       task_result = app.add_task(potentially_failing_task)

       return JSONResponse({
           "message": "Task with error handling started",
           "task_id": task_result.task_id,
           "note": "Task may succeed or fail with different error types"
       })

   if __name__ == "__main__":
       print("🚀 Starting custom error handling example...")
       print("Try: curl -X POST http://localhost:8000/task-with-error-handling")
       app.listen(port=8000)

Production Patterns
-------------------

Task Queues and Priorities
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Manage task execution with priorities:

.. code-block:: python

   from catzilla import Catzilla, Request, Response, JSONResponse
   from catzilla.background_tasks import TaskPriority
   import time

   app = Catzilla()

   # Enable background task system
   app.enable_background_tasks(workers=4)

   def high_priority_task():
       """Critical system maintenance task"""
       print("🔧 Performing critical system maintenance...")
       time.sleep(5)
       return {"maintenance": "completed", "systems": "healthy"}

   def process_batch_item(item_id: int):
       """Process individual batch item"""
       time.sleep(1)  # Simulate processing
       return {"item_id": item_id, "processed": True}

   @app.post("/priority-task")
   def schedule_priority_task(request: Request) -> Response:
       """Schedule task with specific priority"""
       task_result = app.add_task(
           high_priority_task,
           priority=TaskPriority.HIGH
       )

       return JSONResponse({
           "message": "High priority task scheduled",
           "task_id": task_result.task_id,
           "priority": "HIGH"
       })

   @app.post("/batch-processing")
   def schedule_batch_processing(request: Request) -> Response:
       """Schedule multiple related tasks"""
       # Schedule multiple tasks as a batch
       batch_tasks = []
       for i in range(10):
           task_result = app.add_task(
               lambda item=i: process_batch_item(item),
               priority=TaskPriority.NORMAL
           )
           batch_tasks.append(task_result.task_id)

       return JSONResponse({
           "message": "Batch processing started",
           "batch_tasks": batch_tasks,
           "total_items": len(batch_tasks)
       })

   if __name__ == "__main__":
       print("🚀 Starting task priorities example...")
       print("Try: curl -X POST http://localhost:8000/priority-task")
       print("Try: curl -X POST http://localhost:8000/batch-processing")
       app.listen(port=8000)

Graceful Shutdown
~~~~~~~~~~~~~~~~~

Handle application shutdown gracefully:

.. code-block:: python

   from catzilla import Catzilla, Request, Response, JSONResponse
   import signal
   import sys
   import time

   app = Catzilla()

   # Enable background task system
   app.enable_background_tasks(workers=4)

   # Global shutdown flag
   shutdown_requested = False

   def setup_graceful_shutdown():
       """Setup graceful shutdown handlers"""
       def signal_handler(signum, frame):
           global shutdown_requested
           print("🛑 Graceful shutdown initiated...")
           shutdown_requested = True

           # Give tasks time to complete
           print("⏳ Waiting for tasks to complete...")
           time.sleep(5)  # Simple wait - in production, monitor actual task completion

           print("✅ Graceful shutdown completed")
           sys.exit(0)

       signal.signal(signal.SIGINT, signal_handler)
       signal.signal(signal.SIGTERM, signal_handler)

   # Setup graceful shutdown when app starts
   setup_graceful_shutdown()

   @app.get("/shutdown-status")
   def get_shutdown_status(request: Request) -> Response:
       """Get current shutdown status"""
       return JSONResponse({
           "shutdown_requested": shutdown_requested,
           "message": "Server is running normally" if not shutdown_requested else "Shutdown in progress"
       })

   if __name__ == "__main__":
       print("🚀 Starting graceful shutdown example...")
       print("Try: curl http://localhost:8000/shutdown-status")
       print("Press Ctrl+C to test graceful shutdown")
       app.listen(port=8000)

Task Result Storage
-------------------

Persistent Results
~~~~~~~~~~~~~~~~~~

Store and retrieve task results:

.. code-block:: python

   from catzilla import Catzilla, Request, Response, JSONResponse, Path
   from datetime import datetime
   import time
   from typing import Dict, Any

   app = Catzilla()

   # Enable background task system
   app.enable_background_tasks(workers=4)

   # Task results storage (in production, use Redis or database)
   task_results: Dict[str, Any] = {}

   def complex_calculation(task_id: str):
       """Perform complex mathematical calculation"""
       result = 0
       for i in range(1000000):
           result += i ** 2

       calculation_result = {
           "calculation": "sum_of_squares",
           "range": "1 to 1,000,000",
           "result": result,
           "computed_at": datetime.now().isoformat()
       }

       # Store result for later retrieval
       task_results[task_id] = calculation_result
       return calculation_result

   @app.post("/long-calculation")
   def start_calculation(request: Request) -> Response:
       """Start a calculation with persistent results"""
       import uuid
       task_id = f"calc_{uuid.uuid4().hex[:8]}"

       # Schedule the task
       task_result = app.add_task(complex_calculation, task_id)

       return JSONResponse({
           "message": "Calculation started",
           "task_id": task_id,
           "catzilla_task_id": task_result.task_id,
           "note": "Result will be stored for retrieval"
       })

   @app.get("/calculation-result/{task_id}")
   def get_calculation_result(request: Request, task_id: str = Path(...)) -> Response:
       """Retrieve stored calculation result"""
       if task_id not in task_results:
           return JSONResponse({
               "error": "Result not found or not yet available"
           }, status_code=404)

       return JSONResponse({
           "task_id": task_id,
           "result": task_results[task_id],
           "retrieved_at": datetime.now().isoformat()
       })

   if __name__ == "__main__":
       print("🚀 Starting task result storage example...")
       print("Try: curl -X POST http://localhost:8000/long-calculation")
       print("Try: curl http://localhost:8000/calculation-result/{task_id}")
       app.listen(port=8000)

Task Analytics
~~~~~~~~~~~~~~

Monitor task performance and metrics:

.. code-block:: python

   from catzilla import Catzilla, Request, Response, JSONResponse
   from datetime import datetime

   app = Catzilla()

   # Enable background task system
   app.enable_background_tasks(workers=4)

   @app.get("/task-analytics")
   def get_task_analytics(request: Request) -> Response:
       """Get task system analytics"""
       try:
           # Get stats from the actual Catzilla background task system
           stats = app.get_task_stats()

           return JSONResponse({
               "total_tasks_executed": stats.total_tasks_processed,
               "performance_metrics": {
                   "tasks_per_second": stats.tasks_per_second,
                   "average_execution_time_ms": stats.avg_execution_time_ms,
                   "p95_execution_time_ms": stats.p95_execution_time_ms
               },
               "queue_status": {
                   "total_queued": stats.total_queued,
                   "queue_pressure": stats.queue_pressure
               },
               "worker_status": {
                   "active_workers": stats.active_workers,
                   "total_workers": stats.total_workers,
                   "worker_utilization": stats.avg_worker_utilization
               },
               "memory_usage": {
                   "current_mb": stats.memory_usage_mb,
                   "efficiency": stats.memory_efficiency
               },
               "error_metrics": {
                   "failed_tasks": stats.failed_tasks,
                   "error_rate": stats.error_rate
               },
               "uptime_seconds": stats.uptime_seconds
           })

       except Exception as e:
           return JSONResponse({
               "error": "Failed to get analytics",
               "details": str(e)
           }, status_code=500)

   @app.get("/task-performance")
   def get_task_performance(request: Request) -> Response:
       """Get detailed performance metrics"""
       try:
           stats = app.get_task_stats()

           return JSONResponse({
               "performance_summary": {
                   "throughput": f"{stats.tasks_per_second:.2f} tasks/sec",
                   "avg_response_time": f"{stats.avg_execution_time_ms:.2f}ms",
                   "memory_efficiency": f"{stats.memory_efficiency:.1f}%",
                   "worker_utilization": f"{stats.avg_worker_utilization:.1f}%"
               },
               "detailed_metrics": {
                   "execution_times": {
                       "average_ms": stats.avg_execution_time_ms,
                       "p95_ms": stats.p95_execution_time_ms,
                       "p99_ms": stats.p99_execution_time_ms
                   },
                   "resource_usage": {
                       "cpu_usage": stats.worker_cpu_usage,
                       "memory_mb": stats.worker_memory_usage,
                       "engine_cpu": stats.engine_cpu_usage
                   }
               },
               "timestamp": datetime.now().isoformat()
           })

       except Exception as e:
           return JSONResponse({
               "error": "Failed to get performance metrics",
               "details": str(e)
           }, status_code=500)

   if __name__ == "__main__":
       print("🚀 Starting task analytics example...")
       print("Try: curl http://localhost:8000/task-analytics")
       print("Try: curl http://localhost:8000/task-performance")
       app.listen(port=8000)

Best Practices
--------------

Task Design Guidelines
~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from catzilla import Catzilla, Request, Response, JSONResponse

   app = Catzilla()
   app.enable_background_tasks(workers=4)

   # ✅ Good: Stateless tasks
   def good_task(data):
       """Process data without external dependencies"""
       return {"processed": len(data), "result": data.upper()}

   # ❌ Avoid: Tasks with external state
   global_counter = 0
   def bad_task(data):
       """Task depends on global state"""
       global global_counter
       global_counter += 1  # Race condition risk
       return {"count": global_counter}

   # ✅ Good: Idempotent tasks
   def idempotent_task(user_id: str, email: str):
       """Task can be safely retried"""
       # Check if email was already sent
       if not email_already_sent(user_id):
           send_email(email)
       return {"email_sent": True}

   # ✅ Good: Proper error handling
   def robust_task(url: str):
       """Task with proper error handling"""
       try:
           response = fetch_url(url)
           return {"data": response.json()}
       except ConnectionError:
           raise  # Let Catzilla handle connection errors
       except ValueError as e:
           # Don't retry validation errors
           return {"error": str(e), "retry": False}

   # Helper functions (would be implemented in real app)
   def email_already_sent(user_id: str) -> bool:
       return False  # Placeholder

   def send_email(email: str):
       pass  # Placeholder

   def fetch_url(url: str):
       pass  # Placeholder

   @app.post("/good-task")
   def schedule_good_task(request: Request) -> Response:
       """Schedule a well-designed task"""
       task_result = app.add_task(good_task, "sample data")
       return JSONResponse({"task_id": task_result.task_id})

   if __name__ == "__main__":
       print("🚀 Starting best practices example...")
       print("Try: curl -X POST http://localhost:8000/good-task")
       app.listen(port=8000)

Performance Tips
~~~~~~~~~~~~~~~~

.. code-block:: python

   from catzilla import Catzilla, Request, Response, JSONResponse
   from catzilla.background_tasks import TaskPriority
   import asyncio

   app = Catzilla()
   app.enable_background_tasks(workers=4)

   # ✅ Use async for I/O-bound tasks
   async def io_bound_task():
       # Simulate async I/O operation
       await asyncio.sleep(1)
       return {"result": "I/O operation completed"}

   # ✅ Use sync for CPU-bound tasks
   def cpu_bound_task(data):
       # Simulate CPU-intensive computation
       result = sum(i ** 2 for i in range(10000))
       return {"computation_result": result}

   # ✅ Batch related operations
   def batch_task(items):
       """Process multiple items together"""
       results = []
       for item in items:
           results.append(f"processed_{item}")
       return {"batch_results": results, "count": len(results)}

   @app.post("/io-task")
   def schedule_io_task(request: Request) -> Response:
       """Schedule I/O-bound task"""
       task_result = app.add_task(io_bound_task, priority=TaskPriority.NORMAL)
       return JSONResponse({"task_id": task_result.task_id, "type": "io_bound"})

   @app.post("/cpu-task")
   def schedule_cpu_task(request: Request) -> Response:
       """Schedule CPU-bound task"""
       task_result = app.add_task(cpu_bound_task, "sample_data", priority=TaskPriority.HIGH)
       return JSONResponse({"task_id": task_result.task_id, "type": "cpu_bound"})

   @app.post("/batch-task")
   def schedule_batch_task(request: Request) -> Response:
       """Schedule batch processing task"""
       items = ["item1", "item2", "item3", "item4", "item5"]
       task_result = app.add_task(batch_task, items, priority=TaskPriority.NORMAL)
       return JSONResponse({"task_id": task_result.task_id, "type": "batch", "items": len(items)})

   if __name__ == "__main__":
       print("🚀 Starting performance tips example...")
       print("Try: curl -X POST http://localhost:8000/io-task")
       print("Try: curl -X POST http://localhost:8000/cpu-task")
       print("Try: curl -X POST http://localhost:8000/batch-task")
       app.listen(port=8000)

This comprehensive background task system enables you to build scalable, responsive applications that can handle complex workflows and long-running operations efficiently.
