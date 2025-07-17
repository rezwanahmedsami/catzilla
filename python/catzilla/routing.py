"""
Advanced routing system for Catzilla
"""

import re
import warnings
from dataclasses import dataclass
from typing import Callable, Dict, List, Optional, Set, Tuple, Union

from .types import RouteHandler

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
        tags: List[str] = None,
        description: str = "",
        metadata: Dict[str, any] = None,
        **kwargs,
    ):
        """
        Initialize a RouterGroup

        Args:
            prefix: Common path prefix for all routes in this group
            tags: Tags for API organization (e.g., ["users", "api"])
            description: Description of this route group
            metadata: Additional metadata for the group
            **kwargs: Additional custom metadata fields

        Note:
            Auto-validation is controlled globally by the main Catzilla app's auto_validation setting.
            RouterGroup routes will inherit the app's auto-validation configuration.
        """
        self.prefix = self._normalize_prefix(prefix)
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
        if middleware:
            route_metadata["middleware"] = middleware

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
        **kwargs,
    ):
        """PATCH route decorator"""
        return self.route(
            path,
            ["PATCH"],
            overwrite=overwrite,
            tags=tags,
            description=description,
            **kwargs,
        )

    def options(
        self,
        path: str,
        *,
        overwrite: bool = False,
        tags: List[str] = None,
        description: str = "",
        **kwargs,
    ):
        """OPTIONS route decorator"""
        return self.route(
            path,
            ["OPTIONS"],
            overwrite=overwrite,
            tags=tags,
            description=description,
            **kwargs,
        )

    def head(
        self,
        path: str,
        *,
        overwrite: bool = False,
        tags: List[str] = None,
        description: str = "",
        **kwargs,
    ):
        """HEAD route decorator"""
        return self.route(
            path,
            ["HEAD"],
            overwrite=overwrite,
            tags=tags,
            description=description,
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


class Router:
    """Advanced router with dynamic path support"""

    def __init__(self):
        self.root = RouteNode()
        self._route_list: List[Route] = []  # For introspection

    def _normalize_method(self, method: str) -> str:
        """Normalize HTTP method to uppercase"""
        return method.upper() if method else ""

    def _parse_path(self, path: str) -> Tuple[List[str], List[str], re.Pattern]:
        """Parse a path pattern into segments and extract parameter names"""
        if not path.startswith("/"):
            path = "/" + path

        segments = path.split("/")
        param_names = []
        pattern_parts = []

        for segment in segments:
            if segment.startswith("{") and segment.endswith("}"):
                # Dynamic segment
                param_name = segment[1:-1]
                param_names.append(param_name)
                pattern_parts.append(r"([^/]+)")
            else:
                # Static segment
                pattern_parts.append(re.escape(segment))

        pattern = re.compile("^" + "/".join(pattern_parts) + "$")
        return segments, param_names, pattern

    def _add_to_trie(
        self, route: Route, segments: List[str], node: RouteNode = None
    ) -> None:
        """Add a route to the routing trie"""
        if node is None:
            node = self.root

        if not segments:
            # Check for method conflict
            if route.method in node.handlers and not route.overwrite:
                existing = node.handlers[route.method]
                warnings.warn(
                    f"Route conflict: {route.method} {route.path} overwrites existing route. "
                    f"Use overwrite=True to suppress this warning.",
                    RuntimeWarning,
                )

            # Add/update the handler
            node.handlers[route.method] = route
            node.allowed_methods.add(route.method)
            return

        segment = segments[0]
        remaining = segments[1:]

        if segment.startswith("{") and segment.endswith("}"):
            # Dynamic parameter segment
            if node.param_child is None:
                # Create new parameter node
                param_name = segment[1:-1]
                new_node = RouteNode()
                node.param_child = (param_name, new_node)
            self._add_to_trie(route, remaining, node.param_child[1])
        else:
            # Static segment
            if segment not in node.children:
                node.children[segment] = RouteNode()
            self._add_to_trie(route, remaining, node.children[segment])

    def add_route(
        self,
        method: str,
        path: str,
        handler: RouteHandler,
        *,
        overwrite: bool = False,
        tags: List[str] = None,
        description: str = "",
        metadata: Dict[str, any] = None,
        middleware: List[Callable] = None,
    ) -> None:
        """
        Add a route with support for dynamic path segments and per-route middleware.

        Args:
            method: HTTP method (GET, POST, etc.)
            path: URL path pattern (e.g., "/users/{user_id}")
            handler: Function to handle the route
            overwrite: Whether to allow overwriting existing routes
            tags: Tags for API organization
            description: Route description
            metadata: Additional metadata
            middleware: List of middleware functions for this route
        """
        # Normalize method to uppercase
        normalized_method = self._normalize_method(method)

        segments, param_names, pattern = self._parse_path(path)
        route = Route(
            normalized_method,
            path,
            handler,
            param_names,
            pattern,
            overwrite,
            tags or [],
            description,
            metadata or {},
            middleware or [],  # Store per-route middleware
        )

        # Add to trie
        self._add_to_trie(route, segments)

        # Add to route list for introspection
        self._route_list.append(route)

    def include_routes(self, group: RouterGroup) -> None:
        """
        Include all routes from a RouterGroup into this router

        Args:
            group: RouterGroup containing routes to include
        """
        for method, path, handler, metadata in group.routes():
            overwrite = metadata.pop("overwrite", False)
            tags = metadata.pop("tags", None)
            description = metadata.pop("description", "")

            self.add_route(
                method,
                path,
                handler,
                overwrite=overwrite,
                tags=tags,
                description=description,
                metadata=metadata,
            )

    def _match_route(
        self, method: str, path: str, node: RouteNode = None
    ) -> Tuple[Optional[Route], Dict[str, str], Optional[Set[str]]]:
        """
        Match a path against the routing trie.

        Returns:
            Tuple of (matched route, path params, allowed methods)
            If no route matches but path exists, returns (None, {}, allowed_methods)
            If no route exists at all, returns (None, {}, None)
        """
        if not path.startswith("/"):
            path = "/" + path

        if node is None:
            node = self.root

        segments = path.split("/")
        # Method should already be normalized by caller, but ensure it
        normalized_method = self._normalize_method(method)
        return self._match_segments(normalized_method, segments, node)

    def _match_segments(
        self, method: str, segments: List[str], node: RouteNode
    ) -> Tuple[Optional[Route], Dict[str, str], Optional[Set[str]]]:
        """Recursive helper for matching path segments"""
        if not segments:
            # We've reached the end of the path
            if node.handlers:
                # This is a valid endpoint
                if method in node.handlers:
                    # Method matches
                    return node.handlers[method], {}, node.allowed_methods
                else:
                    # Valid path but wrong method
                    return None, {}, node.allowed_methods
            return None, {}, None

        segment = segments[0]
        remaining = segments[1:]

        # Try static routes first
        if segment in node.children:
            route, params, methods = self._match_segments(
                method, remaining, node.children[segment]
            )
            if route is not None or methods is not None:
                return route, params, methods

        # Try dynamic parameter
        if node.param_child is not None:
            param_name, param_node = node.param_child
            route, params, methods = self._match_segments(method, remaining, param_node)
            if route is not None:
                params[param_name] = segment
                return route, params, methods
            if methods is not None:
                return None, {}, methods

        return None, {}, None

    def match(
        self, method: str, path: str
    ) -> Tuple[Optional[Route], Dict[str, str], Optional[Set[str]]]:
        """
        Match a request path to a route.

        Args:
            method: HTTP method
            path: Request path

        Returns:
            Tuple of (matched route, path params, allowed methods)
        """
        # Normalize method to uppercase
        normalized_method = self._normalize_method(method)
        return self._match_route(normalized_method, path)

    def routes(self) -> List[Dict[str, str]]:
        """
        Get a list of all registered routes for introspection.

        Returns:
            List of dicts with keys: method, path, handler_name
        """
        return [
            {
                "method": route.method,
                "path": route.path,
                "handler_name": route.handler.__name__,
            }
            for route in self._route_list
        ]

    # Decorator methods
    def route(
        self,
        path: str,
        methods: List[str] = None,
        *,
        overwrite: bool = False,
        middleware: List[Callable] = None,
    ):
        """Route decorator that supports multiple HTTP methods and per-route middleware"""
        if methods is None:
            methods = ["GET"]

        def decorator(handler: RouteHandler):
            for method in methods:
                self.add_route(
                    method, path, handler, overwrite=overwrite, middleware=middleware
                )
            return handler

        return decorator

    def get(
        self, path: str, *, overwrite: bool = False, middleware: List[Callable] = None
    ):
        """GET route decorator with per-route middleware support"""
        return self.route(path, ["GET"], overwrite=overwrite, middleware=middleware)

    def post(
        self, path: str, *, overwrite: bool = False, middleware: List[Callable] = None
    ):
        """POST route decorator with per-route middleware support"""
        return self.route(path, ["POST"], overwrite=overwrite, middleware=middleware)

    def put(
        self, path: str, *, overwrite: bool = False, middleware: List[Callable] = None
    ):
        """PUT route decorator with per-route middleware support"""
        return self.route(path, ["PUT"], overwrite=overwrite, middleware=middleware)

    def delete(
        self, path: str, *, overwrite: bool = False, middleware: List[Callable] = None
    ):
        """DELETE route decorator with per-route middleware support"""
        return self.route(path, ["DELETE"], overwrite=overwrite, middleware=middleware)

    def patch(
        self, path: str, *, overwrite: bool = False, middleware: List[Callable] = None
    ):
        """PATCH route decorator with per-route middleware support"""
        return self.route(path, ["PATCH"], overwrite=overwrite, middleware=middleware)

    def options(
        self, path: str, *, overwrite: bool = False, middleware: List[Callable] = None
    ):
        """OPTIONS route decorator with per-route middleware support"""
        return self.route(path, ["OPTIONS"], overwrite=overwrite, middleware=middleware)

    def head(
        self, path: str, *, overwrite: bool = False, middleware: List[Callable] = None
    ):
        """HEAD route decorator with per-route middleware support"""
        return self.route(path, ["HEAD"], overwrite=overwrite, middleware=middleware)
