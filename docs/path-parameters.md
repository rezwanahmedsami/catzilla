# Path Parameters

## Overview

Catzilla provides a simple and efficient path parameter extraction system using the `{param}` syntax. When you define routes with path parameters, Catzilla automatically extracts the values and makes them available in your request handlers through `request.path_params`.

## Basic Usage

### Simple Path Parameters

Define path parameters using curly braces:

```python
from catzilla import App

app = App()

@app.get("/users/{user_id}")
def get_user(request):
    user_id = request.path_params["user_id"]
    return {"user_id": user_id}

@app.get("/posts/{post_id}/comments/{comment_id}")
def get_comment(request):
    post_id = request.path_params["post_id"]
    comment_id = request.path_params["comment_id"]
    return {
        "post_id": post_id,
        "comment_id": comment_id
    }
```

### Multiple Parameters

Extract multiple parameters from a single route:

```python
@app.get("/api/v1/users/{user_id}/posts/{post_id}/comments/{comment_id}")
def get_nested_comment(request):
    params = request.path_params
    return {
        "user_id": params["user_id"],
        "post_id": params["post_id"],
        "comment_id": params["comment_id"]
    }
```

### Safe Parameter Access

Use `.get()` method for safe parameter access with defaults:

```python
@app.get("/users/{user_id}")
def get_user(request):
    # Safe access with default value
    user_id = request.path_params.get("user_id", "unknown")
    return {"user_id": user_id}
```

## RouterGroup Integration

### RouterGroup Parameters

Path parameters work seamlessly with RouterGroups:

```python
from catzilla import App, RouterGroup

app = App()

# Create API group
api = RouterGroup(prefix="/api/v1")

# Create users group with parameters
users = RouterGroup(prefix="/users")

@users.get("/{user_id}")
def get_user(request):
    user_id = request.path_params["user_id"]
    return {"user_id": user_id}

@users.get("/{user_id}/profile")
def get_user_profile(request):
    user_id = request.path_params["user_id"]
    return {"user_id": user_id, "profile": "details"}

# Include groups
api.include_group(users)
app.include_routes(api)

# This creates routes like:
# GET /api/v1/users/{user_id}
# GET /api/v1/users/{user_id}/profile
```

### Nested RouterGroups with Parameters

RouterGroups can be nested while preserving parameter extraction:

```python
# Blog API example
blog_api = RouterGroup(prefix="/blog")

# Posts group
posts_group = RouterGroup(prefix="/posts")

@posts_group.get("/{post_id}")
def get_post(request):
    post_id = request.path_params["post_id"]
    return {"post_id": post_id}

@posts_group.get("/{post_id}/comments")
def get_post_comments(request):
    post_id = request.path_params["post_id"]
    return {"post_id": post_id, "comments": []}

@posts_group.get("/{post_id}/comments/{comment_id}")
def get_comment(request):
    post_id = request.path_params["post_id"]
    comment_id = request.path_params["comment_id"]
    return {"post_id": post_id, "comment_id": comment_id}

# Include nested groups
blog_api.include_group(posts_group)
app.include_routes(blog_api)

# Creates routes like:
# GET /blog/posts/{post_id}
# GET /blog/posts/{post_id}/comments
# GET /blog/posts/{post_id}/comments/{comment_id}
```

## Parameter Types and Validation

### String Parameters (Default)

All path parameters are extracted as strings by default:

```python
@app.get("/items/{item_id}")
def get_item(request):
    item_id = request.path_params["item_id"]  # Always a string
    # Convert to int if needed
    try:
        item_id_int = int(item_id)
        return {"item_id": item_id_int, "type": "integer"}
    except ValueError:
        return {"error": "Invalid item ID"}, 400
```

### Manual Type Conversion

Convert parameters manually in your handlers:

```python
@app.get("/users/{user_id}")
def get_user(request):
    user_id_str = request.path_params["user_id"]

    # Validate and convert
    try:
        user_id = int(user_id_str)
        if user_id <= 0:
            return {"error": "User ID must be positive"}, 400
    except ValueError:
        return {"error": "Invalid user ID format"}, 400

    return {"user_id": user_id}

@app.get("/products/{price}")
def get_products_by_price(request):
    price_str = request.path_params["price"]

    try:
        price = float(price_str)
        return {"price": price, "currency": "USD"}
    except ValueError:
        return {"error": "Invalid price format"}, 400
```

### Special Characters in Parameters

Parameters can contain various characters:

```python
@app.get("/files/{filename}")
def get_file(request):
    filename = request.path_params["filename"]
    # filename can contain dots, hyphens, underscores
    # e.g., "document.pdf", "my-file_v2.txt"
    return {"filename": filename}
```

## Error Handling

### Missing Parameters

Handle cases where expected parameters might be missing:

```python
@app.get("/users/{user_id}")
def get_user(request):
    user_id = request.path_params.get("user_id")
    if not user_id:
        return {"error": "User ID is required"}, 400

    return {"user_id": user_id}
```

### Invalid Parameter Values

Validate parameter values and provide helpful error messages:

```python
@app.get("/users/{user_id}")
def get_user(request):
    user_id_str = request.path_params.get("user_id", "")

    # Validate numeric ID
    if not user_id_str.isdigit():
        return {"error": "User ID must be a number"}, 400

    user_id = int(user_id_str)
    if user_id <= 0:
        return {"error": "User ID must be positive"}, 400

    return {"user_id": user_id}
```

## Real-World Examples

### RESTful API with Nested Resources

```python
from catzilla import App, RouterGroup

app = App()

# Create main API group
api = RouterGroup(prefix="/api/v1")

# User management
users_group = RouterGroup(prefix="/users")

@users_group.get("/{user_id}")
def get_user(request):
    user_id = request.path_params["user_id"]
    return {"user_id": user_id, "type": "user"}

@users_group.get("/{user_id}/posts")
def get_user_posts(request):
    user_id = request.path_params["user_id"]
    return {"user_id": user_id, "posts": []}

# Post management
posts_group = RouterGroup(prefix="/posts")

@posts_group.get("/{post_id}")
def get_post(request):
    post_id = request.path_params["post_id"]
    return {"post_id": post_id, "type": "post"}

@posts_group.get("/{post_id}/comments/{comment_id}")
def get_comment(request):
    post_id = request.path_params["post_id"]
    comment_id = request.path_params["comment_id"]
    return {"post_id": post_id, "comment_id": comment_id}

# Include groups
api.include_group(users_group)
api.include_group(posts_group)
app.include_routes(api)

# This creates routes like:
# GET /api/v1/users/{user_id}
# GET /api/v1/users/{user_id}/posts
# GET /api/v1/posts/{post_id}
# GET /api/v1/posts/{post_id}/comments/{comment_id}
```

### Blog API Example

```python
# Complete blog API with path parameters
blog_api = RouterGroup(prefix="/blog")

# Authors
authors_group = RouterGroup(prefix="/authors")

@authors_group.get("/{author_id}")
def get_author(request):
    author_id = request.path_params["author_id"]
    return {"author_id": author_id, "name": "John Doe"}

@authors_group.get("/{author_id}/posts")
def get_author_posts(request):
    author_id = request.path_params["author_id"]
    return {"author_id": author_id, "posts": []}

# Categories
categories_group = RouterGroup(prefix="/categories")

@categories_group.get("/{category_id}")
def get_category(request):
    category_id = request.path_params["category_id"]
    return {"category_id": category_id, "name": "Technology"}

@categories_group.get("/{category_id}/posts")
def get_category_posts(request):
    category_id = request.path_params["category_id"]
    return {"category_id": category_id, "posts": []}

# Posts with complex parameters
posts_group = RouterGroup(prefix="/posts")

@posts_group.get("/{post_id}")
def get_post(request):
    post_id = request.path_params["post_id"]
    return {"post_id": post_id, "title": "Sample Post"}

@posts_group.get("/{post_id}/comments")
def get_post_comments(request):
    post_id = request.path_params["post_id"]
    return {"post_id": post_id, "comments": []}

@posts_group.get("/{post_id}/comments/{comment_id}")
def get_comment(request):
    post_id = request.path_params["post_id"]
    comment_id = request.path_params["comment_id"]
    return {
        "post_id": post_id,
        "comment_id": comment_id,
        "text": "Great post!"
    }

# Include all groups
blog_api.include_group(authors_group)
blog_api.include_group(categories_group)
blog_api.include_group(posts_group)
app.include_routes(blog_api)
```

## Best Practices

### Parameter Naming

Use clear, descriptive parameter names:

```python
# Good
@app.get("/users/{user_id}/posts/{post_id}")

# Less clear
@app.get("/users/{id}/posts/{pid}")
```

### Validation and Error Handling

Always validate parameters and handle errors gracefully:

```python
@app.get("/users/{user_id}")
def get_user(request):
    user_id_str = request.path_params.get("user_id", "")

    # Validate input
    if not user_id_str:
        return {"error": "User ID is required"}, 400

    if not user_id_str.isdigit():
        return {"error": "User ID must be a number"}, 400

    user_id = int(user_id_str)
    if user_id <= 0:
        return {"error": "User ID must be positive"}, 400

    # Proceed with valid user_id
    return {"user_id": user_id}
```

### Safe Parameter Access

Always use `.get()` method for safe parameter access:

```python
# Good - safe access with default
user_id = request.path_params.get("user_id", "unknown")

# Risky - may raise KeyError
user_id = request.path_params["user_id"]
```

### RouterGroup Organization

Organize related routes into logical groups:

```python
# Organize by resource type
users_routes = RouterGroup(prefix="/users")
posts_routes = RouterGroup(prefix="/posts")
comments_routes = RouterGroup(prefix="/comments")

# Or by API version
api_v1 = RouterGroup(prefix="/api/v1")
api_v2 = RouterGroup(prefix="/api/v2")
```

Path parameters in Catzilla provide a powerful and efficient way to build RESTful APIs with clean, readable URLs and fast parameter extraction.
