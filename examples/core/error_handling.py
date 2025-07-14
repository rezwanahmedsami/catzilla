"""
Error Handling Example

This example demonstrates Catzilla's comprehensive error handling capabilities
including custom exception handlers, validation errors, and production-ready
error responses.

Features demonstrated:
- Custom exception handlers
- HTTP error responses (404, 500, etc.)
- Validation error handling
- Production vs development error modes
- Global error middleware
"""

from catzilla import Catzilla, Request, Response, JSONResponse, Path, BaseModel

# Data models for auto-validation
class UserCreate(BaseModel):
    """User creation model with automatic validation"""
    name: str
    email: str

    def validate_name(self, value):
        if not value or not value.strip():
            raise ValueError("Name is required")
        if len(value.strip()) < 2:
            raise ValueError("Name must be at least 2 characters")
        return value.strip()

    def validate_email(self, value):
        if not value or not value.strip():
            raise ValueError("Email is required")
        if "@" not in value:
            raise ValueError("Invalid email format")
        return value.strip()

# Custom exception classes
class ValidationError(Exception):
    """Custom validation error"""
    def __init__(self, message: str, field: str = None):
        self.message = message
        self.field = field
        super().__init__(message)

class NotFoundError(Exception):
    """Custom not found error"""
    def __init__(self, resource: str, resource_id: str):
        self.resource = resource
        self.resource_id = resource_id
        super().__init__(f"{resource} {resource_id} not found")

class AuthenticationError(Exception):
    """Custom authentication error"""
    pass

# Initialize Catzilla with error handling
app = Catzilla(
    production=False,  # Set to True for production error handling
    show_banner=True,
    log_requests=True
)

# Register custom exception handlers
def validation_error_handler(request: Request, exc: ValidationError) -> Response:
    """Handle validation errors"""
    return JSONResponse(
        {
            "error": "validation_error",
            "message": exc.message,
            "field": exc.field,
            "status_code": 422
        },
        status_code=422
    )

def not_found_error_handler(request: Request, exc: NotFoundError) -> Response:
    """Handle not found errors"""
    return JSONResponse(
        {
            "error": "not_found",
            "message": str(exc),
            "resource": exc.resource,
            "resource_id": exc.resource_id,
            "status_code": 404
        },
        status_code=404
    )

def auth_error_handler(request: Request, exc: AuthenticationError) -> Response:
    """Handle authentication errors"""
    return JSONResponse(
        {
            "error": "authentication_required",
            "message": "Valid authentication credentials required",
            "status_code": 401
        },
        status_code=401,
        headers={"WWW-Authenticate": "Bearer"}
    )

# Register the exception handlers
app.set_exception_handler(ValidationError, validation_error_handler)
app.set_exception_handler(NotFoundError, not_found_error_handler)
app.set_exception_handler(AuthenticationError, auth_error_handler)

# Custom 404 handler
@app.set_not_found_handler
def custom_404_handler(request: Request) -> Response:
    """Custom 404 handler"""
    return JSONResponse(
        {
            "error": "not_found",
            "message": f"Endpoint {request.path} not found",
            "method": request.method,
            "path": request.path,
            "available_endpoints": [
                "/api/users/{user_id}",
                "/api/validation-error",
                "/api/server-error",
                "/api/protected",
                "/api/divide/{a}/{b}"
            ]
        },
        status_code=404
    )

# Custom 500 handler
@app.set_internal_error_handler
def custom_500_handler(request: Request, exc: Exception) -> Response:
    """Custom internal server error handler"""
    # In production, don't expose internal error details
    if app.production:
        return JSONResponse(
            {
                "error": "internal_server_error",
                "message": "An internal error occurred",
                "status_code": 500,
                "request_id": "req_12345"
            },
            status_code=500
        )
    else:
        # In development, show detailed error information
        return JSONResponse(
            {
                "error": "internal_server_error",
                "message": str(exc),
                "type": type(exc).__name__,
                "status_code": 500,
                "path": request.path,
                "method": request.method
            },
            status_code=500
        )

# Routes that demonstrate error handling

@app.get("/api/users/{user_id}")
def get_user(request: Request, user_id: str = Path(...)) -> Response:
    """Get user - demonstrates NotFoundError"""
    # Simulate user lookup
    if user_id == "999":
        raise NotFoundError("User", user_id)

    return JSONResponse({
        "id": user_id,
        "name": f"User {user_id}",
        "email": f"user{user_id}@example.com"
    })

@app.post("/api/users")
def create_user(request: Request, user_data: UserCreate) -> Response:
    """Create user - demonstrates auto-validation with BaseModel"""
    # Auto-validation handles all the validation logic
    # If we reach here, the data is already validated
    return JSONResponse({
        "message": "User created successfully",
        "user": {
            "id": 123,
            "name": user_data.name,
            "email": user_data.email
        }
    }, status_code=201)

@app.get("/api/validation-error")
def trigger_validation_error(request: Request) -> Response:
    """Endpoint to test validation error handling"""
    raise ValidationError("This is a test validation error", "test_field")

@app.get("/api/server-error")
def trigger_server_error(request: Request) -> Response:
    """Endpoint to test server error handling"""
    # This will trigger a ZeroDivisionError
    result = 1 / 0
    return JSONResponse({"result": result})

@app.get("/api/protected")
def protected_endpoint(request: Request) -> Response:
    """Protected endpoint - demonstrates authentication error"""
    # Check for authorization header
    auth_header = request.headers.get("Authorization", "")

    if not auth_header.startswith("Bearer "):
        raise AuthenticationError()

    token = auth_header[7:]  # Remove "Bearer " prefix

    if token != "valid-token":
        raise AuthenticationError()

    return JSONResponse({
        "message": "Access granted to protected resource",
        "user": "authenticated_user"
    })

@app.get("/api/divide/{a}/{b}")
def divide_numbers(request: Request, a: float = Path(...), b: float = Path(...)) -> Response:
    """Division endpoint - demonstrates automatic error handling"""
    try:
        if b == 0:
            return JSONResponse(
                {
                    "error": "division_by_zero",
                    "message": "Cannot divide by zero",
                    "a": a,
                    "b": b
                },
                status_code=400
            )

        result = a / b
        return JSONResponse({
            "a": a,
            "b": b,
            "result": result,
            "operation": "division"
        })

    except (ValueError, TypeError):
        return JSONResponse(
            {
                "error": "invalid_numbers",
                "message": "Both parameters must be valid numbers",
                "a": a,
                "b": b
            },
            status_code=400
        )

@app.get("/api/error-test")
def error_test_menu(request: Request) -> Response:
    """Error test menu"""
    return JSONResponse({
        "message": "Error handling test endpoints",
        "endpoints": {
            "validation_error": "/api/validation-error",
            "server_error": "/api/server-error",
            "not_found": "/api/users/999",
            "auth_error": "/api/protected",
            "division_by_zero": "/api/divide/10/0",
            "invalid_numbers": "/api/divide/abc/def"
        },
        "instructions": {
            "auth_test": "Send request to /api/protected with header: Authorization: Bearer valid-token",
            "validation_test": "POST to /api/users with invalid data"
        }
    })

# Health check that shows error handling status
@app.get("/health")
def health_check(request: Request) -> Response:
    """Health check with error handling info"""
    return JSONResponse({
        "status": "healthy",
        "error_handling": {
            "production_mode": app.production,
            "custom_handlers": ["ValidationError", "NotFoundError", "AuthenticationError"],
            "custom_404": True,
            "custom_500": True
        }
    })

if __name__ == "__main__":
    print("🚨 Starting Catzilla Error Handling Example")
    print("📝 Available endpoints:")
    print("   GET  /api/users/{user_id}      - User lookup (try user_id=999 for error)")
    print("   POST /api/users               - Create user (validation errors)")
    print("   GET  /api/validation-error    - Test validation error")
    print("   GET  /api/server-error        - Test server error")
    print("   GET  /api/protected           - Test auth error")
    print("   GET  /api/divide/{a}/{b}      - Test division errors")
    print("   GET  /api/error-test          - Error test menu")
    print("   GET  /health                  - Health check")
    print("\n🛡️  Error handling features:")
    print("   ✅ Custom exception handlers")
    print("   ✅ Custom 404/500 handlers")
    print("   ✅ Validation error handling")
    print("   ✅ Production error sanitization")
    print("🌐 Server will start on http://localhost:8000")

    app.listen(port=8000, host="0.0.0.0")
