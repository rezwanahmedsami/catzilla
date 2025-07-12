#!/usr/bin/env python3
"""
Test global middleware with actual HTTP requests
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'python'))

from catzilla import Catzilla
from catzilla.response import JSONResponse
import time
import threading
import requests

def test_global_middleware_http():
    """Test global middleware with real HTTP requests"""
    app = Catzilla(use_jemalloc=False, memory_profiling=False)

    execution_log = []

    # Register global pre-route middleware
    @app.middleware(priority=100, pre_route=True, name="global_auth")
    def global_auth_middleware(request):
        execution_log.append(f"🌍 GLOBAL AUTH: {request.method} {request.path}")
        print(f"🌍 Global auth middleware executing for {request.method} {request.path}")
        # Add custom header to prove global middleware ran
        request.custom_data = getattr(request, 'custom_data', {})
        request.custom_data['global_auth'] = 'passed'
        return None

    @app.middleware(priority=200, pre_route=True, name="global_logging")
    def global_logging_middleware(request):
        execution_log.append(f"🌍 GLOBAL LOG: {request.method} {request.path}")
        print(f"🌍 Global logging middleware executing for {request.method} {request.path}")
        return None

    # Register global post-route middleware
    @app.middleware(priority=300, pre_route=False, post_route=True, name="global_response_logger")
    def global_response_middleware(request, response):
        execution_log.append(f"🌍 GLOBAL RESPONSE: {request.method} {request.path} -> {response.status_code}")
        print(f"🌍 Global response middleware executing for {request.method} {request.path} -> {response.status_code}")
        # Add custom header to prove post-route middleware ran
        response.headers["X-Global-Middleware"] = "executed"
        return None

    # Per-route middleware for comparison
    def route_specific_middleware(request):
        execution_log.append(f"🎯 ROUTE SPECIFIC: {request.method} {request.path}")
        print(f"🎯 Route-specific middleware executing for {request.method} {request.path}")
        return None

    @app.get("/test", middleware=[route_specific_middleware])
    def test_route(request):
        execution_log.append(f"🎯 HANDLER: {request.method} {request.path}")
        print(f"🎯 Handler executing for {request.method} {request.path}")
        auth_status = getattr(request, 'custom_data', {}).get('global_auth', 'not_found')
        return JSONResponse({
            "message": "test response",
            "global_auth_passed": auth_status,
            "execution_log": execution_log.copy()
        })

    @app.get("/plain")
    def plain_route(request):
        execution_log.append(f"🎯 PLAIN HANDLER: {request.method} {request.path}")
        print(f"🎯 Plain handler executing for {request.method} {request.path}")
        return JSONResponse({
            "message": "plain response",
            "execution_log": execution_log.copy()
        })

    print("\n=== Starting Server for Global Middleware Test ===")

    # Start server in background
    def run_server():
        app.listen(host="127.0.0.1", port=8899)

    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()

    # Wait for server to start
    time.sleep(2)

    try:
        print("\n--- Test 1: Route with per-route middleware ---")
        execution_log.clear()

        response = requests.get("http://127.0.0.1:8899/test", timeout=5)
        print(f"Status: {response.status_code}")
        print(f"Headers: {dict(response.headers)}")

        if response.status_code == 200:
            data = response.json()
            print(f"Response: {data}")

            # Check if global middleware headers are present
            if "X-Global-Middleware" in response.headers:
                print("✅ Global post-route middleware executed (header found)")
            else:
                print("❌ Global post-route middleware NOT executed (header missing)")

            # Check execution log
            if "global_auth_passed" in data and data["global_auth_passed"] == "passed":
                print("✅ Global pre-route middleware executed (auth data found)")
            else:
                print("❌ Global pre-route middleware NOT executed (auth data missing)")

            print(f"Execution log: {data.get('execution_log', [])}")
        else:
            print(f"❌ Request failed with status {response.status_code}")

        print("\n--- Test 2: Route without per-route middleware ---")
        execution_log.clear()

        response = requests.get("http://127.0.0.1:8899/plain", timeout=5)
        print(f"Status: {response.status_code}")
        print(f"Headers: {dict(response.headers)}")

        if response.status_code == 200:
            data = response.json()
            print(f"Response: {data}")

            # Check if global middleware headers are present
            if "X-Global-Middleware" in response.headers:
                print("✅ Global middleware executed on route without per-route middleware")
            else:
                print("❌ Global middleware NOT executed on plain route")

            print(f"Execution log: {data.get('execution_log', [])}")
        else:
            print(f"❌ Request failed with status {response.status_code}")

    except Exception as e:
        print(f"❌ Test failed with exception: {e}")

    print(f"\n=== Global Middleware HTTP Test Complete ===")

if __name__ == "__main__":
    test_global_middleware_http()
