#!/usr/bin/env python3
"""
E2E Test Server for Streaming Functionality

This server mirrors examples/streaming/ for E2E testing.
It provides streaming functionality to be tested via HTTP.
"""
import sys
import argparse
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from catzilla import Catzilla, StreamingResponse
import json
import time
from datetime import datetime
import uuid

# Initialize Catzilla for E2E testing
app = Catzilla(
    production=False,
    show_banner=False,
    log_requests=False
)

# Active stream connections tracking
active_streams = {}

def generate_simple_stream():
    """Generate simple streaming data"""
    for i in range(5):  # Reduced for faster testing
        yield f"Count: {i}, Timestamp: {datetime.now().isoformat()}\n"
        time.sleep(0.1)

def generate_json_stream():
    """Generate JSON stream"""
    for i in range(3):  # Reduced for faster testing
        data = {
            "id": i,
            "timestamp": time.time(),
            "value": i * 3.14159
        }
        yield json.dumps(data) + "\n"
        time.sleep(0.1)

def generate_sse_stream():
    """Generate server-sent events"""
    for i in range(3):  # Reduced for faster testing
        yield f"id: {i}\n"
        yield f"data: {{'count': {i}, 'timestamp': {time.time()}}}\n\n"
        time.sleep(0.1)

def generate_csv_stream():
    """Generate CSV data"""
    yield "id,name,value,timestamp\n"
    for i in range(3):  # Reduced for faster testing
        yield f"{i},item-{i},{i*10},{datetime.now().isoformat()}\n"
        time.sleep(0.1)

def generate_realtime_data():
    """Generate real-time data stream"""
    for i in range(3):  # Reduced for faster testing
        data = {
            "timestamp": datetime.now().isoformat(),
            "count": i + 1,
            "value": (i + 1) * 1.5,
            "status": "active"
        }
        yield f"{json.dumps(data)}\n"
        time.sleep(0.2)

    # Final message
    yield f'{{"status": "completed", "total_items": 3}}\n'

def generate_large_dataset():
    """Generate large dataset for streaming"""
    yield '{"items": [\n'

    for i in range(5):  # Reduced for faster testing
        item = {
            "id": i + 1,
            "name": f"Item {i + 1}",
            "value": (i + 1) * 10,
            "timestamp": datetime.now().isoformat()
        }

        separator = "," if i < 4 else ""
        yield f"  {json.dumps(item)}{separator}\n"
        time.sleep(0.05)

    yield f'], "total": 5, "generated_at": "{datetime.now().isoformat()}"}}'

def generate_file_content():
    """Generate file content for streaming download"""
    for i in range(3):  # Reduced for faster testing
        content = f"Chunk {i + 1} of 3\n" * 5
        content += f"Generated at: {datetime.now().isoformat()}\n"
        content += "=" * 40 + "\n"
        yield content.encode('utf-8')
        time.sleep(0.05)

# ============================================================================
# ROUTES
# ============================================================================

@app.get("/health")
def health_check(request):
    """Health check endpoint"""
    return json.dumps({
        "status": "healthy",
        "server": "streaming_e2e_test",
        "streaming": "enabled",
        "framework": "Catzilla v0.2.0",
        "active_streams": len(active_streams)
    })

@app.get("/")
def home(request):
    """Streaming test server info"""
    return json.dumps({
        "message": "Catzilla E2E Streaming Test Server",
        "features": [
            "Simple text streaming",
            "JSON streaming",
            "Server-sent events (SSE)",
            "CSV streaming",
            "Real-time data streams",
            "Large dataset streaming",
            "File streaming"
        ],
        "endpoints": [
            "GET /stream/simple",
            "GET /stream/json",
            "GET /stream/sse",
            "GET /stream/csv",
            "GET /stream/realtime",
            "GET /stream/dataset",
            "GET /stream/file",
            "GET /stream/status"
        ]
    }, indent=2)

@app.get("/stream/simple")
def stream_simple(request):
    """Simple text streaming"""
    stream_id = f"simple_{int(time.time())}"
    active_streams[stream_id] = {
        "type": "simple",
        "started_at": time.time()
    }

    return StreamingResponse(
        generate_simple_stream(),
        content_type="text/plain",
        headers={
            "X-Stream-ID": stream_id,
            "X-Stream-Type": "simple"
        }
    )

@app.get("/stream/json")
def stream_json(request):
    """JSON line streaming"""
    stream_id = f"json_{int(time.time())}"
    active_streams[stream_id] = {
        "type": "json",
        "started_at": time.time()
    }

    return StreamingResponse(
        generate_json_stream(),
        content_type="application/x-ndjson",
        headers={
            "X-Stream-ID": stream_id,
            "X-Stream-Type": "json"
        }
    )

@app.get("/stream/sse")
def stream_sse(request):
    """Server-sent events streaming"""
    stream_id = f"sse_{uuid.uuid4().hex[:8]}"
    active_streams[stream_id] = {
        "type": "sse",
        "started_at": time.time()
    }

    return StreamingResponse(
        generate_sse_stream(),
        content_type="text/event-stream",
        headers={
            "X-Stream-ID": stream_id,
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*"
        }
    )

@app.get("/stream/csv")
def stream_csv(request):
    """CSV streaming"""
    stream_id = f"csv_{int(time.time())}"
    active_streams[stream_id] = {
        "type": "csv",
        "started_at": time.time()
    }

    return StreamingResponse(
        generate_csv_stream(),
        content_type="text/csv",
        headers={
            "X-Stream-ID": stream_id,
            "Content-Disposition": "attachment; filename=data.csv"
        }
    )

@app.get("/stream/realtime")
def stream_realtime(request):
    """Real-time data streaming"""
    stream_id = f"realtime_{int(time.time())}"
    active_streams[stream_id] = {
        "type": "realtime",
        "started_at": time.time()
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

@app.get("/stream/dataset")
def stream_dataset(request):
    """Large dataset streaming"""
    stream_id = f"dataset_{int(time.time())}"
    active_streams[stream_id] = {
        "type": "dataset",
        "started_at": time.time()
    }

    return StreamingResponse(
        generate_large_dataset(),
        content_type="application/json",
        headers={
            "X-Stream-ID": stream_id,
            "X-Stream-Type": "dataset",
            "X-Total-Items": "5",
            "Content-Disposition": "attachment; filename=dataset.json"
        }
    )

@app.get("/stream/file")
def stream_file(request):
    """File streaming download"""
    stream_id = f"file_{int(time.time())}"
    active_streams[stream_id] = {
        "type": "file",
        "started_at": time.time()
    }

    return StreamingResponse(
        generate_file_content(),
        content_type="text/plain",
        headers={
            "X-Stream-ID": stream_id,
            "Content-Disposition": "attachment; filename=test_file.txt",
            "X-Estimated-Size": "1KB"
        }
    )

@app.get("/stream/status")
def stream_status(request):
    """Stream status information"""
    current_time = time.time()

    stream_status = {}
    for stream_id, info in active_streams.items():
        stream_status[stream_id] = {
            **info,
            "duration_seconds": current_time - info["started_at"],
            "status": "active"
        }

    return json.dumps({
        "active_streams": stream_status,
        "total_active": len(active_streams),
        "stream_types": {
            stream_type: len([s for s in active_streams.values() if s["type"] == stream_type])
            for stream_type in ["simple", "json", "sse", "csv", "realtime", "dataset", "file"]
        }
    }, indent=2)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Catzilla E2E Streaming Test Server")
    parser.add_argument("--port", type=int, default=8106, help="Port to run server on")
    parser.add_argument("--host", type=str, default="127.0.0.1", help="Host to bind to")

    args = parser.parse_args()

    print(f"🚀 Starting Catzilla E2E Streaming Test Server")
    print(f"📍 Server: http://{args.host}:{args.port}")
    print(f"🏥 Health: http://{args.host}:{args.port}/health")

    app.listen(port=args.port, host=args.host)
