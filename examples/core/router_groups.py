"""
Router Groups Example

This example demonstrates Catzilla's router groups feature for organizing
routes hierarchically with shared prefixes and middleware.

Features demonstrated:
- Router group creation with prefixes
- Nested router groups
- Group-level middleware
- Route organization patterns
- API versioning with groups
- Auto-validation support (controlled globally by Catzilla app)

Note: Auto-validation is controlled globally by the main Catzilla app's auto_validation setting.
All RouterGroup routes automatically inherit the app's auto-validation configuration.
"""

from catzilla import (
    Catzilla, Request, Response, JSONResponse,
    Query, Header, Path, Form, ValidationError, BaseModel
)
from catzilla.router import RouterGroup

# Data models for auto-validation (works with both main app and RouterGroup)
class UserCreate(BaseModel):
    """User creation model"""
    name: str
    email: str

# Initialize Catzilla with auto-validation enabled globally
app = Catzilla(
    production=False,
    show_banner=True,
    log_requests=True,
    auto_validation=True  # Global auto-validation for all routes (app + RouterGroup)
)

# Create API v1 router group (inherits global auto-validation setting)
api_v1 = RouterGroup(prefix="/api/v1")

# Create API v2 router group (inherits global auto-validation setting)
api_v2 = RouterGroup(prefix="/api/v2")

# Create admin router group with nested structure (inherits global auto-validation setting)
admin = RouterGroup(prefix="/admin")
admin_users = RouterGroup(prefix="/users")  # Will be mounted under /admin

# Basic endpoints in main app
@app.get("/")
def root(request: Request) -> Response:
    """Root endpoint"""
    return JSONResponse({
        "message": "Catzilla Router Groups Example",
        "available_groups": ["/api/v1", "/api/v2", "/admin"],
        "framework": "Catzilla v0.2.0"
    })

# Main app endpoint with auto-validation
@app.post("/users")
def create_user_main(request, user_data: UserCreate) -> Response:
    """Create user - Main app with auto-validation"""
    return JSONResponse({
        "message": "User created via main app",
        "framework": "Catzilla v0.2.0",
        "user_id": 456,
        "user": {
            "name": user_data.name,
            "email": user_data.email
        },
        "validation": "automatic"
    }, status_code=201)

# API v1 endpoints
@api_v1.get("/users")
def list_users_v1(request: Request) -> Response:
    """List users - API v1"""
    return JSONResponse({
        "users": [
            {"id": 1, "name": "Alice", "email": "alice@example.com"},
            {"id": 2, "name": "Bob", "email": "bob@example.com"}
        ],
        "version": "v1",
        "total": 2
    })

@api_v1.get("/users/{user_id}")
def get_user_v1(request, user_id: int = Path(..., description="User ID", ge=1)) -> Response:
    """Get user by ID - API v1"""

    return JSONResponse({
        "user": {
            "id": user_id,
            "name": f"User {user_id}",
            "email": f"user{user_id}@example.com"
        },
        "version": "v1"
    })

@api_v1.post("/users")
def create_user_v1(request, user: UserCreate) -> Response:
    """Create user - API v1 with auto-validation"""
    return JSONResponse({
        "message": "User created",
        "version": "v1",
        "user_id": 123,
        "user": {"name": user.name, "email": user.email}
    }, status_code=201)

# API v2 endpoints with enhanced features
@api_v2.get("/users")
def list_users_v2(
    request,
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(10, ge=1, le=100, description="Items per page")
) -> Response:
    """List users - API v2 with pagination"""

    return JSONResponse({
        "users": [
            {
                "id": i,
                "name": f"User {i}",
                "email": f"user{i}@example.com",
                "profile": {"active": True, "premium": i % 3 == 0}
            }
            for i in range((page-1)*limit + 1, page*limit + 1)
        ],
        "version": "v2",
        "pagination": {
            "page": page,
            "limit": limit,
            "total": 1000
        }
    })

@api_v2.get("/users/{user_id}")
def get_user_v2(request, user_id: int = Path(..., description="User ID", ge=1)) -> Response:
    """Get user by ID - API v2 with enhanced data"""

    return JSONResponse({
        "user": {
            "id": user_id,
            "name": f"User {user_id}",
            "email": f"user{user_id}@example.com",
            "profile": {
                "active": True,
                "premium": user_id % 3 == 0,
                "last_login": "2024-01-15T10:30:00Z"
            },
            "settings": {
                "notifications": True,
                "theme": "dark"
            }
        },
        "version": "v2"
    })

@api_v2.patch("/users/{user_id}")
def update_user_v2(request, user_id: int = Path(..., description="User ID", ge=1)) -> Response:
    """Update user - API v2 only"""

    return JSONResponse({
        "message": "User updated",
        "user_id": user_id,
        "version": "v2",
        "updated_fields": ["profile", "settings"]
    })

# Admin router group endpoints
@admin.get("/dashboard")
def admin_dashboard(request: Request) -> Response:
    """Admin dashboard"""
    return JSONResponse({
        "dashboard": "Admin Dashboard",
        "stats": {
            "total_users": 1000,
            "active_sessions": 150,
            "system_health": "excellent"
        }
    })

@admin.get("/stats")
def admin_stats(request: Request) -> Response:
    """Admin statistics"""
    return JSONResponse({
        "statistics": {
            "requests_today": 25000,
            "errors_today": 5,
            "avg_response_time": "45ms",
            "uptime": "99.9%"
        }
    })

# Nested admin users group
@admin_users.get("/")
def admin_list_users(request: Request) -> Response:
    """Admin: List all users with admin data"""
    return JSONResponse({
        "admin_users": [
            {
                "id": i,
                "name": f"User {i}",
                "email": f"user{i}@example.com",
                "status": "active" if i % 2 == 0 else "inactive",
                "role": "admin" if i % 10 == 0 else "user",
                "last_login": "2024-01-15T10:30:00Z"
            }
            for i in range(1, 11)
        ],
        "admin_view": True,
        "total": 10
    })

@admin_users.delete("/{user_id}")
def admin_delete_user(request, user_id: int = Path(..., description="User ID", ge=1)) -> Response:
    """Admin: Delete user"""

    return JSONResponse({
        "message": f"User {user_id} deleted by admin",
        "admin_action": True,
        "user_id": user_id
    })

# Register nested group - admin_users under admin BEFORE registering admin with main app
admin.include_group(admin_users)

# Register router groups with the main app
app.include_routes(api_v1)
app.include_routes(api_v2)
app.include_routes(admin)

# Group information endpoint
@app.get("/groups")
def list_groups(request: Request) -> Response:
    """List all mounted router groups"""
    return JSONResponse({
        "router_groups": {
            "api_v1": {
                "prefix": "/api/v1",
                "endpoints": [
                    "GET /api/v1/users",
                    "GET /api/v1/users/{user_id}",
                    "POST /api/v1/users"
                ]
            },
            "api_v2": {
                "prefix": "/api/v2",
                "endpoints": [
                    "GET /api/v2/users",
                    "GET /api/v2/users/{user_id}",
                    "PATCH /api/v2/users/{user_id}"
                ]
            },
            "admin": {
                "prefix": "/admin",
                "endpoints": [
                    "GET /admin/dashboard",
                    "GET /admin/stats"
                ],
                "nested_groups": {
                    "admin_users": {
                        "prefix": "/admin/users",
                        "endpoints": [
                            "GET /admin/users/",
                            "DELETE /admin/users/{user_id}"
                        ]
                    }
                }
            }
        }
    })

if __name__ == "__main__":
    print("🚨 Starting Catzilla Router Groups Example")
    print("📝 Available router groups and endpoints:")
    print()
    print("🏠 Main App:")
    print("   GET  /                    - Root endpoint")
    print("   POST /users               - Create user (auto-validation)")
    print("   GET  /groups              - List all router groups")
    print()
    print("🔗 API v1 Group (/api/v1):")
    print("   GET  /api/v1/users        - List users (v1)")
    print("   GET  /api/v1/users/{id}   - Get user (v1, auto-validation)")
    print("   POST /api/v1/users        - Create user (v1, auto-validation)")
    print()
    print("🔗 API v2 Group (/api/v2):")
    print("   GET  /api/v2/users        - List users with pagination (v2, auto-validation)")
    print("   GET  /api/v2/users/{id}   - Get user with enhanced data (v2, auto-validation)")
    print("   PATCH /api/v2/users/{id}  - Update user (v2, auto-validation)")
    print()
    print("🔗 Admin Group (/admin):")
    print("   GET  /admin/dashboard     - Admin dashboard")
    print("   GET  /admin/stats         - Admin statistics")
    print()
    print("🔗 Nested Admin Users (/admin/users):")
    print("   GET  /admin/users/        - Admin list users")
    print("   DELETE /admin/users/{id}  - Admin delete user (auto-validation)")
    print()
    print("🎨 Features demonstrated:")
    print("   • Router group creation with prefixes")
    print("   • Nested router groups")
    print("   • API versioning with groups")
    print("   • Route organization patterns")
    print("   • Auto-validation with Path(), Query(), BaseModel")
    print()
    print("🔍 Auto-Validation:")
    print("   • Controlled globally by Catzilla app's auto_validation setting")
    print("   • Both main app and RouterGroup routes inherit this setting")
    print("   • Path parameters: user_id: int = Path(...)")
    print("   • Query parameters: page: int = Query(1, ge=1)")
    print("   • Request body: user_data: UserCreate")
    print()
    print("🧪 Try these examples:")
    print("   curl http://localhost:8000/groups")
    print("   curl http://localhost:8000/api/v1/users")
    print("   curl http://localhost:8000/api/v2/users?page=2&limit=5")
    print("   curl http://localhost:8000/admin/dashboard")
    print("   curl http://localhost:8000/admin/users/")
    print()
    print("🔄 Test auto-validation:")
    print("   # Main app auto-validation")
    print('   curl -X POST http://localhost:8000/users -H "Content-Type: application/json" -d \'{"name":"John","email":"john@example.com"}\'')
    print("   # RouterGroup auto-validation")
    print('   curl -X POST http://localhost:8000/api/v1/users -H "Content-Type: application/json" -d \'{"name":"Jane","email":"jane@example.com"}\'')
    print("   # Path parameter auto-validation")
    print('   curl http://localhost:8000/api/v1/users/123')
    print("   # Query parameter auto-validation")
    print('   curl "http://localhost:8000/api/v2/users?page=2&limit=5"')
    print()

    app.listen(host="0.0.0.0", port=8000)
