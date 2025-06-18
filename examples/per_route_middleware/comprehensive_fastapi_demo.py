"""
Comprehensive Per-Route Middleware Demo - FastAPI-Style API
===========================================================

This example demonstrates the complete FastAPI-compatible per-route middleware system
in Catzilla, showing all HTTP methods, middleware types, and real-world usage patterns.

Features demonstrated:
- All HTTP method decorators (@app.get, @app.post, @app.put, @app.delete, @app.patch)
- Multiple middleware per route
- Middleware execution order
- Authentication and authorization patterns
- Rate limiting and request validation
- Response modification and timing
- Error handling and short-circuiting
- Performance optimizations with zero-allocation design

Run with: python comprehensive_fastapi_demo.py
Test with:
  curl -H "Authorization: Bearer secret_key" http://localhost:8000/api/users
  curl -H "X-API-Key: admin_key" http://localhost:8000/admin/status
"""

from catzilla import Catzilla, Request, Response, JSONResponse, BaseModel
from typing import List, Dict, Optional, Callable, Any
import time
import json

# Initialize Catzilla with full performance optimizations
app = Catzilla(
    use_jemalloc=True,           # Zero-allocation memory management
    auto_validation=True,        # Automatic request validation
    memory_profiling=True,       # Performance monitoring
    auto_memory_tuning=True      # Adaptive memory optimization
)

# =====================================================
# DATA MODELS FOR VALIDATION
# =====================================================

class User(BaseModel):
    id: Optional[int] = None
    name: str
    email: str
    age: Optional[int] = None
    is_active: bool = True

class Product(BaseModel):
    name: str
    price: float
    description: Optional[str] = None
    category: str

# =====================================================
# COMPREHENSIVE MIDDLEWARE LIBRARY
# =====================================================

def timing_middleware(request: Request, response: Response) -> Optional[Response]:
    """Request timing middleware - adds response time headers"""
    start_time = time.time()
    request.state.start_time = start_time

    # This executes after the route handler
    if hasattr(request.state, 'start_time'):
        duration = time.time() - request.state.start_time
        response.headers['X-Response-Time'] = f"{duration*1000:.2f}ms"
        response.headers['X-Server'] = 'Catzilla-v0.3.0'

    return None


def cors_middleware(request: Request, response: Response) -> Optional[Response]:
    """CORS middleware - adds cross-origin headers"""
    response.headers.update({
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, PATCH, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type, Authorization, X-API-Key',
        'Access-Control-Max-Age': '86400'
    })
    return None


def auth_middleware(request: Request, response: Response) -> Optional[Response]:
    """Authentication middleware - validates Bearer tokens"""
    auth_header = request.headers.get('Authorization')

    if not auth_header or not auth_header.startswith('Bearer '):
        return JSONResponse(
            {"error": "Unauthorized", "message": "Valid Bearer token required"},
            status_code=401
        )

    token = auth_header.split(' ')[1]
    if token not in ['secret_key', 'user_token', 'admin_token']:
        return JSONResponse(
            {"error": "Unauthorized", "message": "Invalid token"},
            status_code=401
        )

    # Store user context
    request.state.user_id = f"user_{hash(token) % 1000}"
    request.state.token = token
    request.state.authenticated = True

    return None


def admin_auth_middleware(request: Request, response: Response) -> Optional[Response]:
    """Admin authentication - requires admin API key"""
    api_key = request.headers.get('X-API-Key')

    if api_key != 'admin_key':
        return JSONResponse(
            {"error": "Forbidden", "message": "Admin access required"},
            status_code=403
        )

    request.state.admin = True
    return None


def rate_limit_middleware(request: Request, response: Response) -> Optional[Response]:
    """Rate limiting middleware - demo implementation"""
    client_ip = request.headers.get('X-Forwarded-For', '127.0.0.1')
    user_agent = request.headers.get('User-Agent', 'Unknown')

    # In production, use Redis for distributed rate limiting
    # This is a simplified demonstration
    if hasattr(request.state, 'rate_limited'):
        return JSONResponse(
            {"error": "Rate Limited", "message": "Too many requests"},
            status_code=429
        )

    # Add rate limiting info to response
    response.headers['X-RateLimit-Limit'] = '100'
    response.headers['X-RateLimit-Remaining'] = '99'

    return None


def json_validator_middleware(request: Request, response: Response) -> Optional[Response]:
    """JSON validation middleware"""
    content_type = request.headers.get('Content-Type', '')

    if request.method in ['POST', 'PUT', 'PATCH'] and 'application/json' in content_type:
        try:
            if hasattr(request, 'body') and request.body:
                json.loads(request.body.decode('utf-8'))
        except (json.JSONDecodeError, UnicodeDecodeError):
            return JSONResponse(
                {"error": "Bad Request", "message": "Invalid JSON in request body"},
                status_code=400
            )

    return None


def logging_middleware(request: Request, response: Response) -> Optional[Response]:
    """Request logging middleware"""
    method = request.method or request.environ.get('REQUEST_METHOD', 'UNKNOWN')
    path = request.path or request.environ.get('PATH_INFO', '/')
    timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
    user_id = getattr(request.state, 'user_id', 'anonymous')

    print(f"[{timestamp}] {method} {path} - User: {user_id}")
    return None


# =====================================================
# FASTAPI-STYLE ROUTES WITH COMPREHENSIVE MIDDLEWARE
# =====================================================

# Basic route with no middleware - ultra-fast public endpoint
@app.get("/")
def home(request):
    """Public home endpoint - no middleware for maximum speed"""
    return JSONResponse({
        "message": "Welcome to Catzilla FastAPI-Style Per-Route Middleware Demo",
        "version": "0.3.0",
        "performance": "C-compiled middleware execution"
    })


# Health check - minimal middleware for monitoring
@app.get("/health", middleware=[timing_middleware])
def health_check(request):
    """Health check with timing information"""
    return JSONResponse({
        "status": "healthy",
        "timestamp": time.time(),
        "server": "Catzilla"
    })


# Public API with CORS and timing
@app.get("/api/info", middleware=[cors_middleware, timing_middleware])
def api_info(request):
    """Public API information with CORS support"""
    return JSONResponse({
        "api": "Catzilla FastAPI-Style Demo",
        "endpoints": ["/api/users", "/api/products", "/admin/status"],
        "features": ["Per-route middleware", "C-compiled performance", "FastAPI compatibility"]
    })


# Protected user endpoints
@app.get("/api/users", middleware=[auth_middleware, rate_limit_middleware, timing_middleware])
def get_users(request):
    """Get users - requires authentication with rate limiting"""
    return JSONResponse({
        "users": [
            {"id": 1, "name": "Alice", "email": "alice@example.com"},
            {"id": 2, "name": "Bob", "email": "bob@example.com"}
        ],
        "authenticated_user": request.state.user_id,
        "count": 2
    })


@app.post("/api/users", middleware=[
    auth_middleware,
    json_validator_middleware,
    rate_limit_middleware,
    logging_middleware
])
def create_user(request):
    """Create user - full validation and logging"""
    try:
        # In a real app, you'd use the User model for validation
        user_data = json.loads(request.body.decode('utf-8')) if request.body else {}

        return JSONResponse({
            "message": "User created successfully",
            "user": user_data,
            "created_by": request.state.user_id
        }, status_code=201)
    except Exception as e:
        return JSONResponse({
            "error": "Creation failed",
            "message": str(e)
        }, status_code=400)


@app.put("/api/users/{user_id}", middleware=[
    auth_middleware,
    json_validator_middleware,
    timing_middleware
])
def update_user(request):
    """Update user - requires authentication and JSON validation"""
    user_id = request.path_params.get('user_id')

    try:
        user_data = json.loads(request.body.decode('utf-8')) if request.body else {}

        return JSONResponse({
            "message": f"User {user_id} updated successfully",
            "user_id": user_id,
            "updated_fields": list(user_data.keys()),
            "updated_by": request.state.user_id
        })
    except Exception as e:
        return JSONResponse({
            "error": "Update failed",
            "message": str(e)
        }, status_code=400)


@app.delete("/api/users/{user_id}", middleware=[auth_middleware, logging_middleware])
def delete_user(request):
    """Delete user - requires authentication with logging"""
    user_id = request.path_params.get('user_id')

    return JSONResponse({
        "message": f"User {user_id} deleted successfully",
        "deleted_by": request.state.user_id
    })


# Product endpoints with different middleware combinations
@app.get("/api/products", middleware=[cors_middleware, rate_limit_middleware])
def get_products(request):
    """Public products API with CORS and rate limiting"""
    return JSONResponse({
        "products": [
            {"id": 1, "name": "Laptop", "price": 999.99, "category": "Electronics"},
            {"id": 2, "name": "Book", "price": 19.99, "category": "Education"}
        ],
        "count": 2
    })


@app.post("/api/products", middleware=[
    auth_middleware,
    admin_auth_middleware,  # Requires admin privileges
    json_validator_middleware,
    logging_middleware
])
def create_product(request):
    """Create product - admin only with full validation"""
    try:
        product_data = json.loads(request.body.decode('utf-8')) if request.body else {}

        return JSONResponse({
            "message": "Product created successfully",
            "product": product_data,
            "created_by_admin": True
        }, status_code=201)
    except Exception as e:
        return JSONResponse({
            "error": "Product creation failed",
            "message": str(e)
        }, status_code=400)


# Admin endpoints with maximum security
@app.get("/admin/status", middleware=[
    admin_auth_middleware,
    timing_middleware,
    logging_middleware
])
def admin_status(request):
    """Admin status - requires admin authentication"""
    return JSONResponse({
        "admin_status": "online",
        "system_health": "excellent",
        "middleware_performance": "C-compiled ultra-fast",
        "memory_usage": "optimized with jemalloc",
        "admin_user": True
    })


@app.patch("/admin/config", middleware=[
    admin_auth_middleware,
    json_validator_middleware,
    logging_middleware
])
def update_config(request):
    """Update system configuration - admin only"""
    try:
        config_data = json.loads(request.body.decode('utf-8')) if request.body else {}

        return JSONResponse({
            "message": "Configuration updated",
            "updated_settings": list(config_data.keys()),
            "admin_action": True
        })
    except Exception as e:
        return JSONResponse({
            "error": "Configuration update failed",
            "message": str(e)
        }, status_code=400)


if __name__ == "__main__":
    print("🌪️ Catzilla FastAPI-Style Per-Route Middleware Demo")
    print("=" * 55)
    print("✅ Zero-allocation C-compiled middleware execution")
    print("✅ FastAPI-compatible decorators (@app.get, @app.post, etc.)")
    print("✅ Per-route middleware with execution order control")
    print("✅ Authentication, rate limiting, CORS, validation")
    print()
    print("Test endpoints:")
    print("  Public:     curl http://localhost:8000/")
    print("  Health:     curl http://localhost:8000/health")
    print("  API Info:   curl http://localhost:8000/api/info")
    print("  Users:      curl -H 'Authorization: Bearer secret_key' http://localhost:8000/api/users")
    print("  Products:   curl http://localhost:8000/api/products")
    print("  Admin:      curl -H 'X-API-Key: admin_key' http://localhost:8000/admin/status")
    print()
    print("Starting server on http://localhost:8000...")

    # Start the server
    app.run(host="0.0.0.0", port=8000, debug=True)
