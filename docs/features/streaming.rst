Streaming
=========

Catzilla provides advanced streaming capabilities for real-time communication, including Server-Sent Events (SSE), chunked responses, and efficient connection management for high-performance streaming applications.

Overview
--------

Catzilla's streaming system provides:

- **Server-Sent Events (SSE)** - Real-time data streaming to browsers
- **Chunked Transfer Encoding** - Efficient streaming of large responses
- **Connection Management** - Active connection tracking and cleanup
- **Real-Time Communication** - Live data feeds and notifications
- **Memory Efficient** - Stream large datasets without memory overflow
- **Auto-Reconnection** - Client-side reconnection support

Quick Start
-----------

Basic Server-Sent Events
~~~~~~~~~~~~~~~~~~~~~~~~~

Create a simple SSE endpoint:

.. code-block:: python

   from catzilla import Catzilla, Request, Response, StreamingResponse
   import json
   import time

   app = Catzilla()

   @app.get("/events")
   def sse_endpoint(request: Request) -> Response:
       """Stream server-sent events for real-time updates"""
       def generate_sse():
           for i in range(20):
               # Format according to SSE specification
               yield f"id: {i}\n"
               yield f"data: {{'count': {i}, 'timestamp': {time.time()}}}\n\n"
               time.sleep(0.5)  # Add a delay to simulate real-time updates

       return StreamingResponse(
           generate_sse(),
           content_type="text/event-stream"
       )

   @app.get("/")
   def home(request: Request) -> Response:
       return JSONResponse({"message": "Hello with streaming!"})

   if __name__ == "__main__":
       print("🚀 Starting Catzilla streaming example...")
       print("Try: curl -N http://localhost:8000/events")
       app.listen(port=8000)

Real-Time Data Streaming
~~~~~~~~~~~~~~~~~~~~~~~~

Stream live data updates:

.. code-block:: python

   from catzilla import Catzilla, Request, Response, StreamingResponse
   import json
   import time
   from datetime import datetime

   app = Catzilla()

   def generate_realtime_data():
       """Generate real-time data stream"""
       count = 0
       for i in range(10):
           count += 1
           data = {
               "timestamp": datetime.now().isoformat(),
               "count": count,
               "value": count * 1.5,
               "status": "active"
           }

           # Format as simple JSON lines
           yield f"{json.dumps(data)}\n"
           time.sleep(1)

       # Final message
       yield f'{{"status": "completed", "total_items": {count}}}\n'

   @app.get("/stream/realtime")
   def stream_realtime_data(request: Request) -> Response:
       """Stream real-time data"""
       return StreamingResponse(
           generate_realtime_data(),
           content_type="text/plain",
           headers={
               "Cache-Control": "no-cache",
               "Connection": "keep-alive"
           }
       )

   if __name__ == "__main__":
       print("🚀 Starting real-time streaming example...")
       print("Try: curl -N http://localhost:8000/stream/realtime")
       app.listen(port=8000)

Advanced Streaming Patterns
----------------------------

Chunked File Streaming
~~~~~~~~~~~~~~~~~~~~~~~

Stream large files efficiently:

.. code-block:: python

   from catzilla import Catzilla, Request, Response, StreamingResponse, JSONResponse
   import os
   from pathlib import Path

   app = Catzilla()

   def file_streamer(file_path, chunk_size=8192):
       """Stream file in chunks"""
       with open(file_path, "rb") as file:
           while True:
               chunk = file.read(chunk_size)
               if not chunk:
                   break
               yield chunk

   @app.get("/download/{filename}")
   def stream_file_download(request: Request) -> Response:
       """Stream large file download"""
       filename = request.path_params["filename"]
       file_path = Path("uploads") / filename

       if not file_path.exists():
           return JSONResponse({"error": "File not found"}, status_code=404)

       # Get file size for Content-Length header
       file_size = file_path.stat().st_size

       return StreamingResponse(
           file_streamer(file_path),
           content_type="application/octet-stream",
           headers={
               "Content-Disposition": f"attachment; filename={filename}",
               "Content-Length": str(file_size)
           }
       )

   if __name__ == "__main__":
       # Create uploads directory if it doesn't exist
       Path("uploads").mkdir(exist_ok=True)
       print("🚀 Starting file streaming server...")
       print("Try: curl http://localhost:8000/download/sample.txt")
       app.listen(port=8000)

Data Processing Pipeline
~~~~~~~~~~~~~~~~~~~~~~~~

Stream processed data in real-time:

.. code-block:: python

   from catzilla import Catzilla, Request, Response, StreamingResponse
   import json
   import time
   from datetime import datetime

   app = Catzilla()

   def process_and_stream():
       """Process data and stream results"""
       # Simulate large dataset processing
       total_items = 100

       for i in range(total_items):
           # Simulate data processing
           processed_item = {
               "item_id": i,
               "processed_at": datetime.now().isoformat(),
               "result": f"Processed item {i}",
               "progress": round((i + 1) / total_items * 100, 2)
           }

           # Stream each processed item as JSON lines
           yield f"{json.dumps(processed_item)}\n"

           # Simulate processing time
           time.sleep(0.01)

       # Send completion notification
       completion = {
           "event": "completed",
           "total_processed": total_items,
           "completed_at": datetime.now().isoformat()
       }

       yield f"{json.dumps(completion)}\n"

   @app.post("/process-stream")
   def stream_data_processing(request: Request) -> Response:
       """Stream data processing results"""
       return StreamingResponse(
           process_and_stream(),
           content_type="application/x-ndjson",
           headers={
               "Cache-Control": "no-cache",
               "Connection": "keep-alive"
           }
       )

   if __name__ == "__main__":
       print("🚀 Starting data processing streaming server...")
       print("Try: curl -X POST http://localhost:8000/process-stream")
       app.listen(port=8000)

Connection Management
---------------------

Simple Connection Tracking
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Track streaming connections with basic monitoring:

.. code-block:: python

   from catzilla import Catzilla, Request, Response, StreamingResponse
   import json
   import time
   from datetime import datetime
   from collections import defaultdict

   app = Catzilla()

   # Simple connection tracking
   active_connections = defaultdict(dict)
   connection_count = 0

   def generate_connection_status():
       """Generate connection status updates"""
       global connection_count

       for i in range(10):
           status = {
               "timestamp": datetime.now().isoformat(),
               "active_connections": len(active_connections),
               "total_connections": connection_count,
               "update_number": i + 1
           }

           yield f"data: {json.dumps(status)}\n\n"
           time.sleep(2)

   @app.get("/stream/status")
   def stream_connection_status(request: Request) -> Response:
       """Stream connection status updates"""
       global connection_count

       # Track this connection
       connection_id = f"conn_{connection_count}"
       connection_count += 1
       active_connections[connection_id] = {
           "connected_at": datetime.now(),
           "client_ip": request.client.host if hasattr(request, 'client') else "unknown"
       }

       print(f"➕ New connection: {connection_id}")

       try:
           response = StreamingResponse(
               generate_connection_status(),
               content_type="text/event-stream",
               headers={
                   "Cache-Control": "no-cache",
                   "Connection": "keep-alive",
                   "X-Connection-ID": connection_id
               }
           )
           return response
       finally:
           # Note: In real implementation, cleanup would happen on disconnect
           pass

   if __name__ == "__main__":
       print("🚀 Starting connection tracking server...")
       print("Try: curl -N http://localhost:8000/stream/status")
       app.listen(port=8000)

Broadcasting Example
~~~~~~~~~~~~~~~~~~~~

Simple message broadcasting:

.. code-block:: python

   from catzilla import Catzilla, Request, Response, StreamingResponse
   import json
   import time
   from datetime import datetime
   from threading import Thread, Lock
   import queue

   app = Catzilla()

   # Simple broadcasting system
   message_queues = {}
   queues_lock = Lock()

   def broadcast_message(message):
       """Broadcast message to all connected clients"""
       with queues_lock:
           for connection_id, msg_queue in message_queues.items():
               try:
                   msg_queue.put_nowait(message)
               except queue.Full:
                   print(f"Queue full for connection {connection_id}")

   def periodic_broadcaster():
       """Send periodic broadcast messages"""
       counter = 0
       while True:
           message = {
               "type": "broadcast",
               "id": counter,
               "timestamp": datetime.now().isoformat(),
               "message": f"Broadcast message {counter}"
           }
           broadcast_message(message)
           counter += 1
           time.sleep(5)

   # Start background broadcaster
   Thread(target=periodic_broadcaster, daemon=True).start()

   def stream_broadcasts(connection_id):
       """Stream broadcast messages for a connection"""
       msg_queue = queue.Queue(maxsize=100)

       with queues_lock:
           message_queues[connection_id] = msg_queue

       try:
           while True:
               try:
                   # Get message with timeout
                   message = msg_queue.get(timeout=1.0)
                   yield f"data: {json.dumps(message)}\n\n"
               except queue.Empty:
                   # Send heartbeat
                   heartbeat = {"type": "heartbeat", "timestamp": datetime.now().isoformat()}
                   yield f"data: {json.dumps(heartbeat)}\n\n"
       finally:
           with queues_lock:
               message_queues.pop(connection_id, None)

   @app.get("/broadcast-stream")
   def join_broadcast_stream(request: Request) -> Response:
       """Join broadcast stream"""
       import uuid
       connection_id = str(uuid.uuid4())

       print(f"➕ New broadcast subscriber: {connection_id}")

       return StreamingResponse(
           stream_broadcasts(connection_id),
           content_type="text/event-stream",
           headers={
               "Cache-Control": "no-cache",
               "Connection": "keep-alive",
               "X-Connection-ID": connection_id
           }
       )

   @app.post("/broadcast")
   def send_broadcast(request: Request) -> Response:
       """Send message to all connected clients"""
       # Get message from request body (simplified for example)
       message = {
           "type": "manual_broadcast",
           "message": "Hello from server!",
           "timestamp": datetime.now().isoformat()
       }

       # Broadcast to all connected clients
       broadcast_message(message)

       return Response(
           json.dumps({
               "status": "broadcast_sent",
               "message": message,
               "recipients": len(message_queues)
           }),
           content_type="application/json"
       )

   if __name__ == "__main__":
       print("🚀 Starting broadcasting server...")
       print("Try: curl -N http://localhost:8000/broadcast-stream")
       print("Send: curl -X POST http://localhost:8000/broadcast")
       app.listen(port=8000)

Real-Time Applications
----------------------

Simple Chat System
~~~~~~~~~~~~~~~~~~

Build a basic chat with streaming:

.. code-block:: python

   from catzilla import Catzilla, Request, Response, StreamingResponse
   import json
   import time
   from datetime import datetime
   from threading import Lock
   import queue

   app = Catzilla()

   # Simple chat room
   chat_clients = {}
   chat_lock = Lock()
   message_history = []

   def add_chat_client(client_id, client_name):
       """Add client to chat room"""
       client_queue = queue.Queue(maxsize=100)

       with chat_lock:
           chat_clients[client_id] = {
               "name": client_name,
               "queue": client_queue,
               "joined_at": datetime.now()
           }

       # Send join notification
       join_message = {
           "type": "user_joined",
           "user": client_name,
           "timestamp": datetime.now().isoformat(),
           "clients_count": len(chat_clients)
       }
       broadcast_chat_message(join_message)
       return client_queue

   def remove_chat_client(client_id):
       """Remove client from chat room"""
       with chat_lock:
           client = chat_clients.pop(client_id, None)

       if client:
           leave_message = {
               "type": "user_left",
               "user": client["name"],
               "timestamp": datetime.now().isoformat(),
               "clients_count": len(chat_clients)
           }
           broadcast_chat_message(leave_message)

   def broadcast_chat_message(message):
       """Broadcast message to all chat clients"""
       message_history.append(message)

       # Keep only last 50 messages
       if len(message_history) > 50:
           message_history[:] = message_history[-50:]

       with chat_lock:
           for client_id, client in chat_clients.items():
               try:
                   client["queue"].put_nowait(message)
               except queue.Full:
                   print(f"Message queue full for client {client_id}")

   def stream_chat_messages(client_id, client_name):
       """Stream chat messages for a client"""
       client_queue = add_chat_client(client_id, client_name)

       try:
           # Send recent message history
           for msg in message_history[-10:]:  # Last 10 messages
               yield f"data: {json.dumps(msg)}\n\n"

           # Stream new messages
           while True:
               try:
                   message = client_queue.get(timeout=1.0)
                   yield f"data: {json.dumps(message)}\n\n"
               except queue.Empty:
                   # Send heartbeat
                   heartbeat = {"type": "heartbeat", "timestamp": datetime.now().isoformat()}
                   yield f"data: {json.dumps(heartbeat)}\n\n"
       finally:
           remove_chat_client(client_id)

   @app.get("/chat/stream")
   def join_chat_stream(request: Request) -> Response:
       """Join chat stream"""
       import uuid
       client_id = str(uuid.uuid4())
       client_name = request.query_params.get("name", f"User_{client_id[:8]}")

       print(f"🎯 Chat client joined: {client_name} ({client_id})")

       return StreamingResponse(
           stream_chat_messages(client_id, client_name),
           content_type="text/event-stream",
           headers={
               "Cache-Control": "no-cache",
               "Connection": "keep-alive"
           }
       )

   @app.post("/chat/send")
   def send_chat_message(request: Request) -> Response:
       """Send message to chat room"""
       # Simple message sending (in real app, would parse JSON from body)
       sender = request.query_params.get("sender", "Anonymous")
       message_text = request.query_params.get("message", "Hello!")

       chat_message = {
           "type": "chat_message",
           "sender": sender,
           "message": message_text,
           "timestamp": datetime.now().isoformat()
       }

       broadcast_chat_message(chat_message)

       return Response(
           json.dumps({"status": "message_sent", "message": chat_message}),
           content_type="application/json"
       )

   if __name__ == "__main__":
       print("🚀 Starting chat server...")
       print("Join chat: curl -N 'http://localhost:8000/chat/stream?name=Alice'")
       print("Send message: curl -X POST 'http://localhost:8000/chat/send?sender=Alice&message=Hello'")
       app.listen(port=8000)

Live Analytics Dashboard
~~~~~~~~~~~~~~~~~~~~~~~~

Stream analytics data for dashboards:

.. code-block:: python

   from catzilla import Catzilla, Request, Response, StreamingResponse
   import json
   import time
   import random
   import queue
   from datetime import datetime
   from threading import Thread, Lock

   app = Catzilla()

   # Simple analytics data
   analytics_data = {
       "page_views": 0,
       "unique_visitors": set(),
       "api_calls": 0,
       "errors": 0
   }
   analytics_lock = Lock()
   analytics_subscribers = {}

   def track_page_view(visitor_id):
       """Track page view"""
       with analytics_lock:
           analytics_data["page_views"] += 1
           analytics_data["unique_visitors"].add(visitor_id)
       broadcast_analytics_update()

   def track_api_call():
       """Track API call"""
       with analytics_lock:
           analytics_data["api_calls"] += 1
       broadcast_analytics_update()

   def track_error():
       """Track error"""
       with analytics_lock:
           analytics_data["errors"] += 1
       broadcast_analytics_update()

   def broadcast_analytics_update():
       """Broadcast analytics update"""
       with analytics_lock:
           update = {
               "page_views": analytics_data["page_views"],
               "unique_visitors": len(analytics_data["unique_visitors"]),
               "api_calls": analytics_data["api_calls"],
               "errors": analytics_data["errors"],
               "timestamp": datetime.now().isoformat()
           }

       for subscriber_id, queue in analytics_subscribers.items():
           try:
               queue.put_nowait(update)
           except queue.Full:
               print(f"Analytics queue full for subscriber {subscriber_id}")

   def simulate_analytics_data():
       """Simulate incoming analytics data"""
       import uuid
       counter = 0
       while True:
           counter += 1

           # Simulate random events
           if counter % 3 == 0:
               track_page_view(str(uuid.uuid4()))
           if counter % 2 == 0:
               track_api_call()
           if counter % 10 == 0:
               track_error()

           time.sleep(2)

   # Start analytics simulation
   Thread(target=simulate_analytics_data, daemon=True).start()

   def stream_analytics_updates(subscriber_id):
       """Stream analytics updates"""
       subscriber_queue = queue.Queue(maxsize=50)
       analytics_subscribers[subscriber_id] = subscriber_queue

       try:
           # Send current state first
           current_state = {
               "page_views": analytics_data["page_views"],
               "unique_visitors": len(analytics_data["unique_visitors"]),
               "api_calls": analytics_data["api_calls"],
               "errors": analytics_data["errors"],
               "timestamp": datetime.now().isoformat()
           }
           yield f"data: {json.dumps(current_state)}\n\n"

           # Stream updates
           while True:
               try:
                   update = subscriber_queue.get(timeout=5.0)
                   yield f"data: {json.dumps(update)}\n\n"
               except queue.Empty:
                   # Send heartbeat
                   heartbeat = {"type": "heartbeat", "timestamp": datetime.now().isoformat()}
                   yield f"data: {json.dumps(heartbeat)}\n\n"
       finally:
           analytics_subscribers.pop(subscriber_id, None)

   @app.get("/analytics-stream")
   def analytics_dashboard_stream(request: Request) -> Response:
       """Stream analytics for dashboard"""
       import uuid
       subscriber_id = str(uuid.uuid4())

       print(f"📊 Analytics subscriber connected: {subscriber_id}")

       return StreamingResponse(
           stream_analytics_updates(subscriber_id),
           content_type="text/event-stream",
           headers={
               "Cache-Control": "no-cache",
               "Connection": "keep-alive"
           }
       )

   if __name__ == "__main__":
       print("🚀 Starting analytics dashboard server...")
       print("Try: curl -N http://localhost:8000/analytics-stream")
       app.listen(port=8000)

Performance Optimization
------------------------

Memory Efficient Streaming
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Stream large datasets without memory issues:

.. code-block:: python

   from catzilla import Catzilla, Request, Response, StreamingResponse
   import json
   import time
   from datetime import datetime

   app = Catzilla()

   def efficient_data_stream():
       """Generate large dataset efficiently"""
       batch_size = 100
       total_records = 10000  # Smaller for demo

       for batch_start in range(0, total_records, batch_size):
           # Generate batch of records
           batch = []
           for i in range(batch_start, min(batch_start + batch_size, total_records)):
               record = {
                   "id": i,
                   "data": f"Record {i}",
                   "timestamp": datetime.now().isoformat()
               }
               batch.append(record)

           # Stream batch as single chunk
           chunk = {
               "batch": batch,
               "batch_start": batch_start,
               "batch_size": len(batch),
               "total_records": total_records,
               "progress": round((batch_start + len(batch)) / total_records * 100, 2)
           }

           yield f"{json.dumps(chunk)}\n"

           # Small delay to prevent overwhelming the client
           time.sleep(0.01)

   @app.get("/large-dataset")
   def stream_large_dataset(request: Request) -> Response:
       """Stream large dataset efficiently"""
       return StreamingResponse(
           efficient_data_stream(),
           content_type="application/x-ndjson",
           headers={
               "Cache-Control": "no-cache",
               "Transfer-Encoding": "chunked"
           }
       )

   if __name__ == "__main__":
       print("🚀 Starting large dataset streaming server...")
       print("Try: curl -N http://localhost:8000/large-dataset")
       app.listen(port=8000)

Connection Health Monitoring
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Monitor connection health with heartbeats:

.. code-block:: python

   from catzilla import Catzilla, Request, Response, StreamingResponse
   import json
   import time
   from datetime import datetime

   app = Catzilla()

   def monitored_stream():
       """Stream with health checks"""
       last_ping = time.time()
       ping_interval = 10  # Ping every 10 seconds

       counter = 0
       while True:
           current_time = time.time()

           # Send ping if needed
           if current_time - last_ping >= ping_interval:
               ping_message = {
                   "type": "ping",
                   "timestamp": datetime.now().isoformat(),
                   "server_time": current_time
               }
               yield f"event: ping\n"
               yield f"data: {json.dumps(ping_message)}\n\n"
               last_ping = current_time

           # Send regular data
           data_message = {
               "type": "data",
               "counter": counter,
               "timestamp": datetime.now().isoformat(),
               "status": "healthy"
           }

           yield f"data: {json.dumps(data_message)}\n\n"
           counter += 1
           time.sleep(1)

   @app.get("/health-monitored-stream")
   def health_monitored_stream(request: Request) -> Response:
       """Stream with connection health monitoring"""
       return StreamingResponse(
           monitored_stream(),
           content_type="text/event-stream",
           headers={
               "Cache-Control": "no-cache",
               "Connection": "keep-alive",
               "X-Accel-Buffering": "no"  # Disable nginx buffering
           }
       )

   if __name__ == "__main__":
       print("🚀 Starting health monitored streaming server...")
       print("Try: curl -N http://localhost:8000/health-monitored-stream")
       app.listen(port=8000)

Best Practices
--------------

Client-Side JavaScript
~~~~~~~~~~~~~~~~~~~~~~

Example client-side code for consuming streams:

.. code-block:: javascript

   // Basic SSE client
   const eventSource = new EventSource('/events');

   eventSource.onmessage = function(event) {
       const data = JSON.parse(event.data);
       console.log('Received:', data);
   };

   eventSource.onerror = function(event) {
       console.error('SSE error:', event);
   };

   // Auto-reconnection wrapper
   function createReconnectingEventSource(url, options = {}) {
       let eventSource;
       let reconnectInterval = options.reconnectInterval || 3000;

       function connect() {
           eventSource = new EventSource(url);

           eventSource.onopen = function() {
               console.log('Connected to stream');
           };

           eventSource.onmessage = function(event) {
               if (options.onMessage) {
                   options.onMessage(JSON.parse(event.data));
               }
           };

           eventSource.onerror = function() {
               console.log('Connection lost, reconnecting...');
               eventSource.close();
               setTimeout(connect, reconnectInterval);
           };
       }

       connect();
       return eventSource;
   }

Performance Guidelines
~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # ✅ Good: Use generator functions for streaming
   def good_stream():
       for i in range(1000):
           yield f"data: {i}\n"
           time.sleep(0.1)  # Control flow rate

   # ❌ Avoid: Creating all data in memory
   def bad_stream():
       all_data = [f"data: {i}\n" for i in range(1000)]  # Memory intensive
       for item in all_data:
           yield item

   # ✅ Good: Use appropriate chunk sizes
   chunk_size = 8192  # 8KB chunks for files
   batch_size = 100   # 100 records for data

   # ✅ Good: Add delays to prevent overwhelming clients
   def controlled_stream():
       for i in range(100):
           yield f"data: {i}\n"
           time.sleep(0.01)  # Small delay

   # ✅ Good: Use proper content types
   # For SSE: content_type="text/event-stream"
   # For JSON Lines: content_type="application/x-ndjson"
   # For binary: content_type="application/octet-stream"

This streaming system enables real-time communication and efficient data transfer for modern web applications that require live updates and interactive features.
