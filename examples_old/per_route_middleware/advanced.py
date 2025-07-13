"""
Advanced Per-Route Middleware Example
Demonstrates complex middleware patterns with dependency injection and validation.
"""

from catzilla import Catzilla, Request, Response, JSONResponse, BaseModel
from typing import Callable, List, Optional, Dict, Any
import time
import json
import hashlib
import hmac

# Advanced Catzilla setup with all features
app = Catzilla(
    use_jemalloc=True,
    auto_validation=True,
    memory_profiling=True,
    auto_memory_tuning=True,
    enable_di=True  # Enable dependency injection
)

# =====================================================
# DATA MODELS FOR VALIDATION
# =====================================================

class User(BaseModel):
    """User model with validation"""
    name: str
    email: str
    role: str = "user"
    active: bool = True

class UserUpdate(BaseModel):
    """User update model"""
    name: Optional[str] = None
    email: Optional[str] = None
    active: Optional[bool] = None

class APIResponse(BaseModel):
    """Standard API response format"""
    success: bool
    data: Any = None
    message: str = ""
    timestamp: float = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = time.time()

# =====================================================
# ADVANCED MIDDLEWARE FUNCTIONS
# =====================================================

def cors_middleware(request: Request) -> None:
    """CORS middleware for browser compatibility"""
    # Add CORS headers to response (in real implementation)
    print("CORS: Adding cross-origin headers")

def jwt_auth_middleware(request: Request) -> None:
    """JWT token authentication middleware"""
    auth_header = request.headers.get('Authorization', '')

    if not auth_header.startswith('Bearer '):
        raise ValueError("Unauthorized: Missing or invalid Bearer token")

    token = auth_header.split(' ')[1]
    # In production, verify JWT signature and expiration
    if token != 'valid-jwt-token':
        raise ValueError("Unauthorized: Invalid JWT token")

    # Store user info in request context (simplified)
    request.user = {"id": 1, "username": "demo_user", "role": "user"}

def api_key_middleware(request: Request) -> None:
    """API key authentication middleware"""
    api_key = request.headers.get('X-API-Key')

    # Check against valid API keys (in production, use a database)
    valid_keys = {
        'sk_test_123': {'name': 'Test App', 'rate_limit': 1000},
        'sk_prod_456': {'name': 'Production App', 'rate_limit': 10000}
    }

    if api_key not in valid_keys:
        raise ValueError("Unauthorized: Invalid API key")

    request.api_key_info = valid_keys[api_key]

def rate_limit_advanced_middleware(request: Request) -> None:
    """Advanced rate limiting with different limits per API key"""
    # Get rate limit from API key info
    rate_limit = getattr(request, 'api_key_info', {}).get('rate_limit', 100)
    client_ip = request.environ.get('REMOTE_ADDR', 'unknown')

    # In production, use Redis with sliding window
    print(f"Rate limit check: {client_ip} (limit: {rate_limit}/hour)")

def request_signature_middleware(request: Request) -> None:
    """Webhook signature verification middleware"""
    signature = request.headers.get('X-Signature')
    if not signature:
        raise ValueError("Unauthorized: Missing request signature")

    # In production, verify HMAC signature
    print(f"Verifying request signature: {signature[:10]}...")

def audit_log_middleware(request: Request) -> None:
    """Comprehensive audit logging middleware"""
    audit_data = {
        'timestamp': time.time(),
        'method': request.environ.get('REQUEST_METHOD'),
        'path': request.environ.get('PATH_INFO'),
        'user_agent': request.headers.get('User-Agent'),
        'ip': request.environ.get('REMOTE_ADDR'),
        'user': getattr(request, 'user', {}).get('username', 'anonymous')
    }

    # In production, send to audit log service
    print(f"AUDIT: {json.dumps(audit_data, indent=2)}")

def cache_middleware(request: Request) -> None:
    """Caching middleware for GET requests"""
    if request.environ.get('REQUEST_METHOD') == 'GET':
        cache_key = f"cache_{request.environ.get('PATH_INFO', '/')}"
        print(f"Cache check for key: {cache_key}")

def admin_only_middleware(request: Request) -> None:
    """Admin role verification"""
    user = getattr(request, 'user', {})
    if user.get('role') != 'admin':
        raise ValueError("Forbidden: Admin access required")

def webhook_middleware(request: Request) -> None:
    """Webhook-specific middleware"""
    content_type = request.headers.get('Content-Type', '')
    if not content_type.startswith('application/json'):
        raise ValueError("Bad Request: Webhook requires JSON content type")

# =====================================================
# PUBLIC ENDPOINTS
# =====================================================

@app.get("/")
def home(request: Request):
    """Public home endpoint"""
    return JSONResponse({
        "service": "Catzilla Advanced Middleware Demo",
        "version": "1.0.0",
        "features": [
            "Per-route middleware",
            "JWT authentication",
            "API key management",
            "Rate limiting",
            "Audit logging",
            "Request signatures",
            "Zero-allocation design"
        ]
    })

@app.get("/public/health", middleware=[cors_middleware])
def health_check(request: Request):
    """Health check with CORS support"""
    return JSONResponse({
        "status": "healthy",
        "timestamp": time.time(),
        "uptime": "1d 2h 30m"  # In production, calculate real uptime
    })

# =====================================================
# API KEY AUTHENTICATED ENDPOINTS
# =====================================================

@app.get("/api/v1/users", middleware=[api_key_middleware, rate_limit_advanced_middleware, audit_log_middleware])
def list_users(request: Request):
    """List users - requires API key"""
    return JSONResponse({
        "users": [
            {"id": 1, "name": "Alice", "email": "alice@example.com", "role": "user"},
            {"id": 2, "name": "Bob", "email": "bob@example.com", "role": "admin"}
        ],
        "api_key_info": request.api_key_info,
        "total": 2
    })

@app.get("/api/v1/users/{user_id}",
         middleware=[api_key_middleware, rate_limit_advanced_middleware, cache_middleware, audit_log_middleware])
def get_user(request: Request):
    """Get user by ID - with caching"""
    user_id = request.path_params.get('user_id')

    # Simulate database lookup
    users = {
        "1": {"id": 1, "name": "Alice", "email": "alice@example.com", "role": "user"},
        "2": {"id": 2, "name": "Bob", "email": "bob@example.com", "role": "admin"}
    }

    user = users.get(user_id)
    if not user:
        return JSONResponse({"error": "User not found"}, status_code=404)

    return JSONResponse({
        "user": user,
        "cached": True,  # In production, indicate if from cache
        "cache_ttl": 300
    })

# =====================================================
# JWT AUTHENTICATED ENDPOINTS
# =====================================================

@app.post("/api/v1/users", middleware=[jwt_auth_middleware, audit_log_middleware])
def create_user(request: Request):
    """Create user - requires JWT"""
    # Auto-validation will handle User model validation
    return JSONResponse({
        "message": "User created successfully",
        "created_by": request.user['username'],
        "user_id": 3
    })

@app.put("/api/v1/users/{user_id}", middleware=[jwt_auth_middleware, audit_log_middleware])
def update_user(request: Request):
    """Update user - requires JWT"""
    user_id = request.path_params.get('user_id')
    return JSONResponse({
        "message": f"User {user_id} updated successfully",
        "updated_by": request.user['username']
    })

# =====================================================
# ADMIN ENDPOINTS
# =====================================================

@app.get("/admin/dashboard",
         middleware=[jwt_auth_middleware, admin_only_middleware, audit_log_middleware])
def admin_dashboard(request: Request):
    """Admin dashboard - requires JWT + admin role"""
    return JSONResponse({
        "dashboard": "Admin Dashboard",
        "admin_user": request.user['username'],
        "stats": {
            "total_users": 2,
            "api_requests_today": 1547,
            "active_sessions": 23
        }
    })

@app.delete("/admin/users/{user_id}",
            middleware=[jwt_auth_middleware, admin_only_middleware, audit_log_middleware])
def delete_user(request: Request):
    """Delete user - admin only"""
    user_id = request.path_params.get('user_id')
    return JSONResponse({
        "message": f"User {user_id} deleted",
        "deleted_by": request.user['username']
    })

# =====================================================
# WEBHOOK ENDPOINTS
# =====================================================

@app.post("/webhooks/payment",
          middleware=[request_signature_middleware, webhook_middleware, audit_log_middleware])
def payment_webhook(request: Request):
    """Payment webhook with signature verification"""
    return JSONResponse({
        "message": "Payment webhook received",
        "processed": True
    })

@app.post("/webhooks/user-event",
          middleware=[api_key_middleware, webhook_middleware, audit_log_middleware])
def user_event_webhook(request: Request):
    """User event webhook with API key auth"""
    return JSONResponse({
        "message": "User event webhook received",
        "processed": True
    })

# =====================================================
# PERFORMANCE TESTING ENDPOINTS
# =====================================================

@app.get("/perf/baseline")
def performance_baseline(request: Request):
    """Performance baseline - no middleware"""
    start = time.perf_counter()

    # Simulate work
    data = {"numbers": list(range(1000))}

    duration = (time.perf_counter() - start) * 1000
    return JSONResponse({
        "data_size": len(data["numbers"]),
        "processing_time_ms": round(duration, 3),
        "middleware_count": 0
    })

@app.get("/perf/light-middleware", middleware=[cors_middleware])
def performance_light(request: Request):
    """Performance with light middleware"""
    start = time.perf_counter()

    data = {"numbers": list(range(1000))}

    duration = (time.perf_counter() - start) * 1000
    return JSONResponse({
        "data_size": len(data["numbers"]),
        "processing_time_ms": round(duration, 3),
        "middleware_count": 1
    })

@app.get("/perf/heavy-middleware",
         middleware=[api_key_middleware, rate_limit_advanced_middleware, cache_middleware, audit_log_middleware])
def performance_heavy(request: Request):
    """Performance with heavy middleware stack"""
    start = time.perf_counter()

    data = {"numbers": list(range(1000))}

    duration = (time.perf_counter() - start) * 1000
    return JSONResponse({
        "data_size": len(data["numbers"]),
        "processing_time_ms": round(duration, 3),
        "middleware_count": 4,
        "api_key_used": request.api_key_info['name']
    })

# =====================================================
# MIDDLEWARE DEBUGGING
# =====================================================

@app.get("/debug/middleware-execution")
def debug_middleware(request: Request):
    """Debug middleware execution order"""
    return JSONResponse({
        "message": "Middleware debugging info",
        "execution_order": [
            "1. CORS middleware",
            "2. Authentication middleware",
            "3. Rate limiting middleware",
            "4. Caching middleware",
            "5. Audit logging middleware",
            "6. Route handler execution"
        ],
        "performance_notes": [
            "Zero-allocation middleware design",
            "C-accelerated execution",
            "Minimal memory footprint",
            "Sub-microsecond middleware overhead"
        ]
    })

if __name__ == "__main__":
    print("🚀 Starting Catzilla Advanced Per-Route Middleware Demo")
    print("=" * 60)
    print("Endpoint Categories:")
    print("  📖 Public:     /")
    print("               /public/health")
    print()
    print("  🔑 API Key:   /api/v1/users")
    print("               /api/v1/users/{id}")
    print()
    print("  🎫 JWT Auth:  /api/v1/users (POST)")
    print("               /api/v1/users/{id} (PUT)")
    print()
    print("  👑 Admin:     /admin/dashboard")
    print("               /admin/users/{id} (DELETE)")
    print()
    print("  🔗 Webhooks:  /webhooks/payment")
    print("               /webhooks/user-event")
    print()
    print("  ⚡ Performance: /perf/baseline")
    print("                 /perf/light-middleware")
    print("                 /perf/heavy-middleware")
    print()
    print("Testing Commands:")
    print("  # API Key endpoint:")
    print("  curl -H 'X-API-Key: sk_test_123' http://localhost:8000/api/v1/users")
    print()
    print("  # JWT endpoint:")
    print("  curl -H 'Authorization: Bearer valid-jwt-token' \\")
    print("       -X POST http://localhost:8000/api/v1/users")
    print()
    print("  # Admin endpoint:")
    print("  curl -H 'Authorization: Bearer valid-jwt-token' \\")
    print("       http://localhost:8000/admin/dashboard")
    print("=" * 60)

    app.run(host="0.0.0.0", port=8000)
