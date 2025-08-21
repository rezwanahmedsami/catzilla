"""
Color formatting utilities for Catzilla logging system.
"""

import os
import sys
from typing import Dict, Optional


class COLORS:
    """ANSI color codes for terminal output"""

    # Reset
    RESET = "\033[0m"

    # Basic colors
    BLACK = "\033[30m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"

    # Bright colors
    BRIGHT_BLACK = "\033[90m"
    BRIGHT_RED = "\033[91m"
    BRIGHT_GREEN = "\033[92m"
    BRIGHT_YELLOW = "\033[93m"
    BRIGHT_BLUE = "\033[94m"
    BRIGHT_MAGENTA = "\033[95m"
    BRIGHT_CYAN = "\033[96m"
    BRIGHT_WHITE = "\033[97m"

    # Extended colors
    ORANGE = "\033[38;5;208m"
    GRAY = "\033[38;5;8m"

    # Styles
    BOLD = "\033[1m"
    DIM = "\033[2m"
    UNDERLINE = "\033[4m"


class ColorFormatter:
    """Handles color formatting for terminal output"""

    # HTTP Method colors
    METHOD_COLORS = {
        "GET": COLORS.BRIGHT_GREEN,
        "POST": COLORS.BRIGHT_BLUE,
        "PUT": COLORS.BRIGHT_YELLOW,
        "DELETE": COLORS.BRIGHT_RED,
        "PATCH": COLORS.BRIGHT_MAGENTA,
        "OPTIONS": COLORS.BRIGHT_CYAN,
        "HEAD": COLORS.BRIGHT_WHITE,
    }

    # Status code colors
    STATUS_COLORS = {
        2: COLORS.GREEN,  # 2xx
        3: COLORS.YELLOW,  # 3xx
        4: COLORS.RED,  # 4xx
        5: COLORS.BRIGHT_RED,  # 5xx
    }

    # Response time colors (thresholds in ms)
    RESPONSE_TIME_COLORS = [
        (10, COLORS.GREEN),
        (50, COLORS.YELLOW),
        (200, COLORS.ORANGE),
        (float("inf"), COLORS.RED),
    ]

    def __init__(self, enable_colors: Optional[bool] = None):
        """
        Initialize color formatter.

        Args:
            enable_colors: Force enable/disable colors.
                          If None, auto-detect based on TTY.
        """
        if enable_colors is None:
            # Auto-detect color support
            self.colors_enabled = self._supports_color()
        else:
            self.colors_enabled = enable_colors

    def _supports_color(self) -> bool:
        """Check if the terminal supports colors"""
        return (
            hasattr(sys.stdout, "isatty")
            and sys.stdout.isatty()
            and "TERM" in os.environ
            and os.environ["TERM"] != "dumb"
        )

    def colorize(self, text: str, color: str) -> str:
        """Apply color to text if colors are enabled"""
        if not self.colors_enabled:
            return text
        return f"{color}{text}{COLORS.RESET}"

    def format_method(self, method: str) -> str:
        """Format HTTP method with appropriate color"""
        color = self.METHOD_COLORS.get(method.upper(), COLORS.WHITE)
        formatted_method = f"{method:<7}"  # Pad to 7 characters
        return self.colorize(formatted_method, color)

    def format_status(self, status_code: int) -> str:
        """Format status code with appropriate color"""
        status_class = status_code // 100
        color = self.STATUS_COLORS.get(status_class, COLORS.WHITE)
        return self.colorize(str(status_code), color)

    def format_response_time(self, duration_ms: float) -> str:
        """Format response time with performance-based color"""
        for threshold, color in self.RESPONSE_TIME_COLORS:
            if duration_ms < threshold:
                break

        # Format duration
        if duration_ms < 1:
            formatted = f"{duration_ms:.1f}ms"
        elif duration_ms < 1000:
            formatted = f"{duration_ms:.0f}ms"
        else:
            formatted = f"{duration_ms/1000:.1f}s"

        return self.colorize(formatted, color)

    def format_size(self, size_bytes: int) -> str:
        """Format file size in human-readable format"""
        if size_bytes < 1024:
            return f"{size_bytes}B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes/1024:.1f}KB"
        else:
            return f"{size_bytes/(1024*1024):.1f}MB"

    def format_banner_title(self, text: str) -> str:
        """Format banner title text"""
        return self.colorize(text, COLORS.BRIGHT_CYAN + COLORS.BOLD)

    def format_banner_mode(self, mode: str) -> str:
        """Format environment mode in banner"""
        if mode.upper() == "DEVELOPMENT":
            color = COLORS.BRIGHT_YELLOW
        elif mode.upper() == "PRODUCTION":
            color = COLORS.BRIGHT_GREEN
        else:
            color = COLORS.WHITE

        return self.colorize(mode.upper(), color + COLORS.BOLD)

    def format_banner_label(self, text: str) -> str:
        """Format banner labels"""
        return self.colorize(text, COLORS.GRAY)

    def format_banner_value(self, text: str) -> str:
        """Format banner values"""
        return self.colorize(text, COLORS.BRIGHT_WHITE)


# Import os here to avoid circular imports
import os
