#!/usr/bin/env python3
"""
Django Dependency Injection Benchmark Server

Django server implementation for dependency injection performance benchmarking
against Catzilla and other Python web frameworks.
"""

import os
import sys
import json
import argparse
import time
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


# =====================================================
# DEPENDENCY INJECTION SIMULATION FOR DJANGO
# =====================================================

class ServiceRegistry:
    """Simple service registry for dependency injection simulation"""

    def __init__(self):
        self._services = {}
        self._singletons = {}

    def register(self, name: str, service_class, singleton: bool = False):
        """Register a service"""
        self._services[name] = {
            'class': service_class,
            'singleton': singleton
        }

    def get(self, name: str):
        """Get a service instance"""
        if name not in self._services:
            raise ValueError(f"Service '{name}' not registered")

        service_config = self._services[name]

        if service_config['singleton']:
            if name not in self._singletons:
                self._singletons[name] = service_config['class']()
            return self._singletons[name]

        return service_config['class']()


# Service implementations
class DatabaseService:
    """Database service simulation"""

    def __init__(self):
        self.connection_count = 0
        self.queries_executed = 0

    def connect(self):
        """Simulate database connection"""
        self.connection_count += 1
        time.sleep(0.001)  # Simulate connection overhead
        return f"db_connection_{self.connection_count}"

    def query(self, sql: str):
        """Simulate database query"""
        self.queries_executed += 1
        time.sleep(0.002)  # Simulate query time
        return {
            "query": sql,
            "result": f"result_{self.queries_executed}",
            "execution_time": "2ms"
        }

    def get_stats(self):
        """Get database statistics"""
        return {
            "connections": self.connection_count,
            "queries": self.queries_executed
        }


class CacheService:
    """Cache service simulation"""

    def __init__(self):
        self.cache = {}
        self.hits = 0
        self.misses = 0

    def get(self, key: str):
        """Get value from cache"""
        if key in self.cache:
            self.hits += 1
            return self.cache[key]
        self.misses += 1
        return None

    def set(self, key: str, value: Any, ttl: int = 300):
        """Set value in cache"""
        self.cache[key] = {
            "value": value,
            "expires": time.time() + ttl
        }

    def get_stats(self):
        """Get cache statistics"""
        return {
            "hits": self.hits,
            "misses": self.misses,
            "hit_ratio": self.hits / (self.hits + self.misses) if (self.hits + self.misses) > 0 else 0
        }


class LoggerService:
    """Logger service simulation"""

    def __init__(self):
        self.logs = []

    def log(self, level: str, message: str):
        """Log a message"""
        self.logs.append({
            "level": level,
            "message": message,
            "timestamp": time.time()
        })

    def info(self, message: str):
        self.log("INFO", message)

    def error(self, message: str):
        self.log("ERROR", message)

    def get_logs(self):
        """Get all logs"""
        return self.logs[-100:]  # Return last 100 logs


class UserService:
    """User service simulation with dependencies"""

    def __init__(self):
        self.db = registry.get('database')
        self.cache = registry.get('cache')
        self.logger = registry.get('logger')

    def get_user(self, user_id: int):
        """Get user with caching"""
        cache_key = f"user_{user_id}"

        # Try cache first
        cached = self.cache.get(cache_key)
        if cached:
            self.logger.info(f"User {user_id} loaded from cache")
            return cached["value"]

        # Query database
        self.logger.info(f"Loading user {user_id} from database")
        result = self.db.query(f"SELECT * FROM users WHERE id = {user_id}")

        user_data = {
            "id": user_id,
            "name": f"User {user_id}",
            "email": f"user{user_id}@example.com",
            "created_at": time.time()
        }

        # Cache the result
        self.cache.set(cache_key, user_data)

        return user_data

    def create_user(self, user_data: Dict[str, Any]):
        """Create a new user"""
        self.logger.info(f"Creating user: {user_data.get('name', 'Unknown')}")

        # Simulate database insert
        result = self.db.query(f"INSERT INTO users (name, email) VALUES ('{user_data['name']}', '{user_data['email']}')")

        user_id = int(time.time() * 1000) % 10000  # Generate ID

        return {
            "id": user_id,
            "name": user_data["name"],
            "email": user_data["email"],
            "created_at": time.time()
        }


# Global service registry
registry = ServiceRegistry()
registry.register('database', DatabaseService, singleton=True)
registry.register('cache', CacheService, singleton=True)
registry.register('logger', LoggerService, singleton=True)
registry.register('user_service', UserService, singleton=False)  # New instance per request


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


# Django Views with dependency injection
def home(request):
    """Basic dependency injection test"""
    logger = registry.get('logger')
    logger.info("Home endpoint accessed")

    return JsonResponse({
        "message": "Django dependency injection test",
        "framework": "django",
        "services": list(registry._services.keys())
    })


def health_check(request):
    """Health check with service dependencies"""
    logger = registry.get('logger')
    db = registry.get('database')
    cache = registry.get('cache')

    logger.info("Health check performed")

    return JsonResponse({
        "status": "healthy",
        "framework": "django",
        "services": {
            "database": db.get_stats(),
            "cache": cache.get_stats(),
            "logger": {"log_count": len(logger.get_logs())}
        },
        "timestamp": time.time()
    })


def simple_service(request):
    """Simple service resolution test"""
    logger = registry.get('logger')
    logger.info("Simple service endpoint accessed")

    return JsonResponse({
        "message": "Simple service resolution",
        "framework": "django",
        "service_type": "logger",
        "log_count": len(logger.get_logs())
    })


def nested_services(request, user_id):
    """Nested service dependencies test"""
    user_service = registry.get('user_service')
    user_data = user_service.get_user(int(user_id))

    return JsonResponse({
        "message": "Nested service resolution",
        "framework": "django",
        "user": user_data,
        "services_used": ["user_service", "database", "cache", "logger"]
    })


@csrf_exempt
@require_http_methods(["POST"])
def create_user_endpoint(request):
    """User creation with dependency injection"""
    try:
        data = json.loads(request.body.decode('utf-8'))
        user_service = registry.get('user_service')
        user = user_service.create_user(data)

        return JsonResponse({
            "message": "User created successfully",
            "framework": "django",
            "user": user,
            "services_used": ["user_service", "database", "logger"]
        })
    except Exception as e:
        logger = registry.get('logger')
        logger.error(f"User creation failed: {str(e)}")
        return JsonResponse({"error": str(e)}, status=400)


def service_stats(request):
    """Service statistics endpoint"""
    db = registry.get('database')
    cache = registry.get('cache')
    logger = registry.get('logger')

    return JsonResponse({
        "message": "Service statistics",
        "framework": "django",
        "statistics": {
            "database": db.get_stats(),
            "cache": cache.get_stats(),
            "logger": {
                "total_logs": len(logger.get_logs()),
                "recent_logs": logger.get_logs()[-5:]  # Last 5 logs
            }
        },
        "timestamp": time.time()
    })


def complex_resolution(request):
    """Complex dependency resolution test"""
    # Create multiple service instances to test resolution overhead
    services = []
    for i in range(10):
        user_service = registry.get('user_service')
        services.append(user_service)

    # Perform operations with multiple services
    results = []
    for i, service in enumerate(services):
        user = service.get_user(i + 1)
        results.append({"service_id": i, "user_id": user["id"]})

    return JsonResponse({
        "message": "Complex dependency resolution",
        "framework": "django",
        "services_created": len(services),
        "operations": len(results),
        "results": results[:3]  # Return first 3 results
    })


def scoped_services(request):
    """Scoped service testing"""
    # Test singleton vs instance services
    db1 = registry.get('database')  # Singleton
    db2 = registry.get('database')  # Same instance

    user_service1 = registry.get('user_service')  # New instance
    user_service2 = registry.get('user_service')  # New instance

    return JsonResponse({
        "message": "Scoped service testing",
        "framework": "django",
        "singleton_test": {
            "db1_id": id(db1),
            "db2_id": id(db2),
            "same_instance": db1 is db2
        },
        "instance_test": {
            "service1_id": id(user_service1),
            "service2_id": id(user_service2),
            "different_instances": user_service1 is not user_service2
        }
    })


# URL Configuration
urlpatterns = [
    path('', home, name='home'),
    path('health', health_check, name='health_check'),
    path('simple-service', simple_service, name='simple_service'),
    path('nested-services/<int:user_id>', nested_services, name='nested_services'),
    path('create-user', create_user_endpoint, name='create_user'),
    path('service-stats', service_stats, name='service_stats'),
    path('complex-resolution', complex_resolution, name='complex_resolution'),
    path('scoped-services', scoped_services, name='scoped_services'),
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
    """Start the Django dependency injection benchmark server"""
    parser = argparse.ArgumentParser(description="Django Dependency Injection Benchmark Server")
    parser.add_argument("--port", type=int, default=8203, help="Port to run server on")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind to")
    parser.add_argument("--workers", type=int, default=1, help="Number of worker processes")
    args = parser.parse_args()

    print(f"🚀 Starting Django dependency injection benchmark server on {args.host}:{args.port}")
    print("📊 Django DI Features:")
    print("  🏭 Service registry pattern")
    print("  🔄 Singleton and instance scopes")
    print("  🧩 Nested service dependencies")
    print("  📊 Service statistics tracking")
    print()
    print("Available endpoints:")
    print("  GET  /                       - Basic DI test")
    print("  GET  /health                 - Health check with services")
    print("  GET  /simple-service         - Simple service resolution")
    print("  GET  /nested-services/{id}   - Nested service dependencies")
    print("  POST /create-user            - User creation with DI")
    print("  GET  /service-stats          - Service statistics")
    print("  GET  /complex-resolution     - Complex DI resolution")
    print("  GET  /scoped-services        - Scoped service testing")
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
        print("\n👋 Django dependency injection benchmark server stopped")


if __name__ == "__main__":
    main()
