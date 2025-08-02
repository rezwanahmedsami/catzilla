"""
Debug cache example
"""

from catzilla import Catzilla, JSONResponse, SmartCache, SmartCacheConfig, cached, get_cache

print("🔄 Creating cache config...")
cache_config = SmartCacheConfig(
    memory_capacity=100,
    memory_ttl=300,
    compression_enabled=True,
    disk_enabled=True,
    disk_path="/tmp/catzilla_debug_cache"
)

print("🔄 Creating app...")
app = Catzilla()

print("🔄 Getting cache instance...")
cache = get_cache(cache_config)

print("🔄 Testing cache operations...")
cache.set("test", "hello", ttl=60)
value, found = cache.get("test")
print(f"Cache test: found={found}, value={value}")

@app.get("/")
async def debug_home():
    """Debug home endpoint"""
    print("🔄 Home endpoint called!")
    return JSONResponse({
        "message": "Cache Debug Test",
        "cache_test": "working"
    })

@app.get("/test")
async def debug_test():
    """Debug test endpoint"""
    print("🔄 Test endpoint called!")
    stats = cache.get_stats()
    return JSONResponse({
        "cache_stats": {
            "hits": stats.hits,
            "misses": stats.misses,
            "size": stats.size
        }
    })

if __name__ == "__main__":
    print("🚀 Starting debug server...")
    app.listen(port=8001)
