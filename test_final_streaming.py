#!/usr/bin/env python3
"""
Final validation test for 100% perfect streaming
"""
import sys
import time
sys.path.insert(0, 'python')

from catzilla import Catzilla, StreamingResponse

app = Catzilla()

@app.get("/incremental")
def incremental_test(request):
    """Test with delays to show true incremental streaming"""
    def slow_generator():
        for i in range(5):
            yield f"Chunk {i} at {time.time()}\n"
            time.sleep(0.5)  # Half second delay between chunks

    return StreamingResponse(slow_generator(), content_type="text/plain")

@app.get("/large")
def large_test(request):
    """Test with larger data chunks"""
    def large_generator():
        for i in range(3):
            chunk = f"=== LARGE CHUNK {i} ===\n" + "x" * 1000 + f"\n=== END CHUNK {i} ===\n"
            yield chunk
            time.sleep(0.3)

    return StreamingResponse(large_generator(), content_type="text/plain")

if __name__ == "__main__":
    print("🚀 Starting FINAL streaming validation server...")
    print("📡 Incremental test: http://localhost:8003/incremental")
    print("📦 Large chunks test: http://localhost:8003/large")
    app.listen(8003, "0.0.0.0")
