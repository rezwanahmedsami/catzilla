# 🚀 Catzilla Application API

The `Catzilla` class is the **core of your high-performance application**. It provides C-accelerated routing, automatic memory optimization, and revolutionary features for building fast web APIs.

## Class Definition

```python
from catzilla import Catzilla

class Catzilla:
    """
    High-performance web application with C-accelerated core.

    Features:
    - 10x faster routing with C-compiled trie
    - 30% memory reduction with jemalloc
    - 100x faster validation engine
    - Revolutionary background task system
    - Zero-allocation middleware execution
    """
```

## Constructor

### `Catzilla()`

```python
def __init__(
    self,
    # Core settings
    debug: bool = False,
    title: str = "Catzilla App",
    description: str = "",
    version: str = "1.0.0",

    # Performance optimization
    enable_jemalloc: bool = True,           # 30% memory optimization
    enable_c_acceleration: bool = True,      # C-speed core features
    workers: Optional[int] = None,           # Worker processes

    # Background tasks
    enable_background_tasks: bool = False,
    task_workers: int = 4,
    task_queue_size: int = 10000,
    enable_task_c_compilation: bool = True,

    # Dependency injection
    enable_di: bool = False,
    di_auto_register: bool = True,
    di_c_optimization: bool = True,

    # Static files
    static_cache_size_mb: int = 100,
    static_enable_compression: bool = True,
    static_enable_hot_cache: bool = True,

    # Middleware
    enable_cors: bool = False,
    enable_request_logging: bool = False,
    middleware_c_compilation: bool = True,

    # Memory management
    memory_pool_mb: int = 256,
    enable_memory_profiling: bool = False,

    # Validation
    validation_strict_mode: bool = True,
    validation_c_acceleration: bool = True,

    **kwargs
) -> None:
    """
    Create a new Catzilla application with C-accelerated performance.

    Args:
        debug: Enable debug mode (disables C acceleration for debugging)
        title: Application title for documentation
        description: Application description
        version: Application version

        enable_jemalloc: Use jemalloc for 30% memory optimization
        enable_c_acceleration: Enable C-compiled core features
        workers: Number of worker processes (default: CPU count)

        enable_background_tasks: Enable revolutionary task system
        task_workers: Number of background task workers
        task_queue_size: Maximum tasks in queue
        enable_task_c_compilation: Auto-compile tasks to C

        enable_di: Enable C-optimized dependency injection
        di_auto_register: Automatically register services
        di_c_optimization: Use C-compiled service resolution

        static_cache_size_mb: Static file cache size in MB
        static_enable_compression: Enable static file compression
        static_enable_hot_cache: Enable hot cache for static files

        enable_cors: Enable CORS middleware
        enable_request_logging: Enable request logging middleware
        middleware_c_compilation: Compile middleware to C

        memory_pool_mb: Memory pool size for optimization
        enable_memory_profiling: Enable memory profiling

        validation_strict_mode: Strict validation mode
        validation_c_acceleration: Use C-accelerated validation
    """
```

**Example:**

```python
from catzilla import Catzilla

# High-performance production app
app = Catzilla(
    title="My API",
    description="C-accelerated high-performance API",

    # Enable all performance features
    enable_jemalloc=True,           # 30% memory reduction
    enable_c_acceleration=True,     # C-speed routing
    enable_background_tasks=True,   # Revolutionary task system
    enable_di=True,                 # C-optimized DI

    # Production settings
    workers=8,                      # 8 worker processes
    task_workers=16,                # 16 task workers
    static_cache_size_mb=500,       # 500MB static cache
    memory_pool_mb=1024,            # 1GB memory pool
)

# Development app with debugging
dev_app = Catzilla(
    debug=True,                     # Debug mode
    enable_c_acceleration=False,    # Disable C for debugging
    enable_memory_profiling=True,   # Memory profiling
)
```

## Core Methods

### Server Management

#### `listen()`

```python
def listen(
    self,
    host: str = "127.0.0.1",
    port: int = 8000,
    workers: Optional[int] = None,
    access_log: bool = True,
    **kwargs
) -> None:
    """
    Start the high-performance server with C-accelerated request handling.

    Args:
        host: Host to bind to
        port: Port to bind to
        workers: Number of worker processes (overrides constructor)
        access_log: Enable access logging
        **kwargs: Additional server options
    """
```

**Example:**

```python
# Development server
app.listen()  # Default: 127.0.0.1:8000

# Production server
app.listen(
    host="0.0.0.0",
    port=80,
    workers=16,        # 16 worker processes
    access_log=True    # Enable access logs
)

# Custom configuration
app.listen(
    host="api.example.com",
    port=443,
    ssl_keyfile="server.key",
    ssl_certfile="server.crt",
    workers=32
)
```

### Route Registration

#### HTTP Method Decorators

```python
@app.get(path: str, **options)
@app.post(path: str, **options)
@app.put(path: str, **options)
@app.delete(path: str, **options)
@app.patch(path: str, **options)
@app.head(path: str, **options)
@app.options(path: str, **options)
```

**Parameters:**
- `path`: URL pattern with C-accelerated matching
- `overwrite`: Whether to overwrite existing routes (default: False)
- `dependencies`: Route-level dependency injection list
- `middleware`: Per-route middleware functions
- `tags`: Tags for documentation
- `summary`: Short description
- `description`: Detailed description

**Example:**

```python
from catzilla import Catzilla, BaseModel, Response
from typing import List, Optional

app = Catzilla(enable_c_acceleration=True)

class User(BaseModel):
    id: int
    name: str
    email: Optional[str] = None

# GET route with C-accelerated routing
@app.get("/users/{user_id}")
def get_user(request, user_id: int) -> User:
    """Get user by ID - executed at C speed!"""
    return User(id=user_id, name=f"User {user_id}")

# POST route with validation
@app.post("/users")
def create_user(request, user: User) -> User:
    """Create new user with 100x faster validation"""
    print(f"Created user: {user.name}")
    return user

# Complex route with multiple parameters
@app.get("/users")
def list_users(
    request,
    page: int = 1,
    limit: int = 10,
    search: Optional[str] = None
) -> List[User]:
    """List users with C-accelerated parameter parsing"""
    users = []
    start = (page - 1) * limit
    for i in range(start, start + limit):
        users.append(User(id=i, name=f"User {i}"))
    return users

# File upload with streaming
@app.post("/upload")
def upload_file(file: UploadFile) -> dict:
    """Handle file upload with C-accelerated streaming"""
    return {"filename": file.filename, "size": file.size}
```

#### Generic Route Decorator

```python
@app.route(
    path: str,
    methods: List[str],
    **options
)
def handler_function():
    pass
```

**Example:**

```python
# Handle multiple methods
@app.route("/api/data", methods=["GET", "POST", "PUT"])
def handle_data(request: Request):
    if request.method == "GET":
        return {"data": "reading"}
    elif request.method == "POST":
        return {"data": "created"}
    elif request.method == "PUT":
        return {"data": "updated"}

# WebSocket route (coming soon)
@app.route("/ws", methods=["WEBSOCKET"])
def websocket_handler(websocket: WebSocket):
    # Handle WebSocket connections
    pass
```

### Static File Serving

#### `mount_static()`

```python
def mount_static(
    self,
    path: str,
    directory: str,
    name: str = "static",
    check_dir: bool = True,
    enable_hot_cache: bool = True,
    cache_size_mb: int = 100,
    enable_compression: bool = True,
    cache_headers: bool = True,
    **kwargs
) -> None:
    """
    Mount static files with C-accelerated serving and hot caching.

    Args:
        path: URL path prefix (e.g., "/static")
        directory: Local directory to serve
        name: Mount name for URL generation
        check_dir: Check if directory exists
        enable_hot_cache: Enable hot cache for faster serving
        cache_size_mb: Cache size in MB
        enable_compression: Enable gzip compression
        cache_headers: Add cache headers
    """
```

**Example:**

```python
# Basic static files
app.mount_static("/static", directory="./static")

# Advanced static file serving
app.mount_static(
    path="/assets",
    directory="./frontend/dist/assets",
    name="assets",
    enable_hot_cache=True,      # C-accelerated hot cache
    cache_size_mb=500,          # 500MB cache
    enable_compression=True,    # Gzip compression
    cache_headers=True,         # Browser caching
)

# Multiple static mounts
app.mount_static("/images", "./uploads/images")
app.mount_static("/css", "./static/css")
app.mount_static("/js", "./static/js")

# Serve frontend SPA
app.mount_static("/", "./frontend/dist", name="frontend")
```

### Background Tasks

#### `add_task()`

```python
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
) -> TaskResult:
    """
    Add background task with automatic C compilation for maximum performance.

    Args:
        func: Function to execute
        *args: Function arguments
        priority: Task priority (CRITICAL, HIGH, NORMAL, LOW)
        delay_ms: Delay before execution in milliseconds
        max_retries: Maximum retry attempts
        timeout_ms: Task timeout in milliseconds
        compile_to_c: Force C compilation (auto-detected if None)
        **kwargs: Additional function kwargs

    Returns:
        TaskResult: Task handle for monitoring
    """
```

**Example:**

```python
from catzilla import TaskPriority

# Simple background task
@app.post("/send-email")
def send_email_endpoint(request, email: str, message: str):
    # Add task with automatic C compilation
    task = app.add_task(send_email, email, message)
    return {"task_id": task.task_id}

# High-priority task
@app.post("/critical-alert")
def critical_alert(alert_data: dict):
    task = app.add_task(
        process_critical_alert,
        alert_data,
        priority=TaskPriority.CRITICAL,    # Execute immediately
        timeout_ms=5000,                   # 5 second timeout
        max_retries=5                      # Retry 5 times
    )
    return {"alert_task": task.task_id}

# Delayed task
@app.post("/schedule-notification")
def schedule_notification(message: str, delay_minutes: int):
    task = app.add_task(
        send_notification,
        message,
        delay_ms=delay_minutes * 60 * 1000,  # Convert to milliseconds
        compile_to_c=True                     # Force C compilation
    )
    return {"scheduled_task": task.task_id}

# Complex task with multiple arguments
@app.post("/process-data")
def process_data_endpoint(data: dict):
    task = app.add_task(
        complex_data_processing,
        data,
        user_id=data.get("user_id"),
        options={"timeout": 120, "retry": True},
        priority=TaskPriority.HIGH
    )
    return {"processing_task": task.task_id}

def send_email(email: str, message: str):
    # This function will be compiled to C automatically
    print(f"Sending email to {email}: {message}")
    # Actual email sending logic here

def process_critical_alert(alert_data: dict):
    # Critical alert processing - runs at C speed
    print(f"Processing critical alert: {alert_data}")
    # Alert processing logic here
```

## Middleware Management

### `add_middleware()`

```python
def add_middleware(
    self,
    middleware_class: Type,
    **options
) -> None:
    """
    Add middleware with automatic C compilation for zero-allocation execution.

    Args:
        middleware_class: Middleware class
        **options: Middleware configuration options
    """
```

**Example:**

```python
from catzilla.middleware import CORSMiddleware, RequestLoggingMiddleware

# Add CORS middleware (compiled to C)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

# Add request logging middleware
app.add_middleware(
    RequestLoggingMiddleware,
    format="[{time}] {method} {path} - {status} ({duration}ms)"
)

# Custom middleware (auto-compiled to C)
class AuthMiddleware:
    def __init__(self, secret_key: str):
        self.secret_key = secret_key

    def process_request(self, request):
        # Authentication logic here
        pass

    def process_response(self, request, response):
        # Response processing here
        return response

app.add_middleware(AuthMiddleware, secret_key="your-secret-key")
```

## Dependency Injection

### Service Registration

```python
# Service registration is handled by decorators
from catzilla import service, Depends

@service("database")
class DatabaseService:
    def __init__(self):
        # C-optimized service initialization
        pass

# Use in routes
@app.get("/data")
def get_data(db: DatabaseService = Depends("database")):
    # Service resolved at C speed
    return db.get_all_data()
```

## Performance Monitoring

### `get_performance_stats()`

```python
def get_performance_stats(self) -> dict:
    """
    Get comprehensive performance statistics.

    Returns:
        dict: Performance metrics including:
        - requests_per_second: Current RPS
        - average_response_time_ms: Average response time
        - memory_usage_mb: Current memory usage
        - c_acceleration_enabled: C acceleration status
        - jemalloc_enabled: jemalloc status
        - route_compilation_stats: Route compilation metrics
        - task_system_stats: Background task statistics
    """
```

**Example:**

```python
@app.get("/stats")
def get_stats():
    return app.get_performance_stats()

# Example output:
# {
#   "requests_per_second": 75000,
#   "average_response_time_ms": 0.3,
#   "memory_usage_mb": 42,
#   "c_acceleration_enabled": True,
#   "jemalloc_enabled": True,
#   "jemalloc_memory_savings": 0.31,
#   "routes_compiled_to_c": 25,
#   "middleware_compiled_to_c": 4,
#   "task_system_stats": {
#     "tasks_processed": 1500000,
#     "tasks_compiled_to_c": 45,
#     "average_task_time_ms": 0.8
#   }
# }
```

### `get_memory_stats()`

```python
def get_memory_stats(self) -> dict:
    """
    Get detailed memory usage statistics with jemalloc metrics.

    Returns:
        dict: Memory statistics including jemalloc efficiency data
    """
```

**Example:**

```python
memory_stats = app.get_memory_stats()
# {
#   "total_allocated_mb": 45,
#   "jemalloc_efficiency": 0.30,
#   "memory_pool_usage": 0.15,
#   "gc_pressure": "low",
#   "arena_usage": {
#     "active_arenas": 4,
#     "total_arenas": 8
#   }
# }
```

## Application Lifecycle

### Startup and Shutdown

```python
@app.on_event("startup")
def startup_event():
    """Called when application starts - runs before C compilation"""
    print("Starting Catzilla application...")
    # Initialize databases, load configurations, etc.

@app.on_event("shutdown")
def shutdown_event():
    """Called when application shuts down"""
    print("Shutting down Catzilla application...")
    # Cleanup resources, close connections, etc.
```

### Context Managers

```python
# Use as context manager for testing
def test_app():
    with Catzilla() as app:
        @app.get("/test")
        def test_route():
            return {"message": "test"}

        # App automatically starts and stops
        client = TestClient(app)
        response = client.get("/test")
        assert response.status_code == 200
```

## Advanced Configuration

### Environment Integration

```python
import os

app = Catzilla(
    # Read from environment variables
    debug=os.getenv("DEBUG", "false").lower() == "true",
    workers=int(os.getenv("WORKERS", "4")),
    enable_jemalloc=os.getenv("ENABLE_JEMALLOC", "true").lower() == "true",

    # Database configuration
    database_url=os.getenv("DATABASE_URL"),
    redis_url=os.getenv("REDIS_URL"),

    # Custom settings
    custom_memory_pool=int(os.getenv("MEMORY_POOL_MB", "256")),
)
```

### Performance Tuning

```python
# Maximum performance configuration
app = Catzilla(
    # Memory optimization
    enable_jemalloc=True,
    memory_pool_mb=2048,           # 2GB memory pool

    # C acceleration
    enable_c_acceleration=True,

    # Background tasks
    enable_background_tasks=True,
    task_workers=32,               # 32 task workers
    task_queue_size=100000,        # Large queue
    enable_task_c_compilation=True,

    # Static files
    static_cache_size_mb=1024,     # 1GB static cache
    static_enable_hot_cache=True,

    # Worker processes
    workers=16,                    # 16 worker processes
)

# Memory-constrained configuration
app = Catzilla(
    enable_jemalloc=True,
    memory_pool_mb=64,             # 64MB memory pool
    workers=2,                     # 2 workers
    task_workers=2,                # 2 task workers
    static_cache_size_mb=32,       # 32MB static cache
)
```

## Error Handling

### Global Error Handlers

```python
from catzilla.types import HTTPException

@app.exception_handler(404)
def not_found_handler(request, exc):
    return JSONResponse(
        status_code=404,
        content={"error": "Resource not found"}
    )

@app.exception_handler(HTTPException)
def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail}
    )

@app.exception_handler(Exception)
def global_exception_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error"}
    )
```

## Complete Example

```python
from catzilla import (
    Catzilla, BaseModel, Depends, service,
    TaskPriority, JSONResponse
)
from typing import List, Optional
import os

# Create high-performance application
app = Catzilla(
    title="My API",
    description="C-accelerated high-performance API",

    # Enable all performance features
    enable_jemalloc=True,
    enable_c_acceleration=True,
    enable_background_tasks=True,
    enable_di=True,

    # Production configuration
    workers=int(os.getenv("WORKERS", "8")),
    task_workers=16,
    memory_pool_mb=1024,
    static_cache_size_mb=500,
)

# Data models
class User(BaseModel):
    id: int
    name: str
    email: Optional[str] = None

class CreateUserRequest(BaseModel):
    name: str
    email: str

# Services
@service("user_service")
class UserService:
    def get_user(self, user_id: int) -> User:
        return User(id=user_id, name=f"User {user_id}")

    def create_user(self, user_data: CreateUserRequest) -> User:
        return User(id=123, name=user_data.name, email=user_data.email)

# Routes
@app.get("/users/{user_id}")
def get_user(
    request,
    user_id: int,
    user_service: UserService = Depends("user_service")
) -> User:
    """Get user by ID - executed at C speed!"""
    return user_service.get_user(user_id)

@app.post("/users")
def create_user(
    request,
    user_data: CreateUserRequest,
    user_service: UserService = Depends("user_service")
) -> User:
    """Create user with 100x faster validation"""
    # Add background task for email verification
    app.add_task(
        send_verification_email,
        user_data.email,
        priority=TaskPriority.HIGH
    )

    return user_service.create_user(user_data)

# Background task
def send_verification_email(email: str):
    """Send verification email - auto-compiled to C"""
    print(f"Sending verification email to {email}")

# Static files
app.mount_static("/static", directory="./static")

# Performance monitoring
@app.get("/stats")
def get_stats():
    return {
        "performance": app.get_performance_stats(),
        "memory": app.get_memory_stats()
    }

# Start server
if __name__ == "__main__":
    app.listen(host="0.0.0.0", port=8000)
```

---

*The fastest Python web framework ever built - powered by C acceleration!* 🚀
