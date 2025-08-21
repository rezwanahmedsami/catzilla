"""
Query/Header/Form Validation Example

This example demonstrates Catzilla's FastAPI-style parameter validation
for query parameters, headers, and form data with automatic extraction.

Features demonstrated:
- Query parameter validation with Query()
- Header validation with Header()
- Form data validation with Form()
- Path parameter validation with Path()
- Automatic type conversion and validation
- Custom validation rules
"""

from catzilla import (
    Catzilla, Request, Response, JSONResponse,
    Query, Header, Path, Form, ValidationError
)
from typing import Optional, List

# Initialize Catzilla
app = Catzilla(
    production=False,
    show_banner=True,
    log_requests=True,
    auto_validation=True  # Enable automatic parameter validation
)

@app.get("/")
def home(request: Request) -> Response:
    """Home endpoint with parameter validation info"""
    return JSONResponse({
        "message": "Catzilla Parameter Validation Example",
        "features": [
            "Query parameter validation",
            "Header validation",
            "Form data validation",
            "Path parameter validation",
            "Automatic type conversion",
            "FastAPI-style decorators"
        ]
    })

@app.get("/search")
def search_with_query_validation(
    request: Request,
    q: str = Query(..., min_length=1, max_length=100, description="Search query"),
    page: int = Query(1, ge=1, le=1000, description="Page number"),
    limit: int = Query(10, ge=1, le=100, description="Items per page"),
    sort: str = Query("relevance", regex=r"^(relevance|date|title)$", description="Sort order"),
    filters: Optional[List[str]] = Query(None, description="Optional filters")
) -> Response:
    """Search endpoint with comprehensive query parameter validation"""

    return JSONResponse({
        "search_results": {
            "query": q,
            "page": page,
            "limit": limit,
            "sort": sort,
            "filters": filters or [],
            "total_results": 1000,
            "results": [
                {
                    "id": i,
                    "title": f"Result {i} for '{q}'",
                    "relevance": 0.95 - (i * 0.05)
                }
                for i in range(1, min(limit + 1, 11))
            ]
        },
        "validation": "passed"
    })

@app.get("/api/data")
def get_data_with_headers(
    request: Request,
    user_agent: str = Header(..., description="User agent header"),
    authorization: str = Header(..., regex=r"^Bearer [A-Za-z0-9\-_]+$", description="Authorization token"),
    x_api_version: str = Header("v1", alias="X-API-Version", description="API version"),
    x_request_id: Optional[str] = Header(None, alias="X-Request-ID", description="Request ID")
) -> Response:
    """API endpoint with header validation"""

    # Extract token from authorization header
    token = authorization.replace("Bearer ", "")

    return JSONResponse({
        "data": {
            "message": "Data retrieved successfully",
            "user_agent": user_agent,
            "token_length": len(token),
            "api_version": x_api_version,
            "request_id": x_request_id,
            "timestamp": "2024-01-15T10:30:00Z"
        },
        "validation": "headers_validated"
    })

@app.post("/users/{user_id}/profile")
def update_user_profile(
    request: Request,
    user_id: int = Path(..., ge=1, le=1000000, description="User ID"),
    name: str = Form(..., min_length=2, max_length=50, description="Full name"),
    email: str = Form(..., regex=r"^[^@]+@[^@]+\.[^@]+$", description="Email address"),
    age: int = Form(..., ge=13, le=120, description="User age"),
    bio: Optional[str] = Form(None, max_length=500, description="User biography"),
    newsletter: bool = Form(False, description="Subscribe to newsletter")
) -> Response:
    """Update user profile with form data validation"""

    return JSONResponse({
        "message": "Profile updated successfully",
        "user": {
            "id": user_id,
            "name": name,
            "email": email,
            "age": age,
            "bio": bio,
            "newsletter_subscription": newsletter
        },
        "validation": "form_data_validated"
    })

@app.get("/products/{category}")
def get_products(
    request: Request,
    category: str = Path(..., regex=r"^(electronics|books|clothing|sports)$", description="Product category"),
    min_price: Optional[float] = Query(None, ge=0.0, description="Minimum price"),
    max_price: Optional[float] = Query(None, ge=0.0, description="Maximum price"),
    brand: Optional[str] = Query(None, min_length=2, max_length=30, description="Brand filter"),
    in_stock: bool = Query(True, description="Only show in-stock items"),
    sort_by: str = Query("price", regex=r"^(price|rating|date|name)$", description="Sort field")
) -> Response:
    """Get products with path and query parameter validation"""

    # Validate price range
    if min_price is not None and max_price is not None and min_price > max_price:
        return JSONResponse({
            "error": "Validation error",
            "detail": "min_price cannot be greater than max_price"
        }, status_code=400)

    return JSONResponse({
        "products": [
            {
                "id": i,
                "name": f"{category.title()} Product {i}",
                "category": category,
                "price": 19.99 + (i * 10),
                "brand": brand or f"Brand{i}",
                "in_stock": in_stock and (i % 3 != 0),
                "rating": 4.0 + (i * 0.1)
            }
            for i in range(1, 11)
        ],
        "filters": {
            "category": category,
            "min_price": min_price,
            "max_price": max_price,
            "brand": brand,
            "in_stock": in_stock,
            "sort_by": sort_by
        },
        "validation": "path_and_query_validated"
    })

@app.post("/contact")
def contact_form(
    request: Request,
    name: str = Form(..., min_length=2, max_length=100, description="Contact name"),
    email: str = Form(..., regex=r"^[^@]+@[^@]+\.[^@]+$", description="Email address"),
    subject: str = Form(..., min_length=5, max_length=200, description="Message subject"),
    message: str = Form(..., min_length=10, max_length=2000, description="Message content"),
    phone: Optional[str] = Form(None, regex=r"^\+?[\d\s\-\(\)]{10,}$", description="Phone number"),
    newsletter: bool = Form(False, description="Subscribe to newsletter"),
    preferred_contact: str = Form("email", regex=r"^(email|phone|both)$", description="Preferred contact method")
) -> Response:
    """Contact form with comprehensive form validation"""

    return JSONResponse({
        "message": message,
        "contact": {
            "name": name,
            "email": email,
            "subject": subject,
            "message_length": len(message),
            "phone": phone,
            "newsletter": newsletter,
            "preferred_contact": preferred_contact,
            "submitted_at": "2024-01-15T10:30:00Z"
        },
        "validation": "form_validation_passed"
    }, status_code=201)

@app.get("/validation/examples")
def get_validation_examples(request: Request) -> Response:
    """Get example requests for testing parameter validation"""
    return JSONResponse({
        "examples": {
            "search_query": {
                "url": "/search?q=python&page=1&limit=20&sort=relevance&filters=tutorial,advanced",
                "description": "Search with query parameters"
            },
            "api_with_headers": {
                "url": "/api/data",
                "headers": {
                    "User-Agent": "CatzillaClient/1.0",
                    "Authorization": "Bearer abc123def456",
                    "X-API-Version": "v2",
                    "X-Request-ID": "req-12345"
                },
                "description": "API call with required headers"
            },
            "profile_form": {
                "url": "/users/123/profile",
                "method": "POST",
                "form_data": {
                    "name": "John Doe",
                    "email": "john@example.com",
                    "age": 25,
                    "bio": "Software developer",
                    "newsletter": True
                },
                "description": "Update profile with form data"
            },
            "products_path": {
                "url": "/products/electronics?min_price=100&max_price=500&brand=Apple&sort_by=price",
                "description": "Products with path and query validation"
            },
            "contact_form": {
                "url": "/contact",
                "method": "POST",
                "form_data": {
                    "name": "Jane Smith",
                    "email": "jane@example.com",
                    "subject": "Question about products",
                    "message": "I have a question about your electronics products...",
                    "phone": "+1-555-123-4567",
                    "newsletter": False,
                    "preferred_contact": "email"
                },
                "description": "Contact form with comprehensive validation"
            }
        },
        "validation_features": [
            "Automatic type conversion",
            "Min/max length validation",
            "Regex pattern matching",
            "Numeric range validation (ge, le)",
            "Optional parameters with defaults",
            "Custom error messages"
        ]
    })

@app.get("/health")
def health_check(request: Request) -> Response:
    """Health check endpoint"""
    return JSONResponse({
        "status": "healthy",
        "parameter_validation": "active",
        "framework": "Catzilla v0.2.0",
        "features": ["Query", "Header", "Form", "Path validation"]
    })

if __name__ == "__main__":
    print("🚨 Starting Catzilla Parameter Validation Example")
    print("📝 Available endpoints:")
    print("   GET  /                           - Home with validation info")
    print("   GET  /search                     - Search with query validation")
    print("   GET  /api/data                   - API with header validation")
    print("   POST /users/{id}/profile         - Profile update with form validation")
    print("   GET  /products/{category}        - Products with path/query validation")
    print("   POST /contact                    - Contact form with comprehensive validation")
    print("   GET  /validation/examples        - Get example requests")
    print("   GET  /health                     - Health check")
    print()
    print("🎨 Features demonstrated:")
    print("   • Query parameter validation with Query()")
    print("   • Header validation with Header()")
    print("   • Form data validation with Form()")
    print("   • Path parameter validation with Path()")
    print("   • Automatic type conversion")
    print("   • FastAPI-style parameter decorators")
    print()
    print("🧪 Try these examples:")
    print("   curl 'http://localhost:8000/search?q=python&page=1&limit=10&sort=relevance'")
    print("   curl http://localhost:8000/api/data \\")
    print("     -H 'User-Agent: CatzillaClient/1.0' \\")
    print("     -H 'Authorization: Bearer abc123def456'")
    print("   curl -X POST http://localhost:8000/contact \\")
    print("     -F 'name=John Doe' -F 'email=john@example.com' \\")
    print("     -F 'subject=Test Message' -F 'message=This is a test message.'")
    print()

    app.listen(host="0.0.0.0", port=8000)
