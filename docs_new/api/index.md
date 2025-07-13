# 📖 API Reference

Complete API reference for Catzilla's **C-accelerated components** and **Python interfaces**. All APIs are designed for maximum performance while maintaining developer-friendly syntax.

## 🚀 Core APIs

### Primary Interfaces
- [Catzilla Application](app.md) - Main application class and configuration
- [Routing System](routing.md) - C-accelerated router and route definitions
- [Validation Engine](validation.md) - 100x faster validation with Pydantic compatibility
- [Background Tasks](background-tasks.md) - Revolutionary task system with C compilation

### Advanced Systems
- [Dependency Injection](dependency-injection.md) - C-optimized service resolution
- [Middleware System](middleware.md) - Zero-allocation middleware execution
- [Streaming](streaming.md) - High-performance streaming responses
- [Static Files](static-files.md) - Efficient static file serving

### Utilities & Types
- [Request/Response](request-response.md) - HTTP request and response objects
- [Types & Interfaces](types.md) - Core type definitions and protocols
- [Exceptions](exceptions.md) - Error handling and custom exceptions

## 🎯 Quick Reference

### Essential Imports

```python
# Core framework
from catzilla import (
    Catzilla,           # Main application class
    BaseModel,          # Validation models (Pydantic-compatible)
    Request,            # HTTP request object
    Response,           # HTTP response object
    JSONResponse,       # JSON response helper
    HTMLResponse,       # HTML response helper
    FileResponse,       # File response helper
    StreamingResponse,  # Streaming response
)

# Background tasks
from catzilla import (
    TaskPriority,       # Task priority levels
    TaskResult,         # Task result object
    BackgroundTasks,    # Task system class
)

# Dependency injection
from catzilla import (
    Depends,            # Dependency marker
    service,            # Service registration decorator
    DIContainer,        # DI container class
)

# Validation fields
from catzilla import (
    StringField,        # String validation
    IntField,           # Integer validation
    FloatField,         # Float validation
    BoolField,          # Boolean validation
    ListField,          # List validation
    OptionalField,      # Optional field wrapper
)

# Middleware
from catzilla.middleware import (
    CORSMiddleware,     # CORS handling
    RequestLoggingMiddleware,  # Request logging
)

# Types
from catzilla.types import (
    HTTPException,      # HTTP error exceptions
    ValidationError,    # Validation errors
    RequestState,       # Request state object
)
```

### Basic Application Structure

```python
from catzilla import Catzilla, BaseModel, Depends, service
from typing import Optional, List

# Create application with all features enabled
app = Catzilla(
    enable_background_tasks=True,
    enable_di=True,
    enable_jemalloc=True
)

# Define data models
class User(BaseModel):
    id: int
    name: str
    email: Optional[str] = None

# Define services
@service("user_service")
class UserService:
    def get_user(self, user_id: int) -> User:
        return User(id=user_id, name=f"User {user_id}")

# Define routes
@app.get("/users/{user_id}")
def get_user(
    user_id: int,
    user_service: UserService = Depends("user_service")
) -> User:
    return user_service.get_user(user_id)

# Background tasks
@app.post("/notify")
def send_notification(message: str):
    task = app.add_task(lambda: print(f"Notification: {message}"))
    return {"task_id": task.task_id}

# Start server
if __name__ == "__main__":
    app.listen(port=8000)
```

## 📚 API Categories

### Core Framework APIs

#### Application Management
```python
class Catzilla:
    def __init__(
        self,
        enable_background_tasks: bool = False,
        enable_di: bool = False,
        enable_jemalloc: bool = False,
        workers: Optional[int] = None,
        **kwargs
    ) -> None: ...

    def listen(
        self,
        host: str = "127.0.0.1",
        port: int = 8000,
        **kwargs
    ) -> None: ...

    def mount_static(
        self,
        path: str,
        directory: str,
        **options
    ) -> None: ...
```

#### Route Decorators
```python
# HTTP method decorators
@app.get(path: str, **options)
@app.post(path: str, **options)
@app.put(path: str, **options)
@app.delete(path: str, **options)
@app.patch(path: str, **options)
@app.head(path: str, **options)
@app.options(path: str, **options)

# Generic route decorator
@app.route(path: str, methods: List[str], **options)
```

### Validation APIs

#### BaseModel (Pydantic-compatible)
```python
class BaseModel:
    def __init__(self, **data) -> None: ...
    def dict(self) -> dict: ...
    def json(self) -> str: ...

    @classmethod
    def parse_obj(cls, obj: dict): ...

    @classmethod
    def parse_raw(cls, data: str): ...
```

#### Validation Fields
```python
class StringField:
    def __init__(
        self,
        min_len: Optional[int] = None,
        max_len: Optional[int] = None,
        pattern: Optional[str] = None,
        **kwargs
    ) -> None: ...

class IntField:
    def __init__(
        self,
        min: Optional[int] = None,
        max: Optional[int] = None,
        **kwargs
    ) -> None: ...

class FloatField:
    def __init__(
        self,
        min: Optional[float] = None,
        max: Optional[float] = None,
        **kwargs
    ) -> None: ...
```

### Background Task APIs

#### Task Management
```python
class BackgroundTasks:
    def add_task(
        self,
        func: Callable,
        *args,
        priority: TaskPriority = TaskPriority.NORMAL,
        delay_ms: int = 0,
        max_retries: int = 3,
        timeout_ms: int = 30000,
        compile_to_c: Optional[bool] = None,
        **kwargs
    ) -> TaskResult: ...

    def get_stats(self) -> EngineStats: ...

    def shutdown(
        self,
        wait_for_completion: bool = True,
        timeout: float = 30.0
    ) -> None: ...

class TaskPriority(Enum):
    CRITICAL = 0
    HIGH = 1
    NORMAL = 2
    LOW = 3

class TaskResult:
    @property
    def task_id(self) -> str: ...

    def wait(self, timeout: Optional[float] = None): ...

    def is_complete(self) -> bool: ...
```

### Dependency Injection APIs

#### Service Registration
```python
def service(
    name: str,
    scope: str = "singleton"  # "singleton", "request", "transient"
) -> Callable: ...

def Depends(
    service_name: str
) -> Any: ...

class DIContainer:
    def register(
        self,
        name: str,
        factory: Callable,
        scope: str = "singleton"
    ) -> None: ...

    def resolve(
        self,
        name: str,
        context: Optional[Any] = None
    ) -> Any: ...
```

### Response APIs

#### Response Classes
```python
class Response:
    def __init__(
        self,
        content: Any = None,
        status_code: int = 200,
        headers: Optional[dict] = None,
        media_type: Optional[str] = None
    ) -> None: ...

class JSONResponse(Response):
    def __init__(
        self,
        content: Any,
        status_code: int = 200,
        headers: Optional[dict] = None
    ) -> None: ...

class HTMLResponse(Response):
    def __init__(
        self,
        content: str,
        status_code: int = 200,
        headers: Optional[dict] = None
    ) -> None: ...

class FileResponse(Response):
    def __init__(
        self,
        path: str,
        status_code: int = 200,
        headers: Optional[dict] = None,
        media_type: Optional[str] = None,
        filename: Optional[str] = None
    ) -> None: ...

class StreamingResponse(Response):
    def __init__(
        self,
        content: Callable,
        status_code: int = 200,
        headers: Optional[dict] = None,
        media_type: Optional[str] = None
    ) -> None: ...
```

## 🔧 Configuration Reference

### Application Configuration

```python
app = Catzilla(
    # Core settings
    debug: bool = False,
    title: str = "Catzilla App",
    description: str = "",
    version: str = "1.0.0",

    # Performance settings
    enable_jemalloc: bool = True,           # 30% memory optimization
    enable_c_acceleration: bool = True,      # C-speed core features
    workers: Optional[int] = None,           # Worker processes (default: CPU count)

    # Background tasks
    enable_background_tasks: bool = False,
    task_workers: int = 4,
    task_queue_size: int = 10000,
    enable_task_c_compilation: bool = True,

    # Dependency injection
    enable_di: bool = False,
    di_auto_register: bool = True,

    # Static files
    static_cache_size_mb: int = 100,
    static_enable_compression: bool = True,
    static_enable_hot_cache: bool = True,

    # Middleware
    enable_cors: bool = False,
    enable_request_logging: bool = False,

    # Memory management
    memory_pool_mb: int = 256,
    enable_memory_profiling: bool = False,
)
```

### Environment Variables

```bash
# Performance optimization
export CATZILLA_ENABLE_JEMALLOC=1
export CATZILLA_ENABLE_C_ACCELERATION=1
export CATZILLA_WORKERS=4

# Memory settings
export CATZILLA_MEMORY_POOL_SIZE=512MB
export CATZILLA_ENABLE_MEMORY_PROFILING=0

# Background tasks
export CATZILLA_TASK_WORKERS=8
export CATZILLA_TASK_QUEUE_SIZE=50000
export CATZILLA_ENABLE_TASK_C_COMPILATION=1

# Development settings
export CATZILLA_DEBUG=0
export CATZILLA_LOG_LEVEL=INFO

# Static files
export CATZILLA_STATIC_CACHE_SIZE=200MB
export CATZILLA_STATIC_COMPRESSION=1
```

## 🧪 Testing APIs

### Test Utilities

```python
from catzilla.testing import TestClient

def test_my_app():
    client = TestClient(app)

    # Test GET request
    response = client.get("/users/123")
    assert response.status_code == 200
    assert response.json()["user_id"] == 123

    # Test POST request
    response = client.post("/users", json={
        "name": "Alice",
        "email": "alice@example.com"
    })
    assert response.status_code == 201

    # Test with dependency injection
    with client.di_override("user_service", MockUserService()):
        response = client.get("/users/456")
        assert response.json()["name"] == "Mock User"
```

## 📊 Performance Monitoring APIs

### Statistics and Metrics

```python
# Application performance
app_stats = app.get_performance_stats()
# Returns: {
#   "requests_per_second": 50000,
#   "average_response_time_ms": 0.5,
#   "memory_usage_mb": 45,
#   "c_acceleration_enabled": True,
#   "jemalloc_enabled": True
# }

# Background task performance
task_stats = app.tasks.get_stats()
# Returns EngineStats object with detailed metrics

# Memory statistics
memory_stats = app.get_memory_stats()
# Returns: {
#   "total_allocated_mb": 45,
#   "jemalloc_efficiency": 0.30,
#   "gc_pressure": "low",
#   "arena_usage": {...}
# }

# Dependency injection performance
di_stats = app.di_container.get_stats()
# Returns: {
#   "resolution_time_ns": 10,
#   "services_registered": 15,
#   "cache_hit_rate": 0.95
# }
```

## 🚀 Next Steps

Explore specific API documentation:

- **[Catzilla Application →](app.md)** - Complete application API
- **[Validation Engine →](validation.md)** - Validation and field APIs
- **[Background Tasks →](background-tasks.md)** - Task system APIs
- **[Dependency Injection →](dependency-injection.md)** - DI system APIs

### Quick Links
- [Examples Gallery](../examples/index.md) - Real-world usage examples
- [Performance Guide](../performance/index.md) - Optimization and benchmarks
- [Migration Guide](../migration/index.md) - Migrate from other frameworks

---

*Complete API reference for the fastest Python web framework ever built!* 📚
