# Auto-Validation Examples

This document provides comprehensive examples of Catzilla's auto-validation system, demonstrating all features and use cases.

## Basic Examples

### Simple Model Validation

```python
from catzilla import Catzilla, BaseModel, JSONResponse
from typing import Optional

app = Catzilla(auto_validation=True)

class User(BaseModel):
    id: int
    name: str
    email: Optional[str] = None
    age: Optional[int] = None

@app.post("/users")
def create_user(request, user: User):
    """Automatic JSON body validation"""
    return JSONResponse({
        "success": True,
        "user_id": user.id,
        "name": user.name,
        "validation_time": "~2.3μs"
    })

# Test requests:
# POST /users {"id": 1, "name": "John Doe", "email": "john@example.com"}
# → Success: Creates user with all fields
#
# POST /users {"id": 1, "name": "Jane"}
# → Success: Creates user with optional fields as None
#
# POST /users {"name": "Bob"}
# → Error: "Field 'id' is required"
```

### Path Parameter Validation

```python
from catzilla.auto_validation import Path

@app.get("/users/{user_id}")
def get_user(request, user_id: int = Path(..., description="User ID", ge=1)):
    """Path parameter with constraints"""
    return JSONResponse({
        "user_id": user_id,
        "message": f"Retrieved user {user_id}",
        "validation_time": "~0.7μs"
    })

@app.get("/products/{product_id}/reviews/{review_id}")
def get_review(
    request,
    product_id: int = Path(..., ge=1, description="Product ID"),
    review_id: int = Path(..., ge=1, le=999999, description="Review ID")
):
    """Multiple path parameters with different constraints"""
    return JSONResponse({
        "product_id": product_id,
        "review_id": review_id,
        "validation_time": "~1.1μs"
    })

# Test requests:
# GET /users/123 → Success: user_id=123
# GET /users/0 → Error: "user_id must be >= 1"
# GET /users/abc → Error: "invalid literal for int()"
```

### Query Parameter Validation

```python
from catzilla.auto_validation import Query

@app.get("/search")
def search(
    request,
    query: str = Query(..., description="Search query", min_length=1),
    limit: int = Query(10, ge=1, le=100, description="Results limit"),
    offset: int = Query(0, ge=0, description="Results offset"),
    category: Optional[str] = Query("all", description="Search category"),
    include_inactive: bool = Query(False, description="Include inactive items")
):
    """Complex query parameter validation"""
    return JSONResponse({
        "search_params": {
            "query": query,
            "limit": limit,
            "offset": offset,
            "category": category,
            "include_inactive": include_inactive
        },
        "validation_time": "~1.5μs"
    })

# Test requests:
# GET /search?query=python&limit=20&offset=10
# → Success: All parameters validated and converted
#
# GET /search?query=&limit=5
# → Error: "query must have minimum length 1"
#
# GET /search?query=test&limit=150
# → Error: "limit must be <= 100"
```

## Advanced Examples

### Complex Model with Nested Validation

```python
from typing import List, Dict

class Address(BaseModel):
    street: str
    city: str
    state: str
    postal_code: str
    country: str = "US"

class ContactInfo(BaseModel):
    email: str
    phone: Optional[str] = None
    address: Optional[Address] = None

class UserProfile(BaseModel):
    user_id: int
    username: str
    contact: ContactInfo
    preferences: Dict[str, str]
    tags: List[str]
    is_verified: bool = False
    created_at: Optional[str] = None

@app.post("/profiles")
def create_profile(request, profile: UserProfile):
    """Nested model validation with complex types"""
    return JSONResponse({
        "profile_id": profile.user_id,
        "username": profile.username,
        "contact_email": profile.contact.email,
        "tags_count": len(profile.tags),
        "validation_time": "~4.2μs"
    })

# Test request:
# POST /profiles
# {
#     "user_id": 1,
#     "username": "johndoe",
#     "contact": {
#         "email": "john@example.com",
#         "phone": "+1-555-0123",
#         "address": {
#             "street": "123 Main St",
#             "city": "Boston",
#             "state": "MA",
#             "postal_code": "02101"
#         }
#     },
#     "preferences": {"theme": "dark", "language": "en"},
#     "tags": ["developer", "python", "api"]
# }
```

### List and Array Validation

```python
class Product(BaseModel):
    name: str
    categories: List[str]
    prices: List[float]
    features: Optional[List[str]] = None
    metadata: Dict[str, str]

@app.post("/products")
def create_product(request, product: Product):
    """List and dictionary validation"""
    return JSONResponse({
        "product_name": product.name,
        "categories_count": len(product.categories),
        "average_price": sum(product.prices) / len(product.prices),
        "features_count": len(product.features) if product.features else 0,
        "validation_time": "~3.1μs"
    })

class BatchRequest(BaseModel):
    items: List[Product]
    batch_id: str
    process_async: bool = False

@app.post("/products/batch")
def create_products_batch(request, batch: BatchRequest):
    """Batch validation with list of models"""
    return JSONResponse({
        "batch_id": batch.batch_id,
        "items_count": len(batch.items),
        "process_async": batch.process_async,
        "validation_time": f"~{len(batch.items) * 3.1:.1f}μs"
    })

# Test request:
# POST /products/batch
# {
#     "batch_id": "batch_001",
#     "process_async": true,
#     "items": [
#         {
#             "name": "Widget A",
#             "categories": ["tools", "hardware"],
#             "prices": [19.99, 24.99, 22.50],
#             "metadata": {"color": "red", "size": "medium"}
#         },
#         {
#             "name": "Widget B",
#             "categories": ["tools"],
#             "prices": [15.99],
#             "features": ["waterproof", "durable"],
#             "metadata": {"color": "blue"}
#         }
#     ]
# }
```

### Header and Authentication Validation

```python
from catzilla.auto_validation import Header

class AuthToken(BaseModel):
    token: str
    expires_at: Optional[str] = None

@app.get("/protected")
def protected_endpoint(
    request,
    authorization: str = Header(..., alias="Authorization", description="Bearer token"),
    user_agent: Optional[str] = Header(None, alias="User-Agent"),
    api_version: str = Header("v1", alias="X-API-Version")
):
    """Header validation with aliases"""
    # Extract token from Authorization header
    if not authorization.startswith("Bearer "):
        raise ValidationError("Authorization header must start with 'Bearer '")

    token = authorization[7:]  # Remove "Bearer " prefix

    return JSONResponse({
        "token_length": len(token),
        "user_agent": user_agent,
        "api_version": api_version,
        "validation_time": "~0.9μs"
    })

@app.post("/auth/login")
def login(
    request,
    credentials: AuthToken,
    x_forwarded_for: Optional[str] = Header(None, alias="X-Forwarded-For"),
    x_real_ip: Optional[str] = Header(None, alias="X-Real-IP")
):
    """Combined body and header validation"""
    return JSONResponse({
        "token_provided": bool(credentials.token),
        "client_ip": x_forwarded_for or x_real_ip or "unknown",
        "validation_time": "~2.8μs"
    })

# Test request:
# GET /protected
# Headers:
#   Authorization: Bearer abc123xyz789
#   User-Agent: Mozilla/5.0 (...)
#   X-API-Version: v2
```

### Form Data Validation

```python
from catzilla.auto_validation import Form

class ContactForm(BaseModel):
    name: str
    email: str
    subject: str
    message: str
    newsletter: bool = False

@app.post("/contact")
def submit_contact_form(
    request,
    form_data: ContactForm = Form(...),
    csrf_token: str = Form(..., alias="csrf_token")
):
    """Form data validation (when implemented)"""
    # Note: Form data validation is planned for future release
    return JSONResponse({
        "message": "Contact form submitted",
        "name": form_data.name,
        "subject": form_data.subject,
        "validation_time": "~2.5μs"
    })
```

### Custom Validation Logic

```python
import re
from datetime import datetime

class CustomUser(BaseModel):
    username: str
    email: str
    password: str
    age: int
    birth_date: Optional[str] = None

    def __post_init__(self):
        """Custom validation after auto-validation"""
        # Username validation
        if not re.match(r'^[a-zA-Z0-9_]{3,20}$', self.username):
            raise ValidationError("Username must be 3-20 alphanumeric characters or underscores")

        # Email validation
        if not re.match(r'^[^@]+@[^@]+\.[^@]+$', self.email):
            raise ValidationError("Invalid email format")

        # Password strength validation
        if len(self.password) < 8:
            raise ValidationError("Password must be at least 8 characters")

        # Age validation
        if self.age < 13:
            raise ValidationError("User must be at least 13 years old")

        # Birth date validation
        if self.birth_date:
            try:
                birth_dt = datetime.fromisoformat(self.birth_date.replace('Z', '+00:00'))
                today = datetime.now()
                calculated_age = (today - birth_dt).days // 365
                if abs(calculated_age - self.age) > 1:
                    raise ValidationError("Age doesn't match birth date")
            except ValueError:
                raise ValidationError("Invalid birth date format (use ISO 8601)")

@app.post("/register")
def register_user(request, user: CustomUser):
    """Registration with custom validation"""
    return JSONResponse({
        "message": f"User {user.username} registered successfully",
        "validation_time": "~3.5μs"
    })
```

## Performance Examples

### High-Throughput Validation

```python
class SimpleModel(BaseModel):
    """Optimized for maximum validation speed"""
    id: int
    name: str
    value: float

@app.post("/high-speed")
def high_speed_endpoint(request, data: SimpleModel):
    """Optimized for minimal validation overhead"""
    return JSONResponse({
        "id": data.id,
        "validation_time": "~1.1μs"  # Fastest possible validation
    })

class MixedModel(BaseModel):
    """Balanced model with optional fields"""
    id: int
    name: str
    description: Optional[str] = None
    tags: Optional[List[str]] = None
    metadata: Optional[Dict[str, str]] = None

@app.post("/balanced")
def balanced_endpoint(request, data: MixedModel):
    """Balanced performance with flexibility"""
    return JSONResponse({
        "id": data.id,
        "has_description": data.description is not None,
        "tags_count": len(data.tags) if data.tags else 0,
        "validation_time": "~2.3μs"
    })
```

### Batch Processing Examples

```python
class BatchItem(BaseModel):
    id: int
    data: str
    timestamp: Optional[str] = None

class BatchRequest(BaseModel):
    batch_id: str
    items: List[BatchItem]
    options: Dict[str, Any]

@app.post("/batch/process")
def process_batch(request, batch: BatchRequest):
    """High-performance batch validation"""
    item_count = len(batch.items)
    estimated_time = item_count * 1.2  # μs per item

    return JSONResponse({
        "batch_id": batch.batch_id,
        "items_processed": item_count,
        "validation_time": f"~{estimated_time:.1f}μs",
        "throughput": f"{item_count / (estimated_time / 1_000_000):.0f} items/sec"
    })

# Performance benchmark endpoint
@app.get("/benchmark/validation")
def benchmark_validation(request):
    """Validation performance benchmark"""
    import time

    # Simple model benchmark
    simple_data = {"id": 1, "name": "test", "value": 42.0}
    start = time.perf_counter()
    for _ in range(1000):
        SimpleModel.validate(simple_data)
    simple_time = (time.perf_counter() - start) / 1000

    # Complex model benchmark
    complex_data = {
        "id": 1,
        "name": "test",
        "description": "A test item",
        "tags": ["tag1", "tag2", "tag3"],
        "metadata": {"key1": "value1", "key2": "value2"}
    }
    start = time.perf_counter()
    for _ in range(1000):
        MixedModel.validate(complex_data)
    complex_time = (time.perf_counter() - start) / 1000

    return JSONResponse({
        "benchmark_results": {
            "simple_model_μs": f"{simple_time * 1_000_000:.2f}",
            "complex_model_μs": f"{complex_time * 1_000_000:.2f}",
            "simple_throughput_per_sec": f"{1 / simple_time:.0f}",
            "complex_throughput_per_sec": f"{1 / complex_time:.0f}"
        }
    })
```

## Error Handling Examples

### Comprehensive Error Handling

```python
@app.exception_handler(ValidationError)
def validation_error_handler(request, exc):
    """Custom validation error handler"""
    return JSONResponse(
        {
            "error": "Validation Error",
            "message": str(exc),
            "type": "validation_error",
            "timestamp": time.time(),
            "path": request.url.path
        },
        status_code=422
    )

@app.post("/users/strict")
def create_user_strict(request, user: User):
    """Endpoint with additional validation"""
    try:
        # Additional business logic validation
        if user.age and user.age < 18:
            raise ValidationError("User must be 18 or older")

        if user.email and not user.email.endswith(('@company.com', '@partner.com')):
            raise ValidationError("Email must be from approved domains")

        return JSONResponse({
            "user_id": user.id,
            "message": "User created successfully"
        })

    except ValidationError:
        # Re-raise validation errors to be handled by exception handler
        raise
    except Exception as e:
        # Handle unexpected errors
        return JSONResponse(
            {"error": "Internal error", "detail": str(e)},
            status_code=500
        )
```

### Validation Error Details

```python
class DetailedUser(BaseModel):
    id: int
    username: str
    email: str
    age: int
    preferences: Dict[str, str]
    tags: List[str]

@app.post("/users/detailed")
def create_detailed_user(request, user: DetailedUser):
    """Endpoint that demonstrates detailed error messages"""
    return JSONResponse({
        "user_id": user.id,
        "username": user.username
    })

# Example error responses:
#
# POST /users/detailed {}
# → {
#     "error": "Validation Error",
#     "message": "Field 'id' is required",
#     "type": "validation_error"
#   }
#
# POST /users/detailed {"id": "abc", "username": "test"}
# → {
#     "error": "Validation Error",
#     "message": "Field 'id' must be an integer",
#     "type": "validation_error"
#   }
#
# POST /users/detailed {"id": 1, "username": "test", "email": "invalid", "age": 25, "preferences": {}, "tags": [123]}
# → {
#     "error": "Validation Error",
#     "message": "List items in 'tags' must be strings",
#     "type": "validation_error"
#   }
```

## Migration Examples

### FastAPI to Catzilla Migration

```python
# Original FastAPI code
"""
from fastapi import FastAPI, Query, Path, Header
from pydantic import BaseModel
from typing import Optional, List

app = FastAPI()

class User(BaseModel):
    id: int
    name: str
    email: Optional[str] = None

@app.post("/users")
def create_user(user: User):
    return {"user_id": user.id}

@app.get("/users/{user_id}")
def get_user(user_id: int = Path(..., ge=1)):
    return {"user_id": user_id}

@app.get("/search")
def search(query: str = Query(...), limit: int = Query(10, ge=1, le=100)):
    return {"query": query, "limit": limit}
"""

# Migrated Catzilla code
from catzilla import Catzilla, BaseModel, JSONResponse
from catzilla.auto_validation import Query, Path, Header
from typing import Optional, List

app = Catzilla(auto_validation=True)  # Enable auto-validation

class User(BaseModel):  # Same model definition
    id: int
    name: str
    email: Optional[str] = None

@app.post("/users")
def create_user(request, user: User):  # Added 'request' parameter
    return JSONResponse({"user_id": user.id})  # Use JSONResponse

@app.get("/users/{user_id}")
def get_user(request, user_id: int = Path(..., ge=1)):  # Added 'request'
    return JSONResponse({"user_id": user_id})

@app.get("/search")
def search(request, query: str = Query(...), limit: int = Query(10, ge=1, le=100)):
    return JSONResponse({"query": query, "limit": limit})

# Result: 20x faster validation with identical functionality!
```

## Testing Examples

### Validation Testing

```python
import pytest
from catzilla.validation import ValidationError

def test_user_validation():
    """Test user model validation"""
    # Valid user data
    valid_data = {"id": 1, "name": "John Doe", "email": "john@example.com"}
    user = User.validate(valid_data)
    assert user.id == 1
    assert user.name == "John Doe"
    assert user.email == "john@example.com"

    # Missing required field
    with pytest.raises(ValidationError, match="Field 'id' is required"):
        User.validate({"name": "John"})

    # Invalid type
    with pytest.raises(ValidationError, match="must be an integer"):
        User.validate({"id": "invalid", "name": "John"})

def test_performance_requirements():
    """Test that validation meets performance requirements"""
    import time

    user_data = {"id": 1, "name": "John", "email": "john@example.com"}

    # Warm up
    for _ in range(100):
        User.validate(user_data)

    # Measure validation time
    start = time.perf_counter()
    for _ in range(1000):
        User.validate(user_data)
    end = time.perf_counter()

    avg_time = (end - start) / 1000
    assert avg_time < 5e-6, f"Validation too slow: {avg_time*1e6:.2f}μs (should be <5μs)"

def test_endpoint_validation():
    """Test endpoint auto-validation"""
    from catzilla.testing import TestClient

    client = TestClient(app)

    # Valid request
    response = client.post("/users", json={"id": 1, "name": "John"})
    assert response.status_code == 200
    assert response.json()["user_id"] == 1

    # Invalid request - missing field
    response = client.post("/users", json={"name": "John"})
    assert response.status_code == 422
    assert "required" in response.json()["message"].lower()

    # Invalid request - wrong type
    response = client.post("/users", json={"id": "invalid", "name": "John"})
    assert response.status_code == 422
    assert "integer" in response.json()["message"].lower()
```

These examples demonstrate the full range of Catzilla's auto-validation capabilities, from simple field validation to complex nested models, performance optimization, and error handling. The system provides FastAPI-compatible syntax with significantly better performance.
