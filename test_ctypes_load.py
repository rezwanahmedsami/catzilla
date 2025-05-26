"""
Test if the issue is related to global router initialization
"""
import sys
import ctypes

print(f"Python: {sys.version}")
print(f"Platform: {sys.platform}")

# Try to load the shared library directly using ctypes
try:
    # Find the library path
    import importlib.util
    spec = importlib.util.find_spec("catzilla._catzilla")
    if spec and spec.origin:
        print(f"Found _catzilla at: {spec.origin}")

        # Try to load it directly with ctypes
        print("Loading with ctypes...")
        lib = ctypes.CDLL(spec.origin)
        print("✓ Library loaded with ctypes")

        # Try to get the init function
        print("Getting PyInit__catzilla function...")
        init_func = lib.PyInit__catzilla
        print("✓ Got PyInit__catzilla function")

    else:
        print("Module not found")
        sys.exit(1)

except Exception as e:
    print(f"Error with ctypes: {e}")
    import traceback
    traceback.print_exc()
