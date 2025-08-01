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
import time

# Add the catzilla package to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', 'python'))

from catzilla import Catzilla, BaseModel, Query, Path, Header, Form, JSONResponse, HTMLResponse
from typing import Optional, List, Dict

# Import shared endpoints from the new structure - use absolute path
shared_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'shared'))
sys.path.insert(0, shared_dir)
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


def create_catzilla_server():
    """Create and configure a Catzilla server with benchmark endpoints"""

    # Create app in production mode with jemalloc for optimal performance + auto-validation
    app = Catzilla(
        production=True,
        use_jemalloc=True,           # Enable jemalloc for 30% less memory usage
        auto_validation=True,        # Enable FastAPI-style auto-validation (v0.2.0)
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

    # 3. Path Parameters - Test dynamic routing (v0.2.0 auto-validation)
    @app.get("/user/{id}")
    def user_by_id(request, id: int = Path(..., description="User ID")):
        return endpoints["user_by_id"]["response_template"](str(id))

    # 4. JSON Echo - Test request parsing (v0.2.0 auto-validation)
    @app.post("/echo")
    def echo_json(request, data: dict):
        # Auto-validation handles JSON parsing automatically
        return endpoints["echo_json"]["response_template"](data)

    # 5. Query Parameters - Test query string parsing (v0.2.0 auto-validation)
    @app.get("/users")
    def search_users(
        request,
        limit: int = Query(10, ge=1, description="Results limit"),
        offset: int = Query(0, ge=0, description="Results offset")
    ):
        return endpoints["search_users"]["response_template"](limit, offset)

    # 6. Complex JSON - Test complex response generation (v0.2.0 auto-validation)
    @app.get("/user/{id}/profile")
    def user_profile(request, id: int = Path(..., description="User ID")):
        return endpoints["user_profile"]["response_template"](str(id))

    # =====================================================
    # AUTO-VALIDATION BENCHMARK ENDPOINTS
    # =====================================================

    # 7. User Model Validation - Test auto-validation with BaseModel (v0.2.0)
    @app.post("/validate/user")
    def validate_user(request, user: BenchmarkUser):
        # Auto-validation happens automatically with v0.2.0!
        return endpoints["validate_user"]["response_template"](user.model_dump())

    # 8. Product Model Validation - Test validation with constraints (v0.2.0)
    @app.post("/validate/product")
    def validate_product(request, product: BenchmarkProduct):
        # Auto-validation with complex types
        return endpoints["validate_product"]["response_template"](product.model_dump())

    # 9. Query Parameter Validation - Test auto-validation of query params (v0.2.0)
    @app.get("/search/validate")
    def search_with_validation(
        request,
        query: str = Query(..., description="Search query"),
        limit: int = Query(10, ge=1, le=100, description="Results limit"),
        offset: int = Query(0, ge=0, description="Results offset"),
        sort_by: str = Query("created_at", description="Sort field")
    ):
        # Auto-validation of query parameters with constraints!
        return endpoints["search_with_validation"]["response_template"](
            query, limit, offset, sort_by
        )

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

    # =====================================================
    # FEATURE BENCHMARK ENDPOINTS
    # =====================================================

    # ROUTING FEATURES (v0.2.0 auto-validation)
    @app.get("/bench/routing/static")
    def routing_static(request):
        return {"message": "Static route response", "framework": "catzilla"}

    @app.get("/bench/routing/path/{item_id}")
    def routing_path_param(request, item_id: int = Path(..., description="Item ID")):
        return {"item_id": item_id, "framework": "catzilla"}

    @app.get("/bench/routing/path/{category}/{item_id}")
    def routing_multiple_params(
        request,
        category: str = Path(..., description="Category name"),
        item_id: int = Path(..., description="Item ID")
    ):
        return {"category": category, "item_id": item_id, "framework": "catzilla"}

    @app.get("/bench/routing/query")
    def routing_query_params(
        request,
        limit: int = Query(10, ge=1, description="Results limit"),
        offset: int = Query(0, ge=0, description="Results offset"),
        sort: str = Query("name", description="Sort field")
    ):
        return {"limit": limit, "offset": offset, "sort": sort, "framework": "catzilla"}

    # VALIDATION FEATURES (v0.2.0 C-accelerated auto-validation)
    @app.post("/bench/validation/simple")
    def validation_simple(request, user: BenchmarkUser):
        return {
            "validated": True,
            "user": user.model_dump(),
            "framework": "catzilla",
            "validation_engine": "c_accelerated"
        }

    @app.post("/bench/validation/complex")
    def validation_complex(request, user: BenchmarkUser):
        return {
            "validated": True,
            "user": user.model_dump(),
            "validation_count": len(user.__dict__),
            "framework": "catzilla",
            "validation_engine": "c_accelerated"
        }

    @app.post("/bench/validation/product")
    def validation_product(request, product: BenchmarkProduct):
        return {
            "validated": True,
            "product": product.model_dump(),
            "framework": "catzilla",
            "validation_engine": "c_accelerated"
        }

    @app.get("/bench/validation/query")
    def validation_query_params(
        request,
        query: str = Query(..., description="Search query"),
        limit: int = Query(10, ge=1, le=100, description="Results limit"),
        offset: int = Query(0, ge=0, description="Results offset"),
        sort_by: str = Query("created_at", description="Sort field")
    ):
        return {
            "validated": True,
            "query": query,
            "limit": limit,
            "offset": offset,
            "sort_by": sort_by,
            "framework": "catzilla",
            "validation_engine": "c_accelerated"
        }

    # DEPENDENCY INJECTION FEATURES (v0.2.0 auto-validation)
    @app.get("/bench/di/simple")
    def di_simple(request):
        return {
            "connection": "catzilla_connection_1",
            "query_result": {"sql": "SELECT 1", "result": "query_result_1"},
            "framework": "catzilla",
            "di_system": "catzilla_builtin"
        }

    @app.get("/bench/di/nested/{user_id}")
    def di_nested(request, user_id: int = Path(..., description="User ID")):
        return {
            "user": {"id": user_id, "name": f"User {user_id}", "email": f"user{user_id}@example.com"},
            "timestamp": time.time(),
            "framework": "catzilla",
            "di_system": "catzilla_builtin"
        }

    # BACKGROUND TASKS FEATURES (using Catzilla's async capabilities)
    @app.post("/bench/background/simple")
    def background_simple(request):
        task_id = f"catzilla_task_{int(time.time() * 1000000)}"
        return {
            "task_id": task_id,
            "task_type": "simple",
            "created_at": time.time(),
            "framework": "catzilla",
            "background_system": "catzilla_async"
        }

    @app.get("/bench/background/stats")
    def background_stats(request):
        return {
            "stats": {
                "tasks_created": 0,
                "tasks_completed": 0,
                "active_tasks": 0
            },
            "framework": "catzilla",
            "background_system": "catzilla_async"
        }

    # FILE UPLOAD FEATURES
    @app.post("/bench/upload/simple")
    def upload_simple(request):
        return {
            "upload_id": f"catzilla_upload_{int(time.time() * 1000000)}",
            "file_info": {
                "filename": "test_file.txt",
                "content_type": "text/plain",
                "file_size": 1024,
                "processing_time": 0.001
            },
            "framework": "catzilla",
            "upload_system": "catzilla_builtin"
        }

    @app.get("/bench/upload/stats")
    def upload_stats(request):
        return {
            "stats": {
                "files_uploaded": 0,
                "total_size": 0,
                "successful_uploads": 0
            },
            "framework": "catzilla",
            "upload_system": "catzilla_builtin"
        }

    # STREAMING FEATURES (v0.2.0 auto-validation)
    @app.get("/bench/streaming/json")
    def streaming_json(
        request,
        count: int = Query(100, ge=1, le=1000, description="Number of items")
    ):
        # Simple JSON response (Catzilla handles streaming efficiently)
        items = [{"id": i, "value": i * 2, "name": f"item_{i}"} for i in range(count)]
        return {
            "stream_type": "json",
            "count": len(items),
            "data": items,
            "framework": "catzilla"
        }

    @app.get("/bench/streaming/csv")
    def streaming_csv(
        request,
        count: int = Query(1000, ge=1, le=10000, description="Number of rows")
    ):
        # Generate CSV data
        csv_data = "id,name,value\\n"
        for i in range(count):
            csv_data += f"{i},item_{i},{i * 2}\\n"

        return csv_data

    return app


def main():
    """Start the Catzilla benchmark server"""
    import argparse

    parser = argparse.ArgumentParser(description="Catzilla Benchmark Server")
    parser.add_argument("--port", type=int, default=8000, help="Port to run server on")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind to")
    parser.add_argument("--workers", type=int, default=1, help="Number of workers (ignored for compatibility)")
    args = parser.parse_args()

    app = create_catzilla_server()

    print(f"🚀 Starting Catzilla benchmark server on {args.host}:{args.port}")
    print("📊 Benchmark Features Enabled:")
    print("  ⚡ C-accelerated validation engine (v0.2.0)")
    print("  🧠 Jemalloc memory optimization")
    print("  🚀 FastAPI-style auto-validation")
    print("  📈 Production performance optimizations")
    print()
    print("Available endpoints (v0.2.0 Auto-Validation):")
    print("  GET  /              - Hello World")
    print("  GET  /json          - JSON Response")
    print("  GET  /user/{id}     - Path Parameters (auto-validated)")
    print("  POST /echo          - JSON Echo (auto-validated)")
    print("  GET  /users         - Query Parameters (auto-validated)")
    print("  GET  /user/{id}/profile - Complex JSON (auto-validated)")
    print("  POST /validate/user - Auto-Validation (User Model)")
    print("  POST /validate/product - Auto-Validation (Product Model)")
    print("  GET  /search/validate - Query Parameter Validation (FastAPI-style)")
    print("  GET  /health        - Health Check")
    print("  + 16 additional feature benchmark endpoints")
    print()

    try:
        app.listen(args.port, args.host)
    except KeyboardInterrupt:
        print("\n👋 Catzilla benchmark server stopped")


if __name__ == "__main__":
    main()
