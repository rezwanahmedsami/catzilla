"""
Connection Management Example

This example demonstrates Catzilla's streaming connection management,
including WebSocket-like functionality, connection pooling, and graceful handling.

Features demonstrated:
- Connection lifecycle management
- Graceful connection cleanup
- Connection pooling and limits
- Error handling and recovery
- Connection monitoring and metrics
- Memory-efficient stream handling
"""

from catzilla import Catzilla, Request, Response, JSONResponse, StreamingResponse
import json
import time
import weakref
from typing import Generator, Dict, Any, List, Optional, Set
from datetime import datetime, timedelta
import uuid
import logging
from dataclasses import dataclass
from enum import Enum
import threading

# Initialize Catzilla with connection management
app = Catzilla(
    production=False,
    show_banner=True,
    log_requests=True
)

# Connection states
class ConnectionState(Enum):
    CONNECTING = "connecting"
    CONNECTED = "connected"
    STREAMING = "streaming"
    CLOSING = "closing"
    CLOSED = "closed"
    ERROR = "error"

@dataclass
class ConnectionInfo:
    """Connection information tracking"""
    connection_id: str
    client_ip: str
    user_agent: str
    connected_at: datetime
    last_activity: datetime
    state: ConnectionState
    stream_type: str
    bytes_sent: int = 0
    messages_sent: int = 0
    errors: int = 0

# Global connection management
class ConnectionManager:
    """Manages streaming connections with lifecycle tracking"""

    def __init__(self):
        self.connections: Dict[str, ConnectionInfo] = {}
        self.connection_limits: Dict[str, int] = {
            "realtime": 100,
            "events": 200,
            "data": 50,
            "monitoring": 20
        }
        self.cleanup_interval = 60  # seconds
        self.max_idle_time = 300  # 5 minutes
        self._cleanup_thread: Optional[threading.Thread] = None
        self._stop_cleanup = threading.Event()
        self._start_cleanup_thread()

    def _start_cleanup_thread(self):
        """Start background cleanup thread"""
        if self._cleanup_thread is None or not self._cleanup_thread.is_alive():
            self._cleanup_thread = threading.Thread(target=self._cleanup_connections, daemon=True)
            self._cleanup_thread.start()

    def _cleanup_connections(self):
        """Background thread to cleanup idle connections"""
        while not self._stop_cleanup.is_set():
            try:
                self._stop_cleanup.wait(self.cleanup_interval)
                if not self._stop_cleanup.is_set():
                    self._cleanup_idle_connections()
            except Exception as e:
                logging.error(f"Error in connection cleanup: {e}")

    def _cleanup_idle_connections(self):
        """Remove idle and closed connections"""
        current_time = datetime.now()
        to_remove = []

        for conn_id, conn_info in self.connections.items():
            # Check if connection is idle
            idle_time = current_time - conn_info.last_activity
            if idle_time.total_seconds() > self.max_idle_time:
                to_remove.append(conn_id)

            # Check if connection is in error state
            elif conn_info.state in [ConnectionState.CLOSED, ConnectionState.ERROR]:
                to_remove.append(conn_id)

        # Remove idle connections
        for conn_id in to_remove:
            if conn_id in self.connections:
                logging.info(f"Cleaning up idle connection: {conn_id}")
                del self.connections[conn_id]

    def create_connection(
        self,
        client_ip: str,
        user_agent: str,
        stream_type: str
    ) -> str:
        """Create new connection with limits checking"""
        # Check stream type limits
        current_count = sum(
            1 for conn in self.connections.values()
            if conn.stream_type == stream_type and conn.state == ConnectionState.CONNECTED
        )

        if current_count >= self.connection_limits.get(stream_type, 10):
            raise Exception(f"Connection limit reached for {stream_type}: {current_count}")

        # Create connection
        connection_id = f"{stream_type}_{uuid.uuid4().hex[:8]}"

        self.connections[connection_id] = ConnectionInfo(
            connection_id=connection_id,
            client_ip=client_ip,
            user_agent=user_agent,
            connected_at=datetime.now(),
            last_activity=datetime.now(),
            state=ConnectionState.CONNECTING,
            stream_type=stream_type
        )

        logging.info(f"Created connection {connection_id} for {stream_type}")
        return connection_id

    def update_connection_state(self, connection_id: str, state: ConnectionState):
        """Update connection state"""
        if connection_id in self.connections:
            self.connections[connection_id].state = state
            self.connections[connection_id].last_activity = datetime.now()

    def update_connection_stats(self, connection_id: str, bytes_sent: int = 0, messages_sent: int = 0):
        """Update connection statistics"""
        if connection_id in self.connections:
            conn = self.connections[connection_id]
            conn.bytes_sent += bytes_sent
            conn.messages_sent += messages_sent
            conn.last_activity = datetime.now()

    def increment_errors(self, connection_id: str):
        """Increment error count for connection"""
        if connection_id in self.connections:
            self.connections[connection_id].errors += 1
            self.connections[connection_id].last_activity = datetime.now()

    def close_connection(self, connection_id: str):
        """Mark connection as closed"""
        if connection_id in self.connections:
            self.connections[connection_id].state = ConnectionState.CLOSED
            logging.info(f"Closed connection {connection_id}")

    def get_connection_info(self, connection_id: str) -> Optional[ConnectionInfo]:
        """Get connection information"""
        return self.connections.get(connection_id)

    def get_stats(self) -> Dict[str, Any]:
        """Get connection statistics"""
        total_connections = len(self.connections)
        active_connections = sum(
            1 for conn in self.connections.values()
            if conn.state in [ConnectionState.CONNECTED, ConnectionState.STREAMING]
        )

        by_type = {}
        by_state = {}

        for conn in self.connections.values():
            # Count by type
            by_type[conn.stream_type] = by_type.get(conn.stream_type, 0) + 1
            # Count by state
            by_state[conn.state.value] = by_state.get(conn.state.value, 0) + 1

        return {
            "total_connections": total_connections,
            "active_connections": active_connections,
            "by_type": by_type,
            "by_state": by_state,
            "limits": self.connection_limits
        }

# Global connection manager instance
connection_manager = ConnectionManager()

def managed_realtime_stream(connection_id: str) -> Generator[str, None, None]:
    """Managed real-time data stream with connection tracking"""
    try:
        connection_manager.update_connection_state(connection_id, ConnectionState.STREAMING)

        for i in range(100):  # Longer stream for connection testing
            # Check if connection still exists
            conn_info = connection_manager.get_connection_info(connection_id)
            if not conn_info or conn_info.state == ConnectionState.CLOSED:
                logging.info(f"Connection {connection_id} was closed, stopping stream")
                break

            # Generate data
            data = {
                "timestamp": datetime.now().isoformat(),
                "connection_id": connection_id,
                "sequence": i + 1,
                "data": f"realtime_data_{i + 1}",
                "server_time": time.time()
            }

            message = f"data: {json.dumps(data)}\n\n"
            yield message

            # Update connection stats
            connection_manager.update_connection_stats(
                connection_id,
                bytes_sent=len(message.encode()),
                messages_sent=1
            )

            time.sleep(1)

    except Exception as e:
        logging.error(f"Error in managed stream {connection_id}: {e}")
        connection_manager.increment_errors(connection_id)
        connection_manager.update_connection_state(connection_id, ConnectionState.ERROR)

    finally:
        connection_manager.close_connection(connection_id)

def managed_event_stream(connection_id: str) -> Generator[str, None, None]:
    """Managed event stream with heartbeat and error handling"""
    try:
        connection_manager.update_connection_state(connection_id, ConnectionState.STREAMING)

        # Send initial connection event
        initial_event = {
            "type": "connection_established",
            "connection_id": connection_id,
            "timestamp": datetime.now().isoformat()
        }

        message = f"event: connection\ndata: {json.dumps(initial_event)}\n\n"
        yield message
        connection_manager.update_connection_stats(
            connection_id,
            bytes_sent=len(message.encode()),
            messages_sent=1
        )

        # Main event loop
        for i in range(50):
            conn_info = connection_manager.get_connection_info(connection_id)
            if not conn_info or conn_info.state == ConnectionState.CLOSED:
                break

            # Send heartbeat every 5 events
            if i % 5 == 0:
                heartbeat = {
                    "type": "heartbeat",
                    "connection_id": connection_id,
                    "timestamp": datetime.now().isoformat(),
                    "uptime_seconds": (datetime.now() - conn_info.connected_at).total_seconds()
                }

                message = f"event: heartbeat\ndata: {json.dumps(heartbeat)}\n\n"
                yield message
                connection_manager.update_connection_stats(
                    connection_id,
                    bytes_sent=len(message.encode()),
                    messages_sent=1
                )

            # Send data event
            event_data = {
                "type": "data",
                "connection_id": connection_id,
                "sequence": i + 1,
                "payload": f"event_data_{i + 1}",
                "timestamp": datetime.now().isoformat()
            }

            message = f"event: data\ndata: {json.dumps(event_data)}\n\n"
            yield message
            connection_manager.update_connection_stats(
                connection_id,
                bytes_sent=len(message.encode()),
                messages_sent=1
            )

            time.sleep(2)

    except Exception as e:
        logging.error(f"Error in event stream {connection_id}: {e}")
        connection_manager.increment_errors(connection_id)
        connection_manager.update_connection_state(connection_id, ConnectionState.ERROR)

    finally:
        # Send closing event
        try:
            closing_event = {
                "type": "connection_closing",
                "connection_id": connection_id,
                "timestamp": datetime.now().isoformat()
            }

            message = f"event: closing\ndata: {json.dumps(closing_event)}\n\n"
            yield message
        except:
            pass

        connection_manager.close_connection(connection_id)

def managed_monitoring_stream(connection_id: str) -> Generator[str, None, None]:
    """Stream connection monitoring data"""
    try:
        connection_manager.update_connection_state(connection_id, ConnectionState.STREAMING)

        for i in range(30):
            conn_info = connection_manager.get_connection_info(connection_id)
            if not conn_info or conn_info.state == ConnectionState.CLOSED:
                break

            # Get current connection stats
            stats = connection_manager.get_stats()

            monitoring_data = {
                "timestamp": datetime.now().isoformat(),
                "connection_id": connection_id,
                "sequence": i + 1,
                "connection_stats": stats,
                "this_connection": {
                    "connected_at": conn_info.connected_at.isoformat(),
                    "bytes_sent": conn_info.bytes_sent,
                    "messages_sent": conn_info.messages_sent,
                    "errors": conn_info.errors,
                    "uptime_seconds": (datetime.now() - conn_info.connected_at).total_seconds()
                }
            }

            message = f"data: {json.dumps(monitoring_data, indent=2)}\n\n"
            yield message

            connection_manager.update_connection_stats(
                connection_id,
                bytes_sent=len(message.encode()),
                messages_sent=1
            )

            time.sleep(3)

    except Exception as e:
        logging.error(f"Error in monitoring stream {connection_id}: {e}")
        connection_manager.increment_errors(connection_id)
        connection_manager.update_connection_state(connection_id, ConnectionState.ERROR)

    finally:
        connection_manager.close_connection(connection_id)

@app.get("/")
def home(request: Request) -> Response:
    """Home endpoint with connection management info"""
    return JSONResponse({
        "message": "Catzilla Connection Management Example",
        "features": [
            "Connection lifecycle management",
            "Graceful connection cleanup",
            "Connection pooling and limits",
            "Error handling and recovery",
            "Connection monitoring and metrics",
            "Memory-efficient stream handling"
        ],
        "managed_endpoints": {
            "realtime_stream": "/connect/realtime",
            "event_stream": "/connect/events",
            "monitoring_stream": "/connect/monitoring",
            "connection_stats": "/connect/stats",
            "connection_info": "/connect/info/{connection_id}",
            "close_connection": "/connect/close/{connection_id}"
        }
    })

@app.get("/connect/realtime")
def connect_realtime_stream(request: Request) -> Response:
    """Connect to managed real-time stream"""
    try:
        # Get client info safely
        try:
            client_ip = getattr(request.client, 'host', 'unknown') if hasattr(request, 'client') else "unknown"
        except:
            client_ip = "unknown"

        user_agent = request.headers.get("user-agent", "unknown")

        # Create connection
        connection_id = connection_manager.create_connection(
            client_ip=client_ip,
            user_agent=user_agent,
            stream_type="realtime"
        )

        connection_manager.update_connection_state(connection_id, ConnectionState.CONNECTED)

        return StreamingResponse(
            managed_realtime_stream(connection_id),
            content_type="text/plain",
            headers={
                "X-Connection-ID": connection_id,
                "X-Stream-Type": "realtime",
                "Cache-Control": "no-cache",
                "Connection": "keep-alive"
            }
        )

    except Exception as e:
        return JSONResponse(
            {"error": f"Failed to create connection: {str(e)}"},
            status_code=503
        )

@app.get("/connect/events")
def connect_event_stream(request: Request) -> Response:
    """Connect to managed event stream"""
    try:
        # Get client info safely
        try:
            client_ip = getattr(request.client, 'host', 'unknown') if hasattr(request, 'client') else "unknown"
        except:
            client_ip = "unknown"

        user_agent = request.headers.get("user-agent", "unknown")

        # Create connection
        connection_id = connection_manager.create_connection(
            client_ip=client_ip,
            user_agent=user_agent,
            stream_type="events"
        )

        connection_manager.update_connection_state(connection_id, ConnectionState.CONNECTED)

        return StreamingResponse(
            managed_event_stream(connection_id),
            content_type="text/event-stream",
            headers={
                "X-Connection-ID": connection_id,
                "X-Stream-Type": "events",
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Access-Control-Allow-Origin": "*"
            }
        )

    except Exception as e:
        return JSONResponse(
            {"error": f"Failed to create connection: {str(e)}"},
            status_code=503
        )

@app.get("/connect/monitoring")
def connect_monitoring_stream(request: Request) -> Response:
    """Connect to connection monitoring stream"""
    try:
        # Get client info safely
        try:
            client_ip = getattr(request.client, 'host', 'unknown') if hasattr(request, 'client') else "unknown"
        except:
            client_ip = "unknown"

        user_agent = request.headers.get("user-agent", "unknown")

        # Create connection
        connection_id = connection_manager.create_connection(
            client_ip=client_ip,
            user_agent=user_agent,
            stream_type="monitoring"
        )

        connection_manager.update_connection_state(connection_id, ConnectionState.CONNECTED)

        return StreamingResponse(
            managed_monitoring_stream(connection_id),
            content_type="text/plain",
            headers={
                "X-Connection-ID": connection_id,
                "X-Stream-Type": "monitoring",
                "Cache-Control": "no-cache",
                "Connection": "keep-alive"
            }
        )

    except Exception as e:
        return JSONResponse(
            {"error": f"Failed to create connection: {str(e)}"},
            status_code=503
        )

@app.get("/connect/stats")
def get_connection_stats(request: Request) -> Response:
    """Get overall connection statistics"""
    stats = connection_manager.get_stats()

    # Add detailed connection info
    detailed_connections = []
    for conn_id, conn_info in connection_manager.connections.items():
        detailed_connections.append({
            "connection_id": conn_id,
            "client_ip": conn_info.client_ip,
            "connected_at": conn_info.connected_at.isoformat(),
            "last_activity": conn_info.last_activity.isoformat(),
            "state": conn_info.state.value,
            "stream_type": conn_info.stream_type,
            "bytes_sent": conn_info.bytes_sent,
            "messages_sent": conn_info.messages_sent,
            "errors": conn_info.errors,
            "uptime_seconds": (datetime.now() - conn_info.connected_at).total_seconds()
        })

    return JSONResponse({
        "statistics": stats,
        "connections": detailed_connections,
        "server_time": datetime.now().isoformat()
    })

@app.get("/connect/info/{connection_id}")
def get_connection_info(request: Request) -> Response:
    """Get specific connection information"""
    connection_id = request.path_params["connection_id"]

    conn_info = connection_manager.get_connection_info(connection_id)
    if not conn_info:
        return JSONResponse(
            {"error": f"Connection {connection_id} not found"},
            status_code=404
        )

    return JSONResponse({
        "connection_id": connection_id,
        "client_ip": conn_info.client_ip,
        "user_agent": conn_info.user_agent,
        "connected_at": conn_info.connected_at.isoformat(),
        "last_activity": conn_info.last_activity.isoformat(),
        "state": conn_info.state.value,
        "stream_type": conn_info.stream_type,
        "bytes_sent": conn_info.bytes_sent,
        "messages_sent": conn_info.messages_sent,
        "errors": conn_info.errors,
        "uptime_seconds": (datetime.now() - conn_info.connected_at).total_seconds()
    })

@app.post("/connect/close/{connection_id}")
def close_connection_endpoint(request: Request) -> Response:
    """Manually close a connection"""
    connection_id = request.path_params["connection_id"]

    conn_info = connection_manager.get_connection_info(connection_id)
    if not conn_info:
        return JSONResponse(
            {"error": f"Connection {connection_id} not found"},
            status_code=404
        )

    connection_manager.close_connection(connection_id)

    return JSONResponse({
        "message": f"Connection {connection_id} closed",
        "connection_id": connection_id,
        "closed_at": datetime.now().isoformat()
    })

@app.get("/connect/limits")
def get_connection_limits(request: Request) -> Response:
    """Get current connection limits"""
    return JSONResponse({
        "connection_limits": connection_manager.connection_limits,
        "current_stats": connection_manager.get_stats(),
        "cleanup_settings": {
            "cleanup_interval_seconds": connection_manager.cleanup_interval,
            "max_idle_time_seconds": connection_manager.max_idle_time
        }
    })

@app.get("/health")
def health_check(request: Request) -> Response:
    """Health check with connection management status"""
    stats = connection_manager.get_stats()

    return JSONResponse({
        "status": "healthy",
        "connection_management": "enabled",
        "framework": "Catzilla v0.2.0",
        "active_connections": stats["active_connections"],
        "total_connections": stats["total_connections"]
    })

if __name__ == "__main__":
    print("🚨 Starting Catzilla Connection Management Example")
    print("📝 Available endpoints:")
    print("   GET  /                       - Home with connection info")
    print("   GET  /connect/realtime       - Managed real-time stream")
    print("   GET  /connect/events         - Managed event stream")
    print("   GET  /connect/monitoring     - Connection monitoring stream")
    print("   GET  /connect/stats          - Overall connection statistics")
    print("   GET  /connect/info/{id}      - Specific connection info")
    print("   POST /connect/close/{id}     - Manually close connection")
    print("   GET  /connect/limits         - Connection limits and settings")
    print("   GET  /health                 - Health check")
    print()
    print("🎨 Features demonstrated:")
    print("   • Connection lifecycle management")
    print("   • Graceful connection cleanup")
    print("   • Connection pooling and limits")
    print("   • Error handling and recovery")
    print("   • Connection monitoring and metrics")
    print("   • Memory-efficient stream handling")
    print()
    print("🧪 Try these examples:")
    print("   # Start realtime stream:")
    print("   curl -N http://localhost:8000/connect/realtime")
    print()
    print("   # Monitor connections:")
    print("   curl http://localhost:8000/connect/stats")
    print()
    print("   # Get connection limits:")
    print("   curl http://localhost:8000/connect/limits")
    print()

    app.listen(host="0.0.0.0", port=8000)
