# 🔥 Validation Engine API

Catzilla's **100x faster validation engine** with **Pydantic compatibility** and **automatic C compilation**. Experience validation at C speed while maintaining Python's simplicity.

## Core Classes

### BaseModel

```python
from catzilla import BaseModel

class BaseModel:
    """
    Ultra-fast base model with automatic C compilation.

    Features:
    - 100x faster than Pydantic
    - Automatic validation compilation to C
    - Full Pydantic compatibility
    - Zero-copy validation for simple types
    - Type safety with runtime checks
    """
```

### Constructor and Basic Usage

```python
class User(BaseModel):
    id: int
    name: str
    email: Optional[str] = None
    age: Optional[int] = None

# Create instance (validates at C speed)
user = User(id=1, name="Alice", email="alice@example.com")

# Validation happens automatically
try:
    invalid_user = User(id="invalid", name="Bob")  # Raises ValidationError
except ValidationError as e:
    print(f"Validation failed: {e}")
```

## BaseModel Methods

### Core Methods

```python
def __init__(self, **data) -> None:
    """
    Initialize model with automatic C-speed validation.

    Args:
        **data: Field data to validate and assign

    Raises:
        ValidationError: If validation fails
    """

def dict(self, exclude_unset: bool = False) -> dict:
    """
    Convert model to dictionary.

    Args:
        exclude_unset: Exclude fields that weren't explicitly set

    Returns:
        dict: Model data as dictionary
    """

def json(self, exclude_unset: bool = False) -> str:
    """
    Convert model to JSON string using C-accelerated serialization.

    Args:
        exclude_unset: Exclude fields that weren't explicitly set

    Returns:
        str: JSON representation
    """

@classmethod
def parse_obj(cls, obj: dict) -> 'BaseModel':
    """
    Parse object from dictionary with C-speed validation.

    Args:
        obj: Dictionary to parse

    Returns:
        BaseModel: Validated model instance
    """

@classmethod
def parse_raw(cls, data: str) -> 'BaseModel':
    """
    Parse object from JSON string with C-accelerated parsing.

    Args:
        data: JSON string to parse

    Returns:
        BaseModel: Validated model instance
    """

@classmethod
def schema(cls) -> dict:
    """
    Get JSON schema for the model.

    Returns:
        dict: JSON schema definition
    """
```

**Example:**

```python
from catzilla import BaseModel
from typing import Optional, List
import json

class User(BaseModel):
    id: int
    name: str
    email: Optional[str] = None
    tags: List[str] = []

# Create and manipulate models
user = User(id=1, name="Alice", email="alice@example.com", tags=["admin"])

# Convert to dictionary
user_dict = user.dict()
# {'id': 1, 'name': 'Alice', 'email': 'alice@example.com', 'tags': ['admin']}

# Convert to JSON (C-accelerated)
user_json = user.json()
# '{"id": 1, "name": "Alice", "email": "alice@example.com", "tags": ["admin"]}'

# Parse from dictionary (C-speed validation)
user_data = {"id": 2, "name": "Bob", "email": "bob@example.com"}
bob = User.parse_obj(user_data)

# Parse from JSON (C-accelerated parsing + validation)
json_data = '{"id": 3, "name": "Charlie"}'
charlie = User.parse_raw(json_data)

# Get schema
schema = User.schema()
print(json.dumps(schema, indent=2))
```

## Validation Fields

### String Validation

```python
from catzilla import StringField

class StringField:
    """C-accelerated string validation with pattern matching."""

    def __init__(
        self,
        min_len: Optional[int] = None,
        max_len: Optional[int] = None,
        pattern: Optional[str] = None,      # Regex pattern (compiled to C)
        strip_whitespace: bool = True,
        to_lower: bool = False,
        to_upper: bool = False,
        **kwargs
    ) -> None: ...
```

**Example:**

```python
from catzilla import BaseModel, StringField

class UserProfile(BaseModel):
    username: str = StringField(
        min_len=3,
        max_len=20,
        pattern=r'^[a-zA-Z0-9_]+$',    # Alphanumeric + underscore
        strip_whitespace=True
    )

    email: str = StringField(
        pattern=r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$',
        to_lower=True                   # Convert to lowercase
    )

    bio: Optional[str] = StringField(
        max_len=500,
        strip_whitespace=True
    )

# Validation happens at C speed
profile = UserProfile(
    username="alice_123",
    email="  ALICE@EXAMPLE.COM  ",  # Will be lowercased and stripped
    bio="Software developer"
)

print(profile.email)  # "alice@example.com"
```

### Numeric Validation

```python
from catzilla import IntField, FloatField

class IntField:
    """C-accelerated integer validation."""

    def __init__(
        self,
        min: Optional[int] = None,
        max: Optional[int] = None,
        multiple_of: Optional[int] = None,
        **kwargs
    ) -> None: ...

class FloatField:
    """C-accelerated float validation."""

    def __init__(
        self,
        min: Optional[float] = None,
        max: Optional[float] = None,
        multiple_of: Optional[float] = None,
        allow_inf: bool = False,
        allow_nan: bool = False,
        **kwargs
    ) -> None: ...
```

**Example:**

```python
from catzilla import BaseModel, IntField, FloatField

class Product(BaseModel):
    id: int = IntField(min=1)                           # Positive integer
    quantity: int = IntField(min=0, max=10000)          # Stock quantity
    price: float = FloatField(min=0.0, max=999999.99)   # Price range
    rating: float = FloatField(min=0.0, max=5.0)        # Rating 0-5
    discount_percent: int = IntField(
        min=0,
        max=100,
        multiple_of=5                                   # Must be multiple of 5
    )

# All validation happens at C speed
product = Product(
    id=123,
    quantity=50,
    price=29.99,
    rating=4.5,
    discount_percent=15
)
```

### Boolean and List Validation

```python
from catzilla import BoolField, ListField

class BoolField:
    """C-accelerated boolean validation with flexible parsing."""

    def __init__(
        self,
        strict: bool = False,      # True: only bool, False: parse strings/ints
        **kwargs
    ) -> None: ...

class ListField:
    """C-accelerated list validation with item validation."""

    def __init__(
        self,
        item_type: Type,           # Type for list items
        min_items: Optional[int] = None,
        max_items: Optional[int] = None,
        unique_items: bool = False,
        **kwargs
    ) -> None: ...
```

**Example:**

```python
from catzilla import BaseModel, BoolField, ListField, StringField

class BlogPost(BaseModel):
    title: str
    tags: List[str] = ListField(
        item_type=str,
        min_items=1,
        max_items=10,
        unique_items=True          # No duplicate tags
    )
    is_published: bool = BoolField(strict=False)  # Accepts "true", 1, etc.
    categories: List[str] = ListField(
        item_type=StringField(min_len=2, max_len=50),
        max_items=5
    )

# Flexible boolean parsing
post = BlogPost(
    title="My Blog Post",
    tags=["python", "web", "performance"],
    is_published="true",           # Parsed as True
    categories=["tech", "programming"]
)
```

### Optional and Union Fields

```python
from catzilla import OptionalField, UnionField

class OptionalField:
    """Wrapper for optional fields with default values."""

    def __init__(
        self,
        field_type: Type,
        default: Any = None,
        **kwargs
    ) -> None: ...

class UnionField:
    """C-accelerated union type validation."""

    def __init__(
        self,
        types: List[Type],         # List of allowed types
        **kwargs
    ) -> None: ...
```

**Example:**

```python
from catzilla import BaseModel, OptionalField, UnionField, StringField, IntField

class APIResponse(BaseModel):
    success: bool
    data: Union[dict, list, str] = UnionField(types=[dict, list, str])
    message: Optional[str] = OptionalField(
        StringField(max_len=200),
        default="Operation completed"
    )
    error_code: Optional[int] = OptionalField(
        IntField(min=1000, max=9999),
        default=None
    )

# Handles different data types
response1 = APIResponse(success=True, data={"users": []})
response2 = APIResponse(success=False, data="Error message", error_code=4001)
```

## Advanced Validation

### Custom Validators

```python
from catzilla import BaseModel, validator

class User(BaseModel):
    username: str
    password: str
    confirm_password: str

    @validator('username')
    @classmethod
    def validate_username(cls, value: str) -> str:
        """Custom validator - automatically compiled to C"""
        if value.startswith('_'):
            raise ValueError('Username cannot start with underscore')
        return value

    @validator('confirm_password')
    @classmethod
    def validate_password_match(cls, value: str, values: dict) -> str:
        """Cross-field validation"""
        if 'password' in values and value != values['password']:
            raise ValueError('Passwords do not match')
        return value
```

### Root Validators

```python
from catzilla import BaseModel, root_validator

class DateRange(BaseModel):
    start_date: str
    end_date: str

    @root_validator
    @classmethod
    def validate_date_range(cls, values: dict) -> dict:
        """Validate the entire model - compiled to C for speed"""
        start = values.get('start_date')
        end = values.get('end_date')

        if start and end and start > end:
            raise ValueError('Start date must be before end date')

        return values
```

### Model Configuration

```python
class User(BaseModel):
    id: int
    name: str

    class Config:
        # Validation configuration
        validate_assignment = True      # Validate on field assignment
        use_enum_values = True         # Use enum values instead of names
        allow_reuse = True             # Allow model reuse

        # C compilation settings
        compile_to_c = True            # Force C compilation
        c_optimization_level = 3       # C optimization level (1-3)

        # Serialization settings
        json_encoders = {
            # Custom JSON encoders
        }

        # Field settings
        str_strip_whitespace = True    # Strip whitespace from strings
        validate_all = True            # Validate all fields always
```

## Nested Models

### Complex Nested Structures

```python
from catzilla import BaseModel
from typing import List, Optional, Dict

class Address(BaseModel):
    street: str
    city: str
    country: str
    postal_code: str = StringField(pattern=r'^\d{5}(-\d{4})?$')

class Contact(BaseModel):
    email: str = StringField(pattern=r'^[^@]+@[^@]+\.[^@]+$')
    phone: Optional[str] = None

class User(BaseModel):
    id: int
    name: str
    contact: Contact                    # Nested model
    addresses: List[Address]            # List of nested models
    metadata: Dict[str, str] = {}       # Dictionary field

# All validation cascades through nested models at C speed
user = User(
    id=1,
    name="Alice",
    contact={
        "email": "alice@example.com",
        "phone": "+1-555-0123"
    },
    addresses=[
        {
            "street": "123 Main St",
            "city": "New York",
            "country": "USA",
            "postal_code": "10001"
        }
    ],
    metadata={"role": "admin", "department": "engineering"}
)

# Access nested data
print(user.contact.email)                    # alice@example.com
print(user.addresses[0].city)                # New York
```

### Recursive Models

```python
class Category(BaseModel):
    id: int
    name: str
    parent_id: Optional[int] = None
    children: List['Category'] = []     # Self-reference

# Update forward references for C compilation
Category.model_rebuild()
```

## Performance Features

### C Compilation

```python
from catzilla import BaseModel, compile_model

class HighPerformanceModel(BaseModel):
    # Many fields for demonstration
    field1: str
    field2: int
    field3: float
    # ... more fields

# Manual compilation to C (usually automatic)
compile_model(HighPerformanceModel)

# Check if model is compiled
print(HighPerformanceModel.is_compiled_to_c())  # True

# Get compilation stats
stats = HighPerformanceModel.get_compilation_stats()
# {
#   "compiled": True,
#   "compilation_time_ms": 15,
#   "validation_speedup": 127.3,
#   "memory_usage_bytes": 2048
# }
```

### Batch Validation

```python
# Validate multiple objects efficiently
users_data = [
    {"id": 1, "name": "Alice"},
    {"id": 2, "name": "Bob"},
    {"id": 3, "name": "Charlie"},
    # ... thousands of records
]

# C-accelerated batch validation
users = User.parse_batch(users_data)    # Validates all at C speed

# Streaming validation for large datasets
def validate_streaming_data(data_stream):
    for batch in data_stream:
        validated_batch = User.parse_batch(batch)
        yield validated_batch
```

## Integration with Routes

### Request/Response Validation

```python
from catzilla import Catzilla, BaseModel

app = Catzilla(enable_c_acceleration=True)

class CreateUserRequest(BaseModel):
    name: str = StringField(min_len=2, max_len=50)
    email: str = StringField(pattern=r'^[^@]+@[^@]+\.[^@]+$')
    age: int = IntField(min=0, max=150)

class UserResponse(BaseModel):
    id: int
    name: str
    email: str
    created_at: str

@app.post("/users")
def create_user(request, user_data: CreateUserRequest) -> UserResponse:
    """
    Both request and response validation happen at C speed!
    """
    # user_data is already validated
    print(f"Creating user: {user_data.name}")

    # Return response (also validated at C speed)
    return UserResponse(
        id=123,
        name=user_data.name,
        email=user_data.email,
        created_at="2024-01-01T00:00:00Z"
    )
```

### Query Parameter Validation

```python
class SearchParams(BaseModel):
    query: str = StringField(min_len=1, max_len=100)
    page: int = IntField(min=1, default=1)
    limit: int = IntField(min=1, max=100, default=20)
    sort: Optional[str] = StringField(pattern=r'^(name|date|relevance)$')

@app.get("/search")
def search(params: SearchParams = Query()) -> dict:
    """Query parameters validated at C speed"""
    return {
        "query": params.query,
        "page": params.page,
        "limit": params.limit,
        "results": []
    }
```

## Error Handling

### ValidationError

```python
from catzilla.types import ValidationError

try:
    user = User(id="invalid", name="")
except ValidationError as e:
    print(f"Validation errors: {e.errors()}")
    # [
    #   {
    #     "field": "id",
    #     "message": "value is not a valid integer",
    #     "type": "type_error.integer"
    #   },
    #   {
    #     "field": "name",
    #     "message": "ensure this value has at least 1 characters",
    #     "type": "value_error.any_str.min_length"
    #   }
    # ]
```

### Custom Error Messages

```python
class User(BaseModel):
    age: int = IntField(
        min=0,
        max=150,
        error_msg="Age must be between 0 and 150"
    )

    username: str = StringField(
        min_len=3,
        max_len=20,
        pattern=r'^[a-zA-Z0-9_]+$',
        error_msg="Username must be 3-20 characters, alphanumeric and underscore only"
    )
```

## Compatibility with Pydantic

### Migration from Pydantic

```python
# Existing Pydantic code works without changes
from catzilla import BaseModel  # Drop-in replacement for pydantic.BaseModel

# Your existing Pydantic models work immediately
class ExistingModel(BaseModel):
    field1: str
    field2: int
    field3: Optional[float] = None

# Pydantic features supported:
# - Field(...) syntax
# - validator decorators
# - root_validator decorators
# - Config classes
# - JSON schema generation
# - All validation types

# Plus new C-acceleration features!
```

### Performance Comparison

```python
# Benchmark validation performance
import time
from your_app import User

def benchmark_validation():
    data = {"id": 1, "name": "Alice", "email": "alice@example.com"}

    # Time 1000 validations
    start = time.time()
    for _ in range(1000):
        user = User.parse_obj(data)
    end = time.time()

    print(f"Catzilla validation: {(end - start) * 1000:.2f}ms for 1000 validations")
    # Typical output: "Catzilla validation: 0.85ms for 1000 validations"
    # Compare to Pydantic: ~100ms for same workload
```

## Complete Example

```python
from catzilla import (
    Catzilla, BaseModel, StringField, IntField, FloatField,
    ListField, OptionalField, validator
)
from typing import List, Optional
import re

# High-performance validation models
class Address(BaseModel):
    street: str = StringField(min_len=5, max_len=100)
    city: str = StringField(min_len=2, max_len=50)
    postal_code: str = StringField(pattern=r'^\d{5}(-\d{4})?$')
    country: str = StringField(min_len=2, max_len=3)

class Contact(BaseModel):
    email: str = StringField(
        pattern=r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$',
        to_lower=True
    )
    phone: Optional[str] = OptionalField(
        StringField(pattern=r'^\+?1?[-.\s]?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}$')
    )

class User(BaseModel):
    id: int = IntField(min=1)
    username: str = StringField(
        min_len=3,
        max_len=20,
        pattern=r'^[a-zA-Z0-9_]+$'
    )
    age: int = IntField(min=13, max=150)
    contact: Contact
    addresses: List[Address] = ListField(
        item_type=Address,
        min_items=0,
        max_items=5
    )
    tags: List[str] = ListField(
        item_type=StringField(min_len=1, max_len=20),
        unique_items=True
    )
    score: float = FloatField(min=0.0, max=100.0)

    @validator('username')
    @classmethod
    def validate_username(cls, value: str) -> str:
        """Custom validator compiled to C"""
        forbidden = ['admin', 'root', 'test']
        if value.lower() in forbidden:
            raise ValueError(f'Username "{value}" is not allowed')
        return value

    class Config:
        validate_assignment = True
        compile_to_c = True
        c_optimization_level = 3

# Create Catzilla app with C-accelerated validation
app = Catzilla(
    enable_c_acceleration=True,
    validation_c_acceleration=True
)

# API endpoint with automatic validation
@app.post("/users")
def create_user(request, user_data: User) -> User:
    """Create user with 100x faster validation"""
    print(f"User validated at C speed: {user_data.username}")

    # All validation already complete - data is guaranteed valid
    return user_data

# Example usage
if __name__ == "__main__":
    # Test data validation (happens at C speed)
    user_data = {
        "id": 123,
        "username": "alice_dev",
        "age": 28,
        "contact": {
            "email": "ALICE@EXAMPLE.COM",  # Will be lowercased
            "phone": "+1-555-0123"
        },
        "addresses": [
            {
                "street": "123 Main Street",
                "city": "San Francisco",
                "postal_code": "94105",
                "country": "USA"
            }
        ],
        "tags": ["developer", "python", "performance"],
        "score": 95.5
    }

    # Validate at C speed
    user = User.parse_obj(user_data)
    print(f"Validated user: {user.contact.email}")  # alice@example.com

    app.listen()
```

---

*Experience 100x faster validation with automatic C compilation!* ⚡
