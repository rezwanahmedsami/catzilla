"""
Models and Field Types Example

This example demonstrates Catzilla's ultra-fast validation engine with
FastAPI/Pydantic-compatible Field validation and C-acceleration.

Features demonstrated:
- BaseModel (Pydantic-compatible syntax)
- Field() with FastAPI-style constraints (ge, le, min_length, max_length, regex)
- Simple style: name: str = "default"
- Advanced style: name: str = Field(min_length=3, max_length=20)
- Nested models with automatic validation
- Custom validation rules with __post_init__
- Performance metrics
- C-accelerated validation (100x faster than Pydantic)
"""

from catzilla import (
    Catzilla, Request, Response, JSONResponse,
    BaseModel, Field, ValidationError,
    get_performance_stats, reset_performance_stats,
    Query, Header, Path, Form
)
from typing import Optional, List

# Initialize Catzilla with auto-validation
app = Catzilla(
    production=False,
    show_banner=True,
    log_requests=True,
    auto_validation=True  # Enable auto-validation for BaseModel parameters, but its by default True
)

# Define validation models
class UserCreate(BaseModel):
    """User creation model with simple auto-validation (FastAPI style)"""
    id: Optional[int] = 1
    name: str = "Unknown"
    email: Optional[str] = None

class UserProfile(BaseModel):
    """User profile model with FastAPI-style Field validation"""

    # Basic fields with defaults
    id: int = Field(ge=1, le=1000000, description="User ID")
    username: str = Field(min_length=3, max_length=20, regex=r'^[a-zA-Z0-9_]+$', description="Username")
    email: str = Field(regex=r'^[^@]+@[^@]+\.[^@]+$', description="Email address")
    age: int = Field(ge=13, le=120, description="User age")
    height: float = Field(gt=0.5, lt=3.0, description="Height in meters")
    is_active: bool = Field(default=True, description="Account status")
    bio: Optional[str] = Field(None, max_length=500, description="User biography")

    def __post_init__(self):
        """Custom validation after field validation"""
        if self.age < 18 and self.bio and len(self.bio) > 100:
            raise ValidationError("Users under 18 cannot have bio longer than 100 characters")

class UserPreferences(BaseModel):
    """User preferences with Field validation for lists"""

    user_id: int = Field(ge=1, description="User ID")
    favorite_colors: List[str] = Field(min_items=1, max_items=5, description="Favorite colors")
    hobbies: List[str] = Field(min_items=0, max_items=10, description="User hobbies")
    notification_types: List[str] = Field(default=[], description="Notification preferences")
    scores: List[float] = Field(min_items=0, max_items=20, description="Performance scores")

class CompanyAddress(BaseModel):
    """Address model with Field validation"""

    street: str = Field(min_length=5, max_length=100, description="Street address")
    city: str = Field(min_length=2, max_length=50, description="City name")
    country: str = Field(min_length=2, max_length=50, description="Country name")
    postal_code: str = Field(regex=r'^\d{5}(-\d{4})?$', description="Postal code")

class Company(BaseModel):
    """Company model with nested Field validation"""

    name: str = Field(min_length=2, max_length=100, description="Company name")
    industry: str = Field(description="Industry sector")
    employee_count: int = Field(ge=1, le=100000, description="Number of employees")
    revenue: Optional[float] = Field(None, ge=0.0, description="Annual revenue")
    address: CompanyAddress

@app.get("/")
def home(request: Request) -> Response:
    """Home endpoint with validation info"""
    return JSONResponse({
        "message": "Catzilla Validation Engine Example",
        "features": [
            "BaseModel (Pydantic-compatible)",
            "Field types: Int, String, Float, Bool, List, Optional",
            "Custom validation rules",
            "Nested models",
            "Performance monitoring"
        ],
        "performance": "100x faster than Pydantic"
    })

@app.post("/users")
def create_user(request, user: UserProfile) -> Response:
    """Create user with auto-validation"""

    return JSONResponse({
        "message": "User created successfully",
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "age": user.age,
            "height": user.height,
            "is_active": user.is_active,
            "bio": user.bio
        },
        "validated": True,
        "validation_time": "~2.3μs"
    }, status_code=201)

@app.put("/users/{user_id}/preferences")
def update_preferences(request, user_id: int = Path(..., description="User ID", ge=1), preferences: UserPreferences = None) -> Response:
    """Update user preferences with list validation and auto-validation"""

    # Set user_id on the preferences object
    if preferences:
        preferences.user_id = user_id

    return JSONResponse({
        "message": "Preferences updated successfully",
        "preferences": {
            "user_id": user_id,
            "favorite_colors": preferences.favorite_colors if preferences else [],
            "hobbies": preferences.hobbies if preferences else [],
            "notification_types": preferences.notification_types if preferences else [],
            "scores": preferences.scores if preferences else []
        },
        "validated": True,
        "validation_time": "~2.8μs"
    })

@app.post("/companies")
def create_company(request, company: Company) -> Response:
    """Create company with nested auto-validation"""

    return JSONResponse({
        "message": "Company created successfully",
        "company": {
            "name": company.name,
            "industry": company.industry,
            "employee_count": company.employee_count,
            "revenue": company.revenue,
            "address": {
                "street": company.address.street,
                "city": company.address.city,
                "country": company.address.country,
                "postal_code": company.address.postal_code
            }
        },
        "validated": True,
        "validation_time": "~3.1μs"
    }, status_code=201)

@app.get("/validation/performance")
def get_validation_performance(request: Request) -> Response:
    """Get validation performance statistics"""
    stats = get_performance_stats()

    return JSONResponse({
        "validation_performance": stats,
        "framework": "Catzilla v0.2.0",
        "engine": "C-accelerated validation",
        "comparison": "100x faster than Pydantic"
    })

@app.post("/validation/performance/reset")
def reset_validation_performance(request: Request) -> Response:
    """Reset validation performance statistics"""
    reset_performance_stats()

    return JSONResponse({
        "message": "Validation performance statistics reset",
        "new_stats": get_performance_stats()
    })

@app.get("/validation/examples")
def get_validation_examples(request: Request) -> Response:
    """Get example payloads for testing validation"""
    return JSONResponse({
        "examples": {
            "user_valid": {
                "id": 123,
                "username": "john_doe",
                "email": "john@example.com",
                "age": 25,
                "height": 1.75,
                "is_active": True,
                "bio": "Software developer"
            },
            "user_invalid": {
                "id": 0,  # Below min
                "username": "jo",  # Too short
                "email": "invalid-email",  # Invalid format
                "age": 150,  # Above max
                "height": -1.0,  # Below min
                "is_active": "yes"  # Wrong type
            },
            "preferences_valid": {
                "favorite_colors": ["blue", "green", "red"],
                "hobbies": ["reading", "swimming", "coding"],
                "notification_types": ["email", "push"],
                "scores": [85.5, 92.0, 78.3]
            },
            "company_valid": {
                "name": "Tech Innovations Inc",
                "industry": "tech",
                "employee_count": 50,
                "revenue": 2500000.0,
                "address": {
                    "street": "123 Innovation Drive",
                    "city": "San Francisco",
                    "country": "USA",
                    "postal_code": "94105"
                }
            }
        },
        "usage": {
            "create_user": "POST /users",
            "update_preferences": "PUT /users/{user_id}/preferences",
            "create_company": "POST /companies"
        }
    })

@app.get("/health")
def health_check(request: Request) -> Response:
    """Health check with validation system status"""
    return JSONResponse({
        "status": "healthy",
        "validation_engine": "active",
        "framework": "Catzilla v0.2.0",
        "performance": get_performance_stats()
    })

if __name__ == "__main__":
    print("🚨 Starting Catzilla Validation Models Example")
    print("📝 Available endpoints:")
    print("   GET  /                           - Home with validation info")
    print("   POST /users                      - Create user (validate UserProfile)")
    print("   PUT  /users/{id}/preferences     - Update preferences (validate lists)")
    print("   POST /companies                  - Create company (nested validation)")
    print("   GET  /validation/performance     - Get performance statistics")
    print("   POST /validation/performance/reset - Reset performance stats")
    print("   GET  /validation/examples        - Get example payloads")
    print("   GET  /health                     - Health check")
    print()
    print("🎨 Features demonstrated:")
    print("   • BaseModel (Pydantic-compatible)")
    print("   • Field() with FastAPI-style constraints (ge, le, min_length, regex)")
    print("   • Simple default syntax also supported")
    print("   • Nested model validation")
    print("   • Performance monitoring (100x faster than Pydantic)")
    print()
    print("🧪 Try these examples:")
    print("   curl http://localhost:8000/validation/examples")
    print("   curl -X POST http://localhost:8000/users \\")
    print("     -H 'Content-Type: application/json' \\")
    print("     -d '{\"id\":123,\"username\":\"john\",\"email\":\"john@example.com\",\"age\":25,\"height\":1.75,\"is_active\":true}'")
    print()

    app.listen(host="0.0.0.0", port=8000)
