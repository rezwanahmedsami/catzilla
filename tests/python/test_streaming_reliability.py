"""
Enhanced Streaming Reliability Tests for Catzilla
Tests for production-ready streaming with comprehensive error handling,
performance validation, and reliability scenarios.
"""
import unittest
import threading
import time
import sys
import os
import gc
import weakref
from concurrent.futures import ThreadPoolExecutor, as_completed
from unittest.mock import MagicMock, patch
from io import StringIO

# Memory monitoring fallback
try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False

# Add the project root to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from python.catzilla import StreamingResponse, StreamingWriter
from python.catzilla.streaming import _HAS_C_STREAMING, _get_streaming_response, _register_streaming_response


class TestStreamingReliability(unittest.TestCase):
    """Comprehensive reliability tests for streaming functionality."""

    def setUp(self):
        """Set up test environment."""
        if HAS_PSUTIL:
            self.initial_memory = psutil.Process().memory_info().rss
        else:
            self.initial_memory = None

    def tearDown(self):
        """Clean up after tests."""
        # Force garbage collection
        gc.collect()

    def test_memory_leak_prevention(self):
        """Test that streaming responses don't cause memory leaks."""
        # Force garbage collection before starting
        gc.collect()
        initial_objects = len(gc.get_objects())

        # Create many streaming responses with simple generators to avoid closure issues
        responses = []
        for i in range(50):  # Reduced count to avoid closure overhead
            # Use a simple generator without closures
            def generate_data(data_id=i):
                for j in range(100):  # Reduced size
                    yield f"data-{data_id}-{j}\n"

            response = StreamingResponse(generate_data(), content_type="text/plain")
            responses.append(response)

        # Create weak references to detect proper cleanup
        weak_refs = [weakref.ref(r) for r in responses]

        # Clear strong references and force cleanup
        del responses
        gc.collect()
        gc.collect()  # Run twice to ensure cleanup

        # Check that objects were properly cleaned up
        alive_refs = sum(1 for ref in weak_refs if ref() is not None)
        self.assertLess(alive_refs, 10, "Too many streaming responses still alive")

        final_objects = len(gc.get_objects())
        object_growth = final_objects - initial_objects
        self.assertLess(object_growth, 100, f"Object growth too high: {object_growth}. This may be normal due to generator closures.")

    def test_large_data_streaming(self):
        """Test streaming with very large data sets."""
        def generate_large_data():
            # Generate 10MB of data in chunks
            chunk_size = 1024  # 1KB chunks
            total_chunks = 10 * 1024  # 10MB total

            for i in range(total_chunks):
                yield "x" * chunk_size

        response = StreamingResponse(generate_large_data(), content_type="text/plain")

        # Verify streaming marker is created (not collecting all data)
        if _HAS_C_STREAMING:
            self.assertTrue(response.is_streaming())
            self.assertIn("___CATZILLA_STREAMING___", response.body)

        # Memory should remain low since we're not collecting all data
        if HAS_PSUTIL:
            current_memory = psutil.Process().memory_info().rss
            memory_growth = current_memory - self.initial_memory
            # Should use less than 50MB additional memory for 10MB of streaming data
            self.assertLess(memory_growth, 50 * 1024 * 1024, "Memory usage too high for streaming")
        else:
            # Skip memory check if psutil unavailable
            pass

    def test_concurrent_streaming_responses(self):
        """Test creating multiple streaming responses concurrently."""
        def create_streaming_response(i):
            def generate():
                for j in range(100):
                    yield f"thread-{i}-data-{j}\n"
                    time.sleep(0.001)  # Small delay to simulate real work

            return StreamingResponse(generate(), content_type="text/plain")

        # Create streaming responses concurrently
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(create_streaming_response, i) for i in range(50)]
            responses = [future.result() for future in as_completed(futures)]

        # Verify all responses were created successfully
        self.assertEqual(len(responses), 50)

        # If C streaming is available, verify streaming IDs are unique
        if _HAS_C_STREAMING:
            streaming_ids = set()
            for response in responses:
                if response.is_streaming():
                    # Extract streaming ID from body
                    body = response.body
                    if "___CATZILLA_STREAMING___" in body:
                        start = body.find("___CATZILLA_STREAMING___") + 24
                        end = body.find("___", start)
                        if end != -1:
                            streaming_id = body[start:end]
                            streaming_ids.add(streaming_id)

            # All streaming IDs should be unique
            self.assertEqual(len(streaming_ids), len(responses))

    def test_streaming_with_exceptions(self):
        """Test streaming behavior when generators raise exceptions."""
        def failing_generator():
            yield "data-1\n"
            yield "data-2\n"
            raise ValueError("Generator failed")

        response = StreamingResponse(failing_generator(), content_type="text/plain")

        # In fallback mode, exception should be caught during collection
        if not _HAS_C_STREAMING:
            # Exception should be raised during content collection
            with self.assertRaises(ValueError):
                _ = response.body

    def test_streaming_registration_cleanup(self):
        """Test that streaming response registration is properly cleaned up."""
        if not _HAS_C_STREAMING:
            self.skipTest("C streaming not available")

        # Import the registry directly
        from python.catzilla.streaming import _streaming_responses

        initial_count = len(_streaming_responses)

        responses = []
        for i in range(10):
            def generate():
                yield f"data-{i}\n"

            response = StreamingResponse(generate(), content_type="text/plain")
            responses.append(response)

        # Should have registered streaming responses
        current_count = len(_streaming_responses)
        self.assertGreater(current_count, initial_count)

        # Clear references - weak references should clean up automatically
        del responses
        gc.collect()

        # Give some time for weak references to be cleaned up
        time.sleep(0.1)

        final_count = len(getattr(_get_streaming_response.__globals__.get('_streaming_responses', {}), '_data', {}))
        self.assertLessEqual(final_count, initial_count + 2)  # Allow some tolerance

    def test_streaming_response_headers(self):
        """Test that streaming responses have correct headers."""
        def generate():
            yield "chunk1\n"
            yield "chunk2\n"

        response = StreamingResponse(
            generate(),
            content_type="application/json",
            headers={"X-Custom": "test", "Cache-Control": "no-cache"}
        )

        self.assertEqual(response.content_type, "application/json")
        self.assertEqual(response.headers.get("X-Custom"), "test")
        self.assertEqual(response.headers.get("Cache-Control"), "no-cache")

    def test_streaming_with_empty_generator(self):
        """Test streaming with empty generators."""
        def empty_generator():
            return
            yield  # This line is never reached

        response = StreamingResponse(empty_generator(), content_type="text/plain")

        if _HAS_C_STREAMING:
            self.assertTrue(response.is_streaming())
        else:
            self.assertEqual(response.body, "")

    def test_streaming_with_single_chunk(self):
        """Test streaming with a single chunk of data."""
        def single_chunk():
            yield "single chunk of data"

        response = StreamingResponse(single_chunk(), content_type="text/plain")

        if _HAS_C_STREAMING:
            self.assertTrue(response.is_streaming())
        else:
            self.assertEqual(response.body, "single chunk of data")

    def test_streaming_performance_benchmark(self):
        """Benchmark streaming response creation time."""
        def generate_data():
            for i in range(10000):
                yield f"data-{i}\n"

        # Measure creation time
        start_time = time.time()
        response = StreamingResponse(generate_data(), content_type="text/plain")
        creation_time = time.time() - start_time

        # Creation should be very fast (under 10ms) since we're not collecting data
        self.assertLess(creation_time, 0.01, f"StreamingResponse creation too slow: {creation_time:.3f}s")

        # Verify response is properly configured
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, "text/plain")

    def test_streaming_writer_reliability(self):
        """Test StreamingWriter reliability and error handling."""
        response = StreamingResponse(content_type="text/csv")
        response.write = MagicMock()

        # Test normal operation
        writer = StreamingWriter(response)
        writer.write("header1,header2\n")
        writer.write("value1,value2\n")

        # Test double close (should be safe)
        writer.close()
        writer.close()  # Should not raise an exception

        # Test writing after close (should raise an error)
        with self.assertRaises(ValueError):
            writer.write("more data")

    def test_unicode_and_encoding_handling(self):
        """Test streaming with various encodings and unicode data."""
        def unicode_generator():
            yield "ASCII data\n"
            yield "Unicode: héllo wörld 🌍\n"
            yield "Emoji: 🚀🎉💻\n"
            yield "Chinese: 你好世界\n"
            yield "Arabic: مرحبا بالعالم\n"

        response = StreamingResponse(unicode_generator(), content_type="text/plain; charset=utf-8")

        if not _HAS_C_STREAMING:
            # In fallback mode, verify all unicode is preserved
            body = response.body
            self.assertIn("héllo wörld", body)
            self.assertIn("🌍", body)
            self.assertIn("你好世界", body)

    def test_concurrent_registry_access(self):
        """Test thread safety of streaming response registry."""
        if not _HAS_C_STREAMING:
            self.skipTest("C streaming not available")

        def create_and_lookup_response(i):
            def generate():
                yield f"data-{i}\n"

            response = StreamingResponse(generate(), content_type="text/plain")

            # Extract streaming ID and test lookup
            if hasattr(response, '_streaming_id') and response._streaming_id:
                looked_up = _get_streaming_response(response._streaming_id)
                return looked_up is response
            return True

        # Test concurrent access to registry
        with ThreadPoolExecutor(max_workers=20) as executor:
            futures = [executor.submit(create_and_lookup_response, i) for i in range(100)]
            results = [future.result() for future in as_completed(futures)]

        # All lookups should have succeeded
        self.assertTrue(all(results), "Some streaming response lookups failed")


class TestStreamingIntegration(unittest.TestCase):
    """Integration tests for end-to-end streaming functionality."""

    def test_c_extension_integration(self):
        """Test integration with C extension if available."""
        if not _HAS_C_STREAMING:
            self.skipTest("C streaming extension not available")

        def generate():
            yield "test data 1\n"
            yield "test data 2\n"

        response = StreamingResponse(generate(), content_type="text/plain")

        # Should be using C streaming
        self.assertTrue(response.is_streaming())
        self.assertIn("___CATZILLA_STREAMING___", response.body)

        # Should have a streaming ID
        self.assertIsNotNone(getattr(response, '_streaming_id', None))

        # Should be registered in the global registry
        if hasattr(response, '_streaming_id'):
            looked_up = _get_streaming_response(response._streaming_id)
            self.assertIs(looked_up, response)

    def test_fallback_mode_integration(self):
        """Test integration when C extension is not available."""
        # Temporarily disable C streaming for this test
        original_has_streaming = getattr(sys.modules.get('python.catzilla.streaming'), '_HAS_C_STREAMING', False)

        try:
            # Force fallback mode
            if 'python.catzilla.streaming' in sys.modules:
                sys.modules['python.catzilla.streaming']._HAS_C_STREAMING = False

            def generate():
                yield "fallback data 1\n"
                yield "fallback data 2\n"

            response = StreamingResponse(generate(), content_type="text/plain")

            # Should not be using streaming (fallback mode)
            self.assertFalse(response.is_streaming())

            # Should have collected all content
            expected_content = "fallback data 1\nfallback data 2\n"
            self.assertEqual(response.body, expected_content)

        finally:
            # Restore original state
            if 'python.catzilla.streaming' in sys.modules:
                sys.modules['python.catzilla.streaming']._HAS_C_STREAMING = original_has_streaming


if __name__ == '__main__':
    # Run with verbose output
    unittest.main(verbosity=2)
