Caching
=======

Catzilla provides a sophisticated **SmartCache** system with C-accelerated performance, featuring multi-tier caching (Memory, Redis, Disk), intelligent compression, and zero-allocation operations. Build ultra-high-performance applications with automatic cache optimization.

Overview
--------

Catzilla's SmartCache system provides:

- **C-Accelerated Performance** - Native C implementation for maximum speed
- **Multi-Tier Architecture** - Memory (L1), Redis (L2), and Disk (L3) cache layers with automatic fallback
- **Zero-Allocation Design** - Memory-efficient operations with jemalloc integration
- **Intelligent Compression** - Automatic data compression for optimal memory usage
- **Function-Level Caching** - ``@cached`` decorator for automatic function result caching
- **Manual Cache Operations** - Direct cache.get/set/clear operations for fine-grained control
- **Real-Time Analytics** - Detailed hit/miss ratios and performance monitoring
- **High Throughput** - Demonstrated 1,000x+ performance improvements

Quick Start
-----------

Basic SmartCache Setup
~~~~~~~~~~~~~~~~~~~~~~

Simple SmartCache configuration for fast data access:

.. code-block:: python

   from catzilla import Catzilla, Request, Response, JSONResponse, SmartCache, SmartCacheConfig, cached, Path
   import time

   app = Catzilla()

   # Configure SmartCache with multi-tier setup
   cache_config = SmartCacheConfig(
       memory_capacity=1000,     # Store up to 1000 items in memory
       memory_ttl=300,          # 5 minutes default TTL
       compression_enabled=True, # Enable compression for large values
       jemalloc_enabled=True,   # Optimize memory allocation
       disk_enabled=True,       # Enable disk persistence
       disk_path="/tmp/catzilla_cache"
   )

   cache = SmartCache(cache_config)

   @app.get("/cached-data/{key}")
   def get_cached_data(
       request: Request,
       key: str = Path(..., description="Cache key to retrieve")
   ) -> Response:
       """Get data with SmartCache caching"""

       # Try to get from cache first
       cached_value, found = cache.get(f"data:{key}")

       if found:
           return JSONResponse({
               "data": cached_value,
               "source": "cache",
               "cache_hit": True
           })

       # Generate expensive data (simulation)
       time.sleep(0.1)  # Simulate expensive operation
       expensive_data = {
           "key": key,
           "value": f"Generated data for {key}",
           "timestamp": time.time(),
           "computation_time": "100ms"
       }

       # Store in cache for 5 minutes
       cache.set(f"data:{key}", expensive_data, ttl=300)

       return JSONResponse({
           "data": expensive_data,
           "source": "computation",
           "cache_hit": False
       })

   if __name__ == "__main__":
       print("🚀 Starting cache demo server...")
       print("Try: http://localhost:8000/cached-data/example")
       app.listen(port=8000)

Cache Decorator
~~~~~~~~~~~~~~~

Use the ``@cached`` decorator for automatic function result caching:

.. code-block:: python

   from catzilla import Catzilla, Request, Response, JSONResponse, cached, Path
   import time

   app = Catzilla()

   @cached(ttl=600, key_prefix="user_data")
   def get_user_data(user_id: int):
       """Expensive user data retrieval with caching"""
       # Simulate database query
       time.sleep(0.05)

       return {
           "user_id": user_id,
           "name": f"User {user_id}",
           "email": f"user{user_id}@example.com",
           "profile": {
               "created_at": "2023-01-01",
               "last_active": time.time()
           }
       }

   @app.get("/users/{user_id}")
   def get_user(
       request: Request,
       user_id: int = Path(..., ge=1, description="User ID")
   ) -> Response:
       """Get user with automatic caching"""
       user_data = get_user_data(user_id)

       return JSONResponse({
           "user": user_data,
           "cached": True  # Automatically cached by decorator
       })

   if __name__ == "__main__":
       print("🚀 Starting cached function demo...")
       print("Try: http://localhost:8000/users/123")
       app.listen(port=8000)

Multi-Tier SmartCache
---------------------

Configure Multi-Tier Cache
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Set up Memory (L1), Redis (L2), and Disk (L3) caching tiers:

.. code-block:: python

   from catzilla import Catzilla, Request, Response, JSONResponse, SmartCache, SmartCacheConfig, Path
   import time

   app = Catzilla()

   # Configure multi-tier cache with all layers
   cache_config = SmartCacheConfig(
       # Memory Cache (L1) - Ultra-fast C-level cache
       memory_capacity=5000,
       memory_ttl=300,  # 5 minutes
       compression_enabled=True,
       jemalloc_enabled=True,

       # Redis Cache (L2) - Distributed cache
       redis_enabled=True,
       redis_url="redis://localhost:6379/0",
       redis_ttl=1800,  # 30 minutes

       # Disk Cache (L3) - Persistent cache
       disk_enabled=True,
       disk_path="/tmp/catzilla_cache",
       disk_ttl=3600,  # 1 hour

       # Performance settings
       enable_stats=True,
       auto_expire_interval=60,
   )

   # Create SmartCache with multi-tier configuration
   cache = SmartCache(cache_config)

   def generate_complex_computation(key: str):
       """Simulate expensive computation"""
       time.sleep(0.2)  # Simulate 200ms computation

       return {
           "key": key,
           "result": f"Complex result for {key}",
           "computed_at": time.time(),
           "computation_cost": "expensive"
       }

   @app.get("/multilayer-data/{key}")
   def get_multilayer_data(
       request: Request,
       key: str = Path(..., description="Data key for multi-tier caching")
   ) -> Response:
       """Data retrieval with multi-tier caching"""

       cache_key = f"complex_data:{key}"

       # Cache will automatically check tiers in order: Memory → Redis → Disk
       cached_data, found = cache.get(cache_key)

       if found:
           return JSONResponse({
               "data": cached_data,
               "cache_tier": "multi_tier",
               "cache_hit": True
           })

       # Generate complex data
       complex_data = generate_complex_computation(key)

       # Store in cache (will be stored across all available tiers)
       cache.set(cache_key, complex_data, ttl=3600)  # 1 hour

       return JSONResponse({
           "data": complex_data,
           "cache_tier": "none",
           "cache_hit": False
       })

   if __name__ == "__main__":
       print("🚀 Starting multi-tier cache demo...")
       print("Try: http://localhost:8000/multilayer-data/example")
       app.listen(port=8000)

Cache Strategies
~~~~~~~~~~~~~~~~

Implement different caching patterns with SmartCache:

.. code-block:: python

   from catzilla import Catzilla, Request, Response, JSONResponse, SmartCache, SmartCacheConfig, Path
   import time

   app = Catzilla()

   # Initialize cache
   cache_config = SmartCacheConfig(
       memory_capacity=1000,
       memory_ttl=300,
       disk_enabled=True,
       disk_path="/tmp/catzilla_strategies"
   )
   cache = SmartCache(cache_config)

   def expensive_database_query(key: str):
       """Simulate expensive database operation"""
       time.sleep(0.1)
       return {"key": key, "data": f"Database result for {key}", "timestamp": time.time()}

   def fetch_data_for_key(key: str):
       """Fetch data for cache warming"""
       return {"key": key, "warmed_data": f"Warmed data for {key}"}

   # Cache-Aside Pattern (Most Common)
   @app.get("/cache-aside/{key}")
   def cache_aside_example(
       request: Request,
       key: str = Path(..., description="Cache key")
   ) -> Response:
       """Cache-aside pattern with SmartCache"""
       cache_key = f"aside:{key}"

       # 1. Try cache first
       cached, found = cache.get(cache_key)
       if found:
           return JSONResponse({"data": cached, "strategy": "cache_aside", "hit": True})

       # 2. Cache miss - fetch from source
       data = expensive_database_query(key)

       # 3. Store in cache for next time
       cache.set(cache_key, data, ttl=300)

       return JSONResponse({"data": data, "strategy": "cache_aside", "hit": False})

   # Write-Through Pattern
   @app.post("/write-through/{key}")
   def write_through_example(
       request: Request,
       key: str = Path(..., description="Write-through cache key")
   ) -> Response:
       """Write-through pattern with SmartCache"""
       data = request.json()

       # 1. Write to database (simulated)
       print(f"Saving to database: {key} = {data}")

       # 2. Immediately write to cache
       cache.set(f"writethrough:{key}", data, ttl=600)

       return JSONResponse({"message": "Data saved", "strategy": "write_through"})

   # Cache Warming
   @app.post("/warm-cache")
   def warm_cache(request: Request) -> Response:
       """Proactively populate cache with frequently accessed data"""
       popular_keys = ["user:1", "user:2", "user:3", "config:app"]

       warmed_count = 0
       for key in popular_keys:
           cached_value, found = cache.get(key)
           if not found:
               data = fetch_data_for_key(key)
               cache.set(key, data, ttl=1800)  # 30 minutes
               warmed_count += 1

       return JSONResponse({
           "message": f"Warmed {warmed_count} cache entries",
           "strategy": "cache_warming",
           "warmed_keys": popular_keys
       })

   if __name__ == "__main__":
       print("🚀 Starting cache strategies demo...")
       print("Try:")
       print("  GET  http://localhost:8000/cache-aside/example")
       print("  POST http://localhost:8000/write-through/example")
       print("  POST http://localhost:8000/warm-cache")
       app.listen(port=8000)

Performance Optimization
------------------------

Cache Analytics
~~~~~~~~~~~~~~~

Monitor cache performance and optimize hit ratios:

.. code-block:: python

   from catzilla import Catzilla, Request, Response, JSONResponse, SmartCache, SmartCacheConfig

   app = Catzilla()

   # Initialize cache with stats enabled
   cache_config = SmartCacheConfig(
       memory_capacity=1000,
       memory_ttl=300,
       enable_stats=True,
       disk_enabled=True,
       disk_path="/tmp/catzilla_analytics"
   )
   cache = SmartCache(cache_config)

   @app.get("/cache/analytics")
   def get_cache_analytics(request: Request) -> Response:
       """Get detailed cache performance analytics"""

       # Get comprehensive cache statistics
       stats = cache.get_stats()
       health = cache.health_check()

       return JSONResponse({
           "performance": {
               "hit_ratio": f"{stats.hit_ratio:.2%}",
               "total_hits": stats.hits,
               "total_misses": stats.misses,
               "operations_per_second": getattr(stats, 'ops_per_second', 0)
           },
           "memory_usage": {
               "current_usage": f"{stats.memory_usage:.2f}MB",
               "capacity": f"{stats.capacity} items",
               "size": stats.size,
               "compression_ratio": getattr(stats, 'compression_ratio', 1.0)
           },
           "tier_performance": {
               "memory": stats.tier_stats.get("memory", {}),
               "redis": stats.tier_stats.get("redis", {}),
               "disk": stats.tier_stats.get("disk", {})
           },
           "health": health,
           "jemalloc_enabled": cache.config.jemalloc_enabled
       })

   if __name__ == "__main__":
       print("🚀 Starting cache analytics demo...")
       print("Try: http://localhost:8000/cache/analytics")
       app.listen(port=8000)

Cache Warming
~~~~~~~~~~~~~

Proactively populate cache with frequently accessed data:

.. code-block:: python

   from catzilla import Catzilla, Request, Response, JSONResponse, SmartCache, SmartCacheConfig
   import time

   app = Catzilla()

   # Initialize cache
   cache_config = SmartCacheConfig(
       memory_capacity=1000,
       memory_ttl=300,
       disk_enabled=True,
       disk_path="/tmp/catzilla_warming"
   )
   cache = SmartCache(cache_config)

   def get_app_settings():
       """Simulate getting app settings"""
       time.sleep(0.05)
       return {"theme": "dark", "language": "en", "features": ["cache", "analytics"]}

   def get_feature_flags():
       """Simulate getting feature flags"""
       time.sleep(0.03)
       return {"new_ui": True, "beta_features": False, "maintenance_mode": False}

   def get_top_users(limit: int):
       """Simulate getting top users"""
       time.sleep(0.1)
       return [{"id": i, "name": f"User {i}", "score": 100 - i} for i in range(1, limit + 1)]

   def get_daily_statistics():
       """Simulate getting daily stats"""
       time.sleep(0.2)
       return {"visitors": 1500, "page_views": 5200, "signups": 23}

   def get_user_from_database(user_id: int):
       """Simulate database user lookup"""
       time.sleep(0.05)
       return {"id": user_id, "name": f"User {user_id}", "email": f"user{user_id}@example.com"}

   @app.post("/cache/warm-startup")
   def warm_cache_on_startup(request: Request) -> Response:
       """Warm cache with popular data during application startup"""

       # Popular data that should always be cached
       popular_data = {
           "config:app_settings": get_app_settings(),
           "config:feature_flags": get_feature_flags(),
           "users:top_100": get_top_users(100),
           "analytics:daily_stats": get_daily_statistics()
       }

       warmed_count = 0
       for cache_key, data in popular_data.items():
           if data:  # Only cache if data is valid
               cache.set(cache_key, data, ttl=1800)  # 30 minutes
               warmed_count += 1

       return JSONResponse({
           "message": f"Cache warmed with {warmed_count} entries",
           "warmed_keys": list(popular_data.keys()),
           "ttl_minutes": 30
       })

   @app.post("/cache/warm-users")
   def warm_user_data(request: Request) -> Response:
       """Warm cache with specific user data"""
       data = request.json()
       user_ids = data.get("user_ids", [1, 5, 10, 25, 50])

       warmed_users = []
       failed_users = []

       for user_id in user_ids:
           try:
               user_data = get_user_from_database(user_id)
               cache.set(f"user:{user_id}", user_data, ttl=600)
               warmed_users.append(user_id)
           except Exception as e:
               failed_users.append({"user_id": user_id, "error": str(e)})

       return JSONResponse({
           "message": f"Warmed {len(warmed_users)} user records",
           "warmed_users": warmed_users,
           "failed_users": failed_users,
           "ttl_minutes": 10
       })

   if __name__ == "__main__":
       print("🚀 Starting cache warming demo...")
       print("Try:")
       print("  POST http://localhost:8000/cache/warm-startup")
       print("  POST http://localhost:8000/cache/warm-users")
       app.listen(port=8000)

Cache Key Design
~~~~~~~~~~~~~~~~

Design effective cache keys for optimal performance:

.. code-block:: python

   from catzilla import Catzilla, Request, Response, JSONResponse, SmartCache, SmartCacheConfig
   from datetime import datetime

   app = Catzilla()

   # Initialize cache
   cache_config = SmartCacheConfig(memory_capacity=1000, memory_ttl=300)
   cache = SmartCache(cache_config)

   # Cache key best practices
   class CacheKeyBuilder:
       @staticmethod
       def user_key(user_id: int) -> str:
           return f"user:{user_id}"

       @staticmethod
       def user_posts_key(user_id: int, page: int = 1) -> str:
           return f"user:{user_id}:posts:page:{page}"

       @staticmethod
       def search_key(query: str, filters: dict = None) -> str:
           """Create cache key for search results"""
           base_key = f"search:{query.lower().replace(' ', '_')}"

           if filters:
               # Sort filters for consistent key generation
               filter_str = ":".join(f"{k}_{v}" for k, v in sorted(filters.items()))
               return f"{base_key}:{filter_str}"

           return base_key

       @staticmethod
       def config_key(environment: str, feature: str) -> str:
           return f"config:{environment}:{feature}"

       @staticmethod
       def daily_key(date: datetime) -> str:
           return f"daily_stats:{date.strftime('%Y-%m-%d')}"

   @app.get("/cache-key-examples")
   def create_cache_keys(request: Request) -> Response:
       """Examples of well-designed cache keys"""

       user_id = 123
       query = "python programming"
       environment = "production"
       feature = "new_ui"
       date = datetime.now()

       cache_keys = {
           "user": CacheKeyBuilder.user_key(user_id),
           "user_posts": CacheKeyBuilder.user_posts_key(user_id, page=2),
           "search": CacheKeyBuilder.search_key(query),
           "search_filtered": CacheKeyBuilder.search_key(query, {"category": "tutorials", "level": "beginner"}),
           "config": CacheKeyBuilder.config_key(environment, feature),
           "daily": CacheKeyBuilder.daily_key(date)
       }

       # Store some sample data using these keys
       for key_name, cache_key in cache_keys.items():
           sample_data = {"key_type": key_name, "cached_at": datetime.now().isoformat()}
           cache.set(cache_key, sample_data, ttl=300)

       return JSONResponse({
           "cache_key_examples": cache_keys,
           "best_practices": [
               "Use consistent naming patterns (entity:id)",
               "Include relevant parameters in key",
               "Sort filters for consistent keys",
               "Use descriptive prefixes",
               "Avoid special characters",
               "Keep keys readable and debuggable"
           ]
       })

   if __name__ == "__main__":
       print("🚀 Starting cache key design demo...")
       print("Try: http://localhost:8000/cache-key-examples")
       app.listen(port=8000)

Performance Benchmarking
~~~~~~~~~~~~~~~~~~~~~~~~

Benchmark cache performance to optimize your application:

.. code-block:: python

   from catzilla import Catzilla, Request, Response, JSONResponse, SmartCache, SmartCacheConfig
   import time
   import statistics

   app = Catzilla()

   # Initialize cache
   cache_config = SmartCacheConfig(
       memory_capacity=10000,
       memory_ttl=300,
       compression_enabled=True,
       jemalloc_enabled=True
   )
   cache = SmartCache(cache_config)

   def benchmark_cache_performance(cache, num_operations=1000):
       """Benchmark SmartCache performance"""

       # Test data
       test_data = {"benchmark": "data", "value": list(range(100))}

       # Benchmark SET operations
       set_times = []
       for i in range(num_operations):
           start = time.time()
           cache.set(f"benchmark_key_{i}", test_data, ttl=60)
           set_times.append((time.time() - start) * 1000)  # Convert to ms

       # Benchmark GET operations (should be cache hits)
       get_times = []
       for i in range(num_operations):
           start = time.time()
           result, found = cache.get(f"benchmark_key_{i}")
           get_times.append((time.time() - start) * 1000)  # Convert to ms

       # Calculate statistics
       return {
           "set_operations": {
               "count": num_operations,
               "avg_time_ms": statistics.mean(set_times),
               "min_time_ms": min(set_times),
               "max_time_ms": max(set_times),
               "ops_per_second": 1000 / statistics.mean(set_times)
           },
           "get_operations": {
               "count": num_operations,
               "avg_time_ms": statistics.mean(get_times),
               "min_time_ms": min(get_times),
               "max_time_ms": max(get_times),
               "ops_per_second": 1000 / statistics.mean(get_times)
           }
       }

   @app.get("/cache/benchmark")
   def run_cache_benchmark(request: Request) -> Response:
       """Run cache performance benchmark"""

       results = benchmark_cache_performance(cache, num_operations=1000)

       return JSONResponse({
           "benchmark_results": results,
           "cache_config": {
               "memory_capacity": cache.config.memory_capacity,
               "compression_enabled": cache.config.compression_enabled,
               "jemalloc_enabled": cache.config.jemalloc_enabled
           },
           "recommendation": "SmartCache with C-acceleration provides sub-millisecond performance"
       })

   if __name__ == "__main__":
       print("🚀 Starting cache benchmark demo...")
       print("Try: http://localhost:8000/cache/benchmark")
       app.listen(port=8000)

Best Practices
--------------

Cache Configuration Tips
~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from catzilla import SmartCacheConfig

   # Production-ready cache configuration
   production_cache_config = SmartCacheConfig(
       # Memory tier - for hot data
       memory_capacity=10000,        # Adjust based on available RAM
       memory_ttl=300,              # 5 minutes for hot data

       # Redis tier - for distributed caching
       redis_enabled=True,
       redis_url="redis://localhost:6379/0",
       redis_ttl=1800,              # 30 minutes

       # Disk tier - for cold data persistence
       disk_enabled=True,
       disk_path="/var/cache/catzilla",
       disk_ttl=86400,              # 24 hours

       # Performance optimizations
       compression_enabled=True,     # Reduce memory usage
       jemalloc_enabled=True,       # Optimize memory allocation
       enable_stats=True,           # Monitor performance
       auto_expire_interval=60      # Clean expired items every minute
   )

Common Patterns
~~~~~~~~~~~~~~~

.. code-block:: python

   from catzilla import Catzilla, Request, Response, JSONResponse, SmartCache, SmartCacheConfig, cached, Path

   app = Catzilla()

   # Initialize cache
   cache_config = SmartCacheConfig(memory_capacity=1000, memory_ttl=300)
   cache = SmartCache(cache_config)

   # Pattern 1: Function-level caching for expensive computations
   @cached(ttl=600, key_prefix="fibonacci")
   def fibonacci(n: int) -> int:
       if n <= 1:
           return n
       return fibonacci(n-1) + fibonacci(n-2)

   # Pattern 2: Manual caching for external API calls
   def get_weather(city: str):
       cache_key = f"weather:{city}"

       # Try cache first
       weather, found = cache.get(cache_key)
       if found:
           return weather

       # Fetch from API (simulated)
       weather = {"city": city, "temp": 72, "condition": "sunny"}

       # Cache for 30 minutes
       cache.set(cache_key, weather, ttl=1800)

       return weather

   # Pattern 3: Cache invalidation
   def update_user(user_id: int, data: dict):
       # Update database (simulated)
       print(f"Updating user {user_id} with {data}")

       # Invalidate related cache entries
       cache.delete(f"user:{user_id}")
       cache.delete(f"user:{user_id}:posts")
       cache.delete(f"user:{user_id}:profile")

   @app.get("/patterns/fibonacci/{n}")
   def test_fibonacci(
       request: Request,
       n: int = Path(..., ge=1, le=50, description="Fibonacci sequence position")
   ) -> Response:
       """Test cached fibonacci calculation"""
       result = fibonacci(n)
       return JSONResponse({"n": n, "fibonacci": result})

   @app.get("/patterns/weather/{city}")
   def test_weather(
       request: Request,
       city: str = Path(..., min_length=2, max_length=50, description="City name for weather lookup")
   ) -> Response:
       """Test weather API with caching"""
       weather = get_weather(city)
       return JSONResponse(weather)

   @app.post("/patterns/update-user/{user_id}")
   def test_cache_invalidation(
       request: Request,
       user_id: int = Path(..., ge=1, description="User ID to update")
   ) -> Response:
       """Test cache invalidation pattern"""
       data = request.json()
       update_user(user_id, data)
       return JSONResponse({"message": f"User {user_id} updated and cache invalidated"})

   if __name__ == "__main__":
       print("🚀 Starting cache patterns demo...")
       print("Try:")
       print("  GET  http://localhost:8000/patterns/fibonacci/30")
       print("  GET  http://localhost:8000/patterns/weather/London")
       print("  POST http://localhost:8000/patterns/update-user/123")
       app.listen(port=8000)

Troubleshooting
~~~~~~~~~~~~~~~

Common issues and solutions:

**Low Hit Ratio:**
- Check TTL values (too short?)
- Analyze key patterns for consistency
- Monitor memory capacity limits

**High Memory Usage:**
- Enable compression
- Reduce memory_capacity
- Implement better key expiration

**Slow Performance:**
- Enable jemalloc
- Check disk I/O for disk tier
- Monitor Redis connection pool

.. code-block:: python

   from catzilla import Catzilla, Request, Response, JSONResponse, SmartCache, SmartCacheConfig

   app = Catzilla()

   # Initialize cache with debugging enabled
   cache_config = SmartCacheConfig(
       memory_capacity=1000,
       memory_ttl=300,
       enable_stats=True,
       compression_enabled=True,
       jemalloc_enabled=True
   )
   cache = SmartCache(cache_config)

   def debug_cache_health():
       """Debug cache performance"""
       stats = cache.get_stats()
       health = cache.health_check()

       print(f"Hit Ratio: {stats.hit_ratio:.2%}")
       print(f"Memory Usage: {stats.memory_usage:.2f}MB")
       print(f"Operations/sec: {getattr(stats, 'ops_per_second', 'N/A')}")
       print(f"Health Status: {health}")

       recommendations = []
       if stats.hit_ratio < 0.8:
           recommendations.append("Consider increasing TTL values")

       if stats.memory_usage > 100:
           recommendations.append("Consider enabling compression or reducing capacity")

       return {
           "stats": {
               "hit_ratio": stats.hit_ratio,
               "memory_usage": stats.memory_usage,
               "cache_size": stats.size,
               "health": health
           },
           "recommendations": recommendations
       }

   @app.get("/cache/debug")
   def cache_debug_endpoint(request: Request) -> Response:
       """Debug cache health endpoint"""
       debug_info = debug_cache_health()

       return JSONResponse({
           "cache_debug": debug_info,
           "troubleshooting_tips": [
               "Low hit ratio: Increase TTL or warm more data",
               "High memory usage: Enable compression",
               "Slow performance: Enable jemalloc optimization",
               "Connection issues: Check Redis connectivity"
           ]
       })

   if __name__ == "__main__":
       print("🚀 Starting cache debugging demo...")
       print("Try: http://localhost:8000/cache/debug")
       app.listen(port=8000)

Related Documentation
---------------------

- `Cache Examples </examples/cache/>`_ - Complete cache examples and configurations
- :doc:`../core-concepts/async-sync-hybrid` - Async/sync performance patterns
- :doc:`../guides/recipes` - Real-world recipes and patterns
- :doc:`../getting-started/quickstart` - Getting started with Catzilla
