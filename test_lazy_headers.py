#!/usr/bin/env python3
"""
Test script to verify lazy header loading functionality
"""

from catzilla import Catzilla
import threading
import time
import requests

app = Catzilla()

@app.get("/test-headers")
def test_headers(request):
    """Test endpoint that uses get_header to access headers lazily"""
    # Test lazy header loading
    user_agent = request.get_header("User-Agent")
    content_type = request.get_header("Content-Type")
    custom_header = request.get_header("X-Custom-Header")

    return {
        "user_agent": user_agent,
        "content_type": content_type,
        "custom_header": custom_header,
        "message": "Headers extracted lazily"
    }

@app.get("/test-no-headers")
def test_no_headers(request):
    """Test endpoint that doesn't access headers to verify no overhead"""
    return {"message": "No headers accessed - should be fast"}

if __name__ == "__main__":
    # Start server in background
    server_thread = threading.Thread(target=lambda: app.listen(host="127.0.0.1", port=8000), daemon=True)
    server_thread.start()

    # Wait for server to start
    time.sleep(1)

    print("Testing lazy header loading...")

    # Test with headers
    response = requests.get("http://127.0.0.1:8000/test-headers", headers={
        "User-Agent": "TestAgent/1.0",
        "Content-Type": "application/json",
        "X-Custom-Header": "CustomValue"
    })
    print("With headers:", response.json())

    # Test without header access
    response = requests.get("http://127.0.0.1:8000/test-no-headers")
    print("No headers:", response.json())

    print("Test completed successfully!")
