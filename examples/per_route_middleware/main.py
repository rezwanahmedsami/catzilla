"""
Per-Route Middleware Example for Catzilla
Demonstrates zero-allocation per-route middleware with C-accelerated performance.

This example shows how to use per-route middleware in Catzilla to:
- Apply middleware only to specific routes
- Maintain ultra-fast performance with zero allocation design
- Use proper FastAPI-style route decorators
"""

from catzilla import Catzilla, Request, Response, JSONResponse
from typing import Callable, List
import time
import logging

# Initialize Catzilla with performance optimizations
app = Catzilla(
    use_jemalloc=True,           # Memory optimization
    auto_validation=True,        # Automatic validation
    memory_profiling=True,       # Performance monitoring
    auto_memory_tuning=True      # Adaptive memory management
)

# =====================================================
# MIDDLEWARE FUNCTIONS
# =====================================================

def auth_middleware(request: Request) -> None:
    """Authentication middleware - validates API key"""
    api_key = request.headers.get('X-API-Key')
    if not api_key or api_key != 'secret-key-123':
        raise ValueError("Unauthorized: Invalid or missing API key")

def rate_limit_middleware(request: Request) -> None:
    """Rate limiting middleware - simple demonstration"""
    # In production, you'd use Redis or similar for distributed rate limiting
    user_ip = request.environ.get('REMOTE_ADDR', 'unknown')
    # Simplified rate limiting logic
    print(f"Rate limiting check for IP: {user_ip}")

def logging_middleware(request: Request) -> None:
    """Request logging middleware"""
    timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
    method = request.environ.get('REQUEST_METHOD', 'UNKNOWN')
    path = request.environ.get('PATH_INFO', '/')
    print(f"[{timestamp}] {method} {path}")

def admin_middleware(request: Request) -> None:
    """Admin-only middleware"""
    user_role = request.headers.get('X-User-Role')
    if user_role != 'admin':
        raise ValueError("Forbidden: Admin access required")

# =====================================================
# ROUTES WITH PER-ROUTE MIDDLEWARE
# =====================================================

@app.get("/")
def home(request: Request):
    """Public endpoint - no middleware"""
    return JSONResponse({
        "message": "Welcome to Catzilla Per-Route Middleware Demo!",
        "features": [
            "Zero-allocation per-route middleware",
            "C-accelerated performance",
            "FastAPI-style decorators",
            "Industry-grade security"
        ]
    })

@app.get("/public/info", middleware=[logging_middleware])
def public_info(request: Request):
    """Public endpoint with logging middleware only"""
    return JSONResponse({
        "message": "This is a public endpoint with logging",
        "timestamp": time.time()
    })

@app.get("/api/users", middleware=[auth_middleware, logging_middleware])
def get_users(request: Request):
    """API endpoint with authentication and logging middleware"""
    return JSONResponse({
        "users": [
            {"id": 1, "name": "Alice", "role": "user"},
            {"id": 2, "name": "Bob", "role": "user"},
            {"id": 3, "name": "Charlie", "role": "admin"}
        ]
    })

@app.get("/api/users/{user_id}", middleware=[auth_middleware, rate_limit_middleware, logging_middleware])
def get_user(request: Request):
    """API endpoint with auth, rate limiting, and logging"""
    user_id = request.path_params.get('user_id')

    # Simulate user lookup
    users = {
        "1": {"id": 1, "name": "Alice", "role": "user", "email": "alice@example.com"},
        "2": {"id": 2, "name": "Bob", "role": "user", "email": "bob@example.com"},
        "3": {"id": 3, "name": "Charlie", "role": "admin", "email": "charlie@example.com"}
    }

    user = users.get(user_id)
    if not user:
        return JSONResponse({"error": "User not found"}, status_code=404)

    return JSONResponse({"user": user})

@app.post("/api/users", middleware=[auth_middleware, logging_middleware])
def create_user(request: Request):
    """Create user endpoint with auth and logging"""
    # In a real app, you'd parse JSON body here
    return JSONResponse({
        "message": "User created successfully",
        "user_id": 4,
        "note": "This is a demo - user not actually created"
    })

@app.get("/admin/dashboard", middleware=[auth_middleware, admin_middleware, logging_middleware])
def admin_dashboard(request: Request):
    """Admin-only endpoint with full middleware stack"""
    return JSONResponse({
        "message": "Admin Dashboard",
        "stats": {
            "total_users": 3,
            "active_sessions": 12,
            "system_status": "healthy"
        },
        "admin_tools": [
            "User Management",
            "System Monitoring",
            "Configuration"
        ]
    })

@app.delete("/admin/users/{user_id}", middleware=[auth_middleware, admin_middleware, logging_middleware])
def delete_user(request: Request):
    """Delete user endpoint - admin only"""
    user_id = request.path_params.get('user_id')
    return JSONResponse({
        "message": f"User {user_id} deleted successfully",
        "note": "This is a demo - user not actually deleted"
    })

# =====================================================
# MIDDLEWARE PERFORMANCE DEMO
# =====================================================

@app.get("/performance/no-middleware")
def performance_baseline(request: Request):
    """Baseline performance - no middleware"""
    start_time = time.perf_counter()

    # Simulate some work
    result = {"data": list(range(100))}

    end_time = time.perf_counter()
    processing_time = (end_time - start_time) * 1000  # Convert to milliseconds

    return JSONResponse({
        "result": result,
        "processing_time_ms": round(processing_time, 3),
        "middleware_count": 0
    })

@app.get("/performance/with-middleware", middleware=[logging_middleware, auth_middleware])
def performance_with_middleware(request: Request):
    """Performance test with multiple middleware"""
    start_time = time.perf_counter()

    # Simulate some work
    result = {"data": list(range(100))}

    end_time = time.perf_counter()
    processing_time = (end_time - start_time) * 1000  # Convert to milliseconds

    return JSONResponse({
        "result": result,
        "processing_time_ms": round(processing_time, 3),
        "middleware_count": 2
    })

# =====================================================
# ERROR HANDLING DEMO
# =====================================================

@app.get("/demo/error", middleware=[logging_middleware])
def error_demo(request: Request):
    """Demonstrate error handling with middleware"""
    error_type = request.query_params.get('type', 'none')

    if error_type == 'auth':
        # This will be caught by auth middleware if present
        raise ValueError("Authentication failed")
    elif error_type == 'server':
        # Server error
        raise RuntimeError("Internal server error")

    return JSONResponse({"message": "No error - everything is working!"})

# =====================================================
# MIDDLEWARE INTROSPECTION
# =====================================================

@app.get("/debug/middleware-info")
def middleware_info(request: Request):
    """Get information about middleware usage"""
    # In a real implementation, you'd get this from the router
    routes_with_middleware = [
        {"path": "/public/info", "middleware": ["logging"]},
        {"path": "/api/users", "middleware": ["auth", "logging"]},
        {"path": "/api/users/{user_id}", "middleware": ["auth", "rate_limit", "logging"]},
        {"path": "/admin/dashboard", "middleware": ["auth", "admin", "logging"]},
    ]

    return JSONResponse({
        "middleware_system": "Zero-allocation per-route middleware",
        "performance": "C-accelerated execution",
        "routes_with_middleware": routes_with_middleware,
        "available_middleware": [
            "auth_middleware - API key authentication",
            "rate_limit_middleware - Request rate limiting",
            "logging_middleware - Request logging",
            "admin_middleware - Admin role validation"
        ]
    })

if __name__ == "__main__":
    print("🚀 Starting Catzilla Per-Route Middleware Demo")
    print("=" * 50)
    print("Available endpoints:")
    print("  GET  /                           - Home (no middleware)")
    print("  GET  /public/info                - Public with logging")
    print("  GET  /api/users                  - API with auth + logging")
    print("  GET  /api/users/{user_id}        - API with auth + rate limit + logging")
    print("  POST /api/users                  - Create user (auth + logging)")
    print("  GET  /admin/dashboard            - Admin only (full middleware)")
    print("  GET  /performance/no-middleware  - Performance baseline")
    print("  GET  /performance/with-middleware - Performance with middleware")
    print("  GET  /debug/middleware-info      - Middleware information")
    print()
    print("Testing with curl:")
    print("  # Public endpoint:")
    print("  curl http://localhost:8000/")
    print()
    print("  # Authenticated endpoint (requires X-API-Key: secret-key-123):")
    print("  curl -H 'X-API-Key: secret-key-123' http://localhost:8000/api/users")
    print()
    print("  # Admin endpoint (requires X-API-Key and X-User-Role: admin):")
    print("  curl -H 'X-API-Key: secret-key-123' -H 'X-User-Role: admin' http://localhost:8000/admin/dashboard")
    print("=" * 50)

    app.listen(host="0.0.0.0", port=8000)
