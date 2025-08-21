/**
 * 🌪️ Catzilla Zero-Allocation Middleware System - C Tests
 * Comprehensive test suite for middleware functionality, memory management, and performance
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <assert.h>
#include <time.h>
#include <stdbool.h>

// Test framework (Unity)
#include "../../deps/unity/src/unity.h"

// Catzilla core headers
#include "../../src/core/middleware.h"
#include "../../src/core/memory.h"

// Test constants
#define CATZILLA_SUCCESS 0
#define CATZILLA_ERROR_INVALID_PARAM -1
#define CATZILLA_ERROR_OUT_OF_MEMORY -2
#define CATZILLA_ERROR_DUPLICATE -3

// Test macros
#define TEST_ASSERT(condition, message) \
    do { \
        if (!(condition)) { \
            printf("TEST FAILED: %s\n", message); \
            printf("  File: %s, Line: %d\n", __FILE__, __LINE__); \
            return -1; \
        } \
    } while(0)

#define TEST_LOG(message) printf("✓ %s\n", message)

// ============================================================================
// TEST MIDDLEWARE FUNCTIONS
// ============================================================================

/**
 * Simple logging middleware for testing
 */
int test_logging_middleware(catzilla_middleware_context_t* ctx) {
    if (!ctx) return CATZILLA_ERROR_INVALID_PARAM;

    // Set a test header to verify middleware execution
    catzilla_middleware_set_header(ctx, "X-Test-Middleware", "logging");

    TEST_LOG("Logging middleware executed");
    return CATZILLA_SUCCESS;
}

/**
 * Authentication middleware for testing
 */
int test_auth_middleware(catzilla_middleware_context_t* ctx) {
    if (!ctx) return CATZILLA_ERROR_INVALID_PARAM;

    // Simulate authentication check
    const char* auth_header = catzilla_middleware_get_header(ctx, "Authorization");
    if (!auth_header || strncmp(auth_header, "Bearer ", 7) != 0) {
        catzilla_middleware_set_error(ctx, "Authentication required", 401);
        return CATZILLA_ERROR_INVALID_PARAM;
    }

    catzilla_middleware_set_header(ctx, "X-Auth-Status", "authenticated");
    TEST_LOG("Auth middleware executed");
    return CATZILLA_SUCCESS;
}

/**
 * CORS middleware for testing
 */
int test_cors_middleware(catzilla_middleware_context_t* ctx) {
    if (!ctx) return CATZILLA_ERROR_INVALID_PARAM;

    catzilla_middleware_set_header(ctx, "Access-Control-Allow-Origin", "*");
    catzilla_middleware_set_header(ctx, "Access-Control-Allow-Methods", "GET,POST,PUT,DELETE");

    TEST_LOG("CORS middleware executed");
    return CATZILLA_SUCCESS;
}

/**
 * Rate limiting middleware for testing
 */
int test_rate_limit_middleware(catzilla_middleware_context_t* ctx) {
    if (!ctx) return CATZILLA_ERROR_INVALID_PARAM;

    // Simulate rate limiting
    catzilla_middleware_set_header(ctx, "X-Rate-Limit-Remaining", "99");

    TEST_LOG("Rate limit middleware executed");
    return CATZILLA_SUCCESS;
}

// ============================================================================
// BASIC FUNCTIONALITY TESTS
// ============================================================================

/**
 * Test middleware chain creation and destruction
 */
int test_middleware_chain_creation() {
    printf("\n=== Testing Middleware Chain Creation ===\n");

    catzilla_middleware_chain_t* chain = catzilla_middleware_create_chain();
    TEST_ASSERT(chain != NULL, "Middleware chain creation");

    catzilla_middleware_destroy_chain(chain);
    TEST_LOG("Middleware chain creation and destruction");

    return CATZILLA_SUCCESS;
}

/**
 * Test middleware registration
 */
int test_middleware_registration() {
    printf("\n=== Testing Middleware Registration ===\n");

    catzilla_middleware_chain_t* chain = catzilla_middleware_create_chain();
    TEST_ASSERT(chain != NULL, "Chain creation for registration test");

    // Register first middleware
    int result = catzilla_middleware_register(chain, "logging", test_logging_middleware, 1000);
    TEST_ASSERT(result == CATZILLA_SUCCESS, "First middleware registration");

    // Register second middleware
    result = catzilla_middleware_register(chain, "cors", test_cors_middleware, 2000);
    TEST_ASSERT(result == CATZILLA_SUCCESS, "Second middleware registration");

    // Register third middleware
    result = catzilla_middleware_register(chain, "auth", test_auth_middleware, 3000);
    TEST_ASSERT(result == CATZILLA_SUCCESS, "Third middleware registration");

    // Test duplicate registration (should fail)
    result = catzilla_middleware_register(chain, "logging", test_logging_middleware, 1000);
    TEST_ASSERT(result == CATZILLA_ERROR_DUPLICATE, "Duplicate middleware registration fails");

    catzilla_middleware_destroy_chain(chain);
    TEST_LOG("Middleware registration");

    return CATZILLA_SUCCESS;
}

// ============================================================================
// EXECUTION TESTS
// ============================================================================

/**
 * Test middleware execution
 */
int test_middleware_execution() {
    printf("\n=== Testing Middleware Execution ===\n");

    catzilla_middleware_chain_t* chain = catzilla_middleware_create_chain();
    TEST_ASSERT(chain != NULL, "Chain creation for execution test");

    // Register middleware
    catzilla_middleware_register(chain, "logging", test_logging_middleware, 1000);
    catzilla_middleware_register(chain, "cors", test_cors_middleware, 2000);
    catzilla_middleware_register(chain, "rate_limit", test_rate_limit_middleware, 3000);

    // Create context
    catzilla_middleware_context_t ctx = {0};
    ctx.should_continue = true;
    ctx.response_status = 200;

    // Execute middleware chain
    int result = catzilla_middleware_execute_chain(chain, &ctx);
    TEST_ASSERT(result == CATZILLA_SUCCESS, "Middleware chain execution");

    // Verify headers were set
    bool found_logging = false;
    bool found_cors = false;
    bool found_rate_limit = false;

    for (int i = 0; i < ctx.response_header_count; i++) {
        if (strcmp(ctx.response_headers[i].name, "X-Test-Middleware") == 0) {
            found_logging = true;
        }
        if (strcmp(ctx.response_headers[i].name, "Access-Control-Allow-Origin") == 0) {
            found_cors = true;
        }
        if (strcmp(ctx.response_headers[i].name, "X-Rate-Limit-Remaining") == 0) {
            found_rate_limit = true;
        }
    }

    TEST_ASSERT(found_logging, "Logging middleware header set");
    TEST_ASSERT(found_cors, "CORS middleware header set");
    TEST_ASSERT(found_rate_limit, "Rate limit middleware header set");

    catzilla_middleware_destroy_chain(chain);
    TEST_LOG("Middleware execution");

    return CATZILLA_SUCCESS;
}

// ============================================================================
// RESPONSE HANDLING TESTS
// ============================================================================

/**
 * Test response building
 */
int test_response_building() {
    printf("\n=== Testing Response Building ===\n");

    catzilla_middleware_context_t ctx = {0};

    // Test setting response data
    const char* test_content = "{\"message\":\"Hello, World!\"}";
    catzilla_middleware_set_data(&ctx, test_content, strlen(test_content));
    TEST_ASSERT(ctx.response_body != NULL, "Response body set");
    TEST_ASSERT(ctx.response_body_length == strlen(test_content), "Response body length correct");

    // Test setting status
    catzilla_middleware_set_status(&ctx, 201);
    TEST_ASSERT(ctx.response_status == 201, "Response status set");

    // Test setting headers
    int header_result = catzilla_middleware_set_header(&ctx, "Content-Type", "application/json");
    TEST_ASSERT(header_result == CATZILLA_SUCCESS, "Response header set");
    TEST_ASSERT(ctx.response_header_count == 1, "Response header count");

    TEST_LOG("Response building");

    return CATZILLA_SUCCESS;
}

/**
 * Test error handling
 */
int test_error_handling() {
    printf("\n=== Testing Error Handling ===\n");

    catzilla_middleware_context_t ctx = {0};

    // Test setting error
    catzilla_middleware_set_error(&ctx, "Test error message", 500);
    TEST_ASSERT(ctx.error_code == 500, "Error code set");
    TEST_ASSERT(ctx.error_message != NULL, "Error message set");
    TEST_ASSERT(strcmp(ctx.error_message, "Test error message") == 0, "Error message content");

    TEST_LOG("Error handling");

    return CATZILLA_SUCCESS;
}

// ============================================================================
// MEMORY MANAGEMENT TESTS
// ============================================================================

/**
 * Test memory management
 */
int test_memory_management() {
    printf("\n=== Testing Memory Management ===\n");

    // Test multiple chain creation/destruction
    for (int i = 0; i < 10; i++) {
        catzilla_middleware_chain_t* chain = catzilla_middleware_create_chain();
        TEST_ASSERT(chain != NULL, "Memory management - chain creation");

        // Register middleware
        catzilla_middleware_register(chain, "test", test_logging_middleware, 1000);

        catzilla_middleware_destroy_chain(chain);
    }

    TEST_LOG("Memory management");

    return CATZILLA_SUCCESS;
}

// ============================================================================
// PERFORMANCE TESTS
// ============================================================================

/**
 * Test middleware performance
 */
int test_middleware_performance() {
    printf("\n=== Testing Middleware Performance ===\n");

    catzilla_middleware_chain_t* chain = catzilla_middleware_create_chain();
    TEST_ASSERT(chain != NULL, "Performance test - chain creation");

    // Register multiple middleware
    catzilla_middleware_register(chain, "logging", test_logging_middleware, 1000);
    catzilla_middleware_register(chain, "cors", test_cors_middleware, 2000);
    catzilla_middleware_register(chain, "auth", test_auth_middleware, 3000);
    catzilla_middleware_register(chain, "rate_limit", test_rate_limit_middleware, 4000);

    const int iterations = 1000;
    clock_t start = clock();

    // Execute middleware chain multiple times
    for (int i = 0; i < iterations; i++) {
        catzilla_middleware_context_t ctx = {0};
        ctx.should_continue = true;
        ctx.response_status = 200;

        // Set authorization header for auth middleware
        catzilla_middleware_set_header(&ctx, "Authorization", "Bearer valid_token");

        int result = catzilla_middleware_execute_chain(chain, &ctx);
        TEST_ASSERT(result == CATZILLA_SUCCESS, "Performance test execution");
    }

    clock_t end = clock();
    double cpu_time_used = ((double) (end - start)) / CLOCKS_PER_SEC;

    printf("  Executed %d middleware chains in %f seconds\n", iterations, cpu_time_used);
    printf("  Average execution time: %f microseconds per chain\n",
           (cpu_time_used * 1000000) / iterations);

    catzilla_middleware_destroy_chain(chain);
    TEST_LOG("Middleware performance");

    return CATZILLA_SUCCESS;
}

// ============================================================================
// INTEGRATION TESTS
// ============================================================================

/**
 * Test integration with dependency injection
 */
int test_di_integration() {
    printf("\n=== Testing DI Integration ===\n");

    catzilla_middleware_chain_t* chain = catzilla_middleware_create_chain();
    TEST_ASSERT(chain != NULL, "DI integration - chain creation");

    catzilla_middleware_context_t ctx = {0};
    ctx.should_continue = true;

    // Test that middleware works without DI container
    int result = catzilla_middleware_execute_chain(chain, &ctx);
    TEST_ASSERT(result == CATZILLA_SUCCESS, "Middleware execution without DI");

    catzilla_middleware_destroy_chain(chain);
    TEST_LOG("DI integration");

    return CATZILLA_SUCCESS;
}

// ============================================================================
// MAIN TEST RUNNER
// ============================================================================

/**
 * Run all middleware tests
 */
int main(void) {
    printf("🌪️ Catzilla Zero-Allocation Middleware System - C Test Suite\n");
    printf("============================================================\n");

    int failed_tests = 0;

    // Basic functionality tests
    if (test_middleware_chain_creation() != CATZILLA_SUCCESS) failed_tests++;
    if (test_middleware_registration() != CATZILLA_SUCCESS) failed_tests++;

    // Execution tests
    if (test_middleware_execution() != CATZILLA_SUCCESS) failed_tests++;

    // Response handling tests
    if (test_response_building() != CATZILLA_SUCCESS) failed_tests++;
    if (test_error_handling() != CATZILLA_SUCCESS) failed_tests++;

    // Memory management tests
    if (test_memory_management() != CATZILLA_SUCCESS) failed_tests++;

    // Performance tests
    if (test_middleware_performance() != CATZILLA_SUCCESS) failed_tests++;

    // Integration tests
    if (test_di_integration() != CATZILLA_SUCCESS) failed_tests++;

    printf("\n============================================================\n");
    if (failed_tests == 0) {
        printf("🎉 All middleware tests passed!\n");
        return 0;
    } else {
        printf("❌ %d test(s) failed!\n", failed_tests);
        return 1;
    }
}
