#!/usr/bin/env python3
"""
FastAPI Dependency Injection Benchmark Server

This server demonstrates FastAPI's dependency injection performance
for comparison with Catzilla's DI system.
"""

import sys
import os
import json
import time
import asyncio
from typing import Optional, Dict, Any

try:
    from fastapi import FastAPI, Request, Response, HTTPException, Depends, Path, Query
    from fastapi.responses import JSONResponse
    from pydantic import BaseModel
except ImportError:
    print("❌ FastAPI not installed. Install with: pip install fastapi uvicorn pydantic")
    sys.exit(1)

# Initialize FastAPI
app = FastAPI(
    title="FastAPI DI Benchmark",
    docs_url=None,
    redoc_url=None
)

print("⚡ FastAPI Dependency Injection Benchmark Server")

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
# DEPENDENCY SERVICES
# ============================================================================

class BenchmarkConfig:
    """Configuration service - effectively singleton in FastAPI"""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.app_name = "FastAPI DI Benchmark"
            cls._instance.version = "1.0.0"
            cls._instance.database_url = "sqlite:///benchmark.db"
            cls._instance.cache_ttl = 300
            cls._instance.created_at = time.time()
            print(f"📋 BenchmarkConfig created at {cls._instance.created_at}")
        return cls._instance

    def get_database_config(self) -> Dict[str, Any]:
        return {
            "url": self.database_url,
            "pool_size": 10,
            "timeout": 30
        }

class BenchmarkCache:
    """Cache service - effectively singleton in FastAPI"""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.cache = {}
            cls._instance.hit_count = 0
            cls._instance.miss_count = 0
            cls._instance.created_at = time.time()
            print(f"💾 BenchmarkCache created at {cls._instance.created_at}")
        return cls._instance

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

class BenchmarkSession:
    """Database session service - new instance per dependency call"""

    def __init__(self, config: BenchmarkConfig):
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

class BenchmarkRequestContext:
    """Request context service - new instance per dependency call"""

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

class BenchmarkLogger:
    """Logger service - new instance per dependency call"""

    def __init__(self, context: BenchmarkRequestContext):
        self.context = context
        self.logger_id = f"logger_{int(time.time() * 1000000)}"
        self.log_count = 0
        print(f"📊 BenchmarkLogger {self.logger_id} created")

    async def log(self, level: str, message: str) -> None:
        await asyncio.sleep(0.0001)  # 0.1ms log write
        self.log_count += 1
        self.context.add_operation(f"log_{level}", 0.1)

class UserRepository:
    """User repository with multiple dependencies"""

    def __init__(self, config: BenchmarkConfig, cache: BenchmarkCache):
        self.config = config
        self.cache = cache
        self.repository_id = f"user_repo_{int(time.time() * 1000)}"
        print(f"👥 UserRepository {self.repository_id} created")

    async def get_user(self, user_id: int, session: BenchmarkSession, logger: BenchmarkLogger) -> Dict[str, Any]:
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

    async def create_user(self, user_data: UserModel, session: BenchmarkSession, logger: BenchmarkLogger) -> Dict[str, Any]:
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

# ============================================================================
# DEPENDENCY FUNCTIONS
# ============================================================================

def get_config() -> BenchmarkConfig:
    """Get configuration dependency"""
    return BenchmarkConfig()

def get_cache() -> BenchmarkCache:
    """Get cache dependency"""
    return BenchmarkCache()

def get_session(config: BenchmarkConfig = Depends(get_config)) -> BenchmarkSession:
    """Get database session dependency"""
    return BenchmarkSession(config)

def get_context() -> BenchmarkRequestContext:
    """Get request context dependency"""
    return BenchmarkRequestContext()

def get_logger(context: BenchmarkRequestContext = Depends(get_context)) -> BenchmarkLogger:
    """Get logger dependency"""
    return BenchmarkLogger(context)

def get_user_repository(
    config: BenchmarkConfig = Depends(get_config),
    cache: BenchmarkCache = Depends(get_cache)
) -> UserRepository:
    """Get user repository dependency"""
    return UserRepository(config, cache)

# ============================================================================
# BENCHMARK ENDPOINTS
# ============================================================================

@app.get("/")
async def home():
    """Home endpoint - basic DI overhead test"""
    return {
        "message": "FastAPI DI Benchmark",
        "framework": "fastapi",
        "di_system": "depends",
        "features": ["dependency_injection", "function_based"]
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "framework": "fastapi",
        "di_container": "function_based"
    }

@app.get("/di-simple")
async def di_simple_test(config: BenchmarkConfig = Depends(get_config)):
    """Simple DI test - configuration injection"""
    return {
        "test": "di_simple",
        "framework": "fastapi",
        "config": {
            "app_name": config.app_name,
            "version": config.version,
            "created_at": config.created_at
        },
        "di_scope": "function_call"
    }

@app.get("/di-request")
async def di_request_test(
    session: BenchmarkSession = Depends(get_session),
    context: BenchmarkRequestContext = Depends(get_context)
):
    """Request-scoped DI test"""

    # Simulate some operations
    await session.execute_query("SELECT 1")
    context.add_operation("test_operation", 2.0)

    return {
        "test": "di_request",
        "framework": "fastapi",
        "session": session.get_session_stats(),
        "context": context.get_summary(),
        "di_scope": "function_call"
    }

@app.get("/di-transient")
async def di_transient_test(
    logger1: BenchmarkLogger = Depends(get_logger),
    logger2: BenchmarkLogger = Depends(get_logger),
    context: BenchmarkRequestContext = Depends(get_context)
):
    """Transient DI test - multiple instances"""

    await logger1.log("info", "First logger message")
    await logger2.log("info", "Second logger message")

    return {
        "test": "di_transient",
        "framework": "fastapi",
        "logger1_id": logger1.logger_id,
        "logger2_id": logger2.logger_id,
        "different_instances": logger1.logger_id != logger2.logger_id,
        "context": context.get_summary(),
        "di_scope": "function_call"
    }

@app.get("/di-complex")
async def di_complex_test(
    user_repo: UserRepository = Depends(get_user_repository),
    cache: BenchmarkCache = Depends(get_cache),
    session: BenchmarkSession = Depends(get_session),
    logger: BenchmarkLogger = Depends(get_logger),
    context: BenchmarkRequestContext = Depends(get_context)
):
    """Complex DI test - multiple dependencies"""

    # Simulate complex operations
    user_data = await user_repo.get_user(42, session, logger)

    cache_stats = cache.get_stats()
    context_summary = context.get_summary()

    return {
        "test": "di_complex",
        "framework": "fastapi",
        "user": user_data,
        "cache_stats": cache_stats,
        "context": context_summary,
        "di_complexity": "high",
        "nested_dependencies": True
    }

@app.get("/users/{user_id}")
async def get_user(
    user_id: int = Path(..., description="User ID"),
    user_repo: UserRepository = Depends(get_user_repository),
    session: BenchmarkSession = Depends(get_session),
    logger: BenchmarkLogger = Depends(get_logger)
):
    """Get user by ID - repository pattern with DI"""

    user_data = await user_repo.get_user(user_id, session, logger)

    return {
        "user": user_data,
        "framework": "fastapi",
        "di_pattern": "function_dependencies"
    }

@app.post("/users")
async def create_user(
    user_data: UserModel,
    user_repo: UserRepository = Depends(get_user_repository),
    session: BenchmarkSession = Depends(get_session),
    logger: BenchmarkLogger = Depends(get_logger)
):
    """Create user - repository pattern with DI and validation"""

    created_user = await user_repo.create_user(user_data, session, logger)

    return {
        "user": created_user,
        "framework": "fastapi",
        "di_pattern": "function_dependencies",
        "validation": "pydantic"
    }

@app.get("/products")
async def get_products(
    category: str = Query("all", description="Product category"),
    cache: BenchmarkCache = Depends(get_cache),
    session: BenchmarkSession = Depends(get_session),
    logger: BenchmarkLogger = Depends(get_logger)
):
    """Get products by category - simulated repository with DI"""

    cache_key = f"products_{category}"
    cached_products = await cache.get(cache_key)

    if cached_products:
        await logger.log("info", f"Products for {category} found in cache")
        return {"result": cached_products, "framework": "fastapi", "di_pattern": "function_dependencies"}

    await logger.log("info", f"Fetching products for category: {category}")
    await session.execute_query(f"SELECT * FROM products WHERE category = '{category}'")

    products = [
        {"id": i, "name": f"Product {i}", "price": 99.99, "category": category}
        for i in range(1, 6)
    ]

    result = {
        "products": products,
        "category": category,
        "count": len(products)
    }

    await cache.set(cache_key, result)
    await logger.log("info", f"Products for {category} cached")

    return {
        "result": result,
        "framework": "fastapi",
        "di_pattern": "function_dependencies"
    }

@app.get("/di-performance")
async def di_performance_test(
    config: BenchmarkConfig = Depends(get_config),
    cache: BenchmarkCache = Depends(get_cache),
    session: BenchmarkSession = Depends(get_session),
    context: BenchmarkRequestContext = Depends(get_context),
    logger: BenchmarkLogger = Depends(get_logger)
):
    """DI performance test - multiple dependencies in single endpoint"""

    start_time = time.time()

    # Test dependency resolution
    await logger.log("info", "Starting performance test")
    await session.execute_query("SELECT performance_test")
    await cache.set("perf_test", {"timestamp": time.time()})
    perf_data = await cache.get("perf_test")

    total_time = (time.time() - start_time) * 1000

    return {
        "test": "di_performance",
        "framework": "fastapi",
        "total_time_ms": round(total_time, 3),
        "dependencies_injected": 5,
        "di_system": "function_based",
        "config_instance": id(config),
        "cache_stats": cache.get_stats(),
        "session_stats": session.get_session_stats(),
        "context": context.get_summary(),
        "performance": "measured"
    }

# ============================================================================
# SERVER STARTUP
# ============================================================================

def main():
    import argparse

    parser = argparse.ArgumentParser(description='FastAPI DI Benchmark Server')
    parser.add_argument('--port', type=int, default=8201, help='Port to run the server on')
    parser.add_argument('--host', default='0.0.0.0', help='Host to bind the server to')

    args = parser.parse_args()

    print(f"🚀 Starting FastAPI DI Benchmark Server on {args.host}:{args.port}")
    print("Available endpoints:")
    print("  GET  /                     - Home")
    print("  GET  /health               - Health check")
    print("  GET  /di-simple            - Simple DI")
    print("  GET  /di-request           - Request-scoped DI")
    print("  GET  /di-transient         - Transient DI")
    print("  GET  /di-complex           - Complex nested DI")
    print("  GET  /users/{user_id}      - Get user (repository pattern)")
    print("  POST /users                - Create user (repository + validation)")
    print("  GET  /products?category=x  - Get products")
    print("  GET  /di-performance       - DI performance test")

    try:
        import uvicorn
        uvicorn.run(
            "fastapi_di:app",
            host=args.host,
            port=args.port,
            log_level="error",
            access_log=False
        )
    except ImportError:
        print("❌ uvicorn not installed. Install with: pip install uvicorn")
        sys.exit(1)

if __name__ == "__main__":
    main()

# The app instance is already created at module level (line 25) for ASGI servers like uvicorn
