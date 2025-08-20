#!/usr/bin/env python3
"""
E2E Test Server for Caching Functionality

This server mirrors examples/cache/ for E2E testing.
It provides caching functionality to be tested via HTTP.
"""
import sys
import argparse
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from catzilla import Catzilla, Request, Response, JSONResponse, Path as PathParam
from typing import Optional
import time
import random

# Initialize Catzilla for E2E testing
app = Catzilla(
    production=False,
    show_banner=False,
    log_requests=False
)

# Simple in-memory cache for E2E testing
cache = {}

def cached_function(key: str, compute_func, ttl: int = 60):
    """Simple cache implementation for E2E testing"""
    now = time.time()

    if key in cache:
        value, timestamp = cache[key]
        if now - timestamp < ttl:
            return value, True  # Cache hit

    # Cache miss - compute value
    value = compute_func()
    cache[key] = (value, now)
    return value, False

# Health check
@app.get("/health")
def health_check(request: Request) -> Response:
    """Health check endpoint"""
    return JSONResponse({
        "status": "healthy",
        "server": "caching_e2e_test",
        "timestamp": time.time(),
        "cache_size": len(cache)
    })

# Basic info
@app.get("/")
def home(request: Request) -> Response:
    """Caching test server info"""
    return JSONResponse({
        "message": "Catzilla E2E Caching Test Server",
        "features": [
            "Function-level caching",
            "Manual cache operations",
            "Cache statistics",
            "Cache invalidation"
        ],
        "endpoints": [
            "GET /cache/expensive/{value}",
            "GET /cache/weather/{city}",
            "POST /cache/set",
            "GET /cache/get/{key}",
            "DELETE /cache/delete/{key}",
            "DELETE /cache/clear",
            "GET /cache/stats"
        ],
        "cache_size": len(cache),
        "cache_operations": {
            "set": "manual_cache_set",
            "get": "manual_cache_get",
            "delete": "manual_cache_delete",
            "clear": "manual_cache_clear"
        }
    })

# Expensive calculation with caching
@app.get("/cache/expensive/{value}")
def expensive_calculation(request: Request, value: int = PathParam(..., description="Value to calculate")) -> Response:
    """Test expensive calculation with caching"""
    try:
        key = f"calc_{value}"

        def compute():
            # Simulate expensive operation
            result = 1
            for i in range(1, min(value, 20) + 1):  # Limit to prevent huge calculations
                result *= i
            return {
                "value": value,
                "result": result,
                "computed_at": time.time()
            }

        result, is_cache_hit = cached_function(key, compute, ttl=60)

        return JSONResponse({
            "calculation": result,
            "cache_hit": is_cache_hit,
            "cache_key": key,
            "timestamp": time.time()
        })

    except Exception as e:
        return JSONResponse({
            "error": "Failed to calculate",
            "message": str(e)
        }, status_code=500)

# Weather data with caching
@app.get("/cache/weather/{city}")
def get_weather_data(request: Request, city: str = PathParam(..., description="City name")) -> Response:
    """Test weather data caching"""
    try:
        key = f"weather_{city.lower()}"

        def compute():
            # Simulate API call
            return {
                "city": city,
                "temperature": random.randint(10, 35),
                "humidity": random.randint(30, 90),
                "conditions": random.choice(["sunny", "cloudy", "rainy", "snowy"]),
                "fetched_at": time.time()
            }

        result, is_cache_hit = cached_function(key, compute, ttl=180)

        # Flatten the weather data to match test expectations
        weather_data = result.copy()
        weather_data["from_cache"] = is_cache_hit
        weather_data["cache_key"] = key
        weather_data["timestamp"] = time.time()
        # Add 'weather' field for the condition
        weather_data["weather"] = weather_data.pop("conditions")

        return JSONResponse(weather_data)

    except Exception as e:
        return JSONResponse({
            "error": "Failed to get weather data",
            "message": str(e)
        }, status_code=500)

# Manual cache set operation
@app.post("/cache/set")
def cache_set(request: Request) -> Response:
    """Set cache value manually"""
    try:
        # Parse JSON body manually for simplicity
        import json
        body_str = request.body.decode() if isinstance(request.body, bytes) else str(request.body)
        body = json.loads(body_str)
        key = body.get("key")
        value = body.get("value")
        ttl = body.get("ttl", 60)

        if not key:
            return JSONResponse({"error": "Key is required"}, status_code=400)

        cache[key] = (value, time.time(), ttl)  # Store TTL with the value

        return JSONResponse({
            "message": "Cache value set successfully",
            "key": key,
            "value": value,
            "ttl": ttl,
            "set_at": time.time()
        })

    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=400)

# Manual cache get operation
@app.get("/cache/get/{key}")
def cache_get(request: Request, key: str = PathParam(..., description="Cache key")) -> Response:
    """Get cache value manually"""
    if key in cache:
        # Handle both old format (value, timestamp) and new format (value, timestamp, ttl)
        cache_data = cache[key]
        if len(cache_data) == 2:
            value, timestamp = cache_data
            ttl = 60  # Default TTL
        else:
            value, timestamp, ttl = cache_data

        age = time.time() - timestamp

        # Check if TTL expired
        if age > ttl:
            # Remove expired item
            del cache[key]
            return JSONResponse({
                "key": key,
                "found": False,
                "message": "Key not found in cache"
            }, status_code=404)

        return JSONResponse({
            "key": key,
            "value": value,
            "cached_at": timestamp,
            "age": age,
            "found": True
        })
    else:
        return JSONResponse({
            "key": key,
            "found": False,
            "message": "Key not found in cache"
        }, status_code=404)

# Manual cache delete operation
@app.delete("/cache/delete/{key}")
def cache_delete(request: Request, key: str = PathParam(..., description="Cache key")) -> Response:
    """Delete cache value manually"""
    if key in cache:
        del cache[key]
        return JSONResponse({
            "message": "Cache value deleted successfully",
            "key": key,
            "deleted_at": time.time()
        })
    else:
        return JSONResponse({
            "message": "Key not found in cache",
            "key": key
        }, status_code=404)

# Clear all cache
@app.delete("/cache/clear")
def cache_clear(request: Request) -> Response:
    """Clear all cache"""
    old_size = len(cache)
    cache.clear()

    return JSONResponse({
        "message": "Cache cleared",
        "previous_size": old_size,
        "cleared_at": time.time()
    })

# Clear all cache (POST version for test compatibility)
@app.post("/cache/clear")
def cache_clear_post(request: Request) -> Response:
    """Clear all cache via POST"""
    old_size = len(cache)
    cache.clear()

    return JSONResponse({
        "message": "Cache cleared successfully",
        "previous_size": old_size,
        "cleared_at": time.time()
    })

# Cache statistics
@app.get("/cache/stats")
def cache_stats(request: Request) -> Response:
    """Get cache statistics"""
    now = time.time()
    valid_items = 0
    expired_items = 0
    total_size = 0

    for key, (value, timestamp) in cache.items():
        total_size += 1
        if now - timestamp < 60:  # Assume 60s default TTL
            valid_items += 1
        else:
            expired_items += 1

    return JSONResponse({
        "total_items": total_size,
        "valid_items": valid_items,
        "expired_items": expired_items,
        "total_requests": total_size,  # Simplified - would track separately in real app
        "cache_hits": valid_items,  # Simplified approximation
        "cache_misses": expired_items,  # Simplified approximation
        "hit_rate": "N/A",  # Would need hit/miss counters
        "memory_usage": "N/A",  # Would need actual memory tracking
        "stats_at": now
    })

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Catzilla E2E Caching Test Server")
    parser.add_argument("--port", type=int, default=8102, help="Port to run server on")
    parser.add_argument("--host", type=str, default="127.0.0.1", help="Host to bind to")

    args = parser.parse_args()

    print(f"🚀 Starting Catzilla E2E Caching Test Server")
    print(f"📍 Server: http://{args.host}:{args.port}")
    print(f"🏥 Health: http://{args.host}:{args.port}/health")

    app.listen(port=args.port, host=args.host)
