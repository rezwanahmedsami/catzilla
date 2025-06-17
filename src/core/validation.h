#ifndef CATZILLA_VALIDATION_H
#define CATZILLA_VALIDATION_H

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "memory.h"

// Platform-specific regex support
#ifdef _WIN32
    #include "windows_compat.h"
#else
    #include <regex.h>
#endif

/**
 * Catzilla Ultra-Fast Validation Engine
 *
 * Provides C-accelerated field and model validation with jemalloc optimization.
 * Designed to be 100x faster than Python-based validation libraries like Pydantic.
 */

typedef enum {
    TYPE_INT,
    TYPE_FLOAT,
    TYPE_STRING,
    TYPE_BOOL,
    TYPE_LIST,
    TYPE_DICT,
    TYPE_OPTIONAL,
    TYPE_UNION
} catzilla_type_t;

typedef enum {
    VALIDATION_SUCCESS = 0,
    VALIDATION_ERROR_TYPE = 1,
    VALIDATION_ERROR_RANGE = 2,
    VALIDATION_ERROR_LENGTH = 3,
    VALIDATION_ERROR_PATTERN = 4,
    VALIDATION_ERROR_REQUIRED = 5,
    VALIDATION_ERROR_CUSTOM = 6,
    VALIDATION_ERROR_MEMORY = 7
} validation_result_t;

// Forward declarations
typedef struct validator validator_t;
typedef struct field_spec field_spec_t;
typedef struct model_spec model_spec_t;
typedef struct json_object json_object_t;
typedef struct validation_error validation_error_t;

/**
 * Validation Error Structure
 */
struct validation_error {
    char* field_name;
    char* message;
    validation_result_t error_code;
    struct validation_error* next;
};

/**
 * Validator Structure with Union for Type-Specific Rules
 */
struct validator {
    catzilla_type_t type;

    union {
        struct {
            long min;
            long max;
            int has_min;
            int has_max;
        } int_validator;

        struct {
            double min;
            double max;
            int has_min;
            int has_max;
        } float_validator;

        struct {
            int min_len;
            int max_len;
            char* pattern;
            regex_t* compiled_regex;
            int has_min_len;
            int has_max_len;
            int has_pattern;
        } string_validator;

        struct {
            validator_t* item_validator;
            int min_items;
            int max_items;
            int has_min_items;
            int has_max_items;
        } list_validator;

        struct {
            validator_t* value_validator;
            char** required_keys;
            int required_key_count;
        } dict_validator;

        struct {
            validator_t* inner_validator;
        } optional_validator;

        struct {
            validator_t** validators;
            int validator_count;
        } union_validator;
    };

    // Custom validation function pointer
    int (*custom_validator)(void* value, validation_error_t** error);

    // Default value (if applicable)
    void* default_value;
    catzilla_type_t default_type;
};

/**
 * Field Specification for Model Validation
 */
struct field_spec {
    char* field_name;
    validator_t* validator;
    int required;
    void* default_value;
    catzilla_type_t default_type;
};

/**
 * Model Specification Structure
 */
struct model_spec {
    field_spec_t* fields;
    int field_count;        // Maximum number of fields allocated
    int fields_added;       // Number of fields actually added
    char* model_name;
    int compiled;  // Flag to indicate if model is compiled and optimized
};

/**
 * JSON Object Structure (simplified for validation)
 */
struct json_object {
    enum {
        JSON_NULL,
        JSON_BOOL,
        JSON_INT,
        JSON_FLOAT,
        JSON_STRING,
        JSON_ARRAY,
        JSON_OBJECT
    } type;

    union {
        int bool_val;
        long int_val;
        double float_val;
        char* string_val;
        struct {
            struct json_object** items;
            int count;
        } array_val;
        struct {
            char** keys;
            struct json_object** values;
            int count;
        } object_val;
    };
};

/**
 * Validation Context for Memory Management
 */
typedef struct validation_context {
    void* arena;  // jemalloc arena for temporary allocations
    validation_error_t* errors;
    int error_count;
} validation_context_t;

// ============================================================================
// CORE VALIDATION API
// ============================================================================

/**
 * Create a new validator with specified type and rules
 */
validator_t* catzilla_create_validator(catzilla_type_t type);

/**
 * Create integer validator with min/max constraints
 */
validator_t* catzilla_create_int_validator(long min, long max, int has_min, int has_max);

/**
 * Create float validator with min/max constraints
 */
validator_t* catzilla_create_float_validator(double min, double max, int has_min, int has_max);

/**
 * Create string validator with length and pattern constraints
 */
validator_t* catzilla_create_string_validator(int min_len, int max_len, const char* pattern);

/**
 * Create list validator with item type and size constraints
 */
validator_t* catzilla_create_list_validator(validator_t* item_validator, int min_items, int max_items);

/**
 * Create optional validator wrapper
 */
validator_t* catzilla_create_optional_validator(validator_t* inner_validator);

/**
 * Free validator and all associated memory
 */
void catzilla_free_validator(validator_t* validator);

/**
 * Create a new model specification
 */
model_spec_t* catzilla_create_model_spec(const char* model_name, int field_count);

/**
 * Add field specification to model
 */
int catzilla_add_field_spec(model_spec_t* model, const char* field_name,
                           validator_t* validator, int required, void* default_value);

/**
 * Compile model specification for optimal validation performance
 */
int catzilla_compile_model_spec(model_spec_t* model);

/**
 * Free model specification and all associated memory
 */
void catzilla_free_model_spec(model_spec_t* model);

/**
 * Create validation context with jemalloc arena
 */
validation_context_t* catzilla_create_validation_context(void);

/**
 * Free validation context and cleanup memory
 */
void catzilla_free_validation_context(validation_context_t* ctx);

// ============================================================================
// VALIDATION FUNCTIONS
// ============================================================================

/**
 * Validate a single value against a validator
 */
validation_result_t catzilla_validate_value(validator_t* validator, json_object_t* value,
                                           validation_context_t* ctx);

/**
 * Validate entire model against JSON data - MAIN VALIDATION FUNCTION
 * Returns validated/coerced data in validated_data parameter
 */
validation_result_t catzilla_validate_model(model_spec_t* model, json_object_t* data,
                                           json_object_t** validated_data,
                                           validation_context_t* ctx);

/**
 * Get validation errors as formatted string
 */
char* catzilla_get_validation_errors(validation_context_t* ctx);

// ============================================================================
// JSON UTILITY FUNCTIONS
// ============================================================================

/**
 * Create JSON object from Python dict (for Python integration)
 */
json_object_t* catzilla_json_from_dict(void* python_dict);

/**
 * Convert JSON object to Python dict (for Python integration)
 */
void* catzilla_json_to_dict(json_object_t* json_obj);

/**
 * Create a deep copy of a JSON object
 */
json_object_t* catzilla_copy_json_object(json_object_t* obj);

/**
 * Create a new empty JSON object
 */
json_object_t* catzilla_create_json_object(void);

/**
 * Create a new JSON null value
 */
json_object_t* catzilla_create_json_null(void);

/**
 * Create a new JSON string value
 */
json_object_t* catzilla_create_json_string(const char* str);

/**
 * Create a new JSON number value
 */
json_object_t* catzilla_create_json_number(double value);

/**
 * Create a new JSON integer value
 */
json_object_t* catzilla_create_json_int(long value);

/**
 * Create a new JSON boolean value
 */
json_object_t* catzilla_create_json_bool(int value);

/**
 * Free JSON object and all associated memory
 */
void catzilla_free_json_object(json_object_t* obj);

/**
 * Free JSON object and all associated memory
 */
void catzilla_free_json_object(json_object_t* obj);

// ============================================================================
// JSON MANIPULATION FUNCTIONS
// ============================================================================

/**
 * Add a string field to a JSON object
 */
int catzilla_json_add_string(json_object_t* obj, const char* key, const char* value);

/**
 * Add an integer field to a JSON object
 */
int catzilla_json_add_int(json_object_t* obj, const char* key, long value);

/**
 * Add a boolean field to a JSON object
 */
int catzilla_json_add_bool(json_object_t* obj, const char* key, int value);

/**
 * Add a null field to a JSON object
 */
int catzilla_json_add_null(json_object_t* obj, const char* key);

/**
 * Get a string value from a JSON object
 */
char* catzilla_json_get_string(json_object_t* obj, const char* key);

/**
 * Get an integer value from a JSON object
 */
long catzilla_json_get_int(json_object_t* obj, const char* key);

/**
 * Get a boolean value from a JSON object
 */
int catzilla_json_get_bool(json_object_t* obj, const char* key);

// ============================================================================
// PERFORMANCE AND MEMORY OPTIMIZATION
// ============================================================================

/**
 * Pre-compile validation model for maximum performance
 * This optimizes the validation pipeline for repeated use
 */
int catzilla_optimize_model_validation(model_spec_t* model);

/**
 * Batch validate multiple models (for bulk operations)
 */
validation_result_t catzilla_batch_validate(model_spec_t* model, json_object_t** data_array,
                                           int count, json_object_t*** validated_array,
                                           validation_context_t* ctx);

/**
 * Get validation performance statistics
 */
typedef struct {
    unsigned long validations_performed;
    unsigned long total_time_ns;
    unsigned long memory_used_bytes;
    unsigned long cache_hits;
    unsigned long cache_misses;
} validation_stats_t;

validation_stats_t* catzilla_get_validation_stats(void);

/**
 * Reset validation performance statistics
 */
void catzilla_reset_validation_stats(void);

// ============================================================================
// ERROR HANDLING
// ============================================================================

/**
 * Add validation error to context
 */
void catzilla_add_validation_error(validation_context_t* ctx, const char* field_name,
                                 const char* message, validation_result_t error_code);

/**
 * Check if validation context has errors
 */
int catzilla_has_validation_errors(validation_context_t* ctx);

/**
 * Clear all validation errors from context
 */
void catzilla_clear_validation_errors(validation_context_t* ctx);

#endif // CATZILLA_VALIDATION_H
