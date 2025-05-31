#!/usr/bin/env python3
"""
Debug the model compilation issue
"""

import sys
sys.path.insert(0, '/Users/user/devwork/catzilla/python')

def debug_model_compilation():
    """Debug model compilation step by step"""
    try:
        from catzilla._catzilla import create_int_validator, create_string_validator, create_model

        print("1. Creating validators...")
        int_validator = create_int_validator()
        string_validator = create_string_validator()
        print(f"   ✅ Integer validator: {int_validator}")
        print(f"   ✅ String validator: {string_validator}")

        # Check validator types
        print(f"   Type of int_validator: {type(int_validator)}")
        print(f"   Type of string_validator: {type(string_validator)}")

        print("\n2. Testing with minimal fields...")
        # Try with just one field first
        try:
            single_field = {'id': int_validator}
            print(f"   Creating single field model...")
            model1 = create_model(name="SingleField", fields=single_field)
            print(f"   ✅ Single field model created: {model1}")
        except Exception as e:
            print(f"   ❌ Single field model failed: {e}")

        print("\n3. Testing with empty fields...")
        try:
            empty_fields = {}
            print(f"   Creating empty model...")
            model2 = create_model(name="Empty", fields=empty_fields)
            print(f"   ✅ Empty model created: {model2}")
        except Exception as e:
            print(f"   ❌ Empty model failed: {e}")

        print("\n4. Creating fields dict...")
        fields = {
            'id': int_validator,
            'name': string_validator
        }
        print(f"   ✅ Fields dict: {fields}")
        print(f"   Fields count: {len(fields)}")

        print("\n5. Creating model...")
        try:
            model = create_model(name="TestModel", fields=fields)
            print(f"   ✅ Model created: {model}")
        except Exception as e:
            print(f"   ❌ Model creation failed: {e}")
            return False

        return True

    except Exception as e:
        print(f"❌ Debug failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = debug_model_compilation()
    sys.exit(0 if success else 1)
