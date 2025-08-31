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

   from catzilla import Catzilla, JSONResponse, BaseModel, Field, Query
   from typing import List, Optional
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

   from catzilla import Catzilla, JSONResponse, Query
   import time
   import math

   app = Catzilla()

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

   if __name__ == "__main__":
       app.listen(port=8000)

.. code-block:: python

   from catzilla import Catzilla, JSONResponse, BaseModel, Field
   from typing import List, Optional

   app = Catzilla()

   class DataItem(BaseModel):
       """Data item model with validation"""
       id: int = Field(ge=1, description="Item ID")
       value: float = Field(ge=0, description="Item value")
       name: Optional[str] = Field(None, max_length=100, description="Item name")

   class ProcessDataRequest(BaseModel):
       """Request model for data processing"""
       data: List[DataItem] = Field(min_items=1, max_items=1000, description="Data items to process")
       processing_type: str = Field("standard", regex=r'^(standard|advanced|premium)$')

   @app.post("/process-data")
   def process_large_dataset(request, request_data: ProcessDataRequest):
       """Data processing with auto-validation - sync is optimal"""

       # CPU-intensive data processing with validated data
       processed = []
       for item in request_data.data:
           # Complex calculations on validated data
           result = {
               "id": item.id,
               "processed_value": item.value * 1.5,
               "category": "processed",  # classify_item(item)
               "score": item.value * 2,  # calculate_score(item)
               "name": item.name
           }
           processed.append(result)

       return JSONResponse({
           "processed_items": processed,
           "total": len(processed),
           "processing_type": request_data.processing_type,
           "handler_type": "sync",
           "validation": "automatic"
       })

   if __name__ == "__main__":
       app.listen(port=8000)

I/O-Bound Operations (Use Async)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Perfect for database queries, API calls, and file operations:

.. code-block:: python

   from catzilla import Catzilla, JSONResponse, Query
   import asyncio
   import aiohttp
   import time

   app = Catzilla()

   @app.get("/fetch-user-data")
   async def fetch_user_data(request, user_id: int = Query(..., ge=1, description="User ID to fetch data for")):
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

   if __name__ == "__main__":
       app.listen(port=8000)

.. code-block:: python

   from catzilla import Catzilla, JSONResponse, BaseModel, Field, Query
   from typing import List, Optional

   app = Catzilla()

   class NotificationItem(BaseModel):
       """Single notification model"""
       id: int = Field(ge=1, description="Notification ID")
       type: str = Field(regex=r'^(email|sms|push)$', description="Notification type")
       recipient: str = Field(min_length=1, max_length=255, description="Recipient address")
       message: str = Field(min_length=1, max_length=1000, description="Notification message")

   class NotificationRequest(BaseModel):
       """Batch notification request"""
       notifications: List[NotificationItem] = Field(min_items=1, max_items=100, description="Notifications to send")

   @app.post("/send-notifications")
   async def send_notifications(request, notification_request: NotificationRequest):
       """Multiple API calls with validation - async shines here"""

       async def send_single_notification(notification: NotificationItem):
           # Simulate sending email, SMS, push notification
           await asyncio.sleep(0.1)
           return {
               "id": notification.id,
               "status": "sent",
               "type": notification.type,
               "recipient": notification.recipient
           }

       # Send all notifications concurrently
       results = await asyncio.gather(*[
           send_single_notification(notif) for notif in notification_request.notifications
       ])

       return JSONResponse({
           "sent": len(results),
           "results": results,
           "handler_type": "async",
           "execution": "concurrent",
           "validation": "automatic"
       })

   if __name__ == "__main__":
       app.listen(port=8000)

Mixed Workloads
~~~~~~~~~~~~~~~

When you have both CPU and I/O operations, choose based on the primary workload:

.. code-block:: python

   from catzilla import Catzilla, JSONResponse, BaseModel, Field, Query
   from typing import List, Optional
   import asyncio

   app = Catzilla()

   # Primary I/O with some CPU work - use async
   @app.get("/analyze-user")
   async def analyze_user(request, user_id: int = Query(..., ge=1, description="User ID to analyze")):
       """I/O-heavy with some CPU work - async is better"""

       async def fetch_user_from_db(user_id):
           await asyncio.sleep(0.1)
           return {"id": user_id, "name": f"User {user_id}", "created": "2023-01-01"}

       async def fetch_user_activity(user_id):
           await asyncio.sleep(0.15)
           return [{"action": f"action_{i}", "timestamp": f"2023-01-{i:02d}"} for i in range(1, 6)]

       def analyze_activity_patterns(activity):
           # CPU work
           return {"pattern": "active_user", "score": 85}

       def generate_recommendations(user_data, analysis):
           # CPU work
           return ["recommendation_1", "recommendation_2"]

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

   class ReportData(BaseModel):
       """Report data model with validation"""
       title: str = Field(min_length=1, max_length=200, description="Report title")
       data_points: List[dict] = Field(min_items=1, max_items=10000, description="Data points")
       report_type: str = Field(regex=r'^(daily|weekly|monthly|yearly)$', description="Report type")
       filters: Optional[dict] = Field(None, description="Optional filters")

   # Primary CPU with some I/O - use sync
   @app.post("/process-report")
   def process_report(request, report_data: ReportData):
       """CPU-heavy with some I/O - sync is better"""

       def heavy_data_processing(data_points):
           # Simulate heavy CPU processing
           return [{"processed": True, "value": point.get("value", 0) * 2} for point in data_points]

       def calculate_complex_stats(processed_data):
           # Simulate complex statistics calculation
           total = sum(item["value"] for item in processed_data)
           return {"total": total, "average": total / len(processed_data), "count": len(processed_data)}

       def save_report_to_file(report_content):
           # Simulate saving to file (I/O operation)
           import json
           filename = f"report_{report_content['type']}.json"
           # In real app: with open(filename, 'w') as f: json.dump(report_content, f)
           return filename

       # CPU work (primary workload) with validated data
       processed_data = heavy_data_processing(report_data.data_points)
       statistics = calculate_complex_stats(processed_data)

       # I/O work (secondary) - can be done synchronously
       filename = save_report_to_file({
           "title": report_data.title,
           "type": report_data.report_type,
           "data": processed_data,
           "stats": statistics
       })

       return JSONResponse({
           "statistics": statistics,
           "processed_items": len(processed_data),
           "report_title": report_data.title,
           "report_type": report_data.report_type,
           "saved_to": filename,
           "handler_type": "sync",
           "validation": "automatic"
       })

   if __name__ == "__main__":
       app.listen(port=8000)

Advanced Patterns
-----------------

Concurrent Request Handling
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Demonstrate how async handlers handle concurrent requests:

.. code-block:: python

   from catzilla import Catzilla, JSONResponse, Header
   import asyncio

   app = Catzilla()

   @app.get("/concurrent-demo")
   async def concurrent_demo(request, request_id: str = Header("unknown", alias="X-Request-ID", description="Request ID for tracking")):
       """Show concurrent request handling"""

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

   if __name__ == "__main__":
       app.listen(port=8000)

Background Task Integration
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Combine sync/async handlers with background tasks:

.. code-block:: python

   from catzilla import Catzilla, JSONResponse, UploadFile, File
   import asyncio

   app = Catzilla()

   # Enable background task system
   app.enable_background_tasks(workers=4)

   def process_file_async(task_id: str, file_path: str):
       """Background async processing"""
       import time
       # Simulate processing - thumbnails, metadata extraction, etc.
       time.sleep(2)
       print(f"✅ File processed: {file_path}")

   @app.post("/upload-file")
   def upload_file(request, file: UploadFile = File(max_size="50MB")):
       """Sync handler that schedules async background processing"""

       # Sync file handling (fast) - using real Catzilla API
       file_path = file.save_to("uploads/", stream=True)
       file_info = {
           "filename": file.filename,
           "size": file.size,
           "content_type": file.content_type,
           "path": file_path
       }

       # Schedule async background processing using real Catzilla API
       task_id = f"process_{file.filename}_{int(time.time())}"
       app.add_task(process_file_async, task_id, file_path)

       return JSONResponse({
           "message": "File uploaded successfully",
           "file": file_info,
           "task_id": task_id,
           "processing": "scheduled in background",
           "handler_type": "sync"
       }, status_code=201)

   if __name__ == "__main__":
       app.listen(port=8000)

Error Handling Across Contexts
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Error handling works seamlessly across sync and async handlers:

.. code-block:: python

   from catzilla import Catzilla, JSONResponse, Query

   app = Catzilla()

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

   if __name__ == "__main__":
       app.listen(port=8000)

Performance Comparison
----------------------

Real-World Performance Test
~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from catzilla import Catzilla, JSONResponse
   import asyncio
   import time

   app = Catzilla()

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

   if __name__ == "__main__":
       app.listen(port=8000)

Migration Strategies
--------------------

From Sync-Only Code
~~~~~~~~~~~~~~~~~~~

Gradually migrate sync code to take advantage of async where beneficial:

.. code-block:: python

   from catzilla import Catzilla, JSONResponse, Query

   app = Catzilla()

   # Step 1: Start with existing sync code
   @app.get("/user-dashboard")
   def user_dashboard_v1(request, user_id: int = Query(..., ge=1, description="User ID")):
       """Original sync version"""

       def get_user_from_db(user_id):
           # Simulate blocking DB call
           import time
           time.sleep(0.1)
           return {"id": user_id, "name": f"User {user_id}"}

       def get_user_posts(user_id):
           # Simulate blocking DB call
           import time
           time.sleep(0.1)
           return [{"id": i, "title": f"Post {i}"} for i in range(3)]

       def get_user_stats(user_id):
           # Simulate blocking DB call
           import time
           time.sleep(0.1)
           return {"posts": 3, "followers": 100}

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
   async def user_dashboard_v2(request, user_id: int = Query(..., ge=1, description="User ID")):
       """Improved async version"""

       async def get_user_from_db_async(user_id):
           # Simulate async DB call
           await asyncio.sleep(0.1)
           return {"id": user_id, "name": f"User {user_id}"}

       async def get_user_posts_async(user_id):
           # Simulate async DB call
           await asyncio.sleep(0.1)
           return [{"id": i, "title": f"Post {i}"} for i in range(3)]

       async def get_user_stats_async(user_id):
           # Simulate async DB call
           await asyncio.sleep(0.1)
           return {"posts": 3, "followers": 100}

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

   if __name__ == "__main__":
       app.listen(port=8000)

From Async-Only Code
~~~~~~~~~~~~~~~~~~~~

Optimize async-only code by using sync where appropriate:

.. code-block:: python

   from catzilla import Catzilla, JSONResponse
   import asyncio

   app = Catzilla()

   # Original: Everything forced to be async
   @app.post("/calculate-tax")
   async def calculate_tax_v1(request, income: float = Query(..., ge=0, description="Annual income")):
       """Forced async version (suboptimal)"""

       def complex_tax_calculation(income):
           # Simulate complex CPU calculations
           tax_rate = 0.25 if income > 50000 else 0.15
           return income * tax_rate

       # This is pure CPU work - doesn't need to be async!
       tax = await asyncio.get_event_loop().run_in_executor(
           None, complex_tax_calculation, income
       )
       return JSONResponse({"tax": tax, "version": "forced_async"})

   # Optimized: Use sync for CPU-bound operations
   @app.post("/calculate-tax-v2")
   def calculate_tax_v2(request, income: float = Query(..., ge=0, description="Annual income")):
       """Optimized sync version"""

       def complex_tax_calculation(income):
           # Simulate complex CPU calculations
           tax_rate = 0.25 if income > 50000 else 0.15
           return income * tax_rate

       # Pure CPU work - sync is simpler and just as fast
       tax = complex_tax_calculation(income)
       return JSONResponse({
           "tax": tax,
           "version": "optimized_sync",
           "performance": "Simpler and just as fast"
       })

   if __name__ == "__main__":
       app.listen(port=8000)

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

      from catzilla import Catzilla, JSONResponse
      import time

      app = Catzilla()

      @app.get("/profile")
      def profile_endpoint(request):
          start_time = time.time()
          # Your logic here
          time.sleep(0.1)  # Simulate some work
          end_time = time.time()

          return JSONResponse({
              "execution_time": f"{(end_time - start_time) * 1000:.2f}ms"
          })

      if __name__ == "__main__":
          app.listen(port=8000)

2. **Use Concurrent Operations**

   .. code-block:: python

      from catzilla import Catzilla, JSONResponse
      import asyncio

      app = Catzilla()

      # Good: Concurrent async operations
      async def good_async_pattern(request):
          async def fetch_data1():
              await asyncio.sleep(0.1)
              return {"data": "from_service_1"}

          async def fetch_data2():
              await asyncio.sleep(0.1)
              return {"data": "from_service_2"}

          async def fetch_data3():
              await asyncio.sleep(0.1)
              return {"data": "from_service_3"}

          def combine_data(data1, data2, data3):
              return {"combined": [data1, data2, data3]}

          data1, data2, data3 = await asyncio.gather(
              fetch_data1(),
              fetch_data2(),
              fetch_data3()
          )
          return combine_data(data1, data2, data3)

      # Bad: Sequential async operations
      async def bad_async_pattern(request):
          async def fetch_data1():
              await asyncio.sleep(0.1)
              return {"data": "from_service_1"}

          async def fetch_data2():
              await asyncio.sleep(0.1)
              return {"data": "from_service_2"}

          async def fetch_data3():
              await asyncio.sleep(0.1)
              return {"data": "from_service_3"}

          def combine_data(data1, data2, data3):
              return {"combined": [data1, data2, data3]}

          data1 = await fetch_data1()
          data2 = await fetch_data2()  # Waits for data1
          data3 = await fetch_data3()  # Waits for data2
          return combine_data(data1, data2, data3)

      @app.get("/good-pattern")
      async def good_pattern_endpoint(request):
          result = await good_async_pattern(request)
          return JSONResponse(result)

      @app.get("/bad-pattern")
      async def bad_pattern_endpoint(request):
          result = await bad_async_pattern(request)
          return JSONResponse(result)

      if __name__ == "__main__":
          app.listen(port=8000)

3. **Monitor Handler Types**

   .. code-block:: python

      from catzilla import Catzilla, JSONResponse

      app = Catzilla()

      @app.get("/handler-stats")
      def handler_stats(request):
          # Note: get_handler_stats is a conceptual function
          # In real implementation, you'd track this in your app
          stats = {
              "total_handlers": 10,
              "sync_handlers": 6,
              "async_handlers": 4,
              "performance": "Optimal hybrid usage"
          }
          return JSONResponse(stats)

      if __name__ == "__main__":
          app.listen(port=8000)

Common Patterns
~~~~~~~~~~~~~~~

**API Gateway Pattern**

.. code-block:: python

   from catzilla import Catzilla, JSONResponse
   import aiohttp
   import asyncio

   app = Catzilla()

   @app.get("/api-gateway/{service}")
   async def api_gateway(request, service: str):
       """Async is perfect for proxying requests"""
       try:
           async with aiohttp.ClientSession() as session:
               async with session.get(f"http://{service}.internal") as response:
                   data = await response.json()
       except Exception as e:
           return JSONResponse({"error": str(e)}, status_code=500)

       return JSONResponse(data)

   if __name__ == "__main__":
       app.listen(port=8000)

**Data Processing Pipeline**

.. code-block:: python

   from catzilla import Catzilla, JSONResponse, BaseModel, Field
   from typing import List
   import asyncio

   app = Catzilla()

   @app.post("/process-pipeline")
   async def process_pipeline(request, data: List[dict]):
       """Mix async I/O with sync processing"""

       async def enrich_data_async(data):
           # Simulate async data enrichment (I/O bound)
           await asyncio.sleep(0.1)
           return [{"enriched": True, **item} for item in data]

       def process_data_sync(enriched_data):
           # CPU-intensive processing (sync)
           return [{"processed": True, "value": item.get("value", 0) * 2} for item in enriched_data]

       async def save_results_async(processed_data):
           # Simulate async save operation (I/O bound)
           await asyncio.sleep(0.1)
           return {"saved": len(processed_data)}

       # Async: Fetch additional data
       enriched_data = await enrich_data_async(data)

       # Sync: CPU-intensive processing
       processed_data = process_data_sync(enriched_data)

       # Async: Save results
       save_result = await save_results_async(processed_data)

       return JSONResponse({
           "processed": len(processed_data),
           "save_result": save_result
       })

   if __name__ == "__main__":
       app.listen(port=8000)

Debugging and Monitoring
------------------------

Debug Async/Sync Execution
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from catzilla import Catzilla, JSONResponse
   import asyncio
   import threading

   app = Catzilla()

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

   if __name__ == "__main__":
       app.listen(port=8000)

Performance Monitoring
~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from catzilla import Catzilla, JSONResponse

   app = Catzilla()

   @app.get("/performance-metrics")
   def performance_metrics(request):
       """Monitor performance across handler types"""
       # Note: get_performance_metrics is a conceptual function
       # In real implementation, you'd implement your own metrics collection
       metrics = {
           "total_requests": 1000,
           "avg_response_time": "25ms",
           "sync_handlers_performance": "Excellent for CPU tasks",
           "async_handlers_performance": "Excellent for I/O tasks"
       }

       return JSONResponse({
           "metrics": metrics,
           "recommendations": {
               "sync_handlers": "Good for CPU-bound operations",
               "async_handlers": "Good for I/O-bound operations",
               "hybrid_benefit": "Best of both worlds"
           }
       })

   if __name__ == "__main__":
       app.listen(port=8000)

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
