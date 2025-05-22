// tests/c/test_router.c
#include "unity.h"
#include "server.h"

void setUp(void) {}
void tearDown(void) {}

void test_add_route_increments_route_count() {
    catzilla_server_t server;
    TEST_ASSERT_EQUAL(0, catzilla_server_init(&server));

    int result = catzilla_server_add_route(&server, "GET", "/hello", NULL, NULL);
    TEST_ASSERT_EQUAL(0, result);
    TEST_ASSERT_EQUAL(1, server.route_count);

    catzilla_server_cleanup(&server);
}

void test_add_multiple_routes() {
    catzilla_server_t server;
    catzilla_server_init(&server);

    catzilla_server_add_route(&server, "GET", "/a", NULL, NULL);
    catzilla_server_add_route(&server, "POST", "/b", NULL, NULL);
    catzilla_server_add_route(&server, "PUT", "/c", NULL, NULL);

    TEST_ASSERT_EQUAL(3, server.route_count);
    catzilla_server_cleanup(&server);
}

void test_route_storage_correctness() {
    catzilla_server_t server;
    catzilla_server_init(&server);

    catzilla_server_add_route(&server, "GET", "/check", NULL, NULL);

    TEST_ASSERT_EQUAL_STRING("GET", server.routes[0].method);
    TEST_ASSERT_EQUAL_STRING("/check", server.routes[0].path);

    catzilla_server_cleanup(&server);
}


int main(void) {
    UNITY_BEGIN();
    RUN_TEST(test_add_route_increments_route_count);
    RUN_TEST(test_add_multiple_routes);
    RUN_TEST(test_route_storage_correctness);
    return UNITY_END();
}
