"""
Catzilla Startup Banner System

This module provides a beautiful, professional startup banner that displays
server information in both production and development modes.
"""

import os
import platform
import sys
import time
from typing import Any, Dict, Optional


class StartupBanner:
    """Manages the startup banner display with dynamic content and styling"""

    def __init__(self, production: bool = False):
        self.production = production
        self.version = self._get_version()
        self.supports_unicode = self._check_unicode_support()
        self.supports_color = self._check_color_support()

    def print_banner(self, host: str, port: int, app_stats: Dict[str, Any]) -> None:
        """Print the startup banner with server information

        Args:
            host: Server bind host
            port: Server bind port
            app_stats: Application statistics dictionary
        """
        if self.production:
            self._print_production_banner(host, port, app_stats)
        else:
            self._print_development_banner(host, port, app_stats)

    def _print_production_banner(
        self, host: str, port: int, stats: Dict[str, Any]
    ) -> None:
        """Print clean production banner"""
        width = self._calculate_width(host, port, stats, production=True)

        # Use C banner if available for maximum performance
        try:
            from catzilla._catzilla import print_startup_banner

            # TODO: Call C function when available
            # print_startup_banner(stats, True)
            # return
        except (ImportError, AttributeError):
            pass

        # Fallback to Python implementation
        self._render_banner(host, port, stats, width, production=True)

    def _print_development_banner(
        self, host: str, port: int, stats: Dict[str, Any]
    ) -> None:
        """Print rich development banner with extra information"""
        width = self._calculate_width(host, port, stats, production=False)

        # Always use Python for development (more flexibility)
        self._render_banner(host, port, stats, width, production=False)

    def _render_banner(
        self, host: str, port: int, stats: Dict[str, Any], width: int, production: bool
    ) -> None:
        """Render the banner using Python"""
        # Box drawing characters
        if self.supports_unicode:
            top_left, top_right = "╔", "╗"
            bottom_left, bottom_right = "╚", "╝"
            horizontal = "═"
            vertical = "║"
        else:
            top_left, top_right = "+", "+"
            bottom_left, bottom_right = "+", "+"
            horizontal = "="
            vertical = "|"

        # Print top border
        print(top_left + horizontal * (width - 2) + top_right)

        # Print title
        mode_str = "PRODUCTION" if production else "DEVELOPMENT"
        title = f"🐱 Catzilla v{self.version} - {mode_str}"
        self._print_content_line(title, width, vertical)

        # Print URL
        url = f"http://{host}:{port}"
        self._print_content_line(url, width, vertical)

        # Print bind info
        bind_info = f"(bound on host {host} and port {port})"
        self._print_content_line(bind_info, width, vertical)

        # Empty line
        self._print_content_line("", width, vertical)

        # Print statistics
        self._print_kv_line("Routes", str(stats.get("route_count", 0)), width, vertical)
        self._print_kv_line(
            "Workers", str(stats.get("worker_count", 1)), width, vertical
        )

        jemalloc_status = (
            "Enabled" if stats.get("jemalloc_enabled", False) else "Disabled"
        )
        self._print_kv_line("jemalloc", jemalloc_status, width, vertical)

        # Development-only fields
        if not production:
            di_count = stats.get("di_service_count", 0)
            if di_count > 0:
                di_status = f"Enabled ({di_count} services)"
                self._print_kv_line("DI Container", di_status, width, vertical)

            validation_status = (
                "Enabled" if stats.get("auto_validation", False) else "Disabled"
            )
            self._print_kv_line("Auto Validation", validation_status, width, vertical)

            if stats.get("profiling_enabled", False):
                profiling_status = (
                    f"Enabled (interval: {stats.get('profiling_interval', 60)}s)"
                )
                self._print_kv_line("Profiling", profiling_status, width, vertical)

            if stats.get("background_tasks", False):
                self._print_kv_line("Background Tasks", "Enabled", width, vertical)

            self._print_kv_line("Debug Mode", "ON", width, vertical)

        self._print_kv_line("PID", str(stats.get("pid", os.getpid())), width, vertical)

        # Print bottom border
        print(bottom_left + horizontal * (width - 2) + bottom_right)

        # Add spacing
        print()

    def _print_content_line(self, content: str, width: int, border_char: str) -> None:
        """Print a content line with proper padding"""
        content_width = len(content)
        available_space = width - 4  # 2 borders + 2 padding

        if content_width > available_space:
            content = content[:available_space]
            content_width = available_space

        left_padding = 1
        right_padding = available_space - content_width - left_padding

        line = f"{border_char} {' ' * left_padding}{content}{' ' * right_padding} {border_char}"
        print(line)

    def _print_kv_line(
        self, key: str, value: str, width: int, border_char: str
    ) -> None:
        """Print a key-value line with dots"""
        available_space = width - 4  # 2 borders + 2 padding
        key_value_space = len(key) + len(value) + 2  # 2 for spaces
        dots_count = available_space - key_value_space

        if dots_count < 3:
            dots_count = 3

        dots = "." * dots_count
        line = f"{border_char} {key} {dots} {value} {border_char}"
        print(line)

    def _calculate_width(
        self, host: str, port: int, stats: Dict[str, Any], production: bool
    ) -> int:
        """Calculate optimal banner width based on content"""
        min_width = 60

        # Check various content lengths
        mode_str = "PRODUCTION" if production else "DEVELOPMENT"
        title = f"🐱 Catzilla v{self.version} - {mode_str}"
        url = f"http://{host}:{port}"
        bind_info = f"(bound on host {host} and port {port})"

        # Find maximum width needed
        max_width = max(min_width, len(title) + 4, len(url) + 4, len(bind_info) + 4)

        # Cap at reasonable maximum
        return min(max_width, 100)

    def _get_version(self) -> str:
        """Get Catzilla version string"""
        try:
            # Try to get version from package
            import catzilla

            if hasattr(catzilla, "__version__"):
                return catzilla.__version__
        except ImportError:
            pass

        # Fallback version
        return "0.1.0"

    def _check_unicode_support(self) -> bool:
        """Check if terminal supports Unicode box drawing"""
        # Check if we're writing to a terminal
        if not sys.stdout.isatty():
            return False

        # Check environment variables
        term = os.environ.get("TERM", "")
        lang = os.environ.get("LANG", "")
        lc_all = os.environ.get("LC_ALL", "")

        # Windows specific checks
        if platform.system() == "Windows":
            # Modern Windows Terminal supports Unicode
            if os.environ.get("WT_SESSION"):
                return True
            # Check for UTF-8 support
            try:
                import locale

                return "utf-8" in locale.getpreferredencoding().lower()
            except:
                return False

        # Unix-like systems
        if any(t in term for t in ["xterm", "screen", "tmux", "rxvt"]):
            return True

        if "utf-8" in lang.lower() or "utf-8" in lc_all.lower():
            return True

        # Conservative fallback
        return False

    def _check_color_support(self) -> bool:
        """Check if terminal supports ANSI colors"""
        if not sys.stdout.isatty():
            return False

        # Check common environment variables
        if os.environ.get("NO_COLOR"):
            return False

        if os.environ.get("FORCE_COLOR"):
            return True

        term = os.environ.get("TERM", "")
        if "color" in term or term in ["xterm", "xterm-256color", "screen", "tmux"]:
            return True

        # Windows specific
        if platform.system() == "Windows":
            return os.environ.get("WT_SESSION") is not None

        return True


def collect_app_stats(app) -> Dict[str, Any]:
    """Collect comprehensive application statistics for the banner

    Args:
        app: Catzilla application instance

    Returns:
        Dictionary containing application statistics
    """
    stats = {
        "route_count": 0,
        "worker_count": 1,
        "jemalloc_enabled": False,
        "auto_validation": False,
        "di_service_count": 0,
        "profiling_enabled": False,
        "profiling_interval": 60,
        "background_tasks": False,
        "pid": os.getpid(),
    }

    try:
        # Get route count
        if hasattr(app, "routes"):
            stats["route_count"] = len(app.routes())
        elif hasattr(app, "router") and hasattr(app.router, "routes"):
            stats["route_count"] = len(app.router.routes())

        # Get jemalloc status
        if hasattr(app, "has_jemalloc"):
            stats["jemalloc_enabled"] = app.has_jemalloc

        # Get auto-validation status
        if hasattr(app, "auto_validation"):
            stats["auto_validation"] = app.auto_validation

        # Get DI service count
        if hasattr(app, "di_container") and app.di_container:
            if hasattr(app.di_container, "list_services"):
                stats["di_service_count"] = len(app.di_container.list_services())

        # Get profiling status
        if hasattr(app, "memory_profiling"):
            stats["profiling_enabled"] = app.memory_profiling
        if hasattr(app, "memory_stats_interval"):
            stats["profiling_interval"] = app.memory_stats_interval

        # Get background tasks status
        if hasattr(app, "_task_system_enabled"):
            stats["background_tasks"] = app._task_system_enabled

    except Exception:
        # Ignore errors in stats collection
        pass

    return stats
