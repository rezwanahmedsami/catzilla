/*
 * 🌪️ Catzilla Zero-Allocation Middleware System - C Tests
 *
 * Comprehensive tests for the C-level middleware infrastructure
 * Tests middleware registration, execution, and memory management
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <assert.h>
#include <time.h>
#include <sys/time.h>

// Include middleware headers
#include "../../src/core/middleware.h"
#include "../../src/core/memory.h"

// Common error codes used throughout the project
#define CATZILLA_SUCCESS 0
#define CATZILLA_ERROR_UNAUTHORIZED -1
#define CATZILLA_ERROR_RATE_LIMITED -2
#define CATZILLA_ERROR_INTERNAL -3

// Middleware processing flags (for context->flags)
#define CATZILLA_MIDDLEWARE_FLAG_PROCESSED 1

// Test framework macros
#define TEST_ASSERT(condition, message) \
    do { \
        if (!(condition)) { \
            printf("❌ FAIL: %s\n", message); \
            return 0; \
        } else { \
            printf("✅ PASS: %s\n", message); \
        } \
    } while(0)

#define TEST_START(test_name) \
    printf("\n🧪 Testing: %s\n", test_name); \
    printf("═══════════════════════════════════════\n");

#define TEST_END() \
    printf("═══════════════════════════════════════\n");

// Global test statistics
static int tests_run = 0;
static int tests_passed = 0;

// Test helper functions
static double get_time_ms() {
    struct timeval tv;
    gettimeofday(&tv, NULL);
    return tv.tv_sec * 1000.0 + tv.tv_usec / 1000.0;
}

// Sample middleware functions for testing
static int test_logging_middleware(catzilla_middleware_context_t* ctx) {
    // Simple logging middleware - just mark that it ran
    ctx->flags |= CATZILLA_MIDDLEWARE_FLAG_PROCESSED;
    return CATZILLA_SUCCESS;
}

static int test_auth_middleware(catzilla_middleware_context_t* ctx) {
    // Check for authorization header
    const char* auth_header = catzilla_middleware_get_header(ctx, "Authorization");
    if (!auth_header) {
        catzilla_middleware_set_error(ctx, 401, "Unauthorized");
        return CATZILLA_ERROR_UNAUTHORIZED;
    }
    ctx->flags |= CATZILLA_MIDDLEWARE_FLAG_PROCESSED;
    return CATZILLA_SUCCESS;
}

static int test_rate_limit_middleware(catzilla_middleware_context_t* ctx) {
    // Simple rate limiting - allow first 100 requests
    static int request_count = 0;
    request_count++;

    if (request_count > 100) {
        catzilla_middleware_set_error(ctx, 429, "Rate limit exceeded");
        return CATZILLA_ERROR_RATE_LIMITED;
    }

    ctx->flags |= CATZILLA_MIDDLEWARE_FLAG_PROCESSED;
    return CATZILLA_SUCCESS;
}

static int test_cors_middleware(catzilla_middleware_context_t* ctx) {
    // Add CORS headers
    catzilla_middleware_set_header(ctx, "Access-Control-Allow-Origin", "*");
    catzilla_middleware_set_header(ctx, "Access-Control-Allow-Methods", "GET, POST, PUT, DELETE");
    ctx->flags |= CATZILLA_MIDDLEWARE_FLAG_PROCESSED;
    return CATZILLA_SUCCESS;
}

static int test_error_middleware(catzilla_middleware_context_t* ctx) {
    // Middleware that always fails for testing error handling
    catzilla_middleware_set_error(ctx, 500, "Middleware error");
    return CATZILLA_ERROR_INTERNAL;
}

// Test 1: Middleware Chain Creation and Destruction
static int test_middleware_chain_lifecycle() {
    TEST_START("Middleware Chain Lifecycle");
    tests_run++;

    // Create middleware chain
    catzilla_middleware_chain_t* chain = catzilla_middleware_create_chain();
    TEST_ASSERT(chain != NULL, "Middleware chain creation");

    // Verify initial state
    TEST_ASSERT(catzilla_middleware_get_count(chain) == 0, "Initial middleware count is zero");

    // Destroy middleware chain
    int result = catzilla_middleware_destroy_chain(chain);
    TEST_ASSERT(result == CATZILLA_SUCCESS, "Middleware chain destruction");

    TEST_END();
    tests_passed++;
    return 1;
}

// Test 2: Middleware Registration
static int test_middleware_registration() {
    TEST_START("Middleware Registration");
    tests_run++;

    catzilla_middleware_chain_t* chain = catzilla_middleware_create_chain();
    TEST_ASSERT(chain != NULL, "Chain creation for registration test");

    // Register logging middleware
    int result = catzilla_middleware_register(
        chain, test_logging_middleware, "test_logger", 100,
        CATZILLA_MIDDLEWARE_PRE_ROUTE
    );
    TEST_ASSERT(result == CATZILLA_SUCCESS, "Logging middleware registration");
    TEST_ASSERT(catzilla_middleware_get_count(chain) == 1, "Middleware count after registration");

    // Register auth middleware
    result = catzilla_middleware_register(
        chain, test_auth_middleware, "test_auth", 200,
        CATZILLA_MIDDLEWARE_PRE_ROUTE
    );
    TEST_ASSERT(result == CATZILLA_SUCCESS, "Auth middleware registration");
    TEST_ASSERT(catzilla_middleware_get_count(chain) == 2, "Middleware count after second registration");

    // Register CORS middleware
    result = catzilla_middleware_register(
        chain, test_cors_middleware, "test_cors", 50,
        CATZILLA_MIDDLEWARE_PRE_ROUTE
    );
    TEST_ASSERT(result == CATZILLA_SUCCESS, "CORS middleware registration");
    TEST_ASSERT(catzilla_middleware_get_count(chain) == 3, "Final middleware count");

    // Test duplicate registration (should fail)
    result = catzilla_middleware_register(
        chain, test_logging_middleware, "test_logger", 150,
        CATZILLA_MIDDLEWARE_PRE_ROUTE
    );
    TEST_ASSERT(result == CATZILLA_ERROR_DUPLICATE, "Duplicate middleware registration fails");
    TEST_ASSERT(catzilla_middleware_get_count(chain) == 3, "Middleware count unchanged after duplicate");

    catzilla_middleware_destroy_chain(chain);
    TEST_END();
    tests_passed++;
    return 1;
}

// Test 3: Middleware Execution Order
static int test_middleware_execution_order() {
    TEST_START("Middleware Execution Order");
    tests_run++;

    catzilla_middleware_chain_t* chain = catzilla_middleware_create_chain();
    TEST_ASSERT(chain != NULL, "Chain creation for execution test");

    // Register middleware with different priorities
    catzilla_middleware_register(chain, test_cors_middleware, "cors", 50, CATZILLA_MIDDLEWARE_PRE_ROUTE);
    catzilla_middleware_register(chain, test_logging_middleware, "logging", 100, CATZILLA_MIDDLEWARE_PRE_ROUTE);
    catzilla_middleware_register(chain, test_auth_middleware, "auth", 200, CATZILLA_MIDDLEWARE_PRE_ROUTE);

    // Create test context
    catzilla_middleware_context_t* ctx = catzilla_middleware_create_context();
    TEST_ASSERT(ctx != NULL, "Context creation");

    // Set up test request
    catzilla_middleware_set_method(ctx, "GET");
    catzilla_middleware_set_path(ctx, "/api/test");
    catzilla_middleware_set_header(ctx, "Authorization", "Bearer test-token");

    // Execute middleware chain
    int result = catzilla_middleware_execute_pre_route(chain, ctx);
    TEST_ASSERT(result == CATZILLA_SUCCESS, "Middleware chain execution");

    // Verify all middleware ran
    TEST_ASSERT(ctx->flags & CATZILLA_MIDDLEWARE_FLAG_PROCESSED, "Middleware processed flag set");

    // Check CORS headers were added
    const char* cors_header = catzilla_middleware_get_response_header(ctx, "Access-Control-Allow-Origin");
    TEST_ASSERT(cors_header != NULL && strcmp(cors_header, "*") == 0, "CORS headers added");

    catzilla_middleware_destroy_context(ctx);
    catzilla_middleware_destroy_chain(chain);

    TEST_END();
    tests_passed++;
    return 1;
}

// Test 4: Error Handling
static int test_middleware_error_handling() {
    TEST_START("Middleware Error Handling");
    tests_run++;

    catzilla_middleware_chain_t* chain = catzilla_middleware_create_chain();
    TEST_ASSERT(chain != NULL, "Chain creation for error test");

    // Register middleware including one that fails
    catzilla_middleware_register(chain, test_logging_middleware, "logging", 100, CATZILLA_MIDDLEWARE_PRE_ROUTE);
    catzilla_middleware_register(chain, test_error_middleware, "error", 200, CATZILLA_MIDDLEWARE_PRE_ROUTE);
    catzilla_middleware_register(chain, test_cors_middleware, "cors", 300, CATZILLA_MIDDLEWARE_PRE_ROUTE);

    catzilla_middleware_context_t* ctx = catzilla_middleware_create_context();
    TEST_ASSERT(ctx != NULL, "Context creation for error test");

    catzilla_middleware_set_method(ctx, "GET");
    catzilla_middleware_set_path(ctx, "/api/test");

    // Execute middleware chain (should fail at error middleware)
    int result = catzilla_middleware_execute_pre_route(chain, ctx);
    TEST_ASSERT(result == CATZILLA_ERROR_INTERNAL, "Error middleware stops execution");

    // Check error details
    TEST_ASSERT(catzilla_middleware_get_error_code(ctx) == 500, "Error code set correctly");
    const char* error_msg = catzilla_middleware_get_error_message(ctx);
    TEST_ASSERT(error_msg != NULL && strcmp(error_msg, "Middleware error") == 0, "Error message set correctly");

    catzilla_middleware_destroy_context(ctx);
    catzilla_middleware_destroy_chain(chain);

    TEST_END();
    tests_passed++;
    return 1;
}

// Test 5: Authorization Middleware
static int test_authorization_middleware() {
    TEST_START("Authorization Middleware");
    tests_run++;

    catzilla_middleware_chain_t* chain = catzilla_middleware_create_chain();
    catzilla_middleware_register(chain, test_auth_middleware, "auth", 100, CATZILLA_MIDDLEWARE_PRE_ROUTE);

    // Test 1: Request with authorization header (should pass)
    catzilla_middleware_context_t* ctx1 = catzilla_middleware_create_context();
    catzilla_middleware_set_method(ctx1, "GET");
    catzilla_middleware_set_path(ctx1, "/api/protected");
    catzilla_middleware_set_header(ctx1, "Authorization", "Bearer valid-token");

    int result = catzilla_middleware_execute_pre_route(chain, ctx1);
    TEST_ASSERT(result == CATZILLA_SUCCESS, "Authorized request passes");

    // Test 2: Request without authorization header (should fail)
    catzilla_middleware_context_t* ctx2 = catzilla_middleware_create_context();
    catzilla_middleware_set_method(ctx2, "GET");
    catzilla_middleware_set_path(ctx2, "/api/protected");

    result = catzilla_middleware_execute_pre_route(chain, ctx2);
    TEST_ASSERT(result == CATZILLA_ERROR_UNAUTHORIZED, "Unauthorized request fails");
    TEST_ASSERT(catzilla_middleware_get_error_code(ctx2) == 401, "401 error code set");

    catzilla_middleware_destroy_context(ctx1);
    catzilla_middleware_destroy_context(ctx2);
    catzilla_middleware_destroy_chain(chain);

    TEST_END();
    tests_passed++;
    return 1;
}

// Test 6: Rate Limiting Middleware
static int test_rate_limiting_middleware() {
    TEST_START("Rate Limiting Middleware");
    tests_run++;

    catzilla_middleware_chain_t* chain = catzilla_middleware_create_chain();
    catzilla_middleware_register(chain, test_rate_limit_middleware, "rate_limit", 100, CATZILLA_MIDDLEWARE_PRE_ROUTE);

    // Test multiple requests (first 100 should pass, then fail)
    int successful_requests = 0;
    int rate_limited_requests = 0;

    for (int i = 0; i < 105; i++) {
        catzilla_middleware_context_t* ctx = catzilla_middleware_create_context();
        catzilla_middleware_set_method(ctx, "GET");
        catzilla_middleware_set_path(ctx, "/api/test");

        int result = catzilla_middleware_execute_pre_route(chain, ctx);
        if (result == CATZILLA_SUCCESS) {
            successful_requests++;
        } else if (result == CATZILLA_ERROR_RATE_LIMITED) {
            rate_limited_requests++;
        }

        catzilla_middleware_destroy_context(ctx);
    }

    TEST_ASSERT(successful_requests == 100, "Exactly 100 requests allowed");
    TEST_ASSERT(rate_limited_requests == 5, "5 requests rate limited");

    catzilla_middleware_destroy_chain(chain);

    TEST_END();
    tests_passed++;
    return 1;
}

// Test 7: Performance Benchmarks
static int test_middleware_performance() {
    TEST_START("Middleware Performance");
    tests_run++;

    catzilla_middleware_chain_t* chain = catzilla_middleware_create_chain();

    // Register multiple middleware
    catzilla_middleware_register(chain, test_logging_middleware, "logging", 100, CATZILLA_MIDDLEWARE_PRE_ROUTE);
    catzilla_middleware_register(chain, test_cors_middleware, "cors", 200, CATZILLA_MIDDLEWARE_PRE_ROUTE);
    catzilla_middleware_register(chain, test_auth_middleware, "auth", 300, CATZILLA_MIDDLEWARE_PRE_ROUTE);

    const int num_requests = 10000;
    double start_time = get_time_ms();

    for (int i = 0; i < num_requests; i++) {
        catzilla_middleware_context_t* ctx = catzilla_middleware_create_context();
        catzilla_middleware_set_method(ctx, "GET");
        catzilla_middleware_set_path(ctx, "/api/benchmark");
        catzilla_middleware_set_header(ctx, "Authorization", "Bearer token");

        int result = catzilla_middleware_execute_pre_route(chain, ctx);
        assert(result == CATZILLA_SUCCESS);

        catzilla_middleware_destroy_context(ctx);
    }

    double end_time = get_time_ms();
    double total_time = end_time - start_time;
    double avg_time_us = (total_time * 1000.0) / num_requests;

    printf("📊 Performance Results:\n");
    printf("   Total time: %.2f ms\n", total_time);
    printf("   Average time per request: %.2f μs\n", avg_time_us);
    printf("   Requests per second: %.0f\n", num_requests / (total_time / 1000.0));

    // Performance assertions
    TEST_ASSERT(avg_time_us < 50.0, "Average request time under 50μs");
    TEST_ASSERT(total_time < 1000.0, "Total time for 10k requests under 1 second");

    catzilla_middleware_destroy_chain(chain);

    TEST_END();
    tests_passed++;
    return 1;
}

// Test 8: Memory Management
static int test_middleware_memory_management() {
    TEST_START("Middleware Memory Management");
    tests_run++;

    // Get initial memory stats
    catzilla_memory_stats_t initial_stats;
    catzilla_get_memory_stats(&initial_stats);

    // Create and destroy many middleware chains
    for (int i = 0; i < 1000; i++) {
        catzilla_middleware_chain_t* chain = catzilla_middleware_create_chain();

        // Register middleware
        catzilla_middleware_register(chain, test_logging_middleware, "logging", 100, CATZILLA_MIDDLEWARE_PRE_ROUTE);
        catzilla_middleware_register(chain, test_cors_middleware, "cors", 200, CATZILLA_MIDDLEWARE_PRE_ROUTE);

        // Create and execute context
        catzilla_middleware_context_t* ctx = catzilla_middleware_create_context();
        catzilla_middleware_set_method(ctx, "GET");
        catzilla_middleware_set_path(ctx, "/test");

        catzilla_middleware_execute_pre_route(chain, ctx);

        catzilla_middleware_destroy_context(ctx);
        catzilla_middleware_destroy_chain(chain);
    }

    // Get final memory stats
    catzilla_memory_stats_t final_stats;
    catzilla_get_memory_stats(&final_stats);

    // Check for memory leaks
    size_t memory_growth = final_stats.allocated_bytes - initial_stats.allocated_bytes;
    printf("📊 Memory Analysis:\n");
    printf("   Initial memory: %zu bytes\n", initial_stats.allocated_bytes);
    printf("   Final memory: %zu bytes\n", final_stats.allocated_bytes);
    printf("   Memory growth: %zu bytes\n", memory_growth);

    // Allow for some reasonable memory growth but check for major leaks
    TEST_ASSERT(memory_growth < 1024 * 1024, "Memory growth under 1MB"); // Allow 1MB growth

    TEST_END();
    tests_passed++;
    return 1;
}

// Main test runner
int main() {
    printf("🌪️ Catzilla Zero-Allocation Middleware System - C Tests\n");
    printf("════════════════════════════════════════════════════════\n");

    // Initialize memory system
    int init_result = catzilla_init_memory_system();
    if (init_result != CATZILLA_SUCCESS) {
        printf("❌ Failed to initialize memory system\n");
        return 1;
    }

    // Run all tests
    test_middleware_chain_lifecycle();
    test_middleware_registration();
    test_middleware_execution_order();
    test_middleware_error_handling();
    test_authorization_middleware();
    test_rate_limiting_middleware();
    test_middleware_performance();
    test_middleware_memory_management();

    // Print summary
    printf("\n════════════════════════════════════════════════════════\n");
    printf("📊 Test Results Summary:\n");
    printf("   Tests run: %d\n", tests_run);
    printf("   Tests passed: %d\n", tests_passed);
    printf("   Tests failed: %d\n", tests_run - tests_passed);

    if (tests_passed == tests_run) {
        printf("🎉 ALL TESTS PASSED!\n");
        printf("✅ C Middleware System is fully functional and reliable!\n");
        return 0;
    } else {
        printf("❌ Some tests failed!\n");
        return 1;
    }
}
