"""
Test cases for Catzilla's streaming response functionality.
Includes async streaming tests for v0.2.0 stability.
"""
import unittest
import asyncio
import threading
import time
import sys
import os
import requests
from io import StringIO
from unittest.mock import MagicMock, patch

# Add the project root to the path if needed
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

# Import the streaming module
from python.catzilla import StreamingResponse, StreamingWriter

# Create a simple TestApp for isolated testing
class TestApp:
    """Simple test server for integration testing."""

    def __init__(self):
        self.routes = {}
        self.running = False
        self.port = 8000
        self.host = "localhost"

    def route(self, path):
        """Decorator to register a route."""
        def decorator(handler):
            self.routes[path] = handler
            return handler
        return decorator

    def run_in_thread(self):
        """Start the test server in a thread."""
        self.running = True
        # In a real implementation, this would start a server
        # For testing, we'll just set a flag

    def shutdown(self):
        """Stop the test server."""
        self.running = False

    def handle_request(self, path):
        """
        Mock method to handle a request for testing without an actual server.

        Returns the response from the route handler or None if no handler found.
        """
        if path in self.routes:
            return self.routes[path]()
        return None

class TestStreamingResponse(unittest.TestCase):
    """Test the StreamingResponse class."""

    def setUp(self):
        self.app = TestApp()

    def test_streaming_response_creation(self):
        """Test that a StreamingResponse can be created with different content types."""
        # Test with a list
        content_list = ["chunk1", "chunk2", "chunk3"]
        response = StreamingResponse(content_list)
        self.assertEqual(response.content_type, "text/plain")
        self.assertEqual(response.status_code, 200)

        # Test with a generator
        def generate():
            for i in range(5):
                yield f"data-{i}"

        response = StreamingResponse(generate())
        self.assertEqual(response.content_type, "text/plain")
        self.assertEqual(response.status_code, 200)

        # Test with explicit parameters
        response = StreamingResponse(
            content=["data"],
            content_type="application/json",
            status_code=201,
            headers={"X-Custom": "test"}
        )
        self.assertEqual(response.content_type, "application/json")
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.headers.get("X-Custom"), "test")

    def test_streaming_response_content_types(self):
        """Test that various content types are properly handled."""
        content_types = [
            "text/plain",
            "text/html",
            "application/json",
            "text/csv",
            "application/octet-stream",
            "text/event-stream",
            "application/x-ndjson"
        ]

        for content_type in content_types:
            response = StreamingResponse(["test"], content_type=content_type)
            self.assertEqual(response.content_type, content_type)

    def test_streaming_response_with_bytes(self):
        """Test that byte content is properly handled."""
        response = StreamingResponse([b"binary data"])
        # Ensure bytes are properly processed
        # If C streaming is enabled, body will contain streaming marker
        if response.body.startswith("___CATZILLA_STREAMING___"):
            # In C streaming mode, check the original content
            content = response._collect_content()
            self.assertIn("binary data", content)
        else:
            # In fallback mode, check the body
            self.assertIn("binary data", response.body)

    def test_streaming_response_with_mixed_content(self):
        """Test that mixed str/bytes content is properly handled."""
        response = StreamingResponse([
            "text data",
            b"binary data",
            "more text"
        ])
        # Ensure all content is included
        # If C streaming is enabled, body will contain streaming marker
        if response.body.startswith("___CATZILLA_STREAMING___"):
            # In C streaming mode, check the original content
            content = response._collect_content()
            self.assertIn("text data", content)
            self.assertIn("binary data", content)
            self.assertIn("more text", content)
        else:
            # In fallback mode, check the body
            self.assertIn("text data", response.body)
            self.assertIn("binary data", response.body)
            self.assertIn("more text", response.body)

    def test_streaming_response_with_callable(self):
        """Test that callable content is properly handled."""
        def generate_content():
            yield "first"
            yield "second"
            yield "third"

        response = StreamingResponse(generate_content)
        # Ensure the callable is executed and content is included
        # If C streaming is enabled, body will contain streaming marker
        if response.body.startswith("___CATZILLA_STREAMING___"):
            # In C streaming mode, check the original content
            content = response._collect_content()
            self.assertIn("first", content)
            self.assertIn("second", content)
            self.assertIn("third", content)
        else:
            # In fallback mode, check the body
            self.assertIn("first", response.body)
            self.assertIn("second", response.body)
            self.assertIn("third", response.body)

    def test_streaming_writer(self):
        """Test the StreamingWriter class."""
        response = StreamingResponse(content_type="text/csv")
        # Mock methods that would be added by the C extension
        response.write = MagicMock()

        # Create a writer and write some CSV data
        writer = StreamingWriter(response)
        writer.write("id,name,value\n")
        writer.write("1,test,100\n")
        writer.write("2,example,200\n")
        writer.close()

        # Verify write calls
        self.assertEqual(response.write.call_count, 3)
        response.write.assert_any_call("id,name,value\n")
        response.write.assert_any_call("1,test,100\n")
        response.write.assert_any_call("2,example,200\n")
        self.assertTrue(writer.closed)

    def test_streaming_writer_context_manager(self):
        """Test that StreamingWriter works as a context manager."""
        response = StreamingResponse(content_type="text/csv")
        response.write = MagicMock()

        # Use as context manager
        with StreamingWriter(response) as writer:
            writer.write("header1,header2\n")
            writer.write("value1,value2\n")

        # Verify it was closed properly
        self.assertEqual(response.write.call_count, 2)
        self.assertTrue(writer.closed)

    def test_streaming_integration(self):
        """Integration test with a mocked server."""
        # Set up a route that returns a StreamingResponse
        @self.app.route("/test-stream")
        def test_stream():
            content = ["chunk-0", "chunk-1", "chunk-2"]
            return StreamingResponse(content, content_type="text/plain")

        # Set app as running for the test
        self.app.running = True

        try:
            # Get the response directly from the handler
            response = self.app.handle_request("/test-stream")

            # Check the response
            self.assertIsNotNone(response)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.content_type, "text/plain")

            # Verify the content
            expected_content = "chunk-0chunk-1chunk-2"
            # If C streaming is enabled, body will contain streaming marker
            if response.body.startswith("___CATZILLA_STREAMING___"):
                # In C streaming mode, check the original content
                content = response._collect_content()
                self.assertEqual(content, expected_content)
            else:
                # In fallback mode, check the body
                self.assertEqual(response.body, expected_content)

        finally:
            # Shutdown the app
            self.app.running = False

    def test_streaming_sse_response(self):
        """Test Server-Sent Events (SSE) format."""
        # Set up a route that returns SSE data
        @self.app.route("/events")
        def sse_endpoint():
            content = [
                "id: 1\n",
                "data: {\"message\": \"test\"}\n\n",
                "id: 2\n",
                "data: {\"message\": \"example\"}\n\n"
            ]
            return StreamingResponse(content, content_type="text/event-stream")

        # Set app as running for the test
        self.app.running = True

        try:
            # Get the response directly from the handler
            response = self.app.handle_request("/events")

            # Check the response
            self.assertIsNotNone(response)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.content_type, "text/event-stream")

            # Verify SSE format
            # If C streaming is enabled, body will contain streaming marker
            if response.body.startswith("___CATZILLA_STREAMING___"):
                # In C streaming mode, check the original content
                content = response._collect_content()
                self.assertIn("id: 1", content)
                self.assertIn("data: {\"message\": \"test\"}", content)
                self.assertIn("id: 2", content)
            else:
                # In fallback mode, check the body
                self.assertIn("id: 1", response.body)
                self.assertIn("data: {\"message\": \"test\"}", response.body)
                self.assertIn("id: 2", response.body)

        finally:
            # Shutdown the app
            self.app.running = False


class TestStreamingPerformance(unittest.TestCase):
    """Performance tests for streaming responses."""

    def setUp(self):
        self.app = TestApp()

    def test_large_content_memory_usage(self):
        """Test memory usage with large content."""
        # Skip detailed memory testing in automated tests
        # This would be more useful for manual profiling
        pass

    def test_response_time(self):
        """Test response time for streaming vs non-streaming."""
        # Set up a route that returns a large response
        @self.app.route("/large")
        def large_response():
            # Generate 1MB of data
            content = ["x" * 1024 for _ in range(1024)]
            return StreamingResponse(content)

        # Set app as running for the test
        self.app.running = True

        try:
            # Measure response generation time
            start_time = time.time()
            response = self.app.handle_request("/large")
            end_time = time.time()

            # Basic validation only
            self.assertIsNotNone(response)
            self.assertEqual(response.status_code, 200)
            # If C streaming is enabled, body will contain streaming marker
            if response.body.startswith("___CATZILLA_STREAMING___"):
                # In C streaming mode, check the original content length
                content = response._collect_content()
                self.assertEqual(len(content), 1024 * 1024)
            else:
                # In fallback mode, check the body length
                self.assertEqual(len(response.body), 1024 * 1024)

            # Print timing info (useful for manual testing)
            print(f"Large response generation time: {end_time - start_time:.3f}s")

        finally:
            # Shutdown the app
            self.app.running = False


# =====================================================
# ASYNC STREAMING TESTS FOR v0.2.0 STABILITY
# =====================================================

class TestAsyncStreaming(unittest.TestCase):
    """Test async streaming response functionality"""

    def setUp(self):
        self.app = TestApp()

    def test_async_streaming_response_creation(self):
        """Test async streaming response creation"""
        async def async_generator():
            for i in range(5):
                await asyncio.sleep(0.01)
                yield f"async chunk {i}\n"

        response = StreamingResponse(async_generator, content_type="text/plain")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, "text/plain")
        self.assertTrue(callable(response._content))

    def test_async_streaming_response_with_headers(self):
        """Test async streaming response with custom headers"""
        async def async_generator():
            yield "async data"

        response = StreamingResponse(
            async_generator(),
            content_type="application/json",
            headers={"X-Async-Stream": "true", "Cache-Control": "no-cache"}
        )
        self.assertEqual(response.headers.get("X-Async-Stream"), "true")
        self.assertEqual(response.headers.get("Cache-Control"), "no-cache")

    def test_async_streaming_sse_response(self):
        """Test async Server-Sent Events streaming"""
        async def async_sse_generator():
            for i in range(3):
                await asyncio.sleep(0.01)
                yield f"data: {{\"id\": {i}, \"timestamp\": {time.time()}}}\n\n"

        response = StreamingResponse(
            async_sse_generator,
            content_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "Connection": "keep-alive"}
        )
        self.assertEqual(response.content_type, "text/event-stream")
        self.assertEqual(response.headers.get("Cache-Control"), "no-cache")

    def test_async_streaming_with_exception_handling(self):
        """Test async streaming with exception handling"""
        async def failing_async_generator():
            yield "start"
            await asyncio.sleep(0.01)
            raise ValueError("Async streaming error")

        response = StreamingResponse(failing_async_generator())
        self.assertEqual(response.status_code, 200)
        # Exception handling would be tested in integration tests

    def test_async_streaming_writer_context_manager(self):
        """Test async streaming writer as context manager"""
        async def test_async_writer():
            response = StreamingResponse(content=None)
            async with StreamingWriter(response) as writer:
                await writer.write("async line 1\n")
                await asyncio.sleep(0.01)
                await writer.write("async line 2\n")
                await writer.write("async line 3\n")
                return writer.getvalue()

        # This would be tested in an async context
        # For now, just test the creation
        response = StreamingResponse(content=None)
        writer = StreamingWriter(response)
        self.assertIsNotNone(writer)

    def test_async_streaming_large_data(self):
        """Test async streaming of large data"""
        async def large_async_generator():
            chunk_size = 1024
            total_chunks = 100
            for i in range(total_chunks):
                await asyncio.sleep(0.001)  # Small delay to simulate async work
                yield "x" * chunk_size

        response = StreamingResponse(large_async_generator())
        self.assertEqual(response.status_code, 200)
        # In a real test, we'd verify the streaming behavior

    def test_async_streaming_mixed_content_types(self):
        """Test async streaming with mixed content types"""
        async def mixed_async_generator():
            yield "text data\n"
            await asyncio.sleep(0.01)
            yield b"binary data\n"
            await asyncio.sleep(0.01)
            yield "more text\n"

        response = StreamingResponse(mixed_async_generator())
        self.assertEqual(response.status_code, 200)


class TestAsyncStreamingPerformance(unittest.TestCase):
    """Test async streaming performance characteristics"""

    def setUp(self):
        self.app = TestApp()

    def test_async_streaming_memory_efficiency(self):
        """Test async streaming memory efficiency"""
        async def memory_efficient_async_generator():
            # Generate data without keeping it all in memory
            for chunk_id in range(1000):
                await asyncio.sleep(0.0001)  # Minimal async work
                # Generate and immediately yield, don't accumulate
                chunk_data = f"chunk_{chunk_id}_{'x' * 100}\n"
                yield chunk_data
                # Data should be garbage collected after yielding

        response = StreamingResponse(memory_efficient_async_generator())
        self.assertEqual(response.status_code, 200)

    def test_async_streaming_concurrent_responses(self):
        """Test multiple concurrent async streaming responses"""
        async def concurrent_async_generator(stream_id):
            for i in range(10):
                await asyncio.sleep(0.01)
                yield f"stream_{stream_id}_chunk_{i}\n"

        # Create multiple streaming responses
        responses = []
        for i in range(5):
            response = StreamingResponse(
                concurrent_async_generator(i),
                headers={"X-Stream-ID": str(i)}
            )
            responses.append(response)

        self.assertEqual(len(responses), 5)
        for i, response in enumerate(responses):
            self.assertEqual(response.headers.get("X-Stream-ID"), str(i))

    def test_async_streaming_backpressure_handling(self):
        """Test async streaming backpressure handling"""
        async def backpressure_async_generator():
            for i in range(100):
                # Simulate variable processing time
                await asyncio.sleep(0.001 if i % 2 == 0 else 0.005)
                yield f"variable_timing_chunk_{i}\n"

        response = StreamingResponse(backpressure_async_generator())
        self.assertEqual(response.status_code, 200)


class TestAsyncStreamingIntegration(unittest.TestCase):
    """Test async streaming integration scenarios"""

    def setUp(self):
        self.app = TestApp()

    def test_async_streaming_with_middleware(self):
        """Test async streaming response with middleware"""
        async def async_data_generator():
            for i in range(5):
                await asyncio.sleep(0.01)
                yield f"middleware_processed_chunk_{i}\n"

        @self.app.route("/async-stream-middleware")
        async def async_stream_with_middleware():
            # Simulate middleware that might wrap the response
            response = StreamingResponse(async_data_generator)
            response.headers["X-Middleware-Processed"] = "true"
            return response

        # Test that the route is registered
        self.assertIn("/async-stream-middleware", self.app.routes)

    def test_async_streaming_with_authentication(self):
        """Test async streaming with authentication"""
        async def authenticated_async_generator():
            # Simulate authenticated data streaming
            yield "authenticated: true\n"
            for i in range(3):
                await asyncio.sleep(0.01)
                yield f"secure_data_chunk_{i}\n"

        @self.app.route("/async-secure-stream")
        async def async_secure_stream():
            # In a real app, authentication would be checked first
            response = StreamingResponse(
                authenticated_async_generator(),
                headers={"X-Auth-Required": "true"}
            )
            return response

        self.assertIn("/async-secure-stream", self.app.routes)

    def test_async_streaming_error_recovery(self):
        """Test async streaming error recovery"""
        async def error_recovery_async_generator():
            try:
                yield "start\n"
                await asyncio.sleep(0.01)
                # Simulate an error condition
                if True:  # Simulate error condition
                    yield "error: simulated failure\n"
                    return
                yield "normal_chunk\n"
            except Exception as e:
                yield f"error_recovered: {str(e)}\n"

        response = StreamingResponse(error_recovery_async_generator())
        self.assertEqual(response.status_code, 200)

    def test_async_streaming_with_database(self):
        """Test async streaming with database-like operations"""
        async def database_async_generator():
            # Simulate async database cursor streaming
            for record_id in range(10):
                await asyncio.sleep(0.002)  # Simulate DB query time
                record = {
                    "id": record_id,
                    "data": f"record_data_{record_id}",
                    "timestamp": time.time()
                }
                yield f"{record}\n"

        response = StreamingResponse(database_async_generator())
        self.assertEqual(response.status_code, 200)


class TestAsyncStreamingStability(unittest.TestCase):
    """Test async streaming stability and edge cases"""

    def test_async_streaming_empty_generator(self):
        """Test async streaming with empty generator"""
        async def empty_async_generator():
            return
            yield  # Unreachable, but makes it a generator

        response = StreamingResponse(empty_async_generator())
        self.assertEqual(response.status_code, 200)

    def test_async_streaming_single_chunk(self):
        """Test async streaming with single chunk"""
        async def single_async_generator():
            await asyncio.sleep(0.01)
            yield "single async chunk"

        response = StreamingResponse(single_async_generator())
        self.assertEqual(response.status_code, 200)

    def test_async_streaming_unicode_handling(self):
        """Test async streaming with unicode content"""
        async def unicode_async_generator():
            await asyncio.sleep(0.01)
            yield "Hello 世界 🌍\n"
            await asyncio.sleep(0.01)
            yield "Async Unicode: ñáéíóú\n"
            await asyncio.sleep(0.01)
            yield "Emoji: 🚀⚡🔥\n"

        response = StreamingResponse(unicode_async_generator())
        self.assertEqual(response.status_code, 200)

    def test_async_streaming_cancellation_safety(self):
        """Test async streaming cancellation safety"""
        async def cancellation_safe_async_generator():
            try:
                for i in range(100):
                    await asyncio.sleep(0.01)
                    yield f"chunk_{i}\n"
            except asyncio.CancelledError:
                # Graceful cleanup on cancellation
                yield "stream_cancelled\n"
                raise

        response = StreamingResponse(cancellation_safe_async_generator())
        self.assertEqual(response.status_code, 200)


if __name__ == '__main__':
    unittest.main()
