#!/usr/bin/env python3
"""
Catzilla Advanced Per-Route Middleware Example

This example demonstrates advanced per-route middleware patterns:
1. Middleware with state and context sharing
2. Error handling middleware
3. Conditional middleware execution
4. Performance monitoring middleware
5. Request transformation middleware

This showcases the full power of the zero-allocation middleware system.
"""

import sys
import os
import json
import time
from functools import wraps

# Add parent directory to path to import catzilla
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'python'))

from catzilla import Catzilla


# ============================================================================
# ADVANCED MIDDLEWARE IMPLEMENTATIONS
# ============================================================================

class RequestContext:
    """Shared context for middleware to store data"""
    def __init__(self):
        self.user_id = None
        self.session_id = None
        self.request_id = None
        self.start_time = None
        self.metadata = {}


def request_id_middleware(request, response, next_middleware):
    """
    Generates unique request ID and stores it in context.
    Priority: 5 (runs very early)
    """
    import uuid

    request_id = str(uuid.uuid4())

    # Store in request context
    if not hasattr(request, 'context'):
        request.context = RequestContext()

    request.context.request_id = request_id
    request.context.start_time = time.time()

    # Add to response headers
    response.set_header('X-Request-ID', request_id)

    print(f"[REQUEST-ID] Generated ID: {request_id}")

    return next_middleware()


def rate_limiting_middleware(request, response, next_middleware):
    """
    Simple rate limiting middleware.
    Priority: 8 (runs early, before auth)
    """
    client_ip = request.get_header('X-Forwarded-For') or request.remote_addr or 'unknown'

    # Simple in-memory rate limiting (for demo purposes)
    if not hasattr(rate_limiting_middleware, 'requests'):
        rate_limiting_middleware.requests = {}

    now = time.time()
    minute_window = int(now // 60)
    key = f"{client_ip}:{minute_window}"

    # Clean old entries
    rate_limiting_middleware.requests = {
        k: v for k, v in rate_limiting_middleware.requests.items()
        if int(k.split(':')[1]) >= minute_window - 1
    }

    current_count = rate_limiting_middleware.requests.get(key, 0)

    if current_count >= 100:  # 100 requests per minute limit
        response.status = 429
        response.set_header('Content-Type', 'application/json')
        response.set_header('Retry-After', '60')
        response.body = json.dumps({
            "error": "Rate limit exceeded",
            "message": "Too many requests. Limit: 100 per minute",
            "retry_after": 60
        })
        return "SKIP_ROUTE"

    rate_limiting_middleware.requests[key] = current_count + 1

    print(f"[RATE-LIMIT] {client_ip}: {current_count + 1}/100 requests this minute")

    return next_middleware()


def jwt_auth_middleware(request, response, next_middleware):
    """
    JWT authentication middleware with user context.
    Priority: 10 (runs after rate limiting)
    """
    auth_header = request.get_header('Authorization')

    if not auth_header or not auth_header.startswith('Bearer '):
        response.status = 401
        response.set_header('Content-Type', 'application/json')
        response.body = json.dumps({
            "error": "Unauthorized",
            "message": "JWT token required",
            "request_id": getattr(request.context, 'request_id', None)
        })
        return "SKIP_ROUTE"

    token = auth_header[7:]

    # Mock JWT validation (in real app, use proper JWT library)
    try:
        # Simple token format: user_id.session_id.timestamp
        parts = token.split('.')
        if len(parts) != 3:
            raise ValueError("Invalid token format")

        user_id, session_id, timestamp = parts

        # Check if token is expired (demo: 1 hour expiry)
        token_time = float(timestamp)
        if time.time() - token_time > 3600:
            raise ValueError("Token expired")

        # Store user info in context
        request.context.user_id = user_id
        request.context.session_id = session_id

        print(f"[JWT-AUTH] Authenticated user {user_id} (session: {session_id})")

    except (ValueError, IndexError) as e:
        response.status = 401
        response.set_header('Content-Type', 'application/json')
        response.body = json.dumps({
            "error": "Unauthorized",
            "message": f"Invalid JWT token: {str(e)}",
            "request_id": getattr(request.context, 'request_id', None)
        })
        return "SKIP_ROUTE"

    return next_middleware()


def request_validation_middleware(request, response, next_middleware):
    """
    Request validation middleware.
    Priority: 15 (runs after auth)
    """
    # Validate request size
    if request.body_length > 1024 * 1024:  # 1MB limit
        response.status = 413
        response.set_header('Content-Type', 'application/json')
        response.body = json.dumps({
            "error": "Request too large",
            "message": "Request body cannot exceed 1MB",
            "max_size": "1MB",
            "request_id": getattr(request.context, 'request_id', None)
        })
        return "SKIP_ROUTE"

    # Validate content type for POST/PUT requests
    if request.method in ['POST', 'PUT']:
        content_type = request.get_header('Content-Type')
        if not content_type or not content_type.startswith('application/json'):
            response.status = 400
            response.set_header('Content-Type', 'application/json')
            response.body = json.dumps({
                "error": "Invalid content type",
                "message": "Content-Type must be application/json",
                "request_id": getattr(request.context, 'request_id', None)
            })
            return "SKIP_ROUTE"

    print(f"[VALIDATION] Request validation passed")

    return next_middleware()


def metrics_middleware(request, response, next_middleware):
    """
    Performance metrics collection middleware.
    Priority: 90 (runs late, after main processing)
    """
    # Execute next middleware/route
    result = next_middleware()

    # Calculate metrics
    if hasattr(request, 'context') and request.context.start_time:
        duration = time.time() - request.context.start_time
        duration_ms = duration * 1000

        # Add performance headers
        response.set_header('X-Response-Time', f"{duration_ms:.2f}ms")
        response.set_header('X-Processing-Time', f"{duration:.6f}s")

        print(f"[METRICS] Request processed in {duration_ms:.2f}ms")

        # Store metrics (in real app, send to monitoring system)
        if not hasattr(metrics_middleware, 'stats'):
            metrics_middleware.stats = []

        metrics_middleware.stats.append({
            'request_id': getattr(request.context, 'request_id', None),
            'method': request.method,
            'path': request.path,
            'status': response.status,
            'duration_ms': duration_ms,
            'timestamp': time.time()
        })

        # Keep only last 100 requests
        if len(metrics_middleware.stats) > 100:
            metrics_middleware.stats = metrics_middleware.stats[-100:]

    return result


def error_handling_middleware(request, response, next_middleware):
    """
    Global error handling middleware.
    Priority: 95 (runs very late)
    """
    try:
        return next_middleware()
    except Exception as e:
        print(f"[ERROR] Unhandled exception: {str(e)}")

        response.status = 500
        response.set_header('Content-Type', 'application/json')
        response.body = json.dumps({
            "error": "Internal server error",
            "message": "An unexpected error occurred",
            "request_id": getattr(request.context, 'request_id', None) if hasattr(request, 'context') else None
        })

        return "STOP"  # Stop further middleware execution


# ============================================================================
# APPLICATION SETUP
# ============================================================================

app = Catzilla(enable_per_route_middleware=True)


@app.route('/api/public', methods=['GET'])
@app.middleware([
    (request_id_middleware, 5),
    (rate_limiting_middleware, 8),
    (metrics_middleware, 90),
    (error_handling_middleware, 95)
])
def public_api(request, response):
    """Public API endpoint with basic middleware"""
    response.json({
        "message": "Public API endpoint",
        "request_id": request.context.request_id,
        "timestamp": time.time(),
        "middleware": ["request-id", "rate-limiting", "metrics", "error-handling"]
    })


@app.route('/api/protected', methods=['GET', 'POST'])
@app.middleware([
    (request_id_middleware, 5),
    (rate_limiting_middleware, 8),
    (jwt_auth_middleware, 10),
    (request_validation_middleware, 15),
    (metrics_middleware, 90),
    (error_handling_middleware, 95)
])
def protected_api(request, response):
    """Protected API endpoint with full middleware stack"""
    response.json({
        "message": "Protected API endpoint",
        "request_id": request.context.request_id,
        "user_id": request.context.user_id,
        "session_id": request.context.session_id,
        "timestamp": time.time(),
        "middleware": ["request-id", "rate-limiting", "jwt-auth", "validation", "metrics", "error-handling"]
    })


@app.route('/api/error-test', methods=['GET'])
@app.middleware([
    (request_id_middleware, 5),
    (error_handling_middleware, 95)
])
def error_test(request, response):
    """Endpoint that intentionally throws an error to test error handling"""
    raise Exception("This is a test error")


@app.route('/api/metrics', methods=['GET'])
@app.middleware([
    (request_id_middleware, 5),
    (jwt_auth_middleware, 10),
    (metrics_middleware, 90)
])
def get_metrics(request, response):
    """Get performance metrics (requires authentication)"""
    stats = getattr(metrics_middleware, 'stats', [])

    if not stats:
        response.json({
            "message": "No metrics available",
            "request_id": request.context.request_id
        })
        return

    # Calculate summary statistics
    durations = [s['duration_ms'] for s in stats]
    avg_duration = sum(durations) / len(durations) if durations else 0
    min_duration = min(durations) if durations else 0
    max_duration = max(durations) if durations else 0

    response.json({
        "metrics": {
            "total_requests": len(stats),
            "average_duration_ms": round(avg_duration, 2),
            "min_duration_ms": round(min_duration, 2),
            "max_duration_ms": round(max_duration, 2),
            "recent_requests": stats[-10:]  # Last 10 requests
        },
        "request_id": request.context.request_id
    })


@app.route('/api/token', methods=['POST'])
@app.middleware([
    (request_id_middleware, 5),
    (rate_limiting_middleware, 8),
    (request_validation_middleware, 15),
    (metrics_middleware, 90)
])
def generate_token(request, response):
    """Generate a demo JWT token"""
    try:
        data = json.loads(request.body)
        user_id = data.get('user_id', 'demo_user')
        session_id = data.get('session_id', 'demo_session')
    except (json.JSONDecodeError, AttributeError):
        user_id = 'demo_user'
        session_id = 'demo_session'

    # Generate demo token: user_id.session_id.timestamp
    timestamp = str(time.time())
    token = f"{user_id}.{session_id}.{timestamp}"

    response.json({
        "token": token,
        "user_id": user_id,
        "session_id": session_id,
        "expires_in": 3600,
        "request_id": request.context.request_id
    })


if __name__ == '__main__':
    print("🌪️ Catzilla Advanced Per-Route Middleware Example")
    print("=" * 60)
    print()
    print("Available endpoints:")
    print("  GET  /api/public     - Public API (rate limiting only)")
    print("  GET  /api/protected  - Protected API (full middleware)")
    print("  POST /api/protected  - Protected API (with validation)")
    print("  GET  /api/error-test - Error handling test")
    print("  GET  /api/metrics    - Performance metrics (auth required)")
    print("  POST /api/token      - Generate demo JWT token")
    print()
    print("To get a token:")
    print("  curl -X POST http://localhost:8000/api/token \\")
    print("       -H 'Content-Type: application/json' \\")
    print("       -d '{\"user_id\": \"your_user\"}'")
    print()
    print("To test protected endpoints:")
    print("  curl -H 'Authorization: Bearer YOUR_TOKEN' \\")
    print("       http://localhost:8000/api/protected")
    print()
    print("Starting server on http://localhost:8000...")
    print("=" * 60)

    app.run(host='0.0.0.0', port=8000, debug=True)
