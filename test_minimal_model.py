#!/usr/bin/env python3
"""
Minimal test to isolate the exact source of the segfault.
Test model creation with the simplest possible case.
"""

import sys
sys.path.insert(0, '/Users/user/devwork/catzilla/python')

try:
    from catzilla._catzilla import create_int_validator, create_model
    print("✅ Successfully imported catzilla C functions")
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)

def test_minimal_model():
    """Test the absolute minimal model creation"""
    print("🔍 Testing minimal model creation...")

    # Create single validator
    print("Step 1: Creating validator...")
    int_validator = create_int_validator()
    print(f"  Created: {int_validator}")

    # Create minimal fields dict
    print("Step 2: Creating fields...")
    fields = {'id': (int_validator, True)}
    print(f"  Fields: {fields}")

    # Create model
    print("Step 3: Creating model...")
    model = create_model(name="MinimalModel", fields=fields)
    print(f"  Model: {model}")

    print("✅ Model created successfully!")

    # Test explicit cleanup step by step
    print("Step 4: Cleanup test...")
    print("  Deleting model reference...")
    del model
    print("  Model deleted")

    print("  Deleting fields...")
    del fields
    print("  Fields deleted")

    print("  Deleting validator...")
    del int_validator
    print("  Validator deleted")

    print("✅ All cleanup completed successfully!")

if __name__ == "__main__":
    test_minimal_model()
    print("🎉 Test completed without segfault!")
