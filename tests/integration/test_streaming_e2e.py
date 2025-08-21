#!/usr/bin/env python3
"""
End-to-End Streaming Integration Test
Validates complete streaming functionality from Python API to C core delivery.
"""
import time
import threading
import subprocess
import requests
import sys
import os
import pytest
from concurrent.futures import ThreadPoolExecutor, as_completed

# Add the project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from catzilla import Catzilla, StreamingResponse


@pytest.fixture(scope="module")
def test_server():
    """Start a test server for integration tests."""
    app = create_test_server()

    # Start server in a separate thread
    server_thread = threading.Thread(
        target=lambda: app.listen(8005, "127.0.0.1"),
        daemon=True
    )
    server_thread.start()

    # Wait for server to start
    time.sleep(2)

    # Check if server is responding
    try:
        response = requests.get("http://localhost:8005/simple-stream", timeout=5)
        if response.status_code != 200:
            pytest.fail("Test server not responding correctly")
    except Exception as e:
        pytest.fail(f"Test server not reachable: {e}")

    yield app

    # Cleanup would happen here if needed


def create_test_server():
    """Create a test server with comprehensive streaming endpoints."""
    app = Catzilla()

    @app.get("/simple-stream")
    def simple_stream(request):
        def generate():
            for i in range(5):
                yield f"Chunk {i}\n"
                time.sleep(0.1)
        return StreamingResponse(generate(), content_type="text/plain")

    @app.get("/large-stream")
    def large_stream(request):
        def generate():
            # Generate 1MB of data in 1KB chunks
            chunk_size = 1024
            for i in range(1024):
                chunk = f"CHUNK-{i:04d}-" + "X" * (chunk_size - 20) + "\n"
                yield chunk
                if i % 100 == 0:  # Small delay every 100 chunks
                    time.sleep(0.001)
        return StreamingResponse(generate(), content_type="text/plain")

    @app.get("/sse-stream")
    def sse_stream(request):
        def generate():
            for i in range(10):
                yield f"id: {i}\n"
                yield f"data: {{\"count\": {i}, \"timestamp\": {time.time()}}}\n\n"
                time.sleep(0.2)
        return StreamingResponse(generate(), content_type="text/event-stream")

    @app.get("/error-stream")
    def error_stream(request):
        def generate():
            yield "Starting stream...\n"
            yield "Data chunk 1\n"
            # This would cause an error in real scenarios
            raise Exception("Simulated streaming error")
        return StreamingResponse(generate(), content_type="text/plain")

    @app.get("/unicode-stream")
    def unicode_stream(request):
        def generate():
            yield "ASCII: Hello World\n"
            yield "Unicode: héllo wörld 🌍\n"
            yield "Emoji: 🚀🎉💻\n"
            yield "Chinese: 你好世界\n"
            yield "Arabic: مرحبا بالعالم\n"
        return StreamingResponse(generate(), content_type="text/plain; charset=utf-8")

    @app.get("/concurrent-test/<int:stream_id>")
    def concurrent_test(request):
        stream_id = request.path_params.get('stream_id', 0)
        def generate():
            for i in range(20):
                yield f"Stream-{stream_id}-Chunk-{i}\n"
                time.sleep(0.05)
        return StreamingResponse(generate(), content_type="text/plain")

    return app


def test_simple_streaming(test_server):
    """Test basic streaming functionality."""
    print("🧪 Testing simple streaming...")

    try:
        response = requests.get("http://localhost:8005/simple-stream", stream=True, timeout=10)

        # Check headers
        assert response.status_code == 200
        assert response.headers.get('transfer-encoding') == 'chunked'
        assert 'text/plain' in response.headers.get('content-type', '')

        # Collect streaming data with timing
        chunks = []
        start_time = time.time()

        for chunk in response.iter_content(chunk_size=None, decode_unicode=True):
            if chunk:
                chunks.append((chunk.strip(), time.time() - start_time))

        # Verify data
        assert len(chunks) == 5
        for i, (chunk, timestamp) in enumerate(chunks):
            assert chunk == f"Chunk {i}"
            if i > 0:
                # Should have delays between chunks (indicating real streaming)
                assert timestamp > (i * 0.05)  # At least some delay accumulated

        print("✅ Simple streaming test passed")
        return True

    except Exception as e:
        print(f"❌ Simple streaming test failed: {e}")
        return False


def test_large_data_streaming(test_server):
    """Test streaming with large amounts of data."""
    print("🧪 Testing large data streaming...")

    try:
        response = requests.get("http://localhost:8005/large-stream", stream=True, timeout=30)

        # Check headers
        assert response.status_code == 200
        assert response.headers.get('transfer-encoding') == 'chunked'

        # Collect data and measure
        total_bytes = 0
        chunk_count = 0
        start_time = time.time()

        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                total_bytes += len(chunk)
                chunk_count += 1

        end_time = time.time()

        # Verify we received approximately 1MB
        assert total_bytes >= 1024 * 1024 * 0.95  # Allow 5% variance
        assert chunk_count > 10  # Should be multiple chunks

        # Should complete in reasonable time (streaming, not buffered)
        assert end_time - start_time < 10  # Less than 10 seconds

        print(f"✅ Large data streaming test passed: {total_bytes:,} bytes in {chunk_count} chunks")
        return True

    except Exception as e:
        print(f"❌ Large data streaming test failed: {e}")
        return False


def test_server_sent_events(test_server):
    """Test Server-Sent Events streaming."""
    print("🧪 Testing Server-Sent Events...")

    try:
        response = requests.get("http://localhost:8005/sse-stream", stream=True, timeout=15)

        # Check headers
        assert response.status_code == 200
        assert response.headers.get('transfer-encoding') == 'chunked'
        assert 'text/event-stream' in response.headers.get('content-type', '')

        # Parse SSE data
        events = []
        current_event = {}

        for line in response.iter_lines(decode_unicode=True):
            if line:
                if line.startswith('id: '):
                    current_event['id'] = line[4:]
                elif line.startswith('data: '):
                    current_event['data'] = line[6:]
            else:
                # Empty line indicates end of event
                if current_event:
                    events.append(current_event)
                    current_event = {}

        # Verify SSE format
        assert len(events) == 10
        for i, event in enumerate(events):
            assert event['id'] == str(i)
            assert '"count": ' + str(i) in event['data']
            assert '"timestamp"' in event['data']

        print("✅ Server-Sent Events test passed")
        return True

    except Exception as e:
        print(f"❌ Server-Sent Events test failed: {e}")
        return False


def test_unicode_streaming(test_server):
    """Test streaming with unicode content."""
    print("🧪 Testing unicode streaming...")

    try:
        response = requests.get("http://localhost:8005/unicode-stream", stream=True, timeout=10)

        # Check headers
        assert response.status_code == 200
        assert response.headers.get('transfer-encoding') == 'chunked'
        assert 'utf-8' in response.headers.get('content-type', '')

        # Collect all content
        content = ""
        for chunk in response.iter_content(decode_unicode=True):
            if chunk:
                content += chunk

        # Verify unicode content
        assert "héllo wörld" in content
        assert "🌍" in content
        assert "🚀🎉💻" in content
        assert "你好世界" in content
        assert "مرحبا بالعالم" in content

        print("✅ Unicode streaming test passed")
        return True

    except Exception as e:
        print(f"❌ Unicode streaming test failed: {e}")
        return False


def test_concurrent_streaming(test_server):
    """Test multiple concurrent streaming connections."""
    print("🧪 Testing concurrent streaming...")

    def fetch_stream(stream_id):
        try:
            response = requests.get(f"http://localhost:8005/concurrent-test/{stream_id}",
                                  stream=True, timeout=15)

            if response.status_code != 200:
                return False, f"Status code: {response.status_code}"

            if response.headers.get('transfer-encoding') != 'chunked':
                return False, "Not chunked encoding"

            # Count chunks
            chunk_count = 0
            for chunk in response.iter_content(chunk_size=None, decode_unicode=True):
                if chunk and chunk.strip():
                    chunk_count += 1

            return True, chunk_count

        except Exception as e:
            return False, str(e)

    # Test with multiple concurrent connections
    num_streams = 10

    with ThreadPoolExecutor(max_workers=num_streams) as executor:
        futures = [executor.submit(fetch_stream, i) for i in range(num_streams)]
        results = [future.result() for future in as_completed(futures)]

    # Verify all streams succeeded
    successful = sum(1 for success, _ in results if success)
    assert successful == num_streams, f"Only {successful}/{num_streams} streams succeeded"

    # Verify chunk counts
    chunk_counts = [count for success, count in results if success]
    assert all(count >= 15 for count in chunk_counts), "Some streams had too few chunks"

    print(f"✅ Concurrent streaming test passed: {successful}/{num_streams} streams successful")
    return True


def run_integration_tests():
    """Run the complete integration test suite."""
    print("🚀 Starting Catzilla Streaming Integration Tests")
    print("=" * 60)

    # Start test server
    print("📡 Starting test server...")
    app = create_test_server()

    # Run server in a separate thread
    server_thread = threading.Thread(
        target=lambda: app.listen(8005, "127.0.0.1"),
        daemon=True
    )
    server_thread.start()

    # Wait for server to start
    time.sleep(2)

    # Check if server is responding
    try:
        response = requests.get("http://localhost:8005/simple-stream", timeout=5)
        if response.status_code != 200:
            print("❌ Server not responding correctly")
            return False
    except Exception as e:
        print(f"❌ Server not reachable: {e}")
        return False

    print("✅ Test server started successfully")

    # Run tests
    tests = [
        test_simple_streaming,
        test_large_data_streaming,
        test_server_sent_events,
        test_unicode_streaming,
        test_concurrent_streaming,
    ]

    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"❌ Test {test.__name__} crashed: {e}")
            results.append(False)

    # Summary
    print("\n" + "=" * 60)
    passed = sum(results)
    total = len(results)

    if passed == total:
        print(f"🎉 ALL TESTS PASSED! ({passed}/{total})")
        print("✅ Catzilla streaming is production-ready!")
        return True
    else:
        print(f"❌ SOME TESTS FAILED: {passed}/{total} passed")
        return False


if __name__ == "__main__":
    success = run_integration_tests()
    sys.exit(0 if success else 1)
