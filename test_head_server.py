#!/usr/bin/env python3
"""Simple test server for HEAD method testing"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'python'))

from catzilla import Catzilla, Request

def main():
    app = Catzilla()

    @app.get('/test-get')
    def test_get(request: Request):
        return {'message': 'GET response', 'data': 'some data'}

    @app.get('/api/users/{user_id}')
    def get_user(request: Request):
        user_id = request.path_params.get('user_id', 'unknown')
        return {'user_id': user_id, 'name': f'User {user_id}'}

    print("Starting Catzilla test server...")
    print("Test HEAD requests with:")
    print("  curl -I http://127.0.0.1:8000/test-get")
    print("  curl -I http://127.0.0.1:8000/api/users/123")
    print("Compare with GET:")
    print("  curl http://127.0.0.1:8000/test-get")
    print("  curl http://127.0.0.1:8000/api/users/123")

    # Start server (will block)
    app.listen(host='127.0.0.1', port=8000)

if __name__ == '__main__':
    main()
