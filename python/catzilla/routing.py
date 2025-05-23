"""
Advanced routing system for Catzilla
"""

import re
import warnings
from dataclasses import dataclass
from typing import Dict, List, Optional, Set, Tuple, Union

from .types import RouteHandler


@dataclass
class Route:
    """Represents a route with its handler and metadata"""

    method: str
    path: str
    handler: RouteHandler
    param_names: List[str]  # Names of path parameters
    pattern: re.Pattern  # Compiled regex pattern for matching
    overwrite: bool = False  # Whether this route can overwrite existing ones


class RouteNode:
    """Node in the routing trie"""

    def __init__(self):
        self.children: Dict[str, RouteNode] = {}  # Static path segments
        self.param_child: Optional[Tuple[str, RouteNode]] = (
            None  # Dynamic parameter segment
        )
        self.handlers: Dict[str, Route] = {}  # HTTP method -> Route mapping
        self.allowed_methods: Set[str] = set()  # All methods registered for this path


class Router:
    """Advanced router with dynamic path support"""

    def __init__(self):
        self.root = RouteNode()
        self._route_list: List[Route] = []  # For introspection

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
        self, method: str, path: str, handler: RouteHandler, *, overwrite: bool = False
    ) -> None:
        """
        Add a route with support for dynamic path segments.

        Args:
            method: HTTP method (GET, POST, etc.)
            path: URL path pattern (e.g., "/users/{user_id}")
            handler: Function to handle the route
            overwrite: Whether to allow overwriting existing routes
        """
        segments, param_names, pattern = self._parse_path(path)
        route = Route(method, path, handler, param_names, pattern, overwrite)

        # Add to trie
        self._add_to_trie(route, segments)

        # Add to route list for introspection
        self._route_list.append(route)

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
        return self._match_segments(method, segments, node)

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
        return self._match_route(method, path)

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
    def route(self, path: str, methods: List[str] = None, *, overwrite: bool = False):
        """Route decorator that supports multiple HTTP methods"""
        if methods is None:
            methods = ["GET"]

        def decorator(handler: RouteHandler):
            for method in methods:
                self.add_route(method, path, handler, overwrite=overwrite)
            return handler

        return decorator

    def get(self, path: str, *, overwrite: bool = False):
        """GET route decorator"""
        return self.route(path, ["GET"], overwrite=overwrite)

    def post(self, path: str, *, overwrite: bool = False):
        """POST route decorator"""
        return self.route(path, ["POST"], overwrite=overwrite)

    def put(self, path: str, *, overwrite: bool = False):
        """PUT route decorator"""
        return self.route(path, ["PUT"], overwrite=overwrite)

    def delete(self, path: str, *, overwrite: bool = False):
        """DELETE route decorator"""
        return self.route(path, ["DELETE"], overwrite=overwrite)

    def patch(self, path: str, *, overwrite: bool = False):
        """PATCH route decorator"""
        return self.route(path, ["PATCH"], overwrite=overwrite)
