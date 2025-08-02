Catzilla Documentation
=======================

.. image:: _static/logo.png
   :alt: Catzilla - The FastAPI Killer | Lightning Fast Python Web Framework
   :width: 200px
   :align: center

**The fastest Python web framework with C-accelerated routing and async/sync hybrid support**

.. image:: https://img.shields.io/pypi/v/catzilla.svg
   :target: https://pypi.org/project/catzilla/
   :alt: PyPI Version

.. image:: https://img.shields.io/pypi/pyversions/catzilla.svg
   :target: https://pypi.org/project/catzilla/
   :alt: Python Versions

.. image:: https://github.com/rezwanahmedsami/catzilla/actions/workflows/ci.yml/badge.svg
   :target: https://github.com/rezwanahmedsami/catzilla/actions
   :alt: Build Status

Catzilla is a modern Python web framework that delivers **exceptional performance**
through its C-accelerated routing engine powered by libuv. Built for developers who demand both speed and simplicity.

🚀 Key Features
---------------

- **🏎️ C-Accelerated Routing** - Ultra-fast trie-based routing with O(log n) performance
- **⚡ Async/Sync Hybrid** - Seamlessly mix async and sync handlers with automatic detection
- **📦 Zero-Copy Operations** - Memory-efficient request handling with minimal allocations
- **🔍 Auto-Validation** - Pydantic-compatible models with C-accelerated validation
- **🔗 Advanced DI System** - Powerful dependency injection with multiple scopes
- **🗄️ Multi-Layer Caching** - Memory, Redis, and disk caching with intelligent fallbacks
- **📡 Streaming Support** - Server-sent events and chunked responses
- **📁 File Handling** - Optimized upload/download with image processing
- **🔧 Background Tasks** - Async task scheduling and monitoring
- **🛡️ Production Ready** - Built-in security, monitoring, and error handling

Quick Start
-----------

Installation
~~~~~~~~~~~~

.. code-block:: bash

   pip install catzilla

Hello World
~~~~~~~~~~~

.. code-block:: python

   from catzilla import Catzilla, JSONResponse

   app = Catzilla()

   @app.get("/")
   def home(request):
       return JSONResponse({"message": "Hello, World!"})

   if __name__ == "__main__":
       app.listen(port=8000)

Async/Sync Hybrid Example
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from catzilla import Catzilla, JSONResponse, BaseModel
   import asyncio

   app = Catzilla()

   # Sync handler (runs in thread pool)
   @app.get("/sync")
   def sync_handler(request):
       return JSONResponse({"type": "sync"})

   # Async handler (runs in event loop)
   @app.get("/async")
   async def async_handler(request):
       await asyncio.sleep(0.1)  # Non-blocking I/O
       return JSONResponse({"type": "async"})

   class User(BaseModel):
       name: str
       email: str

   # Auto-validation with BaseModel
   @app.post("/users")
   def create_user(request, user: User):
       return JSONResponse({"user": user.dict()})

Documentation Structure
-----------------------

.. toctree::
   :maxdepth: 2
   :caption: Getting Started

   getting-started/installation
   getting-started/quickstart
   getting-started/migration-from-fastapi

.. toctree::
   :maxdepth: 2
   :caption: Core Concepts

   core-concepts/routing
   core-concepts/validation
   core-concepts/async-sync-hybrid
   core-concepts/dependency-injection
   core-concepts/middleware

.. toctree::
   :maxdepth: 2
   :caption: Features

   features/background-tasks
   features/streaming
   features/file-handling
   features/caching

.. toctree::
   :maxdepth: 2
   :caption: Guides

   guides/recipes

.. toctree::
   :maxdepth: 2
   :caption: Examples

   examples/basic-routing



Community & Support
-------------------

- 📖 **Documentation**: This comprehensive guide
- 🐛 **Issues**: `GitHub Issues <https://github.com/rezwanahmedsami/catzilla/issues>`_
- 💬 **Discussions**: `GitHub Discussions <https://github.com/rezwanahmedsami/catzilla/discussions>`_
- 🚀 **Releases**: `GitHub Releases <https://github.com/rezwanahmedsami/catzilla/releases>`_

License
-------

Catzilla is released under the MIT License. See the `LICENSE <https://github.com/rezwanahmedsami/catzilla/blob/main/LICENSE>`_ file for details.

Why Choose Catzilla?
--------------------

**🏃‍♂️ Migrate from FastAPI in Minutes**

Catzilla's API is designed for seamless FastAPI migration:

.. code-block:: python

   # FastAPI code works with minimal changes
   from catzilla import Catzilla, BaseModel  # Just change the import
   from catzilla.responses import JSONResponse

   app = Catzilla()  # Instead of FastAPI()

   # Everything else works the same!

**🚀 Get Exceptional Performance Instantly**

No code changes needed - just install Catzilla and watch your API fly!

**🔧 Production-Grade Features Out of the Box**

- Built-in caching
- Background task processing
- Advanced dependency injection
- File upload handling
- Streaming responses
- Authentication patterns
- Performance monitoring

Ready to supercharge your Python API? Let's get started! 🚀
