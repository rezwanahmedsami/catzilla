"""
Basic Routing Example - C-Accelerated HTTP Router

This example demonstrates Catzilla's C-accelerated HTTP router with
basic route registration and handling.

Features demonstrated:
- Basic GET/POST/PUT/DELETE routes
- Path parameters with auto-validation
- Query parameters with auto-validation
- JSON body validation with BaseModel
- Route registration patterns
"""

from catzilla import (
    Catzilla, Request, Response, JSONResponse, BaseModel,
    Query, Header, Path, Form, ValidationError
)
from typing import Optional

# Initialize Catzilla with C-accelerated routing
app = Catzilla(
    production=False,       # Enable development features
    show_banner=True,      # Show beautiful startup banner
    log_requests=True      # Log all requests in development
)

# User model for JSON body validation
class UserCreate(BaseModel):
    """User creation model with auto-validation"""
    id: Optional[int] = 1
    name: str = "Unknown"
    email: Optional[str] = None

# Basic GET route
@app.get("/")
def home(request: Request) -> Response:
    """Home endpoint with server information"""
    return JSONResponse({
        "message": "Welcome to Catzilla!",
        "framework": "Catzilla v0.2.0",
        "router": "C-Accelerated",
        "performance": "30% faster than FastAPI"
    })

# Route with path parameters
@app.get("/users/{user_id}")
def get_user(request, user_id: int = Path(..., description="User ID", ge=1)) -> Response:
    """Get user by ID - demonstrates path parameters with auto-validation"""

    return JSONResponse({
        "user_id": user_id,
        "message": f"Retrieved user {user_id}",
        "path": request.path
    })

# Route with query parameters
@app.get("/search")
def search(
    request,
    q: str = Query("", description="Search query"),
    limit: int = Query(10, ge=1, le=100, description="Results limit"),
    offset: int = Query(0, ge=0, description="Results offset")
) -> Response:
    """Search endpoint - demonstrates query parameters with auto-validation"""

    return JSONResponse({
        "query": q,
        "limit": limit,
        "offset": offset,
        "results": [
            {"id": i, "title": f"Result {i}", "score": 100 - i}
            for i in range(offset, offset + min(limit, 5))
        ]
    })

# POST route with request body
@app.post("/users")
def create_user(request, user: UserCreate) -> Response:
    """Create user - demonstrates POST with JSON body auto-validation"""

    return JSONResponse({
        "message": "User created successfully",
        "user": {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "created_at": "2025-01-14T10:00:00Z"
        }
    }, status_code=201)

# PUT route for updates
@app.put("/users/{user_id}")
def update_user(request, user_id: int = Path(..., description="User ID", ge=1), user: UserCreate = None) -> Response:
    """Update user - demonstrates PUT method with auto-validation"""

    return JSONResponse({
        "message": f"User {user_id} updated successfully",
        "user_id": user_id,
        "updated_fields": ["name", "email"] if user else [],
        "updated_at": "2025-01-14T10:00:00Z"
    })

# DELETE route
@app.delete("/users/{user_id}")
def delete_user(request, user_id: int = Path(..., description="User ID", ge=1)) -> Response:
    """Delete user - demonstrates DELETE method with auto-validation"""

    return JSONResponse({
        "message": f"User {user_id} deleted successfully",
        "user_id": user_id,
        "deleted_at": "2025-01-14T10:00:00Z"
    })

# Complex path with multiple parameters
@app.get("/api/v1/users/{user_id}/posts/{post_id}")
def get_user_post(
    request,
    user_id: int = Path(..., description="User ID", ge=1),
    post_id: int = Path(..., description="Post ID", ge=1)
) -> Response:
    """Get specific post by user - demonstrates nested path parameters with auto-validation"""

    return JSONResponse({
        "user_id": user_id,
        "post_id": post_id,
        "post": {
            "id": post_id,
            "title": f"Post {post_id} by User {user_id}",
            "content": "This is a sample post content...",
            "author_id": user_id
        }
    })

# Health check endpoint
@app.get("/health")
def health_check(request: Request) -> Response:
    """Health check endpoint"""
    return JSONResponse({
        "status": "healthy",
        "timestamp": "2025-01-14T10:00:00Z",
        "version": "0.2.0",
        "router": "C-Accelerated"
    })

if __name__ == "__main__":
    print("🚀 Starting Catzilla Basic Routing Example")
    print("📝 Available endpoints:")
    print("   GET  /                           - Home page")
    print("   GET  /users/{user_id}           - Get user by ID")
    print("   GET  /search?q=term&limit=10    - Search with query params")
    print("   POST /users                     - Create user")
    print("   PUT  /users/{user_id}           - Update user")
    print("   DELETE /users/{user_id}         - Delete user")
    print("   GET  /api/v1/users/{user_id}/posts/{post_id} - Get user post")
    print("   GET  /health                    - Health check")
    print("\n⚡ C-Accelerated routing active!")
    print("🌐 Server will start on http://localhost:8000")

    app.listen(port=8000, host="0.0.0.0")
