#!/usr/bin/env python3
"""
FastAPI Benchmark Server

FastAPI server implementation for performance benchmarking
against Catzilla and other Python web frameworks.
"""

import sys
import os
import json
import time
from typing import Dict, Any, Optional, List

# Import shared endpoints
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from shared_endpoints import get_benchmark_endpoints, DEFAULT_JSON_PAYLOAD

try:
    from fastapi import FastAPI, Request, HTTPException
    from fastapi.responses import JSONResponse as FastAPIJSONResponse, PlainTextResponse
    from pydantic import BaseModel
    import uvicorn
except ImportError:
    print("❌ FastAPI not installed. Install with: pip install fastapi uvicorn pydantic")
    sys.exit(1)


# =====================================================
# PYDANTIC MODELS FOR VALIDATION COMPARISON
# =====================================================

class FastAPIUser(BaseModel):
    """User model for FastAPI validation comparison"""
    id: int
    name: str
    email: str
    age: Optional[int] = None
    is_active: bool = True
    tags: Optional[List[str]] = None
    metadata: Optional[Dict[str, str]] = None


class FastAPIProduct(BaseModel):
    """Product model for FastAPI validation comparison"""
    name: str
    price: float
    category: str
    description: Optional[str] = None
    in_stock: bool = True
    variants: Optional[List[str]] = None


def create_fastapi_server():
    """Create and configure a FastAPI server with benchmark endpoints"""

    app = FastAPI(title="FastAPI Benchmark Server")
    endpoints = get_benchmark_endpoints()

    # 1. Hello World - Simple text response
    @app.get("/")
    async def hello_world():
        return PlainTextResponse("Hello, World!")

    # 2. JSON Response - Test JSON serialization
    @app.get("/json")
    async def json_response():
        return endpoints["json_response"]["response"]

    # 3. Path Parameters - Test dynamic routing
    @app.get("/user/{user_id}")
    async def user_by_id(user_id: int):
        return endpoints["user_by_id"]["response_template"](str(user_id))

    # 4. JSON Echo - Test request parsing
    @app.post("/echo")
    async def echo_json(request: Request):
        try:
            data = await request.json()
        except Exception:
            data = {"error": "Invalid JSON"}

        return endpoints["echo_json"]["response_template"](data)

    # 5. Query Parameters - Test query string parsing
    @app.get("/users")
    async def search_users(limit: int = 10, offset: int = 0):
        return endpoints["search_users"]["response_template"](limit, offset)

    # 6. Complex JSON - Test complex response generation
    @app.get("/user/{user_id}/profile")
    async def user_profile(user_id: int):
        return endpoints["user_profile"]["response_template"](str(user_id))

    # =====================================================
    # VALIDATION ENDPOINTS FOR COMPARISON WITH CATZILLA
    # =====================================================

    # 7. User Model Validation - Test Pydantic validation
    @app.post("/validate/user")
    async def validate_user(user: FastAPIUser):
        validated_data = user.dict()
        return endpoints["validate_user"]["response_template"](validated_data)

    # 8. Product Model Validation - Test Pydantic validation with constraints
    @app.post("/validate/product")
    async def validate_product(product: FastAPIProduct):
        validated_data = product.dict()
        return endpoints["validate_product"]["response_template"](validated_data)

    # 9. Query Parameter Validation - Test FastAPI query validation
    @app.get("/search/validate")
    async def search_with_validation(
        query: str,
        limit: int = 10,
        offset: int = 0,
        sort_by: str = "created_at"
    ):
        return endpoints["search_with_validation"]["response_template"](
            query, limit, offset, sort_by
        )

    # Add health check endpoint
    @app.get("/health")
    async def health_check():
        return {
            "status": "healthy",
            "framework": "fastapi",
            "features": {
                "pydantic_validation": True,
                "async_support": True
            }
        }

    return app


def main():
    """Start the FastAPI benchmark server"""
    import argparse

    parser = argparse.ArgumentParser(description="FastAPI Benchmark Server")
    parser.add_argument("--port", type=int, default=8001, help="Port to run server on")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind to")
    parser.add_argument("--workers", type=int, default=1, help="Number of worker processes")
    args = parser.parse_args()

    app = create_fastapi_server()

    print(f"🚀 Starting FastAPI benchmark server on {args.host}:{args.port}")
    print("📊 FastAPI Features:")
    print("  🐍 Pydantic validation")
    print("  ⚡ Async/await support")
    print("  📈 Production ASGI server")
    print()
    print("Available endpoints:")
    print("  GET  /              - Hello World")
    print("  GET  /json          - JSON Response")
    print("  GET  /user/{id}     - Path Parameters")
    print("  POST /echo          - JSON Echo")
    print("  GET  /users         - Query Parameters")
    print("  GET  /user/{id}/profile - Complex JSON")
    print("  POST /validate/user - Pydantic Validation (User Model)")
    print("  POST /validate/product - Pydantic Validation (Product Model)")
    print("  GET  /search/validate - Query Parameter Validation")
    print("  GET  /health        - Health Check")
    print()

    try:
        uvicorn.run(
            app,
            host=args.host,
            port=args.port,
            workers=args.workers,
            access_log=False,  # Disable access logs for better performance
            log_level="warning"  # Reduce logging overhead
        )
    except KeyboardInterrupt:
        print("\n👋 FastAPI benchmark server stopped")


if __name__ == "__main__":
    main()
