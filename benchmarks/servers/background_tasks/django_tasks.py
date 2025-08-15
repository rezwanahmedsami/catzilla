#!/usr/bin/env python3
"""
Django Background Tasks Benchmark Server
Advanced task queue management, processing, and monitoring
"""

import os
import sys
import json
import time
import uuid
import hashlib
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from queue import Queue, PriorityQueue, Empty
from dataclasses import dataclass, asdict
from enum import Enum
import logging
import traceback

# Django setup
import django
from django.conf import settings
from django.core.wsgi import get_wsgi_application
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.urls import path
import concurrent.futures

# Add parent directory to path for shared imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import shared utilities
try:
    from shared.background_endpoints import BACKGROUND_ENDPOINTS
    from shared.config import get_port
except ImportError:
    # Fallback if shared modules not available
    BACKGROUND_ENDPOINTS = []
    def get_port(framework, category): return 8000

# Configure Django settings
if not settings.configured:
    settings.configure(
        DEBUG=True,
        SECRET_KEY='django-benchmark-secret-key',
        ALLOWED_HOSTS=['*'],
        ROOT_URLCONF=__name__,
        USE_TZ=True,
        LOGGING={
            'version': 1,
            'disable_existing_loggers': False,
            'handlers': {
                'console': {
                    'class': 'logging.StreamHandler',
                },
            },
            'root': {
                'handlers': ['console'],
                'level': 'INFO',
            },
        }
    )

django.setup()

# Configure logging
logger = logging.getLogger(__name__)

class TaskStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    RETRYING = "retrying"

class TaskPriority(Enum):
    LOW = 3
    NORMAL = 2
    HIGH = 1
    CRITICAL = 0

@dataclass
class Task:
    id: str
    name: str
    operation: str
    params: Dict[str, Any]
    priority: TaskPriority
    status: TaskStatus
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    progress: float = 0.0
    retry_count: int = 0
    max_retries: int = 3
    timeout: Optional[float] = None

    def __lt__(self, other):
        """For priority queue comparison"""
        return self.priority.value < other.priority.value

# Global task management
task_storage: Dict[str, Task] = {}
task_queue = PriorityQueue()
active_tasks: Dict[str, threading.Thread] = {}
storage_lock = threading.Lock()

# Worker thread pool
MAX_WORKERS = 4
executor = concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS)

# Processing stats
stats = {
    'tasks_created': 0,
    'tasks_completed': 0,
    'tasks_failed': 0,
    'tasks_cancelled': 0,
    'tasks_retried': 0,
    'total_processing_time': 0.0,
    'average_processing_time': 0.0,
    'queue_size': 0,
    'active_workers': 0,
    'errors': 0
}
stats_lock = threading.Lock()

def update_stats(key: str, value: float = 1):
    """Thread-safe stats update"""
    with stats_lock:
        if key in stats:
            stats[key] += value
            if key == 'tasks_completed' and stats['tasks_completed'] > 0:
                stats['average_processing_time'] = stats['total_processing_time'] / stats['tasks_completed']

# Task Processing Functions (same as Flask version)

def process_cpu_intensive(params: Dict) -> Dict:
    """CPU-intensive task simulation"""
    iterations = params.get('iterations', 100000)
    complexity = params.get('complexity', 1.0)

    start_time = time.time()
    result = 0

    for i in range(int(iterations * complexity)):
        result += i ** 0.5
        if i % 10000 == 0:
            # Removed artificial delay for benchmarking
            pass

    processing_time = time.time() - start_time

    return {
        'result': result,
        'iterations': int(iterations * complexity),
        'processing_time': processing_time,
        'complexity': complexity
    }

def process_io_simulation(params: Dict) -> Dict:
    """I/O-intensive task simulation"""
    operations = params.get('operations', 50)
    delay_per_op = params.get('delay', 0.1)

    start_time = time.time()
    results = []

    for i in range(operations):
        # Removed artificial delay for benchmarking
        results.append({
            'operation': i + 1,
            'timestamp': time.time(),
            'data': f"result_{i}"
        })

    processing_time = time.time() - start_time

    return {
        'operations_completed': operations,
        'results': results,
        'total_delay': operations * delay_per_op,
        'processing_time': processing_time
    }

def process_data_analysis(params: Dict) -> Dict:
    """Data analysis task simulation"""
    dataset_size = params.get('size', 1000)
    analysis_type = params.get('type', 'summary')

    start_time = time.time()

    import random
    dataset = [random.randint(1, 100) for _ in range(dataset_size)]

    if analysis_type == 'summary':
        result = {
            'count': len(dataset),
            'sum': sum(dataset),
            'average': sum(dataset) / len(dataset),
            'min': min(dataset),
            'max': max(dataset)
        }
    elif analysis_type == 'histogram':
        histogram = {}
        for value in dataset:
            bucket = value // 10 * 10
            histogram[bucket] = histogram.get(bucket, 0) + 1
        result = {'histogram': histogram}
    else:
        result = {'error': f'Unknown analysis type: {analysis_type}'}

    processing_time = time.time() - start_time
    result['processing_time'] = processing_time
    result['dataset_size'] = dataset_size

    return result

def process_image_manipulation(params: Dict) -> Dict:
    """Image processing task simulation"""
    width = params.get('width', 1920)
    height = params.get('height', 1080)
    operations = params.get('operations', ['resize', 'filter', 'compress'])

    start_time = time.time()

    image_data = {
        'width': width,
        'height': height,
        'pixels': width * height,
        'size_bytes': width * height * 3
    }

    processed_operations = []
    for op in operations:
        op_start = time.time()

        if op == 'resize':
            # Removed artificial delay for benchmarking
            result_data = {'new_width': width // 2, 'new_height': height // 2}
        elif op == 'filter':
            # Removed artificial delay for benchmarking
            result_data = {'filter_applied': 'gaussian_blur', 'intensity': 0.5}
        elif op == 'compress':
            # Removed artificial delay for benchmarking
            result_data = {'compression_ratio': 0.8, 'quality': 85}
        else:
            result_data = {'error': f'Unknown operation: {op}'}

        processed_operations.append({
            'operation': op,
            'processing_time': time.time() - op_start,
            'result': result_data
        })

    processing_time = time.time() - start_time

    return {
        'original_image': image_data,
        'operations': processed_operations,
        'total_processing_time': processing_time
    }

def process_machine_learning(params: Dict) -> Dict:
    """Machine learning task simulation"""
    model_type = params.get('model', 'linear_regression')
    data_points = params.get('data_points', 1000)
    epochs = params.get('epochs', 100)

    start_time = time.time()

    import random
    training_data = [(random.random(), random.random()) for _ in range(data_points)]

    metrics = []
    for epoch in range(epochs):
        # Removed artificial delay for benchmarking

        loss = 1.0 / (epoch + 1) + random.random() * 0.1
        accuracy = min(0.99, 0.5 + (epoch / epochs) * 0.4 + random.random() * 0.1)

        if epoch % 10 == 0:
            metrics.append({
                'epoch': epoch,
                'loss': loss,
                'accuracy': accuracy
            })

    processing_time = time.time() - start_time

    return {
        'model_type': model_type,
        'data_points': data_points,
        'epochs': epochs,
        'final_loss': metrics[-1]['loss'] if metrics else None,
        'final_accuracy': metrics[-1]['accuracy'] if metrics else None,
        'training_metrics': metrics,
        'processing_time': processing_time
    }

def process_email_simulation(params: Dict) -> Dict:
    """Email sending task simulation"""
    recipients = params.get('recipients', 10)
    template_type = params.get('template', 'newsletter')
    delay_per_email = params.get('delay', 0.1)

    start_time = time.time()
    sent_emails = []
    failed_emails = []

    for i in range(recipients):
        try:
            # Removed artificial delay for benchmarking

            if i % 20 == 19:  # 5% failure rate
                failed_emails.append({
                    'recipient': f"user{i}@example.com",
                    'error': 'Invalid email address'
                })
            else:
                sent_emails.append({
                    'recipient': f"user{i}@example.com",
                    'template': template_type,
                    'sent_at': time.time()
                })
        except Exception as e:
            failed_emails.append({
                'recipient': f"user{i}@example.com",
                'error': str(e)
            })

    processing_time = time.time() - start_time

    return {
        'total_recipients': recipients,
        'emails_sent': len(sent_emails),
        'emails_failed': len(failed_emails),
        'success_rate': len(sent_emails) / recipients * 100,
        'template_type': template_type,
        'processing_time': processing_time,
        'sent_emails': sent_emails,
        'failed_emails': failed_emails
    }

# Task execution mapping
TASK_PROCESSORS = {
    'cpu_intensive': process_cpu_intensive,
    'io_simulation': process_io_simulation,
    'data_analysis': process_data_analysis,
    'image_manipulation': process_image_manipulation,
    'machine_learning': process_machine_learning,
    'email_simulation': process_email_simulation,
}

def execute_task(task: Task) -> None:
    """Execute a single task"""
    task_id = task.id

    try:
        with storage_lock:
            task.status = TaskStatus.RUNNING
            task.started_at = datetime.now()
            stats['active_workers'] += 1

        logger.info(f"Starting task {task_id}: {task.name}")

        processor = TASK_PROCESSORS.get(task.operation)
        if not processor:
            raise ValueError(f"Unknown task operation: {task.operation}")

        if task.timeout:
            start_time = time.time()

        result = processor(task.params)

        if task.timeout and (time.time() - start_time) > task.timeout:
            raise TimeoutError(f"Task timed out after {task.timeout} seconds")

        with storage_lock:
            task.status = TaskStatus.COMPLETED
            task.completed_at = datetime.now()
            task.result = result
            task.progress = 100.0

            processing_time = (task.completed_at - task.started_at).total_seconds()
            stats['active_workers'] -= 1

        update_stats('tasks_completed')
        update_stats('total_processing_time', processing_time)

        logger.info(f"Task {task_id} completed successfully")

    except Exception as e:
        error_msg = str(e)
        logger.error(f"Task {task_id} failed: {error_msg}")

        with storage_lock:
            task.error = error_msg
            task.completed_at = datetime.now()
            task.progress = 0.0
            stats['active_workers'] -= 1

            if task.retry_count < task.max_retries:
                task.retry_count += 1
                task.status = TaskStatus.RETRYING
                logger.info(f"Retrying task {task_id} (attempt {task.retry_count})")

                task_queue.put(task)
                update_stats('tasks_retried')
            else:
                task.status = TaskStatus.FAILED
                update_stats('tasks_failed')

        update_stats('errors')

    finally:
        with storage_lock:
            active_tasks.pop(task_id, None)

def worker_thread():
    """Background worker thread to process tasks"""
    while True:
        try:
            task = task_queue.get(timeout=1.0)

            with storage_lock:
                stats['queue_size'] = task_queue.qsize()

            future = executor.submit(execute_task, task)

            with storage_lock:
                active_tasks[task.id] = future

            task_queue.task_done()

        except Empty:
            continue
        except Exception as e:
            logger.error(f"Worker thread error: {e}")

# Start worker thread
worker = threading.Thread(target=worker_thread, daemon=True)
worker.start()

# Django Views

def health(request):
    """Health check endpoint"""
    return JsonResponse({
        'status': 'healthy',
        'service': 'Django Background Tasks Server',
        'timestamp': datetime.now().isoformat(),
        'stats': dict(stats),
        'queue_size': task_queue.qsize(),
        'active_tasks': len(active_tasks)
    })

@csrf_exempt
@require_http_methods(["POST"])
def create_task(request):
    """Create a new background task"""
    try:
        data = json.loads(request.body or '{}')

        operation = data.get('operation')
        if not operation or operation not in TASK_PROCESSORS:
            return JsonResponse({
                'error': 'Invalid operation',
                'available_operations': list(TASK_PROCESSORS.keys())
            }, status=400)

        task_id = str(uuid.uuid4())
        task = Task(
            id=task_id,
            name=data.get('name', f'Task {task_id[:8]}'),
            operation=operation,
            params=data.get('params', {}),
            priority=TaskPriority(data.get('priority', TaskPriority.NORMAL.value)),
            status=TaskStatus.PENDING,
            created_at=datetime.now(),
            max_retries=data.get('max_retries', 3),
            timeout=data.get('timeout')
        )

        with storage_lock:
            task_storage[task_id] = task

        task_queue.put(task)

        with storage_lock:
            stats['queue_size'] = task_queue.qsize()

        update_stats('tasks_created')

        return JsonResponse({
            'success': True,
            'task_id': task_id,
            'name': task.name,
            'operation': task.operation,
            'status': task.status.value,
            'created_at': task.created_at.isoformat(),
            'queue_position': task_queue.qsize()
        })

    except Exception as e:
        logger.error(f"Create task error: {e}")
        update_stats('errors')
        return JsonResponse({'error': str(e)}, status=500)

def get_task(request, task_id: str):
    """Get task status and details"""
    try:
        with storage_lock:
            task = task_storage.get(task_id)

        if not task:
            return JsonResponse({'error': 'Task not found'}, status=404)

        response_data = {
            'task_id': task.id,
            'name': task.name,
            'operation': task.operation,
            'status': task.status.value,
            'priority': task.priority.value,
            'progress': task.progress,
            'created_at': task.created_at.isoformat(),
            'retry_count': task.retry_count,
            'max_retries': task.max_retries
        }

        if task.started_at:
            response_data['started_at'] = task.started_at.isoformat()

        if task.completed_at:
            response_data['completed_at'] = task.completed_at.isoformat()
            response_data['processing_time'] = (task.completed_at - task.started_at).total_seconds()

        if task.result:
            response_data['result'] = task.result

        if task.error:
            response_data['error'] = task.error

        return JsonResponse(response_data)

    except Exception as e:
        logger.error(f"Get task error: {e}")
        update_stats('errors')
        return JsonResponse({'error': str(e)}, status=500)

def list_tasks(request):
    """List all tasks with filtering options"""
    try:
        status_filter = request.GET.get('status')
        limit = int(request.GET.get('limit', 100))
        offset = int(request.GET.get('offset', 0))

        with storage_lock:
            tasks = list(task_storage.values())

        if status_filter:
            try:
                status_enum = TaskStatus(status_filter)
                tasks = [t for t in tasks if t.status == status_enum]
            except ValueError:
                return JsonResponse({
                    'error': 'Invalid status filter',
                    'available_statuses': [s.value for s in TaskStatus]
                }, status=400)

        tasks.sort(key=lambda t: t.created_at, reverse=True)

        total_tasks = len(tasks)
        tasks = tasks[offset:offset + limit]

        task_list = []
        for task in tasks:
            task_data = {
                'task_id': task.id,
                'name': task.name,
                'operation': task.operation,
                'status': task.status.value,
                'priority': task.priority.value,
                'progress': task.progress,
                'created_at': task.created_at.isoformat(),
                'retry_count': task.retry_count
            }

            if task.completed_at:
                task_data['completed_at'] = task.completed_at.isoformat()
                if task.started_at:
                    task_data['processing_time'] = (task.completed_at - task.started_at).total_seconds()

            task_list.append(task_data)

        return JsonResponse({
            'total_tasks': total_tasks,
            'limit': limit,
            'offset': offset,
            'tasks': task_list
        })

    except Exception as e:
        logger.error(f"List tasks error: {e}")
        update_stats('errors')
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def cancel_task(request, task_id: str):
    """Cancel a pending or running task"""
    try:
        with storage_lock:
            task = task_storage.get(task_id)

        if not task:
            return JsonResponse({'error': 'Task not found'}, status=404)

        if task.status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]:
            return JsonResponse({'error': f'Cannot cancel task with status: {task.status.value}'}, status=400)

        with storage_lock:
            task.status = TaskStatus.CANCELLED
            task.completed_at = datetime.now()
            task.error = 'Task cancelled by user'

            future = active_tasks.get(task_id)
            if future:
                future.cancel()
                active_tasks.pop(task_id, None)
                stats['active_workers'] -= 1

        update_stats('tasks_cancelled')

        return JsonResponse({
            'success': True,
            'task_id': task_id,
            'status': task.status.value,
            'message': 'Task cancelled successfully'
        })

    except Exception as e:
        logger.error(f"Cancel task error: {e}")
        update_stats('errors')
        return JsonResponse({'error': str(e)}, status=500)

def queue_stats_view(request):
    """Get queue and processing statistics"""
    try:
        with storage_lock:
            queue_size = task_queue.qsize()
            active_count = len(active_tasks)

            status_counts = {}
            for status in TaskStatus:
                status_counts[status.value] = 0

            for task in task_storage.values():
                status_counts[task.status.value] += 1

        return JsonResponse({
            'queue_size': queue_size,
            'active_tasks': active_count,
            'max_workers': MAX_WORKERS,
            'available_workers': MAX_WORKERS - active_count,
            'status_breakdown': status_counts,
            'performance_stats': dict(stats),
            'available_operations': list(TASK_PROCESSORS.keys())
        })

    except Exception as e:
        logger.error(f"Queue stats error: {e}")
        update_stats('errors')
        return JsonResponse({'error': str(e)}, status=500)

# URL patterns
urlpatterns = [
    path('health/', health),
    path('tasks/', create_task),
    path('tasks/<str:task_id>/', get_task),
    path('tasks/', list_tasks),
    path('tasks/<str:task_id>/cancel/', cancel_task),
    path('queue/stats/', queue_stats_view),
]

application = get_wsgi_application()

if __name__ == '__main__':
    import argparse
    from django.core.management import execute_from_command_line

    parser = argparse.ArgumentParser(description='Django Background Tasks Benchmark Server')
    parser.add_argument('--port', type=int, default=None,
                        help='Port to run the server on')
    parser.add_argument('--host', type=str, default='127.0.0.1',
                        help='Host to bind the server to')
    parser.add_argument('--workers', type=int, default=4,
                        help='Number of worker threads')

    args = parser.parse_args()

    if args.workers != 4:
        MAX_WORKERS = args.workers
        executor = concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS)

    port = args.port or get_port('django', 'background_tasks')

    print(f"Starting Django Background Tasks Benchmark Server on {args.host}:{port}")
    print(f"Worker threads: {MAX_WORKERS}")
    print("Available endpoints:")
    print("  POST   /tasks/                  - Create new task")
    print("  GET    /tasks/<task_id>/        - Get task status")
    print("  GET    /tasks/                  - List all tasks")
    print("  POST   /tasks/<task_id>/cancel/ - Cancel task")
    print("  GET    /queue/stats/            - Get queue statistics")
    print("  GET    /health/                 - Health check")
    print("Available operations:", list(TASK_PROCESSORS.keys()))

    sys.argv = ['manage.py', 'runserver', f'{args.host}:{port}']
    execute_from_command_line(sys.argv)

# Create WSGI application instance for external servers like gunicorn
application = get_wsgi_application()
