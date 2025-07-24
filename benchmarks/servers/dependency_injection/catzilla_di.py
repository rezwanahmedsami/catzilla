#!/usr/bin/env python3
"""
Catzilla Dependency Injection Benchmark Server

This server demonstrates Catzilla's DI system performance with various
service configurations, scopes, and complex dependency graphs.

Based on the async_sqlalchemy_example.py with benchmark-focused scenarios.
"""

import sys
import os
import json
import time
import asyncio
from typing import Optional, Dict, Any

# Add the catzilla package to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', 'python'))

from catzilla import Catzilla, Request, Response, JSONResponse, BaseModel, Path, Query
from catzilla.dependency_injection import service, Depends, set_default_container

# Initialize Catzilla with DI enabled
app = Catzilla(
    enable_di=True,
    production=True,
    use_jemalloc=True,
    auto_validation=True,
    show_banner=False,
    log_requests=False
)

set_default_container(app.di_container)

print("🏗️ Catzilla Dependency Injection Benchmark Server")

# ============================================================================
# BENCHMARK DATA MODELS
# ============================================================================

class UserModel(BaseModel):
    """User model for DI benchmarks"""
    id: int
    name: str
    email: str
    created_at: Optional[str] = None

class ProductModel(BaseModel):
    """Product model for DI benchmarks"""
    id: int
    name: str
    price: float
    category: str

# ============================================================================
# SINGLETON SERVICES - Single instance per application
# ============================================================================

@service("benchmark_config", scope="singleton")
class BenchmarkConfig:
    """Configuration service - singleton scope"""

    def __init__(self):
        self.app_name = "Catzilla DI Benchmark"
        self.version = "1.0.0"
        self.database_url = "sqlite:///benchmark.db"
        self.cache_ttl = 300
        self.created_at = time.time()
        print(f"📋 BenchmarkConfig created at {self.created_at}")

    def get_database_config(self) -> Dict[str, Any]:
        return {
            "url": self.database_url,
            "pool_size": 10,
            "timeout": 30
        }

@service("benchmark_cache", scope="singleton")
class BenchmarkCache:
    """Cache service - singleton scope"""

    def __init__(self):
        self.cache = {}
        self.hit_count = 0
        self.miss_count = 0
        self.created_at = time.time()
        print(f"💾 BenchmarkCache created at {self.created_at}")

    async def get(self, key: str) -> Optional[Any]:
        await asyncio.sleep(0.001)  # Simulate async cache lookup
        if key in self.cache:
            self.hit_count += 1
            return self.cache[key]
        self.miss_count += 1
        return None

    async def set(self, key: str, value: Any) -> None:
        await asyncio.sleep(0.0005)  # Simulate async cache write
        self.cache[key] = value

    def get_stats(self) -> Dict[str, Any]:
        total = self.hit_count + self.miss_count
        hit_ratio = (self.hit_count / total) if total > 0 else 0
        return {
            "hits": self.hit_count,
            "misses": self.miss_count,
            "hit_ratio": round(hit_ratio, 3),
            "cache_size": len(self.cache)
        }

# ============================================================================
# REQUEST-SCOPED SERVICES - New instance per request
# ============================================================================

@service("benchmark_session", scope="request")
class BenchmarkSession:
    """Database session service - request scope"""

    def __init__(self, config: BenchmarkConfig = Depends("benchmark_config")):
        self.config = config
        self.session_id = f"session_{int(time.time() * 1000000)}"
        self.queries_executed = 0
        self.created_at = time.time()
        print(f"🔗 BenchmarkSession {self.session_id} created at {self.created_at}")

    async def execute_query(self, query: str) -> Dict[str, Any]:
        """Simulate async database query"""
        await asyncio.sleep(0.002)  # 2ms query time
        self.queries_executed += 1
        return {
            "query": query,
            "session_id": self.session_id,
            "execution_time": "2ms",
            "rows_affected": 1
        }

    def get_session_stats(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "queries_executed": self.queries_executed,
            "duration": round((time.time() - self.created_at) * 1000, 2)
        }

@service("benchmark_request_context", scope="request")
class BenchmarkRequestContext:
    """Request context service - request scope"""

    def __init__(self):
        self.request_id = f"req_{int(time.time() * 1000000)}"
        self.start_time = time.time()
        self.operations = []
        print(f"📝 RequestContext {self.request_id} created")

    def add_operation(self, operation: str, duration_ms: float = 0):
        self.operations.append({
            "operation": operation,
            "duration_ms": duration_ms,
            "timestamp": time.time()
        })

    def get_summary(self) -> Dict[str, Any]:
        total_duration = round((time.time() - self.start_time) * 1000, 2)
        return {
            "request_id": self.request_id,
            "total_duration_ms": total_duration,
            "operations_count": len(self.operations),
            "operations": self.operations
        }

# ============================================================================
# TRANSIENT SERVICES - New instance per injection
# ============================================================================

@service("benchmark_logger", scope="transient")
class BenchmarkLogger:
    """Logger service - transient scope"""

    def __init__(self, context: BenchmarkRequestContext = Depends("benchmark_request_context")):
        self.context = context
        self.logger_id = f"logger_{int(time.time() * 1000000)}"
        self.log_count = 0
        print(f"📊 BenchmarkLogger {self.logger_id} created")

    async def log(self, level: str, message: str) -> None:
        await asyncio.sleep(0.0001)  # 0.1ms log write
        self.log_count += 1
        self.context.add_operation(f"log_{level}", 0.1)

# ============================================================================
# REPOSITORY SERVICES WITH COMPLEX DEPENDENCIES
# ============================================================================

@service("user_repository", scope="singleton")
class UserRepository:
    """User repository with multiple dependencies"""

    def __init__(self,
                 config: BenchmarkConfig = Depends("benchmark_config"),
                 cache: BenchmarkCache = Depends("benchmark_cache")):
        self.config = config
        self.cache = cache
        self.repository_id = f"user_repo_{int(time.time() * 1000)}"
        print(f"👥 UserRepository {self.repository_id} created")

    async def get_user(self,
                       user_id: int,
                       session: BenchmarkSession = Depends("benchmark_session"),
                       logger: BenchmarkLogger = Depends("benchmark_logger")) -> Dict[str, Any]:

        # Check cache first
        cache_key = f"user_{user_id}"
        cached_user = await self.cache.get(cache_key)

        if cached_user:
            await logger.log("info", f"User {user_id} found in cache")
            return cached_user

        # Simulate database lookup
        await logger.log("info", f"Looking up user {user_id} in database")
        query_result = await session.execute_query(f"SELECT * FROM users WHERE id = {user_id}")

        user_data = {
            "id": user_id,
            "name": f"User {user_id}",
            "email": f"user{user_id}@example.com",
            "created_at": time.time(),
            "repository_id": self.repository_id
        }

        # Cache the result
        await self.cache.set(cache_key, user_data)
        await logger.log("info", f"User {user_id} cached")

        return user_data

    async def create_user(self,
                          user_data: UserModel,
                          session: BenchmarkSession = Depends("benchmark_session"),
                          logger: BenchmarkLogger = Depends("benchmark_logger")) -> Dict[str, Any]:

        await logger.log("info", f"Creating user {user_data.name}")

        # Simulate user creation
        query_result = await session.execute_query(
            f"INSERT INTO users (name, email) VALUES ('{user_data.name}', '{user_data.email}')"
        )

        created_user = {
            **user_data.model_dump(),
            "created_at": time.time(),
            "repository_id": self.repository_id
        }

        # Clear cache to maintain consistency
        await self.cache.set(f"user_{user_data.id}", created_user)
        await logger.log("info", f"User {user_data.id} created and cached")

        return created_user

@service("product_repository", scope="singleton")
class ProductRepository:
    """Product repository for DI benchmarks"""

    def __init__(self,
                 config: BenchmarkConfig = Depends("benchmark_config"),
                 cache: BenchmarkCache = Depends("benchmark_cache")):
        self.config = config
        self.cache = cache
        self.repository_id = f"product_repo_{int(time.time() * 1000)}"
        print(f"🛍️ ProductRepository {self.repository_id} created")

    async def get_products(self,
                           category: str = "all",
                           session: BenchmarkSession = Depends("benchmark_session"),
                           logger: BenchmarkLogger = Depends("benchmark_logger")) -> Dict[str, Any]:

        cache_key = f"products_{category}"
        cached_products = await self.cache.get(cache_key)

        if cached_products:
            await logger.log("info", f"Products for {category} found in cache")
            return cached_products

        await logger.log("info", f"Fetching products for category: {category}")
        query_result = await session.execute_query(f"SELECT * FROM products WHERE category = '{category}'")

        products = [
            {"id": i, "name": f"Product {i}", "price": 99.99, "category": category}
            for i in range(1, 6)
        ]

        result = {
            "products": products,
            "category": category,
            "count": len(products),
            "repository_id": self.repository_id
        }

        await self.cache.set(cache_key, result)
        await logger.log("info", f"Products for {category} cached")

        return result

# ============================================================================
# BENCHMARK ENDPOINTS
# ============================================================================

@app.get("/")
def home(request: Request) -> Response:
    """Home endpoint - basic DI overhead test"""
    return JSONResponse({
        "message": "Catzilla DI Benchmark",
        "framework": "catzilla",
        "di_system": "enabled",
        "features": ["singleton", "request", "transient"]
    })

@app.get("/health")
def health_check(request: Request) -> Response:
    """Health check endpoint"""
    return JSONResponse({
        "status": "healthy",
        "framework": "catzilla",
        "di_container": "active"
    })

@app.get("/di-simple")
def di_simple_test(config: BenchmarkConfig = Depends("benchmark_config")) -> Response:
    """Simple DI test - singleton injection"""
    return JSONResponse({
        "test": "di_simple",
        "framework": "catzilla",
        "config": {
            "app_name": config.app_name,
            "version": config.version,
            "created_at": config.created_at
        },
        "di_scope": "singleton"
    })

@app.get("/di-request")
async def di_request_test(
    session: BenchmarkSession = Depends("benchmark_session"),
    context: BenchmarkRequestContext = Depends("benchmark_request_context")
) -> Response:
    """Request-scoped DI test"""

    # Simulate some operations
    await session.execute_query("SELECT 1")
    context.add_operation("test_operation", 2.0)

    return JSONResponse({
        "test": "di_request",
        "framework": "catzilla",
        "session": session.get_session_stats(),
        "context": context.get_summary(),
        "di_scope": "request"
    })

@app.get("/di-transient")
async def di_transient_test(
    logger1: BenchmarkLogger = Depends("benchmark_logger"),
    logger2: BenchmarkLogger = Depends("benchmark_logger"),
    context: BenchmarkRequestContext = Depends("benchmark_request_context")
) -> Response:
    """Transient DI test - multiple instances"""

    await logger1.log("info", "First logger message")
    await logger2.log("info", "Second logger message")

    return JSONResponse({
        "test": "di_transient",
        "framework": "catzilla",
        "logger1_id": logger1.logger_id,
        "logger2_id": logger2.logger_id,
        "different_instances": logger1.logger_id != logger2.logger_id,
        "context": context.get_summary(),
        "di_scope": "transient"
    })

@app.get("/di-complex")
async def di_complex_test(
    user_repo: UserRepository = Depends("user_repository"),
    product_repo: ProductRepository = Depends("product_repository"),
    cache: BenchmarkCache = Depends("benchmark_cache"),
    context: BenchmarkRequestContext = Depends("benchmark_request_context")
) -> Response:
    """Complex DI test - multiple dependencies with nested injections"""

    # Simulate complex operations with nested dependencies
    user_data = await user_repo.get_user(42)
    products_data = await product_repo.get_products("electronics")

    cache_stats = cache.get_stats()
    context_summary = context.get_summary()

    return JSONResponse({
        "test": "di_complex",
        "framework": "catzilla",
        "user": user_data,
        "products": products_data,
        "cache_stats": cache_stats,
        "context": context_summary,
        "di_complexity": "high",
        "nested_dependencies": True
    })

@app.get("/users/{user_id}")
async def get_user(
    user_id: int = Path(..., description="User ID"),
    user_repo: UserRepository = Depends("user_repository")
) -> Response:
    """Get user by ID - repository pattern with DI"""

    user_data = await user_repo.get_user(user_id)

    return JSONResponse({
        "user": user_data,
        "framework": "catzilla",
        "di_pattern": "repository"
    })

@app.post("/users")
async def create_user(
    user_data: UserModel,
    user_repo: UserRepository = Depends("user_repository")
) -> Response:
    """Create user - repository pattern with DI and validation"""

    created_user = await user_repo.create_user(user_data)

    return JSONResponse({
        "user": created_user,
        "framework": "catzilla",
        "di_pattern": "repository",
        "validation": "auto"
    }, status_code=201)

@app.get("/products")
async def get_products(
    category: str = Query("all", description="Product category"),
    product_repo: ProductRepository = Depends("product_repository")
) -> Response:
    """Get products by category - repository pattern with DI"""

    products_data = await product_repo.get_products(category)

    return JSONResponse({
        "result": products_data,
        "framework": "catzilla",
        "di_pattern": "repository"
    })

@app.get("/di-performance")
async def di_performance_test(
    config: BenchmarkConfig = Depends("benchmark_config"),
    cache: BenchmarkCache = Depends("benchmark_cache"),
    session: BenchmarkSession = Depends("benchmark_session"),
    context: BenchmarkRequestContext = Depends("benchmark_request_context"),
    logger: BenchmarkLogger = Depends("benchmark_logger")
) -> Response:
    """DI performance test - multiple scopes in single endpoint"""

    start_time = time.time()

    # Test all DI scopes
    await logger.log("info", "Starting performance test")
    await session.execute_query("SELECT performance_test")
    await cache.set("perf_test", {"timestamp": time.time()})
    perf_data = await cache.get("perf_test")

    total_time = (time.time() - start_time) * 1000

    return JSONResponse({
        "test": "di_performance",
        "framework": "catzilla",
        "total_time_ms": round(total_time, 3),
        "services_injected": 5,
        "scopes_tested": ["singleton", "request", "transient"],
        "config_instance": id(config),
        "cache_stats": cache.get_stats(),
        "session_stats": session.get_session_stats(),
        "context": context.get_summary(),
        "performance": "measured"
    })

# ============================================================================
# SERVER STARTUP
# ============================================================================

def main():
    import argparse

    parser = argparse.ArgumentParser(description='Catzilla DI Benchmark Server')
    parser.add_argument('--port', type=int, default=8200, help='Port to run the server on')
    parser.add_argument('--host', default='0.0.0.0', help='Host to bind the server to')

    args = parser.parse_args()

    print(f"🚀 Starting Catzilla DI Benchmark Server on {args.host}:{args.port}")
    print("Available endpoints:")
    print("  GET  /                     - Home")
    print("  GET  /health               - Health check")
    print("  GET  /di-simple            - Simple DI (singleton)")
    print("  GET  /di-request           - Request-scoped DI")
    print("  GET  /di-transient         - Transient DI")
    print("  GET  /di-complex           - Complex nested DI")
    print("  GET  /users/{user_id}      - Get user (repository pattern)")
    print("  POST /users                - Create user (repository + validation)")
    print("  GET  /products?category=x  - Get products (repository pattern)")
    print("  GET  /di-performance       - DI performance test")
    print("")
    print("🧪 Test POST: curl -X POST -H 'Content-Type: application/json' \\")
    print("     -d '{\"id\":1,\"name\":\"John\",\"email\":\"john@example.com\"}' \\")
    print(f"     http://localhost:{args.port}/users")

    app.listen(port=args.port, host=args.host)

if __name__ == "__main__":
    main()
