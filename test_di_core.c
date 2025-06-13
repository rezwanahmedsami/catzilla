#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <assert.h>
#include "src/core/dependency.h"

// ============================================================================
// TEST HELPER FUNCTIONS AND MOCK SERVICES
// ============================================================================

/**
 * Simple mock database service for testing
 */
typedef struct {
    char connection_string[256];
    bool is_connected;
    int query_count;
} mock_database_t;

/**
 * Mock auth service that depends on database
 */
typedef struct {
    mock_database_t* database;
    char auth_token[128];
    bool is_authenticated;
} mock_auth_service_t;

/**
 * Factory function for database service
 */
void* create_database_service(void** dependencies, int dependency_count, void* user_data) {
    (void)dependencies; // Unused
    (void)dependency_count; // Unused

    mock_database_t* db = malloc(sizeof(mock_database_t));
    if (!db) return NULL;

    strcpy(db->connection_string, (char*)user_data ? (char*)user_data : "default_connection");
    db->is_connected = true;
    db->query_count = 0;

    printf("✓ Created database service with connection: %s\n", db->connection_string);
    return db;
}

/**
 * Factory function for auth service (depends on database)
 */
void* create_auth_service(void** dependencies, int dependency_count, void* user_data) {
    (void)user_data; // Unused

    if (dependency_count != 1 || !dependencies[0]) {
        printf("✗ Auth service: Invalid dependencies\n");
        return NULL;
    }

    mock_auth_service_t* auth = malloc(sizeof(mock_auth_service_t));
    if (!auth) return NULL;

    auth->database = (mock_database_t*)dependencies[0];
    strcpy(auth->auth_token, "mock_token_12345");
    auth->is_authenticated = true;

    printf("✓ Created auth service with database dependency\n");
    return auth;
}

/**
 * Test result tracking
 */
typedef struct {
    int tests_run;
    int tests_passed;
    int tests_failed;
} test_results_t;

static test_results_t g_test_results = {0, 0, 0};

#define RUN_TEST(test_func) do { \
    printf("\n=== Running: %s ===\n", #test_func); \
    g_test_results.tests_run++; \
    if (test_func()) { \
        printf("✓ PASSED: %s\n", #test_func); \
        g_test_results.tests_passed++; \
    } else { \
        printf("✗ FAILED: %s\n", #test_func); \
        g_test_results.tests_failed++; \
    } \
} while(0)

// ============================================================================
// CORE CONTAINER TESTS
// ============================================================================

bool test_container_initialization() {
    catzilla_di_container_t container;

    // Test initialization
    int result = catzilla_di_container_init(&container, NULL);
    if (result != 0) {
        printf("✗ Container initialization failed\n");
        return false;
    }

    if (!container.is_initialized) {
        printf("✗ Container not marked as initialized\n");
        return false;
    }

    if (container.service_count != 0) {
        printf("✗ New container should have 0 services\n");
        return false;
    }

    printf("✓ Container initialized successfully\n");

    // Cleanup
    catzilla_di_container_cleanup(&container);

    return true;
}

bool test_container_create_destroy() {
    // Test container creation
    catzilla_di_container_t* container = catzilla_di_container_create(NULL);
    if (!container) {
        printf("✗ Container creation failed\n");
        return false;
    }

    if (!container->is_initialized) {
        printf("✗ Created container not initialized\n");
        return false;
    }

    printf("✓ Container created successfully\n");

    // Test destruction
    catzilla_di_container_destroy(container);
    printf("✓ Container destroyed successfully\n");

    return true;
}

// ============================================================================
// SERVICE REGISTRATION TESTS
// ============================================================================

bool test_service_registration() {
    catzilla_di_container_t* container = catzilla_di_container_create(NULL);
    if (!container) return false;

    // Test C factory registration
    char* connection_string = "test_database_connection";
    int result = catzilla_di_register_service_c(
        container,
        "database",
        "MockDatabase",
        CATZILLA_DI_SCOPE_SINGLETON,
        create_database_service,
        NULL, // No dependencies
        0,
        connection_string
    );

    if (result != 0) {
        printf("✗ Service registration failed\n");
        catzilla_di_container_destroy(container);
        return false;
    }

    if (container->service_count != 1) {
        printf("✗ Service count should be 1, got %d\n", container->service_count);
        catzilla_di_container_destroy(container);
        return false;
    }

    printf("✓ Service registered successfully\n");

    // Test service lookup
    if (!catzilla_di_has_service(container, "database")) {
        printf("✗ Registered service not found\n");
        catzilla_di_container_destroy(container);
        return false;
    }

    printf("✓ Service lookup successful\n");

    catzilla_di_container_destroy(container);
    return true;
}

bool test_service_with_dependencies() {
    catzilla_di_container_t* container = catzilla_di_container_create(NULL);
    if (!container) return false;

    // Register database service (no dependencies)
    int result = catzilla_di_register_service_c(
        container,
        "database",
        "MockDatabase",
        CATZILLA_DI_SCOPE_SINGLETON,
        create_database_service,
        NULL,
        0,
        "test_connection"
    );

    if (result != 0) {
        printf("✗ Database service registration failed\n");
        catzilla_di_container_destroy(container);
        return false;
    }

    // Register auth service (depends on database)
    const char* auth_deps[] = {"database"};
    result = catzilla_di_register_service_c(
        container,
        "auth",
        "MockAuthService",
        CATZILLA_DI_SCOPE_SINGLETON,
        create_auth_service,
        auth_deps,
        1,
        NULL
    );

    if (result != 0) {
        printf("✗ Auth service registration failed\n");
        catzilla_di_container_destroy(container);
        return false;
    }

    if (container->service_count != 2) {
        printf("✗ Service count should be 2, got %d\n", container->service_count);
        catzilla_di_container_destroy(container);
        return false;
    }

    printf("✓ Services with dependencies registered successfully\n");

    catzilla_di_container_destroy(container);
    return true;
}

// ============================================================================
// SERVICE RESOLUTION TESTS
// ============================================================================

bool test_simple_service_resolution() {
    catzilla_di_container_t* container = catzilla_di_container_create(NULL);
    if (!container) return false;

    // Register database service
    int result = catzilla_di_register_service_c(
        container,
        "database",
        "MockDatabase",
        CATZILLA_DI_SCOPE_SINGLETON,
        create_database_service,
        NULL,
        0,
        "test_connection"
    );

    if (result != 0) {
        printf("✗ Service registration failed\n");
        catzilla_di_container_destroy(container);
        return false;
    }

    // Resolve service
    mock_database_t* db = (mock_database_t*)catzilla_di_resolve_service(container, "database", NULL);
    if (!db) {
        printf("✗ Service resolution failed\n");
        catzilla_di_container_destroy(container);
        return false;
    }

    if (!db->is_connected) {
        printf("✗ Resolved service not properly initialized\n");
        catzilla_di_container_destroy(container);
        return false;
    }

    if (strcmp(db->connection_string, "test_connection") != 0) {
        printf("✗ Service factory user_data not passed correctly\n");
        catzilla_di_container_destroy(container);
        return false;
    }

    printf("✓ Service resolution successful\n");

    catzilla_di_container_destroy(container);
    return true;
}

bool test_dependency_resolution() {
    catzilla_di_container_t* container = catzilla_di_container_create(NULL);
    if (!container) return false;

    // Register both services
    catzilla_di_register_service_c(
        container, "database", "MockDatabase", CATZILLA_DI_SCOPE_SINGLETON,
        create_database_service, NULL, 0, "dep_test_connection"
    );

    const char* auth_deps[] = {"database"};
    catzilla_di_register_service_c(
        container, "auth", "MockAuthService", CATZILLA_DI_SCOPE_SINGLETON,
        create_auth_service, auth_deps, 1, NULL
    );

    // Resolve auth service (should automatically resolve database dependency)
    mock_auth_service_t* auth = (mock_auth_service_t*)catzilla_di_resolve_service(container, "auth", NULL);
    if (!auth) {
        printf("✗ Auth service resolution failed\n");
        catzilla_di_container_destroy(container);
        return false;
    }

    if (!auth->database) {
        printf("✗ Database dependency not injected\n");
        catzilla_di_container_destroy(container);
        return false;
    }

    if (!auth->database->is_connected) {
        printf("✗ Injected database dependency not properly initialized\n");
        catzilla_di_container_destroy(container);
        return false;
    }

    if (strcmp(auth->database->connection_string, "dep_test_connection") != 0) {
        printf("✗ Database dependency has wrong connection string\n");
        catzilla_di_container_destroy(container);
        return false;
    }

    printf("✓ Dependency resolution successful\n");

    catzilla_di_container_destroy(container);
    return true;
}

bool test_singleton_scope() {
    catzilla_di_container_t* container = catzilla_di_container_create(NULL);
    if (!container) return false;

    // Register singleton service
    catzilla_di_register_service_c(
        container, "database", "MockDatabase", CATZILLA_DI_SCOPE_SINGLETON,
        create_database_service, NULL, 0, "singleton_test"
    );

    // Resolve service twice
    mock_database_t* db1 = (mock_database_t*)catzilla_di_resolve_service(container, "database", NULL);
    mock_database_t* db2 = (mock_database_t*)catzilla_di_resolve_service(container, "database", NULL);

    if (!db1 || !db2) {
        printf("✗ Service resolution failed\n");
        catzilla_di_container_destroy(container);
        return false;
    }

    if (db1 != db2) {
        printf("✗ Singleton services should return same instance\n");
        catzilla_di_container_destroy(container);
        return false;
    }

    printf("✓ Singleton scope working correctly\n");

    catzilla_di_container_destroy(container);
    return true;
}

// ============================================================================
// BULK RESOLUTION TESTS
// ============================================================================

bool test_bulk_service_resolution() {
    catzilla_di_container_t* container = catzilla_di_container_create(NULL);
    if (!container) return false;

    // Register services
    catzilla_di_register_service_c(
        container, "database", "MockDatabase", CATZILLA_DI_SCOPE_SINGLETON,
        create_database_service, NULL, 0, "bulk_test"
    );

    const char* auth_deps[] = {"database"};
    catzilla_di_register_service_c(
        container, "auth", "MockAuthService", CATZILLA_DI_SCOPE_SINGLETON,
        create_auth_service, auth_deps, 1, NULL
    );

    // Bulk resolution
    const char* service_names[] = {"database", "auth"};
    void* results[2] = {NULL, NULL};

    int resolved_count = catzilla_di_resolve_services(container, service_names, 2, NULL, results);

    if (resolved_count != 2) {
        printf("✗ Bulk resolution failed, resolved %d/2 services\n", resolved_count);
        catzilla_di_container_destroy(container);
        return false;
    }

    if (!results[0] || !results[1]) {
        printf("✗ Bulk resolution returned NULL results\n");
        catzilla_di_container_destroy(container);
        return false;
    }

    printf("✓ Bulk service resolution successful\n");

    catzilla_di_container_destroy(container);
    return true;
}

// ============================================================================
// VALIDATION TESTS
// ============================================================================

bool test_dependency_validation() {
    catzilla_di_container_t* container = catzilla_di_container_create(NULL);
    if (!container) return false;

    // Register services with valid dependencies
    catzilla_di_register_service_c(
        container, "database", "MockDatabase", CATZILLA_DI_SCOPE_SINGLETON,
        create_database_service, NULL, 0, "validation_test"
    );

    const char* auth_deps[] = {"database"};
    catzilla_di_register_service_c(
        container, "auth", "MockAuthService", CATZILLA_DI_SCOPE_SINGLETON,
        create_auth_service, auth_deps, 1, NULL
    );

    // Validate dependencies
    char error_buffer[512];
    int result = catzilla_di_validate_dependencies(container, error_buffer, sizeof(error_buffer));

    if (result != 0) {
        printf("✗ Dependency validation failed: %s\n", error_buffer);
        catzilla_di_container_destroy(container);
        return false;
    }

    printf("✓ Dependency validation successful\n");

    catzilla_di_container_destroy(container);
    return true;
}

// ============================================================================
// CONTEXT TESTS
// ============================================================================

bool test_di_context() {
    catzilla_di_container_t* container = catzilla_di_container_create(NULL);
    if (!container) return false;

    // Create context
    catzilla_di_context_t* context = catzilla_di_create_context(container);
    if (!context) {
        printf("✗ Context creation failed\n");
        catzilla_di_container_destroy(container);
        return false;
    }

    if (context->container != container) {
        printf("✗ Context not properly linked to container\n");
        catzilla_di_cleanup_context(context);
        catzilla_di_container_destroy(container);
        return false;
    }

    // Test request data association
    char* test_data = "test_request_data";
    catzilla_di_context_set_request_data(context, test_data);

    char* retrieved_data = (char*)catzilla_di_context_get_request_data(context);
    if (retrieved_data != test_data) {
        printf("✗ Context request data not properly stored/retrieved\n");
        catzilla_di_cleanup_context(context);
        catzilla_di_container_destroy(container);
        return false;
    }

    printf("✓ DI context working correctly\n");

    catzilla_di_cleanup_context(context);
    catzilla_di_container_destroy(container);
    return true;
}

// ============================================================================
// STATISTICS TESTS
// ============================================================================

bool test_di_statistics() {
    catzilla_di_container_t* container = catzilla_di_container_create(NULL);
    if (!container) return false;

    // Register some services
    catzilla_di_register_service_c(
        container, "database", "MockDatabase", CATZILLA_DI_SCOPE_SINGLETON,
        create_database_service, NULL, 0, "stats_test"
    );

    const char* auth_deps[] = {"database"};
    catzilla_di_register_service_c(
        container, "auth", "MockAuthService", CATZILLA_DI_SCOPE_TRANSIENT,
        create_auth_service, auth_deps, 1, NULL
    );

    // Get statistics
    catzilla_di_stats_t stats;
    catzilla_di_get_stats(container, &stats);

    if (stats.total_services != 2) {
        printf("✗ Statistics show wrong service count: %d\n", stats.total_services);
        catzilla_di_container_destroy(container);
        return false;
    }

    if (stats.singleton_services != 1) {
        printf("✗ Statistics show wrong singleton count: %d\n", stats.singleton_services);
        catzilla_di_container_destroy(container);
        return false;
    }

    if (stats.transient_services != 1) {
        printf("✗ Statistics show wrong transient count: %d\n", stats.transient_services);
        catzilla_di_container_destroy(container);
        return false;
    }

    printf("✓ DI statistics working correctly\n");

    catzilla_di_container_destroy(container);
    return true;
}

// ============================================================================
// MAIN TEST RUNNER
// ============================================================================

int main() {
    printf("🚀 CATZILLA DEPENDENCY INJECTION - CORE C TESTS\n");
    printf("===============================================\n");

    // Run all tests
    RUN_TEST(test_container_initialization);
    RUN_TEST(test_container_create_destroy);
    RUN_TEST(test_service_registration);
    RUN_TEST(test_service_with_dependencies);
    RUN_TEST(test_simple_service_resolution);
    RUN_TEST(test_dependency_resolution);
    RUN_TEST(test_singleton_scope);
    RUN_TEST(test_bulk_service_resolution);
    RUN_TEST(test_dependency_validation);
    RUN_TEST(test_di_context);
    RUN_TEST(test_di_statistics);

    // Print test results
    printf("\n===============================================\n");
    printf("📊 TEST RESULTS\n");
    printf("===============================================\n");
    printf("Total Tests:  %d\n", g_test_results.tests_run);
    printf("Passed:       %d\n", g_test_results.tests_passed);
    printf("Failed:       %d\n", g_test_results.tests_failed);

    if (g_test_results.tests_failed == 0) {
        printf("🎉 ALL TESTS PASSED! DI Core Implementation Working!\n");
        return 0;
    } else {
        printf("💥 %d TESTS FAILED! Need to fix issues.\n", g_test_results.tests_failed);
        return 1;
    }
}
