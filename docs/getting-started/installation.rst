Installation
============

Catzilla is available on PyPI and can be installed with a single pip command.

Quick Installation
------------------

.. code-block:: bash

   pip install catzilla

That's it! This installs Catzilla with all core features including:

- 🚀 **C-accelerated routing** with libuv (bundled)
- 🔧 **jemalloc memory allocator** (statically built)
- ⚡ **Async/sync hybrid support**
- 📦 **All essential dependencies**

Verification
------------

Verify your installation by creating a simple test:

.. code-block:: python

   # test_catzilla.py
   from catzilla import Catzilla, JSONResponse

   app = Catzilla()

   @app.get("/")
   def home(request):
       return JSONResponse({
           "message": "Catzilla is working!",
           "version": "0.2.0",
           "status": "ready"
       })

   if __name__ == "__main__":
       print("🚀 Starting Catzilla...")
       app.listen(port=8000)

Run the test:

.. code-block:: bash

   python test_catzilla.py

Visit `http://localhost:8000` - you should see the JSON response.

Python Requirements
-------------------

- **Python 3.9+** (recommended: Python 3.10+)
- **All platforms supported**: Linux, macOS, Windows

Next Steps
----------

Now that you have Catzilla installed:

- :doc:`quickstart` - Build your first application in 5 minutes
- :doc:`migration-from-fastapi` - Migrate from FastAPI
- :doc:`../examples/basic-routing` - Explore routing examples

Need Help?
----------

- 📖 **Documentation**: Continue reading this guide
- 🐛 **Issues**: `GitHub Issues <https://github.com/rezwanahmedsami/catzilla/issues>`_
- 💬 **Community**: `GitHub Discussions <https://github.com/rezwanahmedsami/catzilla/discussions>`_
