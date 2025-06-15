"""
🧠 Catzilla Memory Management - Python Bridge
Access to C-level jemalloc memory statistics and optimization
"""

import ctypes
import os
import sys
from typing import Any, Dict, Optional

from .memory_c import CatzillaCExtension


def get_memory_stats() -> Dict[str, Any]:
    """
    Get comprehensive memory statistics from C-level jemalloc system

    Returns:
        Dictionary containing memory statistics including:
        - allocated_mb: Total allocated memory in MB
        - peak_mb: Peak memory usage in MB
        - fragmentation_percent: Memory fragmentation percentage
        - arena_usage: Per-arena memory usage breakdown
        - allocator: Current allocator type
        - jemalloc_enabled: Whether jemalloc is active
    """
    try:
        c_ext = CatzillaCExtension()
        if c_ext.is_available():
            return c_ext.get_memory_stats()
    except:
        pass

    # Fallback to Python-based memory stats if C extension not available
    import gc
    import resource

    # Get current memory usage
    rusage = resource.getrusage(resource.RUSAGE_SELF)

    # Convert to MB (ru_maxrss is in KB on Linux, bytes on macOS)
    if sys.platform == "darwin":  # macOS
        peak_memory_mb = rusage.ru_maxrss / (1024 * 1024)
    else:  # Linux
        peak_memory_mb = rusage.ru_maxrss / 1024

    return {
        "allocated_mb": peak_memory_mb,
        "peak_mb": peak_memory_mb,
        "fragmentation_percent": 0.0,  # Not available without jemalloc
        "arena_usage": {
            "request_arena": 0,
            "response_arena": 0,
            "cache_arena": 0,
            "static_arena": 0,
            "task_arena": 0,
        },
        "allocator": "system_malloc",
        "jemalloc_enabled": False,
        "jemalloc_available": False,
        "gc_objects": len(gc.get_objects()),
        "memory_efficiency_score": 1.0,
    }


def optimize_memory() -> bool:
    """
    Trigger memory optimization through C-level jemalloc

    Returns:
        True if optimization was triggered, False otherwise
    """
    try:
        c_ext = CatzillaCExtension()
        if c_ext.is_available():
            return c_ext.optimize_memory()
    except:
        pass

    # Fallback: trigger Python garbage collection
    import gc

    collected = gc.collect()
    return collected > 0


def reset_memory_stats():
    """Reset memory statistics counters"""
    try:
        c_ext = CatzillaCExtension()
        if c_ext.is_available():
            c_ext.reset_memory_stats()
            return
    except:
        pass

    # Fallback: just trigger GC
    import gc

    gc.collect()


def enable_memory_profiling() -> bool:
    """
    Enable detailed memory profiling

    Returns:
        True if profiling was enabled, False otherwise
    """
    try:
        c_ext = CatzillaCExtension()
        if c_ext.is_available():
            return c_ext.enable_memory_profiling()
    except:
        pass

    return False


def disable_memory_profiling():
    """Disable memory profiling"""
    try:
        c_ext = CatzillaCExtension()
        if c_ext.is_available():
            c_ext.disable_memory_profiling()
            return
    except:
        pass


def get_allocator_info() -> Dict[str, Any]:
    """
    Get information about the current memory allocator

    Returns:
        Dictionary with allocator information
    """
    try:
        c_ext = CatzillaCExtension()
        if c_ext.is_available():
            return c_ext.get_allocator_info()
    except:
        pass

    return {
        "current_allocator": "system_malloc",
        "jemalloc_enabled": False,
        "jemalloc_available": False,
        "arena_count": 0,
    }


class MemoryProfiler:
    """Memory profiling context manager and tools"""

    def __init__(self, name: str = "memory_profile"):
        self.name = name
        self.start_stats = None
        self.end_stats = None

    def __enter__(self):
        self.start_stats = get_memory_stats()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end_stats = get_memory_stats()

    def get_memory_diff(self) -> Dict[str, float]:
        """Get memory usage difference between start and end"""
        if not self.start_stats or not self.end_stats:
            return {}

        return {
            "allocated_mb_diff": self.end_stats["allocated_mb"]
            - self.start_stats["allocated_mb"],
            "peak_mb_diff": self.end_stats["peak_mb"] - self.start_stats["peak_mb"],
            "fragmentation_change": self.end_stats["fragmentation_percent"]
            - self.start_stats["fragmentation_percent"],
        }


# Memory monitoring utilities
def memory_usage_mb() -> float:
    """Get current memory usage in MB"""
    stats = get_memory_stats()
    return stats.get("allocated_mb", 0.0)


def is_jemalloc_available() -> bool:
    """Check if jemalloc is available"""
    info = get_allocator_info()
    return info.get("jemalloc_available", False)


def is_jemalloc_enabled() -> bool:
    """Check if jemalloc is currently enabled"""
    info = get_allocator_info()
    return info.get("jemalloc_enabled", False)


# Export main functions
__all__ = [
    "get_memory_stats",
    "optimize_memory",
    "reset_memory_stats",
    "enable_memory_profiling",
    "disable_memory_profiling",
    "get_allocator_info",
    "MemoryProfiler",
    "memory_usage_mb",
    "is_jemalloc_available",
    "is_jemalloc_enabled",
]
