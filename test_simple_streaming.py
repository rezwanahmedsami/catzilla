#!/usr/bin/env python3
"""
Simple Catzilla streaming server test.
"""

import sys
sys.path.insert(0, 'python')

from catzilla import Catzilla, StreamingResponse

app = Catzilla()

@app.get("/test")
def simple_test(request):
    return "Hello, World!"

@app.get("/stream-simple")
def simple_stream(request):
    def generate():
        yield "Data chunk 1\n"
        yield "Data chunk 2\n"
        yield "Data chunk 3\n"

    return StreamingResponse(generate(), content_type="text/plain")

if __name__ == "__main__":
    print("Starting simple streaming server...")
    print("Test endpoints:")
    print("  - http://localhost:8000/test (regular response)")
    print("  - http://localhost:8000/stream-simple (streaming response)")

    try:
        app.run(host="0.0.0.0", port=8000)
    except KeyboardInterrupt:
        print("\nServer stopped.")
