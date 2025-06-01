#!/usr/bin/env python3
"""
Test to isolate model creation segfault issue.
Focus on the specific model creation logic that was causing crashes.
"""

import gc
import sys
import os

# Ensure we can import catzilla
sys.path.insert(0, '/Users/user/devwork/catzilla/python')

try:
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

def test_simple_model_creation():
    """Test simple model creation and cleanup"""
    print("🔍 Testing simple model creation...")

    # Create simple validators
    int_validator = create_int_validator()
    str_validator = create_string_validator()
    print("✅ Created basic validators")

    # Create simple model
    fields = {
        'id': (int_validator, True),
        'name': (str_validator, True)
    }

    model = create_model(name="SimpleModel", fields=fields)
    print("✅ Created simple model")

    # Cleanup
    del model
    del fields
    del int_validator
    del str_validator
    print("✅ Deleted all references")

    gc.collect()
    print("✅ Manual garbage collection completed")

def test_nested_field_model():
    """Test model with nested field types that was causing segfaults"""
    print("🔍 Testing nested field model creation...")

    # Create nested validators step by step
    str_validator = create_string_validator()
    print("✅ Created string validator")

    list_str_validator = create_list_validator(str_validator)
    print("✅ Created List[str] validator")

    optional_list_str_validator = create_optional_validator(list_str_validator)
    print("✅ Created Optional[List[str]] validator")

    # Create model with nested field
    fields = {
        'tags': (optional_list_str_validator, False)
    }

    print("🔍 Creating model with nested field...")
    model = create_model(name="NestedModel", fields=fields)
    print("✅ Created nested field model")

    # Cleanup - be very explicit about order
    print("🧹 Starting cleanup...")
    del model
    print("   Deleted model")
    del fields
    print("   Deleted fields")
    del optional_list_str_validator
    print("   Deleted optional validator")
    del list_str_validator
    print("   Deleted list validator")
    del str_validator
    print("   Deleted string validator")

    print("🧹 Manual garbage collection...")
    gc.collect()
    print("✅ Cleanup completed")

def test_highly_nested_model():
    """Test model with highly nested types like List[List[str]]"""
    print("🔍 Testing highly nested model creation...")

    # Create List[List[str]] type
    str_validator = create_string_validator()
    inner_list = create_list_validator(str_validator)
    outer_list = create_list_validator(inner_list)
    print("✅ Created List[List[str]] validator")

    # Create model
    fields = {
        'matrix': (outer_list, True)
    }

    print("🔍 Creating model with highly nested field...")
    model = create_model(name="HighlyNestedModel", fields=fields)
    print("✅ Created highly nested model")

    # Explicit cleanup
    print("🧹 Starting cleanup...")
    del model
    print("   Deleted model")
    del fields
    print("   Deleted fields")
    del outer_list
    print("   Deleted outer list validator")
    del inner_list
    print("   Deleted inner list validator")
    del str_validator
    print("   Deleted string validator")

    print("🧹 Manual garbage collection...")
    gc.collect()
    print("✅ Cleanup completed")

def main():
    print("🧪 Testing model creation to identify segfault source...")

    try:
        test_simple_model_creation()
        print()

        test_nested_field_model()
        print()

        test_highly_nested_model()
        print()

        print("✅ All model creation tests passed")

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

    finally:
        # Final cleanup
        print("🧹 Final cleanup...")
        gc.collect()
        print("✅ Final cleanup completed")

        # Additional cleanup attempt
        print("🧹 Additional cleanup...")
        gc.collect()
        print("✅ Additional cleanup completed")

    return 0

if __name__ == "__main__":
    sys.exit(main())
