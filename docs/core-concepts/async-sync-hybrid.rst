Async/Sync Hybrid System
========================

Catzilla's key feature is its **async/sync hybrid system**. Unlike other frameworks that force you to choose one approach, Catzilla automatically detects your handler type and executes it in the optimal context.

Why Hybrid Matters
------------------

Traditional frameworks have limitations:

**Async-Only Frameworks (like FastAPI)**
  - Force everything to be async, even CPU-bound tasks
  - Inefficient for simple operations
  - Complex mental model for beginners
  - Poor performance for mixed workloads

**Sync-Only Frameworks (like Flask)**
  - Block the entire thread on I/O operations
  - Cannot handle concurrent requests efficiently
  - Poor scalability for I/O-heavy applications

**Catzilla's Solution: Automatic Hybrid Execution**
  - Sync handlers run in optimized thread pools
  - Async handlers run in the event loop
  - Automatic detection - no configuration needed
  - Best performance for any workload type

How It Works
------------

Automatic Handler Detection
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Catzilla automatically detects whether your handler is sync or async:

.. code-block:: python

   from catzilla import Catzilla, JSONResponse, Query
   import asyncio

   app = Catzilla()

   # Sync handler - Catzilla automatically detects this
   @app.get("/sync")
   def sync_handler(request):
       # Runs in optimized thread pool
       # Perfect for CPU-bound operations
       return JSONResponse({"type": "sync", "execution": "thread_pool"})

   # Async handler - Catzilla automatically detects this
   @app.get("/async")
   async def async_handler(request):
       # Runs in event loop
       # Perfect for I/O-bound operations
       await asyncio.sleep(0.1)  # Non-blocking!
       return JSONResponse({"type": "async", "execution": "event_loop"})

   if __name__ == "__main__":
       app.listen(port=8000)

Execution Contexts
~~~~~~~~~~~~~~~~~~

**Sync Handler Execution:**
- Runs in optimized thread pool
- Does not block the main event loop
- Optimal for CPU-intensive tasks
- Compatible with existing synchronous code

**Async Handler Execution:**
- Runs directly in the event loop
- True non-blocking execution
- Optimal for I/O-bound operations
- Supports concurrent operations with ``asyncio.gather()``

Performance Characteristics
~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: text

   Operation Type     | Best Choice | Execution Context | Performance
   -------------------|-------------|-------------------|-------------
   CPU-bound          | Sync        | Thread pool       | Optimal
   I/O-bound          | Async       | Event loop        | Optimal
   Database queries   | Async       | Event loop        | Excellent
   File operations    | Sync/Async  | Both supported    | Excellent
   External APIs      | Async       | Event loop        | Excellent
   Simple CRUD        | Sync        | Thread pool       | Fast
   Complex workflows  | Async       | Event loop        | Scalable

Practical Examples
------------------

CPU-Bound Operations (Use Sync)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Perfect for computational tasks, data processing, and algorithms:

.. code-block:: python

   import time
   import math

   @app.get("/compute-prime")
   def compute_prime(request, n: int = Query(100, ge=2, le=10000, description="Number to check for primality")):
       """CPU-intensive prime calculation - perfect for sync"""

       def is_prime(num):
           if num < 2:
               return False
           for i in range(2, int(math.sqrt(num)) + 1):
               if num % i == 0:
                   return False
           return True

       start_time = time.time()
       primes = [i for i in range(2, n) if is_prime(i)]
       execution_time = time.time() - start_time

       return JSONResponse({
           "primes": primes,
           "count": len(primes),
           "execution_time": f"{execution_time:.3f}s",
           "handler_type": "sync",
           "execution": "thread_pool"
       })

   @app.post("/process-data")
   def process_large_dataset(request):
       """Data processing - sync is optimal"""
       # Parse data from request body
       import json
       body = request.body.decode('utf-8') if request.body else '{}'
       request_data = json.loads(body)
       data = request_data.get('data', [])

       # CPU-intensive data processing
       processed = []
       for item in data:
           # Complex calculations
           result = {
               "id": item.get("id"),
               "processed_value": item.get("value", 0) * 1.5,
               "category": "processed",  # classify_item(item)
               "score": item.get("value", 0) * 2  # calculate_score(item)
           }
           processed.append(result)

       return JSONResponse({
           "processed_items": processed,
           "total": len(processed),
           "handler_type": "sync"
       })

I/O-Bound Operations (Use Async)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Perfect for database queries, API calls, and file operations:

.. code-block:: python

   import asyncio
   import aiohttp

   @app.get("/fetch-user-data")
   async def fetch_user_data(request, user_id: int):
       """Database + API calls - perfect for async"""

       # Simulate concurrent I/O operations
       async def fetch_user_profile():
           await asyncio.sleep(0.1)  # Database query
           return {"id": user_id, "name": f"User {user_id}"}

       async def fetch_user_posts():
           await asyncio.sleep(0.15)  # Another database query
           return [{"id": i, "title": f"Post {i}"} for i in range(3)]

       async def fetch_external_data():
           await asyncio.sleep(0.2)  # External API call
           return {"external_score": 95, "verified": True}

       # Run all I/O operations concurrently!
       start_time = time.time()
       user, posts, external = await asyncio.gather(
           fetch_user_profile(),
           fetch_user_posts(),
           fetch_external_data()
       )
       total_time = time.time() - start_time

       return JSONResponse({
           "user": user,
           "posts": posts,
           "external": external,
           "total_time": f"{total_time:.3f}s",
           "sequential_would_be": "0.45s",
           "performance_gain": f"{((0.45 - total_time) / 0.45 * 100):.1f}%",
           "handler_type": "async",
           "execution": "concurrent"
       })

   @app.post("/send-notifications")
   async def send_notifications(request, notifications: List[dict]):
       """Multiple API calls - async shines here"""

       async def send_single_notification(notification):
           # Simulate sending email, SMS, push notification
           await asyncio.sleep(0.1)
           return {
               "id": notification["id"],
               "status": "sent",
               "type": notification["type"]
           }

       # Send all notifications concurrently
       results = await asyncio.gather(*[
           send_single_notification(notif) for notif in notifications
       ])

       return JSONResponse({
           "sent": len(results),
           "results": results,
           "handler_type": "async",
           "execution": "concurrent"
       })

Mixed Workloads
~~~~~~~~~~~~~~~

When you have both CPU and I/O operations, choose based on the primary workload:

.. code-block:: python

   # Primary I/O with some CPU work - use async
   @app.get("/analyze-user")
   async def analyze_user(request, user_id: int):
       """I/O-heavy with some CPU work - async is better"""

       # I/O operations (primary workload)
       user_data = await fetch_user_from_db(user_id)
       user_activity = await fetch_user_activity(user_id)

       # CPU work (secondary)
       analysis = analyze_activity_patterns(user_activity)
       recommendations = generate_recommendations(user_data, analysis)

       return JSONResponse({
           "user_id": user_id,
           "analysis": analysis,
           "recommendations": recommendations,
           "handler_type": "async"
       })

   # Primary CPU with some I/O - use sync
   @app.post("/process-report")
   def process_report(request, report_data: dict):
       """CPU-heavy with some I/O - sync is better"""

       # CPU work (primary workload)
       processed_data = heavy_data_processing(report_data)
       statistics = calculate_complex_stats(processed_data)

       # I/O work (secondary) - can be done synchronously
       save_report_to_file(processed_data)

       return JSONResponse({
           "statistics": statistics,
           "processed_items": len(processed_data),
           "handler_type": "sync"
       })

Advanced Patterns
-----------------

Concurrent Request Handling
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Demonstrate how async handlers handle concurrent requests:

.. code-block:: python

   @app.get("/concurrent-demo")
   async def concurrent_demo(request):
       """Show concurrent request handling"""

       request_id = request.headers.get("X-Request-ID", "unknown")

       # Simulate different I/O operations
       await asyncio.sleep(0.5)  # Each request sleeps independently

       return JSONResponse({
           "request_id": request_id,
           "message": "This request didn't block others!",
           "handler_type": "async"
       })

   # Test with curl:
   # curl -H "X-Request-ID: 1" http://localhost:8000/concurrent-demo &
   # curl -H "X-Request-ID: 2" http://localhost:8000/concurrent-demo &
   # curl -H "X-Request-ID: 3" http://localhost:8000/concurrent-demo &

Background Task Integration
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Combine sync/async handlers with background tasks:

.. code-block:: python

   from catzilla.background_tasks import schedule_task

   @app.post("/upload-file")
   def upload_file(request, file = File(...)):
       """Sync handler that schedules async background processing"""

       # Sync file handling (fast)
       file_path = save_uploaded_file(file)
       file_info = {
           "filename": file.filename,
           "size": file.size,
           "path": file_path
       }

       # Schedule async background processing
       schedule_task(process_file_async, file_path)

       return JSONResponse({
           "message": "File uploaded successfully",
           "file": file_info,
           "processing": "scheduled in background",
           "handler_type": "sync"
       }, status_code=201)

   async def process_file_async(file_path: str):
       """Background async processing"""
       await asyncio.sleep(2)  # Simulate processing
       # Process file, generate thumbnails, extract metadata, etc.

Error Handling Across Contexts
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Error handling works seamlessly across sync and async handlers:

.. code-block:: python

   from catzilla import JSONResponse, Query

   @app.get("/sync-error-demo")
   def sync_error_demo(request, should_fail: bool = Query(False, description="Whether to trigger an error")):
       """Sync error handling"""
       if should_fail:
           return JSONResponse({"error": "Sync error occurred"}, status_code=400)
       return JSONResponse({"message": "Sync success"})

   @app.get("/async-error-demo")
   async def async_error_demo(request, should_fail: bool = Query(False, description="Whether to trigger an error")):
       """Async error handling"""
       await asyncio.sleep(0.1)
       if should_fail:
           return JSONResponse({"error": "Async error occurred"}, status_code=400)
       return JSONResponse({"message": "Async success"})

Performance Comparison
----------------------

Real-World Performance Test
~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   @app.get("/performance-comparison")
   async def performance_comparison(request):
       """Compare sync vs async performance for different workloads"""

       results = {}

       # Test 1: I/O-bound comparison
       start = time.time()
       # Simulate what sync would do (sequential)
       sync_simulation_time = 0.1 + 0.1 + 0.1  # 0.3s total

       # What async actually does (concurrent)
       start_async = time.time()
       await asyncio.gather(
           asyncio.sleep(0.1),
           asyncio.sleep(0.1),
           asyncio.sleep(0.1)
       )
       async_actual_time = time.time() - start_async

       results["io_bound"] = {
           "sync_would_take": f"{sync_simulation_time:.3f}s",
           "async_actual": f"{async_actual_time:.3f}s",
           "improvement": f"{((sync_simulation_time - async_actual_time) / sync_simulation_time * 100):.1f}%"
       }

       # Test 2: CPU-bound (both would be similar, but sync is simpler)
       cpu_task_time = 0.05  # Both sync and async would take similar time
       results["cpu_bound"] = {
           "sync_optimal": f"{cpu_task_time:.3f}s",
           "async_overhead": f"{cpu_task_time + 0.01:.3f}s",
           "recommendation": "Use sync for CPU-bound tasks"
       }

       return JSONResponse({
           "framework": "Catzilla",
           "feature": "Async/Sync Hybrid",
           "results": results,
           "conclusion": "Use the right tool for the right job!"
       })

Migration Strategies
--------------------

From Sync-Only Code
~~~~~~~~~~~~~~~~~~~

Gradually migrate sync code to take advantage of async where beneficial:

.. code-block:: python

   # Step 1: Start with existing sync code
   @app.get("/user-dashboard")
   def user_dashboard_v1(request, user_id: int):
       """Original sync version"""
       user = get_user_from_db(user_id)  # Blocking DB call
       posts = get_user_posts(user_id)   # Blocking DB call
       stats = get_user_stats(user_id)   # Blocking DB call

       return JSONResponse({
           "user": user,
           "posts": posts,
           "stats": stats,
           "version": "v1_sync"
       })

   # Step 2: Migrate to async for better I/O performance
   @app.get("/user-dashboard-v2")
   async def user_dashboard_v2(request, user_id: int):
       """Improved async version"""
       # Run all DB calls concurrently!
       user, posts, stats = await asyncio.gather(
           get_user_from_db_async(user_id),
           get_user_posts_async(user_id),
           get_user_stats_async(user_id)
       )

       return JSONResponse({
           "user": user,
           "posts": posts,
           "stats": stats,
           "version": "v2_async",
           "performance": "3x faster with concurrent I/O"
       })

From Async-Only Code
~~~~~~~~~~~~~~~~~~~~

Optimize async-only code by using sync where appropriate:

.. code-block:: python

   # Original: Everything forced to be async
   @app.post("/calculate-tax")
   async def calculate_tax_v1(request, income: float):
       """Forced async version (suboptimal)"""
       # This is pure CPU work - doesn't need to be async!
       tax = await asyncio.get_event_loop().run_in_executor(
           None, complex_tax_calculation, income
       )
       return JSONResponse({"tax": tax, "version": "forced_async"})

   # Optimized: Use sync for CPU-bound operations
   @app.post("/calculate-tax-v2")
   def calculate_tax_v2(request, income: float):
       """Optimized sync version"""
       # Pure CPU work - sync is simpler and just as fast
       tax = complex_tax_calculation(income)
       return JSONResponse({
           "tax": tax,
           "version": "optimized_sync",
           "performance": "Simpler and just as fast"
       })

Best Practices
--------------

Choosing Sync vs Async
~~~~~~~~~~~~~~~~~~~~~~

**Use Sync When:**
- CPU-bound operations (calculations, data processing)
- Simple CRUD operations
- File system operations (small files)
- Existing synchronous libraries
- Simpler debugging requirements

**Use Async When:**
- Database queries (multiple concurrent)
- External API calls
- Network operations
- File I/O (large files)
- Background task coordination

Performance Optimization Tips
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

1. **Profile Your Application**

   .. code-block:: python

      @app.get("/profile")
      def profile_endpoint(request):
          start_time = time.time()
          # Your logic here
          end_time = time.time()

          return JSONResponse({
              "execution_time": f"{(end_time - start_time) * 1000:.2f}ms"
          })

2. **Use Concurrent Operations**

   .. code-block:: python

      # Good: Concurrent async operations
      async def good_async_pattern(request):
          data1, data2, data3 = await asyncio.gather(
              fetch_data1(),
              fetch_data2(),
              fetch_data3()
          )
          return combine_data(data1, data2, data3)

      # Bad: Sequential async operations
      async def bad_async_pattern(request):
          data1 = await fetch_data1()
          data2 = await fetch_data2()  # Waits for data1
          data3 = await fetch_data3()  # Waits for data2
          return combine_data(data1, data2, data3)

3. **Monitor Handler Types**

   .. code-block:: python

      @app.get("/handler-stats")
      def handler_stats(request):
          from catzilla.core import get_handler_stats
          return JSONResponse(get_handler_stats())

Common Patterns
~~~~~~~~~~~~~~~

**API Gateway Pattern**

.. code-block:: python

   @app.get("/api-gateway/{service}")
   async def api_gateway(request, service: str):
       """Async is perfect for proxying requests"""
       async with aiohttp.ClientSession() as session:
           async with session.get(f"http://{service}.internal") as response:
               data = await response.json()
       return JSONResponse(data)

**Data Processing Pipeline**

.. code-block:: python

   @app.post("/process-pipeline")
   async def process_pipeline(request, data: List[dict]):
       """Mix async I/O with sync processing"""

       # Async: Fetch additional data
       enriched_data = await enrich_data_async(data)

       # Sync: CPU-intensive processing
       processed_data = process_data_sync(enriched_data)

       # Async: Save results
       await save_results_async(processed_data)

       return JSONResponse({"processed": len(processed_data)})

Debugging and Monitoring
------------------------

Debug Async/Sync Execution
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   import asyncio
   import threading

   @app.get("/debug-execution")
   async def debug_execution(request):
       """Debug information about execution context"""

       return JSONResponse({
           "handler_type": "async",
           "thread_id": threading.get_ident(),
           "event_loop": str(asyncio.get_event_loop()),
           "is_main_thread": threading.current_thread() == threading.main_thread()
       })

   @app.get("/debug-execution-sync")
   def debug_execution_sync(request):
       """Debug information about sync execution"""

       return JSONResponse({
           "handler_type": "sync",
           "thread_id": threading.get_ident(),
           "is_main_thread": threading.current_thread() == threading.main_thread(),
           "execution_context": "thread_pool"
       })

Performance Monitoring
~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   @app.get("/performance-metrics")
   def performance_metrics(request):
       """Monitor performance across handler types"""
       from catzilla.core import get_performance_metrics

       return JSONResponse({
           "metrics": get_performance_metrics(),
           "recommendations": {
               "sync_handlers": "Good for CPU-bound operations",
               "async_handlers": "Good for I/O-bound operations",
               "hybrid_benefit": "Best of both worlds"
           }
       })

Conclusion
----------

Catzilla's async/sync hybrid system gives you:

- ✅ **Automatic Optimization** - No manual configuration needed
- ✅ **Performance** - Always optimal execution context
- ✅ **Simplicity** - Use the pattern that makes sense
- ✅ **Flexibility** - Mix and match as needed
- ✅ **Migration Path** - Easy upgrade from any framework

**The Result: Exceptional performance with code that's easier to write and maintain.**

Next Steps
----------

- :doc:`validation` - Learn about Catzilla's validation system
- :doc:`../features/background-tasks` - Async task processing
- :doc:`../examples/basic-routing` - See hybrid patterns in action
- :doc:`../features/caching` - Performance optimization features
