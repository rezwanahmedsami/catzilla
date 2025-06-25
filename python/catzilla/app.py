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


def _safe_print(message: str):
    """Print message with Windows console encoding safety"""
    try:
        print(message)
    except UnicodeEncodeError:
        # Fallback for Windows console - replace problematic Unicode
        safe_message = (
            message.replace("⚡", "[LIGHTNING]")
            .replace("⚠️", "[WARNING]")
            .replace("❌", "[ERROR]")
            .replace("✅", "[SUCCESS]")
            .replace("🔧", "[TOOL]")
            .replace("📊", "[CHART]")
            .replace("💾", "[DISK]")
            .replace("🚀", "[ROCKET]")
        )
        print(safe_message)


from .auto_validation import create_auto_validated_handler

# Import revolutionary Background Task System
from .background_tasks import (
    BackgroundTasks,
    EngineStats,
    TaskConfig,
    TaskPriority,
    TaskResult,
)
from .c_router import CAcceleratedRouter
from .decorators import (
    _clear_current_context,
    _get_current_context,
    _set_current_context,
)

# Import DI system for Phase 3 integration
from .dependency_injection import DIContainer, DIContext
from .integration import DIMiddleware, DIRouteEnhancer
from .middleware import ZeroAllocMiddleware
from .types import HTMLResponse, JSONResponse, Request, Response, RouteHandler

# Import logging system for beautiful startup banners and dev logging
from .ui import BannerRenderer, DevLogger, ProductionLogger, ServerInfoCollector

try:
    from catzilla._catzilla import Server as _Server
    from catzilla._catzilla import (  # New runtime allocator functions
        get_current_allocator,
        get_memory_stats,
        has_jemalloc,
        init_memory_system,
        init_memory_with_allocator,
        jemalloc_available,
        send_response,
        set_allocator,
    )
except ImportError as e:
    # Check if this is a jemalloc TLS error
    if "cannot allocate memory in static TLS block" in str(e):
        # Provide a helpful error message for jemalloc TLS issues
        import os
        import platform

        system = platform.system()
        error_msg = "\n====== JEMALLOC TLS ALLOCATION ERROR ======\n"

        if system == "Linux":
            error_msg += (
                "This error occurs when jemalloc is loaded after other libraries have consumed TLS space.\n\n"
                "To fix on Ubuntu/Debian:\n"
                "  export LD_PRELOAD=/lib/x86_64-linux-gnu/libjemalloc.so.2:$LD_PRELOAD\n\n"
                "To fix on RHEL/CentOS/Fedora:\n"
                "  export LD_PRELOAD=/usr/lib64/libjemalloc.so.2:$LD_PRELOAD\n\n"
                "For CI environments, add this line before running tests or applications.\n"
            )
        elif system == "Darwin":  # macOS
            error_msg += (
                "To fix on macOS:\n"
                "  # For Intel Macs\n"
                "  export DYLD_INSERT_LIBRARIES=/usr/local/lib/libjemalloc.dylib:$DYLD_INSERT_LIBRARIES\n\n"
                "  # For Apple Silicon Macs\n"
                "  export DYLD_INSERT_LIBRARIES=/opt/homebrew/lib/libjemalloc.dylib:$DYLD_INSERT_LIBRARIES\n\n"
            )
        elif system == "Windows":
            error_msg += (
                "To fix on Windows:\n"
                "  1. Install jemalloc via vcpkg:\n"
                "     vcpkg install jemalloc:x64-windows\n\n"
                "  2. Set environment variable:\n"
                "     set CATZILLA_JEMALLOC_PATH=C:\\vcpkg\\installed\\x64-windows\\bin\\jemalloc.dll\n\n"
                "  3. Or run: scripts\\jemalloc_helper.bat\n\n"
            )
        else:
            error_msg += (
                "This error requires preloading jemalloc before other libraries.\n"
                "See our documentation at docs/jemalloc_troubleshooting.md for platform-specific instructions.\n"
            )

        error_msg += "For detailed help: https://github.com/rezwanahmedsami/catzilla/blob/main/docs/jemalloc_troubleshooting.md"
        raise ImportError(error_msg) from e
    else:
        # General import error
        raise ImportError(
            "Failed to import C extension. Make sure Catzilla is properly installed. "
            f"Error details: {str(e)}"
        ) from e


class Catzilla:
    """The Python Framework That BREAKS THE RULES

    Catzilla v0.2.0 Memory Revolution delivers:
    - 🚀 30% less memory usage with jemalloc
    - ⚡ C-speed request processing
    - 🎯 Zero-configuration optimization
    - 📈 Gets faster over time
    """

    @staticmethod
    def jemalloc_available() -> bool:
        """Check if jemalloc is available in the current build and environment

        Returns:
            True if jemalloc is available and can be used, False otherwise

        Note:
            This is a static method that can be called before creating a Catzilla instance
            to check jemalloc availability. Useful for conditional initialization logic.
        """
        try:
            return jemalloc_available()
        except (ImportError, NameError):
            # C extension not available or function not found
            return False

    @staticmethod
    def get_available_allocators() -> list:
        """Get list of available memory allocators

        Returns:
            List of allocator names that are available in this build
        """
        allocators = ["malloc"]  # malloc is always available
        try:
            if jemalloc_available():
                allocators.append("jemalloc")
        except (ImportError, NameError):
            pass
        return allocators

    def __init__(
        self,
        production: bool = False,
        use_jemalloc: bool = True,
        memory_profiling: bool = False,
        auto_memory_tuning: bool = True,
        memory_stats_interval: int = 60,
        auto_validation: bool = True,
        enable_di: bool = True,
        di_container: Optional[DIContainer] = None,
        # New logging parameters
        show_banner: bool = True,
        log_requests: bool = None,  # Auto-detect based on production mode
        enable_colors: bool = True,
        show_request_details: bool = True,
    ):
        """Initialize Catzilla with advanced memory optimization and dependency injection

        Args:
            production: If True, return clean JSON error responses without stack traces
            use_jemalloc: Enable jemalloc memory allocator (30% less memory usage).
                         Uses runtime detection - automatically falls back to malloc if jemalloc
                         is not available in the current build or environment.
            memory_profiling: Enable real-time memory monitoring and optimization
            auto_memory_tuning: Enable adaptive memory management and arena optimization
            memory_stats_interval: Interval in seconds for automatic memory stats collection
            auto_validation: Enable FastAPI-style automatic validation (20x faster)
            enable_di: Enable revolutionary dependency injection system (5-8x faster DI)
            di_container: Custom DI container (creates new one if None)
            show_banner: Show beautiful startup banner with server information
            log_requests: Enable development request logging (auto-disabled in production)
            enable_colors: Enable colorized output for better developer experience
            show_request_details: Show detailed request information in development mode

        Note:
            The `use_jemalloc` parameter now uses conditional runtime support. If jemalloc
            is not available in the build (static linking disabled) or environment,
            Catzilla will automatically fall back to the standard malloc allocator
            without error, ensuring maximum compatibility across different deployments.

            Dependency injection provides C-speed service resolution with FastAPI-style
            decorators and seamless integration with the existing validation system.
        """
        # Store configuration
        self.production = production
        self.debug = not production  # For easier reference
        self.use_jemalloc = use_jemalloc
        self.memory_profiling = memory_profiling
        self.auto_memory_tuning = auto_memory_tuning
        self.memory_stats_interval = memory_stats_interval
        self.auto_validation = auto_validation

        # Logging configuration
        self.show_banner = show_banner
        self.log_requests = (
            log_requests if log_requests is not None else (not production)
        )
        self.enable_colors = enable_colors
        self.show_request_details = show_request_details

        # Initialize logging system
        self.banner_renderer = (
            BannerRenderer(enable_colors=enable_colors) if show_banner else None
        )
        self.server_info_collector = ServerInfoCollector(self) if show_banner else None

        # Initialize appropriate logger based on mode
        if self.log_requests and not production:
            self.logger = DevLogger(
                enable_colors=enable_colors, show_details=show_request_details
            )
        elif production:
            self.logger = ProductionLogger()
        else:
            self.logger = None

        # Route registration buffer for clean startup
        self._route_buffer = []
        self._routes_buffered = not production  # Buffer routes in development

        # Store DI configuration
        self.enable_di = enable_di
        self.di_container = di_container or DIContainer() if enable_di else None

        # Initialize DI middleware and enhancer
        if self.enable_di:
            self.di_middleware = DIMiddleware(self.di_container)
            self.di_enhancer = DIRouteEnhancer(self.di_container)

        # Initialize Zero-Allocation Middleware System
        self.middleware_system = None  # Will be initialized after app is complete
        self._registered_middlewares = []

        # Initialize Revolutionary Background Task System
        self.tasks: Optional[BackgroundTasks] = None
        self._task_system_enabled = False

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

        # Initialize Zero-Allocation Middleware System (after app is set up)
        self.middleware_system = ZeroAllocMiddleware(self)

        # Only set up signal handlers in the main thread to prevent threading issues
        try:
            self._setup_signal_handlers()
        except ValueError as e:
            if "signal only works in main thread" in str(e):
                # This is expected when creating Catzilla instances in worker threads
                # Signal handling is only needed in the main thread anyway
                pass
            else:
                raise

    def _init_memory_revolution(self):
        """Initialize the jemalloc memory revolution with advanced options"""
        try:
            # Check if jemalloc is available at runtime (from conditional compilation)
            jemalloc_runtime_available = jemalloc_available()

            if self.use_jemalloc and jemalloc_runtime_available:
                # Set allocator to jemalloc before initialization
                try:
                    set_allocator("jemalloc")
                    # Initialize memory system with jemalloc
                    # Initialize memory system quietly (no console output)
                    init_memory_system(1)  # 1 = quiet mode
                    self.has_jemalloc = True
                    self._memory_optimization_active = True

                    # Memory revolution messages removed for clean startup
                    # All jemalloc status is shown in the banner instead

                    # Start memory profiling if enabled
                    if self.memory_profiling:
                        self._start_memory_profiling()

                except RuntimeError as e:
                    _safe_print(f"⚠️  Catzilla: Failed to initialize with jemalloc: {e}")
                    _safe_print("⚠️  Catzilla: Falling back to standard memory system")
                    self.has_jemalloc = False
                    self.use_jemalloc = False
                    # Fallback to malloc quietly
                    set_allocator("malloc")
                    init_memory_system(1)  # 1 = quiet mode

            elif self.use_jemalloc and not jemalloc_runtime_available:
                _safe_print(
                    "⚠️  Catzilla: jemalloc requested but not available - falling back to standard memory"
                )
                self.has_jemalloc = False
                self.use_jemalloc = False  # Disable since not available
                # Use standard malloc quietly
                set_allocator("malloc")
                init_memory_system(1)  # 1 = quiet mode

            else:
                _safe_print(
                    "⚡ Catzilla: Running with standard memory system (jemalloc disabled)"
                )
                self.has_jemalloc = False
                # Use standard malloc quietly
                set_allocator("malloc")
                init_memory_system(1)  # 1 = quiet mode

        except Exception as e:
            _safe_print(f"⚠️  Catzilla: Memory system initialization warning: {e}")
            self.has_jemalloc = False
            self.use_jemalloc = False
            # Emergency fallback
            try:
                set_allocator("malloc")
                init_memory_system(1)  # 1 = quiet mode
            except:
                _safe_print(
                    "⚠️  Catzilla: Emergency fallback to uninitialized memory system"
                )
                pass

    def get_memory_stats(self) -> dict:
        """Get comprehensive memory statistics

        Returns:
            Dictionary with memory statistics including efficiency metrics
        """
        try:
            # Get current allocator information
            current_allocator = get_current_allocator()
            jemalloc_runtime_available = jemalloc_available()

            # Base stats always include allocator information
            base_stats = {
                "allocator": current_allocator,
                "jemalloc_available": jemalloc_runtime_available,
                "jemalloc_requested": self.use_jemalloc,
                "jemalloc_enabled": self.has_jemalloc,
            }

            if not self.has_jemalloc:
                base_stats.update(
                    {
                        "message": f"Using {current_allocator} memory system",
                        "jemalloc_reason": (
                            "disabled by user"
                            if not self.use_jemalloc
                            else "not available at runtime"
                        ),
                    }
                )
                return base_stats

            # Get detailed memory stats from C extension
            stats = get_memory_stats()
            stats.update(base_stats)

            # Add computed metrics
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
                "allocator": "unknown",
                "jemalloc_available": False,
                "jemalloc_requested": self.use_jemalloc,
                "jemalloc_enabled": False,
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
                    ) >= self.memory_stats_interval:
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
                    _safe_print(f"⚠️  Memory profiling error: {e}")
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
                _safe_print(
                    f"🔧 Auto-tuning: High fragmentation detected ({fragmentation:.1f}%)"
                )
                # In a real implementation, we could trigger arena cleanup here

            # If memory usage is growing rapidly, warn
            if len(self._memory_stats_history) > 2:
                recent_growth = self._memory_stats_history[-1].get(
                    "allocated_mb", 0
                ) - self._memory_stats_history[-3].get("allocated_mb", 0)
                if recent_growth > 50:  # 50MB growth in recent checks
                    _safe_print(
                        f"📈 Auto-tuning: Rapid memory growth detected (+{recent_growth:.1f}MB)"
                    )

        except Exception as e:
            _safe_print(f"⚠️  Auto-tuning error: {e}")

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
        import time

        # Start timing for request logging
        start_time = time.time()
        status_code = 200
        response_size = 0
        error_message = None

        try:
            # Get base path for routing (strip query string if present)
            base_path = path.split("?", 1)[0] if "?" in path else path
            query_string = path.split("?", 1)[1] if "?" in path else None

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
                        status_code = 415
                        err_resp = Response(
                            status_code=415,
                            content_type="text/plain",
                            body=f"Unsupported Media Type: {content_type}",
                            headers={
                                "X-Error-Detail": f"Content-Type {content_type} is not supported"
                            },
                        )
                        response_size = (
                            len(err_resp.body.encode("utf-8")) if err_resp.body else 0
                        )
                        err_resp.send(client)
                        return

                    # Call the handler with DI context management
                    if self.enable_di:
                        # Create DI context for this request
                        with self.di_container.resolution_context() as di_context:
                            _set_current_context(di_context)
                            try:
                                response = route.handler(request)
                            finally:
                                _clear_current_context()
                    else:
                        # No DI - call handler directly
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

                    # Capture response details for logging
                    status_code = response.status_code
                    response_size = (
                        len(response.body.encode("utf-8")) if response.body else 0
                    )

                    # Send the response
                    response.send(client)
                except Exception as e:
                    # Handle exceptions using the centralized error handling system
                    status_code = 500
                    error_message = str(e)
                    err_resp = self._handle_exception(request, e)
                    status_code = err_resp.status_code
                    response_size = (
                        len(err_resp.body.encode("utf-8")) if err_resp.body else 0
                    )
                    err_resp.send(client)
            else:
                if allowed_methods:
                    # Path exists but method not allowed
                    status_code = 405
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
                    response_size = (
                        len(not_allowed.body.encode("utf-8")) if not_allowed.body else 0
                    )
                    not_allowed.send(client)
                else:
                    # No route found - use custom 404 handler if set
                    status_code = 404
                    if self._not_found_handler:
                        try:
                            not_found_resp = self._not_found_handler(request)
                            status_code = not_found_resp.status_code
                            response_size = (
                                len(not_found_resp.body.encode("utf-8"))
                                if not_found_resp.body
                                else 0
                            )
                            not_found_resp.send(client)
                        except Exception as handler_error:
                            # 404 handler failed, fall back to default
                            status_code = 500
                            error_message = str(handler_error)
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
                            response_size = (
                                len(fallback_resp.body.encode("utf-8"))
                                if fallback_resp.body
                                else 0
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
                        response_size = (
                            len(not_found.body.encode("utf-8")) if not_found.body else 0
                        )
                        not_found.send(client)

        finally:
            # Log the request if logging is enabled
            if self.logger and self.log_requests:
                duration_ms = (time.time() - start_time) * 1000
                client_ip = getattr(client, "remote_addr", "127.0.0.1")

                self.logger.log_request(
                    method=method,
                    path=base_path,
                    status_code=status_code,
                    duration_ms=duration_ms,
                    response_size=response_size,
                    client_ip=client_ip,
                    error_message=error_message,
                    query_params=query_string,
                )

    def route(
        self,
        path: str,
        methods: List[str] = None,
        *,
        overwrite: bool = False,
        dependencies: Optional[List[str]] = None,
    ):
        """Register a route handler for multiple HTTP methods with optional dependency injection"""

        def decorator(handler: RouteHandler):
            # Apply dependency injection if enabled
            if self.enable_di:
                enhanced_handler = self.di_enhancer.enhance_route(handler, dependencies)
            else:
                enhanced_handler = handler

            # Apply auto-validation if enabled
            if self.auto_validation:
                validated_handler = create_auto_validated_handler(enhanced_handler)
            else:
                validated_handler = enhanced_handler

            # Register the (possibly auto-validated and DI-enhanced) handler
            return self.router.route(path, methods, overwrite=overwrite)(
                validated_handler
            )

        return decorator

    def get(
        self,
        path: str,
        *,
        overwrite: bool = False,
        dependencies: Optional[List[str]] = None,
        middleware: Optional[List[Callable]] = None,
    ):
        """Register a GET route handler with optional dependency injection and per-route middleware"""

        def decorator(handler: RouteHandler):
            # Buffer route registration for clean startup
            if self._routes_buffered:
                handler_name = getattr(handler, "__name__", "unknown")
                self._route_buffer.append(f"📍 GET     {path} → {handler_name}")

            # Apply dependency injection if enabled
            if self.enable_di:
                enhanced_handler = self.di_enhancer.enhance_route(handler, dependencies)
            else:
                enhanced_handler = handler

            # Apply auto-validation if enabled
            if self.auto_validation:
                validated_handler = create_auto_validated_handler(enhanced_handler)
            else:
                validated_handler = enhanced_handler

            return self.router.get(path, overwrite=overwrite, middleware=middleware)(
                validated_handler
            )

        return decorator

    def post(
        self,
        path: str,
        *,
        overwrite: bool = False,
        dependencies: Optional[List[str]] = None,
        middleware: Optional[List[Callable]] = None,
    ):
        """Register a POST route handler with optional dependency injection and per-route middleware"""

        def decorator(handler: RouteHandler):
            # Buffer route registration for clean startup
            if self._routes_buffered:
                handler_name = getattr(handler, "__name__", "unknown")
                self._route_buffer.append(f"📍 POST    {path} → {handler_name}")

            # Apply dependency injection if enabled
            if self.enable_di:
                enhanced_handler = self.di_enhancer.enhance_route(handler, dependencies)
            else:
                enhanced_handler = handler

            # Apply auto-validation if enabled
            if self.auto_validation:
                validated_handler = create_auto_validated_handler(enhanced_handler)
            else:
                validated_handler = enhanced_handler

            return self.router.post(path, overwrite=overwrite, middleware=middleware)(
                validated_handler
            )

        return decorator

    def put(
        self,
        path: str,
        *,
        overwrite: bool = False,
        dependencies: Optional[List[str]] = None,
        middleware: Optional[List[Callable]] = None,
    ):
        """Register a PUT route handler with optional dependency injection and per-route middleware"""

        def decorator(handler: RouteHandler):
            # Buffer route registration for clean startup
            if self._routes_buffered:
                handler_name = getattr(handler, "__name__", "unknown")
                self._route_buffer.append(f"📍 PUT     {path} → {handler_name}")

            # Apply dependency injection if enabled
            if self.enable_di:
                enhanced_handler = self.di_enhancer.enhance_route(handler, dependencies)
            else:
                enhanced_handler = handler

            # Apply auto-validation if enabled
            if self.auto_validation:
                validated_handler = create_auto_validated_handler(enhanced_handler)
            else:
                validated_handler = enhanced_handler

            return self.router.put(path, overwrite=overwrite, middleware=middleware)(
                validated_handler
            )

        return decorator

    def delete(
        self,
        path: str,
        *,
        overwrite: bool = False,
        dependencies: Optional[List[str]] = None,
        middleware: Optional[List[Callable]] = None,
    ):
        """Register a DELETE route handler with optional dependency injection and per-route middleware"""

        def decorator(handler: RouteHandler):
            # Buffer route registration for clean startup
            if self._routes_buffered:
                handler_name = getattr(handler, "__name__", "unknown")
                self._route_buffer.append(f"📍 DELETE  {path} → {handler_name}")

            # Apply dependency injection if enabled
            if self.enable_di:
                enhanced_handler = self.di_enhancer.enhance_route(handler, dependencies)
            else:
                enhanced_handler = handler

            # Apply auto-validation if enabled
            if self.auto_validation:
                validated_handler = create_auto_validated_handler(enhanced_handler)
            else:
                validated_handler = enhanced_handler

            return self.router.delete(path, overwrite=overwrite, middleware=middleware)(
                validated_handler
            )

        return decorator

    def patch(
        self,
        path: str,
        *,
        overwrite: bool = False,
        dependencies: Optional[List[str]] = None,
        middleware: Optional[List[Callable]] = None,
    ):
        """Register a PATCH route handler with optional dependency injection and per-route middleware"""

        def decorator(handler: RouteHandler):
            # Apply dependency injection if enabled
            if self.enable_di:
                enhanced_handler = self.di_enhancer.enhance_route(handler, dependencies)
            else:
                enhanced_handler = handler

            # Apply auto-validation if enabled
            if self.auto_validation:
                validated_handler = create_auto_validated_handler(enhanced_handler)
            else:
                validated_handler = enhanced_handler

            return self.router.patch(path, overwrite=overwrite, middleware=middleware)(
                validated_handler
            )

        return decorator

    def _call_c_extension(self, method_name: str, *args) -> Any:
        """Call C extension method with fallback handling"""
        try:
            # Try to call C extension method
            # This would be implemented in the actual C extension
            # For now, return None to indicate C extension is not available
            return None
        except Exception:
            # C extension not available or method failed
            return None

    # ========================================================================
    # MIDDLEWARE SYSTEM METHODS
    # ========================================================================

    def middleware(
        self,
        priority: int = 50,
        pre_route: bool = True,
        post_route: bool = False,
        name: Optional[str] = None,
    ):
        """Register middleware with the Zero-Allocation Middleware System

        Args:
            priority: Middleware priority (0-100, higher numbers run first)
            pre_route: Whether to run before route handling
            post_route: Whether to run after route handling
            name: Optional middleware name for debugging
        """

        def decorator(handler: Callable):
            # Register with the middleware system
            self.middleware_system.register_middleware(
                handler,
                priority=priority,
                pre_route=pre_route,
                post_route=post_route,
                name=name or handler.__name__,
            )
            # Keep track of registered middlewares
            self._registered_middlewares.append(
                {
                    "handler": handler,
                    "priority": priority,
                    "pre_route": pre_route,
                    "post_route": post_route,
                    "name": name or handler.__name__,
                }
            )
            return handler

        return decorator

    def get_middleware_stats(self) -> Dict[str, Any]:
        """Get middleware performance statistics"""
        return self.middleware_system.get_stats()

    def reset_middleware_stats(self):
        """Reset middleware performance statistics"""
        self.middleware_system.reset_stats()

    # ========================================================================
    # DEPENDENCY INJECTION METHODS
    # ========================================================================

    def register_service(
        self,
        name: str,
        factory,
        scope: str = "singleton",
        dependencies: Optional[List[str]] = None,
    ) -> int:
        """
        Register a service with the DI container

        Args:
            name: Service name/identifier
            factory: Service factory (class or function)
            scope: Service lifecycle ('singleton', 'transient', 'scoped', 'request')
            dependencies: List of dependency service names

        Returns:
            0 on success, -1 on failure
        """
        if not self.enable_di:
            raise RuntimeError(
                "Dependency injection is not enabled. Set enable_di=True in Catzilla constructor."
            )

        return self.di_container.register(name, factory, scope, dependencies)

    def resolve_service(self, name: str, context: Optional[DIContext] = None):
        """
        Resolve a service from the DI container

        Args:
            name: Service name to resolve
            context: Optional DI context for request-scoped services

        Returns:
            Service instance
        """
        if not self.enable_di:
            raise RuntimeError(
                "Dependency injection is not enabled. Set enable_di=True in Catzilla constructor."
            )

        return self.di_container.resolve(name, context)

    def create_di_context(self) -> DIContext:
        """Create a new DI context for request-scoped services"""
        if not self.enable_di:
            raise RuntimeError(
                "Dependency injection is not enabled. Set enable_di=True in Catzilla constructor."
            )

        return self.di_container.create_context()

    def get_di_container(self) -> Optional[DIContainer]:
        """Get the DI container instance"""
        return self.di_container

    def list_services(self) -> List[str]:
        """List all registered services in the DI container"""
        if not self.enable_di:
            return []

        return self.di_container.list_services()

    # ========================================================================
    # REVOLUTIONARY BACKGROUND TASK SYSTEM
    # ========================================================================

    def enable_background_tasks(
        self,
        workers: Optional[int] = None,
        min_workers: int = 2,
        max_workers: Optional[int] = None,
        queue_size: int = 10000,
        enable_auto_scaling: bool = True,
        memory_pool_mb: int = 500,
        enable_c_compilation: bool = True,
        enable_profiling: bool = False,
    ) -> None:
        """Enable revolutionary background task system with C-speed execution

        Args:
            workers: Number of worker threads (auto-detected if None)
            min_workers: Minimum number of workers for auto-scaling
            max_workers: Maximum number of workers for auto-scaling (auto-detected if None)
            queue_size: Maximum queue size for tasks
            enable_auto_scaling: Enable intelligent auto-scaling based on queue pressure
            memory_pool_mb: Memory pool size in MB for task execution with jemalloc optimization
            enable_c_compilation: Enable automatic compilation of simple tasks to C
            enable_profiling: Enable real-time performance monitoring

        Note:
            This creates a revolutionary task system that automatically compiles simple
            Python functions to C for maximum performance while maintaining full Python
            compatibility for complex tasks. Memory is optimized using jemalloc arenas.
        """
        if self.tasks is not None:
            raise RuntimeError("Background task system already enabled")

        # Use optimized memory pool if jemalloc is available
        if self.has_jemalloc:
            memory_pool_mb = int(
                memory_pool_mb * 1.5
            )  # 50% larger pool with jemalloc efficiency

        self.tasks = BackgroundTasks(
            workers=workers,
            min_workers=min_workers,
            max_workers=max_workers,
            queue_size=queue_size,
            enable_auto_scaling=enable_auto_scaling,
            memory_pool_mb=memory_pool_mb,
            enable_c_compilation=enable_c_compilation,
            enable_profiling=enable_profiling,
        )
        self._task_system_enabled = True

        # Register cleanup on shutdown
        import atexit

        atexit.register(self._shutdown_tasks)

        _safe_print("🚀 Catzilla: Revolutionary Background Task System enabled")
        _safe_print(f"   Workers: {workers or 'auto-detected'}")
        _safe_print(
            f"   C compilation: {'✅ enabled' if enable_c_compilation else '❌ disabled'}"
        )
        _safe_print(
            f"   Auto-scaling: {'✅ enabled' if enable_auto_scaling else '❌ disabled'}"
        )
        _safe_print(
            f"   Memory pool: {memory_pool_mb}MB ({'jemalloc optimized' if self.has_jemalloc else 'standard'})"
        )

    def add_task(
        self,
        func: Callable[..., Any],
        *args,
        priority: TaskPriority = TaskPriority.NORMAL,
        delay_ms: int = 0,
        max_retries: int = 3,
        timeout_ms: int = 30000,
        compile_to_c: Optional[bool] = None,
        **kwargs,
    ) -> TaskResult:
        """Add task to the background task system

        Args:
            func: Function to execute as background task
            *args: Arguments to pass to the function
            priority: Task priority level (CRITICAL, HIGH, NORMAL, LOW)
            delay_ms: Delay before execution in milliseconds
            max_retries: Maximum retry attempts on failure
            timeout_ms: Task execution timeout in milliseconds
            compile_to_c: Force C compilation (None = auto-detect)
            **kwargs: Keyword arguments to pass to the function

        Returns:
            TaskResult object for tracking completion and getting results

        Raises:
            RuntimeError: If background task system is not enabled
        """
        if not self._task_system_enabled or self.tasks is None:
            raise RuntimeError(
                "Background task system not enabled. Call enable_background_tasks() first."
            )

        return self.tasks.add_task(
            func,
            *args,
            priority=priority,
            delay_ms=delay_ms,
            max_retries=max_retries,
            timeout_ms=timeout_ms,
            compile_to_c=compile_to_c,
            **kwargs,
        )

    def task(
        self,
        priority: TaskPriority = TaskPriority.NORMAL,
        compile_to_c: bool = True,
        **config_kwargs,
    ):
        """Decorator to register tasks with automatic C compilation

        Args:
            priority: Task priority level
            compile_to_c: Enable automatic C compilation for simple tasks
            **config_kwargs: Additional task configuration

        Returns:
            Decorator function

        Usage:
            @app.task(priority=TaskPriority.HIGH, compile_to_c=True)
            def send_notification(user_id: int, message: str):
                # Simple functions automatically compiled to C for maximum speed
                log_notification(user_id, message)
                return {"status": "sent"}
        """
        if not self._task_system_enabled or self.tasks is None:
            raise RuntimeError(
                "Background task system not enabled. Call enable_background_tasks() first."
            )

        return self.tasks.task(
            priority=priority, compile_to_c=compile_to_c, **config_kwargs
        )

    def get_task_stats(self) -> EngineStats:
        """Get comprehensive task system performance statistics

        Returns:
            EngineStats object with detailed performance metrics

        Raises:
            RuntimeError: If background task system is not enabled
        """
        if not self._task_system_enabled or self.tasks is None:
            raise RuntimeError("Background task system not enabled")

        return self.tasks.get_stats()

    def _shutdown_tasks(self):
        """Graceful shutdown of background task system"""
        if self.tasks:
            try:
                self.tasks.shutdown(wait_for_completion=True, timeout=30.0)
                _safe_print("🚀 Catzilla: Background task system shutdown complete")
            except Exception as e:
                _safe_print(f"⚠️  Catzilla: Error during task system shutdown: {e}")
            finally:
                self.tasks = None
                self._task_system_enabled = False

    # ========================================================================
    # ROUTER GROUP INTEGRATION
    # ========================================================================

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

    def _display_buffered_routes(self):
        """Display buffered route registrations in a clean format"""
        if not self._route_buffer or not self.debug:
            return

        print()  # Empty line before routes
        for route_log in self._route_buffer:
            print(route_log)

        # Clear the buffer after displaying
        self._route_buffer.clear()

        print()  # Empty line after routes

    def listen(self, port: int = 8000, host: str = "0.0.0.0"):
        """Start the server with beautiful startup banner"""

        # Show beautiful startup banner
        if self.banner_renderer and self.server_info_collector:
            try:
                server_info = self.server_info_collector.collect(host, port)
                if self.debug:
                    banner = self.banner_renderer.render_startup_banner(server_info)
                else:
                    banner = self.banner_renderer.render_minimal_banner(server_info)
                print(banner)
            except Exception as e:
                # Fallback to simple startup message if banner fails
                mode = "DEVELOPMENT" if self.debug else "PRODUCTION"
                print(f"\n🐱 Catzilla v0.1.0 - {mode}")
                print(f"Server starting on http://{host}:{port}")
                if self.debug:
                    print(f"Banner error: {e}")
        else:
            # Simple startup message
            mode = "DEVELOPMENT" if self.debug else "PRODUCTION"
            print(f"\n🐱 Catzilla v0.1.0 - {mode}")
            print(f"Server starting on http://{host}:{port}")

        # Display buffered route registrations after banner
        self._display_buffered_routes()

        # Log server startup
        if self.logger:
            mode = "development" if self.debug else "production"
            self.logger.log_server_start(host, port, mode)

        # Routes are already logged during registration, no need to log again here

        # Add our Python handler for all registered routes
        for route in self.router.routes():
            self.server.add_route(route["method"], route["path"], self._handle_request)

        # Display buffered routes after banner
        self._display_buffered_routes()

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

    def get_allocator_info(self) -> dict:
        """Get detailed allocator information and capabilities

        Returns:
            Dictionary with allocator information and runtime capabilities
        """
        try:
            return {
                "current_allocator": get_current_allocator(),
                "jemalloc_available": jemalloc_available(),
                "jemalloc_requested": self.use_jemalloc,
                "jemalloc_enabled": self.has_jemalloc,
                "memory_profiling": self.memory_profiling,
                "auto_memory_tuning": self.auto_memory_tuning,
                "memory_stats_interval": self.memory_stats_interval,
                "can_switch_allocator": False,  # Cannot switch after initialization
                "build_supports_jemalloc": jemalloc_available(),
                "status": (
                    "initialized"
                    if self.has_jemalloc or not self.use_jemalloc
                    else "fallback"
                ),
            }
        except Exception as e:
            return {
                "current_allocator": "unknown",
                "jemalloc_available": False,
                "jemalloc_requested": self.use_jemalloc,
                "jemalloc_enabled": False,
                "error": str(e),
                "status": "error",
            }
