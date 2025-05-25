Quickstart Guide
================

.. image:: _static/logo.png
   :alt: Catzilla Logo
   :width: 150px
   :align: right

This guide will get you up and running with Catzilla in minutes. By the end, you'll have a working web server with routes, path parameters, JSON responses, and organized code structure.

Installation
------------

Install Catzilla from PyPI using pip:

.. code-block:: bash

   pip install catzilla

**System Requirements:**
- Python 3.8+ (3.9+ recommended)
- Windows, macOS, or Linux
- No additional dependencies required

For development with the latest features:

.. code-block:: bash

   git clone https://github.com/rezwanahmedsami/catzilla.git
   cd catzilla
   pip install -e .

Hello World
-----------

Let's start with the simplest possible Catzilla application:

.. code-block:: python

   # hello.py
   from catzilla import App

   app = App()

   @app.get("/")
   def home(request):
       return "Hello, World!"

   if __name__ == "__main__":
       app.listen(8000)

Save this as ``hello.py`` and run it:

.. code-block:: bash

   python hello.py

Visit http://localhost:8000 and you'll see "Hello, World!".

**What's happening:**
- ``App()`` creates a new Catzilla application instance
- ``@app.get("/")`` registers a route handler for GET requests to the root path
- ``app.listen(8000)`` starts the server on port 8000

Decorator-Based Routing
-----------------------

Catzilla uses decorators to define routes. Each HTTP method has its own decorator:

.. code-block:: python

   from catzilla import App, JSONResponse

   app = App()

   @app.get("/")
   def home(request):
       return "Welcome to my API!"

   @app.post("/users")
   def create_user(request):
       return JSONResponse({"message": "User created!"})

   @app.put("/users/{user_id}")
   def update_user(request):
       user_id = request.path_params["user_id"]
       return JSONResponse({"message": f"User {user_id} updated!"})

   @app.delete("/users/{user_id}")
   def delete_user(request):
       user_id = request.path_params["user_id"]
       return JSONResponse({"message": f"User {user_id} deleted!"})

   if __name__ == "__main__":
       app.listen(8000)

**Supported HTTP Methods:**
- ``@app.get()`` - GET requests
- ``@app.post()`` - POST requests
- ``@app.put()`` - PUT requests
- ``@app.delete()`` - DELETE requests
- ``@app.patch()`` - PATCH requests
- ``@app.head()`` - HEAD requests
- ``@app.options()`` - OPTIONS requests

Dynamic Path Parameters
-----------------------

Capture dynamic segments from URLs using path parameters:

.. code-block:: python

   from catzilla import App, JSONResponse

   app = App()

   # Single parameter
   @app.get("/users/{user_id}")
   def get_user(request):
       user_id = request.path_params["user_id"]
       return JSONResponse({"user_id": user_id, "name": f"User {user_id}"})

   # Multiple parameters
   @app.get("/users/{user_id}/posts/{post_id}")
   def get_user_post(request):
       user_id = request.path_params["user_id"]
       post_id = request.path_params["post_id"]
       return JSONResponse({
           "user_id": user_id,
           "post_id": post_id,
           "title": f"Post {post_id} by User {user_id}"
       })

   # Mixed static and dynamic segments
   @app.get("/api/v1/users/{user_id}/profile")
   def get_user_profile(request):
       user_id = request.path_params["user_id"]
       return JSONResponse({
           "user_id": user_id,
           "profile": {"bio": "Software developer", "location": "Earth"}
       })

   if __name__ == "__main__":
       app.listen(8000)

Test these endpoints:
- ``GET /users/123`` → Returns user 123
- ``GET /users/456/posts/789`` → Returns post 789 by user 456
- ``GET /api/v1/users/123/profile`` → Returns user 123's profile

Request and Response Usage
--------------------------

Catzilla provides powerful request and response objects for handling HTTP interactions:

**Working with Requests:**

.. code-block:: python

   from catzilla import App, JSONResponse

   app = App()

   @app.post("/users")
   def create_user(request):
       # Access request body (automatically parsed JSON)
       data = request.json()

       # Access query parameters
       page = request.query_params.get("page", "1")
       limit = request.query_params.get("limit", "10")

       # Access headers
       content_type = request.headers.get("Content-Type")
       user_agent = request.headers.get("User-Agent")

       return JSONResponse({
           "received_data": data,
           "page": page,
           "limit": limit,
           "content_type": content_type,
           "user_agent": user_agent
       })

   @app.get("/search")
   def search(request):
       # Query parameters from URL like /search?q=python&category=programming
       query = request.query_params.get("q", "")
       category = request.query_params.get("category", "all")

       return JSONResponse({
           "query": query,
           "category": category,
           "results": [f"Result for '{query}' in {category}"]
       })

   if __name__ == "__main__":
       app.listen(8000)

**Response Types:**

.. code-block:: python

   from catzilla import App, JSONResponse, HTMLResponse, Response

   app = App()

   @app.get("/json")
   def json_endpoint(request):
       # JSON response with automatic Content-Type header
       return JSONResponse({"message": "Hello JSON!"})

   @app.get("/html")
   def html_endpoint(request):
       # HTML response with automatic Content-Type header
       return HTMLResponse("""
           <html>
               <body>
                   <h1>Hello HTML!</h1>
                   <p>This is an HTML response.</p>
               </body>
           </html>
       """)

   @app.get("/text")
   def text_endpoint(request):
       # Plain text response (string return)
       return "Hello, plain text!"

   @app.get("/custom")
   def custom_endpoint(request):
       # Custom response with specific status and headers
       return Response(
           body="Custom response",
           status_code=201,
           content_type="text/plain",
           headers={"X-Custom-Header": "Custom Value"}
       )

   if __name__ == "__main__":
       app.listen(8000)

Router Groups for Organization
------------------------------

As your application grows, organize routes using Router Groups:

.. code-block:: python

   from catzilla import App, JSONResponse, RouterGroup

   app = App()

   # Create router groups with prefixes
   api_router = RouterGroup(prefix="/api/v1", tags=["api"])
   admin_router = RouterGroup(prefix="/admin", tags=["admin"])

   # Add routes to the API group
   @api_router.get("/users")
   def list_users(request):
       return JSONResponse({"users": ["alice", "bob", "charlie"]})

   @api_router.get("/users/{user_id}")
   def get_user(request):
       user_id = request.path_params["user_id"]
       return JSONResponse({"user_id": user_id, "name": f"User {user_id}"})

   @api_router.post("/users")
   def create_user(request):
       data = request.json()
       return JSONResponse({"message": "User created", "data": data})

   # Add routes to the admin group
   @admin_router.get("/stats")
   def admin_stats(request):
       return JSONResponse({"total_users": 3, "active_sessions": 15})

   @admin_router.get("/health")
   def health_check(request):
       return JSONResponse({"status": "healthy", "uptime": "24h"})

   # Register router groups with the main app
   app.include_router(api_router)
   app.include_router(admin_router)

   # Main app routes (no prefix)
   @app.get("/")
   def home(request):
       return JSONResponse({
           "message": "Welcome to the API",
           "endpoints": {
               "api": "/api/v1/users",
               "admin": "/admin/stats"
           }
       })

   if __name__ == "__main__":
       app.listen(8000)

This creates the following routes:
- ``GET /`` → Home page
- ``GET /api/v1/users`` → List users
- ``GET /api/v1/users/{user_id}`` → Get specific user
- ``POST /api/v1/users`` → Create user
- ``GET /admin/stats`` → Admin statistics
- ``GET /admin/health`` → Health check

Running via CLI
---------------

For production deployment, you can run Catzilla applications via command line:

.. code-block:: bash

   # Run with default settings (port 8000)
   python -m catzilla app:app

   # Specify custom port
   python -m catzilla app:app --port 3000

   # Run with host binding
   python -m catzilla app:app --host 0.0.0.0 --port 8080

Where ``app:app`` refers to:
- ``app`` - the Python module name (app.py)
- ``app`` - the variable name of your Catzilla App instance

**Example app.py for CLI usage:**

.. code-block:: python

   # app.py
   from catzilla import App, JSONResponse

   app = App()

   @app.get("/")
   def home(request):
       return JSONResponse({"message": "Hello from CLI!"})

   @app.get("/health")
   def health(request):
       return JSONResponse({"status": "ok"})

   # No need for if __name__ == "__main__" when using CLI

Then run:

.. code-block:: bash

   python -m catzilla app:app --port 8000

Next Steps
----------

You now have the fundamentals! Here's what to explore next:

- **Error Handling**: Learn about custom error handlers and production-mode error responses
- **Advanced Routing**: Explore complex path patterns and route organization
- **Performance**: Discover Catzilla's C-accelerated routing performance
- **Testing**: Write tests for your Catzilla applications
- **Deployment**: Deploy to production with proper configuration

**Complete Example Application:**

Here's a more comprehensive example that demonstrates all the concepts:

.. code-block:: python

   # complete_app.py
   from catzilla import App, JSONResponse, HTMLResponse, RouterGroup

   # Create app with production-mode error handling
   app = App(production=True)

   # API router group
   api = RouterGroup(prefix="/api/v1", tags=["api"])

   @api.get("/users")
   def list_users(request):
       page = int(request.query_params.get("page", "1"))
       limit = int(request.query_params.get("limit", "10"))

       users = [f"user_{i}" for i in range((page-1)*limit, page*limit)]
       return JSONResponse({
           "users": users,
           "page": page,
           "limit": limit,
           "total": 1000
       })

   @api.get("/users/{user_id}")
   def get_user(request):
       user_id = request.path_params["user_id"]
       return JSONResponse({
           "id": user_id,
           "name": f"User {user_id}",
           "email": f"user{user_id}@example.com"
       })

   @api.post("/users")
   def create_user(request):
       data = request.json()
       return JSONResponse({
           "message": "User created successfully",
           "user": data
       }, status_code=201)

   # Register the API router
   app.include_router(api)

   # Main routes
   @app.get("/")
   def home(request):
       return HTMLResponse("""
           <html>
               <head><title>Catzilla API</title></head>
               <body>
                   <h1>Welcome to Catzilla API</h1>
                   <p>Available endpoints:</p>
                   <ul>
                       <li>GET /api/v1/users - List users</li>
                       <li>GET /api/v1/users/{id} - Get user</li>
                       <li>POST /api/v1/users - Create user</li>
                   </ul>
               </body>
           </html>
       """)

   @app.get("/health")
   def health_check(request):
       return JSONResponse({"status": "healthy"})

   if __name__ == "__main__":
       print("Starting Catzilla server on http://localhost:8000")
       app.listen(8000)

Save this as ``complete_app.py`` and run:

.. code-block:: bash

   python complete_app.py

Or use the CLI:

.. code-block:: bash

   python -m catzilla complete_app:app

**Ready for more?** Check out the :doc:`getting-started` guide for detailed explanations and the :doc:`examples` section for real-world use cases.
