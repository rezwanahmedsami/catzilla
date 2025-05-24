#!/usr/bin/env python3
"""
Simple RouterGroup Example for Catzilla

This example demonstrates basic RouterGroup usage with a simple blog API.

Run with: python examples/router_groups/simple_blog.py
"""

from catzilla import App, RouterGroup, JSONResponse


# Initialize the main application
app = App()

# Create the main API RouterGroup
api = RouterGroup(prefix="/api/v1")

# ============================================================================
# Authentication Routes
# ============================================================================

auth = RouterGroup(prefix="/auth")

@auth.post("/login")
def login(request):
    """Login endpoint"""
    return JSONResponse({
        "message": "Login successful",
        "token": "demo_token_12345",
        "user": {"id": 1, "username": "demo_user"}
    })

@auth.post("/logout")
def logout(request):
    """Logout endpoint"""
    return JSONResponse({
        "message": "Logout successful"
    })


# ============================================================================
# Blog Posts Routes
# ============================================================================

posts = RouterGroup(prefix="/posts")

@posts.get("/")
def get_posts(request):
    """Get all blog posts"""
    return JSONResponse({
        "posts": [
            {"id": 1, "title": "First Post", "content": "Hello World!"},
            {"id": 2, "title": "Second Post", "content": "Learning Catzilla"},
            {"id": 3, "title": "Third Post", "content": "RouterGroups are awesome!"}
        ]
    })

@posts.post("/")
def create_post(request):
    """Create a new blog post"""
    return JSONResponse({
        "id": 4,
        "title": "New Blog Post",
        "content": "This is a new post created via API",
        "message": "Post created successfully!"
    })

@posts.get("/{post_id}")
def get_post(request):
    """Get a specific blog post"""
    post_id = request.path_params.get("post_id")
    return JSONResponse({
        "id": post_id,
        "title": f"Blog Post {post_id}",
        "content": "This is the content of the blog post...",
        "author": "John Doe"
    })

@posts.put("/{post_id}")
def update_post(request):
    """Update a blog post"""
    post_id = request.path_params.get("post_id")
    return JSONResponse({
        "id": post_id,
        "title": f"Updated Post {post_id}",
        "message": "Post updated successfully!"
    })

@posts.delete("/{post_id}")
def delete_post(request):
    """Delete a blog post"""
    post_id = request.path_params.get("post_id")
    return JSONResponse({
        "id": post_id,
        "message": f"Post {post_id} deleted successfully!"
    })


# ============================================================================
# Comments Routes (nested under posts)
# ============================================================================

comments = RouterGroup(prefix="/{post_id}/comments")

@comments.get("/")
def get_comments(request):
    """Get all comments for a post"""
    post_id = request.path_params.get("post_id")
    return JSONResponse({
        "post_id": post_id,
        "comments": [
            {"id": 1, "author": "Alice", "content": "Great post!"},
            {"id": 2, "author": "Bob", "content": "Thanks for sharing!"}
        ]
    })

@comments.post("/")
def create_comment(request):
    """Create a comment on a post"""
    post_id = request.path_params.get("post_id")
    return JSONResponse({
        "post_id": post_id,
        "comment": {
            "id": 3,
            "author": "Anonymous",
            "content": "This is a new comment"
        },
        "message": "Comment created successfully!"
    })

@comments.get("/{comment_id}")
def get_comment(request):
    """Get a specific comment"""
    post_id = request.path_params.get("post_id")
    comment_id = request.path_params.get("comment_id")
    return JSONResponse({
        "post_id": post_id,
        "comment": {
            "id": comment_id,
            "author": "Commenter",
            "content": "This is a comment",
            "created_at": "2024-01-15T10:30:00Z"
        }
    })

@comments.delete("/{comment_id}")
def delete_comment(request):
    """Delete a comment"""
    post_id = request.path_params.get("post_id")
    comment_id = request.path_params.get("comment_id")
    return JSONResponse({
        "post_id": post_id,
        "comment_id": comment_id,
        "message": "Comment deleted successfully!"
    })

# Include comments in posts (creates nested routes)
posts.include_group(comments)


# ============================================================================
# Users Routes
# ============================================================================

users = RouterGroup(prefix="/users")

@users.get("/")
def get_users(request):
    """Get all users"""
    return JSONResponse({
        "users": [
            {"id": 1, "name": "John Doe", "email": "john@example.com"},
            {"id": 2, "name": "Jane Smith", "email": "jane@example.com"}
        ]
    })

@users.get("/{user_id}")
def get_user(request):
    """Get a specific user"""
    user_id = request.path_params.get("user_id")
    return JSONResponse({
        "id": user_id,
        "name": f"User {user_id}",
        "email": f"user{user_id}@example.com",
        "joined": "2024-01-01"
    })

@users.get("/{user_id}/posts")
def get_user_posts(request):
    """Get all posts by a user"""
    user_id = request.path_params.get("user_id")
    return JSONResponse({
        "user_id": user_id,
        "posts": [
            {"id": 1, "title": "My First Post"},
            {"id": 2, "title": "Another Post"}
        ]
    })


# ============================================================================
# Include all RouterGroups in the API
# ============================================================================

api.include_group(auth)
api.include_group(posts)
api.include_group(users)

# Include the API in the main app
app.include_routes(api)


# ============================================================================
# Root routes
# ============================================================================

@app.get("/")
def home(request):
    """Home page"""
    return JSONResponse({
        "message": "Welcome to the Simple Blog API!",
        "version": "1.0.0",
        "endpoints": {
            "auth": "/api/v1/auth/login",
            "posts": "/api/v1/posts",
            "users": "/api/v1/users",
            "comments": "/api/v1/posts/{post_id}/comments"
        }
    })

@app.get("/health")
def health_check(request):
    """Health check"""
    return JSONResponse({"status": "healthy", "service": "simple-blog-api"})


if __name__ == "__main__":
    print("🚀 Starting Simple Blog API with RouterGroups")
    print("=" * 45)
    print("Available endpoints:")
    print("  GET    /                                 - Home page")
    print("  GET    /health                           - Health check")
    print("  POST   /api/v1/auth/login                - Login")
    print("  GET    /api/v1/posts                     - Get all posts")
    print("  POST   /api/v1/posts                     - Create post")
    print("  GET    /api/v1/posts/{post_id}           - Get post")
    print("  GET    /api/v1/posts/{post_id}/comments  - Get comments")
    print("  POST   /api/v1/posts/{post_id}/comments  - Create comment")
    print("  GET    /api/v1/users                     - Get all users")
    print("  GET    /api/v1/users/{user_id}           - Get user")
    print("  GET    /api/v1/users/{user_id}/posts     - Get user posts")
    print()
    print("🌐 Server starting on http://localhost:8000")
    print("Try: curl http://localhost:8000/")

    app.listen(8000)
