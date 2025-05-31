#!/usr/bin/env python3
"""
Test script for optional field support in Catzilla validation engine.
"""

import sys
import os

# Add the python package to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'python'))

from catzilla.validation import BaseModel, ValidationError
from typing import Optional

def test_optional_fields():
    """Test models with optional fields"""

    print("=== Testing Optional Field Support ===")

    # Test 1: Model with required and optional fields
    print("\n1. Testing mixed required/optional fields...")

    class User(BaseModel):
        id: int                    # Required
        name: str                  # Required
        email: Optional[str] = None  # Optional
        age: Optional[int] = None    # Optional

    # Test with all fields provided
    try:
        user1 = User(id=1, name="John", email="john@example.com", age=30)
        print(f"✓ All fields: {user1}")
    except Exception as e:
        print(f"✗ All fields failed: {e}")

    # Test with only required fields
    try:
        user2 = User(id=2, name="Jane")
        print(f"✓ Required only: {user2}")
    except Exception as e:
        print(f"✗ Required only failed: {e}")

    # Test with missing required field
    try:
        user3 = User(name="Bob")  # Missing required 'id'
        print(f"✗ Should have failed: {user3}")
    except ValidationError as e:
        print(f"✓ Correctly rejected missing required field: {e}")
    except Exception as e:
        print(f"? Unexpected error: {e}")

    # Test 2: Model with all optional fields
    print("\n2. Testing all optional fields...")

    class Settings(BaseModel):
        theme: Optional[str] = None
        notifications: Optional[bool] = None
        timeout: Optional[int] = None

    try:
        settings1 = Settings()  # No fields provided
        print(f"✓ Empty optional model: {settings1}")
    except Exception as e:
        print(f"✗ Empty optional model failed: {e}")

    try:
        settings2 = Settings(theme="dark", notifications=True)
        print(f"✓ Partial optional model: {settings2}")
    except Exception as e:
        print(f"✗ Partial optional model failed: {e}")

    # Test 3: Optional boolean field specifically
    print("\n3. Testing optional boolean field...")

    class Config(BaseModel):
        enabled: Optional[bool] = None
        debug: bool  # Required boolean

    try:
        config1 = Config(debug=True)  # Optional bool not provided
        print(f"✓ Optional bool not provided: {config1}")
    except Exception as e:
        print(f"✗ Optional bool test failed: {e}")

    try:
        config2 = Config(enabled=False, debug=True)  # Optional bool provided
        print(f"✓ Optional bool provided: {config2}")
    except Exception as e:
        print(f"✗ Optional bool provided failed: {e}")

def test_field_inspection():
    """Test that field metadata is correct"""

    print("\n=== Testing Field Metadata ===")

    class TestModel(BaseModel):
        required_field: int
        optional_field: Optional[str] = None

    if hasattr(TestModel, '_fields'):
        for field_name, field in TestModel._fields.items():
            print(f"Field '{field_name}': optional={field.optional}, default={field.default}")
    else:
        print("No _fields attribute found")

if __name__ == "__main__":
    test_field_inspection()
    test_optional_fields()
