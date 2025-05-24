// tests/c/test_advanced_router.c
#include "unity.h"
#include "router.h"
#include <string.h>

static catzilla_router_t router;

void setUp(void) {
    TEST_ASSERT_EQUAL(0, catzilla_router_init(&router));
}

void tearDown(void) {
    catzilla_router_cleanup(&router);
}

// Basic route operations
void test_router_init_cleanup() {
    catzilla_router_t test_router;
    TEST_ASSERT_EQUAL(0, catzilla_router_init(&test_router));
    TEST_ASSERT_NOT_NULL(test_router.root);
    TEST_ASSERT_EQUAL(0, test_router.route_count);
    catzilla_router_cleanup(&test_router);
}

void test_add_static_route() {
    void* dummy_handler = (void*)0x12345;
    uint32_t route_id = catzilla_router_add_route(&router, "GET", "/hello", dummy_handler, NULL, false);

    TEST_ASSERT_NOT_EQUAL(0, route_id);
    TEST_ASSERT_EQUAL(1, router.route_count);
}

void test_add_multiple_static_routes() {
    void* handler1 = (void*)0x12345;
    void* handler2 = (void*)0x23456;
    void* handler3 = (void*)0x34567;

    uint32_t id1 = catzilla_router_add_route(&router, "GET", "/", handler1, NULL, false);
    uint32_t id2 = catzilla_router_add_route(&router, "POST", "/api", handler2, NULL, false);
    uint32_t id3 = catzilla_router_add_route(&router, "PUT", "/api/v1", handler3, NULL, false);

    TEST_ASSERT_NOT_EQUAL(0, id1);
    TEST_ASSERT_NOT_EQUAL(0, id2);
    TEST_ASSERT_NOT_EQUAL(0, id3);
    TEST_ASSERT_EQUAL(3, router.route_count);
}

// Dynamic route tests
void test_add_dynamic_route() {
    void* dummy_handler = (void*)0x12345;
    uint32_t route_id = catzilla_router_add_route(&router, "GET", "/users/{user_id}", dummy_handler, NULL, false);

    TEST_ASSERT_NOT_EQUAL(0, route_id);
    TEST_ASSERT_EQUAL(1, router.route_count);
}

void test_add_multiple_dynamic_routes() {
    void* handler1 = (void*)0x12345;
    void* handler2 = (void*)0x23456;
    void* handler3 = (void*)0x34567;

    uint32_t id1 = catzilla_router_add_route(&router, "GET", "/users/{user_id}", handler1, NULL, false);
    uint32_t id2 = catzilla_router_add_route(&router, "POST", "/users/{user_id}/posts", handler2, NULL, false);
    uint32_t id3 = catzilla_router_add_route(&router, "GET", "/users/{user_id}/posts/{post_id}", handler3, NULL, false);

    TEST_ASSERT_NOT_EQUAL(0, id1);
    TEST_ASSERT_NOT_EQUAL(0, id2);
    TEST_ASSERT_NOT_EQUAL(0, id3);
    TEST_ASSERT_EQUAL(3, router.route_count);
}

// Route matching tests
void test_match_static_route() {
    void* dummy_handler = (void*)0x12345;
    catzilla_router_add_route(&router, "GET", "/hello", dummy_handler, NULL, false);

    catzilla_route_match_t match;
    int result = catzilla_router_match(&router, "GET", "/hello", &match);

    TEST_ASSERT_EQUAL(0, result);
    TEST_ASSERT_NOT_NULL(match.route);
    TEST_ASSERT_EQUAL_STRING("GET", match.route->method);
    TEST_ASSERT_EQUAL_STRING("/hello", match.route->path);
    TEST_ASSERT_EQUAL_PTR(dummy_handler, match.route->handler);
    TEST_ASSERT_EQUAL(0, match.param_count);
}

void test_match_dynamic_route() {
    void* dummy_handler = (void*)0x12345;
    catzilla_router_add_route(&router, "GET", "/users/{user_id}", dummy_handler, NULL, false);

    catzilla_route_match_t match;
    int result = catzilla_router_match(&router, "GET", "/users/123", &match);

    TEST_ASSERT_EQUAL(0, result);
    TEST_ASSERT_NOT_NULL(match.route);
    TEST_ASSERT_EQUAL_STRING("GET", match.route->method);
    TEST_ASSERT_EQUAL_STRING("/users/{user_id}", match.route->path);
    TEST_ASSERT_EQUAL_PTR(dummy_handler, match.route->handler);
    TEST_ASSERT_EQUAL(1, match.param_count);
    TEST_ASSERT_EQUAL_STRING("user_id", match.params[0].name);
    TEST_ASSERT_EQUAL_STRING("123", match.params[0].value);
}

void test_match_multiple_parameters() {
    void* dummy_handler = (void*)0x12345;
    catzilla_router_add_route(&router, "GET", "/users/{user_id}/posts/{post_id}", dummy_handler, NULL, false);

    catzilla_route_match_t match;
    int result = catzilla_router_match(&router, "GET", "/users/456/posts/789", &match);

    TEST_ASSERT_EQUAL(0, result);
    TEST_ASSERT_NOT_NULL(match.route);
    TEST_ASSERT_EQUAL(2, match.param_count);
    TEST_ASSERT_EQUAL_STRING("user_id", match.params[0].name);
    TEST_ASSERT_EQUAL_STRING("456", match.params[0].value);
    TEST_ASSERT_EQUAL_STRING("post_id", match.params[1].name);
    TEST_ASSERT_EQUAL_STRING("789", match.params[1].value);
}

void test_no_match_wrong_path() {
    void* dummy_handler = (void*)0x12345;
    catzilla_router_add_route(&router, "GET", "/hello", dummy_handler, NULL, false);

    catzilla_route_match_t match;
    int result = catzilla_router_match(&router, "GET", "/goodbye", &match);

    TEST_ASSERT_EQUAL(-1, result);
    TEST_ASSERT_NULL(match.route);
}

void test_no_match_wrong_method() {
    void* dummy_handler = (void*)0x12345;
    catzilla_router_add_route(&router, "GET", "/hello", dummy_handler, NULL, false);

    catzilla_route_match_t match;
    int result = catzilla_router_match(&router, "POST", "/hello", &match);

    TEST_ASSERT_EQUAL(-1, result);
    TEST_ASSERT_NULL(match.route);
}

// Edge cases
void test_invalid_parameters() {
    catzilla_route_match_t match;

    // NULL router
    TEST_ASSERT_EQUAL(-1, catzilla_router_match(NULL, "GET", "/hello", &match));

    // NULL method
    TEST_ASSERT_EQUAL(-1, catzilla_router_match(&router, NULL, "/hello", &match));

    // NULL path
    TEST_ASSERT_EQUAL(-1, catzilla_router_match(&router, "GET", NULL, &match));

    // NULL match
    TEST_ASSERT_EQUAL(-1, catzilla_router_match(&router, "GET", "/hello", NULL));

    // NULL handler for add_route
    TEST_ASSERT_EQUAL(0, catzilla_router_add_route(&router, "GET", "/hello", NULL, NULL, false));
}

void test_root_path() {
    void* dummy_handler = (void*)0x12345;
    uint32_t route_id = catzilla_router_add_route(&router, "GET", "/", dummy_handler, NULL, false);

    TEST_ASSERT_NOT_EQUAL(0, route_id);

    catzilla_route_match_t match;
    int result = catzilla_router_match(&router, "GET", "/", &match);

    TEST_ASSERT_EQUAL(0, result);
    TEST_ASSERT_NOT_NULL(match.route);
    TEST_ASSERT_EQUAL_STRING("/", match.route->path);
}

void test_trailing_slash_normalization() {
    void* dummy_handler = (void*)0x12345;
    catzilla_router_add_route(&router, "GET", "/hello", dummy_handler, NULL, false);

    catzilla_route_match_t match;

    // Should match without trailing slash
    int result1 = catzilla_router_match(&router, "GET", "/hello", &match);
    TEST_ASSERT_EQUAL(0, result1);

    // Should also match with trailing slash (normalized)
    int result2 = catzilla_router_match(&router, "GET", "/hello/", &match);
    TEST_ASSERT_EQUAL(0, result2);
}

// Memory management tests
void test_large_number_of_routes() {
    void* dummy_handler = (void*)0x12345;

    // Add many routes to test capacity expansion
    for (int i = 0; i < 100; i++) {
        char path[64];
        snprintf(path, sizeof(path), "/route_%d", i);
        uint32_t route_id = catzilla_router_add_route(&router, "GET", path, dummy_handler, NULL, false);
        TEST_ASSERT_NOT_EQUAL(0, route_id);
    }

    TEST_ASSERT_EQUAL(100, router.route_count);

    // Test that all routes can be matched
    for (int i = 0; i < 100; i++) {
        char path[64];
        snprintf(path, sizeof(path), "/route_%d", i);

        catzilla_route_match_t match;
        int result = catzilla_router_match(&router, "GET", path, &match);
        TEST_ASSERT_EQUAL(0, result);
        TEST_ASSERT_NOT_NULL(match.route);
    }
}

int main(void) {
    UNITY_BEGIN();

    // Basic operations
    RUN_TEST(test_router_init_cleanup);
    RUN_TEST(test_add_static_route);
    RUN_TEST(test_add_multiple_static_routes);

    // Dynamic routes
    RUN_TEST(test_add_dynamic_route);
    RUN_TEST(test_add_multiple_dynamic_routes);

    // Route matching
    RUN_TEST(test_match_static_route);
    RUN_TEST(test_match_dynamic_route);
    RUN_TEST(test_match_multiple_parameters);
    RUN_TEST(test_no_match_wrong_path);
    RUN_TEST(test_no_match_wrong_method);

    // Edge cases
    RUN_TEST(test_invalid_parameters);
    RUN_TEST(test_root_path);
    RUN_TEST(test_trailing_slash_normalization);

    // Memory management
    RUN_TEST(test_large_number_of_routes);

    return UNITY_END();
}
