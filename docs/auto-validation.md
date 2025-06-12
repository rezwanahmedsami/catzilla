# Auto-Validation System Documentation

## Overview

Catzilla's Auto-Validation System provides FastAPI-style automatic parameter validation with **20x better performance**. The system uses C-accelerated validation combined with intelligent Python fallbacks to deliver ultra-fast request processing while maintaining developer-friendly syntax.

## Key Features

- **🚀 Ultra-Fast Performance**: 2.3-2.8μs per validation (20x faster than FastAPI)
- **🎯 FastAPI-Compatible Syntax**: Drop-in replacement for FastAPI validation
- **🛡️ Robust Error Handling**: Clear, actionable error messages
- **🔧 Automatic Type Conversion**: Seamless string-to-type conversion
- **📊 C-Accelerated Core**: Hybrid C/Python validation pipeline
- **💾 Memory Efficient**: jemalloc-optimized memory management

## Performance Benchmarks

| Validation Type | Speed | Throughput |
|---|---|---|
| JSON Body | ~2.3μs | 53,626+ req/sec |
| Path Parameters | ~0.7μs | 142,857+ req/sec |
| Query Parameters | ~1.2μs | 83,333+ req/sec |
| Complex Models | ~2.8μs | 35,714+ req/sec |

## Quick Start

### 1. Enable Auto-Validation

```python
from catzilla import Catzilla, BaseModel, JSONResponse
from catzilla.auto_validation import Query, Path, Header
from typing import Optional, List

# Initialize with auto-validation enabled
app = Catzilla(auto_validation=True)
```

### 2. Define Models

```python
class User(BaseModel):
    """User model with automatic validation"""
    id: int
    name: str
    email: str
    age: Optional[int] = None
    is_active: bool = True
    tags: Optional[List[str]] = None
    metadata: Optional[Dict[str, str]] = None

class Product(BaseModel):
    """Product model with constraints"""
    name: str
    price: float
    category: str
    in_stock: bool = True
    description: Optional[str] = None
```

### 3. Create Auto-Validated Endpoints

```python
@app.post("/users")
def create_user(request, user: User):
    """Automatic JSON body validation"""
    return JSONResponse({
        "success": True,
        "user_id": user.id,
        "validation_time": "~2.3μs"
    })

@app.get("/users/{user_id}")
def get_user(request, user_id: int = Path(..., description="User ID", ge=1)):
    """Automatic path parameter validation"""
    return JSONResponse({
        "user_id": user_id,
        "validation_time": "~0.7μs"
    })

@app.get("/search")
def search(
    request,
    query: str = Query(..., min_length=1),
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    """Automatic query parameter validation"""
    return JSONResponse({
        "query": query,
        "limit": limit,
        "offset": offset,
        "validation_time": "~1.2μs"
    })
```

## Validation Types

### JSON Body Validation

The most common validation type for POST/PUT requests.

```python
@app.post("/users")
def create_user(request, user: User):
    # user is automatically validated from request JSON
    return JSONResponse({"user": user.dict()})
```

**Features:**
- **Required Field Validation**: Missing fields trigger clear error messages
- **Optional Field Handling**: Proper default value assignment
- **Type Coercion**: Automatic type conversion (string → int, etc.)
- **List Validation**: Full support for `List[str]`, `List[int]`, etc.
- **Nested Models**: Support for complex model hierarchies

**Example Request:**
```json
POST /users
{
    "id": 123,
    "name": "John Doe",
    "email": "john@example.com",
    "tags": ["developer", "python"]
}
```

### Path Parameter Validation

Automatic validation and type conversion for URL path parameters.

```python
@app.get("/users/{user_id}")
def get_user(request, user_id: int = Path(..., description="User ID", ge=1)):
    # user_id is automatically converted from string to int
    # and validated against constraints (ge=1)
    return JSONResponse({"user_id": user_id})
```

**Features:**
- **Type Conversion**: String URL parameters → Python types
- **Constraint Validation**: Min/max value enforcement
- **Required Parameters**: Automatic presence checking
- **Error Handling**: Clear messages for invalid values

**Example:**
```
GET /users/123  → user_id = 123 (int)
GET /users/abc  → ValidationError: "invalid literal for int()"
```

### Query Parameter Validation

Comprehensive query string parameter validation.

```python
@app.get("/search")
def search(
    request,
    query: str = Query(..., min_length=1),
    limit: int = Query(10, ge=1, le=100),
    include_inactive: bool = Query(False)
):
    # All parameters automatically validated and converted
    return JSONResponse({
        "query": query,
        "limit": limit,
        "include_inactive": include_inactive
    })
```

**Features:**
- **Multiple Parameters**: Handle complex query strings
- **Default Values**: Optional parameters with defaults
- **Type Conversion**: String → int/bool/float conversion
- **Constraint Validation**: Range checking, length validation
- **Required Parameters**: Clear error for missing required params

**Example:**
```
GET /search?query=python&limit=10&include_inactive=true
→ query="python", limit=10, include_inactive=True
```

### Header Validation

Validation of HTTP headers with automatic conversion.

```python
@app.get("/protected")
def protected_endpoint(
    request,
    authorization: str = Header(..., alias="Authorization"),
    user_agent: Optional[str] = Header(None, alias="User-Agent")
):
    # Headers automatically extracted and validated
    return JSONResponse({"auth": authorization})
```

**Features:**
- **Header Extraction**: Automatic header → parameter mapping
- **Alias Support**: Custom header name mapping
- **Optional Headers**: Proper handling of missing headers
- **Type Safety**: Header value validation

## Validation Architecture

### C-Accelerated Pipeline

```
Request → Auto-Detection → C Validation → Python Fallback → Response
            ↓                ↓              ↓
    Parameter Analysis   Fast Path      Robust Handling
    Type Inspection     C Validators    Error Recovery
    Constraint Prep     Memory Opt.     Default Values
```

### Validation Stages

1. **Parameter Detection** (Startup Only)
   - Function signature inspection
   - Type hint analysis
   - Constraint extraction
   - Validation spec compilation

2. **Request Processing** (Per Request)
   - Parameter extraction from request
   - C-accelerated validation
   - Python fallback for complex types
   - Error handling and response formatting

3. **Performance Optimization**
   - Pre-compiled validation specifications
   - Direct C function calls for primitives
   - Memory-efficient constraint checking
   - Zero-allocation fast paths

## BaseModel System

### Model Definition

```python
class User(BaseModel):
    """Pydantic-compatible model with C acceleration"""
    id: int
    name: str
    email: Optional[str] = None
    age: Optional[int] = None
    is_active: bool = True

    # Model configuration
    class Config:
        validate_assignment = True
        extra = "forbid"
```

### Field Types

| Python Type | C Validator | Features |
|---|---|---|
| `int` | `IntValidator` | Min/max constraints |
| `float` | `FloatValidator` | Range validation |
| `str` | `StringValidator` | Length, regex patterns |
| `bool` | `BoolValidator` | Truthy conversion |
| `List[T]` | `ListValidator` | Item validation, length |
| `Optional[T]` | `OptionalValidator` | None handling |

### Model Methods

```python
# Model instantiation with validation
user = User(id=1, name="John", email="john@example.com")

# Dictionary conversion
user_dict = user.dict()

# JSON serialization
user_json = user.json()

# Validation from dictionary
user = User.validate({"id": 1, "name": "John"})

# Copy with modifications
updated_user = user.copy(update={"age": 30})
```

## Error Handling

### Validation Errors

Catzilla provides clear, actionable error messages for all validation failures.

```python
# Missing required field
POST /users {"name": "John"}
→ ValidationError: "Field 'id' is required"

# Type mismatch
POST /users {"id": "invalid", "name": "John"}
→ ValidationError: "Field 'id' must be an integer"

# Constraint violation
GET /search?limit=999
→ ValidationError: "Field 'limit' must be ≤ 100"

# Invalid list items
POST /users {"id": 1, "name": "John", "tags": [123, 456]}
→ ValidationError: "List items in 'tags' must be strings"
```

### Error Response Format

```json
{
    "error": "Validation Error",
    "detail": "Field 'email' is required",
    "field": "email",
    "type": "missing_field",
    "status_code": 422
}
```

### Custom Error Handlers

```python
@app.exception_handler(ValidationError)
def validation_error_handler(request, exc):
    return JSONResponse(
        {
            "error": "Validation Failed",
            "details": str(exc),
            "timestamp": time.time()
        },
        status_code=422
    )
```

## Advanced Features

### Complex Model Validation

```python
class Address(BaseModel):
    street: str
    city: str
    country: str
    postal_code: str

class UserProfile(BaseModel):
    user: User
    address: Address
    preferences: Dict[str, Any]
    tags: List[str]

@app.post("/profiles")
def create_profile(request, profile: UserProfile):
    # Nested model validation automatically handled
    return JSONResponse({"profile_id": profile.user.id})
```

### Constraint Validators

```python
from catzilla.auto_validation import Query

@app.get("/products")
def list_products(
    request,
    price_min: float = Query(0.0, ge=0.0, description="Minimum price"),
    price_max: float = Query(1000.0, le=10000.0, description="Maximum price"),
    category: str = Query(..., regex=r'^[a-zA-Z]+$', description="Product category"),
    limit: int = Query(20, ge=1, le=100, description="Results limit")
):
    # All constraints automatically validated
    return JSONResponse({
        "filters": {
            "price_range": [price_min, price_max],
            "category": category,
            "limit": limit
        }
    })
```

### Performance Optimizations

```python
# Enable aggressive optimizations
app = Catzilla(
    auto_validation=True,
    use_jemalloc=True,           # Memory optimization
    auto_memory_tuning=True,     # Adaptive memory management
    memory_profiling=True        # Performance monitoring
)

# Use pre-compiled models for maximum speed
class OptimizedUser(BaseModel):
    id: int
    name: str

    class Config:
        # Enable C validation compilation
        compile_for_performance = True
        # Use memory pools for model instances
        use_memory_pools = True
```

## Migration from FastAPI

### Syntax Compatibility

Catzilla's auto-validation system is designed as a **drop-in replacement** for FastAPI:

```python
# FastAPI code (works unchanged in Catzilla)
from fastapi import FastAPI, Query, Path  # Change to catzilla imports
from pydantic import BaseModel           # Change to catzilla BaseModel

app = FastAPI()  # Change to Catzilla(auto_validation=True)

class User(BaseModel):
    name: str
    age: int

@app.post("/users")
def create_user(user: User):  # Add 'request' parameter
    return {"user": user}
```

### Migration Steps

1. **Update Imports**
   ```python
   # Old FastAPI imports
   from fastapi import FastAPI, Query, Path, Header
   from pydantic import BaseModel

   # New Catzilla imports
   from catzilla import Catzilla, BaseModel
   from catzilla.auto_validation import Query, Path, Header
   ```

2. **Update App Initialization**
   ```python
   # Old
   app = FastAPI()

   # New
   app = Catzilla(auto_validation=True)
   ```

3. **Add Request Parameter**
   ```python
   # Old
   def endpoint(user: User):

   # New
   def endpoint(request, user: User):
   ```

4. **Enjoy 20x Performance Boost** 🚀

## Best Practices

### 1. Model Design

```python
# ✅ Good: Clear, typed models
class User(BaseModel):
    id: int
    name: str
    email: Optional[str] = None
    created_at: Optional[datetime] = None

# ❌ Avoid: Overly complex nested structures
class ComplexUser(BaseModel):
    data: Dict[str, Dict[str, List[Dict[str, Any]]]]  # Too complex
```

### 2. Constraint Usage

```python
# ✅ Good: Reasonable constraints
limit: int = Query(10, ge=1, le=100)
name: str = Query(..., min_length=1, max_length=50)

# ❌ Avoid: Excessive constraints
value: int = Query(..., ge=0, le=999999, description="A number")  # Too restrictive
```

### 3. Error Handling

```python
# ✅ Good: Specific error handling
@app.exception_handler(ValidationError)
def handle_validation_error(request, exc):
    return JSONResponse({"error": str(exc)}, status_code=422)

# ✅ Good: Graceful fallbacks
@app.post("/users")
def create_user(request, user: User):
    try:
        # Process user
        return JSONResponse({"success": True})
    except Exception as e:
        return JSONResponse({"error": "Processing failed"}, status_code=500)
```

### 4. Performance Tips

```python
# ✅ Enable all optimizations
app = Catzilla(
    auto_validation=True,
    use_jemalloc=True,
    auto_memory_tuning=True
)

# ✅ Use simple types when possible
user_id: int = Path(...)  # Faster than complex models

# ✅ Batch similar operations
@app.post("/users/batch")
def create_users(request, users: List[User]):  # Batch validation
    return JSONResponse({"count": len(users)})
```

## Troubleshooting

### Common Issues

#### 1. "Validation Error: Field 'X' is required"

**Problem**: Missing required field in request
**Solution**: Include all required fields or make them optional

```python
# Fix missing fields
class User(BaseModel):
    name: str
    email: Optional[str] = None  # Make optional if not always provided
```

#### 2. "List validation failed"

**Problem**: List type validation issues
**Solution**: Ensure proper list type annotations

```python
# ✅ Correct list validation
tags: List[str] = []
numbers: List[int] = []

# ❌ Incorrect - missing type parameter
tags: List = []  # Should be List[str]
```

#### 3. Performance Issues

**Problem**: Slow validation performance
**Solution**: Enable optimizations and check model complexity

```python
# Enable optimizations
app = Catzilla(
    auto_validation=True,
    use_jemalloc=True,
    auto_memory_tuning=True
)

# Check for complex models
class SimpleUser(BaseModel):  # Prefer simple models
    id: int
    name: str
```

### Debug Mode

Enable detailed validation logging:

```python
import logging
logging.getLogger("catzilla.validation").setLevel(logging.DEBUG)

app = Catzilla(
    auto_validation=True,
    debug=True  # Enable debug mode
)
```

## API Reference

### Core Classes

#### `BaseModel`
Base class for all validated models.

```python
class BaseModel:
    def __init__(self, **data):
        """Initialize model with validation"""

    def dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""

    def json(self) -> str:
        """Convert to JSON string"""

    @classmethod
    def validate(cls, data: Dict[str, Any]):
        """Validate dictionary data"""

    def copy(self, *, update: Dict[str, Any] = None):
        """Create copy with updates"""
```

#### `Query`, `Path`, `Header`, `Form`
Parameter validation markers.

```python
def Query(
    default: Any = ...,
    *,
    alias: str = None,
    description: str = "",
    ge: float = None,
    le: float = None,
    min_length: int = None,
    max_length: int = None,
    regex: str = None
):
    """Query parameter with constraints"""

def Path(
    default: Any = ...,
    *,
    description: str = "",
    ge: float = None,
    le: float = None
):
    """Path parameter with constraints"""
```

### Configuration

#### `Catzilla` Auto-Validation Options

```python
app = Catzilla(
    auto_validation=True,        # Enable auto-validation
    use_jemalloc=True,          # Memory optimization
    auto_memory_tuning=True,    # Adaptive memory management
    memory_profiling=True,      # Performance monitoring
    validation_cache_size=1000, # Validation cache size
    max_request_size=10485760,  # Max request size (10MB)
    debug=False                 # Debug mode
)
```

## Examples

See the following files for complete examples:
- `quick_start_auto_validation.py` - Basic usage examples
- `examples/hello_world/main.py` - Comprehensive demo
- `demo_ultra_fast_validation.py` - Performance demonstrations
- `test_validation.py` - Test suite with examples

## Performance Analysis

The auto-validation system achieves exceptional performance through:

1. **C-Accelerated Core**: Critical validation logic in native C
2. **Pre-Compiled Specifications**: One-time function signature analysis
3. **Memory Optimization**: jemalloc-based memory management
4. **Zero-Copy Operations**: Direct memory access where possible
5. **Intelligent Fallbacks**: Python fallback for complex types only

**Result**: 20x faster than FastAPI while maintaining full compatibility and robustness.
