"""
Catzilla Smart Cache Demo Application
Demonstrates the revolutionary Smart Caching System with real-world examples
"""

import asyncio
import json
import random
import time
from datetime import datetime
from typing import Dict, List, Any

from catzilla.app import Catzilla
from catzilla.smart_cache import SmartCache, SmartCacheConfig, cached
from catzilla.cache_middleware import (
    SmartCacheMiddleware, ConditionalCacheMiddleware,
    create_api_cache_middleware, create_static_cache_middleware
)
from catzilla.response import JSONResponse, PlainTextResponse, HTMLResponse


# ============================================================================
# Application Setup with Smart Caching
# ============================================================================

def create_demo_app() -> Catzilla:
    """Create demo application with Smart Caching enabled"""

    # Configure multi-level caching
    cache_config = SmartCacheConfig(
        # Memory Cache (L1) - Ultra-fast C-level cache
        memory_capacity=10000,
        memory_ttl=300,  # 5 minutes
        compression_enabled=True,
        jemalloc_enabled=True,

        # Redis Cache (L2) - Distributed cache
        redis_enabled=False,  # Enable if Redis available
        redis_url="redis://localhost:6379/0",
        redis_ttl=3600,  # 1 hour

        # Disk Cache (L3) - Persistent cache
        disk_enabled=True,
        disk_path="/tmp/catzilla_demo_cache",
        disk_ttl=86400,  # 24 hours

        # General settings
        enable_stats=True,
        auto_expire_interval=300,
    )

    # Create application
    app = Catzilla()

    # Add conditional cache middleware with path-specific rules
    cache_rules = {
        "/api/users/*": {
            "ttl": 300,  # 5 minutes for user data
            "methods": ["GET"],
            "status_codes": [200, 404]
        },
        "/api/posts/*": {
            "ttl": 600,  # 10 minutes for posts
            "methods": ["GET", "HEAD"],
            "vary_headers": ["accept-language"]
        },
        "/api/analytics/*": {
            "ttl": 900,  # 15 minutes for analytics
            "methods": ["GET"]
        },
        "/static/*": {
            "ttl": 86400,  # 24 hours for static content
            "methods": ["GET", "HEAD"],
            "status_codes": [200, 301, 302, 404]
        },
    }

    # Add cache middleware
    cache_middleware = ConditionalCacheMiddleware(
        config=cache_config,
        cache_rules=cache_rules,
        default_ttl=300
    )

    app.add_middleware(cache_middleware)

    return app, cache_middleware


# ============================================================================
# Demo Data and Helper Functions
# ============================================================================

# Simulated database
USERS_DB = []
POSTS_DB = []
ANALYTICS_DB = {}

def init_demo_data():
    """Initialize demo data"""
    global USERS_DB, POSTS_DB, ANALYTICS_DB

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
                "website": f"https://user{i}.example.com"
            }
        }
        for i in range(1, 1001)
    ]

    # Create posts
    POSTS_DB = [
        {
            "id": i,
            "user_id": random.randint(1, 1000),
            "title": f"Post {i}: Lorem Ipsum Title",
            "content": f"This is the content for post {i}. " * 20,
            "tags": random.sample(["tech", "python", "web", "api", "cache", "performance"], 3),
            "created_at": datetime.now().isoformat(),
            "views": random.randint(0, 10000),
            "likes": random.randint(0, 500)
        }
        for i in range(1, 10001)
    ]

    # Create analytics data
    ANALYTICS_DB = {
        "daily_active_users": random.randint(5000, 15000),
        "total_requests": random.randint(100000, 500000),
        "cache_hit_ratio": random.uniform(0.7, 0.95),
        "avg_response_time": random.uniform(50, 200),
        "top_endpoints": [
            {"path": "/api/posts", "requests": random.randint(10000, 50000)},
            {"path": "/api/users", "requests": random.randint(5000, 25000)},
            {"path": "/api/analytics", "requests": random.randint(1000, 5000)},
        ]
    }

def simulate_expensive_computation():
    """Simulate expensive computation that benefits from caching"""
    time.sleep(0.1)  # Simulate 100ms database query or computation


# ============================================================================
# API Endpoints with Smart Caching
# ============================================================================

def setup_routes(app: Catzilla, cache_middleware):
    """Setup demo routes"""

    @app.get("/")
    async def home():
        """Home page with cache statistics"""
        stats = cache_middleware.get_stats()

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Catzilla Smart Cache Demo</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .stats {{ background: #f5f5f5; padding: 15px; border-radius: 5px; margin: 10px 0; }}
                .endpoint {{ margin: 10px 0; padding: 10px; border: 1px solid #ddd; }}
            </style>
        </head>
        <body>
            <h1>🚀 Catzilla Smart Cache Demo</h1>

            <div class="stats">
                <h2>📊 Cache Statistics</h2>
                <p><strong>Cache Hit Ratio:</strong> {stats['overall_hit_ratio']:.2%}</p>
                <p><strong>Memory Usage:</strong> {stats['cache_stats']['memory_usage']:,} bytes</p>
                <p><strong>Cache Size:</strong> {stats['cache_stats']['size']:,} entries</p>
                <p><strong>Total Hits:</strong> {stats['cache_stats']['hits']:,}</p>
                <p><strong>Total Misses:</strong> {stats['cache_stats']['misses']:,}</p>
            </div>

            <h2>🎯 Demo Endpoints</h2>

            <div class="endpoint">
                <h3>GET /api/users/{{id}}</h3>
                <p>Cached for 5 minutes. Try: <a href="/api/users/1">/api/users/1</a></p>
            </div>

            <div class="endpoint">
                <h3>GET /api/posts/{{id}}</h3>
                <p>Cached for 10 minutes. Try: <a href="/api/posts/1">/api/posts/1</a></p>
            </div>

            <div class="endpoint">
                <h3>GET /api/analytics</h3>
                <p>Cached for 15 minutes. Try: <a href="/api/analytics">/api/analytics</a></p>
            </div>

            <div class="endpoint">
                <h3>GET /expensive-computation</h3>
                <p>Demonstrates function-level caching. Try: <a href="/expensive-computation">/expensive-computation</a></p>
            </div>

            <div class="endpoint">
                <h3>GET /cache/stats</h3>
                <p>Detailed cache statistics. Try: <a href="/cache/stats">/cache/stats</a></p>
            </div>

        </body>
        </html>
        """

        return HTMLResponse(html_content)

    @app.get("/api/users/{user_id}")
    async def get_user(user_id: int):
        """Get user by ID - cached for 5 minutes"""
        simulate_expensive_computation()  # Simulate database query

        user = next((u for u in USERS_DB if u["id"] == user_id), None)
        if not user:
            return JSONResponse({"error": "User not found"}, status_code=404)

        return JSONResponse({
            "user": user,
            "cached_at": datetime.now().isoformat(),
            "cache_info": "This response is cached for 5 minutes"
        })

    @app.get("/api/users")
    async def list_users(page: int = 1, limit: int = 20):
        """List users with pagination - cached based on query parameters"""
        simulate_expensive_computation()

        start = (page - 1) * limit
        end = start + limit
        users = USERS_DB[start:end]

        return JSONResponse({
            "users": users,
            "pagination": {
                "page": page,
                "limit": limit,
                "total": len(USERS_DB),
                "has_next": end < len(USERS_DB)
            },
            "cached_at": datetime.now().isoformat()
        })

    @app.get("/api/posts/{post_id}")
    async def get_post(post_id: int):
        """Get post by ID - cached for 10 minutes"""
        simulate_expensive_computation()

        post = next((p for p in POSTS_DB if p["id"] == post_id), None)
        if not post:
            return JSONResponse({"error": "Post not found"}, status_code=404)

        return JSONResponse({
            "post": post,
            "cached_at": datetime.now().isoformat(),
            "cache_info": "This response is cached for 10 minutes"
        })

    @app.get("/api/posts")
    async def list_posts(page: int = 1, limit: int = 10, tag: str = None):
        """List posts with filtering - cached based on parameters"""
        simulate_expensive_computation()

        posts = POSTS_DB
        if tag:
            posts = [p for p in posts if tag in p.get("tags", [])]

        start = (page - 1) * limit
        end = start + limit
        posts_page = posts[start:end]

        return JSONResponse({
            "posts": posts_page,
            "pagination": {
                "page": page,
                "limit": limit,
                "total": len(posts),
                "has_next": end < len(posts)
            },
            "filter": {"tag": tag} if tag else None,
            "cached_at": datetime.now().isoformat()
        })

    @app.get("/api/analytics")
    async def get_analytics():
        """Get analytics data - cached for 15 minutes"""
        simulate_expensive_computation()  # Simulate complex analytics computation

        return JSONResponse({
            "analytics": ANALYTICS_DB,
            "generated_at": datetime.now().isoformat(),
            "cache_info": "Analytics are cached for 15 minutes"
        })

    @cached(ttl=300, key_prefix="expensive_")
    def expensive_function(complexity: int = 5):
        """Function with expensive computation - cached using decorator"""
        print(f"🔄 Executing expensive computation (complexity: {complexity})")

        # Simulate expensive computation
        result = 0
        for i in range(complexity * 1000000):
            result += i * 0.001

        return {
            "result": result,
            "complexity": complexity,
            "computed_at": datetime.now().isoformat(),
            "message": "This was an expensive computation!"
        }

    @app.get("/expensive-computation")
    async def expensive_computation_endpoint(complexity: int = 5):
        """Endpoint demonstrating function-level caching"""
        start_time = time.time()

        result = expensive_function(complexity)

        end_time = time.time()
        execution_time = end_time - start_time

        return JSONResponse({
            "computation_result": result,
            "execution_time_ms": round(execution_time * 1000, 2),
            "cache_note": "Function result is cached for 5 minutes"
        })

    @app.get("/cache/stats")
    async def cache_statistics():
        """Detailed cache statistics"""
        stats = cache_middleware.get_stats()

        return JSONResponse({
            "cache_statistics": stats,
            "system_info": {
                "timestamp": datetime.now().isoformat(),
                "cache_tiers": {
                    "L1": "C-level Memory Cache (Ultra-fast)",
                    "L2": "Redis Cache (Distributed)" if stats['cache_health']['redis'] else "Redis Cache (Disabled)",
                    "L3": "Disk Cache (Persistent)" if stats['cache_health']['disk'] else "Disk Cache (Disabled)"
                }
            }
        })

    @app.post("/cache/clear")
    async def clear_cache():
        """Clear all cache data"""
        cache_middleware.clear_cache()

        return JSONResponse({
            "message": "Cache cleared successfully",
            "timestamp": datetime.now().isoformat()
        })

    @app.get("/cache/health")
    async def cache_health():
        """Cache health check"""
        health = cache_middleware.cache.health_check()

        return JSONResponse({
            "health": health,
            "status": "healthy" if all(health.values()) else "degraded",
            "timestamp": datetime.now().isoformat()
        })

    # Benchmark endpoint
    @app.get("/benchmark")
    async def benchmark_cache():
        """Benchmark cache performance"""
        cache = cache_middleware.cache

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


# ============================================================================
# Application Factory and Runner
# ============================================================================

def create_app():
    """Application factory"""
    # Initialize demo data
    init_demo_data()

    # Create app with caching
    app, cache_middleware = create_demo_app()

    # Setup routes
    setup_routes(app, cache_middleware)

    return app


async def main():
    """Main application runner"""
    print("🚀 Starting Catzilla Smart Cache Demo Application...")
    print("="*60)

    app = create_app()

    print("✅ Application initialized with Smart Caching enabled!")
    print("\n📊 Cache Configuration:")
    print("   - L1: C-level Memory Cache (Ultra-fast)")
    print("   - L2: Redis Cache (Distributed) - Disabled in demo")
    print("   - L3: Disk Cache (Persistent) - Enabled")

    print("\n🎯 Demo Endpoints:")
    print("   - http://localhost:8000/ - Home page with cache stats")
    print("   - http://localhost:8000/api/users/1 - Cached user data")
    print("   - http://localhost:8000/api/posts/1 - Cached post data")
    print("   - http://localhost:8000/api/analytics - Cached analytics")
    print("   - http://localhost:8000/expensive-computation - Function caching demo")
    print("   - http://localhost:8000/cache/stats - Detailed cache statistics")
    print("   - http://localhost:8000/benchmark - Cache performance benchmark")

    print("\n🌟 Try making the same request multiple times to see caching in action!")
    print("="*60)

    # In a real application, you would run the server here
    # For demo purposes, we'll just return the app
    return app


if __name__ == "__main__":
    # Run the demo
    app = asyncio.run(main())
    print("\n🏁 Demo application ready!")
    print("💡 Tip: Check response headers for 'x-cache' to see cache hits/misses")
