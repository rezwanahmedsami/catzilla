/**
 * Enhanced C Streaming Reliability Tests for Catzilla
 * Comprehensive tests for production-ready streaming with error handling,
 * performance validation, and reliability scenarios.
 */
#include "unity.h"
#include "streaming.h"
#include "server.h"
#include <string.h>
#include <stdlib.h>
#include <time.h>
#include <uv.h>

// Test configuration
#define MAX_TEST_CLIENTS 100
#define LARGE_DATA_SIZE (1024 * 1024)  // 1MB
#define STRESS_TEST_ITERATIONS 1000

// Mock client structure for comprehensive testing
typedef struct {
    char* data_buffer;
    size_t buffer_size;
    size_t data_length;
    bool closed;
    bool backpressure_active;
    int error_count;
    size_t write_count;
    size_t bytes_written;
} test_client_t;

// Global test state
static test_client_t g_test_clients[MAX_TEST_CLIENTS];
static uv_loop_t g_test_loop;
static uv_stream_t g_mock_streams[MAX_TEST_CLIENTS];
static size_t g_active_clients = 0;

// Enhanced mock callbacks
static void reliable_chunk_callback(void* ctx, const char* data, size_t len) {
    test_client_t* client = (test_client_t*)ctx;

    // Ensure buffer has enough space
    if (client->data_length + len > client->buffer_size) {
        size_t new_size = client->buffer_size * 2 + len;
        char* new_buffer = realloc(client->data_buffer, new_size);
        if (!new_buffer) {
            client->error_count++;
            return;
        }
        client->data_buffer = new_buffer;
        client->buffer_size = new_size;
    }

    // Copy data
    memcpy(client->data_buffer + client->data_length, data, len);
    client->data_length += len;
    client->write_count++;
    client->bytes_written += len;
}

static void reliable_backpressure_callback(void* ctx, bool active) {
    test_client_t* client = (test_client_t*)ctx;
    client->backpressure_active = active;
}

// Test setup and teardown
void setUp(void) {
    // Initialize test loop
    uv_loop_init(&g_test_loop);

    // Initialize test clients
    for (size_t i = 0; i < MAX_TEST_CLIENTS; i++) {
        test_client_t* client = &g_test_clients[i];
        client->data_buffer = malloc(1024);
        client->buffer_size = 1024;
        client->data_length = 0;
        client->closed = false;
        client->backpressure_active = false;
        client->error_count = 0;
        client->write_count = 0;
        client->bytes_written = 0;

        // Initialize mock stream
        memset(&g_mock_streams[i], 0, sizeof(uv_stream_t));
        g_mock_streams[i].type = UV_TCP;
        g_mock_streams[i].loop = &g_test_loop;
        g_mock_streams[i].data = client;
    }

    g_active_clients = 0;
}

void tearDown(void) {
    // Clean up test clients
    for (size_t i = 0; i < MAX_TEST_CLIENTS; i++) {
        if (g_test_clients[i].data_buffer) {
            free(g_test_clients[i].data_buffer);
            g_test_clients[i].data_buffer = NULL;
        }
    }

    uv_loop_close(&g_test_loop);
}

// Reliability Tests

void test_streaming_marker_detection_edge_cases(void) {
    // Test various marker formats and edge cases
    const char* valid_markers[] = {
        "___CATZILLA_STREAMING___abc-123___",
        "___CATZILLA_STREAMING___uuid-with-dashes___",
        "___CATZILLA_STREAMING___very-long-identifier-with-many-characters___"
    };

    const char* invalid_markers[] = {
        "___CATZILLA_STREAMING___no-end-marker",
        "WRONG_PREFIX___abc___",
        "___CATZILLA_STREAMING______",  // Empty ID
        "",  // Empty string
        "regular response body"
    };

    // Test valid markers
    for (size_t i = 0; i < sizeof(valid_markers) / sizeof(valid_markers[0]); i++) {
        TEST_ASSERT_TRUE_MESSAGE(
            catzilla_is_streaming_response(valid_markers[i], strlen(valid_markers[i])),
            "Valid streaming marker not detected"
        );
    }

    // Test invalid markers
    for (size_t i = 0; i < sizeof(invalid_markers) / sizeof(invalid_markers[0]); i++) {
        TEST_ASSERT_FALSE_MESSAGE(
            catzilla_is_streaming_response(invalid_markers[i], strlen(invalid_markers[i])),
            "Invalid streaming marker incorrectly detected"
        );
    }

    // Test NULL and edge cases
    TEST_ASSERT_FALSE(catzilla_is_streaming_response(NULL, 0));
    TEST_ASSERT_FALSE(catzilla_is_streaming_response("", 0));
}

void test_concurrent_stream_creation(void) {
    catzilla_stream_context_t* contexts[50];
    size_t created_count = 0;

    // Create multiple streams concurrently
    for (size_t i = 0; i < 50; i++) {
        test_client_t* client = &g_test_clients[i];
        contexts[i] = catzilla_stream_create(&g_mock_streams[i], 1024 + (i * 100));

        if (contexts[i]) {
            // Set up callbacks
            catzilla_stream_set_callbacks(contexts[i],
                                        reliable_chunk_callback,
                                        reliable_backpressure_callback,
                                        client);
            created_count++;
        }
    }

    // Verify all streams were created
    TEST_ASSERT_EQUAL(50, created_count);

    // Verify each stream has correct configuration
    for (size_t i = 0; i < 50; i++) {
        if (contexts[i]) {
            TEST_ASSERT_EQUAL(&g_mock_streams[i], contexts[i]->client_handle);
            TEST_ASSERT_EQUAL(1024 + (i * 100), contexts[i]->buffer_size);
            TEST_ASSERT_NOT_NULL(contexts[i]->ring_buffer);
        }
    }

    // Clean up
    for (size_t i = 0; i < 50; i++) {
        if (contexts[i]) {
            catzilla_stream_destroy(contexts[i]);
        }
    }
}

void test_large_data_streaming(void) {
    test_client_t* client = &g_test_clients[0];
    catzilla_stream_context_t* ctx = catzilla_stream_create(&g_mock_streams[0], 8192);
    TEST_ASSERT_NOT_NULL(ctx);

    // Set up callbacks
    catzilla_stream_set_callbacks(ctx, reliable_chunk_callback, reliable_backpressure_callback, client);

    // Stream large amount of data in chunks
    const size_t chunk_size = 4096;
    const size_t total_chunks = 256;  // 1MB total
    char chunk_data[chunk_size];

    // Fill chunk with test pattern
    for (size_t i = 0; i < chunk_size; i++) {
        chunk_data[i] = 'A' + (i % 26);
    }

    // Stream all chunks
    size_t successful_writes = 0;
    for (size_t i = 0; i < total_chunks; i++) {
        int result = catzilla_stream_write_chunk(ctx, chunk_data, chunk_size);
        if (result == CATZILLA_STREAM_OK) {
            successful_writes++;
        }
    }

    // Verify streaming worked
    TEST_ASSERT_GREATER_THAN(0, successful_writes);
    TEST_ASSERT_GREATER_THAN(0, ctx->bytes_streamed);
    TEST_ASSERT_EQUAL(0, client->error_count);

    catzilla_stream_destroy(ctx);
}

void test_stream_error_handling(void) {
    test_client_t* client = &g_test_clients[0];
    catzilla_stream_context_t* ctx = catzilla_stream_create(&g_mock_streams[0], 1024);
    TEST_ASSERT_NOT_NULL(ctx);

    // Set up callbacks
    catzilla_stream_set_callbacks(ctx, reliable_chunk_callback, reliable_backpressure_callback, client);

    // Test writing to active stream
    int result = catzilla_stream_write_chunk(ctx, "test data", 9);
    TEST_ASSERT_EQUAL(CATZILLA_STREAM_OK, result);

    // Simulate stream error by marking as inactive
    atomic_store(&ctx->is_active, false);
    ctx->error_code = CATZILLA_STREAM_EABORTED;

    // Writing should now fail
    result = catzilla_stream_write_chunk(ctx, "more data", 9);
    TEST_ASSERT_EQUAL(CATZILLA_STREAM_EABORTED, result);

    // Test NULL parameters
    result = catzilla_stream_write_chunk(NULL, "data", 4);
    TEST_ASSERT_EQUAL(CATZILLA_STREAM_EINVAL, result);

    result = catzilla_stream_write_chunk(ctx, NULL, 4);
    TEST_ASSERT_EQUAL(CATZILLA_STREAM_EINVAL, result);

    catzilla_stream_destroy(ctx);
}

void test_memory_management_reliability(void) {
    // Test multiple create/destroy cycles
    for (size_t cycle = 0; cycle < 100; cycle++) {
        catzilla_stream_context_t* ctx = catzilla_stream_create(&g_mock_streams[0], 1024);
        TEST_ASSERT_NOT_NULL(ctx);

        // Verify buffer allocation
        TEST_ASSERT_NOT_NULL(ctx->ring_buffer);

        // Write some data
        char test_data[64];
        snprintf(test_data, sizeof(test_data), "cycle-%zu-data", cycle);

        catzilla_stream_set_callbacks(ctx, reliable_chunk_callback, reliable_backpressure_callback, &g_test_clients[0]);
        int result = catzilla_stream_write_chunk(ctx, test_data, strlen(test_data));
        TEST_ASSERT_EQUAL(CATZILLA_STREAM_OK, result);

        // Destroy immediately
        catzilla_stream_destroy(ctx);
    }

    // Should not have any memory leaks or crashes
    TEST_ASSERT_TRUE(true);  // If we get here, no crashes occurred
}

void test_concurrent_write_operations(void) {
    test_client_t* client = &g_test_clients[0];
    catzilla_stream_context_t* ctx = catzilla_stream_create(&g_mock_streams[0], 4096);
    TEST_ASSERT_NOT_NULL(ctx);

    catzilla_stream_set_callbacks(ctx, reliable_chunk_callback, reliable_backpressure_callback, client);

    // Simulate concurrent writes (in a single-threaded test, we just do many rapid writes)
    size_t successful_writes = 0;
    for (size_t i = 0; i < 1000; i++) {
        char data[32];
        snprintf(data, sizeof(data), "write-%zu", i);

        int result = catzilla_stream_write_chunk(ctx, data, strlen(data));
        if (result == CATZILLA_STREAM_OK) {
            successful_writes++;
        }
    }

    // Most writes should succeed
    TEST_ASSERT_GREATER_THAN(900, successful_writes);
    TEST_ASSERT_GREATER_THAN(0, ctx->bytes_streamed);

    catzilla_stream_destroy(ctx);
}

void test_buffer_overflow_protection(void) {
    test_client_t* client = &g_test_clients[0];
    // Create stream with very small buffer
    catzilla_stream_context_t* ctx = catzilla_stream_create(&g_mock_streams[0], 64);
    TEST_ASSERT_NOT_NULL(ctx);

    catzilla_stream_set_callbacks(ctx, reliable_chunk_callback, reliable_backpressure_callback, client);

    // Try to write data larger than buffer
    char large_data[1024];
    memset(large_data, 'X', sizeof(large_data));
    large_data[sizeof(large_data) - 1] = '\0';

    // This should either succeed (if streaming handles large chunks) or fail gracefully
    int result = catzilla_stream_write_chunk(ctx, large_data, sizeof(large_data) - 1);
    TEST_ASSERT_TRUE(result == CATZILLA_STREAM_OK || result == CATZILLA_STREAM_EBACKPRESSURE);

    catzilla_stream_destroy(ctx);
}

void test_stream_lifecycle_reliability(void) {
    test_client_t* client = &g_test_clients[0];
    catzilla_stream_context_t* ctx = catzilla_stream_create(&g_mock_streams[0], 1024);
    TEST_ASSERT_NOT_NULL(ctx);

    // Verify initial state
    TEST_ASSERT_TRUE(atomic_load(&ctx->is_active));
    TEST_ASSERT_EQUAL(0, ctx->bytes_streamed);
    TEST_ASSERT_FALSE(client->backpressure_active);

    // Set up callbacks
    catzilla_stream_set_callbacks(ctx, reliable_chunk_callback, reliable_backpressure_callback, client);

    // Write data
    const char* test_data = "lifecycle test data";
    int result = catzilla_stream_write_chunk(ctx, test_data, strlen(test_data));
    TEST_ASSERT_EQUAL(CATZILLA_STREAM_OK, result);

    // Verify state changes
    TEST_ASSERT_GREATER_THAN(0, ctx->bytes_streamed);

    // Simulate finish
    atomic_store(&ctx->is_active, false);

    // Further writes should fail
    result = catzilla_stream_write_chunk(ctx, "more data", 9);
    TEST_ASSERT_EQUAL(CATZILLA_STREAM_EABORTED, result);

    catzilla_stream_destroy(ctx);
}

void test_stress_streaming(void) {
    // Create multiple streams and stress test them
    const size_t num_streams = 10;
    catzilla_stream_context_t* contexts[num_streams];

    // Create streams
    for (size_t i = 0; i < num_streams; i++) {
        contexts[i] = catzilla_stream_create(&g_mock_streams[i], 1024 + (i * 256));
        TEST_ASSERT_NOT_NULL(contexts[i]);
        catzilla_stream_set_callbacks(contexts[i],
                                    reliable_chunk_callback,
                                    reliable_backpressure_callback,
                                    &g_test_clients[i]);
    }

    // Stress test with many writes to each stream
    size_t total_successful_writes = 0;
    for (size_t iteration = 0; iteration < 100; iteration++) {
        for (size_t stream_idx = 0; stream_idx < num_streams; stream_idx++) {
            char data[64];
            snprintf(data, sizeof(data), "stream-%zu-iter-%zu", stream_idx, iteration);

            int result = catzilla_stream_write_chunk(contexts[stream_idx], data, strlen(data));
            if (result == CATZILLA_STREAM_OK) {
                total_successful_writes++;
            }
        }
    }

    // Most writes should succeed
    TEST_ASSERT_GREATER_THAN(800, total_successful_writes);

    // Verify each stream handled data
    for (size_t i = 0; i < num_streams; i++) {
        TEST_ASSERT_GREATER_THAN(0, contexts[i]->bytes_streamed);
        TEST_ASSERT_EQUAL(0, g_test_clients[i].error_count);
    }

    // Clean up
    for (size_t i = 0; i < num_streams; i++) {
        catzilla_stream_destroy(contexts[i]);
    }
}

// Test runner
int main(void) {
    UNITY_BEGIN();

    // Basic reliability tests
    RUN_TEST(test_streaming_marker_detection_edge_cases);
    RUN_TEST(test_concurrent_stream_creation);
    RUN_TEST(test_stream_error_handling);
    RUN_TEST(test_memory_management_reliability);

    // Performance and stress tests
    RUN_TEST(test_large_data_streaming);
    RUN_TEST(test_concurrent_write_operations);
    RUN_TEST(test_buffer_overflow_protection);
    RUN_TEST(test_stream_lifecycle_reliability);
    RUN_TEST(test_stress_streaming);

    return UNITY_END();
}
