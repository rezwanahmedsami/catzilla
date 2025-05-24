# RouterGroup System

## Overview

RouterGroup allows you to organize your routes into logical groups with shared URL prefixes. This is perfect for building APIs where you want to group related endpoints together, like all user-related routes under `/users` or all API routes under `/api/v1`.

## Quick Start

```python
from catzilla import App, RouterGroup, JSONResponse

# Create your app
app = App()

# Create a router group for user-related routes
users = RouterGroup(prefix="/users")

@users.get("/")
def list_users(request):
    return JSONResponse({"users": ["alice", "bob"]})

@users.get("/{user_id}")
def get_user(request):
    user_id = request.path_params["user_id"]
    return JSONResponse({"user": f"User {user_id}"})

# Add the group to your app
app.include_routes(users)

if __name__ == "__main__":
    app.listen(8000)
```

This creates:
- `GET /users/` - List all users
- `GET /users/123` - Get user with ID 123

## Creating RouterGroups

### Basic RouterGroup

```python
# Simple group with just a prefix
api_group = RouterGroup(prefix="/api")

@api_group.get("/status")
def api_status(request):
    return JSONResponse({"status": "ok"})
```

### RouterGroup with Metadata

```python
# Group with tags and description for better organization
admin_group = RouterGroup(
    prefix="/admin",
    tags=["admin", "management"],
    description="Administrative endpoints"
)

@admin_group.get("/stats")
def admin_stats(request):
    return JSONResponse({"total_users": 42})
```

## HTTP Methods

RouterGroup supports all standard HTTP methods:

```python
posts = RouterGroup(prefix="/posts")

@posts.get("/")
def list_posts(request):
    return JSONResponse({"posts": []})

@posts.post("/")
def create_post(request):
    return JSONResponse({"message": "Post created"})

@posts.put("/{post_id}")
def update_post(request):
    post_id = request.path_params["post_id"]
    return JSONResponse({"message": f"Post {post_id} updated"})

@posts.delete("/{post_id}")
def delete_post(request):
    post_id = request.path_params["post_id"]
    return JSONResponse({"message": f"Post {post_id} deleted"})

@posts.patch("/{post_id}")
def patch_post(request):
    post_id = request.path_params["post_id"]
    return JSONResponse({"message": f"Post {post_id} patched"})
```

```python
admin_group = RouterGroup(
    prefix="/admin",
    tags=["admin", "management"],
    description="Administrative endpoints",
    # Custom metadata
    auth_required=True,
    rate_limit="100/hour",
    version="1.0"
)

@admin_group.get("/stats")
def admin_stats(request):
    return JSONResponse({"stats": "data"})
```

## Path Parameters

RouterGroups work seamlessly with path parameters:

```python
# Single parameter
users = RouterGroup(prefix="/users")

@users.get("/{user_id}")
def get_user(request):
    user_id = request.path_params["user_id"]
    return JSONResponse({"user_id": user_id})

# Multiple parameters
@users.get("/{user_id}/posts/{post_id}")
def get_user_post(request):
    user_id = request.path_params["user_id"]
    post_id = request.path_params["post_id"]
    return JSONResponse({
        "user_id": user_id,
        "post_id": post_id
    })

app.include_routes(users)
```

## Real-World Example

Here's how to build a complete blog API using RouterGroups:

```python
from catzilla import App, RouterGroup, JSONResponse

app = App()

# Authentication routes
auth = RouterGroup(prefix="/auth")

@auth.post("/login")
def login(request):
    # Your login logic here
    return JSONResponse({"token": "your-jwt-token"})

@auth.post("/logout")
def logout(request):
    return JSONResponse({"message": "Logged out"})

# Blog posts API
posts = RouterGroup(prefix="/posts")

@posts.get("/")
def list_posts(request):
    return JSONResponse({
        "posts": [
            {"id": 1, "title": "Hello World"},
            {"id": 2, "title": "Getting Started with Catzilla"}
        ]
    })

@posts.get("/{post_id}")
def get_post(request):
    post_id = request.path_params["post_id"]
    return JSONResponse({
        "id": post_id,
        "title": f"Post {post_id}",
        "content": "This is the post content..."
    })

@posts.post("/")
def create_post(request):
    # Your post creation logic here
    return JSONResponse({"message": "Post created", "id": 123})

# User management API
users = RouterGroup(prefix="/users")

@users.get("/")
def list_users(request):
    return JSONResponse({"users": ["alice", "bob", "charlie"]})

@users.get("/{user_id}")
def get_user(request):
    user_id = request.path_params["user_id"]
    return JSONResponse({
        "id": user_id,
        "name": f"User {user_id}",
        "email": f"user{user_id}@example.com"
    })

# Include all groups in your app
app.include_routes(auth)
app.include_routes(posts)
app.include_routes(users)

# Health check endpoint (not in any group)
@app.get("/health")
def health_check(request):
    return JSONResponse({"status": "healthy"})

if __name__ == "__main__":
    print("Starting blog API server...")
    app.listen(8000)
```
This creates a complete API with these endpoints:

**Authentication:**
- `POST /auth/login` - User login
- `POST /auth/logout` - User logout

**Blog Posts:**
- `GET /posts/` - List all posts
- `GET /posts/123` - Get specific post
- `POST /posts/` - Create new post

**Users:**
- `GET /users/` - List all users
- `GET /users/456` - Get specific user

**Health:**
- `GET /health` - Health check

## Best Practices

### 1. Group Related Routes

```python
# Good: Group by feature
users_api = RouterGroup(prefix="/users")
posts_api = RouterGroup(prefix="/posts")
auth_api = RouterGroup(prefix="/auth")

# Avoid: Everything in one place
@app.get("/users")  # Direct on app
@app.get("/posts")  # Direct on app
@app.get("/login")  # Direct on app
```

### 2. Use Clear Prefixes

```python
# Good: Clear, descriptive prefixes
api_v1 = RouterGroup(prefix="/api/v1")
admin = RouterGroup(prefix="/admin")

# Avoid: Unclear prefixes
stuff = RouterGroup(prefix="/xyz")  # What does xyz mean?
```

### 3. Add Metadata for Documentation

```python
# Use tags and descriptions to organize your API
api = RouterGroup(
    prefix="/api/v1",
    tags=["api", "v1"],
    description="Version 1 of our REST API"
)
```

## API Reference

### RouterGroup Constructor

```python
RouterGroup(
    prefix="",              # URL prefix (e.g., "/api/v1")
    tags=None,              # List of tags for organization
    description="",         # Description of this group
    **kwargs               # Additional metadata
)
```

### Methods

- `get(path)` - Register GET route
- `post(path)` - Register POST route
- `put(path)` - Register PUT route
- `delete(path)` - Register DELETE route
- `patch(path)` - Register PATCH route
- `routes()` - Get all routes in this group

### Including in Your App

```python
app = App()
my_group = RouterGroup(prefix="/api")

# Add routes to group...

# Include the group in your app
app.include_routes(my_group)
```

RouterGroups make it easy to organize your Catzilla application into logical sections while keeping your code clean and maintainable.
