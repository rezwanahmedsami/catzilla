"""
Async/Sync Routing Example - C-Accelerated HTTP Router with Hybrid Support

This example demonstrates Catzilla v0.2.0's async/sync handler support with
automatic detection and optimal execution.

Features demonstrated:
- Mixed async and sync handlers
- Automatic handler type detection
- Path parameters with auto-validation
- Query parameters with auto-validation
- JSON body validation with BaseModel
- Async I/O operations (simulated)
- Performance comparison
"""

from catzilla import (
    Catzilla, Request, Response, JSONResponse, BaseModel,
    Query, Header, Path, Form, ValidationError
)
from typing import Optional
import asyncio
import time

# Initialize Catzilla with C-accelerated routing and async support
app = Catzilla(
    production=False,       # Enable development features
    show_banner=True,      # Show beautiful startup banner
    log_requests=True      # Log all requests in development
)

# User model for JSON body validation
class UserCreate(BaseModel):
    """User creation model with auto-validation"""
    id: Optional[int] = 1
    name: str = "Unknown"
    email: Optional[str] = None

# Basic GET route (sync - unchanged)
@app.get("/")
def home(request: Request) -> Response:
    """Home endpoint with server information - SYNC handler"""
    return JSONResponse({
        "message": "Welcome to Catzilla v0.2.0!",
        "framework": "Catzilla v0.2.0",
        "router": "C-Accelerated with Async Support",
        "handler_type": "sync",
        "performance": "259% faster than FastAPI"
    })

# Async route with simulated I/O
@app.get("/async-home")
async def async_home(request: Request) -> Response:
    """Home endpoint with async I/O - ASYNC handler"""
    # Simulate async database/API call
    await asyncio.sleep(0.1)

    return JSONResponse({
        "message": "Welcome to Async Catzilla!",
        "framework": "Catzilla v0.2.0",
        "router": "C-Accelerated with Async Support",
        "handler_type": "async",
        "async_feature": "Non-blocking I/O",
        "simulated_io_delay": "0.1s"
    })

# Route with path parameters (sync)
@app.get("/users/{user_id}")
def get_user(request, user_id: int = Path(..., description="User ID", ge=1)) -> Response:
    """Get user by ID - SYNC handler with path parameters"""

    return JSONResponse({
        "user_id": user_id,
        "message": f"Retrieved user {user_id}",
        "path": request.path,
        "handler_type": "sync",
        "execution": "thread_pool"
    })

# Async route with path parameters and I/O
@app.get("/async-users/{user_id}")
async def get_user_async(request, user_id: int = Path(..., description="User ID", ge=1)) -> Response:
    """Get user by ID - ASYNC handler with simulated database lookup"""

    # Simulate async database call
    await asyncio.sleep(0.05)

    # Simulate fetching user data
    user_data = {
        "id": user_id,
        "name": f"User {user_id}",
        "email": f"user{user_id}@example.com",
        "created_at": "2025-01-14T10:00:00Z"
    }

    return JSONResponse({
        "user_id": user_id,
        "message": f"Retrieved user {user_id} from database",
        "path": request.path,
        "handler_type": "async",
        "execution": "event_loop",
        "user": user_data,
        "db_query_time": "0.05s"
    })

# Route with query parameters (sync)
@app.get("/search")
def search(
    request,
    q: str = Query("", description="Search query"),
    limit: int = Query(10, ge=1, le=100, description="Results limit"),
    offset: int = Query(0, ge=0, description="Results offset")
) -> Response:
    """Search endpoint - SYNC handler with query parameters"""

    return JSONResponse({
        "query": q,
        "limit": limit,
        "offset": offset,
        "handler_type": "sync",
        "results": [
            {"id": i, "title": f"Result {i}", "score": 100 - i}
            for i in range(offset, offset + min(limit, 5))
        ]
    })

# Async search with external API simulation
@app.get("/async-search")
async def async_search(
    request,
    q: str = Query("", description="Search query"),
    limit: int = Query(10, ge=1, le=100, description="Results limit"),
    offset: int = Query(0, ge=0, description="Results offset")
) -> Response:
    """Async search endpoint - ASYNC handler with external API simulation"""

    # Simulate async external API call
    await asyncio.sleep(0.2)

    # Simulate enhanced results from async processing
    results = []
    for i in range(offset, offset + min(limit, 5)):
        results.append({
            "id": i,
            "title": f"Enhanced Result {i}",
            "score": 100 - i,
            "source": "external_api",
            "relevance": f"{95 - i}%"
        })

    return JSONResponse({
        "query": q,
        "limit": limit,
        "offset": offset,
        "handler_type": "async",
        "execution": "non_blocking",
        "api_call_time": "0.2s",
        "results": results
    })

# POST route with request body (sync)
@app.post("/users")
def create_user(request, user: UserCreate) -> Response:
    """Create user - SYNC handler with JSON body validation"""

    return JSONResponse({
        "message": "User created successfully",
        "handler_type": "sync",
        "user": {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "created_at": "2025-01-14T10:00:00Z"
        }
    }, status_code=201)

# Async POST with database simulation
@app.post("/async-users")
async def create_user_async(request, user: UserCreate) -> Response:
    """Create user - ASYNC handler with database operation simulation"""

    # Simulate async database insert
    await asyncio.sleep(0.1)

    # Simulate user validation and processing
    await asyncio.sleep(0.05)

    return JSONResponse({
        "message": "User created successfully in database",
        "handler_type": "async",
        "execution": "non_blocking",
        "user": {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "created_at": "2025-01-14T10:00:00Z",
            "db_insert_time": "0.1s",
            "validation_time": "0.05s"
        }
    }, status_code=201)

# Performance comparison endpoint
@app.get("/performance-test")
async def performance_test(request: Request) -> Response:
    """Performance test - ASYNC handler that calls multiple async operations"""

    start_time = time.time()

    # Simulate multiple async operations running concurrently
    tasks = [
        asyncio.sleep(0.1),  # Database query
        asyncio.sleep(0.05), # Cache lookup
        asyncio.sleep(0.08), # External API call
        asyncio.sleep(0.03)  # Log write
    ]

    # Run all operations concurrently
    await asyncio.gather(*tasks)

    total_time = time.time() - start_time

    return JSONResponse({
        "message": "Performance test completed",
        "handler_type": "async",
        "execution": "concurrent",
        "operations": [
            {"name": "database_query", "time": "0.1s"},
            {"name": "cache_lookup", "time": "0.05s"},
            {"name": "api_call", "time": "0.08s"},
            {"name": "log_write", "time": "0.03s"}
        ],
        "sequential_time_would_be": "0.26s",
        "actual_concurrent_time": f"{total_time:.3f}s",
        "performance_gain": f"{((0.26 - total_time) / 0.26 * 100):.1f}%"
    })

# Health check endpoint (sync)
@app.get("/health")
def health_check(request: Request) -> Response:
    """Health check endpoint - SYNC handler"""
    return JSONResponse({
        "status": "healthy",
        "timestamp": "2025-01-14T10:00:00Z",
        "version": "0.2.0",
        "router": "C-Accelerated",
        "async_support": "enabled",
        "handler_type": "sync"
    })

if __name__ == "__main__":
    print("🚀 Starting Catzilla v0.2.0 Async/Sync Routing Example")
    print("⚡ Hybrid handler support: Automatic async/sync detection!")
    print()
    print("📝 Available endpoints:")
    print("   SYNC HANDLERS:")
    print("   GET  /                           - Home page (sync)")
    print("   GET  /users/{user_id}           - Get user by ID (sync)")
    print("   GET  /search?q=term&limit=10    - Search with query params (sync)")
    print("   POST /users                     - Create user (sync)")
    print("   GET  /health                    - Health check (sync)")
    print()
    print("   ASYNC HANDLERS:")
    print("   GET  /async-home                - Home page (async)")
    print("   GET  /async-users/{user_id}     - Get user with DB simulation (async)")
    print("   GET  /async-search?q=term       - Search with API simulation (async)")
    print("   POST /async-users               - Create user with DB ops (async)")
    print("   GET  /performance-test          - Concurrent operations demo (async)")
    print()
    print("🔥 Features demonstrated:")
    print("   ✅ Automatic handler type detection")
    print("   ✅ Optimal execution context (thread pool vs event loop)")
    print("   ✅ Concurrent async operations")
    print("   ✅ Mixed sync/async in same application")
    print("   ✅ Backward compatibility")
    print()
    print("🌐 Server will start on http://localhost:8000")
    print("🧪 Test with: curl http://localhost:8000/async-home")

    app.listen(port=8000, host="0.0.0.0")
