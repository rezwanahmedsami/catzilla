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

   from catzilla import Catzilla, Request, StreamingResponse
   import asyncio
   import json
   import time

   app = Catzilla()

   @app.get("/events")
   async def stream_events(request: Request):
       """Basic SSE endpoint"""

       async def event_generator():
           """Generate server-sent events"""
           counter = 0
           while True:
               # Check if client disconnected
               if await request.is_disconnected():
                   break

               # Create event data
               data = {
                   "id": counter,
                   "message": f"Event {counter}",
                   "timestamp": time.time()
               }

               # Format as SSE
               yield f"data: {json.dumps(data)}\n\n"

               counter += 1
               await asyncio.sleep(1)  # Send event every second

       return StreamingResponse(
           event_generator(),
           media_type="text/event-stream",
           headers={
               "Cache-Control": "no-cache",
               "Connection": "keep-alive",
               "Access-Control-Allow-Origin": "*"
           }
       )

Real-Time Data Streaming
~~~~~~~~~~~~~~~~~~~~~~~~

Stream live data updates:

.. code-block:: python

   import random
   from datetime import datetime

   @app.get("/live-metrics")
   async def stream_live_metrics(request: Request):
       """Stream live system metrics"""

       async def metrics_generator():
           """Generate live system metrics"""
           while True:
               if await request.is_disconnected():
                   print("Client disconnected from metrics stream")
                   break

               # Simulate real-time metrics
               metrics = {
                   "cpu_usage": round(random.uniform(10, 90), 2),
                   "memory_usage": round(random.uniform(30, 85), 2),
                   "active_connections": random.randint(50, 200),
                   "requests_per_second": random.randint(100, 500),
                   "timestamp": datetime.now().isoformat()
               }

               # Send as SSE with event type
               yield f"event: metrics\n"
               yield f"data: {json.dumps(metrics)}\n\n"

               await asyncio.sleep(2)  # Update every 2 seconds

       return StreamingResponse(
           metrics_generator(),
           media_type="text/event-stream"
       )

Advanced Streaming Patterns
----------------------------

Chunked File Streaming
~~~~~~~~~~~~~~~~~~~~~~~

Stream large files efficiently:

.. code-block:: python

   import os
   from pathlib import Path

   @app.get("/download/{filename}")
   async def stream_file_download(request: Request, filename: str):
       """Stream large file download"""

       file_path = Path("uploads") / filename

       if not file_path.exists():
           return JSONResponse({"error": "File not found"}, status_code=404)

       async def file_streamer():
           """Stream file in chunks"""
           chunk_size = 8192  # 8KB chunks

           with open(file_path, "rb") as file:
               while True:
                   chunk = file.read(chunk_size)
                   if not chunk:
                       break
                   yield chunk

       # Get file size for Content-Length header
       file_size = file_path.stat().st_size

       return StreamingResponse(
           file_streamer(),
           media_type="application/octet-stream",
           headers={
               "Content-Disposition": f"attachment; filename={filename}",
               "Content-Length": str(file_size)
           }
       )

Data Processing Pipeline
~~~~~~~~~~~~~~~~~~~~~~~~

Stream processed data in real-time:

.. code-block:: python

   @app.post("/process-stream")
   async def stream_data_processing(request: Request):
       """Stream data processing results"""

       async def process_and_stream():
           """Process data and stream results"""
           # Simulate large dataset processing
           total_items = 1000

           for i in range(total_items):
               if await request.is_disconnected():
                   break

               # Simulate data processing
               processed_item = {
                   "item_id": i,
                   "processed_at": datetime.now().isoformat(),
                   "result": f"Processed item {i}",
                   "progress": round((i + 1) / total_items * 100, 2)
               }

               # Stream each processed item
               yield f"data: {json.dumps(processed_item)}\n\n"

               # Simulate processing time
               await asyncio.sleep(0.01)

           # Send completion event
           completion = {
               "event": "completed",
               "total_processed": total_items,
               "completed_at": datetime.now().isoformat()
           }

           yield f"event: completed\n"
           yield f"data: {json.dumps(completion)}\n\n"

       return StreamingResponse(
           process_and_stream(),
           media_type="text/event-stream"
       )

Connection Management
---------------------

Active Connection Tracking
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Track and manage active streaming connections:

.. code-block:: python

   class ConnectionManager:
       def __init__(self):
           self.active_connections = set()
           self.connection_metadata = {}

       def add_connection(self, connection_id: str, metadata: dict = None):
           """Add new active connection"""
           self.active_connections.add(connection_id)
           self.connection_metadata[connection_id] = {
               "connected_at": datetime.now(),
               "metadata": metadata or {}
           }
           print(f"➕ New connection: {connection_id}")

       def remove_connection(self, connection_id: str):
           """Remove disconnected connection"""
           self.active_connections.discard(connection_id)
           self.connection_metadata.pop(connection_id, None)
           print(f"➖ Removed connection: {connection_id}")

       def get_active_count(self):
           """Get number of active connections"""
           return len(self.active_connections)

       def cleanup_stale_connections(self):
           """Remove stale connections"""
           # Implementation would check for actual connection status
           pass

   # Global connection manager
   connection_manager = ConnectionManager()

   @app.get("/managed-stream")
   async def managed_streaming_endpoint(request: Request):
       """Streaming endpoint with connection management"""

       # Generate unique connection ID
       import uuid
       connection_id = str(uuid.uuid4())

       # Add connection to manager
       connection_manager.add_connection(
           connection_id,
           metadata={
               "client_ip": request.client.host,
               "user_agent": request.headers.get("User-Agent", ""),
               "endpoint": "/managed-stream"
           }
       )

       async def managed_stream():
           """Stream with connection management"""
           try:
               counter = 0
               while True:
                   if await request.is_disconnected():
                       break

                   data = {
                       "connection_id": connection_id,
                       "message": f"Managed message {counter}",
                       "active_connections": connection_manager.get_active_count(),
                       "timestamp": datetime.now().isoformat()
                   }

                   yield f"data: {json.dumps(data)}\n\n"
                   counter += 1
                   await asyncio.sleep(1)

           finally:
               # Cleanup connection when done
               connection_manager.remove_connection(connection_id)

       return StreamingResponse(
           managed_stream(),
           media_type="text/event-stream"
       )

Broadcasting to Multiple Clients
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Broadcast events to all connected clients:

.. code-block:: python

   class Broadcaster:
       def __init__(self):
           self.subscribers = {}

       def subscribe(self, connection_id: str, queue: asyncio.Queue):
           """Subscribe to broadcasts"""
           self.subscribers[connection_id] = queue

       def unsubscribe(self, connection_id: str):
           """Unsubscribe from broadcasts"""
           self.subscribers.pop(connection_id, None)

       async def broadcast(self, message: dict):
           """Broadcast message to all subscribers"""
           if not self.subscribers:
               return

           # Send to all subscribers
           for connection_id, queue in self.subscribers.items():
               try:
                   await queue.put(message)
               except Exception as e:
                   print(f"Failed to send to {connection_id}: {e}")
                   # Remove failed connection
                   self.unsubscribe(connection_id)

   broadcaster = Broadcaster()

   @app.get("/broadcast-stream")
   async def broadcast_stream(request: Request):
       """Join broadcast stream"""

       import uuid
       connection_id = str(uuid.uuid4())
       message_queue = asyncio.Queue()

       # Subscribe to broadcasts
       broadcaster.subscribe(connection_id, message_queue)

       async def stream_broadcasts():
           """Stream broadcast messages"""
           try:
               while True:
                   if await request.is_disconnected():
                       break

                   try:
                       # Wait for broadcast message with timeout
                       message = await asyncio.wait_for(
                           message_queue.get(),
                           timeout=1.0
                       )

                       yield f"data: {json.dumps(message)}\n\n"

                   except asyncio.TimeoutError:
                       # Send heartbeat to keep connection alive
                       heartbeat = {
                           "type": "heartbeat",
                           "timestamp": datetime.now().isoformat(),
                           "connection_id": connection_id
                       }
                       yield f"event: heartbeat\n"
                       yield f"data: {json.dumps(heartbeat)}\n\n"

           finally:
               broadcaster.unsubscribe(connection_id)

       return StreamingResponse(
           stream_broadcasts(),
           media_type="text/event-stream"
       )

   @app.post("/broadcast")
   async def send_broadcast(request: Request):
       """Send message to all connected clients"""

       # Get message from request body
       body = await request.json()
       message = {
           "type": "broadcast",
           "message": body.get("message", ""),
           "sender": body.get("sender", "server"),
           "timestamp": datetime.now().isoformat()
       }

       # Broadcast to all connected clients
       await broadcaster.broadcast(message)

       return JSONResponse({
           "status": "broadcast_sent",
           "message": message,
           "recipients": len(broadcaster.subscribers)
       })

Real-Time Applications
----------------------

Live Chat System
~~~~~~~~~~~~~~~~

Build a live chat with streaming:

.. code-block:: python

   class ChatRoom:
       def __init__(self):
           self.clients = {}
           self.message_history = []

       def join(self, client_id: str, client_name: str, queue: asyncio.Queue):
           """Client joins chat room"""
           self.clients[client_id] = {
               "name": client_name,
               "queue": queue,
               "joined_at": datetime.now()
           }

           # Send join notification
           join_message = {
               "type": "user_joined",
               "user": client_name,
               "timestamp": datetime.now().isoformat(),
               "clients_count": len(self.clients)
           }

           asyncio.create_task(self.broadcast_to_all(join_message))

       def leave(self, client_id: str):
           """Client leaves chat room"""
           client = self.clients.pop(client_id, None)

           if client:
               leave_message = {
                   "type": "user_left",
                   "user": client["name"],
                   "timestamp": datetime.now().isoformat(),
                   "clients_count": len(self.clients)
               }

               asyncio.create_task(self.broadcast_to_all(leave_message))

       async def broadcast_to_all(self, message: dict):
           """Broadcast message to all clients"""
           self.message_history.append(message)

           # Keep only last 100 messages
           if len(self.message_history) > 100:
               self.message_history = self.message_history[-100:]

           for client_id, client in self.clients.items():
               try:
                   await client["queue"].put(message)
               except Exception:
                   # Remove disconnected client
                   self.clients.pop(client_id, None)

   chat_room = ChatRoom()

   @app.get("/chat/{username}")
   async def join_chat(request: Request, username: str):
       """Join chat room stream"""

       import uuid
       client_id = str(uuid.uuid4())
       message_queue = asyncio.Queue()

       # Join chat room
       chat_room.join(client_id, username, message_queue)

       async def chat_stream():
           """Stream chat messages"""
           try:
               # Send chat history first
               for message in chat_room.message_history[-10:]:  # Last 10 messages
                   yield f"data: {json.dumps(message)}\n\n"

               # Stream new messages
               while True:
                   if await request.is_disconnected():
                       break

                   try:
                       message = await asyncio.wait_for(
                           message_queue.get(),
                           timeout=30.0  # 30 second timeout
                       )

                       yield f"data: {json.dumps(message)}\n\n"

                   except asyncio.TimeoutError:
                       # Send keepalive
                       keepalive = {
                           "type": "keepalive",
                           "timestamp": datetime.now().isoformat()
                       }
                       yield f"event: keepalive\n"
                       yield f"data: {json.dumps(keepalive)}\n\n"

           finally:
               chat_room.leave(client_id)

       return StreamingResponse(
           chat_stream(),
           media_type="text/event-stream"
       )

   @app.post("/chat/send")
   async def send_chat_message(request: Request):
       """Send message to chat room"""

       body = await request.json()
       message = {
           "type": "message",
           "user": body.get("user", "Anonymous"),
           "text": body.get("message", ""),
           "timestamp": datetime.now().isoformat()
       }

       await chat_room.broadcast_to_all(message)

       return JSONResponse({"status": "message_sent"})

Live Analytics Dashboard
~~~~~~~~~~~~~~~~~~~~~~~~

Stream analytics data for dashboards:

.. code-block:: python

   class AnalyticsStreamer:
       def __init__(self):
           self.subscribers = {}
           self.analytics_data = {
               "page_views": 0,
               "unique_visitors": set(),
               "api_calls": 0,
               "errors": 0
           }

       def track_page_view(self, visitor_id: str):
           """Track page view"""
           self.analytics_data["page_views"] += 1
           self.analytics_data["unique_visitors"].add(visitor_id)

           asyncio.create_task(self.broadcast_update())

       def track_api_call(self):
           """Track API call"""
           self.analytics_data["api_calls"] += 1
           asyncio.create_task(self.broadcast_update())

       def track_error(self):
           """Track error"""
           self.analytics_data["errors"] += 1
           asyncio.create_task(self.broadcast_update())

       async def broadcast_update(self):
           """Broadcast analytics update"""
           update = {
               "page_views": self.analytics_data["page_views"],
               "unique_visitors": len(self.analytics_data["unique_visitors"]),
               "api_calls": self.analytics_data["api_calls"],
               "errors": self.analytics_data["errors"],
               "timestamp": datetime.now().isoformat()
           }

           for queue in self.subscribers.values():
               try:
                   await queue.put(update)
               except Exception:
                   pass

   analytics = AnalyticsStreamer()

   @app.get("/analytics-stream")
   async def analytics_dashboard_stream(request: Request):
       """Stream analytics for dashboard"""

       import uuid
       subscriber_id = str(uuid.uuid4())
       queue = asyncio.Queue()

       analytics.subscribers[subscriber_id] = queue

       async def stream_analytics():
           """Stream analytics updates"""
           try:
               while True:
                   if await request.is_disconnected():
                       break

                   try:
                       update = await asyncio.wait_for(queue.get(), timeout=5.0)
                       yield f"data: {json.dumps(update)}\n\n"
                   except asyncio.TimeoutError:
                       # Send current state as keepalive
                       current_state = {
                           "page_views": analytics.analytics_data["page_views"],
                           "unique_visitors": len(analytics.analytics_data["unique_visitors"]),
                           "api_calls": analytics.analytics_data["api_calls"],
                           "errors": analytics.analytics_data["errors"],
                           "timestamp": datetime.now().isoformat()
                       }
                       yield f"event: keepalive\n"
                       yield f"data: {json.dumps(current_state)}\n\n"
           finally:
               analytics.subscribers.pop(subscriber_id, None)

       return StreamingResponse(
           stream_analytics(),
           media_type="text/event-stream"
       )

Performance Optimization
------------------------

Memory Efficient Streaming
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Stream large datasets without memory issues:

.. code-block:: python

   @app.get("/large-dataset")
   async def stream_large_dataset(request: Request):
       """Stream large dataset efficiently"""

       async def efficient_data_stream():
           """Generate large dataset efficiently"""
           batch_size = 100
           total_records = 100000

           for batch_start in range(0, total_records, batch_size):
               if await request.is_disconnected():
                   break

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
                   "total_records": total_records
               }

               yield f"data: {json.dumps(chunk)}\n\n"

               # Small delay to prevent overwhelming the client
               await asyncio.sleep(0.01)

       return StreamingResponse(
           efficient_data_stream(),
           media_type="text/event-stream"
       )

Connection Health Monitoring
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Monitor connection health and auto-recovery:

.. code-block:: python

   @app.get("/health-monitored-stream")
   async def health_monitored_stream(request: Request):
       """Stream with connection health monitoring"""

       async def monitored_stream():
           """Stream with health checks"""
           last_ping = time.time()
           ping_interval = 10  # Ping every 10 seconds

           counter = 0
           while True:
               if await request.is_disconnected():
                   print("Client disconnected - health check detected")
                   break

               current_time = time.time()

               # Send ping if needed
               if current_time - last_ping >= ping_interval:
                   ping_data = {
                       "type": "ping",
                       "server_time": current_time,
                       "connection_duration": current_time - last_ping
                   }
                   yield f"event: ping\n"
                   yield f"data: {json.dumps(ping_data)}\n\n"
                   last_ping = current_time

               # Regular data
               data = {
                   "type": "data",
                   "counter": counter,
                   "timestamp": datetime.now().isoformat()
               }

               yield f"data: {json.dumps(data)}\n\n"
               counter += 1
               await asyncio.sleep(1)

       return StreamingResponse(
           monitored_stream(),
           media_type="text/event-stream",
           headers={
               "X-Health-Monitoring": "enabled",
               "X-Ping-Interval": "10"
           }
       )

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

   # ✅ Good: Check for disconnection regularly
   async def good_stream():
       while True:
           if await request.is_disconnected():
               break  # Exit cleanly
           # Generate data...

   # ❌ Avoid: Long-running operations without checks
   async def bad_stream():
       while True:
           expensive_operation()  # No disconnection check
           yield data

   # ✅ Good: Use appropriate chunk sizes
   chunk_size = 8192  # 8KB chunks for files
   batch_size = 100   # 100 records for data

   # ✅ Good: Implement timeouts
   try:
       data = await asyncio.wait_for(get_data(), timeout=30.0)
   except asyncio.TimeoutError:
       yield "data: {\"type\": \"keepalive\"}\n\n"

This streaming system enables real-time communication and efficient data transfer for modern web applications that require live updates and interactive features.
