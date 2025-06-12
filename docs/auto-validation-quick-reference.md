# Auto-Validation Quick Reference

## Basic Setup

```python
from catzilla import Catzilla, BaseModel, JSONResponse
from catzilla.auto_validation import Query, Path, Header
from typing import Optional, List

app = Catzilla(auto_validation=True)
```

## Model Definition

```python
class User(BaseModel):
    id: int
    name: str
    email: Optional[str] = None
    is_active: bool = True
    tags: Optional[List[str]] = None
```

## Endpoint Types

### JSON Body Validation
```python
@app.post("/users")
def create_user(request, user: User):
    return JSONResponse({"user_id": user.id})
```

### Path Parameters
```python
@app.get("/users/{user_id}")
def get_user(request, user_id: int = Path(..., ge=1)):
    return JSONResponse({"user_id": user_id})
```

### Query Parameters
```python
@app.get("/search")
def search(
    request,
    query: str = Query(..., min_length=1),
    limit: int = Query(10, ge=1, le=100)
):
    return JSONResponse({"query": query, "limit": limit})
```

### Headers
```python
@app.get("/protected")
def protected(request, auth: str = Header(..., alias="Authorization")):
    return JSONResponse({"authenticated": True})
```

## Performance Metrics

| Type | Speed | Throughput |
|---|---|---|
| JSON Body | ~2.3μs | 53K+ req/sec |
| Path Params | ~0.7μs | 142K+ req/sec |
| Query Params | ~1.2μs | 83K+ req/sec |

## Common Patterns

### Optional Fields with Defaults
```python
class Product(BaseModel):
    name: str
    price: float
    in_stock: bool = True
    description: Optional[str] = None
```

### Constraints
```python
# Path constraints
user_id: int = Path(..., ge=1, le=999999)

# Query constraints
limit: int = Query(10, ge=1, le=100)
name: str = Query(..., min_length=1, max_length=50)

# String patterns
email: str = Query(..., regex=r'^[^@]+@[^@]+\.[^@]+$')
```

### Complex Types
```python
class Order(BaseModel):
    items: List[str]
    quantities: List[int]
    metadata: Dict[str, str]
    total: float
```

## Error Examples

```python
# Missing required field
{"name": "John"}  # Missing 'id'
→ "Field 'id' is required"

# Type mismatch
{"id": "abc", "name": "John"}
→ "Field 'id' must be an integer"

# Constraint violation
GET /search?limit=999
→ "Field 'limit' must be ≤ 100"
```

## Migration from FastAPI

```python
# FastAPI
from fastapi import FastAPI, Query, Path
from pydantic import BaseModel

app = FastAPI()

# Catzilla
from catzilla import Catzilla, BaseModel
from catzilla.auto_validation import Query, Path

app = Catzilla(auto_validation=True)

# Add 'request' parameter to all endpoints
def endpoint(request, user: User):  # Added 'request'
    pass
```

## Best Practices

✅ **DO:**
- Use simple, clear model definitions
- Add reasonable constraints
- Handle validation errors gracefully
- Enable performance optimizations

❌ **DON'T:**
- Create overly complex nested models
- Add excessive constraints
- Ignore validation errors
- Disable optimizations unnecessarily

## Optimization Settings

```python
app = Catzilla(
    auto_validation=True,        # Enable auto-validation
    use_jemalloc=True,          # Memory optimization
    auto_memory_tuning=True,    # Adaptive memory
    memory_profiling=True       # Performance monitoring
)
```
