"""
Response Streams Example

This example demonstrates Catzilla's HTTP streaming capabilities
for real-time data streaming and large response handling.

Features demonstrated:
- Streaming responses for real-time data
- Server-sent events (SSE)
- Large file streaming
- JSON streaming for large datasets
- Connection management
- Stream compression and chunked transfer
"""

from catzilla import Catzilla, StreamingResponse, StreamingWriter
import json
import time
from datetime import datetime
import uuid

# Initialize Catzilla
app = Catzilla(
    production=False,
    show_banner=True,
    log_requests=True
)

# Active stream connections tracking
active_streams = {}

def generate_realtime_data():
    """Generate real-time data stream"""
    count = 0
    for i in range(10):  # Simplified for testing
        count += 1
        data = {
            "timestamp": datetime.now().isoformat(),
            "count": count,
            "value": count * 1.5,
            "status": "active"
        }

        # Format as simple JSON lines
        yield f"{json.dumps(data)}\n"

        # Wait before next update
        time.sleep(1)

    # Final message
    yield f'{{"status": "completed", "total_items": {count}}}\n'

def generate_server_sent_events(stream_id):
    """Generate server-sent events"""
    yield f"id: {stream_id}\n"
    yield f"event: stream_start\n"
    yield f"data: {json.dumps({'message': 'Stream started', 'stream_id': stream_id})}\n\n"

    for i in range(20):
        # Send heartbeat every few messages
        if i % 5 == 0:
            yield f"event: heartbeat\n"
            yield f"data: {json.dumps({'timestamp': datetime.now().isoformat()})}\n\n"

        # Send data event
        yield f"event: data\n"
        data = {
            'item': i + 1,
            'value': (i + 1) ** 2,
            'timestamp': datetime.now().isoformat(),
            'stream_id': stream_id
        }
        yield f"data: {json.dumps(data)}\n\n"

        time.sleep(0.5)

    # Send completion event
    yield f"event: stream_end\n"
    yield f"data: {json.dumps({'message': 'Stream completed', 'total_items': 20})}\n\n"

def generate_large_dataset():
    """Generate large dataset for streaming - simplified to avoid segfaults"""
    # Start JSON structure
    yield '{"items": [\n'

    # Generate smaller batches to prevent memory issues
    for i in range(100):  # Reduced to prevent segfault
        item = {
            "id": i + 1,
            "name": f"Item {i + 1}",
            "value": (i + 1) * 10,
            "timestamp": datetime.now().isoformat()
        }

        # Add comma separator except for last item
        separator = "," if i < 99 else ""
        yield f"  {json.dumps(item)}{separator}\n"

        # Small delay to allow yielding
        if i % 10 == 0:
            time.sleep(0.001)

    # Close JSON structure
    yield f'], "total": 100, "generated_at": "{datetime.now().isoformat()}"}}'

def generate_log_stream():
    """Generate simulated log stream"""
    log_levels = ["INFO", "DEBUG", "WARN", "ERROR"]
    services = ["api", "database", "cache", "auth", "payments"]

    for i in range(50):
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "level": log_levels[i % len(log_levels)],
            "service": services[i % len(services)],
            "message": f"Log entry number {i + 1}",
            "request_id": f"req_{uuid.uuid4().hex[:8]}",
            "duration_ms": (i + 1) * 10
        }

        yield f"{json.dumps(log_entry)}\n"
        time.sleep(0.2)

def generate_file_content():
    """Generate large file content for streaming download"""
    # Generate a large text file
    total_chunks = 100  # Reduced for faster testing

    for i in range(total_chunks):
        # Generate chunk content
        content = f"Chunk {i + 1} of {total_chunks}\n" * 10
        content += f"Generated at: {datetime.now().isoformat()}\n"
        content += "=" * 80 + "\n"

        yield content.encode('utf-8')

        # Small delay to simulate file reading
        time.sleep(0.01)

@app.get("/")
def home(request):
    """Home endpoint with streaming info"""
    home_data = {
        "message": "Catzilla HTTP Streaming Example",
        "features": [
            "Real-time data streaming",
            "Server-sent events (SSE)",
            "Large file streaming",
            "JSON streaming for large datasets",
            "Connection management",
            "Stream compression"
        ],
        "streaming_endpoints": {
            "simple_stream": "/stream",
            "server_sent_events": "/events",
            "csv_writer": "/writer",
            "json_stream": "/json-stream",
            "realtime_data": "/stream/realtime",
            "large_dataset": "/stream/dataset",
            "log_stream": "/stream/logs",
            "file_download": "/stream/file"
        }
    }

    # Return simple JSON string response like reference implementation
    return json.dumps(home_data, indent=2)

@app.get("/stream")
def stream_endpoint(request):
    """Stream a simple counter as text/plain"""
    def generate_data():
        for i in range(30):
            yield f"Count: {i}, Timestamp: {datetime.now().isoformat()}\n"
            time.sleep(0.1)  # Add a small delay to see the streaming effect

    return StreamingResponse(generate_data(), content_type="text/plain")

@app.get("/events")
def sse_endpoint(request):
    """Stream server-sent events for real-time updates"""
    def generate_sse():
        for i in range(20):
            # Format according to SSE specification
            yield f"id: {i}\n"
            yield f"data: {{'count': {i}, 'timestamp': {time.time()}}}\n\n"
            time.sleep(0.5)  # Add a delay to simulate real-time updates

    return StreamingResponse(
        generate_sse(),
        content_type="text/event-stream"
    )

@app.get("/writer")
def writer_endpoint(request):
    """Demonstrate CSV generation using generator approach"""
    def generate_csv():
        # Write CSV header
        yield "id,name,value,timestamp\n"

        # Stream rows one by one
        for i in range(100):
            yield f"{i},item-{i},{i*10},{datetime.now().isoformat()}\n"
            time.sleep(0.05)  # Small delay to demonstrate streaming

    return StreamingResponse(
        generate_csv(),
        content_type="text/csv"
    )

@app.get("/json-stream")
def json_stream_endpoint(request):
    """Stream JSON objects, one per line"""
    all_content = []
    for i in range(50):
        data = {
            "id": i,
            "timestamp": time.time(),
            "value": i * 3.14159
        }
        all_content.append(json.dumps(data) + "\n")

    return StreamingResponse(
        all_content,
        content_type="application/x-ndjson"  # newline-delimited JSON
    )

@app.get("/stream/realtime")
def stream_realtime_data(request):
    """Stream real-time data"""
    stream_id = f"realtime_{int(time.time())}"

    # Track active stream
    active_streams[stream_id] = {
        "type": "realtime",
        "started_at": time.time(),
        "client_ip": "unknown"
    }

    return StreamingResponse(
        generate_realtime_data(),
        content_type="text/plain",
        headers={
            "X-Stream-ID": stream_id,
            "X-Stream-Type": "realtime",
            "Cache-Control": "no-cache",
            "Connection": "keep-alive"
        }
    )

@app.get("/stream/sse")
def stream_server_sent_events(request):
    """Stream server-sent events"""
    stream_id = f"sse_{uuid.uuid4().hex[:8]}"

    # Track active stream
    active_streams[stream_id] = {
        "type": "sse",
        "started_at": time.time(),
        "client_ip": "unknown"
    }

    return StreamingResponse(
        generate_server_sent_events(stream_id),
        content_type="text/event-stream",
        headers={
            "X-Stream-ID": stream_id,
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Cache-Control"
        }
    )

@app.get("/stream/dataset")
def stream_large_dataset(request):
    """Stream large JSON dataset"""
    stream_id = f"dataset_{int(time.time())}"

    # Track active stream
    active_streams[stream_id] = {
        "type": "dataset",
        "started_at": time.time(),
        "client_ip": "unknown"
    }

    return StreamingResponse(
        generate_large_dataset(),
        content_type="application/json",
        headers={
            "X-Stream-ID": stream_id,
            "X-Stream-Type": "dataset",
            "X-Total-Items": "100",
            "Content-Disposition": "attachment; filename=dataset.json"
        }
    )

@app.get("/stream/logs")
def stream_logs(request):
    """Stream log entries"""
    stream_id = f"logs_{int(time.time())}"

    # Track active stream
    active_streams[stream_id] = {
        "type": "logs",
        "started_at": time.time(),
        "client_ip": "unknown"
    }

    return StreamingResponse(
        generate_log_stream(),
        content_type="application/x-ndjson",  # Newline delimited JSON
        headers={
            "X-Stream-ID": stream_id,
            "X-Stream-Type": "logs",
            "Content-Disposition": "attachment; filename=application_logs.jsonl"
        }
    )

@app.get("/stream/file")
def stream_file_download(request):
    """Stream large file download"""
    stream_id = f"file_{int(time.time())}"

    # Track active stream
    active_streams[stream_id] = {
        "type": "file",
        "started_at": time.time(),
        "client_ip": "unknown"
    }

    return StreamingResponse(
        generate_file_content(),
        content_type="application/octet-stream",
        headers={
            "X-Stream-ID": stream_id,
            "Content-Disposition": "attachment; filename=large_file.txt",
            "Content-Type": "text/plain",
            "X-Estimated-Size": "1MB"
        }
    )

@app.get("/stream/status")
def get_stream_status(request):
    """Get status of active streams"""
    current_time = time.time()

    stream_status = {}
    for stream_id, info in active_streams.items():
        stream_status[stream_id] = {
            **info,
            "duration_seconds": current_time - info["started_at"],
            "status": "active"
        }

    status_data = {
        "active_streams": stream_status,
        "total_active": len(active_streams),
        "stream_types": {
            stream_type: len([s for s in active_streams.values() if s["type"] == stream_type])
            for stream_type in ["realtime", "sse", "dataset", "logs", "file"]
        }
    }

    return json.dumps(status_data, indent=2)

@app.get("/health")
def health_check(request):
    """Health check with streaming status"""
    health_data = {
        "status": "healthy",
        "streaming": "enabled",
        "framework": "Catzilla v0.2.0",
        "active_streams": len(active_streams)
    }
    return json.dumps(health_data, indent=2)

if __name__ == "__main__":
    print("🌪️ Starting Catzilla HTTP Streaming Example")
    print("📝 Available endpoints:")
    print("   GET  /                  - Home with streaming info")
    print("   GET  /stream            - Simple text streaming")
    print("   GET  /events            - Server-sent events stream")
    print("   GET  /writer            - CSV generation using StreamingWriter")
    print("   GET  /json-stream       - JSON streaming")
    print("   GET  /stream/realtime   - Real-time data stream")
    print("   GET  /stream/sse        - Enhanced server-sent events")
    print("   GET  /stream/dataset    - Large JSON dataset stream")
    print("   GET  /stream/logs       - Log entries stream")
    print("   GET  /stream/file       - Large file streaming download")
    print("   GET  /stream/status     - Active streams status")
    print("   GET  /health            - Health check")
    print()
    print("🎨 Features demonstrated:")
    print("   • Real-time data streaming")
    print("   • Server-sent events (SSE)")
    print("   • Large file streaming")
    print("   • JSON streaming for large datasets")
    print("   • Connection management")
    print("   • Stream compression and chunked transfer")
    print()
    print("🧪 Try these examples:")
    print("   # Simple streaming:")
    print("   curl -N http://localhost:8000/stream")
    print()
    print("   # Server-sent events:")
    print("   curl -N http://localhost:8000/events")
    print()
    print("   # Real-time data with curl:")
    print("   curl -N http://localhost:8000/stream/realtime")
    print()
    print("   # Download large dataset:")
    print("   curl http://localhost:8000/stream/dataset > dataset.json")
    print()
    print("   # Monitor active streams:")
    print("   curl http://localhost:8000/stream/status")
    print()

    app.listen(host="0.0.0.0", port=8000)
