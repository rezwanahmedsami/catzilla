#!/usr/bin/env python3
"""
Simplified comprehensive test to verify segfault fixes work.
Focus on the core issues that were causing segfaults without complex validation.
"""

import gc
import sys
import os

# Ensure we can import catzilla
sys.path.insert(0, '/Users/user/devwork/catzilla/python')

from catzilla.validation import BaseModel, ValidationError
from typing import List, Optional


def test_batch_validation_segfault_fix():
    """Test the main segfault fix: batch validation with GC pressure"""
    print("🧪 Testing batch validation segfault fix...")

    class BatchModel(BaseModel):
        id: int
        data: str
        optional_field: Optional[int] = None

    # This is the exact scenario that was causing segfaults
    batch_size = 100
    num_batches = 50
    total_models = 0

    for batch in range(num_batches):
        models = []
        for i in range(batch_size):
            model = BatchModel(
                id=batch * batch_size + i,
                data=f"data_{i}",
                optional_field=i if i % 2 == 0 else None
            )
            models.append(model)
            total_models += 1

        # This garbage collection was triggering segfaults before our fix
        if batch % 10 == 0 and batch > 0:
            gc.collect()

    print(f"✅ Successfully processed {total_models} models without segfaults")
    return True


def test_nested_type_segfault_fix():
    """Test nested type validation segfault fix"""
    print("🧪 Testing nested type validation segfault fix...")

    class NestedModel(BaseModel):
        simple_list: Optional[List[str]] = None

    # These cases were causing segfaults in nested validator creation
    test_cases = [
        {"simple_list": ["a", "b", "c"]},
        {"simple_list": None},
        {},
    ]

    for i, test_data in enumerate(test_cases):
        model = NestedModel(**test_data)
        print(f"   Test case {i+1}: {model.dict()}")

    print("✅ Nested type validation completed successfully")
    return True


def test_memory_cleanup_segfault_fix():
    """Test memory cleanup segfault fix"""
    print("🧪 Testing memory cleanup segfault fix...")

    class CleanupModel(BaseModel):
        id: int
        name: str

    # Create and destroy models to test cleanup
    for round in range(10):
        models = []
        for i in range(50):
            model = CleanupModel(id=i, name=f"model_{i}")
            models.append(model)

        # Clear and force GC - this was causing segfaults
        del models
        gc.collect()

    print("✅ Memory cleanup test completed successfully")
    return True


def run_critical_segfault_tests():
    """Run only the critical tests that verify segfault fixes"""
    print("🚀 Testing critical segfault fixes...")

    tests = [
        test_batch_validation_segfault_fix,
        test_nested_type_segfault_fix,
        test_memory_cleanup_segfault_fix,
    ]

    for test_func in tests:
        try:
            success = test_func()
            if not success:
                print(f"❌ Test {test_func.__name__} failed")
                return False
        except Exception as e:
            print(f"❌ Test {test_func.__name__} crashed: {e}")
            import traceback
            traceback.print_exc()
            return False

    print("\n🎉 ALL CRITICAL SEGFAULT TESTS PASSED!")
    print("✅ Catzilla validation engine segfaults have been fixed")

    return True


if __name__ == "__main__":
    # Disable debug output for cleaner test
    os.environ.pop('CATZILLA_C_DEBUG', None)

    success = run_critical_segfault_tests()

    sys.exit(0 if success else 1)
