#!/usr/bin/env python3
"""
Django Async Operations Benchmark Server

Django server implementation for async operations performance benchmarking
against Catzilla and other Python web frameworks.

Note: Django has limited async support compared to modern frameworks,
but we'll simulate async-like operations where possible.
"""

import os
import sys
import json
import argparse
import time
import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, Any, Optional

# Import shared endpoints from the new structure
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'shared'))

try:
    import django
    from django.conf import settings
    from django.core.wsgi import get_wsgi_application
    from django.http import JsonResponse, HttpResponse
    from django.urls import path
    from django.views.decorators.csrf import csrf_exempt
    from django.views.decorators.http import require_http_methods
    import gunicorn.app.base
except ImportError:
    print("❌ Django/Gunicorn not installed. Install with: pip install django gunicorn")
    sys.exit(1)


# Thread pool for simulating async operations
thread_pool = ThreadPoolExecutor(max_workers=10)


# Async operation simulations
def simulate_database_query(query_time: float = 0.1):
    """Simulate database query with delay"""
    time.sleep(query_time)
    return {
        "query": "SELECT * FROM users",
        "results": [{"id": i, "name": f"User {i}"} for i in range(1, 6)],
        "execution_time": query_time
    }


def simulate_api_call(api_name: str, delay: float = 0.2):
    """Simulate external API call"""
    time.sleep(delay)
    return {
        "api": api_name,
        "response": f"Response from {api_name}",
        "delay": delay,
        "timestamp": time.time()
    }


def simulate_file_operation(operation: str = "read", delay: float = 0.05):
    """Simulate file I/O operation"""
    time.sleep(delay)
    return {
        "operation": operation,
        "file": f"example_{operation}.txt",
        "size": "1.2MB",
        "duration": delay
    }


def simulate_computation(complexity: int = 1000):
    """Simulate CPU-intensive computation"""
    result = sum(i * i for i in range(complexity))
    return {
        "computation": "sum_of_squares",
        "complexity": complexity,
        "result": result
    }


# Configure Django settings
if not settings.configured:
    settings.configure(
        DEBUG=False,
        SECRET_KEY='benchmark-secret-key-not-for-production',
        ROOT_URLCONF=__name__,
        ALLOWED_HOSTS=['*'],
        USE_TZ=True,
        MIDDLEWARE=[
            'django.middleware.common.CommonMiddleware',
        ],
        LOGGING={
            'version': 1,
            'disable_existing_loggers': False,
            'handlers': {
                'null': {
                    'class': 'logging.NullHandler',
                },
            },
            'root': {
                'handlers': ['null'],
            },
        }
    )

django.setup()


# Django Views with async operation simulation
def home(request):
    """Basic async operations test"""
    return JsonResponse({
        "message": "Django async operations test",
        "framework": "django",
        "async_support": "limited",
        "simulation": "thread_pool_based"
    })


def health_check(request):
    """Health check endpoint"""
    return JsonResponse({
        "status": "healthy",
        "framework": "django",
        "timestamp": time.time(),
        "async_features": "simulated"
    })


def sync_operation(request):
    """Synchronous operation baseline"""
    start_time = time.time()

    # Simulate some work
    result = simulate_computation(500)

    return JsonResponse({
        "message": "Synchronous operation",
        "framework": "django",
        "operation_type": "sync",
        "result": result,
        "duration": time.time() - start_time
    })


def simulated_async_operation(request):
    """Simulated async operation using thread pool"""
    start_time = time.time()

    # Submit async tasks to thread pool
    future1 = thread_pool.submit(simulate_database_query, 0.1)
    future2 = thread_pool.submit(simulate_api_call, "payment_service", 0.15)
    future3 = thread_pool.submit(simulate_file_operation, "read", 0.05)

    # Wait for results (blocking, but simulates async pattern)
    db_result = future1.result()
    api_result = future2.result()
    file_result = future3.result()

    return JsonResponse({
        "message": "Simulated async operation",
        "framework": "django",
        "operation_type": "thread_pool_async",
        "results": {
            "database": db_result,
            "api_call": api_result,
            "file_operation": file_result
        },
        "total_duration": time.time() - start_time
    })


def concurrent_operations(request):
    """Multiple concurrent operations"""
    start_time = time.time()

    # Submit multiple concurrent tasks
    futures = []
    for i in range(5):
        future = thread_pool.submit(simulate_api_call, f"service_{i}", 0.1)
        futures.append(future)

    # Collect results
    results = []
    for i, future in enumerate(futures):
        result = future.result()
        results.append({"task_id": i, "result": result})

    return JsonResponse({
        "message": "Concurrent operations",
        "framework": "django",
        "operation_type": "concurrent_thread_pool",
        "task_count": len(futures),
        "results": results,
        "total_duration": time.time() - start_time
    })


def mixed_operations(request):
    """Mixed sync and simulated async operations"""
    start_time = time.time()

    # Synchronous computation
    sync_result = simulate_computation(800)

    # Async database query (simulated)
    db_future = thread_pool.submit(simulate_database_query, 0.12)

    # Async API call (simulated)
    api_future = thread_pool.submit(simulate_api_call, "analytics_service", 0.08)

    # More sync work
    file_result = simulate_file_operation("write", 0.03)

    # Wait for async results
    db_result = db_future.result()
    api_result = api_future.result()

    return JsonResponse({
        "message": "Mixed sync and async operations",
        "framework": "django",
        "operation_type": "mixed",
        "results": {
            "sync_computation": sync_result,
            "async_database": db_result,
            "async_api": api_result,
            "sync_file": file_result
        },
        "total_duration": time.time() - start_time
    })


@csrf_exempt
@require_http_methods(["POST"])
def parallel_processing(request):
    """Parallel data processing simulation"""
    try:
        data = json.loads(request.body.decode('utf-8'))
        items = data.get('items', list(range(10)))
    except:
        items = list(range(10))

    start_time = time.time()

    # Process items in parallel using thread pool
    def process_item(item):
        time.sleep(0.02)  # Simulate processing time
        return {"item": item, "processed": item * 2, "timestamp": time.time()}

    # Submit all items for processing
    futures = [thread_pool.submit(process_item, item) for item in items]

    # Collect results
    results = [future.result() for future in futures]

    return JsonResponse({
        "message": "Parallel data processing",
        "framework": "django",
        "operation_type": "parallel_processing",
        "input_count": len(items),
        "results": results,
        "total_duration": time.time() - start_time
    })


def streaming_simulation(request):
    """Streaming response simulation"""
    def generate_data():
        for i in range(10):
            time.sleep(0.05)  # Simulate data generation delay
            yield f"data_chunk_{i}\n"

    response = HttpResponse(generate_data(), content_type='text/plain')
    response['X-Operation-Type'] = 'streaming_simulation'
    return response


def background_task_simulation(request):
    """Background task simulation"""
    start_time = time.time()

    # Submit background tasks
    background_futures = []
    for i in range(3):
        future = thread_pool.submit(
            simulate_api_call,
            f"background_service_{i}",
            0.2
        )
        background_futures.append(future)

    # Don't wait for background tasks, return immediately
    return JsonResponse({
        "message": "Background tasks started",
        "framework": "django",
        "operation_type": "background_simulation",
        "tasks_submitted": len(background_futures),
        "response_time": time.time() - start_time,
        "note": "Background tasks running in thread pool"
    })


def event_loop_simulation(request):
    """Event loop simulation (limited in Django)"""
    start_time = time.time()

    # Simulate event-driven operations
    events = []
    for i in range(5):
        event_future = thread_pool.submit(
            simulate_computation,
            200 + (i * 100)
        )
        events.append({
            "event_id": i,
            "result": event_future.result(),
            "timestamp": time.time()
        })

    return JsonResponse({
        "message": "Event loop simulation",
        "framework": "django",
        "operation_type": "event_simulation",
        "events_processed": len(events),
        "events": events,
        "total_duration": time.time() - start_time
    })


def async_performance_test(request):
    """Comprehensive async performance test"""
    start_time = time.time()

    # Submit various async operations
    tasks = [
        thread_pool.submit(simulate_database_query, 0.1),
        thread_pool.submit(simulate_api_call, "auth_service", 0.08),
        thread_pool.submit(simulate_api_call, "user_service", 0.12),
        thread_pool.submit(simulate_file_operation, "read", 0.06),
        thread_pool.submit(simulate_computation, 1500),
    ]

    # Wait for all tasks to complete
    results = []
    for i, task in enumerate(tasks):
        result = task.result()
        results.append({
            "task_id": i,
            "task_type": ["database", "auth_api", "user_api", "file_io", "computation"][i],
            "result": result
        })

    return JsonResponse({
        "message": "Comprehensive async performance test",
        "framework": "django",
        "operation_type": "comprehensive_async",
        "tasks_completed": len(results),
        "results": results,
        "total_duration": time.time() - start_time
    })


# URL Configuration
urlpatterns = [
    path('', home, name='home'),
    path('health', health_check, name='health_check'),
    path('sync-operation', sync_operation, name='sync_operation'),
    path('async-operation', simulated_async_operation, name='async_operation'),
    path('concurrent-operations', concurrent_operations, name='concurrent_operations'),
    path('mixed-operations', mixed_operations, name='mixed_operations'),
    path('parallel-processing', parallel_processing, name='parallel_processing'),
    path('streaming-simulation', streaming_simulation, name='streaming_simulation'),
    path('background-task', background_task_simulation, name='background_task'),
    path('event-loop-sim', event_loop_simulation, name='event_loop_simulation'),
    path('async-performance', async_performance_test, name='async_performance_test'),
]


class GunicornDjangoApplication(gunicorn.app.base.BaseApplication):
    """Custom Gunicorn application to run Django with specific config"""

    def __init__(self, app, options=None):
        self.options = options or {}
        self.application = app
        super().__init__()

    def load_config(self):
        for key, value in self.options.items():
            if key in self.cfg.settings and value is not None:
                self.cfg.set(key.lower(), value)

    def load(self):
        return self.application


def main():
    """Start the Django async operations benchmark server"""
    parser = argparse.ArgumentParser(description="Django Async Operations Benchmark Server")
    parser.add_argument("--port", type=int, default=8303, help="Port to run server on")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind to")
    parser.add_argument("--workers", type=int, default=1, help="Number of worker processes")
    args = parser.parse_args()

    print(f"🚀 Starting Django async operations benchmark server on {args.host}:{args.port}")
    print("📊 Django Async Features (Simulated):")
    print("  🧵 Thread pool based async simulation")
    print("  🔄 Concurrent operations via futures")
    print("  📊 Mixed sync/async patterns")
    print("  ⚠️  Limited native async support")
    print()
    print("Available endpoints:")
    print("  GET  /                      - Basic async test")
    print("  GET  /health               - Health check")
    print("  GET  /sync-operation       - Synchronous baseline")
    print("  GET  /async-operation      - Simulated async operation")
    print("  GET  /concurrent-operations - Concurrent operations")
    print("  GET  /mixed-operations     - Mixed sync/async")
    print("  POST /parallel-processing  - Parallel data processing")
    print("  GET  /streaming-simulation - Streaming response")
    print("  GET  /background-task      - Background task simulation")
    print("  GET  /event-loop-sim       - Event loop simulation")
    print("  GET  /async-performance    - Comprehensive async test")
    print()

    try:
        # Production WSGI server
        options = {
            'bind': f'{args.host}:{args.port}',
            'workers': args.workers,
            'worker_class': 'sync',
            'timeout': 30,
            'keepalive': 2,
            'max_requests': 1000,
            'max_requests_jitter': 100,
            'disable_redirect_access_to_syslog': True,
        }

        app = get_wsgi_application()
        GunicornDjangoApplication(app, options).run()

    except KeyboardInterrupt:
        print("\n👋 Django async operations benchmark server stopped")


if __name__ == "__main__":
    main()
