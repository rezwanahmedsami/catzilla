# 🏢 Advanced Dependency Injection Guide

**Enterprise features and production patterns**

This guide covers advanced DI concepts for building production-ready applications with complex dependency graphs, service scopes, health monitoring, and performance optimization.

---

## 📋 What You'll Learn

- 🏗️ **Service Scopes** - singleton, request, transient lifecycles
- 📊 **Health Monitoring** - Service status and diagnostics
- ⚡ **Performance Optimization** - Memory management and caching
- 🔄 **Service Composition** - Complex dependency chains
- 🛡️ **Thread Safety** - Concurrent request handling
- 📈 **Analytics & Logging** - Request tracking and metrics

**Time required: ~30 minutes**

---

## 🏃‍♂️ Quick Setup

### 1. Run the Advanced Example
```bash
./scripts/run_example.sh examples/advanced_di/main.py

# Test advanced features
curl http://localhost:8001/health        # Health monitoring
curl http://localhost:8001/demo-scopes   # Service scopes demo
curl http://localhost:8001/di-info       # DI system information
```

### 2. Architecture Overview
```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Route Layer   │───▶│  Business Logic  │───▶│ Infrastructure  │
│                 │    │                  │    │                 │
│ • /users        │    │ • UserService    │    │ • DatabaseService│
│ • /products     │    │ • ProductService │    │ • CacheService  │
│ • /health       │    │ • Analytics      │    │ • Configuration │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 ▼
                    ┌─────────────────────────┐
                    │   DI Container          │
                    │ • Service Registration  │
                    │ • Scope Management      │
                    │ • Dependency Resolution │
                    │ • Performance Monitoring│
                    └─────────────────────────┘
```

---

## 🏗️ Service Scopes Deep Dive

Service scopes control when and how service instances are created and shared.

### 1. Singleton Scope (Default)
**One instance shared across the entire application**

```python
@service("config", scope="singleton")
class AppConfig:
    def __init__(self):
        self.database_url = "postgresql://localhost:5432/app"
        self.cache_ttl = 3600
        print("🔧 Config service initialized")  # Only printed once

@service("database", scope="singleton")
class DatabaseService:
    def __init__(self, config: AppConfig = Depends("config")):
        self.config = config
        self.connection_pool = self._create_pool()
        print("💾 Database connected")  # Only printed once

    def _create_pool(self):
        # Expensive operation done only once
        time.sleep(0.1)  # Simulate connection setup
        return f"ConnectionPool({self.config.database_url})"
```

**Use Cases:**
- ✅ Configuration services
- ✅ Database connection pools
- ✅ Expensive-to-create services
- ✅ Stateless business logic services

### 2. Request Scope
**One instance per HTTP request**

```python
@service("request_logger", scope="request")
class RequestLogger:
    def __init__(self):
        self.request_id = f"req_{int(time.time() * 1000) % 100000}"
        self.start_time = time.time()
        self.logs = []
        print(f"📝 Request logger created: {self.request_id}")

    def log(self, message: str):
        timestamp = time.time() - self.start_time
        self.logs.append(f"[{timestamp:.3f}s] {message}")

    def get_logs(self):
        return self.logs

# Multiple injections in same request = same instance
@app.get("/test-request-scope")
def test_request_scope(request,
                      logger1: RequestLogger = Depends("request_logger"),
                      logger2: RequestLogger = Depends("request_logger")):
    logger1.log("First log")
    logger2.log("Second log")  # Same logger instance!

    return {
        "same_instance": logger1 is logger2,  # True
        "request_id": logger1.request_id,
        "logs": logger1.get_logs()  # Contains both logs
    }
```

**Use Cases:**
- ✅ Request-specific logging
- ✅ User session data
- ✅ Request metrics and tracing
- ✅ Temporary state during request processing

### 3. Transient Scope
**New instance every time it's injected**

```python
@service("analytics", scope="transient")
class AnalyticsService:
    def __init__(self, config: AppConfig = Depends("config")):
        self.config = config
        self.timestamp = datetime.now()
        self.session_id = uuid.uuid4()
        print(f"📊 Analytics service created at {self.timestamp}")

    def track_event(self, event: str, data: dict = None):
        return {
            "event": event,
            "timestamp": self.timestamp.isoformat(),
            "session_id": str(self.session_id),
            "data": data or {},
            "app_version": self.config.version
        }

# Multiple injections = different instances
@app.get("/test-transient-scope")
def test_transient_scope(request,
                        analytics1: AnalyticsService = Depends("analytics"),
                        analytics2: AnalyticsService = Depends("analytics")):
    return {
        "same_instance": analytics1 is analytics2,  # False
        "analytics1_session": str(analytics1.session_id),
        "analytics2_session": str(analytics2.session_id),
        "timestamps": {
            "analytics1": analytics1.timestamp.isoformat(),
            "analytics2": analytics2.timestamp.isoformat()
        }
    }
```

**Use Cases:**
- ✅ Event tracking and analytics
- ✅ Stateful operations that need isolation
- ✅ Services that should not share state
- ✅ Testing and mocking scenarios

---

## 📊 Health Monitoring System

### 1. Service Health Checks

```python
@app.get("/health")
def health_check(request,
                config: AppConfig = Depends("config"),
                db: DatabaseService = Depends("database"),
                cache: CacheService = Depends("cache"),
                logger: RequestLogger = Depends("request_logger")):
    """Comprehensive health check endpoint"""

    logger.log("Health check requested")

    # Check database connectivity
    try:
        db_status = "connected" if db.connection_pool else "disconnected"
        user_count = len(db.get_all_users())
        product_count = len(db.products)
    except Exception as e:
        db_status = f"error: {str(e)}"
        user_count = product_count = 0

    # Get cache statistics
    cache_stats = cache.get_stats()

    return JSONResponse({
        "status": "healthy" if db_status == "connected" else "degraded",
        "timestamp": datetime.now().isoformat(),
        "app": {
            "name": config.app_name,
            "version": config.version,
            "debug": config.debug
        },
        "services": {
            "database": {
                "status": db_status,
                "connection_pool": str(db.connection_pool),
                "users_count": user_count,
                "products_count": product_count
            },
            "cache": cache_stats,
            "dependency_injection": {
                "status": "active",
                "container_type": "Catzilla Revolutionary DI v0.2.0"
            }
        },
        "request_info": {
            "request_id": logger.request_id,
            "logs": logger.get_logs()
        }
    })
```

### 2. DI System Information

```python
@app.get("/di-info")
def di_info(request,
           config: AppConfig = Depends("config"),
           logger: RequestLogger = Depends("request_logger")):
    """Detailed dependency injection system information"""

    logger.log("DI info requested")

    services_info = {
        "config": {"scope": "singleton", "status": "registered"},
        "database": {"scope": "singleton", "status": "registered"},
        "cache": {"scope": "singleton", "status": "registered"},
        "user_service": {"scope": "singleton", "status": "registered"},
        "product_service": {"scope": "singleton", "status": "registered"},
        "request_logger": {"scope": "request", "status": "registered"},
        "analytics": {"scope": "transient", "status": "registered"}
    }

    return JSONResponse({
        "dependency_injection_info": {
            "container": {
                "name": "Catzilla Revolutionary DI v0.2.0",
                "services_count": len(services_info),
                "features": [
                    "6.5x faster dependency resolution",
                    "31% memory reduction with arena allocation",
                    "Sub-millisecond DI overhead",
                    "Multiple service scopes (singleton, request, transient)",
                    "Thread-safe concurrent access"
                ]
            },
            "services": services_info,
            "performance": {
                "resolution_speed": "6.5x faster than pure Python",
                "memory_efficiency": "31% memory reduction",
                "overhead": "Sub-millisecond dependency injection"
            }
        },
        "request_id": logger.request_id
    })
```

---

## 🔄 Service Composition Patterns

### 1. Layered Architecture

```python
# Infrastructure Layer
@service("database", scope="singleton")
class DatabaseService:
    def get_users(self): return [...]
    def get_products(self): return [...]

@service("cache", scope="singleton")
class CacheService:
    def get(self, key): return None
    def set(self, key, value): pass

# Business Logic Layer
@service("user_service", scope="singleton")
class UserService:
    def __init__(self,
                 database: DatabaseService = Depends("database"),
                 cache: CacheService = Depends("cache")):
        self.db = database
        self.cache = cache

    def get_user_with_caching(self, user_id: int, logger: RequestLogger):
        """Business logic: get user with caching strategy"""
        cache_key = f"user:{user_id}"

        # Try cache first
        cached_user = self.cache.get(cache_key)
        if cached_user:
            logger.log(f"User {user_id} found in cache")
            return cached_user

        # Get from database
        user = self.db.get_user(user_id)
        if user:
            self.cache.set(cache_key, user)
            logger.log(f"User {user_id} cached from database")

        return user

@service("product_service", scope="singleton")
class ProductService:
    def __init__(self,
                 database: DatabaseService = Depends("database"),
                 cache: CacheService = Depends("cache")):
        self.db = database
        self.cache = cache

    def search_products(self, category: str, logger: RequestLogger):
        """Business logic: search with caching"""
        cache_key = f"products:category:{category}"

        cached_products = self.cache.get(cache_key)
        if cached_products:
            logger.log(f"Products for '{category}' found in cache")
            return cached_products

        products = self.db.get_products_by_category(category)
        self.cache.set(cache_key, products)
        logger.log(f"Cached {len(products)} products for '{category}'")

        return products
```

### 2. Cross-Cutting Concerns

```python
# Analytics as a cross-cutting concern
@service("analytics", scope="transient")
class AnalyticsService:
    def __init__(self, config: AppConfig = Depends("config")):
        self.config = config
        self.timestamp = datetime.now()

    def track_request(self, endpoint: str, user_id: int = None):
        return {
            "timestamp": self.timestamp.isoformat(),
            "endpoint": endpoint,
            "user_id": user_id,
            "app_version": self.config.version,
            "instance_id": id(self)
        }

# Use analytics across multiple endpoints
@app.get("/users/{user_id}")
def get_user(request,
            user_id: int,
            user_service: UserService = Depends("user_service"),
            analytics: AnalyticsService = Depends("analytics"),
            logger: RequestLogger = Depends("request_logger")):

    # Business logic
    user = user_service.get_user_with_caching(user_id, logger)

    # Cross-cutting concerns
    analytics_data = analytics.track_request(f"/users/{user_id}", user_id)

    if not user:
        return JSONResponse({
            "error": f"User {user_id} not found",
            "request_logs": logger.get_logs(),
            "analytics": analytics_data
        }, status_code=404)

    return JSONResponse({
        "user": user,
        "request_logs": logger.get_logs(),
        "analytics": analytics_data
    })
```

---

## ⚡ Performance Optimization

### 1. Memory Management with jemalloc

```python
# Configure Catzilla for optimal performance
app = Catzilla(
    auto_validation=True,      # FastAPI-style validation
    memory_profiling=True,     # Monitor memory usage
    enable_di=True,           # Enable dependency injection
    use_jemalloc=True,        # 31% memory reduction
    auto_memory_tuning=True   # Adaptive memory management
)
```

### 2. Caching Strategies

```python
@service("cache", scope="singleton")
class CacheService:
    def __init__(self, config: AppConfig = Depends("config")):
        self.config = config
        self.cache = {}
        self.hit_count = 0
        self.miss_count = 0
        self.ttl_map = {}  # Time-to-live tracking

    def get(self, key: str):
        # Check if key exists and hasn't expired
        if key in self.cache:
            if key in self.ttl_map:
                if time.time() > self.ttl_map[key]:
                    # Expired
                    del self.cache[key]
                    del self.ttl_map[key]
                    self.miss_count += 1
                    return None

            self.hit_count += 1
            return self.cache[key]

        self.miss_count += 1
        return None

    def set(self, key: str, value, ttl: int = None):
        self.cache[key] = value
        if ttl:
            self.ttl_map[key] = time.time() + ttl

    def get_stats(self):
        total = self.hit_count + self.miss_count
        hit_rate = (self.hit_count / total * 100) if total > 0 else 0

        return {
            "hit_count": self.hit_count,
            "miss_count": self.miss_count,
            "hit_rate": f"{hit_rate:.1f}%",
            "cache_size": len(self.cache),
            "memory_efficiency": "31% reduction with arena allocation"
        }
```

### 3. Lazy Loading and Connection Pooling

```python
@service("database", scope="singleton")
class DatabaseService:
    def __init__(self, config: AppConfig = Depends("config")):
        self.config = config
        self._connection_pool = None  # Lazy initialization
        self._users_cache = None
        self._products_cache = None

    @property
    def connection_pool(self):
        """Lazy-loaded connection pool"""
        if self._connection_pool is None:
            print("💾 Creating database connection pool...")
            time.sleep(0.1)  # Simulate connection setup
            self._connection_pool = f"ConnectionPool({self.config.database_url})"
        return self._connection_pool

    @property
    def users(self):
        """Lazy-loaded users data"""
        if self._users_cache is None:
            print("👥 Loading users from database...")
            self._users_cache = [
                {"id": 1, "name": "Alice Johnson", "email": "alice@example.com"},
                {"id": 2, "name": "Bob Smith", "email": "bob@example.com"},
                {"id": 3, "name": "Carol Brown", "email": "carol@example.com"}
            ]
        return self._users_cache

    @property
    def products(self):
        """Lazy-loaded products data"""
        if self._products_cache is None:
            print("🛍️  Loading products from database...")
            self._products_cache = [
                {"id": 1, "name": "Laptop", "price": 999.99, "category": "electronics"},
                {"id": 2, "name": "Coffee Mug", "price": 12.99, "category": "home"},
                {"id": 3, "name": "Python Book", "price": 39.99, "category": "books"}
            ]
        return self._products_cache
```

---

## 🛡️ Thread Safety and Concurrency

### 1. Thread-Safe Services

```python
import threading
from threading import Lock

@service("counter", scope="singleton")
class ThreadSafeCounter:
    def __init__(self):
        self._value = 0
        self._lock = Lock()

    def increment(self):
        with self._lock:
            self._value += 1
            return self._value

    def get_value(self):
        with self._lock:
            return self._value

@service("request_tracker", scope="singleton")
class RequestTracker:
    def __init__(self):
        self._requests = {}
        self._lock = Lock()

    def track_request(self, endpoint: str):
        with self._lock:
            if endpoint not in self._requests:
                self._requests[endpoint] = 0
            self._requests[endpoint] += 1
            return self._requests[endpoint]

    def get_stats(self):
        with self._lock:
            return dict(self._requests)
```

### 2. Request Isolation

```python
@service("request_context", scope="request")
class RequestContext:
    def __init__(self):
        self.user_id = None
        self.session_id = None
        self.permissions = []
        self.metadata = {}

    def set_user(self, user_id: int, permissions: list = None):
        self.user_id = user_id
        self.permissions = permissions or []

    def has_permission(self, permission: str):
        return permission in self.permissions

    def set_metadata(self, key: str, value):
        self.metadata[key] = value

# Each request gets its own context
@app.get("/secure-endpoint")
def secure_endpoint(request,
                   context: RequestContext = Depends("request_context"),
                   user_service: UserService = Depends("user_service")):

    # Set user context
    context.set_user(123, ["read", "write"])
    context.set_metadata("source", "api")

    if not context.has_permission("read"):
        return {"error": "Insufficient permissions"}, 403

    # Proceed with business logic
    return {"message": "Access granted", "user_id": context.user_id}
```

---

## 📈 Production Deployment Patterns

### 1. Environment-Based Configuration

```python
import os

@service("config", scope="singleton")
class AppConfig:
    def __init__(self):
        self.environment = os.getenv("ENVIRONMENT", "development")

        if self.environment == "production":
            self.database_url = os.getenv("DATABASE_URL")
            self.cache_ttl = 7200  # 2 hours
            self.debug = False
            self.log_level = "INFO"
        elif self.environment == "staging":
            self.database_url = os.getenv("STAGING_DATABASE_URL")
            self.cache_ttl = 3600  # 1 hour
            self.debug = True
            self.log_level = "DEBUG"
        else:  # development
            self.database_url = "sqlite:///dev.db"
            self.cache_ttl = 300   # 5 minutes
            self.debug = True
            self.log_level = "DEBUG"

        print(f"🔧 Config initialized for {self.environment} environment")
```

### 2. Graceful Shutdown

```python
import signal
import sys

@service("shutdown_handler", scope="singleton")
class ShutdownHandler:
    def __init__(self,
                 db: DatabaseService = Depends("database"),
                 cache: CacheService = Depends("cache")):
        self.db = db
        self.cache = cache
        self.is_shutting_down = False

        # Register shutdown handlers
        signal.signal(signal.SIGINT, self._handle_shutdown)
        signal.signal(signal.SIGTERM, self._handle_shutdown)

    def _handle_shutdown(self, signum, frame):
        if self.is_shutting_down:
            return

        self.is_shutting_down = True
        print("🛑 Graceful shutdown initiated...")

        # Close database connections
        if hasattr(self.db, 'close'):
            self.db.close()

        # Clear cache
        self.cache.cache.clear()

        print("✅ Shutdown complete")
        sys.exit(0)

    def health_check(self):
        return not self.is_shutting_down
```

---

## 🧪 Testing Strategies

### 1. Service Mocking

```python
# Test doubles
class MockDatabaseService:
    def __init__(self):
        self.users = [{"id": 1, "name": "Test User"}]

    def get_user(self, user_id: int):
        return self.users[0] if user_id == 1 else None

# Test with mocked services
def test_user_endpoint():
    from catzilla.dependency_injection import DIContainer

    # Create test container
    test_container = DIContainer()
    test_container.register("database", MockDatabaseService, scope="singleton")

    # Create app with test container
    app = Catzilla(enable_di=True)
    app.di_container = test_container

    # Test the endpoint
    response = app.test_client.get("/users/1")
    assert response.status_code == 200
    assert response.json()["user"]["name"] == "Test User"
```

### 2. Integration Testing

```python
import pytest
from catzilla.testing import TestClient

@pytest.fixture
def test_app():
    """Create test app with real services"""
    app = Catzilla(enable_di=True)

    # Override config for testing
    @service("config", scope="singleton")
    class TestConfig:
        def __init__(self):
            self.database_url = "sqlite:///:memory:"
            self.debug = True

    return app

def test_health_endpoint(test_app):
    client = TestClient(test_app)

    response = client.get("/health")
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "healthy"
    assert "services" in data
    assert "dependency_injection" in data["services"]
```

---

## 🎯 Best Practices

### 1. Service Design Principles

**✅ DO:**
- Keep services focused on a single responsibility
- Use constructor injection for required dependencies
- Make services stateless when possible
- Use appropriate scopes for service lifecycles
- Implement proper error handling

**❌ DON'T:**
- Create circular dependencies
- Mix business logic with infrastructure concerns
- Use global state in services
- Ignore thread safety in singleton services
- Leak implementation details through interfaces

### 2. Performance Guidelines

**✅ DO:**
- Use singleton scope for expensive-to-create services
- Implement lazy loading for optional dependencies
- Cache frequently accessed data
- Monitor memory usage and service creation costs
- Use request scope for request-specific state

**❌ DON'T:**
- Create unnecessary transient services
- Ignore caching opportunities
- Hold onto expensive resources longer than needed
- Forget to implement connection pooling
- Mix different concerns in the same service

### 3. Error Handling

```python
@service("error_handler", scope="singleton")
class ErrorHandler:
    def __init__(self, logger: RequestLogger = Depends("request_logger")):
        self.logger = logger

    def handle_service_error(self, service_name: str, error: Exception):
        self.logger.log(f"Service error in {service_name}: {str(error)}")

        if isinstance(error, ConnectionError):
            return {"error": "Service temporarily unavailable", "code": "SERVICE_DOWN"}
        elif isinstance(error, ValueError):
            return {"error": "Invalid request", "code": "INVALID_INPUT"}
        else:
            return {"error": "Internal server error", "code": "INTERNAL_ERROR"}

@app.get("/robust-endpoint")
def robust_endpoint(request,
                   user_service: UserService = Depends("user_service"),
                   error_handler: ErrorHandler = Depends("error_handler")):
    try:
        return user_service.get_all_users()
    except Exception as e:
        error_response = error_handler.handle_service_error("user_service", e)
        return JSONResponse(error_response, status_code=500)
```

---

## 🎓 Next Steps

**🎉 Congratulations!** You now have a deep understanding of Catzilla's advanced dependency injection features.

### Continue Learning

1. **Real-world Use Cases** → [Use Cases & Examples](di_use_cases.md)
2. **Performance Optimization** → [Performance Guide](di_performance.md)
3. **FastAPI Migration** → [Migration Guide](migration_from_fastapi.md)
4. **API Reference** → [Complete API Documentation](di_api_reference.md)

### Build Something Amazing

Try implementing these advanced patterns:

1. **Microservices Architecture** with service discovery
2. **Event-Driven System** with async message handling
3. **Multi-tenant Application** with tenant-scoped services
4. **Monitoring Dashboard** with real-time metrics

**Ready to revolutionize your architecture?** 🚀
