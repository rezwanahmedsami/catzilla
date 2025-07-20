"""
REST API Patterns Example

This example demonstrates common REST API patterns and best practices
using Catzilla framework.

Features demonstrated:
- CRUD operations with proper HTTP methods
- Resource-based URL design
- Proper HTTP status codes
- Request validation and error handling
- Response formatting and pagination
- Content negotiation
- Resource relationships and nested endpoints
"""

from catzilla import Catzilla, Request, Response, JSONResponse, BaseModel, Query, Path
from typing import Any, Dict, List, Optional, Union
import json
import time
from typing import Any, Dict, List, Optional, Union
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
import uuid
from enum import Enum

# Initialize Catzilla with validation
app = Catzilla(
    production=False,
    show_banner=True,
    log_requests=True
)

# Data models for REST API
class UserStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"

class UserModel(BaseModel):
    """User data model with validation"""
    name: str = "Unknown"
    email: str = "user@example.com"
    age: Optional[int] = None
    status: UserStatus = UserStatus.ACTIVE
    bio: Optional[str] = None
    tags: List[str] = []

class UserUpdateModel(BaseModel):
    """User update model - all fields optional"""
    name: Optional[str] = None
    email: Optional[str] = None
    age: Optional[int] = None
    status: Optional[UserStatus] = None
    bio: Optional[str] = None
    tags: Optional[List[str]] = None

class PostModel(BaseModel):
    """Post data model"""
    title: str = "Untitled"
    content: str = "No content"
    tags: List[str] = []
    published: bool = False

# In-memory database simulation
@dataclass
class User:
    id: str
    name: str
    email: str
    age: Optional[int] = None
    status: UserStatus = UserStatus.ACTIVE
    bio: Optional[str] = None
    tags: List[str] = None
    created_at: datetime = None
    updated_at: datetime = None

    def __post_init__(self):
        if self.tags is None:
            self.tags = []
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.updated_at is None:
            self.updated_at = datetime.now()

@dataclass
class Post:
    id: str
    user_id: str
    title: str
    content: str
    tags: List[str] = None
    published: bool = False
    created_at: datetime = None
    updated_at: datetime = None

    def __post_init__(self):
        if self.tags is None:
            self.tags = []
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.updated_at is None:
            self.updated_at = datetime.now()

# Database storage
users_db: Dict[str, User] = {}
posts_db: Dict[str, Post] = {}

# Utility functions
def serialize_user(user: User) -> Dict[str, Any]:
    """Serialize user for JSON response"""
    return {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "age": user.age,
        "status": user.status.value,
        "bio": user.bio,
        "tags": user.tags,
        "created_at": user.created_at.isoformat(),
        "updated_at": user.updated_at.isoformat()
    }

def serialize_post(post: Post) -> Dict[str, Any]:
    """Serialize post for JSON response"""
    return {
        "id": post.id,
        "user_id": post.user_id,
        "title": post.title,
        "content": post.content,
        "tags": post.tags,
        "published": post.published,
        "created_at": post.created_at.isoformat(),
        "updated_at": post.updated_at.isoformat()
    }

def paginate_results(items: List[Any], page: int = 1, per_page: int = 10) -> Dict[str, Any]:
    """Paginate results with metadata"""
    total = len(items)
    start = (page - 1) * per_page
    end = start + per_page

    return {
        "data": items[start:end],
        "pagination": {
            "page": page,
            "per_page": per_page,
            "total": total,
            "pages": (total + per_page - 1) // per_page,
            "has_next": end < total,
            "has_prev": page > 1
        }
    }

def validate_user_exists(user_id: str) -> User:
    """Validate user exists and return user"""
    if user_id not in users_db:
        raise ValueError(f"User with id '{user_id}' not found")
    return users_db[user_id]

# CORS headers are handled directly in responses
# Catzilla has built-in performance optimizations

@app.get("/")
def home(request) -> Response:
    """API documentation and available endpoints"""
    return JSONResponse({
        "message": "Catzilla REST API Patterns Example",
        "version": "1.0.0",
        "features": [
            "CRUD operations with proper HTTP methods",
            "Resource-based URL design",
            "Proper HTTP status codes",
            "Request validation and error handling",
            "Response formatting and pagination",
            "Content negotiation",
            "Resource relationships and nested endpoints"
        ],
        "endpoints": {
            "users": {
                "list": "GET /api/v1/users",
                "create": "POST /api/v1/users",
                "get": "GET /api/v1/users/{id}",
                "update": "PUT /api/v1/users/{id}",
                "partial_update": "PATCH /api/v1/users/{id}",
                "delete": "DELETE /api/v1/users/{id}",
                "posts": "GET /api/v1/users/{id}/posts"
            },
            "posts": {
                "list": "GET /api/v1/posts",
                "create": "POST /api/v1/posts",
                "get": "GET /api/v1/posts/{id}",
                "update": "PUT /api/v1/posts/{id}",
                "delete": "DELETE /api/v1/posts/{id}"
            }
        },
        "examples": {
            "create_user": {
                "method": "POST",
                "url": "/api/v1/users",
                "body": {
                    "name": "John Doe",
                    "email": "john@example.com",
                    "age": 30,
                    "bio": "Software developer"
                }
            },
            "pagination": "GET /api/v1/users?page=1&per_page=10",
            "filtering": "GET /api/v1/users?status=active&tags=developer"
        }
    })

# OPTIONS handler for CORS preflight (simplified)
@app.options("/api/v1/users")
def handle_cors_users(request) -> Response:
    """Handle CORS preflight for users endpoint"""
    return Response(
        content="",
        status_code=200,
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, PATCH, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type, Authorization",
            "Access-Control-Max-Age": "86400"  # 24 hours
        }
    )

# Users Resource CRUD Operations
@app.get("/api/v1/users")
def list_users(request,
               page: int = Query(1, ge=1, description="Page number"),
               per_page: int = Query(10, ge=1, le=100, description="Items per page"),
               status: Optional[str] = Query(None, description="Filter by status"),
               search: Optional[str] = Query(None, description="Search in name and email"),
               tags: Optional[str] = Query(None, description="Filter by tags (comma-separated)")) -> Response:
    """
    List users with pagination and filtering
    """
    try:
        # Parse tags filter
        tags_filter = tags.split(",") if tags else []

        # Get all users
        all_users = list(users_db.values())

        # Apply filters
        filtered_users = []
        for user in all_users:
            # Status filter
            if status and user.status.value != status:
                continue

            # Tags filter
            if tags_filter and not any(tag in user.tags for tag in tags_filter):
                continue

            # Search filter
            if search and search.lower() not in user.name.lower() and search.lower() not in user.email.lower():
                continue

            filtered_users.append(serialize_user(user))

        # Sort by created_at (newest first)
        filtered_users.sort(key=lambda x: x["created_at"], reverse=True)

        # Paginate results
        paginated = paginate_results(filtered_users, page, per_page)

        return JSONResponse(paginated)

    except ValueError as e:
        return JSONResponse({"error": "Invalid query parameters", "details": str(e)}, status_code=400)
    except Exception as e:
        return JSONResponse({"error": "Internal server error", "details": str(e)}, status_code=500)

@app.post("/api/v1/users")
def create_user(request, user_data: UserModel) -> Response:
    """Create a new user"""
    try:
        # Check if email already exists
        for existing_user in users_db.values():
            if existing_user.email == user_data.email:
                return JSONResponse(
                    {"error": "Email already exists", "field": "email"},
                    status_code=409
                )

        # Create new user
        user_id = str(uuid.uuid4())
        user = User(
            id=user_id,
            name=user_data.name,
            email=user_data.email,
            age=user_data.age,
            status=user_data.status,
            bio=user_data.bio,
            tags=user_data.tags
        )

        users_db[user_id] = user

        return JSONResponse(
            serialize_user(user),
            status_code=201,
            headers={"Location": f"/api/v1/users/{user_id}"}
        )

        # Create new user
        user_id = str(uuid.uuid4())
        user = User(
            id=user_id,
            name=user_data["name"],
            email=user_data["email"],
            age=user_data.get("age"),
            status=UserStatus(user_data.get("status", "active")),
            bio=user_data.get("bio"),
            tags=user_data.get("tags", [])
        )

        users_db[user_id] = user

        return JSONResponse(
            serialize_user(user),
            status_code=201,
            headers={"Location": f"/api/v1/users/{user_id}"}
        )

    except ValueError as e:
        return JSONResponse({"error": "Validation failed", "details": str(e)}, status_code=400)
    except Exception as e:
        return JSONResponse({"error": "Internal server error", "details": str(e)}, status_code=500)

@app.get("/api/v1/users/{user_id}")
def get_user(request, user_id: str = Path(..., description="User ID")) -> Response:
    """Get user by ID"""
    try:
        user = validate_user_exists(user_id)

        return JSONResponse(serialize_user(user))

    except ValueError as e:
        return JSONResponse({"error": str(e)}, status_code=404)
    except Exception as e:
        return JSONResponse({"error": "Internal server error", "details": str(e)}, status_code=500)

@app.put("/api/v1/users/{user_id}")
def update_user(request, user_id: str = Path(..., description="User ID")) -> Response:
    """Update user (full replacement)"""
    try:
        user = validate_user_exists(user_id)

        # Validate request body
        user_data = UserModel.validate(request.json())

        # Check if email already exists (exclude current user)
        for existing_id, existing_user in users_db.items():
            if existing_id != user_id and existing_user.email == user_data.email:
                return JSONResponse(
                    {"error": "Email already exists", "field": "email"},
                    status_code=409
                )

        # Update user
        user.name = user_data.name
        user.email = user_data.email
        user.age = user_data.age
        user.status = user_data.status
        user.bio = user_data.bio
        user.tags = user_data.tags
        user.updated_at = datetime.now()

        return JSONResponse(serialize_user(user))

    except ValueError as e:
        if "not found" in str(e):
            return JSONResponse({"error": str(e)}, status_code=404)
        return JSONResponse({"error": "Validation failed", "details": str(e)}, status_code=400)
    except Exception as e:
        return JSONResponse({"error": "Internal server error", "details": str(e)}, status_code=500)

@app.patch("/api/v1/users/{user_id}")
def partial_update_user(request, user_id: str = Path(..., description="User ID")) -> Response:
    """Partially update user"""
    try:
        user = validate_user_exists(user_id)

        # Validate request body (partial update)
        update_data = UserUpdateModel.validate(request.json())

        # Check email uniqueness if email is being updated
        if update_data.email and update_data.email != user.email:
            for existing_id, existing_user in users_db.items():
                if existing_id != user_id and existing_user.email == update_data.email:
                    return JSONResponse(
                        {"error": "Email already exists", "field": "email"},
                        status_code=409
                    )

        # Apply updates
        if update_data.name is not None:
            user.name = update_data.name
        if update_data.email is not None:
            user.email = update_data.email
        if update_data.age is not None:
            user.age = update_data.age
        if update_data.status is not None:
            user.status = update_data.status
        if update_data.bio is not None:
            user.bio = update_data.bio
        if update_data.tags is not None:
            user.tags = update_data.tags

        user.updated_at = datetime.now()

        return JSONResponse(serialize_user(user))

    except ValueError as e:
        if "not found" in str(e):
            return JSONResponse({"error": str(e)}, status_code=404)
        return JSONResponse({"error": "Validation failed", "details": str(e)}, status_code=400)
    except Exception as e:
        return JSONResponse({"error": "Internal server error", "details": str(e)}, status_code=500)

@app.delete("/api/v1/users/{user_id}")
def delete_user(request, user_id: str = Path(..., description="User ID")) -> Response:
    """Delete user"""
    try:
        user = validate_user_exists(user_id)

        # Delete user's posts first
        user_posts = [post_id for post_id, post in posts_db.items() if post.user_id == user_id]
        for post_id in user_posts:
            del posts_db[post_id]

        # Delete user
        del users_db[user_id]

        return JSONResponse(
            {"message": f"User '{user.name}' and {len(user_posts)} posts deleted successfully"},
            status_code=200
        )

    except ValueError as e:
        return JSONResponse({"error": str(e)}, status_code=404)
    except Exception as e:
        return JSONResponse({"error": "Internal server error", "details": str(e)}, status_code=500)

# Posts Resource CRUD Operations
@app.get("/api/v1/posts")
def list_posts(request,
              page: int = Query(1, ge=1, description="Page number"),
              per_page: int = Query(10, ge=1, le=100, description="Items per page"),
              user_id: str = Query(None, description="Filter by user ID"),
              published: str = Query(None, description="Filter by published status (true/false)"),
              tags: str = Query(None, description="Filter by tags (comma-separated)")) -> Response:
    """List posts with pagination and filtering"""
    try:
        tags_filter = tags.split(",") if tags else []

        # Get all posts
        all_posts = list(posts_db.values())

        # Apply filters
        filtered_posts = []
        for post in all_posts:
            # User filter
            if user_id and post.user_id != user_id:
                continue

            # Published filter
            if published is not None:
                is_published = published.lower() == "true"
                if post.published != is_published:
                    continue

            # Tags filter
            if tags_filter and not any(tag in post.tags for tag in tags_filter):
                continue

            filtered_posts.append(serialize_post(post))

        # Sort by created_at (newest first)
        filtered_posts.sort(key=lambda x: x["created_at"], reverse=True)

        # Paginate results
        paginated = paginate_results(filtered_posts, page, per_page)

        return JSONResponse(paginated)

    except ValueError as e:
        return JSONResponse({"error": "Invalid query parameters", "details": str(e)}, status_code=400)
    except Exception as e:
        return JSONResponse({"error": "Internal server error", "details": str(e)}, status_code=500)

@app.post("/api/v1/posts")
def create_post(request) -> Response:
    """Create a new post"""
    try:
        # Validate request body
        post_data = PostModel.validate(request.json())

        # Get user_id from request body or path
        user_id = request.json().get("user_id")
        if not user_id:
            return JSONResponse({"error": "user_id is required"}, status_code=400)

        # Validate user exists
        validate_user_exists(user_id)

        # Create new post
        post_id = str(uuid.uuid4())
        post = Post(
            id=post_id,
            user_id=user_id,
            title=post_data.title,
            content=post_data.content,
            tags=post_data.tags,
            published=post_data.published
        )

        posts_db[post_id] = post

        return JSONResponse(
            serialize_post(post),
            status_code=201,
            headers={"Location": f"/api/v1/posts/{post_id}"}
        )

    except ValueError as e:
        if "not found" in str(e):
            return JSONResponse({"error": str(e)}, status_code=404)
        return JSONResponse({"error": "Validation failed", "details": str(e)}, status_code=400)
    except Exception as e:
        return JSONResponse({"error": "Internal server error", "details": str(e)}, status_code=500)

@app.get("/api/v1/posts/{post_id}")
def get_post(request, post_id: str = Path(..., description="Post ID")) -> Response:
    """Get post by ID"""
    try:
        if post_id not in posts_db:
            return JSONResponse({"error": f"Post with id '{post_id}' not found"}, status_code=404)

        post = posts_db[post_id]
        return JSONResponse(serialize_post(post))

    except Exception as e:
        return JSONResponse({"error": "Internal server error", "details": str(e)}, status_code=500)

@app.put("/api/v1/posts/{post_id}")
def update_post(request, post_id: str = Path(..., description="Post ID")) -> Response:
    """Update post"""
    try:
        if post_id not in posts_db:
            return JSONResponse({"error": f"Post with id '{post_id}' not found"}, status_code=404)

        post = posts_db[post_id]

        # Validate request body
        post_data = PostModel.validate(request.json())

        # Update post
        post.title = post_data.title
        post.content = post_data.content
        post.tags = post_data.tags
        post.published = post_data.published
        post.updated_at = datetime.now()

        return JSONResponse(serialize_post(post))

    except ValueError as e:
        return JSONResponse({"error": "Validation failed", "details": str(e)}, status_code=400)
    except Exception as e:
        return JSONResponse({"error": "Internal server error", "details": str(e)}, status_code=500)

@app.delete("/api/v1/posts/{post_id}")
def delete_post(request, post_id: str = Path(..., description="Post ID")) -> Response:
    """Delete post"""
    try:
        if post_id not in posts_db:
            return JSONResponse({"error": f"Post with id '{post_id}' not found"}, status_code=404)

        post = posts_db[post_id]
        del posts_db[post_id]

        return JSONResponse({"message": f"Post '{post.title}' deleted successfully"})

    except Exception as e:
        return JSONResponse({"error": "Internal server error", "details": str(e)}, status_code=500)

# Nested resource: User's posts
@app.get("/api/v1/users/{user_id}/posts")
def get_user_posts(request, user_id: str = Path(..., description="User ID"),
                  page: int = Query(1, ge=1, description="Page number"),
                  per_page: int = Query(10, ge=1, le=100, description="Items per page"),
                  published: str = Query(None, description="Filter by published status (true/false)")) -> Response:
    """Get posts for a specific user"""
    try:
        # Validate user exists
        validate_user_exists(user_id)

        # Get user's posts
        user_posts = []
        for post in posts_db.values():
            if post.user_id == user_id:
                # Published filter
                if published is not None:
                    is_published = published.lower() == "true"
                    if post.published != is_published:
                        continue

                user_posts.append(serialize_post(post))

        # Sort by created_at (newest first)
        user_posts.sort(key=lambda x: x["created_at"], reverse=True)

        # Paginate results
        paginated = paginate_results(user_posts, page, per_page)

        return JSONResponse(paginated)

    except ValueError as e:
        if "not found" in str(e):
            return JSONResponse({"error": str(e)}, status_code=404)
        return JSONResponse({"error": "Invalid query parameters", "details": str(e)}, status_code=400)
    except Exception as e:
        return JSONResponse({"error": "Internal server error", "details": str(e)}, status_code=500)

# Health and status endpoints
@app.get("/health")
def health_check(request) -> Response:
    """Health check endpoint"""
    return JSONResponse({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0",
        "data": {
            "users_count": len(users_db),
            "posts_count": len(posts_db)
        }
    })

# Seed some initial data for testing
def seed_data():
    """Seed initial data for testing"""
    # Create sample users
    users = [
        {
            "name": "Alice Johnson",
            "email": "alice@example.com",
            "age": 28,
            "status": UserStatus.ACTIVE,
            "bio": "Full-stack developer with 5+ years experience",
            "tags": ["developer", "python", "javascript"]
        },
        {
            "name": "Bob Smith",
            "email": "bob@example.com",
            "age": 34,
            "status": UserStatus.ACTIVE,
            "bio": "DevOps engineer and cloud architect",
            "tags": ["devops", "aws", "kubernetes"]
        },
        {
            "name": "Charlie Brown",
            "email": "charlie@example.com",
            "age": 25,
            "status": UserStatus.INACTIVE,
            "bio": "Data scientist and ML engineer",
            "tags": ["data-science", "machine-learning", "python"]
        }
    ]

    created_users = []
    for user_data in users:
        user_id = str(uuid.uuid4())
        user = User(id=user_id, **user_data)
        users_db[user_id] = user
        created_users.append(user)

    # Create sample posts
    posts_data = [
        {
            "title": "Introduction to FastAPI and Catzilla",
            "content": "A comprehensive guide to building high-performance APIs...",
            "tags": ["python", "api", "tutorial"],
            "published": True
        },
        {
            "title": "DevOps Best Practices in 2024",
            "content": "Modern approaches to continuous integration and deployment...",
            "tags": ["devops", "ci-cd", "best-practices"],
            "published": True
        },
        {
            "title": "Machine Learning Model Deployment",
            "content": "How to deploy ML models to production environments...",
            "tags": ["ml", "deployment", "production"],
            "published": False
        }
    ]

    for i, post_data in enumerate(posts_data):
        post_id = str(uuid.uuid4())
        post = Post(
            id=post_id,
            user_id=created_users[i % len(created_users)].id,
            **post_data
        )
        posts_db[post_id] = post

if __name__ == "__main__":
    print("🚨 Starting Catzilla REST API Patterns Example")
    print("📝 Available endpoints:")
    print("   GET    /                          - API documentation")
    print("   GET    /api/v1/users              - List users (with pagination)")
    print("   POST   /api/v1/users              - Create user")
    print("   GET    /api/v1/users/{id}         - Get user")
    print("   PUT    /api/v1/users/{id}         - Update user (full)")
    print("   PATCH  /api/v1/users/{id}         - Update user (partial)")
    print("   DELETE /api/v1/users/{id}         - Delete user")
    print("   GET    /api/v1/users/{id}/posts   - Get user's posts")
    print("   GET    /api/v1/posts              - List posts (with pagination)")
    print("   POST   /api/v1/posts              - Create post")
    print("   GET    /api/v1/posts/{id}         - Get post")
    print("   PUT    /api/v1/posts/{id}         - Update post")
    print("   DELETE /api/v1/posts/{id}         - Delete post")
    print("   GET    /health                    - Health check")
    print()
    print("🎨 Features demonstrated:")
    print("   • CRUD operations with proper HTTP methods")
    print("   • Resource-based URL design")
    print("   • Proper HTTP status codes")
    print("   • Request validation and error handling")
    print("   • Response formatting and pagination")
    print("   • Content negotiation")
    print("   • Resource relationships and nested endpoints")
    print()
    print("🧪 Try these examples:")
    print("   # List users with pagination:")
    print("   curl 'http://localhost:8000/api/v1/users?page=1&per_page=5'")
    print()
    print("   # Create a new user:")
    print("   curl -X POST -H 'Content-Type: application/json' \\")
    print("        -d '{\"name\":\"John Doe\",\"email\":\"john@example.com\",\"age\":30}' \\")
    print("        http://localhost:8000/api/v1/users")
    print()
    print("   # Update user partially:")
    print("   curl -X PATCH -H 'Content-Type: application/json' \\")
    print("        -d '{\"bio\":\"Updated bio\"}' \\")
    print("        http://localhost:8000/api/v1/users/{user_id}")
    print()
    print("   # Filter users by status:")
    print("   curl 'http://localhost:8000/api/v1/users?status=active'")
    print()

    # Seed initial data
    seed_data()
    print("🌱 Sample data seeded successfully!")
    print()

    app.listen(host="0.0.0.0", port=8000)
