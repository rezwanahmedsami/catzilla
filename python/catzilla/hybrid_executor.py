"""
Catzilla Hybrid Executor System

This module provides the core execution engine for Catzilla's hybrid sync/async
handler support. It intelligently routes handlers to appropriate execution contexts
while maintaining optimal performance and thread safety.

Key Features:
- Intelligent sync/async handler routing
- Thread pool management for sync handlers
- Asyncio integration for async handlers
- Performance monitoring and optimization
- Resource management and cleanup
"""

import asyncio
import functools
import logging
import sys
import threading
import time
from concurrent.futures import Future, ThreadPoolExecutor, as_completed
from contextvars import copy_context
from typing import Any, Awaitable, Callable, Dict, List, Optional, Union

from .async_detector import AsyncHandlerDetector, HandlerTypeError, is_async_handler

# Configure logging
logger = logging.getLogger("catzilla.hybrid_executor")


class ExecutionError(Exception):
    """Raised when handler execution fails"""

    pass


class ExecutorConfig:
    """Configuration for the hybrid executor system."""

    def __init__(
        self,
        max_sync_threads: int = 10,
        sync_thread_timeout: float = 30.0,
        async_timeout: float = 30.0,
        enable_performance_monitoring: bool = True,
        thread_name_prefix: str = "catzilla-sync",
        enable_context_vars: bool = True,
    ):
        """
        Initialize executor configuration.

        Args:
            max_sync_threads: Maximum number of threads for sync handlers
            sync_thread_timeout: Timeout for sync handler execution
            async_timeout: Timeout for async handler execution
            enable_performance_monitoring: Enable performance tracking
            thread_name_prefix: Prefix for sync execution threads
            enable_context_vars: Enable context variable propagation
        """
        self.max_sync_threads = max_sync_threads
        self.sync_thread_timeout = sync_thread_timeout
        self.async_timeout = async_timeout
        self.enable_performance_monitoring = enable_performance_monitoring
        self.thread_name_prefix = thread_name_prefix
        self.enable_context_vars = enable_context_vars


class PerformanceMetrics:
    """Track performance metrics for handler execution."""

    def __init__(self):
        self._lock = threading.RLock()
        self.sync_executions = 0
        self.async_executions = 0
        self.sync_total_time = 0.0
        self.async_total_time = 0.0
        self.sync_errors = 0
        self.async_errors = 0
        self.sync_timeouts = 0
        self.async_timeouts = 0
        self.thread_pool_queue_size = 0

        # Performance history (last 100 executions)
        self.sync_execution_times: List[float] = []
        self.async_execution_times: List[float] = []
        self.max_history_size = 100

    def record_sync_execution(
        self, execution_time: float, success: bool, timeout: bool = False
    ):
        """Record a sync handler execution."""
        with self._lock:
            self.sync_executions += 1
            self.sync_total_time += execution_time

            if not success:
                self.sync_errors += 1
            if timeout:
                self.sync_timeouts += 1

            self.sync_execution_times.append(execution_time)
            if len(self.sync_execution_times) > self.max_history_size:
                self.sync_execution_times.pop(0)

    def record_async_execution(
        self, execution_time: float, success: bool, timeout: bool = False
    ):
        """Record an async handler execution."""
        with self._lock:
            self.async_executions += 1
            self.async_total_time += execution_time

            if not success:
                self.async_errors += 1
            if timeout:
                self.async_timeouts += 1

            self.async_execution_times.append(execution_time)
            if len(self.async_execution_times) > self.max_history_size:
                self.async_execution_times.pop(0)

    def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive performance statistics."""
        with self._lock:
            stats = {
                "sync_executions": self.sync_executions,
                "async_executions": self.async_executions,
                "sync_errors": self.sync_errors,
                "async_errors": self.async_errors,
                "sync_timeouts": self.sync_timeouts,
                "async_timeouts": self.async_timeouts,
                "thread_pool_queue_size": self.thread_pool_queue_size,
            }

            # Calculate averages
            if self.sync_executions > 0:
                stats["sync_avg_time"] = self.sync_total_time / self.sync_executions
                stats["sync_success_rate"] = (
                    self.sync_executions - self.sync_errors
                ) / self.sync_executions
            else:
                stats["sync_avg_time"] = 0.0
                stats["sync_success_rate"] = 1.0

            if self.async_executions > 0:
                stats["async_avg_time"] = self.async_total_time / self.async_executions
                stats["async_success_rate"] = (
                    self.async_executions - self.async_errors
                ) / self.async_executions
            else:
                stats["async_avg_time"] = 0.0
                stats["async_success_rate"] = 1.0

            # Recent performance
            if self.sync_execution_times:
                stats["sync_recent_avg"] = sum(self.sync_execution_times[-10:]) / len(
                    self.sync_execution_times[-10:]
                )
                stats["sync_recent_max"] = max(self.sync_execution_times[-10:])
                stats["sync_recent_min"] = min(self.sync_execution_times[-10:])

            if self.async_execution_times:
                stats["async_recent_avg"] = sum(self.async_execution_times[-10:]) / len(
                    self.async_execution_times[-10:]
                )
                stats["async_recent_max"] = max(self.async_execution_times[-10:])
                stats["async_recent_min"] = min(self.async_execution_times[-10:])

            return stats


class HybridExecutor:
    """
    Core hybrid execution engine for Catzilla handlers.

    This class manages the execution of both sync and async handlers,
    providing optimal performance through intelligent routing and
    resource management.
    """

    def __init__(self, config: Optional[ExecutorConfig] = None):
        """
        Initialize the hybrid executor.

        Args:
            config: Configuration for the executor
        """
        self.config = config or ExecutorConfig()
        self.detector = AsyncHandlerDetector()
        self.metrics = PerformanceMetrics()

        # Thread pool for sync handlers
        self._thread_pool: Optional[ThreadPoolExecutor] = None
        self._pool_lock = threading.Lock()

        # Per-thread event loops for sync-to-async execution.
        self._event_loops: Dict[int, asyncio.AbstractEventLoop] = {}
        self._event_loops_lock = threading.Lock()
        self._thread_local = threading.local()

        # Handler tracking
        self._active_handler_count = 0
        self._shutdown_event = threading.Event()

        # Performance monitoring
        self._monitoring_enabled = self.config.enable_performance_monitoring

        logger.info(f"HybridExecutor initialized with config: {self.config.__dict__}")

    def _ensure_thread_pool(self) -> ThreadPoolExecutor:
        """Ensure thread pool is initialized (lazy initialization)."""
        if self._thread_pool is None:
            with self._pool_lock:
                if self._thread_pool is None:
                    self._thread_pool = ThreadPoolExecutor(
                        max_workers=self.config.max_sync_threads,
                        thread_name_prefix=self.config.thread_name_prefix,
                    )
                    logger.info(
                        f"Thread pool initialized with {self.config.max_sync_threads} workers"
                    )

        return self._thread_pool

    def _get_event_loop(self) -> asyncio.AbstractEventLoop:
        """Get or create the executor-managed loop for the current thread."""
        loop = getattr(self._thread_local, "event_loop", None)
        if loop is not None and not loop.is_closed():
            return loop

        thread_id = threading.get_ident()
        with self._event_loops_lock:
            loop = self._event_loops.get(thread_id)
            if loop is None or loop.is_closed():
                loop = asyncio.new_event_loop()
                self._event_loops[thread_id] = loop

        self._thread_local.event_loop = loop
        asyncio.set_event_loop(loop)

        return loop

    def _close_event_loops(self) -> None:
        """Close executor-managed event loops during shutdown."""
        with self._event_loops_lock:
            loops = list(self._event_loops.values())
            self._event_loops.clear()

        for loop in loops:
            if loop.is_closed():
                continue

            if loop.is_running():
                loop.call_soon_threadsafe(loop.stop)

            loop.close()

        self._thread_local.__dict__.pop("event_loop", None)

    def _get_running_loop(self) -> asyncio.AbstractEventLoop:
        """Get the currently running loop, if any."""
        try:
            return asyncio.get_running_loop()
        except RuntimeError:
            return None

    def _mark_handler_started(self) -> None:
        self._active_handler_count += 1

    def _mark_handler_finished(self) -> None:
        if self._active_handler_count > 0:
            self._active_handler_count -= 1

    async def execute_handler(self, handler: Callable, *args, **kwargs) -> Any:
        """
        Execute a handler in the appropriate context (sync or async).

        This is the main entry point for handler execution. It automatically
        detects the handler type and routes it to the appropriate execution method.

        Args:
            handler: The handler function to execute
            *args: Positional arguments for the handler
            **kwargs: Keyword arguments for the handler

        Returns:
            The result of the handler execution

        Raises:
            ExecutionError: If handler execution fails
            HandlerTypeError: If handler type detection fails
        """
        if self._shutdown_event.is_set():
            raise ExecutionError("Executor is shutting down")

        self._mark_handler_started()

        try:
            # Detect handler type
            handler_type = self.detector.get_handler_type(handler)

            if handler_type == "async":
                return await self._execute_async_handler(handler, *args, **kwargs)
            else:
                return await self._execute_sync_handler(handler, *args, **kwargs)

        except Exception as e:
            logger.error(f"Handler execution failed: {e}")
            raise ExecutionError(f"Handler execution failed: {e}") from e
        finally:
            self._mark_handler_finished()

    async def _execute_async_handler(self, handler: Callable, *args, **kwargs) -> Any:
        """Execute an async handler with proper timeout and error handling."""
        start_time = time.time() if self._monitoring_enabled else 0.0
        success = False
        timeout_occurred = False
        timeout = self.config.async_timeout

        try:
            # Handler is already validated as async by detector, no need to re-check

            if timeout is None or timeout <= 0:
                result = await handler(*args, **kwargs)
            else:
                result = await asyncio.wait_for(handler(*args, **kwargs), timeout=timeout)

            success = True
            return result

        except asyncio.TimeoutError:
            timeout_occurred = True
            logger.warning(
                f"Async handler {handler.__name__} timed out after {timeout}s"
            )
            raise ExecutionError(
                f"Async handler timed out after {timeout}s"
            )

        except Exception as e:
            logger.error(f"Async handler {handler.__name__} raised exception: {e}")
            raise ExecutionError(f"Async handler failed: {e}") from e

        finally:
            if self._monitoring_enabled:
                execution_time = time.time() - start_time
                self.metrics.record_async_execution(
                    execution_time, success, timeout_occurred
                )

    async def _execute_sync_handler(self, handler: Callable, *args, **kwargs) -> Any:
        """Execute a sync handler in a thread pool."""
        start_time = time.time() if self._monitoring_enabled else 0.0
        success = False
        timeout_occurred = False

        try:
            # Get thread pool
            executor = self._ensure_thread_pool()

            # Update queue size metric
            if self._monitoring_enabled:
                self.metrics.thread_pool_queue_size = getattr(
                    executor._threads, "qsize", lambda: 0
                )()

            # Prepare execution context
            if self.config.enable_context_vars:
                ctx = copy_context()
                sync_handler = functools.partial(ctx.run, handler, *args, **kwargs)
            else:
                sync_handler = functools.partial(handler, *args, **kwargs)

            # Execute in thread pool with timeout
            loop = self._get_event_loop()
            future = loop.run_in_executor(executor, sync_handler)

            result = await asyncio.wait_for(
                future, timeout=self.config.sync_thread_timeout
            )
            success = True
            return result

        except asyncio.TimeoutError:
            timeout_occurred = True
            logger.warning(
                f"Sync handler {handler.__name__} timed out after {self.config.sync_thread_timeout}s"
            )
            raise ExecutionError(
                f"Sync handler timed out after {self.config.sync_thread_timeout}s"
            )

        except Exception as e:
            logger.error(f"Sync handler {handler.__name__} raised exception: {e}")
            raise ExecutionError(f"Sync handler failed: {e}") from e

        finally:
            if self._monitoring_enabled:
                execution_time = time.time() - start_time
                self.metrics.record_sync_execution(
                    execution_time, success, timeout_occurred
                )

    def execute_handler_sync(self, handler: Callable, *args, **kwargs) -> Any:
        """
        Execute a handler synchronously (blocking call).

        This method is for cases where you need to execute a handler
        from a synchronous context. It manages the event loop internally.

        Args:
            handler: The handler function to execute
            *args: Positional arguments for the handler
            **kwargs: Keyword arguments for the handler

        Returns:
            The result of the handler execution
        """
        # Check if we're already in an async context
        try:
            loop = self._get_running_loop()
            if loop is None:
                raise RuntimeError
            # We're in an async context, can't use run()
            raise ExecutionError(
                "execute_handler_sync cannot be called from an async context. "
                "Use execute_handler() instead."
            )
        except RuntimeError:
            # No running loop, we can proceed
            pass
 
        loop = self._get_event_loop()
        return loop.run_until_complete(self.execute_handler(handler, *args, **kwargs))

    def execute_known_async_handler_sync(self, handler: Callable, *args, **kwargs) -> Any:
        """Execute an already-classified async handler from a sync context."""
        if self._shutdown_event.is_set():
            raise ExecutionError("Executor is shutting down")

        running_loop = self._get_running_loop()
        if running_loop is not None:
            raise ExecutionError(
                "execute_known_async_handler_sync cannot be called from an async context"
            )

        self._mark_handler_started()
        try:
            loop = self._get_event_loop()
            if self.config.async_timeout is None or self.config.async_timeout <= 0:
                return loop.run_until_complete(handler(*args, **kwargs))

            return loop.run_until_complete(self._execute_async_handler(handler, *args, **kwargs))
        except Exception as e:
            raise ExecutionError(f"Async handler execution failed: {e}") from e
        finally:
            self._mark_handler_finished()

    async def execute_multiple_handlers(
        self, handlers_with_args: List[tuple]
    ) -> List[Any]:
        """
        Execute multiple handlers concurrently.

        Args:
            handlers_with_args: List of (handler, args, kwargs) tuples

        Returns:
            List of results in the same order as input
        """
        tasks = []

        for item in handlers_with_args:
            if len(item) == 1:
                handler = item[0]
                args, kwargs = (), {}
            elif len(item) == 2:
                handler, args = item
                kwargs = {}
            else:
                handler, args, kwargs = item

            task = asyncio.create_task(self.execute_handler(handler, *args, **kwargs))
            tasks.append(task)

        return await asyncio.gather(*tasks, return_exceptions=True)

    def get_performance_stats(self) -> Dict[str, Any]:
        """Get comprehensive performance statistics."""
        stats = self.metrics.get_stats()

        # Add executor-specific stats
        stats.update(
            {
                "active_handlers": self._active_handler_count,
                "thread_pool_initialized": self._thread_pool is not None,
                "shutdown_requested": self._shutdown_event.is_set(),
            }
        )

        if self._thread_pool:
            stats.update(
                {
                    "thread_pool_max_workers": self._thread_pool._max_workers,
                    "thread_pool_threads": (
                        len(self._thread_pool._threads)
                        if hasattr(self._thread_pool, "_threads")
                        else 0
                    ),
                }
            )

        return stats

    def configure_monitoring(self, enabled: bool) -> None:
        """Enable or disable performance monitoring."""
        self._monitoring_enabled = enabled
        logger.info(f"Performance monitoring {'enabled' if enabled else 'disabled'}")

    def reset_metrics(self) -> None:
        """Reset all performance metrics."""
        self.metrics = PerformanceMetrics()
        logger.info("Performance metrics reset")

    async def shutdown(self, timeout: float = 30.0) -> None:
        """
        Gracefully shutdown the executor.

        Args:
            timeout: Maximum time to wait for active handlers to complete
        """
        logger.info("Initiating executor shutdown")
        self._shutdown_event.set()

        # Wait for active handlers to complete
        start_time = time.time()
        while self._active_handler_count and (time.time() - start_time) < timeout:
            await asyncio.sleep(0.1)

        if self._active_handler_count:
            logger.warning(
                f"Shutdown timeout reached with {self._active_handler_count} handlers still active"
            )

        # Shutdown thread pool
        if self._thread_pool:
            with self._pool_lock:
                if self._thread_pool:
                    self._thread_pool.shutdown(
                        wait=True
                    )  # timeout not supported in Python 3.10
                    self._thread_pool = None
                    logger.info("Thread pool shutdown completed")

        self._close_event_loops()

        logger.info("Executor shutdown completed")

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        # Run shutdown in a new event loop if needed
        try:
            loop = asyncio.get_running_loop()
            # Create a task for shutdown
            loop.create_task(self.shutdown())
        except RuntimeError:
            # No running loop, create one
            asyncio.run(self.shutdown())


# Global executor instance
_global_executor: Optional[HybridExecutor] = None
_global_executor_lock = threading.Lock()


def get_global_executor() -> HybridExecutor:
    """Get the global executor instance (singleton pattern)."""
    global _global_executor

    if _global_executor is None:
        with _global_executor_lock:
            if _global_executor is None:
                _global_executor = HybridExecutor()

    return _global_executor


def configure_global_executor(config: ExecutorConfig) -> HybridExecutor:
    """Configure the global executor with custom settings."""
    global _global_executor

    with _global_executor_lock:
        if _global_executor is not None:
            # Shutdown existing executor
            asyncio.create_task(_global_executor.shutdown())

        _global_executor = HybridExecutor(config)

    return _global_executor


# Convenience functions using the global executor
async def execute_handler(handler: Callable, *args, **kwargs) -> Any:
    """Execute a handler using the global executor."""
    executor = get_global_executor()
    return await executor.execute_handler(handler, *args, **kwargs)


def execute_handler_sync(handler: Callable, *args, **kwargs) -> Any:
    """Execute a handler synchronously using the global executor."""
    executor = get_global_executor()
    return executor.execute_handler_sync(handler, *args, **kwargs)


async def execute_multiple_handlers(handlers_with_args: List[tuple]) -> List[Any]:
    """Execute multiple handlers concurrently using the global executor."""
    executor = get_global_executor()
    return await executor.execute_multiple_handlers(handlers_with_args)


def get_performance_stats() -> Dict[str, Any]:
    """Get performance statistics from the global executor."""
    executor = get_global_executor()
    return executor.get_performance_stats()


async def shutdown_global_executor(timeout: float = 30.0) -> None:
    """Shutdown the global executor."""
    global _global_executor

    if _global_executor is not None:
        with _global_executor_lock:
            if _global_executor is not None:
                await _global_executor.shutdown(timeout)
                _global_executor = None
