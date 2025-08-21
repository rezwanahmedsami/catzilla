#!/usr/bin/env python3
"""
🌪️ Catzilla Advanced Middleware Features Example

This example demonstrates advanced middleware features in Catzilla using
the real middleware API, including performance monitoring, context passing,
and middleware composition patterns.

Features demonstrated:
- Advanced middleware patterns
- Performance monitoring
- Context passing between middleware
- Conditional middleware execution
- Middleware composition
- Error handling in middleware
- Resource cleanup
- Request/response transformation
"""

from catzilla import Catzilla, Request, Response, JSONResponse
from typing import Optional, Dict, Any, List, Callable
import time
import json
import uuid
import asyncio
from dataclasses import dataclass, asdict
from contextlib import contextmanager

# Initialize Catzilla
app = Catzilla(
    production=False,
    show_banner=True,
    log_requests=True
)

print("🌪️ Catzilla Advanced Middleware Features Example")
print("=" * 55)

# ============================================================================
# 1. PERFORMANCE MONITORING SYSTEM
# ============================================================================

@dataclass
class PerformanceMetrics:
    """Performance metrics for middleware"""
    total_executions: int = 0
    total_time_ms: float = 0.0
    min_time_ms: float = float('inf')
    max_time_ms: float = 0.0
    error_count: int = 0
    success_count: int = 0

# Global metrics storage
middleware_metrics: Dict[str, PerformanceMetrics] = {}
request_contexts: Dict[str, Dict[str, Any]] = {}

def get_or_create_metrics(name: str) -> PerformanceMetrics:
    """Get or create performance metrics for a middleware"""
    if name not in middleware_metrics:
        middleware_metrics[name] = PerformanceMetrics()
    return middleware_metrics[name]

@contextmanager
def measure_performance(middleware_name: str):
    """Context manager for measuring middleware performance"""
    start_time = time.time()
    metrics = get_or_create_metrics(middleware_name)
    metrics.total_executions += 1

    try:
        yield metrics
        # Success case
        execution_time = (time.time() - start_time) * 1000  # Convert to milliseconds
        metrics.total_time_ms += execution_time
        metrics.min_time_ms = min(metrics.min_time_ms, execution_time)
        metrics.max_time_ms = max(metrics.max_time_ms, execution_time)
        metrics.success_count += 1

    except Exception as e:
        # Error case
        metrics.error_count += 1
        raise

# ============================================================================
# 2. CONTEXT MANAGEMENT MIDDLEWARE
# ============================================================================

@app.middleware(priority=5, pre_route=True, name="context_manager")
def context_manager(request: Request) -> Optional[Response]:
    """Initialize and manage request context"""
    with measure_performance("context_manager"):
        print("🔧 Context Manager: Setting up request context")

        # Initialize request context
        request_id = str(uuid.uuid4())
        request.context = {
            'request_id': request_id,
            'start_time': time.time(),
            'features': set(),
            'middleware_chain': ["context_manager"],
            'user_data': {},
            'performance_marks': {},
            'cleanup_tasks': []
        }

        # Store in global context for cleanup
        request_contexts[request_id] = request.context

        print(f"✅ Context Manager: Request {request_id[:8]} initialized")
        return None

# ============================================================================
# 3. FEATURE TOGGLE MIDDLEWARE
# ============================================================================

@app.middleware(priority=15, pre_route=True, name="feature_toggle")
def feature_toggle(request: Request) -> Optional[Response]:
    """Manage feature toggles and conditional functionality"""
    with measure_performance("feature_toggle"):
        print("🎛️ Feature Toggle: Checking feature flags")

        # Add to middleware chain
        if hasattr(request, 'context'):
            request.context['middleware_chain'].append("feature_toggle")

        # Feature flags (in real app, load from config/database)
        features = {
            'rate_limiting': True,
            'advanced_auth': False,
            'request_logging': True,
            'response_caching': True,
            'compression': False
        }

        # Check for feature override headers
        for feature, enabled in features.items():
            header_key = f"x-feature-{feature.replace('_', '-')}"
            if header_key in request.headers:
                override = request.headers[header_key].lower() == 'true'
                features[feature] = override
                print(f"🔄 Feature Toggle: {feature} overridden to {override}")

        # Store enabled features in context
        request.context['features'] = {k for k, v in features.items() if v}

        print(f"✅ Feature Toggle: Enabled features: {list(request.context['features'])}")
        return None

# ============================================================================
# 4. AUTHENTICATION WITH CONTEXT
# ============================================================================

@app.middleware(priority=20, pre_route=True, name="advanced_auth")
def advanced_auth(request: Request) -> Optional[Response]:
    """Advanced authentication with context sharing"""
    with measure_performance("advanced_auth"):
        print("🔐 Advanced Auth: Processing authentication")

        # Add to middleware chain
        if hasattr(request, 'context'):
            request.context['middleware_chain'].append("advanced_auth")

        # Skip auth if feature is disabled
        if 'advanced_auth' not in request.context.get('features', set()):
            print("⏭️ Advanced Auth: Skipped (feature disabled)")
            return None

        # Check authentication
        auth_header = request.headers.get("authorization")

        if "/protected" in request.path or "/admin" in request.path:
            if not auth_header:
                return JSONResponse({
                    "error": "Authentication required",
                    "feature": "advanced_auth",
                    "request_id": request.context.get('request_id')
                }, status_code=401)

            if not auth_header.startswith("Bearer "):
                return JSONResponse({
                    "error": "Invalid authorization format",
                    "expected": "Bearer <token>",
                    "feature": "advanced_auth"
                }, status_code=401)

            token = auth_header[7:]

            # Simulate token validation
            user_data = {
                "id": "user123",
                "email": "user@example.com",
                "roles": ["user", "admin"] if token == "admin-token" else ["user"],
                "token": token,
                "authenticated_at": time.time()
            }

            request.context['user_data'] = user_data
            print(f"✅ Advanced Auth: User {user_data['id']} authenticated")

        return None

# ============================================================================
# 5. PERFORMANCE MONITORING MIDDLEWARE
# ============================================================================

@app.middleware(priority=30, pre_route=True, name="performance_monitor")
def performance_monitor(request: Request) -> Optional[Response]:
    """Monitor request performance and add marks"""
    with measure_performance("performance_monitor"):
        print("📊 Performance Monitor: Adding performance marks")

        # Add to middleware chain
        if hasattr(request, 'context'):
            request.context['middleware_chain'].append("performance_monitor")

        # Add performance marks
        current_time = time.time()
        request.context['performance_marks'] = {
            'middleware_start': current_time,
            'request_received': request.context.get('start_time', current_time)
        }

        # Log middleware execution time so far
        middleware_time = (current_time - request.context['start_time']) * 1000
        print(f"📈 Performance Monitor: Middleware execution time: {middleware_time:.2f}ms")

        return None

# ============================================================================
# 6. REQUEST TRANSFORMATION MIDDLEWARE
# ============================================================================

@app.middleware(priority=40, pre_route=True, name="request_transformer")
def request_transformer(request: Request) -> Optional[Response]:
    """Transform and enrich request data"""
    with measure_performance("request_transformer"):
        print("🔄 Request Transformer: Processing request data")

        # Add to middleware chain
        if hasattr(request, 'context'):
            request.context['middleware_chain'].append("request_transformer")

        # Add request metadata
        request.context['request_metadata'] = {
            'method': request.method,
            'path': request.path,
            'user_agent': request.headers.get('user-agent', 'unknown'),
            'content_type': request.headers.get('content-type', 'unknown'),
            'content_length': request.headers.get('content-length', 0),
            'client_ip': request.headers.get('x-forwarded-for', '127.0.0.1')
        }

        # Add performance mark
        request.context['performance_marks']['request_transformed'] = time.time()

        print("✅ Request Transformer: Request metadata added")
        return None

# ============================================================================
# 7. RESPONSE PROCESSING MIDDLEWARE
# ============================================================================

@app.middleware(priority=10, pre_route=False, post_route=True, name="response_processor")
def response_processor(request: Request) -> Optional[Response]:
    """Process and enhance responses"""
    with measure_performance("response_processor"):
        print("📤 Response Processor: Processing response")

        # Calculate total request time
        end_time = time.time()
        start_time = request.context.get('start_time', end_time)
        total_time = (end_time - start_time) * 1000

        # Add final performance mark
        request.context['performance_marks']['response_processed'] = end_time

        print(f"⏱️ Response Processor: Total request time: {total_time:.2f}ms")

        # Schedule cleanup
        request_id = request.context.get('request_id')
        if request_id:
            cleanup_task = lambda: cleanup_request_context(request_id)
            # In real app, you'd schedule this for later execution
            request.context['cleanup_tasks'].append(cleanup_task)

        return None

# ============================================================================
# 8. CLEANUP FUNCTION
# ============================================================================

def cleanup_request_context(request_id: str):
    """Clean up request context after processing"""
    if request_id in request_contexts:
        del request_contexts[request_id]
        print(f"🧹 Cleanup: Request context {request_id[:8]} cleaned up")

# ============================================================================
# 9. PER-ROUTE MIDDLEWARE FUNCTIONS
# ============================================================================

def rate_limit_middleware(request: Request) -> Optional[Response]:
    """Advanced rate limiting with context"""
    with measure_performance("rate_limit_middleware"):
        print("⏱️ Rate Limit: Checking advanced rate limits")

        # Add to middleware chain
        if hasattr(request, 'context'):
            request.context['middleware_chain'].append("rate_limit_middleware")

        # Check if rate limiting is enabled
        if 'rate_limiting' not in request.context.get('features', set()):
            print("⏭️ Rate Limit: Skipped (feature disabled)")
            return None

        # Get client info from context
        client_ip = request.context.get('request_metadata', {}).get('client_ip', '127.0.0.1')

        # Simple rate limiting logic
        print(f"✅ Rate Limit: Client {client_ip} - OK")
        return None

def admin_validation_middleware(request: Request) -> Optional[Response]:
    """Validate admin access with context"""
    with measure_performance("admin_validation_middleware"):
        print("👑 Admin Validation: Checking admin access")

        # Add to middleware chain
        if hasattr(request, 'context'):
            request.context['middleware_chain'].append("admin_validation_middleware")

        # Check user data from context
        user_data = request.context.get('user_data', {})

        if not user_data:
            return JSONResponse({
                "error": "Authentication required for admin access",
                "middleware": "admin_validation_middleware"
            }, status_code=401)

        # Check admin role
        if 'admin' not in user_data.get('roles', []):
            return JSONResponse({
                "error": "Admin privileges required",
                "user_id": user_data.get('id'),
                "middleware": "admin_validation_middleware"
            }, status_code=403)

        print(f"✅ Admin Validation: Admin access granted for user {user_data.get('id')}")
        return None

def caching_middleware(request: Request) -> Optional[Response]:
    """Response caching middleware"""
    with measure_performance("caching_middleware"):
        print("💾 Caching: Checking cache")

        # Add to middleware chain
        if hasattr(request, 'context'):
            request.context['middleware_chain'].append("caching_middleware")

        # Check if caching is enabled
        if 'response_caching' not in request.context.get('features', set()):
            print("⏭️ Caching: Skipped (feature disabled)")
            return None

        # In real app, check cache here
        print("✅ Caching: Cache miss - continuing to handler")
        return None

# ============================================================================
# 10. ROUTE HANDLERS
# ============================================================================

@app.get("/")
def home(request: Request) -> Response:
    """Home endpoint demonstrating context usage"""
    context = request.context

    return JSONResponse({
        "message": "🌪️ Catzilla Advanced Middleware Features",
        "request_id": context.get('request_id'),
        "middleware_chain": context.get('middleware_chain', []),
        "enabled_features": list(context.get('features', set())),
        "performance_marks": context.get('performance_marks', {}),
        "request_metadata": context.get('request_metadata', {}),
        "total_middleware": len(context.get('middleware_chain', []))
    })

@app.get("/protected")
def protected_endpoint(request: Request) -> Response:
    """Protected endpoint using context data"""
    context = request.context
    user_data = context.get('user_data', {})

    return JSONResponse({
        "message": "🔐 Protected endpoint accessed",
        "user": user_data,
        "request_id": context.get('request_id'),
        "middleware_chain": context.get('middleware_chain', []),
        "features_used": list(context.get('features', set()))
    })

@app.get("/api/data", middleware=[rate_limit_middleware, caching_middleware])
def api_data(request: Request) -> Response:
    """API endpoint with multiple per-route middleware"""
    context = request.context

    # Simulate some processing time
    time.sleep(0.01)

    return JSONResponse({
        "message": "📊 API data with advanced middleware",
        "data": {"items": [1, 2, 3, 4, 5], "total": 5},
        "request_id": context.get('request_id'),
        "middleware_chain": context.get('middleware_chain', []),
        "cache_enabled": 'response_caching' in context.get('features', set()),
        "rate_limit_enabled": 'rate_limiting' in context.get('features', set())
    })

@app.post("/admin/action", middleware=[admin_validation_middleware])
def admin_action(request: Request) -> Response:
    """Admin endpoint with validation middleware"""
    context = request.context
    user_data = context.get('user_data', {})

    return JSONResponse({
        "message": "👑 Admin action executed",
        "action": "data_updated",
        "admin_user": user_data.get('id'),
        "request_id": context.get('request_id'),
        "middleware_chain": context.get('middleware_chain', []),
        "timestamp": time.time()
    })

@app.get("/performance/metrics")
def get_performance_metrics(request: Request) -> Response:
    """Get middleware performance metrics"""
    context = request.context

    # Calculate average times
    metrics_data = {}
    for name, metrics in middleware_metrics.items():
        avg_time = metrics.total_time_ms / metrics.total_executions if metrics.total_executions > 0 else 0
        metrics_data[name] = {
            "executions": metrics.total_executions,
            "avg_time_ms": round(avg_time, 2),
            "min_time_ms": round(metrics.min_time_ms, 2) if metrics.min_time_ms != float('inf') else 0,
            "max_time_ms": round(metrics.max_time_ms, 2),
            "success_rate": round(metrics.success_count / metrics.total_executions * 100, 2) if metrics.total_executions > 0 else 0,
            "error_count": metrics.error_count
        }

    return JSONResponse({
        "message": "📈 Middleware performance metrics",
        "metrics": metrics_data,
        "active_contexts": len(request_contexts),
        "request_id": context.get('request_id')
    })

@app.get("/context/info")
def get_context_info(request: Request) -> Response:
    """Get detailed context information"""
    context = request.context

    return JSONResponse({
        "message": "🔍 Request context information",
        "context": {
            "request_id": context.get('request_id'),
            "middleware_chain": context.get('middleware_chain', []),
            "enabled_features": list(context.get('features', set())),
            "performance_marks": context.get('performance_marks', {}),
            "request_metadata": context.get('request_metadata', {}),
            "user_data": context.get('user_data', {}),
            "cleanup_tasks": len(context.get('cleanup_tasks', []))
        },
        "global_stats": {
            "total_active_contexts": len(request_contexts),
            "total_middleware_metrics": len(middleware_metrics)
        }
    })

@app.post("/performance/reset")
def reset_performance_metrics(request: Request) -> Response:
    """Reset all performance metrics"""
    global middleware_metrics, request_contexts

    middleware_metrics.clear()
    request_contexts.clear()

    return JSONResponse({
        "message": "📊 Performance metrics reset",
        "reset_timestamp": time.time()
    })

# ============================================================================
# 11. APPLICATION STARTUP
# ============================================================================

if __name__ == "__main__":
    print("\n🎯 Starting Catzilla Advanced Middleware Features Example...")
    print("\nGlobal Middleware Chain:")
    print("  1. context_manager (priority 5) - Initialize context")
    print("  2. feature_toggle (priority 15) - Manage feature flags")
    print("  3. advanced_auth (priority 20) - Authentication")
    print("  4. performance_monitor (priority 30) - Performance tracking")
    print("  5. request_transformer (priority 40) - Request enrichment")
    print("  6. response_processor (priority 10, post-route) - Response processing")

    print("\nAdvanced Features:")
    print("  - Context sharing between middleware")
    print("  - Performance monitoring and metrics")
    print("  - Feature toggles and conditional execution")
    print("  - Request/response transformation")
    print("  - Resource cleanup")
    print("  - Per-route middleware composition")

    print("\nAvailable endpoints:")
    print("  GET  /                      - Home (context demo)")
    print("  GET  /protected             - Protected endpoint")
    print("  GET  /api/data              - API with per-route middleware")
    print("  POST /admin/action          - Admin endpoint")
    print("  GET  /performance/metrics   - Performance metrics")
    print("  GET  /context/info          - Context information")
    print("  POST /performance/reset     - Reset metrics")

    print("\n🧪 Try these examples:")
    print("  # Normal request with context")
    print("  curl http://localhost:8000/")
    print()
    print("  # Protected endpoint with auth")
    print("  curl -H 'Authorization: Bearer test-token' http://localhost:8000/protected")
    print()
    print("  # API with feature toggles")
    print("  curl -H 'x-feature-rate-limiting: false' http://localhost:8000/api/data")
    print()
    print("  # Admin endpoint")
    print("  curl -H 'Authorization: Bearer admin-token' -X POST http://localhost:8000/admin/action")
    print()
    print("  # Performance metrics")
    print("  curl http://localhost:8000/performance/metrics")
    print()
    print("  # Context information")
    print("  curl http://localhost:8000/context/info")

    print(f"\n🚀 Server starting on http://localhost:8000")
    app.listen(8000)
