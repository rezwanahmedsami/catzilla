#!/usr/bin/env python3
"""
Catzilla Per-Route Middleware Example

This example demonstrates the new zero-allocation, per-route middleware system
in Catzilla. It shows how to:
1. Define custom middleware functions
2. Register middleware for specific routes
3. See middleware execution with different priorities
4. Handle middleware that can skip route execution

The middleware system provides industry-grade performance with C-compiled
execution and zero memory allocation during request processing.
"""

import sys
import os

# Add parent directory to path to import catzilla
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'python'))

from catzilla import Catzilla


def logging_middleware(request, response, next_middleware):
    """
    Simple logging middleware that logs request details.
    This runs before the route handler.
    """
    print(f"[LOG] {request.method} {request.path}")

    # Continue to next middleware/route handler
    return next_middleware()


def auth_middleware(request, response, next_middleware):
    """
    Authentication middleware that checks for an auth header.
    This can skip route execution if auth fails.
    """
    auth_header = request.get_header('Authorization')

    if not auth_header or not auth_header.startswith('Bearer '):
        # Skip route execution and send custom response
        response.status = 401
        response.set_header('Content-Type', 'application/json')
        response.body = '{"error": "Unauthorized", "message": "Missing or invalid Authorization header"}'
        return "SKIP_ROUTE"  # Special return value to skip route execution

    print(f"[AUTH] Authenticated user with token: {auth_header[7:10]}...")

    # Continue to next middleware/route handler
    return next_middleware()


def timing_middleware(request, response, next_middleware):
    """
    Timing middleware that measures route execution time.
    This runs both before and after the route handler.
    """
    import time

    start_time = time.time()
    print(f"[TIMING] Request started at {start_time}")

    # Execute next middleware/route handler
    result = next_middleware()

    end_time = time.time()
    duration_ms = (end_time - start_time) * 1000
    print(f"[TIMING] Request completed in {duration_ms:.2f}ms")

    # Add timing header to response
    response.set_header('X-Response-Time', f"{duration_ms:.2f}ms")

    return result


def cors_middleware(request, response, next_middleware):
    """
    CORS middleware that adds CORS headers.
    This runs after the route handler to ensure headers are set.
    """
    # Continue to next middleware/route handler first
    result = next_middleware()

    # Add CORS headers to response
    response.set_header('Access-Control-Allow-Origin', '*')
    response.set_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
    response.set_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')

    print("[CORS] Added CORS headers to response")

    return result


# Create Catzilla app with per-route middleware enabled
app = Catzilla(enable_per_route_middleware=True)


@app.route('/public', methods=['GET'])
@app.middleware([
    (logging_middleware, 10),    # Priority 10 - runs first
    (timing_middleware, 20),     # Priority 20 - runs second
    (cors_middleware, 30)        # Priority 30 - runs last
])
def public_endpoint(request, response):
    """
    Public endpoint that doesn't require authentication.
    Only uses logging, timing, and CORS middleware.
    """
    response.json({
        "message": "This is a public endpoint",
        "timestamp": "2025-06-18T00:00:00Z",
        "data": {
            "public": True,
            "middleware": ["logging", "timing", "cors"]
        }
    })


@app.route('/protected', methods=['GET'])
@app.middleware([
    (logging_middleware, 10),    # Priority 10 - runs first
    (auth_middleware, 15),       # Priority 15 - runs second (can skip route)
    (timing_middleware, 20),     # Priority 20 - runs third
    (cors_middleware, 30)        # Priority 30 - runs last
])
def protected_endpoint(request, response):
    """
    Protected endpoint that requires authentication.
    Uses all middleware including authentication.
    """
    response.json({
        "message": "This is a protected endpoint",
        "timestamp": "2025-06-18T00:00:00Z",
        "data": {
            "protected": True,
            "middleware": ["logging", "auth", "timing", "cors"]
        }
    })


@app.route('/fast', methods=['GET'])
@app.middleware([
    (logging_middleware, 10)     # Only logging middleware - minimal overhead
])
def fast_endpoint(request, response):
    """
    Fast endpoint with minimal middleware for maximum performance.
    Only uses logging middleware.
    """
    response.json({
        "message": "This is a fast endpoint",
        "timestamp": "2025-06-18T00:00:00Z",
        "data": {
            "fast": True,
            "middleware": ["logging"]
        }
    })


@app.route('/no-middleware', methods=['GET'])
def no_middleware_endpoint(request, response):
    """
    Endpoint with no per-route middleware.
    Demonstrates that middleware is truly per-route.
    """
    response.json({
        "message": "This endpoint has no middleware",
        "timestamp": "2025-06-18T00:00:00Z",
        "data": {
            "middleware": []
        }
    })


if __name__ == '__main__':
    print("🌪️ Catzilla Per-Route Middleware Example")
    print("=" * 50)
    print()
    print("Available endpoints:")
    print("  GET /public      - Public endpoint with logging, timing, CORS")
    print("  GET /protected   - Protected endpoint requiring auth header")
    print("  GET /fast        - Fast endpoint with minimal middleware")
    print("  GET /no-middleware - Endpoint with no middleware")
    print()
    print("To test authentication, include header:")
    print("  Authorization: Bearer your-token-here")
    print()
    print("Starting server on http://localhost:8000...")
    print("=" * 50)

    app.run(host='0.0.0.0', port=8000, debug=True)
