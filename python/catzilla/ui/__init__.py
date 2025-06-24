"""
Catzilla UI System - Beautiful startup banners and development logging

This module provides beautiful startup banners and development request logging
for the Catzilla web framework.
"""

# Legacy compatibility functions for the existing codebase
import os
import sys
from typing import Any


def _is_debug_enabled() -> bool:
    """Check if debug mode is enabled via environment variable"""
    return os.getenv("CATZILLA_DEBUG") is not None


def log_types_debug(message: str, *args: Any) -> None:
    """Log debug message if debugging is enabled (legacy compatibility)"""
    if _is_debug_enabled():
        formatted_msg = message % args if args else message
        print(
            f"\033[36m[DEBUG-PY-TYPES]\033[0m {formatted_msg}",
            file=sys.stderr,
        )


def log_types_info(message: str, *args: Any) -> None:
    """Log info message if debugging is enabled (legacy compatibility)"""
    if _is_debug_enabled():
        formatted_msg = message % args if args else message
        print(
            f"\033[32m[INFO-PY-TYPES]\033[0m {formatted_msg}",
            file=sys.stderr,
        )


def log_types_error(message: str, *args: Any) -> None:
    """Log error message if debugging is enabled (legacy compatibility)"""
    if _is_debug_enabled():
        formatted_msg = message % args if args else message
        print(
            f"\033[31m[ERROR-PY-TYPES]\033[0m {formatted_msg}",
            file=sys.stderr,
        )


# Main UI system imports
from .banner import BannerRenderer, ServerInfoCollector
from .collectors import SystemInfoCollector
from .dev_logger import DevLogger, ProductionLogger, RequestLogEntry
from .formatters import COLORS, ColorFormatter

__all__ = [
    "BannerRenderer",
    "ServerInfoCollector",
    "DevLogger",
    "ProductionLogger",
    "RequestLogEntry",
    "ColorFormatter",
    "COLORS",
    "SystemInfoCollector",
    # Legacy compatibility
    "log_types_debug",
    "log_types_info",
    "log_types_error",
]
