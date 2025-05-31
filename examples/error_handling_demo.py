#!/usr/bin/env python3
"""
Catzilla Error Handling Example

This example demonstrates all three key error handling features:
1. Production-mode clean JSON error responses
2. Central exception handler support
3. Global fallback 404 and 500 handlers
"""

import sys
import os

# Add the catzilla package to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'python'))

from catzilla import Catzilla, JSONResponse, HTMLResponse


def create_app():
    """Create and configure a Catzilla app with error handling"""

    # Create app with production mode (clean JSON errors)
    app = Catzilla(production=True, auto_validation=True, memory_profiling=False)  # Set to False for debug mode with detailed errors

    # ========================================
    # 1. BASIC ROUTES THAT CAN CAUSE ERRORS
    # ========================================

    @app.get("/")
    def home(request):
        return {"message": "Welcome to Catzilla Error Handling Demo!"}

    @app.get("/error/value")
    def trigger_value_error(request):
        # This will trigger a ValueError
        raise ValueError("This is a custom ValueError for testing")

    @app.get("/error/runtime")
    def trigger_runtime_error(request):
        # This will trigger a RuntimeError
        raise RuntimeError("Something went wrong in the application")

    @app.get("/error/division")
    def trigger_zero_division(request):
        # This will trigger a ZeroDivisionError
        result = 1 / 0
        return {"result": result}

    # ========================================
    # 2. CUSTOM EXCEPTION HANDLERS
    # ========================================

    def handle_value_error(request, exc):
        """Custom handler for ValueError exceptions"""
        return JSONResponse({
            "error": "Invalid Value",
            "message": str(exc),
            "path": request.path,
            "type": "ValueError"
        }, status_code=400)

    def handle_division_error(request, exc):
        """Custom handler for ZeroDivisionError exceptions"""
        return JSONResponse({
            "error": "Math Error",
            "message": "Division by zero is not allowed",
            "path": request.path,
            "type": "ZeroDivisionError"
        }, status_code=400)

    # Register the exception handlers
    app.set_exception_handler(ValueError, handle_value_error)
    app.set_exception_handler(ZeroDivisionError, handle_division_error)

    # ========================================
    # 3. GLOBAL 404 HANDLER
    # ========================================

    def custom_404_handler(request):
        """Custom 404 Not Found handler"""
        return JSONResponse({
            "error": "Route Not Found",
            "message": f"The requested path '{request.path}' does not exist",
            "path": request.path,
            "available_routes": [
                "/",
                "/error/value",
                "/error/runtime",
                "/error/division"
            ]
        }, status_code=404)

    app.set_not_found_handler(custom_404_handler)

    # ========================================
    # 4. GLOBAL 500 HANDLER
    # ========================================

    def custom_500_handler(request, exc):
        """Custom 500 Internal Server Error handler"""
        return JSONResponse({
            "error": "Internal Server Error",
            "message": "An unexpected error occurred",
            "path": request.path,
            "exception_type": type(exc).__name__,
            # Only include details in development mode
            "details": str(exc) if not app.production else None
        }, status_code=500)

    app.set_internal_error_handler(custom_500_handler)

    return app


def main():
    """Run the Catzilla error handling demo"""
    app = create_app()

    print("🚀 Catzilla Error Handling Demo")
    print("=" * 50)
    print(f"Production mode: {app.production}")
    print()
    print("Available endpoints:")
    print("  GET /                  - Home page")
    print("  GET /error/value       - Triggers ValueError")
    print("  GET /error/runtime     - Triggers RuntimeError")
    print("  GET /error/division    - Triggers ZeroDivisionError")
    print("  GET /nonexistent       - Triggers 404 Not Found")
    print()
    print("Error handling features:")
    print("  ✅ Production-mode clean JSON responses")
    print("  ✅ Custom exception handlers for specific types")
    print("  ✅ Global 404 and 500 fallback handlers")
    print()

    try:
        # Note: In a real app, you'd call app.listen(8000) to start the server
        # For this demo, we just show the configuration is working
        print("Error handlers configured:")
        print(f"  - Exception handlers: {len(app._exception_handlers)} types")
        print(f"  - Custom 404 handler: {'✅' if app._not_found_handler else '❌'}")
        print(f"  - Custom 500 handler: {'✅' if app._internal_error_handler else '❌'}")
        print()
        print("To start the server, uncomment: app.listen(8000)")

        # Uncomment to actually start the server:
        # app.listen(8000)

    except KeyboardInterrupt:
        print("\n👋 Server stopped")


if __name__ == "__main__":
    main()
