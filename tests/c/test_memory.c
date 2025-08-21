#include "unity.h"
#include "memory.h"
#include <stdlib.h>
#ifdef _WIN32
    #include <process.h>
    #include <windows.h>
    #define sleep(x) Sleep((x) * 1000)
#else
    #include <unistd.h>
#endif

void setUp(void) {
    // Clean up any existing state
    catzilla_memory_cleanup();
}

void tearDown(void) {
    // Clean up after each test
    catzilla_memory_cleanup();
}

void test_memory_init_and_cleanup(void) {
    // Test basic memory initialization
    int result = catzilla_memory_init();
    TEST_ASSERT_EQUAL(0, result);

    // Test that stats are properly initialized
    catzilla_memory_stats_t stats;
    catzilla_memory_get_stats(&stats);

    // Test cleanup
    catzilla_memory_cleanup();
}

void test_multiple_init_cleanup_cycles(void) {
    // Test that we can initialize and cleanup multiple times without issues
    for (int i = 0; i < 5; i++) {
        int result = catzilla_memory_init();
        TEST_ASSERT_EQUAL(0, result);

        // Allocate some memory using the arena
        void* ptr = catzilla_malloc(1024);
        TEST_ASSERT_NOT_NULL(ptr);

        // Free the memory
        catzilla_free(ptr);

        // Cleanup
        catzilla_memory_cleanup();
    }
}

void test_arena_allocation(void) {
    // Initialize memory system
    int result = catzilla_memory_init();
    TEST_ASSERT_EQUAL(0, result);

    // Test allocations of various sizes
    void* ptr1 = catzilla_malloc(64);
    void* ptr2 = catzilla_malloc(1024);
    void* ptr3 = catzilla_malloc(4096);

    TEST_ASSERT_NOT_NULL(ptr1);
    TEST_ASSERT_NOT_NULL(ptr2);
    TEST_ASSERT_NOT_NULL(ptr3);

    // Free all allocations
    catzilla_free(ptr1);
    catzilla_free(ptr2);
    catzilla_free(ptr3);
}

void test_memory_stats(void) {
    int result = catzilla_memory_init();
    TEST_ASSERT_EQUAL(0, result);

    catzilla_memory_stats_t stats;
    catzilla_memory_get_stats(&stats);

    // Verify that we got reasonable arena IDs
    TEST_ASSERT_NOT_EQUAL(0, stats.request_arena);
    TEST_ASSERT_NOT_EQUAL(0, stats.response_arena);
    TEST_ASSERT_NOT_EQUAL(0, stats.cache_arena);
}

void test_typed_allocations(void) {
    int result = catzilla_memory_init();
    TEST_ASSERT_EQUAL(0, result);

    // Test different types of allocations
    void* req_ptr = catzilla_request_alloc(256);
    void* resp_ptr = catzilla_response_alloc(512);
    void* cache_ptr = catzilla_cache_alloc(1024);

    TEST_ASSERT_NOT_NULL(req_ptr);
    TEST_ASSERT_NOT_NULL(resp_ptr);
    TEST_ASSERT_NOT_NULL(cache_ptr);

    // Free using typed free functions
    catzilla_request_free(req_ptr);
    catzilla_response_free(resp_ptr);
    catzilla_cache_free(cache_ptr);
}

void test_concurrent_operations(void) {
    int result = catzilla_memory_init();
    TEST_ASSERT_EQUAL(0, result);

    // Simulate multiple allocations and deallocations
    void* ptrs[100];

    // Allocate
    for (int i = 0; i < 100; i++) {
        ptrs[i] = catzilla_malloc(64 + (i % 1000));
        TEST_ASSERT_NOT_NULL(ptrs[i]);
    }

    // Free every other one
    for (int i = 0; i < 100; i += 2) {
        catzilla_free(ptrs[i]);
        ptrs[i] = NULL;
    }

    // Allocate again in freed slots
    for (int i = 0; i < 100; i += 2) {
        ptrs[i] = catzilla_malloc(128 + (i % 500));
        TEST_ASSERT_NOT_NULL(ptrs[i]);
    }

    // Free all remaining
    for (int i = 0; i < 100; i++) {
        if (ptrs[i]) {
            catzilla_free(ptrs[i]);
        }
    }
}

int main(void) {
    UNITY_BEGIN();

    RUN_TEST(test_memory_init_and_cleanup);
    RUN_TEST(test_multiple_init_cleanup_cycles);
    RUN_TEST(test_arena_allocation);
    RUN_TEST(test_memory_stats);
    RUN_TEST(test_typed_allocations);
    RUN_TEST(test_concurrent_operations);

    return UNITY_END();
}
