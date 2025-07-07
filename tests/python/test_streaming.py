"""
Test cases for Catzilla's streaming response functionality.
"""
import unittest
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


if __name__ == '__main__':
    unittest.main()
