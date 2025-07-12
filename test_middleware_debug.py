#!/usr/bin/env python3

from catzilla import Catzilla, Request, Response
from typing import Optional
import sys

app = Catzilla()

print("🧪 Testing middleware execution...")

def example_middleware(request: Request) -> Optional[Response]:
    """
    Example middleware that modifies the response.
    This middleware adds a custom header to the response.
    """
    print("🔥 MIDDLEWARE EXECUTED! - This means the Python-C bridge is working!")
    print(f"🔍 Middleware called with request: {type(request)}")

    # Add a header to demonstrate middleware execution
    if hasattr(request, 'headers'):
        print(f"📋 Request headers: {request.headers}")

    return None  # Continue to route handler

@app.get("/", middleware=[example_middleware])
def index(request: Request):
    """
    Example route that returns a simple response.
    The middleware will modify this response.
    """
    print("🎯 Route handler executed")
    return "Hello, World! (Middleware should have executed)"

@app.get("/test", middleware=[example_middleware])
def test_route(request: Request):
    """Test route with middleware"""
    print("🎯 Test route handler executed")
    return "Test endpoint with middleware"

# Test the middleware registration
print(f"📊 Routes registered: {len(app.router._routes)}")
for route in app.router._routes:
    print(f"  - {route.method} {route.path} | Middleware: {route.middleware}")
    if route.middleware:
        print(f"    Middleware count: {len(route.middleware)}")
        for i, mw in enumerate(route.middleware):
            print(f"    [{i}] {mw.__name__}")

if __name__ == "__main__":
    print("🚀 Starting server on http://localhost:8002")
    print("🧪 After starting, test with: curl http://localhost:8002/")
    print("🔍 Watch for 'MIDDLEWARE EXECUTED!' message")

    try:
        app.listen(port=8002)
    except KeyboardInterrupt:
        print("\n🛑 Server stopped")
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)
