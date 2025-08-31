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
   import time

   app = Catzilla()

   @app.middleware(priority=10, pre_route=True, name="timing_middleware")
   def timing_middleware(request: Request):
       """Measure request processing time"""
       import time
       start_time = time.time()

       # Store start time in request context for response processing
       if not hasattr(request, 'context'):
           request.context = {}
       request.context['start_time'] = start_time

       print(f"⏱️ Request started at {start_time}")
       return None  # Continue to next middleware

   @app.get("/")
   def home(request):
       return JSONResponse({"message": "Hello with timing middleware!"})

   if __name__ == "__main__":
       app.listen(port=8000)

Per-Route Middleware
~~~~~~~~~~~~~~~~~~~~

Apply middleware to specific routes only:

.. code-block:: python

   from catzilla import Catzilla, Request, Response, JSONResponse

   app = Catzilla()

   def auth_middleware(request: Request):
       """Check authentication"""
       auth_header = request.headers.get("Authorization")

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
   def protected_endpoint(request):
       user = getattr(request, 'context', {}).get('user', {})
       return JSONResponse({
           "message": "You are authenticated!",
           "user": user
       })

   @app.get("/public")
   def public_endpoint(request):
       return JSONResponse({"message": "No authentication required"})

   if __name__ == "__main__":
       app.listen(port=8000)

RouterGroup Middleware
~~~~~~~~~~~~~~~~~~~~~~

Apply middleware to all routes within a RouterGroup using group-level middleware:

.. code-block:: python

   from catzilla import Catzilla, Request, Response, JSONResponse
   from catzilla.router import RouterGroup

   app = Catzilla()

   def auth_middleware(request: Request):
       """Authentication middleware for protected routes"""
       auth_header = request.headers.get("Authorization")

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

   def api_middleware(request: Request):
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
   def protected_profile(request):
       user = getattr(request, 'context', {}).get('user', {})
       return JSONResponse({
           "message": "Protected profile accessed",
           "user": user
       })

   @protected_group.get("/settings")
   def protected_settings(request):
       user = getattr(request, 'context', {}).get('user', {})
       return JSONResponse({
           "message": "Protected settings accessed",
           "user": user
       })

   # All routes in api_group will automatically run api_middleware
   @api_group.get("/status")
   def api_status(request):
       api_context = getattr(request, 'context', {}).get('api', {})
       return JSONResponse({
           "message": "API status",
           "api_context": api_context
       })

   # Combine group middleware with per-route middleware
   @api_group.get("/data", middleware=[auth_middleware])
   def api_data(request):
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
       app.listen(port=8000)

Multiple RouterGroup Middleware
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Apply multiple middleware functions to a RouterGroup:

.. code-block:: python

   def rate_limit_middleware(request: Request):
       """Rate limiting middleware"""
       client_ip = request.headers.get("x-forwarded-for", "127.0.0.1")

       if not hasattr(request, 'context'):
           request.context = {}
       request.context['rate_limit'] = {
           'ip': client_ip,
           'remaining': 100
       }
       return None

   def admin_middleware(request: Request):
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
   def admin_dashboard(request):
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

   @app.middleware()
   def request_logging_middleware(request: Request, call_next):
       """Log all requests"""
       print(f"📥 {request.method} {request.url}")
       print(f"   Headers: {dict(request.headers)}")

       response = call_next(request)

       print(f"📤 Response: {response.status_code}")
       return response

   if __name__ == "__main__":
       app.listen(port=8000)

CORS Middleware
~~~~~~~~~~~~~~~

Handle Cross-Origin Resource Sharing:

.. code-block:: python

   @app.middleware()
   def cors_middleware(request: Request, call_next):
       """Add CORS headers"""
       # Handle preflight requests
       if request.method == "OPTIONS":
           return Response("", headers={
               "Access-Control-Allow-Origin": "*",
               "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
               "Access-Control-Allow-Headers": "Content-Type, Authorization",
           })

       response = call_next(request)

       # Add CORS headers to all responses
       response.headers["Access-Control-Allow-Origin"] = "*"
       response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"

       return response

   if __name__ == "__main__":
       app.listen(port=8000)

Error Handling Middleware
~~~~~~~~~~~~~~~~~~~~~~~~~

Catch and handle errors gracefully:

.. code-block:: python

   @app.middleware()
   def error_handling_middleware(request: Request, call_next):
       """Global error handling"""
       try:
           return call_next(request)
       except ValueError as e:
           return JSONResponse(
               {"error": "Invalid input", "details": str(e)},
               status_code=400
           )
       except Exception as e:
           print(f"❌ Unhandled error: {e}")
           return JSONResponse(
               {"error": "Internal server error"},
               status_code=500
           )

   if __name__ == "__main__":
       app.listen(port=8000)

Advanced Middleware
-------------------

Middleware with Priority
~~~~~~~~~~~~~~~~~~~~~~~~

Control middleware execution order:

.. code-block:: python

   @app.middleware(priority=10)  # Executes first (highest priority)
   def security_middleware(request: Request, call_next):
       """Security headers - highest priority"""
       response = call_next(request)
       response.headers["X-Frame-Options"] = "DENY"
       response.headers["X-Content-Type-Options"] = "nosniff"
       return response

   @app.middleware(priority=5)   # Executes second
   def logging_middleware(request: Request, call_next):
       """Request logging"""
       print(f"Processing: {request.method} {request.url}")
       return call_next(request)

   @app.middleware(priority=1)   # Executes last (lowest priority)
   def analytics_middleware(request: Request, call_next):
       """Analytics tracking"""
       response = call_next(request)
       # Send analytics data
       return response

   if __name__ == "__main__":
       app.listen(port=8000)

Async Middleware
~~~~~~~~~~~~~~~~

Middleware that works with async operations:

.. code-block:: python

   import asyncio

   @app.middleware()
   async def async_middleware(request: Request, call_next):
       """Async middleware example"""
       # Async preprocessing
       await asyncio.sleep(0.001)  # Simulate async operation

       # Call next middleware/handler
       response = call_next(request)

       # Async postprocessing
       await asyncio.sleep(0.001)  # Simulate async operation

       response.headers["X-Async-Processed"] = "true"
       return response

   # Works with both async and sync handlers
   @app.get("/async-handler")
   async def async_handler(request):
       await asyncio.sleep(0.01)
       return JSONResponse({"message": "Async handler with async middleware"})

   @app.get("/sync-handler")
   def sync_handler(request):
       return JSONResponse({"message": "Sync handler with async middleware"})

   if __name__ == "__main__":
       app.listen(port=8000)

Conditional Middleware
~~~~~~~~~~~~~~~~~~~~~~

Middleware that applies based on conditions:

.. code-block:: python

   def rate_limit_middleware(request: Request, call_next):
       """Rate limiting for API endpoints"""
       # Only apply rate limiting to API routes
       if not request.url.path.startswith("/api/"):
           return call_next(request)

       # Check rate limit (simplified example)
       client_ip = request.headers.get("X-Real-IP", "unknown")

       # In real implementation, check rate limit store (Redis, etc.)
       # For demo, allow all requests

       response = call_next(request)
       response.headers["X-RateLimit-Remaining"] = "100"
       return response

   @app.get("/api/data", middleware=[rate_limit_middleware])
   def api_data(request):
       return JSONResponse({"data": "API response with rate limiting"})

   @app.get("/regular")
   def regular_endpoint(request):
       return JSONResponse({"data": "Regular response without rate limiting"})

   if __name__ == "__main__":
       app.listen(port=8000)

Middleware Composition
----------------------

Combining Multiple Middleware
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Chain multiple middleware for complex processing:

.. code-block:: python

   def request_id_middleware(request: Request, call_next):
       """Add unique request ID"""
       import uuid
       request_id = str(uuid.uuid4())
       request.state.request_id = request_id

       response = call_next(request)
       response.headers["X-Request-ID"] = request_id
       return response

   def user_context_middleware(request: Request, call_next):
       """Extract user context from JWT"""
       auth_header = request.headers.get("Authorization", "")

       if auth_header.startswith("Bearer "):
           # In real app, decode JWT
           request.state.user_id = "user123"
           request.state.user_role = "admin"
       else:
           request.state.user_id = None
           request.state.user_role = "anonymous"

       return call_next(request)

   def audit_middleware(request: Request, call_next):
       """Audit logging with user context"""
       response = call_next(request)

       # Log audit trail
       print(f"AUDIT: {request.state.request_id} - "
             f"User: {request.state.user_id} - "
             f"{request.method} {request.url} - "
             f"Status: {response.status_code}")

       return response

   # Apply middleware chain to specific routes
   middleware_chain = [request_id_middleware, user_context_middleware, audit_middleware]

   @app.get("/admin/users", middleware=middleware_chain)
   def admin_users(request):
       return JSONResponse({
           "users": ["user1", "user2"],
           "request_id": request.state.request_id,
           "user_role": request.state.user_role
       })

   if __name__ == "__main__":
       app.listen(port=8000)

RouterGroup Middleware Composition
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Organize complex middleware chains using RouterGroups:

.. code-block:: python

   from catzilla.router import RouterGroup
   import time

   # Define reusable middleware functions
   def request_id_middleware(request: Request):
       """Add unique request ID"""
       import uuid
       request_id = str(uuid.uuid4())

       if not hasattr(request, 'context'):
           request.context = {}
       request.context['request_id'] = request_id
       return None

   def timing_middleware(request: Request):
       """Track request timing"""
       if not hasattr(request, 'context'):
           request.context = {}
       request.context['start_time'] = time.time()
       return None

   def auth_middleware(request: Request):
       """Authentication middleware"""
       auth_header = request.headers.get("Authorization")
       if not auth_header or not auth_header.startswith("Bearer "):
           return JSONResponse({"error": "Authentication required"}, status_code=401)

       if not hasattr(request, 'context'):
           request.context = {}
       request.context['user'] = {"id": "user123", "token": auth_header[7:]}
       return None

   def audit_middleware(request: Request):
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

   class SecurityMiddleware:
       def __init__(self, enabled_headers=None):
           self.enabled_headers = enabled_headers or [
               "X-Frame-Options",
               "X-Content-Type-Options",
               "X-XSS-Protection"
           ]

       def __call__(self, request: Request, call_next):
           response = call_next(request)

           if "X-Frame-Options" in self.enabled_headers:
               response.headers["X-Frame-Options"] = "DENY"

           if "X-Content-Type-Options" in self.enabled_headers:
               response.headers["X-Content-Type-Options"] = "nosniff"

           if "X-XSS-Protection" in self.enabled_headers:
               response.headers["X-XSS-Protection"] = "1; mode=block"

           return response

   class MetricsMiddleware:
       def __init__(self):
           self.request_count = 0
           self.total_time = 0.0

       def __call__(self, request: Request, call_next):
           start_time = time.time()

           response = call_next(request)

           processing_time = time.time() - start_time
           self.request_count += 1
           self.total_time += processing_time

           response.headers["X-Request-Count"] = str(self.request_count)
           response.headers["X-Avg-Response-Time"] = f"{self.total_time / self.request_count:.4f}"

           return response

   # Use middleware classes
   security_middleware = SecurityMiddleware()
   metrics_middleware = MetricsMiddleware()

   @app.middleware()
   def global_security(request: Request, call_next):
       return security_middleware(request, call_next)

   @app.get("/metrics-demo", middleware=[lambda r, c: metrics_middleware(r, c)])
   def metrics_demo(request):
       return JSONResponse({"message": "Response with metrics tracking"})

   if __name__ == "__main__":
       app.listen(port=8000)

Production Patterns
-------------------

Request/Response Validation
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Validate requests and sanitize responses:

.. code-block:: python

   def request_validation_middleware(request: Request, call_next):
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
       if int(content_length) > 1024 * 1024:  # 1MB limit
           return JSONResponse(
               {"error": "Request too large"},
               status_code=413
           )

       return call_next(request)

   def response_sanitization_middleware(request: Request, call_next):
       """Sanitize response data"""
       response = call_next(request)

       # Remove sensitive headers
       sensitive_headers = ["X-Powered-By", "Server"]
       for header in sensitive_headers:
           response.headers.pop(header, None)

       return response

Performance Monitoring
~~~~~~~~~~~~~~~~~~~~~~

Monitor application performance:

.. code-block:: python

   class PerformanceMonitor:
       def __init__(self):
           self.slow_requests = []
           self.request_times = []

       def __call__(self, request: Request, call_next):
           start_time = time.time()
           start_memory = self.get_memory_usage()

           response = call_next(request)

           end_time = time.time()
           end_memory = self.get_memory_usage()

           processing_time = end_time - start_time
           memory_used = end_memory - start_memory

           # Track performance metrics
           self.request_times.append(processing_time)

           # Log slow requests
           if processing_time > 1.0:  # > 1 second
               self.slow_requests.append({
                   "path": str(request.url),
                   "method": request.method,
                   "time": processing_time,
                   "memory": memory_used
               })

           # Add performance headers
           response.headers["X-Response-Time"] = f"{processing_time:.4f}"
           response.headers["X-Memory-Used"] = f"{memory_used:.2f}MB"

           return response

       def get_memory_usage(self):
           import psutil
           return psutil.Process().memory_info().rss / 1024 / 1024

   performance_monitor = PerformanceMonitor()

   @app.middleware()
   def performance_tracking(request: Request, call_next):
       return performance_monitor(request, call_next)

   @app.get("/performance-stats")
   def performance_stats(request):
       avg_time = sum(performance_monitor.request_times) / len(performance_monitor.request_times)
       return JSONResponse({
           "total_requests": len(performance_monitor.request_times),
           "average_response_time": f"{avg_time:.4f}s",
           "slow_requests_count": len(performance_monitor.slow_requests),
           "slow_requests": performance_monitor.slow_requests[-5:]  # Last 5
       })

   if __name__ == "__main__":
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

   @app.middleware()
   def robust_middleware(request: Request, call_next):
       """Middleware with proper error handling"""
       try:
           # Pre-processing
           request.state.middleware_start = time.time()

           # Call next middleware/handler
           response = call_next(request)

           # Post-processing
           processing_time = time.time() - request.state.middleware_start
           response.headers["X-Middleware-Time"] = f"{processing_time:.4f}"

           return response

       except Exception as e:
           # Log the error
           print(f"Middleware error: {e}")

           # Return error response
           return JSONResponse(
               {"error": "Middleware processing failed"},
               status_code=500
           )

   if __name__ == "__main__":
       app.listen(port=8000)

Performance Tips
~~~~~~~~~~~~~~~~

Optimize middleware for production:

.. code-block:: python

   # ✅ Good: Minimal processing in middleware
   @app.middleware()
   def fast_middleware(request: Request, call_next):
       # Quick check
       if request.method == "OPTIONS":
           return Response("", status_code=200)

       return call_next(request)

   # ❌ Avoid: Heavy processing in middleware
   @app.middleware()
   def slow_middleware(request: Request, call_next):
       # Heavy database query in middleware
       # This will slow down ALL requests
       heavy_computation()
       return call_next(request)

   # ✅ Good: Use per-route middleware for expensive operations
   def expensive_middleware(request: Request, call_next):
       # Only applied to specific routes that need it
       heavy_computation()
       return call_next(request)

   @app.get("/expensive-route", middleware=[expensive_middleware])
   def expensive_route(request):
       return JSONResponse({"message": "Expensive operation complete"})

   if __name__ == "__main__":
       app.listen(port=8000)

This middleware system provides the flexibility and performance you need to build robust, production-ready applications with Catzilla.
