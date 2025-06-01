#!/usr/bin/env python3
"""
Test to isolate validator cleanup segfault issue.
Tests individual validator creation and cleanup without models.
"""

import gc
import sys
import os

# Force garbage collection to be explicit
gc.disable()

# Ensure we can import catzilla
sys.path.insert(0, '/Users/user/devwork/catzilla/python')

try:
    from catzilla._catzilla import (
        create_int_validator,
        create_string_validator,
        create_list_validator,
        create_optional_validator
    )
    print("✅ Successfully imported catzilla C functions")
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)

def test_basic_validator_cleanup():
    """Test basic validator creation and immediate cleanup"""
    print("🔍 Testing basic validator cleanup...")

    # Create a simple validator
    int_validator = create_int_validator()
    print("✅ Created int validator")

    # Force cleanup by deleting reference
    del int_validator
    print("✅ Deleted int validator reference")

    # Manual garbage collection
    gc.collect()
    print("✅ Manual garbage collection completed")

def test_nested_validator_cleanup():
    """Test nested validator cleanup"""
    print("🔍 Testing nested validator cleanup...")

    # Create nested validators step by step
    int_validator = create_int_validator()
    print("✅ Created int validator")

    list_validator = create_list_validator(int_validator)
    print("✅ Created list validator")

    optional_validator = create_optional_validator(list_validator)
    print("✅ Created optional validator")

    # Delete in reverse order
    del optional_validator
    print("✅ Deleted optional validator reference")

    del list_validator
    print("✅ Deleted list validator reference")

    del int_validator
    print("✅ Deleted int validator reference")

    # Manual garbage collection
    gc.collect()
    print("✅ Manual garbage collection completed")

def test_complex_nested_cleanup():
    """Test complex nested validator cleanup"""
    print("🔍 Testing complex nested validator cleanup...")

    # Create List[List[str]] type
    str_validator = create_string_validator()
    print("✅ Created string validator")

    inner_list = create_list_validator(str_validator)
    print("✅ Created inner list validator")

    outer_list = create_list_validator(inner_list)
    print("✅ Created outer list validator")

    # Delete all references
    del outer_list
    del inner_list
    del str_validator
    print("✅ Deleted all validator references")

    # Manual garbage collection
    gc.collect()
    print("✅ Manual garbage collection completed")

def main():
    print("🧪 Testing validator cleanup to identify segfault source...")

    try:
        test_basic_validator_cleanup()
        print()

        test_nested_validator_cleanup()
        print()

        test_complex_nested_cleanup()
        print()

        print("✅ All validator cleanup tests passed")

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

    return 0

if __name__ == "__main__":
    sys.exit(main())
