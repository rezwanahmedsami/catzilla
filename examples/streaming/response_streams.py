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

from catzilla import Catzilla, Request, Response, JSONResponse, StreamingResponse
import asyncio
import json
import time
from typing import AsyncGenerator, Dict, Any, List
from datetime import datetime
import uuid

# Initialize Catzilla with streaming support
app = Catzilla(
    production=False,
    show_banner=True,
    log_requests=True,
    enable_streaming=True
)

# Active stream connections tracking
active_streams: Dict[str, Dict[str, Any]] = {}

def generate_realtime_data() -> AsyncGenerator[str, None]:
    """Generate real-time data stream"""
    count = 0
    while True:
        count += 1
        data = {
            "timestamp": datetime.now().isoformat(),
            "count": count,
            "value": count * 1.5,
            "status": "active",
            "random_data": f"data_{count}_{time.time()}"
        }

        # Format as JSON lines
        yield f"data: {json.dumps(data)}\n\n"

        # Wait before next update
        time.sleep(1)

        # Stop after 30 items for demo
        if count >= 30:
            yield f"data: {json.dumps({'status': 'completed', 'total_items': count})}\n\n"
            break

def generate_server_sent_events(stream_id: str) -> AsyncGenerator[str, None]:
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
        yield f"data: {json.dumps({
            'item': i + 1,
            'value': (i + 1) ** 2,
            'timestamp': datetime.now().isoformat(),
            'stream_id': stream_id
        })}\n\n"

        time.sleep(0.5)

    # Send completion event
    yield f"event: stream_end\n"
    yield f"data: {json.dumps({'message': 'Stream completed', 'total_items': 20})}\n\n"

def generate_large_dataset() -> AsyncGenerator[str, None]:
    """Generate large dataset for streaming"""
    yield '{"items": [\n'

    for i in range(10000):
        item = {
            "id": i + 1,
            "name": f"Item {i + 1}",
            "description": f"This is item number {i + 1} in our large dataset",
            "value": (i + 1) * 10,
            "category": f"category_{(i % 10) + 1}",
            "created_at": datetime.now().isoformat(),
            "metadata": {
                "index": i,
                "is_even": i % 2 == 0,
                "square": i ** 2
            }
        }

        # Add comma separator except for last item
        separator = "," if i < 9999 else ""
        yield f"  {json.dumps(item)}{separator}\n"

        # Yield control every 100 items to prevent blocking
        if i % 100 == 0:
            time.sleep(0.01)

    yield '], "total": 10000, "generated_at": "'
    yield datetime.now().isoformat()
    yield '"}'

def generate_log_stream() -> AsyncGenerator[str, None]:
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

def generate_file_content() -> AsyncGenerator[bytes, None]:
    """Generate large file content for streaming download"""
    # Generate a large text file
    chunk_size = 8192  # 8KB chunks
    total_chunks = 1000  # ~8MB total

    for i in range(total_chunks):
        # Generate chunk content
        content = f"Chunk {i + 1} of {total_chunks}\n" * 100
        content += f"Generated at: {datetime.now().isoformat()}\n"
        content += "=" * 80 + "\n"

        yield content.encode('utf-8')

        # Small delay to simulate file reading
        time.sleep(0.01)

@app.get("/")
def home(request: Request) -> Response:
    """Home endpoint with streaming info"""
    return JSONResponse({
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
            "realtime_data": "/stream/realtime",
            "server_sent_events": "/stream/sse",
            "large_dataset": "/stream/dataset",
            "log_stream": "/stream/logs",
            "file_download": "/stream/file"
        }
    })

@app.get("/stream/realtime")
def stream_realtime_data(request: Request) -> Response:
    """Stream real-time data"""
    stream_id = f"realtime_{int(time.time())}"

    # Track active stream
    active_streams[stream_id] = {
        "type": "realtime",
        "started_at": time.time(),
        "client_ip": request.client.host if hasattr(request, 'client') else "unknown"
    }

    def cleanup_stream():
        """Cleanup when stream ends"""
        if stream_id in active_streams:
            del active_streams[stream_id]

    return StreamingResponse(
        generate_realtime_data(),
        media_type="text/plain",
        headers={
            "X-Stream-ID": stream_id,
            "X-Stream-Type": "realtime",
            "Cache-Control": "no-cache",
            "Connection": "keep-alive"
        }
    )

@app.get("/stream/sse")
def stream_server_sent_events(request: Request) -> Response:
    """Stream server-sent events"""
    stream_id = f"sse_{uuid.uuid4().hex[:8]}"

    # Track active stream
    active_streams[stream_id] = {
        "type": "sse",
        "started_at": time.time(),
        "client_ip": request.client.host if hasattr(request, 'client') else "unknown"
    }

    return StreamingResponse(
        generate_server_sent_events(stream_id),
        media_type="text/event-stream",
        headers={
            "X-Stream-ID": stream_id,
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Cache-Control"
        }
    )

@app.get("/stream/dataset")
def stream_large_dataset(request: Request) -> Response:
    """Stream large JSON dataset"""
    stream_id = f"dataset_{int(time.time())}"

    # Track active stream
    active_streams[stream_id] = {
        "type": "dataset",
        "started_at": time.time(),
        "client_ip": request.client.host if hasattr(request, 'client') else "unknown"
    }

    return StreamingResponse(
        generate_large_dataset(),
        media_type="application/json",
        headers={
            "X-Stream-ID": stream_id,
            "X-Stream-Type": "dataset",
            "X-Total-Items": "10000",
            "Content-Disposition": "attachment; filename=large_dataset.json"
        }
    )

@app.get("/stream/logs")
def stream_logs(request: Request) -> Response:
    """Stream log entries"""
    stream_id = f"logs_{int(time.time())}"

    # Track active stream
    active_streams[stream_id] = {
        "type": "logs",
        "started_at": time.time(),
        "client_ip": request.client.host if hasattr(request, 'client') else "unknown"
    }

    return StreamingResponse(
        generate_log_stream(),
        media_type="application/x-ndjson",  # Newline delimited JSON
        headers={
            "X-Stream-ID": stream_id,
            "X-Stream-Type": "logs",
            "Content-Disposition": "attachment; filename=application_logs.jsonl"
        }
    )

@app.get("/stream/file")
def stream_file_download(request: Request) -> Response:
    """Stream large file download"""
    stream_id = f"file_{int(time.time())}"

    # Track active stream
    active_streams[stream_id] = {
        "type": "file",
        "started_at": time.time(),
        "client_ip": request.client.host if hasattr(request, 'client') else "unknown"
    }

    return StreamingResponse(
        generate_file_content(),
        media_type="application/octet-stream",
        headers={
            "X-Stream-ID": stream_id,
            "Content-Disposition": "attachment; filename=large_file.txt",
            "Content-Type": "text/plain",
            "X-Estimated-Size": "8MB"
        }
    )

@app.get("/stream/status")
def get_stream_status(request: Request) -> Response:
    """Get status of active streams"""
    current_time = time.time()

    stream_status = {}
    for stream_id, info in active_streams.items():
        stream_status[stream_id] = {
            **info,
            "duration_seconds": current_time - info["started_at"],
            "status": "active"
        }

    return JSONResponse({
        "active_streams": stream_status,
        "total_active": len(active_streams),
        "stream_types": {
            stream_type: len([s for s in active_streams.values() if s["type"] == stream_type])
            for stream_type in ["realtime", "sse", "dataset", "logs", "file"]
        }
    })

@app.get("/stream/test-client")
def get_streaming_test_client(request: Request) -> Response:
    """Get HTML test client for streaming endpoints"""
    html_content = """
<!DOCTYPE html>
<html>
<head>
    <title>Catzilla Streaming Test Client</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .container { max-width: 800px; margin: 0 auto; }
        .endpoint { margin: 20px 0; padding: 15px; border: 1px solid #ddd; border-radius: 5px; }
        .output { background: #f5f5f5; padding: 10px; height: 200px; overflow-y: scroll;
                 font-family: monospace; font-size: 12px; white-space: pre-wrap; }
        button { padding: 10px 15px; margin: 5px; background: #007bff; color: white;
                border: none; border-radius: 3px; cursor: pointer; }
        button:hover { background: #0056b3; }
        .status { margin: 10px 0; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🌪️ Catzilla Streaming Test Client</h1>

        <div class="endpoint">
            <h3>Server-Sent Events</h3>
            <button onclick="startSSE()">Start SSE Stream</button>
            <button onclick="stopSSE()">Stop SSE Stream</button>
            <div class="status" id="sse-status">Status: Disconnected</div>
            <div class="output" id="sse-output"></div>
        </div>

        <div class="endpoint">
            <h3>Real-time Data Stream</h3>
            <button onclick="startRealtime()">Start Real-time Stream</button>
            <button onclick="stopRealtime()">Stop Real-time Stream</button>
            <div class="status" id="realtime-status">Status: Disconnected</div>
            <div class="output" id="realtime-output"></div>
        </div>

        <div class="endpoint">
            <h3>Log Stream</h3>
            <button onclick="startLogs()">Start Log Stream</button>
            <button onclick="stopLogs()">Stop Log Stream</button>
            <div class="status" id="logs-status">Status: Disconnected</div>
            <div class="output" id="logs-output"></div>
        </div>
    </div>

    <script>
        let sseSource = null;
        let realtimeAbortController = null;
        let logsAbortController = null;

        function startSSE() {
            if (sseSource) {
                sseSource.close();
            }

            document.getElementById('sse-status').textContent = 'Status: Connecting...';
            document.getElementById('sse-output').textContent = '';

            sseSource = new EventSource('/stream/sse');

            sseSource.onopen = function() {
                document.getElementById('sse-status').textContent = 'Status: Connected';
            };

            sseSource.onmessage = function(event) {
                const output = document.getElementById('sse-output');
                output.textContent += 'Data: ' + event.data + '\\n';
                output.scrollTop = output.scrollHeight;
            };

            sseSource.addEventListener('stream_start', function(event) {
                const output = document.getElementById('sse-output');
                output.textContent += 'Stream Started: ' + event.data + '\\n';
            });

            sseSource.addEventListener('heartbeat', function(event) {
                const output = document.getElementById('sse-output');
                output.textContent += 'Heartbeat: ' + event.data + '\\n';
            });

            sseSource.addEventListener('stream_end', function(event) {
                const output = document.getElementById('sse-output');
                output.textContent += 'Stream Ended: ' + event.data + '\\n';
                document.getElementById('sse-status').textContent = 'Status: Completed';
            });

            sseSource.onerror = function() {
                document.getElementById('sse-status').textContent = 'Status: Error';
            };
        }

        function stopSSE() {
            if (sseSource) {
                sseSource.close();
                sseSource = null;
                document.getElementById('sse-status').textContent = 'Status: Disconnected';
            }
        }

        function startRealtime() {
            if (realtimeAbortController) {
                realtimeAbortController.abort();
            }

            realtimeAbortController = new AbortController();
            document.getElementById('realtime-status').textContent = 'Status: Connecting...';
            document.getElementById('realtime-output').textContent = '';

            fetch('/stream/realtime', { signal: realtimeAbortController.signal })
                .then(response => {
                    document.getElementById('realtime-status').textContent = 'Status: Connected';
                    return response.body.getReader();
                })
                .then(reader => {
                    function read() {
                        return reader.read().then(({ done, value }) => {
                            if (done) {
                                document.getElementById('realtime-status').textContent = 'Status: Completed';
                                return;
                            }

                            const text = new TextDecoder().decode(value);
                            const output = document.getElementById('realtime-output');
                            output.textContent += text;
                            output.scrollTop = output.scrollHeight;

                            return read();
                        });
                    }
                    return read();
                })
                .catch(error => {
                    if (error.name !== 'AbortError') {
                        document.getElementById('realtime-status').textContent = 'Status: Error';
                    }
                });
        }

        function stopRealtime() {
            if (realtimeAbortController) {
                realtimeAbortController.abort();
                realtimeAbortController = null;
                document.getElementById('realtime-status').textContent = 'Status: Disconnected';
            }
        }

        function startLogs() {
            if (logsAbortController) {
                logsAbortController.abort();
            }

            logsAbortController = new AbortController();
            document.getElementById('logs-status').textContent = 'Status: Connecting...';
            document.getElementById('logs-output').textContent = '';

            fetch('/stream/logs', { signal: logsAbortController.signal })
                .then(response => {
                    document.getElementById('logs-status').textContent = 'Status: Connected';
                    return response.body.getReader();
                })
                .then(reader => {
                    function read() {
                        return reader.read().then(({ done, value }) => {
                            if (done) {
                                document.getElementById('logs-status').textContent = 'Status: Completed';
                                return;
                            }

                            const text = new TextDecoder().decode(value);
                            const output = document.getElementById('logs-output');
                            output.textContent += text;
                            output.scrollTop = output.scrollHeight;

                            return read();
                        });
                    }
                    return read();
                })
                .catch(error => {
                    if (error.name !== 'AbortError') {
                        document.getElementById('logs-status').textContent = 'Status: Error';
                    }
                });
        }

        function stopLogs() {
            if (logsAbortController) {
                logsAbortController.abort();
                logsAbortController = null;
                document.getElementById('logs-status').textContent = 'Status: Disconnected';
            }
        }
    </script>
</body>
</html>
    """

    return Response(
        content=html_content,
        media_type="text/html",
        headers={"Cache-Control": "no-cache"}
    )

@app.get("/stream/examples")
def get_streaming_examples(request: Request) -> Response:
    """Get examples for testing streaming endpoints"""
    return JSONResponse({
        "streaming_examples": {
            "server_sent_events": {
                "url": "/stream/sse",
                "description": "Server-sent events stream",
                "media_type": "text/event-stream",
                "javascript_example": "const source = new EventSource('/stream/sse');"
            },
            "realtime_data": {
                "url": "/stream/realtime",
                "description": "Real-time data stream",
                "media_type": "text/plain",
                "curl_example": "curl -N http://localhost:8000/stream/realtime"
            },
            "large_dataset": {
                "url": "/stream/dataset",
                "description": "Large JSON dataset stream",
                "media_type": "application/json",
                "size": "10,000 items",
                "curl_example": "curl http://localhost:8000/stream/dataset > dataset.json"
            },
            "log_stream": {
                "url": "/stream/logs",
                "description": "Streaming log entries",
                "media_type": "application/x-ndjson",
                "curl_example": "curl -N http://localhost:8000/stream/logs"
            },
            "file_download": {
                "url": "/stream/file",
                "description": "Large file streaming download",
                "media_type": "application/octet-stream",
                "size": "~8MB",
                "curl_example": "curl http://localhost:8000/stream/file > large_file.txt"
            }
        },
        "test_client": {
            "url": "/stream/test-client",
            "description": "Interactive HTML test client for streaming"
        },
        "monitoring": {
            "stream_status": "/stream/status",
            "description": "Monitor active streams"
        }
    })

@app.get("/health")
def health_check(request: Request) -> Response:
    """Health check with streaming status"""
    return JSONResponse({
        "status": "healthy",
        "streaming": "enabled",
        "framework": "Catzilla v0.2.0",
        "active_streams": len(active_streams)
    })

if __name__ == "__main__":
    print("🚨 Starting Catzilla HTTP Streaming Example")
    print("📝 Available endpoints:")
    print("   GET  /                  - Home with streaming info")
    print("   GET  /stream/realtime   - Real-time data stream")
    print("   GET  /stream/sse        - Server-sent events stream")
    print("   GET  /stream/dataset    - Large JSON dataset stream")
    print("   GET  /stream/logs       - Log entries stream")
    print("   GET  /stream/file       - Large file streaming download")
    print("   GET  /stream/status     - Active streams status")
    print("   GET  /stream/test-client - Interactive HTML test client")
    print("   GET  /stream/examples   - Get example requests")
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
    print("   # Server-sent events in browser:")
    print("   Open http://localhost:8000/stream/test-client")
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
