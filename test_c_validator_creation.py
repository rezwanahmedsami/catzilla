#!/usr/bin/env python3
"""
Minimal test to isolate C validator creation segfault.

This script tests C validator creation step by step to identify
exactly where the segfault occurs in the nested validator logic.
"""

import gc
import sys
from typing import List, Optional

# Ensure we can import catzilla
sys.path.insert(0, '/Users/user/devwork/catzilla/python')

try:
    from catzilla.validation import BaseModel, IntField, StringField, ListField, OptionalField
    from catzilla._catzilla import (
        create_int_validator,
        create_string_validator,
        create_list_validator,
        create_optional_validator,
        create_model
    )
    print("✅ Successfully imported catzilla C functions")
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)

def test_basic_validators():
    """Test basic validator creation"""
    print("\n🔍 Testing basic validator creation...")

    try:
        # Test simple validators
        int_val = create_int_validator(min=0, max=100)
        print("✅ Int validator created successfully")

        str_val = create_string_validator(min_len=1, max_len=50, pattern="")
        print("✅ String validator created successfully")

        return int_val, str_val
    except Exception as e:
        print(f"❌ Basic validator creation failed: {e}")
        return None, None

def test_list_validator(item_validator):
    """Test list validator creation"""
    print("\n🔍 Testing list validator creation...")

    try:
        list_val = create_list_validator(item_validator=item_validator, min_items=0, max_items=10)
        print("✅ List validator created successfully")
        return list_val
    except Exception as e:
        print(f"❌ List validator creation failed: {e}")
        return None

def test_optional_validator(inner_validator):
    """Test optional validator creation"""
    print("\n🔍 Testing optional validator creation...")

    try:
        opt_val = create_optional_validator(inner_validator=inner_validator)
        print("✅ Optional validator created successfully")
        return opt_val
    except Exception as e:
        print(f"❌ Optional validator creation failed: {e}")
        return None

def test_nested_validators():
    """Test nested validator creation that might cause segfault"""
    print("\n🔍 Testing nested validator creation...")

    try:
        # Create base validators
        int_val, str_val = test_basic_validators()
        if not int_val or not str_val:
            return False

        # Test List[str]
        list_str_val = test_list_validator(str_val)
        if not list_str_val:
            return False

        # Test Optional[str]
        opt_str_val = test_optional_validator(str_val)
        if not opt_str_val:
            return False

        # Test Optional[List[str]] - this might be where the segfault occurs
        print("\n🔍 Testing Optional[List[str]] creation...")
        opt_list_str_val = test_optional_validator(list_str_val)
        if not opt_list_str_val:
            return False

        # Test List[List[str]] - nested lists
        print("\n🔍 Testing List[List[str]] creation...")
        list_list_str_val = test_list_validator(list_str_val)
        if not list_list_str_val:
            return False

        print("✅ All nested validators created successfully")
        return True

    except Exception as e:
        print(f"❌ Nested validator creation failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_model_creation():
    """Test C model creation with validators"""
    print("\n🔍 Testing C model creation...")

    try:
        # Create validators
        int_val = create_int_validator(min=0, max=100)
        str_val = create_string_validator(min_len=1, max_len=50, pattern="")
        list_str_val = create_list_validator(item_validator=str_val, min_items=0, max_items=10)
        opt_str_val = create_optional_validator(inner_validator=str_val)

        # Create model with these validators
        fields = {
            'id': (int_val, True),      # required int
            'name': (str_val, True),    # required string
            'tags': (list_str_val, False),  # optional list
            'description': (opt_str_val, False)  # optional string
        }

        print("🔍 Creating C model...")
        c_model = create_model("TestModel", fields)

        if c_model:
            print("✅ C model created successfully")
            return True
        else:
            print("❌ C model creation returned None")
            return False

    except Exception as e:
        print(f"❌ C model creation failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main test function"""
    print("🧪 Testing C validator creation to identify segfault source...")

    # Disable garbage collection temporarily during testing
    gc.disable()

    try:
        # Test step by step
        success = True

        # Test basic validators
        int_val, str_val = test_basic_validators()
        if not int_val or not str_val:
            success = False

        # Test nested validators
        if success:
            success = test_nested_validators()

        # Test model creation
        if success:
            success = test_model_creation()

        if success:
            print("\n🎉 All tests passed! C validator creation is working correctly.")
        else:
            print("\n💥 Some tests failed. There may be an issue with C validator creation.")

    finally:
        # Re-enable garbage collection
        gc.enable()

    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
