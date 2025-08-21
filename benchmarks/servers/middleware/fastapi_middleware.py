#!/usr/bin/env python3
"""
FastAPI Middleware Benchmark Server

This server demonstrates FastAPI's middleware performance for comparison
with Catzilla's middleware system.
"""

import sys
import os
import json
import time
import asyncio
from typing import Optional


from fastapi import FastAPI, Request, Response, HTTPException, Depends
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi.middleware.cors import CORSMiddleware

# Initialize FastAPI
app = FastAPI(
    title="FastAPI Middleware Benchmark",
    docs_url=None,  # Disable for benchmarking
    redoc_url=None  # Disable for benchmarking
)

print("🚀 FastAPI Middleware Benchmark Server")

# ============================================================================
# MIDDLEWARE CLASSES
# ============================================================================

class BenchmarkRequestLoggerMiddleware(BaseHTTPMiddleware):
    """FastAPI request logging middleware"""

    async def dispatch(self, request: Request, call_next):
        # Simulate async logging operation
        # Removed artificial delay for benchmarking  # 1ms async operation

        start_time = time.time()
        request.state.start_time = start_time
        request.state.request_id = f"req_{int(start_time * 1000000)}"

        response = await call_next(request)
        return response

class BenchmarkSecurityMiddleware(BaseHTTPMiddleware):
    """FastAPI security headers middleware"""

    async def dispatch(self, request: Request, call_next):
        # Simulate async security validation
        # Removed artificial delay for benchmarking  # 0.2ms async operation

        request.state.security_validated = True

        response = await call_next(request)
        return response

class BenchmarkRateLimitMiddleware(BaseHTTPMiddleware):
    """FastAPI rate limiting middleware"""

    async def dispatch(self, request: Request, call_next):
        client_ip = request.client.host if request.client else "127.0.0.1"

        # Simulate async rate limit check
        # Removed artificial delay for benchmarking  # 1ms Redis lookup

        request.state.rate_limit = {
            'ip': client_ip,
            'remaining': 1000,
            'checked_at': time.time()
        }

        response = await call_next(request)
        return response

# ============================================================================
# ADD MIDDLEWARE TO APP
# ============================================================================

# Add CORS middleware (built-in FastAPI)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add custom middleware layers
app.add_middleware(BenchmarkRequestLoggerMiddleware)
app.add_middleware(BenchmarkSecurityMiddleware)

# ============================================================================
# DEPENDENCY FUNCTIONS
# ============================================================================

async def get_authenticated_user(request: Request):
    """FastAPI dependency for authentication"""
    auth_header = request.headers.get("authorization")

    if not auth_header:
        raise HTTPException(status_code=401, detail="Missing Authorization header")

    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid Authorization format")

    token = auth_header[7:]

    # Simulate async token validation
    # Removed artificial delay for benchmarking  # 2ms database lookup

    if token == "invalid":
        raise HTTPException(status_code=401, detail="Invalid token")

    return {
        "id": "user_123",
        "name": "Benchmark User",
        "token": token,
        "validated_at": time.time()
    }

async def rate_limit_check(request: Request):
    """FastAPI dependency for rate limiting"""
    # This would normally check Redis or database
    # Removed artificial delay for benchmarking  # 1ms rate limit check

    return {
        "remaining": 1000,
        "checked_at": time.time()
    }

# ============================================================================
# BENCHMARK ENDPOINTS
# ============================================================================

@app.get("/")
async def home(request: Request):
    """Home endpoint - tests basic middleware overhead"""
    return {
        "message": "FastAPI Middleware Benchmark",
        "framework": "fastapi",
        "middleware_layers": 4,  # CORS + 3 custom
        "request_id": getattr(request.state, 'request_id', 'unknown')
    }

@app.get("/health")
async def health_check():
    """Health check endpoint - minimal processing"""
    return {
        "status": "healthy",
        "framework": "fastapi",
        "middleware": "enabled"
    }

@app.get("/middleware-light")
async def middleware_light_test(request: Request):
    """Light middleware test - only global middleware"""
    return {
        "test": "middleware_light",
        "framework": "fastapi",
        "global_middleware": {
            "request_id": getattr(request.state, 'request_id', None),
            "cors_enabled": True,
            "security_validated": getattr(request.state, 'security_validated', False)
        },
        "performance": "optimized"
    }

@app.get("/middleware-heavy")
async def middleware_heavy_test(
    request: Request,
    user = Depends(get_authenticated_user),
    rate_limit = Depends(rate_limit_check)
):
    """Heavy middleware test - global + dependency middleware"""
    return {
        "test": "middleware_heavy",
        "framework": "fastapi",
        "global_middleware": {
            "request_id": getattr(request.state, 'request_id', None),
            "cors_enabled": True,
            "security_validated": getattr(request.state, 'security_validated', False)
        },
        "dependency_middleware": {
            "auth": user.get('id'),
            "rate_limit": rate_limit.get('remaining')
        },
        "total_middleware_layers": 6,  # 4 global + 2 dependencies
        "performance": "high_load_test"
    }

@app.get("/middleware-auth")
async def middleware_auth_test(user = Depends(get_authenticated_user)):
    """Authentication middleware test"""
    return {
        "test": "middleware_auth",
        "framework": "fastapi",
        "authenticated": True,
        "user": {
            "id": user.get('id'),
            "name": user.get('name')
        },
        "auth_performance": "validated"
    }

@app.get("/middleware-stats")
async def middleware_stats(request: Request):
    """Middleware performance statistics"""
    start_time = getattr(request.state, 'start_time', time.time())
    processing_time = (time.time() - start_time) * 1000  # Convert to milliseconds

    return {
        "test": "middleware_stats",
        "framework": "fastapi",
        "performance": {
            "processing_time_ms": round(processing_time, 3),
            "middleware_overhead": "async_native",
            "async_operations": "native_async"
        },
        "middleware_summary": {
            "global_layers": 4,
            "dependency_layers": "variable",
            "total_async_calls": "all_async",
            "compatibility": "async_native"
        }
    }

@app.post("/middleware-post")
async def middleware_post_test(
    request: Request,
    user = Depends(get_authenticated_user)
):
    """POST endpoint with middleware - tests request body processing"""
    try:
        body = await request.json()
    except:
        body = {"error": "Invalid JSON"}

    return {
        "test": "middleware_post",
        "method": "POST",
        "framework": "fastapi",
        "body_received": body,
        "authenticated": user.get('id') is not None,
        "middleware_performance": "async_optimized"
    }

@app.get("/middleware-concurrent")
async def middleware_concurrent_test(request: Request):
    """Async endpoint to test middleware with concurrent operations"""
    # Fast concurrent operations without artificial delays
    tasks = [
        # Removed artificial delays for benchmarking
    ]

    # No need to wait for empty tasks
    # await asyncio.gather(*tasks)

    return {
        "test": "middleware_concurrent",
        "framework": "fastapi",
        "async_operations": 3,
        "concurrent_execution": True,
        "middleware_compatibility": "native_async",
        "request_context": {
            "request_id": getattr(request.state, 'request_id', None),
            "validated": getattr(request.state, 'security_validated', False)
        }
    }

# ============================================================================
# RATE LIMITED MIDDLEWARE ENDPOINT
# ============================================================================

# Apply rate limiting middleware to specific endpoints
app.add_middleware(BenchmarkRateLimitMiddleware)

# ============================================================================
# SERVER STARTUP
# ============================================================================

def main():
    import argparse

    parser = argparse.ArgumentParser(description='FastAPI Middleware Benchmark Server')
    parser.add_argument('--port', type=int, default=8101, help='Port to run the server on')
    parser.add_argument('--host', default='0.0.0.0', help='Host to bind the server to')

    args = parser.parse_args()

    print(f"🚀 Starting FastAPI Middleware Benchmark Server on {args.host}:{args.port}")
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
    print("🧪 Test with auth: curl -H 'Authorization: Bearer valid-token' http://localhost:8101/middleware-heavy")

    try:
        import uvicorn
        uvicorn.run(
            app,  # Use the app instance directly instead of string path
            host=args.host,
            port=args.port,
            log_level="error",  # Minimize logging for benchmarking
            access_log=False    # Disable access logs for pure performance
        )
    except ImportError:
        print("❌ uvicorn not installed. Install with: pip install uvicorn")
        sys.exit(1)

if __name__ == "__main__":
    main()

# Create app instance for ASGI servers like uvicorn (exposed at module level)
# This is already created above, but we ensure it's available for external ASGI servers
