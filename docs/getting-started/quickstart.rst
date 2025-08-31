Quickstart
==========

This guide will get you up and running with Catzilla in just a few minutes. We'll build a complete API with validation, async support, and real-world patterns.

Your First Catzilla App
------------------------

Let's start with a simple "Hello World" application:

.. code-block:: python

   # main.py
   from catzilla import Catzilla, JSONResponse

   # Initialize Catzilla
   app = Catzilla(
       production=False,    # Enable development features
       show_banner=True,    # Show startup banner
       log_requests=True    # Log requests in development
   )

   @app.get("/")
   def home(request):
       return JSONResponse({
           "message": "Hello, Catzilla!",
           "framework": "Catzilla",
           "performance": "High-performance web framework"
       })

   if __name__ == "__main__":
       app.listen(port=8000)

Run your application:

.. code-block:: bash

   python main.py

Visit `http://localhost:8000` to see your API in action! 🚀

Async/Sync Hybrid Support
--------------------------

Catzilla's key feature is seamless async/sync mixing. You can use both patterns in the same application:

.. code-block:: python

   import asyncio
   from catzilla import Catzilla, JSONResponse

   app = Catzilla()

   # Sync handler (perfect for CPU-bound tasks)
   @app.get("/sync")
   def sync_endpoint(request):
       # Runs in optimized thread pool
       return JSONResponse({"type": "sync", "execution": "thread_pool"})

   # Async handler (perfect for I/O-bound tasks)
   @app.get("/async")
   async def async_endpoint(request):
       # Runs in event loop - non-blocking!
       await asyncio.sleep(0.1)  # Simulated database call
       return JSONResponse({"type": "async", "execution": "event_loop"})

   if __name__ == "__main__":
       app.listen(port=8000)

**Key Benefits:**

- ✅ **Automatic Detection** - Catzilla automatically detects handler types
- ✅ **Optimal Execution** - Sync handlers use thread pools, async uses event loop
- ✅ **No Migration Needed** - Existing sync code works unchanged
- ✅ **True Concurrency** - Async handlers don't block sync handlers

Path Parameters & Validation
-----------------------------

Catzilla provides automatic path parameter extraction and validation:

.. code-block:: python

   import asyncio
   from catzilla import Catzilla, JSONResponse, Path

   app = Catzilla()

   # Simple path parameter
   @app.get("/users/{user_id}")
   def get_user(request, user_id: int = Path(..., description="User ID", ge=1)):
       return JSONResponse({
           "user_id": user_id,
           "message": f"Retrieved user {user_id}"
       })

   # Async version with database simulation
   @app.get("/async-users/{user_id}")
   async def get_user_async(request, user_id: int = Path(..., ge=1)):
       # Simulate database lookup
       await asyncio.sleep(0.05)

       user_data = {
           "id": user_id,
           "name": f"User {user_id}",
           "email": f"user{user_id}@example.com"
       }

       return JSONResponse({"user": user_data})

   if __name__ == "__main__":
       app.listen(port=8000)
Test your endpoints:

.. code-block:: bash

   curl http://localhost:8000/users/123
   curl http://localhost:8000/async-users/456

Query Parameters
----------------

Handle query parameters with automatic validation:

.. code-block:: python

   import asyncio
   from catzilla import Catzilla, JSONResponse, Query

   app = Catzilla()

   @app.get("/search")
   def search(
       request,
       q: str = Query("", description="Search query"),
       limit: int = Query(10, ge=1, le=100, description="Results limit"),
       offset: int = Query(0, ge=0, description="Results offset")
   ):
       return JSONResponse({
           "query": q,
           "limit": limit,
           "offset": offset,
           "results": [f"Result {i}" for i in range(offset, offset + min(limit, 5))]
       })

   # Async search with external API simulation
   @app.get("/async-search")
   async def async_search(
       request,
       q: str = Query(""),
       limit: int = Query(10, ge=1, le=100)
   ):
       # Simulate external API call
       await asyncio.sleep(0.2)

       return JSONResponse({
           "query": q,
           "results": [{"title": f"Enhanced Result {i}"} for i in range(limit)],
           "source": "external_api"
       })

   if __name__ == "__main__":
       app.listen(port=8000)

Test with query parameters:

.. code-block:: bash

   curl "http://localhost:8000/search?q=python&limit=5"
   curl "http://localhost:8000/async-search?q=catzilla&limit=3"

Request Body Validation with BaseModel
---------------------------------------

Catzilla includes Pydantic-compatible BaseModel for request validation:

.. code-block:: python

   import asyncio
   from catzilla import Catzilla, JSONResponse, BaseModel, Field
   from typing import Optional

   app = Catzilla()

   # Define your data model
   class UserCreate(BaseModel):
       """User creation model with validation"""
       name: str = Field(min_length=2, max_length=50, description="User name")
       email: str = Field(regex=r'^[^@]+@[^@]+\.[^@]+$', description="Email address")
       age: Optional[int] = Field(None, ge=13, le=120, description="User age")

   # Sync handler with validation
   @app.post("/users")
   def create_user(request, user: UserCreate):
       return JSONResponse({
           "message": "User created successfully",
           "user": {
               "name": user.name,
               "email": user.email,
               "age": user.age
           }
       }, status_code=201)

   # Async handler with database simulation
   @app.post("/async-users")
   async def create_user_async(request, user: UserCreate):
       # Simulate database insert
       await asyncio.sleep(0.1)

       return JSONResponse({
           "message": "User created in database",
           "user": {
               "name": user.name,
               "email": user.email,
               "age": user.age,
               "id": 123  # Simulated generated ID
           }
       }, status_code=201)

   if __name__ == "__main__":
       app.listen(port=8000)

Test with JSON data:

.. code-block:: bash

   curl -X POST http://localhost:8000/users \\
        -H "Content-Type: application/json" \\
        -d '{"name": "John Doe", "email": "john@example.com", "age": 30}'

Complete Example Application
----------------------------

Here's a complete example combining all the concepts:

.. code-block:: python

   # complete_app.py
   import asyncio
   from typing import Optional
   from catzilla import (
       Catzilla, JSONResponse, BaseModel, Field,
       Path, Query, ValidationError
   )

   app = Catzilla(
       production=False,
       show_banner=True,
       log_requests=True
   )

   # Data models
   class User(BaseModel):
       name: str = Field(min_length=2, max_length=50)
       email: str = Field(regex=r'^[^@]+@[^@]+\.[^@]+$')
       age: Optional[int] = Field(None, ge=13, le=120)

   class UserUpdate(BaseModel):
       name: Optional[str] = Field(None, min_length=2, max_length=50)
       email: Optional[str] = Field(None, regex=r'^[^@]+@[^@]+\.[^@]+$')
       age: Optional[int] = Field(None, ge=13, le=120)

   # In-memory storage for demo
   users_db = {}
   next_id = 1

   # Routes
   @app.get("/")
   def home(request):
       return JSONResponse({
           "message": "Welcome to Catzilla Complete Example!",
           "features": [
               "Async/Sync hybrid support",
               "Auto-validation with BaseModel",
               "Path and query parameters",
               "High-performance web framework"
           ],
           "endpoints": [
               "GET /users - List users",
               "POST /users - Create user",
               "GET /users/{id} - Get user",
               "PUT /users/{id} - Update user",
               "DELETE /users/{id} - Delete user"
           ]
       })

   @app.get("/users")
   def list_users(
       request,
       limit: int = Query(10, ge=1, le=100),
       offset: int = Query(0, ge=0)
   ):
       user_list = list(users_db.values())[offset:offset + limit]
       return JSONResponse({
           "users": user_list,
           "total": len(users_db),
           "limit": limit,
           "offset": offset
       })

   @app.post("/users")
   def create_user(request, user: User):
       global next_id
       user_data = {
           "id": next_id,
           "name": user.name,
           "email": user.email,
           "age": user.age
       }
       users_db[next_id] = user_data
       next_id += 1

       return JSONResponse(user_data, status_code=201)

   @app.get("/users/{user_id}")
   def get_user(request, user_id: int = Path(..., ge=1)):
       if user_id not in users_db:
           return JSONResponse(
               {"error": "User not found"},
               status_code=404
           )
       return JSONResponse(users_db[user_id])

   @app.put("/users/{user_id}")
   def update_user(request, user: UserUpdate, user_id: int = Path(..., ge=1)):
       if user_id not in users_db:
           return JSONResponse(
               {"error": "User not found"},
               status_code=404
           )

       # Update only provided fields
       user_data = users_db[user_id]
       if user.name is not None:
           user_data["name"] = user.name
       if user.email is not None:
           user_data["email"] = user.email
       if user.age is not None:
           user_data["age"] = user.age

       return JSONResponse(user_data)

   @app.delete("/users/{user_id}")
   def delete_user(request, user_id: int = Path(..., ge=1)):
       if user_id not in users_db:
           return JSONResponse(
               {"error": "User not found"},
               status_code=404
           )

       deleted_user = users_db.pop(user_id)
       return JSONResponse({
           "message": "User deleted successfully",
           "user": deleted_user
       })

   # Async endpoints for demonstration
   @app.get("/async-users")
   async def list_users_async(
       request,
       limit: int = Query(10, ge=1, le=100)
   ):
       # Simulate database query
       await asyncio.sleep(0.1)

       user_list = list(users_db.values())[:limit]
       return JSONResponse({
           "users": user_list,
           "total": len(users_db),
           "query_time": "0.1s",
           "source": "async_database"
       })

   @app.get("/health")
   def health_check(request):
       return JSONResponse({
           "status": "healthy",
           "version": "0.2.0",
           "users_count": len(users_db),
           "async_support": True
       })

   if __name__ == "__main__":
       print("🚀 Starting Complete Catzilla Example")
       print("📋 Available endpoints:")
       print("   GET  /              - API documentation")
       print("   GET  /users         - List users")
       print("   POST /users         - Create user")
       print("   GET  /users/{id}    - Get user")
       print("   PUT  /users/{id}    - Update user")
       print("   DELETE /users/{id}  - Delete user")
       print("   GET  /async-users   - Async user list")
       print("   GET  /health        - Health check")
       print()
       print("🌐 Server starting on http://localhost:8000")

       app.listen(port=8000)

Testing Your API
-----------------

Save the complete example as `complete_app.py` and test it:

.. code-block:: bash

   # Start the server
   python complete_app.py

   # Test the endpoints
   curl http://localhost:8000/

   # Create a user
   curl -X POST http://localhost:8000/users \\
        -H "Content-Type: application/json" \\
        -d '{"name": "Alice", "email": "alice@example.com", "age": 25}'

   # List users
   curl http://localhost:8000/users

   # Get specific user
   curl http://localhost:8000/users/1

   # Update user
   curl -X PUT http://localhost:8000/users/1 \\
        -H "Content-Type: application/json" \\
        -d '{"age": 26}'

   # Test async endpoint
   curl http://localhost:8000/async-users

Performance Comparison Demo
---------------------------

Want to see Catzilla's performance in action? Add this endpoint to test concurrent operations:

.. code-block:: python

   import asyncio
   import time
   from catzilla import Catzilla, JSONResponse

   app = Catzilla()

   @app.get("/performance-test")
   async def performance_test(request):
       start_time = time.time()

       # Simulate multiple async operations running concurrently
       tasks = [
           asyncio.sleep(0.1),  # Database query
           asyncio.sleep(0.05), # Cache lookup
           asyncio.sleep(0.08), # External API call
           asyncio.sleep(0.03)  # Log write
       ]

       # Run all operations concurrently
       await asyncio.gather(*tasks)

       total_time = time.time() - start_time

       return JSONResponse({
           "message": "Performance test completed",
           "operations": 4,
           "sequential_time_would_be": "0.26s",
           "actual_concurrent_time": f"{total_time:.3f}s",
           "performance_gain": f"{((0.26 - total_time) / 0.26 * 100):.1f}%"
       })

   if __name__ == "__main__":
       app.listen(port=8000)

Error Handling
--------------

Catzilla automatically handles validation errors and provides detailed error messages:

.. code-block:: bash

   # Try invalid data
   curl -X POST http://localhost:8000/users \\
        -H "Content-Type: application/json" \\
        -d '{"name": "A", "email": "invalid-email", "age": 200}'

You'll get a detailed validation error response:

.. code-block:: json

   {
     "error": "Validation failed",
     "details": [
       {
         "field": "name",
         "message": "String should have at least 2 characters",
         "value": "A"
       },
       {
         "field": "email",
         "message": "String should match pattern '^[^@]+@[^@]+\\.[^@]+$'",
         "value": "invalid-email"
       },
       {
         "field": "age",
         "message": "Input should be less than or equal to 120",
         "value": 200
       }
     ]
   }

What's Next?
------------

Congratulations! You've built a complete REST API with Catzilla. Now explore more advanced features:

**Core Concepts**
  - :doc:`../core-concepts/routing` - Advanced routing patterns
  - :doc:`../core-concepts/validation` - Complex validation scenarios
  - :doc:`../core-concepts/async-sync-hybrid` - Deep dive into async/sync mixing

**Advanced Features**
  - :doc:`../core-concepts/dependency-injection` - Service management and DI
  - :doc:`../features/caching` - Multi-layer caching strategies
  - :doc:`../features/background-tasks` - Async task processing
  - :doc:`../core-concepts/middleware` - Request/response middleware

**Practical Examples**
  - :doc:`../guides/recipes` - Real-world patterns and solutions
  - :doc:`../examples/basic-routing` - JWT auth and security
  - :doc:`../features/file-handling` - File uploads and processing

Why Catzilla?
-------------

After completing this quickstart, you've experienced:

- ✅ **Fast Development** - Build APIs in minutes, not hours
- ✅ **High Performance** - Optimized speed and efficiency
- ✅ **Easy Learning** - If you know FastAPI, you know Catzilla
- ✅ **Flexible Architecture** - Async/sync hybrid for any workload
- ✅ **Production Ready** - Built-in validation, error handling, and monitoring

Ready to build something amazing? Let's dive deeper! 🚀
