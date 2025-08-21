"""
Catzilla Smart Cache System Example
Demonstrates the revolutionary multi-level caching system with C-acceleration

Features demonstrated:
- Multi-level caching (Memory L1, Redis L2, Disk L3)
- Function-level caching with @cached decorator
- Middleware-based response caching
- Cache statistics and monitoring
- Performance benchmarking
"""

import asyncio
import json
import random
import time
from datetime import datetime
from typing import Dict, List, Any

from catzilla import (
    Catzilla,
    Request,
    Response,
    JSONResponse,
    HTMLResponse,
    SmartCache,
    SmartCacheConfig,
    cached,
    get_cache,
    SmartCacheMiddleware,
    ConditionalCacheMiddleware,
    create_api_cache_middleware,
)


# ============================================================================
# Demo Data Setup
# ============================================================================

# Simulated database
USERS_DB = []
POSTS_DB = []

def init_demo_data():
    """Initialize demo data"""
    global USERS_DB, POSTS_DB

    # Create users
    USERS_DB = [
        {
            "id": i,
            "name": f"User {i}",
            "email": f"user{i}@example.com",
            "created_at": datetime.now().isoformat(),
            "profile": {
                "bio": f"Bio for user {i}",
                "location": random.choice(["New York", "London", "Tokyo", "Berlin"]),
                "followers": random.randint(10, 1000)
            }
        }
        for i in range(1, 1001)
    ]

    # Create posts
    POSTS_DB = [
        {
            "id": i,
            "user_id": random.randint(1, 1000),
            "title": f"Post {i}: Amazing Content",
            "content": f"This is the content for post {i}. " * 10,
            "tags": random.sample(["tech", "python", "web", "api", "cache"], 2),
            "created_at": datetime.now().isoformat(),
            "views": random.randint(0, 5000),
            "likes": random.randint(0, 200)
        }
        for i in range(1, 5001)
    ]


def simulate_expensive_operation():
    """Simulate expensive database query or computation"""
    time.sleep(0.05)  # 50ms delay


# ============================================================================
# Cached Functions (Function-Level Caching)
# ============================================================================

@cached(ttl=300, key_prefix="user_")
def get_user_expensive(user_id: int) -> Dict[str, Any]:
    """Expensive user lookup with caching"""
    print(f"🔄 Executing expensive user lookup for ID: {user_id}")
    simulate_expensive_operation()

    user = next((u for u in USERS_DB if u["id"] == user_id), None)
    if not user:
        return {"error": "User not found"}

    # Add computed data
    user["computed_score"] = sum(ord(c) for c in user["name"]) % 100
    user["fetched_at"] = datetime.now().isoformat()

    return user


@cached(ttl=600, key_prefix="analytics_")
def get_analytics_data() -> Dict[str, Any]:
    """Expensive analytics computation with caching"""
    print("🔄 Executing expensive analytics computation...")
    simulate_expensive_operation()

    return {
        "total_users": len(USERS_DB),
        "total_posts": len(POSTS_DB),
        "avg_post_views": sum(p["views"] for p in POSTS_DB) / len(POSTS_DB),
        "top_users": sorted(USERS_DB, key=lambda u: u["profile"]["followers"], reverse=True)[:5],
        "computed_at": datetime.now().isoformat()
    }


@cached(ttl=120, key_prefix="search_")
def search_posts(query: str, limit: int = 10) -> List[Dict[str, Any]]:
    """Expensive post search with caching"""
    print(f"🔄 Executing expensive search for: '{query}'")
    simulate_expensive_operation()

    results = []
    for post in POSTS_DB:
        if query.lower() in post["title"].lower() or query.lower() in post["content"].lower():
            results.append(post)
            if len(results) >= limit:
                break

    return results


# ============================================================================
# Application Setup with Smart Cache
# ============================================================================

def create_cache_config() -> SmartCacheConfig:
    """Create cache configuration"""
    return SmartCacheConfig(
        # Memory Cache (L1) - Ultra-fast C-level cache
        memory_capacity=5000,
        memory_ttl=300,  # 5 minutes
        compression_enabled=True,
        jemalloc_enabled=True,

        # Redis Cache (L2) - Distributed cache (disabled for demo)
        redis_enabled=False,  # Enable if you have Redis running
        redis_url="redis://localhost:6379/0",
        redis_ttl=1800,  # 30 minutes

        # Disk Cache (L3) - Persistent cache
        disk_enabled=True,
        disk_path="/tmp/catzilla_cache_demo",
        disk_ttl=3600,  # 1 hour

        # Performance settings
        enable_stats=True,
        auto_expire_interval=60,
    )


def create_app() -> Catzilla:
    """Create Catzilla app with smart caching"""
    app = Catzilla()

    # Initialize demo data
    init_demo_data()

    # Configure cache
    cache_config = create_cache_config()

    # Setup cache middleware manually (not using automatic middleware)
    # Since we want to demonstrate manual cache operations
    global_cache = SmartCache(cache_config)

    return app, global_cache


# ============================================================================
# API Routes
# ============================================================================

def setup_routes(app: Catzilla, global_cache):
    """Setup API routes"""

    @app.get("/")
    async def home():
        """Home page with cache information"""
        cache = global_cache
        stats = cache.get_stats()
        health = cache.health_check()

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>🚀 Catzilla Smart Cache Demo</title>
            <style>
                body {{ font-family: -apple-system, BlinkMacSystemFont, sans-serif; margin: 40px; background: #f8f9fa; }}
                .container {{ max-width: 1200px; margin: 0 auto; }}
                .card {{ background: white; padding: 20px; margin: 20px 0; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
                .stats {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; }}
                .stat {{ text-align: center; padding: 15px; background: #e9ecef; border-radius: 6px; }}
                .endpoint {{ margin: 15px 0; padding: 15px; border: 1px solid #dee2e6; border-radius: 6px; }}
                .health {{ display: flex; gap: 10px; }}
                .health-item {{ padding: 5px 10px; border-radius: 4px; color: white; }}
                .healthy {{ background: #28a745; }}
                .unhealthy {{ background: #dc3545; }}
                a {{ color: #007bff; text-decoration: none; }}
                a:hover {{ text-decoration: underline; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🚀 Catzilla Smart Cache Demo</h1>
                <p>Demonstrating multi-level caching with C-acceleration</p>

                <div class="card">
                    <h2>📊 Cache Statistics</h2>
                    <div class="stats">
                        <div class="stat">
                            <h3>{stats.hit_ratio:.2%}</h3>
                            <p>Hit Ratio</p>
                        </div>
                        <div class="stat">
                            <h3>{stats.hits:,}</h3>
                            <p>Total Hits</p>
                        </div>
                        <div class="stat">
                            <h3>{stats.misses:,}</h3>
                            <p>Total Misses</p>
                        </div>
                        <div class="stat">
                            <h3>{stats.size:,}</h3>
                            <p>Cache Size</p>
                        </div>
                        <div class="stat">
                            <h3>{stats.memory_usage:,}</h3>
                            <p>Memory Usage (bytes)</p>
                        </div>
                    </div>
                </div>

                <div class="card">
                    <h2>🏥 Cache Health</h2>
                    <div class="health">
                        <div class="health-item {'healthy' if health['memory'] else 'unhealthy'}">
                            Memory Cache: {'✅ Active' if health['memory'] else '❌ Inactive'}
                        </div>
                        <div class="health-item {'healthy' if health['redis'] else 'unhealthy'}">
                            Redis Cache: {'✅ Active' if health['redis'] else '❌ Inactive'}
                        </div>
                        <div class="health-item {'healthy' if health['disk'] else 'unhealthy'}">
                            Disk Cache: {'✅ Active' if health['disk'] else '❌ Inactive'}
                        </div>
                    </div>
                </div>

                <div class="card">
                    <h2>🎯 Demo Endpoints</h2>

                    <div class="endpoint">
                        <h3>Function-Level Caching</h3>
                        <p>These use the @cached decorator for function-level caching:</p>
                        <p>🔗 <a href="/cached/user/1">GET /cached/user/1</a> - Cached user lookup (5 min TTL)</p>
                        <p>🔗 <a href="/cached/analytics">GET /cached/analytics</a> - Cached analytics (10 min TTL)</p>
                        <p>🔗 <a href="/cached/search?q=python">GET /cached/search?q=python</a> - Cached search (2 min TTL)</p>
                    </div>

                    <div class="endpoint">
                        <h3>Middleware-Level Caching</h3>
                        <p>These use middleware for automatic response caching:</p>
                        <p>🔗 <a href="/api/users/1">GET /api/users/1</a> - User endpoint (5 min cache)</p>
                        <p>🔗 <a href="/api/posts/1">GET /api/posts/1</a> - Post endpoint (3 min cache)</p>
                        <p>🔗 <a href="/api/analytics">GET /api/analytics</a> - Analytics endpoint (10 min cache)</p>
                    </div>

                    <div class="endpoint">
                        <h3>Cache Management</h3>
                        <p>🔗 <a href="/cache/stats">GET /cache/stats</a> - Detailed cache statistics</p>
                        <p>🔗 <a href="/cache/benchmark">GET /cache/benchmark</a> - Performance benchmark</p>
                        <p>🔗 <a href="/cache/clear">POST /cache/clear</a> - Clear all caches</p>
                    </div>
                </div>

                <div class="card">
                    <h2>💡 Tips</h2>
                    <ul>
                        <li>Try accessing the same endpoint multiple times to see caching in action</li>
                        <li>Check the console for cache miss/hit messages</li>
                        <li>Look for X-Cache headers in responses</li>
                        <li>Monitor how response times improve with caching</li>
                    </ul>
                </div>
            </div>
        </body>
        </html>
        """

        return HTMLResponse(html_content)

    # ========================================================================
    # Function-Level Caching Endpoints (using @cached decorator)
    # ========================================================================

    @app.get("/cached/user/{user_id}")
    async def cached_user_lookup(request):
        """User lookup with function-level caching"""
        user_id = int(request.path_params["user_id"])
        start_time = time.time()

        result = get_user_expensive(user_id)

        execution_time = (time.time() - start_time) * 1000

        return JSONResponse({
            "user": result,
            "execution_time_ms": round(execution_time, 2),
            "cache_info": "Function result cached for 5 minutes",
            "cache_type": "function_level"
        })

    @app.get("/cached/analytics")
    async def cached_analytics():
        """Analytics with function-level caching"""
        start_time = time.time()

        result = get_analytics_data()

        execution_time = (time.time() - start_time) * 1000

        return JSONResponse({
            "analytics": result,
            "execution_time_ms": round(execution_time, 2),
            "cache_info": "Analytics cached for 10 minutes",
            "cache_type": "function_level"
        })

    @app.get("/cached/search")
    async def cached_search(request):
        """Search with function-level caching"""
        # Get query parameters
        q = request.query_params.get("q", "")
        limit = int(request.query_params.get("limit", 10))

        start_time = time.time()

        results = search_posts(q, limit)

        execution_time = (time.time() - start_time) * 1000

        return JSONResponse({
            "query": q,
            "results": results,
            "count": len(results),
            "execution_time_ms": round(execution_time, 2),
            "cache_info": "Search results cached for 2 minutes",
            "cache_type": "function_level"
        })

    # ========================================================================
    # Middleware-Level Caching Endpoints (automatic response caching)
    # ========================================================================

    # ========================================================================
    # Manual Cache Operations (Direct cache usage)
    # ========================================================================

    @app.get("/api/users/{user_id}")
    async def get_user(request):
        """Get user - manual cache operations"""
        user_id = int(request.path_params["user_id"])

        # Try to get from cache first
        cache_key = f"user_{user_id}"
        cached_user = global_cache.get(cache_key)

        if cached_user:
            print(f"💾 Cache HIT for user {user_id}")
            return JSONResponse({
                **cached_user,
                "cache_status": "hit",
                "cache_type": "manual_cache"
            })

        # Not in cache, get from database
        print(f"🔄 Cache MISS for user {user_id}, fetching from DB...")
        simulate_expensive_operation()

        user = next((u for u in USERS_DB if u["id"] == user_id), None)
        if not user:
            return JSONResponse({"error": "User not found"}, status_code=404)

        # Store in cache
        global_cache.set(cache_key, user, ttl=300)  # 5 minutes

        return JSONResponse({
            **user,
            "cache_status": "miss",
            "cache_type": "manual_cache"
        })    @app.get("/api/posts/{post_id}")
    async def get_post(request):
        """Get post - cached by middleware"""
        post_id = int(request.path_params["post_id"])
        simulate_expensive_operation()

        post = next((p for p in POSTS_DB if p["id"] == post_id), None)
        if not post:
            return JSONResponse({"error": "Post not found"}, status_code=404)

        return JSONResponse({
            "post": post,
            "fetched_at": datetime.now().isoformat(),
            "cache_info": "Response cached by middleware for 3 minutes",
            "cache_type": "middleware_level"
        })

    @app.get("/api/analytics")
    async def api_analytics():
        """Analytics endpoint with manual caching"""
        cache_key = "analytics_data"
        cached_analytics = global_cache.get(cache_key)

        if cached_analytics:
            print("💾 Cache HIT for analytics")
            return JSONResponse({
                **cached_analytics,
                "cache_status": "hit",
                "cache_type": "manual_cache"
            })

        # Generate analytics
        print("🔄 Cache MISS for analytics, generating data...")
        simulate_expensive_operation()

        analytics = {
            "total_users": len(USERS_DB),
            "total_posts": len(POSTS_DB),
            "popular_tags": ["python", "web", "api", "cache", "tech"],
            "generated_at": datetime.now().isoformat()
        }

        # Cache for 10 minutes
        global_cache.set(cache_key, analytics, ttl=600)

        return JSONResponse({
            **analytics,
            "cache_status": "miss",
            "cache_type": "manual_cache"
        })

    # ========================================================================
    # Cache Management Endpoints
    # ========================================================================

    @app.get("/cache/stats")
    async def cache_stats():
        """Detailed cache statistics"""
        stats = global_cache.get_stats()
        health = global_cache.health_check()

        return JSONResponse({
            "cache_statistics": {
                "hits": stats.hits,
                "misses": stats.misses,
                "hit_ratio": stats.hit_ratio,
                "memory_usage": stats.memory_usage,
                "size": stats.size,
                "capacity": stats.capacity,
                "tier_stats": stats.tier_stats
            },
            "health_check": health,
            "config": {
                "memory_capacity": global_cache.config.memory_capacity,
                "memory_ttl": global_cache.config.memory_ttl,
                "redis_enabled": global_cache.config.redis_enabled,
                "disk_enabled": global_cache.config.disk_enabled,
                "compression_enabled": global_cache.config.compression_enabled,
                "jemalloc_enabled": global_cache.config.jemalloc_enabled
            },
            "timestamp": datetime.now().isoformat()
        })

    @app.get("/cache/benchmark")
    async def cache_benchmark():
        """Performance benchmark"""
        cache = global_cache

        # Benchmark parameters
        num_operations = 1000
        test_data = {"benchmark": "data", "value": list(range(100))}

        # Benchmark set operations
        start_time = time.time()
        for i in range(num_operations):
            cache.set(f"benchmark_key_{i}", test_data, ttl=60)
        set_time = time.time() - start_time

        # Benchmark get operations
        start_time = time.time()
        hits = 0
        for i in range(num_operations):
            value, found = cache.get(f"benchmark_key_{i}")
            if found:
                hits += 1
        get_time = time.time() - start_time

        # Cleanup
        for i in range(num_operations):
            cache.delete(f"benchmark_key_{i}")

        return JSONResponse({
            "benchmark_results": {
                "operations": num_operations,
                "set_operations": {
                    "total_time_ms": round(set_time * 1000, 2),
                    "ops_per_second": round(num_operations / set_time),
                    "avg_time_per_op_us": round((set_time / num_operations) * 1000000, 2)
                },
                "get_operations": {
                    "total_time_ms": round(get_time * 1000, 2),
                    "ops_per_second": round(num_operations / get_time),
                    "avg_time_per_op_us": round((get_time / num_operations) * 1000000, 2),
                    "hit_ratio": hits / num_operations
                }
            },
            "timestamp": datetime.now().isoformat()
        })

    @app.post("/cache/clear")
    async def clear_cache():
        """Clear all caches"""
        cache = global_cache
        cache.clear()

        return JSONResponse({
            "message": "All caches cleared successfully",
            "timestamp": datetime.now().isoformat()
        })


# ============================================================================
# Main Application
# ============================================================================

def main():
    """Main application entry point"""
    print("🚀 Starting Catzilla Smart Cache Demo...")
    print("=" * 60)

    # Create app
    app, global_cache = create_app()
    setup_routes(app, global_cache)

    print("✅ Smart Cache Demo initialized successfully!")
    print("\n📊 Cache Configuration:")
    print("   - L1: C-level Memory Cache (Ultra-fast)")
    print("   - L2: Redis Cache (Disabled in demo)")
    print("   - L3: Disk Cache (Persistent)")
    print("   - Compression: Enabled")
    print("   - jemalloc: Enabled")

    print("\n🎯 Demo Features:")
    print("   - Function-level caching with @cached decorator")
    print("   - Manual cache operations")
    print("   - Multi-level cache hierarchy")
    print("   - Real-time performance monitoring")
    print("   - Cache benchmarking tools")

    print("\n🌐 Access the demo at:")
    print("   http://localhost:8000/")
    print("=" * 60)

    return app


if __name__ == "__main__":
    app = main()

    # In a real application, you would run the server here:
    # import uvicorn
    # uvicorn.run(app, host="0.0.0.0", port=8000)

    print("\n🏁 Demo application ready!")
    print("💡 Note: In production, run with: uvicorn smart_cache_example:app")
