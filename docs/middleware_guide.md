# 🌪️ Catzilla Middleware Guide - Getting Started

*A practical, easy-to-understand guide to using Catzilla's powerful middleware system*

## 🚀 What is Middleware?

Middleware in Catzilla allows you to run code **before** and **after** your route handlers. Think of it as a pipeline where each request flows through multiple middleware functions before reaching your route handler.

```
Request → Middleware 1 → Middleware 2 → Route Handler → Response
```

## 🎯 Quick Start

### Basic Middleware

```python
from catzilla import Catzilla
from catzilla.middleware import Response

app = Catzilla()

# Simple logging middleware
@app.middleware(priority=10, pre_route=True)
def log_requests(request):
    print(f"📥 {request.method} {request.path}")
    return None  # Continue to next middleware

@app.route('/hello')
def hello(request):
    return "Hello World!"

if __name__ == '__main__':
    app.run()
```

### Auth Middleware

```python
@app.middleware(priority=50, pre_route=True)
def auth_middleware(request):
    # Skip auth for public endpoints
    if request.path in ['/health', '/login']:
        return None

    # Check for auth header
    auth_header = request.headers.get('Authorization', '')
    if not auth_header.startswith('Bearer '):
        return Response("Unauthorized", status_code=401)

    # Store user info for route handlers
    token = auth_header[7:]  # Remove 'Bearer '

    # Initialize context if needed
    if not hasattr(request, '_context'):
        request._context = {}

    request._context['user'] = get_user_from_token(token)
    return None
```

## 📖 Core Concepts

### 1. Middleware Registration

Use the `@app.middleware()` decorator to register middleware:

```python
@app.middleware(
    priority=50,        # Lower numbers run first (0-100)
    pre_route=True,     # Run before route handler
    post_route=False,   # Run after route handler (optional)
    name="my_middleware"  # Optional name for debugging
)
def my_middleware(request):
    # Your middleware logic here
    return None  # Continue to next middleware
```

### 2. Middleware Priorities

Middleware runs in **priority order** (lower numbers first):

```python
@app.middleware(priority=10)  # Runs FIRST
def middleware_1(request): pass

@app.middleware(priority=20)  # Runs SECOND
def middleware_2(request): pass

@app.middleware(priority=30)  # Runs THIRD
def middleware_3(request): pass
```

### 3. Pre-route vs Post-route

```python
# Pre-route: Runs BEFORE your route handler
@app.middleware(priority=50, pre_route=True)
def auth_middleware(request):
    # Check authentication, validate input, etc.
    return None

# Post-route: Runs AFTER your route handler
@app.middleware(priority=50, post_route=True)
def response_middleware(request, response):
    # Modify response, add headers, log response, etc.
    response.headers['X-Custom'] = 'Added by middleware'
    return response
```

### 4. Returning Responses

Middleware can **short-circuit** the request by returning a Response:

```python
@app.middleware(priority=50, pre_route=True)
def rate_limit_middleware(request):
    if too_many_requests(request.remote_addr):
        # Stop processing and return error immediately
        return Response("Rate limit exceeded", status_code=429)

    # Continue to next middleware/route handler
    return None
```

## 🛠️ Common Middleware Patterns

### 1. Authentication

```python
@app.middleware(priority=50, pre_route=True)
def auth_middleware(request):
    """Simple token authentication"""

    # Skip auth for public endpoints
    public_paths = ['/health', '/login', '/register', '/docs']
    if request.path in public_paths:
        return None

    # Check authorization header
    auth_header = request.headers.get('Authorization', '')
    if not auth_header.startswith('Bearer '):
        return Response(
            {"error": "Authentication required"},
            status_code=401
        )

    # Validate token (implement your own logic)
    token = auth_header[7:]
    user = validate_token(token)
    if not user:
        return Response(
            {"error": "Invalid token"},
            status_code=401
        )

    # Store user for route handlers
    request.context['user'] = user
    return None

# Use in route handlers
@app.route('/profile')
def get_profile(request):
    user = request.context['user']  # User from middleware
    return {"user": user.name, "email": user.email}
```

### 2. CORS (Cross-Origin Resource Sharing)

```python
@app.middleware(priority=10, pre_route=True)
def cors_preflight(request):
    """Handle CORS preflight requests"""
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

@app.middleware(priority=90, post_route=True)
def cors_headers(request, response):
    """Add CORS headers to all responses"""
    response.headers.update({
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Credentials": "true"
    })
    return response
```

### 3. Request Logging

```python
import time

@app.middleware(priority=1, pre_route=True)
def request_logger(request):
    """Log requests with timing"""
    print(f"📥 {request.method} {request.path} from {request.remote_addr}")
    request.context['start_time'] = time.time()
    return None

@app.middleware(priority=99, post_route=True)
def response_logger(request, response):
    """Log response with duration"""
    duration = time.time() - request.context.get('start_time', 0)
    print(f"📤 {response.status_code} - {duration*1000:.1f}ms")
    return response
```

### 4. Error Handling

```python
@app.middleware(priority=95, post_route=True)
def error_handler(request, response):
    """Global error response formatting"""

    # Add consistent error format for 4xx/5xx responses
    if response.status_code >= 400:
        # Ensure JSON content type for errors
        if 'Content-Type' not in response.headers:
            response.headers['Content-Type'] = 'application/json'

        # Add error tracking ID
        import uuid
        response.headers['X-Error-ID'] = str(uuid.uuid4())

    return response
```

### 5. Rate Limiting

```python
import time
from collections import defaultdict

# Simple in-memory rate limiter (use Redis in production)
request_counts = defaultdict(list)

@app.middleware(priority=30, pre_route=True)
def rate_limit_middleware(request):
    """Simple rate limiting: 100 requests per minute"""

    client_ip = request.remote_addr
    now = time.time()

    # Clean old requests (older than 1 minute)
    request_counts[client_ip] = [
        req_time for req_time in request_counts[client_ip]
        if now - req_time < 60
    ]

    # Check if too many requests
    if len(request_counts[client_ip]) >= 100:
        return Response(
            {"error": "Rate limit exceeded. Try again later."},
            status_code=429
        )

    # Record this request
    request_counts[client_ip].append(now)
    return None
```

## 🎓 Advanced Usage

### Sharing Data Between Middleware

Use `request._context` to share data:

```python
@app.middleware(priority=20, pre_route=True)
def user_loader(request):
    """Load user information"""
    user_id = get_user_id_from_request(request)

    # Initialize context if needed
    if not hasattr(request, '_context'):
        request._context = {}

    request._context['user_id'] = user_id
    request._context['user'] = load_user(user_id)
    return None

@app.middleware(priority=40, pre_route=True)
def permission_checker(request):
    """Check permissions using loaded user"""
    user = getattr(request, '_context', {}).get('user')
    required_permission = get_required_permission(request.path)

    if not user.has_permission(required_permission):
        return Response("Forbidden", status_code=403)

    return None
```

### Conditional Middleware

```python
@app.middleware(priority=50, pre_route=True)
def admin_only_middleware(request):
    """Only apply to admin endpoints"""

    # Only check auth for admin paths
    if not request.path.startswith('/admin/'):
        return None

    # Admin-specific authentication logic
    if not is_admin_user(request):
        return Response("Admin access required", status_code=403)

    return None
```

### JSON Request Processing

```python
@app.middleware(priority=30, pre_route=True)
def json_processor(request):
    """Parse JSON requests and validate content type"""

    # Only process POST/PUT/PATCH requests
    if request.method not in ['POST', 'PUT', 'PATCH']:
        return None

    # Check content type
    content_type = request.headers.get('Content-Type', '')
    if not content_type.startswith('application/json'):
        return Response(
            {"error": "Content-Type must be application/json"},
            status_code=400
        )

    # Parse JSON (simplified - Catzilla handles this automatically)
    try:
        # JSON parsing is handled by Catzilla automatically
        # This is just for additional validation
        if hasattr(request, 'json') and request.json is None:
            return Response(
                {"error": "Invalid JSON"},
                status_code=400
            )
    except Exception:
        return Response(
            {"error": "Invalid JSON format"},
            status_code=400
        )

    return None
```

## 🧪 Testing Middleware

### Unit Testing

```python
import pytest
from catzilla.testing import TestClient

@pytest.fixture
def client():
    return TestClient(app)

def test_auth_middleware_blocks_unauthenticated(client):
    """Test that middleware blocks requests without auth"""
    response = client.get('/profile')
    assert response.status_code == 401
    assert "Authentication required" in response.json()["error"]

def test_auth_middleware_allows_authenticated(client):
    """Test that middleware allows valid requests"""
    headers = {'Authorization': 'Bearer valid_token_here'}
    response = client.get('/profile', headers=headers)
    assert response.status_code == 200

def test_cors_preflight(client):
    """Test CORS preflight handling"""
    response = client.options('/api/users')
    assert response.status_code == 200
    assert 'Access-Control-Allow-Origin' in response.headers
```

## ⚠️ Common Mistakes

### 1. Wrong Priority Order
```python
# ❌ WRONG - Auth should run before business logic
@app.middleware(priority=90)  # Runs LATE
def auth_middleware(request): pass

@app.middleware(priority=10)  # Runs EARLY
def business_logic_middleware(request): pass

# ✅ CORRECT - Auth runs first
@app.middleware(priority=10)  # Runs EARLY
def auth_middleware(request): pass

@app.middleware(priority=50)  # Runs LATER
def business_logic_middleware(request): pass
```

### 2. Forgetting to Return None
```python
# ❌ WRONG - No return statement
@app.middleware(priority=50, pre_route=True)
def bad_middleware(request):
    print("Processing request")
    # Missing return None!

# ✅ CORRECT - Always return None to continue
@app.middleware(priority=50, pre_route=True)
def good_middleware(request):
    print("Processing request")
    return None  # Continue to next middleware
```

### 3. Wrong Response API
```python
# ❌ WRONG - Old API style
def middleware(request):
    return Response(status=401, body="Unauthorized")

# ✅ CORRECT - Current API
def middleware(request):
    return Response("Unauthorized", status_code=401)
```

## 🎯 Best Practices

### 1. Keep Middleware Simple
- Do one thing well
- Avoid complex business logic
- Use clear, descriptive names

### 2. Order Matters
```python
# Recommended priority ranges:
# 1-10:   Request setup (CORS, logging)
# 20-40:  Authentication & authorization
# 50-70:  Validation & rate limiting
# 80-90:  Business logic middleware
# 91-99:  Response processing
```

### 3. Error Handling
```python
@app.middleware(priority=50, pre_route=True)
def safe_middleware(request):
    try:
        # Your middleware logic
        result = process_request(request)
        request.context['result'] = result
        return None
    except ValidationError as e:
        return Response(
            {"error": "Validation failed", "details": str(e)},
            status_code=400
        )
    except Exception as e:
        # Log the error
        print(f"Middleware error: {e}")
        return Response(
            {"error": "Internal server error"},
            status_code=500
        )
```

### 4. Use Context Efficiently
```python
# ✅ Good: Store useful data
if not hasattr(request, '_context'):
    request._context = {}

request._context['user'] = user_object
request._context['start_time'] = time.time()

# ❌ Avoid: Large objects or sensitive data
request._context['entire_database'] = db.get_all()  # Too big!
request._context['password'] = user.password        # Sensitive!
```

## 🔗 Next Steps

Once you're comfortable with basic middleware:

1. **[Advanced Features](middleware.md)** - Zero-allocation optimization, built-in middleware
2. **[Integration with DI](simple_di_guide.md)** - Using dependency injection in middleware
3. **[Performance Tips](performance.md)** - Optimizing middleware for production
4. **[Examples](../examples/middleware/)** - Complete working examples

## 💡 Real-World Example

Here's a complete example combining multiple middleware:

```python
from catzilla import Catzilla
from catzilla.middleware import Response
import time

app = Catzilla()

# 1. Request logging (priority 5)
@app.middleware(priority=5, pre_route=True)
def request_logger(request):
    print(f"📥 {request.method} {request.path}")
    request.context['start_time'] = time.time()
    return None

# 2. CORS (priority 10)
@app.middleware(priority=10, pre_route=True)
def cors_preflight(request):
    if request.method == "OPTIONS":
        return Response("", status_code=200, headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET,POST,PUT,DELETE",
            "Access-Control-Allow-Headers": "Content-Type,Authorization"
        })
    return None

# 3. Authentication (priority 30)
@app.middleware(priority=30, pre_route=True)
def auth_middleware(request):
    if request.path in ['/health', '/login']:
        return None

    auth_header = request.headers.get('Authorization', '')
    if not auth_header.startswith('Bearer '):
        return Response({"error": "Authentication required"}, status_code=401)

    request.context['user'] = 'authenticated_user'
    return None

# 4. Add CORS headers to responses (priority 90)
@app.middleware(priority=90, post_route=True)
def cors_response(request, response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    return response

# 5. Response logging (priority 95)
@app.middleware(priority=95, post_route=True)
def response_logger(request, response):
    duration = time.time() - request.context.get('start_time', 0)
    print(f"📤 {response.status_code} - {duration*1000:.1f}ms")
    return response

# Routes
@app.route('/health')
def health(request):
    return {"status": "ok"}

@app.route('/profile')
def profile(request):
    user = request.context['user']
    return {"message": f"Hello {user}!"}

if __name__ == '__main__':
    app.run(port=8000)
```

**Test it:**
```bash
# Public endpoint (no auth required)
curl http://localhost:8000/health

# Protected endpoint (auth required)
curl -H "Authorization: Bearer my-token" http://localhost:8000/profile

# CORS preflight
curl -X OPTIONS http://localhost:8000/profile
```

This guide should get you started with Catzilla's powerful middleware system! 🚀
