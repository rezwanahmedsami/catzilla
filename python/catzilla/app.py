"""
Catzilla application with C-accelerated routing

This module provides the main App class which uses CAcceleratedRouter
as the sole routing option, leveraging C-based matching for maximum performance.
"""

import functools
import signal
import sys
from typing import Any, Callable, Dict, List, Optional, Union
from urllib.parse import parse_qs

from .c_router import CAcceleratedRouter
from .types import HTMLResponse, JSONResponse, Request, Response, RouteHandler

try:
    from catzilla._catzilla import Server as _Server
    from catzilla._catzilla import send_response
except ImportError:
    raise ImportError(
        "Failed to import C extension. Make sure Catzilla is properly installed."
    )


class App:
    """Main Catzilla application with C-accelerated routing"""

    def __init__(self, production: bool = False):
        """Initialize Catzilla app with C-accelerated router (only option)

        Args:
            production: If True, return clean JSON error responses without stack traces
        """
        self.server = _Server()

        # Use C-accelerated router - the only router option
        # Since Catzilla is fundamentally C-based, if this fails, nothing works
        self.router = CAcceleratedRouter()
        self._router_type = "CAcceleratedRouter"

        # Error handling configuration
        self.production = production
        self._exception_handlers: Dict[type, Callable] = {}
        self._not_found_handler: Optional[Callable] = None
        self._internal_error_handler: Optional[Callable] = None

        self._setup_signal_handlers()

    def _setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown"""
        self.original_sigint_handler = signal.getsignal(signal.SIGINT)
        self.original_sigterm_handler = signal.getsignal(signal.SIGTERM)

        def signal_handler(sig, frame):
            print("\n[INFO-PY] Shutting down Catzilla server...")
            self.stop()

            # Restore original handlers
            signal.signal(signal.SIGINT, self.original_sigint_handler)
            signal.signal(signal.SIGTERM, self.original_sigterm_handler)

            # If original handler was default, exit
            if (
                self.original_sigint_handler == signal.default_int_handler
                and sig == signal.SIGINT
            ):
                sys.exit(0)

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

    def _handle_request(self, client, method, path, body, request_capsule):
        """Internal request handler that bridges C and Python"""
        # Get base path for routing (strip query string if present)
        base_path = path.split("?", 1)[0] if "?" in path else path

        # Create request object with empty query params dict - will be populated by C layer
        request = Request(
            method=method,
            path=path,  # Use full path with query string
            body=body,
            client=client,
            request_capsule=request_capsule,
            _query_params={},  # Changed from query_params to _query_params
        )

        # Match the route using our new router
        route, path_params, allowed_methods = self.router.match(method, base_path)

        # Set path parameters on request
        request.path_params = path_params

        if route:
            try:
                # Check content type before calling handler
                content_type = request.content_type
                if content_type and content_type not in [
                    "application/json",
                    "application/x-www-form-urlencoded",
                    "text/plain",
                    "multipart/form-data",
                ]:
                    # Return 415 Unsupported Media Type
                    err_resp = Response(
                        status_code=415,
                        content_type="text/plain",
                        body=f"Unsupported Media Type: {content_type}",
                        headers={
                            "X-Error-Detail": f"Content-Type {content_type} is not supported"
                        },
                    )
                    err_resp.send(client)
                    return

                # Call the handler and get a response
                response = route.handler(request)

                # Normalize response based on return type
                if isinstance(response, Response):
                    # Response object - use as is
                    pass
                elif isinstance(response, dict):
                    # Dictionary - convert to JSONResponse
                    response = JSONResponse(response)
                elif isinstance(response, str):
                    # String - convert to HTMLResponse
                    response = HTMLResponse(response)
                else:
                    # Unsupported type
                    raise TypeError(
                        f"Handler returned unsupported type {type(response)}. "
                        "Must return Response, dict, or str."
                    )

                # Send the response
                response.send(client)
            except Exception as e:
                # Handle exceptions using the centralized error handling system
                err_resp = self._handle_exception(request, e)
                err_resp.send(client)
        else:
            if allowed_methods:
                # Path exists but method not allowed
                if self.production:
                    not_allowed = self._get_clean_error_response(
                        405,
                        "Method not allowed",
                        f"Allowed methods: {', '.join(sorted(allowed_methods))}",
                    )
                else:
                    not_allowed = Response(
                        status_code=405,
                        content_type="text/plain",
                        body=f"Method Not Allowed: {method} {path}",
                        headers={
                            "Allow": ", ".join(sorted(allowed_methods)),
                            "X-Error-Path": path,
                        },
                    )
                not_allowed.send(client)
            else:
                # No route found - use custom 404 handler if set
                if self._not_found_handler:
                    try:
                        not_found_resp = self._not_found_handler(request)
                        not_found_resp.send(client)
                    except Exception as handler_error:
                        # 404 handler failed, fall back to default
                        if self.production:
                            fallback_resp = self._get_clean_error_response(
                                404, "Not found"
                            )
                        else:
                            fallback_resp = Response(
                                status_code=500,
                                content_type="text/plain",
                                body=f"404 handler failed: {str(handler_error)}",
                                headers={"X-Error-Detail": str(handler_error)},
                            )
                        fallback_resp.send(client)
                else:
                    # Default 404 handling
                    if self.production:
                        not_found = self._get_clean_error_response(404, "Not found")
                    else:
                        not_found = Response(
                            status_code=404,
                            content_type="text/plain",
                            body=f"Not Found: {method} {path}",
                            headers={"X-Error-Path": path},
                        )
                    not_found.send(client)

    def route(self, path: str, methods: List[str] = None, *, overwrite: bool = False):
        """Register a route handler for multiple HTTP methods"""
        return self.router.route(path, methods, overwrite=overwrite)

    def get(self, path: str, *, overwrite: bool = False):
        """Register a GET route handler"""
        return self.router.get(path, overwrite=overwrite)

    def post(self, path: str, *, overwrite: bool = False):
        """Register a POST route handler"""
        return self.router.post(path, overwrite=overwrite)

    def put(self, path: str, *, overwrite: bool = False):
        """Register a PUT route handler"""
        return self.router.put(path, overwrite=overwrite)

    def delete(self, path: str, *, overwrite: bool = False):
        """Register a DELETE route handler"""
        return self.router.delete(path, overwrite=overwrite)

    def patch(self, path: str, *, overwrite: bool = False):
        """Register a PATCH route handler"""
        return self.router.patch(path, overwrite=overwrite)

    def include_routes(self, group) -> None:
        """
        Include all routes from a RouterGroup into this application

        Args:
            group: RouterGroup instance containing routes to include
        """
        self.router.include_routes(group)

    def routes(self) -> List[Dict[str, str]]:
        """Get a list of all registered routes"""
        if hasattr(self.router, "routes_list"):
            return self.router.routes_list()
        else:
            return self.router.routes()

    def listen(self, port: int, host: str = "0.0.0.0"):
        """Start the server"""
        print(f"[INFO-PY] Catzilla server starting on http://{host}:{port}")
        print("[INFO-PY] Press Ctrl+C to stop the server")
        print("\nRegistered routes:")
        for route in self.routes():
            print(f"  {route['method']:6} {route['path']}")

        # Add our Python handler for all registered routes
        for route in self.router.routes():
            self.server.add_route(route["method"], route["path"], self._handle_request)

        # Start the server
        self.server.listen(port, host)

    def stop(self):
        """Stop the server"""
        self.server.stop()

    def set_exception_handler(
        self, exception_type: type, handler: Callable[[Request, Exception], Response]
    ) -> None:
        """
        Register a global exception handler for a specific exception type

        Args:
            exception_type: The exception class to handle (e.g., ValueError, FileNotFoundError)
            handler: Function that takes (request, exception) and returns a Response

        Example:
            @app.set_exception_handler(ValueError)
            def handle_value_error(request, exc):
                return JSONResponse({"error": "Invalid value", "detail": str(exc)}, status_code=400)
        """
        self._exception_handlers[exception_type] = handler

    def set_not_found_handler(self, handler: Callable[[Request], Response]) -> None:
        """
        Set a global handler for 404 Not Found errors

        Args:
            handler: Function that takes a request and returns a Response

        Example:
            @app.set_not_found_handler
            def custom_404(request):
                return JSONResponse({"error": "Not found", "path": request.path}, status_code=404)
        """
        self._not_found_handler = handler

    def set_internal_error_handler(
        self, handler: Callable[[Request, Exception], Response]
    ) -> None:
        """
        Set a global handler for 500 Internal Server Error

        Args:
            handler: Function that takes (request, exception) and returns a Response

        Example:
            @app.set_internal_error_handler
            def custom_500(request, exc):
                return JSONResponse({"error": "Server error"}, status_code=500)
        """
        self._internal_error_handler = handler

    def _get_clean_error_response(
        self, status_code: int, message: str, detail: Optional[str] = None
    ) -> Response:
        """Create a clean JSON error response for production mode"""
        error_data = {"error": message}
        if detail and not self.production:
            error_data["detail"] = detail
        return JSONResponse(error_data, status_code=status_code)

    def _handle_exception(self, request: Request, exception: Exception) -> Response:
        """Handle exceptions using registered handlers or defaults"""
        # Check for specific exception type handlers
        for exc_type, handler in self._exception_handlers.items():
            if isinstance(exception, exc_type):
                try:
                    return handler(request, exception)
                except Exception as handler_error:
                    # Handler failed, fall back to default
                    if self.production:
                        return self._get_clean_error_response(
                            500, "Internal server error"
                        )
                    else:
                        return Response(
                            status_code=500,
                            content_type="text/plain",
                            body=f"Exception handler failed: {str(handler_error)}",
                            headers={"X-Error-Detail": str(handler_error)},
                        )

        # Use custom internal error handler if set
        if self._internal_error_handler:
            try:
                return self._internal_error_handler(request, exception)
            except Exception as handler_error:
                # Handler failed, fall back to default
                if self.production:
                    return self._get_clean_error_response(500, "Internal server error")
                else:
                    return Response(
                        status_code=500,
                        content_type="text/plain",
                        body=f"Internal error handler failed: {str(handler_error)}",
                        headers={"X-Error-Detail": str(handler_error)},
                    )

        # Default error handling
        if self.production:
            return self._get_clean_error_response(500, "Internal server error")
        else:
            import traceback

            traceback.print_exc()
            return Response(
                status_code=500,
                content_type="text/plain",
                body=f"Internal Server Error: {str(exception)}",
                headers={"X-Error-Detail": str(exception)},
            )
