Migration from FastAPI
======================

Migrating from FastAPI to Catzilla is designed to be seamless. This guide shows you exactly how to migrate your existing FastAPI applications to get **better performance** with minimal code changes.

Why Migrate to Catzilla?
-------------------------

**Performance Gains**
  - Significantly faster request handling than FastAPI
  - C-accelerated routing with O(log n) lookup
  - Zero-allocation middleware system
  - Optimized memory usage with jemalloc

**Enhanced Features**
  - True async/sync hybrid support (FastAPI is async-only)
  - Advanced dependency injection with multiple scopes
  - Built-in multi-layer caching
  - Background task system with monitoring
  - Superior file handling and streaming

**Better Developer Experience**
  - Faster startup times
  - Better error messages
  - Enhanced debugging tools
  - Production-ready out of the box

Quick Migration Checklist
--------------------------

.. note::
   **Migration Time: 5-15 minutes for most applications**

   Most FastAPI applications can be migrated by changing just the import statements!

1. **Update imports** - Change `fastapi` to `catzilla`
2. **Update app initialization** - `FastAPI()` → `Catzilla()`
3. **Update response imports** - Use Catzilla's response classes
4. **Test your application** - Everything should work immediately
5. **Optimize for performance** - Add async handlers where beneficial

Step-by-Step Migration
----------------------

1. Install Catzilla
~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   pip install catzilla

2. Update Imports
~~~~~~~~~~~~~~~~~

**Before (FastAPI):**

.. code-block:: python

   from fastapi import FastAPI, Depends, HTTPException
   from fastapi.responses import JSONResponse
   from pydantic import BaseModel, Field

**After (Catzilla):**

.. code-block:: python

   from catzilla import Catzilla, Depends, JSONResponse
   from catzilla import BaseModel, Field
   # Note: Use JSONResponse with status codes instead of HTTPException

3. Update App Initialization
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Before (FastAPI):**

.. code-block:: python

   from fastapi import FastAPI

   app = FastAPI(
       title="My API",
       description="My FastAPI application",
       version="1.0.0"
   )

**After (Catzilla):**

.. code-block:: python

   from catzilla import Catzilla

   app = Catzilla(
       title="My API",
       description="My Catzilla application",
       version="1.0.0",
       production=False,    # Enable dev features
       show_banner=True     # Show startup banner
   )

4. Update Response Imports
~~~~~~~~~~~~~~~~~~~~~~~~~~

**Before (FastAPI):**

.. code-block:: python

   from fastapi.responses import JSONResponse, HTMLResponse, FileResponse

**After (Catzilla):**

.. code-block:: python

   from catzilla import JSONResponse, HTMLResponse
   # Note: FileResponse not available in current Catzilla v0.2.0
   # Use Response with appropriate headers for file serving

Migration Examples
------------------

Basic CRUD API
~~~~~~~~~~~~~~

Here's a complete migration example of a typical FastAPI CRUD application:

**FastAPI Version:**

.. code-block:: python

   from fastapi import FastAPI, HTTPException, Depends
   from fastapi.responses import JSONResponse
   from pydantic import BaseModel
   from typing import List, Optional

   app = FastAPI()

   class User(BaseModel):
       name: str
       email: str
       age: Optional[int] = None

   users_db = {}
   user_id_counter = 1

   @app.get("/users", response_model=List[User])
   async def get_users():
       return list(users_db.values())

   @app.post("/users", response_model=User)
   async def create_user(user: User):
       global user_id_counter
       user_data = user.dict()
       user_data["id"] = user_id_counter
       users_db[user_id_counter] = user_data
       user_id_counter += 1
       return user_data

   @app.get("/users/{user_id}")
   async def get_user(user_id: int):
       if user_id not in users_db:
           raise HTTPException(status_code=404, detail="User not found")
       return users_db[user_id]

**Catzilla Version (Direct Migration):**

.. code-block:: python

   from catzilla import Catzilla, Depends, JSONResponse
   from catzilla import BaseModel
   from typing import List, Optional

   app = Catzilla()

   class User(BaseModel):
       name: str
       email: str
       age: Optional[int] = None

   users_db = {}
   user_id_counter = 1

   @app.get("/users")
   async def get_users(request):
       return JSONResponse(list(users_db.values()))

   @app.post("/users")
   async def create_user(request, user: User):
       global user_id_counter
       user_data = user.dict()
       user_data["id"] = user_id_counter
       users_db[user_id_counter] = user_data
       user_id_counter += 1
       return JSONResponse(user_data, status_code=201)

   @app.get("/users/{user_id}")
   async def get_user(request, user_id: int):
       if user_id not in users_db:
           return JSONResponse({"error": "User not found"}, status_code=404)
       return JSONResponse(users_db[user_id])

**Catzilla Version (Optimized with Async/Sync Hybrid):**

.. code-block:: python

   from catzilla import Catzilla, Path, JSONResponse
   from catzilla import BaseModel, Field
   from typing import List, Optional
   import asyncio

   app = Catzilla(production=False, show_banner=True)

   class User(BaseModel):
       name: str = Field(min_length=2, max_length=50)
       email: str = Field(regex=r'^[^@]+@[^@]+\\.[^@]+$')
       age: Optional[int] = Field(None, ge=0, le=120)

   users_db = {}
   user_id_counter = 1

   # Sync handler for simple operations
   @app.get("/users")
   def get_users(request):
       return JSONResponse(list(users_db.values()))

   # Async handler for database operations
   @app.post("/users")
   async def create_user(request, user: User):
       global user_id_counter

       # Simulate async database insert
       await asyncio.sleep(0.01)

       user_data = user.dict()
       user_data["id"] = user_id_counter
       users_db[user_id_counter] = user_data
       user_id_counter += 1

       return JSONResponse(user_data, status_code=201)

   # Sync handler with validation
   @app.get("/users/{user_id}")
   def get_user(request, user_id: int = Path(..., ge=1)):
       if user_id not in users_db:
           return JSONResponse(
               {"error": "User not found"},
               status_code=404
           )
       return JSONResponse(users_db[user_id])

Authentication & Dependencies
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**FastAPI Version:**

.. code-block:: python

   from fastapi import FastAPI, Depends, HTTPException, status
   from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

   app = FastAPI()
   security = HTTPBearer()

   def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
       # Validate JWT token
       if not validate_token(credentials.credentials):
           raise HTTPException(
               status_code=status.HTTP_401_UNAUTHORIZED,
               detail="Invalid token"
           )
       return get_user_from_token(credentials.credentials)

   @app.get("/protected")
   async def protected_route(current_user = Depends(get_current_user)):
       return {"user": current_user}

**Catzilla Version:**

.. code-block:: python

   from catzilla import Catzilla, Depends, service, JSONResponse

   app = Catzilla(enable_di=True)

   # Register auth service
   @service("auth_service", scope="singleton")
   def auth_service():
       return AuthenticationService()

   def get_current_user(request, auth: AuthenticationService = Depends("auth_service")):
       token = request.headers.get("Authorization", "").replace("Bearer ", "")
       if not auth.validate_token(token):
           return JSONResponse(
               {"error": "Invalid token"},
               status_code=401
           )
       return auth.get_user_from_token(token)

   @app.get("/protected")
   def protected_route(request, current_user = Depends(get_current_user)):
       return JSONResponse({"user": current_user})

File Uploads
~~~~~~~~~~~~

**FastAPI Version:**

.. code-block:: python

   from fastapi import FastAPI, File, UploadFile
   from fastapi.responses import JSONResponse

   app = FastAPI()

   @app.post("/upload")
   async def upload_file(file: UploadFile = File(...)):
       content = await file.read()
       return {"filename": file.filename, "size": len(content)}

**Catzilla Version:**

.. code-block:: python

   from catzilla import Catzilla, JSONResponse, File

   app = Catzilla()

   @app.post("/upload")
   async def upload_file(request, file = File(...)):
       # Catzilla provides optimized file handling
       content = await file.read()

       return JSONResponse({
           "filename": file.filename,
           "size": len(content),
           "content_type": file.content_type
       })

   # Or sync version for simple file handling
   @app.post("/upload-sync")
   def upload_file_sync(request, file = File(...)):
       return JSONResponse({
           "filename": file.filename,
           "size": file.size,
           "upload_method": "sync"
       })

Key Differences & Improvements
------------------------------

Request Object
~~~~~~~~~~~~~~

**FastAPI:** Request object is optional and imported separately
**Catzilla:** Request object is always the first parameter

.. code-block:: python

   # FastAPI
   from fastapi import Request

   @app.get("/")
   async def handler(request: Request):
       pass

   # Catzilla - request is always first parameter
   @app.get("/")
   def handler(request):
       pass

Async/Sync Handling
~~~~~~~~~~~~~~~~~~~

**FastAPI:** All handlers must be async
**Catzilla:** Mix async and sync handlers freely

.. code-block:: python

   # FastAPI - everything must be async
   @app.get("/sync-task")
   async def sync_task():
       # Even CPU-bound tasks must be async
       return compute_something()

   # Catzilla - use the right tool for the job
   @app.get("/sync-task")
   def sync_task(request):
       # CPU-bound tasks can be sync
       return JSONResponse(compute_something())

   @app.get("/async-task")
   async def async_task(request):
       # I/O-bound tasks can be async
       data = await fetch_from_database()
       return JSONResponse(data)

Dependency Injection
~~~~~~~~~~~~~~~~~~~~

**FastAPI:** Basic dependency injection
**Catzilla:** Advanced DI with scopes and service management

.. code-block:: python

   # FastAPI - basic dependencies
   def get_database():
       return DatabaseConnection()

   @app.get("/")
   async def handler(db = Depends(get_database)):
       pass

   # Catzilla - advanced DI with scopes
   from catzilla.dependency_injection import service

   @service("database", scope="singleton")
   def get_database():
       return DatabaseConnection()

   @app.get("/")
   def handler(request, db = Depends("database")):
       pass

Performance Optimizations
~~~~~~~~~~~~~~~~~~~~~~~~~

**FastAPI:** Manual optimization required
**Catzilla:** Automatic optimizations built-in

.. code-block:: python

   # Catzilla automatically provides:
   # - C-accelerated routing
   # - Optimal async/sync execution
   # - Memory-efficient request handling
   # - Built-in caching
   # - Connection pooling

Common Migration Issues & Solutions
-----------------------------------

1. Response Model Decorators
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Issue:** FastAPI's `response_model` parameter doesn't exist in Catzilla

**Solution:** Use explicit JSON serialization

.. code-block:: python

   # FastAPI
   @app.get("/users", response_model=List[User])
   async def get_users():
       return users

   # Catzilla
   @app.get("/users")
   def get_users(request):
       return JSONResponse([user.dict() for user in users])

2. Status Code Responses
~~~~~~~~~~~~~~~~~~~~~~~~

**Issue:** FastAPI's automatic status code handling

**Solution:** Use explicit status codes in JSONResponse

.. code-block:: python

   # FastAPI
   @app.post("/users", status_code=201)
   async def create_user(user: User):
       return user

   # Catzilla
   @app.post("/users")
   def create_user(request, user: User):
       return JSONResponse(user.dict(), status_code=201)

3. Background Tasks
~~~~~~~~~~~~~~~~~~~

**Issue:** FastAPI's BackgroundTasks

**Solution:** Use Catzilla's advanced background task system

.. code-block:: python

   # FastAPI
   from fastapi import BackgroundTasks

   @app.post("/send-email")
   async def send_email(background_tasks: BackgroundTasks):
       background_tasks.add_task(send_email_task, "user@example.com")

   # Catzilla
   from catzilla.background_tasks import schedule_task

   @app.post("/send-email")
   def send_email(request):
       schedule_task(send_email_task, "user@example.com")
       return JSONResponse({"message": "Email scheduled"})

Migration Testing
-----------------

After migration, test your application thoroughly:

.. code-block:: bash

   # Install testing dependencies
   pip install pytest httpx

   # Run your existing FastAPI tests
   # Most should work with minimal changes

.. code-block:: python

   # test_migration.py
   import pytest
   from httpx import AsyncClient
   from your_app import app

   @pytest.mark.asyncio
   async def test_get_users():
       async with AsyncClient(app=app, base_url="http://test") as client:
           response = await client.get("/users")
           assert response.status_code == 200

Performance Verification
------------------------

Verify the performance improvements after migration:

.. code-block:: python

   # Add this endpoint to your migrated app
   @app.get("/performance-info")
   def performance_info(request):
       from catzilla.core import get_performance_stats

       return JSONResponse({
           "framework": "Catzilla",
           "performance_vs_fastapi": "significantly faster",
           "router": "C-accelerated",
           "async_support": "hybrid",
           "stats": get_performance_stats()
       })

Benchmark your migrated application:

.. code-block:: bash

   # Install benchmarking tools
   pip install wrk

   # Benchmark your FastAPI app
   wrk -t12 -c400 -d30s http://localhost:8000/users

   # Benchmark your Catzilla app
   wrk -t12 -c400 -d30s http://localhost:8000/users

   # Compare the results!

Advanced Migration Tips
-----------------------

1. **Gradual Migration**
   - Migrate one route at a time
   - Use feature flags to switch between versions
   - Run both versions in parallel during testing

2. **Optimize After Migration**
   - Convert CPU-bound endpoints to sync handlers
   - Use async handlers for I/O-bound operations
   - Implement caching where appropriate

3. **Take Advantage of New Features**
   - Use dependency injection for better service management
   - Implement background tasks for long-running operations
   - Add monitoring and health checks

4. **Production Considerations**
   - Update deployment scripts
   - Update monitoring and logging
   - Test under production load

Migration Checklist
--------------------

.. code-block:: text

   □ Install Catzilla: pip install catzilla
   □ Update imports: fastapi → catzilla
   □ Update app initialization: FastAPI() → Catzilla()
   □ Update response imports
   □ Test basic functionality
   □ Run existing test suite
   □ Optimize async/sync handlers
   □ Add performance monitoring
   □ Benchmark performance improvements
   □ Deploy to staging environment
   □ Monitor production metrics
   □ Celebrate significant performance improvement! 🚀

Key API Differences
-------------------

**Error Handling**

FastAPI uses HTTPException, but Catzilla uses JSONResponse with status codes:

.. code-block:: python

   # ❌ FastAPI pattern (not available in Catzilla):
   raise HTTPException(status_code=404, detail="User not found")

   # ✅ Catzilla pattern:
   return JSONResponse({"error": "User not found"}, status_code=404)

**File Responses**

FileResponse is not available in current Catzilla v0.2.0. Use Response with file content:

.. code-block:: python

   # ❌ Not available:
   return FileResponse("file.pdf")

   # ✅ Catzilla pattern:
   with open("file.pdf", 'rb') as f:
       content = f.read()
   return Response(
       body=content,
       content_type="application/pdf",
       headers={"Content-Length": str(len(content))}
   )

Need Help?
----------

If you encounter issues during migration:

- 📖 **Documentation**: Check this guide and API reference
- 🐛 **Issues**: Report migration issues on GitHub
- 💬 **Community**: Ask questions in GitHub Discussions
- 📧 **Support**: Contact the Catzilla team for enterprise support

**Migration time: 5-15 minutes**
**Performance gain: Significantly faster**
**Code changes: Minimal**

Welcome to the Catzilla family! 🚀
