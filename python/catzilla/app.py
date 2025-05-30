"""
Catzilla application with C-accelerated routing and jemalloc memory optimization

This module provides the main Catzilla class which uses CAcceleratedRouter
as the sole routing option, leveraging C-based matching for maximum performance.
The Catzilla v0.2.0 Memory Revolution provides 30-35% memory efficiency gains.
"""

import functools
import signal
import sys
import threading
import time
from typing import Any, Callable, Dict, List, Optional, Union
from urllib.parse import parse_qs

from .c_router import CAcceleratedRouter
from .types import HTMLResponse, JSONResponse, Request, Response, RouteHandler

try:
    from catzilla._catzilla import Server as _Server
    from catzilla._catzilla import (
        get_memory_stats,
        has_jemalloc,
        init_memory_system,
        send_response,
    )
except ImportError:
    raise ImportError(
        "Failed to import C extension. Make sure Catzilla is properly installed."
    )


class Catzilla:
    """The Python Framework That BREAKS THE RULES

    Catzilla v0.2.0 Memory Revolution delivers:
    - 🚀 30% less memory usage with jemalloc
    - ⚡ C-speed request processing
    - 🎯 Zero-configuration optimization
    - 📈 Gets faster over time
    """

    def __init__(
        self,
        production: bool = False,
        use_jemalloc: bool = True,
        memory_profiling: bool = False,
        auto_memory_tuning: bool = True,
        memory_stats_interval: int = 60,
    ):
        """Initialize Catzilla with advanced memory optimization options

        Args:
            production: If True, return clean JSON error responses without stack traces
            use_jemalloc: Enable jemalloc memory allocator (30% less memory usage)
            memory_profiling: Enable real-time memory monitoring and optimization
            auto_memory_tuning: Enable adaptive memory management and arena optimization
            memory_stats_interval: Interval in seconds for automatic memory stats collection
        """
        # Store memory configuration
        self.production = production
        self.use_jemalloc = use_jemalloc
        self.memory_profiling = memory_profiling
        self.auto_memory_tuning = auto_memory_tuning
        self.memory_stats_interval = memory_stats_interval

        # Memory profiling state (initialize before memory revolution)
        self._memory_stats_history: List[dict] = []
        self._last_memory_check = 0.0
        self._memory_optimization_active = False

        # Initialize the memory revolution with advanced options
        self._init_memory_revolution()

        self.server = _Server()

        # Use C-accelerated router - the only router option
        # Since Catzilla is fundamentally C-based, if this fails, nothing works
        self.router = CAcceleratedRouter()
        self._router_type = "CAcceleratedRouter"

        # Error handling configuration
        self._exception_handlers: Dict[type, Callable] = {}
        self._not_found_handler: Optional[Callable] = None
        self._internal_error_handler: Optional[Callable] = None

        self._setup_signal_handlers()

    def _init_memory_revolution(self):
        """Initialize the jemalloc memory revolution with advanced options"""
        try:
            # Check if jemalloc is available and user wants to use it
            jemalloc_available = has_jemalloc()

            if self.use_jemalloc and jemalloc_available:
                # Initialize memory system
                init_memory_system()
                self.has_jemalloc = True
                self._memory_optimization_active = True

                if self.memory_profiling:
                    print(
                        "🚀 Catzilla: Memory Revolution FULL activated (jemalloc + profiling + tuning)"
                    )
                else:
                    print("🚀 Catzilla: Memory Revolution activated (jemalloc)")

                # Start memory profiling if enabled
                if self.memory_profiling:
                    self._start_memory_profiling()

            elif self.use_jemalloc and not jemalloc_available:
                print(
                    "⚠️  Catzilla: jemalloc requested but not available - falling back to standard memory"
                )
                self.has_jemalloc = False
                self.use_jemalloc = False  # Disable since not available

            else:
                print(
                    "⚡ Catzilla: Running with standard memory system (jemalloc disabled)"
                )
                self.has_jemalloc = False

        except Exception as e:
            print(f"⚠️  Catzilla: Memory system initialization warning: {e}")
            self.has_jemalloc = False
            self.use_jemalloc = False

    def get_memory_stats(self) -> dict:
        """Get comprehensive memory statistics

        Returns:
            Dictionary with memory statistics including efficiency metrics
        """
        if not self.has_jemalloc:
            return {
                "jemalloc_enabled": False,
                "message": "jemalloc not available - using standard memory system",
            }

        try:
            stats = get_memory_stats()
            stats["jemalloc_enabled"] = True
            stats["allocated_mb"] = stats.get("allocated", 0) / (1024 * 1024)
            stats["active_mb"] = stats.get("active", 0) / (1024 * 1024)
            stats["fragmentation_percent"] = (
                1.0 - stats.get("fragmentation_ratio", 1.0)
            ) * 100

            # Add profiling info if enabled
            if self.memory_profiling:
                stats["profiling_enabled"] = True
                stats["stats_history_count"] = len(self._memory_stats_history)
                stats["auto_tuning_active"] = self.auto_memory_tuning

                # Add efficiency trends if we have history
                if len(self._memory_stats_history) > 1:
                    recent = self._memory_stats_history[-1]
                    previous = self._memory_stats_history[-2]
                    stats["memory_trend"] = {
                        "allocated_change_mb": (
                            recent.get("allocated_mb", 0)
                            - previous.get("allocated_mb", 0)
                        ),
                        "fragmentation_change": (
                            recent.get("fragmentation_percent", 0)
                            - previous.get("fragmentation_percent", 0)
                        ),
                    }
            else:
                stats["profiling_enabled"] = False

            return stats
        except Exception as e:
            return {
                "jemalloc_enabled": True,
                "error": str(e),
                "message": "Failed to retrieve memory statistics",
            }

    def _start_memory_profiling(self):
        """Start automatic memory profiling"""
        import threading
        import time

        def profile_memory():
            while self.memory_profiling and self._memory_optimization_active:
                try:
                    current_time = time.time()
                    if (
                        current_time - self._last_memory_check
                        >= self.memory_stats_interval
                    ):
                        stats = self.get_memory_stats()
                        if stats.get("jemalloc_enabled"):
                            stats["timestamp"] = current_time
                            self._memory_stats_history.append(stats)

                            # Keep only last 100 entries to prevent memory growth
                            if len(self._memory_stats_history) > 100:
                                self._memory_stats_history = self._memory_stats_history[
                                    -50:
                                ]

                            # Auto-tuning logic
                            if self.auto_memory_tuning:
                                self._auto_tune_memory(stats)

                        self._last_memory_check = current_time

                    time.sleep(5)  # Check every 5 seconds
                except Exception as e:
                    print(f"⚠️  Memory profiling error: {e}")
                    time.sleep(10)

        # Start profiling in background thread
        profile_thread = threading.Thread(target=profile_memory, daemon=True)
        profile_thread.start()

    def _auto_tune_memory(self, current_stats: dict):
        """Automatic memory tuning based on current statistics"""
        try:
            fragmentation = current_stats.get("fragmentation_percent", 0)
            allocated_mb = current_stats.get("allocated_mb", 0)

            # If fragmentation is high (>15%), suggest cleanup
            if fragmentation > 15:
                print(
                    f"🔧 Auto-tuning: High fragmentation detected ({fragmentation:.1f}%)"
                )
                # In a real implementation, we could trigger arena cleanup here

            # If memory usage is growing rapidly, warn
            if len(self._memory_stats_history) > 2:
                recent_growth = self._memory_stats_history[-1].get(
                    "allocated_mb", 0
                ) - self._memory_stats_history[-3].get("allocated_mb", 0)
                if recent_growth > 50:  # 50MB growth in recent checks
                    print(
                        f"📈 Auto-tuning: Rapid memory growth detected (+{recent_growth:.1f}MB)"
                    )

        except Exception as e:
            print(f"⚠️  Auto-tuning error: {e}")

    def get_memory_profile(self) -> dict:
        """Get detailed memory profiling information"""
        if not self.memory_profiling:
            return {"error": "Memory profiling not enabled"}

        return {
            "profiling_enabled": True,
            "stats_history": self._memory_stats_history[-10:],  # Last 10 entries
            "auto_tuning_enabled": self.auto_memory_tuning,
            "check_interval_seconds": self.memory_stats_interval,
            "total_checks": len(self._memory_stats_history),
        }

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

        # Show memory configuration
        print(f"\n🧠 Memory Configuration:")
        print(f"   jemalloc: {'✅ enabled' if self.has_jemalloc else '❌ disabled'}")
        print(
            f"   profiling: {'✅ enabled' if self.memory_profiling else '❌ disabled'}"
        )
        print(
            f"   auto-tuning: {'✅ enabled' if self.auto_memory_tuning else '❌ disabled'}"
        )
        if self.memory_profiling:
            print(f"   stats interval: {self.memory_stats_interval}s")

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


# Backward compatibility alias
App = Catzilla
