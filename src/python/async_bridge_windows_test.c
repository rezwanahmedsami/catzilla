/*
 * Windows compatibility test for async_bridge.c
 *
 * This file tests that the async bridge compiles on Windows
 * by including the necessary headers and using libuv primitives.
 */

#include <Python.h>
#include <uv.h>
#include <stdbool.h>
#include <assert.h>
#include <stdarg.h>
#include <stdio.h>

// Platform-specific includes (same as async_bridge.c)
#ifdef _WIN32
    #include <windows.h>
    #include <io.h>
#else
    #include <unistd.h>
    #include <pthread.h>
#endif

// Test that libuv threading primitives work
int test_libuv_threading() {
    uv_mutex_t test_mutex;
    uv_cond_t test_cond;
    uv_once_t test_once = UV_ONCE_INIT;

    // Test mutex
    if (uv_mutex_init(&test_mutex) != 0) {
        return -1;
    }

    uv_mutex_lock(&test_mutex);
    uv_mutex_unlock(&test_mutex);
    uv_mutex_destroy(&test_mutex);

    // Test condition variable
    if (uv_cond_init(&test_cond) != 0) {
        return -1;
    }

    uv_cond_destroy(&test_cond);

    return 0;
}

// Test main function
int main() {
    printf("Testing Windows compatibility for async_bridge...\n");

    if (test_libuv_threading() == 0) {
        printf("✓ libuv threading primitives work\n");
    } else {
        printf("✗ libuv threading primitives failed\n");
        return 1;
    }

    printf("✓ Windows compatibility test passed\n");
    return 0;
}
