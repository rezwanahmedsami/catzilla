# RouterGroup Examples

This directory contains comprehensive examples demonstrating the RouterGroup system in Catzilla.

## Examples

### 1. Simple Blog API (`simple_blog.py`)

A beginner-friendly example showing basic RouterGroup usage with a blog API.

**Features demonstrated:**
- Basic RouterGroup creation and nesting
- HTTP method decorators (`@get`, `@post`, `@put`, `@delete`)
- Path parameters with type hints
- Nested routing for comments under posts

**Run the example:**
```bash
python examples/router_groups/simple_blog.py
```

**Test endpoints:**
```bash
# Home page
curl http://localhost:8000/

# Get all posts
curl http://localhost:8000/api/v1/posts

# Get specific post
curl http://localhost:8000/api/v1/posts/1

# Get comments for a post
curl http://localhost:8000/api/v1/posts/1/comments

# Create a new post
curl -X POST http://localhost:8000/api/v1/posts \
  -H "Content-Type: application/json" \
  -d '{"title": "New Post", "content": "This is a new post"}'
```

### 2. Main RouterGroup Example (`main.py`)

A more detailed example showing RouterGroup organization with multiple groups and metadata.

**Features demonstrated:**
- Multiple RouterGroups with different prefixes
- Path parameters and extraction
- Tags and metadata for organization
- Route grouping by functionality
- Integration with the main App

**Run the example:**
```bash
python examples/router_groups/main.py
```

**Test the routes:**
```bash
# Home page with RouterGroup demo
curl http://localhost:8000/

# API status
curl http://localhost:8000/api/v1/status

# Users list
curl http://localhost:8000/api/v1/users

# Specific user
curl http://localhost:8000/api/v1/users/123

# Admin dashboard
curl http://localhost:8000/admin/dashboard
```

## Key RouterGroup Features

### 1. Hierarchical Organization

```python
# Create nested structure
api = RouterGroup(prefix="/api/v1")
users = RouterGroup(prefix="/users")
posts = RouterGroup(prefix="/posts")

# Include groups
api.include_group(users)
api.include_group(posts)
app.include_routes(api)

# Creates organized route structure
```

### 2. Parameter Extraction

```python
# Router with parameter
users = RouterGroup(prefix="/users/{user_id}")

# Access parameters via request.path_params
@users.get("/posts/{post_id}")
def get_user_post(request):
    user_id = request.path_params["user_id"]
    post_id = request.path_params["post_id"]
    return {"user_id": user_id, "post_id": post_id}
```

### 3. HTTP Method Decorators

```python
router = RouterGroup(prefix="/api")

@router.get("/items")           # GET /api/items
@router.post("/items")          # POST /api/items
@router.put("/items/{id}")      # PUT /api/items/{id}
@router.delete("/items/{id}")   # DELETE /api/items/{id}
@router.patch("/items/{id}")    # PATCH /api/items/{id}
```

### 4. Manual Type Conversion

```python
@router.get("/users/{user_id}")
def get_user(request):
    user_id_str = request.path_params["user_id"]
    # Manual conversion with error handling
    try:
        user_id = int(user_id_str)
        return {"user_id": user_id}
    except ValueError:
        return {"error": "Invalid user ID"}, 400
```

### 5. Path Parameters

```python
# Simple parameter
@router.get("/files/{filename}")

# Path parameter (can contain slashes)
@router.get("/files/{file_path:path}")

# Multiple parameters
@router.get("/orgs/{org_id}/teams/{team_id}/members/{member_id}")
```

## Performance Benefits

The RouterGroup system benefits from Catzilla's C-accelerated routing:

- **Fast route matching** with C-accelerated engine
- **Efficient parameter extraction** for nested routes
- **Optimized memory usage** for route organization
- **Scalable architecture** that performs well with many routes

## Best Practices

### 1. Keep Nesting Reasonable

```python
# Good: Reasonable nesting (≤ 4 levels)
/api/v1/users/{user_id}/posts/{post_id}/comments/{comment_id}

# Avoid: Too deep nesting (> 6 levels)
/api/v1/orgs/{org}/teams/{team}/projects/{proj}/tasks/{task}/subtasks/{sub}/items/{item}
```

### 2. Use Clear Parameter Handling

```python
# Good: Clear parameter extraction
def get_user(request):
    user_id = request.path_params["user_id"]
    # Handle user_id as string, convert if needed

# Less clear: Assumptions about types
def get_user(request):
    user_id = request.path_params["user_id"]
    # Unclear what type user_id is
```

### 3. Organize by Domain

```python
# Good: Organized by feature/domain
auth = RouterGroup(prefix="/auth")
users = RouterGroup(prefix="/users")
posts = RouterGroup(prefix="/posts")

# Less clear: Mixed responsibilities
misc = RouterGroup(prefix="/api")  # Everything goes here
```

### 4. Use Descriptive Prefixes

```python
# Good: Clear intent
api_v1 = RouterGroup(prefix="/api/v1")
admin = RouterGroup(prefix="/admin")

# Less clear: Vague names
group1 = RouterGroup(prefix="/g1")
stuff = RouterGroup(prefix="/stuff")
```

## Migration from Direct Routes

### Before (Direct Routes)

```python
@app.get("/api/v1/users/{user_id}")
@app.get("/api/v1/users/{user_id}/posts")
@app.get("/api/v1/users/{user_id}/posts/{post_id}")
@app.get("/api/v1/posts")
@app.get("/api/v1/posts/{post_id}")
```

### After (RouterGroups)

```python
api = RouterGroup(prefix="/api/v1")

users = RouterGroup(prefix="/users/{user_id}")
@users.get("/")
@users.get("/posts")
@users.get("/posts/{post_id}")

posts = RouterGroup(prefix="/posts")
@posts.get("/")
@posts.get("/{post_id}")

api.include_router(users)
api.include_router(posts)
app.include_router(api)
```

## Next Steps

1. **Read the Documentation**: Check `docs/router-groups.md` for comprehensive RouterGroup documentation
2. **Try the Examples**: Run both examples to see RouterGroups in action
3. **Build Your API**: Use RouterGroups to organize your own API routes
4. **Check Performance**: Use `docs/performance.md` to understand the performance benefits

## Related Documentation

- [`docs/router-groups.md`](../../docs/router-groups.md) - Complete RouterGroup documentation
- [`docs/path-parameters.md`](../../docs/path-parameters.md) - Advanced path parameter handling
- [`docs/c-accelerated-routing.md`](../../docs/c-accelerated-routing.md) - C acceleration details
- [`docs/performance.md`](../../docs/performance.md) - Performance benchmarks
