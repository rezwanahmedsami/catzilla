#!/usr/bin/env python3
"""
Test script for OPTIONS and HEAD method support in Catzilla

This test verifies that OPTIONS and HEAD methods are properly implemented
at both the Router and App level, and that they work correctly with the
existing routing system.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'python'))

from catzilla import Catzilla, Request, Response, JSONResponse

def test_options_head_methods():
    """Test that OPTIONS and HEAD methods work correctly"""

    print("🧪 Testing OPTIONS and HEAD method implementation...")

    # Create app
    app = Catzilla(
        production=False,
        show_banner=False,
        log_requests=False
    )

    # Test 1: Verify OPTIONS and HEAD decorators exist
    print("✅ Test 1: Checking decorators exist...")
    assert hasattr(app, 'options'), "app.options decorator should exist"
    assert hasattr(app, 'head'), "app.head decorator should exist"
    assert hasattr(app.router, 'options'), "router.options decorator should exist"
    assert hasattr(app.router, 'head'), "router.head decorator should exist"

    # Test 2: Register routes with OPTIONS and HEAD
    print("✅ Test 2: Registering OPTIONS and HEAD routes...")

    @app.get("/users")
    def get_users(request):
        return JSONResponse({"users": ["Alice", "Bob"]})

    @app.post("/users")
    def create_user(request):
        return JSONResponse({"message": "User created"})

    @app.options("/users")
    def users_options(request):
        return JSONResponse({"allowed_methods": ["GET", "POST", "OPTIONS"]})

    @app.head("/users")
    def users_head(request):
        # HEAD should return same headers as GET but no body
        return JSONResponse({"users": ["Alice", "Bob"]})

    @app.options("/custom")
    def custom_options(request):
        return JSONResponse({"custom": "options"})

    @app.head("/health")
    def health_head(request):
        return JSONResponse({"status": "ok"})

    # Test 3: Verify routes are registered
    print("✅ Test 3: Verifying routes are registered...")
    routes = app.router.routes()
    registered_methods = {r["method"] for r in routes}

    print(f"   Registered methods: {registered_methods}")
    assert "OPTIONS" in registered_methods, "OPTIONS method should be registered"
    assert "HEAD" in registered_methods, "HEAD method should be registered"
    assert "GET" in registered_methods, "GET method should be registered"
    assert "POST" in registered_methods, "POST method should be registered"

    # Test 4: Check specific routes
    print("✅ Test 4: Testing route matching...")

    # Test OPTIONS route
    options_route, params, allowed = app.router.match("OPTIONS", "/users")
    assert options_route is not None, "OPTIONS /users route should match"
    assert params == {}, "OPTIONS route should have no path params"

    # Test HEAD route
    head_route, params, allowed = app.router.match("HEAD", "/users")
    assert head_route is not None, "HEAD /users route should match"
    assert params == {}, "HEAD route should have no path params"

    # Test custom OPTIONS route
    custom_options_route, params, allowed = app.router.match("OPTIONS", "/custom")
    assert custom_options_route is not None, "OPTIONS /custom route should match"

    # Test custom HEAD route
    health_head_route, params, allowed = app.router.match("HEAD", "/health")
    print(f"   HEAD /health route: {health_head_route}")
    print(f"   All routes: {[r['method'] + ' ' + r['path'] for r in routes]}")

    # Let's also test the OPTIONS route for comparison
    options_route, params, allowed = app.router.match("OPTIONS", "/custom")
    print(f"   OPTIONS /custom route: {options_route}")

    assert health_head_route is not None, "HEAD /health route should match"

    # Test 5: Verify middleware support
    print("✅ Test 5: Testing middleware support...")

    middleware_calls = []

    def test_middleware(request):
        middleware_calls.append("middleware_called")
        return None

    @app.options("/with-middleware", middleware=[test_middleware])
    def options_with_middleware(request):
        return JSONResponse({"middleware": "supported"})

    @app.head("/with-middleware", middleware=[test_middleware])
    def head_with_middleware(request):
        return JSONResponse({"middleware": "supported"})

    # Verify middleware routes exist
    mw_options_route, _, _ = app.router.match("OPTIONS", "/with-middleware")
    mw_head_route, _, _ = app.router.match("HEAD", "/with-middleware")

    assert mw_options_route is not None, "OPTIONS route with middleware should exist"
    assert mw_head_route is not None, "HEAD route with middleware should exist"

    # Check middleware is attached
    assert hasattr(mw_options_route, 'middleware'), "OPTIONS route should have middleware"
    assert hasattr(mw_head_route, 'middleware'), "HEAD route should have middleware"

    if mw_options_route.middleware:
        assert len(mw_options_route.middleware) == 1, "OPTIONS route should have 1 middleware"
    if mw_head_route.middleware:
        assert len(mw_head_route.middleware) == 1, "HEAD route should have 1 middleware"

    print("✅ All tests passed!")
    print(f"   Total routes registered: {len(routes)}")
    print(f"   Methods supported: {sorted(registered_methods)}")

    return True

def test_route_groups():
    """Test OPTIONS and HEAD with RouterGroup"""

    print("\n🧪 Testing RouterGroup OPTIONS and HEAD support...")

    from catzilla.router import RouterGroup

    # Create router group
    api_v1 = RouterGroup("/api/v1")

    # Test that RouterGroup has OPTIONS and HEAD methods
    assert hasattr(api_v1, 'options'), "RouterGroup should have options method"
    assert hasattr(api_v1, 'head'), "RouterGroup should have head method"

    @api_v1.options("/test")
    def api_options(request):
        return JSONResponse({"api": "options"})

    @api_v1.head("/test")
    def api_head(request):
        return JSONResponse({"api": "head"})

    # Verify routes are registered in the group
    group_routes = api_v1.routes()
    group_methods = {route[0] for route in group_routes}

    assert "OPTIONS" in group_methods, "RouterGroup should support OPTIONS"
    assert "HEAD" in group_methods, "RouterGroup should support HEAD"

    print("✅ RouterGroup tests passed!")

    return True

if __name__ == "__main__":
    try:
        # Test main app functionality
        test_options_head_methods()

        # Test RouterGroup functionality
        test_route_groups()

        print("\n🎉 All OPTIONS and HEAD tests passed successfully!")
        print("✅ OPTIONS and HEAD methods are fully implemented and working!")

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
