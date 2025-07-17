#!/usr/bin/env python3
"""
Debug script to understand HEAD route matching issue
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'python'))

from catzilla import Catzilla, JSONResponse

# Create app
app = Catzilla(show_banner=False)

# Register a simple HEAD route
@app.head("/test")
def test_head(request):
    return JSONResponse({"test": "head"})

# Register an OPTIONS route for comparison
@app.options("/test")
def test_options(request):
    return JSONResponse({"test": "options"})

print("Routes registered:")
for route in app.router.routes():
    print(f"  {route['method']} {route['path']}")

print("\nTesting route matching:")
head_route, params, allowed = app.router.match("HEAD", "/test")
print(f"HEAD /test match: {head_route}")

options_route, params, allowed = app.router.match("OPTIONS", "/test")
print(f"OPTIONS /test match: {options_route}")

# Let's also check what type of router we're using
print(f"\nRouter type: {type(app.router)}")
print(f"Router has _routes: {hasattr(app.router, '_routes')}")
if hasattr(app.router, '_routes'):
    print(f"Number of routes in _routes: {len(app.router._routes)}")
    for i, route in enumerate(app.router._routes):
        print(f"  Route {i}: {route.method} {route.path}")

print("\nDebug: Detailed route matching...")
for route in app.router._routes:
    print(f"Route: {route.method} {route.path}")
    print(f"  Method match: {route.method == 'HEAD'}")
    print(f"  Path match: {route.path == '/test'}")
    if route.method == 'HEAD':
        print(f"  Route object: {route}")
        print(f"  Route pattern: {route.pattern}")

        # Test pattern matching
        import re
        pattern = route.path
        pattern = re.sub(r"\{([^}]+)\}", r"(?P<\1>[^/]+)", pattern)
        pattern = f"^{pattern}$"
        match = re.match(pattern, "/test")
        print(f"  Pattern '{pattern}' matches '/test': {match is not None}")

        if match:
            print(f"  Match groups: {match.groupdict()}")
    print()

print("\nDebug: Router state...")
print(f"_use_c_router: {app.router._use_c_router}")
print(f"_server: {app.router._server}")
print(f"_c_routes_synced: {app.router._c_routes_synced}")

# Let's try to match directly with Python fallback
print("\nTesting Python fallback matching:")
head_route_py, params_py, allowed_py = app.router._python_fallback_match("HEAD", "/test")
print(f"Python fallback HEAD /test match: {head_route_py}")

options_route_py, params_py, allowed_py = app.router._python_fallback_match("OPTIONS", "/test")
print(f"Python fallback OPTIONS /test match: {options_route_py}")

# Test the C router directly if available
if app.router._use_c_router and app.router._server:
    print("\nTesting C router directly:")
    try:
        head_match_c = app.router._server.match_route("HEAD", "/test")
        print(f"C router HEAD /test match: {head_match_c}")

        options_match_c = app.router._server.match_route("OPTIONS", "/test")
        print(f"C router OPTIONS /test match: {options_match_c}")
    except Exception as e:
        print(f"C router error: {e}")
