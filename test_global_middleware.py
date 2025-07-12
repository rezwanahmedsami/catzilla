#!/usr/bin/env python3
"""
Test global middleware functionality - simplified version
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'python'))

from catzilla import Catzilla
from catzilla.response import JSONResponse

def test_global_middleware_registration():
    """Test that global middleware is properly registered"""
    app = Catzilla(use_jemalloc=False, memory_profiling=False)

    # Register global pre-route middleware
    @app.middleware(priority=100, pre_route=True, name="global_auth")
    def global_auth_middleware(request):
        print(f"🌍 Global auth middleware would execute for {request.method} {request.path}")
        return None

    @app.middleware(priority=200, pre_route=True, name="global_logging")
    def global_logging_middleware(request):
        print(f"🌍 Global logging middleware would execute for {request.method} {request.path}")
        return None

    # Register global post-route middleware
    @app.middleware(priority=300, pre_route=False, post_route=True, name="global_response_logger")
    def global_response_middleware(request, response):
        print(f"🌍 Global response middleware would execute for {request.method} {request.path} -> {response.status_code}")
        return None

    print("\n=== Testing Global Middleware Registration ===")
    print(f"Registered global middlewares: {len(app._registered_middlewares)}")

    # Verify all middleware are registered
    if len(app._registered_middlewares) == 3:
        print("✅ Correct number of global middleware registered")
    else:
        print(f"❌ Expected 3 middleware, got {len(app._registered_middlewares)}")
        return False

    # Check middleware details
    middleware_names = [mw['name'] for mw in app._registered_middlewares]
    expected_names = ["global_auth", "global_logging", "global_response_logger"]

    for name in expected_names:
        if name in middleware_names:
            print(f"✅ Middleware '{name}' registered successfully")
        else:
            print(f"❌ Middleware '{name}' not found in registered middleware")
            return False

    # Check middleware configuration
    for mw in app._registered_middlewares:
        print(f"  - {mw['name']}: priority={mw['priority']}, pre_route={mw['pre_route']}, post_route={mw['post_route']}")

        # Verify priority and flags
        if mw['name'] == 'global_auth' and mw['priority'] == 100 and mw['pre_route'] == True:
            print(f"✅ '{mw['name']}' configuration correct")
        elif mw['name'] == 'global_logging' and mw['priority'] == 200 and mw['pre_route'] == True:
            print(f"✅ '{mw['name']}' configuration correct")
        elif mw['name'] == 'global_response_logger' and mw['priority'] == 300 and mw['post_route'] == True:
            print(f"✅ '{mw['name']}' configuration correct")
        else:
            print(f"❌ '{mw['name']}' configuration incorrect")
            return False

    print("\n=== Testing Middleware Filtering ===")

    # Test pre-route middleware filtering
    pre_route_middlewares = [
        mw for mw in app._registered_middlewares
        if mw.get('pre_route', True)
    ]

    if len(pre_route_middlewares) == 2:
        print(f"✅ Found {len(pre_route_middlewares)} pre-route middleware")
    else:
        print(f"❌ Expected 2 pre-route middleware, found {len(pre_route_middlewares)}")
        return False

    # Test post-route middleware filtering
    post_route_middlewares = [
        mw for mw in app._registered_middlewares
        if mw.get('post_route', False)
    ]

    if len(post_route_middlewares) == 1:
        print(f"✅ Found {len(post_route_middlewares)} post-route middleware")
    else:
        print(f"❌ Expected 1 post-route middleware, found {len(post_route_middlewares)}")
        return False

    print("\n=== Testing Priority Sorting ===")

    # Test priority sorting
    pre_route_middlewares.sort(key=lambda x: x.get('priority', 50))
    sorted_names = [mw['name'] for mw in pre_route_middlewares]
    expected_order = ['global_auth', 'global_logging']  # 100, 200

    if sorted_names == expected_order:
        print(f"✅ Pre-route middleware sorted correctly: {sorted_names}")
    else:
        print(f"❌ Pre-route middleware sorting incorrect. Expected {expected_order}, got {sorted_names}")
        return False

    print("\n✅ All global middleware tests PASSED!")
    print("🌍 Global middleware registration and configuration is working correctly")
    return True

def test_middleware_function_calls():
    """Test that middleware functions can be called directly"""
    app = Catzilla(use_jemalloc=False, memory_profiling=False)

    call_log = []

    @app.middleware(priority=100, pre_route=True, name="test_middleware")
    def test_middleware(request):
        call_log.append("middleware_called")
        return None

    print("\n=== Testing Direct Middleware Function Call ===")

    # Create a mock request object
    class MockRequest:
        def __init__(self):
            self.method = "GET"
            self.path = "/test"

    mock_request = MockRequest()

    # Get the middleware function and call it
    middleware_info = app._registered_middlewares[0]
    middleware_func = middleware_info['handler']

    result = middleware_func(mock_request)

    if "middleware_called" in call_log and result is None:
        print("✅ Middleware function called successfully")
        return True
    else:
        print("❌ Middleware function call failed")
        return False

if __name__ == "__main__":
    success1 = test_global_middleware_registration()
    success2 = test_middleware_function_calls()

    if success1 and success2:
        print("\n🎉 ALL TESTS PASSED! Global middleware system is working.")
    else:
        print("\n❌ Some tests failed. Check the output above.")
        sys.exit(1)
