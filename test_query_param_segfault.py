#!/usr/bin/env python3
"""
Test script to isolate query parameter segfault
"""

import threading
import time
import requests
from catzilla import Catzilla, Query
import sys

app = Catzilla()

@app.get("/search")
def search(query: str = Query(...), limit: int = Query(10, ge=1, le=100)):
    """Search endpoint with query parameters that triggers segfault"""
    return {
        "query": query,
        "limit": limit,
        "results": ["python", "catzilla", "framework"]
    }

@app.get("/simple")
def simple():
    """Simple endpoint without query params"""
    return {"message": "hello"}

def start_server():
    """Start the server in a separate thread"""
    try:
        print("🚀 Starting server...")
        app.listen(8000, "127.0.0.1")
        app.server.loop.run()
    except Exception as e:
        print(f"❌ Server error: {e}")

def test_endpoints():
    """Test the endpoints"""
    time.sleep(0.5)  # Give server time to start

    try:
        print("🧪 Testing simple endpoint...")
        response = requests.get("http://127.0.0.1:8000/simple", timeout=5)
        print(f"✅ Simple endpoint: {response.status_code} - {response.text}")

        print("🧪 Testing search endpoint with query params...")
        response = requests.get("http://127.0.0.1:8000/search?query=python&limit=5", timeout=5)
        print(f"✅ Search endpoint: {response.status_code} - {response.text}")

    except Exception as e:
        print(f"❌ Test error: {e}")

    print("🛑 Test complete")

if __name__ == "__main__":
    print("🔧 Query Parameter Segfault Test")

    # Start server in background thread
    server_thread = threading.Thread(target=start_server, daemon=True)
    server_thread.start()

    # Run tests
    test_endpoints()
