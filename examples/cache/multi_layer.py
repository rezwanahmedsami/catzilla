"""
Multi-Layer Caching Example

This example demonstrates Catzilla's comprehensive caching system
with memory, Redis, and disk caching layers.

Features demonstrated:
- Memory caching with LRU eviction
- Redis caching for distributed systems
- Disk caching for persistence
- Cache warming and preloading
- Cache invalidation strategies
- Performance monitoring and metrics
- Automatic cache layer fallback
"""

from catzilla import Catzilla, Request, Response, JSONResponse
from catzilla.cache import MemoryCache, RedisCache, DiskCache, CacheLayer
from catzilla.middleware import ZeroAllocMiddleware
import asyncio
import json
import time
import hashlib
from typing import Any, Dict, List, Optional, Union
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
import psutil
import uuid

# Initialize Catzilla with caching
app = Catzilla(
    production=False,
    show_banner=True,
    log_requests=True,
    enable_caching=True
)

# Cache configuration
CACHE_CONFIG = {
    "memory": {
        "max_size": 100 * 1024 * 1024,  # 100MB
        "max_items": 10000,
        "ttl_seconds": 300  # 5 minutes
    },
    "redis": {
        "host": "localhost",
        "port": 6379,
        "db": 0,
        "ttl_seconds": 3600  # 1 hour
    },
    "disk": {
        "cache_dir": "cache_storage",
        "max_size": 1024 * 1024 * 1024,  # 1GB
        "ttl_seconds": 86400  # 24 hours
    }
}

# Initialize cache layers
@dataclass
class CacheMetrics:
    """Cache performance metrics"""
    hits: int = 0
    misses: int = 0
    sets: int = 0
    evictions: int = 0
    errors: int = 0
    total_requests: int = 0
    average_response_time_ms: float = 0.0
    memory_usage_bytes: int = 0

class CacheManager:
    """Multi-layer cache manager with fallback support"""

    def __init__(self):
        # Initialize cache layers
        self.memory_cache = MemoryCache(
            max_size=CACHE_CONFIG["memory"]["max_size"],
            max_items=CACHE_CONFIG["memory"]["max_items"],
            default_ttl=CACHE_CONFIG["memory"]["ttl_seconds"]
        )

        # Try to initialize Redis cache
        try:
            self.redis_cache = RedisCache(
                host=CACHE_CONFIG["redis"]["host"],
                port=CACHE_CONFIG["redis"]["port"],
                db=CACHE_CONFIG["redis"]["db"],
                default_ttl=CACHE_CONFIG["redis"]["ttl_seconds"]
            )
            self.redis_available = True
        except Exception as e:
            print(f"Redis not available: {e}")
            self.redis_cache = None
            self.redis_available = False

        self.disk_cache = DiskCache(
            cache_dir=CACHE_CONFIG["disk"]["cache_dir"],
            max_size=CACHE_CONFIG["disk"]["max_size"],
            default_ttl=CACHE_CONFIG["disk"]["ttl_seconds"]
        )

        # Cache layers in order of preference (fastest first)
        self.cache_layers = [
            ("memory", self.memory_cache),
            ("redis", self.redis_cache) if self.redis_available else None,
            ("disk", self.disk_cache)
        ]
        self.cache_layers = [layer for layer in self.cache_layers if layer is not None]

        # Metrics tracking
        self.metrics = {
            "memory": CacheMetrics(),
            "redis": CacheMetrics() if self.redis_available else None,
            "disk": CacheMetrics()
        }
        self.global_metrics = CacheMetrics()

    def get(self, key: str) -> Optional[Any]:
        """Get value from cache with layer fallback"""
        start_time = time.time()

        try:
            # Try each cache layer in order
            for layer_name, cache in self.cache_layers:
                try:
                    value = cache.get(key)
                    if value is not None:
                        # Cache hit - update metrics
                        self.metrics[layer_name].hits += 1
                        self.global_metrics.hits += 1

                        # Populate higher priority caches
                        self._populate_higher_caches(key, value, layer_name)

                        return value

                except Exception as e:
                    self.metrics[layer_name].errors += 1
                    print(f"Error accessing {layer_name} cache: {e}")
                    continue

            # Cache miss - no value found in any layer
            for layer_name, _ in self.cache_layers:
                self.metrics[layer_name].misses += 1
            self.global_metrics.misses += 1

            return None

        finally:
            # Update response time metrics
            response_time = (time.time() - start_time) * 1000
            self.global_metrics.total_requests += 1

            # Calculate running average
            total = self.global_metrics.total_requests
            current_avg = self.global_metrics.average_response_time_ms
            self.global_metrics.average_response_time_ms = (
                (current_avg * (total - 1) + response_time) / total
            )

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in all cache layers"""
        success_count = 0

        for layer_name, cache in self.cache_layers:
            try:
                cache.set(key, value, ttl)
                self.metrics[layer_name].sets += 1
                success_count += 1

            except Exception as e:
                self.metrics[layer_name].errors += 1
                print(f"Error setting {layer_name} cache: {e}")

        self.global_metrics.sets += 1
        return success_count > 0

    def delete(self, key: str) -> bool:
        """Delete key from all cache layers"""
        success_count = 0

        for layer_name, cache in self.cache_layers:
            try:
                cache.delete(key)
                success_count += 1

            except Exception as e:
                self.metrics[layer_name].errors += 1
                print(f"Error deleting from {layer_name} cache: {e}")

        return success_count > 0

    def _populate_higher_caches(self, key: str, value: Any, source_layer: str):
        """Populate caches with higher priority than source layer"""
        source_index = next(
            i for i, (name, _) in enumerate(self.cache_layers)
            if name == source_layer
        )

        # Populate all layers before the source layer
        for i in range(source_index):
            layer_name, cache = self.cache_layers[i]
            try:
                cache.set(key, value)
            except Exception as e:
                print(f"Error populating {layer_name} cache: {e}")

    def clear_all(self):
        """Clear all cache layers"""
        for layer_name, cache in self.cache_layers:
            try:
                cache.clear()
            except Exception as e:
                print(f"Error clearing {layer_name} cache: {e}")

    def get_metrics(self) -> Dict[str, Any]:
        """Get comprehensive cache metrics"""
        layer_metrics = {}

        for layer_name, _ in self.cache_layers:
            metrics = self.metrics[layer_name]
            hit_rate = metrics.hits / (metrics.hits + metrics.misses) if (metrics.hits + metrics.misses) > 0 else 0

            layer_metrics[layer_name] = {
                **asdict(metrics),
                "hit_rate": round(hit_rate * 100, 2),
                "available": True
            }

        # Add global metrics
        global_hit_rate = (
            self.global_metrics.hits / (self.global_metrics.hits + self.global_metrics.misses)
            if (self.global_metrics.hits + self.global_metrics.misses) > 0 else 0
        )

        return {
            "global": {
                **asdict(self.global_metrics),
                "hit_rate": round(global_hit_rate * 100, 2)
            },
            "layers": layer_metrics,
            "configuration": CACHE_CONFIG
        }

# Global cache manager
cache_manager = CacheManager()

class CacheMiddleware(ZeroAllocMiddleware):
    """Middleware for automatic response caching"""

    priority = 50

    def __init__(self):
        self.cacheable_paths = {
            '/api/data/', '/api/stats/', '/api/report/',
            '/api/users/', '/api/products/'
        }
        self.cache_ttl = 300  # 5 minutes

    def _should_cache(self, request: Request) -> bool:
        """Determine if request should be cached"""
        # Only cache GET requests
        if request.method != "GET":
            return False

        # Check if path is cacheable
        path = request.url.path
        return any(path.startswith(cacheable) for cacheable in self.cacheable_paths)

    def _generate_cache_key(self, request: Request) -> str:
        """Generate cache key for request"""
        # Include path and query parameters
        key_data = f"{request.method}:{request.url.path}:{request.url.query}"
        return f"response:{hashlib.md5(key_data.encode()).hexdigest()}"

    def process_request(self, request: Request) -> Optional[Response]:
        """Check cache for existing response"""
        if not self._should_cache(request):
            return None

        cache_key = self._generate_cache_key(request)
        cached_response = cache_manager.get(cache_key)

        if cached_response:
            # Return cached response
            return Response(
                content=cached_response["content"],
                status_code=cached_response["status_code"],
                headers={
                    **cached_response["headers"],
                    "X-Cache": "HIT",
                    "X-Cache-Key": cache_key
                }
            )

        return None

    def process_response(self, request: Request, response: Response) -> Response:
        """Cache response if cacheable"""
        if not self._should_cache(request) or response.status_code != 200:
            return response

        cache_key = self._generate_cache_key(request)

        # Cache response data
        cached_data = {
            "content": response.body.decode() if isinstance(response.body, bytes) else response.body,
            "status_code": response.status_code,
            "headers": dict(response.headers),
            "cached_at": datetime.now().isoformat()
        }

        cache_manager.set(cache_key, cached_data, self.cache_ttl)

        # Add cache headers
        response.headers["X-Cache"] = "MISS"
        response.headers["X-Cache-Key"] = cache_key

        return response

# Add caching middleware
app.add_middleware(CacheMiddleware)

# Sample data for caching demonstrations
SAMPLE_DATA = {
    "users": [
        {"id": i, "name": f"User {i}", "email": f"user{i}@example.com", "active": i % 2 == 0}
        for i in range(1, 101)
    ],
    "products": [
        {"id": i, "name": f"Product {i}", "price": i * 10.0, "category": f"category_{i % 5}"}
        for i in range(1, 51)
    ],
    "orders": [
        {"id": i, "user_id": (i % 100) + 1, "product_id": (i % 50) + 1, "quantity": i % 10 + 1}
        for i in range(1, 201)
    ]
}

@app.get("/")
def home(request: Request) -> Response:
    """Home endpoint with caching info"""
    return JSONResponse({
        "message": "Catzilla Multi-Layer Caching Example",
        "features": [
            "Memory caching with LRU eviction",
            "Redis caching for distributed systems",
            "Disk caching for persistence",
            "Cache warming and preloading",
            "Cache invalidation strategies",
            "Performance monitoring and metrics",
            "Automatic cache layer fallback"
        ],
        "cache_endpoints": {
            "cache_data": "POST /cache/set",
            "get_cached": "GET /cache/get/{key}",
            "delete_cached": "DELETE /cache/delete/{key}",
            "clear_cache": "DELETE /cache/clear",
            "cache_metrics": "GET /cache/metrics",
            "warm_cache": "POST /cache/warm",
            "cached_data_apis": [
                "GET /api/data/users",
                "GET /api/data/products",
                "GET /api/data/orders",
                "GET /api/stats/summary",
                "GET /api/report/performance"
            ]
        },
        "cache_layers": [name for name, _ in cache_manager.cache_layers]
    })

@app.post("/cache/set")
def set_cache_value(request: Request) -> Response:
    """Set value in cache"""
    try:
        data = request.json()
        key = data.get("key")
        value = data.get("value")
        ttl = data.get("ttl")

        if not key:
            return JSONResponse({"error": "Key is required"}, status_code=400)

        success = cache_manager.set(key, value, ttl)

        return JSONResponse({
            "success": success,
            "key": key,
            "cached_at": datetime.now().isoformat(),
            "ttl_seconds": ttl
        })

    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=400)

@app.get("/cache/get/{key}")
def get_cache_value(request: Request) -> Response:
    """Get value from cache"""
    key = request.path_params["key"]

    value = cache_manager.get(key)

    if value is None:
        return JSONResponse({"error": f"Key '{key}' not found in cache"}, status_code=404)

    return JSONResponse({
        "key": key,
        "value": value,
        "retrieved_at": datetime.now().isoformat()
    })

@app.delete("/cache/delete/{key}")
def delete_cache_value(request: Request) -> Response:
    """Delete value from cache"""
    key = request.path_params["key"]

    success = cache_manager.delete(key)

    return JSONResponse({
        "success": success,
        "key": key,
        "deleted_at": datetime.now().isoformat()
    })

@app.delete("/cache/clear")
def clear_all_cache(request: Request) -> Response:
    """Clear all cache layers"""
    cache_manager.clear_all()

    return JSONResponse({
        "success": True,
        "message": "All cache layers cleared",
        "cleared_at": datetime.now().isoformat()
    })

@app.get("/cache/metrics")
def get_cache_metrics(request: Request) -> Response:
    """Get comprehensive cache metrics"""
    metrics = cache_manager.get_metrics()

    # Add system memory info
    memory_info = psutil.virtual_memory()

    metrics["system"] = {
        "total_memory_gb": round(memory_info.total / (1024**3), 2),
        "available_memory_gb": round(memory_info.available / (1024**3), 2),
        "memory_usage_percent": memory_info.percent
    }

    return JSONResponse(metrics)

@app.post("/cache/warm")
def warm_cache(request: Request) -> Response:
    """Warm cache with sample data"""
    warmed_keys = []

    # Warm with sample data
    for data_type, items in SAMPLE_DATA.items():
        cache_key = f"sample_data:{data_type}"
        cache_manager.set(cache_key, items, 3600)  # 1 hour TTL
        warmed_keys.append(cache_key)

        # Also cache individual items
        for item in items[:10]:  # Cache first 10 items
            item_key = f"{data_type}:item:{item['id']}"
            cache_manager.set(item_key, item, 1800)  # 30 minutes TTL
            warmed_keys.append(item_key)

    # Warm with computed data
    stats_data = {
        "total_users": len(SAMPLE_DATA["users"]),
        "total_products": len(SAMPLE_DATA["products"]),
        "total_orders": len(SAMPLE_DATA["orders"]),
        "active_users": sum(1 for u in SAMPLE_DATA["users"] if u["active"]),
        "computed_at": datetime.now().isoformat()
    }

    cache_manager.set("stats:summary", stats_data, 600)  # 10 minutes TTL
    warmed_keys.append("stats:summary")

    return JSONResponse({
        "success": True,
        "warmed_keys": warmed_keys,
        "total_keys_warmed": len(warmed_keys),
        "warmed_at": datetime.now().isoformat()
    })

# Cached API endpoints for demonstration
@app.get("/api/data/users")
def get_users_data(request: Request) -> Response:
    """Get users data (cached automatically)"""
    # Simulate some processing time
    time.sleep(0.1)

    return JSONResponse({
        "users": SAMPLE_DATA["users"],
        "total": len(SAMPLE_DATA["users"]),
        "generated_at": datetime.now().isoformat()
    })

@app.get("/api/data/products")
def get_products_data(request: Request) -> Response:
    """Get products data (cached automatically)"""
    time.sleep(0.1)

    return JSONResponse({
        "products": SAMPLE_DATA["products"],
        "total": len(SAMPLE_DATA["products"]),
        "generated_at": datetime.now().isoformat()
    })

@app.get("/api/data/orders")
def get_orders_data(request: Request) -> Response:
    """Get orders data (cached automatically)"""
    time.sleep(0.15)

    return JSONResponse({
        "orders": SAMPLE_DATA["orders"],
        "total": len(SAMPLE_DATA["orders"]),
        "generated_at": datetime.now().isoformat()
    })

@app.get("/api/stats/summary")
def get_stats_summary(request: Request) -> Response:
    """Get statistics summary (cached automatically)"""
    # Simulate heavy computation
    time.sleep(0.2)

    # Check cache first
    cached_stats = cache_manager.get("stats:summary")
    if cached_stats:
        return JSONResponse(cached_stats)

    # Compute stats
    stats = {
        "total_users": len(SAMPLE_DATA["users"]),
        "active_users": sum(1 for u in SAMPLE_DATA["users"] if u["active"]),
        "total_products": len(SAMPLE_DATA["products"]),
        "total_orders": len(SAMPLE_DATA["orders"]),
        "average_order_quantity": sum(o["quantity"] for o in SAMPLE_DATA["orders"]) / len(SAMPLE_DATA["orders"]),
        "user_activity_rate": sum(1 for u in SAMPLE_DATA["users"] if u["active"]) / len(SAMPLE_DATA["users"]) * 100,
        "computed_at": datetime.now().isoformat()
    }

    # Cache the computed stats
    cache_manager.set("stats:summary", stats, 600)

    return JSONResponse(stats)

@app.get("/api/report/performance")
def get_performance_report(request: Request) -> Response:
    """Get performance report (cached automatically)"""
    time.sleep(0.3)  # Simulate expensive computation

    cache_metrics = cache_manager.get_metrics()

    report = {
        "cache_performance": {
            "global_hit_rate": cache_metrics["global"]["hit_rate"],
            "total_requests": cache_metrics["global"]["total_requests"],
            "average_response_time_ms": cache_metrics["global"]["average_response_time_ms"]
        },
        "layer_performance": {
            layer: {
                "hit_rate": metrics["hit_rate"],
                "hits": metrics["hits"],
                "misses": metrics["misses"]
            }
            for layer, metrics in cache_metrics["layers"].items()
        },
        "recommendations": [],
        "generated_at": datetime.now().isoformat()
    }

    # Add performance recommendations
    if cache_metrics["global"]["hit_rate"] < 50:
        report["recommendations"].append("Consider increasing cache TTL or warming more data")

    if cache_metrics["global"]["average_response_time_ms"] > 100:
        report["recommendations"].append("Cache response times are high, check cache layer performance")

    return JSONResponse(report)

@app.get("/health")
def health_check(request: Request) -> Response:
    """Health check with cache status"""
    cache_metrics = cache_manager.get_metrics()

    return JSONResponse({
        "status": "healthy",
        "caching": "enabled",
        "framework": "Catzilla v0.2.0",
        "cache_layers": [name for name, _ in cache_manager.cache_layers],
        "cache_hit_rate": cache_metrics["global"]["hit_rate"],
        "total_cache_requests": cache_metrics["global"]["total_requests"]
    })

if __name__ == "__main__":
    print("🚨 Starting Catzilla Multi-Layer Caching Example")
    print("📝 Available endpoints:")
    print("   GET  /                        - Home with caching info")
    print("   POST /cache/set               - Set cache value")
    print("   GET  /cache/get/{key}         - Get cache value")
    print("   DELETE /cache/delete/{key}    - Delete cache value")
    print("   DELETE /cache/clear           - Clear all cache")
    print("   GET  /cache/metrics           - Cache metrics")
    print("   POST /cache/warm              - Warm cache with data")
    print("   GET  /api/data/users          - Cached users data")
    print("   GET  /api/data/products       - Cached products data")
    print("   GET  /api/data/orders         - Cached orders data")
    print("   GET  /api/stats/summary       - Cached statistics")
    print("   GET  /api/report/performance  - Cached performance report")
    print("   GET  /health                  - Health check")
    print()
    print("🎨 Features demonstrated:")
    print("   • Memory caching with LRU eviction")
    print("   • Redis caching for distributed systems")
    print("   • Disk caching for persistence")
    print("   • Cache warming and preloading")
    print("   • Cache invalidation strategies")
    print("   • Performance monitoring and metrics")
    print("   • Automatic cache layer fallback")
    print()
    print("🧪 Try these examples:")
    print("   # Warm cache:")
    print("   curl -X POST http://localhost:8000/cache/warm")
    print()
    print("   # Get cached data (fast):")
    print("   curl http://localhost:8000/api/data/users")
    print()
    print("   # View cache metrics:")
    print("   curl http://localhost:8000/cache/metrics")
    print()
    print("   # Set custom cache value:")
    print("   curl -X POST -H 'Content-Type: application/json' \\")
    print("        -d '{\"key\":\"test\",\"value\":\"hello\",\"ttl\":300}' \\")
    print("        http://localhost:8000/cache/set")
    print()

    app.listen(host="0.0.0.0", port=8000)
