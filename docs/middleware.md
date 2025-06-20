# 🌪️ Advanced Global Middleware System

Catzilla's revolutionary Zero-Allocation Middleware System provides **unprecedented performance** by executing middleware chains entirely in C while maintaining Python's flexibility and ease of use.

> � **Recommended for New Projects**: Use [**Per-Route Middleware**](per_route_middleware.md) for better performance and cleaner code.
>
> This document covers **Global Middleware** for cross-cutting concerns like CORS, logging, and security headers.

## 🚀 Quick Start

```python
from catzilla import Catzilla, Response

app = Catzilla()

# Simple global middleware - automatically compiled to C for maximum performance
@app.middleware(priority=100, pre_route=True)
def auth_middleware(request):
    if not request.headers.get('Authorization'):
        return Response("Unauthorized", status_code=401)
    return None  # Continue to next middleware

@app.route('/api/users')
def get_users():
    return {"users": ["alice", "bob"]}

if __name__ == '__main__':
    app.run(port=8000)
```

## 🎯 Key Features

- **🏎️ 10-15x Faster**: Middleware execution in C for maximum performance
- **💾 40-50% Less Memory**: Zero-allocation patterns eliminate memory waste
- **⚡ Sub-microsecond Latency**: Typical middleware chains execute in under 1µs
- **🔧 Python-First API**: Write middleware in Python, execute in C
- **🔗 Seamless Integration**: Works with dependency injection and routing
- **📊 Built-in Profiling**: Detailed performance metrics and memory tracking

## 📖 Core Concepts

### Middleware Types

Catzilla supports two types of middleware:

1. **Global Middleware**: Applied to all routes (this document)
2. **Per-Route Middleware**: Applied to specific routes ([Per-Route Middleware Guide](per_route_middleware.md) - **Recommended**)

### Global Middleware Registration

Global middleware functions are registered using the `@app.middleware()` decorator with configurable options:

```python
@app.middleware(
    priority=100,        # Execution order (lower = earlier)
    pre_route=True,     # Execute before route handler
    name="auth_check"   # Optional name for debugging
)
def auth_middleware(request):
    # Middleware logic here
    pass
```

### Execution Flow

```
Request → Pre-route Middleware → Route Handler → Post-route Middleware → Response
```

### Response Handling

Global middleware can:
- **Continue**: Return `None` to proceed to next middleware
- **Short-circuit**: Return `Response` object to skip remaining middleware and route handler
- **Modify**: Add data to `request.context` for downstream processing

## 🛠️ Basic Usage

### Authentication Middleware

```python
@app.middleware(priority=100, pre_route=True)
def auth_middleware(request):
    """Token-based authentication"""
    auth_header = request.headers.get('Authorization', '')

    # Skip auth for public endpoints
    if request.path in ['/health', '/docs']:
        return None

    if not auth_header.startswith('Bearer '):
        return Response(
            {"error": "Authentication required"},
            status_code=401
        )

    # Verify token (simplified)
    token = auth_header[7:]
    if not is_valid_token(token):
        return Response(
            {"error": "Invalid token"},
            status_code=401
        )

    # Store user info for route handlers
    if not hasattr(request, 'context'):
        request.context = {}
    request.context['user'] = get_user_from_token(token)
    return None
```

### CORS Middleware

```python
@app.middleware(priority=50, pre_route=True)
def cors_middleware(request):
    """Handle CORS preflight requests"""

    # Handle preflight OPTIONS requests
    if request.method == "OPTIONS":
        return Response(
            "",
            status_code=200,
            headers={
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "GET,POST,PUT,DELETE,OPTIONS",
                "Access-Control-Allow-Headers": "Content-Type,Authorization"
            }
        )

    return None

@app.middleware(priority=900, pre_route=False)
def cors_response_middleware(request, response):
    """Add CORS headers to all responses"""
    response.headers.update({
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Credentials": "true"
    })
    return response
```

### Request Logging

```python
import time
import json

@app.middleware(priority=10, pre_route=True)
def request_logger(request):
    """Log incoming requests with timing"""
    if not hasattr(request, 'context'):
        request.context = {}
    request.context['start_time'] = time.time()
    print(f"📥 {request.method} {request.path} - {request.remote_addr}")
    return None

@app.middleware(priority=990, pre_route=False)
def response_logger(request, response):
    """Log response with duration"""
    duration = time.time() - getattr(request, 'context', {}).get('start_time', 0)
    print(f"📤 {response.status} - {duration*1000:.2f}ms")
    return response
```

## 🏗️ Advanced Features

### Priority-Based Execution

Middleware executes in priority order (lower numbers first):

```python
@app.middleware(priority=10)   # Executes first
def cors_middleware(request): pass

@app.middleware(priority=50)   # Executes second
def auth_middleware(request): pass

@app.middleware(priority=100)  # Executes third
def rate_limit_middleware(request): pass
```

### Pre-route vs Post-route

```python
# Pre-route: Executes before route handler
@app.middleware(priority=100, pre_route=True)
def auth_middleware(request):
    return None

# Post-route: Executes after route handler
@app.middleware(priority=100, pre_route=False)
def response_modifier(request, response):
    response.headers['X-Custom'] = 'Value'
    return response
```

### Context Sharing

```python
@app.middleware(priority=50, pre_route=True)
def user_middleware(request):
    """Extract user information"""
    # Initialize context if it doesn't exist
    if not hasattr(request, 'context'):
        request.context = {}

    request.context['user_id'] = extract_user_id(request)
    request.context['permissions'] = get_user_permissions(request.context['user_id'])
    return None

@app.middleware(priority=100, pre_route=True)
def permission_middleware(request):
    """Check permissions using context"""
    required_permission = get_required_permission(request.path)
    user_permissions = getattr(request, 'context', {}).get('permissions', [])

    if required_permission not in user_permissions:
        return Response("Forbidden", status_code=403)

    return None
```

## ⚡ Performance Optimization

### C Compilation

The Zero-Allocation Middleware System automatically analyzes your Python middleware and compiles performance-critical paths to C:

```python
# This middleware will be compiled to C
@app.middleware(priority=100, pre_route=True)
def simple_auth(request):
    """Simple token check - optimized for C compilation"""
    token = request.headers.get('X-API-Key')
    if not token or len(token) < 32:
        return Response("Invalid API key", status_code=401)
    return None

# Complex middleware stays in Python
@app.middleware(priority=200, pre_route=True)
def complex_middleware(request):
    """Complex logic - executed in Python"""
    # Database queries, external API calls, etc.
    result = complex_business_logic(request)

    # Initialize context if needed
    if not hasattr(request, 'context'):
        request.context = {}

    request.context['analysis'] = result
    return None
```

### Memory Pools

Middleware leverages jemalloc memory pools for zero-allocation execution:

```python
# Memory usage is tracked automatically
@app.middleware(priority=100, pre_route=True)
def memory_efficient_middleware(request):
    """Zero-allocation header processing"""
    # These operations use memory pools
    auth_header = request.headers.get('Authorization')
    user_agent = request.headers.get('User-Agent')

    # Memory is automatically returned to pool
    return None
```

### Built-in Profiling

```python
from catzilla.middleware import get_middleware_stats

# Get detailed performance metrics
stats = get_middleware_stats()
print(f"Total executions: {stats.total_executions}")
print(f"Average duration: {stats.avg_duration_us}µs")
print(f"Memory pool usage: {stats.memory_pool_usage_bytes} bytes")
```

## 🔧 Built-in Middleware

Catzilla provides high-performance C middleware for common use cases:

```python
# Enable built-in C middleware
app.enable_builtin_middleware([
    'cors',           # CORS handling
    'rate_limit',     # Rate limiting
    'compression',    # Response compression
    'security_headers' # Security headers
])

# Configure built-in middleware
app.configure_builtin_middleware('rate_limit', {
    'requests_per_minute': 100,
    'burst_size': 10
})
```

### Available Built-in Middleware

| Middleware | Description | Performance |
|------------|-------------|-------------|
| `cors` | Cross-Origin Resource Sharing | Sub-microsecond |
| `rate_limit` | Request rate limiting | ~0.1µs per request |
| `compression` | gzip/deflate compression | ~50µs per KB |
| `security_headers` | Security headers (HSTS, CSP, etc.) | Sub-microsecond |
| `request_id` | Unique request ID generation | Sub-microsecond |

## 🧪 Testing Middleware

### Unit Testing

```python
import pytest
from catzilla.testing import TestClient
from your_app import app

@pytest.fixture
def client():
    return TestClient(app)

def test_auth_middleware_blocks_unauthenticated(client):
    """Test middleware blocks requests without auth"""
    response = client.get('/api/users')
    assert response.status_code == 401
    assert "Unauthorized" in response.text

def test_auth_middleware_allows_authenticated(client):
    """Test middleware allows requests with valid auth"""
    headers = {'Authorization': 'Bearer valid_token'}
    response = client.get('/api/users', headers=headers)
    assert response.status_code == 200
```

### Performance Testing

```python
import time
from catzilla.middleware import get_middleware_stats

def test_middleware_performance():
    """Test middleware execution performance"""
    client = TestClient(app)

    # Reset stats
    get_middleware_stats().reset()

    # Make multiple requests
    for _ in range(1000):
        client.get('/api/test')

    stats = get_middleware_stats()
    assert stats.avg_duration_us < 10  # Less than 10µs average
    assert stats.memory_leaks == 0     # No memory leaks
```

## 🚨 Error Handling

### Middleware Error Handling

```python
@app.middleware(priority=100, pre_route=True)
def safe_middleware(request):
    """Middleware with proper error handling"""
    try:
        # Potentially failing operation
        result = risky_operation(request)
        request.context['result'] = result
        return None

    except ValidationError as e:
        return Response(
            {"error": "Validation failed", "details": str(e)},
            status_code=400
        )

    except AuthenticationError as e:
        return Response(
            {"error": "Authentication failed"},
            status_code=401
        )

    except Exception as e:
        # Log unexpected errors
        logger.error(f"Middleware error: {e}")
        return Response(
            {"error": "Internal server error"},
            status_code=500
        )
```

### Global Error Handling

```python
@app.middleware(priority=999, pre_route=False)
def error_handler_middleware(request, response):
    """Global error response formatting"""
    if response.status >= 400:
        # Ensure error responses have consistent format
        if not response.headers.get('Content-Type'):
            response.content_type = 'application/json'

        # Add error tracking
        response.headers['X-Error-ID'] = generate_error_id()

    return response
```

## 🔍 Debugging

### Debug Mode

```python
# Enable middleware debugging
app = Catzilla(debug=True)

# This will print detailed middleware execution info
# Including timing, memory usage, and execution flow
```

### Middleware Introspection

```python
# List all registered middleware
middleware_list = app.get_middleware_list()
for mw in middleware_list:
    print(f"{mw.name}: priority={mw.priority}, pre_route={mw.pre_route}")

# Get middleware execution trace
trace = app.get_middleware_trace()
for entry in trace:
    print(f"{entry.name}: {entry.duration_us}µs")
```

## 📊 Performance Benchmarks

### Middleware vs No Middleware

| Scenario | RPS | Latency (p95) | Memory |
|----------|-----|---------------|---------|
| No middleware | 25,000 | 2.1ms | 45MB |
| 3 Python middleware | 18,000 | 3.8ms | 67MB |
| 3 C middleware | 24,500 | 2.2ms | 47MB |

### Comparison with Other Frameworks

| Framework | Middleware RPS | Memory Overhead |
|-----------|----------------|-----------------|
| **Catzilla (C)** | **24,500** | **+4%** |
| FastAPI | 12,000 | +45% |
| Flask | 8,500 | +60% |
| Django | 4,200 | +120% |

## 🎯 Best Practices

### 1. Order Matters

```python
# Correct order: CORS → Auth → Rate Limiting → Business Logic
@app.middleware(priority=10)   # CORS first
def cors_middleware(request): pass

@app.middleware(priority=50)   # Auth second
def auth_middleware(request): pass

@app.middleware(priority=100)  # Rate limiting third
def rate_limit_middleware(request): pass
```

### 2. Fail Fast

```python
@app.middleware(priority=100, pre_route=True)
def fast_validation(request):
    """Validate request early to avoid unnecessary processing"""

    # Check required headers first
    if not request.headers.get('Content-Type'):
        return Response("Content-Type required", status_code=400)

    # Validate content length
    if int(request.headers.get('Content-Length', 0)) > 10_000_000:
        return Response("Payload too large", status_code=413)

    return None
```

### 3. Use Context Efficiently

```python
@app.middleware(priority=50, pre_route=True)
def context_middleware(request):
    """Efficient context usage"""

    # Initialize context if not exists
    if not hasattr(request, '_context'):
        request._context = {}

    # Use context for data that multiple middleware/handlers need
    request._context.update({
        'request_id': generate_request_id(),
        'start_time': time.time(),
        'user_ip': get_real_ip(request)
    })

    return None
```

### 4. Optimize for C Compilation

```python
# Good: Simple, C-optimizable middleware
@app.middleware(priority=100, pre_route=True)
def optimized_middleware(request):
    token = request.headers.get('X-API-Key')
    if not token or len(token) != 32:
        return Response(status=401, body="Invalid key")
    return None

# Avoid: Complex operations that can't be compiled to C
@app.middleware(priority=100, pre_route=True)
def complex_middleware(request):
    # Database queries, JSON parsing, regex, etc.
    # Keep these in Python for maintainability
    pass
```

## 🔗 Integration Examples

### With Dependency Injection

```python
from catzilla import Depends, service

@service("auth_service", scope="singleton")
class AuthService:
    def validate_token(self, token: str) -> bool:
        # Token validation logic
        return True

@app.middleware(priority=100, pre_route=True)
def di_auth_middleware(request, auth_service: AuthService = Depends("auth_service")):
    """Middleware with dependency injection"""
    token = request.headers.get('Authorization', '').replace('Bearer ', '')

    if not auth_service.validate_token(token):
        return Response("Invalid token", status_code=401)

    return None
```

### With Route Groups

```python
# Different middleware for different route groups
api_v1 = app.router_group("/api/v1")
api_v2 = app.router_group("/api/v2")

# v1 uses legacy auth
@api_v1.middleware(priority=100)
def legacy_auth_middleware(request):
    # Legacy authentication logic
    pass

# v2 uses modern auth
@api_v2.middleware(priority=100)
def modern_auth_middleware(request):
    # Modern authentication logic
    pass
```

---

## 📚 Related Documentation

- **[Per-Route Middleware](per_route_middleware.md)** - Modern FastAPI-style middleware (recommended)
- [Dependency Injection Guide](DEPENDENCY_INJECTION_GUIDE.md)
- [Performance Optimization](performance.md)
- [Error Handling](error-handling.md)
- [Migration from FastAPI](migration_from_fastapi.md)

---

## 🤝 Contributing

See the [examples/middleware/](../examples/middleware/) directory for complete working examples.
