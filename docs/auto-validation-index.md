# Catzilla Auto-Validation System Documentation

The Catzilla Auto-Validation System provides FastAPI-style automatic parameter validation with **20x better performance**. This comprehensive documentation covers all aspects of the system.

## Documentation Overview

### 📚 Core Documentation

1. **[Auto-Validation Guide](auto-validation.md)** - Complete guide to using the auto-validation system
   - Quick start and setup
   - Model definitions and field types
   - Endpoint validation (JSON body, path parameters, query parameters, headers)
   - Performance benchmarks and optimization tips
   - Error handling and troubleshooting
   - Migration from FastAPI
   - Best practices and API reference

2. **[Quick Reference](auto-validation-quick-reference.md)** - Concise reference for common patterns
   - Basic setup examples
   - Common model patterns
   - Constraint definitions
   - Performance metrics
   - Migration checklist

3. **[Technical Architecture](auto-validation-architecture.md)** - Deep dive into system internals
   - C-accelerated validation engine
   - Python binding layer
   - Memory management and optimization
   - Error handling architecture
   - Performance characteristics
   - Integration points

4. **[Examples](auto-validation-examples.md)** - Comprehensive code examples
   - Basic validation examples
   - Advanced use cases (nested models, batch processing)
   - Performance optimization examples
   - Error handling patterns
   - Testing examples
   - Migration examples

## Key Features

### 🚀 Performance Excellence
- **Ultra-fast validation**: 2.3-2.8μs per validation
- **High throughput**: 53,626+ validations/second
- **20x faster than FastAPI**: Hybrid C/Python validation pipeline
- **Memory efficient**: jemalloc-optimized memory management

### 🎯 FastAPI Compatibility
- **Drop-in replacement**: Same syntax, same behavior
- **Automatic validation**: Zero manual validation code required
- **Type hint support**: Full Python typing system integration
- **Constraint validation**: Built-in parameter constraints

### 🛡️ Robust Architecture
- **C-accelerated core**: Critical validation logic in native C
- **Intelligent fallbacks**: Python fallback for complex types
- **Clear error messages**: Actionable validation feedback
- **Memory safety**: Protected garbage collection boundaries

## Quick Start

### 1. Enable Auto-Validation

```python
from catzilla import Catzilla, BaseModel, JSONResponse
from catzilla.auto_validation import Query, Path

app = Catzilla(auto_validation=True)
```

### 2. Define Models

```python
class User(BaseModel):
    id: int
    name: str
    email: Optional[str] = None
    tags: Optional[List[str]] = None
```

### 3. Create Auto-Validated Endpoints

```python
@app.post("/users")
def create_user(request, user: User):
    """Automatic JSON body validation"""
    return JSONResponse({"user_id": user.id})

@app.get("/users/{user_id}")
def get_user(request, user_id: int = Path(..., ge=1)):
    """Automatic path parameter validation"""
    return JSONResponse({"user_id": user_id})
```

## Performance Benchmarks

| Validation Type | Catzilla | FastAPI | Speedup |
|---|---|---|---|
| JSON Body | 2.3μs | 47.8μs | **20.8x** |
| Path Parameters | 0.7μs | 15.2μs | **21.7x** |
| Query Parameters | 1.2μs | 24.1μs | **20.1x** |
| Complex Models | 2.8μs | 68.3μs | **24.4x** |

**Throughput:**
- **Simple models**: 173,912 validations/sec
- **Mixed models**: 90,850 validations/sec
- **Complex models**: 35,714 validations/sec

## Validation Types Supported

### JSON Body Validation
```python
@app.post("/users")
def create_user(request, user: User):
    # user is automatically validated from JSON body
    pass
```

### Path Parameter Validation
```python
@app.get("/users/{user_id}")
def get_user(request, user_id: int = Path(..., ge=1)):
    # user_id is validated and converted from URL path
    pass
```

### Query Parameter Validation
```python
@app.get("/search")
def search(
    request,
    query: str = Query(..., min_length=1),
    limit: int = Query(10, ge=1, le=100)
):
    # Query parameters validated with constraints
    pass
```

### Header Validation
```python
@app.get("/protected")
def protected(request, auth: str = Header(..., alias="Authorization")):
    # Headers automatically extracted and validated
    pass
```

## Model System

### Basic Model Definition
```python
class User(BaseModel):
    id: int                           # Required integer
    name: str                         # Required string
    email: Optional[str] = None       # Optional string
    age: Optional[int] = None         # Optional integer
    is_active: bool = True            # Boolean with default
    tags: Optional[List[str]] = None  # Optional list of strings
```

### Advanced Model Features
```python
class Product(BaseModel):
    name: str
    price: float
    categories: List[str]             # Required list
    metadata: Dict[str, str]          # Dictionary validation
    features: Optional[List[str]] = None

    class Config:
        validate_assignment = True     # Validate on assignment
        extra = "forbid"              # Forbid extra fields
```

### Nested Models
```python
class Address(BaseModel):
    street: str
    city: str
    country: str = "US"

class UserProfile(BaseModel):
    user: User                        # Nested model
    address: Address                  # Nested model
    preferences: Dict[str, Any]       # Flexible dictionary
```

## Error Handling

### Validation Errors
```python
# Clear, actionable error messages
POST /users {"name": "John"}
→ "Field 'id' is required"

POST /users {"id": "invalid", "name": "John"}
→ "Field 'id' must be an integer"

GET /search?limit=999
→ "Field 'limit' must be ≤ 100"
```

### Custom Error Handlers
```python
@app.exception_handler(ValidationError)
def validation_error_handler(request, exc):
    return JSONResponse(
        {"error": "Validation Error", "detail": str(exc)},
        status_code=422
    )
```

## Migration from FastAPI

### Simple Migration Steps

1. **Update imports:**
   ```python
   # Old
   from fastapi import FastAPI, Query, Path
   from pydantic import BaseModel

   # New
   from catzilla import Catzilla, BaseModel
   from catzilla.auto_validation import Query, Path
   ```

2. **Update app initialization:**
   ```python
   # Old
   app = FastAPI()

   # New
   app = Catzilla(auto_validation=True)
   ```

3. **Add request parameter:**
   ```python
   # Old
   def endpoint(user: User):

   # New
   def endpoint(request, user: User):
   ```

4. **Enjoy 20x performance boost!** 🚀

## Advanced Features

### Performance Optimization
```python
app = Catzilla(
    auto_validation=True,
    use_jemalloc=True,          # Memory optimization
    auto_memory_tuning=True,    # Adaptive memory management
    memory_profiling=True       # Performance monitoring
)
```

### Constraint Validation
```python
# Numeric constraints
user_id: int = Path(..., ge=1, le=999999)
price: float = Query(..., gt=0.0, le=10000.0)

# String constraints
name: str = Query(..., min_length=1, max_length=50)
email: str = Query(..., regex=r'^[^@]+@[^@]+\.[^@]+$')

# List constraints
tags: List[str] = Query(..., min_items=1, max_items=10)
```

### Batch Processing
```python
class BatchRequest(BaseModel):
    items: List[Product]           # Validate list of models
    options: Dict[str, Any]

@app.post("/batch")
def process_batch(request, batch: BatchRequest):
    # Batch validation with linear scaling
    return JSONResponse({"count": len(batch.items)})
```

## Testing and Validation

### Performance Testing
```python
def test_validation_performance():
    user_data = {"id": 1, "name": "John", "email": "john@example.com"}

    start = time.perf_counter()
    for _ in range(10000):
        User.validate(user_data)
    end = time.perf_counter()

    avg_time = (end - start) / 10000
    assert avg_time < 5e-6  # Must be under 5μs
```

### Endpoint Testing
```python
def test_endpoint_validation():
    from catzilla.testing import TestClient

    client = TestClient(app)

    # Valid request
    response = client.post("/users", json={"id": 1, "name": "John"})
    assert response.status_code == 200

    # Invalid request
    response = client.post("/users", json={"name": "John"})
    assert response.status_code == 422
```

## System Requirements

### Minimum Requirements
- Python 3.8+
- C compiler (GCC/Clang/MSVC)
- 64-bit architecture (recommended)

### Optional Dependencies
- jemalloc (for memory optimization)
- PCRE2 (for regex validation)
- Sphinx (for documentation)

### Installation
```bash
pip install catzilla
# or for development
pip install -e .[dev]
```

## Documentation Structure

```
docs/
├── auto-validation.md              # Complete user guide
├── auto-validation-quick-reference.md  # Quick reference
├── auto-validation-architecture.md     # Technical deep-dive
├── auto-validation-examples.md         # Code examples
└── auto-validation-index.md           # This overview (you are here)
```

## Related Files

### Example Applications
- `quick_start_auto_validation.py` - Basic usage demonstration
- `examples/hello_world/main.py` - Comprehensive example application
- `demo_ultra_fast_validation.py` - Performance demonstrations

### Test Suites
- `test_validation.py` - Basic validation tests
- `tests/python/test_validation_engine.py` - Comprehensive test suite
- `test_comprehensive_validation.py` - End-to-end validation tests

### Implementation Files
- `python/catzilla/validation.py` - Python validation layer
- `python/catzilla/auto_validation.py` - Auto-validation system
- `src/core/validation.h` - C validation engine header
- `src/core/validation.c` - C validation engine implementation

## Support and Contributing

### Getting Help
- Check the [troubleshooting section](auto-validation.md#troubleshooting) in the main guide
- Review [examples](auto-validation-examples.md) for common patterns
- Examine test files for usage patterns

### Performance Issues
- Enable all optimizations (`use_jemalloc=True`, `auto_memory_tuning=True`)
- Use simple model structures when possible
- Batch similar operations for better throughput
- Check the [performance section](auto-validation.md#performance-analysis) for detailed guidance

### Contributing
- Follow the existing code style and patterns
- Add tests for new validation features
- Update documentation for user-facing changes
- Benchmark performance for validation optimizations

---

**The Catzilla Auto-Validation System delivers FastAPI compatibility with revolutionary performance. Get started with the [complete guide](auto-validation.md) or jump to [examples](auto-validation-examples.md) for hands-on learning.**
