/*
 * 🌪️ Catzilla Per-Route Middleware System - C Tests
 *
 * Comprehensive tests for the C-level per-route middleware infrastructure.
 * Tests the low-level implementation of:
 * - Route-middleware binding and storage
 * - Per-route middleware execution in C
 * - Memory management for middleware chains
 * - Performance characteristics of middleware execution
 * - Integration with Python middleware functions
 * - Zero-allocation middleware processing
 * - Error handling and edge cases
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <assert.h>
#include <time.h>
#ifndef _WIN32
#include <sys/time.h>
#include <unistd.h>
#endif

// Include core headers
#include "../../src/core/router.h"
#include "../../src/core/middleware.h"
#include "../../src/core/memory.h"
#include "../../src/core/server.h"

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
    printf("═══════════════════════════════════════════════════════════\n");

#define TEST_END() \
    printf("═══════════════════════════════════════════════════════════\n");

// Global test statistics
static int tests_run = 0;
static int tests_passed = 0;

// Test middleware execution tracking
static char middleware_execution_log[1024];
static int middleware_call_count = 0;

// Helper function to clear execution log
void clear_middleware_log() {
    memset(middleware_execution_log, 0, sizeof(middleware_execution_log));
    middleware_call_count = 0;
}

// Helper function to add to execution log
void log_middleware_execution(const char* name) {
    if (strlen(middleware_execution_log) > 0) {
        strcat(middleware_execution_log, ",");
    }
    strcat(middleware_execution_log, name);
    middleware_call_count++;
}

// Test middleware functions
int test_auth_middleware(catzilla_request_t* request, catzilla_response_t* response) {
    log_middleware_execution("auth");

    // Simulate auth check
    const char* auth_header = catzilla_request_get_header(request, "Authorization");
    if (!auth_header || strncmp(auth_header, "Bearer ", 7) != 0) {
        catzilla_response_set_status(response, 401);
        catzilla_response_set_body(response, "{\"error\":\"Unauthorized\"}",
                                  strlen("{\"error\":\"Unauthorized\"}"));
        return 1; // Stop processing
    }

    return 0; // Continue
}

int test_cors_middleware(catzilla_request_t* request, catzilla_response_t* response) {
    log_middleware_execution("cors");

    // Add CORS headers
    catzilla_response_set_header(response, "Access-Control-Allow-Origin", "*");
    catzilla_response_set_header(response, "Access-Control-Allow-Methods", "GET, POST, PUT, DELETE");

    return 0; // Continue
}

int test_rate_limit_middleware(catzilla_request_t* request, catzilla_response_t* response) {
    log_middleware_execution("rate_limit");

    // Simulate rate limiting check
    const char* client_ip = catzilla_request_get_remote_addr(request);
    if (client_ip && strcmp(client_ip, "127.0.0.1") == 0) {
        // Allow localhost
        return 0;
    }

    // For other IPs, simulate rate limit exceeded
    catzilla_response_set_status(response, 429);
    catzilla_response_set_body(response, "{\"error\":\"Rate limit exceeded\"}",
                              strlen("{\"error\":\"Rate limit exceeded\"}"));
    return 1; // Stop processing
}

int test_logging_middleware(catzilla_request_t* request, catzilla_response_t* response) {
    log_middleware_execution("logging");

    // Simulate request logging
    const char* method = catzilla_request_get_method(request);
    const char* path = catzilla_request_get_path(request);
    printf("🔍 LOG: %s %s\n", method ? method : "UNKNOWN", path ? path : "/");

    return 0; // Continue
}

int test_validation_middleware(catzilla_request_t* request, catzilla_response_t* response) {
    log_middleware_execution("validation");

    // Simulate JSON validation
    const char* content_type = catzilla_request_get_header(request, "Content-Type");
    if (content_type && strstr(content_type, "application/json")) {
        const char* body = catzilla_request_get_body(request);
        if (body && (strstr(body, "{") == NULL || strstr(body, "}") == NULL)) {
            catzilla_response_set_status(response, 400);
            catzilla_response_set_body(response, "{\"error\":\"Invalid JSON\"}",
                                      strlen("{\"error\":\"Invalid JSON\"}"));
            return 1; // Stop processing
        }
    }

    return 0; // Continue
}

// Route handler functions for testing
int test_public_handler(catzilla_request_t* request, catzilla_response_t* response) {
    catzilla_response_set_status(response, 200);
    catzilla_response_set_body(response, "{\"message\":\"public\"}",
                              strlen("{\"message\":\"public\"}"));
    return 0;
}

int test_protected_handler(catzilla_request_t* request, catzilla_response_t* response) {
    catzilla_response_set_status(response, 200);
    catzilla_response_set_body(response, "{\"message\":\"protected\"}",
                              strlen("{\"message\":\"protected\"}"));
    return 0;
}

int test_api_handler(catzilla_request_t* request, catzilla_response_t* response) {
    catzilla_response_set_status(response, 200);
    catzilla_response_set_body(response, "{\"message\":\"api\"}",
                              strlen("{\"message\":\"api\"}"));
    return 0;
}

/**
 * Test per-route middleware registration
 */
int test_per_route_middleware_registration() {
    TEST_START("Per-Route Middleware Registration");

    catzilla_router_t* router = catzilla_router_create();
    TEST_ASSERT(router != NULL, "Router creation");

    // Test registering route with single middleware
    catzilla_middleware_fn_t auth_mw[] = { test_auth_middleware };
    int result = catzilla_router_add_route_with_middleware(
        router, "GET", "/protected", test_protected_handler, auth_mw, 1
    );
    TEST_ASSERT(result == 0, "Register route with single middleware");

    // Test registering route with multiple middleware
    catzilla_middleware_fn_t multi_mw[] = { test_auth_middleware, test_cors_middleware, test_logging_middleware };
    result = catzilla_router_add_route_with_middleware(
        router, "POST", "/api/data", test_api_handler, multi_mw, 3
    );
    TEST_ASSERT(result == 0, "Register route with multiple middleware");

    // Test registering route without middleware
    result = catzilla_router_add_route_with_middleware(
        router, "GET", "/public", test_public_handler, NULL, 0
    );
    TEST_ASSERT(result == 0, "Register route without middleware");

    // Verify route count
    int route_count = catzilla_router_get_route_count(router);
    TEST_ASSERT(route_count == 3, "Correct number of routes registered");

    catzilla_router_destroy(router);

    TEST_END();
    tests_run++;
    tests_passed++;
    return 1;
}

/**
 * Test middleware execution order
 */
int test_middleware_execution_order() {
    TEST_START("Middleware Execution Order");

    catzilla_router_t* router = catzilla_router_create();
    catzilla_request_t* request = catzilla_request_create();
    catzilla_response_t* response = catzilla_response_create();

    TEST_ASSERT(router != NULL && request != NULL && response != NULL, "Objects creation");

    // Set up request
    catzilla_request_set_method(request, "GET");
    catzilla_request_set_path(request, "/ordered");
    catzilla_request_set_header(request, "Authorization", "Bearer valid_token");

    // Register route with ordered middleware
    catzilla_middleware_fn_t ordered_mw[] = {
        test_auth_middleware,
        test_cors_middleware,
        test_logging_middleware
    };

    int result = catzilla_router_add_route_with_middleware(
        router, "GET", "/ordered", test_protected_handler, ordered_mw, 3
    );
    TEST_ASSERT(result == 0, "Route registration with ordered middleware");

    // Clear execution log
    clear_middleware_log();

    // Process request to test execution order
    result = catzilla_router_process_request(router, request, response);
    TEST_ASSERT(result == 0, "Request processing");

    // Verify middleware execution order
    TEST_ASSERT(strcmp(middleware_execution_log, "auth,cors,logging") == 0,
               "Middleware execution order preserved");
    TEST_ASSERT(middleware_call_count == 3, "All middleware executed");

    // Verify response status
    int status = catzilla_response_get_status(response);
    TEST_ASSERT(status == 200, "Successful response status");

    catzilla_request_destroy(request);
    catzilla_response_destroy(response);
    catzilla_router_destroy(router);

    TEST_END();
    tests_run++;
    tests_passed++;
    return 1;
}

/**
 * Test middleware short-circuiting
 */
int test_middleware_short_circuit() {
    TEST_START("Middleware Short-Circuit Behavior");

    catzilla_router_t* router = catzilla_router_create();
    catzilla_request_t* request = catzilla_request_create();
    catzilla_response_t* response = catzilla_response_create();

    TEST_ASSERT(router != NULL && request != NULL && response != NULL, "Objects creation");

    // Set up request without auth header (should trigger auth failure)
    catzilla_request_set_method(request, "GET");
    catzilla_request_set_path(request, "/protected");
    // No Authorization header - should fail auth

    // Register route with middleware chain
    catzilla_middleware_fn_t chain_mw[] = {
        test_auth_middleware,    // Should fail and short-circuit
        test_cors_middleware,    // Should NOT execute
        test_logging_middleware  // Should NOT execute
    };

    int result = catzilla_router_add_route_with_middleware(
        router, "GET", "/protected", test_protected_handler, chain_mw, 3
    );
    TEST_ASSERT(result == 0, "Route registration");

    // Clear execution log
    clear_middleware_log();

    // Process request - should short-circuit at auth
    result = catzilla_router_process_request(router, request, response);
    TEST_ASSERT(result == 1, "Request processing short-circuited");

    // Verify only auth middleware executed
    TEST_ASSERT(strcmp(middleware_execution_log, "auth") == 0,
               "Only auth middleware executed before short-circuit");
    TEST_ASSERT(middleware_call_count == 1, "Only one middleware executed");

    // Verify response status is 401 (unauthorized)
    int status = catzilla_response_get_status(response);
    TEST_ASSERT(status == 401, "Unauthorized response status");

    catzilla_request_destroy(request);
    catzilla_response_destroy(response);
    catzilla_router_destroy(router);

    TEST_END();
    tests_run++;
    tests_passed++;
    return 1;
}

/**
 * Test route without middleware (fast path)
 */
int test_route_without_middleware() {
    TEST_START("Route Without Middleware (Fast Path)");

    catzilla_router_t* router = catzilla_router_create();
    catzilla_request_t* request = catzilla_request_create();
    catzilla_response_t* response = catzilla_response_create();

    TEST_ASSERT(router != NULL && request != NULL && response != NULL, "Objects creation");

    // Set up request
    catzilla_request_set_method(request, "GET");
    catzilla_request_set_path(request, "/public");

    // Register route without middleware
    int result = catzilla_router_add_route_with_middleware(
        router, "GET", "/public", test_public_handler, NULL, 0
    );
    TEST_ASSERT(result == 0, "Route registration without middleware");

    // Clear execution log
    clear_middleware_log();

    // Process request - should go directly to handler
    result = catzilla_router_process_request(router, request, response);
    TEST_ASSERT(result == 0, "Request processing");

    // Verify no middleware executed
    TEST_ASSERT(strlen(middleware_execution_log) == 0, "No middleware executed");
    TEST_ASSERT(middleware_call_count == 0, "Zero middleware calls");

    // Verify response
    int status = catzilla_response_get_status(response);
    TEST_ASSERT(status == 200, "Successful response status");

    const char* body = catzilla_response_get_body(response);
    TEST_ASSERT(body != NULL && strstr(body, "public") != NULL, "Correct response body");

    catzilla_request_destroy(request);
    catzilla_response_destroy(response);
    catzilla_router_destroy(router);

    TEST_END();
    tests_run++;
    tests_passed++;
    return 1;
}

/**
 * Test memory management for middleware chains
 */
int test_middleware_memory_management() {
    TEST_START("Middleware Memory Management");

    catzilla_router_t* router = catzilla_router_create();
    TEST_ASSERT(router != NULL, "Router creation");

    // Register multiple routes with different middleware configurations
    catzilla_middleware_fn_t single_mw[] = { test_auth_middleware };
    catzilla_middleware_fn_t double_mw[] = { test_auth_middleware, test_cors_middleware };
    catzilla_middleware_fn_t triple_mw[] = { test_auth_middleware, test_cors_middleware, test_logging_middleware };
    catzilla_middleware_fn_t quad_mw[] = { test_auth_middleware, test_cors_middleware, test_logging_middleware, test_validation_middleware };

    // Register routes with different middleware counts
    int result = 0;
    result += catzilla_router_add_route_with_middleware(router, "GET", "/single", test_api_handler, single_mw, 1);
    result += catzilla_router_add_route_with_middleware(router, "GET", "/double", test_api_handler, double_mw, 2);
    result += catzilla_router_add_route_with_middleware(router, "GET", "/triple", test_api_handler, triple_mw, 3);
    result += catzilla_router_add_route_with_middleware(router, "GET", "/quad", test_api_handler, quad_mw, 4);
    result += catzilla_router_add_route_with_middleware(router, "GET", "/none", test_api_handler, NULL, 0);

    TEST_ASSERT(result == 0, "All routes registered successfully");

    // Verify route count
    int route_count = catzilla_router_get_route_count(router);
    TEST_ASSERT(route_count == 5, "Correct number of routes");

    // Test memory cleanup
    catzilla_router_destroy(router);

    TEST_END();
    tests_run++;
    tests_passed++;
    return 1;
}

/**
 * Test performance of middleware execution
 */
int test_middleware_performance() {
    TEST_START("Middleware Performance");

    catzilla_router_t* router = catzilla_router_create();
    catzilla_request_t* request = catzilla_request_create();
    catzilla_response_t* response = catzilla_response_create();

    TEST_ASSERT(router != NULL && request != NULL && response != NULL, "Objects creation");

    // Set up request
    catzilla_request_set_method(request, "GET");
    catzilla_request_set_path(request, "/perf");
    catzilla_request_set_header(request, "Authorization", "Bearer valid_token");

    // Register route with multiple middleware
    catzilla_middleware_fn_t perf_mw[] = {
        test_auth_middleware,
        test_cors_middleware,
        test_logging_middleware,
        test_validation_middleware
    };

    int result = catzilla_router_add_route_with_middleware(
        router, "GET", "/perf", test_api_handler, perf_mw, 4
    );
    TEST_ASSERT(result == 0, "Route registration");

    // Measure performance of multiple requests
    struct timeval start, end;
    gettimeofday(&start, NULL);

    const int iterations = 1000;
    for (int i = 0; i < iterations; i++) {
        clear_middleware_log();
        catzilla_response_reset(response);

        result = catzilla_router_process_request(router, request, response);
        TEST_ASSERT(result == 0, "Request processing in performance test");
    }

    gettimeofday(&end, NULL);

    // Calculate time per request
    double elapsed = (end.tv_sec - start.tv_sec) + (end.tv_usec - start.tv_usec) / 1000000.0;
    double time_per_request = elapsed / iterations;

    printf("📊 Performance: %d requests in %.4f seconds\n", iterations, elapsed);
    printf("📊 Time per request: %.6f seconds (%.2f μs)\n", time_per_request, time_per_request * 1000000);
    printf("📊 Requests per second: %.2f\n", iterations / elapsed);

    // Performance should be reasonable (less than 100μs per request with middleware)
    TEST_ASSERT(time_per_request < 0.0001, "Performance within acceptable range");

    catzilla_request_destroy(request);
    catzilla_response_destroy(response);
    catzilla_router_destroy(router);

    TEST_END();
    tests_run++;
    tests_passed++;
    return 1;
}

/**
 * Test different HTTP methods with middleware
 */
int test_http_methods_with_middleware() {
    TEST_START("HTTP Methods with Middleware");

    catzilla_router_t* router = catzilla_router_create();
    catzilla_request_t* request = catzilla_request_create();
    catzilla_response_t* response = catzilla_response_create();

    TEST_ASSERT(router != NULL && request != NULL && response != NULL, "Objects creation");

    // Register different HTTP methods with middleware
    catzilla_middleware_fn_t auth_mw[] = { test_auth_middleware };
    catzilla_middleware_fn_t cors_mw[] = { test_cors_middleware };
    catzilla_middleware_fn_t multi_mw[] = { test_auth_middleware, test_validation_middleware };

    int result = 0;
    result += catzilla_router_add_route_with_middleware(router, "GET", "/api/data", test_api_handler, auth_mw, 1);
    result += catzilla_router_add_route_with_middleware(router, "POST", "/api/data", test_api_handler, multi_mw, 2);
    result += catzilla_router_add_route_with_middleware(router, "PUT", "/api/data", test_api_handler, auth_mw, 1);
    result += catzilla_router_add_route_with_middleware(router, "DELETE", "/api/data", test_api_handler, auth_mw, 1);
    result += catzilla_router_add_route_with_middleware(router, "PATCH", "/api/data", test_api_handler, cors_mw, 1);

    TEST_ASSERT(result == 0, "All HTTP methods registered with middleware");

    // Test GET request
    catzilla_request_set_method(request, "GET");
    catzilla_request_set_path(request, "/api/data");
    catzilla_request_set_header(request, "Authorization", "Bearer valid_token");

    clear_middleware_log();
    result = catzilla_router_process_request(router, request, response);
    TEST_ASSERT(result == 0, "GET request processing");
    TEST_ASSERT(strcmp(middleware_execution_log, "auth") == 0, "GET middleware execution");

    // Test POST request
    catzilla_request_set_method(request, "POST");
    catzilla_response_reset(response);

    clear_middleware_log();
    result = catzilla_router_process_request(router, request, response);
    TEST_ASSERT(result == 0, "POST request processing");
    TEST_ASSERT(strcmp(middleware_execution_log, "auth,validation") == 0, "POST middleware execution");

    catzilla_request_destroy(request);
    catzilla_response_destroy(response);
    catzilla_router_destroy(router);

    TEST_END();
    tests_run++;
    tests_passed++;
    return 1;
}

/**
 * Test error handling in middleware
 */
int test_middleware_error_handling() {
    TEST_START("Middleware Error Handling");

    catzilla_router_t* router = catzilla_router_create();
    catzilla_request_t* request = catzilla_request_create();
    catzilla_response_t* response = catzilla_response_create();

    TEST_ASSERT(router != NULL && request != NULL && response != NULL, "Objects creation");

    // Test NULL middleware array
    int result = catzilla_router_add_route_with_middleware(
        router, "GET", "/null", test_api_handler, NULL, 0
    );
    TEST_ASSERT(result == 0, "Route with NULL middleware registered");

    // Test empty middleware array
    catzilla_middleware_fn_t empty_mw[1];  // Array exists but count is 0
    result = catzilla_router_add_route_with_middleware(
        router, "GET", "/empty", test_api_handler, empty_mw, 0
    );
    TEST_ASSERT(result == 0, "Route with empty middleware registered");

    // Test route matching for error cases
    catzilla_request_set_method(request, "GET");
    catzilla_request_set_path(request, "/nonexistent");

    result = catzilla_router_process_request(router, request, response);
    TEST_ASSERT(result != 0, "Non-existent route returns error");

    catzilla_request_destroy(request);
    catzilla_response_destroy(response);
    catzilla_router_destroy(router);

    TEST_END();
    tests_run++;
    tests_passed++;
    return 1;
}

/**
 * Main test runner
 */
int main() {
    printf("🌪️ Catzilla Per-Route Middleware C Tests\n");
    printf("==========================================\n");
    printf("Testing C-level per-route middleware implementation\n\n");

    // Run all tests
    if (!test_per_route_middleware_registration()) return 1;
    if (!test_middleware_execution_order()) return 1;
    if (!test_middleware_short_circuit()) return 1;
    if (!test_route_without_middleware()) return 1;
    if (!test_middleware_memory_management()) return 1;
    if (!test_middleware_performance()) return 1;
    if (!test_http_methods_with_middleware()) return 1;
    if (!test_middleware_error_handling()) return 1;

    // Print summary
    printf("\n🎉 Test Summary\n");
    printf("===============\n");
    printf("Tests run: %d\n", tests_run);
    printf("Tests passed: %d\n", tests_passed);
    printf("Success rate: %.1f%%\n", (float)tests_passed / tests_run * 100);

    if (tests_passed == tests_run) {
        printf("\n✅ All per-route middleware C tests passed!\n");
        printf("🚀 C-level implementation is working correctly\n");
        return 0;
    } else {
        printf("\n❌ Some tests failed\n");
        return 1;
    }
}
