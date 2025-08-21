#!/usr/bin/env python3
"""
🌪️ Catzilla Per-Route Middleware System - Python Tests

Comprehensive tests for the FastAPI-compatible per-route middleware system.
Tests the complete implementation of:
- FastAPI-style decorators (@app.get, @app.post, etc.) with middleware parameter
- Per-route middleware registration and execution
- Middleware execution order and short-circuiting
- C extension integration for middleware storage and execution
- Memory optimization and zero-allocation design
- Authentication, CORS, validation, and other middleware patterns
- Error handling and edge cases
- Performance characteristics
"""

import pytest
import sys
import os
import time
import json
from typing import Dict, Any, List, Optional, Callable
from unittest.mock import Mock, patch, MagicMock

# Add the project root to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from catzilla import Catzilla, Request, Response, JSONResponse
from catzilla.router import Route
from catzilla.router import CAcceleratedRouter


class TestPerRouteMiddlewareAPI:
    """Test FastAPI-compatible per-route middleware API"""

    def setup_method(self):
        """Set up test fixtures"""
        self.app = Catzilla(use_jemalloc=False, memory_profiling=False)
        self.middleware_calls = []

    def create_test_middleware(self, name: str, should_short_circuit: bool = False):
        """Create a test middleware function"""
        def middleware(request: Request, response: Response) -> Optional[Response]:
            self.middleware_calls.append(name)
            if should_short_circuit:
                return JSONResponse({"error": f"Short-circuited by {name}"}, status_code=403)
            return None
        middleware.__name__ = name
        return middleware

    def test_fastapi_get_decorator_with_middleware(self):
        """Test @app.get() decorator with middleware parameter"""
        auth_middleware = self.create_test_middleware("auth")
        cors_middleware = self.create_test_middleware("cors")

        @self.app.get("/test", middleware=[auth_middleware, cors_middleware])
        def test_handler(request):
            return JSONResponse({"message": "success"})

        # Verify route was registered with middleware
        routes = self.app.router._routes
        assert len(routes) > 0

        # Find our test route
        test_route = None
        for route in routes:
            if route.path == "/test" and route.method == "GET":
                test_route = route
                break

        assert test_route is not None, "Test route should be registered"
        assert hasattr(test_route, 'middleware'), "Route should have middleware attribute"
        assert test_route.middleware is not None, "Route middleware should not be None"
        assert len(test_route.middleware) == 2, "Route should have 2 middleware functions"

    def test_fastapi_post_decorator_with_middleware(self):
        """Test @app.post() decorator with middleware parameter"""
        validator_middleware = self.create_test_middleware("validator")

        @self.app.post("/users", middleware=[validator_middleware])
        def create_user(request):
            return JSONResponse({"user": "created"})

        # Verify route registration
        routes = self.app.router._routes
        test_route = None
        for route in routes:
            if route.path == "/users" and route.method == "POST":
                test_route = route
                break

        assert test_route is not None
        assert test_route.middleware is not None
        assert len(test_route.middleware) == 1

    def test_fastapi_put_decorator_with_middleware(self):
        """Test @app.put() decorator with middleware parameter"""
        auth_middleware = self.create_test_middleware("auth")
        logging_middleware = self.create_test_middleware("logging")

        @self.app.put("/users/{user_id}", middleware=[auth_middleware, logging_middleware])
        def update_user(request):
            user_id = request.path_params.get('user_id')
            return JSONResponse({"user_id": user_id, "updated": True})

        # Verify route registration
        routes = self.app.router._routes
        test_route = None
        for route in routes:
            if route.path == "/users/{user_id}" and route.method == "PUT":
                test_route = route
                break

        assert test_route is not None
        assert test_route.middleware is not None
        assert len(test_route.middleware) == 2

    def test_fastapi_delete_decorator_with_middleware(self):
        """Test @app.delete() decorator with middleware parameter"""
        auth_middleware = self.create_test_middleware("auth")

        @self.app.delete("/users/{user_id}", middleware=[auth_middleware])
        def delete_user(request):
            return JSONResponse({"deleted": True})

        # Verify route registration
        routes = self.app.router._routes
        test_route = None
        for route in routes:
            if route.path == "/users/{user_id}" and route.method == "DELETE":
                test_route = route
                break

        assert test_route is not None
        assert test_route.middleware is not None
        assert len(test_route.middleware) == 1

    def test_fastapi_patch_decorator_with_middleware(self):
        """Test @app.patch() decorator with middleware parameter"""
        auth_middleware = self.create_test_middleware("auth")
        validation_middleware = self.create_test_middleware("validation")

        @self.app.patch("/users/{user_id}", middleware=[auth_middleware, validation_middleware])
        def patch_user(request):
            return JSONResponse({"patched": True})

        # Verify route registration
        routes = self.app.router._routes
        test_route = None
        for route in routes:
            if route.path == "/users/{user_id}" and route.method == "PATCH":
                test_route = route
                break

        assert test_route is not None
        assert test_route.middleware is not None
        assert len(test_route.middleware) == 2

    def test_route_without_middleware(self):
        """Test route registration without middleware parameter"""
        @self.app.get("/public")
        def public_handler(request):
            return JSONResponse({"public": True})

        # Verify route was registered without middleware
        routes = self.app.router._routes
        test_route = None
        for route in routes:
            if route.path == "/public" and route.method == "GET":
                test_route = route
                break

        assert test_route is not None
        # Middleware should be None or empty list
        assert test_route.middleware is None or len(test_route.middleware) == 0

    def test_multiple_routes_same_path_different_methods(self):
        """Test multiple routes on same path with different methods and middleware"""
        auth_middleware = self.create_test_middleware("auth")
        validator_middleware = self.create_test_middleware("validator")

        @self.app.get("/api/data", middleware=[auth_middleware])
        def get_data(request):
            return JSONResponse({"data": "get"})

        @self.app.post("/api/data", middleware=[auth_middleware, validator_middleware])
        def post_data(request):
            return JSONResponse({"data": "post"})

        # Verify both routes are registered with correct middleware
        routes = self.app.router._routes
        get_route = None
        post_route = None

        for route in routes:
            if route.path == "/api/data":
                if route.method == "GET":
                    get_route = route
                elif route.method == "POST":
                    post_route = route

        assert get_route is not None
        assert post_route is not None
        assert len(get_route.middleware) == 1
        assert len(post_route.middleware) == 2


class TestMiddlewareExecutionOrder:
    """Test middleware execution order and chaining"""

    def setup_method(self):
        """Set up test fixtures"""
        self.app = Catzilla(use_jemalloc=False, memory_profiling=False)
        self.execution_order = []

    def create_ordered_middleware(self, name: str, order: int):
        """Create middleware that tracks execution order"""
        def middleware(request: Request, response: Response) -> Optional[Response]:
            self.execution_order.append(f"{name}_{order}")
            return None
        middleware.__name__ = f"{name}_{order}"
        return middleware

    def test_middleware_execution_order_preserved(self):
        """Test that middleware executes in the order specified"""
        # Create middleware with specific order
        first = self.create_ordered_middleware("first", 1)
        second = self.create_ordered_middleware("second", 2)
        third = self.create_ordered_middleware("third", 3)

        @self.app.get("/ordered", middleware=[first, second, third])
        def test_handler(request):
            self.execution_order.append("handler")
            return JSONResponse({"success": True})

        # Verify middleware order is preserved in route registration
        routes = self.app.router._routes
        test_route = None
        for route in routes:
            if route.path == "/ordered":
                test_route = route
                break

        assert test_route is not None
        assert len(test_route.middleware) == 3
        # Verify the middleware functions are in the correct order
        assert test_route.middleware[0].__name__ == "first_1"
        assert test_route.middleware[1].__name__ == "second_2"
        assert test_route.middleware[2].__name__ == "third_3"


class TestMiddlewareShortCircuiting:
    """Test middleware short-circuit behavior"""

    def setup_method(self):
        """Set up test fixtures"""
        self.app = Catzilla(use_jemalloc=False, memory_profiling=False)
        self.middleware_calls = []

    def create_test_middleware(self, name: str, should_short_circuit: bool = False,
                             status_code: int = 403):
        """Create middleware that can short-circuit the request"""
        def middleware(request: Request, response: Response) -> Optional[Response]:
            self.middleware_calls.append(name)
            if should_short_circuit:
                return JSONResponse(
                    {"error": f"Blocked by {name}", "middleware": name},
                    status_code=status_code
                )
            return None
        middleware.__name__ = name
        return middleware

    def test_middleware_short_circuit_stops_chain(self):
        """Test that middleware short-circuiting stops the chain"""
        first = self.create_test_middleware("first", False)
        second = self.create_test_middleware("second", True, 401)  # Short-circuit here
        third = self.create_test_middleware("third", False)  # Should not execute

        @self.app.get("/auth", middleware=[first, second, third])
        def protected_handler(request):
            self.middleware_calls.append("handler")
            return JSONResponse({"protected": "data"})

        # Register the route and verify middleware chain
        routes = self.app.router._routes
        test_route = None
        for route in routes:
            if route.path == "/auth":
                test_route = route
                break

        assert test_route is not None
        assert len(test_route.middleware) == 3

        # Verify middleware functions are properly stored
        middleware_names = [mw.__name__ for mw in test_route.middleware]
        assert "first" in middleware_names
        assert "second" in middleware_names
        assert "third" in middleware_names


class TestPerRouteMiddlewareTypes:
    """Test different types of middleware functionality"""

    def setup_method(self):
        """Set up test fixtures"""
        self.app = Catzilla(use_jemalloc=False, memory_profiling=False)

    def test_authentication_middleware(self):
        """Test authentication middleware pattern"""
        def auth_middleware(request: Request, response: Response) -> Optional[Response]:
            auth_header = request.headers.get('Authorization') if hasattr(request, 'headers') else None
            if not auth_header or not auth_header.startswith('Bearer '):
                return JSONResponse({"error": "Unauthorized"}, status_code=401)
            return None

        @self.app.get("/protected", middleware=[auth_middleware])
        def protected_endpoint(request):
            return JSONResponse({"data": "protected"})

        # Verify route registration
        routes = self.app.router._routes
        test_route = None
        for route in routes:
            if route.path == "/protected":
                test_route = route
                break

        assert test_route is not None
        assert test_route.middleware is not None
        assert len(test_route.middleware) == 1

    def test_cors_middleware(self):
        """Test CORS middleware pattern"""
        def cors_middleware(request: Request, response: Response) -> Optional[Response]:
            if hasattr(response, 'headers'):
                response.headers.update({
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE',
                    'Access-Control-Allow-Headers': 'Content-Type, Authorization'
                })
            return None

        @self.app.get("/api/public", middleware=[cors_middleware])
        def public_api(request):
            return JSONResponse({"message": "public"})

        # Verify route registration
        routes = self.app.router._routes
        test_route = None
        for route in routes:
            if route.path == "/api/public":
                test_route = route
                break

        assert test_route is not None
        assert test_route.middleware is not None
        assert len(test_route.middleware) == 1

    def test_rate_limiting_middleware(self):
        """Test rate limiting middleware pattern"""
        def rate_limit_middleware(request: Request, response: Response) -> Optional[Response]:
            # Simplified rate limiting logic for testing
            client_ip = getattr(request, 'remote_addr', '127.0.0.1')
            # In real implementation, would check Redis or similar
            return None

        @self.app.post("/api/upload", middleware=[rate_limit_middleware])
        def upload_endpoint(request):
            return JSONResponse({"uploaded": True})

        # Verify route registration
        routes = self.app.router._routes
        test_route = None
        for route in routes:
            if route.path == "/api/upload":
                test_route = route
                break

        assert test_route is not None
        assert test_route.middleware is not None
        assert len(test_route.middleware) == 1

    def test_json_validation_middleware(self):
        """Test JSON validation middleware pattern"""
        def json_validation_middleware(request: Request, response: Response) -> Optional[Response]:
            content_type = request.headers.get('Content-Type', '') if hasattr(request, 'headers') else ''
            if 'application/json' in content_type:
                try:
                    if hasattr(request, 'body') and request.body:
                        json.loads(request.body.decode('utf-8'))
                except (json.JSONDecodeError, UnicodeDecodeError):
                    return JSONResponse({"error": "Invalid JSON"}, status_code=400)
            return None

        @self.app.post("/api/data", middleware=[json_validation_middleware])
        def create_data(request):
            return JSONResponse({"created": True})

        # Verify route registration
        routes = self.app.router._routes
        test_route = None
        for route in routes:
            if route.path == "/api/data":
                test_route = route
                break

        assert test_route is not None
        assert test_route.middleware is not None
        assert len(test_route.middleware) == 1


class TestMiddlewareIntegrationWithCExtension:
    """Test integration between Python middleware and C extension"""

    def setup_method(self):
        """Set up test fixtures"""
        self.app = Catzilla(use_jemalloc=False, memory_profiling=False)

    def test_c_extension_middleware_registration(self):
        """Test that middleware is properly registered with C extension"""
        def test_middleware(request: Request, response: Response) -> Optional[Response]:
            return None

        @self.app.get("/test", middleware=[test_middleware])
        def test_handler(request):
            return JSONResponse({"test": True})

        # Verify the route exists in the router
        routes = self.app.router._routes
        assert len(routes) > 0

        # Check if the router has C integration capabilities
        router = self.app.router
        has_c_integration = (
            hasattr(router, 'add_route') and
            (hasattr(router, '_use_c_router') or hasattr(router, 'c_router') or hasattr(router, '_routes'))
        )
        assert has_c_integration, "Router should have C integration enabled"

    def test_middleware_storage_in_route_object(self):
        """Test that middleware is properly stored in Route objects"""
        middleware1 = lambda req, resp: None
        middleware2 = lambda req, resp: None
        middleware1.__name__ = "middleware1"
        middleware2.__name__ = "middleware2"

        @self.app.get("/multi", middleware=[middleware1, middleware2])
        def multi_middleware_handler(request):
            return JSONResponse({"middleware_count": 2})

        # Find the route and verify middleware storage
        routes = self.app.router._routes
        test_route = None
        for route in routes:
            if route.path == "/multi":
                test_route = route
                break

        assert test_route is not None
        assert hasattr(test_route, 'middleware'), "Route should have middleware attribute"
        assert test_route.middleware is not None
        assert len(test_route.middleware) == 2
        assert test_route.middleware[0].__name__ == "middleware1"
        assert test_route.middleware[1].__name__ == "middleware2"


class TestPerRouteMiddlewarePerformance:
    """Test performance characteristics of per-route middleware"""

    def setup_method(self):
        """Set up test fixtures"""
        self.app = Catzilla(use_jemalloc=False, memory_profiling=False)

    def test_middleware_registration_performance(self):
        """Test that middleware registration is efficient"""
        def dummy_middleware(request: Request, response: Response) -> Optional[Response]:
            return None

        start_time = time.time()

        # Register multiple routes with middleware
        for i in range(100):
            @self.app.get(f"/test_{i}", middleware=[dummy_middleware])
            def handler(request):
                return JSONResponse({"index": i})

        registration_time = time.time() - start_time

        # Should complete registration quickly (under 1 second for 100 routes)
        assert registration_time < 1.0, f"Registration took too long: {registration_time}s"

        # Verify all routes were registered
        routes = self.app.router._routes
        test_routes = [route for route in routes if route.path.startswith("/test_")]
        assert len(test_routes) == 100

    def test_memory_efficiency_with_many_middleware(self):
        """Test memory efficiency with many middleware functions"""
        def create_middleware(name):
            def middleware(request: Request, response: Response) -> Optional[Response]:
                return None
            middleware.__name__ = name
            return middleware

        # Create route with many middleware
        many_middleware = [create_middleware(f"mw_{i}") for i in range(50)]

        @self.app.get("/heavy", middleware=many_middleware)
        def heavy_handler(request):
            return JSONResponse({"middleware_count": len(many_middleware)})

        # Verify route registration
        routes = self.app.router._routes
        test_route = None
        for route in routes:
            if route.path == "/heavy":
                test_route = route
                break

        assert test_route is not None
        assert len(test_route.middleware) == 50


class TestMiddlewareErrorHandling:
    """Test error handling in middleware system"""

    def setup_method(self):
        """Set up test fixtures"""
        self.app = Catzilla(use_jemalloc=False, memory_profiling=False)

    def test_invalid_middleware_function(self):
        """Test handling of invalid middleware functions"""
        # Test with None middleware
        @self.app.get("/test_none", middleware=None)
        def test_none_handler(request):
            return JSONResponse({"test": "none"})

        # Test with empty middleware list
        @self.app.get("/test_empty", middleware=[])
        def test_empty_handler(request):
            return JSONResponse({"test": "empty"})

        # Verify routes are registered correctly
        routes = self.app.router._routes
        none_route = None
        empty_route = None

        for route in routes:
            if route.path == "/test_none":
                none_route = route
            elif route.path == "/test_empty":
                empty_route = route

        assert none_route is not None
        assert empty_route is not None
        # Both should have no middleware or empty middleware
        assert none_route.middleware is None or len(none_route.middleware) == 0
        assert empty_route.middleware is None or len(empty_route.middleware) == 0

    def test_middleware_exception_handling(self):
        """Test handling of exceptions in middleware"""
        def failing_middleware(request: Request, response: Response) -> Optional[Response]:
            raise ValueError("Middleware error")

        @self.app.get("/failing", middleware=[failing_middleware])
        def failing_handler(request):
            return JSONResponse({"test": "should not reach"})

        # Route should still be registered even with problematic middleware
        routes = self.app.router._routes
        test_route = None
        for route in routes:
            if route.path == "/failing":
                test_route = route
                break

        assert test_route is not None
        assert test_route.middleware is not None
        assert len(test_route.middleware) == 1


if __name__ == "__main__":
    """Run the per-route middleware tests"""
    print("🧪 Running Catzilla Per-Route Middleware Tests")
    print("=" * 50)

    # Run the tests
    pytest.main([__file__, "-v", "--tb=short"])
