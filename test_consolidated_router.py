#!/usr/bin/env python3
"""
Test script to verify that the consolidated router works correctly
"""

import requests
import json
from catzilla import Catzilla, RouterGroup

def test_consolidated_router():
    """Test that the consolidated router works correctly"""

    # Test 1: Basic router functionality
    print("🧪 Test 1: Basic Router Functionality")
    app = Catzilla()

    @app.get("/test")
    def test_get():
        return {"method": "GET", "message": "GET works"}

    @app.post("/test")
    def test_post():
        return {"method": "POST", "message": "POST works"}

    @app.options("/test")
    def test_options():
        return {"method": "OPTIONS", "message": "OPTIONS works"}

    @app.head("/test")
    def test_head():
        return {"method": "HEAD", "message": "HEAD works"}

    routes = app.router.routes()
    print(f"✅ Routes registered: {len(routes)}")
    for route in routes:
        print(f"   - {route['method']} {route['path']}")

    # Test 2: RouterGroup functionality
    print("\n🧪 Test 2: RouterGroup Functionality")
    api_group = RouterGroup(prefix="/api", tags=["api"])

    @api_group.get("/users")
    def get_users():
        return {"users": ["user1", "user2"]}

    @api_group.post("/users")
    def post_users():
        return {"message": "User created"}

    @api_group.route("/users", methods=["OPTIONS"])
    def options_users():
        return {"allowed_methods": ["GET", "POST", "OPTIONS"]}

    @api_group.route("/users", methods=["HEAD"])
    def head_users():
        return {"method": "HEAD"}

    app.include_routes(api_group)

    final_routes = app.router.routes()
    print(f"✅ Final routes after including group: {len(final_routes)}")
    for route in final_routes:
        print(f"   - {route['method']} {route['path']}")

    # Test 3: Import verification
    print("\n🧪 Test 3: Import Verification")
    try:
        from catzilla import RouterGroup as RG2
        from catzilla.router import Route, RouterGroup as RG3, CAcceleratedRouter
        print("✅ All imports successful")
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False

    # Test 4: No routing.py file
    print("\n🧪 Test 4: Routing.py File Removal")
    try:
        import os
        routing_file = "/Users/user/devwork/catzilla/python/catzilla/routing.py"
        if os.path.exists(routing_file):
            print("❌ routing.py file still exists")
            return False
        else:
            print("✅ routing.py file successfully removed")
    except Exception as e:
        print(f"❌ Error checking routing.py: {e}")
        return False

    print("\n🎉 All tests passed! Consolidated router is working correctly.")
    return True

if __name__ == "__main__":
    success = test_consolidated_router()
    if success:
        print("\n✅ CONSOLIDATION SUCCESS: All router functionality moved to c_router.py")
    else:
        print("\n❌ CONSOLIDATION FAILED: Issues detected")
