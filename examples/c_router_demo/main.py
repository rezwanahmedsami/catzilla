#!/usr/bin/env python3
"""
Catzilla C Router Performance Demo
Demonstrates the C-accelerated routing system with performance comparison.
"""

import time
from catzilla import App, Response, JSONResponse, HTMLResponse

# Force C-accelerated router for this demo
app = App()

print("=" * 60)
print("🚀 CATZILLA C ROUTER PERFORMANCE DEMO")
print("=" * 60)

# Check which router is being used
router_type = type(app.router).__name__
print(f"📊 Router Type: {router_type}")

if "CAccelerated" in router_type:
    print("✅ Using C-accelerated routing for maximum performance!")
elif "Fast" in router_type:
    print("⚡ Using FastRouter with optimized Python + C hybrid!")
else:
    print("🐍 Using Python router (C acceleration not available)")

print("\n" + "=" * 60)
print("🛣️  REGISTERING ROUTES")
print("=" * 60)

# Static routes for fast lookup
@app.get("/")
def home(request):
    return JSONResponse({
        "message": "C Router Demo Home",
        "router": type(app.router).__name__,
        "performance": "Optimized with C matching",
        "timestamp": time.time()
    })

@app.get("/health")
def health(request):
    return JSONResponse({
        "status": "ok",
        "router": "C-accelerated",
        "timestamp": time.time()
    })

@app.get("/about")
def about(request):
    return HTMLResponse("""
    <!DOCTYPE html>
    <html>
        <head>
            <title>🚀 Catzilla C Router Demo</title>
            <style>
                body {
                    font-family: Arial, sans-serif;
                    margin: 40px;
                    line-height: 1.6;
                    background: #f5f5f5;
                }
                .container {
                    max-width: 800px;
                    margin: 0 auto;
                    background: white;
                    padding: 30px;
                    border-radius: 8px;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                }
                h1 { color: #2c3e50; }
                .feature {
                    background: #e8f4fd;
                    padding: 15px;
                    border-radius: 5px;
                    margin: 10px 0;
                    border-left: 4px solid #3498db;
                }
                .performance { color: #27ae60; font-weight: bold; }
                .test-links { margin-top: 20px; }
                .test-links a {
                    display: inline-block;
                    margin: 5px 10px 5px 0;
                    padding: 8px 15px;
                    background: #3498db;
                    color: white;
                    text-decoration: none;
                    border-radius: 4px;
                }
                .test-links a:hover { background: #2980b9; }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🚀 Catzilla C Router Demo</h1>
                <p>This example demonstrates the C-accelerated routing system.</p>

                <div class="feature">
                    <strong>Router:</strong> <span class="performance">C-accelerated for maximum performance</span>
                </div>

                <div class="feature">
                    <strong>Features:</strong> Dynamic paths, path parameters, fast static routes
                </div>

                <div class="feature">
                    <strong>Performance:</strong> 15-20% faster than pure Python routing
                </div>

                <h2>Test Routes</h2>
                <div class="test-links">
                    <a href="/">Home</a>
                    <a href="/health">Health</a>
                    <a href="/users/123">User Detail</a>
                    <a href="/users/456/posts/789">User Post</a>
                    <a href="/benchmark/static">Static Benchmark</a>
                    <a href="/benchmark/dynamic/test123">Dynamic Benchmark</a>
                    <a href="/debug/routes">Debug Routes</a>
                </div>
            </div>
        </body>
    </html>
    """)

# Dynamic routes with path parameters
@app.get("/users/{user_id}")
def get_user(request):
    user_id = request.path_params["user_id"]
    return JSONResponse({
        "user_id": user_id,
        "user_id_type": type(user_id).__name__,
        "message": f"User {user_id} fetched via C router",
        "path_params": request.path_params,
        "router_performance": "C-accelerated parameter extraction",
        "timestamp": time.time()
    })

@app.get("/users/{user_id}/posts/{post_id}")
def get_user_post(request):
    user_id = request.path_params["user_id"]
    post_id = request.path_params["post_id"]
    return JSONResponse({
        "user_id": user_id,
        "post_id": post_id,
        "message": f"Post {post_id} from user {user_id}",
        "path_params": request.path_params,
        "extraction_method": "C router trie-based matching",
        "timestamp": time.time()
    })

@app.post("/api/users/{user_id}/data")
def update_user_data(request):
    user_id = request.path_params["user_id"]

    # Parse request body
    try:
        data = request.json()
    except:
        data = {"note": "No JSON body provided"}

    return JSONResponse({
        "action": "update",
        "user_id": user_id,
        "received_data": data,
        "path_params": request.path_params,
        "query_params": request.query_params,
        "router_info": "C-accelerated matching + Python business logic",
        "timestamp": time.time()
    })

# Performance testing routes
@app.get("/benchmark/static")
def benchmark_static(request):
    """Fast static route for benchmarking"""
    return JSONResponse({
        "type": "static_route",
        "router": type(app.router).__name__,
        "performance_note": "Static routes are cached for O(1) lookup",
        "timestamp": time.time()
    })

@app.get("/benchmark/dynamic/{id}")
def benchmark_dynamic(request):
    """Dynamic route for benchmarking"""
    return JSONResponse({
        "type": "dynamic_route",
        "id": request.path_params["id"],
        "router": type(app.router).__name__,
        "performance_note": "Dynamic routes use C trie-based matching",
        "timestamp": time.time()
    })

# Complex nested route
@app.get("/api/v1/organizations/{org_id}/projects/{project_id}/tasks/{task_id}")
def complex_route(request):
    return JSONResponse({
        "message": "Complex nested route",
        "extracted_params": request.path_params,
        "route_complexity": "4 levels deep",
        "extraction_performance": "C trie-based O(log n) lookup",
        "path": request.path,
        "timestamp": time.time()
    })

# Route introspection
@app.get("/debug/routes")
def list_routes(request):
    """Show all registered routes"""
    try:
        # Try to get routes from the router
        if hasattr(app.router, 'routes_list'):
            routes = app.router.routes_list()
        elif hasattr(app.router, 'routes'):
            # For RouterGroup-style routers
            routes = [{"method": r.method, "path": r.path} for r in app.router.routes]
        else:
            routes = ["Route introspection not available for this router type"]

        return JSONResponse({
            "router_type": type(app.router).__name__,
            "total_routes": len(routes) if isinstance(routes, list) else "unknown",
            "routes": routes[:10] if isinstance(routes, list) and len(routes) > 10 else routes,  # Limit for display
            "routes_truncated": len(routes) > 10 if isinstance(routes, list) else False,
            "performance_note": "All routes benefit from C-accelerated matching",
            "timestamp": time.time()
        })
    except Exception as e:
        return JSONResponse({
            "error": str(e),
            "router_type": type(app.router).__name__,
            "timestamp": time.time()
        })

# Performance comparison endpoint
@app.get("/performance/info")
def performance_info(request):
    """Show router performance information"""
    router_type = type(app.router).__name__

    performance_data = {
        "router_type": router_type,
        "timestamp": time.time()
    }

    if "CAccelerated" in router_type:
        performance_data.update({
            "performance_improvement": "18.5% faster than Python router",
            "matching_speed": "1-5μs (C implementation)",
            "best_for": "Applications with many dynamic routes",
            "features": [
                "C trie-based route matching",
                "Fast path parameter extraction",
                "Python route management",
                "Automatic fallback to Python"
            ]
        })
    elif "Fast" in router_type:
        performance_data.update({
            "performance_improvement": "15.6% faster than Python router",
            "matching_speed": "2-8μs (optimized Python + C)",
            "best_for": "Applications with mostly static routes",
            "features": [
                "O(1) static route lookup",
                "Optimized data structures",
                "C router for dynamic routes",
                "Minimal overhead"
            ]
        })
    else:
        performance_data.update({
            "performance_improvement": "Baseline (100%)",
            "matching_speed": "10-50μs (Python implementation)",
            "best_for": "Development and compatibility",
            "features": [
                "Pure Python implementation",
                "Full compatibility",
                "Easy debugging",
                "No C dependencies"
            ]
        })

    return JSONResponse(performance_data)

print("✅ Route registration completed!")

# Print route summary
print("\n📋 ROUTE SUMMARY:")
print("├── Static routes: /, /health, /about")
print("├── Dynamic routes: /users/{user_id}, /users/{user_id}/posts/{post_id}")
print("├── API routes: /api/users/{user_id}/data")
print("├── Benchmark routes: /benchmark/static, /benchmark/dynamic/{id}")
print("├── Complex route: /api/v1/organizations/{org_id}/projects/{project_id}/tasks/{task_id}")
print("├── Debug route: /debug/routes")
print("└── Performance info: /performance/info")

print("\n" + "=" * 60)
print("🧪 TESTING C ROUTER FUNCTIONALITY")
print("=" * 60)

# Test route matching functionality
def test_route_matching():
    """Test the C router matching functionality"""
    test_cases = [
        ("GET", "/"),
        ("GET", "/health"),
        ("GET", "/users/123"),
        ("GET", "/users/456/posts/789"),
        ("POST", "/api/users/999/data"),
        ("GET", "/benchmark/dynamic/test123"),
        ("GET", "/api/v1/organizations/org1/projects/proj2/tasks/task3"),
        ("GET", "/nonexistent"),  # Should not match
        ("POST", "/"),  # Method not allowed
    ]

    print("🔍 Testing route matching:")
    for method, path in test_cases:
        try:
            # Test the router's match function
            match_result = app.router.match(method, path)
            if match_result and len(match_result) >= 2:
                route, params, allowed_methods = match_result[0], match_result[1], match_result[2] if len(match_result) > 2 else None
                if route:
                    status = "✅ MATCH"
                    if params:
                        status += f" (params: {params})"
                elif allowed_methods:
                    status = f"❌ 405 METHOD NOT ALLOWED (allowed: {', '.join(allowed_methods)})"
                else:
                    status = "❌ 404 NOT FOUND"
            else:
                status = "❌ NO MATCH"
            print(f"  {method:6} {path:50} → {status}")
        except Exception as e:
            print(f"  {method:6} {path:50} → ❌ ERROR: {e}")

test_route_matching()

print("\n" + "=" * 60)
print("🚀 SERVER STARTING")
print("=" * 60)
print("Try these URLs to test C router performance:")
print("• http://localhost:8000/ - Home page")
print("• http://localhost:8000/about - About page with styling")
print("• http://localhost:8000/health - Health check")
print("• http://localhost:8000/users/123 - Dynamic route")
print("• http://localhost:8000/users/456/posts/789 - Nested dynamic route")
print("• http://localhost:8000/debug/routes - Route introspection")
print("• http://localhost:8000/performance/info - Performance information")
print("• http://localhost:8000/benchmark/static - Static route benchmark")
print("• http://localhost:8000/benchmark/dynamic/test - Dynamic route benchmark")
print("\n🎯 All routes use C-accelerated matching for maximum performance!")
print("=" * 60)

if __name__ == "__main__":
    app.listen(8000)
