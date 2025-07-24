#!/usr/bin/env python3
"""
Catzilla Middleware Benchmark Server

This server demonstrates Catzilla's middleware performance with various middleware
layers including authentication, CORS, rate limiting, and request logging.

Based on the async_middleware_compatible.py example with benchmark-focused endpoints.
"""

import sys
import os
import json
import time
import asyncio
from typing import Optional

# Add the catzilla package to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', 'python'))

from catzilla import Catzilla, Request, Response, JSONResponse
from catzilla.dependency_injection import service, Depends

# Initialize Catzilla with middleware support
app = Catzilla(
    production=True,
    use_jemalloc=True,
    auto_validation=True,
    show_banner=False,  # Disable for benchmarking
    log_requests=False  # Disable request logging for pure performance
)

print("🌪️ Catzilla Middleware Benchmark Server")

# ============================================================================
# GLOBAL MIDDLEWARE LAYERS (Sync middleware calling async functions)
# ============================================================================

@app.middleware(priority=10, pre_route=True, name="benchmark_request_logger")
def benchmark_request_logger_middleware(request: Request) -> Optional[Response]:
    """High-performance request logging middleware"""
    async def async_log():
        # Simulate async logging operation
        await asyncio.sleep(0.001)  # 1ms async operation

    # Run async function in sync middleware (compatible approach)
    asyncio.run(async_log())

    start_time = time.time()
    if not hasattr(request, 'context'):
        request.context = {}
    request.context['start_time'] = start_time
    request.context['request_id'] = f"req_{int(start_time * 1000000)}"

    return None

@app.middleware(priority=20, pre_route=True, name="benchmark_cors_handler")
def benchmark_cors_middleware(request: Request) -> Optional[Response]:
    """High-performance CORS handling middleware"""
    async def async_cors_validation():
        # Simulate async CORS validation
        await asyncio.sleep(0.0005)  # 0.5ms async operation

    asyncio.run(async_cors_validation())

    if not hasattr(request, 'context'):
        request.context = {}
    request.context['cors_validated'] = True

    return None

@app.middleware(priority=30, pre_route=True, name="benchmark_security_headers")
def benchmark_security_headers_middleware(request: Request) -> Optional[Response]:
    """High-performance security headers middleware"""
    async def async_security_check():
        # Simulate async security validation
        await asyncio.sleep(0.0002)  # 0.2ms async operation

    asyncio.run(async_security_check())

    if not hasattr(request, 'context'):
        request.context = {}
    request.context['security_validated'] = True

    return None

# ============================================================================
# PER-ROUTE MIDDLEWARE (Sync middleware calling async functions)
# ============================================================================

def benchmark_auth_middleware(request: Request) -> Optional[Response]:
    """High-performance authentication middleware"""
    async def async_auth_logic():
        # Check for Authorization header
        auth_header = (
            request.headers.get("Authorization") or
            request.headers.get("authorization") or
            request.get_header("Authorization")
        )

        if not auth_header:
            return JSONResponse({"error": "Missing Authorization header"}, status_code=401)

        if not auth_header.startswith("Bearer "):
            return JSONResponse({"error": "Invalid Authorization format"}, status_code=401)

        token = auth_header[7:]

        # Simulate async token validation
        await asyncio.sleep(0.002)  # 2ms database lookup

        if token == "invalid":
            return JSONResponse({"error": "Invalid token"}, status_code=401)

        # Add user info to request context
        if not hasattr(request, 'context'):
            request.context = {}
        request.context['user'] = {
            "id": "user_123",
            "name": "Benchmark User",
            "token": token,
            "validated_at": time.time()
        }

        return None

    return asyncio.run(async_auth_logic())

def benchmark_rate_limit_middleware(request: Request) -> Optional[Response]:
    """High-performance rate limiting middleware"""
    async def async_rate_limit_logic():
        client_ip = request.headers.get("x-forwarded-for", "127.0.0.1")

        # Simulate async rate limit check
        await asyncio.sleep(0.001)  # 1ms Redis lookup

        if not hasattr(request, 'context'):
            request.context = {}
        request.context['rate_limit'] = {
            'ip': client_ip,
            'remaining': 1000,
            'checked_at': time.time()
        }

        return None

    return asyncio.run(async_rate_limit_logic())

# ============================================================================
# BENCHMARK ENDPOINTS
# ============================================================================

@app.get("/")
def home(request: Request) -> Response:
    """Home endpoint - tests basic middleware overhead"""
    return JSONResponse({
        "message": "Catzilla Middleware Benchmark",
        "framework": "catzilla",
        "middleware_layers": 3,
        "request_id": getattr(request, 'context', {}).get('request_id', 'unknown')
    })

@app.get("/health")
def health_check(request: Request) -> Response:
    """Health check endpoint - minimal middleware overhead"""
    return JSONResponse({
        "status": "healthy",
        "framework": "catzilla",
        "middleware": "enabled"
    })

@app.get("/middleware-light")
def middleware_light_test(request: Request) -> Response:
    """Light middleware test - only global middleware"""
    context = getattr(request, 'context', {})

    return JSONResponse({
        "test": "middleware_light",
        "framework": "catzilla",
        "global_middleware": {
            "request_id": context.get('request_id'),
            "cors_validated": context.get('cors_validated', False),
            "security_validated": context.get('security_validated', False)
        },
        "performance": "optimized"
    })

@app.get("/middleware-heavy", middleware=[benchmark_auth_middleware, benchmark_rate_limit_middleware])
def middleware_heavy_test(request: Request) -> Response:
    """Heavy middleware test - global + per-route middleware"""
    context = getattr(request, 'context', {})

    return JSONResponse({
        "test": "middleware_heavy",
        "framework": "catzilla",
        "global_middleware": {
            "request_id": context.get('request_id'),
            "cors_validated": context.get('cors_validated', False),
            "security_validated": context.get('security_validated', False)
        },
        "per_route_middleware": {
            "auth": context.get('user', {}).get('id'),
            "rate_limit": context.get('rate_limit', {}).get('remaining')
        },
        "total_middleware_layers": 5,
        "performance": "high_load_test"
    })

@app.get("/middleware-auth", middleware=[benchmark_auth_middleware])
def middleware_auth_test(request: Request) -> Response:
    """Authentication middleware test"""
    context = getattr(request, 'context', {})
    user = context.get('user', {})

    return JSONResponse({
        "test": "middleware_auth",
        "framework": "catzilla",
        "authenticated": True,
        "user": {
            "id": user.get('id'),
            "name": user.get('name')
        },
        "auth_performance": "validated"
    })

@app.get("/middleware-stats")
def middleware_stats(request: Request) -> Response:
    """Middleware performance statistics"""
    context = getattr(request, 'context', {})
    start_time = context.get('start_time', time.time())
    processing_time = (time.time() - start_time) * 1000  # Convert to milliseconds

    return JSONResponse({
        "test": "middleware_stats",
        "framework": "catzilla",
        "performance": {
            "processing_time_ms": round(processing_time, 3),
            "middleware_overhead": "minimal",
            "async_operations": "sync_compatible"
        },
        "middleware_summary": {
            "global_layers": 3,
            "per_route_layers": 0,
            "total_async_calls": 3,
            "compatibility": "sync_calling_async"
        }
    })

@app.post("/middleware-post", middleware=[benchmark_auth_middleware])
def middleware_post_test(request: Request) -> Response:
    """POST endpoint with middleware - tests request body processing"""
    try:
        # Parse JSON body
        body = request.json()
    except:
        body = {"error": "Invalid JSON"}

    context = getattr(request, 'context', {})

    return JSONResponse({
        "test": "middleware_post",
        "method": "POST",
        "framework": "catzilla",
        "body_received": body,
        "authenticated": 'user' in context,
        "middleware_performance": "optimized_for_post"
    })

# ============================================================================
# CONCURRENT MIDDLEWARE TEST
# ============================================================================

@app.get("/middleware-concurrent")
async def middleware_concurrent_test(request: Request) -> Response:
    """Async endpoint to test middleware with concurrent operations"""
    # Simulate multiple concurrent operations
    tasks = [
        asyncio.sleep(0.01),  # 10ms operation
        asyncio.sleep(0.005), # 5ms operation
        asyncio.sleep(0.002)  # 2ms operation
    ]

    await asyncio.gather(*tasks)

    context = getattr(request, 'context', {})

    return JSONResponse({
        "test": "middleware_concurrent",
        "framework": "catzilla",
        "async_operations": 3,
        "concurrent_execution": True,
        "middleware_compatibility": "async_route_sync_middleware",
        "request_context": {
            "request_id": context.get('request_id'),
            "validated": context.get('security_validated', False)
        }
    })

# ============================================================================
# SERVER STARTUP
# ============================================================================

def main():
    import argparse

    parser = argparse.ArgumentParser(description='Catzilla Middleware Benchmark Server')
    parser.add_argument('--port', type=int, default=8100, help='Port to run the server on')
    parser.add_argument('--host', default='0.0.0.0', help='Host to bind the server to')

    args = parser.parse_args()

    print(f"🚀 Starting Catzilla Middleware Benchmark Server on {args.host}:{args.port}")
    print("Available endpoints:")
    print("  GET  /                      - Home (basic middleware)")
    print("  GET  /health                - Health check")
    print("  GET  /middleware-light      - Light middleware test")
    print("  GET  /middleware-heavy      - Heavy middleware test (requires auth)")
    print("  GET  /middleware-auth       - Auth middleware test (requires auth)")
    print("  GET  /middleware-stats      - Middleware performance stats")
    print("  POST /middleware-post       - POST with middleware (requires auth)")
    print("  GET  /middleware-concurrent - Async endpoint with middleware")
    print("")
    print("🧪 Test with auth: curl -H 'Authorization: Bearer valid-token' http://localhost:8100/middleware-heavy")

    app.listen(port=args.port, host=args.host)

if __name__ == "__main__":
    main()
