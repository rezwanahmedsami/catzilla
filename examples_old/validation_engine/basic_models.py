#!/usr/bin/env python3
"""
Basic Validation Engine Examples
=================================

This example demonstrates the basic usage of Catzilla's ultra-fast validation engine
with Pydantic-style models, showcasing optional fields, type validation, and
performance benefits.
"""

from typing import Optional, List, Dict, Union
from catzilla import BaseModel
import time
import json


class User(BaseModel):
    """A basic user model with required and optional fields."""
    id: int
    name: str
    email: str
    age: Optional[int] = None
    is_active: bool = True


class Product(BaseModel):
    """A product model demonstrating various field types."""
    id: int
    name: str
    price: float
    description: Optional[str] = None
    tags: Optional[List[str]] = None
    metadata: Optional[Dict[str, str]] = None
    in_stock: bool = True


class Order(BaseModel):
    """An order model showing nested model relationships."""
    id: int
    user: User
    products: List[Product]
    total_amount: float
    discount: Optional[float] = 0.0
    notes: Optional[str] = None


def demonstrate_basic_validation():
    """Demonstrate basic model validation."""
    print("🔍 Basic Model Validation Examples")
    print("=" * 50)

    # Valid user creation
    print("\n1. Creating a valid user:")
    user_data = {
        "id": 1,
        "name": "Alice Smith",
        "email": "alice@example.com",
        "age": 28
    }

    user = User(**user_data)
    print(f"   ✅ User created: {user}")
    print(f"   📊 User data: {user.model_dump()}")

    # User with optional fields omitted
    print("\n2. Creating user with optional fields omitted:")
    minimal_user_data = {
        "id": 2,
        "name": "Bob Johnson",
        "email": "bob@example.com"
    }

    minimal_user = User(**minimal_user_data)
    print(f"   ✅ Minimal user: {minimal_user}")
    print(f"   📊 Default age: {minimal_user.age}")
    print(f"   📊 Default is_active: {minimal_user.is_active}")

    # Product with complex types
    print("\n3. Creating product with complex optional fields:")
    product_data = {
        "id": 101,
        "name": "Gaming Laptop",
        "price": 1299.99,
        "description": "High-performance gaming laptop",
        "tags": ["gaming", "laptop", "high-performance"],
        "metadata": {
            "brand": "TechCorp",
            "model": "GameMaster Pro",
            "warranty": "2 years"
        }
    }

    product = Product(**product_data)
    print(f"   ✅ Product created: {product.name}")
    print(f"   📊 Tags: {product.tags}")
    print(f"   📊 Metadata: {product.metadata}")


def demonstrate_validation_errors():
    """Demonstrate validation error handling."""
    print("\n\n🚨 Validation Error Examples")
    print("=" * 50)

    # Missing required field
    print("\n1. Missing required field:")
    try:
        User(name="Invalid User", email="invalid@example.com")  # Missing 'id'
    except Exception as e:
        print(f"   ❌ Error: {e}")

    # Wrong type
    print("\n2. Wrong field type:")
    try:
        User(id="not_an_int", name="John", email="john@example.com")
    except Exception as e:
        print(f"   ❌ Error: {e}")

    # Invalid email (if validation is implemented)
    print("\n3. Optional field wrong type:")
    try:
        User(id=3, name="Jane", email="jane@example.com", age="not_an_int")
    except Exception as e:
        print(f"   ❌ Error: {e}")


def demonstrate_nested_models():
    """Demonstrate nested model validation."""
    print("\n\n🔗 Nested Model Examples")
    print("=" * 50)

    # Create user and products
    user = User(id=1, name="Alice", email="alice@example.com", age=28)

    products = [
        Product(id=101, name="Laptop", price=999.99),
        Product(id=102, name="Mouse", price=29.99, tags=["peripheral", "wireless"])
    ]

    # Create order with nested models
    order_data = {
        "id": 1001,
        "user": user.model_dump(),  # Convert to dict for validation
        "products": [p.model_dump() for p in products],
        "total_amount": 1029.98,
        "notes": "Express delivery requested"
    }

    order = Order(**order_data)
    print(f"   ✅ Order created: #{order.id}")
    print(f"   👤 Customer: {order.user.name}")
    print(f"   📦 Products: {len(order.products)} items")
    print(f"   💰 Total: ${order.total_amount}")
    print(f"   🏷️  Discount: ${order.discount}")


def demonstrate_performance():
    """Demonstrate validation performance."""
    print("\n\n⚡ Performance Demonstration")
    print("=" * 50)

    # Prepare test data
    test_users = []
    for i in range(1000):
        user_data = {
            "id": i,
            "name": f"User {i}",
            "email": f"user{i}@example.com",
            "age": 20 + (i % 50),
            "is_active": i % 2 == 0
        }
        test_users.append(user_data)

    # Benchmark validation
    print(f"\n   📊 Validating {len(test_users)} user models...")

    start_time = time.perf_counter()
    validated_users = []

    for user_data in test_users:
        user = User(**user_data)
        validated_users.append(user)

    end_time = time.perf_counter()
    total_time = end_time - start_time
    rate = len(test_users) / total_time

    print(f"   ⚡ Validation completed in {total_time:.4f} seconds")
    print(f"   🚀 Rate: {rate:.0f} validations/second")
    print(f"   ✅ All {len(validated_users)} models validated successfully")

    # Demonstrate field access performance
    print(f"\n   📊 Testing field access performance...")
    start_time = time.perf_counter()

    total_age = 0
    active_count = 0

    for user in validated_users:
        if user.age:
            total_age += user.age
        if user.is_active:
            active_count += 1

    end_time = time.perf_counter()
    access_time = end_time - start_time

    print(f"   ⚡ Field access completed in {access_time:.4f} seconds")
    print(f"   📈 Average age: {total_age / len(validated_users):.1f}")
    print(f"   📊 Active users: {active_count}/{len(validated_users)}")


def demonstrate_json_serialization():
    """Demonstrate JSON serialization/deserialization."""
    print("\n\n📄 JSON Serialization Examples")
    print("=" * 50)

    # Create a complex model
    user = User(id=1, name="Alice", email="alice@example.com", age=28)
    product = Product(
        id=101,
        name="Gaming Setup",
        price=2499.99,
        tags=["gaming", "complete-setup"],
        metadata={"includes": "monitor, keyboard, mouse"}
    )

    print("\n1. Model to JSON:")
    user_json = user.model_dump_json()
    product_json = product.model_dump_json()

    print(f"   👤 User JSON: {user_json}")
    print(f"   📦 Product JSON: {product_json}")

    print("\n2. JSON to Model:")
    # Parse back from JSON
    user_dict = json.loads(user_json)
    product_dict = json.loads(product_json)

    recreated_user = User(**user_dict)
    recreated_product = Product(**product_dict)

    print(f"   ✅ Recreated user: {recreated_user.name}")
    print(f"   ✅ Recreated product: {recreated_product.name}")
    print(f"   📊 Data integrity: {recreated_user == user}")


if __name__ == "__main__":
    print("🚀 Catzilla Validation Engine - Basic Examples")
    print("=" * 60)

    try:
        demonstrate_basic_validation()
        demonstrate_validation_errors()
        demonstrate_nested_models()
        demonstrate_performance()
        demonstrate_json_serialization()

        print("\n\n🎉 All examples completed successfully!")
        print("📚 Check out advanced_validation.py for more complex examples.")

    except Exception as e:
        print(f"\n❌ Example failed: {e}")
        import traceback
        traceback.print_exc()
