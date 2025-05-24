"""
Ultra-fast C-accelerated router with minimal Python overhead

This router minimizes Python-C bridge overhead by:
1. Using direct C function calls without object creation
2. Caching route information in Python structures
3. Optimizing for the common case (successful matches)
4. Falling back to Python only when necessary
"""

import re
from typing import TYPE_CHECKING, Any, Callable, Dict, List, Optional, Set, Tuple, Union

if TYPE_CHECKING:
    from .routing import Route, RouteHandler
    from .types import Request, Response
else:
    # Runtime imports to avoid circular dependencies
    Route = Any
    RouteHandler = Callable
    Request = Any
    Response = Any


class FastRouter:
    """
    Ultra-fast router optimized for performance

    Uses minimal Python-C bridge overhead with intelligent caching
    and optimized data structures for maximum speed.
    """

    def __init__(self):
        self.routes: List[Route] = []
        self.static_routes: Dict[str, Route] = {}  # "METHOD:/path" -> Route
        self.dynamic_routes: List[Route] = []  # Routes with path parameters
        self.route_map: Dict[int, Route] = {}  # route_id -> Route mapping
        self.next_route_id = 1
        self._use_c_router = False
        self._server = None

        # Try to initialize C router
        try:
            from catzilla._catzilla import Server as _Server

            self._server = _Server()
            self._use_c_router = True
        except Exception:
            pass

    def add_route(
        self,
        method: str,
        path: str,
        handler: "RouteHandler",
        *,
        overwrite: bool = False,
        **metadata,
    ) -> "Route":
        """Add a route with optimized storage"""
        # Import Route at runtime to avoid circular imports
        from .routing import Route

        # Extract parameter names from path
        param_names = re.findall(r"\{([^}]+)\}", path)

        # Convert path to regex pattern for fallback matching
        pattern_str = re.escape(path)
        pattern_str = re.sub(r"\\{([^}]+)\\}", r"(?P<\1>[^/]+)", pattern_str)
        pattern_str = f"^{pattern_str}$"
        pattern = re.compile(pattern_str)

        # Create route object
        route = Route(
            method=method,
            path=path,
            handler=handler,
            param_names=param_names,
            pattern=pattern,
            overwrite=overwrite,
            tags=metadata.get("tags"),
            description=metadata.get("description", ""),
            metadata=metadata,
        )

        # Assign route ID
        route_id = self.next_route_id
        self.next_route_id += 1

        # Store in Python structures
        self.routes.append(route)
        self.route_map[route_id] = route

        # Optimize storage: separate static vs dynamic routes
        route_key = f"{method}:{path}"
        if param_names:
            # Dynamic route with parameters
            self.dynamic_routes.append(route)
        else:
            # Static route - can be matched directly
            self.static_routes[route_key] = route

        # Add to C router if available
        if self._use_c_router and self._server:
            try:
                self._server.add_c_route(method, path, route_id)
            except Exception:
                # C router failed, continue with Python only
                self._use_c_router = False

        return route

    def match(
        self, method: str, path: str
    ) -> Tuple[Optional["Route"], Dict[str, str], Optional[Set[str]]]:
        """
        Ultra-fast route matching with optimized paths
        """
        # Fast path: try static route lookup first (most common case)
        route_key = f"{method}:{path}"
        if route_key in self.static_routes:
            route = self.static_routes[route_key]
            return route, {}, None

        # Medium path: try C router for dynamic routes (if available)
        if self._use_c_router and self._server and self.dynamic_routes:
            try:
                match_result = self._server.match_route(method, path)
                if match_result.get("matched"):
                    route_id = match_result.get("route_id")
                    if route_id in self.route_map:
                        route = self.route_map[route_id]
                        path_params = match_result.get("path_params", {})
                        return route, path_params, None
            except Exception:
                # C router failed, disable it
                self._use_c_router = False

        # Slow path: Python fallback for dynamic routes
        return self._python_match_dynamic(method, path)

    def _python_match_dynamic(
        self, method: str, path: str
    ) -> Tuple[Optional["Route"], Dict[str, str], Optional[Set[str]]]:
        """Optimized Python matching for dynamic routes"""
        path_exists = False
        allowed_methods = set()

        # Check dynamic routes
        for route in self.dynamic_routes:
            match = route.pattern.match(path)
            if match:
                path_exists = True
                allowed_methods.add(route.method)

                if route.method == method:
                    # Found matching route
                    path_params = match.groupdict()
                    return route, path_params, None

        # Check static routes for method not allowed
        for static_key, route in self.static_routes.items():
            static_method, static_path = static_key.split(":", 1)
            if static_path == path:
                path_exists = True
                allowed_methods.add(static_method)

        if path_exists:
            # Path exists but method not allowed
            return None, {}, allowed_methods

        # No match found
        return None, {}, None

    def routes_list(self) -> List[Dict[str, str]]:
        """Get a list of all registered routes"""
        return [
            {
                "method": route.method,
                "path": route.path,
                "handler": str(route.handler),
                **{k: str(v) for k, v in route.metadata.items()},
            }
            for route in self.routes
        ]

    def routes(self) -> List[Dict[str, str]]:
        """Get a list of all registered routes (compatible with App interface)"""
        return self.routes_list()

    def get_route_count(self) -> int:
        """Get the number of registered routes"""
        return len(self.routes)

    def include_routes(self, group) -> None:
        """Include all routes from a RouterGroup"""
        # Import RouterGroup at runtime to avoid circular imports
        from .routing import RouterGroup

        if not isinstance(group, RouterGroup):
            raise TypeError("Expected RouterGroup instance")

        # Add all routes from the group
        for route in group.routes:
            # Combine group prefix with route path
            combined_path = group._combine_path(group.prefix, route.path)

            # Add route with combined path
            self.add_route(
                method=route.method,
                path=combined_path,
                handler=route.handler,
                overwrite=route.overwrite,
                **route.metadata,
            )

    # HTTP method decorators for compatibility
    def get(self, path: str, **metadata):
        """Decorator for GET routes"""

        def decorator(handler: "RouteHandler") -> "RouteHandler":
            self.add_route("GET", path, handler, **metadata)
            return handler

        return decorator

    def post(self, path: str, **metadata):
        """Decorator for POST routes"""

        def decorator(handler: "RouteHandler") -> "RouteHandler":
            self.add_route("POST", path, handler, **metadata)
            return handler

        return decorator

    def put(self, path: str, **metadata):
        """Decorator for PUT routes"""

        def decorator(handler: "RouteHandler") -> "RouteHandler":
            self.add_route("PUT", path, handler, **metadata)
            return handler

        return decorator

    def delete(self, path: str, **metadata):
        """Decorator for DELETE routes"""

        def decorator(handler: "RouteHandler") -> "RouteHandler":
            self.add_route("DELETE", path, handler, **metadata)
            return handler

        return decorator

    def patch(self, path: str, **metadata):
        """Decorator for PATCH routes"""

        def decorator(handler: "RouteHandler") -> "RouteHandler":
            self.add_route("PATCH", path, handler, **metadata)
            return handler

        return decorator
