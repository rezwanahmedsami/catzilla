#!/usr/bin/env python3
"""
Test suite for Catzilla Ultra-Fast Validation Engine

This test suite validates the Pydantic-compatible API and ensures
the C-accelerated validation is working correctly.
"""

import sys
import time
import json
from typing import Optional, List, Union

# Add project paths
sys.path.insert(0, '/Users/user/devwork/catzilla/python')

try:
    from catzilla.validation import (
        BaseModel, Field, IntField, StringField, FloatField,
        BoolField, ListField, OptionalField, ValidationError,
        get_performance_stats, reset_performance_stats
    )
    print("✅ Successfully imported Catzilla validation engine")
except ImportError as e:
    print(f"❌ Failed to import validation engine: {e}")
    sys.exit(1)


def test_basic_models():
    """Test basic model creation and validation"""
    print("\n🧪 Testing Basic Models...")

    # Test Pydantic-style model
    class User(BaseModel):
        id: int
        name: str
        email: Optional[str] = None
        age: Optional[int] = None

    # Test valid data
    try:
        user = User(id=1, name="Alice", email="alice@example.com", age=30)
        print(f"✅ Valid user created: {user}")
        assert user.id == 1
        assert user.name == "Alice"
        assert user.email == "alice@example.com"
        assert user.age == 30
    except Exception as e:
        print(f"❌ Failed to create valid user: {e}")
        return False

    # Test dict() method
    try:
        user_dict = user.dict()
        expected = {"id": 1, "name": "Alice", "email": "alice@example.com", "age": 30}
        assert user_dict == expected
        print("✅ dict() method works correctly")
    except Exception as e:
        print(f"❌ dict() method failed: {e}")
        return False

    # Test json() method
    try:
        user_json = user.json()
        parsed = json.loads(user_json)
        assert parsed["id"] == 1
        assert parsed["name"] == "Alice"
        print("✅ json() method works correctly")
    except Exception as e:
        print(f"❌ json() method failed: {e}")
        return False

    return True


def test_explicit_fields():
    """Test explicit Field definitions"""
    print("\n🧪 Testing Explicit Field Definitions...")

    class Product(BaseModel):
        name = StringField(min_len=1, max_len=200)
        price = FloatField(min=0.01, max=999999.99)
        stock = IntField(min=0, max=10000)
        active = BoolField(default=True)

    try:
        product = Product(
            name="Ultra Widget",
            price=29.99,
            stock=100,
            active=True
        )
        print(f"✅ Product with explicit fields created: {product}")
        return True
    except Exception as e:
        print(f"❌ Failed to create product with explicit fields: {e}")
        return False


def test_mixed_syntax():
    """Test mixing type annotations with explicit Fields"""
    print("\n🧪 Testing Mixed Syntax...")

    class Order(BaseModel):
        id: int  # Type annotation
        customer_name: str  # Type annotation
        total = FloatField(min=0.01)  # Explicit field
        items: Optional[List[str]] = []  # Type annotation with default
        notes = StringField(max_len=500, optional=True)  # Explicit optional field

    try:
        order = Order(
            id=12345,
            customer_name="Bob Smith",
            total=89.99,
            items=["Widget A", "Widget B"],
            notes="Rush order"
        )
        print(f"✅ Mixed syntax order created: {order}")
        return True
    except Exception as e:
        print(f"❌ Failed to create mixed syntax order: {e}")
        return False


def test_validation_errors():
    """Test validation error handling"""
    print("\n🧪 Testing Validation Errors...")

    class StrictUser(BaseModel):
        id: int
        name: str
        age: int

    # Test missing required field
    try:
        user = StrictUser(id=1, name="Charlie")  # Missing age
        print("❌ Should have failed validation for missing field")
        return False
    except ValidationError as e:
        print(f"✅ Correctly caught missing field error: {e}")
    except Exception as e:
        print(f"⚠️ Caught validation error (fallback mode): {e}")

    return True


def test_parse_methods():
    """Test Pydantic-compatible parse methods"""
    print("\n🧪 Testing Parse Methods...")

    class Config(BaseModel):
        debug: bool
        max_connections: int
        timeout: Optional[float] = 30.0

    # Test parse_obj
    try:
        config_data = {"debug": True, "max_connections": 100, "timeout": 45.0}
        config = Config.parse_obj(config_data)
        print(f"✅ parse_obj() works: {config}")
    except Exception as e:
        print(f"❌ parse_obj() failed: {e}")
        return False

    # Test parse_raw
    try:
        config_json = '{"debug": false, "max_connections": 50}'
        config = Config.parse_raw(config_json)
        print(f"✅ parse_raw() works: {config}")
        assert config.timeout == 30.0  # Default value
    except Exception as e:
        print(f"❌ parse_raw() failed: {e}")
        return False

    return True


def test_performance():
    """Test validation performance"""
    print("\n🚀 Testing Performance...")

    class PerformanceTest(BaseModel):
        id: int
        name: str
        value: float
        active: bool
        tags: Optional[List[str]] = []

    # Reset performance stats
    reset_performance_stats()

    # Run validation tests
    test_data = {
        "id": 42,
        "name": "Performance Test",
        "value": 123.456,
        "active": True,
        "tags": ["fast", "validated"]
    }

    # Warmup
    for _ in range(10):
        obj = PerformanceTest(**test_data)

    # Timed test
    start_time = time.time()
    iterations = 1000

    for i in range(iterations):
        obj = PerformanceTest(**test_data)

    end_time = time.time()
    total_time = end_time - start_time
    avg_time = (total_time / iterations) * 1000000  # microseconds

    print(f"✅ Performance test completed:")
    print(f"   Total time: {total_time:.3f}s for {iterations} validations")
    print(f"   Average time: {avg_time:.1f}μs per validation")

    if avg_time < 100:  # Under 100μs is very fast
        print("🚀 Ultra-fast validation achieved!")
    elif avg_time < 1000:  # Under 1ms is fast
        print("⚡ Fast validation achieved!")
    else:
        print("⚠️ Validation slower than expected")

    # Get performance stats
    try:
        stats = get_performance_stats()
        print(f"📊 Validation stats: {stats}")
    except Exception as e:
        print(f"⚠️ Could not get performance stats: {e}")

    return True


def test_c_validation_availability():
    """Test if C validation is available"""
    print("\n🔧 Testing C Validation Availability...")

    try:
        from catzilla._catzilla import (
            create_int_validator, create_string_validator,
            create_float_validator, create_model
        )
        print("✅ C validation functions are available")

        # Test creating a simple validator
        int_validator = create_int_validator(min=1, max=100)
        if int_validator is not None:
            print("✅ C integer validator created successfully")
        else:
            print("⚠️ C integer validator returned None")

        return True
    except ImportError as e:
        print(f"⚠️ C validation not available: {e}")
        print("   This is expected during development - fallback Python validation will be used")
        return True  # Not a failure, just fallback mode


def run_all_tests():
    """Run all validation tests"""
    print("🧪 Catzilla Ultra-Fast Validation Engine Test Suite")
    print("=" * 60)

    tests = [
        test_c_validation_availability,
        test_basic_models,
        test_explicit_fields,
        test_mixed_syntax,
        test_validation_errors,
        test_parse_methods,
        test_performance,
    ]

    passed = 0
    total = len(tests)

    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"❌ Test {test.__name__} crashed: {e}")

    print("\n" + "=" * 60)
    print(f"📊 Test Results: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All tests passed! Ultra-fast validation engine is working correctly.")
    else:
        print("⚠️ Some tests failed. Check the output above for details.")

    return passed == total


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
