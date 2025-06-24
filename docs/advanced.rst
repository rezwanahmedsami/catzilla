Advanced Guide
==============

.. image:: _static/logo.png
   :alt: Catzilla Logo
   :width: 120px
   :align: right

This guide covers advanced Catzilla features for building production-ready web applications. You'll learn about dynamic routing patterns, comprehensive error handling, CLI deployment, and performance optimization.

Dynamic Routes and Patterns
----------------------------

Advanced Path Parameters
~~~~~~~~~~~~~~~~~~~~~~~~~

Catzilla's C-powered trie router supports sophisticated path patterns:

.. code-block:: python

   from catzilla import App, JSONResponse

   app = App()

   # Nested path parameters
   @app.get("/users/{user_id}/posts/{post_id}/comments/{comment_id}")
   def get_comment(request):
       params = request.path_params
       return JSONResponse({
           "user_id": params["user_id"],
           "post_id": params["post_id"],
           "comment_id": params["comment_id"],
           "content": f"Comment {params['comment_id']} on post {params['post_id']}"
       })

   # Mixed static and dynamic segments
   @app.get("/api/v1/users/{user_id}/profile/settings")
   def get_user_settings(request):
       user_id = request.path_params["user_id"]
       return JSONResponse({
           "user_id": user_id,
           "settings": {"theme": "dark", "notifications": True}
       })

   # Optional-like patterns with multiple routes
   @app.get("/blog")
   def blog_home(request):
       return JSONResponse({"posts": ["post1", "post2", "post3"]})

   @app.get("/blog/{slug}")
   def blog_post(request):
       slug = request.path_params["slug"]
       return JSONResponse({
           "slug": slug,
           "title": f"Blog post: {slug}",
           "content": "Blog post content here..."
       })

   if __name__ == "__main__":
       app.listen(host="127.0.0.1", port=8000)

Route Organization with Router Groups
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Create modular, maintainable applications using router groups:

.. code-block:: python

   from catzilla import App, JSONResponse, RouterGroup

   app = App()

   # API versioning with router groups
   v1_api = RouterGroup(prefix="/api/v1", tags=["v1"])
   v2_api = RouterGroup(prefix="/api/v2", tags=["v2"])

   # Authentication router
   auth_router = RouterGroup(prefix="/auth", tags=["authentication"])

   # Admin panel router
   admin_router = RouterGroup(prefix="/admin", tags=["admin"])

   # V1 API routes
   @v1_api.get("/users")
   def v1_list_users(request):
       return JSONResponse({"version": "v1", "users": ["alice", "bob"]})

   @v1_api.get("/users/{user_id}")
   def v1_get_user(request):
       user_id = request.path_params["user_id"]
       return JSONResponse({
           "version": "v1",
           "user": {"id": user_id, "name": f"User {user_id}"}
       })

   # V2 API routes (enhanced)
   @v2_api.get("/users")
   def v2_list_users(request):
       page = int(request.query_params.get("page", "1"))
       limit = int(request.query_params.get("limit", "10"))

       return JSONResponse({
           "version": "v2",
           "users": [f"user_{i}" for i in range(page*limit, (page+1)*limit)],
           "pagination": {"page": page, "limit": limit, "total": 100}
       })

   @v2_api.get("/users/{user_id}")
   def v2_get_user(request):
       user_id = request.path_params["user_id"]
       return JSONResponse({
           "version": "v2",
           "user": {
               "id": user_id,
               "name": f"User {user_id}",
               "email": f"user{user_id}@example.com",
               "created_at": "2025-01-01T00:00:00Z"
           }
       })

   # Authentication routes
   @auth_router.post("/login")
   def login(request):
       credentials = request.json()
       return JSONResponse({
           "message": "Login successful",
           "token": "jwt_token_here",
           "user": credentials.get("username")
       })

   @auth_router.post("/logout")
   def logout(request):
       return JSONResponse({"message": "Logged out successfully"})

   # Admin routes
   @admin_router.get("/stats")
   def admin_stats(request):
       return JSONResponse({
           "total_users": 150,
           "active_sessions": 45,
           "requests_today": 2500
       })

   @admin_router.get("/users/{user_id}/ban")
   def ban_user(request):
       user_id = request.path_params["user_id"]
       return JSONResponse({
           "message": f"User {user_id} has been banned",
           "admin_action": True
       })

   # Register all router groups
   app.include_router(v1_api)
   app.include_router(v2_api)
   app.include_router(auth_router)
   app.include_router(admin_router)

   # Main app routes
   @app.get("/")
   def api_info(request):
       return JSONResponse({
           "name": "Advanced API",
           "versions": ["v1", "v2"],
           "endpoints": {
               "v1_users": "/api/v1/users",
               "v2_users": "/api/v2/users",
               "login": "/auth/login",
               "admin": "/admin/stats"
           }
       })

   if __name__ == "__main__":
       app.listen(host="127.0.0.1", port=8000)

This creates a well-organized API with clear separation of concerns:

- ``/api/v1/*`` - Version 1 API endpoints
- ``/api/v2/*`` - Version 2 API endpoints
- ``/auth/*`` - Authentication endpoints
- ``/admin/*`` - Administrative endpoints

Error Handling
--------------

Production-Ready Error Management
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Catzilla provides comprehensive error handling for production applications:

.. code-block:: python

   from catzilla import App, JSONResponse, HTMLResponse

   # Create app with production mode for clean error responses
   app = App(production=True)

   # Custom exception for business logic errors
   class UserNotFoundError(Exception):
       def __init__(self, user_id):
           self.user_id = user_id
           super().__init__(f"User {user_id} not found")

   class ValidationError(Exception):
       def __init__(self, message, field=None):
           self.field = field
           super().__init__(message)

   # ==========================================
   # CUSTOM ERROR HANDLERS
   # ==========================================

   @app.exception_handler(UserNotFoundError)
   def handle_user_not_found(request, exc):
       return JSONResponse({
           "error": "User not found",
           "user_id": exc.user_id,
           "code": "USER_NOT_FOUND"
       }, status_code=404)

   @app.exception_handler(ValidationError)
   def handle_validation_error(request, exc):
       response_data = {
           "error": "Validation failed",
           "message": str(exc),
           "code": "VALIDATION_ERROR"
       }
       if exc.field:
           response_data["field"] = exc.field
       return JSONResponse(response_data, status_code=400)

   @app.exception_handler(ValueError)
   def handle_value_error(request, exc):
       return JSONResponse({
           "error": "Invalid value provided",
           "message": str(exc),
           "code": "INVALID_VALUE"
       }, status_code=400)

   # ==========================================
   # GLOBAL ERROR HANDLERS
   # ==========================================

   @app.not_found_handler
   def custom_404(request):
       if request.path.startswith("/api/"):
           # JSON response for API endpoints
           return JSONResponse({
               "error": "Endpoint not found",
               "path": request.path,
               "code": "NOT_FOUND"
           }, status_code=404)
       else:
           # HTML response for web pages
           return HTMLResponse("""
               <html>
                   <head><title>Page Not Found</title></head>
                   <body>
                       <h1>404 - Page Not Found</h1>
                       <p>The page you're looking for doesn't exist.</p>
                       <a href="/">Go Home</a>
                   </body>
               </html>
           """, status_code=404)

   @app.server_error_handler
   def custom_500(request, exc):
       # Log the error in production
       print(f"Server error: {exc}")

       return JSONResponse({
           "error": "Internal server error",
           "message": "Something went wrong on our end",
           "code": "INTERNAL_ERROR"
       }, status_code=500)

   # ==========================================
   # ROUTES THAT DEMONSTRATE ERROR HANDLING
   # ==========================================

   @app.get("/users/{user_id}")
   def get_user(request):
       user_id = request.path_params["user_id"]

       # Simulate user lookup
       if user_id == "999":
           raise UserNotFoundError(user_id)

       return JSONResponse({
           "id": user_id,
           "name": f"User {user_id}",
           "email": f"user{user_id}@example.com"
       })

   @app.post("/users")
   def create_user(request):
       try:
           data = request.json()
       except Exception:
           raise ValidationError("Invalid JSON in request body")

       # Validate required fields
       if not data.get("name"):
           raise ValidationError("Name is required", field="name")

       if not data.get("email") or "@" not in data.get("email", ""):
           raise ValidationError("Valid email is required", field="email")

       # Simulate user creation
       return JSONResponse({
           "message": "User created successfully",
           "user": data
       }, status_code=201)

   @app.get("/divide/{a}/{b}")
   def divide_numbers(request):
       try:
           a = float(request.path_params["a"])
           b = float(request.path_params["b"])
       except ValueError:
           raise ValueError("Parameters must be numbers")

       if b == 0:
           raise ValueError("Cannot divide by zero")

       return JSONResponse({"result": a / b})

   @app.get("/error-demo")
   def trigger_server_error(request):
       # This will trigger the server_error_handler
       raise Exception("This is a demo server error")

   @app.get("/")
   def home(request):
       return JSONResponse({
           "message": "Error handling demo API",
           "endpoints": {
               "get_user": "/users/{user_id} (try /users/999 for 404)",
               "create_user": "POST /users (requires name and email)",
               "divide": "/divide/{a}/{b} (try /divide/10/0 for error)",
               "not_found": "/nonexistent (try any invalid path)",
               "server_error": "/error-demo"
           }
       })

   if __name__ == "__main__":
       print("Starting error handling demo server...")
       app.listen(host="127.0.0.1", port=8000)

Test the error handling:

.. code-block:: bash

   # Test various error scenarios
   curl http://localhost:8000/users/999          # UserNotFoundError
   curl http://localhost:8000/divide/10/0        # ValueError
   curl http://localhost:8000/nonexistent        # 404 handler
   curl -X POST http://localhost:8000/users      # ValidationError

Debug vs Production Mode
~~~~~~~~~~~~~~~~~~~~~~~~

Control error response verbosity with production mode:

.. code-block:: python

   # Debug mode (development) - detailed error messages
   app = App(production=False)

   # Production mode - clean, safe error messages
   app = App(production=True)

**Debug Mode Response:**

.. code-block:: json

   {
     "error": "Internal server error",
     "message": "division by zero",
     "traceback": "Traceback (most recent call last):\n  File...",
     "type": "ZeroDivisionError"
   }

**Production Mode Response:**

.. code-block:: json

   {
     "error": "Internal server error",
     "message": "Something went wrong on our end",
     "code": "INTERNAL_ERROR"
   }

Running via CLI
---------------

Command Line Deployment
~~~~~~~~~~~~~~~~~~~~~~~~

Catzilla provides a built-in CLI for running applications in production:

**Basic Usage:**

.. code-block:: bash

   # Run with default settings (port 8000, host 127.0.0.1)
   python -m catzilla myapp:app

   # Specify custom port
   python -m catzilla myapp:app --port 3000

   # Bind to all interfaces for external access
   python -m catzilla myapp:app --host 0.0.0.0 --port 8080

   # Multiple options
   python -m catzilla myapp:app --host 0.0.0.0 --port 3000

**App Module Structure:**

Your application should be structured for CLI usage:

.. code-block:: python

   # myapp.py
   from catzilla import App, JSONResponse

   app = App(production=True)  # Production mode for CLI deployment

   @app.get("/")
   def home(request):
       return JSONResponse({"message": "Hello from production!"})

   @app.get("/health")
   def health_check(request):
       return JSONResponse({"status": "healthy"})

   # No need for if __name__ == "__main__" when using CLI

**Production Deployment Example:**

.. code-block:: bash

   # Development
   python -m catzilla myapp:app --port 8000

   # Staging
   python -m catzilla myapp:app --host 0.0.0.0 --port 5000

   # Production (behind reverse proxy)
   python -m catzilla myapp:app --host 127.0.0.1 --port 8080

Environment Configuration
~~~~~~~~~~~~~~~~~~~~~~~~~

Use environment variables for configuration:

.. code-block:: python

   # config.py
   import os

   class Config:
       HOST = os.getenv("CATZILLA_HOST", "127.0.0.1")
       PORT = int(os.getenv("CATZILLA_PORT", "8000"))
       PRODUCTION = os.getenv("CATZILLA_ENV", "development") == "production"
       DEBUG = not PRODUCTION

   # app.py
   from catzilla import App, JSONResponse
   from config import Config

   app = App(production=Config.PRODUCTION)

   @app.get("/")
   def home(request):
       return JSONResponse({
           "message": "Hello!",
           "environment": "production" if Config.PRODUCTION else "development"
       })

   @app.get("/config")
   def show_config(request):
       return JSONResponse({
           "host": Config.HOST,
           "port": Config.PORT,
           "production": Config.PRODUCTION,
           "debug": Config.DEBUG
       })

Run with environment variables:

.. code-block:: bash

   # Set environment variables
   export CATZILLA_HOST=0.0.0.0
   export CATZILLA_PORT=3000
   export CATZILLA_ENV=production

   # Run with CLI
   python -m catzilla app:app

Performance Optimization
------------------------

C-Accelerated Routing
~~~~~~~~~~~~~~~~~~~~~

Catzilla's C core provides exceptional routing performance:

.. code-block:: python

   from catzilla import App, JSONResponse
   import time

   app = App()

   # Catzilla handles hundreds of routes efficiently
   # The C trie router provides O(log n) lookup performance

   # Static routes
   for i in range(100):
       @app.get(f"/static-route-{i}")
       def static_handler(request, route_id=i):
           return JSONResponse({"route_id": route_id, "type": "static"})

   # Dynamic routes
   for i in range(100):
       @app.get(f"/dynamic-{i}/{{param}}")
       def dynamic_handler(request, route_id=i):
           param = request.path_params["param"]
           return JSONResponse({
               "route_id": route_id,
               "param": param,
               "type": "dynamic"
           })

   # Nested dynamic routes
   @app.get("/users/{user_id}/posts/{post_id}/comments/{comment_id}")
   def nested_handler(request):
       params = request.path_params
       return JSONResponse({
           "nested_params": params,
           "lookup_time": "microseconds"  # Thanks to C trie routing
       })

   @app.get("/benchmark")
   def benchmark_routing(request):
       start_time = time.time()

       # The route lookup itself is extremely fast due to C implementation
       # This endpoint demonstrates that even with hundreds of routes,
       # lookup time remains consistently fast

       end_time = time.time()
       return JSONResponse({
           "message": "Route lookup performance test",
           "total_routes": 200,  # 100 static + 100 dynamic
           "lookup_algorithm": "C trie-based",
           "complexity": "O(log n)",
           "response_time_ms": (end_time - start_time) * 1000
       })

   if __name__ == "__main__":
       print("Starting performance demo with 200+ routes...")
       app.listen(host="127.0.0.1", port=8000)

Memory Efficiency
~~~~~~~~~~~~~~~~~

Optimize memory usage for high-traffic applications:

.. code-block:: python

   from catzilla import App, JSONResponse

   # Use production mode to reduce memory overhead
   app = App(production=True)

   # Efficient response patterns
   @app.get("/users/{user_id}")
   def get_user(request):
       user_id = request.path_params["user_id"]

       # Return lightweight responses
       return JSONResponse({
           "id": user_id,
           "name": f"User {user_id}"
       })

   # Avoid storing large objects in memory
   @app.get("/large-dataset")
   def get_large_dataset(request):
       # Stream or paginate instead of loading everything
       page = int(request.query_params.get("page", "1"))
       limit = int(request.query_params.get("limit", "50"))

       # Generate data on-demand instead of storing
       data = [{"id": i, "value": f"item_{i}"}
               for i in range((page-1)*limit, page*limit)]

       return JSONResponse({
           "data": data,
           "page": page,
           "limit": limit
       })

   if __name__ == "__main__":
       app.listen(host="127.0.0.1", port=8000)

Real-World Example
------------------

Complete REST API Application
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Here's a comprehensive example that demonstrates all advanced features:

.. code-block:: python

   # production_api.py
   from catzilla import App, JSONResponse, RouterGroup
   import json
   import time
   from datetime import datetime

   # Production-ready app with error handling
   app = App(production=True)

   # Exception classes
   class APIError(Exception):
       def __init__(self, message, status_code=400):
           self.message = message
           self.status_code = status_code
           super().__init__(message)

   class ResourceNotFound(APIError):
       def __init__(self, resource_type, resource_id):
           super().__init__(f"{resource_type} {resource_id} not found", 404)

   # Global error handlers
   @app.exception_handler(APIError)
   def handle_api_error(request, exc):
       return JSONResponse({
           "error": exc.message,
           "timestamp": datetime.utcnow().isoformat(),
           "path": request.path
       }, status_code=exc.status_code)

   @app.not_found_handler
   def api_not_found(request):
       return JSONResponse({
           "error": "Endpoint not found",
           "path": request.path,
           "available_endpoints": [
               "GET /",
               "GET /api/v1/users",
               "GET /api/v1/users/{id}",
               "POST /api/v1/users",
               "GET /health"
           ]
       }, status_code=404)

   # Router groups
   api_v1 = RouterGroup(prefix="/api/v1", tags=["v1"])

   # In-memory storage (use database in production)
   users_db = {
       "1": {"id": "1", "name": "Alice", "email": "alice@example.com"},
       "2": {"id": "2", "name": "Bob", "email": "bob@example.com"}
   }

   # API endpoints
   @api_v1.get("/users")
   def list_users(request):
       page = int(request.query_params.get("page", "1"))
       limit = int(request.query_params.get("limit", "10"))
       search = request.query_params.get("search", "")

       users = list(users_db.values())

       # Filter by search term
       if search:
           users = [u for u in users if search.lower() in u["name"].lower()]

       # Pagination
       start = (page - 1) * limit
       end = start + limit
       paginated_users = users[start:end]

       return JSONResponse({
           "users": paginated_users,
           "pagination": {
               "page": page,
               "limit": limit,
               "total": len(users),
               "pages": (len(users) + limit - 1) // limit
           },
           "filters": {"search": search} if search else {}
       })

   @api_v1.get("/users/{user_id}")
   def get_user(request):
       user_id = request.path_params["user_id"]

       if user_id not in users_db:
           raise ResourceNotFound("User", user_id)

       return JSONResponse(users_db[user_id])

   @api_v1.post("/users")
   def create_user(request):
       try:
           data = request.json()
       except:
           raise APIError("Invalid JSON in request body")

       # Validation
       if not data.get("name"):
           raise APIError("Name is required")
       if not data.get("email") or "@" not in data["email"]:
           raise APIError("Valid email is required")

       # Create user
       user_id = str(len(users_db) + 1)
       user = {
           "id": user_id,
           "name": data["name"],
           "email": data["email"],
           "created_at": datetime.utcnow().isoformat()
       }

       users_db[user_id] = user

       return JSONResponse(user, status_code=201)

   @api_v1.put("/users/{user_id}")
   def update_user(request):
       user_id = request.path_params["user_id"]

       if user_id not in users_db:
           raise ResourceNotFound("User", user_id)

       try:
           data = request.json()
       except:
           raise APIError("Invalid JSON in request body")

       user = users_db[user_id].copy()
       user.update(data)
       user["updated_at"] = datetime.utcnow().isoformat()
       users_db[user_id] = user

       return JSONResponse(user)

   @api_v1.delete("/users/{user_id}")
   def delete_user(request):
       user_id = request.path_params["user_id"]

       if user_id not in users_db:
           raise ResourceNotFound("User", user_id)

       del users_db[user_id]
       return JSONResponse({"message": f"User {user_id} deleted"})

   # Register router
   app.include_router(api_v1)

   # Main routes
   @app.get("/")
   def api_info(request):
       return JSONResponse({
           "name": "Production API",
           "version": "1.0.0",
           "endpoints": {
               "users": "/api/v1/users",
               "health": "/health",
               "docs": "https://docs.example.com"
           },
           "timestamp": datetime.utcnow().isoformat()
       })

   @app.get("/health")
   def health_check(request):
       return JSONResponse({
           "status": "healthy",
           "uptime": time.time(),
           "users_count": len(users_db),
           "timestamp": datetime.utcnow().isoformat()
       })

   if __name__ == "__main__":
       print("Starting production API server...")
       print("Available endpoints:")
       print("  GET  /")
       print("  GET  /health")
       print("  GET  /api/v1/users")
       print("  GET  /api/v1/users/{id}")
       print("  POST /api/v1/users")
       print("  PUT  /api/v1/users/{id}")
       print("  DELETE /api/v1/users/{id}")
       app.listen(host="127.0.0.1", port=8000)

Deploy this production API:

.. code-block:: bash

   # Development
   python production_api.py

   # Production via CLI
   python -m catzilla production_api:app --host 0.0.0.0 --port 8080

Test the API:

.. code-block:: bash

   # Get all users
   curl http://localhost:8000/api/v1/users

   # Get specific user
   curl http://localhost:8000/api/v1/users/1

   # Create new user
   curl -X POST http://localhost:8000/api/v1/users \
        -H "Content-Type: application/json" \
        -d '{"name": "Charlie", "email": "charlie@example.com"}'

   # Search users
   curl "http://localhost:8000/api/v1/users?search=alice&page=1&limit=5"

   # Health check
   curl http://localhost:8000/health

This advanced example demonstrates:

- **Router Groups**: Organized API structure with versioning
- **Error Handling**: Custom exceptions and global error handlers
- **Dynamic Routing**: Path parameters with validation
- **Request Processing**: JSON parsing, query parameters, pagination
- **Production Ready**: Clean error responses, health checks
- **CLI Deployment**: Ready for production deployment

You now have all the tools to build high-performance, production-ready web applications with Catzilla!
