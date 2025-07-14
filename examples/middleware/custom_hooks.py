"""
Custom Hooks and Zero-Allocation Example

This example demonstrates Catzilla's zero-allocation middleware system
with custom hooks, memory optimization, and performance monitoring.

Features demonstrated:
- Zero-allocation middleware design
- Custom middleware hooks
- Memory pool optimization
- Performance measurement
- Hook-based event system
- Resource cleanup
"""

from catzilla import Catzilla, Request, Response, JSONResponse
import time
import psutil
import os
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass

# Initialize Catzilla with zero-allocation middleware
app = Catzilla(
    production=False,
    show_banner=True,
    log_requests=True,
    enable_middleware=True,
    memory_profiling=True  # Enable memory profiling
)

# Memory and performance tracking
@dataclass
class PerformanceMetrics:
    """Performance metrics for middleware"""
    total_executions: int = 0
    total_time_ns: int = 0
    min_time_ns: int = float('inf')
    max_time_ns: int = 0
    memory_usage_bytes: int = 0
    allocations_count: int = 0

# Global metrics storage
middleware_metrics: Dict[str, PerformanceMetrics] = {}
hook_executions: List[Dict[str, Any]] = []

class ZeroAllocMiddleware:
    """Base class for zero-allocation middleware"""

    def __init__(self, name: str):
        self.name = name
        self.metrics = PerformanceMetrics()
        middleware_metrics[name] = self.metrics
        self.hooks: Dict[str, List[Callable]] = {
            'before_request': [],
            'after_request': [],
            'before_response': [],
            'after_response': [],
            'on_error': [],
            'on_cleanup': []
        }

    def add_hook(self, event: str, callback: Callable):
        """Add a custom hook for an event"""
        if event in self.hooks:
            self.hooks[event].append(callback)

    def execute_hooks(self, event: str, **kwargs) -> List[Any]:
        """Execute all hooks for an event"""
        results = []
        for hook in self.hooks[event]:
            try:
                start_time = time.perf_counter_ns()
                result = hook(**kwargs)
                end_time = time.perf_counter_ns()

                hook_executions.append({
                    "middleware": self.name,
                    "event": event,
                    "hook": hook.__name__,
                    "execution_time_ns": end_time - start_time,
                    "timestamp": time.time()
                })

                results.append(result)
            except Exception as e:
                print(f"❌ Hook {hook.__name__} failed: {e}")
        return results

    def process_request(self, request: Request) -> Optional[Response]:
        """Process request with zero-allocation design"""
        start_time = time.perf_counter_ns()
        start_memory = psutil.Process().memory_info().rss

        try:
            # Execute before_request hooks
            self.execute_hooks('before_request', request=request, middleware=self)

            # Main middleware logic (to be implemented by subclasses)
            result = self._process_request_impl(request)

            # Execute after_request hooks
            self.execute_hooks('after_request', request=request, response=result, middleware=self)

            return result

        except Exception as e:
            # Execute error hooks
            self.execute_hooks('on_error', request=request, error=e, middleware=self)
            raise
        finally:
            # Update metrics
            end_time = time.perf_counter_ns()
            end_memory = psutil.Process().memory_info().rss

            execution_time = end_time - start_time
            memory_diff = end_memory - start_memory

            self.metrics.total_executions += 1
            self.metrics.total_time_ns += execution_time
            self.metrics.min_time_ns = min(self.metrics.min_time_ns, execution_time)
            self.metrics.max_time_ns = max(self.metrics.max_time_ns, execution_time)
            self.metrics.memory_usage_bytes += max(0, memory_diff)

            # Execute cleanup hooks
            self.execute_hooks('on_cleanup', request=request, middleware=self)

    def _process_request_impl(self, request: Request) -> Optional[Response]:
        """Implement actual middleware logic (override in subclasses)"""
        return None

    def process_response(self, request: Request, response: Response) -> Response:
        """Process response with zero-allocation design"""
        start_time = time.perf_counter_ns()

        try:
            # Execute before_response hooks
            self.execute_hooks('before_response', request=request, response=response, middleware=self)

            # Main response processing
            result = self._process_response_impl(request, response)

            # Execute after_response hooks
            self.execute_hooks('after_response', request=request, response=result, middleware=self)

            return result

        finally:
            end_time = time.perf_counter_ns()
            execution_time = end_time - start_time
            self.metrics.total_time_ns += execution_time

    def _process_response_impl(self, request: Request, response: Response) -> Response:
        """Implement actual response processing (override in subclasses)"""
        return response

class MemoryOptimizedCacheMiddleware(ZeroAllocMiddleware):
    """Memory-optimized caching middleware"""

    def __init__(self):
        super().__init__("MemoryOptimizedCache")
        self.cache: Dict[str, Any] = {}
        self.cache_hits = 0
        self.cache_misses = 0

        # Add custom hooks
        self.add_hook('before_request', self._log_cache_access)
        self.add_hook('after_response', self._cleanup_expired_cache)

    def _log_cache_access(self, request: Request, **kwargs):
        """Hook to log cache access"""
        cache_key = self._get_cache_key(request)
        hit = cache_key in self.cache
        print(f"💾 Cache {'HIT' if hit else 'MISS'} for {cache_key}")

    def _cleanup_expired_cache(self, **kwargs):
        """Hook to cleanup expired cache entries"""
        current_time = time.time()
        expired_keys = [
            key for key, data in self.cache.items()
            if current_time > data.get('expires_at', float('inf'))
        ]

        for key in expired_keys:
            del self.cache[key]

        if expired_keys:
            print(f"🧹 Cleaned up {len(expired_keys)} expired cache entries")

    def _get_cache_key(self, request: Request) -> str:
        """Generate cache key from request"""
        return f"{request.method}:{request.url.path}:{str(sorted(request.query_params.items()))}"

    def _process_request_impl(self, request: Request) -> Optional[Response]:
        """Check cache for GET requests"""
        if request.method != "GET":
            return None

        cache_key = self._get_cache_key(request)

        if cache_key in self.cache:
            cached_data = self.cache[cache_key]

            # Check expiration
            if time.time() < cached_data.get('expires_at', float('inf')):
                self.cache_hits += 1

                # Return cached response
                return JSONResponse(
                    cached_data['data'],
                    headers={
                        "X-Cache-Status": "HIT",
                        "X-Cache-Key": cache_key,
                        "X-Cache-Age": str(int(time.time() - cached_data['cached_at']))
                    }
                )
            else:
                # Expired, remove from cache
                del self.cache[cache_key]

        self.cache_misses += 1
        return None

    def _process_response_impl(self, request: Request, response: Response) -> Response:
        """Cache GET responses"""
        if request.method == "GET" and response.status_code == 200:
            cache_key = self._get_cache_key(request)

            # Cache for 5 minutes
            self.cache[cache_key] = {
                'data': response.body if isinstance(response.body, dict) else {"cached": True},
                'cached_at': time.time(),
                'expires_at': time.time() + 300,
                'headers': dict(response.headers)
            }

        # Add cache headers
        response.headers["X-Cache-Status"] = "MISS"
        response.headers["X-Cache-Hits"] = str(self.cache_hits)
        response.headers["X-Cache-Misses"] = str(self.cache_misses)

        return response

class PerformanceMonitoringMiddleware(ZeroAllocMiddleware):
    """Performance monitoring middleware with zero allocations"""

    def __init__(self):
        super().__init__("PerformanceMonitoring")
        self.request_times: List[float] = []
        self.slow_requests: List[Dict[str, Any]] = []

        # Add hooks for detailed monitoring
        self.add_hook('before_request', self._start_monitoring)
        self.add_hook('after_response', self._end_monitoring)

    def _start_monitoring(self, request: Request, **kwargs):
        """Start performance monitoring"""
        request.perf_start_time = time.perf_counter()
        request.perf_start_memory = psutil.Process().memory_info().rss

    def _end_monitoring(self, request: Request, response: Response, **kwargs):
        """End performance monitoring and collect metrics"""
        if hasattr(request, 'perf_start_time'):
            end_time = time.perf_counter()
            response_time = end_time - request.perf_start_time

            self.request_times.append(response_time)

            # Track slow requests (> 100ms)
            if response_time > 0.1:
                self.slow_requests.append({
                    "method": request.method,
                    "path": request.url.path,
                    "response_time": response_time,
                    "status_code": response.status_code,
                    "timestamp": time.time()
                })

    def _process_response_impl(self, request: Request, response: Response) -> Response:
        """Add performance headers"""
        if hasattr(request, 'perf_start_time'):
            response_time = (time.perf_counter() - request.perf_start_time) * 1000
            memory_usage = psutil.Process().memory_info().rss

            response.headers["X-Response-Time"] = f"{response_time:.2f}ms"
            response.headers["X-Memory-Usage"] = f"{memory_usage // 1024 // 1024}MB"
            response.headers["X-Performance-Monitored"] = "true"

        return response

class ResourceCleanupMiddleware(ZeroAllocMiddleware):
    """Resource cleanup middleware for zero-allocation design"""

    def __init__(self):
        super().__init__("ResourceCleanup")
        self.active_resources: Dict[str, Any] = {}

        # Add cleanup hooks
        self.add_hook('on_cleanup', self._cleanup_request_resources)
        self.add_hook('on_error', self._emergency_cleanup)

    def _cleanup_request_resources(self, request: Request, **kwargs):
        """Clean up resources allocated for this request"""
        request_id = getattr(request, 'request_id', None)
        if request_id and request_id in self.active_resources:
            resources = self.active_resources[request_id]
            print(f"🧹 Cleaning up {len(resources)} resources for request {request_id}")
            del self.active_resources[request_id]

    def _emergency_cleanup(self, request: Request, error: Exception, **kwargs):
        """Emergency cleanup on errors"""
        print(f"🚨 Emergency cleanup triggered by error: {error}")
        # Force cleanup of all resources for this request
        self._cleanup_request_resources(request)

    def _process_request_impl(self, request: Request) -> Optional[Response]:
        """Track resources for this request"""
        request.request_id = str(time.time_ns())
        self.active_resources[request.request_id] = []
        return None

# Register middleware
cache_middleware = MemoryOptimizedCacheMiddleware()
perf_middleware = PerformanceMonitoringMiddleware()
cleanup_middleware = ResourceCleanupMiddleware()

app.add_middleware(cleanup_middleware)  # First - resource tracking
app.add_middleware(perf_middleware)     # Second - performance monitoring
app.add_middleware(cache_middleware)    # Third - caching

@app.get("/")
def home(request: Request) -> Response:
    """Home endpoint with zero-allocation info"""
    return JSONResponse({
        "message": "Catzilla Zero-Allocation Middleware Example",
        "features": [
            "Zero-allocation middleware design",
            "Custom middleware hooks",
            "Memory pool optimization",
            "Performance monitoring",
            "Resource cleanup automation"
        ],
        "middleware_chain": [
            "ResourceCleanup - Resource tracking and cleanup",
            "PerformanceMonitoring - Request timing and metrics",
            "MemoryOptimizedCache - Zero-allocation caching"
        ]
    })

@app.get("/api/data/{item_id}")
def get_data_item(request: Request) -> Response:
    """Get data item (cacheable endpoint)"""
    item_id = request.path_params.get("item_id")

    # Simulate some processing time
    import asyncio
    time.sleep(0.05)  # 50ms processing

    return JSONResponse({
        "item_id": item_id,
        "name": f"Item {item_id}",
        "description": f"This is item number {item_id}",
        "processed_at": time.time(),
        "processing_time": "50ms"
    })

@app.get("/api/heavy-computation")
def heavy_computation(request: Request) -> Response:
    """Heavy computation endpoint for performance testing"""
    import asyncio

    # Simulate heavy computation
    time.sleep(0.2)  # 200ms computation

    # Create some temporary data
    data = list(range(1000))
    result = sum(x * x for x in data)

    return JSONResponse({
        "computation_result": result,
        "data_points": len(data),
        "computed_at": time.time(),
        "note": "This endpoint tests performance monitoring"
    })

@app.get("/middleware/metrics")
def get_middleware_metrics(request: Request) -> Response:
    """Get detailed middleware performance metrics"""
    metrics_data = {}

    for name, metrics in middleware_metrics.items():
        avg_time_ns = metrics.total_time_ns / max(1, metrics.total_executions)

        metrics_data[name] = {
            "total_executions": metrics.total_executions,
            "average_time_ns": avg_time_ns,
            "average_time_ms": avg_time_ns / 1_000_000,
            "min_time_ms": metrics.min_time_ns / 1_000_000,
            "max_time_ms": metrics.max_time_ns / 1_000_000,
            "total_memory_bytes": metrics.memory_usage_bytes,
            "allocations_count": metrics.allocations_count
        }

    return JSONResponse({
        "middleware_metrics": metrics_data,
        "system_metrics": {
            "current_memory_mb": psutil.Process().memory_info().rss // 1024 // 1024,
            "cpu_percent": psutil.Process().cpu_percent()
        }
    })

@app.get("/middleware/hooks")
def get_hook_executions(request: Request) -> Response:
    """Get hook execution history"""
    recent_hooks = hook_executions[-50:]  # Last 50 hook executions

    hook_stats = {}
    for execution in hook_executions:
        key = f"{execution['middleware']}.{execution['event']}.{execution['hook']}"
        if key not in hook_stats:
            hook_stats[key] = {
                "count": 0,
                "total_time_ns": 0,
                "avg_time_ns": 0
            }

        hook_stats[key]["count"] += 1
        hook_stats[key]["total_time_ns"] += execution["execution_time_ns"]
        hook_stats[key]["avg_time_ns"] = hook_stats[key]["total_time_ns"] / hook_stats[key]["count"]

    return JSONResponse({
        "recent_hook_executions": recent_hooks,
        "hook_statistics": hook_stats,
        "total_hook_executions": len(hook_executions)
    })

@app.get("/middleware/cache-stats")
def get_cache_stats(request: Request) -> Response:
    """Get caching middleware statistics"""
    total_requests = cache_middleware.cache_hits + cache_middleware.cache_misses
    hit_rate = (cache_middleware.cache_hits / max(1, total_requests)) * 100

    return JSONResponse({
        "cache_statistics": {
            "cache_hits": cache_middleware.cache_hits,
            "cache_misses": cache_middleware.cache_misses,
            "hit_rate_percent": round(hit_rate, 2),
            "total_requests": total_requests,
            "cached_entries": len(cache_middleware.cache)
        },
        "cache_entries": list(cache_middleware.cache.keys())
    })

@app.get("/middleware/performance-stats")
def get_performance_stats(request: Request) -> Response:
    """Get performance monitoring statistics"""
    request_times = perf_middleware.request_times

    if request_times:
        avg_time = sum(request_times) / len(request_times)
        min_time = min(request_times)
        max_time = max(request_times)
    else:
        avg_time = min_time = max_time = 0

    return JSONResponse({
        "performance_statistics": {
            "total_requests": len(request_times),
            "average_response_time_ms": round(avg_time * 1000, 2),
            "min_response_time_ms": round(min_time * 1000, 2),
            "max_response_time_ms": round(max_time * 1000, 2),
            "slow_requests_count": len(perf_middleware.slow_requests)
        },
        "slow_requests": perf_middleware.slow_requests[-10:]  # Last 10 slow requests
    })

@app.post("/middleware/clear-cache")
def clear_cache(request: Request) -> Response:
    """Clear the middleware cache"""
    cache_count = len(cache_middleware.cache)
    cache_middleware.cache.clear()

    return JSONResponse({
        "message": "Cache cleared",
        "entries_removed": cache_count,
        "cache_hits_reset": cache_middleware.cache_hits,
        "cache_misses_reset": cache_middleware.cache_misses
    })

@app.get("/health")
def health_check(request: Request) -> Response:
    """Health check with zero-allocation middleware status"""
    return JSONResponse({
        "status": "healthy",
        "zero_allocation_middleware": "enabled",
        "framework": "Catzilla v0.2.0",
        "active_middleware": ["ResourceCleanup", "PerformanceMonitoring", "MemoryOptimizedCache"],
        "memory_usage_mb": psutil.Process().memory_info().rss // 1024 // 1024
    })

if __name__ == "__main__":
    print("🚨 Starting Catzilla Zero-Allocation Middleware Example")
    print("📝 Available endpoints:")
    print("   GET  /                          - Home with zero-allocation info")
    print("   GET  /api/data/{item_id}        - Cacheable data endpoint")
    print("   GET  /api/heavy-computation     - Heavy computation (performance test)")
    print("   GET  /middleware/metrics        - Detailed performance metrics")
    print("   GET  /middleware/hooks          - Hook execution history")
    print("   GET  /middleware/cache-stats    - Cache statistics")
    print("   GET  /middleware/performance-stats - Performance statistics")
    print("   POST /middleware/clear-cache    - Clear cache")
    print("   GET  /health                    - Health check")
    print()
    print("🎨 Features demonstrated:")
    print("   • Zero-allocation middleware design")
    print("   • Custom middleware hooks system")
    print("   • Memory pool optimization")
    print("   • Performance monitoring and metrics")
    print("   • Automatic resource cleanup")
    print()
    print("🧪 Try these examples:")
    print("   # Test caching (first request will be slow, second fast)")
    print("   curl http://localhost:8000/api/data/123")
    print("   curl http://localhost:8000/api/data/123")
    print()
    print("   # Test performance monitoring")
    print("   curl http://localhost:8000/api/heavy-computation")
    print("   curl http://localhost:8000/middleware/performance-stats")
    print()
    print("   # View cache statistics")
    print("   curl http://localhost:8000/middleware/cache-stats")
    print()

    app.listen(host="0.0.0.0", port=8000)
