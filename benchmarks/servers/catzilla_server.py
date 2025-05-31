#!/usr/bin/env python3
"""
Catzilla Benchmark Server

High-performance server implementation using Catzilla framework
for performance benchmarking against other Python web frameworks.

Features:
- Ultra-fast C-accelerated validation engine
- Auto-validation with BaseModel (FastAPI-style)
- Jemalloc memory optimization (Memory Revolution v0.2.0)
- Model validation performance testing
- Production-optimized configuration with Catzilla() class
"""

import sys
import os
import json
from urllib.parse import parse_qs
from typing import Optional, List, Dict

# Add the catzilla package to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'python'))

from catzilla import Catzilla
from catzilla.validation import BaseModel
from catzilla.types import JSONResponse, HTMLResponse

# Import shared endpoints
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from shared_endpoints import get_benchmark_endpoints, DEFAULT_JSON_PAYLOAD


# =====================================================
# BENCHMARK MODELS FOR AUTO-VALIDATION TESTING
# =====================================================

class BenchmarkUser(BaseModel):
    """User model for auto-validation benchmarks"""
    id: int
    name: str
    email: str
    age: Optional[int] = None
    is_active: bool = True
    tags: Optional[List[str]] = None
    metadata: Optional[Dict[str, str]] = None


class BenchmarkProduct(BaseModel):
    """Product model for validation with constraints"""
    name: str
    price: float
    category: str
    description: Optional[str] = None
    in_stock: bool = True
    variants: Optional[List[str]] = None


class SearchParams(BaseModel):
    """Search parameters for query validation"""
    query: str
    limit: int = 10
    offset: int = 0
    sort_by: str = "created_at"


def create_catzilla_server():
    """Create and configure a Catzilla server with benchmark endpoints"""

    # Create app in production mode with jemalloc for optimal performance
    app = Catzilla(
        production=True,
        use_jemalloc=True,           # Enable jemalloc for 30% less memory usage
        memory_profiling=False,      # Disable for benchmarks (small overhead)
        auto_memory_tuning=True      # Enable adaptive memory management
    )

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

    # =====================================================
    # AUTO-VALIDATION BENCHMARK ENDPOINTS
    # =====================================================

    # 7. User Model Validation - Test auto-validation with BaseModel
    @app.post("/validate/user")
    def validate_user(request):
        try:
            # Parse JSON body
            data = json.loads(request.body) if request.body else {}

            # Create and validate user model (this will use C-accelerated validation)
            user = BenchmarkUser(**data)
            validated_data = user.dict()

            return endpoints["validate_user"]["response_template"](validated_data)
        except Exception as e:
            return {"error": f"Validation failed: {str(e)}", "valid": False}

    # 8. Product Model Validation - Test validation with constraints
    @app.post("/validate/product")
    def validate_product(request):
        try:
            # Parse JSON body
            data = json.loads(request.body) if request.body else {}

            # Create and validate product model (with price constraints, etc.)
            product = BenchmarkProduct(**data)
            validated_data = product.dict()

            return endpoints["validate_product"]["response_template"](validated_data)
        except Exception as e:
            return {"error": f"Validation failed: {str(e)}", "valid": False}

    # 9. Query Parameter Validation - Test auto-validation of query params
    @app.get("/search/validate")
    def search_with_validation(request):
        try:
            # Extract query parameters
            query_params = request.query_params if hasattr(request, 'query_params') else {}

            # Build search params dict
            search_data = {
                "query": query_params.get("query", [""])[0] if isinstance(query_params.get("query"), list) else query_params.get("query", ""),
                "limit": int(query_params.get("limit", ["10"])[0] if isinstance(query_params.get("limit"), list) else query_params.get("limit", "10")),
                "offset": int(query_params.get("offset", ["0"])[0] if isinstance(query_params.get("offset"), list) else query_params.get("offset", "0")),
                "sort_by": query_params.get("sort_by", ["created_at"])[0] if isinstance(query_params.get("sort_by"), list) else query_params.get("sort_by", "created_at")
            }

            # Validate using SearchParams model
            params = SearchParams(**search_data)

            return endpoints["search_with_validation"]["response_template"](
                params.query, params.limit, params.offset, params.sort_by
            )
        except Exception as e:
            return {"error": f"Validation failed: {str(e)}", "valid": False}

    # Add health check endpoint
    @app.get("/health")
    def health_check(request):
        return {
            "status": "healthy",
            "framework": "catzilla",
            "features": {
                "jemalloc": app.has_jemalloc if hasattr(app, 'has_jemalloc') else False,
                "auto_validation": True,
                "c_acceleration": True
            }
        }

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
    print("📊 Benchmark Features Enabled:")
    print("  ⚡ C-accelerated validation engine")
    print("  🧠 Jemalloc memory optimization")
    print("  🚀 Auto-validation with BaseModel")
    print("  📈 Production performance optimizations")
    print()
    print("Available endpoints:")
    print("  GET  /              - Hello World")
    print("  GET  /json          - JSON Response")
    print("  GET  /user/{id}     - Path Parameters")
    print("  POST /echo          - JSON Echo")
    print("  GET  /users         - Query Parameters")
    print("  GET  /user/{id}/profile - Complex JSON")
    print("  POST /validate/user - Auto-Validation (User Model)")
    print("  POST /validate/product - Auto-Validation (Product Model)")
    print("  GET  /search/validate - Query Parameter Validation")
    print("  GET  /health        - Health Check")
    print()

    try:
        app.listen(args.port, args.host)
    except KeyboardInterrupt:
        print("\n👋 Catzilla benchmark server stopped")


if __name__ == "__main__":
    main()
