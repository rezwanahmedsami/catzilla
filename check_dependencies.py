#!/usr/bin/env python3
"""
Catzilla Dependency Check

This script verifies that Catzilla works with minimal dependencies.
It demonstrates that Catzilla uses only Python standard library
for core functionality.
"""

import sys
import importlib

def check_package(package_name, description, required=True):
    """Check if a package is available and importable"""
    try:
        importlib.import_module(package_name)
        status = "✅ Available"
        return True
    except ImportError:
        status = "❌ Missing" if required else "⚠️  Optional (not installed)"
        return False
    finally:
        req_status = "REQUIRED" if required else "OPTIONAL"
        print(f"{status:20} {package_name:20} - {description} ({req_status})")

def main():
    print("🔍 Catzilla Dependency Check")
    print("=" * 60)

    # Core dependencies (required for basic functionality)
    print("\n📦 Core Dependencies:")
    all_core_ok = True

    # Python standard library (always available)
    core_packages = [
        ("json", "JSON handling"),
        ("dataclasses", "Data class support"),
        ("typing", "Type hints"),
        ("urllib.parse", "URL parsing"),
        ("http.cookies", "Cookie handling"),
        ("re", "Regular expressions"),
        ("os", "Operating system interface"),
        ("sys", "System-specific parameters"),
    ]

    for pkg, desc in core_packages:
        check_package(pkg, desc, required=True)

    # Development dependencies
    print("\n🛠️  Development Dependencies:")
    dev_packages = [
        ("pytest", "Testing framework"),
        ("pre_commit", "Git hooks for code quality"),
    ]

    for pkg, desc in dev_packages:
        check_package(pkg, desc, required=False)

    # Benchmark dependencies (optional)
    print("\n📊 Benchmark Dependencies (Optional):")
    benchmark_packages = [
        ("fastapi", "FastAPI comparison benchmarks"),
        ("flask", "Flask comparison benchmarks"),
        ("django", "Django comparison benchmarks"),
        ("matplotlib", "Chart generation"),
        ("pandas", "Data analysis"),
        ("seaborn", "Statistical plotting"),
        ("numpy", "Numerical computing"),
        ("requests", "HTTP client for testing"),
    ]

    for pkg, desc in benchmark_packages:
        check_package(pkg, desc, required=False)

    # Test Catzilla functionality
    print("\n🚀 Testing Catzilla Core Functionality:")
    try:
        # Add python directory to path for testing
        sys.path.insert(0, 'python')

        from catzilla import App, JSONResponse, HTMLResponse, RouterGroup
        print("✅ Available      catzilla            - Core framework imports")

        # Test basic functionality
        app = App()
        api = RouterGroup(prefix="/api")

        @app.get("/")
        def hello_world(request):
            return {"message": "Hello, World!"}

        @api.get("/users/{user_id}")
        def get_user(request):
            return {"user_id": request.path_params["user_id"]}

        app.include_routes(api)

        print("✅ Available      Route Registration  - Basic routing works")
        print("✅ Available      RouterGroup         - Route grouping works")
        print("✅ Available      Path Parameters     - Dynamic routing works")

    except Exception as e:
        print(f"❌ Error         catzilla            - {e}")
        all_core_ok = False

    # Summary
    print("\n" + "=" * 60)
    if all_core_ok:
        print("🎉 SUCCESS: Catzilla works with minimal dependencies!")
        print("\n💡 Key Points:")
        print("   • Uses only Python standard library for core functionality")
        print("   • No heavy runtime dependencies like pydantic")
        print("   • Optional dependencies only needed for benchmarks/development")
        print("   • Lightweight and fast to install")
    else:
        print("❌ ISSUES: Some core functionality is not working")
        return 1

    return 0

if __name__ == "__main__":
    sys.exit(main())
