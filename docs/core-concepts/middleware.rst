Middleware
==========

Catzilla provides a powerful, **zero-allocation middleware system** with both global and per-route middleware support. Build custom middleware chains with optimal performance and minimal memory overhead.

Overview
--------

Catzilla's middleware system provides:

- **Global Middleware** - Applied to all routes with ``@app.middleware()``
- **RouterGroup Middleware** - Applied to all routes within a RouterGroup
- **Per-Route Middleware** - Specific middleware for individual routes
- **Zero-Allocation Design** - C-accelerated middleware execution
- **Middleware Ordering** - Control execution order with priority system
- **Request/Response Processing** - Full access to request and response objects
- **Short-Circuiting** - Stop middleware chain and return early responses

Quick Start
-----------

Basic Global Middleware
~~~~~~~~~~~~~~~~~~~~~~~

Create middleware that applies to all routes:

.. code-block:: python

   from catzilla import Catzilla, Request, Response, JSONResponse
   from typing import Optional
   import time

   app = Catzilla()

   @app.middleware(priority=10, pre_route=True, name="timing_middleware")
   def timing_middleware(request: Request) -> Optional[Response]:
       """Measure request processing time"""
       start_time = time.time()

       # Store start time in request context for response processing
       if not hasattr(request, 'context'):
           request.context = {}
       request.context['start_time'] = start_time

       print(f"⏱️ Request started at {start_time}")
       return None  # Continue to next middleware

   @app.get("/")
   def home(request: Request) -> Response:
       return JSONResponse({"message": "Hello with timing middleware!"})

   if __name__ == "__main__":
       print("🚀 Starting Catzilla middleware example...")
       print("Try: curl http://localhost:8000/")
       app.listen(port=8000)

Per-Route Middleware
~~~~~~~~~~~~~~~~~~~~

Apply middleware to specific routes only:

.. code-block:: python

   from catzilla import Catzilla, Request, Response, JSONResponse
   from typing import Optional

   app = Catzilla()

   def auth_middleware(request: Request) -> Optional[Response]:
       """Check authentication"""
       auth_header = request.headers.get("Authorization") or request.headers.get("authorization")

       if not auth_header or not auth_header.startswith("Bearer "):
           return JSONResponse({
               "error": "Missing or invalid authentication"
           }, status_code=401)

       # Authentication passed, add user info to context
       if not hasattr(request, 'context'):
           request.context = {}
       request.context['user'] = {
           "id": "user123",
           "token": auth_header[7:]  # Remove "Bearer "
       }

       return None  # Continue to route handler

   # Apply middleware only to protected routes
   @app.get("/protected", middleware=[auth_middleware])
   def protected_endpoint(request: Request) -> Response:
       user = getattr(request, 'context', {}).get('user', {})
       return JSONResponse({
           "message": "You are authenticated!",
           "user": user
       })

   @app.get("/public")
   def public_endpoint(request: Request) -> Response:
       return JSONResponse({"message": "No authentication required"})

   if __name__ == "__main__":
       print("🚀 Starting per-route middleware example...")
       print("Try: curl http://localhost:8000/public")
       print("Try: curl -H 'Authorization: Bearer token' http://localhost:8000/protected")
       app.listen(port=8000)

RouterGroup Middleware
~~~~~~~~~~~~~~~~~~~~~~

Apply middleware to all routes within a RouterGroup using group-level middleware:

.. code-block:: python

   from catzilla import Catzilla, Request, Response, JSONResponse
   from catzilla.router import RouterGroup
   from typing import Optional
   import time

   app = Catzilla()

   def auth_middleware(request: Request) -> Optional[Response]:
       """Authentication middleware for protected routes"""
       auth_header = request.headers.get("Authorization") or request.headers.get("authorization")

       if not auth_header or not auth_header.startswith("Bearer "):
           return JSONResponse({
               "error": "Authentication required"
           }, status_code=401)

       # Add user info to request context
       if not hasattr(request, 'context'):
           request.context = {}
       request.context['user'] = {
           "id": "user123",
           "token": auth_header[7:]  # Remove "Bearer "
       }

       return None  # Continue to route handler

   def api_middleware(request: Request) -> Optional[Response]:
       """API-specific middleware"""
       if not hasattr(request, 'context'):
           request.context = {}
       request.context['api'] = {
           "version": "v1",
           "timestamp": time.time()
       }
       return None

   # Create RouterGroups with group-level middleware
   protected_group = RouterGroup(prefix="/protected", middleware=[auth_middleware])
   api_group = RouterGroup(prefix="/api", middleware=[api_middleware])

   # All routes in protected_group will automatically run auth_middleware
   @protected_group.get("/profile")
   def protected_profile(request: Request) -> Response:
       user = getattr(request, 'context', {}).get('user', {})
       return JSONResponse({
           "message": "Protected profile accessed",
           "user": user
       })

   @protected_group.get("/settings")
   def protected_settings(request: Request) -> Response:
       user = getattr(request, 'context', {}).get('user', {})
       return JSONResponse({
           "message": "Protected settings accessed",
           "user": user
       })

   # All routes in api_group will automatically run api_middleware
   @api_group.get("/status")
   def api_status(request: Request) -> Response:
       api_context = getattr(request, 'context', {}).get('api', {})
       return JSONResponse({
           "message": "API status",
           "api_context": api_context
       })

   # Combine group middleware with per-route middleware
   @api_group.get("/data", middleware=[auth_middleware])
   def api_data(request: Request) -> Response:
       """Group middleware + per-route middleware"""
       api_context = getattr(request, 'context', {}).get('api', {})
       user = getattr(request, 'context', {}).get('user', {})
       return JSONResponse({
           "message": "API data with combined middleware",
           "api_context": api_context,
           "user": user,
           "middleware_chain": [
               "1. Global middleware",
               "2. Group: API middleware",
               "3. Per-route: Auth middleware"
           ]
       })

   # Register router groups with the app
   app.include_routes(protected_group)
   app.include_routes(api_group)

   if __name__ == "__main__":
       print("🚀 Starting RouterGroup middleware example...")
       print("Try: curl -H 'Authorization: Bearer token' http://localhost:8000/protected/profile")
       print("Try: curl http://localhost:8000/api/status")
       print("Try: curl -H 'Authorization: Bearer token' http://localhost:8000/api/data")
       app.listen(port=8000)

Multiple RouterGroup Middleware
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Apply multiple middleware functions to a RouterGroup:

.. code-block:: python

   def rate_limit_middleware(request: Request) -> Optional[Response]:
       """Rate limiting middleware"""
       client_ip = request.headers.get("x-forwarded-for", "127.0.0.1")

       if not hasattr(request, 'context'):
           request.context = {}
       request.context['rate_limit'] = {
           'ip': client_ip,
           'remaining': 100
       }
       return None

   def admin_middleware(request: Request) -> Optional[Response]:
       """Admin access middleware"""
       user = getattr(request, 'context', {}).get('user')
       if not user:
           return JSONResponse({
               "error": "Authentication required"
           }, status_code=401)

       # Check admin privileges
       if user.get('token') != 'admin-token':
           return JSONResponse({
               "error": "Admin access required"
           }, status_code=403)

       return None

   # RouterGroup with multiple middleware (executes in order)
   admin_group = RouterGroup(
       prefix="/admin",
       middleware=[auth_middleware, rate_limit_middleware, admin_middleware]
   )

   @admin_group.get("/dashboard")
   def admin_dashboard(request: Request) -> Response:
       """Admin dashboard with triple middleware protection"""
       user = getattr(request, 'context', {}).get('user', {})
       rate_limit = getattr(request, 'context', {}).get('rate_limit', {})

       return JSONResponse({
           "message": "Admin dashboard accessed",
           "user": user,
           "rate_limit": rate_limit,
           "middleware_chain": [
               "1. Global middleware",
               "2. Group: Auth middleware",
               "3. Group: Rate limit middleware",
               "4. Group: Admin middleware"
           ]
       })

   app.include_routes(admin_group)

   if __name__ == "__main__":
       app.listen(port=8000)

Basic Middleware Patterns
--------------------------

Request Logging
~~~~~~~~~~~~~~~

Log all incoming requests:

.. code-block:: python

   from catzilla import Catzilla, Request, Response, JSONResponse
   from typing import Optional

   app = Catzilla()

   @app.middleware(priority=10, pre_route=True, name="request_logger")
   def request_logging_middleware(request: Request) -> Optional[Response]:
       """Log all requests"""
       print(f"📥 {request.method} {request.path}")
       print(f"   Headers: {dict(request.headers)}")

       # Add request info to context for response logging
       if not hasattr(request, 'context'):
           request.context = {}
       request.context['logged'] = True

       return None  # Continue to next middleware

   @app.middleware(priority=10, pre_route=False, post_route=True, name="response_logger")
   def response_logger_middleware(request: Request) -> Optional[Response]:
       """Log responses"""
       if getattr(request, 'context', {}).get('logged'):
           print(f"📤 Response processed for {request.method} {request.path}")
       return None

   @app.get("/")
   def home(request: Request) -> Response:
       return JSONResponse({"message": "Hello with request logging!"})

   if __name__ == "__main__":
       print("🚀 Starting request logging example...")
       print("Try: curl http://localhost:8000/")
       app.listen(port=8000)

CORS Middleware
~~~~~~~~~~~~~~~

Handle Cross-Origin Resource Sharing:

.. code-block:: python

   from catzilla import Catzilla, Request, Response, JSONResponse
   from typing import Optional

   app = Catzilla()

   @app.middleware(priority=50, pre_route=True, name="cors_handler")
   def cors_middleware(request: Request) -> Optional[Response]:
       """Add CORS headers"""
       print("🌍 CORS Middleware: Processing request")

       # Handle preflight requests
       if request.method == "OPTIONS":
           return Response("", headers={
               "Access-Control-Allow-Origin": "*",
               "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
               "Access-Control-Allow-Headers": "Content-Type, Authorization",
           })

       # Add CORS info to context for response processing
       if not hasattr(request, 'context'):
           request.context = {}
       request.context['cors_enabled'] = True

       return None  # Continue to next middleware

   @app.get("/")
   def home(request: Request) -> Response:
       return JSONResponse({"message": "CORS-enabled endpoint"})

   if __name__ == "__main__":
       print("🚀 Starting CORS middleware example...")
       print("Try: curl -X OPTIONS http://localhost:8000/")
       print("Try: curl http://localhost:8000/")
       app.listen(port=8000)


Error Handling Middleware
~~~~~~~~~~~~~~~~~~~~~~~~~

Catch and handle errors gracefully:

.. code-block:: python

   from catzilla import Catzilla, Request, Response, JSONResponse
   from typing import Optional

   app = Catzilla()

   @app.middleware(priority=100, pre_route=True, name="error_handler")
   def error_handling_middleware(request: Request) -> Optional[Response]:
       """Global error handling preparation"""
       # Add error handling context
       if not hasattr(request, 'context'):
           request.context = {}
       request.context['error_handling_enabled'] = True
       return None

   @app.get("/error")
   def error_endpoint(request):
       """Endpoint that triggers an error"""
       raise ValueError("This is a test error")

   @app.get("/")
   def home(request):
       return JSONResponse({"message": "Error handling middleware enabled"})

   if __name__ == "__main__":
       print("🚀 Starting error handling example...")
       print("Try: curl http://localhost:8000/")
       print("Try: curl http://localhost:8000/error")
       app.listen(port=8000)

Advanced Middleware
-------------------

Middleware with Priority
~~~~~~~~~~~~~~~~~~~~~~~~

Control middleware execution order:

.. code-block:: python

   from catzilla import Catzilla, Request, Response, JSONResponse
   from typing import Optional

   app = Catzilla()

   @app.middleware(priority=10, pre_route=True, name="security_headers")  # Executes first
   def security_middleware(request: Request) -> Optional[Response]:
       """Security headers - highest priority"""
       print("🔒 Security Middleware: Adding security context")

       if not hasattr(request, 'context'):
           request.context = {}
       request.context['security'] = {
           'x_frame_options': 'DENY',
           'x_content_type_options': 'nosniff'
       }
       return None

   @app.middleware(priority=50, pre_route=True, name="logging")   # Executes second
   def logging_middleware(request: Request) -> Optional[Response]:
       """Request logging"""
       print(f"📝 Logging Middleware: Processing {request.method} {request.path}")
       return None

   @app.middleware(priority=100, pre_route=True, name="analytics")   # Executes last
   def analytics_middleware(request: Request) -> Optional[Response]:
       """Analytics tracking"""
       print("📊 Analytics Middleware: Tracking request")
       return None

   @app.get("/")
   def home(request):
       return JSONResponse({
           "message": "Priority-ordered middleware example",
           "security": getattr(request, 'context', {}).get('security', {})
       })

   if __name__ == "__main__":
       print("🚀 Starting priority middleware example...")
       print("Execution order: security (10) → logging (50) → analytics (100)")
       print("Try: curl http://localhost:8000/")
       app.listen(port=8000)

Async Middleware
~~~~~~~~~~~~~~~~

Middleware that works with async operations:

.. code-block:: python

   import asyncio
   from catzilla import Catzilla, Request, Response, JSONResponse
   from typing import Optional

   app = Catzilla()

   @app.middleware(priority=50, pre_route=True, name="async_processor")
   def async_middleware(request: Request) -> Optional[Response]:
       """Sync middleware calling async operations"""
       async def async_processing():
           # Async preprocessing
           await asyncio.sleep(0.001)  # Simulate async operation
           print("🔄 Async Middleware: Async processing completed")

       # Run async function in sync middleware
       asyncio.run(async_processing())

       # Add async processing info to context
       if not hasattr(request, 'context'):
           request.context = {}
       request.context['async_processed'] = True

       return None  # Continue to next middleware

   # Works with both async and sync handlers
   @app.get("/async-handler")
   async def async_handler(request):
       await asyncio.sleep(0.01)
       return JSONResponse({
           "message": "Async handler with async middleware",
           "async_processed": getattr(request, 'context', {}).get('async_processed', False)
       })

   @app.get("/sync-handler")
   def sync_handler(request):
       return JSONResponse({
           "message": "Sync handler with async middleware",
           "async_processed": getattr(request, 'context', {}).get('async_processed', False)
       })

   if __name__ == "__main__":
       print("🚀 Starting async middleware example...")
       print("Try: curl http://localhost:8000/async-handler")
       print("Try: curl http://localhost:8000/sync-handler")
       app.listen(port=8000)

Conditional Middleware
~~~~~~~~~~~~~~~~~~~~~~

Middleware that applies based on conditions:

.. code-block:: python

   from catzilla import Catzilla, Request, Response, JSONResponse
   from typing import Optional

   app = Catzilla()

   def rate_limit_middleware(request: Request) -> Optional[Response]:
       """Rate limiting for API endpoints"""
       print(f"⏱️ Rate Limit: Checking path {request.path}")

       # Only apply rate limiting to API routes
       if not request.path.startswith("/api/"):
           print("⏭️ Rate Limit: Skipping non-API route")
           return None

       # Check rate limit (simplified example)
       client_ip = request.headers.get("X-Real-IP", "127.0.0.1")

       # In real implementation, check rate limit store (Redis, etc.)
       # For demo, allow all requests
       print(f"✅ Rate Limit: IP {client_ip} - OK")

       # Add rate limit info to context
       if not hasattr(request, 'context'):
           request.context = {}
       request.context['rate_limit'] = {
           'ip': client_ip,
           'remaining': 100
       }

       return None  # Continue to handler

   @app.get("/api/data", middleware=[rate_limit_middleware])
   def api_data(request):
       rate_limit = getattr(request, 'context', {}).get('rate_limit', {})
       return JSONResponse({
           "data": "API response with rate limiting",
           "rate_limit": rate_limit
       })

   @app.get("/regular")
   def regular_endpoint(request):
       return JSONResponse({"data": "Regular response without rate limiting"})

   if __name__ == "__main__":
       print("🚀 Starting conditional middleware example...")
       print("Try: curl http://localhost:8000/api/data")
       print("Try: curl http://localhost:8000/regular")
       app.listen(port=8000)

Middleware Composition
----------------------

Combining Multiple Middleware
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Chain multiple middleware for complex processing:

.. code-block:: python

   import uuid
   from catzilla import Catzilla, Request, Response, JSONResponse
   from typing import Optional

   app = Catzilla()

   def request_id_middleware(request: Request) -> Optional[Response]:
       """Add unique request ID"""
       request_id = str(uuid.uuid4())

       if not hasattr(request, 'context'):
           request.context = {}
       request.context['request_id'] = request_id

       print(f"🆔 Request ID: {request_id}")
       return None

   def user_context_middleware(request: Request) -> Optional[Response]:
       """Extract user context from JWT"""
       auth_header = request.headers.get("Authorization", "")

       if not hasattr(request, 'context'):
           request.context = {}

       if auth_header.startswith("Bearer "):
           # In real app, decode JWT
           request.context['user'] = {
               'id': 'user123',
               'role': 'admin'
           }
       else:
           request.context['user'] = {
               'id': None,
               'role': 'anonymous'
           }

       print(f"👤 User Context: {request.context['user']['role']}")
       return None

   def audit_middleware(request: Request) -> Optional[Response]:
       """Audit logging with user context"""
       context = getattr(request, 'context', {})
       request_id = context.get('request_id', 'unknown')
       user = context.get('user', {})

       # Log audit trail
       print(f"📋 AUDIT: {request_id} - "
             f"User: {user.get('id')} - "
             f"{request.method} {request.path}")

       return None

   # Apply middleware chain to specific routes
   middleware_chain = [request_id_middleware, user_context_middleware, audit_middleware]

   @app.get("/admin/users", middleware=middleware_chain)
   def admin_users(request):
       context = getattr(request, 'context', {})
       return JSONResponse({
           "users": ["user1", "user2"],
           "request_id": context.get('request_id'),
           "user_role": context.get('user', {}).get('role')
       })

   if __name__ == "__main__":
       print("🚀 Starting middleware composition example...")
       print("Try: curl -H 'Authorization: Bearer token' http://localhost:8000/admin/users")
       app.listen(port=8000)

RouterGroup Middleware Composition
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Organize complex middleware chains using RouterGroups:

.. code-block:: python

   from catzilla import Catzilla, Request, Response, JSONResponse
   from catzilla.router import RouterGroup
   from typing import Optional
   import time
   import uuid

   app = Catzilla()

   # Define reusable middleware functions
   def request_id_middleware(request: Request) -> Optional[Response]:
       """Add unique request ID"""
       request_id = str(uuid.uuid4())

       if not hasattr(request, 'context'):
           request.context = {}
       request.context['request_id'] = request_id
       return None

   def timing_middleware(request: Request) -> Optional[Response]:
       """Track request timing"""
       if not hasattr(request, 'context'):
           request.context = {}
       request.context['start_time'] = time.time()
       return None

   def auth_middleware(request: Request) -> Optional[Response]:
       """Authentication middleware"""
       auth_header = request.headers.get("Authorization")
       if not auth_header or not auth_header.startswith("Bearer "):
           return JSONResponse({"error": "Authentication required"}, status_code=401)

       if not hasattr(request, 'context'):
           request.context = {}
       request.context['user'] = {"id": "user123", "token": auth_header[7:]}
       return None

   def audit_middleware(request: Request) -> Optional[Response]:
       """Audit logging with context"""
       context = getattr(request, 'context', {})
       request_id = context.get('request_id', 'unknown')
       user_id = context.get('user', {}).get('id', 'anonymous')

       print(f"AUDIT: {request_id} - User: {user_id} - {request.method} {request.path}")
       return None

   # Create API v1 group with common middleware
   api_v1 = RouterGroup(
       prefix="/api/v1",
       middleware=[request_id_middleware, timing_middleware]
   )

   # Create protected API group with authentication
   protected_api = RouterGroup(
       prefix="/protected",
       middleware=[request_id_middleware, timing_middleware, auth_middleware, audit_middleware]
   )

   # API v1 routes (with request ID and timing)
   @api_v1.get("/status")
   def api_status(request):
       context = getattr(request, 'context', {})
       return JSONResponse({
           "status": "OK",
           "request_id": context.get('request_id'),
           "start_time": context.get('start_time')
       })

   # Protected routes (with full middleware chain)
   @protected_api.get("/user-data")
   def protected_user_data(request):
       context = getattr(request, 'context', {})
       return JSONResponse({
           "message": "Protected user data",
           "request_id": context.get('request_id'),
           "user": context.get('user'),
           "processing_time": time.time() - context.get('start_time', 0)
       })

   # Nested RouterGroups for complex organization
   admin_api = RouterGroup(prefix="/admin")

   # Admin users subgroup with additional middleware
   admin_users = RouterGroup(
       prefix="/users",
       middleware=[auth_middleware, audit_middleware]
   )

   @admin_users.get("/")
   def admin_list_users(request):
       return JSONResponse({"users": ["user1", "user2"]})

   # Include the users group in admin group, then in main app
   admin_api.include_group(admin_users)

   app.include_routes(api_v1)
   app.include_routes(protected_api)
   app.include_routes(admin_api)

   if __name__ == "__main__":
       app.listen(port=8000)

Custom Middleware Classes
~~~~~~~~~~~~~~~~~~~~~~~~~

Create reusable middleware classes:

.. code-block:: python

   from catzilla import Catzilla, Request, Response, JSONResponse
   from typing import Optional
   import time

   app = Catzilla()

   class SecurityMiddleware:
       def __init__(self, enabled_headers=None):
           self.enabled_headers = enabled_headers or [
               "X-Frame-Options",
               "X-Content-Type-Options",
               "X-XSS-Protection"
           ]

       def __call__(self, request: Request) -> Optional[Response]:
           # Store headers to be added in response middleware
           if not hasattr(request, 'context'):
               request.context = {}
           request.context['security_headers'] = {}

           if "X-Frame-Options" in self.enabled_headers:
               request.context['security_headers']["X-Frame-Options"] = "DENY"

           if "X-Content-Type-Options" in self.enabled_headers:
               request.context['security_headers']["X-Content-Type-Options"] = "nosniff"

           if "X-XSS-Protection" in self.enabled_headers:
               request.context['security_headers']["X-XSS-Protection"] = "1; mode=block"

           return None

   class MetricsMiddleware:
       def __init__(self):
           self.request_count = 0
           self.total_time = 0.0

       def __call__(self, request: Request) -> Optional[Response]:
           # Store start time for response middleware to calculate duration
           if not hasattr(request, 'context'):
               request.context = {}
           request.context['metrics_start'] = time.time()

           self.request_count += 1
           request.context['request_count'] = self.request_count

           return None

   # Response middleware to add headers (would typically be a separate decorator)
   def add_security_headers(request: Request) -> Optional[Response]:
       # This would be implemented as a post-route middleware
       # For now, demonstrating the pattern
       return None

   # Create middleware class instances
   security_middleware = SecurityMiddleware()
   metrics_middleware = MetricsMiddleware()

   # Register middleware instances with the app
   # Note: Use function call syntax for class instances, not decorator syntax
   app.middleware(priority=100, name="security")(security_middleware)
   app.middleware(priority=110, name="metrics")(metrics_middleware)

   # For comparison - this is how you'd register a function:
   # @app.middleware(priority=120, name="function_middleware")
   # def some_function_middleware(request: Request) -> Optional[Response]:
   #     return None

   @app.get("/metrics-demo")
   def metrics_demo(request: Request) -> Response:
       # Access metrics data from context
       context = getattr(request, 'context', {})
       request_count = context.get('request_count', 0)

       return JSONResponse({
           "message": "Response with metrics tracking",
           "request_count": request_count
       })

   if __name__ == "__main__":
       app.listen(port=8000)

Production Patterns
-------------------

Request/Response Validation
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Validate requests and sanitize responses:

.. code-block:: python

   from catzilla import Catzilla, Request, Response, JSONResponse
   from typing import Optional

   app = Catzilla()

   @app.middleware(priority=100, name="request_validation")
   def request_validation_middleware(request: Request) -> Optional[Response]:
       """Validate request format"""
       # Check content type for POST/PUT requests
       if request.method in ["POST", "PUT"]:
           content_type = request.headers.get("Content-Type", "")
           if not content_type.startswith("application/json"):
               return JSONResponse(
                   {"error": "Content-Type must be application/json"},
                   status_code=400
               )

       # Check request size
       content_length = request.headers.get("Content-Length", "0")
       try:
           if int(content_length) > 1024 * 1024:  # 1MB limit
               return JSONResponse(
                   {"error": "Request too large"},
                   status_code=413
               )
       except ValueError:
           pass

       return None

   @app.middleware(priority=200, name="security_headers")
   def security_headers_middleware(request: Request) -> Optional[Response]:
       """Add security headers via context"""
       if not hasattr(request, 'context'):
           request.context = {}

       # Store security headers to be added in post-processing
       request.context['security_headers'] = {
           "X-Content-Type-Options": "nosniff",
           "X-Frame-Options": "DENY",
           "X-XSS-Protection": "1; mode=block"
       }

       # Mark sensitive headers for removal
       request.context['remove_headers'] = ["X-Powered-By", "Server"]

       return None

   @app.get("/api/upload")
   def upload_endpoint(request: Request) -> Response:
       """Example endpoint that benefits from validation middleware"""
       return JSONResponse({
           "message": "Upload endpoint with validation",
           "security_headers": getattr(request, 'context', {}).get('security_headers', {})
       })

   @app.post("/api/data")
   def create_data(request: Request) -> Response:
       """Example POST endpoint"""
       return JSONResponse({"message": "Data created successfully"})

   if __name__ == "__main__":
       print("🚀 Starting request/response validation example...")
       print("Try: curl -H 'Content-Type: application/json' -d '{}' http://localhost:8000/api/data")
       print("Try: curl -H 'Content-Type: text/plain' -d 'test' http://localhost:8000/api/data")
       app.listen(port=8000)

Performance Monitoring
~~~~~~~~~~~~~~~~~~~~~~

Monitor application performance:

.. code-block:: python

   from catzilla import Catzilla, Request, Response, JSONResponse
   from typing import Optional
   import time
   import psutil
   import os

   app = Catzilla()

   class PerformanceMonitor:
       def __init__(self):
           self.slow_requests = []
           self.request_times = []

       def get_memory_usage(self):
           """Get current memory usage in MB"""
           process = psutil.Process(os.getpid())
           return process.memory_info().rss / 1024 / 1024

       def __call__(self, request: Request) -> Optional[Response]:
           start_time = time.time()
           start_memory = self.get_memory_usage()

           if not hasattr(request, 'context'):
               request.context = {}

           # Store performance tracking data
           request.context['perf_start_time'] = start_time
           request.context['perf_start_memory'] = start_memory
           request.context['perf_monitor'] = self

           return None

   # Response middleware to calculate and log performance metrics
   def performance_response_middleware(request: Request) -> Optional[Response]:
       """Log performance metrics after request processing"""
       context = getattr(request, 'context', {})

       if 'perf_start_time' in context:
           start_time = context['perf_start_time']
           start_memory = context['perf_start_memory']
           perf_monitor = context.get('perf_monitor')

           if perf_monitor:
               end_time = time.time()
               end_memory = perf_monitor.get_memory_usage()

               processing_time = end_time - start_time
               memory_used = end_memory - start_memory

               # Track performance metrics
               perf_monitor.request_times.append(processing_time)

               # Log slow requests
               if processing_time > 1.0:  # > 1 second
                   perf_monitor.slow_requests.append({
                       "path": request.path,
                       "method": request.method,
                       "time": processing_time,
                       "memory": memory_used
                   })

               print(f"Request {request.method} {request.path} took {processing_time:.3f}s")

       return None

   # Apply performance monitoring
   perf_monitor = PerformanceMonitor()
   app.middleware(priority=50, name="perf_start")(perf_monitor)

   @app.middleware(priority=900, name="perf_end", pre_route=False, post_route=True)
   def performance_response_middleware(request: Request) -> Optional[Response]:
       """Log performance metrics after request processing"""
       context = getattr(request, 'context', {})

       if 'perf_start_time' in context:
           start_time = context['perf_start_time']
           start_memory = context['perf_start_memory']
           perf_monitor = context.get('perf_monitor')

           if perf_monitor:
               end_time = time.time()
               end_memory = perf_monitor.get_memory_usage()

               processing_time = end_time - start_time
               memory_used = end_memory - start_memory

               # Track performance metrics
               perf_monitor.request_times.append(processing_time)

               # Log slow requests
               if processing_time > 1.0:  # > 1 second
                   perf_monitor.slow_requests.append({
                       "path": request.path,
                       "method": request.method,
                       "time": processing_time,
                       "memory": memory_used
                   })

               print(f"Request {request.method} {request.path} took {processing_time:.3f}s")

       return None

   @app.get("/performance-stats")
   def performance_stats(request: Request):
       if perf_monitor.request_times:
           avg_time = sum(perf_monitor.request_times) / len(perf_monitor.request_times)
       else:
           avg_time = 0.0

       return JSONResponse({
           "total_requests": len(perf_monitor.request_times),
           "average_response_time": f"{avg_time:.4f}s",
           "slow_requests_count": len(perf_monitor.slow_requests),
           "slow_requests": perf_monitor.slow_requests[-5:]  # Last 5
       })

   @app.get("/test-slow")
   def slow_endpoint(request: Request) -> Response:
       """Test endpoint that's intentionally slow"""
       import time
       time.sleep(1.5)  # Simulate slow processing
       return JSONResponse({"message": "Slow endpoint completed"})

   if __name__ == "__main__":
       print("🚀 Starting performance monitoring example...")
       print("Try: curl http://localhost:8000/performance-stats")
       print("Try: curl http://localhost:8000/test-slow")
       app.listen(port=8000)

Best Practices
--------------

RouterGroup Middleware Best Practices
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Guidelines for effective RouterGroup middleware usage:

.. code-block:: python

   # ✅ Good: Logical grouping with shared middleware
   auth_required_group = RouterGroup(
       prefix="/protected",
       middleware=[auth_middleware]
   )

   api_group = RouterGroup(
       prefix="/api",
       middleware=[rate_limit_middleware, api_versioning_middleware]
   )

   # ✅ Good: Combine group and per-route middleware strategically
   @api_group.get("/upload", middleware=[file_validation_middleware])
   def upload_file(request):
       # Runs: rate_limit -> api_versioning -> file_validation -> handler
       pass

   # ✅ Good: Keep middleware functions pure and reusable
   def cors_middleware(request: Request):
       """Reusable CORS middleware"""
       if not hasattr(request, 'context'):
           request.context = {}
       request.context['cors_enabled'] = True
       return None

   # ❌ Avoid: Too many middleware in one group (performance impact)
   heavy_group = RouterGroup(
       prefix="/heavy",
       middleware=[
           auth_middleware, rate_limit_middleware, audit_middleware,
           validation_middleware, logging_middleware, metrics_middleware,
           security_middleware, caching_middleware  # Too many!
       ]
   )

   # ✅ Better: Split into logical layers
   base_group = RouterGroup(
       prefix="/api",
       middleware=[rate_limit_middleware, auth_middleware]
   )

   @base_group.get("/data", middleware=[validation_middleware])
   def get_data(request):
       # Clear middleware chain: rate_limit -> auth -> validation -> handler
       pass

   # ✅ Good: Document middleware execution order
   """
   Middleware Execution Order for /protected/admin/users:

   1. Global: request_logger_middleware (priority 10)
   2. Global: cors_middleware (priority 50)
   3. Global: security_middleware (priority 100)
   4. Group: auth_middleware (from protected_group)
   5. Group: admin_middleware (from protected_group)
   6. Per-route: audit_middleware (from route decorator)
   7. Route Handler: admin_users()
   8. Response flows back through middleware in reverse order
   """

   if __name__ == "__main__":
       app.listen(port=8000)

Middleware Order
~~~~~~~~~~~~~~~~

Understand middleware execution order:

.. code-block:: text

   Request Flow:

   1. Global Middleware (by priority)
      - Security Middleware (priority=100)       ↓
      - CORS Middleware (priority=50)            ↓
      - Auth Middleware (priority=30)            ↓
      - Logging Middleware (priority=10)         ↓

   2. RouterGroup Middleware (in order)
      - Group Middleware 1                       ↓
      - Group Middleware 2                       ↓
      - Group Middleware N                       ↓

   3. Per-Route Middleware (in order)
      - Route Middleware 1                       ↓
      - Route Middleware 2                       ↓
      - Route Middleware N                       ↓

   4. Route Handler                              ↓

   5. Response Flow (reverse order)
      - Route Middleware N                       ↑
      - Route Middleware 2                       ↑
      - Route Middleware 1                       ↑
      - Group Middleware N                       ↑
      - Group Middleware 2                       ↑
      - Group Middleware 1                       ↑
      - Logging Middleware                       ↑
      - Auth Middleware                          ↑
      - CORS Middleware                          ↑
      - Security Middleware                      ↑

   Example with RouterGroup:

   protected_group = RouterGroup(
       prefix="/protected",
       middleware=[auth_middleware, rate_limit_middleware]
   )

   @protected_group.get("/data", middleware=[validation_middleware])
   def get_data(request):
       return JSONResponse({"data": "response"})

   Execution order for GET /protected/data:
   1. Global middlewares (by priority)
   2. auth_middleware (from RouterGroup)
   3. rate_limit_middleware (from RouterGroup)
   4. validation_middleware (from route)
   5. get_data() handler
   6. Response flows back through all middleware in reverse

Error Handling
~~~~~~~~~~~~~~

Best practices for middleware error handling:

.. code-block:: python

   from catzilla import Catzilla, Request, Response, JSONResponse
   from typing import Optional
   import time

   app = Catzilla()

   @app.middleware(priority=100, name="robust")
   def robust_middleware(request: Request) -> Optional[Response]:
       """Middleware with proper error handling"""
       try:
           # Pre-processing
           if not hasattr(request, 'context'):
               request.context = {}
           request.context['middleware_start'] = time.time()

           # Store success marker for post-processing
           request.context['middleware_success'] = True

           return None

       except Exception as e:
           # Log the error
           print(f"Middleware error: {e}")

           # Return error response
           return JSONResponse(
               {"error": "Middleware processing failed"},
               status_code=500
           )

   # Post-processing middleware to add timing headers
   @app.middleware(priority=900, name="timing", pre_route=False, post_route=True)
   def timing_response_middleware(request: Request) -> Optional[Response]:
       """Add timing headers after request processing"""
       context = getattr(request, 'context', {})

       if 'middleware_start' in context and context.get('middleware_success'):
           processing_time = time.time() - context['middleware_start']
           # In a real implementation, this would modify the response headers
           print(f"Processing time: {processing_time:.4f}s")

       return None

   @app.get("/")
   def home(request: Request) -> Response:
       """Test route with error handling middleware"""
       return JSONResponse({
           "message": "Error handling middleware enabled",
           "middleware_success": getattr(request, 'context', {}).get('middleware_success', False)
       })

   @app.get("/error-test")
   def error_test(request: Request) -> Response:
       """Route that might cause middleware errors"""
       # Simulate potential error condition
       import random
       if random.random() < 0.1:  # 10% chance of error
           raise Exception("Simulated error")

       return JSONResponse({"message": "No error occurred"})

   if __name__ == "__main__":
       print("🚀 Starting error handling middleware example...")
       print("Try: curl http://localhost:8000/")
       print("Try: curl http://localhost:8000/error-test")
       app.listen(port=8000)

Performance Tips
~~~~~~~~~~~~~~~~

Optimize middleware for production:

.. code-block:: python

   from catzilla import Catzilla, Request, Response, JSONResponse
   from typing import Optional

   app = Catzilla()

   # ✅ Good: Minimal processing in middleware
   @app.middleware(priority=100, name="fast")
   def fast_middleware(request: Request) -> Optional[Response]:
       # Quick check
       if request.method == "OPTIONS":
           return Response("", status_code=200)

       return None

   # ❌ Avoid: Heavy processing in middleware
   def slow_middleware(request: Request) -> Optional[Response]:
       # Heavy processing in middleware slows down ALL requests
       # This should be avoided for global middleware
       print("Performing heavy computation for all requests (BAD)")
       return None

   # ✅ Good: Use per-route middleware for expensive operations
   def expensive_middleware(request: Request) -> Optional[Response]:
       # Only applied to specific routes that need it
       print("Performing expensive operation for specific route")
       if not hasattr(request, 'context'):
           request.context = {}
       request.context['expensive_operation_done'] = True
       return None

   @app.get("/expensive-route", middleware=[expensive_middleware])
   def expensive_route(request: Request) -> Response:
       context = getattr(request, 'context', {})
       operation_done = context.get('expensive_operation_done', False)

       return JSONResponse({
           "message": "Expensive operation complete",
           "operation_performed": operation_done
       })

   @app.get("/fast")
   def fast_route(request: Request) -> Response:
       """Fast route that benefits from minimal middleware"""
       return JSONResponse({
           "message": "Fast route with minimal middleware overhead"
       })

   if __name__ == "__main__":
       print("🚀 Starting performance tips example...")
       print("Try: curl http://localhost:8000/fast")
       print("Try: curl http://localhost:8000/expensive-route")
       app.listen(port=8000)

This middleware system provides the flexibility and performance you need to build robust, production-ready applications with Catzilla.
