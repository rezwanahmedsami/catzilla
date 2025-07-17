#!/usr/bin/env python3
"""
🌪️ Catzilla Middleware Ordering Example

This example demonstrates how Catzilla's middleware system handles priority-based
ordering and execution flow using the real Catzilla middleware API.

Features demonstrated:
- Priority-based middleware ordering
- Global middleware execution
- Per-route middleware execution
- Middleware short-circuiting
- Request/response processing
- Execution tracking and analytics
"""

from catzilla import Catzilla, Request, Response, JSONResponse
from typing import Optional, Dict, Any, List
import time
import uuid

# Initialize Catzilla
app = Catzilla(
    production=False,
    show_banner=True,
    log_requests=True
)

print("🌪️ Catzilla Middleware Ordering Example")
print("=" * 50)

# Middleware execution tracking
middleware_execution_log: List[Dict[str, Any]] = []

# ============================================================================
# 1. GLOBAL MIDDLEWARE WITH DIFFERENT PRIORITIES
# ============================================================================

@app.middleware(priority=10, pre_route=True, name="first_middleware")
def first_middleware(request: Request) -> Optional[Response]:
    """First middleware to run (highest priority)"""
    execution_time = time.time()

    middleware_execution_log.append({
        "middleware": "first_middleware",
        "phase": "request",
        "timestamp": execution_time,
        "priority": 10
    })

    print("1️⃣ First Middleware: Running first (priority 10)")

    # Initialize request context
    if not hasattr(request, 'context'):
        request.context = {}
    request.context['request_id'] = str(uuid.uuid4())
    request.context['start_time'] = execution_time
    request.context['middleware_chain'] = ["first_middleware"]

    return None  # Continue to next middleware

@app.middleware(priority=50, pre_route=True, name="second_middleware")
def second_middleware(request: Request) -> Optional[Response]:
    """Second middleware to run (medium priority)"""
    execution_time = time.time()

    middleware_execution_log.append({
        "middleware": "second_middleware",
        "phase": "request",
        "timestamp": execution_time,
        "priority": 50
    })

    print("2️⃣ Second Middleware: Running second (priority 50)")

    # Add to middleware chain
    if hasattr(request, 'context') and 'middleware_chain' in request.context:
        request.context['middleware_chain'].append("second_middleware")

    return None  # Continue to next middleware

@app.middleware(priority=100, pre_route=True, name="third_middleware")
def third_middleware(request: Request) -> Optional[Response]:
    """Third middleware to run (lowest priority)"""
    execution_time = time.time()

    middleware_execution_log.append({
        "middleware": "third_middleware",
        "phase": "request",
        "timestamp": execution_time,
        "priority": 100
    })

    print("3️⃣ Third Middleware: Running third (priority 100)")

    # Add to middleware chain
    if hasattr(request, 'context') and 'middleware_chain' in request.context:
        request.context['middleware_chain'].append("third_middleware")

    return None  # Continue to next middleware

# ============================================================================
# 2. AUTHENTICATION MIDDLEWARE WITH SHORT-CIRCUITING
# ============================================================================

@app.middleware(priority=25, pre_route=True, name="auth_middleware")
def auth_middleware(request: Request) -> Optional[Response]:
    """Authentication middleware that can short-circuit"""
    execution_time = time.time()

    middleware_execution_log.append({
        "middleware": "auth_middleware",
        "phase": "request",
        "timestamp": execution_time,
        "priority": 25
    })

    print("🔐 Auth Middleware: Checking authentication (priority 25)")

    # Check for auth header
    auth_header = request.headers.get("authorization")

    # For /protected routes, enforce authentication
    if "/protected" in request.path:
        if not auth_header:
            print("❌ Auth Middleware: SHORT-CIRCUITING - No auth header")
            return JSONResponse({
                "error": "Authentication required",
                "middleware": "auth_middleware",
                "execution_order": len(middleware_execution_log),
                "short_circuited": True
            }, status_code=401)

        if not auth_header.startswith("Bearer "):
            print("❌ Auth Middleware: SHORT-CIRCUITING - Invalid auth format")
            return JSONResponse({
                "error": "Invalid authorization format",
                "middleware": "auth_middleware",
                "short_circuited": True
            }, status_code=401)

    # Add user info if authenticated
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header[7:]
        if hasattr(request, 'context'):
            request.context['user'] = {
                "token": token,
                "authenticated": True,
                "authenticated_at": execution_time
            }
            request.context['middleware_chain'].append("auth_middleware")

    print("✅ Auth Middleware: Continuing to next middleware")
    return None  # Continue to next middleware

# ============================================================================
# 3. POST-ROUTE MIDDLEWARE (RESPONSE PROCESSING)
# ============================================================================

@app.middleware(priority=10, pre_route=False, post_route=True, name="response_logger")
def response_logger(request: Request) -> Optional[Response]:
    """Response logging middleware"""
    execution_time = time.time()

    middleware_execution_log.append({
        "middleware": "response_logger",
        "phase": "response",
        "timestamp": execution_time,
        "priority": 10
    })

    # Calculate total request time
    start_time = getattr(request, 'context', {}).get('start_time', execution_time)
    total_time = (execution_time - start_time) * 1000  # Convert to milliseconds

    print(f"📊 Response Logger: Request completed in {total_time:.2f}ms")

    return None  # Don't modify response

@app.middleware(priority=50, pre_route=False, post_route=True, name="cors_response")
def cors_response(request: Request) -> Optional[Response]:
    """CORS response headers middleware"""
    execution_time = time.time()

    middleware_execution_log.append({
        "middleware": "cors_response",
        "phase": "response",
        "timestamp": execution_time,
        "priority": 50
    })

    print("🌍 CORS Response: Adding CORS headers to response")

    return None  # Don't modify response (headers would be added in real implementation)

# ============================================================================
# 4. PER-ROUTE MIDDLEWARE
# ============================================================================

def rate_limit_middleware(request: Request) -> Optional[Response]:
    """Per-route rate limiting middleware"""
    print("⏱️ Rate Limit Middleware: Checking rate limits")

    # Add to middleware chain
    if hasattr(request, 'context') and 'middleware_chain' in request.context:
        request.context['middleware_chain'].append("rate_limit_middleware")

    # Simple rate limit check (in real app, use Redis or similar)
    client_ip = request.headers.get("x-forwarded-for", "127.0.0.1")

    # For demo, allow all requests
    print(f"✅ Rate Limit Middleware: IP {client_ip} - OK")

    return None  # Continue to route handler

def admin_middleware(request: Request) -> Optional[Response]:
    """Per-route admin middleware"""
    print("👑 Admin Middleware: Checking admin privileges")

    # Add to middleware chain
    if hasattr(request, 'context') and 'middleware_chain' in request.context:
        request.context['middleware_chain'].append("admin_middleware")

    # Check if user is authenticated
    user = getattr(request, 'context', {}).get('user')
    if not user:
        return JSONResponse({
            "error": "Authentication required for admin access",
            "middleware": "admin_middleware"
        }, status_code=401)

    # Check admin token
    if user.get('token') != 'admin-token':
        return JSONResponse({
            "error": "Admin privileges required",
            "middleware": "admin_middleware"
        }, status_code=403)

    print("✅ Admin Middleware: Admin access granted")
    return None  # Continue to route handler

# ============================================================================
# 5. ROUTE HANDLERS
# ============================================================================

@app.get("/")
def home(request: Request) -> Response:
    """Home endpoint - demonstrates global middleware ordering"""
    context = getattr(request, 'context', {})

    return JSONResponse({
        "message": "🌪️ Catzilla Middleware Ordering Example",
        "middleware_execution_order": [
            "1. first_middleware (priority 10)",
            "2. auth_middleware (priority 25)",
            "3. second_middleware (priority 50)",
            "4. third_middleware (priority 100)"
        ],
        "request_id": context.get('request_id'),
        "middleware_chain": context.get('middleware_chain', []),
        "total_global_middleware": len(context.get('middleware_chain', [])),
        "note": "Lower priority numbers execute first"
    })

@app.get("/protected")
def protected_endpoint(request: Request) -> Response:
    """Protected endpoint - demonstrates auth middleware short-circuiting"""
    context = getattr(request, 'context', {})
    user = context.get('user', {})

    return JSONResponse({
        "message": "🔐 Protected endpoint accessed",
        "user": user,
        "middleware_chain": context.get('middleware_chain', []),
        "request_id": context.get('request_id'),
        "note": "This endpoint requires authentication"
    })

@app.get("/api/data", middleware=[rate_limit_middleware])
def api_data(request: Request) -> Response:
    """API endpoint with per-route middleware"""
    context = getattr(request, 'context', {})

    return JSONResponse({
        "message": "📊 API data endpoint",
        "data": {"items": [1, 2, 3], "total": 3},
        "middleware_chain": context.get('middleware_chain', []),
        "request_id": context.get('request_id'),
        "note": "Global middleware + per-route rate limiting"
    })

@app.post("/admin/action", middleware=[admin_middleware])
def admin_action(request: Request) -> Response:
    """Admin endpoint with multiple middleware layers"""
    context = getattr(request, 'context', {})
    user = context.get('user', {})

    return JSONResponse({
        "message": "👑 Admin action executed",
        "user": user,
        "middleware_chain": context.get('middleware_chain', []),
        "request_id": context.get('request_id'),
        "note": "Global middleware + admin middleware"
    })

@app.get("/middleware/execution-log")
def get_execution_log(request: Request) -> Response:
    """Get middleware execution log"""
    context = getattr(request, 'context', {})

    # Get recent executions
    recent_executions = middleware_execution_log[-20:]

    return JSONResponse({
        "message": "Middleware execution log",
        "recent_executions": recent_executions,
        "total_executions": len(middleware_execution_log),
        "request_id": context.get('request_id'),
        "middleware_chain": context.get('middleware_chain', [])
    })

@app.get("/middleware/stats")
def get_middleware_stats(request: Request) -> Response:
    """Get middleware performance statistics"""
    context = getattr(request, 'context', {})

    # Get app middleware stats
    app_stats = app.get_middleware_stats()

    return JSONResponse({
        "message": "Middleware performance statistics",
        "app_stats": app_stats,
        "execution_log_size": len(middleware_execution_log),
        "request_id": context.get('request_id'),
        "middleware_chain": context.get('middleware_chain', [])
    })

@app.post("/middleware/clear-log")
def clear_execution_log(request: Request) -> Response:
    """Clear middleware execution log"""
    global middleware_execution_log
    middleware_execution_log.clear()

    return JSONResponse({
        "message": "Middleware execution log cleared",
        "new_log_size": len(middleware_execution_log)
    })

# ============================================================================
# 6. ERROR DEMONSTRATION
# ============================================================================

@app.get("/error")
def error_endpoint(request: Request) -> Response:
    """Endpoint that triggers an error"""
    context = getattr(request, 'context', {})

    # This will trigger an error to show middleware behavior
    raise ValueError("Test error - middleware should still execute")

# ============================================================================
# 7. APPLICATION STARTUP
# ============================================================================

if __name__ == "__main__":
    print("\n🎯 Starting Catzilla Middleware Ordering Example...")
    print("\nGlobal Middleware Execution Order:")
    print("  1. first_middleware (priority 10) - Runs first")
    print("  2. auth_middleware (priority 25) - Can short-circuit")
    print("  3. second_middleware (priority 50) - Runs third")
    print("  4. third_middleware (priority 100) - Runs last")
    print("\nPost-Route Middleware:")
    print("  1. response_logger (priority 10) - Logs response")
    print("  2. cors_response (priority 50) - Adds CORS headers")

    print("\nAvailable endpoints:")
    print("  GET  /                        - Home (global middleware only)")
    print("  GET  /protected               - Protected endpoint (auth required)")
    print("  GET  /api/data                - API with rate limiting")
    print("  POST /admin/action            - Admin-only endpoint")
    print("  GET  /middleware/execution-log - View execution log")
    print("  GET  /middleware/stats        - Performance statistics")
    print("  POST /middleware/clear-log    - Clear execution log")
    print("  GET  /error                   - Error endpoint")

    print("\n🧪 Try these examples:")
    print("  # Normal request (all global middleware)")
    print("  curl http://localhost:8000/")
    print()
    print("  # Protected endpoint without auth (short-circuit)")
    print("  curl http://localhost:8000/protected")
    print()
    print("  # Protected endpoint with auth")
    print("  curl -H 'Authorization: Bearer test-token' http://localhost:8000/protected")
    print()
    print("  # Admin endpoint with admin token")
    print("  curl -H 'Authorization: Bearer admin-token' -X POST http://localhost:8000/admin/action")
    print()
    print("  # View execution log")
    print("  curl http://localhost:8000/middleware/execution-log")
    print()
    print("  # Performance stats")
    print("  curl http://localhost:8000/middleware/stats")

    print(f"\n🚀 Server starting on http://localhost:8000")
    app.listen(8000)
