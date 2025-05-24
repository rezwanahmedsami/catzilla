Catzilla Documentation
======================

Welcome to Catzilla, a high-performance Python web framework featuring C-accelerated routing and modern API design patterns.

.. toctree::
   :maxdepth: 2
   :caption: Getting Started

   getting-started
   quickstart
   examples

.. toctree::
   :maxdepth: 2
   :caption: Core Features

   routing
   router-groups
   request-handling
   response-types
   path-parameters

.. toctree::
   :maxdepth: 2
   :caption: Advanced Features

   c-accelerated-routing
   cookies-and-headers
   performance

.. toctree::
   :maxdepth: 2
   :caption: Development

   features
   README

Overview
--------

Catzilla is a modern Python web framework that combines the performance of C with the simplicity of Python. Key features include:

**Performance**
- C-accelerated route matching for optimal performance
- Efficient path parameter extraction
- Scalable RouterGroup system for large applications
- Optimized memory usage with C-based routing core

**Developer Experience**
- RouterGroup system for organizing routes with shared prefixes
- Manual type conversion for path parameters
- Comprehensive path parameter support via `request.path_params`
- Synchronous request handling

**Architecture**
- Hybrid C-Python design for optimal performance
- Automatic fallback to pure Python when needed
- Production-grade memory management
- Comprehensive test coverage (90 tests total)

Quick Example
-------------

.. code-block:: python

   from catzilla import App, RouterGroup

   app = App()

   # Create a RouterGroup for API v1
   api_v1 = RouterGroup(prefix="/api/v1")

   @api_v1.get("/users/{user_id}")
   def get_user(request):
       user_id = request.path_params["user_id"]
       return {"user_id": user_id}

   @api_v1.post("/users")
   def create_user(request):
       return {"message": "User created"}

   # Include the router group
   app.include_routes(api_v1)

   if __name__ == "__main__":
       app.listen(8000)

Key Documentation Sections
---------------------------

**RouterGroup System**
   Learn how to organize your routes hierarchically using the RouterGroup system. Supports route grouping with shared prefixes and HTTP method decorators.

**C-Accelerated Routing**
   Understand the hybrid C-Python architecture that provides performance improvements while maintaining full Python compatibility.

**Path Parameters**
   Master path parameter extraction using `request.path_params` and manual type conversion patterns.

**Performance Features**
   Learn about the architectural benefits of C acceleration and performance best practices.

Installation
------------

.. code-block:: bash

   pip install catzilla

For development:

.. code-block:: bash

   git clone https://github.com/your-username/catzilla.git
   cd catzilla
   ./scripts/build.sh

Performance Highlights
----------------------

Catzilla provides performance improvements over pure Python implementations through its C-accelerated routing architecture:

- **C-Accelerated Route Matching**: Transparent performance improvements for route lookup
- **Efficient Path Parameter Extraction**: Fast parameter parsing in C with Python accessibility
- **Scalable Architecture**: Performance scales well with route complexity
- **Memory Efficiency**: Optimized memory usage patterns

The hybrid architecture automatically falls back to Python routing when C acceleration is not available, ensuring compatibility across all environments.

Community and Support
----------------------

- **GitHub**: https://github.com/your-username/catzilla
- **Issues**: Bug reports and feature requests
- **Discussions**: Community support and questions
- **Contributing**: See CONTRIBUTING.md for development guidelines

License
-------

Catzilla is released under the MIT License. See LICENSE file for details.

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
