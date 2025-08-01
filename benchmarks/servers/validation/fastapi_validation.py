#!/usr/bin/env python3
"""
FastAPI Validation Benchmark Server

FastAPI validation benchmarks using Pydantic models for comparison
with Catzilla's C-accelerated validation engine.

Features:
- Standard Pydantic validation
- FastAPI dependency injection
- Type validation and constraints
- Nested model validation
- Batch validation testing
"""

import sys
import os
import json
import time
import argparse
from typing import Optional, List, Dict, Union, Any
from decimal import Decimal
from datetime import datetime

# Import shared validation endpoints
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'shared'))
from validation_endpoints import get_validation_endpoints

try:
    from fastapi import FastAPI, HTTPException
    from fastapi.responses import JSONResponse
    from pydantic import BaseModel, Field, validator
    import uvicorn
except ImportError:
    print("❌ FastAPI not installed. Install with: pip install fastapi uvicorn pydantic")
    sys.exit(1)


# =====================================================
# PYDANTIC VALIDATION MODELS
# =====================================================

class SimpleUser(BaseModel):
    """Simple user model for basic validation benchmarks"""
    id: int
    name: str
    email: str
    age: Optional[int] = None

class AdvancedUser(BaseModel):
    """Advanced user model with Pydantic Field constraints"""
    id: int = Field(ge=1, le=1000000, description="User ID")
    username: str = Field(min_length=3, max_length=20, pattern=r'^[a-zA-Z0-9_]+$')
    email: str = Field(pattern=r'^[^@]+@[^@]+\.[^@]+$')
    age: int = Field(ge=13, le=120)
    height: float = Field(gt=0.5, lt=3.0)
    is_active: bool = True
    tags: Optional[List[str]] = Field(default=None)
    metadata: Optional[Dict[str, str]] = None

class Address(BaseModel):
    """Address model for nested validation"""
    street: str = Field(min_length=5, max_length=100)
    city: str = Field(min_length=2, max_length=50)
    state: str = Field(min_length=2, max_length=2)
    zip_code: str = Field(pattern=r'^\d{5}(-\d{4})?$')
    country: str = "USA"

class ComplexUser(BaseModel):
    """Complex user model with nested validation"""
    id: int = Field(ge=1)
    personal_info: AdvancedUser
    billing_address: Address
    shipping_address: Optional[Address] = None
    preferences: Dict[str, Union[str, int, bool]] = {}
    created_at: datetime
    updated_at: Optional[datetime] = None

class Product(BaseModel):
    """Product model with comprehensive validation"""
    name: str = Field(min_length=1, max_length=200)
    price: Decimal = Field(ge=0.01, le=999999.99)
    category: str = Field(pattern=r'^[a-zA-Z0-9\s\-_]+$')
    description: Optional[str] = Field(max_length=1000)
    sku: str = Field(pattern=r'^[A-Z0-9\-]+$')
    in_stock: bool = True
    stock_quantity: int = Field(ge=0, le=100000)
    dimensions: Optional[Dict[str, float]] = None
    tags: List[str] = []
    variants: Optional[List[Dict[str, Any]]] = None

class OrderItem(BaseModel):
    """Order item for batch validation"""
    product_id: int = Field(ge=1)
    quantity: int = Field(ge=1, le=1000)
    unit_price: Decimal = Field(ge=0.01)

class Order(BaseModel):
    """Order model for complex batch validation"""
    id: int = Field(ge=1)
    customer_id: int = Field(ge=1)
    items: List[OrderItem]
    shipping_address: Address
    billing_address: Optional[Address] = None
    total_amount: Optional[Decimal] = None
    order_date: datetime
    status: str = Field(pattern=r'^(pending|confirmed|shipped|delivered|cancelled)$')

    @validator('total_amount', always=True)
    def calculate_total(cls, v, values):
        """Custom validation: calculate total if not provided"""
        if v is None and 'items' in values:
            return sum(item.quantity * item.unit_price for item in values['items'])
        return v

class BatchValidationRequest(BaseModel):
    """Batch validation request for performance testing"""
    users: List[AdvancedUser]
    products: List[Product]
    orders: List[Order]
    timestamp: datetime
    batch_id: str = Field(pattern=r'^[A-Z0-9\-]+$')

class BatchUsers(BaseModel):
    """Batch users for validation testing"""
    users: List[AdvancedUser]

class BatchProducts(BaseModel):
    """Batch products for validation testing"""
    products: List[Product]

class BatchOrders(BaseModel):
    """Batch orders for validation testing"""
    orders: List[Order]


def create_fastapi_validation_server():
    """Create FastAPI server for validation benchmarks"""

    app = FastAPI(
        title="FastAPI Validation Benchmarks",
        description="Pydantic validation performance testing",
        version="1.0.0"
    )

    endpoints = get_validation_endpoints()

    # ==========================================
    # BASIC VALIDATION BENCHMARKS
    # ==========================================

    @app.post("/validate/simple-user")
    async def validate_simple_user(user: SimpleUser):
        """Basic user validation benchmark"""
        return {
            "validated": True,
            "user": user.dict(),
            "framework": "fastapi",
            "validation_type": "simple"
        }

    @app.post("/validate/advanced-user")
    async def validate_advanced_user(user: AdvancedUser):
        """Advanced user validation with constraints"""
        return {
            "validated": True,
            "user": user.dict(),
            "framework": "fastapi",
            "validation_type": "advanced_constraints",
            "constraints_validated": ["id_range", "username_regex", "email_format", "age_range", "height_range"]
        }

    @app.post("/validate/complex-user")
    async def validate_complex_user(user: ComplexUser):
        """Complex nested model validation"""
        return {
            "validated": True,
            "user": user.dict(),
            "framework": "fastapi",
            "validation_type": "nested_models",
            "models_validated": ["ComplexUser", "AdvancedUser", "Address"]
        }

    @app.post("/validate/product")
    async def validate_product(product: Product):
        """Product validation with comprehensive constraints"""
        return {
            "validated": True,
            "product": product.dict(),
            "framework": "fastapi",
            "validation_type": "comprehensive_product",
            "decimal_precision": "validated"
        }

    # ==========================================
    # BATCH VALIDATION BENCHMARKS
    # ==========================================

    @app.post("/validate/batch-users")
    async def validate_batch_users(data: BatchUsers):
        """Batch user validation performance test"""
        start_time = time.perf_counter()

        validated_count = len(data.users)

        validation_time = (time.perf_counter() - start_time) * 1000

        return {
            "validated": True,
            "count": validated_count,
            "validation_time_ms": round(validation_time, 3),
            "throughput_per_sec": round(validated_count / (validation_time / 1000), 2) if validation_time > 0 else 0,
            "framework": "fastapi",
            "validation_type": "batch_users"
        }

    @app.post("/validate/batch-products")
    async def validate_batch_products(data: BatchProducts):
        """Batch product validation performance test"""
        start_time = time.perf_counter()

        validated_count = len(data.products)

        validation_time = (time.perf_counter() - start_time) * 1000

        return {
            "validated": True,
            "count": validated_count,
            "validation_time_ms": round(validation_time, 3),
            "throughput_per_sec": round(validated_count / (validation_time / 1000), 2) if validation_time > 0 else 0,
            "framework": "fastapi",
            "validation_type": "batch_products"
        }

    @app.post("/validate/batch-orders")
    async def validate_batch_orders(data: BatchOrders):
        """Batch order validation with custom validation"""
        start_time = time.perf_counter()

        validated_count = len(data.orders)

        validation_time = (time.perf_counter() - start_time) * 1000

        return {
            "validated": True,
            "count": validated_count,
            "validation_time_ms": round(validation_time, 3),
            "throughput_per_sec": round(validated_count / (validation_time / 1000), 2) if validation_time > 0 else 0,
            "framework": "fastapi",
            "validation_type": "batch_orders_with_custom_validation"
        }

    @app.post("/validate/mega-batch")
    async def validate_mega_batch(batch: BatchValidationRequest):
        """Comprehensive batch validation performance test"""
        start_time = time.perf_counter()

        total_items = len(batch.users) + len(batch.products) + len(batch.orders)
        validation_time = (time.perf_counter() - start_time) * 1000

        return {
            "validated": True,
            "batch_id": batch.batch_id,
            "total_items": total_items,
            "breakdown": {
                "users": len(batch.users),
                "products": len(batch.products),
                "orders": len(batch.orders)
            },
            "validation_time_ms": round(validation_time, 3),
            "throughput_per_sec": round(total_items / (validation_time / 1000), 2) if validation_time > 0 else 0,
            "framework": "fastapi",
            "validation_type": "mega_batch_comprehensive"
        }

    # ==========================================
    # ERROR HANDLING BENCHMARKS
    # ==========================================

    @app.post("/validate/error-handling")
    async def validate_error_handling():
        """Test validation error handling performance"""
        try:
            # This should trigger validation errors
            invalid_user = AdvancedUser(
                id=-1,  # Invalid: should be >= 1
                username="a",  # Invalid: too short
                email="invalid",  # Invalid: wrong format
                age=200,  # Invalid: too old
                height=-1.0  # Invalid: negative
            )
            return {"error": "Should not reach here"}
        except Exception as e:
            return {
                "validation_error": True,
                "errors": str(e),
                "framework": "fastapi",
                "error_handling": "pydantic_validation"
            }

    @app.get("/health")
    async def health():
        """Health check endpoint"""
        return {
            "status": "healthy",
            "framework": "fastapi",
            "validation_engine": "pydantic",
            "memory_optimization": "standard"
        }

    return app


def main():
    parser = argparse.ArgumentParser(description='FastAPI validation benchmark server')
    parser.add_argument('--host', default='127.0.0.1', help='Host to bind to')
    parser.add_argument('--port', type=int, default=8101, help='Port to bind to')
    parser.add_argument('--workers', type=int, default=1, help='Number of workers')

    args = parser.parse_args()

    app = create_fastapi_validation_server()

    print(f"🚀 Starting FastAPI validation benchmark server on {args.host}:{args.port}")
    print("Validation endpoints:")
    print("  POST /validate/simple-user      - Basic user validation")
    print("  POST /validate/advanced-user    - Advanced user with constraints")
    print("  POST /validate/complex-user     - Nested model validation")
    print("  POST /validate/product          - Product validation")
    print("  POST /validate/batch-users      - Batch user validation")
    print("  POST /validate/batch-products   - Batch product validation")
    print("  POST /validate/batch-orders     - Batch order validation")
    print("  POST /validate/mega-batch       - Comprehensive batch validation")
    print("  POST /validate/error-handling   - Error handling benchmark")
    print("  GET  /health                    - Health check")
    print()

    uvicorn.run(
        app,
        host=args.host,
        port=args.port,
        workers=args.workers,
        access_log=False,
        log_level="error"
    )


if __name__ == "__main__":
    main()
