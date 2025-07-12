# 🌪️ Per-Route Middleware in Catzilla

**A FastAPI-compatible per-route middleware system with C-accelerated performance**

> 💡 **Recommended Approach**: This is the modern, preferred way to use middleware in Catzilla.
>
> For legacy global middleware, see [Advanced Global Middleware](middleware.md).

---

## 📖 Overview

Catzilla's per-route middleware system allows you to attach middleware functions directly to specific routes using FastAPI-style decorators. Unlike traditional global middleware that runs on every request, per-route middleware only executes for the routes that need it, resulting in better performance and more explicit security.

**🚀 Key Features:**
- ✅ **FastAPI-Compatible API**: Use familiar `@app.get()`, `@app.post()`, etc. decorators
- ✅ **C-Accelerated Performance**: Middleware execution happens in C for maximum speed
- ✅ **Zero-Allocation Design**: Constant memory usage regardless of middleware count
- ✅ **Explicit Security Model**: Clear visibility of which middleware applies to which routes
- ✅ **Execution Order Control**: Middleware runs in the order you specify
- ✅ **Short-Circuit Support**: Middleware can stop execution and return early responses

---

## 🚀 Quick Start

### Basic Usage

```python
from catzilla import Catzilla, Request, Response, JSONResponse
from typing import Optional

app = Catzilla()

def auth_middleware(request: Request, response: Response) -> Optional[Response]:
    """Authentication middleware"""
    api_key = request.headers.get('Authorization')
    if not api_key or api_key != 'Bearer secret_token':
        return JSONResponse({"error": "Unauthorized"}, status_code=401)
    return None  # Continue to next middleware/handler

def cors_middleware(request: Request, response: Response) -> Optional[Response]:
    """CORS middleware"""
    response.set_header('Access-Control-Allow-Origin', '*')
    return None  # Continue processing

# Apply middleware to specific routes
@app.get("/public")
def public_endpoint(request):
    return JSONResponse({"message": "This is public"})

@app.get("/protected", middleware=[auth_middleware])
def protected_endpoint(request):
    return JSONResponse({"message": "This is protected"})

@app.get("/api/data", middleware=[auth_middleware, cors_middleware])
def api_endpoint(request):
    return JSONResponse({"data": "This has auth + CORS"})
```

### All HTTP Methods Supported

```python
# GET with middleware
@app.get("/users", middleware=[auth_middleware])
def get_users(request):
    return JSONResponse({"users": []})

# POST with validation middleware
@app.post("/users", middleware=[auth_middleware, json_validator])
def create_user(request):
    return JSONResponse({"user": "created"})

# PUT with multiple middleware
@app.put("/users/{user_id}", middleware=[auth_middleware, rate_limiter])
def update_user(request):
    user_id = request.path_params.get('user_id')
    return JSONResponse({"user_id": user_id, "updated": True})

# DELETE with audit logging
@app.delete("/users/{user_id}", middleware=[auth_middleware, audit_logger])
def delete_user(request):
    user_id = request.path_params.get('user_id')
    return JSONResponse({"user_id": user_id, "deleted": True})

# PATCH with conditional middleware
@app.patch("/users/{user_id}", middleware=[auth_middleware])
def patch_user(request):
    return JSONResponse({"updated": True})
```

---

## 🔧 Middleware Function Signature

All middleware functions must follow this signature:

```python
def my_middleware(request: Request, response: Response) -> Optional[Response]:
    """
    Middleware function signature

    Args:
        request: The incoming request object
        response: The response object (can be modified)

    Returns:
        None: Continue to next middleware/handler
        Response: Short-circuit and return immediately
    """
    # Pre-processing logic here

    # Option 1: Continue processing
    return None

    # Option 2: Short-circuit with custom response
    # return JSONResponse({"error": "Blocked"}, status_code=403)
```

### Middleware Behavior

- **Return `None`**: Continue to the next middleware or route handler
- **Return `Response`**: Stop processing and return the response immediately
- **Modify `response`**: Add headers, set status codes, etc.
- **Access `request`**: Read headers, body, path parameters, query parameters

---

## 🎯 Middleware Execution Order

Middleware executes in the order specified in the list:

```python
@app.get("/api/data", middleware=[
    auth_middleware,        # Runs first
    rate_limit_middleware,  # Runs second
    validation_middleware,  # Runs third
    logging_middleware      # Runs last
])
def api_endpoint(request):
    return JSONResponse({"data": "value"})
```

**Execution Flow:**
1. `auth_middleware` runs first
2. If it returns `None`, `rate_limit_middleware` runs
3. If it returns `None`, `validation_middleware` runs
4. If it returns `None`, `logging_middleware` runs
5. If all middleware return `None`, the route handler executes

**Short-Circuit Example:**
```python
def strict_auth(request: Request, response: Response) -> Optional[Response]:
    if not request.headers.get('Authorization'):
        # Short-circuit - remaining middleware won't run
        return JSONResponse({"error": "Missing auth"}, status_code=401)
    return None

@app.get("/secure", middleware=[
    strict_auth,      # If this fails, the rest won't run
    logging_middleware,
    rate_limiter
])
def secure_endpoint(request):
    return JSONResponse({"secure": "data"})
```

---

## 💡 Common Middleware Patterns

### 1. Authentication Middleware

```python
def jwt_auth_middleware(request: Request, response: Response) -> Optional[Response]:
    """JWT token authentication"""
    auth_header = request.headers.get('Authorization', '')

    if not auth_header.startswith('Bearer '):
        return JSONResponse(
            {"error": "Missing or invalid authorization header"},
            status_code=401
        )

    token = auth_header[7:]  # Remove "Bearer "

    try:
        # Validate JWT token (replace with your logic)
        user = validate_jwt_token(token)
        request.context['user'] = user  # Store user for handler
        return None
    except InvalidTokenError:
        return JSONResponse(
            {"error": "Invalid token"},
            status_code=401
        )

# Usage
@app.get("/profile", middleware=[jwt_auth_middleware])
def get_profile(request):
    user = request.context['user']
    return JSONResponse({"user": user})
```

### 2. Rate Limiting Middleware

```python
import time
from collections import defaultdict

# Simple in-memory rate limiter (use Redis in production)
request_counts = defaultdict(list)

def rate_limit_middleware(max_requests=100, window_seconds=60):
    """Rate limiting middleware factory"""
    def middleware(request: Request, response: Response) -> Optional[Response]:
        client_ip = request.environ.get('REMOTE_ADDR', 'unknown')
        now = time.time()

        # Clean old requests
        request_counts[client_ip] = [
            req_time for req_time in request_counts[client_ip]
            if now - req_time < window_seconds
        ]

        # Check rate limit
        if len(request_counts[client_ip]) >= max_requests:
            return JSONResponse(
                {
                    "error": "Rate limit exceeded",
                    "retry_after": window_seconds
                },
                status_code=429
            )

        # Record this request
        request_counts[client_ip].append(now)
        return None

    return middleware

# Usage
@app.get("/api/search", middleware=[rate_limit_middleware(max_requests=10, window_seconds=60)])
def search_api(request):
    return JSONResponse({"results": []})
```

### 3. CORS Middleware

```python
def cors_middleware(origins=['*'], methods=['GET', 'POST', 'PUT', 'DELETE']):
    """CORS middleware factory"""
    def middleware(request: Request, response: Response) -> Optional[Response]:
        # Handle preflight requests
        if request.method == 'OPTIONS':
            response.set_header('Access-Control-Allow-Origin', ', '.join(origins))
            response.set_header('Access-Control-Allow-Methods', ', '.join(methods))
            response.set_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
            response.set_header('Access-Control-Max-Age', '86400')
            return Response("", status_code=200)

        # Add CORS headers to actual requests
        response.set_header('Access-Control-Allow-Origin', ', '.join(origins))
        return None

    return middleware

# Usage
@app.get("/api/public", middleware=[cors_middleware(origins=['https://myapp.com'])])
def public_api(request):
    return JSONResponse({"data": "public"})
```

### 4. Request Logging Middleware

```python
import logging
import time

logger = logging.getLogger(__name__)

def logging_middleware(request: Request, response: Response) -> Optional[Response]:
    """Request logging middleware"""
    start_time = time.time()
    method = request.method
    path = request.path
    client_ip = request.environ.get('REMOTE_ADDR', 'unknown')

    # Log request start
    logger.info(f"Request started: {method} {path} from {client_ip}")

    # Store start time for response logging
    request.context['start_time'] = start_time

    return None

def response_logging_middleware(request: Request, response: Response) -> Optional[Response]:
    """Response logging middleware (runs after handler)"""
    start_time = request.context.get('start_time', time.time())
    duration = (time.time() - start_time) * 1000  # ms

    logger.info(
        f"Request completed: {request.method} {request.path} "
        f"[{response.status_code}] in {duration:.2f}ms"
    )

    return None

# Usage
@app.get("/api/logs", middleware=[logging_middleware, response_logging_middleware])
def logged_endpoint(request):
    return JSONResponse({"message": "This request is logged"})
```

### 5. JSON Validation Middleware

```python
import json
from jsonschema import validate, ValidationError

def json_validation_middleware(schema):
    """JSON validation middleware factory"""
    def middleware(request: Request, response: Response) -> Optional[Response]:
        if request.method in ['POST', 'PUT', 'PATCH']:
            try:
                # Parse JSON body
                body = request.get_body()
                if body:
                    data = json.loads(body)
                    validate(data, schema)  # Validate against JSON schema
                    request.context['validated_data'] = data
            except json.JSONDecodeError:
                return JSONResponse(
                    {"error": "Invalid JSON format"},
                    status_code=400
                )
            except ValidationError as e:
                return JSONResponse(
                    {"error": f"Validation error: {e.message}"},
                    status_code=400
                )

        return None

    return middleware

# Usage
user_schema = {
    "type": "object",
    "properties": {
        "name": {"type": "string", "minLength": 1},
        "email": {"type": "string", "format": "email"}
    },
    "required": ["name", "email"]
}

@app.post("/users", middleware=[json_validation_middleware(user_schema)])
def create_user(request):
    user_data = request.context['validated_data']
    return JSONResponse({"user": user_data, "created": True})
```

---

## 🔗 Combining Middleware

### Middleware Chains

```python
# Define reusable middleware combinations
API_MIDDLEWARE = [auth_middleware, rate_limit_middleware(50), cors_middleware()]
ADMIN_MIDDLEWARE = [auth_middleware, admin_role_middleware, audit_logger]
PUBLIC_MIDDLEWARE = [cors_middleware(), logging_middleware]

# Apply different middleware combinations
@app.get("/public/info", middleware=PUBLIC_MIDDLEWARE)
def public_info(request):
    return JSONResponse({"info": "public"})

@app.get("/api/users", middleware=API_MIDDLEWARE)
def get_users(request):
    return JSONResponse({"users": []})

@app.get("/admin/stats", middleware=ADMIN_MIDDLEWARE)
def admin_stats(request):
    return JSONResponse({"stats": "admin only"})
```

### Conditional Middleware

```python
def conditional_middleware(condition_func, middleware_func):
    """Apply middleware only if condition is met"""
    def middleware(request: Request, response: Response) -> Optional[Response]:
        if condition_func(request):
            return middleware_func(request, response)
        return None
    return middleware

def is_api_request(request):
    return request.path.startswith('/api/')

# Only apply rate limiting to API requests
conditional_rate_limit = conditional_middleware(
    is_api_request,
    rate_limit_middleware(100)
)

@app.get("/api/data", middleware=[conditional_rate_limit])
def api_data(request):
    return JSONResponse({"data": "api"})

@app.get("/regular", middleware=[conditional_rate_limit])  # Won't be rate limited
def regular_page(request):
    return JSONResponse({"page": "regular"})
```

---

## 🔒 Security Best Practices

### 1. Explicit Security Model

```python
# ✅ Good: Explicit middleware makes security visible
@app.get("/admin/users", middleware=[auth_middleware, admin_role_middleware])
def admin_users(request):
    return JSONResponse({"admin_users": []})

# ✅ Good: Public endpoints are clearly public
@app.get("/health")  # No middleware = clearly public
def health_check(request):
    return JSONResponse({"status": "ok"})

# ❌ Avoid: Relying on global middleware for security
# Global middleware can be forgotten or bypassed
```

### 2. Defense in Depth

```python
# Multiple security layers
@app.delete("/admin/users/{user_id}", middleware=[
    auth_middleware,           # Authentication
    admin_role_middleware,     # Authorization
    rate_limit_middleware(5),  # Strict rate limiting for destructive actions
    audit_log_middleware,      # Audit trail
    csrf_protection_middleware # CSRF protection
])
def delete_user(request):
    user_id = request.path_params.get('user_id')
    return JSONResponse({"deleted": user_id})
```

### 3. Role-Based Access Control

```python
def role_required(required_roles):
    """Role-based access control middleware"""
    def middleware(request: Request, response: Response) -> Optional[Response]:
        user = request.context.get('user')
        if not user:
            return JSONResponse({"error": "Authentication required"}, status_code=401)

        user_roles = set(user.get('roles', []))
        if not user_roles.intersection(set(required_roles)):
            return JSONResponse(
                {"error": f"Requires one of: {', '.join(required_roles)}"},
                status_code=403
            )

        return None
    return middleware

# Usage
@app.get("/admin/dashboard", middleware=[
    auth_middleware,
    role_required(['admin', 'super_admin'])
])
def admin_dashboard(request):
    return JSONResponse({"dashboard": "admin"})

@app.post("/users", middleware=[
    auth_middleware,
    role_required(['admin', 'manager', 'user'])
])
def create_user(request):
    return JSONResponse({"user": "created"})
```

---

## ⚡ Performance Benefits

### 1. Route-Specific Execution

```python
# Traditional global middleware runs on EVERY request
@app.middleware("http")  # FastAPI style - runs on ALL routes
async def global_middleware(request, call_next):
    # Runs for /health, /docs, /favicon.ico, everything!
    response = await call_next(request)
    return response

# Catzilla per-route middleware - only runs when needed
@app.get("/health")  # No middleware = ultra-fast
def health(request):
    return JSONResponse({"status": "ok"})

@app.get("/api/data", middleware=[auth_middleware])  # Only runs auth when needed
def api_data(request):
    return JSONResponse({"data": []})
```

### 2. C-Accelerated Execution

- **Middleware registration**: Stored in C data structures for fast lookup
- **Route matching**: C-based trie matching identifies middleware to run
- **Execution**: Middleware functions called directly from C with minimal Python overhead
- **Memory efficiency**: Zero allocation design with memory pooling

### 3. Performance Comparison

```python
# Performance characteristics (approximate)
# Route without middleware:     ~5-10μs
# Route with 1 middleware:      ~15-25μs
# Route with 3 middleware:      ~35-50μs
# Route with 5 middleware:      ~55-75μs

# Compare to FastAPI global middleware:
# Any route with global middleware: ~100-500μs
```

---

## 🧪 Testing Middleware

### Unit Testing Individual Middleware

```python
import pytest
from unittest.mock import Mock
from catzilla import Request, Response, JSONResponse

def test_auth_middleware_success():
    """Test successful authentication"""
    request = Mock(spec=Request)
    response = Mock(spec=Response)
    request.headers = {'Authorization': 'Bearer valid_token'}

    result = auth_middleware(request, response)

    assert result is None  # Should continue processing

def test_auth_middleware_failure():
    """Test authentication failure"""
    request = Mock(spec=Request)
    response = Mock(spec=Response)
    request.headers = {}  # No auth header

    result = auth_middleware(request, response)

    assert isinstance(result, JSONResponse)
    assert result.status_code == 401

def test_rate_limit_middleware():
    """Test rate limiting"""
    request = Mock(spec=Request)
    response = Mock(spec=Response)
    request.environ = {'REMOTE_ADDR': '127.0.0.1'}

    rate_limiter = rate_limit_middleware(max_requests=2, window_seconds=60)

    # First request should pass
    result1 = rate_limiter(request, response)
    assert result1 is None

    # Second request should pass
    result2 = rate_limiter(request, response)
    assert result2 is None

    # Third request should be rate limited
    result3 = rate_limiter(request, response)
    assert isinstance(result3, JSONResponse)
    assert result3.status_code == 429
```

### Integration Testing with Routes

```python
def test_protected_route_with_auth():
    """Test route with authentication middleware"""
    app = Catzilla()

    @app.get("/protected", middleware=[auth_middleware])
    def protected(request):
        return JSONResponse({"message": "protected"})

    # Test without authentication
    response = app.test_client().get("/protected")
    assert response.status_code == 401

    # Test with authentication
    response = app.test_client().get(
        "/protected",
        headers={"Authorization": "Bearer valid_token"}
    )
    assert response.status_code == 200
    assert response.json()["message"] == "protected"

def test_middleware_execution_order():
    """Test that middleware executes in correct order"""
    execution_order = []

    def middleware_1(request, response):
        execution_order.append("middleware_1")
        return None

    def middleware_2(request, response):
        execution_order.append("middleware_2")
        return None

    app = Catzilla()

    @app.get("/test", middleware=[middleware_1, middleware_2])
    def test_handler(request):
        execution_order.append("handler")
        return JSONResponse({"ok": True})

    response = app.test_client().get("/test")

    assert execution_order == ["middleware_1", "middleware_2", "handler"]
    assert response.status_code == 200
```

---

## 🔄 Migration from Other Frameworks

### From FastAPI

```python
# FastAPI global middleware
@app.middleware("http")
async def fastapi_middleware(request: Request, call_next):
    # Runs on EVERY request
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response

# Catzilla per-route middleware
def timing_middleware(request: Request, response: Response) -> Optional[Response]:
    start_time = time.time()
    request.context['start_time'] = start_time
    return None

def add_timing_header(request: Request, response: Response) -> Optional[Response]:
    start_time = request.context.get('start_time', time.time())
    process_time = time.time() - start_time
    response.set_header("X-Process-Time", str(process_time))
    return None

# Apply only to routes that need timing
@app.get("/api/timed", middleware=[timing_middleware, add_timing_header])
def timed_endpoint(request):
    return JSONResponse({"data": "timed"})
```

### From Flask

```python
# Flask before_request (global)
@app.before_request
def flask_auth():
    if request.path.startswith('/api/'):
        # Check authentication
        pass

# Catzilla per-route (more explicit)
@app.get("/api/data", middleware=[auth_middleware])
def api_data(request):
    return JSONResponse({"data": []})

@app.get("/public")  # No auth needed - explicit
def public_page(request):
    return JSONResponse({"message": "public"})
```

### From Django

```python
# Django middleware (global, in settings.py)
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    # Runs on ALL requests
]

# Catzilla per-route
security_middleware = [csrf_protection, session_middleware]

@app.get("/admin/panel", middleware=security_middleware)
def admin_panel(request):
    return JSONResponse({"panel": "admin"})

@app.get("/api/health")  # No session/CSRF needed
def health_check(request):
    return JSONResponse({"status": "ok"})
```

---

## 🔍 Debugging and Introspection

### Viewing Route Middleware

```python
# Get all routes with their middleware
for route in app.router._route_list:
    print(f"{route.method} {route.path}")
    if route.middleware:
        for mw in route.middleware:
            print(f"  - {mw.__name__}")
    else:
        print("  - No middleware")

# Output:
# GET /health
#   - No middleware
# GET /api/data
#   - auth_middleware
#   - rate_limit_middleware
# POST /users
#   - auth_middleware
#   - json_validator
```

### Middleware Execution Debugging

```python
def debug_middleware(name):
    """Middleware that logs its execution"""
    def middleware(request: Request, response: Response) -> Optional[Response]:
        print(f"🔧 {name} middleware executing for {request.method} {request.path}")
        return None
    middleware.__name__ = f"debug_{name}"
    return middleware

@app.get("/debug", middleware=[
    debug_middleware("auth"),
    debug_middleware("validation"),
    debug_middleware("logging")
])
def debug_endpoint(request):
    print("🎯 Handler executing")
    return JSONResponse({"debug": True})

# Output when calling GET /debug:
# 🔧 auth middleware executing for GET /debug
# 🔧 validation middleware executing for GET /debug
# 🔧 logging middleware executing for GET /debug
# 🎯 Handler executing
```

---

## 📊 Advanced Use Cases

### 1. API Versioning with Middleware

```python
def api_version_middleware(version):
    """API versioning middleware"""
    def middleware(request: Request, response: Response) -> Optional[Response]:
        request.context['api_version'] = version
        response.set_header('X-API-Version', version)
        return None
    return middleware

# Version-specific middleware
v1_middleware = [api_version_middleware('v1'), legacy_auth_middleware]
v2_middleware = [api_version_middleware('v2'), modern_auth_middleware, rate_limiter]

@app.get("/v1/users", middleware=v1_middleware)
def get_users_v1(request):
    return JSONResponse({"users": [], "version": "v1"})

@app.get("/v2/users", middleware=v2_middleware)
def get_users_v2(request):
    return JSONResponse({"users": [], "version": "v2", "enhanced": True})
```

### 2. Feature Flags with Middleware

```python
def feature_flag_middleware(feature_name):
    """Feature flag middleware"""
    def middleware(request: Request, response: Response) -> Optional[Response]:
        if not is_feature_enabled(feature_name, request.context.get('user')):
            return JSONResponse(
                {"error": "Feature not available"},
                status_code=404
            )
        return None
    return middleware

@app.get("/beta/new-feature", middleware=[
    auth_middleware,
    feature_flag_middleware('new_feature_beta')
])
def beta_feature(request):
    return JSONResponse({"feature": "beta", "enabled": True})
```

### 3. Request Transformation Middleware

```python
def json_to_form_middleware(request: Request, response: Response) -> Optional[Response]:
    """Transform JSON requests to form data for legacy handlers"""
    if request.headers.get('Content-Type') == 'application/json':
        try:
            json_data = json.loads(request.get_body())
            # Transform to form data format
            request.context['form_data'] = json_data
        except json.JSONDecodeError:
            return JSONResponse({"error": "Invalid JSON"}, status_code=400)
    return None

@app.post("/legacy/submit", middleware=[json_to_form_middleware])
def legacy_handler(request):
    form_data = request.context.get('form_data', {})
    return JSONResponse({"received": form_data, "processed": True})
```

---

## 🛡️ Error Handling in Middleware

### Graceful Error Handling

```python
def safe_middleware(request: Request, response: Response) -> Optional[Response]:
    """Middleware with error handling"""
    try:
        # Middleware logic that might fail
        result = some_external_service_call()
        request.context['external_data'] = result
        return None
    except ExternalServiceError as e:
        # Log error but don't break the request
        logger.error(f"External service failed: {e}")
        request.context['external_data'] = None
        return None
    except CriticalError as e:
        # For critical errors, stop the request
        logger.critical(f"Critical error in middleware: {e}")
        return JSONResponse(
            {"error": "Service temporarily unavailable"},
            status_code=503
        )

def error_recovery_middleware(request: Request, response: Response) -> Optional[Response]:
    """Middleware that provides fallbacks"""
    if 'error' in request.context:
        # Previous middleware had an error, provide fallback
        request.context['fallback_mode'] = True
    return None

@app.get("/resilient", middleware=[safe_middleware, error_recovery_middleware])
def resilient_endpoint(request):
    if request.context.get('fallback_mode'):
        return JSONResponse({"message": "fallback response"})

    external_data = request.context.get('external_data')
    return JSONResponse({"data": external_data})
```

---

## 📈 Performance Monitoring

### Middleware Performance Metrics

```python
import time
from collections import defaultdict

middleware_metrics = defaultdict(list)

def performance_monitoring_middleware(middleware_name):
    """Monitor middleware performance"""
    def middleware(request: Request, response: Response) -> Optional[Response]:
        start_time = time.perf_counter()

        # Store for cleanup after request
        if 'middleware_timings' not in request.context:
            request.context['middleware_timings'] = []

        def record_timing():
            end_time = time.perf_counter()
            duration = (end_time - start_time) * 1000  # ms
            middleware_metrics[middleware_name].append(duration)
            request.context['middleware_timings'].append({
                'name': middleware_name,
                'duration_ms': duration
            })

        # Schedule timing recording
        response.on_finish = record_timing
        return None

    return middleware

# Wrap existing middleware
monitored_auth = performance_monitoring_middleware('auth')(auth_middleware)
monitored_rate_limit = performance_monitoring_middleware('rate_limit')(rate_limit_middleware())

@app.get("/monitored", middleware=[monitored_auth, monitored_rate_limit])
def monitored_endpoint(request):
    return JSONResponse({
        "data": "response",
        "middleware_timings": request.context.get('middleware_timings', [])
    })

# Get performance statistics
@app.get("/admin/middleware-stats")
def middleware_stats(request):
    stats = {}
    for name, timings in middleware_metrics.items():
        if timings:
            stats[name] = {
                'count': len(timings),
                'avg_ms': sum(timings) / len(timings),
                'min_ms': min(timings),
                'max_ms': max(timings)
            }
    return JSONResponse({"middleware_performance": stats})
```

---

## 🎯 Best Practices Summary

### ✅ Do's

1. **Use per-route middleware for explicit security**
   ```python
   @app.get("/admin/users", middleware=[auth_middleware, admin_role_middleware])
   ```

2. **Keep middleware functions simple and focused**
   ```python
   def single_purpose_middleware(request, response):
       # Do one thing well
       return None
   ```

3. **Use middleware factories for configuration**
   ```python
   rate_limiter = rate_limit_middleware(max_requests=100, window=60)
   @app.get("/api/data", middleware=[rate_limiter])
   ```

4. **Handle errors gracefully**
   ```python
   def safe_middleware(request, response):
       try:
           # middleware logic
           return None
       except Exception as e:
           logger.error(f"Middleware error: {e}")
           return None  # Continue processing
   ```

5. **Use meaningful middleware names**
   ```python
   def user_authentication_middleware(request, response):
       pass
   user_authentication_middleware.__name__ = "user_auth"
   ```

### ❌ Don'ts

1. **Don't use global middleware for route-specific needs**
   ```python
   # ❌ Bad - applies to ALL routes
   @app.middleware("http")
   def admin_only_middleware(request, call_next):
       pass
   ```

2. **Don't make middleware stateful between requests**
   ```python
   # ❌ Bad - shared state
   request_counter = 0
   def bad_middleware(request, response):
       global request_counter
       request_counter += 1  # Race conditions!
   ```

3. **Don't ignore middleware return values**
   ```python
   # ❌ Bad - not checking if middleware short-circuited
   def bad_handler(request):
       # Handler might run even if auth failed
       return JSONResponse({"data": "secret"})
   ```

4. **Don't create overly complex middleware chains**
   ```python
   # ❌ Bad - too many middleware, hard to debug
   @app.get("/complex", middleware=[mw1, mw2, mw3, mw4, mw5, mw6, mw7])
   ```

---

## 🔗 Related Documentation

- [Advanced Global Middleware](middleware.md) - For cross-cutting concerns (CORS, logging, security headers)
- [Migration from FastAPI](migration_from_fastapi.md) - FastAPI compatibility guide
- [Error Handling](error-handling.md) - Error handling patterns
- [Performance Optimization](performance.md) - Performance tuning guide

---

**Need help?** Check out the [examples directory](../examples/per_route_middleware/) for complete working examples, or visit our [community forum](https://github.com/rezwanahmedsami/catzilla/discussions) for support.
