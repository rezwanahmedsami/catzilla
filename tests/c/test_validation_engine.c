/**
 * Comprehensive C unit tests for Catzilla's ultra-fast validation engine core.
 *
 * Tests cover:
 * 1. Memory management functions (allocation, deep copying)
 * 2. Validation core functions (model validation, value validation)
 * 3. Model specification functions (field specs, model compilation)
 * 4. Error handling functions (error collection, reporting)
 * 5. Performance and memory safety under stress
 */

#include "unity.h"
#include "validation.h"
#include "memory.h"
#include <string.h>
#include <stdlib.h>
#include <time.h>

// Test fixture setup and teardown
void setUp(void) {
    // Initialize memory system if needed
    catzilla_memory_init();
}

void tearDown(void) {
    // Cleanup memory system
    catzilla_memory_cleanup();
}

// ============================================================================
// Memory Management Tests
// ============================================================================

void test_memory_allocation_basic(void) {
    // Test basic memory allocation
    void* ptr1 = catzilla_malloc(64);
    TEST_ASSERT_NOT_NULL(ptr1);

    void* ptr2 = catzilla_malloc(128);
    TEST_ASSERT_NOT_NULL(ptr2);
    TEST_ASSERT_NOT_EQUAL(ptr1, ptr2);

    catzilla_free(ptr1);
    catzilla_free(ptr2);
}

void test_memory_typed_allocation(void) {
    // Test typed memory allocation functions
    void* request_ptr = catzilla_request_alloc(64);
    TEST_ASSERT_NOT_NULL(request_ptr);

    void* response_ptr = catzilla_response_alloc(128);
    TEST_ASSERT_NOT_NULL(response_ptr);

    void* cache_ptr = catzilla_cache_alloc(256);
    TEST_ASSERT_NOT_NULL(cache_ptr);

    catzilla_request_free(request_ptr);
    catzilla_response_free(response_ptr);
    catzilla_cache_free(cache_ptr);
}

void test_memory_reallocation(void) {
    // Test memory reallocation
    void* ptr = catzilla_malloc(64);
    TEST_ASSERT_NOT_NULL(ptr);

    // Write some data
    memset(ptr, 0xAA, 64);

    // Reallocate to larger size
    ptr = catzilla_realloc(ptr, 128);
    TEST_ASSERT_NOT_NULL(ptr);

    // Verify data is preserved (at least first 64 bytes)
    unsigned char* data = (unsigned char*)ptr;
    for (int i = 0; i < 64; i++) {
        TEST_ASSERT_EQUAL_HEX8(0xAA, data[i]);
    }

    catzilla_free(ptr);
}

void test_json_object_creation_and_manipulation(void) {
    // Test JSON object creation and manipulation
    json_object_t* obj = catzilla_create_json_object();
    TEST_ASSERT_NOT_NULL(obj);
    TEST_ASSERT_EQUAL(JSON_OBJECT, obj->type);

    // Add various types of values
    int result1 = catzilla_json_add_string(obj, "name", "test_user");
    TEST_ASSERT_EQUAL(0, result1);

    int result2 = catzilla_json_add_int(obj, "age", 25);
    TEST_ASSERT_EQUAL(0, result2);

    int result3 = catzilla_json_add_bool(obj, "active", 1);
    TEST_ASSERT_EQUAL(0, result3);

    // Verify values can be retrieved
    char* name = catzilla_json_get_string(obj, "name");
    TEST_ASSERT_NOT_NULL(name);
    TEST_ASSERT_EQUAL_STRING("test_user", name);

    long age = catzilla_json_get_int(obj, "age");
    TEST_ASSERT_EQUAL(25, age);

    int active = catzilla_json_get_bool(obj, "active");
    TEST_ASSERT_EQUAL(1, active);

    catzilla_free_json_object(obj);
}

void test_json_object_deep_copy(void) {
    // Create original JSON object
    json_object_t* original = catzilla_create_json_object();
    TEST_ASSERT_NOT_NULL(original);

    // Add some test data
    catzilla_json_add_string(original, "name", "test_user");
    catzilla_json_add_int(original, "age", 25);
    catzilla_json_add_bool(original, "active", 1);

    // Perform deep copy
    json_object_t* copy = catzilla_copy_json_object(original);
    TEST_ASSERT_NOT_NULL(copy);
    TEST_ASSERT_NOT_EQUAL(original, copy);

    // Verify copy contents
    char* name = catzilla_json_get_string(copy, "name");
    TEST_ASSERT_NOT_NULL(name);
    TEST_ASSERT_EQUAL_STRING("test_user", name);

    long age = catzilla_json_get_int(copy, "age");
    TEST_ASSERT_EQUAL(25, age);

    int active = catzilla_json_get_bool(copy, "active");
    TEST_ASSERT_EQUAL(1, active);

    // Cleanup
    catzilla_free_json_object(original);
    catzilla_free_json_object(copy);
}

// ============================================================================
// Validation Core Tests
// ============================================================================

void test_create_int_validator_basic(void) {
    validator_t* validator = catzilla_create_int_validator(0, 100, 1, 1);
    TEST_ASSERT_NOT_NULL(validator);
    TEST_ASSERT_EQUAL(TYPE_INT, validator->type);
    TEST_ASSERT_EQUAL(1, validator->int_validator.has_min);
    TEST_ASSERT_EQUAL(1, validator->int_validator.has_max);
    TEST_ASSERT_EQUAL(0, validator->int_validator.min);
    TEST_ASSERT_EQUAL(100, validator->int_validator.max);

    catzilla_free_validator(validator);
}

void test_create_string_validator_basic(void) {
    validator_t* validator = catzilla_create_string_validator(1, 50, NULL);
    TEST_ASSERT_NOT_NULL(validator);
    TEST_ASSERT_EQUAL(TYPE_STRING, validator->type);
    TEST_ASSERT_EQUAL(1, validator->string_validator.has_min_len);
    TEST_ASSERT_EQUAL(1, validator->string_validator.has_max_len);
    TEST_ASSERT_EQUAL(1, validator->string_validator.min_len);
    TEST_ASSERT_EQUAL(50, validator->string_validator.max_len);

    catzilla_free_validator(validator);
}

void test_validate_int_value_valid(void) {
    validator_t* validator = catzilla_create_int_validator(0, 100, 1, 1);
    json_object_t* value = catzilla_create_json_int(50);
    validation_context_t ctx = {0};

    validation_result_t result = catzilla_validate_value(validator, value, &ctx);

    TEST_ASSERT_EQUAL(VALIDATION_SUCCESS, result);

    catzilla_free_json_object(value);
    catzilla_free_validator(validator);
}

void test_validate_int_value_out_of_range(void) {
    validator_t* validator = catzilla_create_int_validator(0, 100, 1, 1);
    json_object_t* value = catzilla_create_json_int(150);
    validation_context_t ctx = {0};

    validation_result_t result = catzilla_validate_value(validator, value, &ctx);

    TEST_ASSERT_EQUAL(VALIDATION_ERROR_RANGE, result);

    catzilla_free_json_object(value);
    catzilla_free_validator(validator);
}

void test_validate_string_value_valid(void) {
    validator_t* validator = catzilla_create_string_validator(1, 20, NULL);
    json_object_t* value = catzilla_create_json_string("valid_string");
    validation_context_t ctx = {0};

    validation_result_t result = catzilla_validate_value(validator, value, &ctx);

    TEST_ASSERT_EQUAL(VALIDATION_SUCCESS, result);

    catzilla_free_json_object(value);
    catzilla_free_validator(validator);
}

void test_validate_string_value_too_long(void) {
    validator_t* validator = catzilla_create_string_validator(1, 5, NULL);
    json_object_t* value = catzilla_create_json_string("this_string_is_too_long");
    validation_context_t ctx = {0};

    validation_result_t result = catzilla_validate_value(validator, value, &ctx);

    TEST_ASSERT_EQUAL(VALIDATION_ERROR_LENGTH, result);

    catzilla_free_json_object(value);
    catzilla_free_validator(validator);
}

void test_validate_optional_value_with_data(void) {
    validator_t* int_validator = catzilla_create_int_validator(0, 100, 1, 1);
    validator_t* optional_validator = catzilla_create_optional_validator(int_validator);
    json_object_t* value = catzilla_create_json_int(42);
    validation_context_t ctx = {0};

    validation_result_t result = catzilla_validate_value(optional_validator, value, &ctx);

    TEST_ASSERT_EQUAL(VALIDATION_SUCCESS, result);

    catzilla_free_json_object(value);
    catzilla_free_validator(optional_validator);
}

void test_validate_optional_value_null(void) {
    validator_t* int_validator = catzilla_create_int_validator(0, 100, 1, 1);
    validator_t* optional_validator = catzilla_create_optional_validator(int_validator);
    json_object_t* value = catzilla_create_json_null();
    validation_context_t ctx = {0};

    validation_result_t result = catzilla_validate_value(optional_validator, value, &ctx);

    TEST_ASSERT_EQUAL(VALIDATION_SUCCESS, result);

    catzilla_free_json_object(value);
    catzilla_free_validator(optional_validator);
}

// ============================================================================
// Model Validation Tests
// ============================================================================

void test_validate_model_all_required_fields(void) {
    model_spec_t* model = catzilla_create_model_spec("User", 10);

    validator_t* id_validator = catzilla_create_int_validator(0, 999999, 1, 1);
    catzilla_add_field_spec(model, "id", id_validator, 1, NULL);

    validator_t* name_validator = catzilla_create_string_validator(1, 100, NULL);
    catzilla_add_field_spec(model, "name", name_validator, 1, NULL);

    // Create valid input data
    json_object_t* data = catzilla_create_json_object();
    catzilla_json_add_int(data, "id", 123);
    catzilla_json_add_string(data, "name", "John Doe");

    json_object_t* validated_data = NULL;
    validation_context_t ctx = {0};

    validation_result_t result = catzilla_validate_model(model, data, &validated_data, &ctx);
    TEST_ASSERT_EQUAL(VALIDATION_SUCCESS, result);
    TEST_ASSERT_NOT_NULL(validated_data);

    catzilla_free_json_object(data);
    catzilla_free_json_object(validated_data);
    catzilla_free_model_spec(model);
}

void test_validate_model_with_optional_fields(void) {
    model_spec_t* model = catzilla_create_model_spec("User", 10);

    // Required field
    validator_t* name_validator = catzilla_create_string_validator(1, 100, NULL);
    catzilla_add_field_spec(model, "name", name_validator, 1, NULL);

    // Optional field with default
    validator_t* age_validator = catzilla_create_int_validator(0, 150, 1, 1);
    json_object_t* default_age = catzilla_create_json_int(25);
    catzilla_add_field_spec(model, "age", age_validator, 0, default_age);

    // Test 1: Only required field
    json_object_t* data1 = catzilla_create_json_object();
    catzilla_json_add_string(data1, "name", "John");

    json_object_t* validated_data1 = NULL;
    validation_context_t ctx1 = {0};

    validation_result_t result1 = catzilla_validate_model(model, data1, &validated_data1, &ctx1);
    TEST_ASSERT_EQUAL(VALIDATION_SUCCESS, result1);
    TEST_ASSERT_NOT_NULL(validated_data1);

    // Validated data should include default age
    long validated_age = catzilla_json_get_int(validated_data1, "age");
    TEST_ASSERT_EQUAL(25, validated_age);

    // Test 2: Required + explicit optional field
    json_object_t* data2 = catzilla_create_json_object();
    catzilla_json_add_string(data2, "name", "Jane");
    catzilla_json_add_int(data2, "age", 30);

    json_object_t* validated_data2 = NULL;
    validation_context_t ctx2 = {0};

    validation_result_t result2 = catzilla_validate_model(model, data2, &validated_data2, &ctx2);
    TEST_ASSERT_EQUAL(VALIDATION_SUCCESS, result2);
    TEST_ASSERT_NOT_NULL(validated_data2);

    // Validated data should use explicit age
    long validated_age2 = catzilla_json_get_int(validated_data2, "age");
    TEST_ASSERT_EQUAL(30, validated_age2);

    catzilla_free_json_object(data1);
    catzilla_free_json_object(validated_data1);
    catzilla_free_json_object(data2);
    catzilla_free_json_object(validated_data2);
    catzilla_free_model_spec(model);
}

void test_validate_model_optional_field_null(void) {
    model_spec_t* model = catzilla_create_model_spec("User", 10);

    validator_t* name_validator = catzilla_create_string_validator(1, 100, NULL);
    catzilla_add_field_spec(model, "name", name_validator, 1, NULL);

    validator_t* age_validator = catzilla_create_int_validator(0, 150, 1, 1);
    catzilla_add_field_spec(model, "age", age_validator, 0, NULL);

    json_object_t* data = catzilla_create_json_object();
    catzilla_json_add_string(data, "name", "John");
    catzilla_json_add_null(data, "age");

    json_object_t* validated_data = NULL;
    validation_context_t ctx = {0};

    validation_result_t result = catzilla_validate_model(model, data, &validated_data, &ctx);
    TEST_ASSERT_EQUAL(VALIDATION_SUCCESS, result);
    TEST_ASSERT_NOT_NULL(validated_data);

    catzilla_free_json_object(data);
    catzilla_free_json_object(validated_data);
    catzilla_free_model_spec(model);
}

// ============================================================================
// Performance Tests
// ============================================================================

void test_performance_validation_benchmark(void) {
    model_spec_t* model = catzilla_create_model_spec("BenchmarkModel", 10);

    // Create model with mixed required/optional fields
    validator_t* id_validator = catzilla_create_int_validator(0, 999999, 1, 1);
    catzilla_add_field_spec(model, "id", id_validator, 1, NULL);

    validator_t* name_validator = catzilla_create_string_validator(1, 100, NULL);
    catzilla_add_field_spec(model, "name", name_validator, 1, NULL);

    validator_t* email_validator = catzilla_create_string_validator(5, 100, NULL);
    catzilla_add_field_spec(model, "email", email_validator, 0, NULL);

    validator_t* age_validator = catzilla_create_int_validator(0, 150, 1, 1);
    json_object_t* default_age = catzilla_create_json_int(25);
    catzilla_add_field_spec(model, "age", age_validator, 0, default_age);

    // Perform benchmark with reduced iterations for testing
    clock_t start = clock();
    int iterations = 1000;  // Reduced for test stability

    for (int i = 0; i < iterations; i++) {
        json_object_t* data = catzilla_create_json_object();
        catzilla_json_add_int(data, "id", i);
        catzilla_json_add_string(data, "name", "test_user");

        if (i % 2 == 0) {
            catzilla_json_add_string(data, "email", "test@example.com");
        }
        if (i % 3 == 0) {
            catzilla_json_add_int(data, "age", 30);
        }

        json_object_t* validated_data = NULL;
        validation_context_t ctx = {0};

        validation_result_t result = catzilla_validate_model(model, data, &validated_data, &ctx);
        TEST_ASSERT_EQUAL(VALIDATION_SUCCESS, result);

        catzilla_free_json_object(data);
        catzilla_free_json_object(validated_data);
    }

    clock_t end = clock();
    double time_taken = ((double)(end - start)) / CLOCKS_PER_SEC;
    double validations_per_sec = iterations / time_taken;

    printf("Validation performance: %.0f validations/sec\n", validations_per_sec);

    // Should achieve reasonable performance
    TEST_ASSERT_TRUE(validations_per_sec > 100.0);

    catzilla_free_model_spec(model);
}

// ============================================================================
// Main Test Runner
// ============================================================================

int main(void) {
    UNITY_BEGIN();

    // Memory Management Tests
    RUN_TEST(test_memory_allocation_basic);
    RUN_TEST(test_memory_typed_allocation);
    RUN_TEST(test_memory_reallocation);
    RUN_TEST(test_json_object_creation_and_manipulation);
    RUN_TEST(test_json_object_deep_copy);

    // Validation Core Tests
    RUN_TEST(test_create_int_validator_basic);
    RUN_TEST(test_create_string_validator_basic);
    RUN_TEST(test_validate_int_value_valid);
    RUN_TEST(test_validate_int_value_out_of_range);
    RUN_TEST(test_validate_string_value_valid);
    RUN_TEST(test_validate_string_value_too_long);
    RUN_TEST(test_validate_optional_value_with_data);
    RUN_TEST(test_validate_optional_value_null);

    // Model Validation Tests
    RUN_TEST(test_validate_model_all_required_fields);
    RUN_TEST(test_validate_model_with_optional_fields);
    RUN_TEST(test_validate_model_optional_field_null);

    // Performance Tests
    RUN_TEST(test_performance_validation_benchmark);

    return UNITY_END();
}
