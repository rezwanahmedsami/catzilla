# Background Task System

Catzilla's revolutionary background task system delivers **unparalleled performance** with C-accelerated task execution, lock-free queues, and automatic Python-to-C compilation. Built for production scale with sub-millisecond task scheduling.

## Why Catzilla Background Tasks?

### ⚡ Revolutionary Performance
- **Lock-free queues** with atomic operations for maximum throughput
- **Automatic C compilation** for eligible Python tasks
- **81,466+ tasks/second** submission rate in benchmarks
- **Sub-millisecond** task scheduling latency

### 🧠 Intelligent Task Engine
- **Priority-based scheduling** (Critical, High, Normal, Low)
- **Smart auto-scaling** based on queue pressure
- **Memory-optimized** with jemalloc integration
- **Graceful shutdown** with task completion guarantees

### 🔧 Developer Experience
- **FastAPI-style decorators** for easy task definition
- **Type-safe** task parameters and return values
- **Real-time monitoring** with comprehensive statistics
- **Production-ready** error handling and retries

## 🚀 Quick Start

### Enable Background Tasks

```python
from catzilla import Catzilla, TaskPriority

# Enable background tasks with all optimizations
app = Catzilla(
    enable_background_tasks=True,
    enable_jemalloc=True  # 30% memory optimization
)

# Simple task - automatically compiled to C for speed!
def send_notification(user_id: int, message: str):
    # This function will be compiled to C automatically
    print(f"Sending to user {user_id}: {message}")
    return f"Notification sent to {user_id}"

@app.post("/notify")
def create_notification(user_id: int, message: str):
    # Schedule task with high priority
    task_result = app.add_task(
        send_notification,
        user_id,
        message,
        priority=TaskPriority.HIGH
    )

    return {
        "task_id": task_result.task_id,
        "status": "scheduled",
        "priority": "high"
    }

if __name__ == "__main__":
    app.listen(port=8000)
```

### Task Decorator Syntax

```python
from catzilla import Catzilla, TaskPriority

app = Catzilla(enable_background_tasks=True)

@app.task(priority=TaskPriority.CRITICAL, compile_to_c=True)
def process_payment(payment_id: int, amount: float):
    """Critical payment processing - compiled to C for maximum speed"""
    # Simulate payment processing
    time.sleep(0.1)
    return f"Payment {payment_id} of ${amount} processed"

@app.task(priority=TaskPriority.NORMAL)
def update_analytics(user_id: int, action: str):
    """Analytics update - auto-compiled if possible"""
    return f"Analytics updated for user {user_id}: {action}"

@app.post("/payment")
def process_payment_endpoint(payment_id: int, amount: float):
    # Use the decorated task
    task = process_payment.delay(payment_id, amount)
    return {"payment_task_id": task.task_id}
```

## 🏗️ Architecture Overview

### C-Accelerated Core

```
┌─────────────────────────────────────────────────────────┐
│                   Python Task Layer                     │
│  ┌─────────────────────────────────────────────────────┐ │
│  │    Task Definitions & Results (Python API)          │ │
│  └─────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────┐
│                 C-Accelerated Engine                    │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────────────┐ │
│  │ Lock-Free   │ │   Worker    │ │      jemalloc       │ │
│  │   Queues    │ │   Threads   │ │   Memory Pool       │ │
│  │(4 Priority) │ │(Auto-Scale) │ │  (30% Reduction)    │ │
│  └─────────────┘ └─────────────┘ └─────────────────────┘ │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────────────┐ │
│  │   Task      │ │Performance  │ │   Auto C Compiler   │ │
│  │ Execution   │ │ Monitoring  │ │  (Python → C)       │ │
│  └─────────────┘ └─────────────┘ └─────────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

### Lock-Free Queue System

Based on the C implementation in `src/core/task_system.c`:

```c
// Lock-free queue with atomic operations
typedef struct lock_free_queue {
    atomic_ptr_t head;             // Queue head pointer
    atomic_ptr_t tail;             // Queue tail pointer
    atomic_uint64_t size;          // Current queue size
    uint64_t max_size;             // Maximum capacity

    // Performance counters
    atomic_uint64_t enqueue_count;
    atomic_uint64_t dequeue_count;
    atomic_uint64_t contention_count;
} lock_free_queue_t;
```

## 📊 Documentation Structure

### Getting Started
- [Basic Usage](basic-usage.md) - Simple task examples and concepts
- [Priority Scheduling](priority-scheduling.md) - Task priorities and queue management
- [Monitoring](monitoring.md) - Performance metrics and task tracking

### Advanced Features
- [C Compilation](c-compilation.md) - Automatic Python to C compilation
- [Production Guide](production.md) - Production deployment and scaling

## 🔥 Real-World Examples

### Email Processing System

```python
from catzilla import Catzilla, BaseModel, TaskPriority
from typing import List
import time

app = Catzilla(
    enable_background_tasks=True,
    enable_jemalloc=True
)

class EmailTask(BaseModel):
    recipient: str
    subject: str
    body: str
    priority: str = "normal"

def send_email(recipient: str, subject: str, body: str):
    """Email sending - compiled to C automatically for speed"""
    # Simulate email API call
    time.sleep(0.1)
    return f"Email sent to {recipient}: {subject}"

def send_sms(phone: str, message: str):
    """SMS sending - C-compiled for performance"""
    time.sleep(0.05)
    return f"SMS sent to {phone}: {message}"

@app.post("/email/send")
def send_email_endpoint(email: EmailTask):
    priority_map = {
        "critical": TaskPriority.CRITICAL,
        "high": TaskPriority.HIGH,
        "normal": TaskPriority.NORMAL,
        "low": TaskPriority.LOW
    }

    # Schedule email task
    email_task = app.add_task(
        send_email,
        email.recipient,
        email.subject,
        email.body,
        priority=priority_map.get(email.priority, TaskPriority.NORMAL)
    )

    return {
        "task_id": email_task.task_id,
        "recipient": email.recipient,
        "priority": email.priority,
        "status": "scheduled"
    }

@app.post("/email/batch")
def send_batch_emails(emails: List[EmailTask]):
    """Send multiple emails with different priorities"""
    task_ids = []

    for email in emails:
        task = app.add_task(
            send_email,
            email.recipient,
            email.subject,
            email.body,
            priority=TaskPriority.HIGH if "urgent" in email.subject.lower()
                     else TaskPriority.NORMAL
        )
        task_ids.append(task.task_id)

    return {
        "batch_size": len(emails),
        "task_ids": task_ids,
        "estimated_completion": f"{len(emails) * 0.1:.1f} seconds"
    }
```

### Data Processing Pipeline

```python
from catzilla import Catzilla, TaskPriority
import json

app = Catzilla(enable_background_tasks=True)

def process_raw_data(data_id: int, data_chunk: str):
    """Raw data processing - auto-compiled to C"""
    # Simulate data transformation
    processed = json.loads(data_chunk)
    processed['processed_at'] = time.time()
    processed['data_id'] = data_id
    return processed

def analyze_data(processed_data: dict):
    """Data analysis - benefits from C-speed execution"""
    # Simulate complex analysis
    analysis_result = {
        'mean': sum(processed_data.get('values', [])) / len(processed_data.get('values', [1])),
        'count': len(processed_data.get('values', [])),
        'data_id': processed_data.get('data_id')
    }
    return analysis_result

def store_results(analysis_result: dict):
    """Store final results"""
    # Simulate database storage
    return f"Stored analysis for data_id {analysis_result['data_id']}"

@app.post("/data/process")
def process_data_pipeline(data_id: int, raw_data: str):
    """Chain multiple background tasks for data processing"""

    # Step 1: Process raw data (high priority)
    process_task = app.add_task(
        process_raw_data,
        data_id,
        raw_data,
        priority=TaskPriority.HIGH
    )

    # Step 2: Analyze processed data (normal priority)
    # Note: In real implementation, you'd chain these tasks
    analyze_task = app.add_task(
        analyze_data,
        {"values": [1, 2, 3, 4, 5], "data_id": data_id},
        priority=TaskPriority.NORMAL
    )

    # Step 3: Store results (low priority)
    store_task = app.add_task(
        store_results,
        {"mean": 3.0, "count": 5, "data_id": data_id},
        priority=TaskPriority.LOW
    )

    return {
        "pipeline_id": f"pipeline_{data_id}",
        "tasks": {
            "process": process_task.task_id,
            "analyze": analyze_task.task_id,
            "store": store_task.task_id
        },
        "status": "pipeline_scheduled"
    }
```

## 📈 Performance Monitoring

### Real-Time Task Statistics

```python
from catzilla import Catzilla

app = Catzilla(enable_background_tasks=True)

@app.get("/tasks/stats")
def get_task_stats():
    """Get comprehensive task system statistics"""
    stats = app.tasks.get_stats()

    return {
        "queue_stats": {
            "critical": stats.critical_queue_size,
            "high": stats.high_queue_size,
            "normal": stats.normal_queue_size,
            "low": stats.low_queue_size,
            "total_queued": stats.total_queued
        },
        "worker_stats": {
            "active_workers": stats.active_workers,
            "idle_workers": stats.idle_workers,
            "total_workers": stats.total_workers,
            "worker_utilization": f"{stats.avg_worker_utilization:.2%}"
        },
        "performance": {
            "tasks_per_second": stats.tasks_per_second,
            "avg_execution_time_ms": stats.avg_execution_time_ms,
            "p95_execution_time_ms": stats.p95_execution_time_ms,
            "memory_usage_mb": stats.memory_usage_mb,
            "memory_efficiency": f"{stats.memory_efficiency:.2%}"
        },
        "system": {
            "c_acceleration": True,
            "jemalloc_enabled": True,
            "auto_scaling": True
        }
    }

@app.get("/tasks/health")
def task_system_health():
    """Health check for task system"""
    stats = app.tasks.get_stats()

    # Health indicators
    queue_pressure = stats.total_queued / (stats.total_workers * 100)  # Rough estimate
    is_healthy = (
        stats.error_rate < 0.01 and  # Less than 1% error rate
        queue_pressure < 0.8 and     # Queue not overwhelmed
        stats.avg_worker_utilization > 0.1  # Workers are active
    )

    return {
        "healthy": is_healthy,
        "queue_pressure": f"{queue_pressure:.2%}",
        "error_rate": f"{stats.error_rate:.2%}",
        "uptime_seconds": stats.uptime_seconds,
        "total_tasks_processed": stats.total_tasks_processed
    }
```

## 🚀 Getting Started

Ready to experience revolutionary task processing?

**[Start with Basic Usage →](basic-usage.md)**

### Learning Path
1. **[Basic Usage](basic-usage.md)** - Simple tasks and core concepts
2. **[Priority Scheduling](priority-scheduling.md)** - Master task priorities
3. **[Monitoring](monitoring.md)** - Track performance and health
4. **[C Compilation](c-compilation.md)** - Automatic performance optimization
5. **[Production Guide](production.md)** - Deploy at scale

## 💡 Key Benefits

### Automatic C Compilation
- **Zero effort**: Python functions compiled automatically
- **Maximum speed**: C-level performance for eligible tasks
- **Fallback support**: Python execution when C compilation isn't possible

### Memory Optimization
- **jemalloc integration**: 30% memory reduction
- **Zero allocation**: Lock-free queue operations
- **Efficient cleanup**: Automatic memory management

### Production Ready
- **Graceful shutdown**: Wait for task completion
- **Error handling**: Comprehensive error reporting
- **Monitoring**: Real-time performance metrics
- **Scaling**: Auto-scaling worker pools

---

*Transform your background processing with C-speed execution and zero-allocation queues!* 🚀

**[Get Started Now →](basic-usage.md)**
