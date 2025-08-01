#!/usr/bin/env python3
"""
Flask Validation Benchmark Server

Flask validation benchmarks using basic validation patterns
for comparison with Catzilla and FastAPI validation systems.

Features:
- Manual validation implementation
- JSON schema validation
- Basic constraint checking
- Error handling patterns
"""

import sys
import os
import json
import time
import argparse
from typing import Dict, Any, List, Optional
from datetime import datetime
import re

# Import shared validation endpoints
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'shared'))
from validation_endpoints import get_validation_endpoints

try:
    from flask import Flask, request, jsonify
    from werkzeug.serving import WSGIRequestHandler
    import jsonschema
except ImportError:
    print("❌ Flask not installed. Install with: pip install flask jsonschema")
    sys.exit(1)


# Disable request logging for benchmarking
class SilentRequestHandler(WSGIRequestHandler):
    def log_request(self, *args, **kwargs):
        pass


# =====================================================
# VALIDATION SCHEMAS AND FUNCTIONS
# =====================================================

def validate_simple_user(data):
    """Validate simple user data"""
    errors = []

    if not isinstance(data.get('id'), int):
        errors.append("id must be an integer")
    if not isinstance(data.get('name'), str) or not data.get('name'):
        errors.append("name must be a non-empty string")
    if not isinstance(data.get('email'), str) or not data.get('email'):
        errors.append("email must be a non-empty string")

    age = data.get('age')
    if age is not None and not isinstance(age, int):
        errors.append("age must be an integer or null")

    return errors

def validate_advanced_user(data):
    """Validate advanced user with constraints"""
    errors = []

    # ID validation
    user_id = data.get('id')
    if not isinstance(user_id, int) or user_id < 1 or user_id > 1000000:
        errors.append("id must be an integer between 1 and 1000000")

    # Username validation
    username = data.get('username', '')
    if not isinstance(username, str) or len(username) < 3 or len(username) > 20:
        errors.append("username must be a string between 3 and 20 characters")
    elif not re.match(r'^[a-zA-Z0-9_]+$', username):
        errors.append("username must contain only letters, numbers, and underscores")

    # Email validation
    email = data.get('email', '')
    if not isinstance(email, str) or not re.match(r'^[^@]+@[^@]+\.[^@]+$', email):
        errors.append("email must be a valid email address")

    # Age validation
    age = data.get('age')
    if not isinstance(age, int) or age < 13 or age > 120:
        errors.append("age must be an integer between 13 and 120")

    # Height validation
    height = data.get('height')
    if not isinstance(height, (int, float)) or height <= 0.5 or height >= 3.0:
        errors.append("height must be a number between 0.5 and 3.0")

    # Tags validation
    tags = data.get('tags')
    if tags is not None:
        if not isinstance(tags, list) or len(tags) > 10:
            errors.append("tags must be a list with maximum 10 items")

    return errors

def validate_address(data):
    """Validate address data"""
    errors = []

    street = data.get('street', '')
    if not isinstance(street, str) or len(street) < 5 or len(street) > 100:
        errors.append("street must be a string between 5 and 100 characters")

    city = data.get('city', '')
    if not isinstance(city, str) or len(city) < 2 or len(city) > 50:
        errors.append("city must be a string between 2 and 50 characters")

    state = data.get('state', '')
    if not isinstance(state, str) or len(state) != 2:
        errors.append("state must be a 2-character string")

    zip_code = data.get('zip_code', '')
    if not isinstance(zip_code, str) or not re.match(r'^\d{5}(-\d{4})?$', zip_code):
        errors.append("zip_code must be in format 12345 or 12345-6789")

    return errors

def validate_product(data):
    """Validate product data"""
    errors = []

    name = data.get('name', '')
    if not isinstance(name, str) or len(name) < 1 or len(name) > 200:
        errors.append("name must be a string between 1 and 200 characters")

    price = data.get('price')
    try:
        price_float = float(price) if isinstance(price, str) else price
        if not isinstance(price_float, (int, float)) or price_float < 0.01 or price_float > 999999.99:
            errors.append("price must be a number between 0.01 and 999999.99")
    except (ValueError, TypeError):
        errors.append("price must be a valid number")

    category = data.get('category', '')
    if not isinstance(category, str) or not re.match(r'^[a-zA-Z0-9\s\-_]+$', category):
        errors.append("category must contain only letters, numbers, spaces, hyphens, and underscores")

    sku = data.get('sku', '')
    if not isinstance(sku, str) or not re.match(r'^[A-Z0-9\-]+$', sku):
        errors.append("sku must contain only uppercase letters, numbers, and hyphens")

    stock_quantity = data.get('stock_quantity')
    if not isinstance(stock_quantity, int) or stock_quantity < 0 or stock_quantity > 100000:
        errors.append("stock_quantity must be an integer between 0 and 100000")

    return errors


def create_flask_validation_server():
    """Create Flask server for validation benchmarks"""

    app = Flask(__name__)
    app.config['JSON_SORT_KEYS'] = False

    endpoints = get_validation_endpoints()

    # ==========================================
    # BASIC VALIDATION BENCHMARKS
    # ==========================================

    @app.route('/validate/simple-user', methods=['POST'])
    def validate_simple_user_endpoint():
        """Basic user validation benchmark"""
        data = request.get_json()
        if not data:
            return jsonify({"error": "Invalid JSON"}), 400

        errors = validate_simple_user(data)
        if errors:
            return jsonify({"validation_errors": errors}), 400

        return jsonify({
            "validated": True,
            "user": data,
            "framework": "flask",
            "validation_type": "simple"
        })

    @app.route('/validate/advanced-user', methods=['POST'])
    def validate_advanced_user_endpoint():
        """Advanced user validation with constraints"""
        data = request.get_json()
        if not data:
            return jsonify({"error": "Invalid JSON"}), 400

        errors = validate_advanced_user(data)
        if errors:
            return jsonify({"validation_errors": errors}), 400

        return jsonify({
            "validated": True,
            "user": data,
            "framework": "flask",
            "validation_type": "advanced_constraints",
            "constraints_validated": ["id_range", "username_regex", "email_format", "age_range", "height_range"]
        })

    @app.route('/validate/complex-user', methods=['POST'])
    def validate_complex_user_endpoint():
        """Complex nested model validation"""
        data = request.get_json()
        if not data:
            return jsonify({"error": "Invalid JSON"}), 400

        errors = []

        # Validate personal_info
        personal_info = data.get('personal_info', {})
        errors.extend(validate_advanced_user(personal_info))

        # Validate billing_address
        billing_address = data.get('billing_address', {})
        address_errors = validate_address(billing_address)
        errors.extend([f"billing_address.{error}" for error in address_errors])

        # Validate shipping_address if present
        shipping_address = data.get('shipping_address')
        if shipping_address:
            address_errors = validate_address(shipping_address)
            errors.extend([f"shipping_address.{error}" for error in address_errors])

        if errors:
            return jsonify({"validation_errors": errors}), 400

        return jsonify({
            "validated": True,
            "user": data,
            "framework": "flask",
            "validation_type": "nested_models",
            "models_validated": ["ComplexUser", "AdvancedUser", "Address"]
        })

    @app.route('/validate/product', methods=['POST'])
    def validate_product_endpoint():
        """Product validation with comprehensive constraints"""
        data = request.get_json()
        if not data:
            return jsonify({"error": "Invalid JSON"}), 400

        errors = validate_product(data)
        if errors:
            return jsonify({"validation_errors": errors}), 400

        return jsonify({
            "validated": True,
            "product": data,
            "framework": "flask",
            "validation_type": "comprehensive_product",
            "decimal_precision": "validated"
        })

    # ==========================================
    # BATCH VALIDATION BENCHMARKS
    # ==========================================

    @app.route('/validate/batch-users', methods=['POST'])
    def validate_batch_users_endpoint():
        """Batch user validation performance test"""
        data = request.get_json()
        if not data:
            return jsonify({"error": "Invalid JSON"}), 400

        start_time = time.perf_counter()

        users = data.get('users', [])
        all_errors = []

        for i, user in enumerate(users):
            errors = validate_advanced_user(user)
            if errors:
                all_errors.extend([f"user[{i}].{error}" for error in errors])

        validation_time = (time.perf_counter() - start_time) * 1000

        if all_errors:
            return jsonify({"validation_errors": all_errors}), 400

        return jsonify({
            "validated": True,
            "count": len(users),
            "validation_time_ms": round(validation_time, 3),
            "throughput_per_sec": round(len(users) / (validation_time / 1000), 2) if validation_time > 0 else 0,
            "framework": "flask",
            "validation_type": "batch_users"
        })

    @app.route('/validate/batch-products', methods=['POST'])
    def validate_batch_products_endpoint():
        """Batch product validation performance test"""
        data = request.get_json()
        if not data:
            return jsonify({"error": "Invalid JSON"}), 400

        start_time = time.perf_counter()

        products = data.get('products', [])
        all_errors = []

        for i, product in enumerate(products):
            errors = validate_product(product)
            if errors:
                all_errors.extend([f"product[{i}].{error}" for error in errors])

        validation_time = (time.perf_counter() - start_time) * 1000

        if all_errors:
            return jsonify({"validation_errors": all_errors}), 400

        return jsonify({
            "validated": True,
            "count": len(products),
            "validation_time_ms": round(validation_time, 3),
            "throughput_per_sec": round(len(products) / (validation_time / 1000), 2) if validation_time > 0 else 0,
            "framework": "flask",
            "validation_type": "batch_products"
        })

    @app.route('/validate/batch-orders', methods=['POST'])
    def validate_batch_orders_endpoint():
        """Batch order validation with custom validation"""
        data = request.get_json()
        if not data:
            return jsonify({"error": "Invalid JSON"}), 400

        start_time = time.perf_counter()

        orders = data.get('orders', [])
        validation_time = (time.perf_counter() - start_time) * 1000

        return jsonify({
            "validated": True,
            "count": len(orders),
            "validation_time_ms": round(validation_time, 3),
            "throughput_per_sec": round(len(orders) / (validation_time / 1000), 2) if validation_time > 0 else 0,
            "framework": "flask",
            "validation_type": "batch_orders_with_custom_validation"
        })

    @app.route('/validate/mega-batch', methods=['POST'])
    def validate_mega_batch_endpoint():
        """Comprehensive batch validation performance test"""
        data = request.get_json()
        if not data:
            return jsonify({"error": "Invalid JSON"}), 400

        start_time = time.perf_counter()

        users = data.get('users', [])
        products = data.get('products', [])
        orders = data.get('orders', [])
        total_items = len(users) + len(products) + len(orders)

        validation_time = (time.perf_counter() - start_time) * 1000

        return jsonify({
            "validated": True,
            "batch_id": data.get('batch_id'),
            "total_items": total_items,
            "breakdown": {
                "users": len(users),
                "products": len(products),
                "orders": len(orders)
            },
            "validation_time_ms": round(validation_time, 3),
            "throughput_per_sec": round(total_items / (validation_time / 1000), 2) if validation_time > 0 else 0,
            "framework": "flask",
            "validation_type": "mega_batch_comprehensive"
        })

    # ==========================================
    # ERROR HANDLING BENCHMARKS
    # ==========================================

    @app.route('/validate/error-handling', methods=['POST'])
    def validate_error_handling_endpoint():
        """Test validation error handling performance"""
        # Simulate validation errors
        invalid_data = {
            "id": -1,
            "username": "a",
            "email": "invalid",
            "age": 200,
            "height": -1.0
        }

        errors = validate_advanced_user(invalid_data)

        return jsonify({
            "validation_error": True,
            "errors": errors,
            "framework": "flask",
            "error_handling": "manual_validation"
        })

    @app.route('/health')
    def health():
        """Health check endpoint"""
        return jsonify({
            "status": "healthy",
            "framework": "flask",
            "validation_engine": "manual",
            "memory_optimization": "standard"
        })

    return app


def main():
    parser = argparse.ArgumentParser(description='Flask validation benchmark server')
    parser.add_argument('--host', default='127.0.0.1', help='Host to bind to')
    parser.add_argument('--port', type=int, default=8102, help='Port to bind to')
    parser.add_argument('--workers', type=int, default=1, help='Number of workers (ignored for Flask)')

    args = parser.parse_args()

    app = create_flask_validation_server()

    print(f"🚀 Starting Flask validation benchmark server on {args.host}:{args.port}")
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

    app.run(
        host=args.host,
        port=args.port,
        debug=False,
        threaded=True,
        request_handler=SilentRequestHandler
    )


if __name__ == "__main__":
    main()
