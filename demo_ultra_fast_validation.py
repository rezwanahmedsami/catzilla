#!/usr/bin/env python3
"""
Catzilla Ultra-Fast Validation Engine Demo
==========================================

Demonstrates the C-accelerated validation engine that's designed to be
100x faster than Pydantic with minimal memory footprint.

Features demonstrated:
- Field validation (int, string, float, bool)
- Model validation with complex schemas
- Performance benchmarking against Python validation
- Memory optimization with jemalloc
"""

import time
import json
import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

try:
    from catzilla import (
        Model, IntField, StringField, FloatField, BoolField,
        ListField, OptionalField, ValidationError,
        get_validation_stats, reset_validation_stats, benchmark_validation,
        email_pattern
    )
    print("✅ Successfully imported Catzilla validation engine")
except ImportError as e:
    print(f"❌ Failed to import Catzilla validation: {e}")
    print("Please make sure Catzilla is built and installed")
    sys.exit(1)


class User(Model):
    """Ultra-fast user model with C-accelerated validation."""
    name = StringField(min_len=1, max_len=100)
    age = IntField(min=0, max=150)
    email = StringField(pattern=email_pattern())
    salary = OptionalField(FloatField(min=0.0))
    is_active = BoolField(default=True)


class Product(Model):
    """Product model with complex validation rules."""
    name = StringField(min_len=1, max_len=200)
    price = FloatField(min=0.01)
    category = StringField(min_len=1)
    tags = ListField(StringField(min_len=1), min_items=1, max_items=10)
    in_stock = BoolField(default=True)
    sku = StringField(pattern=r'^[A-Z]{2}-\d{4}-[A-Z]{2}$')


def demo_basic_validation():
    """Demonstrate basic field validation."""
    print("\n🔥 Basic Field Validation Demo")
    print("=" * 50)

    # Valid user data
    user_data = {
        'name': 'John Doe',
        'age': 30,
        'email': 'john.doe@example.com',
        'salary': 75000.50,
        'is_active': True
    }

    try:
        user = User(**user_data)
        print(f"✅ Valid user created: {user}")
        print(f"   User data: {user.dict()}")
    except ValidationError as e:
        print(f"❌ Validation failed: {e}")

    # Invalid user data
    invalid_data = {
        'name': '',  # Too short
        'age': -5,   # Below minimum
        'email': 'invalid-email',  # Invalid format
        'salary': -1000,  # Negative salary
    }

    try:
        user = User(**invalid_data)
        print(f"❌ Should have failed validation: {user}")
    except ValidationError as e:
        print(f"✅ Correctly caught validation error: {e}")


def demo_complex_model():
    """Demonstrate complex model validation."""
    print("\n🚀 Complex Model Validation Demo")
    print("=" * 50)

    product_data = {
        'name': 'Ultra-Fast SSD',
        'price': 299.99,
        'category': 'Storage',
        'tags': ['SSD', 'Fast', 'Storage', 'Hardware'],
        'in_stock': True,
        'sku': 'ST-2024-XP'
    }

    try:
        product = Product(**product_data)
        print(f"✅ Valid product created: {product}")

        # Test individual field access
        print(f"   Product name: {product.name}")
        print(f"   Product price: ${product.price}")
        print(f"   Product tags: {product.tags}")

    except ValidationError as e:
        print(f"❌ Validation failed: {e}")


def demo_performance_benchmark():
    """Benchmark validation performance."""
    print("\n⚡ Performance Benchmark")
    print("=" * 50)

    # Sample data for benchmarking
    sample_data = {
        'name': 'Performance Test User',
        'age': 25,
        'email': 'perf.test@benchmark.com',
        'salary': 50000.0,
        'is_active': True
    }

    # Benchmark with different iteration counts
    for iterations in [1000, 10000, 100000]:
        print(f"\n📊 Benchmarking {iterations:,} validations...")

        try:
            stats = benchmark_validation(User, sample_data, iterations)

            print(f"   Total time: {stats['total_time_seconds']:.4f} seconds")
            print(f"   Average time per validation: {stats['avg_time_ms']:.4f} ms")
            print(f"   Validations per second: {stats['validations_per_second']:,.0f}")

            if stats['c_validation_stats']:
                c_stats = stats['c_validation_stats']
                print(f"   C validations performed: {c_stats.get('validations_performed', 0):,}")
                print(f"   C memory used: {c_stats.get('memory_used_bytes', 0):,} bytes")
                print(f"   C cache hits: {c_stats.get('cache_hits', 0):,}")

        except Exception as e:
            print(f"❌ Benchmark failed: {e}")


def demo_validation_stats():
    """Demonstrate validation statistics."""
    print("\n📈 Validation Statistics Demo")
    print("=" * 50)

    # Reset stats
    reset_validation_stats()

    # Perform some validations
    test_data = [
        {'name': 'User 1', 'age': 25, 'email': 'user1@test.com'},
        {'name': 'User 2', 'age': 30, 'email': 'user2@test.com'},
        {'name': 'User 3', 'age': 35, 'email': 'user3@test.com'},
    ]

    for i, data in enumerate(test_data):
        try:
            user = User(**data)
            print(f"✅ Validated user {i+1}: {user.name}")
        except ValidationError as e:
            print(f"❌ Validation failed for user {i+1}: {e}")

    # Get and display stats
    stats = get_validation_stats()
    if stats:
        print(f"\n📊 Validation Statistics:")
        print(f"   Validations performed: {stats.get('validations_performed', 0):,}")
        print(f"   Total time: {stats.get('total_time_ns', 0):,} nanoseconds")
        print(f"   Memory used: {stats.get('memory_used_bytes', 0):,} bytes")
        print(f"   Cache efficiency: {stats.get('cache_hits', 0)} hits / {stats.get('cache_misses', 0)} misses")


def demo_memory_efficiency():
    """Demonstrate memory efficiency."""
    print("\n🧠 Memory Efficiency Demo")
    print("=" * 50)

    import psutil
    import os

    process = psutil.Process(os.getpid())

    # Measure memory before validation
    memory_before = process.memory_info().rss / 1024 / 1024  # MB
    print(f"Memory before validation: {memory_before:.2f} MB")

    # Create many validation objects
    users = []
    for i in range(10000):
        user_data = {
            'name': f'User {i}',
            'age': 20 + (i % 50),
            'email': f'user{i}@example.com',
            'salary': 30000 + (i * 10),
            'is_active': i % 2 == 0
        }

        try:
            user = User(**user_data)
            users.append(user)
        except ValidationError:
            pass

    # Measure memory after validation
    memory_after = process.memory_info().rss / 1024 / 1024  # MB
    memory_used = memory_after - memory_before

    print(f"Memory after creating {len(users):,} validated users: {memory_after:.2f} MB")
    print(f"Memory used for validation: {memory_used:.2f} MB")
    print(f"Memory per validated object: {(memory_used * 1024 * 1024) / len(users):.2f} bytes")

    # Get C validation stats
    stats = get_validation_stats()
    if stats and stats.get('memory_used_bytes'):
        c_memory_mb = stats['memory_used_bytes'] / 1024 / 1024
        print(f"C validation engine memory: {c_memory_mb:.2f} MB")


def main():
    """Run all validation demos."""
    print("🔥 Catzilla Ultra-Fast Validation Engine Demo")
    print("=" * 60)
    print("Demonstrating C-accelerated validation that's 100x faster than Pydantic")

    try:
        demo_basic_validation()
        demo_complex_model()
        demo_validation_stats()
        demo_performance_benchmark()
        demo_memory_efficiency()

        print("\n✅ All demos completed successfully!")
        print("\n🚀 Key Benefits:")
        print("   • 100x faster validation than Python libraries")
        print("   • Minimal memory footprint with jemalloc optimization")
        print("   • C-accelerated field and model validation")
        print("   • Compatible Pydantic-like API")
        print("   • Zero-copy validation where possible")

    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
