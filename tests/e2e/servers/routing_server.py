#!/usr/bin/env python3
"""
E2E Test Server for Routing Functionality

This server mirrors examples/core/basic_routing.py for E2E testing.
It provides all routing functionality to be tested via HTTP.
"""
import sys
import argparse
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from catzilla import (
    Catzilla, Request, Response, JSONResponse, BaseModel,
    Query, Header, Path as PathParam, Form, ValidationError
)
from typing import Optional
import asyncio
import time

# Initialize Catzilla for E2E testing
app = Catzilla(
    production=False,
    show_banner=False,  # Silent for testing
    log_requests=False  # Reduce noise in tests
)

# User model for JSON body validation
class UserCreate(BaseModel):
    """User creation model with auto-validation"""
    id: Optional[int] = None
    name: str = "Unknown"  # Has default but still validates JSON structure
    email: Optional[str] = None

class UserUpdate(BaseModel):
    """User update model"""
    name: Optional[str] = None
    email: Optional[str] = None

# Health check endpoint (required for E2E server management)
@app.get("/health")
def health_check(request: Request) -> Response:
    """Health check endpoint for E2E test management"""
    return JSONResponse({
        "status": "healthy",
        "server": "routing_e2e_test",
        "timestamp": time.time()
    })

# Basic GET route
@app.get("/")
def home(request: Request) -> Response:
    """Home endpoint with server information"""
    return JSONResponse({
        "message": "Welcome to Catzilla E2E Routing Test!",
        "framework": "Catzilla v0.2.0",
        "server": "routing_e2e_test",
        "endpoints": [
            "GET /",
            "GET /health",
            "GET /users/{user_id}",
            "GET /users/{user_id}/posts/{post_id}",
            "GET /search",
            "POST /users",
            "PUT /users/{user_id}",
            "DELETE /users/{user_id}",
            "GET /error/{error_type}"
        ]
    })

# Route with path parameters
@app.get("/users/{user_id}")
def get_user(request: Request, user_id: int = PathParam(..., description="User ID", ge=1)) -> Response:
    """Get user by ID with path parameters"""
    return JSONResponse({
        "user_id": user_id,
        "name": f"User {user_id}",
        "email": f"user{user_id}@example.com",
        "type": "user",
        "path": request.path,
        "method": request.method
    })

# Route with multiple path parameters
@app.get("/users/{user_id}/posts/{post_id}")
def get_user_post(
    request: Request,
    user_id: int = PathParam(..., description="User ID", ge=1),
    post_id: int = PathParam(..., description="Post ID", ge=1)
) -> Response:
    """Get user post with multiple path parameters"""
    return JSONResponse({
        "user_id": user_id,
        "post_id": post_id,
        "title": f"Post {post_id} by User {user_id}",
        "content": f"This is post {post_id} created by user {user_id}",
        "type": "user_post",
        "path": request.path
    })

# Route with query parameters
@app.get("/search")
def search(
    request: Request,
    q: str = Query("", description="Search query"),
    limit: int = Query(10, ge=1, le=100, description="Results limit"),
    offset: int = Query(0, ge=0, description="Results offset")
) -> Response:
    """Search endpoint with query parameters"""
    return JSONResponse({
        "query": q,
        "limit": limit,
        "offset": offset,
        "total": 50,  # Mock total
        "results": [
            {"id": i, "title": f"Result {i} for '{q}'", "score": 100 - i}
            for i in range(offset, min(offset + limit, 50))
        ]
    })

# POST route with request body
@app.post("/users")
def create_user(request: Request, user: UserCreate) -> Response:
    """Create user with JSON body validation"""
    # Generate ID if not provided
    user_id = user.id or int(time.time() * 1000) % 100000

    return JSONResponse({
        "message": "User created successfully",
        "id": user_id,
        "created": {
            "id": user_id,
            "name": user.name,
            "email": user.email,
            "created_at": time.time()
        }
    }, status_code=201)

# PUT route for updates
@app.put("/users/{user_id}")
def update_user(
    request: Request,
    user_id: int = PathParam(..., description="User ID", ge=1),
    user: UserUpdate = None
) -> Response:
    """Update user with PUT request"""
    return JSONResponse({
        "message": "User updated successfully",
        "user_id": user_id,
        "updated": {
            "name": user.name if user and user.name else f"User {user_id}",
            "email": user.email if user and user.email else f"user{user_id}@example.com"
        },
        "updated_at": time.time()
    })

# DELETE route
@app.delete("/users/{user_id}")
def delete_user(request: Request, user_id: int = PathParam(..., description="User ID", ge=1)) -> Response:
    """Delete user"""
    return JSONResponse({
        "message": "User deleted successfully",
        "user_id": user_id,
        "deleted": True,
        "deleted_at": time.time()
    })

# Error handling routes
@app.get("/error/{error_type}")
def error_handler(request: Request, error_type: str = PathParam(...)) -> Response:
    """Test error responses"""
    if error_type == "400":
        return JSONResponse({"error": "Bad Request", "code": 400}, status_code=400)
    elif error_type == "404":
        return JSONResponse({"error": "Not Found", "code": 404}, status_code=404)
    elif error_type == "500":
        return JSONResponse({"error": "Internal Server Error", "code": 500}, status_code=500)
    else:
        return JSONResponse({"error": f"Unknown error type: {error_type}"}, status_code=400)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Catzilla E2E Routing Test Server")
    parser.add_argument("--port", type=int, default=8100, help="Port to run server on")
    parser.add_argument("--host", type=str, default="127.0.0.1", help="Host to bind to")

    args = parser.parse_args()

    print(f"🚀 Starting Catzilla E2E Routing Test Server")
    print(f"📍 Server: http://{args.host}:{args.port}")
    print(f"🏥 Health: http://{args.host}:{args.port}/health")

    app.listen(port=args.port, host=args.host)
