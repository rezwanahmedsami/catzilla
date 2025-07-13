# 🛣️ Basic Routing

Learn how to create routes with Catzilla's **C-accelerated router** that delivers **O(log n) performance** - up to 10x faster than traditional Python routers.

## Creating Your First Routes

### Simple Routes

```python
from catzilla import Catzilla

app = Catzilla()

@app.get("/")
def root(request):
    return {"message": "Hello, World!"}

@app.get("/hello")
def hello(request):
    return {"greeting": "Hello from Catzilla!"}

@app.post("/users")
def create_user(request):
    return {"action": "user created"}

if __name__ == "__main__":
    app.listen(port=8000)
```

**Performance Note:** 🔥 Catzilla's router uses a **C-implemented trie structure** for O(log n) route matching, compared to O(n) in most Python frameworks.

### HTTP Methods

Catzilla supports all standard HTTP methods:

```python
from catzilla import Catzilla

app = Catzilla()

@app.get("/items")
def get_items(request):
    return {"items": ["item1", "item2"]}

@app.post("/items")
def create_item(request):
    return {"status": "created"}

@app.put("/items/{item_id}")
def update_item(request, item_id: int):
    return {"status": "updated", "item_id": item_id}

@app.delete("/items/{item_id}")
def delete_item(request, item_id: int):
    return {"status": "deleted", "item_id": item_id}

@app.patch("/items/{item_id}")
def patch_item(request, item_id: int):
    return {"status": "patched", "item_id": item_id}

@app.options("/items")
def options_items(request):
    return {"allowed_methods": ["GET", "POST", "PUT", "DELETE", "PATCH"]}
```

## Path Parameters

### Basic Path Parameters

Catzilla automatically extracts and validates path parameters:

```python
from catzilla import Catzilla

app = Catzilla()

@app.get("/users/{user_id}")
def get_user(request, user_id: int):
    return {"user_id": user_id, "name": f"User {user_id}"}

@app.get("/products/{product_id}")
def get_product(request, product_id: str):
    return {"product_id": product_id}

@app.get("/files/{file_path:path}")
def get_file(request, file_path: str):
    # Handles file paths with slashes
    return {"file_path": file_path}
```

### Type Validation

Catzilla automatically validates path parameter types at **C-speed**:

```python
from catzilla import Catzilla

app = Catzilla()

@app.get("/users/{user_id}")
def get_user(request, user_id: int):
    # user_id is guaranteed to be an integer
    return {"user_id": user_id, "next_user": user_id + 1}

@app.get("/products/{product_id}/price/{price}")
def get_product_price(request, product_id: str, price: float):
    # product_id is string, price is guaranteed to be float
    return {
        "product_id": product_id,
        "price": price,
        "discounted_price": price * 0.9
    }

@app.get("/files/{file_path}")
def get_file(request, file_path: str):
    # Handles complex paths
    return {"file_path": file_path}
```

### Advanced Path Parameters

For complex parameter validation, use the Path validator:

```python
from catzilla import Catzilla, Path

app = Catzilla()

@app.get("/users/{user_id}")
def get_user(request, user_id: int = Path(..., ge=1, description="User ID")):
    """Get user by ID with validation"""
    return {"user_id": user_id}

@app.get("/products/{product_code}")
def get_product(request, product_code: str = Path(..., min_length=3, max_length=10)):
    """Get product by code with string validation"""
    return {"product_code": product_code}

@app.get("/posts/{post_id}/comments/{comment_id}")
def get_comment(
    request,
    post_id: int = Path(..., ge=1),
    comment_id: int = Path(..., ge=1)
):
    """Get comment with multiple path parameters"""
    return {
        "post_id": post_id,
        "comment_id": comment_id
    }
```

## Multiple Path Parameters

Handle complex URLs with multiple parameters:

```python
from catzilla import Catzilla

app = Catzilla()

@app.get("/api/v{version}/users/{user_id}/posts/{post_id}")
def get_user_post(request, version: int, user_id: int, post_id: int):
    return {
        "version": version,
        "user_id": user_id,
        "post_id": post_id,
        "post_title": f"Post {post_id} by User {user_id}"
    }

@app.get("/categories/{category}/products/{product_id}")
def get_categorized_product(request, category: str, product_id: int):
    return {
        "category": category,
        "product_id": product_id
    }
```

## Route Organization

### Simple RESTful Routes

```python
from catzilla import Catzilla

app = Catzilla()

# Users resource
@app.get("/users")
def list_users(request):
    return {"users": ["user1", "user2", "user3"]}

@app.get("/users/{user_id}")
def get_user(request, user_id: int):
    return {"user_id": user_id}

@app.post("/users")
def create_user(request):
    return {"status": "created"}

@app.put("/users/{user_id}")
def update_user(request, user_id: int):
    return {"user_id": user_id, "status": "updated"}

@app.delete("/users/{user_id}")
def delete_user(request, user_id: int):
    return {"user_id": user_id, "status": "deleted"}

# Products resource
@app.get("/products")
def list_products(request):
    return {"products": ["product1", "product2"]}

@app.get("/products/{product_id}")
def get_product(request, product_id: int):
    return {"product_id": product_id}
```

### Route Prefixes

Organize routes with common prefixes:

```python
from catzilla import Catzilla

app = Catzilla()

# API versioning
@app.get("/api/v1/users")
def list_users_v1(request):
    return {"version": "v1", "users": []}

@app.get("/api/v2/users")
def list_users_v2(request):
    return {"version": "v2", "users": [], "features": ["advanced"]}

# Admin routes
@app.get("/admin/dashboard")
def admin_dashboard(request):
    return {"page": "admin dashboard"}

@app.get("/admin/users/{user_id}")
def admin_get_user(request, user_id: int):
    return {"admin_view": True, "user_id": user_id}
```

## Performance Features

### Route Matching Performance

Catzilla's C-accelerated router provides superior performance:

```python
from catzilla import Catzilla
import time

app = Catzilla()

@app.get("/benchmark/route-matching")
def benchmark_routing(request):
    """Demonstrate C-speed route matching"""
    start_time = time.time()

    # Route matching happens at C-speed before this function is called
    # This demonstrates the performance after route resolution

    processing_time = (time.time() - start_time) * 1000000  # microseconds

    return {
        "message": "Route matched at C-speed",
        "python_processing_time_us": processing_time,
        "note": "Route matching itself happens in ~0.1μs in C"
    }
```

### Route Caching

Routes are compiled into an optimized C structure for maximum performance:

```python
from catzilla import Catzilla

app = Catzilla()

# During startup, routes are compiled into C structures
# for O(log n) matching performance

@app.get("/api/users/{user_id}")
def cached_route_example(request, user_id: int):
    """This route is pre-compiled for maximum performance"""
    return {
        "user_id": user_id,
        "performance_note": "Route matching: ~0.1μs (C-accelerated)"
    }
```

## Error Handling

### Invalid Path Parameters

Catzilla automatically handles type validation errors:

```python
from catzilla import Catzilla

app = Catzilla()

@app.get("/users/{user_id}")
def get_user_with_validation(request, user_id: int):
    """If user_id is not a valid integer, Catzilla returns 422 automatically"""
    return {"user_id": user_id}

# Test with: GET /users/abc
# Automatic response: {"detail": "Invalid path parameter: user_id must be an integer"}
```

### Route Not Found

```python
from catzilla import Catzilla

app = Catzilla()

@app.get("/existing-route")
def existing_route(request):
    return {"message": "This route exists"}

# Accessing any non-existent route returns:
# Status: 404 Not Found
# Body: {"detail": "Route not found"}
```

## Best Practices

### 1. Use Type Hints

Always use type hints for automatic validation:

```python
# ✅ Good - Type validation at C-speed
@app.get("/users/{user_id}")
def get_user(request, user_id: int):
    return {"user_id": user_id}

# ❌ Avoid - No type validation
@app.get("/items/{item_id}")
def get_item(request, item_id):
    return {"item_id": item_id}
```

### 2. Descriptive Function Names

Use clear, descriptive function names:

```python
# ✅ Good - Clear intent
@app.get("/users/{user_id}")
def get_user_by_id(request, user_id: int):
    return {"user_id": user_id}

@app.post("/users")
def create_new_user(request):
    return {"status": "created"}

# ❌ Avoid - Unclear names
@app.get("/users/{user_id}")
def func1(request, user_id: int):
    return {"user_id": user_id}
```

### 3. Consistent URL Patterns

Follow RESTful conventions:

```python
# ✅ Good - RESTful patterns
@app.get("/users")           # List all users
@app.get("/users/{user_id}") # Get specific user
@app.post("/users")          # Create user
@app.put("/users/{user_id}") # Update user
@app.delete("/users/{user_id}") # Delete user

# ✅ Good - Nested resources
@app.get("/users/{user_id}/posts")         # User's posts
@app.get("/users/{user_id}/posts/{post_id}") # Specific post
```

## Next Steps

- Learn about [Request and Response handling](request-response.md) to work with request data
- Explore [Query Parameters](../validation/index.md) for advanced parameter handling
- Check out [Performance optimization](../performance/index.md) for production tips

---

**Performance Summary:** Catzilla's C-accelerated router provides O(log n) route matching with ~0.1μs latency per route resolution, delivering up to 10x better performance than traditional Python routers.
