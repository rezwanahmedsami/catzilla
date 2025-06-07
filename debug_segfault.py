#!/usr/bin/env python3
"""
Debug script to isolate the segfault issue.
"""
import sys
import os
import time
import threading
import requests
from catzilla import Catzilla

def test_server():
    """Test basic server functionality"""
    print("🔧 Creating Catzilla instance...")

    # Create app with minimal configuration
    app = Catzilla(
        use_jemalloc=True,
        memory_profiling=True,
        auto_memory_tuning=True
    )

    @app.get("/")
    def hello(request):
        return {"message": "Hello World"}

    print("🔧 Starting server...")

    # Start server in a thread
    def run_server():
        try:
            app.listen(port=8000, host="127.0.0.1")
        except Exception as e:
            print(f"❌ Server exception: {e}")
            import traceback
            traceback.print_exc()

    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()

    # Wait for server to start
    print("🔧 Waiting for server to start...")
    time.sleep(2)

    print("🔧 Making test request...")
    try:
        response = requests.get("http://127.0.0.1:8000/", timeout=5)
        print(f"✅ Response: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ Request failed: {e}")
        import traceback
        traceback.print_exc()

    print("🔧 Test complete")

if __name__ == "__main__":
    test_server()
