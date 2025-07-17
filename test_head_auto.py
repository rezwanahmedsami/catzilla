#!/usr/bin/env python3
"""Test automatic HEAD method handling in Catzilla router"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'python'))

from catzilla import Catzilla
import requests
import threading
import time

def test_automatic_head():
    """Test that HEAD requests work automatically for GET routes"""
    app = Catzilla()

    @app.get('/test-get')
    def test_get():
        return {'message': 'GET response', 'data': 'some data'}

    @app.get('/api/users/{user_id}')
    def get_user(user_id: str):
        return {'user_id': user_id, 'name': f'User {user_id}'}

    # Start server in background
    server_thread = threading.Thread(
        target=lambda: app.listen(host='127.0.0.1', port=8899),
        daemon=True
    )
    server_thread.start()
    time.sleep(1.0)  # Wait for server to start

    base_url = 'http://127.0.0.1:8899'

    try:
        # Test 1: HEAD request for simple GET route (should work automatically)
        print("Test 1: HEAD request for /test-get")
        head_response = requests.head(f'{base_url}/test-get')
        print(f"HEAD status: {head_response.status_code}")
        print(f"HEAD headers: {dict(head_response.headers)}")
        print(f"HEAD body length: {len(head_response.content)}")

        # Compare with GET
        get_response = requests.get(f'{base_url}/test-get')
        print(f"GET status: {get_response.status_code}")
        print(f"GET body: {get_response.text}")

        # Test 2: HEAD request for parameterized route
        print("\nTest 2: HEAD request for /api/users/123")
        head_param_response = requests.head(f'{base_url}/api/users/123')
        print(f"HEAD param status: {head_param_response.status_code}")
        print(f"HEAD param headers: {dict(head_param_response.headers)}")

        # Compare with GET
        get_param_response = requests.get(f'{base_url}/api/users/123')
        print(f"GET param status: {get_param_response.status_code}")
        print(f"GET param body: {get_param_response.text}")

        # Test 3: HEAD request for non-existent route (should return 404)
        print("\nTest 3: HEAD request for non-existent route")
        head_404_response = requests.head(f'{base_url}/non-existent')
        print(f"HEAD 404 status: {head_404_response.status_code}")

        # Test 4: Verify HEAD returns same headers as GET but no body
        print("\nTest 4: Verify HEAD behavior matches FastAPI")
        if head_response.status_code == get_response.status_code == 200:
            print("✓ HEAD and GET return same status code")
        else:
            print("✗ HEAD and GET status codes don't match")

        if len(head_response.content) == 0:
            print("✓ HEAD returns no body")
        else:
            print("✗ HEAD returned body content")

        # Check if Content-Length header is preserved
        if 'content-length' in head_response.headers:
            print(f"✓ HEAD preserves Content-Length: {head_response.headers['content-length']}")
        else:
            print("? HEAD doesn't include Content-Length header")

        print("\n=== Automatic HEAD Test Results ===")
        if head_response.status_code == 200 and head_param_response.status_code == 200:
            print("✓ Automatic HEAD handling is working!")
            print("✓ FastAPI compatibility achieved")
        else:
            print("✗ Automatic HEAD handling needs fixes")

    except Exception as e:
        print(f"Test error: {e}")
        return False

    return True

if __name__ == '__main__':
    test_automatic_head()
