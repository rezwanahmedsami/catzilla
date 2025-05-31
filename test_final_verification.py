#!/usr/bin/env python3
"""
Final verification test for optional field support in Catzilla.
Tests all aspects of the fix without debug output.
"""

from typing import Optional, List
from catzilla import BaseModel, Field, ValidationError

def test_field_metadata():
    """Test that field metadata correctly identifies required vs optional fields."""
    print("=== Testing Field Metadata ===")

    class TestModel(BaseModel):
        required_field: str
        optional_field: Optional[str] = None
        optional_with_default: Optional[str] = "default"
        required_with_annotation: str

    # Check field metadata
    fields = TestModel._fields

    assert not fields['required_field'].optional, f"required_field should not be optional, got {fields['required_field'].optional}"
    assert fields['optional_field'].optional, f"optional_field should be optional, got {fields['optional_field'].optional}"
    assert fields['optional_with_default'].optional, f"optional_with_default should be optional, got {fields['optional_with_default'].optional}"
    assert not fields['required_with_annotation'].optional, f"required_with_annotation should not be optional, got {fields['required_with_annotation'].optional}"

    print("✓ Field metadata correctly identifies required vs optional fields")

def test_validation_behavior():
    """Test that validation properly enforces required/optional field rules."""
    print("\n=== Testing Validation Behavior ===")

    class User(BaseModel):
        id: int
        name: str
        email: Optional[str] = None
        age: Optional[int] = None

    # Test with all fields
    user1 = User(**{
        'id': 1,
        'name': 'John',
        'email': 'john@example.com',
        'age': 30
    })
    assert user1.id == 1
    assert user1.name == 'John'
    assert user1.email == 'john@example.com'
    assert user1.age == 30
    print("✓ Model with all fields creates successfully")

    # Test with only required fields
    user2 = User(**{
        'id': 2,
        'name': 'Jane'
    })
    assert user2.id == 2
    assert user2.name == 'Jane'
    print("✓ Model with only required fields creates successfully")

    # Test missing required field should fail
    try:
        User(**{'name': 'Bob'})  # missing id
        assert False, "Should have failed due to missing required field"
    except (ValueError, ValidationError) as e:
        assert 'id' in str(e) and 'required' in str(e)
        print("✓ Missing required field properly rejected")

    # Test missing another required field should fail
    try:
        User(**{'id': 3})  # missing name
        assert False, "Should have failed due to missing required field"
    except (ValueError, ValidationError) as e:
        assert 'name' in str(e) and 'required' in str(e)
        print("✓ Missing another required field properly rejected")

def test_all_optional_model():
    """Test model with all optional fields."""
    print("\n=== Testing All Optional Model ===")

    class Settings(BaseModel):
        theme: Optional[str] = None
        notifications: Optional[bool] = None
        timeout: Optional[int] = None

    # Test empty model
    settings1 = Settings(**{})
    print("✓ Empty optional model creates successfully")

    # Test partial model
    settings2 = Settings(**{
        'theme': 'dark',
        'notifications': True
    })
    assert settings2.theme == 'dark'
    assert settings2.notifications == True
    print("✓ Partial optional model creates successfully")

def test_basic_optional_types():
    """Test optional fields with basic types that are supported."""
    print("\n=== Testing Basic Optional Types ===")

    class BasicModel(BaseModel):
        required_str: str
        optional_str: Optional[str] = None
        optional_int: Optional[int] = None
        optional_float: Optional[float] = None
        optional_bool: Optional[bool] = None

    # Test with required field only
    model1 = BasicModel(**{
        'required_str': 'hello'
    })
    assert model1.required_str == 'hello'
    print("✓ Basic model with only required field works")

    # Test with all fields
    model2 = BasicModel(**{
        'required_str': 'world',
        'optional_str': 'optional',
        'optional_int': 42,
        'optional_float': 3.14,
        'optional_bool': True
    })
    assert model2.required_str == 'world'
    assert model2.optional_str == 'optional'
    assert model2.optional_int == 42
    assert model2.optional_float == 3.14
    assert model2.optional_bool == True
    print("✓ Basic model with all fields works")

def test_field_annotation_consistency():
    """Test that field annotations work consistently."""
    print("\n=== Testing Field Annotation Consistency ===")

    class SimpleProduct(BaseModel):
        name: str
        price: Optional[float] = None
        category: str
        active: Optional[bool] = None

    # Check field metadata
    fields = SimpleProduct._fields
    assert not fields['name'].optional
    assert fields['price'].optional
    assert not fields['category'].optional
    assert fields['active'].optional
    print("✓ Field annotations correctly handle optional status")

    # Test validation with mixed required/optional
    product = SimpleProduct(**{
        'name': 'Laptop',
        'category': 'Electronics',
        'price': 999.99
    })
    assert product.name == 'Laptop'
    assert product.category == 'Electronics'
    assert product.price == 999.99
    print("✓ Mixed required/optional validation works correctly")

if __name__ == '__main__':
    print("Testing Catzilla Optional Field Support - Final Verification")
    print("=" * 60)

    try:
        test_field_metadata()
        test_validation_behavior()
        test_all_optional_model()
        test_basic_optional_types()
        test_field_annotation_consistency()

        print("\n" + "=" * 60)
        print("🎉 ALL TESTS PASSED! Optional field support is working correctly.")
        print("✓ Field metadata correctly identifies required vs optional")
        print("✓ Validation properly enforces required field rules")
        print("✓ Optional fields work as expected")
        print("✓ Basic types are supported")
        print("✓ Field annotation integration works")
        print("\nNote: Complex types (List, Dict) support may require additional work.")

    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
