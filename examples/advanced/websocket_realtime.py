"""
WebSocket Real-time Communication Example

This example demonstrates advanced WebSocket capabilities
using Catzilla framework.

Features demonstrated:
- WebSocket connections and lifecycle
- Real-time bidirectional communication
- Room-based message broadcasting
- Connection pooling and management
- Message queuing and delivery
- Heartbeat and connection health
- Event-based architecture
- Authentication over WebSocket
"""

from catzilla import Catzilla, Request, Response, JSONResponse, WebSocket
from catzilla.validation import ValidationMiddleware, Field, Model
from catzilla.middleware import ZeroAllocMiddleware
import json
import time
from typing import Any, Dict, List, Optional, Set, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
import uuid
import threading
from collections import defaultdict

# Initialize Catzilla with WebSocket support
app = Catzilla(
    production=False,
    show_banner=True,
    log_requests=True,
    enable_websockets=True,
    enable_validation=True
)

# Add validation middleware
app.add_middleware(ValidationMiddleware)

# WebSocket message types
class MessageType(str, Enum):
    CONNECT = "connect"
    DISCONNECT = "disconnect"
    JOIN_ROOM = "join_room"
    LEAVE_ROOM = "leave_room"
    CHAT_MESSAGE = "chat_message"
    PRIVATE_MESSAGE = "private_message"
    BROADCAST = "broadcast"
    TYPING = "typing"
    HEARTBEAT = "heartbeat"
    ERROR = "error"
    NOTIFICATION = "notification"

# Data models
class WebSocketMessage(Model):
    """WebSocket message model"""
    type: MessageType = Field(description="Message type")
    room: Optional[str] = Field(description="Room identifier")
    data: Dict[str, Any] = Field(default_factory=dict, description="Message data")
    timestamp: Optional[str] = Field(description="Message timestamp")

class ChatMessage(Model):
    """Chat message model"""
    content: str = Field(min_length=1, max_length=1000, description="Message content")
    room: str = Field(min_length=1, description="Room identifier")

class PrivateMessage(Model):
    """Private message model"""
    content: str = Field(min_length=1, max_length=1000, description="Message content")
    recipient: str = Field(description="Recipient user ID")

class RoomJoin(Model):
    """Room join model"""
    room: str = Field(min_length=1, description="Room identifier")
    password: Optional[str] = Field(description="Room password if required")

# Connection and room management
@dataclass
class WebSocketConnection:
    """WebSocket connection info"""
    id: str
    websocket: WebSocket
    user_id: Optional[str] = None
    username: Optional[str] = None
    rooms: Set[str] = None
    connected_at: datetime = None
    last_heartbeat: datetime = None

    def __post_init__(self):
        if self.rooms is None:
            self.rooms = set()
        if self.connected_at is None:
            self.connected_at = datetime.now()
        if self.last_heartbeat is None:
            self.last_heartbeat = datetime.now()

@dataclass
class Room:
    """Chat room info"""
    id: str
    name: str
    description: str = ""
    password: Optional[str] = None
    max_users: int = 100
    created_at: datetime = None
    owner_id: Optional[str] = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()

@dataclass
class Message:
    """Stored message"""
    id: str
    type: MessageType
    content: str
    user_id: str
    username: str
    room: Optional[str] = None
    recipient: Optional[str] = None
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()

# Global storage
connections: Dict[str, WebSocketConnection] = {}
rooms: Dict[str, Room] = {}
room_connections: Dict[str, Set[str]] = defaultdict(set)  # room_id -> connection_ids
user_connections: Dict[str, str] = {}  # user_id -> connection_id
message_history: List[Message] = []
typing_users: Dict[str, Set[str]] = defaultdict(set)  # room_id -> set of user_ids

# Connection lock for thread safety
connection_lock = threading.Lock()

class WebSocketManager:
    """WebSocket connection and room manager"""

    def __init__(self):
        self.heartbeat_interval = 30  # seconds
        self.connection_timeout = 60  # seconds
        self.max_message_history = 1000

    def add_connection(self, connection: WebSocketConnection):
        """Add new WebSocket connection"""
        with connection_lock:
            connections[connection.id] = connection
            if connection.user_id:
                user_connections[connection.user_id] = connection.id

    def remove_connection(self, connection_id: str):
        """Remove WebSocket connection"""
        with connection_lock:
            if connection_id in connections:
                connection = connections[connection_id]

                # Remove from all rooms
                for room_id in list(connection.rooms):
                    self.leave_room(connection_id, room_id)

                # Remove user connection mapping
                if connection.user_id and connection.user_id in user_connections:
                    del user_connections[connection.user_id]

                # Remove connection
                del connections[connection_id]

    def join_room(self, connection_id: str, room_id: str, password: Optional[str] = None) -> bool:
        """Join user to room"""
        with connection_lock:
            if connection_id not in connections:
                return False

            connection = connections[connection_id]

            # Check if room exists
            if room_id not in rooms:
                return False

            room = rooms[room_id]

            # Check password if required
            if room.password and room.password != password:
                return False

            # Check room capacity
            if len(room_connections[room_id]) >= room.max_users:
                return False

            # Add to room
            connection.rooms.add(room_id)
            room_connections[room_id].add(connection_id)

            return True

    def leave_room(self, connection_id: str, room_id: str):
        """Remove user from room"""
        with connection_lock:
            if connection_id in connections:
                connection = connections[connection_id]
                connection.rooms.discard(room_id)

            room_connections[room_id].discard(connection_id)

            # Remove from typing users
            if connection_id in connections and connections[connection_id].user_id:
                typing_users[room_id].discard(connections[connection_id].user_id)

    def broadcast_to_room(self, room_id: str, message: Dict[str, Any], exclude_connection: Optional[str] = None):
        """Broadcast message to all users in room"""
        message_json = json.dumps(message)

        with connection_lock:
            for connection_id in list(room_connections[room_id]):
                if connection_id != exclude_connection and connection_id in connections:
                    try:
                        connections[connection_id].websocket.send_text(message_json)
                    except Exception as e:
                        print(f"Error sending to connection {connection_id}: {e}")
                        # Remove broken connection
                        self.remove_connection(connection_id)

    def send_to_user(self, user_id: str, message: Dict[str, Any]) -> bool:
        """Send message to specific user"""
        with connection_lock:
            if user_id in user_connections:
                connection_id = user_connections[user_id]
                if connection_id in connections:
                    try:
                        connections[connection_id].websocket.send_text(json.dumps(message))
                        return True
                    except Exception as e:
                        print(f"Error sending to user {user_id}: {e}")
                        self.remove_connection(connection_id)
        return False

    def get_room_users(self, room_id: str) -> List[Dict[str, Any]]:
        """Get list of users in room"""
        users = []
        with connection_lock:
            for connection_id in room_connections[room_id]:
                if connection_id in connections:
                    conn = connections[connection_id]
                    if conn.user_id and conn.username:
                        users.append({
                            "user_id": conn.user_id,
                            "username": conn.username,
                            "connected_at": conn.connected_at.isoformat()
                        })
        return users

    def add_message(self, message: Message):
        """Add message to history"""
        message_history.append(message)

        # Trim history if too long
        if len(message_history) > self.max_message_history:
            message_history.pop(0)

    def get_room_history(self, room_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent messages for room"""
        room_messages = []
        for msg in reversed(message_history):
            if msg.room == room_id:
                room_messages.append({
                    "id": msg.id,
                    "type": msg.type.value,
                    "content": msg.content,
                    "user_id": msg.user_id,
                    "username": msg.username,
                    "timestamp": msg.timestamp.isoformat()
                })
                if len(room_messages) >= limit:
                    break

        return list(reversed(room_messages))

    def cleanup_stale_connections(self):
        """Remove connections that haven't sent heartbeat"""
        now = datetime.now()
        stale_connections = []

        with connection_lock:
            for connection_id, connection in connections.items():
                if (now - connection.last_heartbeat).total_seconds() > self.connection_timeout:
                    stale_connections.append(connection_id)

        for connection_id in stale_connections:
            print(f"Removing stale connection: {connection_id}")
            self.remove_connection(connection_id)

# Global WebSocket manager
ws_manager = WebSocketManager()

@app.get("/")
def home(request: Request) -> Response:
    """WebSocket API documentation"""
    return JSONResponse({
        "message": "Catzilla WebSocket Real-time Communication Example",
        "features": [
            "WebSocket connections and lifecycle",
            "Real-time bidirectional communication",
            "Room-based message broadcasting",
            "Connection pooling and management",
            "Message queuing and delivery",
            "Heartbeat and connection health",
            "Event-based architecture",
            "Authentication over WebSocket"
        ],
        "websocket_endpoint": "ws://localhost:8000/ws",
        "message_types": [msg_type.value for msg_type in MessageType],
        "available_rooms": list(rooms.keys()),
        "connection_stats": {
            "total_connections": len(connections),
            "total_rooms": len(rooms),
            "total_messages": len(message_history)
        },
        "examples": {
            "connect": {
                "type": "connect",
                "data": {"username": "john_doe", "user_id": "user123"}
            },
            "join_room": {
                "type": "join_room",
                "data": {"room": "general", "password": None}
            },
            "chat_message": {
                "type": "chat_message",
                "data": {"content": "Hello everyone!", "room": "general"}
            }
        }
    })

# REST endpoints for room management
@app.post("/api/rooms")
def create_room(request: Request) -> Response:
    """Create a new chat room"""
    try:
        data = request.json()
        room_id = data.get("id") or str(uuid.uuid4())
        name = data.get("name")
        description = data.get("description", "")
        password = data.get("password")
        max_users = data.get("max_users", 100)
        owner_id = data.get("owner_id")

        if not name:
            return JSONResponse({"error": "Room name is required"}, status_code=400)

        if room_id in rooms:
            return JSONResponse({"error": "Room already exists"}, status_code=409)

        room = Room(
            id=room_id,
            name=name,
            description=description,
            password=password,
            max_users=max_users,
            owner_id=owner_id
        )

        rooms[room_id] = room

        return JSONResponse({
            "id": room.id,
            "name": room.name,
            "description": room.description,
            "has_password": bool(room.password),
            "max_users": room.max_users,
            "created_at": room.created_at.isoformat()
        }, status_code=201)

    except Exception as e:
        return JSONResponse({"error": "Invalid request", "details": str(e)}, status_code=400)

@app.get("/api/rooms")
def list_rooms(request: Request) -> Response:
    """List all chat rooms"""
    rooms_list = []
    for room in rooms.values():
        rooms_list.append({
            "id": room.id,
            "name": room.name,
            "description": room.description,
            "has_password": bool(room.password),
            "max_users": room.max_users,
            "current_users": len(room_connections[room.id]),
            "created_at": room.created_at.isoformat()
        })

    return JSONResponse({"rooms": rooms_list})

@app.get("/api/rooms/{room_id}")
def get_room_info(request: Request) -> Response:
    """Get room information and users"""
    room_id = request.path_params["room_id"]

    if room_id not in rooms:
        return JSONResponse({"error": "Room not found"}, status_code=404)

    room = rooms[room_id]
    users = ws_manager.get_room_users(room_id)

    return JSONResponse({
        "id": room.id,
        "name": room.name,
        "description": room.description,
        "has_password": bool(room.password),
        "max_users": room.max_users,
        "current_users": len(users),
        "users": users,
        "created_at": room.created_at.isoformat()
    })

@app.get("/api/rooms/{room_id}/messages")
def get_room_messages(request: Request) -> Response:
    """Get room message history"""
    room_id = request.path_params["room_id"]
    limit = int(request.query_params.get("limit", 50))

    if room_id not in rooms:
        return JSONResponse({"error": "Room not found"}, status_code=404)

    messages = ws_manager.get_room_history(room_id, limit)

    return JSONResponse({
        "room_id": room_id,
        "messages": messages,
        "total": len(messages)
    })

# WebSocket endpoint
@app.websocket("/ws")
def websocket_endpoint(websocket: WebSocket):
    """Main WebSocket endpoint"""
    connection_id = str(uuid.uuid4())
    connection = None

    try:
        # Accept WebSocket connection
        websocket.accept()

        # Create connection object
        connection = WebSocketConnection(
            id=connection_id,
            websocket=websocket
        )

        ws_manager.add_connection(connection)

        print(f"WebSocket connection established: {connection_id}")

        # Send welcome message
        welcome_message = {
            "type": MessageType.CONNECT.value,
            "data": {
                "connection_id": connection_id,
                "message": "Connected to Catzilla WebSocket server",
                "timestamp": datetime.now().isoformat()
            }
        }
        websocket.send_text(json.dumps(welcome_message))

        # Message handling loop
        while True:
            try:
                # Receive message
                data = websocket.receive_text()
                message_data = json.loads(data)

                # Update heartbeat
                connection.last_heartbeat = datetime.now()

                # Process message
                handle_websocket_message(connection, message_data)

            except Exception as e:
                print(f"Error processing WebSocket message: {e}")
                error_message = {
                    "type": MessageType.ERROR.value,
                    "data": {
                        "error": "Invalid message format",
                        "details": str(e)
                    }
                }
                websocket.send_text(json.dumps(error_message))

    except Exception as e:
        print(f"WebSocket error: {e}")

    finally:
        # Clean up connection
        if connection:
            print(f"WebSocket connection closed: {connection_id}")
            ws_manager.remove_connection(connection_id)

def handle_websocket_message(connection: WebSocketConnection, message_data: Dict[str, Any]):
    """Handle incoming WebSocket message"""
    try:
        # Validate message structure
        message = WebSocketMessage.validate(message_data)
        message_type = message.type
        data = message.data

        if message_type == MessageType.CONNECT:
            handle_connect(connection, data)

        elif message_type == MessageType.JOIN_ROOM:
            handle_join_room(connection, data)

        elif message_type == MessageType.LEAVE_ROOM:
            handle_leave_room(connection, data)

        elif message_type == MessageType.CHAT_MESSAGE:
            handle_chat_message(connection, data)

        elif message_type == MessageType.PRIVATE_MESSAGE:
            handle_private_message(connection, data)

        elif message_type == MessageType.TYPING:
            handle_typing(connection, data)

        elif message_type == MessageType.HEARTBEAT:
            handle_heartbeat(connection, data)

        else:
            send_error(connection, f"Unknown message type: {message_type}")

    except ValueError as e:
        send_error(connection, f"Invalid message: {str(e)}")
    except Exception as e:
        send_error(connection, f"Server error: {str(e)}")

def handle_connect(connection: WebSocketConnection, data: Dict[str, Any]):
    """Handle user connection with authentication"""
    username = data.get("username")
    user_id = data.get("user_id")

    if not username:
        send_error(connection, "Username is required")
        return

    # Update connection info
    connection.username = username
    connection.user_id = user_id

    # Update user connection mapping
    if user_id:
        user_connections[user_id] = connection.id

    # Send confirmation
    response = {
        "type": MessageType.CONNECT.value,
        "data": {
            "success": True,
            "user_id": user_id,
            "username": username,
            "connection_id": connection.id,
            "available_rooms": list(rooms.keys())
        }
    }
    connection.websocket.send_text(json.dumps(response))

def handle_join_room(connection: WebSocketConnection, data: Dict[str, Any]):
    """Handle room join request"""
    try:
        room_data = RoomJoin.validate(data)
        room_id = room_data.room
        password = room_data.password

        # Check if user is authenticated
        if not connection.username:
            send_error(connection, "Must authenticate before joining rooms")
            return

        # Try to join room
        success = ws_manager.join_room(connection.id, room_id, password)

        if success:
            # Send confirmation to user
            response = {
                "type": MessageType.JOIN_ROOM.value,
                "data": {
                    "success": True,
                    "room": room_id,
                    "users": ws_manager.get_room_users(room_id),
                    "recent_messages": ws_manager.get_room_history(room_id, 20)
                }
            }
            connection.websocket.send_text(json.dumps(response))

            # Notify other users in room
            room_notification = {
                "type": MessageType.NOTIFICATION.value,
                "data": {
                    "message": f"{connection.username} joined the room",
                    "room": room_id,
                    "user_id": connection.user_id,
                    "username": connection.username,
                    "timestamp": datetime.now().isoformat()
                }
            }
            ws_manager.broadcast_to_room(room_id, room_notification, exclude_connection=connection.id)

        else:
            send_error(connection, "Failed to join room (invalid password or room full)")

    except ValueError as e:
        send_error(connection, f"Invalid room join request: {str(e)}")

def handle_leave_room(connection: WebSocketConnection, data: Dict[str, Any]):
    """Handle room leave request"""
    room_id = data.get("room")

    if not room_id:
        send_error(connection, "Room ID is required")
        return

    # Leave room
    ws_manager.leave_room(connection.id, room_id)

    # Send confirmation
    response = {
        "type": MessageType.LEAVE_ROOM.value,
        "data": {
            "success": True,
            "room": room_id
        }
    }
    connection.websocket.send_text(json.dumps(response))

    # Notify other users in room
    room_notification = {
        "type": MessageType.NOTIFICATION.value,
        "data": {
            "message": f"{connection.username} left the room",
            "room": room_id,
            "user_id": connection.user_id,
            "username": connection.username,
            "timestamp": datetime.now().isoformat()
        }
    }
    ws_manager.broadcast_to_room(room_id, room_notification)

def handle_chat_message(connection: WebSocketConnection, data: Dict[str, Any]):
    """Handle chat message"""
    try:
        chat_data = ChatMessage.validate(data)
        room_id = chat_data.room
        content = chat_data.content

        # Check if user is in room
        if room_id not in connection.rooms:
            send_error(connection, "You are not in this room")
            return

        # Create message
        message = Message(
            id=str(uuid.uuid4()),
            type=MessageType.CHAT_MESSAGE,
            content=content,
            user_id=connection.user_id,
            username=connection.username,
            room=room_id
        )

        # Store message
        ws_manager.add_message(message)

        # Broadcast to room
        broadcast_message = {
            "type": MessageType.CHAT_MESSAGE.value,
            "data": {
                "id": message.id,
                "content": content,
                "room": room_id,
                "user_id": connection.user_id,
                "username": connection.username,
                "timestamp": message.timestamp.isoformat()
            }
        }
        ws_manager.broadcast_to_room(room_id, broadcast_message)

    except ValueError as e:
        send_error(connection, f"Invalid chat message: {str(e)}")

def handle_private_message(connection: WebSocketConnection, data: Dict[str, Any]):
    """Handle private message"""
    try:
        private_data = PrivateMessage.validate(data)
        recipient_id = private_data.recipient
        content = private_data.content

        # Create message
        message = Message(
            id=str(uuid.uuid4()),
            type=MessageType.PRIVATE_MESSAGE,
            content=content,
            user_id=connection.user_id,
            username=connection.username,
            recipient=recipient_id
        )

        # Store message
        ws_manager.add_message(message)

        # Send to recipient
        private_message = {
            "type": MessageType.PRIVATE_MESSAGE.value,
            "data": {
                "id": message.id,
                "content": content,
                "from_user_id": connection.user_id,
                "from_username": connection.username,
                "timestamp": message.timestamp.isoformat()
            }
        }

        success = ws_manager.send_to_user(recipient_id, private_message)

        # Send confirmation to sender
        confirmation = {
            "type": MessageType.PRIVATE_MESSAGE.value,
            "data": {
                "id": message.id,
                "delivered": success,
                "recipient": recipient_id,
                "timestamp": message.timestamp.isoformat()
            }
        }
        connection.websocket.send_text(json.dumps(confirmation))

    except ValueError as e:
        send_error(connection, f"Invalid private message: {str(e)}")

def handle_typing(connection: WebSocketConnection, data: Dict[str, Any]):
    """Handle typing indicator"""
    room_id = data.get("room")
    is_typing = data.get("typing", False)

    if not room_id or room_id not in connection.rooms:
        return

    # Update typing status
    if is_typing:
        typing_users[room_id].add(connection.user_id)
    else:
        typing_users[room_id].discard(connection.user_id)

    # Broadcast typing status
    typing_message = {
        "type": MessageType.TYPING.value,
        "data": {
            "room": room_id,
            "user_id": connection.user_id,
            "username": connection.username,
            "typing": is_typing,
            "typing_users": list(typing_users[room_id])
        }
    }
    ws_manager.broadcast_to_room(room_id, typing_message, exclude_connection=connection.id)

def handle_heartbeat(connection: WebSocketConnection, data: Dict[str, Any]):
    """Handle heartbeat message"""
    connection.last_heartbeat = datetime.now()

    # Send heartbeat response
    response = {
        "type": MessageType.HEARTBEAT.value,
        "data": {
            "timestamp": connection.last_heartbeat.isoformat(),
            "connection_id": connection.id
        }
    }
    connection.websocket.send_text(json.dumps(response))

def send_error(connection: WebSocketConnection, error_message: str):
    """Send error message to connection"""
    error_response = {
        "type": MessageType.ERROR.value,
        "data": {
            "error": error_message,
            "timestamp": datetime.now().isoformat()
        }
    }
    connection.websocket.send_text(json.dumps(error_response))

@app.get("/health")
def health_check(request: Request) -> Response:
    """Health check with WebSocket stats"""
    return JSONResponse({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "websocket_stats": {
            "active_connections": len(connections),
            "total_rooms": len(rooms),
            "total_messages": len(message_history),
            "room_stats": {
                room_id: len(connections_set)
                for room_id, connections_set in room_connections.items()
            }
        }
    })

# Create default rooms
def create_default_rooms():
    """Create default chat rooms"""
    default_rooms = [
        {"id": "general", "name": "General", "description": "General discussion"},
        {"id": "tech", "name": "Technology", "description": "Tech talk and programming"},
        {"id": "random", "name": "Random", "description": "Random chat and fun"},
    ]

    for room_data in default_rooms:
        if room_data["id"] not in rooms:
            room = Room(**room_data)
            rooms[room.id] = room

# Background task to clean up stale connections
def cleanup_task():
    """Background task to clean up stale connections"""
    import threading
    import time

    def cleanup_loop():
        while True:
            time.sleep(30)  # Check every 30 seconds
            ws_manager.cleanup_stale_connections()

    cleanup_thread = threading.Thread(target=cleanup_loop, daemon=True)
    cleanup_thread.start()

if __name__ == "__main__":
    print("🚨 Starting Catzilla WebSocket Real-time Communication Example")
    print("📝 Available endpoints:")
    print("   GET    /                          - WebSocket API documentation")
    print("   WS     /ws                        - WebSocket endpoint")
    print("   POST   /api/rooms                 - Create chat room")
    print("   GET    /api/rooms                 - List chat rooms")
    print("   GET    /api/rooms/{id}            - Get room info")
    print("   GET    /api/rooms/{id}/messages   - Get room messages")
    print("   GET    /health                    - Health check")
    print()
    print("🎨 Features demonstrated:")
    print("   • WebSocket connections and lifecycle")
    print("   • Real-time bidirectional communication")
    print("   • Room-based message broadcasting")
    print("   • Connection pooling and management")
    print("   • Message queuing and delivery")
    print("   • Heartbeat and connection health")
    print("   • Event-based architecture")
    print("   • Authentication over WebSocket")
    print()
    print("🧪 WebSocket message examples:")
    print("   # Connect:")
    print('   {"type": "connect", "data": {"username": "john", "user_id": "123"}}')
    print()
    print("   # Join room:")
    print('   {"type": "join_room", "data": {"room": "general"}}')
    print()
    print("   # Send message:")
    print('   {"type": "chat_message", "data": {"room": "general", "content": "Hello!"}}')
    print()
    print("   # Typing indicator:")
    print('   {"type": "typing", "data": {"room": "general", "typing": true}}')
    print()

    # Create default rooms
    create_default_rooms()
    print("🏠 Default rooms created: general, tech, random")

    # Start cleanup task
    cleanup_task()
    print("🧹 Connection cleanup task started")
    print()

    app.listen(host="0.0.0.0", port=8000)
