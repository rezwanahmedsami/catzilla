"""
Catzilla Professional Python Logging System

This logging system is designed for Catzilla contributors and developers only.
End users will never see these logs unless they explicitly enable debug mode.

Usage:
  - Contributors: CATZILLA_DEBUG=1 python app.py
  - End users: python app.py (clean output, no Python logs)

Log levels:
  - DEBUG: Detailed debugging information
  - INFO: General information about operations
  - ERROR: Error conditions that need attention
"""

import os
import sys
from typing import Any


class CatzillaLogger:
    """Professional logging for Catzilla Python components"""

    def __init__(self):
        self._debug_enabled = None

    def _is_debug_enabled(self) -> bool:
        """Check if debug mode is enabled via environment variable"""
        if self._debug_enabled is None:
            self._debug_enabled = os.getenv("CATZILLA_DEBUG") is not None
        return self._debug_enabled

    def debug(self, module: str, message: str, *args: Any) -> None:
        """Log debug message if debugging is enabled"""
        if self._is_debug_enabled():
            formatted_msg = message % args if args else message
            print(
                f"\033[36m[DEBUG-PY-{module.upper()}]\033[0m {formatted_msg}",
                file=sys.stderr,
            )

    def info(self, module: str, message: str, *args: Any) -> None:
        """Log info message if debugging is enabled"""
        if self._is_debug_enabled():
            formatted_msg = message % args if args else message
            print(
                f"\033[32m[INFO-PY-{module.upper()}]\033[0m {formatted_msg}",
                file=sys.stderr,
            )

    def error(self, module: str, message: str, *args: Any) -> None:
        """Log error message if debugging is enabled"""
        if self._is_debug_enabled():
            formatted_msg = message % args if args else message
            print(
                f"\033[31m[ERROR-PY-{module.upper()}]\033[0m {formatted_msg}",
                file=sys.stderr,
            )


# Global logger instance
_logger = CatzillaLogger()


# Convenience functions for different modules
def log_types_debug(message: str, *args: Any) -> None:
    """Log debug message for types module"""
    _logger.debug("TYPES", message, *args)


def log_types_info(message: str, *args: Any) -> None:
    """Log info message for types module"""
    _logger.info("TYPES", message, *args)


def log_types_error(message: str, *args: Any) -> None:
    """Log error message for types module"""
    _logger.error("TYPES", message, *args)


def log_app_debug(message: str, *args: Any) -> None:
    """Log debug message for app module"""
    _logger.debug("APP", message, *args)


def log_app_info(message: str, *args: Any) -> None:
    """Log info message for app module"""
    _logger.info("APP", message, *args)


def log_app_error(message: str, *args: Any) -> None:
    """Log error message for app module"""
    _logger.error("APP", message, *args)


def log_request_debug(message: str, *args: Any) -> None:
    """Log debug message for request processing"""
    _logger.debug("REQUEST", message, *args)


def log_request_info(message: str, *args: Any) -> None:
    """Log info message for request processing"""
    _logger.info("REQUEST", message, *args)


def log_request_error(message: str, *args: Any) -> None:
    """Log error message for request processing"""
    _logger.error("REQUEST", message, *args)
