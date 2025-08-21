#!/usr/bin/env python3
"""
Shared validation endpoint definitions for consistent benchmarking across frameworks.

This module defines validation test scenarios that each framework will implement
to ensure fair performance comparisons for validation engines.
"""

import json
import time
from typing import Dict, Any, List
from datetime import datetime
from decimal import Decimal

def get_validation_endpoints():
    """
    Returns validation endpoint definitions for benchmarking.
    Each endpoint tests different aspects of validation performance.
    """
    return {
        # Simple validation test
        "simple_user": {
            "method": "POST",
            "path": "/validate/simple-user",
            "description": "Basic user model validation",
            "sample_data": {
                "id": 123,
                "name": "John Doe",
                "email": "john@example.com",
                "age": 30
            }
        },

        # Advanced validation with constraints
        "advanced_user": {
            "method": "POST",
            "path": "/validate/advanced-user",
            "description": "Advanced user validation with Field constraints",
            "sample_data": {
                "id": 123,
                "username": "johndoe123",
                "email": "john@example.com",
                "age": 30,
                "height": 1.75,
                "is_active": True,
                "tags": ["developer", "python", "web"],
                "metadata": {"department": "engineering", "role": "senior"}
            }
        },

        # Complex nested validation
        "complex_user": {
            "method": "POST",
            "path": "/validate/complex-user",
            "description": "Complex nested model validation",
            "sample_data": {
                "id": 123,
                "personal_info": {
                    "id": 123,
                    "username": "johndoe123",
                    "email": "john@example.com",
                    "age": 30,
                    "height": 1.75,
                    "is_active": True,
                    "tags": ["developer"],
                    "metadata": {"role": "senior"}
                },
                "billing_address": {
                    "street": "123 Main Street",
                    "city": "San Francisco",
                    "state": "CA",
                    "zip_code": "94102",
                    "country": "USA"
                },
                "preferences": {"theme": "dark", "notifications": True},
                "created_at": "2024-01-01T00:00:00Z"
            }
        },

        # Product validation with comprehensive constraints
        "product": {
            "method": "POST",
            "path": "/validate/product",
            "description": "Product validation with comprehensive constraints",
            "sample_data": {
                "name": "Premium Widget",
                "price": "29.99",
                "category": "Electronics",
                "description": "A high-quality widget for all your needs",
                "sku": "WIDGET-001",
                "in_stock": True,
                "stock_quantity": 100,
                "dimensions": {"length": 10.0, "width": 5.0, "height": 2.0},
                "tags": ["premium", "electronics", "widget"],
                "variants": [
                    {"color": "red", "size": "small"},
                    {"color": "blue", "size": "large"}
                ]
            }
        },

        # Batch validation tests
        "batch_users": {
            "method": "POST",
            "path": "/validate/batch-users",
            "description": "Batch user validation performance test",
            "sample_data": {
                "users": [
                    {
                        "id": i,
                        "username": f"user{i}",
                        "email": f"user{i}@example.com",
                        "age": 25 + (i % 50),
                        "height": 1.5 + (i % 5) * 0.1,
                        "is_active": True,
                        "tags": ["user", f"group{i % 10}"]
                    }
                    for i in range(1, 101)  # 100 users
                ]
            }
        },

        "batch_products": {
            "method": "POST",
            "path": "/validate/batch-products",
            "description": "Batch product validation performance test",
            "sample_data": {
                "products": [
                    {
                        "name": f"Product {i}",
                        "price": f"{(i * 10 + 99) / 100:.2f}",
                        "category": f"Category{i % 5}",
                        "description": f"Description for product {i}",
                        "sku": f"PROD-{i:03d}",
                        "in_stock": True,
                        "stock_quantity": i * 10,
                        "tags": [f"tag{i % 3}", f"category{i % 5}"]
                    }
                    for i in range(1, 101)  # 100 products
                ]
            }
        },

        "batch_orders": {
            "method": "POST",
            "path": "/validate/batch-orders",
            "description": "Batch order validation with custom validation",
            "sample_data": {
                "orders": [
                    {
                        "id": i,
                        "customer_id": (i % 50) + 1,
                        "items": [
                            {
                                "product_id": (i % 20) + 1,
                                "quantity": (i % 5) + 1,
                                "unit_price": f"{(i * 5 + 10):.2f}"
                            }
                        ],
                        "shipping_address": {
                            "street": f"{i} Test Street",
                            "city": "Test City",
                            "state": "CA",
                            "zip_code": "94102",
                            "country": "USA"
                        },
                        "order_date": "2024-01-01T00:00:00Z",
                        "status": "pending"
                    }
                    for i in range(1, 51)  # 50 orders
                ]
            }
        },

        # Mega batch validation
        "mega_batch": {
            "method": "POST",
            "path": "/validate/mega-batch",
            "description": "Comprehensive batch validation performance test",
            "sample_data": {
                "users": [
                    {
                        "id": i,
                        "username": f"user{i}",
                        "email": f"user{i}@example.com",
                        "age": 25 + (i % 50),
                        "height": 1.5 + (i % 5) * 0.1,
                        "is_active": True,
                        "tags": ["user"]
                    }
                    for i in range(1, 51)  # 50 users
                ],
                "products": [
                    {
                        "name": f"Product {i}",
                        "price": f"{(i * 10 + 99) / 100:.2f}",
                        "category": f"Category{i % 5}",
                        "sku": f"PROD-{i:03d}",
                        "in_stock": True,
                        "stock_quantity": i * 10,
                        "tags": [f"tag{i % 3}"]
                    }
                    for i in range(1, 51)  # 50 products
                ],
                "orders": [
                    {
                        "id": i,
                        "customer_id": (i % 25) + 1,
                        "items": [
                            {
                                "product_id": (i % 10) + 1,
                                "quantity": (i % 3) + 1,
                                "unit_price": f"{(i * 5 + 10):.2f}"
                            }
                        ],
                        "shipping_address": {
                            "street": f"{i} Test Street",
                            "city": "Test City",
                            "state": "CA",
                            "zip_code": "94102",
                            "country": "USA"
                        },
                        "order_date": "2024-01-01T00:00:00Z",
                        "status": "pending"
                    }
                    for i in range(1, 26)  # 25 orders
                ],
                "timestamp": "2024-01-01T00:00:00Z",
                "batch_id": "BATCH-001"
            }
        },

        # Error handling test
        "error_handling": {
            "method": "POST",
            "path": "/validate/error-handling",
            "description": "Validation error handling performance",
            "sample_data": {
                "id": -1,  # Invalid
                "username": "a",  # Too short
                "email": "invalid",  # Wrong format
                "age": 200,  # Too old
                "height": -1.0  # Negative
            }
        }
    }


# Test data generators for load testing
def generate_large_user_batch(count: int = 1000) -> Dict[str, List[Dict]]:
    """Generate large batch of users for stress testing"""
    return {
        "users": [
            {
                "id": i,
                "username": f"stressuser{i}",
                "email": f"stress{i}@example.com",
                "age": 20 + (i % 60),
                "height": 1.5 + (i % 10) * 0.05,
                "is_active": i % 2 == 0,
                "tags": [f"stress", f"batch{i // 100}", f"group{i % 20}"],
                "metadata": {
                    "test_batch": "stress",
                    "iteration": str(i),
                    "timestamp": str(time.time())
                }
            }
            for i in range(1, count + 1)
        ]
    }

def generate_large_product_batch(count: int = 1000) -> Dict[str, List[Dict]]:
    """Generate large batch of products for stress testing"""
    return {
        "products": [
            {
                "name": f"Stress Product {i}",
                "price": f"{(i * 13 + 99) / 100:.2f}",
                "category": f"StressCategory{i % 10}",
                "description": f"Stress test product {i} with detailed description for validation performance testing",
                "sku": f"STRESS-{i:04d}",
                "in_stock": i % 3 != 0,
                "stock_quantity": i * 7,
                "dimensions": {
                    "length": 10.0 + (i % 5),
                    "width": 5.0 + (i % 3),
                    "height": 2.0 + (i % 2)
                },
                "tags": [f"stress", f"category{i % 10}", f"batch{i // 100}"],
                "variants": [
                    {"color": f"color{i % 5}", "size": f"size{i % 3}"}
                ]
            }
            for i in range(1, count + 1)
        ]
    }
