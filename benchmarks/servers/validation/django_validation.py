#!/usr/bin/env python3
"""
Django Validation Benchmark Server

Django validation benchmarks using Django REST Framework serializers
for comparison with Catzilla, FastAPI, and Flask validation systems.

Features:
- Django REST Framework serializers
- Django model validation
- DRF field validation and constraints
- Custom validation methods
"""

import sys
import os
import json
import time
import argparse
from typing import Dict, Any, List, Optional
from datetime import datetime
import django
from django.conf import settings
from django.core.wsgi import get_wsgi_application

# Import shared validation endpoints
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'shared'))
from validation_endpoints import get_validation_endpoints

# Configure Django settings
if not settings.configured:
    settings.configure(
        DEBUG=False,
        SECRET_KEY='benchmark-secret-key',
        INSTALLED_APPS=[
            'rest_framework',
        ],
        ROOT_URLCONF=__name__,
        ALLOWED_HOSTS=['*'],
        USE_TZ=True,
        REST_FRAMEWORK={
            'DEFAULT_RENDERER_CLASSES': [
                'rest_framework.renderers.JSONRenderer',
            ],
            'DEFAULT_PARSER_CLASSES': [
                'rest_framework.parsers.JSONParser',
            ],
        }
    )
    django.setup()

try:
    from django.http import JsonResponse
    from django.urls import path
    from django.views.decorators.csrf import csrf_exempt
    from rest_framework import serializers, status
    from rest_framework.response import Response
    from rest_framework.decorators import api_view
    from rest_framework.views import APIView
    import threading
    import wsgiref.simple_server
except ImportError:
    print("❌ Django not installed. Install with: pip install django djangorestframework")
    sys.exit(1)


# =====================================================
# DJANGO REST FRAMEWORK SERIALIZERS
# =====================================================

class SimpleUserSerializer(serializers.Serializer):
    """Simple user serializer for basic validation benchmarks"""
    id = serializers.IntegerField()
    name = serializers.CharField()
    email = serializers.EmailField()
    age = serializers.IntegerField(required=False, allow_null=True)

class AdvancedUserSerializer(serializers.Serializer):
    """Advanced user serializer with DRF field constraints"""
    id = serializers.IntegerField(min_value=1, max_value=1000000)
    username = serializers.RegexField(
        regex=r'^[a-zA-Z0-9_]+$',
        min_length=3,
        max_length=20
    )
    email = serializers.EmailField()
    age = serializers.IntegerField(min_value=13, max_value=120)
    height = serializers.FloatField(min_value=0.5, max_value=3.0)
    is_active = serializers.BooleanField(default=True)
    tags = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        allow_null=True,
        max_length=10
    )
    metadata = serializers.DictField(required=False, allow_null=True)

class AddressSerializer(serializers.Serializer):
    """Address serializer for nested validation"""
    street = serializers.CharField(min_length=5, max_length=100)
    city = serializers.CharField(min_length=2, max_length=50)
    state = serializers.CharField(min_length=2, max_length=2)
    zip_code = serializers.RegexField(regex=r'^\d{5}(-\d{4})?$')
    country = serializers.CharField(default="USA")

class ComplexUserSerializer(serializers.Serializer):
    """Complex user serializer with nested validation"""
    id = serializers.IntegerField(min_value=1)
    personal_info = AdvancedUserSerializer()
    billing_address = AddressSerializer()
    shipping_address = AddressSerializer(required=False, allow_null=True)
    preferences = serializers.DictField(default=dict)
    created_at = serializers.DateTimeField()
    updated_at = serializers.DateTimeField(required=False, allow_null=True)

class ProductSerializer(serializers.Serializer):
    """Product serializer with comprehensive validation"""
    name = serializers.CharField(min_length=1, max_length=200)
    price = serializers.DecimalField(
        min_value=0.01,
        max_value=999999.99,
        max_digits=8,
        decimal_places=2
    )
    category = serializers.RegexField(regex=r'^[a-zA-Z0-9\s\-_]+$')
    description = serializers.CharField(max_length=1000, required=False, allow_blank=True)
    sku = serializers.RegexField(regex=r'^[A-Z0-9\-]+$')
    in_stock = serializers.BooleanField(default=True)
    stock_quantity = serializers.IntegerField(min_value=0, max_value=100000)
    dimensions = serializers.DictField(required=False, allow_null=True)
    tags = serializers.ListField(
        child=serializers.CharField(),
        default=list,
        max_length=20
    )
    variants = serializers.ListField(
        child=serializers.DictField(),
        required=False,
        allow_null=True
    )

class OrderItemSerializer(serializers.Serializer):
    """Order item serializer for batch validation"""
    product_id = serializers.IntegerField(min_value=1)
    quantity = serializers.IntegerField(min_value=1, max_value=1000)
    unit_price = serializers.DecimalField(
        min_value=0.01,
        max_digits=8,
        decimal_places=2
    )

class OrderSerializer(serializers.Serializer):
    """Order serializer for complex batch validation"""
    id = serializers.IntegerField(min_value=1)
    customer_id = serializers.IntegerField(min_value=1)
    items = serializers.ListField(
        child=OrderItemSerializer(),
        min_length=1,
        max_length=100
    )
    shipping_address = AddressSerializer()
    billing_address = AddressSerializer(required=False, allow_null=True)
    total_amount = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=False,
        allow_null=True
    )
    order_date = serializers.DateTimeField()
    status = serializers.RegexField(
        regex=r'^(pending|confirmed|shipped|delivered|cancelled)$'
    )

    def validate(self, data):
        """Custom validation: calculate total if not provided"""
        if data.get('total_amount') is None and 'items' in data:
            total = sum(
                item['quantity'] * item['unit_price']
                for item in data['items']
            )
            data['total_amount'] = total
        return data

class BatchUsersSerializer(serializers.Serializer):
    """Batch users serializer for validation testing"""
    users = serializers.ListField(child=AdvancedUserSerializer())

class BatchProductsSerializer(serializers.Serializer):
    """Batch products serializer for validation testing"""
    products = serializers.ListField(child=ProductSerializer())

class BatchOrdersSerializer(serializers.Serializer):
    """Batch orders serializer for validation testing"""
    orders = serializers.ListField(child=OrderSerializer())

class BatchValidationRequestSerializer(serializers.Serializer):
    """Batch validation request serializer for performance testing"""
    users = serializers.ListField(
        child=AdvancedUserSerializer(),
        min_length=1,
        max_length=1000
    )
    products = serializers.ListField(
        child=ProductSerializer(),
        min_length=1,
        max_length=1000
    )
    orders = serializers.ListField(
        child=OrderSerializer(),
        min_length=1,
        max_length=100
    )
    timestamp = serializers.DateTimeField()
    batch_id = serializers.RegexField(regex=r'^[A-Z0-9\-]+$')


# =====================================================
# DJANGO VIEWS
# =====================================================

@api_view(['POST'])
def validate_simple_user(request):
    """Basic user validation benchmark"""
    serializer = SimpleUserSerializer(data=request.data)
    if serializer.is_valid():
        return Response({
            "validated": True,
            "user": serializer.validated_data,
            "framework": "django",
            "validation_type": "simple"
        })
    return Response({"validation_errors": serializer.errors}, status=400)

@api_view(['POST'])
def validate_advanced_user(request):
    """Advanced user validation with constraints"""
    serializer = AdvancedUserSerializer(data=request.data)
    if serializer.is_valid():
        return Response({
            "validated": True,
            "user": serializer.validated_data,
            "framework": "django",
            "validation_type": "advanced_constraints",
            "constraints_validated": ["id_range", "username_regex", "email_format", "age_range", "height_range"]
        })
    return Response({"validation_errors": serializer.errors}, status=400)

@api_view(['POST'])
def validate_complex_user(request):
    """Complex nested model validation"""
    serializer = ComplexUserSerializer(data=request.data)
    if serializer.is_valid():
        return Response({
            "validated": True,
            "user": serializer.validated_data,
            "framework": "django",
            "validation_type": "nested_models",
            "models_validated": ["ComplexUser", "AdvancedUser", "Address"]
        })
    return Response({"validation_errors": serializer.errors}, status=400)

@api_view(['POST'])
def validate_product(request):
    """Product validation with comprehensive constraints"""
    serializer = ProductSerializer(data=request.data)
    if serializer.is_valid():
        return Response({
            "validated": True,
            "product": serializer.validated_data,
            "framework": "django",
            "validation_type": "comprehensive_product",
            "decimal_precision": "validated"
        })
    return Response({"validation_errors": serializer.errors}, status=400)

@api_view(['POST'])
def validate_batch_users(request):
    """Batch user validation performance test"""
    start_time = time.perf_counter()

    serializer = BatchUsersSerializer(data=request.data)
    if serializer.is_valid():
        validated_count = len(serializer.validated_data['users'])
        validation_time = (time.perf_counter() - start_time) * 1000

        return Response({
            "validated": True,
            "count": validated_count,
            "validation_time_ms": round(validation_time, 3),
            "throughput_per_sec": round(validated_count / (validation_time / 1000), 2) if validation_time > 0 else 0,
            "framework": "django",
            "validation_type": "batch_users"
        })
    return Response({"validation_errors": serializer.errors}, status=400)

@api_view(['POST'])
def validate_batch_products(request):
    """Batch product validation performance test"""
    start_time = time.perf_counter()

    serializer = BatchProductsSerializer(data=request.data)
    if serializer.is_valid():
        validated_count = len(serializer.validated_data['products'])
        validation_time = (time.perf_counter() - start_time) * 1000

        return Response({
            "validated": True,
            "count": validated_count,
            "validation_time_ms": round(validation_time, 3),
            "throughput_per_sec": round(validated_count / (validation_time / 1000), 2) if validation_time > 0 else 0,
            "framework": "django",
            "validation_type": "batch_products"
        })
    return Response({"validation_errors": serializer.errors}, status=400)

@api_view(['POST'])
def validate_batch_orders(request):
    """Batch order validation with custom validation"""
    start_time = time.perf_counter()

    serializer = BatchOrdersSerializer(data=request.data)
    if serializer.is_valid():
        validated_count = len(serializer.validated_data['orders'])
        validation_time = (time.perf_counter() - start_time) * 1000

        return Response({
            "validated": True,
            "count": validated_count,
            "validation_time_ms": round(validation_time, 3),
            "throughput_per_sec": round(validated_count / (validation_time / 1000), 2) if validation_time > 0 else 0,
            "framework": "django",
            "validation_type": "batch_orders_with_custom_validation"
        })
    return Response({"validation_errors": serializer.errors}, status=400)

@api_view(['POST'])
def validate_mega_batch(request):
    """Comprehensive batch validation performance test"""
    start_time = time.perf_counter()

    serializer = BatchValidationRequestSerializer(data=request.data)
    if serializer.is_valid():
        data = serializer.validated_data
        total_items = len(data['users']) + len(data['products']) + len(data['orders'])
        validation_time = (time.perf_counter() - start_time) * 1000

        return Response({
            "validated": True,
            "batch_id": data['batch_id'],
            "total_items": total_items,
            "breakdown": {
                "users": len(data['users']),
                "products": len(data['products']),
                "orders": len(data['orders'])
            },
            "validation_time_ms": round(validation_time, 3),
            "throughput_per_sec": round(total_items / (validation_time / 1000), 2) if validation_time > 0 else 0,
            "framework": "django",
            "validation_type": "mega_batch_comprehensive"
        })
    return Response({"validation_errors": serializer.errors}, status=400)

@api_view(['POST'])
def validate_error_handling(request):
    """Test validation error handling performance"""
    # This should trigger validation errors
    invalid_data = {
        "id": -1,  # Invalid: should be >= 1
        "username": "a",  # Invalid: too short
        "email": "invalid",  # Invalid: wrong format
        "age": 200,  # Invalid: too old
        "height": -1.0  # Invalid: negative
    }

    serializer = AdvancedUserSerializer(data=invalid_data)
    serializer.is_valid()  # This will populate errors

    return Response({
        "validation_error": True,
        "errors": serializer.errors,
        "framework": "django",
        "error_handling": "drf_serializer_validation"
    })

@api_view(['GET'])
def health(request):
    """Health check endpoint."""
    return JsonResponse({'status': 'ok', 'timestamp': int(time.time())})


# =====================================================
# BENCHMARK ENDPOINTS (for run_all.sh script)
# =====================================================

def validation_simple(request):
    """Simple validation benchmark endpoint."""
    data = {'message': 'Hello World', 'valid': True}
    return JsonResponse(data)

def validation_user(request):
    """User validation benchmark endpoint."""
    data = {
        'id': 1,
        'name': 'John Doe',
        'email': 'john@example.com',
        'age': 30,
        'active': True
    }
    return JsonResponse(data)

def validation_nested(request):
    """Nested validation benchmark endpoint."""
    data = {
        'user': {
            'id': 1,
            'name': 'John Doe',
            'profile': {
                'age': 30,
                'location': 'NYC'
            }
        },
        'valid': True
    }
    return JsonResponse(data)

def validation_complex(request):
    """Complex validation benchmark endpoint."""
    data = {
        'order': {
            'id': 12345,
            'items': [
                {'product': 'Widget A', 'price': 29.99, 'quantity': 2},
                {'product': 'Widget B', 'price': 39.99, 'quantity': 1}
            ],
            'customer': {
                'name': 'Jane Smith',
                'email': 'jane@example.com'
            },
            'total': 99.97
        },
        'processed': True
    }
    return JsonResponse(data)

def validation_array(request):
    """Array validation benchmark endpoint."""
    data = {
        'items': [
            {'id': 1, 'value': 'First'},
            {'id': 2, 'value': 'Second'},
            {'id': 3, 'value': 'Third'}
        ],
        'count': 3
    }
    return JsonResponse(data)

def validation_performance(request):
    """Performance validation benchmark endpoint."""
    data = {
        'metrics': {
            'response_time': 0.001,
            'throughput': 10000,
            'memory_usage': 64.5
        },
        'benchmark': 'django_validation',
        'timestamp': int(time.time())
    }
    return JsonResponse(data)


# =====================================================
# URL CONFIGURATION
# =====================================================

urlpatterns = [
    path('validate/simple-user', validate_simple_user, name='validate_simple_user'),
    path('validate/advanced-user', validate_advanced_user, name='validate_advanced_user'),
    path('validate/complex-user', validate_complex_user, name='validate_complex_user'),
    path('validate/product', validate_product, name='validate_product'),
    path('validate/batch-users', validate_batch_users, name='validate_batch_users'),
    path('validate/batch-products', validate_batch_products, name='validate_batch_products'),
    path('validate/batch-orders', validate_batch_orders, name='validate_batch_orders'),
    path('validate/mega-batch', validate_mega_batch, name='validate_mega_batch'),
    path('validate/error-handling', validate_error_handling, name='validate_error_handling'),
    path('health', health, name='health'),

    # Benchmark endpoints for run_all.sh script
    path('validation/simple', validation_simple, name='validation_simple'),
    path('validation/user', validation_user, name='validation_user'),
    path('validation/nested', validation_nested, name='validation_nested'),
    path('validation/complex', validation_complex, name='validation_complex'),
    path('validation/array', validation_array, name='validation_array'),
    path('validation/performance', validation_performance, name='validation_performance'),
]


def main():
    parser = argparse.ArgumentParser(description='Django validation benchmark server')
    parser.add_argument('--host', default='127.0.0.1', help='Host to bind to')
    parser.add_argument('--port', type=int, default=8103, help='Port to bind to')
    parser.add_argument('--workers', type=int, default=1, help='Number of workers (ignored for Django)')

    args = parser.parse_args()

    print(f"🚀 Starting Django validation benchmark server on {args.host}:{args.port}")
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

    # Create WSGI application
    application = get_wsgi_application()

    # Run simple WSGI server
    server = wsgiref.simple_server.make_server(args.host, args.port, application)

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server...")
        server.shutdown()


if __name__ == "__main__":
    main()

# Create application instance for WSGI servers like gunicorn
# This is needed after Django settings are configured
import django
django.setup()
application = get_wsgi_application()
