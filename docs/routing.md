# Routing

Catzilla provides a simple and flexible routing system that supports all standard HTTP methods.

## Basic Routing

### Route Decorators

Use decorators to define routes:

```python
from catzilla import App

app = App()

@app.get("/hello")
def hello(request):
    return "Hello, World!"

@app.post("/data")
def create_data(request):
    return {"status": "created"}

@app.put("/data/{id}")
def update_data(request):
    return {"status": "updated"}

@app.delete("/data/{id}")
def delete_data(request):
    return {"status": "deleted"}

@app.patch("/data/{id}")
def patch_data(request):
    return {"status": "patched"}
```

### HTTP Methods

Catzilla supports all standard HTTP methods:

- `@app.get()` - GET requests
- `@app.post()` - POST requests
- `@app.put()` - PUT requests
- `@app.delete()` - DELETE requests
- `@app.patch()` - PATCH requests
- `@app.options()` - OPTIONS requests
- `@app.head()` - HEAD requests

## Route Parameters

### Query Parameters

Access query parameters using `request.query_params`:

```python
@app.get("/search")
def search(request):
    query = request.query_params.get("q")
    category = request.query_params.get("category", "all")
    page = int(request.query_params.get("page", "1"))

    return {
        "query": query,
        "category": category,
        "page": page
    }
```

### Path Parameters (Coming Soon)

Path parameter support is planned for future releases:

```python
@app.get("/users/{id}")
def get_user(request, id):
    return {
        "user_id": id,
        "name": f"User {id}"
    }
```

## Response Types

Routes can return different types:

```python
# HTML string (auto-converted to HTMLResponse)
@app.get("/page")
def page(request):
    return "<h1>Welcome</h1>"

# Dictionary (auto-converted to JSONResponse)
@app.get("/api/data")
def get_data(request):
    return {"key": "value"}

# Direct Response objects
@app.get("/custom")
def custom(request):
    return Response(
        body="Custom response",
        status_code=200,
        headers={"X-Custom": "value"}
    )
```

## Route Organization

### Grouping Routes

Organize related routes together:

```python
# User routes
@app.get("/users")
def list_users(request):
    return {"users": [...]}

@app.post("/users")
def create_user(request):
    return {"status": "created"}

@app.get("/users/{id}")
def get_user(request):
    return {"user": {...}}

# Product routes
@app.get("/products")
def list_products(request):
    return {"products": [...]}

@app.post("/products")
def create_product(request):
    return {"status": "created"}
```

### API Versioning

Version your APIs using URL prefixes:

```python
# v1 API
@app.get("/api/v1/users")
def list_users_v1(request):
    return {"version": "1.0", "users": [...]}

# v2 API
@app.get("/api/v2/users")
def list_users_v2(request):
    return {"version": "2.0", "users": [...]}
```

## Error Handling

Handle route errors appropriately:

```python
@app.get("/api/resource/{id}")
def get_resource(request):
    try:
        # Simulate resource lookup
        if request.query_params.get("id") == "404":
            return JSONResponse(
                {"error": "Not found"},
                status_code=404
            )

        return {"data": "Resource data"}

    except ValueError:
        return JSONResponse(
            {"error": "Invalid ID"},
            status_code=400
        )
    except Exception:
        return JSONResponse(
            {"error": "Server error"},
            status_code=500
        )
```

## Best Practices

### 1. RESTful Routes

Follow RESTful conventions:

```python
# Collection routes
@app.get("/api/articles")         # List articles
@app.post("/api/articles")        # Create article

# Individual resource routes
@app.get("/api/articles/{id}")    # Get article
@app.put("/api/articles/{id}")    # Update article
@app.delete("/api/articles/{id}") # Delete article
```

### 2. Route Naming

Use clear, descriptive route names:

```python
# Good
@app.get("/api/users")
@app.get("/api/users/{id}")
@app.get("/api/users/{id}/posts")

# Avoid
@app.get("/api/u")
@app.get("/api/get-user")
@app.get("/api/userPosts")
```

### 3. Response Consistency

Maintain consistent response formats:

```python
# Success response
@app.get("/api/success")
def success(request):
    return {
        "status": "success",
        "data": {...}
    }

# Error response
@app.get("/api/error")
def error(request):
    return JSONResponse({
        "status": "error",
        "message": "Error description"
    }, status_code=400)
```

### 4. Security

Protect sensitive routes:

```python
@app.post("/api/admin")
def admin(request):
    # Check authorization header
    auth = request.headers.get("authorization")
    if not auth:
        return JSONResponse(
            {"error": "Unauthorized"},
            status_code=401
        )

    # Process admin request
    return {"status": "success"}
```

## Starting the Server

Start the server on a specific port:

```python
if __name__ == "__main__":
    app.listen(8080)  # Server will start on port 8080
```
