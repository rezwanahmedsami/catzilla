#!/usr/bin/env python3
"""
Test to isolate model creation segfault issue with debugging.
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
        create_model
    )
    print("✅ Successfully imported catzilla C functions")
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)

def test_step_by_step():
    """Test each step individually to isolate the segfault"""
    print("🔍 Testing step-by-step model creation...")

    # Step 1: Create validators
    print("Step 1: Creating validators...")
    int_validator = create_int_validator()
    print(f"  int_validator: {int_validator}")

    str_validator = create_string_validator()
    print(f"  str_validator: {str_validator}")

    # Step 2: Create fields dict
    print("Step 2: Creating fields dict...")
    fields = {
        'id': (int_validator, True),
        'name': (str_validator, True)
    }
    print(f"  fields: {fields}")

    # Step 3: Create model (this is where segfault occurs)
    print("Step 3: Creating model...")
    try:
        model = create_model(name="SimpleModel", fields=fields)
        print(f"  model: {model}")
        print("✅ Model created successfully!")
    except Exception as e:
        print(f"❌ Exception during model creation: {e}")
        return

    # Step 4: Explicit cleanup (checking if segfault happens here)
    print("Step 4: Explicit cleanup...")
    del model
    print("  model deleted")

    del fields
    print("  fields deleted")

    del int_validator
    print("  int_validator deleted")

    del str_validator
    print("  str_validator deleted")

    print("✅ All objects deleted successfully!")

    # Step 5: Force garbage collection (checking if segfault happens here)
    print("Step 5: Force garbage collection...")
    gc.collect()
    print("✅ Garbage collection completed!")

if __name__ == "__main__":
    test_step_by_step()
    print("🎉 Test completed without segfault!")
