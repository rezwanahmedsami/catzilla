"""
C-accelerated router for high-performance route matching

This module provides a hybrid Python-C routing system that uses the fast C
router for route matching while maintaining Python's flexibility for route
management and organization.
"""

import re
from dataclasses import dataclass
from typing import Callable, Dict, List, Optional, Set, Tuple, Union

from .types import Request, Response, RouteHandler

# Import auto-validation system for RouterGroup support
try:
    from .auto_validation import create_auto_validated_handler

    AUTO_VALIDATION_AVAILABLE = True
except ImportError:
    AUTO_VALIDATION_AVAILABLE = False
    create_auto_validated_handler = None


@dataclass
class Route:
    """Represents a route with its handler and metadata"""

    method: str
    path: str
    handler: RouteHandler
    param_names: List[str]  # Names of path parameters
    pattern: re.Pattern  # Compiled regex pattern for matching
    overwrite: bool = False  # Whether this route can overwrite existing ones
    tags: List[str] = None  # Tags for API organization
    description: str = ""  # Route description
    metadata: Dict[str, any] = None  # Additional metadata
    middleware: List[Callable] = None  # Per-route middleware (NEW!)


class RouteNode:
    """Node in the routing trie"""

    def __init__(self):
        self.children: Dict[str, RouteNode] = {}  # Static path segments
        self.param_child: Optional[Tuple[str, RouteNode]] = (
            None  # Dynamic parameter segment
        )
        self.handlers: Dict[str, Route] = {}  # HTTP method -> Route mapping
        self.allowed_methods: Set[str] = set()  # All methods registered for this path


class RouterGroup:
    """Router group for organizing routes with shared prefix and metadata"""

    def __init__(
        self,
        prefix: str = "",
        *,
        middleware: List[Callable] = None,
        tags: List[str] = None,
        description: str = "",
        metadata: Dict[str, any] = None,
        **kwargs,
    ):
        """
        Initialize a RouterGroup

        Args:
            prefix: Common path prefix for all routes in this group
            middleware: List of middleware functions to apply to all routes in this group
            tags: Tags for API organization (e.g., ["users", "api"])
            description: Description of this route group
            metadata: Additional metadata for the group
            **kwargs: Additional custom metadata fields

        Note:
            Auto-validation is controlled globally by the main Catzilla app's auto_validation setting.
            RouterGroup routes will inherit the app's auto-validation configuration.
            Group middleware runs before per-route middleware.
        """
        self.prefix = self._normalize_prefix(prefix)
        self.middleware = middleware or []
        self.tags = tags or []
        self.description = description
        self.metadata = metadata or {}
        # Include any additional keyword arguments as metadata
        self.metadata.update(kwargs)
        self._routes: List[Tuple[str, str, RouteHandler, Dict[str, any]]] = []

    def _normalize_prefix(self, prefix: str) -> str:
        """Normalize route prefix"""
        if not prefix or prefix == "/":
            return ""

        # Ensure prefix starts with / but doesn't end with / (unless it's root)
        if not prefix.startswith("/"):
            prefix = "/" + prefix
        if len(prefix) > 1 and prefix.endswith("/"):
            prefix = prefix.rstrip("/")

        # Normalize double slashes
        while "//" in prefix:
            prefix = prefix.replace("//", "/")

        return prefix

    def _combine_path(self, path: str) -> str:
        """Combine group prefix with route path"""
        # Normalize the input path
        if not path.startswith("/"):
            path = "/" + path

        # Clean up double slashes in the path
        while "//" in path:
            path = path.replace("//", "/")

        # If no prefix, just return the normalized path
        if not self.prefix:
            return path

        # Handle root path in group - just return the prefix
        if path == "/":
            return self.prefix

        # Combine prefix and path
        combined = self.prefix + path

        # Normalize double slashes again after combination
        while "//" in combined:
            combined = combined.replace("//", "/")

        # Remove trailing slash (except for root)
        if len(combined) > 1 and combined.endswith("/"):
            combined = combined.rstrip("/")

        return combined

    def _register_route(
        self,
        method: str,
        path: str,
        handler: RouteHandler,
        *,
        overwrite: bool = False,
        tags: List[str] = None,
        description: str = "",
        middleware: List[Callable] = None,
        **kwargs,
    ) -> None:
        """Register a route in this group"""
        combined_path = self._combine_path(path)

        # Special case: if this is a root route (/) in a group with a prefix,
        # add a trailing slash to distinguish it from the prefix itself
        if path == "/" and self.prefix and combined_path == self.prefix:
            combined_path = self.prefix + "/"

        # Combine group tags with route-specific tags
        all_tags = self.tags.copy()
        if tags:
            all_tags.extend(tags)

        # Combine group metadata with route-specific metadata
        route_metadata = self.metadata.copy()
        route_metadata.update(kwargs)
        if description:
            route_metadata["description"] = description
        if all_tags:
            route_metadata["tags"] = all_tags
        route_metadata["overwrite"] = overwrite
        route_metadata["group_prefix"] = self.prefix
        route_metadata["group_description"] = self.description

        # Add middleware to metadata
        # Combine group middleware with per-route middleware (group runs first)
        combined_middleware = self.middleware.copy()
        if middleware:
            combined_middleware.extend(middleware)

        if combined_middleware:
            route_metadata["middleware"] = combined_middleware

        # Note: Auto-validation is now applied by the main Catzilla app when routes are included
        # This ensures consistent auto-validation behavior across all routes
        route_metadata["auto_validation_applied"] = (
            False  # Will be updated by app if enabled
        )

        # Store the route for later registration
        self._routes.append((method, combined_path, handler, route_metadata))

    def route(
        self,
        path: str,
        methods: List[str] = None,
        *,
        overwrite: bool = False,
        tags: List[str] = None,
        description: str = "",
        middleware: List[Callable] = None,
        **kwargs,
    ):
        """Route decorator that supports multiple HTTP methods and per-route middleware"""
        if methods is None:
            methods = ["GET"]

        def decorator(handler: RouteHandler):
            for method in methods:
                self._register_route(
                    method,
                    path,
                    handler,
                    overwrite=overwrite,
                    tags=tags,
                    description=description,
                    middleware=middleware,
                    **kwargs,
                )
            return handler

        return decorator

    def get(
        self,
        path: str,
        *,
        overwrite: bool = False,
        tags: List[str] = None,
        description: str = "",
        middleware: List[Callable] = None,
        **kwargs,
    ):
        """GET route decorator with per-route middleware support"""
        return self.route(
            path,
            ["GET"],
            overwrite=overwrite,
            tags=tags,
            description=description,
            middleware=middleware,
            **kwargs,
        )

    def post(
        self,
        path: str,
        *,
        overwrite: bool = False,
        tags: List[str] = None,
        description: str = "",
        middleware: List[Callable] = None,
        **kwargs,
    ):
        """POST route decorator with per-route middleware support"""
        return self.route(
            path,
            ["POST"],
            overwrite=overwrite,
            tags=tags,
            description=description,
            middleware=middleware,
            **kwargs,
        )

    def put(
        self,
        path: str,
        *,
        overwrite: bool = False,
        tags: List[str] = None,
        description: str = "",
        middleware: List[Callable] = None,
        **kwargs,
    ):
        """PUT route decorator with per-route middleware support"""
        return self.route(
            path,
            ["PUT"],
            overwrite=overwrite,
            tags=tags,
            description=description,
            middleware=middleware,
            **kwargs,
        )

    def delete(
        self,
        path: str,
        *,
        overwrite: bool = False,
        tags: List[str] = None,
        description: str = "",
        **kwargs,
    ):
        """DELETE route decorator"""
        return self.route(
            path,
            ["DELETE"],
            overwrite=overwrite,
            tags=tags,
            description=description,
            **kwargs,
        )

    def patch(
        self,
        path: str,
        *,
        overwrite: bool = False,
        tags: List[str] = None,
        description: str = "",
        middleware: List[Callable] = None,
        **kwargs,
    ):
        """PATCH route decorator with per-route middleware support"""
        return self.route(
            path,
            ["PATCH"],
            overwrite=overwrite,
            tags=tags,
            description=description,
            middleware=middleware,
            **kwargs,
        )

    def options(
        self,
        path: str,
        *,
        overwrite: bool = False,
        tags: List[str] = None,
        description: str = "",
        middleware: List[Callable] = None,
        **kwargs,
    ):
        """OPTIONS route decorator with per-route middleware support"""
        return self.route(
            path,
            ["OPTIONS"],
            overwrite=overwrite,
            tags=tags,
            description=description,
            middleware=middleware,
            **kwargs,
        )

    def head(
        self,
        path: str,
        *,
        overwrite: bool = False,
        tags: List[str] = None,
        description: str = "",
        middleware: List[Callable] = None,
        **kwargs,
    ):
        """HEAD route decorator with per-route middleware support"""
        return self.route(
            path,
            ["HEAD"],
            overwrite=overwrite,
            tags=tags,
            description=description,
            middleware=middleware,
            **kwargs,
        )

    def routes(self) -> List[Tuple[str, str, RouteHandler, Dict[str, any]]]:
        """Get all routes registered in this group"""
        return self._routes.copy()

    def include_group(self, other_group: "RouterGroup") -> None:
        """Include routes from another RouterGroup into this one"""
        for method, path, handler, metadata in other_group.routes():
            # Remove the other group's prefix and add to this group
            relative_path = path
            if other_group.prefix and path.startswith(other_group.prefix):
                # Get the part after the prefix
                remaining_path = path[len(other_group.prefix) :]
                # If nothing remains after removing prefix, it was a root route in that group
                relative_path = remaining_path if remaining_path else "/"

            # Merge metadata and track the full prefix chain
            merged_metadata = metadata.copy()

            # Build the full original prefix chain
            existing_original_prefix = metadata.get("original_group_prefix", "")
            if existing_original_prefix:
                # This route was already included from another group, so build the chain
                full_original_prefix = other_group.prefix + existing_original_prefix
            else:
                # This is the first inclusion, so the original prefix is just the other group's prefix
                full_original_prefix = other_group.prefix

            merged_metadata["original_group_prefix"] = full_original_prefix
            merged_metadata["included_in_group"] = self.prefix

            # Combine this group's prefix with the other group's prefix, then the relative path
            # This ensures nested group prefixes are preserved
            combined_prefix = (
                self.prefix + other_group.prefix if other_group.prefix else self.prefix
            )

            # Special handling for root paths in group inclusion context
            if relative_path == "/":
                # For root paths from included groups, use the combined prefix
                final_path = combined_prefix if combined_prefix else "/"
                self._routes.append((method, final_path, handler, merged_metadata))
            else:
                # For non-root paths, combine the prefixes with the relative path
                final_path = combined_prefix + relative_path
                # Normalize double slashes
                while "//" in final_path:
                    final_path = final_path.replace("//", "/")
                self._routes.append((method, final_path, handler, merged_metadata))


try:
    from catzilla._catzilla import (
        router_add_route,
        router_add_route_with_middleware,
        router_match,
    )
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

    def router_add_route_with_middleware(
        method: str,
        path: str,
        handler_id: int,
        middleware_ids: List[int] = None,
        middleware_priorities: List[int] = None,
    ) -> int:
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
        middleware: List[Callable] = None,
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
            middleware=middleware,  # Store per-route middleware
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
                if middleware:
                    # If per-route middleware is specified, use the middleware-aware function
                    self._server.add_c_route_with_middleware(
                        method, path, route_id, middleware
                    )
                else:
                    # No middleware, use the regular function
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
                "handler_name": route.handler.__name__,
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
        """Include all routes from a RouterGroup

        Note: This method is kept for compatibility but auto-validation
        should be handled by the main Catzilla app's include_routes method.
        """
        if not isinstance(group, RouterGroup):
            raise TypeError("Expected RouterGroup instance")

        # Add all routes from the group (handlers should already be processed by main app)
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

    def get(
        self, path: str, *, overwrite: bool = False, middleware: List[Callable] = None
    ):
        """Decorator to register a GET route handler with optional per-route middleware"""

        def decorator(handler: RouteHandler):
            self.add_route(
                "GET", path, handler, overwrite=overwrite, middleware=middleware
            )
            return handler

        return decorator

    def post(
        self, path: str, *, overwrite: bool = False, middleware: List[Callable] = None
    ):
        """Decorator to register a POST route handler with optional per-route middleware"""

        def decorator(handler: RouteHandler):
            self.add_route(
                "POST", path, handler, overwrite=overwrite, middleware=middleware
            )
            return handler

        return decorator

    def put(
        self, path: str, *, overwrite: bool = False, middleware: List[Callable] = None
    ):
        """Decorator to register a PUT route handler with optional per-route middleware"""

        def decorator(handler: RouteHandler):
            self.add_route(
                "PUT", path, handler, overwrite=overwrite, middleware=middleware
            )
            return handler

        return decorator

    def delete(
        self, path: str, *, overwrite: bool = False, middleware: List[Callable] = None
    ):
        """Decorator to register a DELETE route handler with optional per-route middleware"""

        def decorator(handler: RouteHandler):
            self.add_route(
                "DELETE", path, handler, overwrite=overwrite, middleware=middleware
            )
            return handler

        return decorator

    def patch(
        self, path: str, *, overwrite: bool = False, middleware: List[Callable] = None
    ):
        """Decorator to register a PATCH route handler with optional per-route middleware"""

        def decorator(handler: RouteHandler):
            self.add_route(
                "PATCH", path, handler, overwrite=overwrite, middleware=middleware
            )
            return handler

        return decorator

    def options(
        self, path: str, *, overwrite: bool = False, middleware: List[Callable] = None
    ):
        """Decorator to register an OPTIONS route handler with optional per-route middleware"""

        def decorator(handler: RouteHandler):
            self.add_route(
                "OPTIONS", path, handler, overwrite=overwrite, middleware=middleware
            )
            return handler

        return decorator

    def head(
        self, path: str, *, overwrite: bool = False, middleware: List[Callable] = None
    ):
        """Decorator to register a HEAD route handler with optional per-route middleware"""

        def decorator(handler: RouteHandler):
            self.add_route(
                "HEAD", path, handler, overwrite=overwrite, middleware=middleware
            )
            return handler

        return decorator
