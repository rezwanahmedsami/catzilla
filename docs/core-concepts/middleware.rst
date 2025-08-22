Middleware
==========

Catzilla provides a powerful, **zero-allocation middleware system** with both global and per-route middleware support. Build custom middleware chains with optimal performance and minimal memory overhead.

Overview
--------

Catzilla's middleware system provides:

- **Global Middleware** - Applied to all routes with ``@app.middleware()``
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

   @app.middleware()
   def timing_middleware(request: Request, call_next):
       """Measure request processing time"""
       start_time = time.time()

       # Process request
       response = call_next(request)

       # Add timing header
       processing_time = time.time() - start_time
       response.headers["X-Process-Time"] = f"{processing_time:.4f}"

       return response

   @app.get("/")
   def home(request):
       return JSONResponse({"message": "Hello with timing middleware!"})

   if __name__ == "__main__":
       app.listen(port=8000)

Per-Route Middleware
~~~~~~~~~~~~~~~~~~~~

Apply middleware to specific routes only:

.. code-block:: python

   def auth_middleware(request: Request, call_next):
       """Check authentication"""
       auth_header = request.headers.get("Authorization")

       if not auth_header or not auth_header.startswith("Bearer "):
           return JSONResponse(
               {"error": "Missing or invalid authentication"},
               status_code=401
           )

       # Authentication passed, continue
       return call_next(request)

   # Apply middleware only to protected routes
   @app.get("/protected", middleware=[auth_middleware])
   def protected_endpoint(request):
       return JSONResponse({"message": "You are authenticated!"})

   @app.get("/public")
   def public_endpoint(request):
       return JSONResponse({"message": "No authentication required"})

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

Middleware Order
~~~~~~~~~~~~~~~~

Understand middleware execution order:

.. code-block:: text

   Request Flow:

   1. Security Middleware (priority=100)     ↓
   2. CORS Middleware (priority=50)          ↓
   3. Auth Middleware (priority=30)          ↓
   4. Logging Middleware (priority=10)       ↓
   5. Route Handler                          ↓
   6. Logging Middleware                     ↑
   7. Auth Middleware                        ↑
   8. CORS Middleware                        ↑
   9. Security Middleware                    ↑

   Response Flow (reverse order)

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
