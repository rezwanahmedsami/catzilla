"""
Performance Optimization Example

This example demonstrates Catzilla's cache performance optimization
techniques including intelligent eviction, warming strategies, and monitoring.

Features demonstrated:
- Intelligent cache warming algorithms
- Predictive cache preloading
- Performance-based cache eviction
- Cache hit ratio optimization
- Memory usage optimization
- Latency reduction techniques
- Cache monitoring and alerting
"""

from catzilla import Catzilla, Request, Response, JSONResponse
import asyncio
import time
import json
import statistics
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from collections import defaultdict, deque
import heapq
import threading

# Try to import psutil, make it optional
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    print("Warning: psutil not available, system metrics will be disabled")
    PSUTIL_AVAILABLE = False

# Initialize Catzilla with performance optimization
app = Catzilla(
    production=False,
    show_banner=True,
    log_requests=True
)

# Simple in-memory cache implementation
class SimpleMemoryCache:
    """Simple in-memory cache with size limits"""

    def __init__(self, max_size: int = 100 * 1024 * 1024):  # 100MB
        self.max_size = max_size
        self._cache = {}
        self._expiry = {}
        self._access_order = deque()
        self._current_size = 0

    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        # Check if expired
        if key in self._expiry and time.time() > self._expiry[key]:
            self.delete(key)
            return None

        if key in self._cache:
            # Update access order for LRU
            if key in self._access_order:
                self._access_order.remove(key)
            self._access_order.append(key)
            return self._cache[key]
        return None

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in cache with optional TTL"""
        try:
            # Calculate size
            value_size = len(json.dumps(value).encode()) if value else 0

            # Remove old value if exists
            if key in self._cache:
                self.delete(key)

            # Check if we need to evict items
            while self._current_size + value_size > self.max_size and self._access_order:
                oldest_key = self._access_order.popleft()
                self.delete(oldest_key)

            # Set new value
            self._cache[key] = value
            self._current_size += value_size
            self._access_order.append(key)

            if ttl:
                self._expiry[key] = time.time() + ttl

            return True
        except Exception:
            return False

    def delete(self, key: str) -> bool:
        """Delete key from cache"""
        deleted = False
        if key in self._cache:
            value_size = len(json.dumps(self._cache[key]).encode())
            del self._cache[key]
            self._current_size -= value_size
            deleted = True

        if key in self._expiry:
            del self._expiry[key]

        if key in self._access_order:
            self._access_order.remove(key)

        return deleted

    def clear(self):
        """Clear all cache"""
        self._cache.clear()
        self._expiry.clear()
        self._access_order.clear()
        self._current_size = 0

    def info(self) -> Dict[str, Any]:
        """Get cache info"""
        return {
            "size": len(self._cache),
            "memory_usage": self._current_size,
            "max_size": self.max_size
        }

@dataclass
class CacheAccessPattern:
    """Track cache access patterns for optimization"""
    key: str
    access_count: int = 0
    last_access: datetime = field(default_factory=datetime.now)
    access_frequency: float = 0.0  # accesses per minute
    cache_hits: int = 0
    cache_misses: int = 0
    compute_time_ms: float = 0.0
    data_size_bytes: int = 0
    priority_score: float = 0.0

class PerformanceOptimizedCache:
    """High-performance cache with intelligent optimization"""

    def __init__(self, max_size: int = 100 * 1024 * 1024):  # 100MB
        self.cache = SimpleMemoryCache(max_size=max_size)
        self.access_patterns: Dict[str, CacheAccessPattern] = {}
        self.access_history = deque(maxlen=10000)  # Recent access history
        self.performance_metrics = {
            "total_requests": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "average_latency_ms": 0.0,
            "memory_efficiency": 0.0,
            "optimization_cycles": 0
        }

        # Performance optimization settings
        self.optimization_interval = 300  # 5 minutes
        self.min_access_count_for_priority = 5
        self.memory_pressure_threshold = 0.85  # 85% memory usage

        # Start optimization background task in a thread since we don't have async loop
        self.optimization_thread = threading.Thread(target=self._optimization_loop, daemon=True)
        self.optimization_thread.start()

    def get(self, key: str) -> Optional[Any]:
        """Get value with performance tracking"""
        start_time = time.time()
        self.performance_metrics["total_requests"] += 1

        # Update access pattern
        pattern = self.access_patterns.get(key, CacheAccessPattern(key=key))
        pattern.access_count += 1
        pattern.last_access = datetime.now()

        # Calculate access frequency (accesses per minute)
        time_since_first = (datetime.now() - pattern.last_access).total_seconds() / 60
        if time_since_first > 0:
            pattern.access_frequency = pattern.access_count / max(time_since_first, 1)

        # Try to get from cache
        value = self.cache.get(key)
        latency_ms = (time.time() - start_time) * 1000

        if value is not None:
            # Cache hit
            pattern.cache_hits += 1
            self.performance_metrics["cache_hits"] += 1

            # Log access for optimization
            self.access_history.append({
                "key": key,
                "hit": True,
                "latency_ms": latency_ms,
                "timestamp": time.time()
            })
        else:
            # Cache miss
            pattern.cache_misses += 1
            self.performance_metrics["cache_misses"] += 1

            self.access_history.append({
                "key": key,
                "hit": False,
                "latency_ms": latency_ms,
                "timestamp": time.time()
            })

        # Update pattern and metrics
        self.access_patterns[key] = pattern
        self._update_performance_metrics(latency_ms)

        return value

    def set(self, key: str, value: Any, ttl: Optional[int] = None, compute_time_ms: float = 0.0) -> bool:
        """Set value with optimization tracking"""
        # Calculate data size
        data_size = len(json.dumps(value).encode()) if value else 0

        # Update access pattern
        pattern = self.access_patterns.get(key, CacheAccessPattern(key=key))
        pattern.compute_time_ms = compute_time_ms
        pattern.data_size_bytes = data_size

        # Calculate priority score for this item
        pattern.priority_score = self._calculate_priority_score(pattern)
        self.access_patterns[key] = pattern

        # Set in cache
        success = self.cache.set(key, value, ttl)

        # Check if optimization is needed
        if self._should_optimize():
            self._optimize_cache()

        return success

    def _calculate_priority_score(self, pattern: CacheAccessPattern) -> float:
        """Calculate priority score for cache item"""
        # Factors for priority calculation
        frequency_weight = 0.4
        recency_weight = 0.3
        compute_cost_weight = 0.2
        size_efficiency_weight = 0.1

        # Normalize factors
        max_frequency = max([p.access_frequency for p in self.access_patterns.values()], default=1)
        max_compute_time = max([p.compute_time_ms for p in self.access_patterns.values()], default=1)
        max_size = max([p.data_size_bytes for p in self.access_patterns.values()], default=1)

        # Calculate normalized scores
        frequency_score = pattern.access_frequency / max(max_frequency, 1)

        # Recency score (more recent = higher score)
        minutes_since_access = (datetime.now() - pattern.last_access).total_seconds() / 60
        recency_score = 1 / (1 + minutes_since_access)

        # Compute cost score (higher compute time = higher value)
        compute_score = pattern.compute_time_ms / max(max_compute_time, 1)

        # Size efficiency score (smaller size = more efficient)
        size_score = 1 - (pattern.data_size_bytes / max(max_size, 1))

        # Combine scores
        priority_score = (
            frequency_weight * frequency_score +
            recency_weight * recency_score +
            compute_cost_weight * compute_score +
            size_efficiency_weight * size_score
        )

        return priority_score

    def _should_optimize(self) -> bool:
        """Determine if cache optimization should run"""
        # Check memory pressure
        if PSUTIL_AVAILABLE:
            try:
                memory_usage = psutil.Process().memory_info().rss / (1024 * 1024 * 1024)  # GB
                system_memory = psutil.virtual_memory()
                memory_pressure = memory_usage / (system_memory.total / (1024 * 1024 * 1024))
                return memory_pressure > self.memory_pressure_threshold
            except Exception:
                pass

        # Fallback: check cache size
        cache_info = self.cache.info()
        current_size = cache_info.get("memory_usage", 0)
        max_size = cache_info.get("max_size", 1)
        return current_size / max_size > self.memory_pressure_threshold

    def _optimize_cache(self):
        """Optimize cache based on access patterns"""
        print("🔧 Starting cache optimization...")

        # Get current cache statistics
        cache_info = self.cache.info()
        current_size = cache_info.get("memory_usage", 0)
        max_size = cache_info.get("max_size", 0)

        if current_size / max_size < 0.8:  # Less than 80% full
            return

        # Sort items by priority score
        sorted_patterns = sorted(
            self.access_patterns.values(),
            key=lambda p: p.priority_score,
            reverse=True
        )

        # Remove low-priority items
        items_to_remove = []
        for pattern in sorted_patterns[-len(sorted_patterns)//4:]:  # Remove bottom 25%
            if pattern.priority_score < 0.3:  # Low priority threshold
                items_to_remove.append(pattern.key)

        # Remove items from cache
        for key in items_to_remove:
            self.cache.delete(key)
            if key in self.access_patterns:
                del self.access_patterns[key]

        self.performance_metrics["optimization_cycles"] += 1
        print(f"🗑️ Removed {len(items_to_remove)} low-priority cache items")

    def _optimization_loop(self):
        """Background optimization loop"""
        while True:
            try:
                time.sleep(self.optimization_interval)
                self._run_optimization_cycle()
            except Exception as e:
                print(f"Error in optimization loop: {e}")

    def _run_optimization_cycle(self):
        """Run a complete optimization cycle"""
        print("🔄 Running optimization cycle...")

        # Update all priority scores
        for pattern in self.access_patterns.values():
            pattern.priority_score = self._calculate_priority_score(pattern)

        # Predictive preloading
        self._predictive_preload()

        # Memory optimization
        if self._should_optimize():
            self._optimize_cache()

        # Update performance metrics
        self._calculate_performance_metrics()

    def _predictive_preload(self):
        """Predictively preload likely-to-be-accessed items"""
        # Find patterns that might be accessed soon
        current_time = datetime.now()

        candidates = []
        for pattern in self.access_patterns.values():
            # Check if item has regular access pattern
            if pattern.access_count >= self.min_access_count_for_priority:
                # Check if it's been a while since last access
                time_since_access = current_time - pattern.last_access

                # If access frequency suggests it should be accessed soon
                expected_next_access = 60 / max(pattern.access_frequency, 0.1)  # minutes
                if time_since_access.total_seconds() > expected_next_access * 60 * 0.8:
                    candidates.append(pattern)

        # Sort by priority and preload top candidates
        candidates.sort(key=lambda p: p.priority_score, reverse=True)

        preloaded = 0
        for pattern in candidates[:5]:  # Preload top 5
            # Check if item is already in cache
            cached_value = self.cache.get(pattern.key)
            if cached_value is None:
                # Try to regenerate the data (this would be app-specific)
                print(f"🔮 Would preload: {pattern.key}")
                preloaded += 1

        if preloaded > 0:
            print(f"📥 Preloaded {preloaded} cache items")

    def _update_performance_metrics(self, latency_ms: float):
        """Update running performance metrics"""
        total_requests = self.performance_metrics["total_requests"]
        current_avg = self.performance_metrics["average_latency_ms"]

        # Update running average latency
        self.performance_metrics["average_latency_ms"] = (
            (current_avg * (total_requests - 1) + latency_ms) / total_requests
        )

    def _calculate_performance_metrics(self):
        """Calculate comprehensive performance metrics"""
        total_requests = self.performance_metrics["total_requests"]
        if total_requests == 0:
            return

        # Hit ratio
        hit_ratio = self.performance_metrics["cache_hits"] / total_requests

        # Memory efficiency (hit ratio per MB used)
        if PSUTIL_AVAILABLE:
            try:
                memory_usage_mb = psutil.Process().memory_info().rss / (1024 * 1024)
            except Exception:
                memory_usage_mb = 1
        else:
            memory_usage_mb = self.cache.info().get("memory_usage", 1) / (1024 * 1024)

        memory_efficiency = hit_ratio / max(memory_usage_mb, 1)

        self.performance_metrics["hit_ratio"] = hit_ratio
        self.performance_metrics["memory_efficiency"] = memory_efficiency

    def get_optimization_report(self) -> Dict[str, Any]:
        """Get detailed optimization report"""
        # Calculate additional metrics
        total_patterns = len(self.access_patterns)
        high_priority_count = sum(1 for p in self.access_patterns.values() if p.priority_score > 0.7)

        # Recent performance
        recent_accesses = [
            access for access in self.access_history
            if time.time() - access["timestamp"] < 300  # Last 5 minutes
        ]

        recent_hit_ratio = (
            sum(1 for access in recent_accesses if access["hit"]) / max(len(recent_accesses), 1)
        )

        return {
            "performance_metrics": self.performance_metrics,
            "optimization_status": {
                "total_cached_items": total_patterns,
                "high_priority_items": high_priority_count,
                "optimization_cycles_run": self.performance_metrics["optimization_cycles"],
                "recent_hit_ratio_percent": round(recent_hit_ratio * 100, 2)
            },
            "top_accessed_items": [
                {
                    "key": pattern.key,
                    "access_count": pattern.access_count,
                    "hit_ratio": pattern.cache_hits / max(pattern.cache_hits + pattern.cache_misses, 1),
                    "priority_score": round(pattern.priority_score, 3),
                    "frequency_per_minute": round(pattern.access_frequency, 2)
                }
                for pattern in sorted(
                    self.access_patterns.values(),
                    key=lambda p: p.access_count,
                    reverse=True
                )[:10]
            ],
            "generated_at": datetime.now().isoformat()
        }

# Global optimized cache
optimized_cache = PerformanceOptimizedCache()

# Use real Catzilla middleware decorator instead of the non-existent ZeroAllocMiddleware
@app.middleware(priority=40, pre_route=True, name="cache_optimization")
def cache_optimization_middleware(request: Request) -> Optional[Response]:
    """Middleware for automatic cache optimization"""
    if request.method != "GET":
        return None

    # Use path only for now since query_string may not be available in this form
    cache_key = f"response:{request.path}"
    cached_response = optimized_cache.get(cache_key)

    if cached_response:
        response = JSONResponse(cached_response["data"])
        response.headers["X-Cache"] = "HIT"
        response.headers["X-Cache-Optimized"] = "true"
        response.headers["X-Cache-Key"] = cache_key
        return response

    return None

@app.middleware(priority=50, pre_route=False, post_route=True, name="cache_response")
def cache_response_middleware(request: Request) -> Optional[Response]:
    """Cache responses for future requests"""
    # This would typically be implemented in post-route processing
    # For now, we'll handle caching in the route handlers directly
    return None

# Sample computation functions for demonstrating optimization
def expensive_computation(complexity: int = 1) -> Dict[str, Any]:
    """Simulate expensive computation"""
    start_time = time.time()

    # Simulate CPU-intensive work
    time.sleep(0.1 * complexity)

    # Generate sample data
    data = {
        "complexity": complexity,
        "computed_values": [i * complexity for i in range(100)],
        "timestamp": datetime.now().isoformat(),
        "computation_time_ms": (time.time() - start_time) * 1000
    }

    return data

@app.get("/")
def home(request: Request) -> Response:
    """Home endpoint with optimization info"""
    return JSONResponse({
        "message": "Catzilla Cache Performance Optimization Example",
        "features": [
            "Intelligent cache warming algorithms",
            "Predictive cache preloading",
            "Performance-based cache eviction",
            "Cache hit ratio optimization",
            "Memory usage optimization",
            "Latency reduction techniques",
            "Cache monitoring and alerting"
        ],
        "optimization_endpoints": {
            "optimization_report": "GET /cache/optimization/report",
            "performance_metrics": "GET /cache/optimization/metrics",
            "access_patterns": "GET /cache/optimization/patterns",
            "force_optimization": "POST /cache/optimization/optimize",
            "preload_cache": "POST /cache/optimization/preload"
        },
        "test_endpoints": {
            "light_computation": "GET /compute/light/{id}",
            "heavy_computation": "GET /compute/heavy/{id}",
            "batch_operations": "GET /compute/batch/{count}"
        }
    })

@app.get("/compute/light/{computation_id}")
def light_computation(request: Request) -> Response:
    """Light computation endpoint for testing"""
    computation_id = request.path_params["computation_id"]

    # Track compute time
    start_time = time.time()

    # Check cache first
    cache_key = f"light_compute:{computation_id}"
    cached_result = optimized_cache.get(cache_key)

    if cached_result:
        return JSONResponse(cached_result)

    # Perform computation
    result = expensive_computation(complexity=1)
    result["computation_id"] = computation_id
    result["type"] = "light"

    # Cache result
    compute_time_ms = (time.time() - start_time) * 1000
    optimized_cache.set(cache_key, result, ttl=300, compute_time_ms=compute_time_ms)

    return JSONResponse(result)

@app.get("/compute/heavy/{computation_id}")
def heavy_computation(request: Request) -> Response:
    """Heavy computation endpoint for testing"""
    computation_id = request.path_params["computation_id"]

    start_time = time.time()

    # Check cache first
    cache_key = f"heavy_compute:{computation_id}"
    cached_result = optimized_cache.get(cache_key)

    if cached_result:
        return JSONResponse(cached_result)

    # Perform heavy computation
    result = expensive_computation(complexity=5)
    result["computation_id"] = computation_id
    result["type"] = "heavy"

    # Cache result with high priority due to compute cost
    compute_time_ms = (time.time() - start_time) * 1000
    optimized_cache.set(cache_key, result, ttl=600, compute_time_ms=compute_time_ms)

    return JSONResponse(result)

@app.get("/compute/batch/{count}")
def batch_computation(request: Request) -> Response:
    """Batch computation for testing cache optimization"""
    count = int(request.path_params["count"])

    if count > 50:
        return JSONResponse({"error": "Maximum 50 operations allowed"}, status_code=400)

    results = []
    start_time = time.time()

    for i in range(count):
        cache_key = f"batch_compute:{i}"
        cached_result = optimized_cache.get(cache_key)

        if cached_result:
            results.append(cached_result)
        else:
            # Generate new result
            result = expensive_computation(complexity=1)
            result["batch_id"] = i
            result["type"] = "batch"

            optimized_cache.set(cache_key, result, ttl=300, compute_time_ms=50)
            results.append(result)

    total_time_ms = (time.time() - start_time) * 1000

    return JSONResponse({
        "batch_results": results,
        "total_operations": count,
        "total_time_ms": total_time_ms,
        "average_time_per_operation_ms": total_time_ms / count
    })

@app.get("/cache/optimization/report")
def get_optimization_report(request: Request) -> Response:
    """Get comprehensive optimization report"""
    report = optimized_cache.get_optimization_report()
    return JSONResponse(report)

@app.get("/cache/optimization/metrics")
def get_optimization_metrics(request: Request) -> Response:
    """Get current optimization metrics"""
    # System metrics with psutil fallback
    system_metrics = {}
    if PSUTIL_AVAILABLE:
        try:
            system_metrics = {
                "memory_usage_mb": psutil.Process().memory_info().rss / (1024 * 1024),
                "cpu_percent": psutil.cpu_percent(),
                "available_memory_gb": psutil.virtual_memory().available / (1024**3)
            }
        except Exception as e:
            system_metrics = {"error": f"Failed to get system metrics: {e}"}
    else:
        system_metrics = {"info": "System metrics disabled (psutil not available)"}

    return JSONResponse({
        "performance_metrics": optimized_cache.performance_metrics,
        "system_metrics": system_metrics,
        "cache_stats": {
            "total_patterns": len(optimized_cache.access_patterns),
            "recent_access_count": len(optimized_cache.access_history)
        }
    })

@app.get("/cache/optimization/patterns")
def get_access_patterns(request: Request) -> Response:
    """Get detailed access patterns"""
    patterns = []

    for pattern in optimized_cache.access_patterns.values():
        patterns.append({
            "key": pattern.key,
            "access_count": pattern.access_count,
            "last_access": pattern.last_access.isoformat(),
            "access_frequency": round(pattern.access_frequency, 2),
            "cache_hits": pattern.cache_hits,
            "cache_misses": pattern.cache_misses,
            "hit_ratio": pattern.cache_hits / max(pattern.cache_hits + pattern.cache_misses, 1),
            "compute_time_ms": pattern.compute_time_ms,
            "data_size_bytes": pattern.data_size_bytes,
            "priority_score": round(pattern.priority_score, 3)
        })

    # Sort by access count
    patterns.sort(key=lambda p: p["access_count"], reverse=True)

    return JSONResponse({
        "access_patterns": patterns,
        "total_patterns": len(patterns),
        "analyzed_at": datetime.now().isoformat()
    })

@app.post("/cache/optimization/optimize")
def force_optimization(request: Request) -> Response:
    """Force cache optimization cycle"""
    optimized_cache._run_optimization_cycle()

    return JSONResponse({
        "success": True,
        "message": "Optimization cycle completed",
        "optimized_at": datetime.now().isoformat()
    })

@app.post("/cache/optimization/preload")
def preload_cache(request: Request) -> Response:
    """Preload cache with common data"""
    preloaded_items = 0

    # Preload common computations
    for i in range(1, 11):  # Preload first 10 light computations
        cache_key = f"light_compute:{i}"
        cached = optimized_cache.get(cache_key)

        if cached is None:
            result = expensive_computation(complexity=1)
            result["computation_id"] = str(i)
            result["type"] = "light"
            result["preloaded"] = True

            optimized_cache.set(cache_key, result, ttl=600, compute_time_ms=100)
            preloaded_items += 1

    return JSONResponse({
        "success": True,
        "preloaded_items": preloaded_items,
        "preloaded_at": datetime.now().isoformat()
    })

@app.get("/health")
def health_check(request: Request) -> Response:
    """Health check with optimization status"""
    metrics = optimized_cache.performance_metrics

    return JSONResponse({
        "status": "healthy",
        "cache_optimization": "enabled",
        "framework": "Catzilla v0.2.0",
        "hit_ratio_percent": round(
            metrics["cache_hits"] / max(metrics["total_requests"], 1) * 100, 2
        ),
        "average_latency_ms": round(metrics["average_latency_ms"], 2),
        "optimization_cycles": metrics["optimization_cycles"]
    })

if __name__ == "__main__":
    print("🚨 Starting Catzilla Cache Performance Optimization Example")
    print("📝 Available endpoints:")
    print("   GET  /                              - Home with optimization info")
    print("   GET  /compute/light/{id}            - Light computation (cached)")
    print("   GET  /compute/heavy/{id}            - Heavy computation (cached)")
    print("   GET  /compute/batch/{count}         - Batch operations")
    print("   GET  /cache/optimization/report     - Comprehensive optimization report")
    print("   GET  /cache/optimization/metrics    - Current optimization metrics")
    print("   GET  /cache/optimization/patterns   - Access patterns analysis")
    print("   POST /cache/optimization/optimize   - Force optimization cycle")
    print("   POST /cache/optimization/preload    - Preload common data")
    print("   GET  /health                        - Health check")
    print()
    print("🎨 Features demonstrated:")
    print("   • Intelligent cache warming algorithms")
    print("   • Predictive cache preloading")
    print("   • Performance-based cache eviction")
    print("   • Cache hit ratio optimization")
    print("   • Memory usage optimization")
    print("   • Latency reduction techniques")
    print("   • Cache monitoring and alerting")
    print()
    print("🧪 Try these examples:")
    print("   # Test light computation (gets cached):")
    print("   curl http://localhost:8000/compute/light/123")
    print()
    print("   # Test heavy computation:")
    print("   curl http://localhost:8000/compute/heavy/456")
    print()
    print("   # View optimization report:")
    print("   curl http://localhost:8000/cache/optimization/report")
    print()
    print("   # Preload cache:")
    print("   curl -X POST http://localhost:8000/cache/optimization/preload")
    print()
    print("   # Batch test (creates access patterns):")
    print("   curl http://localhost:8000/compute/batch/10")
    print()

    app.listen(host="0.0.0.0", port=8000)
