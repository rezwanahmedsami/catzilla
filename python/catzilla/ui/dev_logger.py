"""
Development request logger for Catzilla web framework.
"""

import time
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from .formatters import COLORS, ColorFormatter


@dataclass
class RequestLogEntry:
    """Container for request log information"""

    timestamp: datetime
    method: str
    path: str
    status_code: int
    duration_ms: float
    response_size: int
    client_ip: str
    user_agent: Optional[str] = None
    error_message: Optional[str] = None
    query_params: Optional[str] = None


class DevLogger:
    """Development request logger with beautiful colorized output"""

    def __init__(self, enable_colors: bool = True, show_details: bool = True):
        """
        Initialize development logger.

        Args:
            enable_colors: Enable color output
            show_details: Show detailed request information
        """
        self.formatter = ColorFormatter(enable_colors)
        self.show_details = show_details
        self.start_time = time.time()

    def log_request(
        self,
        method: str,
        path: str,
        status_code: int,
        duration_ms: float,
        response_size: int = 0,
        client_ip: str = "127.0.0.1",
        user_agent: Optional[str] = None,
        error_message: Optional[str] = None,
        query_params: Optional[str] = None,
    ) -> None:
        """
        Log a request/response cycle.

        Args:
            method: HTTP method
            path: Request path
            status_code: HTTP status code
            duration_ms: Response time in milliseconds
            response_size: Response size in bytes
            client_ip: Client IP address
            user_agent: User agent string
            error_message: Error message if request failed
            query_params: Query parameters string
        """

        entry = RequestLogEntry(
            timestamp=datetime.now(timezone.utc),
            method=method,
            path=path,
            status_code=status_code,
            duration_ms=duration_ms,
            response_size=response_size,
            client_ip=client_ip,
            user_agent=user_agent,
            error_message=error_message,
            query_params=query_params,
        )

        # Format and print the main request line
        main_line = self._format_main_line(entry)
        print(main_line)

        # Print additional details if enabled and available
        if self.show_details:
            if entry.error_message:
                self._print_error_details(entry)
            elif entry.user_agent and len(entry.user_agent) > 0:
                self._print_request_details(entry)

    def _format_main_line(self, entry: RequestLogEntry) -> str:
        """Format the main request log line"""
        # Format timestamp as ISO 8601 UTC with milliseconds
        timestamp = entry.timestamp.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
        timestamp_colored = self.formatter.colorize(f"[{timestamp}]", COLORS.GRAY)

        # Format method
        method = self.formatter.format_method(entry.method)

        # Format path with query params
        path = entry.path
        if entry.query_params:
            path += f"?{entry.query_params}"

        # Truncate long paths
        if len(path) > 35:
            path = path[:32] + "..."

        path = f"{path:<35}"  # Pad to consistent width

        # Format status code
        status = self.formatter.format_status(entry.status_code)

        # Format response time
        duration = self.formatter.format_response_time(entry.duration_ms)

        # Format response size
        size = self.formatter.format_size(entry.response_size)
        size_formatted = f"{size:>6}"

        # Format client IP
        ip = entry.client_ip
        if self.formatter.colors_enabled:
            ip = self.formatter.colorize(ip, COLORS.BRIGHT_BLACK)

        # Construct the main line
        main_line = f"{timestamp_colored} {method} {path} {status} {duration:>6} {size_formatted} → {ip}"

        return main_line

    def _print_error_details(self, entry: RequestLogEntry) -> None:
        """Print error details for failed requests"""
        error_prefix = "           "

        # Error icon and message
        error_icon = "❌" if self.formatter.colors_enabled else "[ERROR]"
        error_msg = self.formatter.colorize(entry.error_message, COLORS.BRIGHT_RED)
        print(f"{error_prefix}{error_icon} {error_msg}")

        # Additional error context if available
        if hasattr(entry, "error_field") and entry.error_field:
            field_info = f"├─ Field: {entry.error_field}"
            print(f"{error_prefix}{field_info}")

        if hasattr(entry, "error_value") and entry.error_value:
            value_info = f'└─ Value: "{entry.error_value}"'
            print(f"{error_prefix}{value_info}")

    def _print_request_details(self, entry: RequestLogEntry) -> None:
        """Print additional request details"""
        if not entry.user_agent:
            return

        detail_prefix = "           "

        # Truncate user agent for readability
        user_agent = entry.user_agent
        if len(user_agent) > 60:
            user_agent = user_agent[:57] + "..."

        user_agent_line = f"├─ User-Agent: {user_agent}"
        if self.formatter.colors_enabled:
            user_agent_line = self.formatter.colorize(
                user_agent_line, COLORS.BRIGHT_BLACK
            )

        print(f"{detail_prefix}{user_agent_line}")

    def log_server_start(self, host: str, port: int, mode: str) -> None:
        """Log server startup message"""
        if mode == "development":
            message = f"🔥 Development server started on {host}:{port}"
            color = COLORS.BRIGHT_YELLOW
        else:
            message = f"🚀 Production server started on {host}:{port}"
            color = COLORS.BRIGHT_GREEN

        colored_message = self.formatter.colorize(message, color)
        print(f"\n{colored_message}\n")

    def log_route_registration(self, method: str, path: str, handler: str) -> None:
        """Log route registration during development"""
        method_colored = self.formatter.format_method(method)
        path_colored = self.formatter.colorize(path, COLORS.BRIGHT_WHITE)
        handler_colored = self.formatter.colorize(handler, COLORS.GRAY)

        print(f"📍 {method_colored} {path_colored} → {handler_colored}")

    def log_middleware_registration(
        self, middleware_name: str, route_path: Optional[str] = None
    ) -> None:
        """Log middleware registration"""
        if route_path:
            message = f"🔧 Middleware '{middleware_name}' registered for {route_path}"
        else:
            message = f"🔧 Global middleware '{middleware_name}' registered"

        colored_message = self.formatter.colorize(message, COLORS.BRIGHT_CYAN)
        print(colored_message)

    def log_dependency_injection(
        self, dependency_name: str, scope: str = "singleton"
    ) -> None:
        """Log dependency injection registration"""
        message = f"💉 Dependency '{dependency_name}' registered ({scope})"
        colored_message = self.formatter.colorize(message, COLORS.BRIGHT_MAGENTA)
        print(colored_message)

    def log_cache_operation(self, operation: str, key: str, hit: bool = False) -> None:
        """Log cache operations"""
        if hit:
            icon = "🎯"
            color = COLORS.BRIGHT_GREEN
            message = f"Cache HIT: {operation} '{key}'"
        else:
            icon = "💾"
            color = COLORS.BRIGHT_BLUE
            message = f"Cache {operation.upper()}: '{key}'"

        colored_message = self.formatter.colorize(f"{icon} {message}", color)
        print(colored_message)


class ProductionLogger:
    """Minimal production logger - no colors, structured output"""

    def __init__(self):
        """Initialize production logger"""
        self.start_time = time.time()

    def log_request(
        self,
        method: str,
        path: str,
        status_code: int,
        duration_ms: float,
        response_size: int = 0,
        client_ip: str = "127.0.0.1",
        **kwargs,
    ) -> None:
        """Log request in structured format for production"""
        timestamp = datetime.now(timezone.utc).isoformat()

        # Simple structured log entry
        log_entry = {
            "timestamp": timestamp,
            "method": method,
            "path": path,
            "status": status_code,
            "duration_ms": round(duration_ms, 2),
            "size": response_size,
            "ip": client_ip,
        }

        # Convert to simple log line for now
        # In real production, this would go to structured logging
        print(
            f"{timestamp} {method} {path} {status_code} {duration_ms:.1f}ms {client_ip}"
        )

    def log_server_start(self, host: str, port: int, mode: str) -> None:
        """Log server startup in production"""
        timestamp = datetime.now(timezone.utc).isoformat()
        print(f"{timestamp} Server started on {host}:{port} (mode: {mode})")

    # No-op methods for production
    def log_route_registration(self, *args, **kwargs) -> None:
        pass

    def log_middleware_registration(self, *args, **kwargs) -> None:
        pass

    def log_dependency_injection(self, *args, **kwargs) -> None:
        pass

    def log_cache_operation(self, *args, **kwargs) -> None:
        pass
