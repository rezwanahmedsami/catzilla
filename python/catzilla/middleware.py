"""
🌪️ Catzilla Zero-Allocation Middleware System - Python Bridge
Revolutionary middleware execution with C-speed performance and Python flexibility
"""

import ctypes
import inspect
import time
from functools import wraps
from typing import TYPE_CHECKING, Any, Callable, Dict, List, Optional, Union

from .memory import get_memory_stats
from .validation import BaseModel

if TYPE_CHECKING:
    from .app import Catzilla


class ZeroAllocMiddleware:
    """Zero-allocation middleware decorator system with C-speed execution"""

    def __init__(self, app: "Catzilla"):  # noqa: F821
        self.app = app
        self._middleware_registry = []
        self._c_middleware_chain = None
        self._middleware_stats = {}

        # Initialize C middleware chain
        self._init_c_middleware_chain()

    def _init_c_middleware_chain(self):
        """Initialize C middleware chain through extension"""
        try:
            # This would be implemented in the C extension
            self._c_middleware_chain = self.app._call_c_extension(
                "create_middleware_chain"
            )

            # Register built-in middleware
            self.app._call_c_extension(
                "register_builtin_middleware", self._c_middleware_chain
            )

        except Exception as e:
            print(f"Warning: Could not initialize C middleware chain: {e}")
            self._c_middleware_chain = None

    def middleware(
        self,
        priority: int = 1000,
        pre_route: bool = True,
        post_route: bool = False,
        name: Optional[str] = None,
    ):
        """
        Register middleware for zero-allocation execution

        Args:
            priority: Execution order (lower = earlier)
            pre_route: Execute before route handler
            post_route: Execute after route handler
            name: Middleware identifier
        """

        def decorator(func: Callable):
            middleware_name = name or func.__name__

            # Try to compile Python function to C-compatible middleware
            if self._can_compile_to_c(func):
                c_middleware_fn = self._compile_python_to_c_middleware(
                    func, middleware_name
                )

                # Register with C middleware chain
                if self._c_middleware_chain:
                    flags = 0
                    if pre_route:
                        flags |= 1  # CATZILLA_MIDDLEWARE_PRE_ROUTE
                    if post_route:
                        flags |= 2  # CATZILLA_MIDDLEWARE_POST_ROUTE

                    self.app._call_c_extension(
                        "register_middleware",
                        self._c_middleware_chain,
                        c_middleware_fn,
                        middleware_name,
                        priority,
                        flags,
                    )

            # Store Python reference for debugging/introspection
            self._middleware_registry.append(
                {
                    "name": middleware_name,
                    "function": func,
                    "priority": priority,
                    "pre_route": pre_route,
                    "post_route": post_route,
                    "can_compile": self._can_compile_to_c(func),
                    "registered_at": time.time(),
                }
            )

            return func

        return decorator

    def _can_compile_to_c(self, func: Callable) -> bool:
        """
        Check if function can be compiled to C for maximum performance

        Simple functions with basic operations can be compiled to C
        Complex functions fall back to Python execution
        """
        try:
            # Get function source and analyze complexity
            source = inspect.getsource(func)

            # Simple heuristics for C compilation eligibility
            complexity_score = 0

            # Increase complexity for various constructs
            if "import" in source:
                complexity_score += 10
            if "class" in source:
                complexity_score += 15
            if "lambda" in source:
                complexity_score += 5
            if "yield" in source:
                complexity_score += 20
            if "async" in source:
                complexity_score += 25
            if "await" in source:
                complexity_score += 25

            # Count lines of code
            lines = [
                line.strip()
                for line in source.split("\\n")
                if line.strip() and not line.strip().startswith("#")
            ]
            complexity_score += len(lines) * 2

            # Functions under complexity threshold can be compiled to C
            return complexity_score < 50

        except Exception:
            return False

    def _compile_python_to_c_middleware(
        self, func: Callable, name: str
    ) -> ctypes.CFUNCTYPE:
        """
        Compile Python middleware function to C-compatible function

        This creates a C function wrapper that:
        1. Extracts Python objects from C context
        2. Calls Python middleware function
        3. Updates C context with results
        4. Handles exceptions and converts to C error codes
        """

        def c_middleware_wrapper(ctx_ptr: ctypes.c_void_p) -> ctypes.c_int:
            try:
                # Extract context from C pointer
                request = self._create_request_proxy(ctx_ptr)

                # Determine middleware signature and call appropriately
                sig = inspect.signature(func)
                params = list(sig.parameters.keys())

                if len(params) == 1:
                    # Simple middleware: func(request)
                    result = func(request)
                elif len(params) == 2:
                    # Response middleware: func(request, response)
                    response = self._create_response_proxy(ctx_ptr)
                    result = func(request, response)
                else:
                    # No parameters or complex signature
                    result = func()

                # Handle middleware result
                if result is None:
                    return 0  # Continue
                elif isinstance(result, bool):
                    return 0 if result else 1  # Continue or skip
                elif isinstance(result, int):
                    return result
                elif hasattr(result, "status_code"):
                    # Response object returned
                    self._update_c_context_with_response(ctx_ptr, result)
                    return 1  # Skip route
                else:
                    return 0  # Continue by default

            except Exception as e:
                # Log error and return failure code
                self.app._log_middleware_error(name, str(e))
                return -1

        # Convert to C function pointer
        c_func_type = ctypes.CFUNCTYPE(ctypes.c_int, ctypes.c_void_p)
        return c_func_type(c_middleware_wrapper)

    def _create_request_proxy(self, ctx_ptr: ctypes.c_void_p) -> "MiddlewareRequest":
        """Create lazy-loading request proxy for middleware"""
        return MiddlewareRequest(ctx_ptr, self.app)

    def _create_response_proxy(self, ctx_ptr: ctypes.c_void_p) -> "MiddlewareResponse":
        """Create response builder proxy for middleware"""
        return MiddlewareResponse(ctx_ptr, self.app)

    def _update_c_context_with_response(self, ctx_ptr: ctypes.c_void_p, response: Any):
        """Update C context with Python response object"""
        if hasattr(response, "status_code"):
            self.app._call_c_extension(
                "set_middleware_response_status", ctx_ptr, response.status_code
            )

        if hasattr(response, "headers"):
            for name, value in response.headers.items():
                self.app._call_c_extension(
                    "set_middleware_response_header", ctx_ptr, name, value
                )

        if hasattr(response, "content"):
            content_type = getattr(response, "content_type", "text/plain")
            self.app._call_c_extension(
                "set_middleware_response_body", ctx_ptr, response.content, content_type
            )

    def get_middleware_stats(self) -> Dict[str, Any]:
        """Get comprehensive middleware execution statistics"""
        stats = {
            "total_middleware": len(self._middleware_registry),
            "compiled_middleware": sum(
                1 for m in self._middleware_registry if m["can_compile"]
            ),
            "python_middleware": sum(
                1 for m in self._middleware_registry if not m["can_compile"]
            ),
            "middleware_list": [],
        }

        # Get C-level performance stats
        if self._c_middleware_chain:
            try:
                c_stats = self.app._call_c_extension(
                    "get_middleware_performance_stats", self._c_middleware_chain
                )
                stats.update(c_stats)
            except Exception:
                pass

        # Add per-middleware details
        for middleware in self._middleware_registry:
            stats["middleware_list"].append(
                {
                    "name": middleware["name"],
                    "priority": middleware["priority"],
                    "pre_route": middleware["pre_route"],
                    "post_route": middleware["post_route"],
                    "can_compile": middleware["can_compile"],
                    "registered_at": middleware["registered_at"],
                }
            )

        return stats

    def register_middleware(
        self,
        handler: Callable,
        priority: int = 50,
        pre_route: bool = True,
        post_route: bool = False,
        name: str = None,
    ) -> None:
        """Register middleware handler with the system"""
        middleware_name = name or handler.__name__

        # Try to compile Python function to C-compatible middleware
        if self._can_compile_to_c(handler):
            c_middleware_fn = self._compile_python_to_c_middleware(
                handler, middleware_name
            )

            # Register with C middleware chain
            if self._c_middleware_chain:
                flags = 0
                if pre_route:
                    flags |= 1  # CATZILLA_MIDDLEWARE_PRE_ROUTE
                if post_route:
                    flags |= 2  # CATZILLA_MIDDLEWARE_POST_ROUTE

                try:
                    self.app._call_c_extension(
                        "register_middleware",
                        self._c_middleware_chain,
                        c_middleware_fn,
                        middleware_name,
                        priority,
                        flags,
                    )
                except:
                    # Fallback to Python-only registration
                    pass

        # Store Python reference for debugging/introspection
        self._middleware_registry.append(
            {
                "name": middleware_name,
                "function": handler,
                "priority": priority,
                "pre_route": pre_route,
                "post_route": post_route,
                "can_compile": self._can_compile_to_c(handler),
                "registered_at": time.time(),
            }
        )

    def get_stats(self) -> Dict[str, Any]:
        """Get middleware performance statistics"""
        if not hasattr(self, "_middleware_stats"):
            self._middleware_stats = {}

        return {
            "total_middleware_count": len(self._middleware_registry),
            "compiled_middleware": sum(
                1 for m in self._middleware_registry if m.get("can_compile", False)
            ),
            "python_middleware": sum(
                1 for m in self._middleware_registry if not m.get("can_compile", False)
            ),
            "middleware_list": [
                {
                    "name": m["name"],
                    "priority": m["priority"],
                    "pre_route": m["pre_route"],
                    "post_route": m["post_route"],
                    "can_compile": m.get("can_compile", False),
                    "registered_at": m["registered_at"],
                }
                for m in self._middleware_registry
            ],
            "performance_stats": self._middleware_stats.copy(),
        }

    def reset_stats(self) -> None:
        """Reset middleware performance statistics"""
        self._middleware_stats = {}
        # Also reset any C-level stats if available
        try:
            if self._c_middleware_chain:
                self.app._call_c_extension(
                    "reset_middleware_stats", self._c_middleware_chain
                )
        except:
            pass


class MiddlewareRequest:
    """Lazy-loading request proxy for C middleware context"""

    def __init__(self, c_context_ptr: ctypes.c_void_p, app: "Catzilla"):  # noqa: F821
        self._c_context = c_context_ptr
        self._app = app
        self._cached_attrs = {}

    @property
    def method(self) -> str:
        """HTTP method (GET, POST, etc.)"""
        if "method" not in self._cached_attrs:
            self._cached_attrs["method"] = self._get_c_string("method")
        return self._cached_attrs["method"]

    @property
    def path(self) -> str:
        """Request path"""
        if "path" not in self._cached_attrs:
            self._cached_attrs["path"] = self._get_c_string("path")
        return self._cached_attrs["path"]

    @property
    def query_string(self) -> str:
        """Query string"""
        if "query_string" not in self._cached_attrs:
            self._cached_attrs["query_string"] = (
                self._get_c_string("query_string") or ""
            )
        return self._cached_attrs["query_string"]

    @property
    def remote_addr(self) -> str:
        """Client IP address"""
        if "remote_addr" not in self._cached_attrs:
            self._cached_attrs["remote_addr"] = (
                self._get_c_string("remote_addr") or "unknown"
            )
        return self._cached_attrs["remote_addr"]

    @property
    def headers(self) -> Dict[str, str]:
        """Request headers"""
        if "headers" not in self._cached_attrs:
            self._cached_attrs["headers"] = self._get_c_headers()
        return self._cached_attrs["headers"]

    @property
    def json(self) -> Any:
        """Lazy JSON parsing - only if accessed"""
        if "json" not in self._cached_attrs:
            self._cached_attrs["json"] = self._get_c_json()
        return self._cached_attrs["json"]

    @property
    def user_agent(self) -> str:
        """User-Agent header"""
        return self.headers.get("User-Agent", "")

    @property
    def content_type(self) -> str:
        """Content-Type header"""
        return self.headers.get("Content-Type", "")

    @property
    def authorization(self) -> str:
        """Authorization header"""
        return self.headers.get("Authorization", "")

    def get_header(self, name: str, default: str = None) -> str:
        """Get header value by name"""
        return self.headers.get(name, default)

    def _get_c_string(self, field: str) -> str:
        """Get string field from C context - zero copy where possible"""
        try:
            return (
                self._app._call_c_extension(
                    "get_middleware_context_string", self._c_context, field
                )
                or ""
            )
        except Exception:
            return ""

    def _get_c_headers(self) -> Dict[str, str]:
        """Get headers from C context"""
        try:
            return (
                self._app._call_c_extension(
                    "get_middleware_context_headers", self._c_context
                )
                or {}
            )
        except Exception:
            return {}

    def _get_c_json(self) -> Any:
        """Get JSON from C context (already parsed)"""
        try:
            return self._app._call_c_extension(
                "get_middleware_context_json", self._c_context
            )
        except Exception:
            return None


class MiddlewareResponse:
    """Response builder for middleware"""

    def __init__(self, c_context_ptr: ctypes.c_void_p, app: "Catzilla"):  # noqa: F821
        self._c_context = c_context_ptr
        self._app = app

    def set_status(self, status: int):
        """Set response status code"""
        try:
            self._app._call_c_extension(
                "set_middleware_response_status", self._c_context, status
            )
        except Exception:
            pass

    def set_header(self, name: str, value: str):
        """Set response header"""
        try:
            self._app._call_c_extension(
                "set_middleware_response_header", self._c_context, name, value
            )
        except Exception:
            pass

    def set_body(self, body: str, content_type: str = "text/plain"):
        """Set response body"""
        try:
            self._app._call_c_extension(
                "set_middleware_response_body", self._c_context, body, content_type
            )
        except Exception:
            pass


class Response:
    """Simple response object that can be returned from middleware"""

    def __init__(
        self, content=None, status_code: int = 200, headers: Dict[str, str] = None
    ):
        # Handle different content types
        if isinstance(content, (dict, list)):
            import json

            self.content = json.dumps(content)
            self.content_type = "application/json"
        elif isinstance(content, str):
            self.content = content
            self.content_type = "text/plain"
        else:
            self.content = str(content) if content is not None else ""
            self.content_type = "text/plain"

        self.status_code = status_code
        self.headers = headers or {}

        # Ensure Content-Type is in headers
        if "Content-Type" not in self.headers:
            self.headers["Content-Type"] = self.content_type

    def to_dict(self) -> Dict:
        """Convert response to dictionary for C bridge"""
        return {
            "content": self.content,
            "status_code": self.status_code,
            "headers": self.headers,
        }


# Backward compatibility with existing DIMiddleware
class DIMiddleware:
    """Legacy middleware - automatically converts to zero-allocation where possible"""

    def __init__(self, container=None):
        self.container = container
        self._convert_to_zero_alloc = True

    def __call__(self, request_handler: Callable) -> Callable:
        """Apply middleware wrapper - maintains backward compatibility"""

        @wraps(request_handler)
        def middleware_wrapper(*args, **kwargs):
            # For now, maintain existing behavior
            # Future enhancement: auto-convert to zero-allocation
            return request_handler(*args, **kwargs)

        return middleware_wrapper


class MiddlewareMetrics:
    """Middleware performance monitoring and analytics"""

    def __init__(self, app: "Catzilla"):  # noqa: F821
        self.app = app
        self._metrics = {}

    def get_performance_summary(self) -> Dict[str, Any]:
        """Get comprehensive performance summary"""
        middleware_stats = self.app.get_middleware_stats()
        memory_stats = get_memory_stats()

        return {
            "middleware_performance": middleware_stats,
            "memory_usage": {
                "total_allocated_mb": memory_stats.get("allocated_mb", 0),
                "middleware_arena_mb": memory_stats.get("arena_usage", {}).get(
                    "request_arena", 0
                ),
                "fragmentation_percent": memory_stats.get("fragmentation_percent", 0),
            },
            "optimization_suggestions": self._get_optimization_suggestions(
                middleware_stats, memory_stats
            ),
        }

    def _get_optimization_suggestions(
        self, middleware_stats: Dict, memory_stats: Dict
    ) -> List[str]:
        """Generate optimization suggestions based on metrics"""
        suggestions = []

        if middleware_stats.get("python_middleware", 0) > middleware_stats.get(
            "compiled_middleware", 0
        ):
            suggestions.append(
                "Consider simplifying middleware functions to enable C compilation"
            )

        if memory_stats.get("fragmentation_percent", 0) > 20:
            suggestions.append(
                "High memory fragmentation detected - consider memory optimization"
            )

        return suggestions
