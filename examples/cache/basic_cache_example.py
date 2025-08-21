"""
Basic Catzilla Smart Cache Example
Simple demonstration of the Smart Cache system
"""

from catzilla import Catzilla, JSONResponse, SmartCache, SmartCacheConfig, cached

# Create a simple cache configuration
cache_config = SmartCacheConfig(
    memory_capacity=1000,     # Store up to 1000 items in memory
    memory_ttl=300,          # 5 minutes default TTL
    compression_enabled=True, # Enable compression for large values
    disk_enabled=True,       # Enable disk cache for persistence
    disk_path="/tmp/catzilla_basic_cache"
)

app = Catzilla(
    production=False,
    show_banner=True,
    log_requests=True
)

# ============================================================================
# Function-Level Caching Examples
# ============================================================================

@cached(ttl=60, key_prefix="calc_")
def expensive_calculation(n: int) -> int:
    """Simulate expensive calculation"""
    print(f"🔄 Computing factorial of {n}...")

    # Simulate expensive operation
    import time
    time.sleep(0.1)

    result = 1
    for i in range(1, n + 1):
        result *= i
    return result


@cached(ttl=180, key_prefix="weather_")
def get_weather_data(city: str) -> dict:
    """Simulate weather API call"""
    print(f"🔄 Fetching weather for {city}...")

    # Simulate API call delay
    import time
    time.sleep(0.2)

    import random
    return {
        "city": city,
        "temperature": random.randint(-10, 35),
        "condition": random.choice(["sunny", "cloudy", "rainy", "snowy"]),
        "humidity": random.randint(30, 90),
        "fetched_at": time.time()
    }


# ============================================================================
# Direct Cache Usage Examples
# ============================================================================

# Get the global cache instance
from catzilla import get_cache
cache = get_cache(cache_config)


@app.get("/")
async def home(request):
    """Home page with basic cache info"""
    stats = cache.get_stats()

    return JSONResponse({
        "message": "Welcome to Catzilla Smart Cache Demo",
        "cache_stats": {
            "hits": stats.hits,
            "misses": stats.misses,
            "hit_ratio": stats.hit_ratio,
            "size": stats.size
        },
        "endpoints": {
            "factorial": "/factorial/{number} - Cached expensive calculation",
            "weather": "/weather/{city} - Cached weather data",
            "manual": "/manual/{key}/{value} - Manual cache operations",
            "stats": "/cache/stats - Detailed cache statistics"
        }
    })


@app.get("/factorial/{number}")
async def factorial_endpoint(request):
    """Calculate factorial with caching"""
    import time
    start_time = time.time()

    number = int(request.path_params["number"])
    result = expensive_calculation(number)

    execution_time = (time.time() - start_time) * 1000

    return JSONResponse({
        "number": number,
        "factorial": result,
        "execution_time_ms": round(execution_time, 2),
        "cache_info": "Result cached for 1 minute"
    })


@app.get("/weather/{city}")
async def weather_endpoint(request):
    """Get weather with caching"""
    import time
    start_time = time.time()

    city = request.path_params["city"]
    weather = get_weather_data(city)

    execution_time = (time.time() - start_time) * 1000

    return JSONResponse({
        "weather": weather,
        "execution_time_ms": round(execution_time, 2),
        "cache_info": "Weather data cached for 3 minutes"
    })


@app.get("/manual/{key}/{value}")
async def manual_cache_operations(request):
    """Demonstrate manual cache operations"""

    key = request.path_params["key"]
    value = request.path_params["value"]

    # Store in cache
    cache.set(key, value, ttl=120)  # Cache for 2 minutes

    # Retrieve from cache
    cached_value, found = cache.get(key)

    # Check existence
    exists = cache.exists(key)

    return JSONResponse({
        "operation": "manual_cache",
        "key": key,
        "stored_value": value,
        "retrieved_value": cached_value,
        "found": found,
        "exists": exists,
        "cache_info": "Manually stored with 2 minute TTL"
    })


@app.get("/cache/stats")
async def cache_statistics(request):
    """Get detailed cache statistics"""
    stats = cache.get_stats()
    health = cache.health_check()

    return JSONResponse({
        "statistics": {
            "hits": stats.hits,
            "misses": stats.misses,
            "hit_ratio": stats.hit_ratio,
            "memory_usage": stats.memory_usage,
            "size": stats.size,
            "capacity": stats.capacity,
            "tier_stats": stats.tier_stats
        },
        "health": health,
        "config": {
            "memory_capacity": cache.config.memory_capacity,
            "memory_ttl": cache.config.memory_ttl,
            "compression_enabled": cache.config.compression_enabled,
            "disk_enabled": cache.config.disk_enabled,
            "redis_enabled": cache.config.redis_enabled
        }
    })


@app.post("/cache/clear")
async def clear_cache(request):
    """Clear all cache data"""
    cache.clear()

    return JSONResponse({
        "message": "Cache cleared successfully"
    })


if __name__ == "__main__":
    print("🚀 Starting Basic Catzilla Cache Demo...")
    print("📁 Cache directory: /tmp/catzilla_basic_cache")
    print("🌐 Try these endpoints:")
    print("   http://localhost:8000/")
    print("   http://localhost:8000/factorial/10")
    print("   http://localhost:8000/weather/London")
    print("   http://localhost:8000/manual/mykey/myvalue")
    print("   http://localhost:8000/cache/stats")
    print("\n✨ Starting server on http://localhost:8000")
    app.listen(port=8000)
