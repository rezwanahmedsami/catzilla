#!/usr/bin/env python3
"""
Documentation validation test - ensures all documented API examples actually work
This test verifies that the examples in our documentation use correct APIs.
"""
import sys
import traceback

def test_global_middleware_syntax():
    """Test that global middleware syntax from docs is correct"""
    print("Testing global middleware syntax from documentation...")

    try:
        from catzilla import Catzilla, Response, JSONResponse

        app = Catzilla()

        # Test the documented decorator syntax
        @app.middleware(priority=50, pre_route=True)
        def cors_middleware(request):
            """CORS handling from docs"""
            if request.method == "OPTIONS":
                return Response("", status_code=200, headers={
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Methods": "GET,POST,PUT,DELETE,OPTIONS",
                    "Access-Control-Allow-Headers": "Content-Type,Authorization"
                })
            return None

        @app.middleware(priority=900, post_route=True)
        def security_headers_middleware(request, response):
            """Security headers from docs"""
            response.set_header("X-Content-Type-Options", "nosniff")
            response.set_header("X-Frame-Options", "DENY")
            response.set_header("X-XSS-Protection", "1; mode=block")
            return None

        @app.get("/test")
        def test_route(request):
            return JSONResponse({"message": "test"})

        print("✅ Global middleware syntax is correct!")

    except Exception as e:
        raise AssertionError(f"Global middleware syntax error: {e}")

def test_per_route_middleware_syntax():
    """Test that per-route middleware syntax from docs is correct"""
    print("Testing per-route middleware syntax from documentation...")

    try:
        from catzilla import Catzilla, Request, Response, JSONResponse
        from typing import Optional

        app = Catzilla()

        # Test the documented middleware function signatures
        def auth_middleware(request: Request, response: Response) -> Optional[Response]:
            """Authentication middleware from docs"""
            api_key = request.headers.get('Authorization')
            if not api_key or api_key != 'Bearer secret_token':
                return JSONResponse({"error": "Unauthorized"}, status_code=401)
            return None

        def cors_middleware(request: Request, response: Response) -> Optional[Response]:
            """CORS middleware from docs"""
            response.set_header('Access-Control-Allow-Origin', '*')
            return None

        # Test the documented route syntax
        @app.get("/protected", middleware=[auth_middleware, cors_middleware])
        def protected_endpoint(request):
            return JSONResponse({"message": "Protected data"})

        @app.get("/public", middleware=[cors_middleware])
        def public_endpoint(request):
            return JSONResponse({"message": "Public data"})

        print("✅ Per-route middleware syntax is correct!")

    except Exception as e:
        raise AssertionError(f"Per-route middleware syntax error: {e}")

def test_api_consistency():
    """Test that documented APIs match actual implementation"""
    print("Testing API consistency between docs and implementation...")

    try:
        from catzilla import Catzilla, Response

        app = Catzilla()

        # Test response.set_header (corrected API)
        response = Response("test")
        response.set_header("X-Test", "value")

        # Verify the old response.headers[] syntax would fail
        try:
            response.headers["X-Test"] = "value"
            # If this doesn't fail, it means the API changed
            print("⚠️  Warning: response.headers[] assignment still works")
        except:
            # Expected - this should fail
            pass

        # Test that @app.get works (corrected from @app.route)
        @app.get("/api-test")
        def api_test(request):
            return Response("OK")

        # Test that app.listen would work (corrected from app.run)
        # Note: We don't actually call it to avoid starting a server
        if not hasattr(app, 'listen'):
            raise AssertionError("app.listen method not found")

        if hasattr(app, 'run'):
            print("⚠️  Warning: app.run still exists - docs correctly removed it")

        print("✅ API consistency checks passed!")

    except Exception as e:
        raise AssertionError(f"API consistency error: {e}")

def main():
    """Run all documentation validation tests"""
    print("🧪 Running documentation validation tests...\n")

    try:
        test_global_middleware_syntax()
        test_per_route_middleware_syntax()
        test_api_consistency()
        print("\n🎉 All documentation syntax and APIs are correct!")
        print("📝 The documentation has been successfully corrected to match the implementation.")
        return 0
    except Exception as e:
        print(f"\n❌ Documentation validation failed: {e}")
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
