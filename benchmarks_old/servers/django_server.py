#!/usr/bin/env python3
"""
Django Benchmark Server

Django server implementation for performance benchmarking
against Catzilla and other Python web frameworks.
"""

import sys
import os
import json
import django
from django.conf import settings
from django.core.wsgi import get_wsgi_application
from django.http import JsonResponse, HttpResponse
from django.urls import path
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import time

# Import shared endpoints
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from shared_endpoints import get_benchmark_endpoints, DEFAULT_JSON_PAYLOAD

try:
    import gunicorn.app.base
except ImportError:
    print("❌ Django/Gunicorn not installed. Install with: pip install django gunicorn")
    sys.exit(1)

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

# Get benchmark endpoints configuration
endpoints = get_benchmark_endpoints()


# Django Views
def hello_world(request):
    """Simple text response"""
    return HttpResponse("Hello, World!", content_type="text/plain")


def json_response(request):
    """JSON serialization test"""
    return JsonResponse(endpoints["json_response"]["response"])


def user_by_id(request, user_id):
    """Path parameter extraction test"""
    return JsonResponse(endpoints["user_by_id"]["response_template"](str(user_id)))


@csrf_exempt
@require_http_methods(["POST"])
def echo_json(request):
    """JSON request parsing test"""
    try:
        data = json.loads(request.body.decode('utf-8')) if request.body else {}
    except (json.JSONDecodeError, UnicodeDecodeError):
        data = {"error": "Invalid JSON"}

    return JsonResponse(endpoints["echo_json"]["response_template"](data))


def search_users(request):
    """Query parameter handling test"""
    limit = int(request.GET.get("limit", 10))
    offset = int(request.GET.get("offset", 0))
    return JsonResponse(endpoints["search_users"]["response_template"](limit, offset))


def user_profile(request, user_id):
    """Complex JSON response test"""
    return JsonResponse(endpoints["user_profile"]["response_template"](str(user_id)))


def health_check(request):
    """Health check endpoint"""
    return JsonResponse({"status": "healthy", "framework": "django"})


# =====================================================
# FEATURE BENCHMARK VIEWS
# =====================================================

# ROUTING FEATURES
def routing_static(request):
    """Static routing test"""
    return JsonResponse({"message": "Static route response", "framework": "django"})


def routing_path_param(request, item_id):
    """Path parameter routing test"""
    return JsonResponse({"item_id": item_id, "framework": "django"})


def routing_multiple_params(request, category, item_id):
    """Multiple path parameters routing test"""
    return JsonResponse({"category": category, "item_id": item_id, "framework": "django"})


def routing_query_params(request):
    """Query parameter routing test"""
    limit = int(request.GET.get("limit", 10))
    offset = int(request.GET.get("offset", 0))
    sort = request.GET.get("sort", "name")
    return JsonResponse({"limit": limit, "offset": offset, "sort": sort, "framework": "django"})


# VALIDATION FEATURES (manual validation - Django doesn't have built-in validation like FastAPI)
@csrf_exempt
@require_http_methods(["POST"])
def validation_simple(request):
    """Simple validation test"""
    try:
        data = json.loads(request.body.decode('utf-8')) if request.body else {}
        # Manual validation for Django
        required_fields = ["id", "name", "email"]
        for field in required_fields:
            if field not in data:
                raise ValueError(f"Missing required field: {field}")

        # Simple type checking
        if not isinstance(data["id"], int):
            data["id"] = int(data["id"])

        return JsonResponse({
            "validated": True,
            "user": data,
            "framework": "django",
            "validation_engine": "manual"
        })
    except Exception as e:
        return JsonResponse({
            "validated": False,
            "error": str(e),
            "framework": "django",
            "validation_engine": "manual"
        })


@csrf_exempt
@require_http_methods(["POST"])
def validation_complex(request):
    """Complex validation test"""
    try:
        data = json.loads(request.body.decode('utf-8')) if request.body else {}
        # Manual validation for Django
        required_fields = ["id", "name", "email"]
        for field in required_fields:
            if field not in data:
                raise ValueError(f"Missing required field: {field}")

        # Simple type checking
        if not isinstance(data["id"], int):
            data["id"] = int(data["id"])

        return JsonResponse({
            "validated": True,
            "user": data,
            "validation_count": len(data.keys()),
            "framework": "django",
            "validation_engine": "manual"
        })
    except Exception as e:
        return JsonResponse({
            "validated": False,
            "error": str(e),
            "framework": "django",
            "validation_engine": "manual"
        })


@csrf_exempt
@require_http_methods(["POST"])
def validation_product(request):
    """Product validation test"""
    try:
        data = json.loads(request.body.decode('utf-8')) if request.body else {}
        # Manual validation for Django
        required_fields = ["name", "price", "category"]
        for field in required_fields:
            if field not in data:
                raise ValueError(f"Missing required field: {field}")

        # Type checking
        if not isinstance(data["price"], (int, float)):
            data["price"] = float(data["price"])

        return JsonResponse({
            "validated": True,
            "product": data,
            "framework": "django",
            "validation_engine": "manual"
        })
    except Exception as e:
        return JsonResponse({
            "validated": False,
            "error": str(e),
            "framework": "django",
            "validation_engine": "manual"
        })


def validation_query_params(request):
    """Query parameter validation test"""
    try:
        query = request.GET.get("query", "")
        limit = int(request.GET.get("limit", 10))
        offset = int(request.GET.get("offset", 0))
        sort_by = request.GET.get("sort_by", "created_at")

        # Basic validation
        if not query:
            raise ValueError("Query parameter is required")
        if limit < 1 or limit > 1000:
            raise ValueError("Limit must be between 1 and 1000")

        return JsonResponse({
            "validated": True,
            "query": query,
            "limit": limit,
            "offset": offset,
            "sort_by": sort_by,
            "framework": "django",
            "validation_engine": "manual"
        })
    except Exception as e:
        return JsonResponse({
            "validated": False,
            "error": str(e),
            "framework": "django",
            "validation_engine": "manual"
        })


# DEPENDENCY INJECTION FEATURES (manual DI - Django doesn't have built-in DI)
def di_simple(request):
    """Simple dependency injection test"""
    return JsonResponse({
        "connection": "django_connection_1",
        "query_result": {"sql": "SELECT 1", "result": "query_result_1"},
        "framework": "django",
        "di_system": "manual"
    })


def di_nested(request, user_id):
    """Nested dependency injection test"""
    return JsonResponse({
        "user": {"id": user_id, "name": f"User {user_id}", "email": f"user{user_id}@example.com"},
        "timestamp": time.time(),
        "framework": "django",
        "di_system": "manual"
    })


# BACKGROUND TASKS FEATURES (basic implementation - Django doesn't have built-in background tasks)
@csrf_exempt
@require_http_methods(["POST"])
def background_simple(request):
    """Simple background task test"""
    task_id = f"django_task_{int(time.time() * 1000000)}"
    # In a real app, you'd use Celery or similar
    return JsonResponse({
        "task_id": task_id,
        "task_type": "simple",
        "created_at": time.time(),
        "framework": "django",
        "background_system": "manual"
    })


def background_stats(request):
    """Background task stats"""
    return JsonResponse({
        "stats": {
            "tasks_created": 0,
            "tasks_completed": 0,
            "active_tasks": 0
        },
        "framework": "django",
        "background_system": "manual"
    })


# FILE UPLOAD FEATURES
@csrf_exempt
@require_http_methods(["POST"])
def upload_simple(request):
    """Simple file upload test"""
    uploaded_file = request.FILES.get('file') if request.FILES else None
    return JsonResponse({
        "upload_id": f"django_upload_{int(time.time() * 1000000)}",
        "file_info": {
            "filename": uploaded_file.name if uploaded_file else "test_file.txt",
            "content_type": uploaded_file.content_type if uploaded_file else "text/plain",
            "file_size": 1024,
            "processing_time": 0.001
        },
        "framework": "django",
        "upload_system": "django_builtin"
    })


def upload_stats(request):
    """File upload stats"""
    return JsonResponse({
        "stats": {
            "files_uploaded": 0,
            "total_size": 0,
            "successful_uploads": 0
        },
        "framework": "django",
        "upload_system": "django_builtin"
    })


# STREAMING FEATURES
def streaming_json(request):
    """JSON streaming test"""
    count = int(request.GET.get("count", 100))
    # Simple JSON response (Django handles this)
    items = [{"id": i, "value": i * 2, "name": f"item_{i}"} for i in range(min(count, 1000))]
    return JsonResponse({
        "stream_type": "json",
        "count": len(items),
        "data": items,
        "framework": "django"
    })


def streaming_csv(request):
    """CSV streaming test"""
    count = int(request.GET.get("count", 1000))

    def generate_csv():
        yield "id,name,value\n"
        for i in range(min(count, 10000)):
            yield f"{i},item_{i},{i * 2}\n"

    response = HttpResponse(generate_csv(), content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="data.csv"'
    return response


# URL Configuration
urlpatterns = [
    # Basic endpoints
    path('', hello_world, name='hello_world'),
    path('json', json_response, name='json_response'),
    path('user/<int:user_id>', user_by_id, name='user_by_id'),
    path('echo', echo_json, name='echo_json'),
    path('users', search_users, name='search_users'),
    path('user/<int:user_id>/profile', user_profile, name='user_profile'),
    path('health', health_check, name='health_check'),

    # Feature benchmark endpoints
    # Routing features
    path('bench/routing/static', routing_static, name='routing_static'),
    path('bench/routing/path/<int:item_id>', routing_path_param, name='routing_path_param'),
    path('bench/routing/path/<str:category>/<int:item_id>', routing_multiple_params, name='routing_multiple_params'),
    path('bench/routing/query', routing_query_params, name='routing_query_params'),

    # Validation features
    path('bench/validation/simple', validation_simple, name='validation_simple'),
    path('bench/validation/complex', validation_complex, name='validation_complex'),
    path('bench/validation/product', validation_product, name='validation_product'),
    path('bench/validation/query', validation_query_params, name='validation_query_params'),

    # Dependency injection features
    path('bench/di/simple', di_simple, name='di_simple'),
    path('bench/di/nested/<int:user_id>', di_nested, name='di_nested'),

    # Background tasks features
    path('bench/background/simple', background_simple, name='background_simple'),
    path('bench/background/stats', background_stats, name='background_stats'),

    # File upload features
    path('bench/upload/simple', upload_simple, name='upload_simple'),
    path('bench/upload/stats', upload_stats, name='upload_stats'),

    # Streaming features
    path('bench/streaming/json', streaming_json, name='streaming_json'),
    path('bench/streaming/csv', streaming_csv, name='streaming_csv'),
]


class GunicornDjangoApplication(gunicorn.app.base.BaseApplication):
    """Custom Gunicorn application to run Django with specific config"""

    def __init__(self, options=None):
        self.options = options or {}
        super().__init__()

    def load_config(self):
        for key, value in self.options.items():
            self.cfg.set(key.lower(), value)

    def load(self):
        return get_wsgi_application()


def main():
    """Start the Django benchmark server"""
    import argparse

    parser = argparse.ArgumentParser(description="Django Benchmark Server")
    parser.add_argument("--port", type=int, default=8003, help="Port to run server on")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind to")
    parser.add_argument("--workers", type=int, default=1, help="Number of worker processes")
    args = parser.parse_args()

    print(f"🚀 Starting Django benchmark server on {args.host}:{args.port}")
    print("Available endpoints:")
    print("  GET  /              - Hello World")
    print("  GET  /json          - JSON Response")
    print("  GET  /user/{id}     - Path Parameters")
    print("  POST /echo          - JSON Echo")
    print("  GET  /users         - Query Parameters")
    print("  GET  /user/{id}/profile - Complex JSON")
    print("  GET  /health        - Health Check")
    print()

    try:
        # Use Gunicorn for better performance
        options = {
            'bind': f'{args.host}:{args.port}',
            'workers': args.workers,
            'worker_class': 'sync',
            'accesslog': None,  # Use 'accesslog' instead of 'access_log'
            'errorlog': '-',     # Use 'errorlog' instead of 'error_log'
            'loglevel': 'warning',  # Use 'loglevel' instead of 'log_level'
            'preload_app': True,
        }
        GunicornDjangoApplication(options).run()
    except KeyboardInterrupt:
        print("\n👋 Django benchmark server stopped")


if __name__ == "__main__":
    main()
