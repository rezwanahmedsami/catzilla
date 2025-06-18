# 🌪️ Zero-Allocation Middleware System - User Guide

Welcome to Catzilla's Zero-Allocation Middleware System! This guide provides a practical, step-by-step introduction to building high-performance middleware with Catzilla.

## 📖 What is the Zero-Allocation Middleware System?

Catzilla's middleware system is designed for **maximum performance** with **minimal overhead**. Unlike traditional Python middleware that creates objects and allocates memory for each request, our system uses:

- **Memory pools** via jemalloc for zero-allocation request processing
- **C-bridge integration** for performance-critical operations
- **Efficient context passing** to minimize object creation
- **Priority-based execution** for optimal middleware ordering

## 🚀 Quick Start

Let's start with a simple example:

```python
from catzilla import Catzilla
from catzilla.middleware import Response

app = Catzilla()

# Basic middleware registration
@app.middleware(priority=100, pre_route=True)
def auth_middleware(request):
    \"\"\"Check if request has authorization header\"\"\"
    if not request.headers.get('Authorization'):
        return Response(
            status=401,
            body={\"error\": \"Authorization required\"},
            content_type=\"application/json\"
        )
    # Return None to continue to next middleware
    return None

@app.route('/api/users')
def get_users():
    return {\"users\": [\"alice\", \"bob\"]}

if __name__ == '__main__':
    app.run(port=8000)
```

## 🎯 Core Concepts

### 1. Middleware Registration

Use the `@app.middleware()` decorator to register middleware:

```python
@app.middleware(
    priority=100,        # Lower numbers execute first
    pre_route=True,      # Execute before route handler
    name=\"my_middleware\"  # Optional name for debugging
)
def my_middleware(request):
    # Your middleware logic here
    pass
```

### 2. Execution Flow

```
Request → Pre-route Middleware (priority order) → Route Handler → Response
```

### 3. Middleware Return Values

- **`None`**: Continue to next middleware
- **`Response` object**: Skip remaining middleware and return response
- **Any other value**: Convert to response and return

### 4. Request Context

Use `request._context` to share data between middleware:

```python
@app.middleware(priority=50, pre_route=True)
def user_middleware(request):
    # Extract user from token
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    user = get_user_from_token(token)

    # Initialize context if needed
    if not hasattr(request, '_context'):
        request._context = {}

    # Store in context for other middleware/handlers
    request._context['user'] = user
    request._context['user_id'] = user.id
    return None

@app.middleware(priority=100, pre_route=True)
def permission_middleware(request):
    # Use context from previous middleware
    user = getattr(request, '_context', {}).get('user')
    if not user.has_permission(request.path):
        return Response(status=403, body="Forbidden")
    return None
```

## 🛠️ Common Middleware Patterns

### Authentication Middleware

```python
@app.middleware(priority=100, pre_route=True)
def jwt_auth_middleware(request):
    \"\"\"JWT token authentication\"\"\"

    # Skip auth for public endpoints
    if request.path in ['/health', '/docs', '/login']:
        return None

    # Extract token
    auth_header = request.headers.get('Authorization', '')
    if not auth_header.startswith('Bearer '):
        return Response(
            status=401,
            body={\"error\": \"Bearer token required\"},
            content_type=\"application/json\"
        )

    token = auth_header[7:]  # Remove 'Bearer '

    try:
        # Validate token (you'd use a proper JWT library)
        payload = validate_jwt_token(token)

        # Initialize context if needed
        if not hasattr(request, '_context'):
            request._context = {}

        request._context['user_id'] = payload['user_id']
        request._context['permissions'] = payload['permissions']
        return None

    except InvalidTokenError:
        return Response(
            status=401,
            body={\"error\": \"Invalid token\"},
            content_type=\"application/json\"
        )
```

### CORS Middleware

```python
@app.middleware(priority=10, pre_route=True)  # Early priority
def cors_middleware(request):
    \"\"\"Handle CORS preflight requests\"\"\"

    if request.method == \"OPTIONS\":
        return Response(
            status=200,
            headers={
                \"Access-Control-Allow-Origin\": \"*\",
                \"Access-Control-Allow-Methods\": \"GET,POST,PUT,DELETE,OPTIONS\",
                \"Access-Control-Allow-Headers\": \"Content-Type,Authorization\",
                \"Access-Control-Max-Age\": \"86400\"
            },
            body=\"\"
        )

    return None
```

### Request Logging Middleware

```python
import time

@app.middleware(priority=1, pre_route=True)  # Very early
def request_logger_start(request):
    """Log request start and timing"""
    # Initialize context if needed
    if not hasattr(request, '_context'):
        request._context = {}

    request._context['start_time'] = time.time()
    request._context['request_id'] = str(uuid.uuid4())

    print(f"📥 [{request._context['request_id']}] {request.method} {request.path}")
    return None

@app.middleware(priority=999, pre_route=False)  # Very late
def request_logger_end(request, response):
    """Log request completion"""
    duration = time.time() - getattr(request, '_context', {}).get('start_time', 0)
    request_id = getattr(request, '_context', {}).get('request_id', 'unknown')

    print(f"📤 [{request_id}] {response.status} - {duration*1000:.2f}ms")
    return response
```

### Rate Limiting Middleware

```python
from collections import defaultdict
import time

# Simple in-memory rate limiter (use Redis in production)
rate_limit_storage = defaultdict(list)

@app.middleware(priority=50, pre_route=True)
def rate_limit_middleware(request):
    \"\"\"Simple rate limiting by IP address\"\"\"

    client_ip = request.remote_addr
    current_time = time.time()
    window_size = 60  # 1 minute window
    max_requests = 100  # 100 requests per minute

    # Clean old entries
    rate_limit_storage[client_ip] = [
        timestamp for timestamp in rate_limit_storage[client_ip]
        if current_time - timestamp < window_size
    ]

    # Check limit
    if len(rate_limit_storage[client_ip]) >= max_requests:
        return Response(
            status=429,
            body={\"error\": \"Rate limit exceeded\"},
            headers={\"Retry-After\": \"60\"},
            content_type=\"application/json\"
        )

    # Record this request
    rate_limit_storage[client_ip].append(current_time)
    return None
```

## 🔧 Advanced Features

### Post-Route Middleware

Post-route middleware executes after the route handler and can modify responses:

```python
@app.middleware(priority=100, pre_route=False)
def security_headers_middleware(request, response):
    \"\"\"Add security headers to all responses\"\"\"

    response.headers.update({
        \"X-Content-Type-Options\": \"nosniff\",
        \"X-Frame-Options\": \"DENY\",
        \"X-XSS-Protection\": \"1; mode=block\",
        \"Strict-Transport-Security\": \"max-age=31536000; includeSubDomains\"
    })

    return response

@app.middleware(priority=200, pre_route=False)
def cors_response_middleware(request, response):
    \"\"\"Add CORS headers to responses\"\"\"

    response.headers.update({
        \"Access-Control-Allow-Origin\": \"*\",
        \"Access-Control-Allow-Credentials\": \"true\"
    })

    return response
```

### Error Handling Middleware

```python
@app.middleware(priority=10, pre_route=True)
def error_handler_middleware(request):
    \"\"\"Global error handling\"\"\"

    try:
        # This middleware will wrap the entire request
        return None  # Continue normally

    except ValidationError as e:
        return Response(
            status=400,
            body={\"error\": \"Validation failed\", \"details\": str(e)},
            content_type=\"application/json\"
        )
    except AuthenticationError as e:
        return Response(
            status=401,
            body={\"error\": \"Authentication failed\"},
            content_type=\"application/json\"
        )
    except Exception as e:
        # Log unexpected errors
        print(f\"❌ Unexpected error: {e}\")
        return Response(
            status=500,
            body={\"error\": \"Internal server error\"},
            content_type=\"application/json\"
        )
```

### Dependency Injection in Middleware

```python
from catzilla.integration import Service, Inject

# Define a service
class AuthService(Service):
    def validate_token(self, token: str) -> dict:
        # Token validation logic
        return {\"user_id\": \"123\", \"permissions\": [\"read\", \"write\"]}

# Register service
app.di_container.register_service(\"auth_service\", AuthService)

@app.middleware(priority=100, pre_route=True)
def di_auth_middleware(request, auth_service: AuthService = Inject(\"auth_service\")):
    \"\"\"Middleware with dependency injection\"\"\"

    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    if not token:
        return Response(status=401, body=\"Token required\")

    try:
        user_data = auth_service.validate_token(token)
        request.context.update(user_data)
        return None
    except Exception:
        return Response(status=401, body=\"Invalid token\")
```

## 📊 Performance Tips

### 1. Use Appropriate Priorities

```python
# System middleware (early)
@app.middleware(priority=1)    # CORS
@app.middleware(priority=10)   # Request logging
@app.middleware(priority=50)   # Rate limiting

# Authentication/Authorization (middle)
@app.middleware(priority=100)  # Authentication
@app.middleware(priority=200)  # Authorization

# Business logic (later)
@app.middleware(priority=500)  # Custom business logic

# Response processing (latest)
@app.middleware(priority=900)  # Response headers
@app.middleware(priority=999)  # Final logging
```

### 2. Minimize Memory Allocation

```python
# Good: Reuse objects, minimal allocations
@app.middleware(priority=100, pre_route=True)
def efficient_middleware(request):
    # Direct header access (no extra dict creation)
    token = request.headers.get('Authorization')

    # Simple string operations
    if not token or len(token) < 10:
        return Response(status=401, body=\"Invalid token\")

    return None

# Avoid: Complex operations, lots of object creation
@app.middleware(priority=100, pre_route=True)
def inefficient_middleware(request):
    # Avoid complex parsing, regex, json in middleware
    data = json.loads(complex_parsing(request.body))
    result = expensive_operation(data)
    request.context['complex_result'] = result
    return None
```

### 3. Fail Fast

```python
@app.middleware(priority=50, pre_route=True)
def validation_middleware(request):
    \"\"\"Validate requests early to avoid unnecessary processing\"\"\"

    # Check content length first
    content_length = request.headers.get('Content-Length')
    if content_length and int(content_length) > 10_000_000:  # 10MB limit
        return Response(status=413, body=\"Payload too large\")

    # Check content type for POST/PUT
    if request.method in ['POST', 'PUT']:
        content_type = request.headers.get('Content-Type', '')
        if not content_type.startswith(('application/json', 'application/x-www-form-urlencoded')):
            return Response(status=415, body=\"Unsupported content type\")

    return None
```

## 🧪 Testing Middleware

### Unit Testing

```python
import pytest
from catzilla.testing import TestClient

@pytest.fixture
def app():
    from catzilla import Catzilla
    app = Catzilla()

    @app.middleware(priority=100, pre_route=True)
    def auth_middleware(request):
        if not request.headers.get('Authorization'):
            return Response(status=401, body=\"Unauthorized\")
        return None

    @app.route('/api/test')
    def test_endpoint():
        return {\"message\": \"success\"}

    return app

def test_middleware_blocks_unauthenticated(app):
    \"\"\"Test middleware blocks requests without auth\"\"\"
    client = TestClient(app)
    response = client.get('/api/test')
    assert response.status_code == 401

def test_middleware_allows_authenticated(app):
    \"\"\"Test middleware allows requests with auth\"\"\"
    client = TestClient(app)
    headers = {'Authorization': 'Bearer valid_token'}
    response = client.get('/api/test', headers=headers)
    assert response.status_code == 200
```

### Integration Testing

```python
def test_middleware_chain_execution(app):
    \"\"\"Test complete middleware chain\"\"\"
    client = TestClient(app)

    response = client.get('/api/test', headers={
        'Authorization': 'Bearer test_token',
        'User-Agent': 'test-client'
    })

    # Check that all middleware executed
    assert response.status_code == 200
    assert 'X-Request-ID' in response.headers  # From logging middleware
    assert 'Access-Control-Allow-Origin' in response.headers  # From CORS
```

## 🚨 Common Pitfalls and Solutions

### 1. Middleware Order Issues

```python
# ❌ Wrong: Auth before CORS
@app.middleware(priority=50)   # Auth first
@app.middleware(priority=100)  # CORS second

# ✅ Correct: CORS before Auth
@app.middleware(priority=50)   # CORS first
@app.middleware(priority=100)  # Auth second
```

### 2. Forgetting Return Values

```python
# ❌ Wrong: No return value
@app.middleware(priority=100, pre_route=True)
def broken_middleware(request):
    if not request.headers.get('Authorization'):
        Response(status=401, body=\"Unauthorized\")  # Missing return!

# ✅ Correct: Always return
@app.middleware(priority=100, pre_route=True)
def working_middleware(request):
    if not request.headers.get('Authorization'):
        return Response(status=401, body=\"Unauthorized\")
    return None  # Explicitly return None to continue
```

### 3. Modifying Request in Post-Route

```python
# ❌ Wrong: Can't modify request in post-route
@app.middleware(priority=100, pre_route=False)
def wrong_post_middleware(request, response):
    request.context['new_data'] = 'value'  # Too late!
    return response

# ✅ Correct: Only modify response in post-route
@app.middleware(priority=100, pre_route=False)
def correct_post_middleware(request, response):
    response.headers['X-Custom'] = 'value'
    return response
```

## 📚 Examples and Migration

### Complete Examples

Check out the `examples/middleware/` directory for comprehensive examples:

- **`basic_middleware.py`** - Simple middleware patterns
- **`production_api.py`** - Complete production API with full middleware stack
- **`di_integration.py`** - Dependency injection in middleware
- **`migration_example.py`** - Migrating from other frameworks

### Migration from Other Frameworks

**From FastAPI:**
```python
# FastAPI
@app.middleware(\"http\")
async def fastapi_middleware(request: Request, call_next):
    response = await call_next(request)
    return response

# Catzilla
@app.middleware(priority=100, pre_route=True)
def catzilla_middleware(request):
    # Pre-processing logic
    return None

@app.middleware(priority=100, pre_route=False)
def catzilla_post_middleware(request, response):
    # Post-processing logic
    return response
```

**From Flask:**
```python
# Flask
@app.before_request
def flask_middleware():
    # Pre-request logic
    pass

# Catzilla
@app.middleware(priority=100, pre_route=True)
def catzilla_middleware(request):
    # Same pre-request logic
    return None
```

## 🔗 Related Documentation

- [Main Middleware Documentation](middleware.md) - Complete technical reference
- [Performance Guide](performance.md) - Optimization techniques
- [Dependency Injection Guide](DEPENDENCY_INJECTION_GUIDE.md) - DI integration
- [Migration Guide](../examples/middleware/migration_guide.md) - Detailed migration examples

## ⚡ Next Steps

1. **Start Simple**: Begin with basic authentication or logging middleware
2. **Add Complexity**: Integrate with dependency injection and complex business logic
3. **Optimize**: Use performance profiling to identify bottlenecks
4. **Scale**: Leverage memory pools and C-bridge features for maximum performance

The Zero-Allocation Middleware System gives you the flexibility of Python with the performance of C. Start with simple patterns and gradually adopt advanced features as your application grows!
