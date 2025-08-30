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

   from catzilla import Catzilla, JSONResponse, BaseModel
   import asyncio
   import time

   app = Catzilla()

   # Enable background task system
   app.enable_background_tasks(
       workers=4,
       enable_profiling=True,
       memory_pool_mb=500
   )

   @app.post("/start-task")
   def start_background_task(request):
       """Start a background task"""

       def long_running_task():
           """Simulate a long-running operation"""
           for i in range(10):
               time.sleep(1)  # Simulate work
               print(f"Task progress: {i+1}/10")
           return {"result": "Task completed successfully"}

       # Schedule the task
       task_id = app.add_task(long_running_task)

       return JSONResponse({
           "message": "Task started",
           "task_id": task_id,
           "status": "running"
       })

   @app.get("/task-status/{task_id}")
   def get_task_status(request, task_id: str):
       """Check task status"""
       # In a real implementation, you'd track task status
       # This is a simplified example
       return JSONResponse({
           "task_id": task_id,
           "status": "completed",
           "result": "Task finished"
       })

Async Background Tasks
~~~~~~~~~~~~~~~~~~~~~~

Background tasks with async operations:

.. code-block:: python

   import aiohttp
   import asyncio

   @app.post("/fetch-data")
   async def fetch_external_data(request):
       """Start async background task"""

       async def fetch_from_api():
           """Fetch data from external API"""
           async with aiohttp.ClientSession() as session:
               # Simulate multiple API calls
               results = []
               for i in range(5):
                   await asyncio.sleep(0.5)  # Simulate API delay
                   results.append(f"Data chunk {i+1}")

               return {"data": results, "total_items": len(results)}

       task_id = app.add_task(fetch_from_api)

       return JSONResponse({
           "message": "Async task started",
           "task_id": task_id,
           "estimated_duration": "2-3 seconds"
       })

Task Scheduling
---------------

Delayed Execution
~~~~~~~~~~~~~~~~~

Schedule tasks for future execution:

.. code-block:: python

   from datetime import datetime, timedelta

   @app.post("/schedule-reminder")
   def schedule_reminder(request):
       """Schedule a reminder task"""

       def send_reminder():
           """Send reminder notification"""
           print("📧 Sending reminder email...")
           # Simulate email sending
           time.sleep(2)
           return {"notification": "Reminder sent", "timestamp": datetime.now().isoformat()}

       # Schedule task to run in 30 seconds (Note: actual delay scheduling may vary in implementation)
       task_id = app.add_task(send_reminder)

       return JSONResponse({
           "message": "Reminder scheduled",
           "task_id": task_id,
           "scheduled_for": (datetime.now() + timedelta(seconds=30)).isoformat()
       })

Recurring Tasks
~~~~~~~~~~~~~~~

Schedule periodic tasks:

.. code-block:: python

   @app.post("/start-monitoring")
   def start_system_monitoring(request):
       """Start periodic system monitoring"""

       def check_system_health():
           """Monitor system health"""
           import psutil

           cpu_percent = psutil.cpu_percent()
           memory_percent = psutil.virtual_memory().percent

           print(f"🖥️  System Health - CPU: {cpu_percent}%, Memory: {memory_percent}%")

           return {
               "cpu_percent": cpu_percent,
               "memory_percent": memory_percent,
               "timestamp": datetime.now().isoformat()
           }

       # Schedule recurring task (Note: actual recurring implementation may vary)
       task_id = app.add_task(check_system_health)

       return JSONResponse({
           "message": "System monitoring started",
           "task_id": task_id,
           "interval": "10 seconds",
           "duration": "10 minutes"
       })

Task Monitoring
---------------

Progress Tracking
~~~~~~~~~~~~~~~~~

Track task progress with custom updates:

.. code-block:: python

   class TaskProgress:
       def __init__(self, task_id):
           self.task_id = task_id
           self.progress = 0
           self.message = "Starting..."

       def update(self, progress: int, message: str = ""):
           self.progress = progress
           self.message = message
           task_manager.update_progress(self.task_id, progress, message)

   @app.post("/process-data")
   def process_large_dataset(request):
       """Process data with progress tracking"""

       def data_processing_task(task_id):
           """Process data with progress updates"""
           progress = TaskProgress(task_id)

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
               progress.update((i + 1) * 100 // len(steps), step)
               time.sleep(1)  # Simulate processing time

           return {
               "processed_records": 1000,
               "generated_file": "report_2024.pdf",
               "processing_time": f"{len(steps)} seconds"
           }

       task_id = task_manager.schedule_with_progress(data_processing_task)

       return JSONResponse({
           "message": "Data processing started",
           "task_id": task_id,
           "progress_available": True
       })

Real-Time Task Updates
~~~~~~~~~~~~~~~~~~~~~~

Get real-time task updates:

.. code-block:: python

   @app.get("/task-progress/{task_id}")
   def get_task_progress(request, task_id: str):
       """Get detailed task progress"""
       progress_info = task_manager.get_progress(task_id)

       return JSONResponse({
           "task_id": task_id,
           "progress_percent": progress_info.get("progress", 0),
           "current_step": progress_info.get("message", "Unknown"),
           "status": progress_info.get("status", "unknown"),
           "started_at": progress_info.get("started_at"),
           "estimated_completion": progress_info.get("estimated_completion")
       })

   @app.get("/active-tasks")
   def list_active_tasks(request):
       """List all active tasks"""
       active_tasks = task_manager.get_active_tasks()

       return JSONResponse({
           "active_tasks": active_tasks,
           "total_count": len(active_tasks)
       })

Error Handling and Retry
-------------------------

Task Error Recovery
~~~~~~~~~~~~~~~~~~~

Handle task failures with retry logic:

.. code-block:: python

   @app.post("/unreliable-task")
   def start_unreliable_task(request):
       """Start task that might fail"""

       def unreliable_operation():
           """Simulate an operation that might fail"""
           import random

           if random.random() < 0.3:  # 30% chance of failure
               raise Exception("Simulated network error")

           # Simulate successful operation
           time.sleep(2)
           return {"status": "success", "data": "Operation completed"}

       # Schedule with retry configuration
       task_id = task_manager.schedule_with_retry(
           unreliable_operation,
           max_retries=3,
           retry_delay=5,  # Wait 5 seconds between retries
           backoff_multiplier=2  # Exponential backoff
       )

       return JSONResponse({
           "message": "Unreliable task started",
           "task_id": task_id,
           "max_retries": 3,
           "retry_policy": "exponential_backoff"
       })

Custom Error Handlers
~~~~~~~~~~~~~~~~~~~~~

Define custom error handling strategies:

.. code-block:: python

   def custom_error_handler(task_id: str, error: Exception, attempt: int):
       """Custom error handling for failed tasks"""
       print(f"❌ Task {task_id} failed on attempt {attempt}: {error}")

       # Log to external monitoring system
       # send_error_to_monitoring(task_id, error, attempt)

       # Decide whether to retry based on error type
       if isinstance(error, ConnectionError):
           return True  # Retry connection errors
       elif isinstance(error, ValueError):
           return False  # Don't retry validation errors
       else:
           return attempt < 2  # Retry other errors up to 2 times

   @app.post("/task-with-custom-error-handling")
   def task_with_custom_errors(request):
       """Start task with custom error handling"""

       def potentially_failing_task():
           # Simulate different types of errors
           import random
           error_type = random.choice(["connection", "validation", "unknown"])

           if error_type == "connection":
               raise ConnectionError("Failed to connect to external service")
           elif error_type == "validation":
               raise ValueError("Invalid data format")
           elif error_type == "unknown":
               raise RuntimeError("Unknown error occurred")

           return {"status": "success"}

       task_id = task_manager.schedule_with_error_handler(
           potentially_failing_task,
           error_handler=custom_error_handler
       )

       return JSONResponse({
           "message": "Task with custom error handling started",
           "task_id": task_id
       })

Production Patterns
-------------------

Task Queues and Priorities
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Manage task execution with priorities:

.. code-block:: python

   from enum import Enum

   class TaskPriority(Enum):
       LOW = 1
       NORMAL = 5
       HIGH = 10
       CRITICAL = 20

   @app.post("/priority-task")
   def schedule_priority_task(request):
       """Schedule task with specific priority"""

       def high_priority_task():
           """Critical system maintenance task"""
           print("🔧 Performing critical system maintenance...")
           time.sleep(5)
           return {"maintenance": "completed", "systems": "healthy"}

       task_id = task_manager.schedule_with_priority(
           high_priority_task,
           priority=TaskPriority.HIGH
       )

       return JSONResponse({
           "message": "High priority task scheduled",
           "task_id": task_id,
           "priority": "HIGH"
       })

   @app.post("/batch-processing")
   def schedule_batch_processing(request):
       """Schedule multiple related tasks"""

       def process_batch_item(item_id: int):
           """Process individual batch item"""
           time.sleep(1)  # Simulate processing
           return {"item_id": item_id, "processed": True}

       # Schedule multiple tasks as a batch
       batch_tasks = []
       for i in range(10):
           task_id = task_manager.schedule_with_priority(
               lambda item=i: process_batch_item(item),
               priority=TaskPriority.NORMAL
           )
           batch_tasks.append(task_id)

       return JSONResponse({
           "message": "Batch processing started",
           "batch_tasks": batch_tasks,
           "total_items": len(batch_tasks)
       })

Graceful Shutdown
~~~~~~~~~~~~~~~~~

Handle application shutdown gracefully:

.. code-block:: python

   import signal
   import sys

   def setup_graceful_shutdown():
       """Setup graceful shutdown handlers"""

       def signal_handler(signum, frame):
           print("🛑 Graceful shutdown initiated...")

           # Stop accepting new tasks
           task_manager.stop_accepting_tasks()

           # Wait for current tasks to complete (with timeout)
           task_manager.wait_for_completion(timeout=30)

           # Force stop remaining tasks
           remaining_tasks = task_manager.stop_all_tasks()
           if remaining_tasks:
               print(f"⚠️  Force stopped {len(remaining_tasks)} tasks")

           print("✅ Graceful shutdown completed")
           sys.exit(0)

       signal.signal(signal.SIGINT, signal_handler)
       signal.signal(signal.SIGTERM, signal_handler)

   # Setup graceful shutdown when app starts
   setup_graceful_shutdown()

   @app.get("/shutdown-status")
   def get_shutdown_status(request):
       """Get current shutdown status"""
       return JSONResponse({
           "accepting_new_tasks": task_manager.is_accepting_tasks(),
           "active_tasks": len(task_manager.get_active_tasks()),
           "shutdown_initiated": task_manager.is_shutdown_initiated()
       })

Task Result Storage
-------------------

Persistent Results
~~~~~~~~~~~~~~~~~~

Store and retrieve task results:

.. code-block:: python

   @app.post("/long-calculation")
   def start_calculation(request):
       """Start a calculation with persistent results"""

       def complex_calculation():
           """Perform complex mathematical calculation"""
           result = 0
           for i in range(1000000):
               result += i ** 2

           return {
               "calculation": "sum_of_squares",
               "range": "1 to 1,000,000",
               "result": result,
               "computed_at": datetime.now().isoformat()
           }

       task_id = task_manager.schedule_with_storage(
           complex_calculation,
           store_result=True,
           ttl_hours=24  # Keep result for 24 hours
       )

       return JSONResponse({
           "message": "Calculation started",
           "task_id": task_id,
           "result_available_for": "24 hours"
       })

   @app.get("/calculation-result/{task_id}")
   def get_calculation_result(request, task_id: str):
       """Retrieve stored calculation result"""
       result = task_manager.get_stored_result(task_id)

       if result is None:
           return JSONResponse({
               "error": "Result not found or expired"
           }, status_code=404)

       return JSONResponse({
           "task_id": task_id,
           "result": result,
           "retrieved_at": datetime.now().isoformat()
       })

Task Analytics
~~~~~~~~~~~~~~

Monitor task performance and metrics:

.. code-block:: python

   @app.get("/task-analytics")
   def get_task_analytics(request):
       """Get task system analytics"""
       analytics = task_manager.get_analytics()

       return JSONResponse({
           "total_tasks_executed": analytics["total_executed"],
           "successful_tasks": analytics["successful"],
           "failed_tasks": analytics["failed"],
           "average_execution_time": f"{analytics['avg_execution_time']:.2f}s",
           "current_queue_size": analytics["queue_size"],
           "peak_concurrent_tasks": analytics["peak_concurrent"],
           "uptime": f"{analytics['uptime_hours']:.1f} hours"
       })

   @app.get("/task-performance")
   def get_task_performance(request):
       """Get detailed performance metrics"""
       performance = task_manager.get_performance_metrics()

       return JSONResponse({
           "cpu_usage": performance["cpu_percent"],
           "memory_usage": performance["memory_usage_mb"],
           "active_workers": performance["active_workers"],
           "tasks_per_second": performance["throughput"],
           "error_rate": f"{performance['error_rate']:.2f}%"
       })

Best Practices
--------------

Task Design Guidelines
~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

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
   def idempotent_task(user_id, email):
       """Task can be safely retried"""
       # Check if email was already sent
       if not email_already_sent(user_id):
           send_email(email)
       return {"email_sent": True}

   # ✅ Good: Proper error handling
   def robust_task(url):
       """Task with proper error handling"""
       try:
           response = fetch_url(url)
           return {"data": response.json()}
       except ConnectionError:
           raise  # Let retry mechanism handle
       except ValueError as e:
           # Don't retry validation errors
           return {"error": str(e), "retry": False}

Performance Tips
~~~~~~~~~~~~~~~~

.. code-block:: python

   # ✅ Use async for I/O-bound tasks
   async def io_bound_task():
       async with aiohttp.ClientSession() as session:
           async with session.get("https://api.example.com") as response:
               return await response.json()

   # ✅ Use sync for CPU-bound tasks
   def cpu_bound_task(data):
       return heavy_computation(data)

   # ✅ Batch related operations
   def batch_task(items):
       """Process multiple items together"""
       results = []
       for item in items:
           results.append(process_item(item))
       return results

This comprehensive background task system enables you to build scalable, responsive applications that can handle complex workflows and long-running operations efficiently.
