"""
C-accelerated router for high-performance route matching

This module provides a hybrid Python-C routing system that uses the fast C
router for route matching while maintaining Python's flexibility for route
management and organization.
"""

from typing import Dict, List, Optional, Set, Tuple, Union

from .routing import Route, RouteHandler
from .types import Request, Response

try:
    from catzilla._catzilla import router_add_route, router_match
except ImportError:
    # Fallback for when C extension is not available
    def router_match(method: str, path: str) -> Dict:
        return {
            "matched": False,
            "status_code": 404,
            "path_params": {},
            "allowed_methods": None,
        }

    def router_add_route(method: str, path: str, handler_id: int) -> int:
        return 0


class CAcceleratedRouter:
    """
    High-performance router that uses C for route matching

    This router maintains Python route objects for organization while
    using the C router for fast path matching. Provides ~15-20% performance
    improvement over pure Python routing.
    """

    def __init__(self):
        self._routes: List[Route] = []  # Renamed to avoid conflict with routes() method
        self.route_map: Dict[int, Route] = {}  # route_id -> Route mapping
        self.next_route_id = 1
        self._c_routes_synced = False
        self._use_c_router = False
        self._server = None

        # Try to create a dedicated server instance for C routing
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
        handler: RouteHandler,
        *,
        overwrite: bool = False,
        **metadata,
    ) -> Route:
        """Add a route to both Python and C routers"""
        import re

        # Normalize method to uppercase
        method = method.upper()

        # Extract parameter names from path
        param_names = []
        pattern_str = path

        # Find all {param} patterns and extract names
        param_matches = re.findall(r"\{([^}]+)\}", path)
        param_names = param_matches

        # Convert path to regex pattern for Python fallback
        pattern_str = re.escape(path)
        pattern_str = re.sub(r"\\{([^}]+)\\}", r"(?P<\1>[^/]+)", pattern_str)
        pattern_str = f"^{pattern_str}$"
        pattern = re.compile(pattern_str)

        # Create Python route object
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

        # Check for conflicts if not overwriting
        if not overwrite:
            for existing_route in self._routes:
                if existing_route.method == method and existing_route.path == path:
                    if not existing_route.overwrite:
                        import warnings

                        warnings.warn(
                            f"Route conflict: {method} {path} already exists. "
                            f"Use overwrite=True to replace it.",
                            UserWarning,
                            stacklevel=3,
                        )
                    break

        # Assign unique route ID
        route_id = self.next_route_id
        self.next_route_id += 1

        # Add to Python structures
        self._routes.append(route)
        self.route_map[route_id] = route

        # Try to add to C router for fast matching (if available)
        if self._use_c_router and self._server:
            try:
                # Use the server's dedicated C router instead of global router
                self._server.add_c_route(method, path, route_id)
                self._c_routes_synced = True
            except Exception:
                # C router failed, but keep Python route
                self._use_c_router = False

        return route

    def match(
        self, method: str, path: str
    ) -> Tuple[Optional[Route], Dict[str, str], Optional[Set[str]]]:
        """
        Match a route using the fast C router

        Returns:
            - Route object if matched, None otherwise
            - Path parameters dictionary
            - Set of allowed methods if path exists but method doesn't match
        """
        # Normalize method to uppercase
        method = method.upper()

        # Try C router first (if available and synced)
        if self._use_c_router and self._server and self._c_routes_synced:
            try:
                # Use server's dedicated C router for better performance
                match_result = self._server.match_route(method, path)

                if match_result["matched"]:
                    # Route matched - get the Python route object
                    route_id = match_result.get("route_id")
                    if route_id and route_id in self.route_map:
                        route = self.route_map[route_id]
                        path_params = match_result.get("path_params", {})
                        return route, path_params, None
                    else:
                        # C router matched but we lost the Python route - fallback
                        return self._python_fallback_match(method, path)

                elif match_result["status_code"] == 405:
                    # Method not allowed - path exists but method doesn't match
                    allowed_methods_str = match_result.get("allowed_methods")
                    if allowed_methods_str:
                        allowed_methods = set(allowed_methods_str.split(", "))
                        return None, {}, allowed_methods
                    else:
                        return None, {}, set()

                else:
                    # No match (404)
                    return None, {}, None

            except Exception:
                # C router failed - fallback to Python and disable C router
                self._use_c_router = False

        # Fallback to Python matching
        return self._python_fallback_match(method, path)

    def _python_fallback_match(
        self, method: str, path: str
    ) -> Tuple[Optional[Route], Dict[str, str], Optional[Set[str]]]:
        """Fallback to Python-only route matching"""
        import re

        # Normalize method to uppercase (should already be done by caller)
        method = method.upper()

        # Simple static matching first
        for route in self._routes:
            if route.method == method and route.path == path:
                return route, {}, None

        # Dynamic matching with path parameters
        path_routes_by_method = {}
        for route in self._routes:
            if route.method not in path_routes_by_method:
                path_routes_by_method[route.method] = []
            path_routes_by_method[route.method].append(route)

        # Check if any route matches the path (for 405 detection)
        path_exists = False
        allowed_methods = set()

        for route_method, routes in path_routes_by_method.items():
            for route in routes:
                # Convert route path to regex
                pattern = route.path
                # Replace {param} with regex groups
                pattern = re.sub(r"\{([^}]+)\}", r"(?P<\1>[^/]+)", pattern)
                pattern = f"^{pattern}$"

                match = re.match(pattern, path)
                if match:
                    path_exists = True
                    allowed_methods.add(route_method)

                    if route_method == method:
                        # Method and path match
                        path_params = match.groupdict()
                        return route, path_params, None

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
            for route in self._routes
        ]

    def routes(self) -> List[Dict[str, str]]:
        """Get a list of all registered routes (compatible with App interface)"""
        return self.routes_list()

    def get_route_count(self) -> int:
        """Get the number of registered routes"""
        return len(self._routes)

    def include_routes(self, group) -> None:
        """Include all routes from a RouterGroup"""
        from .routing import RouterGroup

        if not isinstance(group, RouterGroup):
            raise TypeError("Expected RouterGroup instance")

        # Add all routes from the group
        for method, path, handler, metadata in group.routes():
            # Get overwrite flag from metadata
            overwrite = metadata.get("overwrite", False)

            # Remove internal metadata before passing to add_route
            clean_metadata = metadata.copy()
            clean_metadata.pop("overwrite", None)

            self.add_route(
                method=method,
                path=path,
                handler=handler,
                overwrite=overwrite,
                **clean_metadata,
            )

    # Decorator methods for compatibility with Router interface
    def route(self, path: str, methods: List[str] = None, *, overwrite: bool = False):
        """Decorator to register a route handler for multiple HTTP methods"""
        if methods is None:
            methods = ["GET"]

        def decorator(handler: RouteHandler):
            for method in methods:
                self.add_route(method, path, handler, overwrite=overwrite)
            return handler

        return decorator

    def get(self, path: str, *, overwrite: bool = False):
        """Decorator to register a GET route handler"""

        def decorator(handler: RouteHandler):
            self.add_route("GET", path, handler, overwrite=overwrite)
            return handler

        return decorator

    def post(self, path: str, *, overwrite: bool = False):
        """Decorator to register a POST route handler"""

        def decorator(handler: RouteHandler):
            self.add_route("POST", path, handler, overwrite=overwrite)
            return handler

        return decorator

    def put(self, path: str, *, overwrite: bool = False):
        """Decorator to register a PUT route handler"""

        def decorator(handler: RouteHandler):
            self.add_route("PUT", path, handler, overwrite=overwrite)
            return handler

        return decorator

    def delete(self, path: str, *, overwrite: bool = False):
        """Decorator to register a DELETE route handler"""

        def decorator(handler: RouteHandler):
            self.add_route("DELETE", path, handler, overwrite=overwrite)
            return handler

        return decorator

    def patch(self, path: str, *, overwrite: bool = False):
        """Decorator to register a PATCH route handler"""

        def decorator(handler: RouteHandler):
            self.add_route("PATCH", path, handler, overwrite=overwrite)
            return handler

        return decorator
