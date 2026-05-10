#!/usr/bin/env python3
"""
BlackSheep Benchmark Server

BlackSheep server implementation for performance benchmarking
against Catzilla and other Python web frameworks.
"""

import argparse
import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'shared'))
from shared_endpoints import get_benchmark_endpoints

if sys.version_info < (3, 10):
    print("❌ BlackSheep benchmark server requires Python 3.10+.")
    sys.exit(1)

try:
    import uvicorn
    from blacksheep import Application, Request, get, json, post, text
    from blacksheep.server.responses import bad_request
except ImportError:
    print("❌ BlackSheep not installed. Install with: pip install blacksheep uvicorn (Python 3.10+)")
    sys.exit(1)


app = Application()
endpoints = get_benchmark_endpoints()


@get("/")
async def hello_world():
    return text("Hello, World!")


@get("/health")
async def health_check():
    return json({"status": "healthy", "framework": "blacksheep", "timestamp": time.time()})


@get("/json")
async def json_response():
    return json(endpoints["json_response"]["response"])


@get("/user/{user_id}")
async def user_by_id(user_id: int):
    return json(endpoints["user_by_id"]["response_template"](str(user_id)))


@post("/echo")
async def echo_json(request: Request):
    try:
        data = await request.json()
    except Exception:
        data = {"error": "Invalid JSON"}
    return json(endpoints["echo_json"]["response_template"](data))


@get("/users")
async def search_users(limit: int = 10, offset: int = 0):
    return json(endpoints["search_users"]["response_template"](limit, offset))


@get("/user/{user_id}/profile")
async def user_profile(user_id: int):
    return json(endpoints["user_profile"]["response_template"](str(user_id)))


@post("/validate/user")
async def validate_user(request: Request):
    try:
        data = await request.json()
        required_fields = ["id", "name", "email"]
        for field in required_fields:
            if field not in data:
                return bad_request(f"Missing required field: {field}")

        if not isinstance(data["id"], int):
            data["id"] = int(data["id"])

        return json(endpoints["validate_user"]["response_template"](data))
    except Exception as exc:
        return bad_request(str(exc))


@post("/validate/product")
async def validate_product(request: Request):
    try:
        data = await request.json()
        required_fields = ["name", "price", "category"]
        for field in required_fields:
            if field not in data:
                return bad_request(f"Missing required field: {field}")

        if not isinstance(data["price"], (int, float)):
            data["price"] = float(data["price"])
        if data["price"] <= 0:
            return bad_request("price must be a positive number")

        return json(endpoints["validate_product"]["response_template"](data))
    except Exception as exc:
        return bad_request(str(exc))


@get("/search/validate")
async def search_with_validation(query: str, limit: int = 10, offset: int = 0, sort_by: str = "created_at"):
    if not query:
        return bad_request("query parameter is required")
    if limit < 1 or limit > 100:
        return bad_request("limit must be between 1 and 100")
    if offset < 0:
        return bad_request("offset must be non-negative")

    return json(endpoints["search_with_validation"]["response_template"](query, limit, offset, sort_by))


def main() -> None:
    parser = argparse.ArgumentParser(description="BlackSheep Benchmark Server")
    parser.add_argument("--port", type=int, default=8500, help="Port to run server on")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind to")
    parser.add_argument("--workers", type=int, default=1, help="Number of worker processes")
    args = parser.parse_args()

    if args.workers != 1:
        print("⚠️  BlackSheep benchmark server currently runs as a single process when launched programmatically.")

    uvicorn.run(app, host=args.host, port=args.port, log_level="warning", access_log=False)


if __name__ == "__main__":
    main()