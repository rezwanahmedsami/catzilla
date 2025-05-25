Catzilla Documentation
======================

.. image:: _static/logo.png
   :alt: Catzilla Logo
   :width: 200px
   :align: center

**Blazing-fast Python web framework with production-grade routing backed by a minimal, event-driven C core**

.. image:: https://img.shields.io/pypi/v/catzilla.svg
   :target: https://pypi.org/project/catzilla/

.. image:: https://img.shields.io/pypi/pyversions/catzilla.svg
   :target: https://pypi.org/project/catzilla/

.. image:: https://github.com/rezwanahmedsami/catzilla/actions/workflows/ci.yml/badge.svg
   :target: https://github.com/rezwanahmedsami/catzilla/actions

Catzilla is a modern Python web framework purpose-built for **extreme performance** and **developer productivity**.
At its heart is a sophisticated C HTTP engine featuring an advanced **trie-based routing system** that delivers
O(log n) route lookup performance while maintaining a clean, Pythonic API.

**Key Features:**

- 🚀 **Ultra-fast C core** with Python bindings for maximum performance
- 🔗 **Advanced trie-based routing** with O(log n) lookup performance
- 🎯 **Dynamic path parameters** and flexible route patterns
- 📦 **Router groups** for organized, modular code structure
- ⚡ **Built-in JSON/HTML responses** with automatic content-type handling
- 🛡️ **Production-ready error handling** with clean responses
- 🔧 **Simple CLI integration** for easy deployment
- 📊 **Comprehensive testing** across platforms (Windows, macOS, Linux)

**Quick Start:**

.. code-block:: bash

   pip install catzilla

.. code-block:: python

   from catzilla import App

   app = App()

   @app.get("/")
   def home(request):
       return "Hello, World!"

   @app.get("/users/{user_id}")
   def get_user(request):
       user_id = request.path_params["user_id"]
       return {"user_id": user_id}

   if __name__ == "__main__":
       app.listen(8000)

.. toctree::
   :maxdepth: 2
   :caption: Getting Started

   quickstart

.. toctree::
   :maxdepth: 2
   :caption: User Guide

   advanced

.. toctree::
   :maxdepth: 2
   :caption: Reference

   c-accelerated-routing.md
   error-handling.md
   performance.md

Why Choose Catzilla?
--------------------

🚀 **Exceptional Performance**
   Catzilla delivers **2-4x faster** throughput than FastAPI with **60% lower latency**.
   Our C-accelerated routing engine provides production-grade performance for high-traffic applications.

⚡ **Zero Boilerplate**
   Clean decorator-style routing with no configuration overhead. Write ``@app.get("/users/{id}")``
   and Catzilla handles the rest - parameter extraction, HTTP method routing, and error handling.

🧱 **Production Ready**
   Comprehensive test coverage (90+ tests), memory-safe C core, automatic error handling
   (404, 405, 415), and battle-tested routing algorithms.

🔧 **Developer Experience**
   RouterGroup system for organizing complex APIs, intuitive path parameters via ``request.path_params``,
   and familiar Python patterns throughout.

Quick Start
-----------

Install and create your first API in under 30 seconds:

.. code-block:: bash

   pip install catzilla

.. code-block:: python

   from catzilla import App, RouterGroup

   app = App()

   # Simple routes
   @app.get("/")
   def home(request):
       return {"message": "Welcome to Catzilla!"}

   # RouterGroup for organization
   api = RouterGroup(prefix="/api/v1")

   @api.get("/users/{user_id}")
   def get_user(request):
       user_id = request.path_params["user_id"]
       return {"user_id": user_id, "name": f"User {user_id}"}

   @api.post("/users")
   def create_user(request):
       return {"message": "User created"}, 201

   app.include_routes(api)

   if __name__ == "__main__":
       app.listen(8000)

This creates a production-ready API with:

- ``GET /`` - Welcome message
- ``GET /api/v1/users/123`` - Get user with ID extraction
- ``POST /api/v1/users`` - Create new user
- Automatic 404/405 error handling
- C-accelerated route matching

Performance Highlights
----------------------

Catzilla has been extensively benchmarked against popular Python frameworks:

.. list-table:: **Performance Comparison vs FastAPI**
   :header-rows: 1

   * - Endpoint Type
     - Catzilla RPS
     - FastAPI RPS
     - Performance Gain
   * - Hello World
     - 8,130
     - 2,087
     - **+289% faster**
   * - JSON Response
     - 5,165
     - 1,844
     - **+180% faster**
   * - Path Parameters
     - 5,765
     - 1,621
     - **+256% faster**
   * - Query Parameters
     - 3,785
     - 923
     - **+310% faster**
   * - Complex JSON
     - 5,156
     - 1,344
     - **+284% faster**

**Latency Excellence**: Average latency of 25.36ms vs FastAPI's 69.11ms (**63% lower**)

Architecture Overview
---------------------

**Hybrid C-Python Design**
   C-accelerated trie-based routing with Python handler execution. Automatic fallback
   to pure Python ensures compatibility across all environments.

**Advanced Routing Engine**
   - O(log n) route lookup performance
   - Dynamic path parameter extraction in C
   - Method-specific routing with conflict detection
   - Memory-efficient trie data structure

**RouterGroup System**
   Hierarchical route organization with shared prefixes, metadata inheritance,
   and nested group support for building complex APIs.

**Production Features**
   - Zero memory leaks with C-level memory management
   - Comprehensive HTTP status code handling
   - Thread-safe design for concurrent workloads
   - Extensive test coverage (90+ tests)

Core Concepts
-------------

**App**: The main application instance that orchestrates HTTP request handling

.. code-block:: python

   app = App()

   @app.get("/health")
   def health_check(request):
       return {"status": "healthy"}

**RouterGroup**: Organize related routes with shared prefixes and metadata

.. code-block:: python

   users_api = RouterGroup(prefix="/users", tags=["users"])

   @users_api.get("/{user_id}")
   def get_user(request):
       return {"user_id": request.path_params["user_id"]}

**Path Parameters**: Dynamic URL segments extracted automatically

.. code-block:: python

   @app.get("/posts/{post_id}/comments/{comment_id}")
   def get_comment(request):
       post_id = request.path_params["post_id"]
       comment_id = request.path_params["comment_id"]
       return {"post_id": post_id, "comment_id": comment_id}

**Request & Response**: Intuitive request/response handling

.. code-block:: python

   from catzilla import JSONResponse, HTMLResponse

   @app.post("/data")
   def handle_data(request):
       # Access request properties
       method = request.method
       headers = request.headers

       # Return various response types
       return JSONResponse({"received": "data"}, status_code=201)

Real-World Example
------------------

Here's a complete blog API showcasing Catzilla's capabilities:

.. code-block:: python

   from catzilla import App, RouterGroup, JSONResponse

   app = App()

   # Authentication API
   auth = RouterGroup(prefix="/auth")

   @auth.post("/login")
   def login(request):
       return {"token": "jwt-token-here"}

   @auth.post("/logout")
   def logout(request):
       return {"message": "Logged out successfully"}

   # Blog Posts API
   posts = RouterGroup(prefix="/posts")

   @posts.get("/")
   def list_posts(request):
       return {
           "posts": [
               {"id": 1, "title": "Hello World", "author": "alice"},
               {"id": 2, "title": "Catzilla Guide", "author": "bob"}
           ]
       }

   @posts.get("/{post_id}")
   def get_post(request):
       post_id = request.path_params["post_id"]
       return {
           "id": post_id,
           "title": f"Post {post_id}",
           "content": "Post content here..."
       }

   @posts.post("/")
   def create_post(request):
       return JSONResponse({"message": "Post created"}, status_code=201)

   @posts.put("/{post_id}")
   def update_post(request):
       post_id = request.path_params["post_id"]
       return {"message": f"Post {post_id} updated"}

   # Users API
   users = RouterGroup(prefix="/users")

   @users.get("/{user_id}")
   def get_user(request):
       user_id = request.path_params["user_id"]
       return {"id": user_id, "name": f"User {user_id}"}

   @users.get("/{user_id}/posts")
   def get_user_posts(request):
       user_id = request.path_params["user_id"]
       return {
           "user_id": user_id,
           "posts": [{"id": 1, "title": "My First Post"}]
       }

   # Include all route groups
   app.include_routes(auth)
   app.include_routes(posts)
   app.include_routes(users)

   if __name__ == "__main__":
       app.listen(8000)

This creates a full REST API with organized endpoints:

**Authentication**
- ``POST /auth/login`` - User authentication
- ``POST /auth/logout`` - User logout

**Blog Management**
- ``GET /posts/`` - List all posts
- ``GET /posts/123`` - Get specific post
- ``POST /posts/`` - Create new post
- ``PUT /posts/123`` - Update existing post

**User Management**
- ``GET /users/456`` - Get user profile
- ``GET /users/456/posts`` - Get user's posts

When to Use Catzilla
--------------------

**Perfect For:**

✅ **High-throughput APIs** - Microservices, API gateways, data processing pipelines

✅ **Low-latency applications** - Real-time APIs, financial systems, gaming backends

✅ **Resource-constrained environments** - Cloud functions, edge computing, embedded systems

✅ **Performance-critical workloads** - When every millisecond and CPU cycle matters

**Consider Alternatives For:**

❌ **Full-stack web applications** - Catzilla focuses on APIs, not template rendering

❌ **Rapid prototyping** - More mature frameworks may have richer ecosystems for quick builds

❌ **Complex authentication flows** - Built-in auth systems may be more convenient

Installation & Dependencies
----------------------------

Catzilla uses **only Python standard library** - no external runtime dependencies:

.. code-block:: bash

   # Production installation
   pip install catzilla

   # Development installation
   git clone https://github.com/rezwanahmedsami/catzilla.git
   cd catzilla
   pip install -e .

**Requirements:**
- Python 3.8+
- No external dependencies (pure Python standard library)
- C compiler for building from source (CMake, GCC/Clang/MSVC)

**Supported Platforms:**
- Linux (x86_64, ARM64)
- macOS (Intel, Apple Silicon)
- Windows (x86_64)

Community & Support
-------------------

**GitHub Repository**
   https://github.com/rezwanahmedsami/catzilla

**Documentation**
   Complete guides, API reference, and examples

**Issue Tracking**
   Bug reports, feature requests, and community discussion

**Contributing**
   See ``CONTRIBUTING.md`` for development setup and contribution guidelines

**Author**
   Rezwan Ahmed Sami - samiahmed0f0@gmail.com

License
-------

Catzilla is released under the **MIT License**. See ``LICENSE`` file for complete terms.

The MIT License allows you to:
- ✅ Use Catzilla in commercial applications
- ✅ Modify and distribute the source code
- ✅ Include in proprietary software
- ✅ Sell applications built with Catzilla

Index & Search
==============

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
