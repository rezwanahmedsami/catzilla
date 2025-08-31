Basic Routing Examples
======================

This page provides comprehensive examples of Catzilla's routing capabilities, from simple endpoints to advanced patterns. All examples are based on working code from the Catzilla examples repository.

Hello World
-----------

The simplest possible Catzilla application:

.. code-block:: python

   from catzilla import Catzilla, JSONResponse

   app = Catzilla()

   @app.get("/")
   def home(request):
       return JSONResponse({
           "message": "Hello, Catzilla!",
           "performance": "High-performance web framework"
       })

   if __name__ == "__main__":
       app.listen(port=8000)

Async/Sync Hybrid Example
--------------------------

Catzilla's killer feature - seamlessly mixing async and sync handlers:

.. code-block:: python

   from catzilla import Catzilla, JSONResponse
   import asyncio
   import time

   app = Catzilla(
       production=False,
       show_banner=True,
       log_requests=True
   )

   # Sync handler (perfect for CPU-bound tasks)
   @app.get("/sync")
   def sync_endpoint(request):
       """Runs in optimized thread pool"""
       start_time = time.time()

       # Simulate CPU-bound work
       result = sum(i * i for i in range(10000))

       return JSONResponse({
           "result": result,
           "handler_type": "sync",
           "execution": "thread_pool",
           "time": f"{time.time() - start_time:.3f}s"
       })

   # Async handler (perfect for I/O-bound tasks)
   @app.get("/async")
   async def async_endpoint(request):
       """Runs in event loop - non-blocking"""
       start_time = time.time()

       # Simulate I/O-bound work (database, API calls, etc.)
       await asyncio.sleep(0.1)

       return JSONResponse({
           "message": "Completed async operation",
           "handler_type": "async",
           "execution": "event_loop",
           "time": f"{time.time() - start_time:.3f}s"
       })

   # Performance comparison endpoint
   @app.get("/performance-test")
   async def performance_test(request):
       """Demonstrates concurrent async operations"""
       start_time = time.time()

       # Run multiple I/O operations concurrently
       tasks = [
           asyncio.sleep(0.1),  # Database query
           asyncio.sleep(0.05), # Cache lookup
           asyncio.sleep(0.08), # External API call
           asyncio.sleep(0.03)  # Log write
       ]

       await asyncio.gather(*tasks)
       total_time = time.time() - start_time

       return JSONResponse({
           "operations": 4,
           "sequential_time_would_be": "0.26s",
           "actual_concurrent_time": f"{total_time:.3f}s",
           "performance_gain": f"{((0.26 - total_time) / 0.26 * 100):.1f}%"
       })

    if __name__ == "__main__":
        app.listen(port=8000)

Path Parameters
---------------

Extract and validate values from URL paths:

.. code-block:: python

   from catzilla import Path

   # Simple path parameter
   @app.get("/users/{user_id}")
   def get_user(request, user_id: int):
       return JSONResponse({
           "user_id": user_id,
           "name": f"User {user_id}"
       })

   # Path parameter with validation
   @app.get("/users/{user_id}/profile")
   def get_user_profile(
       request,
       user_id: int = Path(..., description="User ID", ge=1, le=1000000)
   ):
       return JSONResponse({
           "user_id": user_id,
           "profile": {
               "name": f"User {user_id}",
               "email": f"user{user_id}@example.com"
           }
       })

   # Multiple path parameters
   @app.get("/users/{user_id}/posts/{post_id}")
   def get_user_post(request, user_id: int, post_id: int):
       return JSONResponse({
           "user_id": user_id,
           "post_id": post_id,
           "post": {
               "title": f"Post {post_id} by User {user_id}",
               "content": "Sample post content"
           }
       })

   # Async version with database simulation
   @app.get("/async-users/{user_id}")
   async def get_user_async(
       request,
       user_id: int = Path(..., description="User ID", ge=1)
   ):
       # Simulate database lookup
       await asyncio.sleep(0.05)

       user_data = {
           "id": user_id,
           "name": f"User {user_id}",
           "email": f"user{user_id}@example.com",
           "created_at": "2025-01-14T10:00:00Z"
       }

       return JSONResponse({
           "user": user_data,
           "db_query_time": "0.05s",
           "handler_type": "async"
       })

Query Parameters
----------------

Handle URL query parameters with validation:

.. code-block:: python

   from catzilla import Query
   from typing import Optional

   @app.get("/search")
   def search(
       request,
       q: str = Query("", description="Search query"),
       limit: int = Query(10, ge=1, le=100, description="Results limit"),
       offset: int = Query(0, ge=0, description="Results offset"),
       sort: str = Query("name", regex=r'^(name|date|relevance)$')
   ):
       # Simulate search results
       results = [
           {"id": i, "title": f"Result {i}", "score": 100 - i}
           for i in range(offset, offset + min(limit, 5))
       ]

       return JSONResponse({
           "query": q,
           "pagination": {
               "limit": limit,
               "offset": offset,
               "total": 100
           },
           "sort": sort,
           "results": results
       })

   # Async search with external API simulation
   @app.get("/async-search")
   async def async_search(
       request,
       q: str = Query("", description="Search query"),
       limit: int = Query(10, ge=1, le=100),
       include_external: bool = Query(False)
   ):
       # Local search (fast)
       local_results = [f"Local result {i}" for i in range(limit)]

       external_results = []
       if include_external:
           # Simulate external API call
           await asyncio.sleep(0.2)
           external_results = [f"External result {i}" for i in range(3)]

       return JSONResponse({
           "query": q,
           "local_results": local_results,
           "external_results": external_results,
           "total": len(local_results) + len(external_results),
           "api_call_time": "0.2s" if include_external else "0s"
       })

Request Body Validation
-----------------------

Use BaseModel for automatic request validation:

.. code-block:: python

   from catzilla import BaseModel, Field
   from typing import Optional, List

   class UserCreate(BaseModel):
       """User creation model with validation"""
       name: str = Field(min_length=2, max_length=50, description="User name")
       email: str = Field(regex=r'^[^@]+@[^@]+\.[^@]+$', description="Email address")
       age: Optional[int] = Field(None, ge=13, le=120, description="User age")
       tags: List[str] = Field([], max_items=10, description="User tags")

   class UserUpdate(BaseModel):
       """User update model - all fields optional"""
       name: Optional[str] = Field(None, min_length=2, max_length=50)
       email: Optional[str] = Field(None, regex=r'^[^@]+@[^@]+\.[^@]+$')
       age: Optional[int] = Field(None, ge=13, le=120)

   # In-memory storage for demo
   users_db = {}
   next_id = 1

   # Create user (sync)
   @app.post("/users")
   def create_user(request, user: UserCreate):
       global next_id

       user_data = {
           "id": next_id,
           "name": user.name,
           "email": user.email,
           "age": user.age,
           "tags": user.tags,
           "created_at": "2025-01-14T10:00:00Z"
       }

       users_db[next_id] = user_data
       next_id += 1

       return JSONResponse(user_data, status_code=201)

   # Create user (async with database simulation)
   @app.post("/async-users")
   async def create_user_async(request, user: UserCreate):
       global next_id

       # Simulate database operations
       await asyncio.sleep(0.1)  # Database insert
       await asyncio.sleep(0.05) # Email verification send

       user_data = {
           "id": next_id,
           "name": user.name,
           "email": user.email,
           "age": user.age,
           "tags": user.tags,
           "created_at": "2025-01-14T10:00:00Z",
           "verification_sent": True
       }

       users_db[next_id] = user_data
       next_id += 1

       return JSONResponse(user_data, status_code=201)

   # Update user
   @app.put("/users/{user_id}")
   def update_user(
       request,
       user: UserUpdate,
       user_id: int = Path(..., ge=1)
   ):
       if user_id not in users_db:
           return JSONResponse(
               {"error": "User not found"},
               status_code=404
           )

       user_data = users_db[user_id]

       # Update only provided fields
       if user.name is not None:
           user_data["name"] = user.name
       if user.email is not None:
           user_data["email"] = user.email
       if user.age is not None:
           user_data["age"] = user.age

       user_data["updated_at"] = "2025-01-14T10:30:00Z"

       return JSONResponse(user_data)

Complete CRUD Example
---------------------

A full CRUD (Create, Read, Update, Delete) API example:

.. code-block:: python

   @app.get("/")
   def api_home(request):
       """API documentation and endpoints"""
       return JSONResponse({
           "message": "Catzilla CRUD API Example",
           "version": "0.2.0",
           "endpoints": {
               "users": {
                   "GET /users": "List all users",
                   "POST /users": "Create new user",
                   "GET /users/{id}": "Get user by ID",
                   "PUT /users/{id}": "Update user",
                   "DELETE /users/{id}": "Delete user"
               },
               "async_endpoints": {
                   "GET /async-users": "List users (async)",
                   "POST /async-users": "Create user (async)",
                   "GET /async-users/{id}": "Get user (async)"
               }
           },
           "features": [
               "Auto-validation with BaseModel",
               "Path and query parameter validation",
               "Async/sync hybrid support",
               "High-performance web framework"
           ]
       })

   @app.get("/users")
   def list_users(
       request,
       limit: int = Query(10, ge=1, le=100),
       offset: int = Query(0, ge=0),
       search: Optional[str] = Query(None, min_length=1)
   ):
       """List users with pagination and search"""
       user_list = list(users_db.values())

       # Apply search filter
       if search:
           user_list = [
               user for user in user_list
               if search.lower() in user.get("name", "").lower()
           ]

       # Apply pagination
       paginated_users = user_list[offset:offset + limit]

       return JSONResponse({
           "users": paginated_users,
           "pagination": {
               "total": len(user_list),
               "limit": limit,
               "offset": offset,
               "has_more": offset + limit < len(user_list)
           },
           "search": search
       })

   @app.get("/users/{user_id}")
   def get_user(request, user_id: int = Path(..., ge=1)):
       """Get user by ID"""
       if user_id not in users_db:
           return JSONResponse(
               {"error": f"User {user_id} not found"},
               status_code=404
           )

       return JSONResponse(users_db[user_id])

   @app.delete("/users/{user_id}")
   def delete_user(request, user_id: int = Path(..., ge=1)):
       """Delete user by ID"""
       if user_id not in users_db:
           return JSONResponse(
               {"error": f"User {user_id} not found"},
               status_code=404
           )

       deleted_user = users_db.pop(user_id)

       return JSONResponse({
           "message": f"User {user_id} deleted successfully",
           "deleted_user": deleted_user
       })

   # Async versions for I/O-heavy operations
   @app.get("/async-users")
   async def list_users_async(
       request,
       limit: int = Query(10, ge=1, le=100)
   ):
       """Async user listing with simulated database query"""
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
       """Health check endpoint"""
       return JSONResponse({
           "status": "healthy",
           "version": "0.2.0",
           "users_count": len(users_db),
           "features": {
               "async_support": True,
               "validation": True,
               "c_acceleration": True
           }
       })

Error Handling
--------------

Comprehensive error handling examples:

.. code-block:: python

   from catzilla import JSONResponse

   @app.get("/users/{user_id}/profile")
   def get_user_profile_with_errors(
       request,
       user_id: int = Path(..., ge=1, le=1000000)
   ):
       """Demonstrate error handling patterns"""

       # Simulate different error conditions
       if user_id == 999:
           return JSONResponse(
               {"error": "Access denied to this user profile"},
               status_code=403
           )

       if user_id > 1000:
           return JSONResponse(
               {"error": f"User {user_id} not found in our system"},
               status_code=404
           )

       if user_id == 500:
           return JSONResponse(
               {"error": "Internal server error occurred"},
               status_code=500
           )

       # Success case
       return JSONResponse({
           "user_id": user_id,
           "profile": {
               "name": f"User {user_id}",
               "email": f"user{user_id}@example.com",
               "status": "active"
           }
       })

Running the Examples
--------------------

Save any of these examples as a Python file and run:

.. code-block:: bash

   # Save as basic_routing_example.py
   python basic_routing_example.py

   # Server starts on http://localhost:8000

Testing the API
---------------

Test your endpoints using curl:

.. code-block:: bash

   # Basic endpoints
   curl http://localhost:8000/
   curl http://localhost:8000/sync
   curl http://localhost:8000/async

   # Path parameters
   curl http://localhost:8000/users/123
   curl http://localhost:8000/async-users/456

   # Query parameters
   curl "http://localhost:8000/search?q=python&limit=5&sort=relevance"
   curl "http://localhost:8000/async-search?q=catzilla&include_external=true"

   # Create user
   curl -X POST http://localhost:8000/users \\
        -H "Content-Type: application/json" \\
        -d '{
          "name": "John Doe",
          "email": "john@example.com",
          "age": 30,
          "tags": ["developer", "python"]
        }'

   # Update user
   curl -X PUT http://localhost:8000/users/1 \\
        -H "Content-Type: application/json" \\
        -d '{"age": 31}'

   # List users with pagination
   curl "http://localhost:8000/users?limit=5&offset=0"

   # Health check
   curl http://localhost:8000/health

Key Features Demonstrated
-------------------------

1. **Async/Sync Hybrid**
   - Automatic handler type detection
   - Optimal execution context for each handler type
   - Performance benefits of concurrent async operations

2. **Auto-Validation**
   - BaseModel for request body validation
   - Path parameter validation with constraints
   - Query parameter validation with types and constraints

3. **C-Accelerated Performance**
   - Fast routing with O(log n) lookup
   - Optimized request/response handling
   - Exceptional performance with C-accelerated routing

4. **Developer-Friendly API**
   - Intuitive decorators and patterns
   - Comprehensive error handling
   - Easy migration from FastAPI

Next Steps
----------

What's Next?
------------

Now that you understand basic routing, explore these advanced topics:

- :doc:`../core-concepts/validation` - Learn about request/response validation with BaseModel
- :doc:`../core-concepts/dependency-injection` - Explore dependency injection patterns
- :doc:`../core-concepts/middleware` - Add middleware for authentication, logging, etc.
- :doc:`../guides/recipes` - Real-world application patterns
