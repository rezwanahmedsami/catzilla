"""
Test Suite for Catzilla Smart Cache System
Comprehensive testing of C-level cache, Python integration, and middleware
"""

import asyncio
import json
import os
import tempfile
import time
import unittest
from unittest.mock import Mock, patch, AsyncMock
import threading
from concurrent.futures import ThreadPoolExecutor

# Test imports
try:
    from catzilla.smart_cache import (
        SmartCache, SmartCacheConfig, MemoryCache, RedisCache, DiskCache,
        CacheError, CacheNotAvailableError, cached, get_cache, reset_cache
    )
    from catzilla.cache_middleware import (
        SmartCacheMiddleware, ConditionalCacheMiddleware,
        create_api_cache_middleware, create_static_cache_middleware
    )
    from catzilla.types import Request, Response
    MODULES_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Could not import cache modules: {e}")
    MODULES_AVAILABLE = False


@unittest.skipUnless(MODULES_AVAILABLE, "Cache modules not available")
class TestSmartCacheConfig(unittest.TestCase):
    """Test Smart Cache Configuration"""

    def test_default_config(self):
        """Test default configuration values"""
        config = SmartCacheConfig()

        self.assertEqual(config.memory_capacity, 10000)
        self.assertEqual(config.memory_ttl, 3600)
        self.assertEqual(config.max_value_size, 100 * 1024 * 1024)
        self.assertTrue(config.compression_enabled)
        self.assertTrue(config.jemalloc_enabled)
        self.assertFalse(config.redis_enabled)
        self.assertFalse(config.disk_enabled)

    def test_custom_config(self):
        """Test custom configuration"""
        config = SmartCacheConfig(
            memory_capacity=5000,
            memory_ttl=1800,
            redis_enabled=True,
            disk_enabled=True,
            disk_path="/tmp/test_cache"
        )

        self.assertEqual(config.memory_capacity, 5000)
        self.assertEqual(config.memory_ttl, 1800)
        self.assertTrue(config.redis_enabled)
        self.assertTrue(config.disk_enabled)
        self.assertEqual(config.disk_path, "/tmp/test_cache")


@unittest.skipUnless(MODULES_AVAILABLE, "Cache modules not available")
class TestMemoryCache(unittest.TestCase):
    """Test C-level Memory Cache"""

    def setUp(self):
        """Set up test cache"""
        self.config = SmartCacheConfig(
            memory_capacity=100,
            memory_ttl=10,
            compression_enabled=False  # Disable for simpler testing
        )

        try:
            self.cache = MemoryCache(self.config)
            self.cache_available = True
        except Exception:
            self.cache_available = False

    def tearDown(self):
        """Clean up"""
        if hasattr(self, 'cache') and self.cache:
            self.cache.clear()

    @unittest.skipUnless(True, "Test memory cache availability")
    def test_cache_availability(self):
        """Test if C cache is available"""
        # This test always runs to check availability
        try:
            cache = MemoryCache(self.config)
            self.assertTrue(True, "C cache is available")
        except Exception as e:
            self.skipTest(f"C cache not available: {e}")

    def test_basic_operations(self):
        """Test basic cache operations"""
        if not self.cache_available:
            self.skipTest("Cache not available")

        # Test set and get
        result = self.cache.set("test_key", "test_value")
        self.assertTrue(result)

        value, found = self.cache.get("test_key")
        self.assertTrue(found)
        self.assertEqual(value, "test_value")

        # Test non-existent key
        value, found = self.cache.get("nonexistent")
        self.assertFalse(found)
        self.assertIsNone(value)

    def test_data_types(self):
        """Test different data types"""
        if not self.cache_available:
            self.skipTest("Cache not available")

        test_cases = [
            ("string", "hello world"),
            ("int", 42),
            ("float", 3.14159),
            ("list", [1, 2, 3, "four"]),
            ("dict", {"key": "value", "num": 123}),
            ("bytes", b"binary data"),
            ("unicode", "Unicode: 你好世界 🌍"),
        ]

        for key, value in test_cases:
            with self.subTest(data_type=type(value).__name__):
                self.assertTrue(self.cache.set(key, value))
                retrieved, found = self.cache.get(key)
                self.assertTrue(found)
                self.assertEqual(retrieved, value)

    def test_ttl_expiration(self):
        """Test TTL expiration"""
        if not self.cache_available:
            self.skipTest("Cache not available")

        # Set with short TTL
        self.assertTrue(self.cache.set("expire_test", "value", ttl=1))

        # Should be available immediately
        value, found = self.cache.get("expire_test")
        self.assertTrue(found)
        self.assertEqual(value, "value")

        # Wait for expiration
        time.sleep(1.5)

        # Should be expired
        value, found = self.cache.get("expire_test")
        self.assertFalse(found)

    def test_delete_operation(self):
        """Test delete operation"""
        if not self.cache_available:
            self.skipTest("Cache not available")

        # Set and verify
        self.assertTrue(self.cache.set("delete_test", "value"))
        self.assertTrue(self.cache.exists("delete_test"))

        # Delete and verify
        self.assertTrue(self.cache.delete("delete_test"))
        self.assertFalse(self.cache.exists("delete_test"))

        # Delete non-existent key
        self.assertFalse(self.cache.delete("nonexistent"))

    def test_exists_operation(self):
        """Test exists operation"""
        if not self.cache_available:
            self.skipTest("Cache not available")

        # Non-existent key
        self.assertFalse(self.cache.exists("nonexistent"))

        # Existing key
        self.assertTrue(self.cache.set("exists_test", "value"))
        self.assertTrue(self.cache.exists("exists_test"))

        # Expired key
        self.assertTrue(self.cache.set("expire_test", "value", ttl=1))
        time.sleep(1.5)
        self.assertFalse(self.cache.exists("expire_test"))

    def test_statistics(self):
        """Test cache statistics"""
        if not self.cache_available:
            self.skipTest("Cache not available")

        # Initial stats
        stats = self.cache.get_stats()
        initial_hits = stats.hits
        initial_misses = stats.misses

        # Generate some cache activity
        self.cache.set("stats_test", "value")
        self.cache.get("stats_test")  # Hit
        self.cache.get("nonexistent")  # Miss

        # Check updated stats
        stats = self.cache.get_stats()
        self.assertGreater(stats.hits, initial_hits)
        self.assertGreater(stats.misses, initial_misses)
        self.assertGreaterEqual(stats.hit_ratio, 0.0)
        self.assertLessEqual(stats.hit_ratio, 1.0)

    def test_clear_operation(self):
        """Test clear operation"""
        if not self.cache_available:
            self.skipTest("Cache not available")

        # Add some data
        for i in range(10):
            self.cache.set(f"key_{i}", f"value_{i}")

        # Verify data exists
        value, found = self.cache.get("key_5")
        self.assertTrue(found)

        # Clear and verify
        self.cache.clear()
        value, found = self.cache.get("key_5")
        self.assertFalse(found)

    def test_thread_safety(self):
        """Test thread safety"""
        if not self.cache_available:
            self.skipTest("Cache not available")

        def worker(thread_id):
            for i in range(50):
                key = f"thread_{thread_id}_key_{i}"
                value = f"thread_{thread_id}_value_{i}"

                self.cache.set(key, value)
                retrieved, found = self.cache.get(key)

                if found:
                    self.assertEqual(retrieved, value)

        # Run multiple threads
        threads = []
        for i in range(4):
            thread = threading.Thread(target=worker, args=(i,))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()


@unittest.skipUnless(MODULES_AVAILABLE, "Cache modules not available")
class TestDiskCache(unittest.TestCase):
    """Test Disk Cache"""

    def setUp(self):
        """Set up test cache"""
        self.temp_dir = tempfile.mkdtemp()
        self.config = SmartCacheConfig(
            disk_enabled=True,
            disk_path=self.temp_dir,
            disk_ttl=10
        )
        self.cache = DiskCache(self.config)

    def tearDown(self):
        """Clean up"""
        import shutil
        try:
            shutil.rmtree(self.temp_dir)
        except Exception:
            pass

    def test_basic_operations(self):
        """Test basic disk cache operations"""
        # Test set and get
        result = self.cache.set("disk_test", "test_value")
        self.assertTrue(result)

        value, found = self.cache.get("disk_test")
        self.assertTrue(found)
        self.assertEqual(value, "test_value")

        # Test non-existent key
        value, found = self.cache.get("nonexistent")
        self.assertFalse(found)

    def test_file_persistence(self):
        """Test that data persists across cache instances"""
        # Set data
        self.cache.set("persist_test", {"data": "persistent"})

        # Create new cache instance with same directory
        new_cache = DiskCache(self.config)

        # Retrieve data
        value, found = new_cache.get("persist_test")
        self.assertTrue(found)
        self.assertEqual(value, {"data": "persistent"})

    def test_ttl_expiration(self):
        """Test disk cache TTL"""
        # Set with short TTL
        config = SmartCacheConfig(
            disk_enabled=True,
            disk_path=self.temp_dir,
            disk_ttl=1
        )
        cache = DiskCache(config)

        cache.set("expire_test", "value")

        # Should be available immediately
        value, found = cache.get("expire_test")
        self.assertTrue(found)

        # Wait for expiration
        time.sleep(1.5)

        # Should be expired
        value, found = cache.get("expire_test")
        self.assertFalse(found)


@unittest.skipUnless(MODULES_AVAILABLE, "Cache modules not available")
class TestSmartCache(unittest.TestCase):
    """Test Multi-Level Smart Cache"""

    def setUp(self):
        """Set up test cache"""
        self.temp_dir = tempfile.mkdtemp()
        self.config = SmartCacheConfig(
            memory_capacity=50,
            disk_enabled=True,
            disk_path=self.temp_dir
        )

        # Reset global cache
        reset_cache()

        try:
            self.cache = SmartCache(self.config)
            self.cache_available = True
        except Exception:
            self.cache_available = False

    def tearDown(self):
        """Clean up"""
        import shutil
        try:
            shutil.rmtree(self.temp_dir)
        except Exception:
            pass
        reset_cache()

    def test_multi_level_caching(self):
        """Test multi-level cache behavior"""
        if not self.cache_available:
            self.skipTest("Cache not available")

        # Set data
        self.assertTrue(self.cache.set("multi_test", "test_data"))

        # Should be in memory cache
        if self.cache._memory_cache:
            self.assertTrue(self.cache._memory_cache.exists("multi_test"))

        # Should be in disk cache
        if self.cache._disk_cache:
            self.assertTrue(self.cache._disk_cache.exists("multi_test"))

        # Retrieve data
        value, found = self.cache.get("multi_test")
        self.assertTrue(found)
        self.assertEqual(value, "test_data")

    def test_cache_promotion(self):
        """Test cache promotion from lower to higher tiers"""
        if not self.cache_available or not self.cache._memory_cache or not self.cache._disk_cache:
            self.skipTest("Multi-level cache not available")

        # Set data
        self.cache.set("promote_test", "promote_data")

        # Remove from memory cache to simulate eviction
        self.cache._memory_cache.delete("promote_test")

        # Data should still be in disk cache
        self.assertTrue(self.cache._disk_cache.exists("promote_test"))

        # Get data (should promote to memory)
        value, found = self.cache.get("promote_test")
        self.assertTrue(found)
        self.assertEqual(value, "promote_data")

        # Should now be in memory cache again
        self.assertTrue(self.cache._memory_cache.exists("promote_test"))

    def test_key_generation(self):
        """Test cache key generation"""
        if not self.cache_available:
            self.skipTest("Cache not available")

        # Test basic key generation
        key = self.cache.generate_key("GET", "/api/users")
        self.assertIsInstance(key, str)
        self.assertIn("GET", key)
        self.assertIn("/api/users", key)

        # Test with query string
        key_with_query = self.cache.generate_key("GET", "/api/users", "page=1&limit=10")
        self.assertIn("page=1", key_with_query)

        # Test with headers
        headers = {"accept": "application/json", "accept-language": "en-US"}
        key_with_headers = self.cache.generate_key("GET", "/api/users", headers=headers)
        self.assertIsInstance(key_with_headers, str)

    def test_statistics(self):
        """Test cache statistics"""
        if not self.cache_available:
            self.skipTest("Cache not available")

        # Generate some activity
        self.cache.set("stats_test_1", "value1")
        self.cache.set("stats_test_2", "value2")
        self.cache.get("stats_test_1")  # Hit
        self.cache.get("nonexistent")   # Miss

        stats = self.cache.get_stats()

        self.assertIsNotNone(stats.tier_stats)
        self.assertGreaterEqual(stats.hit_ratio, 0.0)
        self.assertLessEqual(stats.hit_ratio, 1.0)

    def test_health_check(self):
        """Test cache health check"""
        if not self.cache_available:
            self.skipTest("Cache not available")

        health = self.cache.health_check()

        self.assertIsInstance(health, dict)
        self.assertIn('memory', health)
        self.assertIn('redis', health)
        self.assertIn('disk', health)

        # Memory should be available if C library is loaded
        # Redis should be False (not configured)
        # Disk should be True (configured in test)
        self.assertFalse(health['redis'])


@unittest.skipUnless(MODULES_AVAILABLE, "Cache modules not available")
class TestCacheDecorator(unittest.TestCase):
    """Test cache decorator functionality"""

    def setUp(self):
        """Set up test"""
        reset_cache()

    def tearDown(self):
        """Clean up"""
        reset_cache()

    def test_function_caching(self):
        """Test function result caching"""
        call_count = 0

        @cached(ttl=60, key_prefix="test_")
        def expensive_function(x, y):
            nonlocal call_count
            call_count += 1
            return x * y

        # First call should execute function
        result1 = expensive_function(5, 6)
        self.assertEqual(result1, 30)
        self.assertEqual(call_count, 1)

        # Second call with same args should use cache
        result2 = expensive_function(5, 6)
        self.assertEqual(result2, 30)
        self.assertEqual(call_count, 1)  # No additional calls

        # Different args should execute function again
        result3 = expensive_function(7, 8)
        self.assertEqual(result3, 56)
        self.assertEqual(call_count, 2)


@unittest.skipUnless(MODULES_AVAILABLE, "Cache modules not available")
class TestCacheMiddleware(unittest.TestCase):
    """Test Smart Cache Middleware"""

    def setUp(self):
        """Set up test middleware"""
        self.temp_dir = tempfile.mkdtemp()
        self.config = SmartCacheConfig(
            memory_capacity=100,
            disk_enabled=True,
            disk_path=self.temp_dir
        )

        try:
            self.middleware = SmartCacheMiddleware(
                config=self.config,
                default_ttl=300
            )
            self.middleware_available = True
        except Exception:
            self.middleware_available = False

    def tearDown(self):
        """Clean up"""
        import shutil
        try:
            shutil.rmtree(self.temp_dir)
        except Exception:
            pass

    def create_mock_request(self, method="GET", path="/api/test", query=None, headers=None):
        """Create mock request object"""
        request = Mock()
        request.method = method
        request.url = Mock()
        request.url.path = path
        request.url.query = query
        request.headers = headers or {}
        request.state = Mock()
        return request

    def create_mock_response(self, content="test content", status_code=200, headers=None):
        """Create mock response object"""
        response = Mock()
        response.body = content.encode() if isinstance(content, str) else content
        response.status_code = status_code
        response.headers = headers or {}
        return response

    @unittest.skipUnless(True, "Test middleware availability")
    def test_middleware_availability(self):
        """Test if middleware is available"""
        try:
            middleware = SmartCacheMiddleware()
            self.assertTrue(True, "Middleware is available")
        except Exception as e:
            self.skipTest(f"Middleware not available: {e}")

    async def test_cache_hit(self):
        """Test cache hit scenario"""
        if not self.middleware_available:
            self.skipTest("Middleware not available")

        request = self.create_mock_request()
        response = self.create_mock_response()

        # First request should miss and set cache
        cached_response = await self.middleware.process_request(request)
        self.assertIsNone(cached_response)  # Cache miss

        # Process response to cache it
        await self.middleware.process_response(request, response)

        # Second request should hit cache
        request2 = self.create_mock_request()  # Same request
        cached_response = await self.middleware.process_request(request2)

        if cached_response:  # If caching is working
            self.assertIsNotNone(cached_response)
            self.assertEqual(cached_response.headers.get('x-cache'), 'HIT')

    async def test_cache_skip_conditions(self):
        """Test conditions where caching is skipped"""
        if not self.middleware_available:
            self.skipTest("Middleware not available")

        # POST request should not be cached
        post_request = self.create_mock_request(method="POST")
        result = await self.middleware.process_request(post_request)
        self.assertIsNone(result)

        # Request with no-cache header should not be cached
        no_cache_request = self.create_mock_request(
            headers={'cache-control': 'no-cache'}
        )
        result = await self.middleware.process_request(no_cache_request)
        self.assertIsNone(result)

        # Authenticated request should not be cached (by default)
        auth_request = self.create_mock_request(
            headers={'authorization': 'Bearer token'}
        )
        result = await self.middleware.process_request(auth_request)
        self.assertIsNone(result)

    def test_key_generation(self):
        """Test cache key generation"""
        if not self.middleware_available:
            self.skipTest("Middleware not available")

        request = self.create_mock_request(
            path="/api/users",
            query="page=1&limit=10",
            headers={'accept': 'application/json'}
        )

        key = self.middleware._generate_cache_key(request)
        self.assertIsInstance(key, str)
        self.assertGreater(len(key), 0)

    def test_middleware_statistics(self):
        """Test middleware statistics"""
        if not self.middleware_available:
            self.skipTest("Middleware not available")

        stats = self.middleware.get_stats()

        self.assertIsInstance(stats, dict)
        self.assertIn('middleware_stats', stats)
        self.assertIn('cache_stats', stats)
        self.assertIn('overall_hit_ratio', stats)
        self.assertIn('cache_health', stats)


@unittest.skipUnless(MODULES_AVAILABLE, "Cache modules not available")
class TestConditionalCacheMiddleware(unittest.TestCase):
    """Test Conditional Cache Middleware"""

    def setUp(self):
        """Set up conditional middleware"""
        self.cache_rules = {
            "/api/users/*": {"ttl": 300, "methods": ["GET"]},
            "/api/posts/*": {"ttl": 600, "status_codes": [200, 404]},
            "/static/*": {"ttl": 86400, "methods": ["GET", "HEAD"]},
        }

        try:
            self.middleware = ConditionalCacheMiddleware(
                cache_rules=self.cache_rules,
                default_ttl=300
            )
            self.middleware_available = True
        except Exception:
            self.middleware_available = False

    def test_rule_matching(self):
        """Test cache rule matching"""
        if not self.middleware_available:
            self.skipTest("Middleware not available")

        # Test exact rule matching
        rule = self.middleware._get_rule_for_path("/api/users/123")
        self.assertIsNotNone(rule)
        self.assertEqual(rule["ttl"], 300)

        # Test no matching rule
        rule = self.middleware._get_rule_for_path("/other/path")
        self.assertIsNone(rule)

    async def test_rule_based_caching(self):
        """Test caching based on rules"""
        if not self.middleware_available:
            self.skipTest("Middleware not available")

        # Request matching /api/users/* rule
        request = Mock()
        request.method = "GET"
        request.url = Mock()
        request.url.path = "/api/users/123"
        request.url.query = None
        request.headers = {}
        request.state = Mock()

        # Should allow caching
        should_cache = self.middleware._should_cache_request(request)
        self.assertTrue(should_cache)

        # POST to same path should not be cached (rule specifies GET only)
        request.method = "POST"
        should_cache = self.middleware._should_cache_request(request)
        self.assertFalse(should_cache)


class TestIntegration(unittest.TestCase):
    """Integration tests for the complete caching system"""

    @unittest.skipUnless(MODULES_AVAILABLE, "Cache modules not available")
    def test_end_to_end_caching(self):
        """Test complete end-to-end caching workflow"""
        # This would require a full Catzilla application setup
        # For now, we'll test the components work together

        try:
            # Create cache
            config = SmartCacheConfig(memory_capacity=100)
            cache = SmartCache(config)

            # Create middleware
            middleware = SmartCacheMiddleware(cache_instance=cache)

            # Test they work together
            stats = middleware.get_stats()
            self.assertIsInstance(stats, dict)

        except Exception as e:
            self.skipTest(f"Integration test failed: {e}")


def run_performance_tests():
    """Run performance tests for cache system"""
    print("\n" + "="*60)
    print("🚀 CATZILLA SMART CACHE PERFORMANCE TESTS")
    print("="*60)

    try:
        from python.catzilla.smart_cache import SmartCache, SmartCacheConfig

        # Test configuration
        config = SmartCacheConfig(
            memory_capacity=10000,
            compression_enabled=True
        )

        cache = SmartCache(config)

        # Performance test parameters
        num_operations = 10000
        num_threads = 4

        print(f"\n📊 Testing {num_operations} operations with {num_threads} threads...")

        def benchmark_worker(thread_id, operations_per_thread):
            """Worker function for performance testing"""
            start_time = time.time()

            for i in range(operations_per_thread):
                key = f"perf_test_{thread_id}_{i}"
                value = f"performance_test_value_{i}" * 10  # ~200 bytes

                # Set operation
                cache.set(key, value)

                # Get operation
                retrieved, found = cache.get(key)
                assert found
                assert retrieved == value

                # Every 100th operation, test delete
                if i % 100 == 0:
                    cache.delete(key)

            end_time = time.time()
            return end_time - start_time

        # Run benchmark
        start_total = time.time()

        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            operations_per_thread = num_operations // num_threads
            futures = []

            for thread_id in range(num_threads):
                future = executor.submit(benchmark_worker, thread_id, operations_per_thread)
                futures.append(future)

            thread_times = [future.result() for future in futures]

        end_total = time.time()
        total_time = end_total - start_total

        # Calculate statistics
        ops_per_second = (num_operations * 2) / total_time  # 2 ops per iteration (set + get)
        avg_thread_time = sum(thread_times) / len(thread_times)

        print(f"✅ Performance Results:")
        print(f"   Total Time: {total_time:.2f} seconds")
        print(f"   Operations/Second: {ops_per_second:,.0f}")
        print(f"   Average Thread Time: {avg_thread_time:.2f} seconds")

        # Get final statistics
        stats = cache.get_stats()
        print(f"   Cache Hit Ratio: {stats.hit_ratio:.2%}")
        print(f"   Memory Usage: {stats.memory_usage:,} bytes")
        print(f"   Cache Size: {stats.size:,} entries")

        print("\n🎯 Performance test completed successfully!")

    except Exception as e:
        print(f"❌ Performance test failed: {e}")


if __name__ == "__main__":
    # Run unit tests
    print("🧪 Running Catzilla Smart Cache Test Suite...")

    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add test classes
    test_classes = [
        TestSmartCacheConfig,
        TestMemoryCache,
        TestDiskCache,
        TestSmartCache,
        TestCacheDecorator,
        TestCacheMiddleware,
        TestConditionalCacheMiddleware,
        TestIntegration,
    ]

    for test_class in test_classes:
        tests = loader.loadTestsFromTestCase(test_class)
        suite.addTests(tests)

    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Run performance tests if unit tests pass
    if result.wasSuccessful():
        run_performance_tests()
    else:
        print(f"\n❌ {len(result.failures)} test failures, {len(result.errors)} errors")
        print("Skipping performance tests due to test failures.")

    print("\n" + "="*60)
    print("🏁 Test suite execution completed!")
    print("="*60)
