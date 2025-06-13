# 🚀 Catzilla v0.2.0 - Dependency Injection Guide

## 📋 Table of Contents
- [Quick Start](#quick-start)
- [Core Concepts](#core-concepts)
- [API Reference](#api-reference)
- [Advanced Features](#advanced-features)
- [Integration Examples](#integration-examples)
- [Performance Guide](#performance-guide)
- [Troubleshooting](#troubleshooting)

---

## 🚀 Quick Start

### Installation

Catzilla's dependency injection system is included with the main framework:

```bash
pip install catzilla>=0.2.0
```

### Basic Usage

```python
from catzilla import Catzilla, service, inject, Depends
from catzilla.dependency_injection import DIContainer

# Create application with DI enabled
app = Catzilla()

# 1. Register services using decorators
@service("config", scope="singleton")
class Config:
    def __init__(self):
        self.database_url = "postgresql://localhost:5432/myapp"
        self.debug = True

@service("database", scope="singleton")
class DatabaseService:
    def __init__(self, config: Config = Depends("config")):
        self.config = config
        self.connection_pool = self._create_pool()

    def _create_pool(self):
        # Create database connection pool
        return f"Connected to {self.config.database_url}"

# 2. Use dependency injection in route handlers
@app.get("/status")
def health_check(db: DatabaseService = Depends("database")):
    return {
        "status": "healthy",
        "database": db.connection_pool,
        "debug": db.config.debug
    }

# 3. Alternative: Function-based injection
@inject("database")
def get_users(db: DatabaseService):
    return {"users": ["alice", "bob"], "db_status": db.connection_pool}

@app.get("/users")
def users_endpoint():
    return get_users()

if __name__ == "__main__":
    app.run()
```

---

## 🧠 Core Concepts

### Dependency Injection Container

The DI container is the central registry for all services in your application:

```python
from catzilla.dependency_injection import DIContainer

# Create container
container = DIContainer()

# Register services
container.register("my_service", MyServiceClass, scope="singleton")

# Resolve services
service_instance = container.resolve("my_service")
```

### Service Scopes

Catzilla supports multiple service lifecycles:

- **`singleton`**: One instance per container (default)
- **`transient`**: New instance every time
- **`scoped`**: One instance per request/context
- **`request`**: Alias for scoped

```python
@service("cache", scope="singleton")     # Shared across all requests
class CacheService:
    pass

@service("user_session", scope="request") # New per request
class UserSession:
    pass

@service("temp_processor", scope="transient") # New every time
class TempProcessor:
    pass
```

### Dependency Declaration

Multiple ways to declare dependencies:

```python
# 1. Constructor injection with type hints
@service("user_service")
class UserService:
    def __init__(self, db: DatabaseService, cache: CacheService):
        self.db = db
        self.cache = cache

# 2. Explicit dependency declaration
@service("user_service", dependencies=["database", "cache"])
class UserService:
    def __init__(self, database, cache):
        self.db = database
        self.cache = cache

# 3. Function parameter injection
@inject("database", "cache")
def process_users(db, cache):
    return {"processed": True}

# 4. Route handler injection
@app.get("/users/{user_id}")
def get_user(user_id: int,
            db: DatabaseService = Depends("database"),
            cache: CacheService = Depends("cache")):
    # Dependencies automatically resolved
    pass
```

---

## 📚 API Reference

### DIContainer Class

```python
class DIContainer:
    def __init__(self, parent: Optional[DIContainer] = None)
    def register(self, name: str, factory: callable,
                scope: str = "singleton",
                dependencies: List[str] = None) -> int
    def resolve(self, name: str, context: Optional[DIContext] = None) -> Any
    def create_context(self) -> DIContext
    def is_registered(self, name: str) -> bool
    def unregister(self, name: str) -> bool
```

### Decorators

```python
@service(name: str = None, scope: str = "singleton",
         dependencies: List[str] = None)

@inject(*dependency_names: str)

def Depends(dependency_name: str) -> Any
```

### Advanced Container Features (Phase 5)

```python
class AdvancedDIContainer(DIContainer):
    # Hierarchical containers
    def create_child_container(self, config: ContainerConfig) -> 'AdvancedDIContainer'

    # Advanced factories
    def register_builder_factory(self, name: str, builder_func: Callable,
                                factory_func: Callable) -> int
    def register_conditional_factory(self, name: str, condition_func: Callable,
                                   primary_factory: Callable,
                                   fallback_factory: Callable) -> int

    # Configuration-based registration
    def register_services_from_config(self, configs: List[ServiceConfig]) -> int

    # Debugging and introspection
    def enable_debug_mode(self, level: int = 1) -> None
    def get_container_info(self) -> ContainerInfo
    def get_service_info(self, name: str) -> ServiceInfo

    # Health monitoring
    def get_health_status(self) -> Dict[str, Any]
    def run_health_check(self) -> bool
    def get_performance_metrics(self) -> Dict[str, float]
```

---

## 🔧 Advanced Features

### Hierarchical Containers

Create parent-child container relationships for modular applications:

```python
from catzilla.dependency_injection import AdvancedDIContainer, ContainerConfig

# Parent container with core services
parent_config = ContainerConfig(
    name="CoreContainer",
    inherit_services=True,
    allowed_service_patterns=["config", "database*", "cache*"]
)
parent = AdvancedDIContainer(config=parent_config)

# Register core services
parent.register("config", CoreConfig, "singleton")
parent.register("database", DatabaseService, "singleton", ["config"])

# Child container for feature module
child_config = ContainerConfig(
    name="FeatureContainer",
    inherit_services=True,
    allowed_service_patterns=["*"]  # Allow all services
)
child = parent.create_child_container(child_config)

# Child can access parent services + add its own
child.register("feature_service", FeatureService, "singleton", ["database"])

# Resolve from child - automatically checks parent
service = child.resolve("database")  # Found in parent
feature = child.resolve("feature_service")  # Found in child
```

### Advanced Factory Patterns

#### Builder Pattern Factory

```python
# Complex service construction
def config_builder():
    """Build configuration from multiple sources"""
    config = BaseConfig()
    config.load_from_file("app.yaml")
    config.load_from_env()
    config.validate()
    return config

def database_factory(config):
    """Create database service with built config"""
    return DatabaseService(
        url=config.database_url,
        pool_size=config.db_pool_size,
        ssl_mode=config.ssl_mode
    )

container.register_builder_factory(
    "database_advanced",
    config_builder,
    database_factory
)
```

#### Conditional Factory

```python
def should_use_redis():
    """Check if Redis should be used for caching"""
    return os.environ.get("USE_REDIS", "false").lower() == "true"

def redis_cache_factory():
    return RedisCache(url=os.environ.get("REDIS_URL"))

def memory_cache_factory():
    return MemoryCache(max_size=1000)

container.register_conditional_factory(
    "cache",
    should_use_redis,
    redis_cache_factory,
    memory_cache_factory
)

# Cache implementation automatically chosen based on environment
cache = container.resolve("cache")
```

### Configuration-Based Registration

Register services from configuration files:

```python
from catzilla.dependency_injection import ServiceConfig

# Define services in configuration
service_configs = [
    ServiceConfig(
        service_name="database",
        service_type="DatabaseService",
        scope="singleton",
        dependencies=["config"],
        enabled=True,
        priority=10,
        tags=["core", "persistence"]
    ),
    ServiceConfig(
        service_name="cache",
        service_type="CacheService",
        scope="singleton",
        dependencies=["config"],
        enabled=True,
        priority=5,
        tags=["core", "performance"]
    )
]

# Bulk register services
container.register_services_from_config(service_configs)
```

### Debugging and Introspection

Debug your dependency injection setup:

```python
# Enable debug mode
container.enable_debug_mode(level=2)

# Get container information
info = container.get_container_info()
print(f"Container: {info.name}")
print(f"Services: {len(info.services)}")
print(f"Parent: {info.parent_container}")

# Get service information
service_info = container.get_service_info("database")
print(f"Service: {service_info.name}")
print(f"Scope: {service_info.scope}")
print(f"Dependencies: {service_info.dependencies}")
print(f"Instances created: {service_info.instance_count}")

# Health monitoring
health = container.get_health_status()
print(f"Status: {health['status']}")
print(f"Services registered: {health['services_registered']}")
print(f"Services resolved: {health['services_resolved']}")

# Performance metrics
metrics = container.get_performance_metrics()
print(f"Avg resolution time: {metrics['avg_resolution_time_ms']}ms")
print(f"Cache hit rate: {metrics['cache_hit_rate']}%")
```

---

## 🌟 Integration Examples

### SQLAlchemy Integration

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from catzilla import service, Depends

@service("config", scope="singleton")
class DatabaseConfig:
    def __init__(self):
        self.database_url = "postgresql://user:pass@localhost/db"
        self.echo = True

@service("database_engine", scope="singleton")
class DatabaseEngine:
    def __init__(self, config: DatabaseConfig = Depends("config")):
        self.engine = create_engine(
            config.database_url,
            echo=config.echo,
            pool_size=10,
            max_overflow=20
        )

@service("database_session", scope="request")
class DatabaseSession:
    def __init__(self, engine: DatabaseEngine = Depends("database_engine")):
        SessionLocal = sessionmaker(bind=engine.engine)
        self.session = SessionLocal()

    def __enter__(self):
        return self.session

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            self.session.rollback()
        else:
            self.session.commit()
        self.session.close()

# Repository pattern
@service("user_repository", scope="singleton")
class UserRepository:
    def find_by_id(self, user_id: int,
                   session: DatabaseSession = Depends("database_session")):
        with session as db:
            return db.query(User).filter(User.id == user_id).first()

    def create_user(self, user_data: dict,
                   session: DatabaseSession = Depends("database_session")):
        with session as db:
            user = User(**user_data)
            db.add(user)
            return user

# Route handlers
@app.get("/users/{user_id}")
def get_user(user_id: int,
            user_repo: UserRepository = Depends("user_repository")):
    user = user_repo.find_by_id(user_id)
    if not user:
        raise HTTPException(404, "User not found")
    return {"user": user.to_dict()}
```

### FastAPI Migration Example

Migrating from FastAPI's dependency injection:

```python
# Before (FastAPI)
from fastapi import FastAPI, Depends

def get_database():
    return DatabaseService()

def get_user_service(db: DatabaseService = Depends(get_database)):
    return UserService(db)

@app.get("/users/{user_id}")
def get_user(user_id: int,
            user_service: UserService = Depends(get_user_service)):
    return user_service.get_user(user_id)

# After (Catzilla)
from catzilla import Catzilla, service, Depends

@service("database", scope="singleton")
class DatabaseService:
    pass

@service("user_service", scope="singleton")
class UserService:
    def __init__(self, db: DatabaseService = Depends("database")):
        self.db = db

@app.get("/users/{user_id}")
def get_user(user_id: int,
            user_service: UserService = Depends("user_service")):
    return user_service.get_user(user_id)
```

### Microservice Architecture

Structure services for microservice applications:

```python
# Core services container
core_container = AdvancedDIContainer(config=ContainerConfig(
    name="CoreServices",
    inherit_services=True
))

# Shared infrastructure services
@service("message_bus", scope="singleton", container=core_container)
class MessageBus:
    def publish(self, event): pass
    def subscribe(self, handler): pass

@service("metrics", scope="singleton", container=core_container)
class MetricsCollector:
    def increment(self, counter): pass
    def gauge(self, metric, value): pass

# User service container
user_container = core_container.create_child_container(
    ContainerConfig(name="UserService")
)

@service("user_repository", scope="singleton", container=user_container)
class UserRepository:
    def __init__(self, message_bus=Depends("message_bus")):
        self.bus = message_bus

@service("user_service", scope="singleton", container=user_container)
class UserService:
    def __init__(self,
                repo=Depends("user_repository"),
                metrics=Depends("metrics")):
        self.repo = repo
        self.metrics = metrics
```

---

## ⚡ Performance Guide

### Optimization Tips

1. **Use Singleton Scope for Expensive Resources**
```python
@service("database_pool", scope="singleton")  # Good
class DatabasePool:
    def __init__(self):
        # Expensive initialization
        pass

@service("database_connection", scope="request")  # Better for connections
class DatabaseConnection:
    pass
```

2. **Minimize Dependency Chains**
```python
# Avoid deep dependency chains
A -> B -> C -> D -> E  # Slower resolution

# Prefer flatter structures
A -> D  # Direct dependency when possible
B -> D
C -> D
```

3. **Use Type Hints for Automatic Discovery**
```python
# Automatic dependency discovery (faster registration)
@service("user_service")
class UserService:
    def __init__(self, db: DatabaseService, cache: CacheService):
        pass

# Manual dependency specification (use when needed)
@service("user_service", dependencies=["db", "cache"])
class UserService:
    def __init__(self, db, cache):
        pass
```

### Performance Monitoring

```python
# Monitor container performance
container.enable_debug_mode(level=1)

metrics = container.get_performance_metrics()
print(f"Average resolution time: {metrics['avg_resolution_time_ms']}ms")
print(f"Cache hit rate: {metrics['cache_hit_rate']}%")
print(f"Memory usage: {metrics['memory_usage_mb']}MB")

# Health checks
health = container.get_health_status()
if health['status'] != 'healthy':
    print(f"Container issues: {health['issues']}")
```

---

## 🐛 Troubleshooting

### Common Issues

#### 1. Circular Dependencies
```python
# Problem: A depends on B, B depends on A
@service("service_a")
class ServiceA:
    def __init__(self, b: ServiceB = Depends("service_b")):
        pass

@service("service_b")
class ServiceB:
    def __init__(self, a: ServiceA = Depends("service_a")):
        pass

# Solution: Use factory pattern or break the cycle
@service("service_a")
class ServiceA:
    def __init__(self):
        self._service_b = None

    def get_service_b(self):
        if not self._service_b:
            self._service_b = container.resolve("service_b")
        return self._service_b
```

#### 2. Service Not Found
```python
# Error: Service 'database' not found

# Check registration
if not container.is_registered("database"):
    print("Service not registered!")

# Check service name spelling
container.register("database", DatabaseService)  # Correct
# container.resolve("databse")  # Typo!

# Enable debug mode for more information
container.enable_debug_mode(level=2)
```

#### 3. Scope Issues
```python
# Problem: Request-scoped service in singleton
@service("user_session", scope="request")
class UserSession:
    pass

@service("singleton_service", scope="singleton")
class SingletonService:
    def __init__(self, session: UserSession = Depends("user_session")):
        # This will create session once and reuse it!
        pass

# Solution: Use factory or change scope
@service("singleton_service", scope="singleton")
class SingletonService:
    def get_current_session(self):
        return container.resolve("user_session")  # Fresh each time
```

### Debug Commands

```python
# Enable comprehensive debugging
container.enable_debug_mode(level=3)

# Inspect container state
info = container.get_container_info()
print(f"Services: {[s.name for s in info.services]}")

# Check specific service
service_info = container.get_service_info("problematic_service")
print(f"Dependencies: {service_info.dependencies}")
print(f"Scope: {service_info.scope}")
print(f"Registered: {service_info.is_registered}")

# Test resolution manually
try:
    service = container.resolve("test_service")
    print("Resolution successful")
except Exception as e:
    print(f"Resolution failed: {e}")
```

---

## 🔗 Additional Resources

- [Catzilla Documentation](https://github.com/user/catzilla)
- [API Reference](https://github.com/user/catzilla/docs/api)
- [Examples Repository](https://github.com/user/catzilla-examples)
- [Performance Benchmarks](https://github.com/user/catzilla/benchmarks)

## 📝 Migration Guides

- [From FastAPI Dependency Injection](./migration-fastapi.md)
- [From Django Service Layer](./migration-django.md)
- [From Flask with Dependency Injector](./migration-flask.md)

---

*This guide covers Catzilla v0.2.0's revolutionary dependency injection system. For older versions, see the legacy documentation.*
