"""
Catzilla Cache Configuration Examples
Demonstrates different cache configurations and use cases
"""

from catzilla import Catzilla, JSONResponse, SmartCache, SmartCacheConfig, cached, get_cache

app = Catzilla()

# ============================================================================
# Configuration Examples
# ============================================================================

def create_memory_only_config():
    """High-performance memory-only cache for hot data"""
    return SmartCacheConfig(
        memory_capacity=50000,        # Large memory cache
        memory_ttl=600,              # 10 minutes
        compression_enabled=True,     # Compress large objects
        jemalloc_enabled=True,       # Optimize memory allocation

        # Disable other tiers for maximum speed
        redis_enabled=False,
        disk_enabled=False,

        enable_stats=True
    )

def create_persistent_config():
    """Persistent cache that survives restarts"""
    return SmartCacheConfig(
        memory_capacity=5000,         # Moderate memory cache
        memory_ttl=300,              # 5 minutes in memory

        # Enable disk for persistence
        disk_enabled=True,
        disk_path="/tmp/catzilla_persistent",
        disk_ttl=86400,              # 24 hours on disk

        # Disable Redis for simplicity
        redis_enabled=False,

        compression_enabled=True,
        enable_stats=True
    )

def create_distributed_config():
    """Multi-tier cache for distributed systems"""
    return SmartCacheConfig(
        # Fast L1 cache
        memory_capacity=10000,
        memory_ttl=180,              # 3 minutes

        # Distributed L2 cache
        redis_enabled=True,          # Enable for production
        redis_url="redis://localhost:6379/0",
        redis_ttl=1800,             # 30 minutes
        redis_max_connections=20,

        # Persistent L3 cache
        disk_enabled=True,
        disk_path="/tmp/catzilla_distributed",
        disk_ttl=86400,             # 24 hours

        compression_enabled=True,
        jemalloc_enabled=True,
        enable_stats=True
    )


# ============================================================================
# Demonstration Routes
# ============================================================================

@app.get("/")
async def home():
    """Configuration examples overview"""
    return JSONResponse({
        "message": "Catzilla Cache Configuration Examples",
        "configurations": {
            "memory_only": {
                "description": "High-performance memory-only cache",
                "use_case": "Hot data, maximum speed",
                "endpoint": "/demo/memory-only"
            },
            "persistent": {
                "description": "Persistent cache with disk storage",
                "use_case": "Data that survives restarts",
                "endpoint": "/demo/persistent"
            },
            "distributed": {
                "description": "Multi-tier distributed cache",
                "use_case": "Scalable distributed systems",
                "endpoint": "/demo/distributed"
            }
        },
        "management": {
            "compare_configs": "/compare-configs",
            "benchmark_all": "/benchmark-all"
        }
    })


@app.get("/demo/memory-only")
async def demo_memory_only():
    """Demonstrate memory-only cache configuration"""
    config = create_memory_only_config()
    cache = SmartCache(config)

    # Store some test data
    cache.set("user:1001", {"name": "John", "email": "john@example.com"}, ttl=300)
    cache.set("session:abc123", {"user_id": 1001, "expires": "2024-12-31"}, ttl=600)

    # Retrieve data
    user, found_user = cache.get("user:1001")
    session, found_session = cache.get("session:abc123")

    stats = cache.get_stats()
    health = cache.health_check()

    return JSONResponse({
        "configuration": "memory_only",
        "description": "Ultra-fast memory-only cache with jemalloc optimization",
        "config": {
            "memory_capacity": config.memory_capacity,
            "memory_ttl": config.memory_ttl,
            "redis_enabled": config.redis_enabled,
            "disk_enabled": config.disk_enabled,
            "compression_enabled": config.compression_enabled,
            "jemalloc_enabled": config.jemalloc_enabled
        },
        "test_data": {
            "user_found": found_user,
            "user_data": user,
            "session_found": found_session,
            "session_data": session
        },
        "performance": {
            "memory_usage": stats.memory_usage,
            "cache_size": stats.size,
            "hit_ratio": stats.hit_ratio
        },
        "health": health,
        "use_cases": [
            "High-frequency API responses",
            "User session data",
            "Computed values with short TTL",
            "Real-time analytics cache"
        ]
    })


@app.get("/demo/persistent")
async def demo_persistent():
    """Demonstrate persistent cache configuration"""
    config = create_persistent_config()
    cache = SmartCache(config)

    # Store persistent data
    cache.set("config:app_settings", {
        "theme": "dark",
        "language": "en",
        "features": ["notifications", "analytics"]
    }, ttl=3600)

    cache.set("cache:user_preferences:1001", {
        "dashboard_layout": "grid",
        "email_notifications": True,
        "dark_mode": True
    }, ttl=7200)

    # Retrieve data
    app_settings, found_settings = cache.get("config:app_settings")
    preferences, found_prefs = cache.get("cache:user_preferences:1001")

    stats = cache.get_stats()
    health = cache.health_check()

    return JSONResponse({
        "configuration": "persistent",
        "description": "Persistent cache with disk storage for data durability",
        "config": {
            "memory_capacity": config.memory_capacity,
            "disk_enabled": config.disk_enabled,
            "disk_path": config.disk_path,
            "disk_ttl": config.disk_ttl,
            "compression_enabled": config.compression_enabled
        },
        "test_data": {
            "app_settings_found": found_settings,
            "app_settings": app_settings,
            "user_preferences_found": found_prefs,
            "user_preferences": preferences
        },
        "performance": {
            "memory_usage": stats.memory_usage,
            "cache_size": stats.size,
            "hit_ratio": stats.hit_ratio
        },
        "health": health,
        "use_cases": [
            "Application configuration",
            "User preferences",
            "Computed reports",
            "Feature flags",
            "Static content metadata"
        ]
    })


@app.get("/demo/distributed")
async def demo_distributed():
    """Demonstrate distributed cache configuration"""
    config = create_distributed_config()

    # Note: This will work even if Redis is not available
    # The cache will automatically fall back to memory + disk
    try:
        cache = SmartCache(config)
    except Exception as e:
        # Fallback to memory + disk only
        config.redis_enabled = False
        cache = SmartCache(config)

    # Store data across tiers
    cache.set("global:rate_limits", {
        "api_calls_per_minute": 1000,
        "burst_limit": 100,
        "blocked_ips": ["192.168.1.100", "10.0.0.50"]
    }, ttl=900)

    cache.set("shared:feature_flags", {
        "new_ui_enabled": True,
        "beta_features": False,
        "maintenance_mode": False
    }, ttl=1800)

    # Retrieve data
    rate_limits, found_limits = cache.get("global:rate_limits")
    feature_flags, found_flags = cache.get("shared:feature_flags")

    stats = cache.get_stats()
    health = cache.health_check()

    return JSONResponse({
        "configuration": "distributed",
        "description": "Multi-tier cache for distributed systems",
        "config": {
            "memory_capacity": config.memory_capacity,
            "redis_enabled": config.redis_enabled,
            "redis_url": config.redis_url if config.redis_enabled else "disabled",
            "disk_enabled": config.disk_enabled,
            "compression_enabled": config.compression_enabled,
            "jemalloc_enabled": config.jemalloc_enabled
        },
        "test_data": {
            "rate_limits_found": found_limits,
            "rate_limits": rate_limits,
            "feature_flags_found": found_flags,
            "feature_flags": feature_flags
        },
        "performance": {
            "memory_usage": stats.memory_usage,
            "cache_size": stats.size,
            "hit_ratio": stats.hit_ratio,
            "tier_stats": stats.tier_stats
        },
        "health": health,
        "cache_tiers": {
            "L1_memory": "✅ Active" if health["memory"] else "❌ Inactive",
            "L2_redis": "✅ Active" if health["redis"] else "❌ Inactive",
            "L3_disk": "✅ Active" if health["disk"] else "❌ Inactive"
        },
        "use_cases": [
            "Shared application state",
            "Rate limiting data",
            "Feature flags",
            "Global configuration",
            "Cross-service data sharing"
        ]
    })


@app.get("/compare-configs")
async def compare_configurations():
    """Compare different cache configurations"""

    configs = {
        "memory_only": create_memory_only_config(),
        "persistent": create_persistent_config(),
        "distributed": create_distributed_config()
    }

    comparison = {}
    for name, config in configs.items():
        comparison[name] = {
            "memory_capacity": config.memory_capacity,
            "memory_ttl": config.memory_ttl,
            "redis_enabled": config.redis_enabled,
            "disk_enabled": config.disk_enabled,
            "compression_enabled": config.compression_enabled,
            "jemalloc_enabled": config.jemalloc_enabled,
            "use_case": {
                "memory_only": "Maximum speed, volatile data",
                "persistent": "Data durability, moderate speed",
                "distributed": "Scalability, shared state"
            }[name]
        }

    return JSONResponse({
        "title": "Cache Configuration Comparison",
        "configurations": comparison,
        "recommendations": {
            "high_performance_apis": "memory_only",
            "user_data_storage": "persistent",
            "microservices": "distributed"
        },
        "performance_characteristics": {
            "memory_only": {
                "latency": "~1-2 microseconds",
                "throughput": "1M+ ops/sec",
                "durability": "Volatile (lost on restart)"
            },
            "persistent": {
                "latency": "~1-5 milliseconds (with disk)",
                "throughput": "100K+ ops/sec",
                "durability": "Persistent across restarts"
            },
            "distributed": {
                "latency": "~1 microsecond (L1) to 500 microseconds (L2)",
                "throughput": "500K+ ops/sec",
                "durability": "Multi-tier with redundancy"
            }
        }
    })


@app.get("/benchmark-all")
async def benchmark_all():
    """Benchmark all cache configurations"""
    import time

    configs = {
        "memory_only": create_memory_only_config(),
        "persistent": create_persistent_config(),
        "distributed": create_distributed_config()
    }

    # Disable Redis for distributed config if not available
    configs["distributed"].redis_enabled = False

    results = {}

    for name, config in configs.items():
        cache = SmartCache(config)

        # Benchmark set operations
        num_ops = 1000
        test_data = {"benchmark": True, "data": list(range(50))}

        start_time = time.time()
        for i in range(num_ops):
            cache.set(f"bench_{name}_{i}", test_data, ttl=60)
        set_time = time.time() - start_time

        # Benchmark get operations
        start_time = time.time()
        hits = 0
        for i in range(num_ops):
            value, found = cache.get(f"bench_{name}_{i}")
            if found:
                hits += 1
        get_time = time.time() - start_time

        # Get stats
        stats = cache.get_stats()

        results[name] = {
            "set_operations": {
                "total_time_ms": round(set_time * 1000, 2),
                "ops_per_second": round(num_ops / set_time),
                "avg_latency_us": round((set_time / num_ops) * 1000000, 2)
            },
            "get_operations": {
                "total_time_ms": round(get_time * 1000, 2),
                "ops_per_second": round(num_ops / get_time),
                "avg_latency_us": round((get_time / num_ops) * 1000000, 2),
                "hit_ratio": hits / num_ops
            },
            "cache_stats": {
                "memory_usage": stats.memory_usage,
                "size": stats.size,
                "hit_ratio": stats.hit_ratio
            }
        }

        # Cleanup
        cache.clear()

    return JSONResponse({
        "benchmark_results": results,
        "test_parameters": {
            "operations_per_test": num_ops,
            "data_size": "~200 bytes per item",
            "ttl": "60 seconds"
        },
        "winner": {
            "fastest_set": min(results.keys(), key=lambda k: results[k]["set_operations"]["avg_latency_us"]),
            "fastest_get": min(results.keys(), key=lambda k: results[k]["get_operations"]["avg_latency_us"]),
            "highest_throughput": max(results.keys(), key=lambda k: results[k]["get_operations"]["ops_per_second"])
        }
    })


if __name__ == "__main__":
    print("🚀 Starting Catzilla Cache Configuration Examples...")
    print("🎯 Demonstrating different cache configurations:")
    print("   - Memory-only: Ultra-fast volatile cache")
    print("   - Persistent: Durable cache with disk storage")
    print("   - Distributed: Multi-tier cache for scaling")
    print("\n🌐 Endpoints:")
    print("   http://localhost:8000/ - Overview")
    print("   http://localhost:8000/demo/memory-only")
    print("   http://localhost:8000/demo/persistent")
    print("   http://localhost:8000/demo/distributed")
    print("   http://localhost:8000/compare-configs")
    print("   http://localhost:8000/benchmark-all")
