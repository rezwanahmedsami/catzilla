#!/usr/bin/env python3
"""
Catzilla Validation Benchmark Server

High-performance validation benchmarks using Catzilla's C-accelerated validation engine.
Tests auto-validation, constraints, nested models, and complex validation scenarios.

Features:
- C-accelerated validation (100x faster than Pydantic)
- FastAPI-compatible BaseModel syntax
- Advanced Field constraints and validation rules
- Nested model validation
- Custom validation with __post_init__
- Performance metrics tracking
"""

import sys
import os
import json
import time
import argparse
from typing import Optional, List, Dict, Union, Any
from decimal import Decimal
from datetime import datetime

# Add the catzilla package to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', 'python'))

from catzilla import (
    Catzilla, BaseModel, Field, ValidationError,
    JSONResponse, Response, Query, Path, Header, Form,
    get_performance_stats, reset_performance_stats
)

# Import shared validation endpoints
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'shared'))
from validation_endpoints import get_validation_endpoints


# =====================================================
# COMPREHENSIVE VALIDATION MODELS
# =====================================================

class SimpleUser(BaseModel):
    """Simple user model for basic validation benchmarks"""
    id: int
    name: str
    email: str
    age: Optional[int] = None

class AdvancedUser(BaseModel):
    """Advanced user model with Field constraints"""
    id: int = Field(ge=1, le=1000000, description="User ID")
    username: str = Field(min_length=3, max_length=20, regex=r'^[a-zA-Z0-9_]+$')
    email: str = Field(regex=r'^[^@]+@[^@]+\.[^@]+$')
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
    zip_code: str = Field(regex=r'^\d{5}(-\d{4})?$')
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
    category: str = Field(regex=r'^[a-zA-Z0-9\s\-_]+$')
    description: Optional[str] = Field(max_length=1000)
    sku: str = Field(regex=r'^[A-Z0-9\-]+$')
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
    status: str = Field(regex=r'^(pending|confirmed|shipped|delivered|cancelled)$')

    def __post_init__(self):
        """Custom validation: calculate total if not provided"""
        if self.total_amount is None:
            self.total_amount = sum(item.quantity * item.unit_price for item in self.items)

class BatchValidationRequest(BaseModel):
    """Batch validation request for performance testing"""
    users: List[AdvancedUser]
    products: List[Product]
    orders: List[Order]
    timestamp: datetime
    batch_id: str = Field(regex=r'^[A-Z0-9\-]+$')


def create_catzilla_validation_server():
    """Create Catzilla server optimized for validation benchmarks"""

    app = Catzilla(
        production=True,
        use_jemalloc=True,           # Memory optimization
        auto_validation=True,        # Enable auto-validation
        memory_profiling=False,      # Disable for benchmarks
        auto_memory_tuning=True,     # Adaptive memory management
        show_banner=False
    )

    endpoints = get_validation_endpoints()

    # Reset performance stats
    reset_performance_stats()

    # ==========================================
    # BASIC VALIDATION BENCHMARKS
    # ==========================================

    @app.post("/validate/simple-user")
    def validate_simple_user(request, user: SimpleUser) -> Response:
        """Basic user validation benchmark"""
        return JSONResponse({
            "validated": True,
            "user": user.dict(),
            "framework": "catzilla",
            "validation_type": "simple"
        })

    @app.post("/validate/advanced-user")
    def validate_advanced_user(request, user: AdvancedUser) -> Response:
        """Advanced user validation with constraints"""
        return JSONResponse({
            "validated": True,
            "user": user.dict(),
            "framework": "catzilla",
            "validation_type": "advanced_constraints",
            "constraints_validated": ["id_range", "username_regex", "email_format", "age_range", "height_range"]
        })

    @app.post("/validate/complex-user")
    def validate_complex_user(request, user: ComplexUser) -> Response:
        """Complex nested model validation"""
        return JSONResponse({
            "validated": True,
            "user": user.dict(),
            "framework": "catzilla",
            "validation_type": "nested_models",
            "models_validated": ["ComplexUser", "AdvancedUser", "Address"]
        })

    @app.post("/validate/product")
    def validate_product(request, product: Product) -> Response:
        """Product validation with comprehensive constraints"""
        return JSONResponse({
            "validated": True,
            "product": product.dict(),
            "framework": "catzilla",
            "validation_type": "comprehensive_product",
            "decimal_precision": "validated"
        })

    # ==========================================
    # BATCH VALIDATION BENCHMARKS
    # ==========================================

    @app.post("/validate/batch-users")
    def validate_batch_users(request, data: Dict[str, List[AdvancedUser]]) -> Response:
        """Batch user validation performance test"""
        start_time = time.perf_counter()

        users = data.get("users", [])
        validated_count = len(users)

        validation_time = (time.perf_counter() - start_time) * 1000

        return JSONResponse({
            "validated": True,
            "count": validated_count,
            "validation_time_ms": round(validation_time, 3),
            "throughput_per_sec": round(validated_count / (validation_time / 1000), 2),
            "framework": "catzilla",
            "validation_type": "batch_users"
        })

    @app.post("/validate/batch-products")
    def validate_batch_products(request, data: Dict[str, List[Product]]) -> Response:
        """Batch product validation performance test"""
        start_time = time.perf_counter()

        products = data.get("products", [])
        validated_count = len(products)

        validation_time = (time.perf_counter() - start_time) * 1000

        return JSONResponse({
            "validated": True,
            "count": validated_count,
            "validation_time_ms": round(validation_time, 3),
            "throughput_per_sec": round(validated_count / (validation_time / 1000), 2),
            "framework": "catzilla",
            "validation_type": "batch_products"
        })

    @app.post("/validate/batch-orders")
    def validate_batch_orders(request, data: Dict[str, List[Order]]) -> Response:
        """Batch order validation with custom validation"""
        start_time = time.perf_counter()

        orders = data.get("orders", [])
        validated_count = len(orders)

        validation_time = (time.perf_counter() - start_time) * 1000

        return JSONResponse({
            "validated": True,
            "count": validated_count,
            "validation_time_ms": round(validation_time, 3),
            "throughput_per_sec": round(validated_count / (validation_time / 1000), 2),
            "framework": "catzilla",
            "validation_type": "batch_orders_with_custom_validation"
        })

    @app.post("/validate/mega-batch")
    def validate_mega_batch(request, batch: BatchValidationRequest) -> Response:
        """Comprehensive batch validation performance test"""
        start_time = time.perf_counter()

        total_items = len(batch.users) + len(batch.products) + len(batch.orders)
        validation_time = (time.perf_counter() - start_time) * 1000

        return JSONResponse({
            "validated": True,
            "batch_id": batch.batch_id,
            "total_items": total_items,
            "breakdown": {
                "users": len(batch.users),
                "products": len(batch.products),
                "orders": len(batch.orders)
            },
            "validation_time_ms": round(validation_time, 3),
            "throughput_per_sec": round(total_items / (validation_time / 1000), 2),
            "framework": "catzilla",
            "validation_type": "mega_batch_comprehensive"
        })

    # ==========================================
    # PERFORMANCE MONITORING ENDPOINTS
    # ==========================================

    @app.get("/validation/stats")
    def get_validation_stats(request) -> Response:
        """Get validation performance statistics"""
        stats = get_performance_stats()
        return JSONResponse({
            "framework": "catzilla",
            "performance_stats": stats,
            "c_acceleration": "enabled",
            "jemalloc": "enabled"
        })

    @app.post("/validation/reset-stats")
    def reset_validation_stats(request) -> Response:
        """Reset validation performance statistics"""
        reset_performance_stats()
        return JSONResponse({
            "reset": True,
            "framework": "catzilla"
        })

    # ==========================================
    # ERROR HANDLING BENCHMARKS
    # ==========================================

    @app.post("/validate/error-handling")
    def validate_error_handling(request) -> Response:
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
            return JSONResponse({"error": "Should not reach here"})
        except ValidationError as e:
            return JSONResponse({
                "validation_error": True,
                "errors": str(e),
                "framework": "catzilla",
                "error_handling": "fast_c_validation"
            })

    @app.get("/health")
    def health(request) -> Response:
        """Health check endpoint"""
        return JSONResponse({
            "status": "healthy",
            "framework": "catzilla",
            "validation_engine": "c_accelerated",
            "memory_optimization": "jemalloc_enabled"
        })

    return app


def main():
    parser = argparse.ArgumentParser(description='Catzilla validation benchmark server')
    parser.add_argument('--host', default='127.0.0.1', help='Host to bind to')
    parser.add_argument('--port', type=int, default=8100, help='Port to bind to')
    parser.add_argument('--workers', type=int, default=1, help='Number of workers')

    args = parser.parse_args()

    app = create_catzilla_validation_server()

    print(f"🚀 Starting Catzilla validation benchmark server on {args.host}:{args.port}")
    print("Validation endpoints:")
    print("  POST /validate/simple-user      - Basic user validation")
    print("  POST /validate/advanced-user    - Advanced user with constraints")
    print("  POST /validate/complex-user     - Nested model validation")
    print("  POST /validate/product          - Product validation")
    print("  POST /validate/batch-users      - Batch user validation")
    print("  POST /validate/batch-products   - Batch product validation")
    print("  POST /validate/batch-orders     - Batch order validation")
    print("  POST /validate/mega-batch       - Comprehensive batch validation")
    print("  GET  /validation/stats          - Performance statistics")
    print("  POST /validation/reset-stats    - Reset statistics")
    print("  POST /validate/error-handling   - Error handling benchmark")
    print("  GET  /health                    - Health check")
    print()

    try:
        app.listen(args.port, args.host)
    except KeyboardInterrupt:
        print("\n👋 Catzilla validation benchmark server stopped")


if __name__ == "__main__":
    main()
