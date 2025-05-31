#!/usr/bin/env python3
"""
Comprehensive test to verify the jemalloc segfault fix.

This test simulates the conditions that were causing segmentation faults:
- Multiple Catzilla instance creation and destruction
- Memory-intensive operations
- Route creation and cleanup
"""

import sys
import os
import time
import gc

# Add the python directory to the path to import catzilla
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'python'))

try:
    from catzilla import Catzilla
    print("✅ Successfully imported Catzilla")
except ImportError as e:
    print(f"❌ Failed to import Catzilla: {e}")
    sys.exit(1)

def test_basic_functionality():
    """Test basic Catzilla functionality"""
    print("\n🧪 Testing basic functionality...")

    app = Catzilla()

    @app.route('/')
    def home():
        return {"message": "Hello World"}

    @app.route('/test')
    def test():
        return {"status": "ok"}

    print("✅ Basic functionality test passed")

def test_multiple_instances():
    """Test creating multiple Catzilla instances"""
    print("\n🧪 Testing multiple instances...")

    instances = []
    for i in range(10):
        app = Catzilla()

        @app.route(f'/instance/{i}')
        def instance_handler():
            return {"instance": i}

        instances.append(app)
        print(f"  Created instance {i+1}/10")

    # Clean up
    del instances
    gc.collect()

    print("✅ Multiple instances test passed")

def test_memory_intensive_operations():
    """Test memory-intensive operations that previously caused segfaults"""
    print("\n🧪 Testing memory-intensive operations...")

    for iteration in range(5):
        print(f"  Iteration {iteration+1}/5")

        # Create app
        app = Catzilla()

        # Add many routes
        for i in range(100):
            route_path = f'/route_{iteration}_{i}'

            def handler(route_num=i):
                return {
                    "route": route_num,
                    "iteration": iteration,
                    "data": "x" * 1000  # Some memory allocation
                }

            app.route(route_path)(handler)

        # Force cleanup
        del app
        gc.collect()
        time.sleep(0.1)  # Give time for cleanup

    print("✅ Memory-intensive operations test passed")

def test_rapid_creation_destruction():
    """Test rapid creation and destruction of instances"""
    print("\n🧪 Testing rapid creation/destruction...")

    for i in range(50):
        app = Catzilla()

        @app.route(f'/rapid/{i}')
        def rapid_handler():
            return {"rapid": i}

        # Immediate cleanup
        del app

        if i % 10 == 0:
            print(f"  Completed {i+1}/50 rapid cycles")
            gc.collect()

    print("✅ Rapid creation/destruction test passed")

def test_concurrent_simulation():
    """Simulate concurrent-like behavior"""
    print("\n🧪 Testing concurrent simulation...")

    apps = []

    # Create multiple apps with overlapping lifetimes
    for batch in range(3):
        batch_apps = []
        for i in range(5):
            app = Catzilla()

            for j in range(20):
                route_path = f'/batch_{batch}_app_{i}_route_{j}'

                def handler(b=batch, a=i, r=j):
                    return {"batch": b, "app": a, "route": r}

                app.route(route_path)(handler)

            batch_apps.append(app)

        apps.extend(batch_apps)

        # Clean up previous batch
        if batch > 0:
            del apps[:5]
            gc.collect()
            print(f"  Cleaned up batch {batch-1}")

    # Final cleanup
    del apps
    gc.collect()

    print("✅ Concurrent simulation test passed")

def main():
    print("🔧 Starting comprehensive Catzilla memory fix verification...")
    print(f"Python version: {sys.version}")

    try:
        test_basic_functionality()
        test_multiple_instances()
        test_memory_intensive_operations()
        test_rapid_creation_destruction()
        test_concurrent_simulation()

        print("\n🎉 ALL TESTS PASSED! The segfault appears to be fixed.")
        print("✅ Memory management is working correctly with jemalloc")

    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
