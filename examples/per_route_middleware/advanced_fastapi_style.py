"""
Advanced Per-Route Middleware Example - FastAPI Style

This example demonstrates the FastAPI-style per-route middleware system in Catzilla.
Uses @app.get(), @app.post(), etc. decorators with middleware parameter.

Features:
- Zero-allocation middleware execution
- C-compiled performance
- Per-route middleware with different priorities
- Authentication, logging, rate limiting, and validation middleware
- Memory-optimized execution
"""

from catzilla import Catzilla, Request, Response, JSONResponse
from typing import List, Dict, Optional, Callable
import time
import json

# Initialize Catzilla with zero-allocation optimizations
app = Catzilla(
    use_jemalloc=True,
    auto_memory_tuning=True,
    memory_profiling=True
)

# =====================================================
# MIDDLEWARE FUNCTIONS (ZERO-ALLOCATION DESIGN)
# =====================================================

def auth_middleware(request: Request, response: Response) -> Optional[Response]:
    """Authentication middleware - checks for valid API key"""
    api_key = request.headers.get('Authorization')
    if not api_key or not api_key.startswith('Bearer '):
        return JSONResponse(
            {"error": "Unauthorized", "message": "Missing or invalid API key"},
            status_code=401
        )

    # Store user info in request context for downstream handlers
    request.state.user_id = "user_123"  # Mock user ID
    request.state.authenticated = True
    return None  # Continue to next middleware/handler


def rate_limit_middleware(request: Request, response: Response) -> Optional[Response]:
    """Rate limiting middleware - simple demo implementation"""
    # In production, use Redis or similar for distributed rate limiting
    client_ip = request.headers.get('X-Forwarded-For', '127.0.0.1')

    # Mock rate limiting check
    if hasattr(request.state, 'rate_limited'):
        return JSONResponse(
            {"error": "Rate Limited", "message": "Too many requests"},
            status_code=429
        )

    request.state.rate_check_passed = True
    return None


def logging_middleware(request: Request, response: Response) -> Optional[Response]:
    """Request logging middleware"""
    start_time = time.time()

    # Log request
    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {request.method} {request.path}")

    # Store start time for response logging
    request.state.start_time = start_time
    return None


def validation_middleware(request: Request, response: Response) -> Optional[Response]:
    """Data validation middleware"""
    if request.method == 'POST' and request.path.startswith('/api/'):
        content_type = request.headers.get('Content-Type', '')
        if 'application/json' not in content_type:
            return JSONResponse(
                {"error": "Invalid Content-Type", "message": "Expected application/json"},
                status_code=400
            )

    request.state.validation_passed = True
    return None


def response_timing_middleware(request: Request, response: Response) -> Optional[Response]:
    """Add response timing headers"""
    if hasattr(request.state, 'start_time'):
        duration = time.time() - request.state.start_time
        response.headers['X-Response-Time'] = f"{duration*1000:.2f}ms"
    return None


def cors_middleware(request: Request, response: Response) -> Optional[Response]:
    """CORS handling middleware"""
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
    return None


# =====================================================
# ROUTES WITH FASTAPI-STYLE PER-ROUTE MIDDLEWARE
# =====================================================

@app.get("/", middleware=[cors_middleware, response_timing_middleware])
def home(request):
    """Home endpoint with basic CORS and timing"""
    return JSONResponse({
        "message": "Catzilla Per-Route Middleware Demo",
        "features": [
            "FastAPI-style decorators",
            "Zero-allocation middleware",
            "C-compiled performance",
            "Memory-optimized execution"
        ]
    })


@app.get("/public/status", middleware=[logging_middleware, cors_middleware])
def public_status(request):
    """Public status endpoint with logging and CORS"""
    return JSONResponse({
        "status": "healthy",
        "timestamp": time.time(),
        "memory_optimized": True
    })


@app.get("/api/profile", middleware=[
    auth_middleware,
    rate_limit_middleware,
    logging_middleware,
    response_timing_middleware
])
def get_profile(request):
    """Protected profile endpoint with auth, rate limiting, logging, and timing"""
    return JSONResponse({
        "user_id": request.state.user_id,
        "profile": {
            "name": "John Doe",
            "email": "john@example.com",
            "verified": True
        },
        "authenticated": request.state.authenticated
    })


@app.post("/api/users", middleware=[
    auth_middleware,
    validation_middleware,
    rate_limit_middleware,
    logging_middleware,
    response_timing_middleware
])
def create_user(request):
    """Create user endpoint with full middleware stack"""
    # Parse JSON body
    try:
        data = json.loads(request.body) if request.body else {}
    except json.JSONDecodeError:
        return JSONResponse(
            {"error": "Invalid JSON"},
            status_code=400
        )

    return JSONResponse({
        "message": "User created successfully",
        "user_id": "new_user_456",
        "data": data,
        "validation_passed": request.state.validation_passed,
        "rate_check_passed": request.state.rate_check_passed
    }, status_code=201)


@app.put("/api/users/{user_id}", middleware=[
    auth_middleware,
    validation_middleware,
    logging_middleware
])
def update_user(request):
    """Update user endpoint with auth, validation, and logging"""
    user_id = request.path_params.get('user_id')

    try:
        data = json.loads(request.body) if request.body else {}
    except json.JSONDecodeError:
        return JSONResponse(
            {"error": "Invalid JSON"},
            status_code=400
        )

    return JSONResponse({
        "message": f"User {user_id} updated successfully",
        "user_id": user_id,
        "data": data,
        "updated_by": request.state.user_id
    })


@app.delete("/api/users/{user_id}", middleware=[auth_middleware, logging_middleware])
def delete_user(request):
    """Delete user endpoint with auth and logging"""
    user_id = request.path_params.get('user_id')

    return JSONResponse({
        "message": f"User {user_id} deleted successfully",
        "deleted_by": request.state.user_id
    })


@app.get("/metrics", middleware=[logging_middleware])
def get_metrics(request):
    """Metrics endpoint with logging only"""
    return JSONResponse({
        "requests_processed": 1250,
        "avg_response_time": "45ms",
        "memory_usage": "12MB",
        "middleware_overhead": "< 1%",
        "performance": "C-compiled speed"
    })


# =====================================================
# ADVANCED: CONDITIONAL MIDDLEWARE
# =====================================================

def admin_auth_middleware(request: Request, response: Response) -> Optional[Response]:
    """Admin-only authentication middleware"""
    api_key = request.headers.get('Authorization')
    if not api_key or api_key != 'Bearer admin_secret_key':
        return JSONResponse(
            {"error": "Admin access required"},
            status_code=403
        )

    request.state.admin_user = True
    return None


@app.get("/admin/stats", middleware=[admin_auth_middleware, logging_middleware])
def admin_stats(request):
    """Admin-only endpoint with specialized auth"""
    return JSONResponse({
        "admin_stats": {
            "total_users": 1500,
            "system_health": "excellent",
            "memory_efficiency": "95%",
            "middleware_performance": "zero-allocation"
        },
        "admin_access": request.state.admin_user
    })


# =====================================================
# PERFORMANCE TESTING ENDPOINTS
# =====================================================

@app.get("/benchmark/no-middleware")
def benchmark_no_middleware(request):
    """Benchmark endpoint with no middleware"""
    return JSONResponse({"benchmark": "no_middleware", "timestamp": time.time()})


@app.get("/benchmark/single-middleware", middleware=[logging_middleware])
def benchmark_single_middleware(request):
    """Benchmark endpoint with single middleware"""
    return JSONResponse({"benchmark": "single_middleware", "timestamp": time.time()})


@app.get("/benchmark/multiple-middleware", middleware=[
    logging_middleware,
    cors_middleware,
    response_timing_middleware
])
def benchmark_multiple_middleware(request):
    """Benchmark endpoint with multiple middleware"""
    return JSONResponse({"benchmark": "multiple_middleware", "timestamp": time.time()})


# =====================================================
# MIDDLEWARE CHAINING DEMONSTRATION
# =====================================================

def middleware_order_test_1(request: Request, response: Response) -> Optional[Response]:
    """First middleware in chain - adds to execution order"""
    if not hasattr(request.state, 'middleware_order'):
        request.state.middleware_order = []
    request.state.middleware_order.append("middleware_1")
    return None


def middleware_order_test_2(request: Request, response: Response) -> Optional[Response]:
    """Second middleware in chain - adds to execution order"""
    if not hasattr(request.state, 'middleware_order'):
        request.state.middleware_order = []
    request.state.middleware_order.append("middleware_2")
    return None


def middleware_order_test_3(request: Request, response: Response) -> Optional[Response]:
    """Third middleware in chain - adds to execution order"""
    if not hasattr(request.state, 'middleware_order'):
        request.state.middleware_order = []
    request.state.middleware_order.append("middleware_3")
    return None


@app.get("/test/middleware-order", middleware=[
    middleware_order_test_1,
    middleware_order_test_2,
    middleware_order_test_3,
    logging_middleware
])
def test_middleware_order(request):
    """Test endpoint to verify middleware execution order"""
    return JSONResponse({
        "message": "Middleware order test",
        "execution_order": request.state.middleware_order,
        "expected_order": ["middleware_1", "middleware_2", "middleware_3"]
    })


if __name__ == "__main__":
    print("🚀 Starting Catzilla FastAPI-Style Per-Route Middleware Demo")
    print("📋 Available endpoints:")
    print("   GET  /                      - Home (CORS + timing)")
    print("   GET  /public/status         - Public status (logging + CORS)")
    print("   GET  /api/profile           - Protected profile (auth + rate + logging + timing)")
    print("   POST /api/users             - Create user (full middleware stack)")
    print("   PUT  /api/users/{user_id}   - Update user (auth + validation + logging)")
    print("   DELETE /api/users/{user_id} - Delete user (auth + logging)")
    print("   GET  /metrics               - Metrics (logging only)")
    print("   GET  /admin/stats           - Admin stats (admin auth + logging)")
    print("   GET  /benchmark/*           - Performance benchmarks")
    print("   GET  /test/middleware-order - Middleware execution order test")
    print("\n🔑 Use 'Bearer valid_api_key' for regular auth")
    print("🔑 Use 'Bearer admin_secret_key' for admin endpoints")
    print("\n⚡ FastAPI-Style Middleware features:")
    print("   - @app.get('/path', middleware=[...]) syntax")
    print("   - @app.post('/path', middleware=[...]) syntax")
    print("   - Zero-allocation execution")
    print("   - C-compiled performance")
    print("   - Memory-optimized design")

    app.run(host="0.0.0.0", port=8000)
