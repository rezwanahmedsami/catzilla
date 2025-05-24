// tests/c/test_server_integration.c
#include "unity.h"
#include "server.h"
#include <string.h>

static catzilla_server_t server;

void setUp(void) {
    TEST_ASSERT_EQUAL(0, catzilla_server_init(&server));
}

void tearDown(void) {
    catzilla_server_cleanup(&server);
}

// Mock handler function for testing
void mock_handler(catzilla_request_t* request) {
    // Mock handler does nothing
}

// Server integration tests
void test_server_init_cleanup() {
    catzilla_server_t test_server;
    TEST_ASSERT_EQUAL(0, catzilla_server_init(&test_server));
    TEST_ASSERT_EQUAL(0, test_server.route_count);
    TEST_ASSERT_NOT_NULL(test_server.router.root);
    catzilla_server_cleanup(&test_server);
}

void test_add_route_to_server() {
    int result = catzilla_server_add_route(&server, "GET", "/hello", (void*)mock_handler, NULL);
    TEST_ASSERT_EQUAL(0, result);
}

void test_add_dynamic_route_to_server() {
    int result = catzilla_server_add_route(&server, "GET", "/users/{id}", (void*)mock_handler, NULL);
    TEST_ASSERT_EQUAL(0, result);
}

void test_route_count() {
    TEST_ASSERT_EQUAL(0, catzilla_server_get_route_count(&server));

    catzilla_server_add_route(&server, "GET", "/route1", (void*)mock_handler, NULL);
    TEST_ASSERT_EQUAL(1, catzilla_server_get_route_count(&server));

    catzilla_server_add_route(&server, "POST", "/route2", (void*)mock_handler, NULL);
    TEST_ASSERT_EQUAL(2, catzilla_server_get_route_count(&server));
}

void test_has_route() {
    // Initially no routes
    TEST_ASSERT_FALSE(catzilla_server_has_route(&server, "GET", "/hello"));

    // Add a route
    catzilla_server_add_route(&server, "GET", "/hello", (void*)mock_handler, NULL);
    TEST_ASSERT_TRUE(catzilla_server_has_route(&server, "GET", "/hello"));

    // Different method should not match
    TEST_ASSERT_FALSE(catzilla_server_has_route(&server, "POST", "/hello"));

    // Different path should not match
    TEST_ASSERT_FALSE(catzilla_server_has_route(&server, "GET", "/goodbye"));
}

void test_has_dynamic_route() {
    catzilla_server_add_route(&server, "GET", "/users/{id}", (void*)mock_handler, NULL);

    // Should find the dynamic route pattern
    TEST_ASSERT_TRUE(catzilla_server_has_route(&server, "GET", "/users/123"));
    TEST_ASSERT_TRUE(catzilla_server_has_route(&server, "GET", "/users/abc"));

    // Should not match wrong paths
    TEST_ASSERT_FALSE(catzilla_server_has_route(&server, "GET", "/users"));
    TEST_ASSERT_FALSE(catzilla_server_has_route(&server, "GET", "/users/123/extra"));
}

void test_route_info() {
    catzilla_server_add_route(&server, "GET", "/users/{id}", (void*)mock_handler, NULL);

    char info[256];
    int result = catzilla_server_get_route_info(&server, "GET", "/users/123", info, sizeof(info));

    TEST_ASSERT_EQUAL(0, result);
    TEST_ASSERT_NOT_EQUAL(0, strlen(info)); // Should have some info
}

void test_route_conflict_detection() {
    // Add initial route
    catzilla_server_add_route(&server, "GET", "/users/{id}", (void*)mock_handler, NULL);

    // This should trigger conflict detection (but still succeed)
    catzilla_server_add_route(&server, "GET", "/users/profile", (void*)mock_handler, NULL);

    // Both routes should exist
    TEST_ASSERT_TRUE(catzilla_server_has_route(&server, "GET", "/users/123"));
    TEST_ASSERT_TRUE(catzilla_server_has_route(&server, "GET", "/users/profile"));
}

void test_multiple_methods_same_path() {
    // Add multiple methods for same path
    catzilla_server_add_route(&server, "GET", "/api/data", (void*)mock_handler, NULL);
    catzilla_server_add_route(&server, "POST", "/api/data", (void*)mock_handler, NULL);
    catzilla_server_add_route(&server, "PUT", "/api/data", (void*)mock_handler, NULL);

    // All should be findable
    TEST_ASSERT_TRUE(catzilla_server_has_route(&server, "GET", "/api/data"));
    TEST_ASSERT_TRUE(catzilla_server_has_route(&server, "POST", "/api/data"));
    TEST_ASSERT_TRUE(catzilla_server_has_route(&server, "PUT", "/api/data"));
    TEST_ASSERT_FALSE(catzilla_server_has_route(&server, "DELETE", "/api/data"));
}

void test_route_parameter_validation() {
    // Test invalid parameters
    TEST_ASSERT_EQUAL(-1, catzilla_server_add_route(NULL, "GET", "/hello", (void*)mock_handler, NULL));
    TEST_ASSERT_EQUAL(-1, catzilla_server_add_route(&server, NULL, "/hello", (void*)mock_handler, NULL));
    TEST_ASSERT_EQUAL(-1, catzilla_server_add_route(&server, "GET", NULL, (void*)mock_handler, NULL));

    // Valid parameters should work
    TEST_ASSERT_EQUAL(0, catzilla_server_add_route(&server, "GET", "/hello", (void*)mock_handler, NULL));
}

void test_complex_routing_patterns() {
    // Add various complex patterns
    catzilla_server_add_route(&server, "GET", "/", (void*)mock_handler, NULL);
    catzilla_server_add_route(&server, "GET", "/api", (void*)mock_handler, NULL);
    catzilla_server_add_route(&server, "GET", "/api/v1", (void*)mock_handler, NULL);
    catzilla_server_add_route(&server, "GET", "/api/v1/users", (void*)mock_handler, NULL);
    catzilla_server_add_route(&server, "GET", "/api/v1/users/{id}", (void*)mock_handler, NULL);
    catzilla_server_add_route(&server, "GET", "/api/v1/users/{id}/posts", (void*)mock_handler, NULL);
    catzilla_server_add_route(&server, "GET", "/api/v1/users/{id}/posts/{post_id}", (void*)mock_handler, NULL);

    // Test that all patterns work
    TEST_ASSERT_TRUE(catzilla_server_has_route(&server, "GET", "/"));
    TEST_ASSERT_TRUE(catzilla_server_has_route(&server, "GET", "/api"));
    TEST_ASSERT_TRUE(catzilla_server_has_route(&server, "GET", "/api/v1"));
    TEST_ASSERT_TRUE(catzilla_server_has_route(&server, "GET", "/api/v1/users"));
    TEST_ASSERT_TRUE(catzilla_server_has_route(&server, "GET", "/api/v1/users/123"));
    TEST_ASSERT_TRUE(catzilla_server_has_route(&server, "GET", "/api/v1/users/123/posts"));
    TEST_ASSERT_TRUE(catzilla_server_has_route(&server, "GET", "/api/v1/users/123/posts/456"));
}

int main(void) {
    UNITY_BEGIN();

    // Basic server integration
    RUN_TEST(test_server_init_cleanup);
    RUN_TEST(test_add_route_to_server);
    RUN_TEST(test_add_dynamic_route_to_server);

    // Route management
    RUN_TEST(test_route_count);
    RUN_TEST(test_has_route);
    RUN_TEST(test_has_dynamic_route);
    RUN_TEST(test_route_info);

    // Advanced features
    RUN_TEST(test_route_conflict_detection);
    RUN_TEST(test_multiple_methods_same_path);
    RUN_TEST(test_route_parameter_validation);
    RUN_TEST(test_complex_routing_patterns);

    return UNITY_END();
}
