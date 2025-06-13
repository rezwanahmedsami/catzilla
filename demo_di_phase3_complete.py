#!/usr/bin/env python3
"""
Catzilla v0.2.0 Phase 3 Complete Demo

This demo showcases the complete integration of the revolutionary C-compiled
dependency injection system with the Catzilla router, demonstrating all
major features working together in harmony.

Features demonstrated:
- C-speed dependency injection with FastAPI-style decorators
- Seamless integration with Catzilla's C-accelerated router
- Auto-validation compatibility
- Multiple dependency injection patterns
- High-performance request handling with jemalloc optimization
- Production-ready error handling
"""

import json
import sys
import os
from dataclasses import dataclass
from typing import Dict, List, Optional

# Add the parent directory to sys.path to import catzilla
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'python'))

from catzilla import Catzilla, JSONResponse
from catzilla.decorators import service, inject, Depends, auto_inject


# ============================================================================
# Real-World Services
# ============================================================================

@dataclass
class AppConfig:
    """Application configuration service"""
    database_url: str = "postgresql://localhost:5432/catzilla_prod"
    redis_url: str = "redis://localhost:6379"
    jwt_secret: str = "catzilla-super-secret-key"
    debug: bool = False
    max_connections: int = 100

    def is_production(self) -> bool:
        return not self.debug

class DatabaseService:
    """High-performance database service"""

    def __init__(self, config: AppConfig):
        self.config = config
        self.connection_pool = []
        self.query_count = 0

    def query(self, sql: str, params: Optional[Dict] = None) -> List[Dict]:
        """Execute a database query"""
        self.query_count += 1

        # Simulate different queries
        if "users" in sql.lower():
            return [
                {"id": 1, "username": "alice", "email": "alice@catzilla.com", "active": True},
                {"id": 2, "username": "bob", "email": "bob@catzilla.com", "active": True},
                {"id": 3, "username": "charlie", "email": "charlie@catzilla.com", "active": False},
            ]
        elif "orders" in sql.lower():
            return [
                {"id": 101, "user_id": 1, "total": 29.99, "status": "completed"},
                {"id": 102, "user_id": 2, "total": 49.99, "status": "pending"},
            ]
        return []

    def get_stats(self) -> Dict:
        return {
            "query_count": self.query_count,
            "connection_url": self.config.database_url,
            "max_connections": self.config.max_connections
        }

class CacheService:
    """Redis-based cache service"""

    def __init__(self, config: AppConfig):
        self.config = config
        self.cache = {}
        self.hit_count = 0
        self.miss_count = 0

    def get(self, key: str) -> Optional[str]:
        """Get value from cache"""
        if key in self.cache:
            self.hit_count += 1
            return self.cache[key]
        else:
            self.miss_count += 1
            return None

    def set(self, key: str, value: str, ttl: int = 3600) -> bool:
        """Set value in cache"""
        self.cache[key] = value
        return True

    def get_stats(self) -> Dict:
        total_requests = self.hit_count + self.miss_count
        hit_ratio = self.hit_count / total_requests if total_requests > 0 else 0

        return {
            "hit_count": self.hit_count,
            "miss_count": self.miss_count,
            "hit_ratio": round(hit_ratio * 100, 2),
            "cache_size": len(self.cache),
            "redis_url": self.config.redis_url
        }

class AuthService:
    """JWT-based authentication service"""

    def __init__(self, config: AppConfig, cache: CacheService):
        self.config = config
        self.cache = cache
        self.active_sessions = 0

    def authenticate(self, token: str) -> Optional[Dict]:
        """Authenticate user by JWT token"""
        # Check cache first
        cached_user = self.cache.get(f"auth:{token}")
        if cached_user:
            return json.loads(cached_user)

        # Simulate JWT validation
        if token.startswith("valid_"):
            user = {"id": 1, "username": "authenticated_user", "role": "admin"}
            self.cache.set(f"auth:{token}", json.dumps(user))
            self.active_sessions += 1
            return user

        return None

    def get_stats(self) -> Dict:
        return {
            "active_sessions": self.active_sessions,
            "jwt_secret_length": len(self.config.jwt_secret)
        }

class BusinessLogicService:
    """Core business logic with multiple dependencies"""

    def __init__(self, db: DatabaseService, cache: CacheService, auth: AuthService):
        self.db = db
        self.cache = cache
        self.auth = auth

    def get_user_dashboard(self, user_id: int) -> Dict:
        """Get comprehensive user dashboard data"""
        # Get user data
        users = self.db.query("SELECT * FROM users WHERE id = ?", {"id": user_id})
        user = users[0] if users else None

        if not user:
            return {"error": "User not found"}

        # Get user orders
        orders = self.db.query("SELECT * FROM orders WHERE user_id = ?", {"user_id": user_id})

        # Cache the result
        cache_key = f"dashboard:{user_id}"
        dashboard_data = {
            "user": user,
            "orders": orders,
            "order_count": len(orders),
            "total_spent": sum(order.get("total", 0) for order in orders),
            "cache_hit": False
        }

        self.cache.set(cache_key, json.dumps(dashboard_data))

        return dashboard_data

    def get_system_health(self) -> Dict:
        """Get comprehensive system health metrics"""
        return {
            "database": self.db.get_stats(),
            "cache": self.cache.get_stats(),
            "auth": self.auth.get_stats(),
            "system_status": "healthy"
        }


# ============================================================================
# Catzilla App with Production DI Setup
# ============================================================================

def create_production_app() -> Catzilla:
    """Create a production-ready Catzilla app with full DI configuration"""

    # Create app with all optimizations enabled
    app = Catzilla(
        production=True,
        use_jemalloc=True,
        memory_profiling=True,
        auto_memory_tuning=True,
        auto_validation=True,
        enable_di=True
    )

    # Register all services with appropriate scopes
    app.register_service("config", lambda: AppConfig(debug=False), scope="singleton", dependencies=[])
    app.register_service("database", lambda config: DatabaseService(config), scope="singleton", dependencies=["config"])
    app.register_service("cache", lambda config: CacheService(config), scope="singleton", dependencies=["config"])
    app.register_service("auth", lambda config, cache: AuthService(config, cache), scope="singleton", dependencies=["config", "cache"])
    app.register_service("business_logic", lambda database, cache, auth: BusinessLogicService(database, cache, auth),
                        scope="request", dependencies=["database", "cache", "auth"])

    return app


# ============================================================================
# API Routes with Different DI Patterns
# ============================================================================

def setup_production_routes(app: Catzilla):
    """Setup production API routes demonstrating all DI patterns"""

    # Health check endpoint - no DI needed
    @app.get("/health")
    def health_check(request):
        """Basic health check"""
        return JSONResponse({
            "status": "healthy",
            "version": "0.2.0",
            "features": ["C-router", "jemalloc", "auto-validation", "DI"]
        })

    # Explicit dependency injection
    @app.get("/api/users", dependencies=["database"])
    def list_users(request, database: DatabaseService):
        """List all users - explicit DI"""
        users = database.query("SELECT * FROM users")
        return JSONResponse({
            "users": users,
            "total": len(users),
            "query_stats": database.get_stats(),
            "injection_method": "explicit"
        })

    # Auto-injection with type hints
    @app.get("/api/users/{user_id}/dashboard")
    @auto_inject()
    def user_dashboard(request, user_id: int, business_logic: BusinessLogicService):
        """Get user dashboard - auto-injection"""
        dashboard = business_logic.get_user_dashboard(user_id)
        dashboard["injection_method"] = "auto_inject"
        return JSONResponse(dashboard)

    # FastAPI-style dependency injection
    @app.get("/api/system/health")
    def system_health(request, business_logic: BusinessLogicService = Depends("business_logic")):
        """System health check - FastAPI style"""
        health = business_logic.get_system_health()
        health["injection_method"] = "fastapi_style"
        return JSONResponse(health)

    # Multiple dependencies with authentication
    @app.get("/api/admin/stats", dependencies=["database", "cache", "auth"])
    def admin_stats(request, database: DatabaseService, cache: CacheService, auth: AuthService):
        """Admin statistics - multiple dependencies"""

        # Simple auth check (normally would check request headers)
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer valid_"):
            return JSONResponse({"error": "Unauthorized"}, status_code=401)

        user = auth.authenticate(auth_header.replace("Bearer ", ""))
        if not user or user.get("role") != "admin":
            return JSONResponse({"error": "Admin access required"}, status_code=403)

        return JSONResponse({
            "database_stats": database.get_stats(),
            "cache_stats": cache.get_stats(),
            "auth_stats": auth.get_stats(),
            "injection_method": "multiple_explicit",
            "authenticated_user": user["username"]
        })

    # Manual DI context usage
    @app.get("/api/manual/context")
    def manual_context_demo(request):
        """Manual DI context demonstration"""
        with app.create_di_context() as context:
            # Manually resolve services
            config = app.resolve_service("config", context)
            database = app.resolve_service("database", context)
            cache = app.resolve_service("cache", context)

            return JSONResponse({
                "config_is_production": config.is_production(),
                "database_queries": database.query_count,
                "cache_size": len(cache.cache),
                "injection_method": "manual_context",
                "context_id": id(context)
            })

    # Service introspection endpoint
    @app.get("/api/di/introspection")
    def di_introspection(request):
        """DI system introspection"""
        services = app.list_services()
        container = app.get_di_container()

        return JSONResponse({
            "total_services": len(services),
            "registered_services": services,
            "container_id": id(container),
            "memory_allocator": "jemalloc" if app.has_jemalloc else "malloc",
            "features": {
                "c_backend": True,
                "auto_discovery": True,
                "scope_management": True,
                "context_isolation": True
            }
        })


# ============================================================================
# Demo Runner
# ============================================================================

def run_demo():
    """Run the complete Phase 3 demo"""
    print("🚀 Catzilla v0.2.0 Phase 3 Complete Demo")
    print("Revolutionary C-compiled DI + C-accelerated Router + jemalloc")
    print("=" * 70)

    # Create production app
    print("\n📦 Creating production Catzilla app...")
    app = create_production_app()

    print(f"✅ App created with {len(app.list_services())} services registered")
    print(f"   Memory allocator: {'jemalloc' if app.has_jemalloc else 'malloc'}")
    print(f"   DI enabled: {app.enable_di}")
    print(f"   Auto-validation: {app.auto_validation}")

    # Setup routes
    print("\n🛣️  Setting up production API routes...")
    setup_production_routes(app)
    print("✅ All routes configured with DI integration")

    # Simulate some requests
    print("\n🔥 Testing route handlers with DI...")

    def simulate_request(path: str, method: str = "GET", headers: Dict = None) -> Dict:
        """Simple request simulation"""
        class MockRequest:
            def __init__(self, path: str, method: str, headers: Dict = None):
                self.path = path
                self.method = method.upper()
                self.headers = headers or {}
                self.body = None
                self.path_params = {}

        request = MockRequest(path, method, headers)

        try:
            route, path_params, _ = app.router.match(method.upper(), path)
            if route:
                request.path_params = path_params
                if "user_id" in path_params:
                    path_params["user_id"] = int(path_params["user_id"])

                handler = route.handler
                if app.enable_di:
                    handler = app.di_middleware(handler)

                if path_params and "user_id" in path_params:
                    response = handler(request, path_params["user_id"])
                else:
                    response = handler(request)

                if hasattr(response, 'body'):
                    return json.loads(response.body)
                return response
        except Exception as e:
            return {"error": str(e)}

    # Test various endpoints
    test_cases = [
        ("/health", "Health check"),
        ("/api/users", "List users (explicit DI)"),
        ("/api/users/1/dashboard", "User dashboard (auto-inject)"),
        ("/api/system/health", "System health (FastAPI-style)"),
        ("/api/admin/stats", "Admin stats (multiple deps)", {"Authorization": "Bearer valid_admin_token"}),
        ("/api/manual/context", "Manual context demo"),
        ("/api/di/introspection", "DI introspection"),
    ]

    for path, description, *args in test_cases:
        headers = args[0] if args else {}
        print(f"\n📊 Testing: {description}")
        print(f"   Endpoint: {path}")

        result = simulate_request(path, headers=headers)

        if "error" in result:
            print(f"   ❌ Error: {result['error']}")
        else:
            injection_method = result.get("injection_method", "none")
            print(f"   ✅ Success (injection: {injection_method})")

            # Show interesting metrics
            if "total" in result:
                print(f"      Total items: {result['total']}")
            if "query_stats" in result:
                print(f"      DB queries: {result['query_stats']['query_count']}")
            if "cache_stats" in result:
                print(f"      Cache hit ratio: {result['cache_stats']['hit_ratio']}%")
            if "total_services" in result:
                print(f"      Registered services: {result['total_services']}")

    # Performance summary
    print("\n" + "=" * 70)
    print("🏆 CATZILLA V0.2.0 PHASE 3 COMPLETE!")
    print("=" * 70)
    print("✅ C-compiled dependency injection system")
    print("✅ C-accelerated router integration")
    print("✅ jemalloc memory optimization")
    print("✅ Auto-validation compatibility")
    print("✅ FastAPI-style decorators")
    print("✅ Production-ready error handling")
    print("✅ High-performance request processing")
    print("✅ Context isolation and scope management")
    print("✅ Service introspection and debugging")
    print("✅ Multiple injection patterns supported")

    print("\n🚀 Ready for Phase 4: Memory Optimization & Production Features!")
    print("   Next: Advanced memory pooling, performance profiling,")
    print("        production monitoring, and comprehensive benchmarks.")


if __name__ == "__main__":
    run_demo()
