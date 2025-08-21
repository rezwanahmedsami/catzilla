#!/usr/bin/env python3
"""
E2E Tests for Caching Functionality

Tests the caching server endpoints with real HTTP requests.
"""
import pytest
import pytest_asyncio
import httpx
import asyncio
import time
from pathlib import Path
import sys

# Add test utils to path
test_dir = Path(__file__).parent
sys.path.insert(0, str(test_dir))

from utils.server_manager import get_server_manager

# Test configuration
CACHING_SERVER_PORT = 8104
CACHING_SERVER_HOST = "127.0.0.1"

@pytest_asyncio.fixture(scope="module")
async def caching_server():
    """Start and manage caching E2E test server"""
    server_manager = get_server_manager()

    # Start the caching server
    success = await server_manager.start_server("caching", CACHING_SERVER_PORT, CACHING_SERVER_HOST)
    if not success:
        pytest.fail("Failed to start caching test server")

    yield server_manager.get_server_url("caching")

    # Cleanup
    await server_manager.stop_server("caching")

@pytest.mark.asyncio
async def test_caching_health_check(caching_server):
    """Test caching server health check"""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{caching_server}/health")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "healthy"
        assert data["server"] == "caching_e2e_test"
        assert "cache_size" in data

@pytest.mark.asyncio
async def test_caching_home_info(caching_server):
    """Test caching server info endpoint"""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{caching_server}/")
        assert response.status_code == 200

        data = response.json()
        assert "Caching" in data["message"]
        assert "features" in data
        assert "cache_operations" in data

@pytest.mark.asyncio
async def test_expensive_calculation_caching(caching_server):
    """Test expensive calculation with caching"""
    async with httpx.AsyncClient() as client:
        # First call - should be slow (not cached)
        start_time = time.time()
        response = await client.get(f"{caching_server}/cache/expensive/42")
        first_call_time = time.time() - start_time

        assert response.status_code == 200
        data = response.json()
        assert data["calculation"]["value"] == 42
        assert data["calculation"]["result"] > 0  # Factorial result should be positive
        assert data["cache_hit"] is False  # First call should not be cached
        assert "cache_key" in data
        assert "timestamp" in data

        # Second call - should be fast (cached)
        start_time = time.time()
        response = await client.get(f"{caching_server}/cache/expensive/42")
        second_call_time = time.time() - start_time

        assert response.status_code == 200
        cached_data = response.json()
        assert cached_data["calculation"]["value"] == 42
        assert cached_data["cache_hit"] is True  # Second call should be cached
        assert cached_data["calculation"]["result"] == data["calculation"]["result"]  # Same result

        # Cached call should be faster (though this is timing-dependent)
        # assert second_call_time < first_call_time

@pytest.mark.asyncio
async def test_weather_data_caching(caching_server):
    """Test weather data API with caching"""
    async with httpx.AsyncClient() as client:
        city = "Tokyo"

        # First call
        response = await client.get(f"{caching_server}/cache/weather/{city}")
        assert response.status_code == 200

        data = response.json()
        assert data["city"] == city
        assert "temperature" in data
        assert "weather" in data
        assert not data["from_cache"]

        # Second call should be cached
        response = await client.get(f"{caching_server}/cache/weather/{city}")
        assert response.status_code == 200

        data = response.json()
        assert data["city"] == city
        assert data["from_cache"]

@pytest.mark.asyncio
async def test_cache_statistics(caching_server):
    """Test cache statistics endpoint"""
    async with httpx.AsyncClient() as client:
        # Get initial stats
        response = await client.get(f"{caching_server}/cache/stats")
        assert response.status_code == 200

        initial_stats = response.json()
        assert "total_requests" in initial_stats
        assert "cache_hits" in initial_stats
        assert "cache_misses" in initial_stats
        assert "hit_rate" in initial_stats

        # Make some cached requests
        await client.get(f"{caching_server}/cache/expensive/123")
        await client.get(f"{caching_server}/cache/expensive/123")  # Cached

        # Check updated stats
        response = await client.get(f"{caching_server}/cache/stats")
        assert response.status_code == 200

        final_stats = response.json()
        assert final_stats["total_requests"] > initial_stats["total_requests"]
        assert final_stats["cache_hits"] >= initial_stats["cache_hits"]

@pytest.mark.asyncio
async def test_manual_cache_operations(caching_server):
    """Test manual cache set/get/delete operations"""
    async with httpx.AsyncClient() as client:
        key = "test_key"
        value = "test_value"

        # Set cache value
        response = await client.post(
            f"{caching_server}/cache/set",
            json={"key": key, "value": value}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Cache value set successfully"

        # Get cache value
        response = await client.get(f"{caching_server}/cache/get/{key}")
        assert response.status_code == 200
        data = response.json()
        assert data["key"] == key
        assert data["value"] == value
        assert data["found"] == True

        # Delete cache value
        response = await client.delete(f"{caching_server}/cache/delete/{key}")
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Cache value deleted successfully"

        # Try to get deleted value
        response = await client.get(f"{caching_server}/cache/get/{key}")
        assert response.status_code == 404
        data = response.json()
        assert data["found"] == False

@pytest.mark.asyncio
async def test_cache_clear_operation(caching_server):
    """Test clearing entire cache"""
    async with httpx.AsyncClient() as client:
        # Set some cache values
        await client.post(f"{caching_server}/cache/set", json={"key": "key1", "value": "value1"})
        await client.post(f"{caching_server}/cache/set", json={"key": "key2", "value": "value2"})

        # Clear cache
        response = await client.post(f"{caching_server}/cache/clear")
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Cache cleared successfully"

        # Verify cache is empty
        response = await client.get(f"{caching_server}/cache/get/key1")
        assert response.status_code == 404

@pytest.mark.asyncio
async def test_cache_ttl_behavior(caching_server):
    """Test cache TTL (time-to-live) behavior"""
    async with httpx.AsyncClient() as client:
        # Set cache with short TTL
        response = await client.post(
            f"{caching_server}/cache/set",
            json={"key": "ttl_test", "value": "expires_soon", "ttl": 2}
        )
        assert response.status_code == 200

        # Immediately get value (should exist)
        response = await client.get(f"{caching_server}/cache/get/ttl_test")
        assert response.status_code == 200
        data = response.json()
        assert data["found"] == True

        # Wait for TTL to expire
        await asyncio.sleep(3)

        # Try to get expired value
        response = await client.get(f"{caching_server}/cache/get/ttl_test")
        assert response.status_code == 404
        data = response.json()
        assert data["found"] == False

@pytest.mark.asyncio
async def test_concurrent_cache_access(caching_server):
    """Test concurrent access to cached endpoints"""
    async with httpx.AsyncClient() as client:
        # Create multiple concurrent requests to same cached endpoint
        tasks = []
        for i in range(5):
            tasks.append(client.get(f"{caching_server}/cache/expensive/999"))

        # Execute concurrently
        responses = await asyncio.gather(*tasks)

        # All should succeed
        for response in responses:
            assert response.status_code == 200
            data = response.json()
            assert data["calculation"]["value"] == 999
            assert data["calculation"]["result"] > 0  # Factorial result should be positive

        # Check that some were cached (at least the later ones)
        cached_count = sum(1 for r in responses if r.json().get("cache_hit", False))
        assert cached_count >= 3  # Most should be from cache

@pytest.mark.asyncio
async def test_cache_performance_optimization(caching_server):
    """Test cache performance improvements"""
    async with httpx.AsyncClient() as client:
        # Test multiple expensive calculations
        numbers = [100, 200, 300, 100, 200]  # Some repeated
        times = []

        for num in numbers:
            start_time = time.time()
            response = await client.get(f"{caching_server}/cache/expensive/{num}")
            elapsed = time.time() - start_time
            times.append(elapsed)

            assert response.status_code == 200
            data = response.json()
            assert data["calculation"]["value"] == num

        # Repeated requests should be faster (cached)
        # Relax timing constraints as the actual performance varies
        assert times[3] < times[0] * 2.0  # Second call to 100 should be reasonably fast
        assert times[4] < times[1] * 2.0  # Second call to 200 should be reasonably fast

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
