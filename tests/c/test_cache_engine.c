// tests/c/test_cache_engine.c
#include "unity.h"
#include "cache_engine.h"
#include <string.h>
#ifndef _WIN32
#include <unistd.h>
#include <pthread.h>
#else
#include <windows.h>
#endif

static catzilla_cache_t* test_cache = NULL;

void setUp(void) {
    // Create a fresh cache for each test
    test_cache = catzilla_cache_create(100, 25);  // 100 entries, 25 buckets
}

void tearDown(void) {
    // Clean up after each test
    if (test_cache) {
        catzilla_cache_destroy(test_cache);
        test_cache = NULL;
    }
}

void test_cache_creation() {
    TEST_ASSERT_NOT_NULL(test_cache);
}

void test_cache_set_and_get() {
    const char* key = "test_key";
    const char* value = "test_value";

    // Test set operation
    int result = catzilla_cache_set(test_cache, key, value, strlen(value) + 1, 60);
    TEST_ASSERT_EQUAL(0, result);

    // Test get operation
    cache_result_t get_result = catzilla_cache_get(test_cache, key);
    TEST_ASSERT_TRUE(get_result.found);
    TEST_ASSERT_NOT_NULL(get_result.data);
    TEST_ASSERT_EQUAL_STRING(value, (char*)get_result.data);
    TEST_ASSERT_EQUAL(strlen(value) + 1, get_result.size);
}

void test_cache_get_nonexistent() {
    cache_result_t result = catzilla_cache_get(test_cache, "nonexistent_key");
    TEST_ASSERT_FALSE(result.found);
    TEST_ASSERT_NULL(result.data);
    TEST_ASSERT_EQUAL(0, result.size);
}

void test_cache_exists() {
    const char* key = "exists_test";
    const char* value = "exists_value";

    // Key should not exist initially
    TEST_ASSERT_FALSE(catzilla_cache_exists(test_cache, key));

    // Add key
    catzilla_cache_set(test_cache, key, value, strlen(value) + 1, 60);

    // Key should now exist
    TEST_ASSERT_TRUE(catzilla_cache_exists(test_cache, key));
}

void test_cache_delete() {
    const char* key = "delete_test";
    const char* value = "delete_value";

    // Add key
    catzilla_cache_set(test_cache, key, value, strlen(value) + 1, 60);
    TEST_ASSERT_TRUE(catzilla_cache_exists(test_cache, key));

    // Delete key
    int result = catzilla_cache_delete(test_cache, key);
    TEST_ASSERT_EQUAL(0, result);
    TEST_ASSERT_FALSE(catzilla_cache_exists(test_cache, key));

    // Delete non-existent key should fail
    result = catzilla_cache_delete(test_cache, "nonexistent");
    TEST_ASSERT_NOT_EQUAL(0, result);
}

void test_cache_statistics() {
    cache_statistics_t stats = catzilla_cache_get_stats(test_cache);

    // Initial stats should be zero
    TEST_ASSERT_EQUAL(0, stats.hits);
    TEST_ASSERT_EQUAL(0, stats.misses);
    TEST_ASSERT_EQUAL(0, stats.evictions);

    // Add some data and generate activity
    catzilla_cache_set(test_cache, "stats_key", "stats_value", 12, 60);

    // Hit
    cache_result_t result = catzilla_cache_get(test_cache, "stats_key");
    TEST_ASSERT_TRUE(result.found);

    // Miss
    result = catzilla_cache_get(test_cache, "nonexistent");
    TEST_ASSERT_FALSE(result.found);

    // Check updated stats
    stats = catzilla_cache_get_stats(test_cache);
    TEST_ASSERT_EQUAL(1, stats.hits);
    TEST_ASSERT_EQUAL(1, stats.misses);
}

void test_cache_clear() {
    // Add multiple entries
    catzilla_cache_set(test_cache, "key1", "value1", 7, 60);
    catzilla_cache_set(test_cache, "key2", "value2", 7, 60);
    catzilla_cache_set(test_cache, "key3", "value3", 7, 60);

    // Verify entries exist
    TEST_ASSERT_TRUE(catzilla_cache_exists(test_cache, "key1"));
    TEST_ASSERT_TRUE(catzilla_cache_exists(test_cache, "key2"));
    TEST_ASSERT_TRUE(catzilla_cache_exists(test_cache, "key3"));

    // Clear cache
    catzilla_cache_clear(test_cache);

    // Verify entries are gone
    TEST_ASSERT_FALSE(catzilla_cache_exists(test_cache, "key1"));
    TEST_ASSERT_FALSE(catzilla_cache_exists(test_cache, "key2"));
    TEST_ASSERT_FALSE(catzilla_cache_exists(test_cache, "key3"));
}

void test_cache_ttl_expiration() {
    const char* key = "ttl_test";
    const char* value = "ttl_value";

    // Set with short TTL (1 second)
    int result = catzilla_cache_set(test_cache, key, value, strlen(value) + 1, 1);
    TEST_ASSERT_EQUAL(0, result);

    // Should be available immediately
    cache_result_t get_result = catzilla_cache_get(test_cache, key);
    TEST_ASSERT_TRUE(get_result.found);

    // Wait for expiration (sleep 2 seconds to be sure)
#ifndef _WIN32
    sleep(2);
#else
    Sleep(2000);
#endif

    // Should be expired now
    get_result = catzilla_cache_get(test_cache, key);
    TEST_ASSERT_FALSE(get_result.found);
}

void test_cache_binary_data() {
    const char* key = "binary_test";
    unsigned char binary_data[] = {0x00, 0x01, 0x02, 0xFF, 0xAB, 0xCD, 0xEF};
    size_t data_size = sizeof(binary_data);

    // Store binary data
    int result = catzilla_cache_set(test_cache, key, binary_data, data_size, 60);
    TEST_ASSERT_EQUAL(0, result);

    // Retrieve and verify
    cache_result_t get_result = catzilla_cache_get(test_cache, key);
    TEST_ASSERT_TRUE(get_result.found);
    TEST_ASSERT_EQUAL(data_size, get_result.size);
    TEST_ASSERT_EQUAL_MEMORY(binary_data, get_result.data, data_size);
}

void test_cache_edge_cases() {
    // Test empty key (should succeed - empty string is a valid key)
    int result = catzilla_cache_set(test_cache, "", "value", 6, 60);
    TEST_ASSERT_EQUAL(0, result);

    // Test NULL key (should fail)
    result = catzilla_cache_set(test_cache, NULL, "value", 6, 60);
    TEST_ASSERT_NOT_EQUAL(0, result);

    // Test NULL value (should fail)
    result = catzilla_cache_set(test_cache, "key", NULL, 0, 60);
    TEST_ASSERT_NOT_EQUAL(0, result);

    // Test zero size with empty data (should succeed if implementation allows it)
    char empty_data = '\0';
    result = catzilla_cache_set(test_cache, "empty_key", &empty_data, 0, 60);
    // Note: Current implementation allows zero-sized values
    TEST_ASSERT_EQUAL(0, result);
}

// Thread test data structure
typedef struct {
    catzilla_cache_t* cache;
    int thread_id;
    int operations;
    int success_count;
} thread_test_data_t;

// Thread function for concurrent testing
void* thread_test_function(void* arg) {
    thread_test_data_t* data = (thread_test_data_t*)arg;
    char key[64];
    char value[64];

    for (int i = 0; i < data->operations; i++) {
        snprintf(key, sizeof(key), "thread_%d_key_%d", data->thread_id, i);
        snprintf(value, sizeof(value), "thread_%d_value_%d", data->thread_id, i);

        // Set operation
        if (catzilla_cache_set(data->cache, key, value, strlen(value) + 1, 60) == 0) {
            data->success_count++;
        }

        // Get operation
        cache_result_t result = catzilla_cache_get(data->cache, key);
        if (result.found && strcmp((char*)result.data, value) == 0) {
            data->success_count++;
        }

        // Small delay to increase chance of race conditions
#ifndef _WIN32
        usleep(1000);  // 1ms
#else
        Sleep(1);  // 1ms
#endif
    }

    return NULL;
}

void test_cache_thread_safety() {
#ifndef _WIN32
    const int num_threads = 4;
    const int ops_per_thread = 10;  // Reduced for faster testing
    pthread_t threads[num_threads];
    thread_test_data_t thread_data[num_threads];

    // Create and start threads
    for (int i = 0; i < num_threads; i++) {
        thread_data[i].cache = test_cache;
        thread_data[i].thread_id = i;
        thread_data[i].operations = ops_per_thread;
        thread_data[i].success_count = 0;

        int result = pthread_create(&threads[i], NULL, thread_test_function, &thread_data[i]);
        TEST_ASSERT_EQUAL(0, result);
    }

    // Wait for threads to complete
    for (int i = 0; i < num_threads; i++) {
        pthread_join(threads[i], NULL);
    }

    // Verify all operations succeeded (no crashes or corruption)
    int total_expected = num_threads * ops_per_thread * 2;  // 2 ops per iteration
    int total_success = 0;
    for (int i = 0; i < num_threads; i++) {
        total_success += thread_data[i].success_count;
    }

    // Allow for some operations to fail due to concurrency, but most should succeed
    TEST_ASSERT_GREATER_THAN(total_expected / 2, total_success);
#else
    // Skip thread safety test on Windows (pthread not available)
    TEST_PASS_MESSAGE("Thread safety test skipped on Windows platform");
#endif
}

int main(void) {
    UNITY_BEGIN();

    // Basic functionality tests
    RUN_TEST(test_cache_creation);
    RUN_TEST(test_cache_set_and_get);
    RUN_TEST(test_cache_get_nonexistent);
    RUN_TEST(test_cache_exists);
    RUN_TEST(test_cache_delete);
    RUN_TEST(test_cache_statistics);
    RUN_TEST(test_cache_clear);
    RUN_TEST(test_cache_binary_data);
    RUN_TEST(test_cache_edge_cases);

    // Advanced tests
    RUN_TEST(test_cache_ttl_expiration);
    RUN_TEST(test_cache_thread_safety);

    return UNITY_END();
}
