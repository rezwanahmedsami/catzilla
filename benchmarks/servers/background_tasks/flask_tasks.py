#!/usr/bin/env python3
"""
Flask Background Tasks Benchmark Server
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
from typing import Dict, List, Optional, Any, Callable
from queue import Queue, PriorityQueue, Empty
from dataclasses import dataclass, asdict
from enum import Enum
import logging
import traceback

# Add parent directory to path for shared imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask, request, jsonify
import concurrent.futures

# Import shared utilities
try:
    from shared.background_endpoints import BACKGROUND_ENDPOINTS
    from shared.config import get_port
except ImportError:
    # Fallback if shared modules not available
    BACKGROUND_ENDPOINTS = []
    def get_port(framework, category): return 8000

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Flask app configuration
app = Flask(__name__)
app.config['SECRET_KEY'] = 'benchmark-secret-key'

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

# Task Processing Functions

def process_cpu_intensive(params: Dict) -> Dict:
    """CPU-intensive task simulation"""
    iterations = params.get('iterations', 100000)
    complexity = params.get('complexity', 1.0)

    start_time = time.time()
    result = 0

    for i in range(int(iterations * complexity)):
        result += i ** 0.5
        if i % 10000 == 0:
            # Simulate progress updates
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
        # Simulate I/O delay
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

    # Generate mock dataset
    import random
    dataset = [random.randint(1, 100) for _ in range(dataset_size)]

    # Perform analysis
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

    # Simulate image processing
    image_data = {
        'width': width,
        'height': height,
        'pixels': width * height,
        'size_bytes': width * height * 3  # RGB
    }

    processed_operations = []
    for op in operations:
        op_start = time.time()

        # Simulate processing time based on operation
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

    # Generate training data
    import random
    training_data = [(random.random(), random.random()) for _ in range(data_points)]

    # Simulate training
    metrics = []
    for epoch in range(epochs):
        # Simulate training step
        # Removed artificial delay for benchmarking

        # Mock metrics
        loss = 1.0 / (epoch + 1) + random.random() * 0.1
        accuracy = min(0.99, 0.5 + (epoch / epochs) * 0.4 + random.random() * 0.1)

        if epoch % 10 == 0:  # Save metrics every 10 epochs
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
            # Simulate email sending delay
            # Removed artificial delay for benchmarking

            # Simulate occasional failures
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

        # Get processor function
        processor = TASK_PROCESSORS.get(task.operation)
        if not processor:
            raise ValueError(f"Unknown task operation: {task.operation}")

        # Set timeout if specified
        if task.timeout:
            # Note: This is a simplified timeout implementation
            # In production, you might want to use more sophisticated timeout handling
            start_time = time.time()

        # Execute the task
        result = processor(task.params)

        # Check timeout
        if task.timeout and (time.time() - start_time) > task.timeout:
            raise TimeoutError(f"Task timed out after {task.timeout} seconds")

        # Update task with success
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

            # Check if we should retry
            if task.retry_count < task.max_retries:
                task.retry_count += 1
                task.status = TaskStatus.RETRYING
                logger.info(f"Retrying task {task_id} (attempt {task.retry_count})")

                # Re-queue the task
                task_queue.put(task)
                update_stats('tasks_retried')
            else:
                task.status = TaskStatus.FAILED
                update_stats('tasks_failed')

        update_stats('errors')

    finally:
        # Remove from active tasks
        with storage_lock:
            active_tasks.pop(task_id, None)

def worker_thread():
    """Background worker thread to process tasks"""
    while True:
        try:
            # Get task from queue (blocks until available)
            task = task_queue.get(timeout=1.0)

            with storage_lock:
                stats['queue_size'] = task_queue.qsize()

            # Submit task to thread pool
            future = executor.submit(execute_task, task)

            with storage_lock:
                active_tasks[task.id] = future

            task_queue.task_done()

        except Empty:
            # No tasks available, continue loop
            continue
        except Exception as e:
            logger.error(f"Worker thread error: {e}")

# Start worker thread
worker = threading.Thread(target=worker_thread, daemon=True)
worker.start()

# HTTP Routes

@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'Flask Background Tasks Server',
        'timestamp': datetime.now().isoformat(),
        'stats': dict(stats),
        'queue_size': task_queue.qsize(),
        'active_tasks': len(active_tasks)
    })

@app.route('/tasks', methods=['POST'])
def create_task():
    """Create a new background task"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'JSON data required'}), 400

        # Validate required fields
        operation = data.get('operation')
        if not operation or operation not in TASK_PROCESSORS:
            return jsonify({
                'error': 'Invalid operation',
                'available_operations': list(TASK_PROCESSORS.keys())
            }), 400

        # Create task
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

        # Store task
        with storage_lock:
            task_storage[task_id] = task

        # Add to queue
        task_queue.put(task)

        with storage_lock:
            stats['queue_size'] = task_queue.qsize()

        update_stats('tasks_created')

        return jsonify({
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
        return jsonify({'error': str(e)}), 500

@app.route('/tasks/<task_id>')
def get_task(task_id: str):
    """Get task status and details"""
    try:
        with storage_lock:
            task = task_storage.get(task_id)

        if not task:
            return jsonify({'error': 'Task not found'}), 404

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

        return jsonify(response_data)

    except Exception as e:
        logger.error(f"Get task error: {e}")
        update_stats('errors')
        return jsonify({'error': str(e)}), 500

@app.route('/tasks')
def list_tasks():
    """List all tasks with filtering options"""
    try:
        status_filter = request.args.get('status')
        limit = int(request.args.get('limit', 100))
        offset = int(request.args.get('offset', 0))

        with storage_lock:
            tasks = list(task_storage.values())

        # Apply status filter
        if status_filter:
            try:
                status_enum = TaskStatus(status_filter)
                tasks = [t for t in tasks if t.status == status_enum]
            except ValueError:
                return jsonify({
                    'error': 'Invalid status filter',
                    'available_statuses': [s.value for s in TaskStatus]
                }), 400

        # Sort by creation time (newest first)
        tasks.sort(key=lambda t: t.created_at, reverse=True)

        # Apply pagination
        total_tasks = len(tasks)
        tasks = tasks[offset:offset + limit]

        # Format response
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

        return jsonify({
            'total_tasks': total_tasks,
            'limit': limit,
            'offset': offset,
            'tasks': task_list
        })

    except Exception as e:
        logger.error(f"List tasks error: {e}")
        update_stats('errors')
        return jsonify({'error': str(e)}), 500

@app.route('/tasks/<task_id>/cancel', methods=['POST'])
def cancel_task(task_id: str):
    """Cancel a pending or running task"""
    try:
        with storage_lock:
            task = task_storage.get(task_id)

        if not task:
            return jsonify({'error': 'Task not found'}), 404

        if task.status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]:
            return jsonify({'error': f'Cannot cancel task with status: {task.status.value}'}), 400

        # Cancel the task
        with storage_lock:
            task.status = TaskStatus.CANCELLED
            task.completed_at = datetime.now()
            task.error = 'Task cancelled by user'

            # Try to cancel if it's running
            future = active_tasks.get(task_id)
            if future:
                future.cancel()
                active_tasks.pop(task_id, None)
                stats['active_workers'] -= 1

        update_stats('tasks_cancelled')

        return jsonify({
            'success': True,
            'task_id': task_id,
            'status': task.status.value,
            'message': 'Task cancelled successfully'
        })

    except Exception as e:
        logger.error(f"Cancel task error: {e}")
        update_stats('errors')
        return jsonify({'error': str(e)}), 500

@app.route('/tasks/bulk', methods=['POST'])
def create_bulk_tasks():
    """Create multiple tasks at once"""
    try:
        data = request.get_json()
        if not data or 'tasks' not in data:
            return jsonify({'error': 'JSON data with tasks array required'}), 400

        task_definitions = data['tasks']
        if not isinstance(task_definitions, list):
            return jsonify({'error': 'tasks must be an array'}), 400

        created_tasks = []
        failed_tasks = []

        for i, task_def in enumerate(task_definitions):
            try:
                operation = task_def.get('operation')
                if not operation or operation not in TASK_PROCESSORS:
                    failed_tasks.append({
                        'index': i,
                        'error': 'Invalid or missing operation',
                        'task': task_def
                    })
                    continue

                # Create task
                task_id = str(uuid.uuid4())
                task = Task(
                    id=task_id,
                    name=task_def.get('name', f'Bulk Task {i+1}'),
                    operation=operation,
                    params=task_def.get('params', {}),
                    priority=TaskPriority(task_def.get('priority', TaskPriority.NORMAL.value)),
                    status=TaskStatus.PENDING,
                    created_at=datetime.now(),
                    max_retries=task_def.get('max_retries', 3),
                    timeout=task_def.get('timeout')
                )

                # Store and queue task
                with storage_lock:
                    task_storage[task_id] = task

                task_queue.put(task)

                created_tasks.append({
                    'task_id': task_id,
                    'name': task.name,
                    'operation': task.operation,
                    'status': task.status.value
                })

                update_stats('tasks_created')

            except Exception as e:
                failed_tasks.append({
                    'index': i,
                    'error': str(e),
                    'task': task_def
                })

        with storage_lock:
            stats['queue_size'] = task_queue.qsize()

        return jsonify({
            'success': True,
            'created_tasks': len(created_tasks),
            'failed_tasks': len(failed_tasks),
            'total_requested': len(task_definitions),
            'tasks': created_tasks,
            'failures': failed_tasks
        })

    except Exception as e:
        logger.error(f"Bulk create error: {e}")
        update_stats('errors')
        return jsonify({'error': str(e)}), 500

@app.route('/queue/stats')
def queue_stats():
    """Get queue and processing statistics"""
    try:
        with storage_lock:
            queue_size = task_queue.qsize()
            active_count = len(active_tasks)

            # Count tasks by status
            status_counts = {}
            for status in TaskStatus:
                status_counts[status.value] = 0

            for task in task_storage.values():
                status_counts[task.status.value] += 1

        return jsonify({
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
        return jsonify({'error': str(e)}), 500

@app.route('/cleanup', methods=['POST'])
def cleanup_tasks():
    """Clean up completed and failed tasks"""
    try:
        max_age_hours = int(request.args.get('max_age_hours', 24))
        keep_recent = int(request.args.get('keep_recent', 100))

        cutoff_time = datetime.now() - timedelta(hours=max_age_hours)

        with storage_lock:
            tasks_to_remove = []
            completed_tasks = []

            for task_id, task in task_storage.items():
                if task.status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]:
                    if task.completed_at and task.completed_at < cutoff_time:
                        completed_tasks.append((task.completed_at, task_id))

            # Sort by completion time and keep only the most recent ones
            completed_tasks.sort(reverse=True)
            if len(completed_tasks) > keep_recent:
                tasks_to_remove = [task_id for _, task_id in completed_tasks[keep_recent:]]

            # Remove old tasks
            for task_id in tasks_to_remove:
                task_storage.pop(task_id, None)
                active_tasks.pop(task_id, None)  # Just in case

        return jsonify({
            'success': True,
            'cleaned_tasks': len(tasks_to_remove),
            'remaining_tasks': len(task_storage),
            'cutoff_time': cutoff_time.isoformat()
        })

    except Exception as e:
        logger.error(f"Cleanup error: {e}")
        update_stats('errors')
        return jsonify({'error': str(e)}), 500

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({'error': 'Resource not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle internal server errors"""
    update_stats('errors')
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Flask Background Tasks Benchmark Server')
    parser.add_argument('--port', type=int, default=None,
                        help='Port to run the server on')
    parser.add_argument('--host', type=str, default='127.0.0.1',
                        help='Host to bind the server to')
    parser.add_argument('--debug', action='store_true',
                        help='Enable debug mode')
    parser.add_argument('--workers', type=int, default=4,
                        help='Number of worker threads')

    args = parser.parse_args()

    # Update worker count if specified
    if args.workers != 4:
        MAX_WORKERS = args.workers
        executor = concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS)

    # Get port from config or argument
    port = args.port or get_port('flask', 'background_tasks')

    print(f"Starting Flask Background Tasks Benchmark Server on {args.host}:{port}")
    print(f"Worker threads: {MAX_WORKERS}")
    print("Available endpoints:")
    print("  POST   /tasks                    - Create new task")
    print("  GET    /tasks/<task_id>          - Get task status")
    print("  GET    /tasks                    - List all tasks")
    print("  POST   /tasks/<task_id>/cancel   - Cancel task")
    print("  POST   /tasks/bulk               - Create multiple tasks")
    print("  GET    /queue/stats              - Get queue statistics")
    print("  POST   /cleanup                  - Clean up old tasks")
    print("  GET    /health                   - Health check")
    print("Available operations:", list(TASK_PROCESSORS.keys()))

    app.run(host=args.host, port=port, debug=args.debug, threaded=True)

# The app instance is already created at module level (line 42) for WSGI servers like gunicorn
