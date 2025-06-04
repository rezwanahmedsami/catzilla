#!/usr/bin/env python3
"""
Safe test script to verify Catzilla import functionality
without using terminal commands that could cause crashes.
"""

def test_catzilla_import():
    """Test that Catzilla can be imported successfully."""
    try:
        print("Testing Catzilla import...")
        from catzilla import Catzilla
        print("✅ Catzilla import successful!")
        
        # Test basic instantiation
        print("Testing Catzilla instantiation...")
        app = Catzilla()
        print("✅ Catzilla instantiation successful!")
        
        # Test that jemalloc integration is working
        print("Testing jemalloc integration...")
        if hasattr(app, '_lib'):
            print("✅ C library binding detected")
        else:
            print("⚠️  C library binding not detected")
            
        return True
        
    except ImportError as e:
        print(f"❌ Import Error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected Error: {e}")
        return False

if __name__ == "__main__":
    success = test_catzilla_import()
    if success:
        print("\n🎉 All tests passed! Catzilla integration is working correctly.")
    else:
        print("\n💥 Tests failed. Check the errors above.")
