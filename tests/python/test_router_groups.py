"""
Router Group tests for Catzilla framework

Tests the RouterGroup functionality for organizing routes
with shared prefixes, tags, and metadata.
"""

import pytest
from unittest.mock import Mock
from catzilla import App, Request, Response, JSONResponse, RouterGroup


class TestRouterGroup:
    """Test RouterGroup basic functionality"""

    def test_router_group_creation(self):
        """Test RouterGroup initialization"""
        group = RouterGroup()
        assert group.prefix == ""
        assert group.tags == []
        assert group.description == ""
        assert group.metadata == {}
        assert group.routes() == []

    def test_router_group_with_prefix(self):
        """Test RouterGroup with prefix"""
        group = RouterGroup("/api")
        assert group.prefix == "/api"

        # Test prefix normalization
        group2 = RouterGroup("api")
        assert group2.prefix == "/api"

        group3 = RouterGroup("/api/")
        assert group3.prefix == "/api"

        # Root prefix should remain empty
        group4 = RouterGroup("/")
        assert group4.prefix == ""

    def test_router_group_with_metadata(self):
        """Test RouterGroup with tags and metadata"""
        group = RouterGroup(
            "/api/v1",
            tags=["api", "v1"],
            description="API version 1",
            metadata={"version": "1.0.0"}
        )
        assert group.prefix == "/api/v1"
        assert group.tags == ["api", "v1"]
        assert group.description == "API version 1"
        assert group.metadata == {"version": "1.0.0"}

    def test_path_combination(self):
        """Test path combination with prefix"""
        group = RouterGroup("/api")

        # Test various path combinations
        assert group._combine_path("/users") == "/api/users"
        assert group._combine_path("users") == "/api/users"
        assert group._combine_path("/") == "/api"

        # Test with empty prefix
        empty_group = RouterGroup("")
        assert empty_group._combine_path("/users") == "/users"
        assert empty_group._combine_path("users") == "/users"

    def test_route_registration(self):
        """Test route registration in group"""
        group = RouterGroup("/api")

        @group.get("/users")
        def get_users(request):
            return JSONResponse({"users": []})

        @group.post("/users")
        def create_user(request):
            return JSONResponse({"user": "created"})

        routes = group.routes()
        assert len(routes) == 2

        # Check first route (GET)
        method1, path1, handler1, metadata1 = routes[0]
        assert method1 == "GET"
        assert path1 == "/api/users"
        assert handler1 == get_users
        assert metadata1["group_prefix"] == "/api"

        # Check second route (POST)
        method2, path2, handler2, metadata2 = routes[1]
        assert method2 == "POST"
        assert path2 == "/api/users"
        assert handler2 == create_user

    def test_all_http_methods(self):
        """Test all HTTP method decorators"""
        group = RouterGroup("/api")

        @group.get("/test")
        def get_handler(request):
            return {}

        @group.post("/test")
        def post_handler(request):
            return {}

        @group.put("/test")
        def put_handler(request):
            return {}

        @group.delete("/test")
        def delete_handler(request):
            return {}

        @group.patch("/test")
        def patch_handler(request):
            return {}

        routes = group.routes()
        assert len(routes) == 5

        methods = {route[0] for route in routes}
        assert methods == {"GET", "POST", "PUT", "DELETE", "PATCH"}

        # All should have the same path
        paths = {route[1] for route in routes}
        assert paths == {"/api/test"}

    def test_route_metadata_inheritance(self):
        """Test that routes inherit group metadata"""
        group = RouterGroup(
            "/api",
            tags=["api"],
            description="API routes",
            metadata={"api_version": "1.0"}
        )

        @group.get("/users", tags=["users"], description="Get all users")
        def get_users(request):
            return {}

        routes = group.routes()
        assert len(routes) == 1

        method, path, handler, metadata = routes[0]
        assert metadata["group_prefix"] == "/api"
        assert metadata["group_description"] == "API routes"
        assert metadata["tags"] == ["api", "users"]  # Combined tags
        assert metadata["description"] == "Get all users"
        assert metadata["api_version"] == "1.0"

    def test_multiple_routes_decorator(self):
        """Test route decorator with multiple methods"""
        group = RouterGroup("/api")

        @group.route("/test", methods=["GET", "POST"])
        def test_handler(request):
            return {}

        routes = group.routes()
        assert len(routes) == 2

        methods = {route[0] for route in routes}
        assert methods == {"GET", "POST"}


class TestRouterGroupNesting:
    """Test RouterGroup nesting and inclusion"""

    def test_group_include_group(self):
        """Test including one group in another"""
        users_group = RouterGroup("/users")

        @users_group.get("/")
        def list_users(request):
            return {}

        @users_group.get("/{user_id}")
        def get_user(request):
            return {}

        api_group = RouterGroup("/api")
        api_group.include_group(users_group)

        routes = api_group.routes()
        assert len(routes) == 2

        # Check that paths are properly combined
        paths = {route[1] for route in routes}
        assert "/api/" in paths
        assert "/api/{user_id}" in paths

    def test_deep_group_nesting(self):
        """Test deep nesting of groups"""
        resource_group = RouterGroup("/resource")

        @resource_group.get("/")
        def list_resources(request):
            return {}

        v1_group = RouterGroup("/v1")
        v1_group.include_group(resource_group)

        api_group = RouterGroup("/api")
        api_group.include_group(v1_group)

        routes = api_group.routes()
        assert len(routes) == 1

        method, path, handler, metadata = routes[0]
        assert path == "/api/"  # /api + /v1 + /resource + / with prefix handling
        assert metadata["original_group_prefix"] == "/v1/resource"
        assert metadata["included_in_group"] == "/api"


class TestAppIntegration:
    """Test RouterGroup integration with App"""

    def test_app_include_routes(self):
        """Test App.include_routes functionality"""
        app = App()

        # Create a router group
        api_group = RouterGroup("/api/v1", tags=["api", "v1"])

        @api_group.get("/users")
        def get_users(request):
            return JSONResponse({"users": []})

        @api_group.post("/users")
        def create_user(request):
            return JSONResponse({"message": "User created"})

        @api_group.get("/users/{user_id}")
        def get_user(request):
            user_id = request.path_params.get("user_id")
            return JSONResponse({"user_id": user_id})

        # Include the group routes in the app
        app.include_routes(api_group)

        # Check that routes are registered in the app
        routes = app.routes()
        assert len(routes) == 3

        # Check specific routes
        paths = {r["path"] for r in routes}
        assert "/api/v1/users" in paths
        assert "/api/v1/users/{user_id}" in paths

        methods = {r["method"] for r in routes}
        assert "GET" in methods
        assert "POST" in methods

    def test_app_multiple_groups(self):
        """Test including multiple RouterGroups in an App"""
        app = App()

        # Users group
        users_group = RouterGroup("/api/users", tags=["users"])

        @users_group.get("/")
        def list_users(request):
            return JSONResponse({"users": []})

        @users_group.post("/")
        def create_user(request):
            return JSONResponse({"user": "created"})

        # Posts group
        posts_group = RouterGroup("/api/posts", tags=["posts"])

        @posts_group.get("/")
        def list_posts(request):
            return JSONResponse({"posts": []})

        @posts_group.get("/{post_id}")
        def get_post(request):
            return JSONResponse({"post_id": request.path_params.get("post_id")})

        # Include both groups
        app.include_routes(users_group)
        app.include_routes(posts_group)

        routes = app.routes()
        assert len(routes) == 4

        paths = {r["path"] for r in routes}
        assert "/api/users/" in paths
        assert "/api/posts/" in paths
        assert "/api/posts/{post_id}" in paths

    def test_app_group_with_regular_routes(self):
        """Test mixing RouterGroup routes with regular app routes"""
        app = App()

        # Regular app route
        @app.get("/health")
        def health_check(request):
            return JSONResponse({"status": "ok"})

        # RouterGroup routes
        api_group = RouterGroup("/api")

        @api_group.get("/users")
        def get_users(request):
            return JSONResponse({"users": []})

        app.include_routes(api_group)

        routes = app.routes()
        assert len(routes) == 2

        paths = {r["path"] for r in routes}
        assert "/health" in paths
        assert "/api/users" in paths

    def test_group_conflict_detection(self):
        """Test that RouterGroup routes trigger conflict detection"""
        app = App()

        # First group
        group1 = RouterGroup("/api")

        @group1.get("/users")
        def get_users_v1(request):
            return JSONResponse({"version": "v1"})

        app.include_routes(group1)

        # Second group with conflicting route
        group2 = RouterGroup("/api")

        @group2.get("/users")
        def get_users_v2(request):
            return JSONResponse({"version": "v2"})

        # This should warn about route conflict
        with pytest.warns(RuntimeWarning):
            app.include_routes(group2)

    def test_empty_group_inclusion(self):
        """Test including an empty RouterGroup"""
        app = App()
        empty_group = RouterGroup("/api")

        # Should not raise any errors
        app.include_routes(empty_group)

        routes = app.routes()
        assert len(routes) == 0


class TestRouterGroupEdgeCases:
    """Test edge cases and error conditions"""

    def test_root_prefix_group(self):
        """Test RouterGroup with root prefix"""
        root_group = RouterGroup("/")

        @root_group.get("/test")
        def test_handler(request):
            return {}

        routes = root_group.routes()
        assert len(routes) == 1

        method, path, handler, metadata = routes[0]
        assert path == "/test"  # Should not double up slashes

    def test_complex_path_normalization(self):
        """Test complex path combinations and normalization"""
        group = RouterGroup("/api//v1/")  # Double slashes and trailing slash

        @group.get("//users//")
        def get_users(request):
            return {}

        routes = group.routes()
        method, path, handler, metadata = routes[0]
        # Should normalize to clean path
        assert "//" not in path
        assert path == "/api/v1/users"

    def test_group_with_dynamic_paths(self):
        """Test RouterGroup with dynamic path parameters"""
        group = RouterGroup("/api/v1")

        @group.get("/users/{user_id}")
        def get_user(request):
            return {"user_id": request.path_params.get("user_id")}

        @group.get("/users/{user_id}/posts/{post_id}")
        def get_user_post(request):
            return {
                "user_id": request.path_params.get("user_id"),
                "post_id": request.path_params.get("post_id")
            }

        routes = group.routes()
        assert len(routes) == 2

        paths = {route[1] for route in routes}
        assert "/api/v1/users/{user_id}" in paths
        assert "/api/v1/users/{user_id}/posts/{post_id}" in paths

    def test_group_overwrite_behavior(self):
        """Test overwrite behavior in RouterGroups"""
        group = RouterGroup("/api")

        @group.get("/test")
        def handler1(request):
            return {"version": 1}

        # Add another handler for the same route without overwrite
        @group.get("/test")
        def handler2(request):
            return {"version": 2}

        routes = group.routes()
        # Should have both routes registered (warning will be shown during app.include_routes)
        assert len(routes) == 2

        # Now with explicit overwrite
        @group.get("/test", overwrite=True)
        def handler3(request):
            return {"version": 3}

        routes = group.routes()
        assert len(routes) == 3

    def test_group_custom_metadata(self):
        """Test RouterGroup with custom metadata fields"""
        group = RouterGroup(
            "/api",
            custom_field="custom_value",
            middleware=["auth", "cors"],
            rate_limit=100
        )

        @group.get("/test", extra_field="test_value")
        def test_handler(request):
            return {}

        routes = group.routes()
        method, path, handler, metadata = routes[0]

        assert metadata["custom_field"] == "custom_value"
        assert metadata["middleware"] == ["auth", "cors"]
        assert metadata["rate_limit"] == 100
        assert metadata["extra_field"] == "test_value"
