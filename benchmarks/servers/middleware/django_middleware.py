#!/usr/bin/env python3
"""
Django Middleware Benchmark Server

Django server implementation for middleware performance benchmarking
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
from shared_endpoints import get_benchmark_endpoints

try:
    import django
    from django.conf import settings
    from django.core.wsgi import get_wsgi_application
    from django.http import JsonResponse, HttpResponse
    from django.urls import path
    from django.views.decorators.csrf import csrf_exempt
    from django.views.decorators.http import require_http_methods
    from django.utils.deprecation import MiddlewareMixin
    import gunicorn.app.base
except ImportError:
    print("❌ Django/Gunicorn not installed. Install with: pip install django gunicorn")
    sys.exit(1)


# Custom middleware classes for testing
class TimingMiddleware(MiddlewareMixin):
    """Timing middleware for performance measurement"""

    def process_request(self, request):
        request.start_time = time.time()
        return None

    def process_response(self, request, response):
        if hasattr(request, 'start_time'):
            duration = time.time() - request.start_time
            response['X-Response-Time'] = f"{duration:.4f}"
        return response


class AuthMiddleware(MiddlewareMixin):
    """Simple auth middleware for testing"""

    def process_request(self, request):
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        if auth_header.startswith('Bearer '):
            request.user_id = 'authenticated'
        else:
            request.user_id = 'anonymous'
        return None


class LoggingMiddleware(MiddlewareMixin):
    """Logging middleware for testing"""

    def process_request(self, request):
        request.request_id = f"req_{int(time.time() * 1000)}"
        return None

    def process_response(self, request, response):
        if hasattr(request, 'request_id'):
            response['X-Request-ID'] = request.request_id
        return response


class RateLimitMiddleware(MiddlewareMixin):
    """Rate limiting middleware for testing"""

    def __init__(self, get_response):
        self.get_response = get_response
        self.request_counts = {}
        super().__init__(get_response)

    def process_request(self, request):
        client_ip = self.get_client_ip(request)
        current_time = int(time.time())

        # Simple rate limiting (100 requests per minute)
        key = f"{client_ip}:{current_time // 60}"
        self.request_counts[key] = self.request_counts.get(key, 0) + 1

        if self.request_counts[key] > 100:
            return JsonResponse({"error": "Rate limit exceeded"}, status=429)

        return None

    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class CORSMiddleware(MiddlewareMixin):
    """CORS middleware for testing"""

    def process_response(self, request, response):
        response['Access-Control-Allow-Origin'] = '*'
        response['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
        response['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        return response


# Configure Django settings with middleware
if not settings.configured:
    settings.configure(
        DEBUG=False,
        SECRET_KEY='benchmark-secret-key-not-for-production',
        ROOT_URLCONF=__name__,
        ALLOWED_HOSTS=['*'],
        USE_TZ=True,
        MIDDLEWARE=[
            'django.middleware.common.CommonMiddleware',
            'benchmarks.servers.middleware.django_middleware.TimingMiddleware',
            'benchmarks.servers.middleware.django_middleware.AuthMiddleware',
            'benchmarks.servers.middleware.django_middleware.LoggingMiddleware',
            'benchmarks.servers.middleware.django_middleware.RateLimitMiddleware',
            'benchmarks.servers.middleware.django_middleware.CORSMiddleware',
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


# Django Views with middleware testing
def home(request):
    """Basic middleware overhead test"""
    return JsonResponse({
        "message": "Django middleware test",
        "framework": "django",
        "middleware_count": len(settings.MIDDLEWARE),
        "user_id": getattr(request, 'user_id', 'unknown'),
        "request_id": getattr(request, 'request_id', 'unknown')
    })


def health_check(request):
    """Health check with minimal middleware"""
    return JsonResponse({
        "status": "healthy",
        "framework": "django",
        "timestamp": time.time(),
        "middleware": "enabled"
    })


def light_middleware(request):
    """Light middleware stack test - fewer operations"""
    return JsonResponse({
        "message": "Light middleware response",
        "framework": "django",
        "processing": "minimal",
        "user_id": getattr(request, 'user_id', 'unknown')
    })


def heavy_middleware(request):
    """Heavy middleware stack test - more operations"""
    # Simulate heavy processing
    data = {
        "message": "Heavy middleware response",
        "framework": "django",
        "processing": "intensive",
        "user_id": getattr(request, 'user_id', 'unknown'),
        "request_id": getattr(request, 'request_id', 'unknown'),
        "computed_data": [i * 2 for i in range(100)],  # Some computation
        "timestamp": time.time()
    }

    return JsonResponse(data)


@csrf_exempt
@require_http_methods(["POST"])
def auth_test(request):
    """Authentication middleware test"""
    user_id = getattr(request, 'user_id', 'anonymous')

    if user_id == 'anonymous':
        return JsonResponse({"error": "Authentication required"}, status=401)

    try:
        data = json.loads(request.body.decode('utf-8'))
    except json.JSONDecodeError:
        data = {}

    return JsonResponse({
        "message": "Authenticated request processed",
        "user_id": user_id,
        "data": data,
        "request_id": getattr(request, 'request_id', 'unknown')
    })


def cors_test(request):
    """CORS middleware test"""
    return JsonResponse({
        "message": "CORS enabled response",
        "framework": "django",
        "origin": request.META.get('HTTP_ORIGIN', 'unknown'),
        "method": request.method
    })


def rate_limit_test(request):
    """Rate limiting middleware test"""
    return JsonResponse({
        "message": "Rate limited endpoint",
        "framework": "django",
        "timestamp": time.time(),
        "user_id": getattr(request, 'user_id', 'unknown')
    })


def complex_middleware_stack(request):
    """Complex middleware stack with all features"""
    # This endpoint exercises all middleware
    data = {
        "message": "Complex middleware stack response",
        "framework": "django",
        "middleware_features": [
            "timing",
            "authentication",
            "logging",
            "rate_limiting",
            "cors"
        ],
        "user_id": getattr(request, 'user_id', 'unknown'),
        "request_id": getattr(request, 'request_id', 'unknown'),
        "computed_result": sum(range(1000)),  # Some computation
        "timestamp": time.time()
    }

    return JsonResponse(data)


# URL Configuration
urlpatterns = [
    path('', home, name='home'),
    path('health', health_check, name='health_check'),
    path('middleware-light', light_middleware, name='light_middleware'),
    path('middleware-heavy', heavy_middleware, name='heavy_middleware'),
    path('auth-test', auth_test, name='auth_test'),
    path('cors-test', cors_test, name='cors_test'),
    path('rate-limit-test', rate_limit_test, name='rate_limit_test'),
    path('complex-stack', complex_middleware_stack, name='complex_middleware_stack'),
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
    """Start the Django middleware benchmark server"""
    parser = argparse.ArgumentParser(description="Django Middleware Benchmark Server")
    parser.add_argument("--port", type=int, default=8103, help="Port to run server on")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind to")
    parser.add_argument("--workers", type=int, default=1, help="Number of worker processes")
    args = parser.parse_args()

    print(f"🚀 Starting Django middleware benchmark server on {args.host}:{args.port}")
    print("📊 Django Middleware Features:")
    print("  ⏱️  Timing middleware")
    print("  🔐 Authentication middleware")
    print("  📝 Logging middleware")
    print("  🚦 Rate limiting middleware")
    print("  🌐 CORS middleware")
    print()
    print("Available endpoints:")
    print("  GET  /                    - Basic middleware test")
    print("  GET  /health             - Health check")
    print("  GET  /middleware-light   - Light middleware stack")
    print("  GET  /middleware-heavy   - Heavy middleware stack")
    print("  POST /auth-test          - Authentication test")
    print("  GET  /cors-test          - CORS test")
    print("  GET  /rate-limit-test    - Rate limiting test")
    print("  GET  /complex-stack      - Complex middleware stack")
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
        print("\n👋 Django middleware benchmark server stopped")


if __name__ == "__main__":
    main()

# Create WSGI application instance for external servers like gunicorn
application = get_wsgi_application()
