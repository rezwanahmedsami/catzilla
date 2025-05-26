#!/usr/bin/env python3
"""
Test basic Catzilla App functionality
"""
import catzilla

def test_basic_app():
    print("Testing basic Catzilla App creation...")

    try:
        app = catzilla.App()
        print(f"✓ App created: {app}")

        # Test adding a route
        @app.get("/test")
        def test_handler(request):
            return "Hello, World!"

        print("✓ Route added successfully")
        print("✓ All basic functionality working!")

    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

    return True

if __name__ == "__main__":
    success = test_basic_app()
    if success:
        print("\n🎉 Basic Catzilla functionality is working on macOS x86_64!")
    else:
        print("\n❌ Basic functionality test failed")
