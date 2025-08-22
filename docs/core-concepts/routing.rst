Routing
=======

Catzilla features a C-accelerated routing engine that delivers O(log n) performance through an advanced trie-based data structure. This section covers everything from basic routing to advanced patterns.

Basic Routing
-------------

Route Decorators
~~~~~~~~~~~~~~~~

Catzilla supports all standard HTTP methods with intuitive decorators:

.. code-block:: python

   from catzilla import Catzilla, JSONResponse

   app = Catzilla()

   @app.get("/")
   def home(request):
       return JSONResponse({"message": "Hello, World!"})

   @app.post("/users")
   def create_user(request):
       return JSONResponse({"message": "User created"}, status_code=201)

   @app.put("/users/{user_id}")
   def update_user(request, user_id: int):
       return JSONResponse({"message": f"User {user_id} updated"})

   @app.delete("/users/{user_id}")
   def delete_user(request, user_id: int):
       return JSONResponse({"message": f"User {user_id} deleted"})

   @app.patch("/users/{user_id}")
   def patch_user(request, user_id: int):
       return JSONResponse({"message": f"User {user_id} patched"})

   @app.head("/users/{user_id}")
   def head_user(request, user_id: int):
       return JSONResponse({})

   @app.options("/users")
   def options_users(request):
       return JSONResponse({"allowed_methods": ["GET", "POST", "PUT", "DELETE"]})

   if __name__ == "__main__":
       app.listen(port=8000)

Multiple HTTP Methods
~~~~~~~~~~~~~~~~~~~~~

Handle multiple methods for the same path:

.. code-block:: python

   # Method-specific handlers
   @app.get("/users/{user_id}")
   def get_user(request, user_id: int):
       return JSONResponse({"user_id": user_id, "method": "GET"})

   @app.put("/users/{user_id}")
   def update_user(request, user_id: int):
       return JSONResponse({"user_id": user_id, "method": "PUT"})

   # Or handle multiple methods in one function
   @app.route("/status", methods=["GET", "POST"])
   def status(request):
       method = request.method
       return JSONResponse({"status": "ok", "method": method})

Path Parameters
---------------

Simple Path Parameters
~~~~~~~~~~~~~~~~~~~~~~

Extract values directly from the URL path:

.. code-block:: python

   from catzilla import Path

   @app.get("/users/{user_id}")
   def get_user(request, user_id: int):
       return JSONResponse({"user_id": user_id})

   @app.get("/users/{user_id}/posts/{post_id}")
   def get_user_post(request, user_id: int, post_id: int):
       return JSONResponse({
           "user_id": user_id,
           "post_id": post_id
       })

Path Parameter Validation
~~~~~~~~~~~~~~~~~~~~~~~~~

Use the ``Path`` parameter for advanced validation:

.. code-block:: python

   from catzilla import Path

   @app.get("/users/{user_id}")
   def get_user(
       request,
       user_id: int = Path(..., description="User ID", ge=1, le=1000000)
   ):
       return JSONResponse({"user_id": user_id})

   @app.get("/products/{product_code}")
   def get_product(
       request,
       product_code: str = Path(..., regex=r'^[A-Z]{2}\\d{4}$', description="Product code")
   ):
       return JSONResponse({"product_code": product_code})

   @app.get("/files/{filename}")
   def get_file(
       request,
       filename: str = Path(..., min_length=1, max_length=255)
   ):
       return JSONResponse({"filename": filename})

Query Parameters
----------------

Basic Query Parameters
~~~~~~~~~~~~~~~~~~~~~~

Extract and validate query parameters:

.. code-block:: python

   from catzilla import Query

   @app.get("/search")
   def search(
       request,
       q: str = Query("", description="Search query"),
       limit: int = Query(10, ge=1, le=100, description="Results limit"),
       offset: int = Query(0, ge=0, description="Results offset"),
       sort: str = Query("name", regex=r'^(name|date|relevance)$')
   ):
       return JSONResponse({
           "query": q,
           "limit": limit,
           "offset": offset,
           "sort": sort,
           "results": []  # Your search logic here
       })

Optional and Required Parameters
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from typing import Optional

   @app.get("/users")
   def list_users(
       request,
       # Required parameter
       api_key: str = Query(..., description="API key required"),

       # Optional parameters with defaults
       active: Optional[bool] = Query(None, description="Filter by active status"),
       role: Optional[str] = Query(None, description="Filter by role"),

       # Pagination
       page: int = Query(1, ge=1),
       per_page: int = Query(20, ge=1, le=100)
   ):
       filters = {}
       if active is not None:
           filters["active"] = active
       if role is not None:
           filters["role"] = role

       return JSONResponse({
           "filters": filters,
           "pagination": {"page": page, "per_page": per_page}
       })

Headers and Form Data
---------------------

Header Parameters
~~~~~~~~~~~~~~~~~

Extract and validate HTTP headers:

.. code-block:: python

   from catzilla import Header

   @app.get("/protected")
   def protected_endpoint(
       request,
       authorization: str = Header(..., description="Authorization header"),
       user_agent: str = Header(None, alias="User-Agent"),
       content_type: str = Header("application/json", alias="Content-Type")
   ):
       return JSONResponse({
           "auth": authorization,
           "user_agent": user_agent,
           "content_type": content_type
       })

Form Data
~~~~~~~~~

Handle form submissions:

.. code-block:: python

   from catzilla import Form

   @app.post("/contact")
   def contact_form(
       request,
       name: str = Form(..., min_length=2, max_length=100),
       email: str = Form(..., regex=r'^[^@]+@[^@]+\\.[^@]+$'),
       message: str = Form(..., min_length=10, max_length=1000),
       subscribe: bool = Form(False)
   ):
       return JSONResponse({
           "message": "Form submitted successfully",
           "data": {
               "name": name,
               "email": email,
               "message": message,
               "subscribe": subscribe
           }
       }, status_code=201)

Router Groups
-------------

Catzilla's router groups allow you to organize routes hierarchically with shared prefixes and middleware.

Basic Router Groups
~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from catzilla import Catzilla, RouterGroup, JSONResponse

   app = Catzilla()

   # Create API version groups
   api_v1 = RouterGroup(prefix="/api/v1")
   api_v2 = RouterGroup(prefix="/api/v2")

   # V1 endpoints
   @api_v1.get("/users")
   def list_users_v1(request):
       return JSONResponse({
           "users": ["user1", "user2"],
           "version": "v1"
       })

   @api_v1.get("/users/{user_id}")
   def get_user_v1(request, user_id: int):
       return JSONResponse({
           "user_id": user_id,
           "version": "v1"
       })

   # V2 endpoints with enhanced features
   @api_v2.get("/users")
   def list_users_v2(
       request,
       page: int = Query(1, ge=1),
       limit: int = Query(10, ge=1, le=100)
   ):
       return JSONResponse({
           "users": [f"user{i}" for i in range((page-1)*limit + 1, page*limit + 1)],
           "version": "v2",
           "pagination": {"page": page, "limit": limit}
       })

   # Register router groups with the main app
   app.include_router(api_v1)
   app.include_router(api_v2)

   if __name__ == "__main__":
       app.listen(port=8000)

Nested Router Groups
~~~~~~~~~~~~~~~~~~~~

Create hierarchical route structures:

.. code-block:: python

   # Admin section
   admin = RouterGroup(prefix="/admin")
   admin_users = RouterGroup(prefix="/users")
   admin_reports = RouterGroup(prefix="/reports")

   # Admin user management
   @admin_users.get("/")
   def admin_list_users(request):
       return JSONResponse({"admin": True, "users": []})

   @admin_users.post("/")
   def admin_create_user(request):
       return JSONResponse({"admin": True, "message": "User created"})

   @admin_users.delete("/{user_id}")
   def admin_delete_user(request, user_id: int):
       return JSONResponse({"admin": True, "deleted_user": user_id})

   # Admin reports
   @admin_reports.get("/daily")
   def daily_report(request):
       return JSONResponse({"report": "daily", "admin": True})

   @admin_reports.get("/monthly")
   def monthly_report(request):
       return JSONResponse({"report": "monthly", "admin": True})

   # Mount nested groups
   admin.include_router(admin_users)  # /admin/users/*
   admin.include_router(admin_reports)  # /admin/reports/*
   app.include_router(admin)

Group-Level Middleware
~~~~~~~~~~~~~~~~~~~~~~

Apply middleware to entire router groups:

.. code-block:: python

   from catzilla.middleware import Middleware

   # Authentication middleware
   def auth_middleware(request, call_next):
       auth_header = request.headers.get("Authorization")
       if not auth_header or not auth_header.startswith("Bearer "):
           return JSONResponse({"error": "Authentication required"}, status_code=401)

       # Validate token here
       token = auth_header[7:]  # Remove "Bearer "
       if not validate_token(token):
           return JSONResponse({"error": "Invalid token"}, status_code=401)

       return call_next(request)

   # Create protected router group
   protected = RouterGroup(prefix="/protected", middleware=[auth_middleware])

   @protected.get("/profile")
   def get_profile(request):
       return JSONResponse({"profile": "user profile data"})

   @protected.post("/settings")
   def update_settings(request):
       return JSONResponse({"message": "Settings updated"})

   app.include_router(protected)

Advanced Routing Patterns
--------------------------

Route Priorities
~~~~~~~~~~~~~~~~

Catzilla automatically handles route priorities, with more specific routes taking precedence:

.. code-block:: python

   # More specific routes are matched first
   @app.get("/users/current")  # This will match first
   def get_current_user(request):
       return JSONResponse({"user": "current user"})

   @app.get("/users/{user_id}")  # This will match if above doesn't
   def get_user(request, user_id: str):
       return JSONResponse({"user_id": user_id})

   @app.get("/users/{user_id}/profile")  # More specific path
   def get_user_profile(request, user_id: int):
       return JSONResponse({"user_id": user_id, "profile": {}})

Wildcard Routes
~~~~~~~~~~~~~~~

Catch-all routes for handling dynamic paths:

.. code-block:: python

   @app.get("/static/{file_path:path}")
   def serve_static(request, file_path: str):
       # file_path will contain the entire remaining path
       return JSONResponse({"file_path": file_path})

   # Example matches:
   # /static/css/main.css -> file_path = "css/main.css"
   # /static/js/app.min.js -> file_path = "js/app.min.js"
   # /static/images/logo.png -> file_path = "images/logo.png"

Route with Multiple Parameters
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Complex routes with multiple parameter types:

.. code-block:: python

   @app.get("/users/{user_id}/posts/{post_id}/comments")
   def get_post_comments(
       request,
       user_id: int = Path(..., ge=1),
       post_id: int = Path(..., ge=1),
       limit: int = Query(10, ge=1, le=100),
       sort: str = Query("date", regex=r'^(date|likes|replies)$')
   ):
       return JSONResponse({
           "user_id": user_id,
           "post_id": post_id,
           "comments": [],
           "limit": limit,
           "sort": sort
       })

Async/Sync Routing
------------------

Mix Async and Sync Handlers
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Catzilla's killer feature - seamlessly mix async and sync route handlers:

.. code-block:: python

   import asyncio

   # Sync handler (good for CPU-bound tasks)
   @app.get("/sync-endpoint")
   def sync_handler(request):
       # Runs in optimized thread pool
       result = cpu_intensive_operation()
       return JSONResponse({"result": result, "type": "sync"})

   # Async handler (good for I/O-bound tasks)
   @app.get("/async-endpoint")
   async def async_handler(request):
       # Runs in event loop - non-blocking
       data = await fetch_from_database()
       return JSONResponse({"data": data, "type": "async"})

   # Mixed operations in one endpoint
   @app.get("/hybrid-endpoint")
   async def hybrid_handler(request):
       # Async I/O operations
       user_data = await fetch_user_data()

       # CPU-bound operation (could be offloaded to thread pool)
       processed_data = process_data(user_data)

       # More async I/O
       await log_request()

       return JSONResponse({"data": processed_data})

Performance Considerations
~~~~~~~~~~~~~~~~~~~~~~~~~~

Choose the right handler type for optimal performance:

.. code-block:: python

   # CPU-bound: Use sync handlers
   @app.get("/compute")
   def compute_heavy(request):
       # Mathematical calculations, data processing, etc.
       result = expensive_calculation()
       return JSONResponse({"result": result})

   # I/O-bound: Use async handlers
   @app.get("/fetch-data")
   async def fetch_external_data(request):
       # Database queries, API calls, file I/O, etc.
       data1 = await fetch_from_api1()
       data2 = await fetch_from_api2()
       return JSONResponse({"data1": data1, "data2": data2})

   # Mixed workload: Choose based on primary operation
   @app.get("/mixed-workload")
   async def mixed_handler(request):
       # If primary operation is I/O, use async
       data = await fetch_from_database()

       # CPU work can be done inline or offloaded
       processed = process_quickly(data)

       return JSONResponse({"processed": processed})

Route Registration Patterns
----------------------------

Dynamic Route Registration
~~~~~~~~~~~~~~~~~~~~~~~~~~

Register routes programmatically:

.. code-block:: python

   # Define route handlers
   def create_crud_routes(resource_name, handlers):
       @app.get(f"/{resource_name}")
       def list_items(request):
           return JSONResponse(handlers.list())

       @app.post(f"/{resource_name}")
       def create_item(request):
           return JSONResponse(handlers.create(request.json()))

       @app.get(f"/{resource_name}/{{item_id}}")
       def get_item(request, item_id: int):
           return JSONResponse(handlers.get(item_id))

       @app.put(f"/{resource_name}/{{item_id}}")
       def update_item(request, item_id: int):
           return JSONResponse(handlers.update(item_id, request.json()))

       @app.delete(f"/{resource_name}/{{item_id}}")
       def delete_item(request, item_id: int):
           return JSONResponse(handlers.delete(item_id))

   # Use it for multiple resources
   create_crud_routes("users", UserHandlers())
   create_crud_routes("posts", PostHandlers())
   create_crud_routes("comments", CommentHandlers())

Route Validation
~~~~~~~~~~~~~~~~

Comprehensive validation example:

.. code-block:: python

   from catzilla import BaseModel, Field, Query, Path, Header
   from typing import Optional, List
   from enum import Enum

   class SortOrder(str, Enum):
       ASC = "asc"
       DESC = "desc"

   class UserFilter(BaseModel):
       active: Optional[bool] = None
       role: Optional[str] = Field(None, regex=r'^(admin|user|guest)$')
       min_age: Optional[int] = Field(None, ge=0, le=120)

   @app.get("/advanced-search")
   def advanced_search(
       request,
       # Path parameters
       category: str = Path(..., regex=r'^[a-z]+$'),

       # Query parameters
       q: str = Query(..., min_length=1, max_length=100),
       sort: SortOrder = Query(SortOrder.ASC),
       limit: int = Query(10, ge=1, le=100),
       offset: int = Query(0, ge=0),
       tags: List[str] = Query([]),

       # Headers
       api_key: str = Header(..., alias="X-API-Key"),
       client_version: Optional[str] = Header(None, alias="X-Client-Version")
   ):
       return JSONResponse({
           "category": category,
           "query": q,
           "sort": sort,
           "pagination": {"limit": limit, "offset": offset},
           "tags": tags,
           "api_key": api_key[:8] + "...",  # Don't expose full key
           "client_version": client_version
       })

Error Handling in Routes
-------------------------

Handle routing errors gracefully:

.. code-block:: python

   from catzilla import JSONResponse

   @app.get("/users/{user_id}")
   def get_user(request, user_id: int = Path(..., ge=1)):
       # Simulate user lookup
       if user_id > 1000:
           return JSONResponse(
               {"error": f"User {user_id} not found"},
               status_code=404
           )

       if user_id == 999:
           return JSONResponse(
               {"error": "Access denied to this user"},
               status_code=403
           )

       return JSONResponse({
           "user_id": user_id,
           "name": f"User {user_id}"
       })

Performance Monitoring
----------------------

Monitor route performance:

.. code-block:: python

   import time
   from catzilla.core import get_route_stats

   @app.get("/performance-stats")
   def get_performance_stats(request):
       return JSONResponse({
           "router": "C-accelerated",
           "lookup_time": "O(log n)",
           "stats": get_route_stats()
       })

   @app.get("/benchmark")
   def benchmark_route(request):
       start_time = time.time()

       # Your route logic here
       result = {"message": "Benchmark complete"}

       end_time = time.time()
       result["execution_time"] = f"{(end_time - start_time) * 1000:.2f}ms"

       return JSONResponse(result)

Best Practices
--------------

1. **Route Organization**
   - Use router groups for logical organization
   - Keep related routes together
   - Use consistent naming conventions

2. **Parameter Validation**
   - Always validate path parameters
   - Use appropriate constraints (ge, le, regex)
   - Provide meaningful descriptions

3. **Performance Optimization**
   - Use sync handlers for CPU-bound operations
   - Use async handlers for I/O-bound operations
   - Leverage Catzilla's automatic optimizations

4. **Error Handling**
   - Use JSONResponse with status codes for error responses
   - Provide meaningful error messages
   - Handle edge cases gracefully

5. **Documentation**
   - Add docstrings to route handlers
   - Use parameter descriptions
   - Document expected response formats

Next Steps
----------

Now that you understand Catzilla's routing system, explore:

- :doc:`middleware` - Handling requests and responses
- :doc:`validation` - Advanced validation patterns
- :doc:`middleware` - Middleware for cross-cutting concerns
- :doc:`../examples/basic-routing` - Complete routing examples
