# Catzilla Smart Cache Examples

This directory contains examples demonstrating Catzilla's revolutionary Smart Cache system with C-acceleration and multi-level caching.

## Features Demonstrated

- 🚀 **C-accelerated Memory Cache (L1)**: Ultra-fast memory cache with jemalloc optimization
- 🌐 **Redis Cache (L2)**: Distributed caching for scalability (optional)
- 💾 **Disk Cache (L3)**: Persistent cache for durability
- 🎯 **Function-level Caching**: `@cached` decorator for easy function caching
- 🔄 **Middleware Caching**: Automatic response caching with configurable rules
- 📊 **Performance Monitoring**: Real-time statistics and benchmarking
- 🗜️ **Compression**: LZ4 compression for large values
- 🧠 **Memory Optimization**: jemalloc integration for optimal memory usage

## Examples

### 1. Basic Cache Example (`basic_cache_example.py`)

Simple demonstration of Smart Cache features:

```bash
python examples/cache/basic_cache_example.py
```

**Features:**
- Function-level caching with `@cached` decorator
- Manual cache operations
- Cache statistics monitoring
- Simple configuration

**Endpoints:**
- `GET /` - Home with cache info
- `GET /factorial/{number}` - Cached factorial calculation
- `GET /weather/{city}` - Cached weather data simulation
- `GET /manual/{key}/{value}` - Manual cache operations
- `GET /cache/stats` - Cache statistics
- `POST /cache/clear` - Clear cache

### 2. Advanced Cache Example (`smart_cache_example.py`)

Comprehensive demonstration with middleware and advanced features:

```bash
python examples/cache/smart_cache_example.py
```

**Features:**
- Multi-level caching (Memory + Redis + Disk)
- Conditional cache middleware with path-specific rules
- Performance benchmarking
- Real-time monitoring dashboard
- Cache health checks

**Endpoints:**
- `GET /` - Interactive dashboard
- `GET /cached/user/{id}` - Function-level cached user lookup
- `GET /cached/analytics` - Function-level cached analytics
- `GET /cached/search?q=term` - Function-level cached search
- `GET /api/users/{id}` - Middleware cached user API
- `GET /api/posts/{id}` - Middleware cached post API
- `GET /api/analytics` - Middleware cached analytics API
- `GET /cache/benchmark` - Performance benchmark
- `GET /cache/stats` - Detailed statistics

## Quick Start

### 1. Basic Usage

```python
from catzilla import Catzilla, SmartCache, SmartCacheConfig, cached

# Create cache configuration
config = SmartCacheConfig(
    memory_capacity=1000,
    memory_ttl=300,  # 5 minutes
    compression_enabled=True,
    disk_enabled=True
)

app = Catzilla()

# Function-level caching
@cached(ttl=60, key_prefix="calc_")
def expensive_calculation(n: int):
    # Your expensive operation here
    return result

# Direct cache usage
from catzilla import get_cache
cache = get_cache(config)

cache.set("key", "value", ttl=120)
value, found = cache.get("key")
```

### 2. Middleware Caching

```python
from catzilla import ConditionalCacheMiddleware

# Configure middleware with path-specific rules
cache_rules = {
    "/api/users/*": {
        "ttl": 300,  # 5 minutes
        "methods": ["GET"],
        "status_codes": [200, 404]
    },
    "/api/posts/*": {
        "ttl": 180,  # 3 minutes
        "methods": ["GET", "HEAD"]
    }
}

middleware = ConditionalCacheMiddleware(
    config=config,
    cache_rules=cache_rules,
    default_ttl=120
)

app.add_middleware(middleware)
```

## Configuration Options

### SmartCacheConfig

```python
SmartCacheConfig(
    # Memory Cache (L1)
    memory_capacity=10000,          # Number of items
    memory_ttl=3600,               # Default TTL in seconds
    max_value_size=100*1024*1024,  # 100MB max value size
    compression_enabled=True,       # Enable LZ4 compression
    jemalloc_enabled=True,         # Enable jemalloc optimization

    # Redis Cache (L2)
    redis_enabled=False,           # Enable Redis caching
    redis_url="redis://localhost:6379/0",
    redis_ttl=86400,              # 24 hours
    redis_max_connections=10,

    # Disk Cache (L3)
    disk_enabled=False,           # Enable disk caching
    disk_path="/tmp/catzilla_cache",
    disk_ttl=604800,             # 7 days
    disk_max_size=1024*1024*1024, # 1GB

    # Performance
    enable_stats=True,            # Enable statistics collection
    auto_expire_interval=300,     # Cleanup interval (5 minutes)
)
```

## Performance Characteristics

### Benchmark Results (typical)

- **Memory Cache (C-level)**:
  - Set operations: ~500,000+ ops/sec
  - Get operations: ~1,000,000+ ops/sec
  - Average latency: ~1-2 microseconds

- **Multi-level Cache**:
  - L1 hit: ~1-2 microseconds
  - L2 hit: ~100-500 microseconds
  - L3 hit: ~1-5 milliseconds

### Memory Usage

- C-level memory cache uses jemalloc for optimal allocation
- Compression reduces memory usage by 60-80% for large objects
- Automatic memory pressure handling and eviction

## Cache Hierarchy

1. **L1 - Memory Cache**: Ultra-fast C-level cache with jemalloc
2. **L2 - Redis Cache**: Distributed cache for scaling across servers
3. **L3 - Disk Cache**: Persistent cache surviving restarts

Cache promotion: L3 → L2 → L1 on cache hits for optimal performance.

## Monitoring and Debugging

### Cache Statistics

```python
stats = cache.get_stats()
print(f"Hit ratio: {stats.hit_ratio:.2%}")
print(f"Memory usage: {stats.memory_usage:,} bytes")
print(f"Total hits: {stats.hits:,}")
```

### Health Checks

```python
health = cache.health_check()
print(f"Memory cache: {health['memory']}")
print(f"Redis cache: {health['redis']}")
print(f"Disk cache: {health['disk']}")
```

## Tips for Production

1. **Memory Settings**: Start with 10,000 capacity, adjust based on memory usage
2. **TTL Strategy**: Use shorter TTL for frequently changing data
3. **Redis Setup**: Enable Redis for distributed deployments
4. **Disk Cache**: Enable for persistence across restarts
5. **Monitoring**: Monitor hit ratios and adjust configuration accordingly
6. **Compression**: Enable for large objects (>1KB)

## Requirements

- Python 3.8+
- Catzilla framework
- Optional: Redis server (for L2 cache)
- Optional: LZ4 library (for compression)

## Running the Examples

1. Install Catzilla:
   ```bash
   pip install catzilla
   ```

2. Run basic example:
   ```bash
   cd examples/cache
   python basic_cache_example.py
   ```

3. Run advanced example:
   ```bash
   python smart_cache_example.py
   ```

4. Access the web interface at `http://localhost:8000`

## Troubleshooting

### C Library Not Available
If you see "C library not available", run:
```bash
make build
```

### Redis Connection Issues
For Redis cache (L2), ensure Redis is running:
```bash
redis-server
```

### Disk Cache Permissions
Ensure write permissions for cache directory:
```bash
mkdir -p /tmp/catzilla_cache
chmod 755 /tmp/catzilla_cache
```
