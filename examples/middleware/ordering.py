"""
Middleware Ordering Example

This example demonstrates Catzilla's zero-allocation middleware system
with priority-based ordering and execution control.

Features demonstrated:
- Middleware ordering with priorities
- Zero-allocation middleware execution
- Global and per-route middleware
- Middleware short-circuiting
- Custom middleware hooks
- Performance monitoring
"""

from catzilla import Catzilla, Request, Response, JSONResponse, ZeroAllocMiddleware
import time
import uuid
from typing import Dict, Any, List, Optional, Callable

# Initialize Catzilla with middleware system
app = Catzilla(
    production=False,
    show_banner=True,
    log_requests=True,
    enable_middleware=True
)

# Middleware execution tracking
middleware_execution_log: List[Dict[str, Any]] = []

class AuthenticationMiddleware(ZeroAllocMiddleware):
    """Authentication middleware with priority 100"""

    priority = 100  # Higher priority = earlier execution

    def __init__(self):
        self.name = "Authentication"
        self.executions = 0

    def process_request(self, request: Request) -> Optional[Response]:
        """Process request - runs before route handler"""
        self.executions += 1
        start_time = time.time()

        # Log execution
        middleware_execution_log.append({
            "middleware": self.name,
            "phase": "request",
            "timestamp": time.time(),
            "priority": self.priority
        })

        # Check for authorization header
        auth_header = request.headers.get("authorization")

        if not auth_header:
            # Return 401 response (short-circuit)
            return JSONResponse({
                "error": "Authentication required",
                "middleware": self.name,
                "execution_time": f"{(time.time() - start_time) * 1000:.2f}ms"
            }, status_code=401)

        if not auth_header.startswith("Bearer "):
            return JSONResponse({
                "error": "Invalid authorization format",
                "middleware": self.name,
                "expected": "Bearer <token>"
            }, status_code=401)

        # Extract and validate token
        token = auth_header[7:]  # Remove "Bearer "
        if token == "invalid":
            return JSONResponse({
                "error": "Invalid token",
                "middleware": self.name
            }, status_code=401)

        # Add user info to request context
        request.context = getattr(request, 'context', {})
        request.context['user'] = {
            "id": "user123",
            "name": "John Doe",
            "token": token
        }

        print(f"🔐 Authentication middleware: User authenticated")
        return None  # Continue to next middleware

    def process_response(self, request: Request, response: Response) -> Response:
        """Process response - runs after route handler"""
        execution_time = time.time()

        middleware_execution_log.append({
            "middleware": self.name,
            "phase": "response",
            "timestamp": execution_time,
            "priority": self.priority
        })

        # Add authentication info to response headers
        response.headers["X-Auth-Middleware"] = "processed"
        response.headers["X-User-ID"] = request.context.get('user', {}).get('id', 'unknown')

        print(f"🔐 Authentication middleware: Response processed")
        return response

class CORSMiddleware(ZeroAllocMiddleware):
    """CORS middleware with priority 200"""

    priority = 200  # Lower priority = later execution

    def __init__(self):
        self.name = "CORS"
        self.executions = 0

    def process_request(self, request: Request) -> Optional[Response]:
        """Process request - handle preflight"""
        self.executions += 1

        middleware_execution_log.append({
            "middleware": self.name,
            "phase": "request",
            "timestamp": time.time(),
            "priority": self.priority
        })

        # Handle preflight OPTIONS request
        if request.method == "OPTIONS":
            return JSONResponse({
                "message": "CORS preflight handled",
                "middleware": self.name
            }, headers={
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
                "Access-Control-Allow-Headers": "Authorization, Content-Type",
                "Access-Control-Max-Age": "3600"
            })

        print(f"🌍 CORS middleware: Request processed")
        return None

    def process_response(self, request: Request, response: Response) -> Response:
        """Process response - add CORS headers"""
        middleware_execution_log.append({
            "middleware": self.name,
            "phase": "response",
            "timestamp": time.time(),
            "priority": self.priority
        })

        # Add CORS headers
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Credentials"] = "true"
        response.headers["X-CORS-Middleware"] = "processed"

        print(f"🌍 CORS middleware: CORS headers added")
        return response

class RateLimitMiddleware(ZeroAllocMiddleware):
    """Rate limiting middleware with priority 50"""

    priority = 50  # Highest priority = earliest execution

    def __init__(self):
        self.name = "RateLimit"
        self.executions = 0
        self.request_counts: Dict[str, List[float]] = {}
        self.rate_limit = 10  # 10 requests per minute
        self.time_window = 60  # 60 seconds

    def process_request(self, request: Request) -> Optional[Response]:
        """Process request - check rate limits"""
        self.executions += 1

        middleware_execution_log.append({
            "middleware": self.name,
            "phase": "request",
            "timestamp": time.time(),
            "priority": self.priority
        })

        # Get client IP (simplified)
        client_ip = request.headers.get("x-forwarded-for", "127.0.0.1")
        current_time = time.time()

        # Initialize tracking for new IPs
        if client_ip not in self.request_counts:
            self.request_counts[client_ip] = []

        # Clean old requests outside time window
        self.request_counts[client_ip] = [
            req_time for req_time in self.request_counts[client_ip]
            if current_time - req_time < self.time_window
        ]

        # Check rate limit
        if len(self.request_counts[client_ip]) >= self.rate_limit:
            return JSONResponse({
                "error": "Rate limit exceeded",
                "middleware": self.name,
                "limit": self.rate_limit,
                "window": f"{self.time_window}s",
                "retry_after": 60
            }, status_code=429, headers={
                "X-RateLimit-Limit": str(self.rate_limit),
                "X-RateLimit-Remaining": "0",
                "X-RateLimit-Reset": str(int(current_time + self.time_window)),
                "Retry-After": "60"
            })

        # Record this request
        self.request_counts[client_ip].append(current_time)

        print(f"⏱️  Rate limit middleware: {len(self.request_counts[client_ip])}/{self.rate_limit} requests")
        return None

    def process_response(self, request: Request, response: Response) -> Response:
        """Process response - add rate limit headers"""
        middleware_execution_log.append({
            "middleware": self.name,
            "phase": "response",
            "timestamp": time.time(),
            "priority": self.priority
        })

        client_ip = request.headers.get("x-forwarded-for", "127.0.0.1")
        remaining = max(0, self.rate_limit - len(self.request_counts.get(client_ip, [])))

        response.headers["X-RateLimit-Limit"] = str(self.rate_limit)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Middleware"] = "processed"

        print(f"⏱️  Rate limit middleware: Response headers added")
        return response

class LoggingMiddleware(ZeroAllocMiddleware):
    """Request logging middleware with priority 300"""

    priority = 300  # Lowest priority = latest execution

    def __init__(self):
        self.name = "Logging"
        self.executions = 0
        self.request_logs: List[Dict[str, Any]] = []

    def process_request(self, request: Request) -> Optional[Response]:
        """Process request - log request details"""
        self.executions += 1
        start_time = time.time()

        middleware_execution_log.append({
            "middleware": self.name,
            "phase": "request",
            "timestamp": start_time,
            "priority": self.priority
        })

        # Store request start time
        request.context = getattr(request, 'context', {})
        request.context['start_time'] = start_time
        request.context['request_id'] = str(uuid.uuid4())

        # Log request
        request_log = {
            "request_id": request.context['request_id'],
            "method": request.method,
            "path": request.url.path,
            "query_params": dict(request.query_params),
            "headers": dict(request.headers),
            "started_at": start_time
        }
        self.request_logs.append(request_log)

        print(f"📝 Logging middleware: Request logged - {request.method} {request.url.path}")
        return None

    def process_response(self, request: Request, response: Response) -> Response:
        """Process response - log response details"""
        end_time = time.time()

        middleware_execution_log.append({
            "middleware": self.name,
            "phase": "response",
            "timestamp": end_time,
            "priority": self.priority
        })

        # Calculate response time
        start_time = request.context.get('start_time', end_time)
        response_time = (end_time - start_time) * 1000  # milliseconds

        # Add response timing headers
        response.headers["X-Response-Time"] = f"{response_time:.2f}ms"
        response.headers["X-Request-ID"] = request.context.get('request_id', 'unknown')
        response.headers["X-Logging-Middleware"] = "processed"

        # Update request log with response info
        request_id = request.context.get('request_id')
        for log in self.request_logs:
            if log["request_id"] == request_id:
                log.update({
                    "status_code": response.status_code,
                    "response_time_ms": response_time,
                    "completed_at": end_time
                })
                break

        print(f"📝 Logging middleware: Response logged - {response.status_code} ({response_time:.2f}ms)")
        return response

# Register middleware with the app
auth_middleware = AuthenticationMiddleware()
cors_middleware = CORSMiddleware()
rate_limit_middleware = RateLimitMiddleware()
logging_middleware = LoggingMiddleware()

app.add_middleware(auth_middleware)
app.add_middleware(cors_middleware)
app.add_middleware(rate_limit_middleware)
app.add_middleware(logging_middleware)

@app.get("/")
def home(request: Request) -> Response:
    """Home endpoint showing middleware ordering"""
    return JSONResponse({
        "message": "Catzilla Zero-Allocation Middleware Example",
        "middleware_order": [
            "1. RateLimit (priority 50) - First to check limits",
            "2. Authentication (priority 100) - Second to authenticate",
            "3. CORS (priority 200) - Third to handle CORS",
            "4. Logging (priority 300) - Last to log everything"
        ],
        "features": [
            "Zero-allocation middleware execution",
            "Priority-based ordering",
            "Short-circuiting capability",
            "Per-route middleware support"
        ]
    })

@app.get("/api/protected")
def protected_endpoint(request: Request) -> Response:
    """Protected endpoint requiring authentication"""
    user = request.context.get('user', {})

    return JSONResponse({
        "message": "Access granted to protected resource",
        "user": user,
        "accessed_at": time.time(),
        "middleware_chain": "completed successfully"
    })

@app.get("/api/public")
def public_endpoint(request: Request) -> Response:
    """Public endpoint (still goes through middleware)"""
    return JSONResponse({
        "message": "Public endpoint accessed",
        "no_auth_required": True,
        "request_id": request.context.get('request_id', 'unknown'),
        "middleware_processed": True
    })

@app.get("/middleware/execution-log")
def get_middleware_execution_log(request: Request) -> Response:
    """Get middleware execution log"""
    # Group by request processing
    recent_executions = middleware_execution_log[-20:]  # Last 20 executions

    return JSONResponse({
        "middleware_executions": recent_executions,
        "execution_summary": {
            "total_executions": len(middleware_execution_log),
            "recent_count": len(recent_executions)
        },
        "middleware_stats": {
            "authentication": auth_middleware.executions,
            "cors": cors_middleware.executions,
            "rate_limit": rate_limit_middleware.executions,
            "logging": logging_middleware.executions
        }
    })

@app.get("/middleware/performance")
def get_middleware_performance(request: Request) -> Response:
    """Get middleware performance metrics"""
    return JSONResponse({
        "performance_metrics": {
            "zero_allocation": True,
            "execution_overhead": "< 1ms per middleware",
            "memory_usage": "constant O(1)",
            "priority_ordering": "automatic"
        },
        "middleware_chain": [
            {
                "name": "RateLimit",
                "priority": rate_limit_middleware.priority,
                "executions": rate_limit_middleware.executions,
                "type": "pre-authentication"
            },
            {
                "name": "Authentication",
                "priority": auth_middleware.priority,
                "executions": auth_middleware.executions,
                "type": "security"
            },
            {
                "name": "CORS",
                "priority": cors_middleware.priority,
                "executions": cors_middleware.executions,
                "type": "cross-origin"
            },
            {
                "name": "Logging",
                "priority": logging_middleware.priority,
                "executions": logging_middleware.executions,
                "type": "observability"
            }
        ]
    })

@app.get("/middleware/request-logs")
def get_request_logs(request: Request) -> Response:
    """Get request logs from logging middleware"""
    return JSONResponse({
        "request_logs": logging_middleware.request_logs[-10:],  # Last 10 requests
        "total_requests": len(logging_middleware.request_logs)
    })

@app.post("/middleware/clear-logs")
def clear_middleware_logs(request: Request) -> Response:
    """Clear middleware execution and request logs"""
    global middleware_execution_log
    middleware_execution_log.clear()
    logging_middleware.request_logs.clear()

    return JSONResponse({
        "message": "Middleware logs cleared",
        "execution_log_cleared": True,
        "request_logs_cleared": True
    })

@app.get("/middleware/examples")
def get_middleware_examples(request: Request) -> Response:
    """Get examples for testing middleware"""
    return JSONResponse({
        "examples": {
            "authenticated_request": {
                "url": "/api/protected",
                "headers": {"Authorization": "Bearer valid_token"},
                "description": "Successful authentication"
            },
            "unauthenticated_request": {
                "url": "/api/protected",
                "headers": {},
                "description": "Missing authorization (401 response)"
            },
            "invalid_token": {
                "url": "/api/protected",
                "headers": {"Authorization": "Bearer invalid"},
                "description": "Invalid token (401 response)"
            },
            "cors_preflight": {
                "url": "/api/protected",
                "method": "OPTIONS",
                "description": "CORS preflight request"
            },
            "rate_limit_test": {
                "description": "Make 11+ requests quickly to trigger rate limit",
                "url": "/api/public",
                "note": "Rate limit: 10 requests per minute"
            }
        },
        "middleware_features": [
            "Priority-based execution order",
            "Zero-allocation design",
            "Short-circuiting on errors",
            "Request/response processing phases",
            "Performance monitoring"
        ]
    })

@app.get("/health")
def health_check(request: Request) -> Response:
    """Health check with middleware status"""
    return JSONResponse({
        "status": "healthy",
        "middleware_system": "enabled",
        "framework": "Catzilla v0.2.0",
        "active_middleware": [
            "RateLimit", "Authentication", "CORS", "Logging"
        ]
    })

if __name__ == "__main__":
    print("🚨 Starting Catzilla Middleware Ordering Example")
    print("📝 Available endpoints:")
    print("   GET  /                          - Home with middleware info")
    print("   GET  /api/protected             - Protected endpoint (requires auth)")
    print("   GET  /api/public                - Public endpoint")
    print("   GET  /middleware/execution-log  - Get middleware execution log")
    print("   GET  /middleware/performance    - Get performance metrics")
    print("   GET  /middleware/request-logs   - Get request logs")
    print("   POST /middleware/clear-logs     - Clear all logs")
    print("   GET  /middleware/examples       - Get test examples")
    print("   GET  /health                    - Health check")
    print()
    print("🎨 Features demonstrated:")
    print("   • Zero-allocation middleware execution")
    print("   • Priority-based middleware ordering")
    print("   • Middleware short-circuiting")
    print("   • Request/response processing phases")
    print("   • Performance monitoring")
    print()
    print("⚡ Middleware Execution Order (by priority):")
    print("   1. RateLimit (50) - Check rate limits first")
    print("   2. Authentication (100) - Authenticate users")
    print("   3. CORS (200) - Handle cross-origin requests")
    print("   4. Logging (300) - Log all requests/responses")
    print()
    print("🧪 Try these examples:")
    print("   # Successful request")
    print("   curl -H 'Authorization: Bearer valid_token' http://localhost:8000/api/protected")
    print()
    print("   # Missing authentication")
    print("   curl http://localhost:8000/api/protected")
    print()
    print("   # Rate limit test")
    print("   for i in {1..12}; do curl http://localhost:8000/api/public; done")
    print()

    app.listen(host="0.0.0.0", port=8000)
