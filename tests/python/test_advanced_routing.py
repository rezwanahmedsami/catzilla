"""
Advanced routing tests for Catzilla framework

Tests the new dynamic routing system with path parameters,
route conflict detection, 405/415 responses, and performance.
"""

import pytest
from unittest.mock import Mock
from catzilla import Catzilla, Request, Response, JSONResponse, BaseModel, Query, Path
from catzilla.router import Route, CAcceleratedRouter


class TestDynamicRouting:
    """Test dynamic path parameters and route matching"""

    def test_basic_dynamic_route(self):
        """Test basic dynamic route registration and matching"""
        router = CAcceleratedRouter()

        def handler(request):
            return {"user_id": request.path_params["user_id"]}

        router.add_route("GET", "/users/{user_id}", handler)

        # Test matching
        route, params, methods = router.match("GET", "/users/123")
        assert route is not None
        assert params == {"user_id": "123"}
        assert route.handler == handler

    def test_multiple_path_parameters(self):
        """Test routes with multiple path parameters"""
        router = CAcceleratedRouter()

        def handler(request):
            return {
                "user_id": request.path_params["user_id"],
                "post_id": request.path_params["post_id"]
            }

        router.add_route("GET", "/users/{user_id}/posts/{post_id}", handler)

        route, params, methods = router.match("GET", "/users/456/posts/789")
        assert route is not None
        assert params == {"user_id": "456", "post_id": "789"}

    def test_mixed_static_dynamic_segments(self):
        """Test routes mixing static and dynamic segments"""
        router = CAcceleratedRouter()

        def handler1(request):
            return {"type": "static"}

        def handler2(request):
            return {"user_id": request.path_params["user_id"]}

        router.add_route("GET", "/api/v1/users", handler1)
        router.add_route("GET", "/api/v1/users/{user_id}", handler2)

        # Test static route
        route, params, methods = router.match("GET", "/api/v1/users")
        assert route is not None
        assert route.handler == handler1
        assert params == {}

        # Test dynamic route
        route, params, methods = router.match("GET", "/api/v1/users/123")
        assert route is not None
        assert route.handler == handler2
        assert params == {"user_id": "123"}

    def test_route_not_found(self):
        """Test behavior when route is not found"""
        router = CAcceleratedRouter()

        def handler(request):
            return {"message": "hello"}

        router.add_route("GET", "/hello", handler)

        # Non-existent route
        route, params, methods = router.match("GET", "/goodbye")
        assert route is None
        assert params == {}
        assert methods is None

    def test_method_not_allowed(self):
        """Test 405 Method Not Allowed detection"""
        router = CAcceleratedRouter()

        def handler(request):
            return {"message": "hello"}

        router.add_route("GET", "/hello", handler)
        router.add_route("POST", "/hello", handler)

        # Wrong method for existing path
        route, params, methods = router.match("PUT", "/hello")
        assert route is None
        assert params == {}
        # HEAD is automatically supported for GET routes
        assert methods == {"GET", "HEAD", "POST"}

    def test_parameter_extraction_special_chars(self):
        """Test parameter extraction with special characters"""
        router = CAcceleratedRouter()

        def handler(request):
            return {"id": request.path_params["id"]}

        router.add_route("GET", "/items/{id}", handler)

        # Test with special characters (URL encoded values)
        route, params, methods = router.match("GET", "/items/abc-123_test")
        assert route is not None
        assert params == {"id": "abc-123_test"}


class TestRouteConflicts:
    """Test route conflict detection and warnings"""

    def test_route_conflict_warning(self):
        """Test that route conflicts generate warnings"""
        router = CAcceleratedRouter()

        def handler1(request):
            return {"type": "dynamic"}

        def handler2(request):
            return {"type": "static"}

        # Add dynamic route first
        router.add_route("GET", "/users/{user_id}", handler1)

        # Add potentially conflicting static route
        with pytest.warns(UserWarning, match="Route conflict"):
            router.add_route("GET", "/users/{user_id}", handler2, overwrite=False)

    def test_route_overwrite_allowed(self):
        """Test that overwrite=True suppresses warnings"""
        router = CAcceleratedRouter()

        def handler1(request):
            return {"version": 1}

        def handler2(request):
            return {"version": 2}

        router.add_route("GET", "/api", handler1)

        # Should not warn when overwrite=True
        router.add_route("GET", "/api", handler2, overwrite=True)

        # Verify the route was overwritten
        route, params, methods = router.match("GET", "/api")
        assert route.handler == handler2

    def test_complex_conflict_scenarios(self):
        """Test complex route conflict scenarios"""
        router = CAcceleratedRouter()

        def handler(request):
            return {}

        # These should potentially conflict
        router.add_route("GET", "/api/{version}/users", handler)
        router.add_route("GET", "/api/v1/users", handler)  # Specific case
        router.add_route("GET", "/api/{version}/posts", handler)

        # All should be accessible
        route1, params1, _ = router.match("GET", "/api/v2/users")
        route2, params2, _ = router.match("GET", "/api/v1/users")
        route3, params3, _ = router.match("GET", "/api/v1/posts")

        assert route1 is not None
        assert route2 is not None  # Should match specific route
        assert route3 is not None


class TestRouteIntrospection:
    """Test route introspection and debugging features"""

    def test_list_routes(self):
        """Test getting list of all registered routes"""
        router = CAcceleratedRouter()

        def handler1(request):
            return {}

        def handler2(request):
            return {}

        router.add_route("GET", "/", handler1)
        router.add_route("POST", "/api/data", handler2)
        router.add_route("GET", "/users/{id}", handler1)

        routes = router.routes()
        assert len(routes) == 3

        # Check route information
        routes_info = {(r["method"], r["path"]) for r in routes}
        expected = {
            ("GET", "/"),
            ("POST", "/api/data"),
            ("GET", "/users/{id}")
        }
        assert routes_info == expected

    def test_route_handler_names(self):
        """Test that handler names are correctly reported"""
        router = CAcceleratedRouter()

        def get_user(request):
            return {}

        def create_user(request):
            return {}

        router.add_route("GET", "/users/{id}", get_user)
        router.add_route("POST", "/users", create_user)

        routes = router.routes()
        handler_names = {r["handler_name"] for r in routes}
        assert "get_user" in handler_names
        assert "create_user" in handler_names


class TestRouteDecorators:
    """Test route decorator methods"""

    def test_http_method_decorators(self):
        """Test all HTTP method decorators"""
        router = CAcceleratedRouter()

        @router.get("/get")
        def get_handler(request):
            return {"method": "GET"}

        @router.post("/post")
        def post_handler(request):
            return {"method": "POST"}

        @router.put("/put")
        def put_handler(request):
            return {"method": "PUT"}

        @router.delete("/delete")
        def delete_handler(request):
            return {"method": "DELETE"}

        @router.patch("/patch")
        def patch_handler(request):
            return {"method": "PATCH"}

        # Test all routes are registered
        routes = router.routes()
        methods = {r["method"] for r in routes}
        assert methods == {"GET", "POST", "PUT", "DELETE", "PATCH"}

    def test_multi_method_decorator(self):
        """Test route decorator with multiple methods"""
        router = CAcceleratedRouter()

        @router.route("/api/data", ["GET", "POST"])
        def data_handler(request):
            return {"method": request.method}

        # Both methods should work
        get_route, _, _ = router.match("GET", "/api/data")
        post_route, _, _ = router.match("POST", "/api/data")

        assert get_route is not None
        assert post_route is not None
        assert get_route.handler == data_handler
        assert post_route.handler == data_handler


class TestAppIntegration:
    """Test integration with App class"""

    def test_app_dynamic_routing(self):
        """Test that Catzilla class supports dynamic routing with Memory Revolution"""
        app = Catzilla(auto_validation=True, memory_profiling=False)

        @app.get("/users/{user_id}")
        def get_user(request):
            user_id = request.path_params.get("user_id")
            return JSONResponse({"user_id": user_id})

        @app.post("/users/{user_id}/posts")
        def create_post(request):
            user_id = request.path_params.get("user_id")
            return JSONResponse({"user_id": user_id, "action": "create_post"})

        # Check routes are registered
        routes = app.router.routes()
        assert len(routes) == 2

        paths = {r["path"] for r in routes}
        assert "/users/{user_id}" in paths
        assert "/users/{user_id}/posts" in paths

    def test_app_route_conflicts_detected(self):
        """Test that Catzilla detects route conflicts with auto-validation"""
        app = Catzilla(auto_validation=True)

        @app.get("/api/{version}")
        def api_version(request):
            return {}

        # This should warn about potential conflict
        with pytest.warns(UserWarning):
            @app.get("/api/{version}")
            def api_version_duplicate(request):
                return {}


class TestErrorHandling:
    """Test error handling and edge cases"""

    def test_invalid_route_patterns(self):
        """Test handling of invalid route patterns"""
        router = CAcceleratedRouter()

        def handler(request):
            return {}

        # These should work fine
        router.add_route("GET", "/valid/{param}", handler)
        router.add_route("GET", "/also/valid/{param}/more", handler)

        # Test malformed parameters (should still work, treated as literal)
        router.add_route("GET", "/malformed/{param", handler)  # Missing closing brace
        router.add_route("GET", "/malformed/param}", handler)  # Missing opening brace

    def test_empty_and_root_routes(self):
        """Test edge cases with empty and root routes"""
        router = CAcceleratedRouter()

        def root_handler(request):
            return {"path": "root"}

        def empty_handler(request):
            return {"path": "empty"}

        router.add_route("GET", "/", root_handler)

        # Test root path matching
        route, params, methods = router.match("GET", "/")
        assert route is not None
        assert route.handler == root_handler
        assert params == {}

    def test_case_sensitivity(self):
        """Test case sensitivity in routes"""
        router = CAcceleratedRouter()

        def handler(request):
            return {}

        router.add_route("GET", "/CamelCase/{Id}", handler)

        # Exact match should work
        route, params, methods = router.match("GET", "/CamelCase/123")
        assert route is not None
        assert params == {"Id": "123"}

        # Different case should not match (case sensitive)
        route, params, methods = router.match("GET", "/camelcase/123")
        assert route is None

    def test_method_case_insensitivity(self):
        """Test that HTTP methods are case insensitive"""
        router = CAcceleratedRouter()

        def handler(request):
            return {}

        router.add_route("get", "/test", handler)  # lowercase

        # Should match regardless of case
        route, params, methods = router.match("GET", "/test")
        assert route is not None

        route, params, methods = router.match("get", "/test")
        assert route is not None

        route, params, methods = router.match("Get", "/test")
        assert route is not None


class TestPerformance:
    """Test routing performance with many routes"""

    def test_many_static_routes(self):
        """Test performance with many static routes"""
        router = CAcceleratedRouter()

        def handler(request):
            return {}

        # Add many static routes
        for i in range(100):
            router.add_route("GET", f"/route_{i}", handler)

        # Test that all can be found efficiently
        for i in range(100):
            route, params, methods = router.match("GET", f"/route_{i}")
            assert route is not None

    def test_many_dynamic_routes(self):
        """Test performance with many dynamic routes"""
        router = CAcceleratedRouter()

        def handler(request):
            return {}

        # Add many dynamic routes
        for i in range(50):
            router.add_route("GET", f"/api/v{i}/users/{{user_id}}/data", handler)

        # Test that all can be found efficiently
        for i in range(50):
            route, params, methods = router.match("GET", f"/api/v{i}/users/123/data")
            assert route is not None
            assert params == {"user_id": "123"}

    def test_deep_nesting(self):
        """Test performance with deeply nested routes"""
        router = CAcceleratedRouter()

        def handler(request):
            return {}

        # Create deeply nested route
        path = "/api/v1/users/{user_id}/posts/{post_id}/comments/{comment_id}/replies/{reply_id}"
        router.add_route("GET", path, handler)

        # Test matching
        test_path = "/api/v1/users/123/posts/456/comments/789/replies/101112"
        route, params, methods = router.match("GET", test_path)

        assert route is not None
        assert len(params) == 4
        assert params["user_id"] == "123"
        assert params["post_id"] == "456"
        assert params["comment_id"] == "789"
        assert params["reply_id"] == "101112"
