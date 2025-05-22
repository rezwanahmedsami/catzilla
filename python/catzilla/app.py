"""
Catzilla application and router
"""

import functools
import signal
import sys
from typing import Any, Callable, Dict, List, Optional, Union

from .types import HTMLResponse, JSONResponse, Request, Response, RouteHandler

try:
    from catzilla._catzilla import Server as _Server
    from catzilla._catzilla import send_response
except ImportError:
    raise ImportError(
        "Failed to import C extension. Make sure Catzilla is properly installed."
    )


class Router:
    """A collection of routes with their handlers"""

    def __init__(self):
        self.routes = {}

    def add_route(self, method: str, path: str, handler: RouteHandler) -> None:
        """Add a route handler"""
        if method not in self.routes:
            self.routes[method] = {}
        self.routes[method][path] = handler

    def get(self, path):
        """Register a GET route handler"""

        def decorator(handler):
            self.add_route("GET", path, handler)
            return handler

        return decorator

    def post(self, path):
        """Register a POST route handler"""

        def decorator(handler):
            self.add_route("POST", path, handler)
            return handler

        return decorator

    def put(self, path):
        """Register a PUT route handler"""

        def decorator(handler):
            self.add_route("PUT", path, handler)
            return handler

        return decorator

    def delete(self, path):
        """Register a DELETE route handler"""

        def decorator(handler):
            self.add_route("DELETE", path, handler)
            return handler

        return decorator

    def patch(self, path):
        """Register a PATCH route handler"""

        def decorator(handler):
            self.add_route("PATCH", path, handler)
            return handler

        return decorator


class App:
    """Main Catzilla application"""

    def __init__(self):
        self.server = _Server()
        self.router = Router()
        self._setup_signal_handlers()

    def _setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown"""
        self.original_sigint_handler = signal.getsignal(signal.SIGINT)
        self.original_sigterm_handler = signal.getsignal(signal.SIGTERM)

        def signal_handler(sig, frame):
            print("\nShutting down Catzilla server...")
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

    def _handle_request(self, client, method, path, body):
        """Internal request handler that bridges C and Python"""
        # Create a request object
        request = Request(method=method, path=path, body=body, client=client)

        # Look up the handler
        handler = None
        if method in self.router.routes and path in self.router.routes[method]:
            handler = self.router.routes[method][path]

        if handler:
            try:
                # Call the handler and get a response
                response = handler(request)
                if not isinstance(response, Response):
                    response = Response(
                        status_code=200,
                        # content_type="text/plain",
                        content_type="application/json",
                        body=str(response),
                    )
                # Send the response
                response.send(client)
            except Exception as e:
                # Handle exceptions by returning a 500 response
                import traceback

                err_resp = Response(
                    status_code=500,
                    content_type="text/plain",
                    body=f"Internal Server Error: {str(e)}",
                )
                err_resp.send(client)
                traceback.print_exc()
        else:
            # No handler found
            not_found = Response(
                status_code=404,
                content_type="text/plain",
                body=f"Not Found: {method} {path}",
            )
            not_found.send(client)

    def get(self, path):
        """Register a GET route handler"""
        return self.router.get(path)

    def post(self, path):
        """Register a POST route handler"""
        return self.router.post(path)

    def put(self, path):
        """Register a PUT route handler"""
        return self.router.put(path)

    def delete(self, path):
        """Register a DELETE route handler"""
        return self.router.delete(path)

    def patch(self, path):
        """Register a PATCH route handler"""
        return self.router.patch(path)

    def listen(self, port: int, host: str = "0.0.0.0"):
        """Start the server"""
        print(f"Catzilla server starting on http://{host}:{port}")
        print("Press Ctrl+C to stop the server")

        # Add our Python handler for all registered routes
        for method, paths in self.router.routes.items():
            for path in paths:
                self.server.add_route(method, path, self._handle_request)

        # Start the server
        self.server.listen(port, host)

    def stop(self):
        """Stop the server"""
        self.server.stop()
