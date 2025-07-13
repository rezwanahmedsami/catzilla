# 💫 Background Tasks API

Catzilla's **revolutionary background task system** with **automatic C compilation** and **lock-free queues**. Process 1M+ tasks per second with sub-millisecond latency.

## Core Classes

### BackgroundTasks

```python
from catzilla import BackgroundTasks, TaskPriority, TaskResult

class BackgroundTasks:
    """
    Revolutionary background task system with C-compiled execution.

    Features:
    - 1M+ tasks/second processing
    - Automatic C compilation for performance
    - Lock-free queue implementation
    - Priority-based scheduling
    - Atomic task state management
    - Memory-efficient task storage
    """
```

### TaskPriority Enum

```python
from enum import Enum

class TaskPriority(Enum):
    """Task execution priorities."""
    CRITICAL = 0    # Execute immediately, bypass queue
    HIGH = 1        # High priority queue
    NORMAL = 2      # Normal priority queue (default)
    LOW = 3         # Low priority queue
```

### TaskResult

```python
class TaskResult:
    """Handle for monitoring and controlling background tasks."""

    @property
    def task_id(self) -> str:
        """Unique task identifier."""

    @property
    def status(self) -> TaskStatus:
        """Current task status."""

    @property
    def priority(self) -> TaskPriority:
        """Task priority level."""

    @property
    def created_at(self) -> float:
        """Task creation timestamp."""

    @property
    def started_at(self) -> Optional[float]:
        """Task start timestamp."""

    @property
    def completed_at(self) -> Optional[float]:
        """Task completion timestamp."""
```

## BackgroundTasks Methods

### Task Creation

#### `add_task()`

```python
def add_task(
    self,
    func: Callable,
    *args,
    priority: TaskPriority = TaskPriority.NORMAL,
    delay_ms: int = 0,
    max_retries: int = 3,
    timeout_ms: int = 30000,
    compile_to_c: Optional[bool] = None,
    tags: Optional[List[str]] = None,
    metadata: Optional[Dict[str, Any]] = None,
    **kwargs
) -> TaskResult:
    """
    Add background task with automatic C compilation.

    Args:
        func: Function to execute (auto-compiled to C if possible)
        *args: Positional arguments for the function
        priority: Task execution priority
        delay_ms: Delay before execution in milliseconds
        max_retries: Maximum retry attempts on failure
        timeout_ms: Task timeout in milliseconds
        compile_to_c: Force C compilation (auto-detected if None)
        tags: Tags for task categorization and filtering
        metadata: Additional metadata for the task
        **kwargs: Keyword arguments for the function

    Returns:
        TaskResult: Task handle for monitoring and control
    """
```

**Example:**

```python
from catzilla import Catzilla, TaskPriority

app = Catzilla(enable_background_tasks=True)

# Simple background task
def send_email(to: str, subject: str, body: str):
    """This function will be automatically compiled to C"""
    print(f"Sending email to {to}: {subject}")
    # Email sending logic here
    time.sleep(0.1)  # Simulate email sending

@app.post("/send-email")
def send_email_endpoint(to: str, subject: str, body: str):
    # Add task with automatic C compilation
    task = app.add_task(send_email, to, subject, body)
    return {"task_id": task.task_id, "status": "queued"}

# High-priority task
@app.post("/urgent-notification")
def urgent_notification(message: str, user_ids: List[int]):
    task = app.add_task(
        process_urgent_notification,
        message,
        user_ids,
        priority=TaskPriority.CRITICAL,    # Execute immediately
        timeout_ms=5000,                   # 5 second timeout
        max_retries=5,                     # Retry 5 times
        tags=["notification", "urgent"],   # Tags for filtering
        metadata={"sender": "system"}      # Additional metadata
    )
    return {"urgent_task_id": task.task_id}

# Delayed task
@app.post("/schedule-reminder")
def schedule_reminder(message: str, delay_minutes: int):
    task = app.add_task(
        send_reminder,
        message,
        delay_ms=delay_minutes * 60 * 1000,  # Convert to milliseconds
        compile_to_c=True,                    # Force C compilation
        tags=["reminder", "scheduled"]
    )
    return {"reminder_task_id": task.task_id}

def process_urgent_notification(message: str, user_ids: List[int]):
    """Critical task - compiled to C for maximum speed"""
    print(f"Processing urgent notification for {len(user_ids)} users")
    for user_id in user_ids:
        # Send notification logic
        print(f"Notifying user {user_id}: {message}")

def send_reminder(message: str):
    """Reminder function - auto-compiled to C"""
    print(f"Reminder: {message}")
```

### Batch Task Operations

#### `add_batch()`

```python
def add_batch(
    self,
    tasks: List[Dict[str, Any]],
    default_priority: TaskPriority = TaskPriority.NORMAL,
    batch_size: int = 1000,
    **default_options
) -> List[TaskResult]:
    """
    Add multiple tasks efficiently with batch processing.

    Args:
        tasks: List of task definitions
        default_priority: Default priority for tasks
        batch_size: Processing batch size
        **default_options: Default options for all tasks

    Returns:
        List[TaskResult]: Task handles for all tasks
    """
```

**Example:**

```python
# Prepare batch of tasks
email_tasks = []
for user in users:
    email_tasks.append({
        "func": send_welcome_email,
        "args": (user.email, user.name),
        "priority": TaskPriority.NORMAL,
        "tags": ["welcome", "email"],
        "metadata": {"user_id": user.id}
    })

# Add all tasks efficiently
task_results = app.add_batch(
    email_tasks,
    batch_size=500,                    # Process in batches of 500
    default_priority=TaskPriority.NORMAL,
    timeout_ms=60000                   # 60 second timeout for all
)

print(f"Queued {len(task_results)} welcome email tasks")
```

### Task Monitoring

#### `wait()`

```python
def wait(
    self,
    timeout: Optional[float] = None
) -> Any:
    """
    Wait for task completion and return result.

    Args:
        timeout: Maximum wait time in seconds

    Returns:
        Any: Task result

    Raises:
        TaskTimeoutError: If task doesn't complete within timeout
        TaskExecutionError: If task execution fails
    """
```

**Example:**

```python
# Add task and wait for completion
task = app.add_task(compute_report, data_set)

try:
    result = task.wait(timeout=30.0)  # Wait up to 30 seconds
    print(f"Report completed: {result}")
except TaskTimeoutError:
    print("Task timed out")
except TaskExecutionError as e:
    print(f"Task failed: {e}")
```

#### `is_complete()`

```python
def is_complete(self) -> bool:
    """Check if task has completed (success or failure)."""

def is_successful(self) -> bool:
    """Check if task completed successfully."""

def is_failed(self) -> bool:
    """Check if task failed."""

def get_result(self) -> Any:
    """Get task result (blocks if not complete)."""

def get_error(self) -> Optional[Exception]:
    """Get task error if failed."""
```

**Example:**

```python
task = app.add_task(long_running_computation, large_dataset)

# Non-blocking status check
if task.is_complete():
    if task.is_successful():
        result = task.get_result()
        print(f"Computation result: {result}")
    else:
        error = task.get_error()
        print(f"Computation failed: {error}")
else:
    print("Task still running...")
```

### Task Management

#### `cancel()`

```python
def cancel(self) -> bool:
    """
    Cancel task execution (if not already started).

    Returns:
        bool: True if task was cancelled, False if already started/completed
    """
```

#### `retry()`

```python
def retry(
    self,
    max_retries: Optional[int] = None,
    delay_ms: int = 0
) -> TaskResult:
    """
    Retry failed task with optional parameters.

    Args:
        max_retries: Override max retries
        delay_ms: Delay before retry

    Returns:
        TaskResult: New task handle for retry
    """
```

**Example:**

```python
task = app.add_task(unreliable_api_call, endpoint, data)

# Wait a bit, then check
time.sleep(1)

if task.is_failed():
    print("Task failed, retrying...")
    retry_task = task.retry(max_retries=5, delay_ms=1000)

    # Wait for retry
    try:
        result = retry_task.wait(timeout=10)
        print(f"Retry successful: {result}")
    except TaskExecutionError:
        print("Retry also failed")
elif not task.is_complete():
    print("Cancelling slow task")
    if task.cancel():
        print("Task cancelled successfully")
```

## System Management

### Engine Statistics

#### `get_stats()`

```python
def get_stats(self) -> EngineStats:
    """
    Get comprehensive task engine statistics.

    Returns:
        EngineStats: Detailed performance and usage statistics
    """

class EngineStats:
    # Performance metrics
    tasks_processed: int                    # Total tasks processed
    tasks_per_second: float                 # Current processing rate
    average_task_time_ms: float             # Average task execution time

    # Queue metrics
    queued_tasks: int                       # Tasks currently queued
    running_tasks: int                      # Tasks currently executing
    completed_tasks: int                    # Total completed tasks
    failed_tasks: int                       # Total failed tasks

    # Priority queue metrics
    critical_queue_size: int
    high_queue_size: int
    normal_queue_size: int
    low_queue_size: int

    # Worker metrics
    active_workers: int                     # Active worker threads
    total_workers: int                      # Total worker threads
    worker_utilization: float               # Worker utilization percentage

    # C compilation metrics
    tasks_compiled_to_c: int                # Tasks compiled to C
    c_compilation_success_rate: float       # C compilation success rate
    c_speedup_factor: float                 # Average C speedup

    # Memory metrics
    memory_usage_mb: float                  # Current memory usage
    queue_memory_usage_mb: float            # Queue memory usage
    peak_memory_usage_mb: float             # Peak memory usage
```

**Example:**

```python
@app.get("/task-stats")
def get_task_statistics():
    stats = app.tasks.get_stats()

    return {
        "performance": {
            "tasks_per_second": stats.tasks_per_second,
            "average_time_ms": stats.average_task_time_ms,
            "c_speedup_factor": stats.c_speedup_factor
        },
        "queues": {
            "total_queued": stats.queued_tasks,
            "by_priority": {
                "critical": stats.critical_queue_size,
                "high": stats.high_queue_size,
                "normal": stats.normal_queue_size,
                "low": stats.low_queue_size
            }
        },
        "workers": {
            "active": stats.active_workers,
            "total": stats.total_workers,
            "utilization": f"{stats.worker_utilization:.1%}"
        },
        "compilation": {
            "tasks_compiled": stats.tasks_compiled_to_c,
            "success_rate": f"{stats.c_compilation_success_rate:.1%}"
        },
        "memory": {
            "current_mb": stats.memory_usage_mb,
            "peak_mb": stats.peak_memory_usage_mb
        }
    }

# Example output:
# {
#   "performance": {
#     "tasks_per_second": 1247000,
#     "average_time_ms": 0.8,
#     "c_speedup_factor": 127.3
#   },
#   "queues": {
#     "total_queued": 450,
#     "by_priority": {
#       "critical": 0,
#       "high": 12,
#       "normal": 380,
#       "low": 58
#     }
#   },
#   "workers": {
#     "active": 16,
#     "total": 16,
#     "utilization": "94.5%"
#   },
#   "compilation": {
#     "tasks_compiled": 234,
#     "success_rate": "87.2%"
#   },
#   "memory": {
#     "current_mb": 45.2,
#     "peak_mb": 67.8
#   }
# }
```

### System Control

#### `shutdown()`

```python
def shutdown(
    self,
    wait_for_completion: bool = True,
    timeout: float = 30.0,
    cancel_pending: bool = False
) -> None:
    """
    Graceful shutdown of task engine.

    Args:
        wait_for_completion: Wait for running tasks to complete
        timeout: Maximum wait time for completion
        cancel_pending: Cancel pending tasks in queue
    """
```

#### `pause()` / `resume()`

```python
def pause(self) -> None:
    """Pause task processing (current tasks continue)."""

def resume(self) -> None:
    """Resume task processing."""

def is_paused(self) -> bool:
    """Check if task processing is paused."""
```

**Example:**

```python
# Pause task processing for maintenance
app.tasks.pause()
print("Task processing paused")

# Perform maintenance
perform_system_maintenance()

# Resume processing
app.tasks.resume()
print("Task processing resumed")

# Graceful shutdown
@app.on_event("shutdown")
def shutdown_tasks():
    print("Shutting down task engine...")
    app.tasks.shutdown(
        wait_for_completion=True,
        timeout=60.0,                   # Wait up to 60 seconds
        cancel_pending=True             # Cancel pending tasks
    )
    print("Task engine shutdown complete")
```

## Task Filtering and Querying

### Task Queries

```python
def get_tasks(
    self,
    status: Optional[TaskStatus] = None,
    priority: Optional[TaskPriority] = None,
    tags: Optional[List[str]] = None,
    limit: int = 100
) -> List[TaskResult]:
    """
    Query tasks by criteria.

    Args:
        status: Filter by task status
        priority: Filter by priority
        tags: Filter by tags (AND operation)
        limit: Maximum results to return

    Returns:
        List[TaskResult]: Matching task handles
    """

def get_task_by_id(self, task_id: str) -> Optional[TaskResult]:
    """Get task by ID."""

def count_tasks(
    self,
    status: Optional[TaskStatus] = None,
    priority: Optional[TaskPriority] = None
) -> int:
    """Count tasks matching criteria."""
```

**Example:**

```python
# Get all running tasks
running_tasks = app.tasks.get_tasks(status=TaskStatus.RUNNING)
print(f"Currently running: {len(running_tasks)} tasks")

# Get high priority tasks
high_priority_tasks = app.tasks.get_tasks(priority=TaskPriority.HIGH)

# Get tasks by tags
email_tasks = app.tasks.get_tasks(tags=["email"])
urgent_tasks = app.tasks.get_tasks(tags=["urgent", "notification"])

# Count failed tasks
failed_count = app.tasks.count_tasks(status=TaskStatus.FAILED)
print(f"Failed tasks: {failed_count}")

# Find specific task
task = app.tasks.get_task_by_id("task_123456")
if task:
    print(f"Task status: {task.status}")
```

## Advanced Features

### Task Chaining

```python
def chain_tasks(
    self,
    tasks: List[Callable],
    chain_on_success: bool = True,
    stop_on_failure: bool = True
) -> TaskResult:
    """
    Chain multiple tasks for sequential execution.

    Args:
        tasks: List of functions to execute in sequence
        chain_on_success: Only continue if previous task succeeds
        stop_on_failure: Stop chain if any task fails

    Returns:
        TaskResult: Handle for the entire chain
    """
```

**Example:**

```python
# Chain of data processing tasks
def download_data(url: str) -> str:
    print(f"Downloading from {url}")
    return "downloaded_file.json"

def process_data(filename: str) -> dict:
    print(f"Processing {filename}")
    return {"processed": True, "records": 1000}

def send_report(result: dict) -> None:
    print(f"Sending report: {result}")

# Create task chain
chain_task = app.tasks.chain_tasks([
    lambda: download_data("https://api.example.com/data"),
    lambda data: process_data(data),
    lambda result: send_report(result)
], stop_on_failure=True)

# Monitor chain progress
result = chain_task.wait(timeout=120)
print(f"Chain completed: {result}")
```

### Parallel Task Execution

```python
def parallel_tasks(
    self,
    tasks: List[Callable],
    wait_for_all: bool = True,
    max_parallelism: Optional[int] = None
) -> List[TaskResult]:
    """
    Execute multiple tasks in parallel.

    Args:
        tasks: List of functions to execute
        wait_for_all: Wait for all tasks to complete
        max_parallelism: Limit concurrent tasks

    Returns:
        List[TaskResult]: Handles for all parallel tasks
    """
```

**Example:**

```python
# Parallel data processing
def process_chunk(chunk_id: int, data: List[dict]) -> dict:
    print(f"Processing chunk {chunk_id}")
    # Process data chunk
    return {"chunk_id": chunk_id, "processed": len(data)}

# Split data into chunks
chunks = [data[i:i+1000] for i in range(0, len(data), 1000)]

# Process chunks in parallel
parallel_tasks = []
for i, chunk in enumerate(chunks):
    parallel_tasks.append(lambda c=chunk, idx=i: process_chunk(idx, c))

# Execute in parallel (auto-compiled to C)
task_results = app.tasks.parallel_tasks(
    parallel_tasks,
    max_parallelism=8,          # Limit to 8 concurrent tasks
    wait_for_all=False          # Don't wait, return immediately
)

# Wait for all to complete
results = []
for task in task_results:
    result = task.wait()
    results.append(result)

print(f"Processed {len(results)} chunks in parallel")
```

## C Compilation Features

### Auto-Compilation

```python
# Functions are automatically analyzed for C compilation
def fast_computation(numbers: List[int]) -> int:
    """
    This function will be automatically compiled to C because:
    - Simple control flow
    - Basic data types
    - No complex Python features
    """
    total = 0
    for num in numbers:
        if num > 0:
            total += num * 2
    return total

# Add task - automatically compiled to C
task = app.add_task(fast_computation, list(range(1000000)))
```

### Manual C Compilation Control

```python
def complex_function(data: dict) -> str:
    """Complex function that might not auto-compile"""
    # Complex logic here
    return "result"

# Force C compilation attempt
task = app.add_task(
    complex_function,
    {"key": "value"},
    compile_to_c=True          # Force compilation attempt
)

# Disable C compilation
task = app.add_task(
    debug_function,
    debug_data,
    compile_to_c=False         # Use Python interpreter
)
```

### Compilation Statistics

```python
def get_compilation_info(func: Callable) -> dict:
    """Get C compilation info for a function."""

# Check if function can be compiled
info = app.tasks.get_compilation_info(fast_computation)
# {
#   "can_compile": True,
#   "estimated_speedup": 150.0,
#   "compilation_time_ms": 12,
#   "memory_usage": "minimal"
# }
```

## Complete Example

```python
from catzilla import (
    Catzilla, TaskPriority, TaskResult, BaseModel
)
from typing import List, Dict, Any
import time
import asyncio

# Create app with background tasks enabled
app = Catzilla(
    enable_background_tasks=True,
    task_workers=16,                    # 16 worker threads
    task_queue_size=50000,              # Large queue
    enable_task_c_compilation=True      # Auto C compilation
)

# Data models
class ProcessingJob(BaseModel):
    job_id: str
    data: List[dict]
    priority: str = "normal"
    options: Dict[str, Any] = {}

class JobStatus(BaseModel):
    job_id: str
    status: str
    progress: float
    result: Any = None
    error: str = None

# Background task functions (auto-compiled to C)
def process_data_chunk(chunk_id: int, data: List[dict], options: dict) -> dict:
    """Process data chunk - compiled to C for maximum speed"""
    print(f"Processing chunk {chunk_id} with {len(data)} records")

    # Simulate processing
    processed = 0
    for record in data:
        # Complex processing logic here
        if record.get("valid", True):
            processed += 1

    return {
        "chunk_id": chunk_id,
        "processed_records": processed,
        "success": True
    }

def send_notification(user_id: int, message: str, priority: str = "normal") -> bool:
    """Send notification - auto-compiled to C"""
    print(f"Sending {priority} notification to user {user_id}: {message}")

    # Notification logic here
    time.sleep(0.01)  # Simulate network call
    return True

def generate_report(job_id: str, results: List[dict]) -> str:
    """Generate final report"""
    total_processed = sum(r.get("processed_records", 0) for r in results)

    report = f"""
    Job Report: {job_id}
    Total Records Processed: {total_processed}
    Total Chunks: {len(results)}
    Success Rate: {len([r for r in results if r.get('success')]) / len(results):.1%}
    """

    return report

# Job storage (in production, use a database)
jobs: Dict[str, Dict[str, Any]] = {}

@app.post("/jobs")
def create_processing_job(request, job: ProcessingJob) -> JobStatus:
    """Create a new data processing job"""

    # Store job info
    jobs[job.job_id] = {
        "status": "processing",
        "progress": 0.0,
        "task_ids": [],
        "chunk_results": []
    }

    # Split data into chunks for parallel processing
    chunk_size = 1000
    chunks = [job.data[i:i+chunk_size] for i in range(0, len(job.data), chunk_size)]

    # Determine priority
    priority_map = {
        "critical": TaskPriority.CRITICAL,
        "high": TaskPriority.HIGH,
        "normal": TaskPriority.NORMAL,
        "low": TaskPriority.LOW
    }
    task_priority = priority_map.get(job.priority, TaskPriority.NORMAL)

    # Create parallel processing tasks
    chunk_tasks = []
    for i, chunk in enumerate(chunks):
        task = app.add_task(
            process_data_chunk,
            i,
            chunk,
            job.options,
            priority=task_priority,
            tags=["data_processing", f"job_{job.job_id}"],
            metadata={"job_id": job.job_id, "chunk_id": i}
        )
        chunk_tasks.append(task)

    jobs[job.job_id]["task_ids"] = [t.task_id for t in chunk_tasks]

    # Create completion handler task
    completion_task = app.add_task(
        handle_job_completion,
        job.job_id,
        [t.task_id for t in chunk_tasks],
        delay_ms=1000,  # Check after 1 second
        priority=TaskPriority.HIGH
    )

    return JobStatus(
        job_id=job.job_id,
        status="processing",
        progress=0.0
    )

def handle_job_completion(job_id: str, task_ids: List[str]):
    """Handle job completion - monitors chunk tasks"""
    job_info = jobs.get(job_id)
    if not job_info:
        return

    # Check if all chunk tasks are complete
    completed_tasks = []
    for task_id in task_ids:
        task = app.tasks.get_task_by_id(task_id)
        if task and task.is_complete():
            if task.is_successful():
                result = task.get_result()
                completed_tasks.append(result)
            else:
                # Handle task failure
                print(f"Task {task_id} failed: {task.get_error()}")

    # Update progress
    progress = len(completed_tasks) / len(task_ids)
    job_info["progress"] = progress

    if progress >= 1.0:
        # All tasks complete - generate report
        report_task = app.add_task(
            generate_report,
            job_id,
            completed_tasks,
            priority=TaskPriority.HIGH,
            tags=["report_generation", f"job_{job_id}"]
        )

        # Update job status
        job_info["status"] = "generating_report"
        job_info["chunk_results"] = completed_tasks

        # Send completion notification
        app.add_task(
            send_notification,
            1,  # Admin user ID
            f"Job {job_id} completed processing",
            "high",
            priority=TaskPriority.HIGH
        )
    else:
        # Reschedule completion check
        app.add_task(
            handle_job_completion,
            job_id,
            task_ids,
            delay_ms=2000,  # Check again in 2 seconds
            priority=TaskPriority.NORMAL
        )

@app.get("/jobs/{job_id}")
def get_job_status(request, job_id: str) -> JobStatus:
    """Get job processing status"""
    job_info = jobs.get(job_id)
    if not job_info:
        raise HTTPException(status_code=404, detail="Job not found")

    return JobStatus(
        job_id=job_id,
        status=job_info["status"],
        progress=job_info["progress"]
    )

@app.get("/stats/tasks")
def get_task_stats():
    """Get comprehensive task system statistics"""
    stats = app.tasks.get_stats()

    return {
        "performance": {
            "tasks_per_second": stats.tasks_per_second,
            "average_execution_time_ms": stats.average_task_time_ms,
            "c_compilation_speedup": f"{stats.c_speedup_factor:.1f}x"
        },
        "queues": {
            "total_queued": stats.queued_tasks,
            "by_priority": {
                "critical": stats.critical_queue_size,
                "high": stats.high_queue_size,
                "normal": stats.normal_queue_size,
                "low": stats.low_queue_size
            }
        },
        "execution": {
            "running_tasks": stats.running_tasks,
            "completed_tasks": stats.completed_tasks,
            "failed_tasks": stats.failed_tasks,
            "success_rate": f"{(stats.completed_tasks / (stats.completed_tasks + stats.failed_tasks) * 100):.1f}%" if (stats.completed_tasks + stats.failed_tasks) > 0 else "N/A"
        },
        "workers": {
            "active_workers": stats.active_workers,
            "total_workers": stats.total_workers,
            "utilization_percentage": f"{stats.worker_utilization:.1f}%"
        },
        "compilation": {
            "tasks_compiled_to_c": stats.tasks_compiled_to_c,
            "compilation_success_rate": f"{stats.c_compilation_success_rate:.1f}%"
        },
        "memory": {
            "current_usage_mb": stats.memory_usage_mb,
            "queue_memory_mb": stats.queue_memory_usage_mb,
            "peak_usage_mb": stats.peak_memory_usage_mb
        }
    }

@app.post("/admin/tasks/pause")
def pause_task_processing():
    """Pause task processing for maintenance"""
    app.tasks.pause()
    return {"message": "Task processing paused"}

@app.post("/admin/tasks/resume")
def resume_task_processing():
    """Resume task processing"""
    app.tasks.resume()
    return {"message": "Task processing resumed"}

# Example usage
if __name__ == "__main__":
    # Create sample processing job
    sample_job = ProcessingJob(
        job_id="job_001",
        data=[{"id": i, "value": f"data_{i}", "valid": True} for i in range(10000)],
        priority="high",
        options={"validation": True, "format": "json"}
    )

    print("Starting Catzilla with background task processing...")
    print(f"Task workers: 16")
    print(f"Queue size: 50,000")
    print(f"C compilation: Enabled")

    app.listen(port=8000)
```

---

*Process 1M+ tasks per second with automatic C compilation!* ⚡
