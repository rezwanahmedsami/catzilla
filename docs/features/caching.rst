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

   from catzilla import Catzilla, JSONResponse, SmartCache, SmartCacheConfig, cached

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
   def get_cached_data(request):
       """Get data with SmartCache caching"""
       key = request.path_params["key"]

       # Try to get from cache first
       cached_value = cache.get(f"data:{key}")

       if cached_value is not None:
           return JSONResponse({
               "data": cached_value,
               "source": "cache",
               "cache_hit": True
           })


       # Generate expensive data (simulation)
       import time
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

Cache Decorator
~~~~~~~~~~~~~~~

Use the ``@cached`` decorator for automatic function result caching:

.. code-block:: python

   from catzilla import cached

   @cached(ttl=600, key_prefix="user_data")
   def get_user_data(user_id: int):
       """Expensive user data retrieval with caching"""
       # Simulate database query
       import time
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
   def get_user(request):
       """Get user with automatic caching"""
       user_id = int(request.path_params["user_id"])
       user_data = get_user_data(user_id)

       return JSONResponse({
           "user": user_data,
           "cached": True  # Automatically cached by decorator
       })

Multi-Tier SmartCache
---------------------

Configure Multi-Tier Cache
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Set up Memory (L1), Redis (L2), and Disk (L3) caching tiers:

.. code-block:: python

   from catzilla import SmartCache, SmartCacheConfig

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

   @app.get("/multilayer-data/{key}")
   def get_multilayer_data(request):
       """Data retrieval with multi-tier caching"""
       key = request.path_params["key"]

       cache_key = f"complex_data:{key}"

       # Cache will automatically check tiers in order: Memory → Redis → Disk
       cached_data = cache.get(cache_key)

       if cached_data:
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

   def generate_complex_computation(key: str):
       """Simulate expensive computation"""
       import time
       time.sleep(0.2)  # Simulate 200ms computation

       return {
           "key": key,
           "result": f"Complex result for {key}",
           "computed_at": time.time(),
           "computation_cost": "expensive"
       }

Cache Strategies
~~~~~~~~~~~~~~~~

Implement different caching patterns with SmartCache:

.. code-block:: python

   # Cache-Aside Pattern (Most Common)
   def cache_aside_example(request):
       """Cache-aside pattern with SmartCache"""
       key = request.path_params["key"]
       cache_key = f"aside:{key}"

       # 1. Try cache first
       cached = cache.get(cache_key)
       if cached:
           return JSONResponse({"data": cached, "strategy": "cache_aside", "hit": True})

       # 2. Cache miss - fetch from source
       data = expensive_database_query(key)

       # 3. Store in cache for next time
       cache.set(cache_key, data, ttl=300)

       return JSONResponse({"data": data, "strategy": "cache_aside", "hit": False})

   # Write-Through Pattern
   def write_through_example(request):
       """Write-through pattern with SmartCache"""
       key = request.path_params["key"]
       data = request.json()

       # 1. Write to database
       database.save(key, data)

       # 2. Immediately write to cache
       cache.set(f"writethrough:{key}", data, ttl=600)

       return JSONResponse({"message": "Data saved", "strategy": "write_through"})

   # Cache Warming
   def warm_cache():
       """Proactively populate cache with frequently accessed data"""
       popular_keys = ["user:1", "user:2", "user:3", "config:app"]

       for key in popular_keys:
           if not cache.get(key):
               data = fetch_data_for_key(key)
               cache.set(key, data, ttl=1800)  # 30 minutes

       return f"Warmed {len(popular_keys)} cache entries"

   async def _refresh_ahead(self, key: str, fetch_function, ttl: int):
       # Implementation for refresh-ahead logic
       pass

Performance Optimization
------------------------

Cache Analytics
~~~~~~~~~~~~~~~

Monitor cache performance and optimize hit ratios:

.. code-block:: python

   @app.get("/cache/analytics")
   def get_cache_analytics(request):
       """Get detailed cache performance analytics"""

       # Get comprehensive cache statistics
       stats = cache.get_stats()
       health = cache.health_check()

       return JSONResponse({
           "performance": {
               "hit_ratio": f"{stats.hit_ratio:.2%}",
               "total_hits": stats.hits,
               "total_misses": stats.misses,
               "operations_per_second": stats.ops_per_second
           },
           "memory_usage": {
               "current_usage": f"{stats.memory_usage:.2f}MB",
               "capacity": f"{stats.capacity} items",
               "size": stats.size,
               "compression_ratio": f"{stats.compression_ratio:.2f}x"
           },
           "tier_performance": {
               "memory": stats.tier_stats.get("memory", {}),
               "redis": stats.tier_stats.get("redis", {}),
               "disk": stats.tier_stats.get("disk", {})
           },
           "health": health,
           "jemalloc_enabled": cache.config.jemalloc_enabled
       })

Cache Warming
~~~~~~~~~~~~~

Proactively populate cache with frequently accessed data:

.. code-block:: python

   def warm_cache_on_startup():
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

       print(f"🔥 Cache warmed with {warmed_count} entries")
       return warmed_count

   def warm_user_data(user_ids: list):
       """Warm cache with specific user data"""
       for user_id in user_ids:
           try:
               user_data = get_user_from_database(user_id)
               cache.set(f"user:{user_id}", user_data, ttl=600)
           except Exception as e:
               print(f"Failed to warm user {user_id}: {e}")

   # Warm cache during application startup
   @app.on_startup
   def startup_cache_warming():
       warm_cache_on_startup()

       # Warm popular user data
       popular_user_ids = [1, 5, 10, 25, 50]  # Could come from analytics
       warm_user_data(popular_user_ids)
               "popular": True
           }

       async def _fetch_weather_data(self, city: str):
           """Simulate weather data fetching"""
           await asyncio.sleep(0.1)
           return {
               "city": city,
               "temperature": 72,
               "condition": "sunny"
           }

       async def start_warming_schedule(self):
           """Start scheduled cache warming"""
           import asyncio

Cache Key Design
~~~~~~~~~~~~~~~~

Design effective cache keys for optimal performance:

.. code-block:: python

   # Good cache key patterns
   def create_cache_keys():
       """Examples of well-designed cache keys"""

       # User data: user:{user_id}
       user_key = f"user:{user_id}"

       # User posts: user:{user_id}:posts
       user_posts_key = f"user:{user_id}:posts"

       # Search results: search:{query}:{page}:{limit}
       search_key = f"search:{query}:{page}:{limit}"

       # Configuration: config:{environment}:{feature}
       config_key = f"config:{environment}:{feature}"

       # Time-based: daily_stats:{date}
       daily_key = f"daily_stats:{date.strftime('%Y-%m-%d')}"

       return {
           "user": user_key,
           "posts": user_posts_key,
           "search": search_key,
           "config": config_key,
           "daily": daily_key
       }

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

Performance Benchmarking
~~~~~~~~~~~~~~~~~~~~~~~~

Benchmark cache performance to optimize your application:

.. code-block:: python

   import time
   import statistics

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
           result = cache.get(f"benchmark_key_{i}")
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
   def run_cache_benchmark(request):
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

Best Practices
--------------

Cache Configuration Tips
~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

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
       weather = cache.get(cache_key)
       if weather:
           return weather

       # Fetch from API
       weather = external_weather_api.get(city)

       # Cache for 30 minutes
       cache.set(cache_key, weather, ttl=1800)

       return weather

   # Pattern 3: Cache invalidation
   def update_user(user_id: int, data: dict):
       # Update database
       database.update_user(user_id, data)

       # Invalidate related cache entries
       cache.delete(f"user:{user_id}")
       cache.delete(f"user:{user_id}:posts")
       cache.delete(f"user:{user_id}:profile")

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

   # Debug cache performance
   def debug_cache_health():
       stats = cache.get_stats()
       health = cache.health_check()

       print(f"Hit Ratio: {stats.hit_ratio:.2%}")
       print(f"Memory Usage: {stats.memory_usage:.2f}MB")
       print(f"Operations/sec: {stats.ops_per_second}")
       print(f"Health Status: {health}")

       if stats.hit_ratio < 0.8:
           print("⚠️  Consider increasing TTL values")

       if stats.memory_usage > 100:
           print("⚠️  Consider enabling compression or reducing capacity")

Related Documentation
---------------------

- `Cache Examples </examples/cache/>`_ - Complete cache examples and configurations
- :doc:`../core-concepts/async-sync-hybrid` - Async/sync performance patterns
- :doc:`../guides/recipes` - Real-world recipes and patterns
- :doc:`../getting-started/quickstart` - Getting started with Catzilla
