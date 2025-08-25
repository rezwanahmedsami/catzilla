"""
Catzilla Smart Cache System - Python Integration
Ultra-High Performance Multi-Level Caching with C-Acceleration

This module provides Python bindings for the C-level cache engine and implements
a comprehensive multi-level caching system with Redis and disk fallback.
"""

import ctypes
import hashlib
import json
import os
import pickle
import time
import weakref
from ctypes import (
    POINTER,
    Structure,
    c_bool,
    c_char_p,
    c_int,
    c_size_t,
    c_uint32,
    c_uint64,
    c_void_p,
)
from dataclasses import dataclass
from threading import Lock
from typing import Any, Dict, List, Optional, Tuple, Union

try:
    import redis

    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

try:
    import lz4.frame

    LZ4_AVAILABLE = True
except ImportError:
    LZ4_AVAILABLE = False


# ============================================================================
# C Library Interface
# ============================================================================


class CacheEntry(Structure):
    """C cache entry structure"""

    pass


class CacheStatistics(Structure):
    """C cache statistics structure"""

    _fields_ = [
        ("hits", c_uint64),
        ("misses", c_uint64),
        ("evictions", c_uint64),
        ("memory_usage", c_uint64),
        ("total_requests", c_uint64),
        ("hit_ratio", ctypes.c_double),
        ("size", c_uint64),
        ("capacity", c_uint64),
    ]


class CacheResult(Structure):
    """C cache result structure"""

    _fields_ = [
        ("data", c_void_p),
        ("size", c_size_t),
        ("found", c_bool),
    ]


class CacheConfig(Structure):
    """C cache configuration structure"""

    _fields_ = [
        ("capacity", c_size_t),
        ("bucket_count", c_size_t),
        ("default_ttl", c_uint32),
        ("max_value_size", c_size_t),
        ("compression_enabled", c_bool),
        ("jemalloc_enabled", c_bool),
    ]


# ============================================================================
# Load C Library
# ============================================================================

# Load the C extension directly using Python import mechanism
try:
    import catzilla._catzilla as _catzilla_module

    C_LIBRARY_AVAILABLE = True
    _clib = _catzilla_module  # Use the module directly instead of ctypes.CDLL
except ImportError:
    C_LIBRARY_AVAILABLE = False
    _catzilla_module = None
    _clib = None

# Define function signatures if library is available
if C_LIBRARY_AVAILABLE and _clib:
    # Cache functions are available directly from the C module
    # Check if cache functions exist in the module
    if hasattr(_clib, "catzilla_cache_create"):
        # Cache creation and destruction
        _clib.catzilla_cache_create.argtypes = [c_size_t, c_size_t]
        _clib.catzilla_cache_create.restype = c_void_p

        _clib.catzilla_cache_create_with_config.argtypes = [POINTER(CacheConfig)]
        _clib.catzilla_cache_create_with_config.restype = c_void_p

        _clib.catzilla_cache_destroy.argtypes = [c_void_p]
        _clib.catzilla_cache_destroy.restype = None

        # Cache operations
        _clib.catzilla_cache_set.argtypes = [
            c_void_p,
            c_char_p,
            c_void_p,
            c_size_t,
            c_uint32,
        ]
        _clib.catzilla_cache_set.restype = c_int

        _clib.catzilla_cache_get.argtypes = [c_void_p, c_char_p]
        _clib.catzilla_cache_get.restype = CacheResult

        _clib.catzilla_cache_delete.argtypes = [c_void_p, c_char_p]
        _clib.catzilla_cache_delete.restype = c_int

        _clib.catzilla_cache_exists.argtypes = [c_void_p, c_char_p]
        _clib.catzilla_cache_exists.restype = c_bool

        _clib.catzilla_cache_clear.argtypes = [c_void_p]
        _clib.catzilla_cache_clear.restype = None

        # Statistics and utilities
        _clib.catzilla_cache_get_stats.argtypes = [c_void_p]
        _clib.catzilla_cache_get_stats.restype = CacheStatistics

        _clib.catzilla_cache_generate_key.argtypes = [
            c_char_p,
            c_char_p,
            c_char_p,
            c_uint32,
            c_char_p,
            c_size_t,
        ]
        _clib.catzilla_cache_generate_key.restype = c_int
    else:
        # Cache functions not available in this C module build
        C_LIBRARY_AVAILABLE = False
        _clib = None


# ============================================================================
# Configuration Classes
# ============================================================================


@dataclass
class SmartCacheConfig:
    """Configuration for the Smart Cache System"""

    # Memory Cache (C-level)
    memory_capacity: int = 10000
    memory_bucket_count: int = 0  # Auto-calculate
    memory_ttl: int = 3600  # 1 hour
    max_value_size: int = 100 * 1024 * 1024  # 100MB
    compression_enabled: bool = True
    jemalloc_enabled: bool = True

    # Redis Cache (L2)
    redis_enabled: bool = False
    redis_url: str = "redis://localhost:6379/0"
    redis_ttl: int = 86400  # 24 hours
    redis_max_connections: int = 10

    # Disk Cache (L3)
    disk_enabled: bool = False
    disk_path: str = "/tmp/catzilla_cache"
    disk_ttl: int = 604800  # 7 days
    disk_max_size: int = 1024 * 1024 * 1024  # 1GB

    # General Settings
    enable_stats: bool = True
    stats_collection_interval: int = 60  # seconds
    auto_expire_interval: int = 300  # 5 minutes


@dataclass
class CacheStats:
    """Cache statistics"""

    hits: int = 0
    misses: int = 0
    evictions: int = 0
    memory_usage: int = 0
    total_requests: int = 0
    hit_ratio: float = 0.0
    size: int = 0
    capacity: int = 0
    tier_stats: Dict[str, Dict[str, int]] = None


# ============================================================================
# Exception Classes
# ============================================================================


class CacheError(Exception):
    """Base cache exception"""

    pass


class CacheNotAvailableError(CacheError):
    """Raised when cache backend is not available"""

    pass


class CacheKeyError(CacheError):
    """Raised when there's an issue with cache key"""

    pass


class CacheValueError(CacheError):
    """Raised when there's an issue with cache value"""

    pass


# ============================================================================
# Memory Cache (C-Level)
# ============================================================================


class MemoryCache:
    """High-performance C-level memory cache"""

    def __init__(self, config: SmartCacheConfig):
        if not C_LIBRARY_AVAILABLE:
            raise CacheNotAvailableError("C library not available")

        self.config = config
        self._cache_ptr = None
        self._lock = Lock()

        # Create C cache configuration
        c_config = CacheConfig()
        c_config.capacity = config.memory_capacity
        c_config.bucket_count = config.memory_bucket_count
        c_config.default_ttl = config.memory_ttl
        c_config.max_value_size = config.max_value_size
        c_config.compression_enabled = config.compression_enabled
        c_config.jemalloc_enabled = config.jemalloc_enabled

        # Create cache instance
        self._cache_ptr = _clib.catzilla_cache_create_with_config(
            ctypes.byref(c_config)
        )
        if not self._cache_ptr:
            raise CacheError("Failed to create C cache instance")

        # Register cleanup
        weakref.finalize(self, self._cleanup, self._cache_ptr)

    @staticmethod
    def _cleanup(cache_ptr):
        """Cleanup C cache instance"""
        if cache_ptr and _clib:
            _clib.catzilla_cache_destroy(cache_ptr)

    def _serialize_value(self, value: Any) -> bytes:
        """Serialize Python value for C storage"""
        if isinstance(value, str):
            # Store strings with a prefix to identify them
            return b"STR:" + value.encode("utf-8")
        elif isinstance(value, (bytes, bytearray)):
            # Store bytes with a prefix to identify them
            return b"BYTES:" + bytes(value)
        else:
            # Use pickle for complex objects
            data = pickle.dumps(value, protocol=pickle.HIGHEST_PROTOCOL)

            # Compress if enabled and data is large enough
            if self.config.compression_enabled and len(data) > 1024 and LZ4_AVAILABLE:
                data = b"LZ4:" + lz4.frame.compress(data)
            else:
                data = b"PICKLE:" + data

            return data

    def _deserialize_value(self, data: bytes) -> Any:
        """Deserialize value from C storage"""
        if data.startswith(b"LZ4:") and LZ4_AVAILABLE:
            # Decompress LZ4 data and try to unpickle
            data = lz4.frame.decompress(data[4:])
            return pickle.loads(data)
        elif data.startswith(b"PICKLE:"):
            # Unpickle the data
            return pickle.loads(data[7:])
        elif data.startswith(b"STR:"):
            # Decode as string
            return data[4:].decode("utf-8")
        elif data.startswith(b"BYTES:"):
            # Return as bytes
            return data[6:]
        else:
            # Legacy handling - try to unpickle, then decode, then return as bytes
            try:
                return pickle.loads(data)
            except (pickle.UnpicklingError, TypeError):
                try:
                    return data.decode("utf-8")
                except UnicodeDecodeError:
                    return data

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Store value in cache"""
        if not self._cache_ptr:
            return False

        try:
            serialized = self._serialize_value(value)
            ttl = ttl or self.config.memory_ttl

            key_bytes = key.encode("utf-8")
            result = _clib.catzilla_cache_set(
                self._cache_ptr, key_bytes, serialized, len(serialized), ttl
            )

            return result == 0
        except Exception:
            return False

    def get(self, key: str) -> Tuple[Any, bool]:
        """Retrieve value from cache"""
        if not self._cache_ptr:
            return None, False

        try:
            key_bytes = key.encode("utf-8")
            result = _clib.catzilla_cache_get(self._cache_ptr, key_bytes)

            if not result.found:
                return None, False

            # Extract data from C memory
            data = ctypes.string_at(result.data, result.size)
            value = self._deserialize_value(data)

            return value, True
        except Exception:
            return None, False

    def delete(self, key: str) -> bool:
        """Delete key from cache"""
        if not self._cache_ptr:
            return False

        try:
            key_bytes = key.encode("utf-8")
            result = _clib.catzilla_cache_delete(self._cache_ptr, key_bytes)
            return result == 0
        except Exception:
            return False

    def exists(self, key: str) -> bool:
        """Check if key exists in cache"""
        if not self._cache_ptr:
            return False

        try:
            key_bytes = key.encode("utf-8")
            return bool(_clib.catzilla_cache_exists(self._cache_ptr, key_bytes))
        except Exception:
            return False

    def clear(self) -> None:
        """Clear all entries from cache"""
        if self._cache_ptr:
            _clib.catzilla_cache_clear(self._cache_ptr)

    def get_stats(self) -> CacheStats:
        """Get cache statistics"""
        if not self._cache_ptr:
            return CacheStats()

        try:
            c_stats = _clib.catzilla_cache_get_stats(self._cache_ptr)
            return CacheStats(
                hits=c_stats.hits,
                misses=c_stats.misses,
                evictions=c_stats.evictions,
                memory_usage=c_stats.memory_usage,
                total_requests=c_stats.total_requests,
                hit_ratio=c_stats.hit_ratio,
                size=c_stats.size,
                capacity=c_stats.capacity,
            )
        except Exception:
            return CacheStats()


# ============================================================================
# Redis Cache (L2)
# ============================================================================


class RedisCache:
    """Redis cache backend"""

    def __init__(self, config: SmartCacheConfig):
        if not REDIS_AVAILABLE:
            raise CacheNotAvailableError("Redis library not available")

        self.config = config
        self._redis = None

        if config.redis_enabled:
            try:
                self._redis = redis.from_url(
                    config.redis_url,
                    max_connections=config.redis_max_connections,
                    decode_responses=False,  # We handle bytes directly
                )
                # Test connection
                self._redis.ping()
            except Exception as e:
                raise CacheNotAvailableError(f"Could not connect to Redis: {e}")

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Store value in Redis"""
        if not self._redis:
            return False

        try:
            serialized = pickle.dumps(value, protocol=pickle.HIGHEST_PROTOCOL)

            # Compress if large enough
            if (
                self.config.compression_enabled
                and len(serialized) > 1024
                and LZ4_AVAILABLE
            ):
                serialized = b"LZ4:" + lz4.frame.compress(serialized)

            ttl = ttl or self.config.redis_ttl
            return self._redis.setex(key, ttl, serialized)
        except Exception:
            return False

    def get(self, key: str) -> Tuple[Any, bool]:
        """Retrieve value from Redis"""
        if not self._redis:
            return None, False

        try:
            data = self._redis.get(key)
            if data is None:
                return None, False

            # Decompress if needed
            if data.startswith(b"LZ4:") and LZ4_AVAILABLE:
                data = lz4.frame.decompress(data[4:])

            value = pickle.loads(data)
            return value, True
        except Exception:
            return None, False

    def delete(self, key: str) -> bool:
        """Delete key from Redis"""
        if not self._redis:
            return False

        try:
            return bool(self._redis.delete(key))
        except Exception:
            return False

    def exists(self, key: str) -> bool:
        """Check if key exists in Redis"""
        if not self._redis:
            return False

        try:
            return bool(self._redis.exists(key))
        except Exception:
            return False

    def clear(self) -> None:
        """Clear Redis cache"""
        if self._redis:
            try:
                self._redis.flushdb()
            except Exception:
                pass


# ============================================================================
# Disk Cache (L3)
# ============================================================================


class DiskCache:
    """Disk-based cache backend"""

    def __init__(self, config: SmartCacheConfig):
        self.config = config
        self.cache_dir = config.disk_path

        if config.disk_enabled:
            try:
                os.makedirs(self.cache_dir, exist_ok=True)
            except Exception as e:
                raise CacheNotAvailableError(
                    f"Could not create disk cache directory: {e}"
                )

    def _get_file_path(self, key: str) -> str:
        """Get file path for cache key"""
        # Use hash to avoid filesystem issues with long/special keys
        key_hash = hashlib.sha256(key.encode()).hexdigest()
        return os.path.join(self.cache_dir, f"{key_hash}.cache")

    def _is_expired(self, file_path: str, ttl: int) -> bool:
        """Check if cache file is expired"""
        try:
            mtime = os.path.getmtime(file_path)
            return time.time() - mtime > ttl
        except OSError:
            return True

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Store value on disk"""
        if not self.config.disk_enabled:
            return False

        try:
            file_path = self._get_file_path(key)
            data = pickle.dumps(value, protocol=pickle.HIGHEST_PROTOCOL)

            # Compress if enabled
            if self.config.compression_enabled and LZ4_AVAILABLE:
                data = lz4.frame.compress(data)

            with open(file_path, "wb") as f:
                f.write(data)

            return True
        except Exception:
            return False

    def get(self, key: str) -> Tuple[Any, bool]:
        """Retrieve value from disk"""
        if not self.config.disk_enabled:
            return None, False

        try:
            file_path = self._get_file_path(key)

            if not os.path.exists(file_path):
                return None, False

            # Check if expired
            if self._is_expired(file_path, self.config.disk_ttl):
                try:
                    os.remove(file_path)
                except OSError:
                    pass
                return None, False

            with open(file_path, "rb") as f:
                data = f.read()

            # Decompress if needed
            if self.config.compression_enabled and LZ4_AVAILABLE:
                try:
                    data = lz4.frame.decompress(data)
                except Exception:
                    pass  # Data might not be compressed

            value = pickle.loads(data)
            return value, True
        except Exception:
            return None, False

    def delete(self, key: str) -> bool:
        """Delete key from disk"""
        if not self.config.disk_enabled:
            return False

        try:
            file_path = self._get_file_path(key)
            os.remove(file_path)
            return True
        except OSError:
            return False

    def exists(self, key: str) -> bool:
        """Check if key exists on disk"""
        if not self.config.disk_enabled:
            return False

        try:
            file_path = self._get_file_path(key)
            return os.path.exists(file_path) and not self._is_expired(
                file_path, self.config.disk_ttl
            )
        except Exception:
            return False

    def clear(self) -> None:
        """Clear disk cache"""
        if not self.config.disk_enabled:
            return

        try:
            for filename in os.listdir(self.cache_dir):
                if filename.endswith(".cache"):
                    os.remove(os.path.join(self.cache_dir, filename))
        except Exception:
            pass


# ============================================================================
# Multi-Level Smart Cache
# ============================================================================


class SmartCache:
    """Industry-grade multi-level caching system"""

    def __init__(self, config: Optional[SmartCacheConfig] = None):
        self.config = config or SmartCacheConfig()
        self._memory_cache = None
        self._redis_cache = None
        self._disk_cache = None
        self._lock = Lock()

        # Initialize cache tiers
        self._init_caches()

        # Statistics
        self._stats = CacheStats(
            tier_stats={
                "memory": {"hits": 0, "misses": 0},
                "redis": {"hits": 0, "misses": 0},
                "disk": {"hits": 0, "misses": 0},
            }
        )

    def _init_caches(self):
        """Initialize cache backends"""
        # Memory cache (always enabled if C library available)
        if C_LIBRARY_AVAILABLE:
            try:
                self._memory_cache = MemoryCache(self.config)
            except Exception as e:
                print(f"Warning: Could not initialize memory cache: {e}")

        # Redis cache
        if self.config.redis_enabled:
            try:
                self._redis_cache = RedisCache(self.config)
            except Exception as e:
                print(f"Warning: Could not initialize Redis cache: {e}")

        # Disk cache - enable automatically if memory cache is not available as fallback
        if self.config.disk_enabled or (
            not self._memory_cache and not self._redis_cache
        ):
            # Enable disk cache in config if using as fallback
            if not self.config.disk_enabled and (
                not self._memory_cache and not self._redis_cache
            ):
                self.config.disk_enabled = True

            try:
                self._disk_cache = DiskCache(self.config)
            except Exception as e:
                print(f"Warning: Could not initialize disk cache: {e}")

        # Ensure we have at least one working cache backend
        if not self._memory_cache and not self._redis_cache and not self._disk_cache:
            print(
                "Warning: No cache backends available. Cache operations will be no-ops."
            )

    def generate_key(
        self,
        method: str,
        path: str,
        query_string: str = None,
        headers: Dict[str, str] = None,
    ) -> str:
        """Generate cache key from request components"""
        # Calculate headers hash
        headers_hash = 0
        if headers:
            header_str = "".join(f"{k}:{v}" for k, v in sorted(headers.items()))
            headers_hash = hash(header_str) & 0xFFFFFFFF

        # Try to use C implementation if available
        if C_LIBRARY_AVAILABLE and self._memory_cache:
            key_buffer = ctypes.create_string_buffer(512)
            result = _clib.catzilla_cache_generate_key(
                method.encode(),
                path.encode(),
                query_string.encode() if query_string else None,
                headers_hash,
                key_buffer,
                512,
            )

            if result > 0:
                return key_buffer.value.decode()

        # Fallback to Python implementation
        if query_string:
            return f"{method}:{path}?{query_string}:{headers_hash:08x}"
        else:
            return f"{method}:{path}:{headers_hash:08x}"

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Store value in all available cache tiers"""
        success = False

        # Store in memory cache first
        if self._memory_cache:
            if self._memory_cache.set(key, value, ttl or self.config.memory_ttl):
                success = True

        # Store in Redis cache
        if self._redis_cache:
            if self._redis_cache.set(key, value, ttl or self.config.redis_ttl):
                success = True

        # Store in disk cache
        if self._disk_cache:
            if self._disk_cache.set(key, value, ttl or self.config.disk_ttl):
                success = True

        return success

    def get(self, key: str) -> Tuple[Any, bool]:
        """Retrieve value from cache tiers (L1 -> L2 -> L3)"""
        # Try memory cache first (L1)
        if self._memory_cache:
            value, found = self._memory_cache.get(key)
            if found:
                self._stats.tier_stats["memory"]["hits"] += 1
                return value, True
            else:
                self._stats.tier_stats["memory"]["misses"] += 1

        # Try Redis cache (L2)
        if self._redis_cache:
            value, found = self._redis_cache.get(key)
            if found:
                self._stats.tier_stats["redis"]["hits"] += 1
                # Promote to memory cache
                if self._memory_cache:
                    self._memory_cache.set(key, value, self.config.memory_ttl)
                return value, True
            else:
                self._stats.tier_stats["redis"]["misses"] += 1

        # Try disk cache (L3)
        if self._disk_cache:
            value, found = self._disk_cache.get(key)
            if found:
                self._stats.tier_stats["disk"]["hits"] += 1
                # Promote to higher tiers
                if self._redis_cache:
                    self._redis_cache.set(key, value, self.config.redis_ttl)
                if self._memory_cache:
                    self._memory_cache.set(key, value, self.config.memory_ttl)
                return value, True
            else:
                self._stats.tier_stats["disk"]["misses"] += 1

        return None, False

    def delete(self, key: str) -> bool:
        """Delete key from all cache tiers"""
        results = []

        if self._memory_cache:
            results.append(self._memory_cache.delete(key))

        if self._redis_cache:
            results.append(self._redis_cache.delete(key))

        if self._disk_cache:
            results.append(self._disk_cache.delete(key))

        return any(results)

    def exists(self, key: str) -> bool:
        """Check if key exists in any cache tier"""
        if self._memory_cache and self._memory_cache.exists(key):
            return True

        if self._redis_cache and self._redis_cache.exists(key):
            return True

        if self._disk_cache and self._disk_cache.exists(key):
            return True

        return False

    def clear(self) -> None:
        """Clear all cache tiers"""
        if self._memory_cache:
            self._memory_cache.clear()

        if self._redis_cache:
            self._redis_cache.clear()

        if self._disk_cache:
            self._disk_cache.clear()

        # Reset stats
        self._stats = CacheStats(
            tier_stats={
                "memory": {"hits": 0, "misses": 0},
                "redis": {"hits": 0, "misses": 0},
                "disk": {"hits": 0, "misses": 0},
            }
        )

    def get_stats(self) -> CacheStats:
        """Get comprehensive cache statistics"""
        stats = CacheStats(tier_stats=self._stats.tier_stats.copy())

        # Get memory cache stats
        if self._memory_cache:
            memory_stats = self._memory_cache.get_stats()
            stats.hits += memory_stats.hits
            stats.misses += memory_stats.misses
            stats.evictions += memory_stats.evictions
            stats.memory_usage += memory_stats.memory_usage
            stats.total_requests += memory_stats.total_requests
            stats.size += memory_stats.size
            stats.capacity = memory_stats.capacity

        # Calculate overall hit ratio
        if stats.total_requests > 0:
            stats.hit_ratio = stats.hits / stats.total_requests

        return stats

    def health_check(self) -> Dict[str, bool]:
        """Check health of all cache tiers"""
        health = {}

        # Memory cache
        health["memory"] = self._memory_cache is not None

        # Redis cache
        if self._redis_cache and self._redis_cache._redis:
            try:
                self._redis_cache._redis.ping()
                health["redis"] = True
            except Exception:
                health["redis"] = False
        else:
            health["redis"] = False

        # Disk cache
        if self._disk_cache and self.config.disk_enabled:
            try:
                health["disk"] = os.path.exists(self.config.disk_path)
            except Exception:
                health["disk"] = False
        else:
            health["disk"] = False

        return health


# ============================================================================
# Global Cache Instance
# ============================================================================

# Global cache instance for easy access
_global_cache: Optional[SmartCache] = None
_global_cache_lock = Lock()


def get_cache(config: Optional[SmartCacheConfig] = None) -> SmartCache:
    """Get global cache instance"""
    global _global_cache

    with _global_cache_lock:
        if _global_cache is None:
            _global_cache = SmartCache(config)
        return _global_cache


def reset_cache():
    """Reset global cache instance"""
    global _global_cache

    with _global_cache_lock:
        if _global_cache:
            _global_cache.clear()
        _global_cache = None


# ============================================================================
# Decorator for Caching
# ============================================================================


def cached(ttl: int = 3600, key_prefix: str = ""):
    """Decorator for caching function results"""

    def decorator(func):
        def wrapper(*args, **kwargs):
            # Generate cache key
            key_data = f"{key_prefix}{func.__name__}:{str(args)}:{str(kwargs)}"
            key = hashlib.md5(key_data.encode()).hexdigest()

            # Try to get from cache
            cache = get_cache()
            value, found = cache.get(key)

            if found:
                return value

            # Execute function and cache result
            result = func(*args, **kwargs)
            cache.set(key, result, ttl)

            return result

        return wrapper

    return decorator
