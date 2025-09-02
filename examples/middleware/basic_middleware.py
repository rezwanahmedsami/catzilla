#!/usr/bin/env python3
"""
🌪️ Catzilla Basic Middleware Example

This example demonstrates Catzilla's middleware system with both global
and per-route middleware using the real Catzilla API.

Features demonstrated:
- Global middleware with @app.middleware() decorator
- Per-route middleware using middleware=[] parameter
- Group-level middleware with RouterGroup middleware=[] parameter
- Middleware priority and execution order
- Request/response processing
- Middleware short-circuiting
"""

from catzilla import Catzilla, Request, Response, JSONResponse
from catzilla.router import RouterGroup
from typing import Optional
import time

# Initialize Catzilla - signal handling is now automatically native C for better performance
app = Catzilla(
    production=False,
    show_banner=True,
    log_requests=True
)

print("🌪️ Catzilla Basic Middleware Example")
print("=" * 50)

# ============================================================================
# 1. GLOBAL MIDDLEWARE - Runs on every request
# ============================================================================

@app.middleware(priority=10, pre_route=True, name="request_logger")
def request_logger_middleware(request: Request) -> Optional[Response]:
    """Log all incoming requests - runs first due to high priority"""
    start_time = time.time()

    # Store start time in request context for response timing
    if not hasattr(request, 'context'):
        request.context = {}
    request.context['start_time'] = start_time
    request.context['request_id'] = f"req_{int(start_time * 1000)}"

    print(f"📝 Request Logger: {request.method} {request.path} - ID: {request.context['request_id']}")
    return None  # Continue to next middleware

@app.middleware(priority=50, pre_route=True, name="cors_handler")
def cors_middleware(request: Request) -> Optional[Response]:
    """CORS middleware - adds CORS headers to responses"""
    print("🌍 CORS Middleware: Processing request")

    # Note: OPTIONS requests are automatically handled by Catzilla's built-in CORS middleware
    # This middleware just adds CORS headers to regular responses
    print(f"🌍 CORS Middleware: Processing {request.method} request")

    # Add CORS info to request context for response processing
    if not hasattr(request, 'context'):
        request.context = {}
    request.context['cors_enabled'] = True

    return None  # Continue to next middleware

@app.middleware(priority=100, pre_route=True, name="security_headers")
def security_headers_middleware(request: Request) -> Optional[Response]:
    """Add security headers - runs after CORS"""
    print("🔒 Security Headers: Adding security context")

    # Add security info to request context
    if not hasattr(request, 'context'):
        request.context = {}
    request.context['security'] = {
        'https_only': False,  # Would be True in production
        'csrf_token': f"csrf_{int(time.time() * 1000)}",
        'request_origin': request.headers.get('origin', 'unknown')
    }

    return None  # Continue to next middleware

# ============================================================================
# 2. PER-ROUTE MIDDLEWARE - Runs only on specific routes
# ============================================================================

def auth_middleware(request: Request) -> Optional[Response]:
    """Authentication middleware for protected routes"""
    print("🔐 Auth Middleware: Checking authentication")

    # Debug: Print all headers to understand what's available
    print(f"🔍 Available headers: {list(request.headers.keys())}")
    print(f"🔍 All headers: {dict(request.headers)}")

    # Check for Authorization header (try different cases)
    auth_header = (
        request.headers.get("Authorization") or
        request.headers.get("authorization") or
        request.headers.get("AUTHORIZATION") or
        request.get_header("Authorization") or
        request.get_header("authorization")
    )

    if not auth_header:
        print("❌ Auth Middleware: No authorization header found")
        return JSONResponse({
            "error": "Authentication required",
            "message": "Please provide Authorization header",
            "example": "Authorization: Bearer your-token"
        }, status_code=401)

    if not auth_header.startswith("Bearer "):
        print("❌ Auth Middleware: Invalid authorization format")
        return JSONResponse({
            "error": "Invalid authorization format",
            "message": "Authorization header must start with 'Bearer '"
        }, status_code=401)

    # Extract token
    token = auth_header[7:]  # Remove "Bearer "

    # Simple token validation (in real app, verify with JWT/database)
    if token == "invalid":
        print("❌ Auth Middleware: Invalid token")
        return JSONResponse({
            "error": "Invalid token",
            "message": "The provided token is invalid"
        }, status_code=401)

    # Add user info to request context
    if not hasattr(request, 'context'):
        request.context = {}
    request.context['user'] = {
        "id": "user123",
        "name": "John Doe",
        "token": token,
        "authenticated_at": time.time()
    }

    print("✅ Auth Middleware: User authenticated successfully")
    return None  # Continue to route handler

def rate_limit_middleware(request: Request) -> Optional[Response]:
    """Rate limiting middleware"""
    print("⏱️ Rate Limit Middleware: Checking rate limits")

    # Simple rate limiting (in real app, use Redis or similar)
    client_ip = request.headers.get("x-forwarded-for", "127.0.0.1")

    # For demo, allow all requests but log the check
    print(f"⏱️ Rate Limit Middleware: IP {client_ip} - OK")

    if not hasattr(request, 'context'):
        request.context = {}
    request.context['rate_limit'] = {
        'ip': client_ip,
        'remaining': 100,
        'reset_time': time.time() + 3600
    }

    return None  # Continue to route handler

def admin_middleware(request: Request) -> Optional[Response]:
    """Admin-only middleware"""
    print("👑 Admin Middleware: Checking admin privileges")

    # Check if user is authenticated first
    user = getattr(request, 'context', {}).get('user')
    if not user:
        return JSONResponse({
            "error": "Authentication required",
            "message": "Admin access requires authentication"
        }, status_code=401)

    # Check admin privileges (in real app, check user roles)
    if user.get('token') != 'admin-token':
        return JSONResponse({
            "error": "Admin access required",
            "message": "This endpoint requires admin privileges"
        }, status_code=403)

    print("✅ Admin Middleware: Admin access granted")
    return None  # Continue to route handler

def api_middleware(request: Request) -> Optional[Response]:
    """API-specific middleware for API router group"""
    print("🔗 API Middleware: Adding API context")

    # Add API-specific info to request context
    if not hasattr(request, 'context'):
        request.context = {}
    request.context['api'] = {
        'version': 'v1',
        'rate_limited': True,
        'authenticated': hasattr(request, 'context') and 'user' in getattr(request, 'context', {}),
        'timestamp': time.time()
    }

    print("✅ API Middleware: API context added")
    return None  # Continue to route handler

# ============================================================================
# 3. RESPONSE MIDDLEWARE - Runs after route handlers
# ============================================================================

@app.middleware(priority=10, pre_route=False, post_route=True, name="response_timer")
def response_timer_middleware(request: Request) -> Optional[Response]:
    """Add response timing headers"""
    start_time = getattr(request, 'context', {}).get('start_time')
    if start_time:
        duration = (time.time() - start_time) * 1000  # Convert to milliseconds
        print(f"⏱️ Response Timer: Request completed in {duration:.2f}ms")

    return None  # Don't modify response, just log

# ============================================================================
# 4. GROUP MIDDLEWARE - Runs on all routes in a RouterGroup
# ============================================================================

# Create protected router group with group-level middleware
protected_group = RouterGroup(prefix="/protected", middleware=[auth_middleware])

# Create API router group with API-specific middleware
api_group = RouterGroup(prefix="/api", middleware=[api_middleware])

# Create admin router group with both auth and admin middleware
admin_group = RouterGroup(prefix="/admin", middleware=[auth_middleware, admin_middleware])

# ============================================================================
# 5. ROUTE HANDLERS
# ============================================================================

@app.get("/")
def home(request: Request) -> Response:
    """Public home endpoint - only global middleware runs"""
    return JSONResponse({
        "message": "🌪️ Catzilla Middleware Example",
        "info": "This endpoint runs global middleware only",
        "middleware_chain": [
            "1. Request Logger (priority 10)",
            "2. CORS Handler (priority 50)",
            "3. Security Headers (priority 100)"
        ],
        "request_id": getattr(request, 'context', {}).get('request_id'),
        "security": getattr(request, 'context', {}).get('security', {}),
        "note": "HEAD and OPTIONS methods work automatically"
    })

@app.get("/public")
def public_endpoint(request: Request) -> Response:
    """Public endpoint with rate limiting"""
    return JSONResponse({
        "message": "Public endpoint with rate limiting",
        "rate_limit": getattr(request, 'context', {}).get('rate_limit', {}),
        "request_id": getattr(request, 'context', {}).get('request_id')
    })

@app.get("/protected", middleware=[auth_middleware])
def protected_endpoint(request: Request) -> Response:
    """Protected endpoint requiring authentication"""
    user = getattr(request, 'context', {}).get('user', {})

    return JSONResponse({
        "message": "🔐 Protected content accessed successfully",
        "user": user,
        "access_time": time.time(),
        "middleware_chain": [
            "1. Global: Request Logger",
            "2. Global: CORS Handler",
            "3. Global: Security Headers",
            "4. Per-route: Auth Middleware"
        ]
    })

@app.get("/api/data", middleware=[auth_middleware, rate_limit_middleware])
def api_data(request: Request) -> Response:
    """API endpoint with auth and rate limiting"""
    user = getattr(request, 'context', {}).get('user', {})
    rate_limit = getattr(request, 'context', {}).get('rate_limit', {})

    return JSONResponse({
        "message": "API data retrieved",
        "data": {
            "items": ["item1", "item2", "item3"],
            "total": 3,
            "generated_at": time.time()
        },
        "user": user,
        "rate_limit": rate_limit,
        "middleware_chain": [
            "1. Global: Request Logger",
            "2. Global: CORS Handler",
            "3. Global: Security Headers",
            "4. Per-route: Auth Middleware",
            "5. Per-route: Rate Limit Middleware"
        ],
        "note": "HEAD and OPTIONS methods work automatically via GET route"
    })

@app.post("/admin/users", middleware=[auth_middleware, admin_middleware])
def create_user(request: Request) -> Response:
    """Admin-only endpoint for creating users"""
    user = getattr(request, 'context', {}).get('user', {})

    return JSONResponse({
        "message": "👑 Admin endpoint accessed",
        "action": "create_user",
        "admin_user": user,
        "created_at": time.time(),
        "middleware_chain": [
            "1. Global: Request Logger",
            "2. Global: CORS Handler",
            "3. Global: Security Headers",
            "4. Per-route: Auth Middleware",
            "5. Per-route: Admin Middleware"
        ]
    }, status_code=201)

@app.get("/middleware/stats")
def middleware_stats(request: Request) -> Response:
    """Get middleware performance statistics"""
    stats = app.get_middleware_stats()

    return JSONResponse({
        "message": "Middleware performance statistics",
        "stats": stats,
        "request_id": getattr(request, 'context', {}).get('request_id')
    })

# ============================================================================
# 6. ROUTER GROUP ENDPOINTS (with group middleware)
# ============================================================================

@protected_group.get("/profile")
def protected_profile(request: Request) -> Response:
    """Protected endpoint - group middleware (auth) runs automatically"""
    user = getattr(request, 'context', {}).get('user', {})

    return JSONResponse({
        "message": "🔐 Protected profile accessed via RouterGroup",
        "user": user,
        "group": "protected",
        "middleware_chain": [
            "1. Global: Request Logger",
            "2. Global: CORS Handler",
            "3. Global: Security Headers",
            "4. Group: Auth Middleware (from RouterGroup)"
        ]
    })

@protected_group.get("/settings")
def protected_settings(request: Request) -> Response:
    """Another protected endpoint - same group middleware applies"""
    user = getattr(request, 'context', {}).get('user', {})

    return JSONResponse({
        "message": "🔐 Protected settings accessed via RouterGroup",
        "user": user,
        "group": "protected"
    })

@api_group.get("/status")
def api_status(request: Request) -> Response:
    """API endpoint with group middleware"""
    api_context = getattr(request, 'context', {}).get('api', {})

    return JSONResponse({
        "message": "🔗 API status via RouterGroup",
        "api_context": api_context,
        "group": "api",
        "middleware_chain": [
            "1. Global: Request Logger",
            "2. Global: CORS Handler",
            "3. Global: Security Headers",
            "4. Group: API Middleware (from RouterGroup)"
        ]
    })

@api_group.get("/data", middleware=[rate_limit_middleware])
def api_data_with_extra(request: Request) -> Response:
    """API endpoint with group middleware + additional per-route middleware"""
    api_context = getattr(request, 'context', {}).get('api', {})
    rate_limit = getattr(request, 'context', {}).get('rate_limit', {})

    return JSONResponse({
        "message": "🔗 API data with group + per-route middleware",
        "api_context": api_context,
        "rate_limit": rate_limit,
        "group": "api",
        "middleware_chain": [
            "1. Global: Request Logger",
            "2. Global: CORS Handler",
            "3. Global: Security Headers",
            "4. Group: API Middleware (from RouterGroup)",
            "5. Per-route: Rate Limit Middleware"
        ]
    })

@admin_group.post("/users")
def admin_create_user(request: Request) -> Response:
    """Admin endpoint - both auth and admin middleware from group"""
    user = getattr(request, 'context', {}).get('user', {})

    return JSONResponse({
        "message": "👑 Admin user creation via RouterGroup",
        "admin_user": user,
        "group": "admin",
        "middleware_chain": [
            "1. Global: Request Logger",
            "2. Global: CORS Handler",
            "3. Global: Security Headers",
            "4. Group: Auth Middleware (from RouterGroup)",
            "5. Group: Admin Middleware (from RouterGroup)"
        ]
    }, status_code=201)

# Register router groups with the main app
app.include_routes(protected_group)
app.include_routes(api_group)
app.include_routes(admin_group)

# ============================================================================
# 7. ERROR HANDLING
# ============================================================================

@app.get("/error")
def error_endpoint(request: Request) -> Response:
    """Endpoint that triggers an error to test middleware behavior"""
    raise ValueError("This is a test error")

# ============================================================================
# 8. APPLICATION STARTUP
# ============================================================================

if __name__ == "__main__":
    print("\n🎯 Starting Catzilla Middleware Example...")
    print("\nAvailable endpoints:")
    print("  GET  /                   - Home (global middleware only)")
    print("  GET  /public             - Public endpoint")
    print("  GET  /protected          - Protected endpoint (requires auth)")
    print("  GET  /api/data           - API with auth + rate limiting")
    print("  POST /admin/users        - Admin-only endpoint")
    print("  GET  /middleware/stats   - Middleware performance stats")
    print("  GET  /error              - Error endpoint for testing")
    print("  Note: HEAD and OPTIONS methods work automatically for all GET routes!")
    print()
    print("  RouterGroup endpoints (with group middleware):")
    print("  GET  /protected/profile  - Protected profile (group auth)")
    print("  GET  /protected/settings - Protected settings (group auth)")
    print("  GET  /api/status         - API status (group API middleware)")
    print("  GET  /api/data           - API data (group + per-route middleware)")
    print("  POST /admin/users        - Admin user creation (group auth + admin)")

    print("\n🔧 Middleware Chain:")
    print("  Global Middleware (runs on all requests):")
    print("    1. Request Logger (priority 10)")
    print("    2. CORS Handler (priority 50)")
    print("    3. Security Headers (priority 100)")
    print("    4. Response Timer (post-route)")
    print("  Per-route Middleware (runs on specific routes):")
    print("    - Auth Middleware (authentication)")
    print("    - Rate Limit Middleware (rate limiting)")
    print("    - Admin Middleware (admin access)")
    print("  Group Middleware (runs on all routes in a RouterGroup):")
    print("    - Protected Group: Auth Middleware")
    print("    - API Group: API Middleware")
    print("    - Admin Group: Auth Middleware + Admin Middleware")

    print("\n🧪 Try these examples:")
    print("  # Public endpoint (global middleware only)")
    print("  curl http://localhost:8000/")
    print()
    print("  # Test automatic HEAD method")
    print("  curl -I http://localhost:8000/")
    print()
    print("  # Test automatic OPTIONS method")
    print("  curl -X OPTIONS http://localhost:8000/")
    print()
    print("  # Protected endpoint (will fail without auth)")
    print("  curl http://localhost:8000/protected")
    print()
    print("  # Protected endpoint with auth")
    print("  curl -H 'Authorization: Bearer my-token' http://localhost:8000/protected")
    print()
    print("  # Test HEAD with auth")
    print("  curl -I -H 'Authorization: Bearer my-token' http://localhost:8000/api/data")
    print()
    print("  # Admin endpoint (requires admin token)")
    print("  curl -H 'Authorization: Bearer admin-token' -X POST http://localhost:8000/admin/users")
    print()
    print("  # Middleware stats")
    print("  curl http://localhost:8000/middleware/stats")
    print()
    print("  # RouterGroup endpoints with group middleware")
    print("  curl -H 'Authorization: Bearer my-token' http://localhost:8000/protected/profile")
    print("  curl http://localhost:8000/api/status")
    print("  curl -H 'Authorization: Bearer my-token' http://localhost:8000/api/data")
    print("  curl -H 'Authorization: Bearer admin-token' -X POST http://localhost:8000/admin/users")

    print(f"\n🚀 Server starting on http://localhost:8000")
    print("Press Ctrl+C to stop the server")

    # Catzilla now handles graceful shutdown automatically!
    app.listen(8000)
