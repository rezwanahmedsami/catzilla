#!/usr/bin/env python3
"""
Catzilla Benchmark Server

High-performance server implementation using Catzilla framework
for performance benchmarking against other Python web frameworks.
"""

import sys
import os
import json
from urllib.parse import parse_qs

# Add the catzilla package to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'python'))

from catzilla.app import App
from catzilla.types import JSONResponse, HTMLResponse

# Import shared endpoints
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from shared_endpoints import get_benchmark_endpoints, DEFAULT_JSON_PAYLOAD


def create_catzilla_server():
    """Create and configure a Catzilla server with benchmark endpoints"""

    # Create app in production mode for optimal performance
    app = App(production=True)

    endpoints = get_benchmark_endpoints()

    # 1. Hello World - Simple text response
    @app.get("/")
    def hello_world(request):
        return "Hello, World!"

    # 2. JSON Response - Test JSON serialization
    @app.get("/json")
    def json_response(request):
        return endpoints["json_response"]["response"]

    # 3. Path Parameters - Test dynamic routing
    @app.get("/user/{id}")
    def user_by_id(request):
        user_id = request.path_params.get("id", "0")
        return endpoints["user_by_id"]["response_template"](user_id)

    # 4. JSON Echo - Test request parsing
    @app.post("/echo")
    def echo_json(request):
        try:
            # Parse JSON body
            data = json.loads(request.body) if request.body else {}
        except json.JSONDecodeError:
            data = {"error": "Invalid JSON"}

        return endpoints["echo_json"]["response_template"](data)

    # 5. Query Parameters - Test query string parsing
    @app.get("/users")
    def search_users(request):
        # Parse query parameters
        query_params = request.query_params if hasattr(request, 'query_params') else {}
        limit = query_params.get("limit", ["10"])[0] if isinstance(query_params.get("limit"), list) else query_params.get("limit", "10")
        offset = query_params.get("offset", ["0"])[0] if isinstance(query_params.get("offset"), list) else query_params.get("offset", "0")

        return endpoints["search_users"]["response_template"](limit, offset)

    # 6. Complex JSON - Test complex response generation
    @app.get("/user/{id}/profile")
    def user_profile(request):
        user_id = request.path_params.get("id", "0")
        return endpoints["user_profile"]["response_template"](user_id)

    # Add health check endpoint
    @app.get("/health")
    def health_check(request):
        return {"status": "healthy", "framework": "catzilla"}

    return app


def main():
    """Start the Catzilla benchmark server"""
    import argparse

    parser = argparse.ArgumentParser(description="Catzilla Benchmark Server")
    parser.add_argument("--port", type=int, default=8000, help="Port to run server on")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind to")
    args = parser.parse_args()

    app = create_catzilla_server()

    print(f"🚀 Starting Catzilla benchmark server on {args.host}:{args.port}")
    print("Available endpoints:")
    print("  GET  /              - Hello World")
    print("  GET  /json          - JSON Response")
    print("  GET  /user/{id}     - Path Parameters")
    print("  POST /echo          - JSON Echo")
    print("  GET  /users         - Query Parameters")
    print("  GET  /user/{id}/profile - Complex JSON")
    print("  GET  /health        - Health Check")
    print()

    try:
        app.listen(args.port, args.host)
    except KeyboardInterrupt:
        print("\n👋 Catzilla benchmark server stopped")


if __name__ == "__main__":
    main()
