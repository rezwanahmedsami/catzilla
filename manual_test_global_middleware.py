#!/usr/bin/env python3
"""
Manual test server to verify global middleware execution
Start this and make curl requests to test global middleware
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'python'))

from catzilla import Catzilla
from catzilla.response import JSONResponse

app = Catzilla(use_jemalloc=False, memory_profiling=False)

# Global pre-route middleware
@app.middleware(priority=100, pre_route=True, name="global_cors")
def global_cors_middleware(request):
    print(f"🌍 GLOBAL CORS: {request.method} {request.path}")
    return None

@app.middleware(priority=200, pre_route=True, name="global_auth")
def global_auth_middleware(request):
    print(f"🌍 GLOBAL AUTH: {request.method} {request.path}")
    # Add custom data to prove global middleware ran
    request.custom_data = getattr(request, 'custom_data', {})
    request.custom_data['global_auth'] = 'passed'
    return None

# Global post-route middleware
@app.middleware(priority=300, pre_route=False, post_route=True, name="global_response_logger")
def global_response_logger(request, response):
    print(f"🌍 GLOBAL RESPONSE: {request.method} {request.path} -> {response.status_code}")
    # Add header to prove post-route middleware ran
    response.headers["X-Global-Middleware"] = "executed"
    return None

# Per-route middleware for comparison
def route_auth_middleware(request):
    print(f"🎯 ROUTE AUTH: {request.method} {request.path}")
    return None

def route_logging_middleware(request):
    print(f"🎯 ROUTE LOG: {request.method} {request.path}")
    return None

# Routes
@app.get("/test", middleware=[route_auth_middleware, route_logging_middleware])
def test_route(request):
    print(f"🎯 HANDLER: {request.method} {request.path}")
    auth_status = getattr(request, 'custom_data', {}).get('global_auth', 'not_found')
    return JSONResponse({
        "message": "test route with per-route middleware",
        "global_auth_passed": auth_status,
        "path": request.path
    })

@app.get("/plain")
def plain_route(request):
    print(f"🎯 PLAIN HANDLER: {request.method} {request.path}")
    auth_status = getattr(request, 'custom_data', {}).get('global_auth', 'not_found')
    return JSONResponse({
        "message": "plain route (no per-route middleware)",
        "global_auth_passed": auth_status,
        "path": request.path
    })

@app.get("/health")
def health_route(request):
    print(f"🎯 HEALTH HANDLER: {request.method} {request.path}")
    return JSONResponse({"status": "ok"})

if __name__ == "__main__":
    print("🌍 Global Middleware Test Server")
    print("================================")
    print(f"Registered global middlewares: {len(app._registered_middlewares)}")
    for mw in app._registered_middlewares:
        print(f"  - {mw['name']}: priority={mw['priority']}, pre_route={mw['pre_route']}, post_route={mw['post_route']}")

    print("\nTest routes:")
    print("  GET /test   - has per-route middleware")
    print("  GET /plain  - no per-route middleware")
    print("  GET /health - simple health check")

    print("\nExpected execution order for /test:")
    print("  1. 🌍 GLOBAL CORS (priority 100)")
    print("  2. 🌍 GLOBAL AUTH (priority 200)")
    print("  3. 🎯 ROUTE AUTH (per-route)")
    print("  4. 🎯 ROUTE LOG (per-route)")
    print("  5. 🎯 HANDLER")
    print("  6. 🌍 GLOBAL RESPONSE (post-route)")

    print("\nExpected execution order for /plain:")
    print("  1. 🌍 GLOBAL CORS (priority 100)")
    print("  2. 🌍 GLOBAL AUTH (priority 200)")
    print("  3. 🎯 PLAIN HANDLER")
    print("  4. 🌍 GLOBAL RESPONSE (post-route)")

    print("\nStarting server on http://127.0.0.1:8899")
    print("Test with:")
    print("  curl http://127.0.0.1:8899/test")
    print("  curl http://127.0.0.1:8899/plain")
    print("  curl http://127.0.0.1:8899/health")
    print("\nPress Ctrl+C to stop")

    try:
        app.listen(host="127.0.0.1", port=8899)
    except KeyboardInterrupt:
        print("\n\nServer stopped by user")
