"""
Simple Per-Route Middleware Example - FastAPI Style

This example demonstrates the correct FastAPI-style per-route middleware API in Catzilla.
Uses @app.get(), @app.post(), etc. decorators with middleware parameter.
"""

from catzilla import Catzilla, Request, Response, JSONResponse
from typing import List, Optional, Callable
import time

# Initialize Catzilla
app = Catzilla(use_jemalloc=True)

# =====================================================
# SIMPLE MIDDLEWARE FUNCTIONS
# =====================================================

def timing_middleware(request: Request, response: Response) -> Optional[Response]:
    """Add response timing"""
    start_time = time.time()
    request.state.start_time = start_time

    # Process request (this runs after the route handler)
    if hasattr(request.state, 'start_time'):
        duration = time.time() - request.state.start_time
        response.headers['X-Response-Time'] = f"{duration*1000:.2f}ms"

    return None


def cors_middleware(request: Request, response: Response) -> Optional[Response]:
    """Add CORS headers"""
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE'
    return None


def auth_middleware(request: Request, response: Response) -> Optional[Response]:
    """Simple authentication check"""
    api_key = request.headers.get('Authorization')
    if not api_key or api_key != 'Bearer secret_key':
        return JSONResponse({"error": "Unauthorized"}, status_code=401)

    request.state.authenticated = True
    return None


# =====================================================
# FASTAPI-STYLE ROUTES WITH PER-ROUTE MIDDLEWARE
# =====================================================

# Route with no middleware
@app.get("/")
def home(request):
    return JSONResponse({"message": "Hello from Catzilla!"})


# Route with single middleware
@app.get("/time", middleware=[timing_middleware])
def with_timing(request):
    return JSONResponse({"message": "This response includes timing"})


# Route with multiple middleware
@app.get("/public", middleware=[timing_middleware, cors_middleware])
def public_endpoint(request):
    return JSONResponse({"message": "Public endpoint with CORS and timing"})


# Protected route with auth middleware
@app.get("/protected", middleware=[auth_middleware, timing_middleware])
def protected_endpoint(request):
    return JSONResponse({
        "message": "Protected endpoint",
        "authenticated": request.state.authenticated
    })


# POST route with middleware
@app.post("/api/data", middleware=[auth_middleware, cors_middleware])
def create_data(request):
    return JSONResponse({"message": "Data created", "method": "POST"})


# PUT route with middleware
@app.put("/api/data/{item_id}", middleware=[auth_middleware, timing_middleware])
def update_data(request):
    item_id = request.path_params.get('item_id')
    return JSONResponse({"message": f"Updated item {item_id}"})


# DELETE route with middleware
@app.delete("/api/data/{item_id}", middleware=[auth_middleware])
def delete_data(request):
    item_id = request.path_params.get('item_id')
    return JSONResponse({"message": f"Deleted item {item_id}"})


if __name__ == "__main__":
    print("🚀 Simple FastAPI-Style Per-Route Middleware Demo")
    print("📋 Routes:")
    print("   GET  /              - No middleware")
    print("   GET  /time          - With timing middleware")
    print("   GET  /public        - With timing + CORS middleware")
    print("   GET  /protected     - With auth + timing middleware")
    print("   POST /api/data      - With auth + CORS middleware")
    print("   PUT  /api/data/{id} - With auth + timing middleware")
    print("   DELETE /api/data/{id} - With auth middleware")
    print("\n🔑 Use 'Authorization: Bearer secret_key' for protected routes")
    print("\n✅ Correct FastAPI-style syntax:")
    print("   @app.get('/path', middleware=[middleware1, middleware2])")
    print("   @app.post('/path', middleware=[middleware1])")

    app.run(host="0.0.0.0", port=8000)
