"""
Catzilla Development Logger

Provides rich, colorful logging for development mode with zero production overhead.
Features emoji indicators, color coding, and performance metrics.
"""

import os
import platform
import sys
import time
from datetime import datetime, timezone
from typing import Any, Dict, Optional


class DevelopmentLogger:
    """Rich logging system for development mode"""

    def __init__(self, enabled: bool = True):
        self.enabled = enabled
        self.supports_color = self._check_color_support()
        self.colors = self._setup_colors()
        self.emojis = self._setup_emojis()

        # Performance tracking
        self._request_start_times: Dict[str, float] = {}

    def log_route_registration(self, method: str, path: str, handler_name: str) -> None:
        """Log route registration with emoji and colors

        Args:
            method: HTTP method (GET, POST, etc.)
            path: Route path pattern
            handler_name: Name of the handler function
        """
        if not self.enabled:
            return

        emoji = self.emojis["methods"].get(method, self.emojis["methods"]["DEFAULT"])
        colored_method = self._colorize_method(method)

        print(f"🚀 {emoji} {colored_method:<6} {path:<30} → {handler_name}")

    def log_request_start(
        self, method: str, path: str, request_id: Optional[str] = None
    ) -> str:
        """Log the start of a request and return a tracking ID

        Args:
            method: HTTP method
            path: Request path
            request_id: Optional request ID for tracking

        Returns:
            Request tracking ID
        """
        if not self.enabled:
            return ""

        if not request_id:
            request_id = f"{method}:{path}:{time.time()}"

        self._request_start_times[request_id] = time.perf_counter()
        return request_id

    def log_request_complete(
        self,
        method: str,
        path: str,
        status_code: int,
        request_id: Optional[str] = None,
        extra_info: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Log completed request with timing and status

        Args:
            method: HTTP method
            path: Request path
            status_code: HTTP status code
            request_id: Request tracking ID from log_request_start
            extra_info: Additional information to log
        """
        if not self.enabled:
            return

        # Calculate duration
        duration_ms = 0.0
        if request_id and request_id in self._request_start_times:
            end_time = time.perf_counter()
            start_time = self._request_start_times.pop(request_id)
            duration_ms = (end_time - start_time) * 1000

        # Get status emoji and color
        status_emoji = self._get_status_emoji(status_code)
        status_text = self._get_status_text(status_code)
        colored_status = self._colorize_status(status_code, status_text)

        # Format timestamp as ISO 8601 UTC with milliseconds
        timestamp = (
            datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
        )

        # Build log message
        log_parts = [
            f"[{timestamp}]",
            status_emoji,
            method,
            path,
            "→",
            colored_status,
            f"({duration_ms:.1f}ms)",
        ]

        # Add extra info if provided
        if extra_info:
            for key, value in extra_info.items():
                log_parts.append(f"{key}={value}")

        print(" ".join(log_parts))

    def log_error(
        self,
        message: str,
        exception: Optional[Exception] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Log an error with context

        Args:
            message: Error message
            exception: Optional exception object
            context: Optional context information
        """
        if not self.enabled:
            return

        timestamp = (
            datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
        )
        colored_error = self._colorize("ERROR", "red")

        log_parts = [f"[{timestamp}]", "🔴", colored_error, message]

        if exception:
            log_parts.append(f"({type(exception).__name__}: {str(exception)})")

        print(" ".join(log_parts))

        # Print context if provided
        if context:
            for key, value in context.items():
                print(f"    {key}: {value}")

    def log_info(self, message: str, context: Optional[Dict[str, Any]] = None) -> None:
        """Log an info message

        Args:
            message: Info message
            context: Optional context information
        """
        if not self.enabled:
            return

        timestamp = (
            datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
        )
        colored_info = self._colorize("INFO", "blue")

        print(f"[{timestamp}] ℹ️  {colored_info} {message}")

        if context:
            for key, value in context.items():
                print(f"    {key}: {value}")

    def log_warning(
        self, message: str, context: Optional[Dict[str, Any]] = None
    ) -> None:
        """Log a warning message

        Args:
            message: Warning message
            context: Optional context information
        """
        if not self.enabled:
            return

        timestamp = (
            datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
        )
        colored_warning = self._colorize("WARN", "yellow")

        print(f"[{timestamp}] ⚠️  {colored_warning} {message}")

        if context:
            for key, value in context.items():
                print(f"    {key}: {value}")

    def _colorize_method(self, method: str) -> str:
        """Colorize HTTP method"""
        if not self.supports_color:
            return method

        color_map = {
            "GET": "green",
            "POST": "blue",
            "PUT": "yellow",
            "DELETE": "red",
            "PATCH": "magenta",
            "HEAD": "cyan",
            "OPTIONS": "white",
        }

        color = color_map.get(method, "white")
        return self._colorize(method, color)

    def _colorize_status(self, status_code: int, status_text: str) -> str:
        """Colorize HTTP status code and text"""
        if not self.supports_color:
            return f"{status_code} {status_text}"

        if 200 <= status_code < 300:
            color = "green"
        elif 300 <= status_code < 400:
            color = "blue"
        elif 400 <= status_code < 500:
            color = "yellow"
        else:
            color = "red"

        return self._colorize(f"{status_code} {status_text}", color)

    def _colorize(self, text: str, color: str) -> str:
        """Apply ANSI color codes to text"""
        if not self.supports_color:
            return text

        color_code = self.colors.get(color, self.colors["white"])
        reset_code = self.colors["reset"]
        return f"{color_code}{text}{reset_code}"

    def _get_status_emoji(self, status_code: int) -> str:
        """Get emoji for HTTP status code"""
        if 200 <= status_code < 300:
            return "🟢"
        elif 300 <= status_code < 400:
            return "🔵"
        elif 400 <= status_code < 500:
            return "🟡"
        else:
            return "🔴"

    def _get_status_text(self, status_code: int) -> str:
        """Get text description for HTTP status code"""
        status_texts = {
            200: "OK",
            201: "Created",
            202: "Accepted",
            204: "No Content",
            301: "Moved Permanently",
            302: "Found",
            304: "Not Modified",
            400: "Bad Request",
            401: "Unauthorized",
            403: "Forbidden",
            404: "Not Found",
            405: "Method Not Allowed",
            409: "Conflict",
            422: "Unprocessable Entity",
            429: "Too Many Requests",
            500: "Internal Server Error",
            502: "Bad Gateway",
            503: "Service Unavailable",
            504: "Gateway Timeout",
        }

        return status_texts.get(status_code, "Unknown")

    def _setup_colors(self) -> Dict[str, str]:
        """Setup ANSI color codes"""
        if not self.supports_color:
            return {
                color: ""
                for color in [
                    "red",
                    "green",
                    "yellow",
                    "blue",
                    "magenta",
                    "cyan",
                    "white",
                    "reset",
                ]
            }

        return {
            "red": "\033[91m",
            "green": "\033[92m",
            "yellow": "\033[93m",
            "blue": "\033[94m",
            "magenta": "\033[95m",
            "cyan": "\033[96m",
            "white": "\033[97m",
            "reset": "\033[0m",
        }

    def _setup_emojis(self) -> Dict[str, Any]:
        """Setup emoji mappings"""
        return {
            "methods": {
                "GET": "🟢",
                "POST": "🔵",
                "PUT": "🟡",
                "DELETE": "🔴",
                "PATCH": "🟠",
                "HEAD": "⚪",
                "OPTIONS": "⚫",
                "DEFAULT": "⚪",
            },
            "status": {"success": "✅", "error": "❌", "warning": "⚠️", "info": "ℹ️"},
        }

    def _check_color_support(self) -> bool:
        """Check if terminal supports ANSI colors"""
        # Don't use colors if not a terminal
        if not sys.stdout.isatty():
            return False

        # Check for explicit color control
        if os.environ.get("NO_COLOR"):
            return False

        if os.environ.get("FORCE_COLOR"):
            return True

        # Check terminal capabilities
        term = os.environ.get("TERM", "")
        if "color" in term or term in ["xterm", "xterm-256color", "screen", "tmux"]:
            return True

        # Windows specific checks
        if platform.system() == "Windows":
            # Windows Terminal supports colors
            if os.environ.get("WT_SESSION"):
                return True
            # Try to enable virtual terminal processing
            try:
                import ctypes

                kernel32 = ctypes.windll.kernel32
                handle = kernel32.GetStdHandle(-11)  # STD_OUTPUT_HANDLE
                mode = ctypes.c_ulong()
                kernel32.GetConsoleMode(handle, ctypes.byref(mode))
                mode.value |= 4  # ENABLE_VIRTUAL_TERMINAL_PROCESSING
                return kernel32.SetConsoleMode(handle, mode) != 0
            except:
                return False

        return True


# Global development logger instance
_dev_logger: Optional[DevelopmentLogger] = None


def get_dev_logger() -> DevelopmentLogger:
    """Get the global development logger instance"""
    global _dev_logger
    if _dev_logger is None:
        _dev_logger = DevelopmentLogger()
    return _dev_logger


def enable_dev_logging(enabled: bool = True) -> None:
    """Enable or disable development logging globally"""
    global _dev_logger
    if _dev_logger is None:
        _dev_logger = DevelopmentLogger(enabled)
    else:
        _dev_logger.enabled = enabled


def disable_dev_logging() -> None:
    """Disable development logging globally"""
    enable_dev_logging(False)
