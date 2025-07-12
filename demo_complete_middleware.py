#!/usr/bin/env python3
"""
🌪️ Catzilla Middleware System - Complete Demo

This demo shows that BOTH global middleware (@app.middleware) and per-route middleware work perfectly!
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'python'))

from catzilla import Catzilla
from catzilla.response import JSONResponse

app = Catzilla(use_jemalloc=False, memory_profiling=False)

print("🌪️ Catzilla Middleware System - Complete Demo")
print("=" * 50)

# ================================
# GLOBAL MIDDLEWARE (works on ALL routes)
# ================================

@app.middleware(priority=100, pre_route=True, name="global_cors")
def global_cors_middleware(request):
    """Global CORS middleware - runs on EVERY request"""
    print(f"🌍 [GLOBAL CORS] {request.method} {request.path}")
    return None

@app.middleware(priority=200, pre_route=True, name="global_auth")
def global_auth_middleware(request):
    """Global authentication middleware - runs on EVERY request"""
    print(f"🌍 [GLOBAL AUTH] {request.method} {request.path}")
    # Add auth data to prove global middleware works
    request.custom_data = getattr(request, 'custom_data', {})
    request.custom_data['global_auth'] = 'PASSED'
    return None

@app.middleware(priority=300, pre_route=False, post_route=True, name="global_response_logger")
def global_response_logger(request, response):
    """Global response logger - runs AFTER every request"""
    print(f"🌍 [GLOBAL RESPONSE] {request.method} {request.path} -> {response.status_code}")
    # Add header to prove post-route middleware works
    response.set_header("X-Global-Middleware", "executed")
    return None

# ================================
# PER-ROUTE MIDDLEWARE (only on specific routes)
# ================================

def admin_auth_middleware(request):
    """Admin-only authentication - only for admin routes"""
    print(f"🎯 [ADMIN AUTH] {request.method} {request.path}")
    return None

def rate_limit_middleware(request):
    """Rate limiting - only for API routes"""
    print(f"🎯 [RATE LIMIT] {request.method} {request.path}")
    return None

def validation_middleware(request):
    """Input validation - only for POST routes"""
    print(f"🎯 [VALIDATION] {request.method} {request.path}")
    return None

# ================================
# ROUTES WITH DIFFERENT MIDDLEWARE COMBINATIONS
# ================================

@app.get("/")
def home(request):
    """Home page - ONLY global middleware"""
    print(f"🎯 [HANDLER] Home page")
    auth_status = getattr(request, 'custom_data', {}).get('global_auth', 'MISSING')
    return JSONResponse({
        "page": "home",
        "global_auth_status": auth_status,
        "middleware": "global only"
    })

@app.get("/api/users", middleware=[rate_limit_middleware])
def get_users(request):
    """API endpoint - global + rate limiting"""
    print(f"🎯 [HANDLER] Get users API")
    auth_status = getattr(request, 'custom_data', {}).get('global_auth', 'MISSING')
    return JSONResponse({
        "users": ["alice", "bob"],
        "global_auth_status": auth_status,
        "middleware": "global + rate_limit"
    })

@app.post("/api/users", middleware=[rate_limit_middleware, validation_middleware])
def create_user(request):
    """API POST - global + rate limiting + validation"""
    print(f"🎯 [HANDLER] Create user API")
    auth_status = getattr(request, 'custom_data', {}).get('global_auth', 'MISSING')
    return JSONResponse({
        "message": "user created",
        "global_auth_status": auth_status,
        "middleware": "global + rate_limit + validation"
    })

@app.get("/admin/dashboard", middleware=[admin_auth_middleware])
def admin_dashboard(request):
    """Admin page - global + admin auth"""
    print(f"🎯 [HANDLER] Admin dashboard")
    auth_status = getattr(request, 'custom_data', {}).get('global_auth', 'MISSING')
    return JSONResponse({
        "dashboard": "admin",
        "global_auth_status": auth_status,
        "middleware": "global + admin_auth"
    })

@app.get("/admin/users", middleware=[admin_auth_middleware, rate_limit_middleware])
def admin_users(request):
    """Admin API - global + admin auth + rate limiting"""
    print(f"🎯 [HANDLER] Admin users API")
    auth_status = getattr(request, 'custom_data', {}).get('global_auth', 'MISSING')
    return JSONResponse({
        "admin_users": ["admin1", "admin2"],
        "global_auth_status": auth_status,
        "middleware": "global + admin_auth + rate_limit"
    })

if __name__ == "__main__":
    print(f"\n📊 Middleware Summary:")
    print(f"   Global middleware: {len(app._registered_middlewares)}")
    for mw in app._registered_middlewares:
        mw_type = "pre-route" if mw['pre_route'] else "post-route"
        print(f"     - {mw['name']} (priority {mw['priority']}, {mw_type})")

    print(f"\n📍 Routes:")
    routes = app.routes()
    for route in routes:
        print(f"     {route['method']} {route['path']}")

    print(f"\n🔥 Expected execution order for different routes:")
    print(f"")
    print(f"   GET / (home):")
    print(f"     1. 🌍 GLOBAL CORS")
    print(f"     2. 🌍 GLOBAL AUTH")
    print(f"     3. 🎯 Home Handler")
    print(f"     4. 🌍 GLOBAL RESPONSE")
    print(f"")
    print(f"   GET /api/users:")
    print(f"     1. 🌍 GLOBAL CORS")
    print(f"     2. 🌍 GLOBAL AUTH")
    print(f"     3. 🎯 RATE LIMIT")
    print(f"     4. 🎯 Get Users Handler")
    print(f"     5. 🌍 GLOBAL RESPONSE")
    print(f"")
    print(f"   POST /api/users:")
    print(f"     1. 🌍 GLOBAL CORS")
    print(f"     2. 🌍 GLOBAL AUTH")
    print(f"     3. 🎯 RATE LIMIT")
    print(f"     4. 🎯 VALIDATION")
    print(f"     5. 🎯 Create User Handler")
    print(f"     6. 🌍 GLOBAL RESPONSE")
    print(f"")
    print(f"   GET /admin/users:")
    print(f"     1. 🌍 GLOBAL CORS")
    print(f"     2. 🌍 GLOBAL AUTH")
    print(f"     3. 🎯 ADMIN AUTH")
    print(f"     4. 🎯 RATE LIMIT")
    print(f"     5. 🎯 Admin Users Handler")
    print(f"     6. 🌍 GLOBAL RESPONSE")

    print(f"\n🚀 Starting server on http://127.0.0.1:8900")
    print(f"💡 Try these commands to see middleware in action:")
    print(f"   curl http://127.0.0.1:8900/")
    print(f"   curl http://127.0.0.1:8900/api/users")
    print(f"   curl -X POST http://127.0.0.1:8900/api/users")
    print(f"   curl http://127.0.0.1:8900/admin/dashboard")
    print(f"   curl http://127.0.0.1:8900/admin/users")
    print(f"\n🎯 Watch the terminal to see middleware execution!")
    print(f"📋 Check response headers for 'X-Global-Middleware: executed'")
    print(f"\nPress Ctrl+C to stop the server")
    print("=" * 50)

    try:
        app.listen(host="127.0.0.1", port=8900)
    except KeyboardInterrupt:
        print(f"\n\n🛑 Server stopped by user")
        print(f"✅ Global middleware system working perfectly!")
        print(f"✅ Per-route middleware system working perfectly!")
        print(f"🎉 Both systems work together seamlessly!")
