#!/usr/bin/env python3
"""
Comprehensive wheel import test for Catzilla
This test ensures the wheel can be imported and basic functionality works
"""

import sys
import traceback

def test_basic_import():
    """Test basic module import"""
    try:
        import catzilla
        print("✅ Basic catzilla module import successful")
        return True
    except Exception as e:
        print(f"❌ Basic import failed: {e}")
        traceback.print_exc()
        return False

def test_core_classes():
    """Test core class imports"""
    try:
        from catzilla import App, JSONResponse, HTMLResponse, RouterGroup
        print("✅ Core class imports successful")
        return True
    except Exception as e:
        print(f"❌ Core class imports failed: {e}")
        traceback.print_exc()
        return False

def test_app_creation():
    """Test App creation and basic functionality"""
    try:
        from catzilla import App, JSONResponse

        app = App()
        print("✅ App creation successful")

        # Test route registration
        @app.get('/test')
        def test_handler(request):
            return JSONResponse({'status': 'ok', 'test': 'wheel_import'})

        print("✅ Route registration successful")
        return True
    except Exception as e:
        print(f"❌ App creation/route registration failed: {e}")
        traceback.print_exc()
        return False

def test_c_extension():
    """Test C extension import"""
    try:
        from catzilla import _catzilla
        print("✅ C extension import successful")
        return True
    except Exception as e:
        print(f"❌ C extension import failed: {e}")
        traceback.print_exc()
        return False

def test_router_group():
    """Test RouterGroup functionality"""
    try:
        from catzilla import App, RouterGroup, JSONResponse

        app = App()
        api = RouterGroup(prefix="/api/v1")

        @api.get("/test")
        def api_test(request):
            return JSONResponse({'api': 'test'})

        app.include_routes(api)
        print("✅ RouterGroup functionality successful")
        return True
    except Exception as e:
        print(f"❌ RouterGroup functionality failed: {e}")
        traceback.print_exc()
        return False

def main():
    """Run all wheel import tests"""
    print("🧪 Running Catzilla wheel import tests...")

    tests = [
        test_basic_import,
        test_core_classes,
        test_app_creation,
        test_c_extension,
        test_router_group,
    ]

    all_passed = True

    for i, test in enumerate(tests, 1):
        print(f"\n[{i}/{len(tests)}] {test.__doc__}")
        if not test():
            all_passed = False

    print("\n" + "="*50)
    if all_passed:
        print("🎉 All wheel import tests PASSED!")
        print("✅ Wheel is ready for distribution")
        sys.exit(0)
    else:
        print("❌ Some wheel import tests FAILED!")
        print("🚫 Wheel is NOT ready for distribution")
        sys.exit(1)

if __name__ == "__main__":
    main()
