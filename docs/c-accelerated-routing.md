# C-Accelerated Routing

## Overview

Catzilla includes a C-accelerated routing system that provides fast route matching and path parameter extraction. When you use Catzilla in your Python applications, the routing system automatically benefits from C acceleration for better performance.

## Basic Usage

### Route Registration

Define routes normally using the `App` class. The C acceleration works transparently:

```python
from catzilla import App

app = App()

@app.get("/users/{user_id}")
def get_user(request):
    # Path parameters are extracted by C code and available here
    user_id = request.path_params["user_id"]
    return {"user_id": user_id}

@app.get("/users/{user_id}/posts/{post_id}")
def get_user_post(request):
    # Multiple parameters work seamlessly
    user_id = request.path_params["user_id"]
    post_id = request.path_params["post_id"]
    return {"user_id": user_id, "post_id": post_id}
```

### Complex Parameter Patterns

The C router handles complex nested parameter patterns efficiently:

```python
@app.get("/api/v1/companies/{company_id}/departments/{dept_id}/employees/{emp_id}")
def get_employee(request):
    # All parameters extracted by C router
    params = request.path_params
    return {
        "company_id": params["company_id"],
        "dept_id": params["dept_id"],
        "emp_id": params["emp_id"]
    }
```

## RouterGroup Integration

RouterGroups also benefit from C acceleration:

```python
from catzilla import App, RouterGroup

app = App()

# Create RouterGroup for API v1
api_v1 = RouterGroup(prefix="/api/v1")

@api_v1.get("/users/{user_id}")
def get_user(request):
    user_id = request.path_params["user_id"]
    return {"user_id": user_id}

@api_v1.post("/users/{user_id}/posts")
def create_user_post(request):
    user_id = request.path_params["user_id"]
    # Create new post for user
    return {"created_for_user": user_id}

# Include routes - C acceleration applies to all routes
app.include_routes(api_v1)
```

## Performance Benefits

The C-accelerated routing system provides:

- **Fast Route Matching**: Routes are matched using optimized C code
- **Efficient Parameter Extraction**: Path parameters are extracted in C and made available to Python handlers
- **Scalable Performance**: Performance scales well with large numbers of routes
- **Memory Efficiency**: Optimized memory usage for route storage and matching

## Best Practices

### Route Design for Performance

Design your routes to take advantage of C acceleration:

```python
# Good: Clear parameter patterns
@app.get("/users/{user_id}")
@app.get("/posts/{post_id}/comments/{comment_id}")
def handler(request):
    # Parameters available immediately
    return request.path_params

# Avoid: Overly complex nesting (though still supported)
@app.get("/a/{p1}/b/{p2}/c/{p3}/d/{p4}/e/{p5}")
def complex_handler(request):
    # Works but simpler patterns perform better
    return request.path_params
```

### RouterGroup Organization

Organize routes with RouterGroups for better structure:

```python
# Users API
users_api = RouterGroup(prefix="/users")

@users_api.get("/{user_id}")
def get_user(request):
    return {"user_id": request.path_params["user_id"]}

@users_api.get("/{user_id}/profile")
def get_user_profile(request):
    return {"user_id": request.path_params["user_id"]}

# Posts API
posts_api = RouterGroup(prefix="/posts")

@posts_api.get("/{post_id}")
def get_post(request):
    return {"post_id": request.path_params["post_id"]}

# Main API group
api = RouterGroup(prefix="/api/v1")
api.include_group(users_api)
api.include_group(posts_api)

app.include_routes(api)
```

## How It Works

When you make a request to your Catzilla application:

1. **Route Matching**: The C router quickly finds the matching route pattern
2. **Parameter Extraction**: Path parameters are extracted by C code
3. **Python Handler**: Your Python handler receives the request with populated `path_params`

This happens transparently - you don't need to do anything special to use C acceleration. It's automatically available when you install Catzilla.
