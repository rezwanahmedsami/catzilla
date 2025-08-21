#!/usr/bin/env python3
"""
E2E Test Server for Middleware Functionality

This server mirrors examples/middleware/ for E2E testing.
It provides middleware functionality to be tested via HTTP.
"""
import sys
import argparse
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from catzilla import Catzilla, Request, Response, JSONResponse, BaseModel, Path as PathParam
from typing import Optional
import time
import json

# Initialize Catzilla for E2E testing
app = Catzilla(
    production=False,
    show_banner=False,
    log_requests=False
)

# Request/Response tracking for middleware testing
request_log = []
middleware_log = []
rate_limit_data = {}

# Pydantic models
class ProcessData(BaseModel):
    """Data processing model"""
    data: str
    process_type: str = "default"

class AuthData(BaseModel):
    """Authentication data model"""
    token: str

# ============================================================================
# GLOBAL MIDDLEWARE - Runs on every request
# ============================================================================

@app.middleware()
def timing_middleware(request: Request) -> Optional[Response]:
    """Global timing middleware - measures request duration"""
    start_time = time.time()

    # Log this middleware execution
    middleware_log.append({
        "middleware": "timing",
        "phase": "start",
        "path": request.path,
        "timestamp": start_time
    })

    # Store timing in request state
    request.state = getattr(request, 'state', {})
    request.state['start_time'] = start_time

    # Log the request
    request_log.append({
        "method": request.method,
        "path": request.path,
        "timestamp": start_time,
        "headers": dict(request.headers)
    })

@app.middleware()
def logging_middleware(request: Request) -> Optional[Response]:
    """Global logging middleware - logs all requests"""
    request_info = {
        "method": request.method,
        "path": request.path,
        "timestamp": time.time(),
        "user_agent": request.headers.get("user-agent", "unknown")
    }
    request_log.append(request_info)

    middleware_log.append({
        "middleware": "logging",
        "phase": "before",
        "path": request.path,
        "timestamp": time.time()
    })

    # Continue to next middleware/route
    return None

@app.middleware()
def cors_middleware(request: Request) -> Optional[Response]:
    """CORS middleware - enables cross-origin requests"""
    # Log this middleware execution
    middleware_log.append({
        "middleware": "cors",
        "phase": "start",
        "path": request.path,
        "timestamp": time.time()
    })
    middleware_log.append({
        "middleware": "cors",
        "phase": "before",
        "path": request.path,
        "timestamp": time.time()
    })

    # Handle preflight requests
    if request.method == "OPTIONS":
        return JSONResponse({
            "message": "CORS preflight",
            "allowed_methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allowed_headers": ["Content-Type", "Authorization"]
        }, headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type, Authorization"
        })

    # Continue to next middleware/route (CORS headers will be added in response middleware)
    return None

# ============================================================================
# PER-ROUTE MIDDLEWARE
# ============================================================================

def auth_middleware(request: Request) -> Optional[Response]:
    """Authentication middleware for protected routes"""
    middleware_log.append({
        "middleware": "auth",
        "phase": "check",
        "path": request.path,
        "timestamp": time.time()
    })

    # Try multiple ways to get the authorization header (framework bug workaround)
    auth_header = (
        request.headers.get("authorization") or
        request.headers.get("Authorization") or
        request.get_header("Authorization") or
        request.get_header("authorization") or
        ""
    )

    if not auth_header or not auth_header.startswith("Bearer "):
        return JSONResponse({
            "error": "Authentication required",
            "message": "Missing or invalid authorization header",
            "middleware": "auth"
        }, status_code=401)

    token = auth_header[7:]  # Remove "Bearer " prefix

    if token != "valid-token":
        return JSONResponse({
            "error": "Invalid token",
            "message": "The provided token is invalid",
            "middleware": "auth"
        }, status_code=403)

    # Add user info to request
    request.state = getattr(request, 'state', {})
    request.state['user'] = {"id": 1, "username": "testuser"}

    middleware_log.append({
        "middleware": "auth",
        "phase": "success",
        "path": request.path,
        "timestamp": time.time()
    })

    return None  # Continue to route

def rate_limit_middleware(request: Request) -> Optional[Response]:
    """Rate limiting middleware"""
    middleware_log.append({
        "middleware": "rate_limit",
        "phase": "check",
        "path": request.path,
        "timestamp": time.time()
    })

    # Simple rate limiting simulation
    client_ip = (
        request.headers.get("x-forwarded-for") or
        request.get_header("x-forwarded-for") or
        "127.0.0.1"
    )
    current_time = time.time()

    # Check if rate limit exceeded (simplified)
    rate_limit_header = (
        request.headers.get("x-rate-limit-test") or
        request.get_header("x-rate-limit-test") or
        ""
    )

    if rate_limit_header == "exceeded":
        return JSONResponse({
            "error": "Rate limit exceeded",
            "message": "Too many requests",
            "middleware": "rate_limit",
            "retry_after": 60
        }, status_code=429)

    middleware_log.append({
        "middleware": "rate_limit",
        "phase": "allowed",
        "path": request.path,
        "timestamp": time.time()
    })

    return None  # Continue to route

def validation_middleware(request: Request) -> Optional[Response]:
    """Custom validation middleware"""
    middleware_log.append({
        "middleware": "validation",
        "phase": "check",
        "path": request.path,
        "timestamp": time.time()
    })

    # Check for custom validation header (framework bug workaround)
    validation_header = (
        request.headers.get("x-custom-validation") or
        request.get_header("x-custom-validation") or
        ""
    )

    if validation_header == "fail":
        return JSONResponse({
            "error": "Custom validation failed",
            "message": "Custom validation rules not met",
            "middleware": "validation"
        }, status_code=400)

    return None  # Continue to route

# ============================================================================
# ROUTES WITH MIDDLEWARE
# ============================================================================

# Health check
@app.get("/health")
def health_check(request: Request) -> Response:
    """Health check endpoint"""
    duration = 0
    if hasattr(request, 'state') and 'start_time' in request.state:
        duration = time.time() - request.state['start_time']

    return JSONResponse({
        "status": "healthy",
        "server": "middleware_e2e_test",
        "timestamp": time.time(),
        "request_duration": duration,
        "middleware_count": len(middleware_log)
    })

# Basic info
@app.get("/")
def home(request: Request) -> Response:
    """Middleware test server info"""
    return JSONResponse({
        "message": "Catzilla E2E Middleware Test Server",
        "features": [
            "Global middleware",
            "Per-route middleware",
            "Middleware ordering",
            "Authentication middleware",
            "Rate limiting middleware",
            "Custom validation middleware"
        ],
        "endpoints": [
            "GET /public",
            "GET /protected (requires auth)",
            "GET /rate-limited",
            "POST /process",
            "GET /middleware/logs",
            "GET /middleware/stats"
        ]
    })

# Public endpoint (only global middleware)
@app.get("/public")
def public_endpoint(request: Request) -> Response:
    """Public endpoint with only global middleware"""
    duration = 0
    if hasattr(request, 'state') and 'start_time' in request.state:
        duration = time.time() - request.state['start_time']

    return JSONResponse({
        "message": "This is a public endpoint",
        "middleware_applied": ["timing", "logging", "cors"],
        "request_duration": duration,
        "timestamp": time.time()
    })

# Protected endpoint (global + auth middleware)
@app.get("/protected", middleware=[auth_middleware])
def protected_endpoint(request: Request) -> Response:
    """Protected endpoint requiring authentication"""
    duration = 0
    user = None
    if hasattr(request, 'state'):
        if 'start_time' in request.state:
            duration = time.time() - request.state['start_time']
        user = request.state.get('user')

    return JSONResponse({
        "message": "This is a protected endpoint",
        "user": user,
        "middleware_applied": ["timing", "logging", "cors", "auth"],
        "request_duration": duration,
        "timestamp": time.time()
    })

# Rate limited endpoint
@app.get("/rate-limited", middleware=[rate_limit_middleware])
def rate_limited_endpoint(request: Request) -> Response:
    """Rate limited endpoint"""
    duration = 0
    if hasattr(request, 'state') and 'start_time' in request.state:
        duration = time.time() - request.state['start_time']

    return JSONResponse({
        "message": "This endpoint has rate limiting",
        "middleware_applied": ["timing", "logging", "cors", "rate_limit"],
        "request_duration": duration,
        "timestamp": time.time()
    })

# Multiple middleware endpoint
@app.get("/multi-middleware", middleware=[auth_middleware, rate_limit_middleware, validation_middleware])
def multi_middleware_endpoint(request: Request) -> Response:
    """Endpoint with multiple middleware layers"""
    duration = 0
    user = None
    if hasattr(request, 'state'):
        if 'start_time' in request.state:
            duration = time.time() - request.state['start_time']
        user = request.state.get('user')

    return JSONResponse({
        "message": "This endpoint has multiple middleware layers",
        "user": user,
        "middleware_applied": ["timing", "logging", "cors", "auth", "rate_limit", "validation"],
        "request_duration": duration,
        "timestamp": time.time()
    })

# POST endpoint with middleware
@app.post("/process", middleware=[validation_middleware])
def process_data(request: Request, data: ProcessData) -> Response:
    """Process data with validation middleware"""
    duration = 0
    if hasattr(request, 'state') and 'start_time' in request.state:
        duration = time.time() - request.state['start_time']

    # Simulate data processing
    processed_result = {
        "original": data.data,
        "processed": data.data.upper(),
        "type": data.process_type,
        "processed_at": time.time()
    }

    return JSONResponse({
        "message": "Data processed successfully",
        "result": processed_result,
        "middleware_applied": ["timing", "logging", "cors", "validation"],
        "request_duration": duration,
        "timestamp": time.time()
    }, status_code=201)

# Middleware logs endpoint
@app.get("/middleware/logs")
def get_middleware_logs(request: Request) -> Response:
    """Get middleware execution logs"""
    return JSONResponse({
        "middleware_logs": middleware_log,
        "total_logs": len(middleware_log),
        "request_logs": request_log,
        "total_requests": len(request_log)
    })

# Middleware statistics
@app.get("/middleware/stats")
def get_middleware_stats(request: Request) -> Response:
    """Get middleware execution statistics"""
    # Count middleware executions by type
    middleware_counts = {}
    for log in middleware_log:
        mw_name = log["middleware"]
        middleware_counts[mw_name] = middleware_counts.get(mw_name, 0) + 1

    # Calculate average request duration (from timing middleware)
    total_requests = len(request_log)
    avg_duration = 0
    if total_requests > 0:
        # Simplified calculation
        avg_duration = 0.05  # Mock average

    return JSONResponse({
        "total_requests": total_requests,
        "middleware_executions": middleware_counts,
        "total_middleware_logs": len(middleware_log),
        "average_request_duration": avg_duration,
        "timestamp": time.time()
    })

# Clear logs endpoint
@app.post("/middleware/clear-logs")
def clear_middleware_logs(request: Request) -> Response:
    """Clear middleware and request logs"""
    global middleware_log, request_log

    cleared_middleware = len(middleware_log)
    cleared_requests = len(request_log)

    middleware_log.clear()
    request_log.clear()

    return JSONResponse({
        "message": "Logs cleared successfully",
        "cleared_middleware_logs": cleared_middleware,
        "cleared_request_logs": cleared_requests,
        "total_logs": 0,
        "total_requests": 0
    })

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Catzilla E2E Middleware Test Server")
    parser.add_argument("--port", type=int, default=8105, help="Port to run server on")
    parser.add_argument("--host", type=str, default="127.0.0.1", help="Host to bind to")

    args = parser.parse_args()

    print(f"🚀 Starting Catzilla E2E Middleware Test Server")
    print(f"📍 Server: http://{args.host}:{args.port}")
    print(f"🏥 Health: http://{args.host}:{args.port}/health")

    app.listen(port=args.port, host=args.host)
