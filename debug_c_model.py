#!/usr/bin/env python3
"""
Debug the C model creation with more detailed output
"""

import sys
sys.path.insert(0, '/Users/user/devwork/catzilla/python')

def debug_c_model():
    """Debug C model creation step by step"""
    try:
        from catzilla._catzilla import create_int_validator, create_string_validator, create_model

        print("Creating validators...")
        int_validator = create_int_validator()
        string_validator = create_string_validator()
        print(f"✅ Validators created")

        # Test adding fields one by one
        print("\nTesting single field addition...")
        try:
            fields_1 = {'id': int_validator}
            model_1 = create_model(name="Test1", fields=fields_1)
            print(f"✅ Single field model: {model_1}")
        except Exception as e:
            print(f"❌ Single field failed: {e}")
            return

        # Test with two fields
        print("\nTesting two field addition...")
        try:
            fields_2 = {'id': int_validator, 'name': string_validator}
            model_2 = create_model(name="Test2", fields=fields_2)
            print(f"✅ Two field model: {model_2}")
        except Exception as e:
            print(f"❌ Two field failed: {e}")
            import traceback
            traceback.print_exc()
            return

        # Test with three fields
        print("\nTesting three field addition...")
        try:
            float_validator = create_int_validator()  # Use int as float for now
            fields_3 = {'id': int_validator, 'name': string_validator, 'score': float_validator}
            model_3 = create_model(name="Test3", fields=fields_3)
            print(f"✅ Three field model: {model_3}")
        except Exception as e:
            print(f"❌ Three field failed: {e}")
            import traceback
            traceback.print_exc()
            return

        print("\n✅ All tests passed!")

    except Exception as e:
        print(f"❌ Error importing: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_c_model()
