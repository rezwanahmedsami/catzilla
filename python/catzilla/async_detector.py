"""
Catzilla Async Handler Detection System

This module provides sophisticated detection and classification of Python handlers,
distinguishing between synchronous and asynchronous functions to enable optimal
routing through Catzilla's hybrid execution system.

Key Features:
- Thread-safe handler type detection
- Coroutine validation and safety checks
- Performance-optimized handler wrapping
- Debug and introspection capabilities
"""

import asyncio
import functools
import inspect
import logging
import threading
import weakref
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Callable, Dict, Optional, Union

# Configure logging
logger = logging.getLogger("catzilla.async_detector")


class HandlerTypeError(Exception):
    """Raised when handler type detection fails or handler is invalid"""

    pass


class AsyncHandlerDetector:
    """
    Thread-safe handler detection and classification system.

    This class provides methods to detect whether a handler is synchronous
    or asynchronous, and to wrap handlers for optimal execution in Catzilla's
    hybrid sync/async environment.
    """

    def __init__(self):
        self._handler_cache: Dict[int, str] = {}  # Cache for handler types
        self._cache_lock = threading.RLock()  # Thread safety for cache
        self._stats = {
            "sync_handlers_detected": 0,
            "async_handlers_detected": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "validation_errors": 0,
        }

        # Weak reference to handlers to avoid memory leaks
        self._handler_refs: weakref.WeakSet = weakref.WeakSet()

    @staticmethod
    def is_async_handler(handler: Callable) -> bool:
        """
        Determine if a handler is an async function (coroutine function).

        This method provides multiple layers of detection to ensure accuracy:
        1. asyncio.iscoroutinefunction() - standard detection
        2. inspect.iscoroutinefunction() - backup detection
        3. __code__.co_flags inspection - low-level detection

        Args:
            handler: The handler function to check

        Returns:
            bool: True if handler is async, False if sync

        Raises:
            HandlerTypeError: If handler type cannot be determined
        """
        if not callable(handler):
            raise HandlerTypeError(f"Handler {handler} is not callable")

        # Primary detection using asyncio
        if asyncio.iscoroutinefunction(handler):
            return True

        # Secondary detection using inspect
        if inspect.iscoroutinefunction(handler):
            return True

        # Low-level detection for edge cases
        if hasattr(handler, "__code__"):
            # Check CO_ITERABLE_COROUTINE flag (bit 8)
            if handler.__code__.co_flags & 0x100:
                return True

        # Check if it's a wrapped async function
        if hasattr(handler, "__wrapped__"):
            return AsyncHandlerDetector.is_async_handler(handler.__wrapped__)

        # Check for async generators (should not be used as handlers)
        if inspect.isasyncgenfunction(handler):
            raise HandlerTypeError(
                f"Async generator functions cannot be used as handlers: {handler.__name__}"
            )

        return False

    def get_handler_type(self, handler: Callable) -> str:
        """
        Get the type of a handler with caching for performance.

        Args:
            handler: The handler function to classify

        Returns:
            str: "async" or "sync"

        Raises:
            HandlerTypeError: If handler type cannot be determined
        """
        # Use handler's id for caching (memory address)
        handler_id = id(handler)

        with self._cache_lock:
            # Check cache first
            if handler_id in self._handler_cache:
                self._stats["cache_hits"] += 1
                return self._handler_cache[handler_id]

            # Cache miss - detect type
            self._stats["cache_misses"] += 1

            try:
                is_async = self.is_async_handler(handler)
                handler_type = "async" if is_async else "sync"

                # Update statistics
                if is_async:
                    self._stats["async_handlers_detected"] += 1
                else:
                    self._stats["sync_handlers_detected"] += 1

                # Cache the result
                self._handler_cache[handler_id] = handler_type

                # Add to weak reference set for tracking
                self._handler_refs.add(handler)

                logger.debug(f"Detected {handler_type} handler: {handler.__name__}")

                return handler_type

            except Exception as e:
                self._stats["validation_errors"] += 1
                logger.error(f"Failed to detect handler type for {handler}: {e}")
                raise HandlerTypeError(f"Could not determine handler type: {e}") from e

    def wrap_handler_with_type_info(self, handler: Callable) -> Callable:
        """
        Wrap a handler with type information for faster runtime detection.

        This method annotates the handler with metadata that can be used
        for quick type checking without re-running detection logic.

        Args:
            handler: The handler function to wrap

        Returns:
            Callable: The wrapped handler with type metadata
        """
        handler_type = self.get_handler_type(handler)

        # Add type metadata to the handler
        handler._catzilla_handler_type = handler_type
        handler._catzilla_is_async = handler_type == "async"

        # Add validation metadata
        handler._catzilla_validated = True
        handler._catzilla_detection_time = asyncio.get_event_loop().time()

        return handler

    def validate_async_handler(self, handler: Callable) -> bool:
        """
        Perform comprehensive validation of an async handler.

        This method checks various aspects of an async handler to ensure
        it's suitable for use in Catzilla's async execution system.

        Args:
            handler: The async handler to validate

        Returns:
            bool: True if handler is valid, False otherwise

        Raises:
            HandlerTypeError: If handler has serious issues
        """
        if not self.is_async_handler(handler):
            raise HandlerTypeError(f"Handler {handler.__name__} is not async")

        # Check function signature
        sig = inspect.signature(handler)
        params = list(sig.parameters.values())

        # Should have at least one parameter (request)
        if len(params) < 1:
            raise HandlerTypeError(
                f"Async handler {handler.__name__} must accept at least one parameter (request)"
            )

        # First parameter should not have a default value
        if params[0].default != inspect.Parameter.empty:
            logger.warning(
                f"Async handler {handler.__name__} first parameter has default value, "
                "this may cause issues"
            )

        # Check if handler uses deprecated patterns
        if hasattr(handler, "__annotations__"):
            return_annotation = handler.__annotations__.get("return")
            if return_annotation and "Generator" in str(return_annotation):
                raise HandlerTypeError(
                    f"Async handler {handler.__name__} should not return a generator"
                )

        return True

    def validate_sync_handler(self, handler: Callable) -> bool:
        """
        Perform validation of a sync handler.

        Args:
            handler: The sync handler to validate

        Returns:
            bool: True if handler is valid, False otherwise
        """
        if self.is_async_handler(handler):
            raise HandlerTypeError(
                f"Handler {handler.__name__} is async, expected sync"
            )

        # Check if it's a proper callable
        if not callable(handler):
            raise HandlerTypeError(f"Handler {handler} is not callable")

        # Check function signature
        sig = inspect.signature(handler)
        params = list(sig.parameters.values())

        # Should have at least one parameter (request)
        if len(params) < 1:
            raise HandlerTypeError(
                f"Sync handler {handler.__name__} must accept at least one parameter (request)"
            )

        return True

    def create_type_safe_wrapper(self, handler: Callable) -> Callable:
        """
        Create a type-safe wrapper that ensures proper execution context.

        This wrapper provides additional safety checks and ensures the handler
        executes in the correct context (sync vs async).

        Args:
            handler: The handler to wrap

        Returns:
            Callable: Type-safe wrapped handler
        """
        handler_type = self.get_handler_type(handler)

        if handler_type == "async":
            return self._create_async_wrapper(handler)
        else:
            return self._create_sync_wrapper(handler)

    def _create_async_wrapper(self, handler: Callable) -> Callable:
        """Create a wrapper for async handlers with safety checks."""

        @functools.wraps(handler)
        async def async_wrapper(*args, **kwargs):
            # Validate we're in an async context
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                raise HandlerTypeError(
                    f"Async handler {handler.__name__} called outside async context"
                )

            # Execute the handler
            try:
                result = await handler(*args, **kwargs)
                return result
            except Exception as e:
                logger.error(f"Async handler {handler.__name__} raised exception: {e}")
                raise

        # Preserve type metadata
        async_wrapper._catzilla_handler_type = "async"
        async_wrapper._catzilla_is_async = True
        async_wrapper._catzilla_original_handler = handler

        return async_wrapper

    def _create_sync_wrapper(self, handler: Callable) -> Callable:
        """Create a wrapper for sync handlers with safety checks."""

        @functools.wraps(handler)
        def sync_wrapper(*args, **kwargs):
            # Execute the handler
            try:
                result = handler(*args, **kwargs)
                return result
            except Exception as e:
                logger.error(f"Sync handler {handler.__name__} raised exception: {e}")
                raise

        # Preserve type metadata
        sync_wrapper._catzilla_handler_type = "sync"
        sync_wrapper._catzilla_is_async = False
        sync_wrapper._catzilla_original_handler = handler

        return sync_wrapper

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get detection statistics for monitoring and debugging.

        Returns:
            Dict containing detection statistics
        """
        with self._cache_lock:
            return {
                **self._stats.copy(),
                "cache_size": len(self._handler_cache),
                "tracked_handlers": len(self._handler_refs),
            }

    def clear_cache(self) -> None:
        """Clear the handler type cache."""
        with self._cache_lock:
            self._handler_cache.clear()
            logger.debug("Handler type cache cleared")

    def is_handler_cached(self, handler: Callable) -> bool:
        """Check if a handler's type is cached."""
        with self._cache_lock:
            return id(handler) in self._handler_cache


# Global instance for convenience
default_detector = AsyncHandlerDetector()


# Convenience functions using the default detector
def is_async_handler(handler: Callable) -> bool:
    """Check if a handler is async using the default detector."""
    return default_detector.is_async_handler(handler)


def get_handler_type(handler: Callable) -> str:
    """Get handler type using the default detector."""
    return default_detector.get_handler_type(handler)


def wrap_handler(handler: Callable) -> Callable:
    """Wrap handler with type info using the default detector."""
    return default_detector.wrap_handler_with_type_info(handler)


def validate_handler(handler: Callable) -> bool:
    """Validate a handler using the default detector."""
    handler_type = default_detector.get_handler_type(handler)
    if handler_type == "async":
        return default_detector.validate_async_handler(handler)
    else:
        return default_detector.validate_sync_handler(handler)


# Type checking utilities
def require_async_handler(handler: Callable) -> Callable:
    """Decorator that ensures a handler is async."""
    if not is_async_handler(handler):
        raise HandlerTypeError(f"Handler {handler.__name__} must be async")
    return handler


def require_sync_handler(handler: Callable) -> Callable:
    """Decorator that ensures a handler is sync."""
    if is_async_handler(handler):
        raise HandlerTypeError(f"Handler {handler.__name__} must be sync")
    return handler


# Advanced introspection
def get_handler_info(handler: Callable) -> Dict[str, Any]:
    """Get comprehensive information about a handler."""
    info = {
        "name": getattr(handler, "__name__", "<unknown>"),
        "type": get_handler_type(handler),
        "is_async": is_async_handler(handler),
        "module": getattr(handler, "__module__", "<unknown>"),
        "qualname": getattr(handler, "__qualname__", "<unknown>"),
    }

    # Add signature information
    try:
        sig = inspect.signature(handler)
        info["signature"] = str(sig)
        info["parameter_count"] = len(sig.parameters)
        info["parameters"] = list(sig.parameters.keys())
    except (ValueError, TypeError):
        info["signature"] = "<unavailable>"
        info["parameter_count"] = 0
        info["parameters"] = []

    # Add source information if available
    try:
        info["source_file"] = inspect.getfile(handler)
        info["source_line"] = inspect.getsourcelines(handler)[1]
    except (OSError, TypeError):
        info["source_file"] = "<unavailable>"
        info["source_line"] = 0

    return info
