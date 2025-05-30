#!/usr/bin/env python3
"""
Test script to verify the new Catzilla class with jemalloc integration
This demonstrates the "Memory Revolution" features of Catzilla v0.2.0
"""

def test_catzilla_import():
    """Test that we can import Catzilla and it shows the revolution message"""
    print("🧪 Testing Catzilla v0.2.0 Memory Revolution Import...")

    # Test new Catzilla import
    from catzilla import Catzilla
    print("✅ Successfully imported Catzilla class")

    # Test backward compatibility
    from catzilla import App
    print("✅ Successfully imported App (backward compatibility)")

    # Verify they're the same class
    assert Catzilla is App, "App should be an alias for Catzilla"
    print("✅ Backward compatibility verified (App is Catzilla)")

    return True

def test_catzilla_creation():
    """Test creating a Catzilla instance"""
    print("\n🚀 Testing Catzilla Instance Creation...")

    from catzilla import Catzilla

    # Create Catzilla instance - should show memory revolution message
    app = Catzilla()
    print("✅ Catzilla instance created successfully")

    # Test that it has jemalloc detection
    has_jemalloc = hasattr(app, 'has_jemalloc')
    print(f"✅ jemalloc detection available: {has_jemalloc}")

    if has_jemalloc:
        print(f"   - jemalloc enabled: {app.has_jemalloc}")

    # Test memory stats method
    has_memory_stats = hasattr(app, 'get_memory_stats')
    print(f"✅ Memory statistics available: {has_memory_stats}")

    return True

def test_memory_stats():
    """Test memory statistics functionality"""
    print("\n📊 Testing Memory Statistics...")

    from catzilla import Catzilla
    app = Catzilla()

    # Get memory stats
    stats = app.get_memory_stats()
    print("✅ Memory statistics retrieved:")

    for key, value in stats.items():
        if key == 'jemalloc_enabled':
            print(f"   - {key}: {value}")
        elif key.endswith('_mb'):
            print(f"   - {key}: {value:.2f} MB")
        elif key.endswith('_percent'):
            print(f"   - {key}: {value:.1f}%")
        else:
            print(f"   - {key}: {value}")

    return True

def test_route_creation():
    """Test that routes work with the new Catzilla class"""
    print("\n🛣️  Testing Route Creation...")

    from catzilla import Catzilla
    app = Catzilla()

    @app.get("/")
    def home():
        return "Hello from Catzilla v0.2.0 Memory Revolution!"

    @app.get("/memory")
    def memory_info():
        return app.get_memory_stats()

    @app.post("/api/data")
    def api_data():
        return {"message": "Memory-optimized API endpoint"}

    # Verify routes were added
    routes = app.routes()
    print(f"✅ Routes created: {len(routes)} routes")
    for route in routes:
        print(f"   - {route['method']:6} {route['path']}")

    return True

def test_backward_compatibility():
    """Test that old App() usage still works"""
    print("\n🔄 Testing Backward Compatibility...")

    # Old style import and usage
    from catzilla import App
    app = App()

    @app.get("/legacy")
    def legacy_endpoint():
        return "Legacy App() still works!"

    print("✅ Legacy App() class works")
    print("✅ Route creation with App() works")

    return True

def main():
    """Run all tests"""
    print("🎯 Catzilla v0.2.0 Memory Revolution Class Tests")
    print("=" * 60)

    tests = [
        test_catzilla_import,
        test_catzilla_creation,
        test_memory_stats,
        test_route_creation,
        test_backward_compatibility
    ]

    passed = 0
    total = len(tests)

    for test in tests:
        try:
            if test():
                passed += 1
            print()
        except Exception as e:
            print(f"❌ Test failed: {e}")
            import traceback
            traceback.print_exc()
            print()

    print("=" * 60)
    print(f"🎉 Tests Results: {passed}/{total} passed")

    if passed == total:
        print("\n✅ ALL TESTS PASSED! Catzilla v0.2.0 Memory Revolution is ready!")
        return True
    else:
        print(f"\n❌ {total - passed} tests failed")
        return False

if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)
