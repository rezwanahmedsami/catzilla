#!/usr/bin/env python3
"""
Advanced Validation Engine Examples
===================================

This example demonstrates advanced features of Catzilla's validation engine,
including complex types, custom validators, inheritance, and performance optimization.
"""

from typing import Optional, List, Dict, Union, Any, Literal
from catzilla import BaseModel
import time
import json
from datetime import datetime
from enum import Enum


class UserRole(str, Enum):
    """User role enumeration."""
    ADMIN = "admin"
    USER = "user"
    MODERATOR = "moderator"
    GUEST = "guest"


class Address(BaseModel):
    """Address model for nested validation."""
    street: str
    city: str
    state: str
    zip_code: str
    country: str = "USA"


class Contact(BaseModel):
    """Contact information model."""
    email: str
    phone: Optional[str] = None
    address: Optional[Address] = None


class User(BaseModel):
    """Advanced user model with complex fields."""
    id: int
    username: str
    contact: Contact
    role: UserRole = UserRole.USER
    preferences: Optional[Dict[str, Any]] = None
    tags: Optional[List[str]] = None
    metadata: Optional[Dict[str, Union[str, int, bool]]] = None
    created_at: Optional[str] = None  # ISO datetime string
    is_active: bool = True


class APIKey(BaseModel):
    """API key model with specific constraints."""
    key: str
    name: str
    permissions: List[str]
    rate_limit: Optional[int] = 1000
    expires_at: Optional[str] = None
    user_id: int


class DatabaseConfig(BaseModel):
    """Database configuration model."""
    host: str
    port: int = 5432
    database: str
    username: str
    password: str
    ssl_mode: Literal["require", "prefer", "disable"] = "prefer"
    connection_pool_size: int = 10
    timeout: int = 30


class APIResponse(BaseModel):
    """Generic API response model."""
    success: bool
    data: Optional[Dict[str, Any]] = None
    errors: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None
    timestamp: str


def demonstrate_complex_types():
    """Demonstrate validation with complex nested types."""
    print("🔧 Complex Type Validation")
    print("=" * 50)

    # Create a complex user with nested models
    print("\n1. Creating user with nested models:")

    user_data = {
        "id": 1,
        "username": "alice_admin",
        "contact": {
            "email": "alice@company.com",
            "phone": "+1-555-0123",
            "address": {
                "street": "123 Tech Street",
                "city": "San Francisco",
                "state": "CA",
                "zip_code": "94105"
            }
        },
        "role": "admin",
        "preferences": {
            "theme": "dark",
            "notifications": True,
            "language": "en-US",
            "timeout": 3600
        },
        "tags": ["premium", "early-adopter", "beta-tester"],
        "metadata": {
            "source": "internal",
            "priority": 5,
            "verified": True
        },
        "created_at": "2024-01-15T10:30:00Z"
    }

    user = User(**user_data)
    print(f"   ✅ User created: {user.username}")
    print(f"   👤 Role: {user.role}")
    print(f"   📧 Email: {user.contact.email}")
    print(f"   🏠 Address: {user.contact.address.city}, {user.contact.address.state}")
    print(f"   🏷️  Tags: {user.tags}")

    # API Key with permissions
    print("\n2. Creating API key with permissions:")

    api_key_data = {
        "key": "sk_test_1234567890abcdef",
        "name": "Production API Key",
        "permissions": ["read", "write", "admin"],
        "rate_limit": 5000,
        "user_id": user.id
    }

    api_key = APIKey(**api_key_data)
    print(f"   🔑 API Key: {api_key.name}")
    print(f"   🔒 Permissions: {api_key.permissions}")
    print(f"   ⚡ Rate limit: {api_key.rate_limit}/hour")


def demonstrate_literal_types():
    """Demonstrate Literal type validation."""
    print("\n\n🎯 Literal Type Validation")
    print("=" * 50)

    # Database configuration with literal types
    print("\n1. Database configuration with SSL modes:")

    configs = [
        {
            "host": "db.example.com",
            "database": "production",
            "username": "app_user",
            "password": "secure_password",
            "ssl_mode": "require"
        },
        {
            "host": "localhost",
            "database": "development",
            "username": "dev_user",
            "password": "dev_password",
            "ssl_mode": "disable",
            "port": 5433
        }
    ]

    for i, config_data in enumerate(configs, 1):
        config = DatabaseConfig(**config_data)
        print(f"   ✅ Config {i}: {config.host}:{config.port}")
        print(f"      🔒 SSL Mode: {config.ssl_mode}")
        print(f"      🏊 Pool Size: {config.connection_pool_size}")

    # Try invalid SSL mode
    print("\n2. Testing invalid literal value:")
    try:
        invalid_config = {
            "host": "bad.example.com",
            "database": "test",
            "username": "user",
            "password": "pass",
            "ssl_mode": "invalid_mode"  # This should fail
        }
        DatabaseConfig(**invalid_config)
    except Exception as e:
        print(f"   ❌ Expected error: {e}")


def demonstrate_optional_defaults():
    """Demonstrate optional fields with complex defaults."""
    print("\n\n🎛️  Optional Fields and Defaults")
    print("=" * 50)

    # Minimal user (only required fields)
    print("\n1. Minimal user creation:")
    minimal_user_data = {
        "id": 2,
        "username": "minimal_user",
        "contact": {
            "email": "minimal@example.com"
        }
    }

    minimal_user = User(**minimal_user_data)
    print(f"   ✅ User: {minimal_user.username}")
    print(f"   📧 Email: {minimal_user.contact.email}")
    print(f"   👤 Role: {minimal_user.role} (default)")
    print(f"   📱 Phone: {minimal_user.contact.phone} (default)")
    print(f"   🏠 Address: {minimal_user.contact.address} (default)")
    print(f"   ⚙️  Preferences: {minimal_user.preferences} (default)")

    # API response with defaults
    print("\n2. API response with partial data:")
    response_data = {
        "success": True,
        "data": {"user_count": 42, "last_update": "2024-01-15"},
        "timestamp": "2024-01-15T10:30:00Z"
    }

    response = APIResponse(**response_data)
    print(f"   ✅ Success: {response.success}")
    print(f"   📊 Data: {response.data}")
    print(f"   ❌ Errors: {response.errors} (default)")
    print(f"   ⏰ Timestamp: {response.timestamp}")


def demonstrate_union_types():
    """Demonstrate Union type handling."""
    print("\n\n🔀 Union Type Validation")
    print("=" * 50)

    class FlexibleModel(BaseModel):
        """Model with flexible field types."""
        id: Union[int, str]
        value: Union[str, int, float, bool]
        data: Optional[Union[List[str], Dict[str, Any]]] = None

    # Test different union combinations
    test_cases = [
        {"id": 1, "value": "text", "data": ["item1", "item2"]},
        {"id": "uuid-123", "value": 42.5, "data": {"key": "value"}},
        {"id": 999, "value": True},
        {"id": "string-id", "value": 0}
    ]

    for i, case_data in enumerate(test_cases, 1):
        model = FlexibleModel(**case_data)
        print(f"   ✅ Case {i}: id={model.id} ({type(model.id).__name__})")
        print(f"      Value: {model.value} ({type(model.value).__name__})")
        if model.data:
            print(f"      Data: {type(model.data).__name__} with {len(model.data)} items")


def demonstrate_performance_optimization():
    """Demonstrate performance with large datasets."""
    print("\n\n🚀 Performance Optimization")
    print("=" * 50)

    # Generate large dataset
    print("\n1. Creating large dataset...")
    dataset_size = 10000

    user_templates = []
    for i in range(dataset_size):
        user_data = {
            "id": i,
            "username": f"user_{i}",
            "contact": {
                "email": f"user{i}@example.com",
                "phone": f"+1-555-{i:04d}" if i % 3 == 0 else None
            },
            "role": ["user", "moderator", "admin"][i % 3],
            "preferences": {
                "theme": ["light", "dark"][i % 2],
                "notifications": i % 2 == 0,
                "api_version": "v2"
            } if i % 5 == 0 else None,
            "tags": [f"group_{i // 100}", "active"] if i % 10 == 0 else None,
            "is_active": i % 20 != 0
        }
        user_templates.append(user_data)

    # Benchmark validation
    print(f"   📊 Validating {dataset_size} complex user models...")

    start_time = time.perf_counter()
    validated_users = []

    for user_data in user_templates:
        user = User(**user_data)
        validated_users.append(user)

    end_time = time.perf_counter()
    total_time = end_time - start_time
    rate = dataset_size / total_time

    print(f"   ⚡ Validation: {total_time:.4f}s ({rate:.0f} models/sec)")

    # Benchmark serialization
    print(f"   📊 Serializing {dataset_size} models to JSON...")

    start_time = time.perf_counter()
    json_outputs = []

    for user in validated_users:
        json_data = user.model_dump_json()
        json_outputs.append(json_data)

    end_time = time.perf_counter()
    serialize_time = end_time - start_time
    serialize_rate = dataset_size / serialize_time

    print(f"   ⚡ Serialization: {serialize_time:.4f}s ({serialize_rate:.0f} models/sec)")

    # Benchmark deserialization
    print(f"   📊 Deserializing {dataset_size} JSON models...")

    start_time = time.perf_counter()
    recreated_users = []

    for json_data in json_outputs:
        user_dict = json.loads(json_data)
        user = User(**user_dict)
        recreated_users.append(user)

    end_time = time.perf_counter()
    deserialize_time = end_time - start_time
    deserialize_rate = dataset_size / deserialize_time

    print(f"   ⚡ Deserialization: {deserialize_time:.4f}s ({deserialize_rate:.0f} models/sec)")

    # Statistics
    active_users = sum(1 for u in validated_users if u.is_active)
    users_with_prefs = sum(1 for u in validated_users if u.preferences)
    admin_users = sum(1 for u in validated_users if u.role == UserRole.ADMIN)

    print(f"\n   📈 Dataset Statistics:")
    print(f"      👥 Total users: {len(validated_users)}")
    print(f"      ✅ Active users: {active_users}")
    print(f"      ⚙️  Users with preferences: {users_with_prefs}")
    print(f"      👑 Admin users: {admin_users}")


def demonstrate_error_aggregation():
    """Demonstrate advanced error handling."""
    print("\n\n🚨 Advanced Error Handling")
    print("=" * 50)

    # Multiple validation errors
    print("\n1. Multiple validation errors:")
    try:
        invalid_user_data = {
            "id": "not_an_int",  # Wrong type
            "username": "",       # Empty string
            "contact": {
                "email": "invalid-email"  # Invalid email format
                # Missing required fields
            },
            "role": "invalid_role",  # Invalid enum value
            "preferences": "not_a_dict"  # Wrong type
        }
        User(**invalid_user_data)
    except Exception as e:
        print(f"   ❌ Validation errors: {e}")

    # Nested validation errors
    print("\n2. Nested model validation errors:")
    try:
        invalid_config = {
            "host": "",  # Empty host
            "port": "not_an_int",  # Wrong type
            "database": "",  # Empty database
            "username": "user",
            "password": "pass",
            "ssl_mode": "invalid",  # Invalid literal
            "connection_pool_size": -1,  # Invalid value
            "timeout": "not_an_int"  # Wrong type
        }
        DatabaseConfig(**invalid_config)
    except Exception as e:
        print(f"   ❌ Configuration errors: {e}")


if __name__ == "__main__":
    print("🚀 Catzilla Validation Engine - Advanced Examples")
    print("=" * 65)

    try:
        demonstrate_complex_types()
        demonstrate_literal_types()
        demonstrate_optional_defaults()
        demonstrate_union_types()
        demonstrate_performance_optimization()
        demonstrate_error_aggregation()

        print("\n\n🎉 All advanced examples completed successfully!")
        print("📚 Check out real_world_examples.py for practical use cases.")

    except Exception as e:
        print(f"\n❌ Example failed: {e}")
        import traceback
        traceback.print_exc()
