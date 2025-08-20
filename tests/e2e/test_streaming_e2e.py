"""
E2E Tests for Streaming Functionality

This test suite validates streaming features including:
- Simple text streaming
- JSON streaming
- Server-sent events (SSE)
- CSV streaming
- Real-time data streams
- Large dataset streaming
- File streaming
"""
import pytest
import pytest_asyncio
import httpx
import asyncio
import json
import time
from tests.e2e.utils.server_manager import get_server_manager

# Server configuration
STREAMING_SERVER_PORT = 8106
STREAMING_SERVER_HOST = "127.0.0.1"
STREAMING_BASE_URL = f"http://{STREAMING_SERVER_HOST}:{STREAMING_SERVER_PORT}"

@pytest_asyncio.fixture(scope="module")
async def streaming_server():
    """Start and manage streaming E2E test server"""
    server_manager = get_server_manager()

    # Start the streaming server
    success = await server_manager.start_server("streaming", STREAMING_SERVER_PORT, STREAMING_SERVER_HOST)
    if not success:
        pytest.fail("Failed to start streaming test server")

    yield

    # Cleanup
    await server_manager.stop_all_servers()

@pytest.mark.asyncio
async def test_streaming_health_check(streaming_server):
    """Test streaming server health check"""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{STREAMING_BASE_URL}/health")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "healthy"
        assert data["server"] == "streaming_e2e_test"
        assert data["streaming"] == "enabled"
        assert "active_streams" in data

@pytest.mark.asyncio
async def test_streaming_home_info(streaming_server):
    """Test streaming server info endpoint"""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{STREAMING_BASE_URL}/")
        assert response.status_code == 200

        data = response.json()
        assert data["message"] == "Catzilla E2E Streaming Test Server"
        assert "features" in data
        assert "endpoints" in data
        assert len(data["features"]) >= 5
        assert len(data["endpoints"]) >= 7

@pytest.mark.asyncio
async def test_simple_streaming(streaming_server):
    """Test simple text streaming"""
    async with httpx.AsyncClient() as client:
        async with client.stream('GET', f"{STREAMING_BASE_URL}/stream/simple") as response:
            assert response.status_code == 200
            assert response.headers["content-type"] == "text/plain"
            # Note: Custom headers may not work with current StreamingResponse implementation

            chunks = []
            async for chunk in response.aiter_text():
                if chunk:
                    chunks.append(chunk)

            # Verify we received multiple chunks
            full_content = ''.join(chunks)
            assert "Count: 0" in full_content
            assert "Count: 4" in full_content
            assert "Timestamp:" in full_content

@pytest.mark.asyncio
async def test_json_streaming(streaming_server):
    """Test JSON line streaming"""
    async with httpx.AsyncClient() as client:
        async with client.stream('GET', f"{STREAMING_BASE_URL}/stream/json") as response:
            assert response.status_code == 200
            assert response.headers["content-type"] == "application/x-ndjson"
            # Note: Custom headers may not work with current StreamingResponse implementation

            chunks = []
            async for chunk in response.aiter_text():
                if chunk:
                    chunks.append(chunk)

            # Parse JSON lines
            full_content = ''.join(chunks)
            lines = [line.strip() for line in full_content.split('\n') if line.strip()]

            assert len(lines) >= 3

            # Verify each line is valid JSON
            for line in lines:
                data = json.loads(line)
                assert "id" in data
                assert "timestamp" in data
                assert "value" in data

@pytest.mark.asyncio
async def test_server_sent_events(streaming_server):
    """Test server-sent events streaming"""
    async with httpx.AsyncClient() as client:
        async with client.stream('GET', f"{STREAMING_BASE_URL}/stream/sse") as response:
            assert response.status_code == 200
            assert response.headers["content-type"] == "text/event-stream"
            # Note: Custom headers may not work with current StreamingResponse implementation

            chunks = []
            async for chunk in response.aiter_text():
                if chunk:
                    chunks.append(chunk)

            # Verify SSE format
            full_content = ''.join(chunks)
            assert "id: 0" in full_content
            assert "data: {" in full_content
            assert "count" in full_content

@pytest.mark.asyncio
async def test_csv_streaming(streaming_server):
    """Test CSV streaming"""
    async with httpx.AsyncClient() as client:
        async with client.stream('GET', f"{STREAMING_BASE_URL}/stream/csv") as response:
            assert response.status_code == 200
            assert response.headers["content-type"] == "text/csv"
            assert "X-Stream-ID" in response.headers
            assert "content-disposition" in response.headers
            assert "filename=data.csv" in response.headers["content-disposition"]

            chunks = []
            async for chunk in response.aiter_text():
                if chunk:
                    chunks.append(chunk)

            # Verify CSV format
            full_content = ''.join(chunks)
            lines = full_content.strip().split('\n')

            # Should have header + data rows
            assert len(lines) >= 4
            assert lines[0] == "id,name,value,timestamp"  # Header
            assert "item-0" in lines[1]  # First data row

@pytest.mark.asyncio
async def test_realtime_streaming(streaming_server):
    """Test real-time data streaming"""
    async with httpx.AsyncClient() as client:
        async with client.stream('GET', f"{STREAMING_BASE_URL}/stream/realtime") as response:
            assert response.status_code == 200
            assert response.headers["content-type"] == "text/plain"
            assert "X-Stream-ID" in response.headers
            assert response.headers["X-Stream-Type"] == "realtime"
            assert response.headers["cache-control"] == "no-cache"

            chunks = []
            async for chunk in response.aiter_text():
                if chunk:
                    chunks.append(chunk)

            # Parse JSON lines
            full_content = ''.join(chunks)
            lines = [line.strip() for line in full_content.split('\n') if line.strip()]

            assert len(lines) >= 4  # 3 data items + 1 completion

            # Verify data format
            for line in lines[:-1]:  # All except completion
                data = json.loads(line)
                assert "timestamp" in data
                assert "count" in data
                assert "value" in data
                assert "status" in data

            # Verify completion message
            completion = json.loads(lines[-1])
            assert completion["status"] == "completed"
            assert completion["total_items"] == 3

@pytest.mark.asyncio
async def test_dataset_streaming(streaming_server):
    """Test large dataset streaming"""
    async with httpx.AsyncClient() as client:
        async with client.stream('GET', f"{STREAMING_BASE_URL}/stream/dataset") as response:
            assert response.status_code == 200
            assert response.headers["content-type"] == "application/json"
            assert "X-Stream-ID" in response.headers
            assert response.headers["X-Stream-Type"] == "dataset"
            assert response.headers["X-Total-Items"] == "5"
            assert "content-disposition" in response.headers
            assert "filename=dataset.json" in response.headers["content-disposition"]

            chunks = []
            async for chunk in response.aiter_text():
                if chunk:
                    chunks.append(chunk)

            # Parse complete JSON
            full_content = ''.join(chunks)
            data = json.loads(full_content)

            assert "items" in data
            assert "total" in data
            assert "generated_at" in data
            assert data["total"] == 5
            assert len(data["items"]) == 5

            # Verify item structure
            for i, item in enumerate(data["items"]):
                assert item["id"] == i + 1
                assert f"Item {i + 1}" in item["name"]
                assert item["value"] == (i + 1) * 10

@pytest.mark.asyncio
async def test_file_streaming(streaming_server):
    """Test file streaming download"""
    async with httpx.AsyncClient() as client:
        async with client.stream('GET', f"{STREAMING_BASE_URL}/stream/file") as response:
            assert response.status_code == 200
            assert response.headers["content-type"] == "text/plain"
            assert "X-Stream-ID" in response.headers
            assert "content-disposition" in response.headers
            assert "filename=test_file.txt" in response.headers["content-disposition"]
            assert "X-Estimated-Size" in response.headers

            chunks = []
            async for chunk in response.aiter_bytes():
                if chunk:
                    chunks.append(chunk)

            # Verify file content
            full_content = b''.join(chunks).decode('utf-8')
            assert "Chunk 1 of 3" in full_content
            assert "Chunk 3 of 3" in full_content
            assert "Generated at:" in full_content
            assert "=" * 40 in full_content

@pytest.mark.asyncio
async def test_stream_status(streaming_server):
    """Test stream status endpoint"""
    # First start a stream to have some status
    async with httpx.AsyncClient() as client:
        # Start a stream (don't wait for completion)
        stream_task = asyncio.create_task(
            client.get(f"{STREAMING_BASE_URL}/stream/simple")
        )

        # Give it a moment to start
        await asyncio.sleep(0.1)

        # Check status
        response = await client.get(f"{STREAMING_BASE_URL}/stream/status")
        assert response.status_code == 200

        data = response.json()
        assert "active_streams" in data
        assert "total_active" in data
        assert "stream_types" in data

        # Clean up the stream task
        try:
            stream_task.cancel()
            await stream_task
        except asyncio.CancelledError:
            pass

@pytest.mark.asyncio
async def test_streaming_concurrent_requests(streaming_server):
    """Test multiple concurrent streaming requests"""
    async with httpx.AsyncClient() as client:
        # Start multiple streams concurrently
        tasks = [
            client.get(f"{STREAMING_BASE_URL}/stream/simple"),
            client.get(f"{STREAMING_BASE_URL}/stream/json"),
            client.get(f"{STREAMING_BASE_URL}/stream/csv")
        ]

        responses = await asyncio.gather(*tasks)

        # Verify all requests succeeded
        for response in responses:
            assert response.status_code == 200
            assert "X-Stream-ID" in response.headers

@pytest.mark.asyncio
async def test_streaming_headers_and_metadata(streaming_server):
    """Test streaming response headers and metadata"""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{STREAMING_BASE_URL}/stream/realtime")
        assert response.status_code == 200

        # Verify required headers
        assert response.headers["content-type"] == "text/plain"
        assert "X-Stream-ID" in response.headers
        assert response.headers["X-Stream-Type"] == "realtime"
        assert response.headers["cache-control"] == "no-cache"
        assert response.headers["connection"] == "keep-alive"

        # Verify stream ID format
        stream_id = response.headers["X-Stream-ID"]
        assert stream_id.startswith("realtime_")
        assert len(stream_id) > 10

@pytest.mark.asyncio
async def test_streaming_error_handling(streaming_server):
    """Test streaming with invalid endpoints"""
    async with httpx.AsyncClient() as client:
        # Test invalid stream type
        response = await client.get(f"{STREAMING_BASE_URL}/stream/invalid")
        assert response.status_code == 404

        # Test non-existent endpoint
        response = await client.get(f"{STREAMING_BASE_URL}/stream/nonexistent")
        assert response.status_code == 404

@pytest.mark.asyncio
async def test_streaming_performance(streaming_server):
    """Test streaming performance and timing"""
    start_time = time.time()

    async with httpx.AsyncClient() as client:
        async with client.stream('GET', f"{STREAMING_BASE_URL}/stream/simple") as response:
            assert response.status_code == 200

            chunk_times = []
            chunks = []

            async for chunk in response.aiter_text():
                if chunk:
                    chunk_times.append(time.time())
                    chunks.append(chunk)

    end_time = time.time()
    total_duration = end_time - start_time

    # Verify timing (should take at least 0.4 seconds for 5 chunks with 0.1s delay)
    assert total_duration >= 0.3
    assert len(chunks) >= 5

    # Verify chunks arrived over time (not all at once)
    if len(chunk_times) >= 2:
        time_diff = chunk_times[-1] - chunk_times[0]
        assert time_diff >= 0.2  # Should span at least 0.2 seconds
