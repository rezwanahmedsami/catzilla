#!/usr/bin/env python3
"""
E2E Test Server for Validation Functionality

This server mirrors examples/validation/ for E2E testing.
It provides validation functionality to be tested via HTTP.
"""
import sys
import argparse
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from catzilla import (
    Catzilla, Request, Response, JSONResponse, BaseModel, Field,
    Query, Header, Path as PathParam, Form, ValidationError
)
from typing import Optional, List
import time

# Initialize Catzilla for E2E testing
app = Catzilla(
    production=False,
    show_banner=False,
    log_requests=False
)

# Validation models
class UserProfile(BaseModel):
    """User profile with comprehensive validation"""
    id: int = Field(ge=1, le=1000000, description="User ID")
    username: str = Field(min_length=3, max_length=20, regex=r'^[a-zA-Z0-9_]+$')
    email: str = Field(regex=r'^[^@]+@[^@]+\.[^@]+$')
    age: int = Field(ge=13, le=120, description="User age")
    is_active: bool = Field(default=True)
    bio: Optional[str] = Field(None, max_length=500)

class SimpleUser(BaseModel):
    """Simple user model for basic validation"""
    name: str = Field(min_length=2, max_length=50)
    email: str = Field(regex=r'^[^@]+@[^@]+\.[^@]+$')

class NestedAddress(BaseModel):
    """Address model for nested validation"""
    street: str = Field(min_length=5, max_length=100)
    city: str = Field(min_length=2, max_length=50)
    zipcode: str = Field(regex=r'^\d{5}(-\d{4})?$')

class UserWithAddress(BaseModel):
    """User with nested address validation"""
    name: str = Field(min_length=2, max_length=50)
    email: str = Field(regex=r'^[^@]+@[^@]+\.[^@]+$')
    address: NestedAddress

class ProductList(BaseModel):
    """Array validation model"""
    products: List[str] = Field(min_items=1, max_items=10)
    category: str = Field(min_length=2, max_length=30)

# Health check
@app.get("/health")
def health_check(request: Request) -> Response:
    """Health check endpoint"""
    return JSONResponse({
        "status": "healthy",
        "server": "validation_e2e_test",
        "timestamp": time.time()
    })

# Basic info
@app.get("/")
def home(request: Request) -> Response:
    """Validation test server info"""
    return JSONResponse({
        "message": "Catzilla E2E Validation Test Server",
        "features": [
            "Model validation",
            "Field constraints",
            "Nested models",
            "Array validation",
            "Custom validators"
        ],
        "endpoints": [
            "POST /validation/simple",
            "POST /validation/user",
            "POST /validation/nested",
            "POST /validation/array",
            "GET /validation/query"
        ]
    })

# Simple validation
@app.post("/validation/simple")
def simple_validation(request: Request, user: SimpleUser) -> Response:
    """Test simple model validation"""
    return JSONResponse({
        "message": "Simple validation passed",
        "validation": "success",
        "user": {
            "name": user.name,
            "email": user.email
        }
    }, status_code=201)

# Complex user validation
@app.post("/validation/user")
def user_validation(request: Request, user: UserProfile) -> Response:
    """Test comprehensive user validation"""
    return JSONResponse({
        "message": "User validation passed",
        "validation": "success",
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "age": user.age,
            "is_active": user.is_active,
            "bio": user.bio
        }
    }, status_code=201)

# Nested model validation
@app.post("/validation/nested")
def nested_validation(request: Request, user: UserWithAddress) -> Response:
    """Test nested model validation"""
    return JSONResponse({
        "message": "Nested validation passed",
        "validation": "success",
        "user": {
            "name": user.name,
            "email": user.email,
            "address": {
                "street": user.address.street,
                "city": user.address.city,
                "zipcode": user.address.zipcode
            }
        }
    }, status_code=201)

# Array validation
@app.post("/validation/array")
def array_validation(request: Request, data: ProductList) -> Response:
    """Test array validation"""
    return JSONResponse({
        "message": "Array validation passed",
        "validation": "success",
        "data": {
            "products": data.products,
            "category": data.category,
            "count": len(data.products)
        }
    }, status_code=201)

# Query parameter validation
@app.get("/validation/query")
def query_validation(
    request: Request,
    name: str = Query(..., min_length=2, max_length=20),
    age: int = Query(..., ge=0, le=150),
    active: bool = Query(True)
) -> Response:
    """Test query parameter validation"""
    return JSONResponse({
        "message": "Query validation passed",
        "validation": "success",
        "query_params": {
            "name": name,
            "age": age,
            "active": active
        }
    })

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Catzilla E2E Validation Test Server")
    parser.add_argument("--port", type=int, default=8101, help="Port to run server on")
    parser.add_argument("--host", type=str, default="127.0.0.1", help="Host to bind to")

    args = parser.parse_args()

    print(f"🚀 Starting Catzilla E2E Validation Test Server")
    print(f"📍 Server: http://{args.host}:{args.port}")
    print(f"🏥 Health: http://{args.host}:{args.port}/health")

    app.listen(port=args.port, host=args.host)
