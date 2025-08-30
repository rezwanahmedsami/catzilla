#!/usr/bin/env python3
"""
🏭 Catzilla DI Factory Patterns Example

This example demonstrates advanced factory patterns in Catzilla's DI system.
Shows how to create complex service instantiation patterns.

Features:
- Simple factory functions
- Builder pattern factories
- Conditional factory resolution
- Service factory abstraction
- Advanced configuration-based factories
"""

import time
from datetime import datetime
from typing import Dict, List, Optional, Any, Protocol
from abc import ABC, abstractmethod

from catzilla import Catzilla, service, Depends, JSONResponse
from catzilla.dependency_injection import set_default_container

# ============================================================================
# SETUP APPLICATION
# ============================================================================

app = Catzilla(enable_di=True)
set_default_container(app.di_container)

print("🏭 Catzilla DI Factory Patterns Example")
print("=" * 50)

# ============================================================================
# 1. SIMPLE FACTORY FUNCTIONS
# ============================================================================

@service("config", scope="singleton")
class Config:
    """Application configuration"""

    def __init__(self):
        self.environment = "development"
        self.debug = True
        self.database_url = "postgresql://localhost:5432/app"
        self.cache_ttl = 300
        self.log_level = "INFO"
        print(f"📋 Config initialized for {self.environment}")

# Factory function for creating database connections
def create_database_connection(config: Config) -> Dict[str, Any]:
    """Factory function to create database connection"""
    print(f"🔌 Creating database connection to {config.database_url}")

    # Simulate database connection creation
    time.sleep(0.1)

    return {
        "connection": f"Connection({config.database_url})",
        "pool_size": 10,
        "timeout": 30,
        "created_at": datetime.now().isoformat()
    }

# Register factory function as service
@service("database", scope="singleton")
def database_service(config: Config = Depends("config")):
    """Database service using factory function"""
    return create_database_connection(config)

# ============================================================================
# 2. BUILDER PATTERN FACTORY
# ============================================================================

class CacheBuilder:
    """Builder pattern for cache configuration"""

    def __init__(self):
        self._config = {
            "type": "memory",
            "max_size": 1000,
            "ttl": 300,
            "eviction_policy": "lru"
        }

    def with_type(self, cache_type: str):
        self._config["type"] = cache_type
        return self

    def with_max_size(self, size: int):
        self._config["max_size"] = size
        return self

    def with_ttl(self, ttl: int):
        self._config["ttl"] = ttl
        return self

    def with_eviction_policy(self, policy: str):
        self._config["eviction_policy"] = policy
        return self

    def build(self) -> Dict[str, Any]:
        print(f"🏗️  Building cache with config: {self._config}")
        return {
            "cache_instance": f"Cache({self._config['type']})",
            "config": self._config,
            "created_at": datetime.now().isoformat()
        }

@service("cache", scope="singleton")
def cache_service(config: Config = Depends("config")):
    """Cache service using builder pattern"""
    builder = CacheBuilder()

    # Configure based on environment
    if config.environment == "production":
        builder = (builder
                  .with_type("redis")
                  .with_max_size(10000)
                  .with_ttl(3600)
                  .with_eviction_policy("lru"))
    else:
        builder = (builder
                  .with_type("memory")
                  .with_max_size(1000)
                  .with_ttl(config.cache_ttl))

    return builder.build()

# ============================================================================
# 3. CONDITIONAL FACTORY RESOLUTION
# ============================================================================

class Logger(ABC):
    """Abstract logger interface"""

    @abstractmethod
    def log(self, message: str, level: str = "INFO"):
        pass

class FileLogger(Logger):
    """File-based logger implementation"""

    def __init__(self, filename: str):
        self.filename = filename
        self.logs = []
        print(f"📁 FileLogger initialized: {filename}")

    def log(self, message: str, level: str = "INFO"):
        entry = f"[{level}] {datetime.now().isoformat()}: {message}"
        self.logs.append(entry)
        print(f"FILE LOG: {entry}")

class ConsoleLogger(Logger):
    """Console-based logger implementation"""

    def __init__(self):
        self.logs = []
        print("🖥️  ConsoleLogger initialized")

    def log(self, message: str, level: str = "INFO"):
        entry = f"[{level}] {datetime.now().isoformat()}: {message}"
        self.logs.append(entry)
        print(f"CONSOLE LOG: {entry}")

# Conditional factory for logger
@service("logger", scope="singleton")
def logger_factory(config: Config = Depends("config")) -> Logger:
    """Conditional factory for logger based on environment"""

    if config.environment == "production":
        return FileLogger("app.log")
    else:
        return ConsoleLogger()

# ============================================================================
# 4. ABSTRACT FACTORY PATTERN
# ============================================================================

class ServiceFactory(Protocol):
    """Abstract factory interface"""

    def create_user_service(self) -> Any:
        """Create user service"""
        pass

    def create_auth_service(self) -> Any:
        """Create auth service"""
        pass

class DevelopmentServiceFactory:
    """Development environment service factory"""

    def __init__(self, config: Config):
        self.config = config
        print("🧪 Development service factory initialized")

    def create_user_service(self):
        return {
            "type": "MockUserService",
            "data": ["user1", "user2", "user3"],
            "config": self.config.environment
        }

    def create_auth_service(self):
        return {
            "type": "MockAuthService",
            "auth_required": False,
            "config": self.config.environment
        }

class ProductionServiceFactory:
    """Production environment service factory"""

    def __init__(self, config: Config):
        self.config = config
        print("🏭 Production service factory initialized")

    def create_user_service(self):
        return {
            "type": "RealUserService",
            "connection": "postgresql://...",
            "config": self.config.environment
        }

    def create_auth_service(self):
        return {
            "type": "RealAuthService",
            "auth_required": True,
            "jwt_secret": "secure_secret",
            "config": self.config.environment
        }

@service("service_factory", scope="singleton")
def service_factory(config: Config = Depends("config")) -> ServiceFactory:
    """Abstract factory for creating services"""

    if config.environment == "production":
        return ProductionServiceFactory(config)
    else:
        return DevelopmentServiceFactory(config)

# ============================================================================
# 5. COMPLEX FACTORY WITH DEPENDENCIES
# ============================================================================

class ApplicationContext:
    """Complex application context with multiple dependencies"""

    def __init__(self, config: Config, database: Dict, cache: Dict, logger: Logger):
        self.config = config
        self.database = database
        self.cache = cache
        self.logger = logger
        self.startup_time = datetime.now()

        print("🚀 Application context initialized")
        logger.log("Application context created", "INFO")

    def get_status(self) -> Dict[str, Any]:
        """Get application status"""
        return {
            "environment": self.config.environment,
            "database_status": "connected",
            "cache_status": "active",
            "uptime": (datetime.now() - self.startup_time).total_seconds(),
            "log_entries": len(self.logger.logs)
        }

@service("app_context", scope="singleton")
def application_context_factory(
    config: Config = Depends("config"),
    database: Dict = Depends("database"),
    cache: Dict = Depends("cache"),
    logger: Logger = Depends("logger")
) -> ApplicationContext:
    """Factory for creating application context with all dependencies"""

    return ApplicationContext(config, database, cache, logger)

# ============================================================================
# 6. LAZY FACTORY PATTERN
# ============================================================================

class LazyServiceWrapper:
    """Wrapper for lazy service initialization"""

    def __init__(self, factory_func, *args, **kwargs):
        self.factory_func = factory_func
        self.args = args
        self.kwargs = kwargs
        self._instance = None
        self._initialized = False
        print("💤 Lazy service wrapper created")

    def get_instance(self):
        """Get the service instance (lazy initialization)"""
        if not self._initialized:
            print("⚡ Lazy service being initialized...")
            self._instance = self.factory_func(*self.args, **self.kwargs)
            self._initialized = True
        return self._instance

def create_expensive_service(config: Config) -> Dict[str, Any]:
    """Simulate expensive service creation"""
    print("💰 Creating expensive service...")
    time.sleep(0.5)  # Simulate expensive operation

    return {
        "type": "ExpensiveService",
        "initialized": True,
        "cost": "high",
        "config": config.environment
    }

@service("expensive_service", scope="singleton")
def expensive_service_factory(config: Config = Depends("config")) -> LazyServiceWrapper:
    """Factory for lazy expensive service"""

    return LazyServiceWrapper(create_expensive_service, config)

# ============================================================================
# 7. ROUTE HANDLERS DEMONSTRATING FACTORY PATTERNS
# ============================================================================

@app.get("/")
def home(request):
    """Home page showing factory patterns"""
    return JSONResponse({
        "message": "🏭 Catzilla DI Factory Patterns Demo",
        "patterns": [
            "Simple factory functions",
            "Builder pattern factories",
            "Conditional factory resolution",
            "Abstract factory pattern",
            "Complex factories with dependencies",
            "Lazy initialization factories"
        ]
    })

@app.get("/services/simple")
def simple_factory_demo(
    request,
    database: Dict = Depends("database")
):
    """Demonstrate simple factory pattern"""

    return JSONResponse({
        "pattern": "Simple Factory",
        "database_service": database,
        "description": "Services created by simple factory functions"
    })

@app.get("/services/builder")
def builder_pattern_demo(
    request,
    cache: Dict = Depends("cache")
):
    """Demonstrate builder pattern"""

    return JSONResponse({
        "pattern": "Builder Pattern",
        "cache_service": cache,
        "description": "Service configured using builder pattern"
    })

@app.get("/services/conditional")
def conditional_factory_demo(
    request,
    logger: Logger = Depends("logger")
):
    """Demonstrate conditional factory"""

    logger.log("Conditional factory demo accessed", "INFO")

    return JSONResponse({
        "pattern": "Conditional Factory",
        "logger_type": type(logger).__name__,
        "recent_logs": logger.logs[-3:] if logger.logs else [],
        "description": "Logger created based on environment condition"
    })

@app.get("/services/abstract")
def abstract_factory_demo(
    request,
    service_factory: ServiceFactory = Depends("service_factory")
):
    """Demonstrate abstract factory pattern"""

    user_service = service_factory.create_user_service()
    auth_service = service_factory.create_auth_service()

    return JSONResponse({
        "pattern": "Abstract Factory",
        "user_service": user_service,
        "auth_service": auth_service,
        "description": "Services created by abstract factory"
    })

@app.get("/services/complex")
def complex_factory_demo(
    request,
    app_context: ApplicationContext = Depends("app_context")
):
    """Demonstrate complex factory with dependencies"""

    return JSONResponse({
        "pattern": "Complex Factory",
        "app_status": app_context.get_status(),
        "description": "Application context with multiple injected dependencies"
    })

@app.get("/services/lazy")
def lazy_factory_demo(
    request,
    lazy_wrapper: LazyServiceWrapper = Depends("expensive_service")
):
    """Demonstrate lazy factory pattern"""

    # This will trigger lazy initialization
    expensive_service = lazy_wrapper.get_instance()

    return JSONResponse({
        "pattern": "Lazy Factory",
        "service": expensive_service,
        "was_initialized": lazy_wrapper._initialized,
        "description": "Service with lazy initialization"
    })

@app.get("/health")
def health_check(
    request,
    config: Config = Depends("config"),
    database: Dict = Depends("database"),
    cache: Dict = Depends("cache"),
    logger: Logger = Depends("logger"),
    app_context: ApplicationContext = Depends("app_context")
):
    """Health check showing all factory-created services"""

    logger.log("Health check performed", "INFO")

    return JSONResponse({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "services": {
            "config": {"environment": config.environment},
            "database": {"status": "connected"},
            "cache": {"type": cache["config"]["type"]},
            "logger": {"type": type(logger).__name__},
            "app_context": app_context.get_status()
        },
        "di_info": {
            "container_type": "Catzilla DI Container",
            "factory_patterns": "All patterns active"
        }
    })

# ============================================================================
# 8. APPLICATION STARTUP
# ============================================================================

if __name__ == "__main__":
    print("\n🎯 Starting Catzilla DI Factory Patterns Demo...")
    print("\nAvailable endpoints:")
    print("  GET  /                    - Home page")
    print("  GET  /services/simple     - Simple factory demo")
    print("  GET  /services/builder    - Builder pattern demo")
    print("  GET  /services/conditional - Conditional factory demo")
    print("  GET  /services/abstract   - Abstract factory demo")
    print("  GET  /services/complex    - Complex factory demo")
    print("  GET  /services/lazy       - Lazy factory demo")
    print("  GET  /health              - Health check")

    print("\n🏭 Factory Patterns:")
    print("  ✅ Simple factory functions")
    print("  ✅ Builder pattern factories")
    print("  ✅ Conditional factory resolution")
    print("  ✅ Abstract factory pattern")
    print("  ✅ Complex factories with dependencies")
    print("  ✅ Lazy initialization factories")

    print(f"\n🚀 Server starting on http://localhost:8002")
    print("   Try: curl http://localhost:8002/health")

    app.listen(8002)
