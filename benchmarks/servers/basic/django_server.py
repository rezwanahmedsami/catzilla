#!/usr/bin/env python3
"""
Django Benchmark Server

Django server implementation for performance benchmarking
against Catzilla and other Python web frameworks.
"""

import os
import sys
import json
import argparse
import time
from urllib.parse import parse_qs

# Import shared endpoints from the new structure
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'shared'))
from shared_endpoints import get_benchmark_endpoints, DEFAULT_JSON_PAYLOAD

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


def health_check(request):
    """Health check endpoint"""
    return JsonResponse({"status": "healthy", "framework": "django", "timestamp": time.time()})


def json_response(request):
    """JSON serialization test"""
    return JsonResponse(endpoints["json_response"]["response"])


def user_by_id(request, user_id):
    """Path parameter extraction test"""
    return JsonResponse(endpoints["user_by_id"]["response_template"](str(user_id)))


@csrf_exempt
@require_http_methods(["POST"])
def echo_json(request):
    """JSON echo test"""
    try:
        data = json.loads(request.body.decode('utf-8'))
    except json.JSONDecodeError:
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


# Auto-validation endpoints (manual validation - Django doesn't have built-in validation like FastAPI)
@csrf_exempt
@require_http_methods(["POST"])
def validate_user(request):
    """User model validation test"""
    try:
        data = json.loads(request.body.decode('utf-8'))

        # Manual validation - simulate Catzilla's auto-validation
        required_fields = ['id', 'name', 'email']
        for field in required_fields:
            if field not in data:
                return JsonResponse({"error": f"Missing required field: {field}"}, status=400)

        # Type validation
        if not isinstance(data['id'], int):
            return JsonResponse({"error": "id must be an integer"}, status=400)
        if not isinstance(data['name'], str):
            return JsonResponse({"error": "name must be a string"}, status=400)
        if not isinstance(data['email'], str):
            return JsonResponse({"error": "email must be a string"}, status=400)

        return JsonResponse(endpoints["validate_user"]["response_template"](data))
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)


@csrf_exempt
@require_http_methods(["POST"])
def validate_product(request):
    """Product model validation test"""
    try:
        data = json.loads(request.body.decode('utf-8'))

        # Manual validation
        required_fields = ['name', 'price', 'category']
        for field in required_fields:
            if field not in data:
                return JsonResponse({"error": f"Missing required field: {field}"}, status=400)

        # Type and constraint validation
        if not isinstance(data['price'], (int, float)) or data['price'] <= 0:
            return JsonResponse({"error": "price must be a positive number"}, status=400)

        return JsonResponse(endpoints["validate_product"]["response_template"](data))
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)


def search_with_validation(request):
    """Query parameter validation test"""
    try:
        query = request.GET.get("query")
        if not query:
            return JsonResponse({"error": "query parameter is required"}, status=400)

        limit = int(request.GET.get("limit", 10))
        offset = int(request.GET.get("offset", 0))
        sort_by = request.GET.get("sort_by", "created_at")

        # Validation constraints
        if limit < 1 or limit > 100:
            return JsonResponse({"error": "limit must be between 1 and 100"}, status=400)
        if offset < 0:
            return JsonResponse({"error": "offset must be non-negative"}, status=400)

        return JsonResponse(endpoints["search_with_validation"]["response_template"](query, limit, offset, sort_by))
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)


# URL Configuration
urlpatterns = [
    path('', hello_world, name='hello_world'),
    path('health', health_check, name='health_check'),
    path('json', json_response, name='json_response'),
    path('user/<int:user_id>', user_by_id, name='user_by_id'),
    path('echo', echo_json, name='echo_json'),
    path('users', search_users, name='search_users'),
    path('user/<int:user_id>/profile', user_profile, name='user_profile'),
    path('validate/user', validate_user, name='validate_user'),
    path('validate/product', validate_product, name='validate_product'),
    path('search/validate', search_with_validation, name='search_with_validation'),
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
    """Start the Django benchmark server"""
    parser = argparse.ArgumentParser(description="Django Benchmark Server")
    parser.add_argument("--port", type=int, default=8003, help="Port to run server on")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind to")
    parser.add_argument("--workers", type=int, default=1, help="Number of worker processes")
    parser.add_argument("--use-gunicorn", action="store_true", default=True, help="Use Gunicorn (default)")
    args = parser.parse_args()

    print(f"🚀 Starting Django benchmark server on {args.host}:{args.port}")
    print("📊 Django Features:")
    print("  🐍 Python/Django framework")
    print("  🗄️ ORM integration")
    print("  📋 Manual validation")
    print()
    print("Available endpoints:")
    print("  GET  /              - Hello World")
    print("  GET  /health        - Health Check")
    print("  GET  /json          - JSON Response")
    print("  GET  /user/{id}     - Path Parameters")
    print("  POST /echo          - JSON Echo")
    print("  GET  /users         - Query Parameters")
    print("  GET  /user/{id}/profile - Complex JSON")
    print("  POST /validate/user - Manual User Validation")
    print("  POST /validate/product - Manual Product Validation")
    print("  GET  /search/validate - Query Parameter Validation")
    print()

    try:
        if args.use_gunicorn:
            # Production WSGI server
            options = {
                'bind': f'{args.host}:{args.port}',
                'workers': args.workers,
                'worker_class': 'sync',
                'timeout': 30,
                'keepalive': 2,
                'max_requests': 1000,
                'max_requests_jitter': 100,
                'access_log_format': '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s',
                'disable_redirect_access_to_syslog': True,
                'capture_output': True,
                'enable_stdio_inheritance': True,
            }

            app = get_wsgi_application()
            GunicornDjangoApplication(app, options).run()
        else:
            # Development server (not recommended for benchmarks)
            from django.core.management import execute_from_command_line
            execute_from_command_line(['manage.py', 'runserver', f'{args.host}:{args.port}'])

    except KeyboardInterrupt:
        print("\n👋 Django benchmark server stopped")


if __name__ == "__main__":
    main()

# Create WSGI application instance for external servers like gunicorn
application = get_wsgi_application()
