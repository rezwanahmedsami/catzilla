"""
Catzilla Streaming Response Example

This example demonstrates how to use the StreamingResponse class to send streaming responses
to clients without using async/await syntax.
"""
import time
from catzilla import Catzilla, StreamingResponse, StreamingWriter

app = Catzilla()

# Simple text streaming example
@app.get("/stream")
def stream_endpoint(request):
    """Stream a simple counter as text/plain"""
    def generate_data():
        for i in range(10):
            yield f"Count: {i}\n"
            time.sleep(0.1)  # Add a small delay to see the streaming effect

    return StreamingResponse(generate_data(), content_type="text/plain")

# Server-sent events example
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

# Using the StreamingWriter (file-like interface)
@app.get("/writer")
def writer_endpoint(request):
    """Demonstrate using the file-like StreamingWriter interface"""
    response = StreamingResponse(
        content_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=data.csv"}
    )

    def write_csv(writer):
        # Write CSV header
        writer.write("id,name,value\n")

        # Stream rows one by one
        for i in range(100):
            writer.write(f"{i},item-{i},{i*10}\n")
            time.sleep(0.05)  # Small delay to demonstrate streaming

    # Use the context manager pattern
    with response.writer() as writer:
        write_csv(writer)

    return response

# JSON streaming example (one object per line)
@app.get("/json-stream")
def json_stream_endpoint(request):
    """Stream JSON objects, one per line"""
    import json
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

if __name__ == "__main__":
    print("Starting Catzilla streaming example server...")
    print("Available endpoints:")
    print("  - /stream      - Simple text streaming")
    print("  - /events      - Server-sent events")
    print("  - /writer      - StreamingWriter example (CSV)")
    print("  - /json-stream - Streaming JSON objects")
    app.listen(host="127.0.0.1", port=8000)
