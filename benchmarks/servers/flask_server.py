#!/usr/bin/env python3
"""
Flask Benchmark Server

Flask server implementation for performance benchmarking
against Catzilla and other Python web frameworks.
"""

import sys
import os
import json
import time
from urllib.parse import parse_qs

# Import shared endpoints
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from shared_endpoints import get_benchmark_endpoints, DEFAULT_JSON_PAYLOAD

try:
    from flask import Flask, request, jsonify, Response
    from werkzeug.serving import make_server
    import gunicorn.app.base
except ImportError:
    print("❌ Flask not installed. Install with: pip install flask gunicorn")
    sys.exit(1)


def create_flask_server():
    """Create and configure a Flask server with benchmark endpoints"""

    app = Flask(__name__)
    app.config['JSON_SORT_KEYS'] = False  # Don't sort JSON keys for performance

    endpoints = get_benchmark_endpoints()

    # 1. Hello World - Simple text response
    @app.route("/")
    def hello_world():
        return "Hello, World!"

    # 2. JSON Response - Test JSON serialization
    @app.route("/json")
    def json_response():
        return jsonify(endpoints["json_response"]["response"])

    # 3. Path Parameters - Test dynamic routing
    @app.route("/user/<int:user_id>")
    def user_by_id(user_id):
        return jsonify(endpoints["user_by_id"]["response_template"](str(user_id)))

    # 4. JSON Echo - Test request parsing
    @app.route("/echo", methods=["POST"])
    def echo_json():
        try:
            data = request.get_json() or {}
        except Exception:
            data = {"error": "Invalid JSON"}

        return jsonify(endpoints["echo_json"]["response_template"](data))

    # 5. Query Parameters - Test query string parsing
    @app.route("/users")
    def search_users():
        limit = int(request.args.get("limit", 10))
        offset = int(request.args.get("offset", 0))
        return jsonify(endpoints["search_users"]["response_template"](limit, offset))

    # 6. Complex JSON - Test complex response generation
    @app.route("/user/<int:user_id>/profile")
    def user_profile(user_id):
        return jsonify(endpoints["user_profile"]["response_template"](str(user_id)))

    # Add health check endpoint
    @app.route("/health")
    def health_check():
        return jsonify({"status": "healthy", "framework": "flask"})

    return app


class GunicornApplication(gunicorn.app.base.BaseApplication):
    """Custom Gunicorn application to run Flask with specific config"""

    def __init__(self, app, options=None):
        self.options = options or {}
        self.application = app
        super().__init__()

    def load_config(self):
        for key, value in self.options.items():
            self.cfg.set(key.lower(), value)

    def load(self):
        return self.application


def main():
    """Start the Flask benchmark server"""
    import argparse

    parser = argparse.ArgumentParser(description="Flask Benchmark Server")
    parser.add_argument("--port", type=int, default=8002, help="Port to run server on")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind to")
    parser.add_argument("--workers", type=int, default=1, help="Number of worker processes")
    parser.add_argument("--use-gunicorn", action="store_true", help="Use Gunicorn instead of development server")
    args = parser.parse_args()

    app = create_flask_server()

    print(f"🚀 Starting Flask benchmark server on {args.host}:{args.port}")
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
        if args.use_gunicorn:
            # Use Gunicorn for better performance
            options = {
                'bind': f'{args.host}:{args.port}',
                'workers': args.workers,
                'worker_class': 'sync',
                'accesslog': None,  # Use 'accesslog' instead of 'access_log'
                'errorlog': '-',     # Use 'errorlog' instead of 'error_log'
                'loglevel': 'warning'  # Use 'loglevel' instead of 'log_level'
            }
            GunicornApplication(app, options).run()
        else:
            # Use Flask development server
            app.run(host=args.host, port=args.port, debug=False, threaded=True)
    except KeyboardInterrupt:
        print("\n👋 Flask benchmark server stopped")


if __name__ == "__main__":
    main()
