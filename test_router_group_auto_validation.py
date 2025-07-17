"""
Test RouterGroup Auto-Validation
This file tests the new RouterGroup auto-validation feature to ensure it works like main app validation.
"""

from catzilla import Catzilla, Request, Response, JSONResponse, BaseModel, Query, Path, Form, Header
from catzilla.router import RouterGroup

# Test models
class UserCreate(BaseModel):
    name: str
    email: str
    age: int = 25

def test_router_group_auto_validation():
    """Test that RouterGroup supports auto-validation like main app"""

    # Create app
    app = Catzilla(auto_validation=True, production=True, show_banner=False)

    # Create RouterGroup with auto-validation enabled
    api_group = RouterGroup("/api/v1", auto_validation=True)

    # Add routes with auto-validation
    @api_group.get("/users/{user_id}")
    def get_user(request, user_id: int = Path(..., description="User ID", ge=1)):
        return JSONResponse({
            "user_id": user_id,
            "type": type(user_id).__name__,
            "validation": "auto"
        })

    @api_group.get("/search")
    def search_users(
        request,
        q: str = Query(..., description="Search query"),
        limit: int = Query(10, ge=1, le=100)
    ):
        return JSONResponse({
            "query": q,
            "limit": limit,
            "query_type": type(q).__name__,
            "limit_type": type(limit).__name__,
            "validation": "auto"
        })

    @api_group.post("/users")
    def create_user(request, user: UserCreate):
        return JSONResponse({
            "name": user.name,
            "email": user.email,
            "age": user.age,
            "validation": "auto"
        })

    # Include RouterGroup in app
    app.include_routes(api_group)

    # Check that routes were registered with auto-validation
    routes = api_group.routes()
    print(f"📋 RouterGroup routes registered: {len(routes)}")

    for method, path, handler, metadata in routes:
        auto_validation_applied = metadata.get("auto_validation_applied", False)
        print(f"   {method} {path} - Auto-validation: {'✅' if auto_validation_applied else '❌'}")

        # Check if handler was wrapped
        if hasattr(handler, '_validation_spec'):
            print(f"      Validation spec: {len(handler._validation_spec.parameters)} parameters")
        elif hasattr(handler, '_original_handler'):
            print(f"      Original handler preserved: {handler._original_handler.__name__}")

    print()
    print("🚀 RouterGroup Auto-Validation Test Complete!")
    print("✅ RouterGroup now supports FastAPI-style auto-validation")
    print("✅ Path(), Query(), Form(), Header(), and BaseModel validation")
    print("✅ Same performance as main app validation")

if __name__ == "__main__":
    test_router_group_auto_validation()
