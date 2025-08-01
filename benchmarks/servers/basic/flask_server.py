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

# Import shared endpoints - use absolute path to avoid import issues
shared_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'shared'))
sys.path.insert(0, shared_dir)
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

    # =====================================================
    # FEATURE BENCHMARK ENDPOINTS
    # =====================================================

    # ROUTING FEATURES
    @app.route("/bench/routing/static")
    def routing_static():
        return jsonify({"message": "Static route response", "framework": "flask"})

    @app.route("/bench/routing/path/<int:item_id>")
    def routing_path_param(item_id):
        return jsonify({"item_id": item_id, "framework": "flask"})

    @app.route("/bench/routing/path/<category>/<int:item_id>")
    def routing_multiple_params(category, item_id):
        return jsonify({"category": category, "item_id": item_id, "framework": "flask"})

    @app.route("/bench/routing/query")
    def routing_query_params():
        limit = int(request.args.get("limit", 10))
        offset = int(request.args.get("offset", 0))
        sort = request.args.get("sort", "name")
        return jsonify({"limit": limit, "offset": offset, "sort": sort, "framework": "flask"})

    # VALIDATION FEATURES (manual validation - Flask doesn't have built-in validation)
    @app.route("/bench/validation/simple", methods=["POST"])
    def validation_simple():
        try:
            data = request.get_json() or {}
            # Manual validation for Flask
            required_fields = ["id", "name", "email"]
            for field in required_fields:
                if field not in data:
                    raise ValueError(f"Missing required field: {field}")

            # Simple type checking
            if not isinstance(data["id"], int):
                data["id"] = int(data["id"])

            return jsonify({
                "validated": True,
                "user": data,
                "framework": "flask",
                "validation_engine": "manual"
            })
        except Exception as e:
            return jsonify({
                "validated": False,
                "error": str(e),
                "framework": "flask",
                "validation_engine": "manual"
            })

    @app.route("/bench/validation/complex", methods=["POST"])
    def validation_complex():
        try:
            data = request.get_json() or {}
            # Manual validation for Flask
            required_fields = ["id", "name", "email"]
            for field in required_fields:
                if field not in data:
                    raise ValueError(f"Missing required field: {field}")

            # Simple type checking
            if not isinstance(data["id"], int):
                data["id"] = int(data["id"])

            return jsonify({
                "validated": True,
                "user": data,
                "validation_count": len(data.keys()),
                "framework": "flask",
                "validation_engine": "manual"
            })
        except Exception as e:
            return jsonify({
                "validated": False,
                "error": str(e),
                "framework": "flask",
                "validation_engine": "manual"
            })

    @app.route("/bench/validation/product", methods=["POST"])
    def validation_product():
        try:
            data = request.get_json() or {}
            # Manual validation for Flask
            required_fields = ["name", "price", "category"]
            for field in required_fields:
                if field not in data:
                    raise ValueError(f"Missing required field: {field}")

            # Type checking
            if not isinstance(data["price"], (int, float)):
                data["price"] = float(data["price"])

            return jsonify({
                "validated": True,
                "product": data,
                "framework": "flask",
                "validation_engine": "manual"
            })
        except Exception as e:
            return jsonify({
                "validated": False,
                "error": str(e),
                "framework": "flask",
                "validation_engine": "manual"
            })

    @app.route("/bench/validation/query")
    def validation_query_params():
        try:
            query = request.args.get("query", "")
            limit = int(request.args.get("limit", 10))
            offset = int(request.args.get("offset", 0))
            sort_by = request.args.get("sort_by", "created_at")

            # Basic validation
            if not query:
                raise ValueError("Query parameter is required")
            if limit < 1 or limit > 1000:
                raise ValueError("Limit must be between 1 and 1000")

            return jsonify({
                "validated": True,
                "query": query,
                "limit": limit,
                "offset": offset,
                "sort_by": sort_by,
                "framework": "flask",
                "validation_engine": "manual"
            })
        except Exception as e:
            return jsonify({
                "validated": False,
                "error": str(e),
                "framework": "flask",
                "validation_engine": "manual"
            })

    # DEPENDENCY INJECTION FEATURES (manual DI - Flask doesn't have built-in DI)
    @app.route("/bench/di/simple")
    def di_simple():
        return jsonify({
            "connection": "flask_connection_1",
            "query_result": {"sql": "SELECT 1", "result": "query_result_1"},
            "framework": "flask",
            "di_system": "manual"
        })

    @app.route("/bench/di/nested/<int:user_id>")
    def di_nested(user_id):
        return jsonify({
            "user": {"id": user_id, "name": f"User {user_id}", "email": f"user{user_id}@example.com"},
            "timestamp": time.time(),
            "framework": "flask",
            "di_system": "manual"
        })

    # BACKGROUND TASKS FEATURES (basic implementation - Flask doesn't have built-in background tasks)
    @app.route("/bench/background/simple", methods=["POST"])
    def background_simple():
        task_id = f"flask_task_{int(time.time() * 1000000)}"
        # In a real app, you'd use Celery or similar
        return jsonify({
            "task_id": task_id,
            "task_type": "simple",
            "created_at": time.time(),
            "framework": "flask",
            "background_system": "manual"
        })

    @app.route("/bench/background/stats")
    def background_stats():
        return jsonify({
            "stats": {
                "tasks_created": 0,
                "tasks_completed": 0,
                "active_tasks": 0
            },
            "framework": "flask",
            "background_system": "manual"
        })

    # FILE UPLOAD FEATURES
    @app.route("/bench/upload/simple", methods=["POST"])
    def upload_simple():
        # Check if file was uploaded
        uploaded_file = request.files.get('file') if request.files else None
        return jsonify({
            "upload_id": f"flask_upload_{int(time.time() * 1000000)}",
            "file_info": {
                "filename": uploaded_file.filename if uploaded_file else "test_file.txt",
                "content_type": uploaded_file.content_type if uploaded_file else "text/plain",
                "file_size": 1024,
                "processing_time": 0.001
            },
            "framework": "flask",
            "upload_system": "werkzeug"
        })

    @app.route("/bench/upload/stats")
    def upload_stats():
        return jsonify({
            "stats": {
                "files_uploaded": 0,
                "total_size": 0,
                "successful_uploads": 0
            },
            "framework": "flask",
            "upload_system": "werkzeug"
        })

    # STREAMING FEATURES
    @app.route("/bench/streaming/json")
    def streaming_json():
        count = int(request.args.get("count", 100))
        # Simple JSON response (Flask handles this)
        items = [{"id": i, "value": i * 2, "name": f"item_{i}"} for i in range(min(count, 1000))]
        return jsonify({
            "stream_type": "json",
            "count": len(items),
            "data": items,
            "framework": "flask"
        })

    @app.route("/bench/streaming/csv")
    def streaming_csv():
        count = int(request.args.get("count", 1000))

        def generate_csv():
            yield "id,name,value\n"
            for i in range(min(count, 10000)):
                yield f"{i},item_{i},{i * 2}\n"

        return Response(generate_csv(), mimetype='text/csv')

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
