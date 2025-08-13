#!/usr/bin/env python3
"""
Flask Middleware Benchmark Server

This server demonstrates Flask's middleware performance for comparison
with Catzilla's middleware system using Flask's before_request/after_request hooks.
"""

import sys
import os
import json
import time
from typing import Optional

from flask import Flask, request, jsonify, g

# Initialize Flask
app = Flask(__name__)

print("🚀 Flask Middleware Benchmark Server")

# ============================================================================
# MIDDLEWARE CLASSES
# ============================================================================

class BenchmarkRequestLogger:
    """Flask request logging middleware"""

    def __init__(self, app):
        self.app = app
        self.init_app()

    def init_app(self):
        @self.app.before_request
        def log_request():
            # Simulate request logging operation
            # Removed artificial delay for benchmarking

            g.start_time = time.time()
            g.request_id = f"req_{int(g.start_time * 1000000)}"

class BenchmarkSecurityMiddleware:
    """Flask security headers middleware"""

    def __init__(self, app):
        self.app = app
        self.init_app()

    def init_app(self):
        @self.app.before_request
        def validate_security():
            # Simulate security validation
            # Removed artificial delay for benchmarking

            g.security_validated = True

class BenchmarkRateLimitMiddleware:
    """Flask rate limiting middleware"""

    def __init__(self, app):
        self.app = app
        self.init_app()

    def init_app(self):
        @self.app.before_request
        def check_rate_limit():
            client_ip = request.remote_addr or "127.0.0.1"

            # Simulate rate limit check
            # Removed artificial delay for benchmarking

            g.rate_limit = {
                'ip': client_ip,
                'remaining': 1000,
                'checked_at': time.time()
            }

class BenchmarkCORSMiddleware:
    """Flask CORS middleware"""

    def __init__(self, app):
        self.app = app
        self.init_app()

    def init_app(self):
        @self.app.after_request
        def add_cors_headers(response):
            response.headers['Access-Control-Allow-Origin'] = '*'
            response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
            response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
            return response

# ============================================================================
# APPLY MIDDLEWARE TO APP
# ============================================================================

# Initialize middleware
request_logger = BenchmarkRequestLogger(app)
security_middleware = BenchmarkSecurityMiddleware(app)
rate_limit_middleware = BenchmarkRateLimitMiddleware(app)
cors_middleware = BenchmarkCORSMiddleware(app)

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def check_auth_token():
    """Helper function for authentication"""
    auth_header = request.headers.get("authorization")

    if not auth_header:
        return None, "Missing Authorization header"

    if not auth_header.startswith("Bearer "):
        return None, "Invalid Authorization format"

    token = auth_header[7:]

    # Simulate token validation
    # Removed artificial delay for benchmarking

    if token == "invalid":
        return None, "Invalid token"

    return {
        "id": "user_123",
        "name": "Benchmark User",
        "token": token,
        "validated_at": time.time()
    }, None

def perform_rate_limit_check():
    """Helper function for rate limiting"""
    # This would normally check Redis or database
    # Removed artificial delay for benchmarking

    return {
        "remaining": 1000,
        "checked_at": time.time()
    }

# ============================================================================
# BENCHMARK ENDPOINTS
# ============================================================================

@app.route("/")
def home():
    """Home endpoint - tests basic middleware overhead"""
    return jsonify({
        "message": "Flask Middleware Benchmark",
        "framework": "flask",
        "middleware_layers": 4,  # Logger + Security + Rate Limit + CORS
        "request_id": getattr(g, 'request_id', 'unknown')
    })

@app.route("/health")
def health_check():
    """Health check endpoint - minimal processing"""
    return jsonify({
        "status": "healthy",
        "framework": "flask",
        "middleware": "enabled"
    })

@app.route("/middleware-light")
def middleware_light_test():
    """Light middleware test - only global middleware"""
    return jsonify({
        "test": "middleware_light",
        "framework": "flask",
        "global_middleware": {
            "request_id": getattr(g, 'request_id', None),
            "cors_enabled": True,
            "security_validated": getattr(g, 'security_validated', False)
        },
        "performance": "optimized"
    })

@app.route("/middleware-heavy")
def middleware_heavy_test():
    """Heavy middleware test - global + authentication + rate limiting"""
    # Check authentication
    user, auth_error = check_auth_token()
    if auth_error:
        return jsonify({"error": auth_error}), 401

    # Check rate limiting
    rate_limit = perform_rate_limit_check()

    return jsonify({
        "test": "middleware_heavy",
        "framework": "flask",
        "global_middleware": {
            "request_id": getattr(g, 'request_id', None),
            "cors_enabled": True,
            "security_validated": getattr(g, 'security_validated', False)
        },
        "function_middleware": {
            "auth": user.get('id') if user else None,
            "rate_limit": rate_limit.get('remaining')
        },
        "total_middleware_layers": 6,  # 4 global + 2 function-level
        "performance": "high_load_test"
    })

@app.route("/middleware-auth")
def middleware_auth_test():
    """Authentication middleware test"""
    user, auth_error = check_auth_token()
    if auth_error:
        return jsonify({"error": auth_error}), 401

    return jsonify({
        "test": "middleware_auth",
        "framework": "flask",
        "authenticated": True,
        "user": {
            "id": user.get('id'),
            "name": user.get('name')
        },
        "auth_performance": "validated"
    })

@app.route("/middleware-cors")
def middleware_cors_test():
    """CORS middleware test"""
    return jsonify({
        "test": "middleware_cors",
        "framework": "flask",
        "cors_enabled": True,
        "global_middleware": {
            "request_id": getattr(g, 'request_id', None),
            "cors_headers": "enabled"
        },
        "performance": "cors_optimized"
    })

@app.route("/middleware-logging")
def middleware_logging_test():
    """Logging middleware test"""
    return jsonify({
        "test": "middleware_logging",
        "framework": "flask",
        "logging_enabled": True,
        "global_middleware": {
            "request_id": getattr(g, 'request_id', None),
            "logged": True
        },
        "performance": "logging_optimized"
    })

@app.route("/middleware-compression")
def middleware_compression_test():
    """Compression middleware test"""
    return jsonify({
        "test": "middleware_compression",
        "framework": "flask",
        "compression": "simulated",
        "global_middleware": {
            "request_id": getattr(g, 'request_id', None),
            "compression_enabled": True
        },
        "performance": "compression_ready"
    })

@app.route("/middleware-stats")
def middleware_stats():
    """Middleware performance statistics"""
    start_time = getattr(g, 'start_time', time.time())
    processing_time = (time.time() - start_time) * 1000  # Convert to milliseconds

    return jsonify({
        "test": "middleware_stats",
        "framework": "flask",
        "performance": {
            "processing_time_ms": round(processing_time, 3),
            "middleware_overhead": "before_after_request",
            "sync_operations": "blocking"
        },
        "middleware_summary": {
            "global_layers": 4,
            "function_layers": "variable",
            "total_hooks": "before_request + after_request",
            "compatibility": "wsgi_sync"
        }
    })

@app.route("/middleware-post", methods=["POST"])
def middleware_post_test():
    """POST endpoint with middleware - tests request body processing"""
    # Check authentication
    user, auth_error = check_auth_token()
    if auth_error:
        return jsonify({"error": auth_error}), 401

    try:
        body = request.get_json() or {}
    except:
        body = {"error": "Invalid JSON"}

    return jsonify({
        "test": "middleware_post",
        "method": "POST",
        "framework": "flask",
        "body_received": body,
        "authenticated": user.get('id') is not None if user else False,
        "middleware_performance": "wsgi_optimized"
    })

@app.route("/middleware-concurrent")
def middleware_concurrent_test():
    """Endpoint to test middleware with concurrent operations"""
    # Fast operations without artificial delays
    operations = [
        "operation_1_completed",
        "operation_2_completed",
        "operation_3_completed"
    ]

    return jsonify({
        "test": "middleware_concurrent",
        "framework": "flask",
        "operations": operations,
        "concurrent_execution": "simulated",
        "middleware_compatibility": "wsgi_sync",
        "request_context": {
            "request_id": getattr(g, 'request_id', None),
            "validated": getattr(g, 'security_validated', False)
        }
    })

# ============================================================================
# SERVER STARTUP
# ============================================================================

def main():
    import argparse

    parser = argparse.ArgumentParser(description='Flask Middleware Benchmark Server')
    parser.add_argument('--port', type=int, default=8033, help='Port to run the server on')
    parser.add_argument('--host', default='0.0.0.0', help='Host to bind the server to')

    args = parser.parse_args()

    print(f"🚀 Starting Flask Middleware Benchmark Server on {args.host}:{args.port}")
    print("Available endpoints:")
    print("  GET  /                      - Home (basic middleware)")
    print("  GET  /health                - Health check")
    print("  GET  /middleware-light      - Light middleware test")
    print("  GET  /middleware-heavy      - Heavy middleware test (requires auth)")
    print("  GET  /middleware-auth       - Auth middleware test (requires auth)")
    print("  GET  /middleware-cors       - CORS middleware test")
    print("  GET  /middleware-logging    - Logging middleware test")
    print("  GET  /middleware-compression - Compression middleware test")
    print("  GET  /middleware-stats      - Middleware performance stats")
    print("  POST /middleware-post       - POST with middleware (requires auth)")
    print("  GET  /middleware-concurrent - Concurrent operations with middleware")
    print("")
    print("🧪 Test with auth: curl -H 'Authorization: Bearer valid-token' http://localhost:8033/middleware-heavy")

    try:
        app.run(
            host=args.host,
            port=args.port,
            debug=False,  # Disable debug for benchmarking
            threaded=True  # Enable threading for better concurrency
        )
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

# Create app instance for WSGI servers like gunicorn (exposed at module level)
# This is already created above as 'app'
