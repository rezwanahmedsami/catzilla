#!/usr/bin/env python3
"""
🌪️ Catzilla Async Middleware Example (Compatible)

This example demonstrates Catzilla's middleware system with async operations
using sync middleware that call async functions, compatible with current architecture.

Features demonstrated:
- Sync middleware calling async functions with asyncio.run()
- Async per-route middleware functions
- Middleware with async I/O operations
- Async route handlers
- Mixed async/sync compatibility
- Performance timing with async operations
"""

from catzilla import Catzilla, Request, Response, JSONResponse
from typing import Optional
import time
import asyncio

# Initialize Catzilla
app = Catzilla(
    production=False,
    show_banner=True,
    log_requests=True
)

print("🌪️ Catzilla Async Middleware Example (Compatible)")
print("=" * 60)

# ============================================================================
# 1. SYNC GLOBAL MIDDLEWARE CALLING ASYNC FUNCTIONS - Compatible approach
# ============================================================================

@app.middleware(priority=10, pre_route=True, name="async_request_logger")
def async_request_logger_middleware(request: Request) -> Optional[Response]:
    """Sync middleware that calls async logging functions"""
    async def async_log():
        # Simulate async logging to database/external service
        await asyncio.sleep(0.01)  # 10ms async I/O simulation
        print(f"📝 Async Request Logger: {request.method} {request.path}")

    # Run async function in sync middleware
    asyncio.run(async_log())

    start_time = time.time()
    # Store start time in request context
    if not hasattr(request, 'context'):
        request.context = {}
    request.context['start_time'] = start_time
    request.context['request_id'] = f"async_req_{int(start_time * 1000)}"

    return None  # Continue to next middleware

@app.middleware(priority=50, pre_route=True, name="async_cors_handler")
def async_cors_middleware(request: Request) -> Optional[Response]:
    """Sync middleware with async CORS validation"""
    async def async_cors_validation():
        # Simulate async external CORS validation
        await asyncio.sleep(0.005)  # 5ms async validation
        print(f"🌍 Async CORS: Processing {request.method} request")

    # Run async validation
    asyncio.run(async_cors_validation())

    # Add CORS info to request context
    if not hasattr(request, 'context'):
        request.context = {}
    request.context['cors_enabled'] = True
    request.context['cors_validation_time'] = '5ms'

    return None

@app.middleware(priority=100, pre_route=True, name="async_security_headers")
def async_security_headers_middleware(request: Request) -> Optional[Response]:
    """Sync middleware with async threat detection"""
    async def async_threat_detection():
        # Simulate async threat detection API call
        await asyncio.sleep(0.02)  # 20ms threat detection
        print("🔒 Async Security: Threat scan completed")

    # Run async threat detection
    asyncio.run(async_threat_detection())

    # Add security info to request context
    if not hasattr(request, 'context'):
        request.context = {}
    request.context['security'] = {
        'https_only': False,
        'csrf_token': f"async_csrf_{int(time.time() * 1000)}",
        'request_origin': request.headers.get('origin', 'unknown'),
        'threat_scan_time': '20ms',
        'threat_level': 'low'
    }

    return None

# ============================================================================
# 2. SYNC PER-ROUTE MIDDLEWARE CALLING ASYNC FUNCTIONS - Compatible approach
# ============================================================================

def async_auth_middleware(request: Request) -> Optional[Response]:
    """Sync middleware calling async authentication functions"""
    async def async_auth_logic():
        print("🔐 Async Auth Middleware: Starting authentication")

        # Check for Authorization header
        auth_header = (
            request.headers.get("Authorization") or
            request.headers.get("authorization") or
            request.get_header("Authorization")
        )

        if not auth_header:
            print("❌ Async Auth: No authorization header")
            return JSONResponse({
                "error": "Authentication required",
                "message": "Please provide Authorization header",
                "example": "Authorization: Bearer your-token",
                "middleware_type": "sync_calling_async"
            }, status_code=401)

        if not auth_header.startswith("Bearer "):
            print("❌ Async Auth: Invalid format")
            return JSONResponse({
                "error": "Invalid authorization format",
                "message": "Authorization header must start with 'Bearer '",
                "middleware_type": "sync_calling_async"
            }, status_code=401)

        token = auth_header[7:]  # Remove "Bearer "

        # Simulate async database user lookup
        print("🔍 Async Auth: Looking up user in database...")
        await asyncio.sleep(0.05)  # 50ms database query

        if token == "invalid":
            print("❌ Async Auth: Invalid token")
            return JSONResponse({
                "error": "Invalid token",
                "message": "The provided token is invalid",
                "middleware_type": "sync_calling_async"
            }, status_code=401)

        # Simulate async user data enrichment
        await asyncio.sleep(0.02)  # 20ms enrichment

        # Add user info to request context
        if not hasattr(request, 'context'):
            request.context = {}
        request.context['user'] = {
            "id": "async_user123",
            "name": "Async John Doe",
            "token": token,
            "authenticated_at": time.time(),
            "auth_method": "sync_calling_async_bearer",
            "db_lookup_time": "50ms",
            "enrichment_time": "20ms"
        }

        print("✅ Async Auth: User authenticated successfully")
        return None

    # Run async logic and return result
    return asyncio.run(async_auth_logic())

def async_rate_limit_middleware(request: Request) -> Optional[Response]:
    """Sync middleware calling async rate limiting functions"""
    async def async_rate_limit_logic():
        print("⏱️ Async Rate Limit: Checking limits")

        client_ip = request.headers.get("x-forwarded-for", "127.0.0.1")

        # Simulate async Redis lookup
        print("🔍 Async Rate Limit: Checking Redis...")
        await asyncio.sleep(0.03)  # 30ms Redis lookup
        await asyncio.sleep(0.01)  # 10ms calculation

        print(f"⏱️ Async Rate Limit: IP {client_ip} - OK")

        if not hasattr(request, 'context'):
            request.context = {}
        request.context['rate_limit'] = {
            'ip': client_ip,
            'remaining': 100,
            'reset_time': time.time() + 3600,
            'redis_lookup_time': '30ms',
            'calculation_time': '10ms',
            'method': 'sync_calling_async_redis'
        }

        return None

    # Run async logic and return result
    return asyncio.run(async_rate_limit_logic())

def async_admin_middleware(request: Request) -> Optional[Response]:
    """Sync middleware calling async admin verification functions"""
    async def async_admin_logic():
        print("👑 Async Admin: Checking privileges")

        user = getattr(request, 'context', {}).get('user')
        if not user:
            return JSONResponse({
                "error": "Authentication required",
                "message": "Admin access requires authentication",
                "middleware_type": "sync_calling_async"
            }, status_code=401)

        # Simulate async role verification
        print("🔍 Async Admin: Verifying role in database...")
        await asyncio.sleep(0.04)  # 40ms role verification

        if user.get('token') != 'admin-token':
            return JSONResponse({
                "error": "Admin access required",
                "message": "This endpoint requires admin privileges",
                "middleware_type": "sync_calling_async"
            }, status_code=403)

        user['admin_verified'] = True
        user['admin_verification_time'] = '40ms'
        user['auth_method'] = 'sync_calling_async_admin'

        print("✅ Async Admin: Access granted")
        return None

    # Run async logic and return result
    return asyncio.run(async_admin_logic())

# ============================================================================
# 3. ASYNC ROUTE HANDLERS
# ============================================================================

@app.get("/")
async def async_home(request: Request) -> Response:
    """Async home endpoint"""
    # Simulate async content generation
    await asyncio.sleep(0.02)  # 20ms content generation

    return JSONResponse({
        "message": "🌪️ Async Catzilla Middleware Example",
        "info": "Sync middleware calling async functions + async handlers",
        "middleware_chain": [
            "1. Sync → Async Request Logger (~10ms)",
            "2. Sync → Async CORS Handler (~5ms)",
            "3. Sync → Async Security Headers (~20ms)"
        ],
        "request_id": getattr(request, 'context', {}).get('request_id'),
        "security": getattr(request, 'context', {}).get('security', {}),
        "handler_type": "async",
        "content_generation_time": "20ms",
        "architecture": "sync_middleware_calling_async + async_handlers"
    })

@app.get("/public")
async def async_public_endpoint(request: Request) -> Response:
    """Async public endpoint with concurrent data fetching"""
    # Simulate concurrent async operations
    data_tasks = [
        asyncio.sleep(0.03),  # Database query
        asyncio.sleep(0.02),  # Cache lookup
        asyncio.sleep(0.01)   # Config fetch
    ]

    await asyncio.gather(*data_tasks)

    return JSONResponse({
        "message": "Async public endpoint with concurrent data fetching",
        "request_id": getattr(request, 'context', {}).get('request_id'),
        "handler_type": "async",
        "data_sources": [
            {"name": "database", "time": "30ms"},
            {"name": "cache", "time": "20ms"},
            {"name": "config", "time": "10ms"}
        ],
        "total_fetch_time": "~30ms (concurrent)",
        "sequential_would_be": "60ms"
    })

@app.get("/protected", middleware=[async_auth_middleware])
async def async_protected_endpoint(request: Request) -> Response:
    """Async protected endpoint"""
    user = getattr(request, 'context', {}).get('user', {})

    # Simulate async protected data fetching
    await asyncio.sleep(0.04)  # 40ms protected data fetch

    return JSONResponse({
        "message": "🔐 Async protected content accessed",
        "user": user,
        "access_time": time.time(),
        "handler_type": "async",
        "protected_data_fetch_time": "40ms",
        "middleware_chain": [
            "1. Global: Sync → Async Request Logger (~10ms)",
            "2. Global: Sync → Async CORS Handler (~5ms)",
            "3. Global: Sync → Async Security Headers (~20ms)",
            "4. Per-route: Async Auth Middleware (~70ms)"
        ]
    })

@app.get("/api/data", middleware=[async_auth_middleware, async_rate_limit_middleware])
async def async_api_data(request: Request) -> Response:
    """Async API endpoint with multiple middleware"""
    user = getattr(request, 'context', {}).get('user', {})
    rate_limit = getattr(request, 'context', {}).get('rate_limit', {})

    # Simulate concurrent API calls
    api_tasks = [
        asyncio.sleep(0.08),  # External API 1
        asyncio.sleep(0.06),  # External API 2
        asyncio.sleep(0.04)   # Data processing
    ]

    await asyncio.gather(*api_tasks)

    return JSONResponse({
        "message": "Async API data retrieved",
        "data": {
            "items": ["async_item1", "async_item2", "async_item3"],
            "total": 3,
            "generated_at": time.time(),
            "generation_method": "async_concurrent"
        },
        "user": user,
        "rate_limit": rate_limit,
        "handler_type": "async",
        "api_calls": [
            {"name": "external_api_1", "time": "80ms"},
            {"name": "external_api_2", "time": "60ms"},
            {"name": "data_processing", "time": "40ms"}
        ],
        "total_api_time": "~80ms (concurrent)"
    })

@app.post("/admin/users", middleware=[async_auth_middleware, async_admin_middleware])
async def async_create_user(request: Request) -> Response:
    """Async admin endpoint"""
    user = getattr(request, 'context', {}).get('user', {})

    # Simulate async database transaction
    print("💾 Async Create User: Starting transaction...")
    await asyncio.sleep(0.1)  # 100ms transaction

    # Concurrent validation tasks
    validation_tasks = [
        asyncio.sleep(0.03),  # Email validation
        asyncio.sleep(0.02),  # Password hashing
        asyncio.sleep(0.04)   # User enrichment
    ]

    await asyncio.gather(*validation_tasks)

    return JSONResponse({
        "message": "👑 Async admin endpoint accessed",
        "action": "async_create_user",
        "admin_user": user,
        "created_at": time.time(),
        "handler_type": "async",
        "operations": [
            {"name": "database_transaction", "time": "100ms"},
            {"name": "email_validation", "time": "30ms"},
            {"name": "password_hashing", "time": "20ms"},
            {"name": "user_enrichment", "time": "40ms"}
        ],
        "total_operation_time": "~140ms (100ms + 40ms concurrent)"
    }, status_code=201)

@app.get("/performance-demo")
async def async_performance_demo(request: Request) -> Response:
    """Async performance demonstration"""
    start_time = time.time()

    # Multiple concurrent operations
    operations = [
        asyncio.sleep(0.1),   # Database query
        asyncio.sleep(0.08),  # External API
        asyncio.sleep(0.06),  # Cache lookup
        asyncio.sleep(0.04),  # File I/O
        asyncio.sleep(0.02)   # Config fetch
    ]

    await asyncio.gather(*operations)

    total_time = (time.time() - start_time) * 1000

    return JSONResponse({
        "message": "Async performance demonstration",
        "operations": [
            {"name": "database_query", "time": "100ms"},
            {"name": "external_api", "time": "80ms"},
            {"name": "cache_lookup", "time": "60ms"},
            {"name": "file_io", "time": "40ms"},
            {"name": "config_fetch", "time": "20ms"}
        ],
        "sequential_time_would_be": "300ms",
        "actual_concurrent_time": f"{total_time:.1f}ms",
        "performance_gain": f"{((300 - total_time) / 300 * 100):.1f}%",
        "handler_type": "async"
    })

@app.get("/middleware/stats")
async def async_middleware_stats(request: Request) -> Response:
    """Async middleware stats"""
    # Simulate async stats collection
    await asyncio.sleep(0.025)  # 25ms collection

    return JSONResponse({
        "message": "Async middleware performance statistics",
        "stats": {
            "global_middleware_count": 3,
            "async_per_route_middleware": 3,
            "architecture": "sync_global_calling_async + async_per_route"
        },
        "request_id": getattr(request, 'context', {}).get('request_id'),
        "collection_time": "25ms",
        "handler_type": "async"
    })

# ============================================================================
# APPLICATION STARTUP
# ============================================================================

if __name__ == "__main__":
    print("\n🎯 Starting Compatible Async Middleware Example...")
    print("\nArchitecture:")
    print("  • Global Middleware: Sync functions calling async operations")
    print("  • Per-route Middleware: Sync functions calling async operations")
    print("  • Route Handlers: Async functions")
    print("  • Fully compatible with current Catzilla middleware system")
    print("  • All middleware use asyncio.run() to call async functions")

    print("\nAvailable endpoints:")
    print("  GET  /                   - Async home (global middleware)")
    print("  GET  /public             - Async public with concurrent data")
    print("  GET  /protected          - Async protected (requires auth)")
    print("  GET  /api/data           - Async API (auth + rate limit)")
    print("  POST /admin/users        - Async admin (auth + admin)")
    print("  GET  /performance-demo   - Async concurrent demo")
    print("  GET  /middleware/stats   - Async middleware stats")

    print("\n🧪 Test commands:")
    print("  # Home with global async middleware")
    print("  curl http://localhost:8000/")
    print()
    print("  # Public endpoint with concurrent operations")
    print("  curl http://localhost:8000/public")
    print()
    print("  # Protected endpoint (will fail)")
    print("  curl http://localhost:8000/protected")
    print()
    print("  # Protected with auth")
    print("  curl -H 'Authorization: Bearer my-token' http://localhost:8000/protected")
    print()
    print("  # API with multiple async middleware")
    print("  curl -H 'Authorization: Bearer my-token' http://localhost:8000/api/data")
    print()
    print("  # Admin endpoint")
    print("  curl -H 'Authorization: Bearer admin-token' -X POST http://localhost:8000/admin/users")
    print()
    print("  # Performance demo")
    print("  curl http://localhost:8000/performance-demo")

    print(f"\n🚀 Starting on http://localhost:8000")
    print("⚡ Demonstrating async operations in Catzilla middleware!")

    app.listen(8000)
