#!/usr/bin/env python3
"""
Sanic Benchmark Server

Sanic server implementation for performance benchmarking
against Catzilla and other Python web frameworks.
"""

import argparse
import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'shared'))
from shared_endpoints import get_benchmark_endpoints

try:
    from sanic import Sanic, response
except ImportError:
    print("❌ Sanic not installed. Install with: pip install sanic")
    sys.exit(1)


def create_sanic_server() -> Sanic:
    """Create and configure a Sanic server with benchmark endpoints."""
    app = Sanic("sanic_benchmark_server")
    endpoints = get_benchmark_endpoints()

    @app.get("/")
    async def hello_world(_request):
        return response.text("Hello, World!")

    @app.get("/health")
    async def health_check(_request):
        return response.json({"status": "healthy", "framework": "sanic", "timestamp": time.time()})

    @app.get("/json")
    async def json_response(_request):
        return response.json(endpoints["json_response"]["response"])

    @app.get("/user/<user_id:int>")
    async def user_by_id(_request, user_id: int):
        return response.json(endpoints["user_by_id"]["response_template"](str(user_id)))

    @app.post("/echo")
    async def echo_json(request):
        data = request.json or {}
        return response.json(endpoints["echo_json"]["response_template"](data))

    @app.get("/users")
    async def search_users(request):
        limit = int(request.args.get("limit", 10))
        offset = int(request.args.get("offset", 0))
        return response.json(endpoints["search_users"]["response_template"](limit, offset))

    @app.get("/user/<user_id:int>/profile")
    async def user_profile(_request, user_id: int):
        return response.json(endpoints["user_profile"]["response_template"](str(user_id)))

    @app.post("/validate/user")
    async def validate_user(request):
        try:
            data = request.json or {}
            required_fields = ["id", "name", "email"]
            for field in required_fields:
                if field not in data:
                    return response.json({"error": f"Missing required field: {field}"}, status=400)

            if not isinstance(data["id"], int):
                data["id"] = int(data["id"])

            return response.json(endpoints["validate_user"]["response_template"](data))
        except Exception as exc:
            return response.json({"error": str(exc)}, status=400)

    @app.post("/validate/product")
    async def validate_product(request):
        try:
            data = request.json or {}
            required_fields = ["name", "price", "category"]
            for field in required_fields:
                if field not in data:
                    return response.json({"error": f"Missing required field: {field}"}, status=400)

            if not isinstance(data["price"], (int, float)):
                data["price"] = float(data["price"])
            if data["price"] <= 0:
                return response.json({"error": "price must be a positive number"}, status=400)

            return response.json(endpoints["validate_product"]["response_template"](data))
        except Exception as exc:
            return response.json({"error": str(exc)}, status=400)

    @app.get("/search/validate")
    async def search_with_validation(request):
        try:
            query = request.args.get("query")
            if not query:
                return response.json({"error": "query parameter is required"}, status=400)

            limit = int(request.args.get("limit", 10))
            offset = int(request.args.get("offset", 0))
            sort_by = request.args.get("sort_by", "created_at")

            if limit < 1 or limit > 100:
                return response.json({"error": "limit must be between 1 and 100"}, status=400)
            if offset < 0:
                return response.json({"error": "offset must be non-negative"}, status=400)

            return response.json(
                endpoints["search_with_validation"]["response_template"](query, limit, offset, sort_by)
            )
        except Exception as exc:
            return response.json({"error": str(exc)}, status=400)

    return app


app = create_sanic_server()


def main() -> None:
    parser = argparse.ArgumentParser(description="Sanic Benchmark Server")
    parser.add_argument("--port", type=int, default=8400, help="Port to run server on")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind to")
    parser.add_argument("--workers", type=int, default=1, help="Number of worker processes")
    args = parser.parse_args()

    app.run(
        host=args.host,
        port=args.port,
        workers=args.workers,
        access_log=False,
        debug=False,
        auto_reload=False,
        single_process=args.workers == 1,
    )


if __name__ == "__main__":
    main()