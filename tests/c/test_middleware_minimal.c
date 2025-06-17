/**
 * 🌪️ Catzilla Zero-Allocation Middleware System - Minimal C Tests
 * Basic tests that don't depend on complex middleware structures
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

// Unity test framework
#include "../../deps/unity/src/unity.h"

// Only memory functions - keep it simple
#include "../../src/core/memory.h"

void setUp(void) {
    // Setup before each test
}

void tearDown(void) {
    // Cleanup after each test
}

// Test basic memory allocation which middleware would use
void test_middleware_memory_basics() {
    // Test memory allocation
    void* ptr = catzilla_malloc(256);
    TEST_ASSERT_NOT_NULL_MESSAGE(ptr, "Memory allocation should succeed");

    // Use the memory
    memset(ptr, 0xFF, 256);
    unsigned char* test_data = (unsigned char*)ptr;
    TEST_ASSERT_EQUAL_MESSAGE(0xFF, test_data[0], "Memory should be writable");
    TEST_ASSERT_EQUAL_MESSAGE(0xFF, test_data[255], "Full memory range accessible");

    // Free memory
    catzilla_free(ptr);
}

// Test memory allocation patterns middleware would use
void test_middleware_allocation_patterns() {
    const int num_allocations = 100;
    void* ptrs[100];  // Fixed size array for MSVC compatibility

    // Allocate multiple small blocks (typical middleware usage)
    for (int i = 0; i < num_allocations; i++) {
        ptrs[i] = catzilla_malloc(64);
        TEST_ASSERT_NOT_NULL_MESSAGE(ptrs[i], "Sequential allocations should succeed");

        // Write unique data to each block
        memset(ptrs[i], i & 0xFF, 64);
    }

    // Verify data integrity
    for (int i = 0; i < num_allocations; i++) {
        char* data = (char*)ptrs[i];
        TEST_ASSERT_EQUAL_MESSAGE(i & 0xFF, data[0], "Data should be preserved");
    }

    // Free all memory
    for (int i = 0; i < num_allocations; i++) {
        catzilla_free(ptrs[i]);
    }
}

// Test large allocation (potential middleware context)
void test_middleware_large_allocation() {
    void* large_ptr = catzilla_malloc(8192);
    TEST_ASSERT_NOT_NULL_MESSAGE(large_ptr, "Large allocation should succeed");

    // Write pattern to verify memory integrity
    unsigned char* data = (unsigned char*)large_ptr;
    for (int i = 0; i < 8192; i++) {
        data[i] = i % 256;
    }

    // Verify pattern
    for (int i = 0; i < 8192; i++) {
        TEST_ASSERT_EQUAL_MESSAGE(i % 256, data[i], "Large memory pattern should be preserved");
    }

    catzilla_free(large_ptr);
}

// Test null pointer handling (defensive programming for middleware)
void test_middleware_null_handling() {
    // These should not crash the program
    catzilla_free(NULL);  // Should be safe to free NULL

    // Test allocation of zero size
    void* zero_ptr = catzilla_malloc(0);
    if (zero_ptr != NULL) {
        catzilla_free(zero_ptr);
    }
}

// Test rapid allocation/deallocation (middleware stress test)
void test_middleware_rapid_allocation() {
    for (int iteration = 0; iteration < 1000; iteration++) {
        void* ptr = catzilla_malloc(128);
        TEST_ASSERT_NOT_NULL_MESSAGE(ptr, "Rapid allocation should not fail");

        // Quick write to ensure memory is valid
        memset(ptr, 0xAA, 128);

        catzilla_free(ptr);
    }
}

int main(void) {
    UNITY_BEGIN();

    printf("🌪️ Catzilla Middleware - Minimal C Tests\n");
    printf("========================================\n");

    RUN_TEST(test_middleware_memory_basics);
    RUN_TEST(test_middleware_allocation_patterns);
    RUN_TEST(test_middleware_large_allocation);
    RUN_TEST(test_middleware_null_handling);
    RUN_TEST(test_middleware_rapid_allocation);

    printf("\n✅ Minimal middleware memory tests completed!\n");

    return UNITY_END();
}
