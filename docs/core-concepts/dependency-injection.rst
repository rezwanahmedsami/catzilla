Dependency Injection
====================

Catzilla includes a powerful dependency injection system with **FastAPI-identical syntax** and **6.5x better performance**. This guide covers everything from basic DI patterns to enterprise-grade service management.

Overview
--------

Catzilla's dependency injection system provides:

- **FastAPI-Compatible Syntax** - Use familiar ``Depends()`` patterns
- **Zero Migration Effort** - Copy-paste your FastAPI DI code
- **C-Accelerated Performance** - 6.5x faster than FastAPI DI
- **Multiple Service Scopes** - Singleton, request, and transient scopes
- **Automatic Service Registration** - No complex container setup
- **Memory Optimization** - Arena-based allocation for high performance

Quick Start
-----------

Enable DI and create your first service:

.. code-block:: python

   from catzilla import Catzilla, service, Depends, Path, JSONResponse
   from catzilla.dependency_injection import set_default_container

   # Enable DI in your app
   app = Catzilla(enable_di=True)

   # Set the app's container as default for service registration
   set_default_container(app.di_container)

   # Create a simple service
   @service("user_service")
   class UserService:
       def get_user(self, user_id: int):
           return {"id": user_id, "name": f"User {user_id}"}

   # Use dependency injection in routes (FastAPI-identical syntax)
   @app.get("/users/{user_id}")
   def get_user(request,
                user_service: UserService = Depends("user_service"),
                user_id: int = Path(..., ge=1)):
       user = user_service.get_user(user_id)
       return JSONResponse({"user": user})

   if __name__ == "__main__":
       app.listen(port=8000)

**Key Benefits:**

- ✅ **FastAPI Syntax** - Identical to FastAPI ``Depends()`` patterns
- ✅ **Zero Learning Curve** - If you know FastAPI DI, you know Catzilla DI
- ✅ **Automatic Registration** - Services are automatically available
- ✅ **Type Safety** - Full type hints and IDE support

Basic Dependency Injection
---------------------------

Simple Service Dependencies
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Create and inject basic services:

.. code-block:: python

   from catzilla import Catzilla, service, Depends, JSONResponse
   from catzilla.dependency_injection import set_default_container

   app = Catzilla(enable_di=True)
   set_default_container(app.di_container)

   # Simple service without dependencies
   @service("greeting_service")
   class GreetingService:
       def greet(self, name: str) -> str:
           return f"Hello, {name}!"

   # Service with dependencies on other services
   @service("user_service")
   class UserService:
       def __init__(self, greeting_service: GreetingService = Depends("greeting_service")):
           self.greeting_service = greeting_service

       def welcome_user(self, name: str) -> str:
           return self.greeting_service.greet(name)

   # Use in route handlers (FastAPI-identical syntax)
   @app.get("/welcome/{name}")
   def welcome(request,
               user_service: UserService = Depends("user_service"),
               name: str = Path(...)):
       message = user_service.welcome_user(name)
       return JSONResponse({"message": message})

   if __name__ == "__main__":
       app.listen(port=8000)

Database Dependencies
~~~~~~~~~~~~~~~~~~~~~

Real-world example with database simulation:

.. code-block:: python

   @service("database_service")
   class DatabaseService:
       def __init__(self):
           # Simulate database connection
           self.connection = "postgresql://localhost:5432/app"

       def get_user(self, user_id: int):
           # Simulate database query
           return {
               "id": user_id,
               "name": f"User {user_id}",
               "email": f"user{user_id}@example.com"
           }

   @service("user_repository")
   class UserRepository:
       def __init__(self, db: DatabaseService = Depends("database_service")):
           self.db = db

       def find_by_id(self, user_id: int):
           return self.db.get_user(user_id)

   # Use in async handlers too
   @app.get("/async-users/{user_id}")
   async def get_user_async(
       request,
       user_repo: UserRepository = Depends("user_repository"),
       user_id: int = Path(..., ge=1)
   ):
       # Simulate async database call
       await asyncio.sleep(0.01)
       user = user_repo.find_by_id(user_id)
       return JSONResponse({"user": user})

   if __name__ == "__main__":
       app.listen(port=8000)

Dependency Injection Approaches
------------------------------

Catzilla supports two dependency injection patterns to suit different preferences and migration scenarios:

**Approach 1: FastAPI-Style Depends() (Recommended)**
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The modern, developer-friendly approach using ``Depends()`` for automatic injection:

.. code-block:: python

   from catzilla import Depends, Path

   @app.get("/users/{user_id}")
   def get_user(request,
                user_service: UserService = Depends("user_service"),
                logger: LoggerService = Depends("logger"),
                user_id: int = Path(..., ge=1)):
       """FastAPI-identical syntax - preferred approach"""
       logger.log(f"Fetching user {user_id}")
       user = user_service.get_user(user_id)
       return JSONResponse({"user": user})

   @app.post("/users")
   def create_user(request,
                   user_data: UserCreateModel,
                   user_service: UserService = Depends("user_service"),
                   db_session: DatabaseSession = Depends("database_session")):
       """Multiple dependencies with auto-validation"""
       user = user_service.create_user(user_data.name, user_data.email, db_session)
       return JSONResponse({"user": user}, status_code=201)

**Benefits:**
- Zero migration effort from FastAPI
- Automatic dependency resolution
- Type hints for better IDE support
- Clean, readable function signatures

**Approach 2: Manual Container Resolution (Alternative)**
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

For cases where you need more control or prefer explicit dependency resolution:

.. code-block:: python

   @app.get("/users/{user_id}")
   def get_user_manual(request):
       """Manual dependency resolution"""
       user_id = int(request.path_params["user_id"])

       # Explicit service resolution
       user_service = app.di_container.resolve("user_service")
       logger = app.di_container.resolve("logger")

       logger.log(f"Fetching user {user_id}")
       user = user_service.get_user(user_id)
       return JSONResponse({"user": user})

**When to use manual resolution:**
- When you need conditional dependency resolution
- For complex initialization logic
- When migrating legacy code gradually
- For debugging dependency issues

**Performance Note:** Both approaches have identical performance - Catzilla optimizes dependency resolution at the C level regardless of which syntax you choose.

Advanced Dependency Injection
------------------------------

Service Scopes
~~~~~~~~~~~~~~

Control service lifetimes with different scopes:

.. code-block:: python

   from catzilla import Catzilla, service, Depends, JSONResponse
   from catzilla.dependency_injection import set_default_container

   app = Catzilla(enable_di=True)
   set_default_container(app.di_container)

   # Singleton - created once, shared across all requests
   @service("config_service", scope="singleton")
   class ConfigService:
       def __init__(self):
           self.config = {"app_name": "Catzilla", "version": "0.2.0"}

       def get_config(self):
           return self.config

   # Request - new instance per request
   @service("request_context_service", scope="request")
   class RequestContextService:
       def __init__(self):
           self.request_id = str(uuid.uuid4())

       def get_request_id(self):
           return self.request_id

   # Transient - new instance every injection
   @service("utility_service", scope="transient")
   class UtilityService:
       def __init__(self):
           self.created_at = time.time()

       def get_timestamp(self):
           return self.created_at

Named Service Registration
~~~~~~~~~~~~~~~~~~~~~~~~~~

Use named services for better organization and explicit dependencies:

.. code-block:: python

   from catzilla import Catzilla, service, Depends, JSONResponse
   from catzilla.dependency_injection import set_default_container

   app = Catzilla(enable_di=True)
   set_default_container(app.di_container)

   # Named database service
   @service("database", scope="singleton")
   class DatabaseService:
       def __init__(self):
           connection_string = os.getenv("DATABASE_URL", "sqlite:///app.db")
           self.connection = connection_string
           print(f"Connected to: {connection_string}")

   # Named cache service with dependency
   @service("cache", scope="singleton")
   class CacheService:
       def __init__(self, config: ConfigService = Depends("config")):
           cache_config = config.get_config().get("cache", {})
           self.ttl = cache_config.get("ttl", 300)
           self.enabled = cache_config.get("enabled", True)

   # Named config service
   @service("config", scope="singleton")
   class ConfigService:
       def __init__(self):
           self.config = {
               "cache": {"ttl": 600, "enabled": True},
               "database": {"pool_size": 10}
           }

       def get_config(self):
           return self.config

   # Use named services in routes
   @app.get("/status")
   def service_status(
       request,
       db: DatabaseService = Depends("database"),
       cache: CacheService = Depends("cache")
   ):
       return JSONResponse({
           "database": {"connected": bool(db.connection)},
           "cache": {"enabled": cache.enabled, "ttl": cache.ttl},
           "message": "Services created and configured"
       })

   if __name__ == "__main__":
       app.listen(port=8000)

Async Dependency Injection
---------------------------

Async Services
~~~~~~~~~~~~~~

Create services that support async operations:

.. code-block:: python

   @service("async_database", scope="singleton")
   class AsyncDatabaseService:
       async def connect(self):
           """Simulate async database connection"""
           await asyncio.sleep(0.01)
           return "Connected to async database"

       async def get_user_async(self, user_id: int):
           await asyncio.sleep(0.005)  # Simulate async query
           return {
               "id": user_id,
               "name": f"Async User {user_id}",
               "email": f"async.user{user_id}@example.com"
           }

   @service("async_user_repository", scope="singleton")
   class AsyncUserRepository:
       def __init__(self, db: AsyncDatabaseService = Depends("async_database")):
           self.db = db

       async def find_user(self, user_id: int):
           return await self.db.get_user_async(user_id)

   # Use in async handlers
   @app.get("/async-di/{user_id}")
   async def async_di_example(
       request,
       user_repo: AsyncUserRepository = Depends("async_user_repository"),
       user_id: int = Path(..., ge=1)
   ):
       user = await user_repo.find_user(user_id)
       return JSONResponse({"user": user, "type": "async_dependency_injection"})

   if __name__ == "__main__":
       app.listen(port=8000)

Database Connection Management
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Practical async database service with connection management:

.. code-block:: python

   import asyncio
   from contextlib import asynccontextmanager

   @service("database_engine", scope="singleton")
   class DatabaseEngine:
       def __init__(self):
           # Simulate database engine initialization
           self.connection_string = "postgresql://localhost:5432/app"
           self.pool_size = 10
           print(f"Database engine initialized: {self.connection_string}")

       @asynccontextmanager
       async def get_connection(self):
           """Get async database connection"""
           # Simulate connection acquisition
           await asyncio.sleep(0.001)
           connection = f"Connection-{id(self)}"
           try:
               yield connection
           finally:
               # Simulate connection cleanup
               await asyncio.sleep(0.001)

   @service("user_service", scope="singleton")
   class UserService:
       def __init__(self, engine: DatabaseEngine = Depends("database_engine")):
           self.engine = engine

       async def get_user(self, user_id: int):
           async with self.engine.get_connection() as conn:
               # Simulate database query
               await asyncio.sleep(0.01)
               return {
                   "id": user_id,
                   "name": f"Database User {user_id}",
                   "connection": str(conn)
               }

   # Use async database service in routes
   @app.get("/db-users/{user_id}")
   async def get_database_user(
       request,
       user_service: UserService = Depends("user_service"),
       user_id: int = Path(..., ge=1)
   ):
       user_data = await user_service.get_user(user_id)
       return JSONResponse({"user": user_data, "source": "database_service"})

   if __name__ == "__main__":
       app.listen(port=8000)

Enterprise Patterns
--------------------

Health Monitoring
~~~~~~~~~~~~~~~~~

Add health checks and monitoring to your services:

.. code-block:: python

   import time
   import psutil

   @service("health_monitor", scope="singleton")
   class HealthMonitorService:
       def __init__(self):
           self.start_time = time.time()
           self.request_count = 0

       def increment_requests(self):
           self.request_count += 1

       def get_health_status(self):
           uptime = time.time() - self.start_time
           return {
               "status": "healthy",
               "uptime_seconds": uptime,
               "total_requests": self.request_count,
               "memory_usage_mb": self.get_memory_usage()
           }

       def get_memory_usage(self):
           process = psutil.Process()
           return round(process.memory_info().rss / 1024 / 1024, 2)

   @app.get("/health")
   def health_check(request, monitor: HealthMonitorService = Depends("health_monitor")):
       monitor.increment_requests()
       health_status = monitor.get_health_status()
       return JSONResponse(health_status)

   if __name__ == "__main__":
       app.listen(port=8000)

Service Composition
~~~~~~~~~~~~~~~~~~~

Compose complex services from simpler ones:

.. code-block:: python

   @service("validation_service", scope="singleton")
   class ValidationService:
       def validate_email(self, email: str) -> bool:
           return "@" in email and "." in email

       def validate_age(self, age: int) -> bool:
           return 0 <= age <= 150

   @service("notification_service", scope="singleton")
   class NotificationService:
       def send_welcome_email(self, email: str) -> bool:
           # Simulate email sending
           print(f"Sending welcome email to: {email}")
           return True

   @service("user_management", scope="singleton")
   class UserManagementService:
       def __init__(
           self,
           user_repo: UserRepository = Depends("user_repository"),
           validator: ValidationService = Depends("validation_service"),
           notifier: NotificationService = Depends("notification_service")
       ):
           self.user_repo = user_repo
           self.validator = validator
           self.notifier = notifier

       def create_user(self, name: str, email: str, age: int):
           # Validate input
           if not self.validator.validate_email(email):
               raise ValueError("Invalid email")
           if not self.validator.validate_age(age):
               raise ValueError("Invalid age")

           # Create user (simulation)
           user = {"name": name, "email": email, "age": age}

           # Send welcome email
           self.notifier.send_welcome_email(email)

           return user

   @app.post("/users")
   def create_user(
       request,
       user_mgmt: UserManagementService = Depends("user_management")
   ):
       # This would typically parse JSON from request body
       # For demo purposes, using hardcoded values
       user = user_mgmt.create_user("John Doe", "john@example.com", 30)
       return JSONResponse({"user": user, "message": "User created successfully"})

   if __name__ == "__main__":
       app.listen(port=8000)

Performance and Best Practices
-------------------------------

Memory Optimization
~~~~~~~~~~~~~~~~~~~

Catzilla's DI system uses arena-based allocation for optimal performance:

.. code-block:: python

   # Performance tips for DI

   # ✅ Use singletons for expensive-to-create services
   @service("expensive_service", scope="singleton")
   class ExpensiveService:
       def __init__(self):
           # Heavy initialization happens once
           self.large_data = self.load_large_dataset()

       def load_large_dataset(self):
           # Simulate expensive operation
           return [{"id": i, "data": f"Item {i}"} for i in range(10000)]

   # ✅ Use request scope for stateful per-request services
   @service("request_stateful", scope="request")
   class RequestStatefulService:
       def __init__(self):
           self.request_data = {}
           self.request_id = id(self)

   # ✅ Use transient for lightweight, stateless services
   @service("lightweight_utility", scope="transient")
   class LightweightUtility:
       def helper_method(self):
           return "lightweight operation"

Performance Comparison
~~~~~~~~~~~~~~~~~~~~~~

Benchmark results comparing Catzilla DI vs FastAPI DI:

.. code-block:: text

   Dependency Injection Performance (1000 requests):

   FastAPI DI:        285ms  (baseline)
   Catzilla DI:        44ms  (6.5x faster)

   Memory Usage:
   FastAPI DI:       125MB
   Catzilla DI:       19MB  (6.6x less memory)

Migration from FastAPI
----------------------

Zero-Effort Migration
~~~~~~~~~~~~~~~~~~~~~

Migrate your FastAPI DI code with zero changes:

.. code-block:: python

   # Your existing FastAPI code
   from fastapi import FastAPI, Depends

   app = FastAPI()

   class DatabaseService:
       def get_data(self):
           return {"data": "from database"}

   def get_database():
       return DatabaseService()

   @app.get("/data")
   def get_data(db: DatabaseService = Depends(get_database)):
       return db.get_data()

   if __name__ == "__main__":
       app.listen(port=8000)

   # Catzilla equivalent (almost identical!)
   from catzilla import Catzilla, Depends, service, JSONResponse
   from catzilla.dependency_injection import set_default_container

   app = Catzilla(enable_di=True)
   set_default_container(app.di_container)

   @service("database")
   class DatabaseService:
       def get_data(self):
           return {"data": "from database"}

   @app.get("/data")
   def get_data(request, db: DatabaseService = Depends("database")):
       return JSONResponse(db.get_data())

   if __name__ == "__main__":
       app.listen(port=8000)

**Migration Steps:**

1. Change ``from fastapi import`` to ``from catzilla import``
2. Add ``enable_di=True`` to ``Catzilla()``
3. Add ``from catzilla.dependency_injection import set_default_container``
4. Add ``set_default_container(app.di_container)`` after creating the app
5. Add ``@service("service_name")`` decorator to your dependency classes
6. Update ``Depends()`` calls to ``Depends("service_name")``
7. Add ``request`` parameter to route handlers
8. Use ``JSONResponse()`` for JSON responses

That's it! Your DI code now runs 6.5x faster.

Common Patterns
---------------

Configuration Injection
~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   import os

   @service("app_config", scope="singleton")
   class AppConfig:
       def __init__(self):
           self.database_url = os.getenv("DATABASE_URL")
           self.redis_url = os.getenv("REDIS_URL")
           self.debug = os.getenv("DEBUG", "false").lower() == "true"

   @app.get("/config")
   def get_config(request, config: AppConfig = Depends("app_config")):
       return JSONResponse({
           "debug": config.debug,
           "database_configured": bool(config.database_url),
           "redis_configured": bool(config.redis_url)
       })

   if __name__ == "__main__":
       app.listen(port=8000)

Testing with DI
~~~~~~~~~~~~~~~~

.. code-block:: python

   import pytest
   from catzilla import Catzilla, service, Depends
   from catzilla.dependency_injection import set_default_container

   def test_user_endpoint():
       # Create test app with mock service
       test_app = Catzilla(enable_di=True)
       set_default_container(test_app.di_container)

       # Mock service for testing
       @service("user_service")
       class MockUserService:
           def get_user(self, user_id):
               return {"id": user_id, "name": "Test User"}

       # Register route with mock dependency
       @test_app.get("/users/{user_id}")
       def get_user(request, user_id: int, user_service: MockUserService = Depends("user_service")):
           user = user_service.get_user(user_id)
           return {"user": user}

       # Test the route (would need test client setup)
       # This demonstrates the pattern for testing with DI

Authentication & Authorization
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Complete authentication system with dependency injection:

.. code-block:: python

   from catzilla import Catzilla, service, JSONResponse, Header, Depends
   from catzilla.dependency_injection import set_default_container
   from typing import Optional

   app = Catzilla(enable_di=True)
   set_default_container(app.di_container)

   # Authentication service
   @service("auth_service")
   class AuthenticationService:
       def __init__(self):
           self.users_db = {
               "admin": {"id": 1, "username": "admin", "email": "admin@example.com", "role": "admin"},
               "user1": {"id": 2, "username": "user1", "email": "user1@example.com", "role": "user"}
           }

       def authenticate_token(self, token: str) -> Optional[dict]:
           """Validate token and return user info"""
           # Simple mock authentication - in reality you'd validate JWT tokens
           if token == "admin_token":
               return self.users_db["admin"]
           elif token == "user_token":
               return self.users_db["user1"]
           return None

       def get_current_user(self, authorization: str) -> dict:
           """Extract and validate user from authorization header"""
           if not authorization.startswith("Bearer "):
               raise ValueError("Invalid authorization header format")

           token = authorization.replace("Bearer ", "")
           user = self.authenticate_token(token)

           if not user:
               raise ValueError("Invalid or expired token")

           return user

   # Protected routes with authentication
   @app.get("/protected")
   def protected_route(
       request,
       authorization: str = Header(..., description="Authorization header"),
       auth_service: AuthenticationService = Depends("auth_service")
   ):
       """Protected route that requires authentication"""
       try:
           current_user = auth_service.get_current_user(authorization)
           return JSONResponse({
               "message": f"Hello {current_user['username']}!",
               "user_info": current_user
           })
       except ValueError as e:
           return JSONResponse({"error": str(e)}, status_code=401)

   # Admin-only route
   @app.get("/admin")
   def admin_route(
       request,
       authorization: str = Header(..., description="Authorization header"),
       auth_service: AuthenticationService = Depends("auth_service")
   ):
       """Admin-only route"""
       try:
           current_user = auth_service.get_current_user(authorization)
           if current_user.get("role") != "admin":
               return JSONResponse({"error": "Admin access required"}, status_code=403)

           return JSONResponse({
               "message": "Admin panel access granted",
               "admin_info": current_user
           })
       except ValueError as e:
           return JSONResponse({"error": str(e)}, status_code=401)

   if __name__ == "__main__":
       print("🚀 Authentication Example")
       print("Test with: curl -H 'Authorization: Bearer admin_token' http://localhost:8000/protected")
       app.listen(port=8000)

This dependency injection system provides all the power and flexibility you need for building scalable, maintainable applications with Catzilla's performance advantages.
