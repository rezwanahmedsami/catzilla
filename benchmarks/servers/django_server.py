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


# URL Configuration
urlpatterns = [
    path('', hello_world, name='hello_world'),
    path('json', json_response, name='json_response'),
    path('user/<int:user_id>', user_by_id, name='user_by_id'),
    path('echo', echo_json, name='echo_json'),
    path('users', search_users, name='search_users'),
    path('user/<int:user_id>/profile', user_profile, name='user_profile'),
    path('health', health_check, name='health_check'),
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
