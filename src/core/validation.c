// Platform compatibility
#include "platform_compat.h"

// System headers
#include <stdlib.h>
#include <string.h>
#include <stdio.h>
#include <time.h>
#include <assert.h>

// Project headers
#include "validation.h"
#include "memory.h"

// Platform-specific regex support
#ifdef _WIN32
    #include "windows_compat.h"
#else
    #include <regex.h>
#endif

// Global validation statistics
static validation_stats_t g_validation_stats = {0};

// ============================================================================
// VALIDATOR CREATION FUNCTIONS
// ============================================================================

validator_t* catzilla_create_validator(catzilla_type_t type) {
    validator_t* validator = catzilla_cache_alloc(sizeof(validator_t));
    if (!validator) return NULL;

    memset(validator, 0, sizeof(validator_t));
    validator->type = type;
    validator->custom_validator = NULL;
    validator->default_value = NULL;

    return validator;
}

validator_t* catzilla_create_int_validator(long min, long max, int has_min, int has_max) {
    validator_t* validator = catzilla_create_validator(TYPE_INT);
    if (!validator) return NULL;

    validator->int_validator.min = min;
    validator->int_validator.max = max;
    validator->int_validator.has_min = has_min;
    validator->int_validator.has_max = has_max;

    return validator;
}

validator_t* catzilla_create_float_validator(double min, double max, int has_min, int has_max) {
    validator_t* validator = catzilla_create_validator(TYPE_FLOAT);
    if (!validator) return NULL;

    validator->float_validator.min = min;
    validator->float_validator.max = max;
    validator->float_validator.has_min = has_min;
    validator->float_validator.has_max = has_max;

    return validator;
}

validator_t* catzilla_create_string_validator(int min_len, int max_len, const char* pattern) {
    validator_t* validator = catzilla_create_validator(TYPE_STRING);
    if (!validator) return NULL;

    validator->string_validator.min_len = min_len;
    validator->string_validator.max_len = max_len;
    validator->string_validator.has_min_len = (min_len >= 0);
    validator->string_validator.has_max_len = (max_len >= 0);
    validator->string_validator.has_pattern = 0;

    if (pattern && strlen(pattern) > 0) {
        validator->string_validator.pattern = catzilla_cache_alloc(strlen(pattern) + 1);
        if (validator->string_validator.pattern) {
            strcpy(validator->string_validator.pattern, pattern);
            validator->string_validator.has_pattern = 1;

            // Compile regex for performance
            validator->string_validator.compiled_regex = catzilla_cache_alloc(sizeof(regex_t));
            if (validator->string_validator.compiled_regex) {
                int result = regcomp(validator->string_validator.compiled_regex, pattern, REG_EXTENDED);
                if (result != 0) {
                    // Failed to compile regex, disable pattern matching
                    catzilla_cache_free(validator->string_validator.compiled_regex);
                    validator->string_validator.compiled_regex = NULL;
                    validator->string_validator.has_pattern = 0;
                }
            }
        }
    }

    return validator;
}

validator_t* catzilla_create_list_validator(validator_t* item_validator, int min_items, int max_items) {
    validator_t* validator = catzilla_create_validator(TYPE_LIST);
    if (!validator) return NULL;

    validator->list_validator.item_validator = item_validator;
    validator->list_validator.min_items = min_items;
    validator->list_validator.max_items = max_items;
    validator->list_validator.has_min_items = (min_items >= 0);
    validator->list_validator.has_max_items = (max_items >= 0);

    return validator;
}

validator_t* catzilla_create_optional_validator(validator_t* inner_validator) {
    validator_t* validator = catzilla_create_validator(TYPE_OPTIONAL);
    if (!validator) return NULL;

    validator->optional_validator.inner_validator = inner_validator;

    return validator;
}

void catzilla_free_validator(validator_t* validator) {
    if (!validator) return;

    switch (validator->type) {
        case TYPE_STRING:
            if (validator->string_validator.pattern) {
                catzilla_cache_free(validator->string_validator.pattern);
            }
            if (validator->string_validator.compiled_regex) {
                regfree(validator->string_validator.compiled_regex);
                catzilla_cache_free(validator->string_validator.compiled_regex);
            }
            break;

        case TYPE_LIST:
            if (validator->list_validator.item_validator) {
                catzilla_free_validator(validator->list_validator.item_validator);
            }
            break;

        case TYPE_OPTIONAL:
            if (validator->optional_validator.inner_validator) {
                catzilla_free_validator(validator->optional_validator.inner_validator);
            }
            break;

        case TYPE_UNION:
            if (validator->union_validator.validators) {
                for (int i = 0; i < validator->union_validator.validator_count; i++) {
                    catzilla_free_validator(validator->union_validator.validators[i]);
                }
                catzilla_cache_free(validator->union_validator.validators);
            }
            break;

        default:
            break;
    }

    if (validator->default_value) {
        catzilla_cache_free(validator->default_value);
    }

    catzilla_cache_free(validator);
}

// ============================================================================
// MODEL SPECIFICATION FUNCTIONS
// ============================================================================

model_spec_t* catzilla_create_model_spec(const char* model_name, int field_count) {
    model_spec_t* model = catzilla_cache_alloc(sizeof(model_spec_t));
    if (!model) return NULL;

    memset(model, 0, sizeof(model_spec_t));

    if (model_name) {
        model->model_name = catzilla_cache_alloc(strlen(model_name) + 1);
        if (model->model_name) {
            strcpy(model->model_name, model_name);
        }
    }

    if (field_count > 0) {
        model->fields = catzilla_cache_alloc(sizeof(field_spec_t) * field_count);
        if (!model->fields) {
            catzilla_cache_free(model);
            return NULL;
        }
        memset(model->fields, 0, sizeof(field_spec_t) * field_count);
    }

    model->field_count = field_count;
    model->fields_added = 0;  // Initialize fields_added counter
    model->compiled = 0;

    return model;
}

int catzilla_add_field_spec(model_spec_t* model, const char* field_name,
                           validator_t* validator, int required, void* default_value) {
    if (!model || !field_name || !validator) {
        return -1;
    }

    // printf("[DEBUG] catzilla_add_field_spec: model=%p, fields_added=%d, field_count=%d\n",
    //        model, model->fields_added, model->field_count);
    // fflush(stdout);

    // Check if we have space for more fields
    if (model->fields_added >= model->field_count) {
        // printf("[DEBUG] catzilla_add_field_spec: No space for more fields\n");
        // fflush(stdout);
        return -1;
    }

    int field_index = model->fields_added;
    // printf("[DEBUG] catzilla_add_field_spec: field_index=%d\n", field_index);
    // fflush(stdout);

    field_spec_t* field = &model->fields[field_index];
    // printf("[DEBUG] catzilla_add_field_spec: field pointer=%p\n", field);
    // fflush(stdout);

    // printf("[DEBUG] catzilla_add_field_spec: About to allocate memory for field name\n");
    // fflush(stdout);

    field->field_name = catzilla_cache_alloc(strlen(field_name) + 1);
    if (!field->field_name) {
        // printf("[DEBUG] catzilla_add_field_spec: Failed to allocate field name\n");
        // fflush(stdout);
        return -1;
    }

    // printf("[DEBUG] catzilla_add_field_spec: About to copy field name\n");
    // fflush(stdout);

    strcpy(field->field_name, field_name);

    // printf("[DEBUG] catzilla_add_field_spec: About to set validator\n");
    // fflush(stdout);

    field->validator = validator;
    field->required = required;
    field->default_value = default_value;

    // printf("[DEBUG] catzilla_add_field_spec: About to increment fields_added\n");
    // fflush(stdout);

    model->fields_added++;  // Increment the counter

    // printf("[DEBUG] catzilla_add_field_spec: Successfully added field, returning %d\n", field_index);
    // fflush(stdout);

    return field_index;
}

int catzilla_compile_model_spec(model_spec_t* model) {
    // printf("[DEBUG] catzilla_compile_model_spec: Starting compilation\n");
    // fflush(stdout);

    if (!model) {
        // printf("[DEBUG] catzilla_compile_model_spec: Model is NULL\n");
        // fflush(stdout);
        return -1;
    }

    // printf("[DEBUG] catzilla_compile_model_spec: Model has %d fields\n", model->fields_added);
    // fflush(stdout);

    // Optimize field access patterns
    // Sort fields by frequency of access (if we had usage data)
    // Pre-compile any complex validators

    for (int i = 0; i < model->fields_added; i++) {
        // printf("[DEBUG] catzilla_compile_model_spec: Processing field %d\n", i);
        // fflush(stdout);

        field_spec_t* field = &model->fields[i];
        // printf("[DEBUG] catzilla_compile_model_spec: Field %d - name=%s, validator=%p, required=%d\n",
        //        i, field->field_name, field->validator, field->required);
        // fflush(stdout);

        if (field->validator && field->validator->type == TYPE_STRING) {
            // printf("[DEBUG] catzilla_compile_model_spec: Processing string validator for field %d\n", i);
            // fflush(stdout);

            // Pre-compile string regex patterns for maximum performance
            if (field->validator->string_validator.has_pattern &&
                !field->validator->string_validator.compiled_regex) {
                // printf("[DEBUG] catzilla_compile_model_spec: Compiling regex for field %d\n", i);
                // fflush(stdout);

                // Compile regex if not already done
                field->validator->string_validator.compiled_regex = catzilla_cache_alloc(sizeof(regex_t));
                if (field->validator->string_validator.compiled_regex) {
                    int regex_result = regcomp(field->validator->string_validator.compiled_regex,
                           field->validator->string_validator.pattern, REG_EXTENDED);
                    if (regex_result != 0) {
                        // printf("[DEBUG] catzilla_compile_model_spec: Regex compilation failed for field %d\n", i);
                        // fflush(stdout);
                        return -1;
                    }
                    // printf("[DEBUG] catzilla_compile_model_spec: Regex compilation successful for field %d\n", i);
                    // fflush(stdout);
                }
            }
        }
    }

    // printf("[DEBUG] catzilla_compile_model_spec: Setting compiled flag\n");
    // fflush(stdout);

    model->compiled = 1;

    // printf("[DEBUG] catzilla_compile_model_spec: Compilation completed successfully\n");
    // fflush(stdout);

    return 0;
}

void catzilla_free_model_spec(model_spec_t* model) {
    if (!model) return;

    if (model->fields) {
        for (int i = 0; i < model->fields_added; i++) {
            field_spec_t* field = &model->fields[i];
            if (field->field_name) {
                catzilla_cache_free(field->field_name);
            }
            if (field->validator) {
                catzilla_free_validator(field->validator);
            }
            if (field->default_value) {
                catzilla_cache_free(field->default_value);
            }
        }
        catzilla_cache_free(model->fields);
    }

    if (model->model_name) {
        catzilla_cache_free(model->model_name);
    }

    catzilla_cache_free(model);
}

// ============================================================================
// VALIDATION CONTEXT FUNCTIONS
// ============================================================================

validation_context_t* catzilla_create_validation_context(void) {
    validation_context_t* ctx = catzilla_request_alloc(sizeof(validation_context_t));
    if (!ctx) return NULL;

    memset(ctx, 0, sizeof(validation_context_t));
    ctx->errors = NULL;
    ctx->error_count = 0;

    return ctx;
}

void catzilla_free_validation_context(validation_context_t* ctx) {
    if (!ctx) return;

    // Free all validation errors
    validation_error_t* error = ctx->errors;
    while (error) {
        validation_error_t* next = error->next;
        if (error->field_name) catzilla_request_free(error->field_name);
        if (error->message) catzilla_request_free(error->message);
        catzilla_request_free(error);
        error = next;
    }

    catzilla_request_free(ctx);
}

// ============================================================================
// CORE VALIDATION FUNCTIONS
// ============================================================================

validation_result_t catzilla_validate_value(validator_t* validator, json_object_t* value,
                                           validation_context_t* ctx) {
    if (!validator || !value) return VALIDATION_ERROR_TYPE;

    struct timespec start_time, end_time;
    clock_gettime(CLOCK_MONOTONIC, &start_time);

    validation_result_t result = VALIDATION_SUCCESS;

    // Handle optional values
    if (validator->type == TYPE_OPTIONAL) {
        if (value->type == JSON_NULL) {
            // NULL is valid for optional fields
            result = VALIDATION_SUCCESS;
            goto validation_complete;
        } else {
            // Validate the inner type
            result = catzilla_validate_value(validator->optional_validator.inner_validator, value, ctx);
            goto validation_complete;
        }
    }

    // Type-specific validation
    switch (validator->type) {
        case TYPE_INT:
            if (value->type != JSON_INT) {
                result = VALIDATION_ERROR_TYPE;
                break;
            }

            if (validator->int_validator.has_min && value->int_val < validator->int_validator.min) {
                result = VALIDATION_ERROR_RANGE;
                break;
            }

            if (validator->int_validator.has_max && value->int_val > validator->int_validator.max) {
                result = VALIDATION_ERROR_RANGE;
                break;
            }
            break;

        case TYPE_FLOAT:
            if (value->type != JSON_FLOAT && value->type != JSON_INT) {
                result = VALIDATION_ERROR_TYPE;
                break;
            }

            double val = (value->type == JSON_FLOAT) ? value->float_val : (double)value->int_val;

            if (validator->float_validator.has_min && val < validator->float_validator.min) {
                result = VALIDATION_ERROR_RANGE;
                break;
            }

            if (validator->float_validator.has_max && val > validator->float_validator.max) {
                result = VALIDATION_ERROR_RANGE;
                break;
            }
            break;

        case TYPE_STRING:
            if (value->type != JSON_STRING) {
                result = VALIDATION_ERROR_TYPE;
                break;
            }

            int len = strlen(value->string_val);

            if (validator->string_validator.has_min_len && len < validator->string_validator.min_len) {
                result = VALIDATION_ERROR_LENGTH;
                break;
            }

            if (validator->string_validator.has_max_len && len > validator->string_validator.max_len) {
                result = VALIDATION_ERROR_LENGTH;
                break;
            }

            if (validator->string_validator.has_pattern && validator->string_validator.compiled_regex) {
                int match_result = regexec(validator->string_validator.compiled_regex,
                                         value->string_val, 0, NULL, 0);
                if (match_result != 0) {
                    result = VALIDATION_ERROR_PATTERN;
                    break;
                }
            }
            break;

        case TYPE_BOOL:
            if (value->type != JSON_BOOL) {
                result = VALIDATION_ERROR_TYPE;
                break;
            }
            break;

        case TYPE_LIST:
            if (value->type != JSON_ARRAY) {
                result = VALIDATION_ERROR_TYPE;
                break;
            }

            if (validator->list_validator.has_min_items &&
                value->array_val.count < validator->list_validator.min_items) {
                result = VALIDATION_ERROR_LENGTH;
                break;
            }

            if (validator->list_validator.has_max_items &&
                value->array_val.count > validator->list_validator.max_items) {
                result = VALIDATION_ERROR_LENGTH;
                break;
            }

            // Validate each item if item validator is specified
            if (validator->list_validator.item_validator) {
                for (int i = 0; i < value->array_val.count; i++) {
                    validation_result_t item_result = catzilla_validate_value(
                        validator->list_validator.item_validator,
                        value->array_val.items[i], ctx);
                    if (item_result != VALIDATION_SUCCESS) {
                        result = item_result;
                        break;
                    }
                }
            }
            break;

        default:
            result = VALIDATION_ERROR_TYPE;
            break;
    }

    // Custom validator
    if (result == VALIDATION_SUCCESS && validator->custom_validator) {
        validation_error_t* custom_error = NULL;
        int custom_result = validator->custom_validator(value, &custom_error);
        if (custom_result != 0) {
            result = VALIDATION_ERROR_CUSTOM;
            if (custom_error && ctx) {
                // Add custom error to context
                custom_error->next = ctx->errors;
                ctx->errors = custom_error;
                ctx->error_count++;
            }
        }
    }

validation_complete:
    // Update performance statistics
    clock_gettime(CLOCK_MONOTONIC, &end_time);
    long ns = (end_time.tv_sec - start_time.tv_sec) * 1000000000L +
              (end_time.tv_nsec - start_time.tv_nsec);

    g_validation_stats.validations_performed++;
    g_validation_stats.total_time_ns += ns;

    return result;
}

validation_result_t catzilla_validate_model(model_spec_t* model, json_object_t* data,
                                           json_object_t** validated_data,
                                           validation_context_t* ctx) {
    // printf("[DEBUG] catzilla_validate_model: Starting validation\n");
    if (!model || !data || !validated_data || !ctx) return VALIDATION_ERROR_TYPE;

    // printf("[DEBUG] model->fields_added: %d\n", model->fields_added);

    // Initialize validated_data to NULL
    *validated_data = NULL;

    // First do all validations without building result
    // This is more robust since we don't have to deal with partial objects

    if (data->type != JSON_OBJECT) {
        catzilla_add_validation_error(ctx, "", "Expected object for model validation", VALIDATION_ERROR_TYPE);
        return VALIDATION_ERROR_TYPE;
    }

    // printf("[DEBUG] Input data has %d fields\n", data->object_val.count);

    // First pass: validate all fields
    validation_result_t overall_result = VALIDATION_SUCCESS;

    for (int i = 0; i < model->fields_added; i++) {
        field_spec_t* field = &model->fields[i];
        // printf("[DEBUG] Validating field %d: %s (required: %d)\n", i, field->field_name ? field->field_name : "NULL", field->required);

        if (!field->field_name) continue;

        // Find field in input data
        json_object_t* field_value = NULL;
        for (int j = 0; j < data->object_val.count; j++) {
            if (strcmp(data->object_val.keys[j], field->field_name) == 0) {
                field_value = data->object_val.values[j];
                // printf("[DEBUG] Found field %s in input data\n", field->field_name);
                break;
            }
        }

        // Handle missing field
        if (!field_value) {
            if (field->required) {
                char error_msg[256];
                snprintf(error_msg, sizeof(error_msg), "Field '%s' is required", field->field_name);
                catzilla_add_validation_error(ctx, field->field_name, error_msg, VALIDATION_ERROR_REQUIRED);
                overall_result = VALIDATION_ERROR_REQUIRED;
            }
            continue;
        }

        // Validate field value
        // printf("[DEBUG] About to validate field %s with validator type %d\n", field->field_name, field->validator->type);
        validation_result_t field_result = VALIDATION_SUCCESS;

        // Special handling for optional fields with null values
        if (!field->required && field_value->type == JSON_NULL) {
            // Optional field with explicit null value is valid
            field_result = VALIDATION_SUCCESS;
        } else {
            // Normal validation
            field_result = catzilla_validate_value(field->validator, field_value, ctx);
        }

        // printf("[DEBUG] Field %s validation result: %d\n", field->field_name, field_result);
        if (field_result != VALIDATION_SUCCESS) {
            char error_msg[256];
            snprintf(error_msg, sizeof(error_msg), "Validation failed for field '%s'", field->field_name);
            catzilla_add_validation_error(ctx, field->field_name, error_msg, field_result);
            overall_result = field_result;
        }
    }

    // If any validation failed, don't create output object
    if (overall_result != VALIDATION_SUCCESS) {
        return overall_result;
    }

    // All validations passed, create result object
    *validated_data = catzilla_request_alloc(sizeof(json_object_t));
    if (!*validated_data) return VALIDATION_ERROR_MEMORY;

    (*validated_data)->type = JSON_OBJECT;
    (*validated_data)->object_val.count = 0;  // Will be updated as we add fields
    (*validated_data)->object_val.keys = catzilla_request_alloc(sizeof(char*) * model->fields_added);
    (*validated_data)->object_val.values = catzilla_request_alloc(sizeof(json_object_t*) * model->fields_added);

    if (!(*validated_data)->object_val.keys || !(*validated_data)->object_val.values) {
        // Clean up memory
        catzilla_free_json_object(*validated_data);
        *validated_data = NULL;
        return VALIDATION_ERROR_MEMORY;
    }

    // Now second pass: build output object (which we only do if validation succeeded)
    int validated_field_count = 0;

    // Add all fields from input
    for (int i = 0; i < model->fields_added; i++) {
        field_spec_t* field = &model->fields[i];
        if (!field->field_name) continue;

        // Find field in input data
        json_object_t* field_value = NULL;
        for (int j = 0; j < data->object_val.count; j++) {
            if (strcmp(data->object_val.keys[j], field->field_name) == 0) {
                field_value = data->object_val.values[j];
                break;
            }
        }

        // Handle missing optional fields by using default values
        if (!field_value && !field->required) {
            // Use field's default value if available
            if (field->default_value) {
                field_value = catzilla_copy_json_object((json_object_t*)field->default_value);
            } else {
                // Create default value for optional fields (None/NULL)
                field_value = catzilla_create_json_null();
            }
        }

        // This should not happen since we already validated
        if (!field_value) {
            continue;
        }

        // Add field to result
        (*validated_data)->object_val.keys[validated_field_count] = catzilla_request_alloc(strlen(field->field_name) + 1);
        if (!(*validated_data)->object_val.keys[validated_field_count]) {
            // Memory allocation failure
            catzilla_free_json_object(*validated_data);
            *validated_data = NULL;
            return VALIDATION_ERROR_MEMORY;
        }

        strcpy((*validated_data)->object_val.keys[validated_field_count], field->field_name);

        // Create a deep copy of the field value to avoid use-after-free
        (*validated_data)->object_val.values[validated_field_count] = catzilla_copy_json_object(field_value);
        if (!(*validated_data)->object_val.values[validated_field_count]) {
            // Memory allocation failure during copy
            catzilla_free_json_object(*validated_data);
            *validated_data = NULL;
            return VALIDATION_ERROR_MEMORY;
        }
        validated_field_count++;
    }

    // Update the count
    (*validated_data)->object_val.count = validated_field_count;

    return VALIDATION_SUCCESS;
}

// ============================================================================
// ERROR HANDLING FUNCTIONS
// ============================================================================

void catzilla_add_validation_error(validation_context_t* ctx, const char* field_name,
                                 const char* message, validation_result_t error_code) {
    if (!ctx) return;

    validation_error_t* error = catzilla_request_alloc(sizeof(validation_error_t));
    if (!error) return;

    error->field_name = field_name ? catzilla_request_alloc(strlen(field_name) + 1) : NULL;
    if (error->field_name && field_name) {
        strcpy(error->field_name, field_name);
    }

    error->message = message ? catzilla_request_alloc(strlen(message) + 1) : NULL;
    if (error->message && message) {
        strcpy(error->message, message);
    }

    error->error_code = error_code;
    error->next = ctx->errors;

    ctx->errors = error;
    ctx->error_count++;
}

int catzilla_has_validation_errors(validation_context_t* ctx) {
    return ctx ? (ctx->error_count > 0) : 0;
}

char* catzilla_get_validation_errors(validation_context_t* ctx) {
    if (!ctx || !ctx->errors) return NULL;

    // Calculate total size needed
    int total_size = 1;  // For null terminator
    validation_error_t* error = ctx->errors;
    while (error) {
        if (error->field_name) total_size += strlen(error->field_name) + 2;  // field + ": "
        if (error->message) total_size += strlen(error->message);
        total_size += 2;  // for "; " or "\n"
        error = error->next;
    }

    char* result = catzilla_request_alloc(total_size);
    if (!result) return NULL;

    result[0] = '\0';
    error = ctx->errors;
    while (error) {
        if (error->field_name) {
            strcat(result, error->field_name);
            strcat(result, ": ");
        }
        if (error->message) {
            strcat(result, error->message);
        }
        if (error->next) {
            strcat(result, "; ");
        }
        error = error->next;
    }

    return result;
}

void catzilla_clear_validation_errors(validation_context_t* ctx) {
    if (!ctx) return;

    validation_error_t* error = ctx->errors;
    while (error) {
        validation_error_t* next = error->next;

        if (error->field_name) {
            catzilla_request_free(error->field_name);
        }

        if (error->message) {
            catzilla_request_free(error->message);
        }

        catzilla_request_free(error);
        error = next;
    }

    ctx->errors = NULL;
    ctx->error_count = 0;
}

// ============================================================================
// PERFORMANCE AND STATISTICS
// ============================================================================

validation_stats_t* catzilla_get_validation_stats(void) {
    return &g_validation_stats;
}

void catzilla_reset_validation_stats(void) {
    memset(&g_validation_stats, 0, sizeof(validation_stats_t));
}

// ============================================================================
// JSON UTILITY FUNCTIONS
// ============================================================================

json_object_t* catzilla_create_json_object(void) {
    json_object_t* obj = catzilla_request_alloc(sizeof(json_object_t));
    if (!obj) return NULL;

    memset(obj, 0, sizeof(json_object_t));
    obj->type = JSON_OBJECT;
    obj->object_val.keys = NULL;
    obj->object_val.values = NULL;
    obj->object_val.count = 0;

    return obj;
}

json_object_t* catzilla_create_json_null(void) {
    json_object_t* obj = catzilla_request_alloc(sizeof(json_object_t));
    if (!obj) return NULL;

    memset(obj, 0, sizeof(json_object_t));
    obj->type = JSON_NULL;

    return obj;
}

json_object_t* catzilla_create_json_string(const char* str) {
    if (!str) return catzilla_create_json_null();

    json_object_t* obj = catzilla_request_alloc(sizeof(json_object_t));
    if (!obj) return NULL;

    memset(obj, 0, sizeof(json_object_t));
    obj->type = JSON_STRING;

    // Allocate and copy the string
    size_t len = strlen(str);
    obj->string_val = catzilla_request_alloc(len + 1);
    if (!obj->string_val) {
        catzilla_request_free(obj);
        return NULL;
    }
    strcpy(obj->string_val, str);

    return obj;
}

json_object_t* catzilla_create_json_number(double value) {
    json_object_t* obj = catzilla_request_alloc(sizeof(json_object_t));
    if (!obj) return NULL;

    memset(obj, 0, sizeof(json_object_t));

    // Check if the value is an integer
    if (value == (long)value) {
        obj->type = JSON_INT;
        obj->int_val = (long)value;
    } else {
        obj->type = JSON_FLOAT;
        obj->float_val = value;
    }

    return obj;
}

json_object_t* catzilla_create_json_int(long value) {
    json_object_t* obj = catzilla_request_alloc(sizeof(json_object_t));
    if (!obj) return NULL;

    memset(obj, 0, sizeof(json_object_t));
    obj->type = JSON_INT;
    obj->int_val = value;

    return obj;
}

json_object_t* catzilla_create_json_bool(int value) {
    json_object_t* obj = catzilla_request_alloc(sizeof(json_object_t));
    if (!obj) return NULL;

    memset(obj, 0, sizeof(json_object_t));
    obj->type = JSON_BOOL;
    obj->bool_val = value ? 1 : 0;

    return obj;
}

json_object_t* catzilla_copy_json_object(json_object_t* obj) {
    if (!obj) return NULL;

    json_object_t* copy = catzilla_request_alloc(sizeof(json_object_t));
    if (!copy) return NULL;

    copy->type = obj->type;

    switch (obj->type) {
        case JSON_NULL:
        case JSON_BOOL:
        case JSON_INT:
        case JSON_FLOAT:
            // Simple types - just copy the value
            copy->bool_val = obj->bool_val;  // This covers all the simple union members
            copy->int_val = obj->int_val;
            copy->float_val = obj->float_val;
            break;

        case JSON_STRING:
            if (obj->string_val) {
                copy->string_val = catzilla_request_alloc(strlen(obj->string_val) + 1);
                if (copy->string_val) {
                    strcpy(copy->string_val, obj->string_val);
                } else {
                    catzilla_request_free(copy);
                    return NULL;
                }
            } else {
                copy->string_val = NULL;
            }
            break;

        case JSON_ARRAY:
            copy->array_val.count = obj->array_val.count;
            if (obj->array_val.count > 0 && obj->array_val.items) {
                copy->array_val.items = catzilla_request_alloc(sizeof(json_object_t*) * obj->array_val.count);
                if (!copy->array_val.items) {
                    catzilla_request_free(copy);
                    return NULL;
                }
                for (int i = 0; i < obj->array_val.count; i++) {
                    copy->array_val.items[i] = catzilla_copy_json_object(obj->array_val.items[i]);
                    if (!copy->array_val.items[i]) {
                        // Clean up partial copy
                        for (int j = 0; j < i; j++) {
                            catzilla_free_json_object(copy->array_val.items[j]);
                        }
                        catzilla_request_free(copy->array_val.items);
                        catzilla_request_free(copy);
                        return NULL;
                    }
                }
            } else {
                copy->array_val.items = NULL;
            }
            break;

        case JSON_OBJECT:
            copy->object_val.count = obj->object_val.count;
            if (obj->object_val.count > 0) {
                // Copy keys
                copy->object_val.keys = catzilla_request_alloc(sizeof(char*) * obj->object_val.count);
                if (!copy->object_val.keys) {
                    catzilla_request_free(copy);
                    return NULL;
                }

                // Copy values
                copy->object_val.values = catzilla_request_alloc(sizeof(json_object_t*) * obj->object_val.count);
                if (!copy->object_val.values) {
                    catzilla_request_free(copy->object_val.keys);
                    catzilla_request_free(copy);
                    return NULL;
                }

                for (int i = 0; i < obj->object_val.count; i++) {
                    // Copy key
                    if (obj->object_val.keys[i]) {
                        copy->object_val.keys[i] = catzilla_request_alloc(strlen(obj->object_val.keys[i]) + 1);
                        if (copy->object_val.keys[i]) {
                            strcpy(copy->object_val.keys[i], obj->object_val.keys[i]);
                        } else {
                            // Clean up partial copy
                            for (int j = 0; j < i; j++) {
                                if (copy->object_val.keys[j]) catzilla_request_free(copy->object_val.keys[j]);
                                catzilla_free_json_object(copy->object_val.values[j]);
                            }
                            catzilla_request_free(copy->object_val.keys);
                            catzilla_request_free(copy->object_val.values);
                            catzilla_request_free(copy);
                            return NULL;
                        }
                    } else {
                        copy->object_val.keys[i] = NULL;
                    }

                    // Copy value
                    copy->object_val.values[i] = catzilla_copy_json_object(obj->object_val.values[i]);
                    if (!copy->object_val.values[i]) {
                        // Clean up partial copy
                        for (int j = 0; j <= i; j++) {
                            if (copy->object_val.keys[j]) catzilla_request_free(copy->object_val.keys[j]);
                        }
                        for (int j = 0; j < i; j++) {
                            catzilla_free_json_object(copy->object_val.values[j]);
                        }
                        catzilla_request_free(copy->object_val.keys);
                        catzilla_request_free(copy->object_val.values);
                        catzilla_request_free(copy);
                        return NULL;
                    }
                }
            } else {
                copy->object_val.keys = NULL;
                copy->object_val.values = NULL;
            }
            break;

        default:
            catzilla_request_free(copy);
            return NULL;
    }

    return copy;
}

void catzilla_free_json_object(json_object_t* obj) {
    if (!obj) return;

    switch (obj->type) {
        case JSON_STRING:
            if (obj->string_val) catzilla_request_free(obj->string_val);
            break;
        case JSON_ARRAY:
            if (obj->array_val.items) {
                for (int i = 0; i < obj->array_val.count; i++) {
                    catzilla_free_json_object(obj->array_val.items[i]);
                }
                catzilla_request_free(obj->array_val.items);
            }
            break;
        case JSON_OBJECT:
            if (obj->object_val.keys) {
                for (int i = 0; i < obj->object_val.count; i++) {
                    if (obj->object_val.keys[i]) catzilla_request_free(obj->object_val.keys[i]);
                }
                catzilla_request_free(obj->object_val.keys);
            }
            if (obj->object_val.values) {
                for (int i = 0; i < obj->object_val.count; i++) {
                    catzilla_free_json_object(obj->object_val.values[i]);
                }
                catzilla_request_free(obj->object_val.values);
            }
            break;
        default:
            break;
    }

    catzilla_request_free(obj);
}

// ============================================================================
// JSON MANIPULATION FUNCTIONS
// ============================================================================

static int catzilla_json_resize_object(json_object_t* obj, int new_count) {
    if (obj->type != JSON_OBJECT) return -1;

    // Reallocate keys array - handle NULL case for first allocation
    char** new_keys;
    if (obj->object_val.keys == NULL) {
        new_keys = catzilla_request_alloc(sizeof(char*) * new_count);
    } else {
        new_keys = catzilla_request_realloc(obj->object_val.keys, sizeof(char*) * new_count);
    }
    if (!new_keys) return -1;
    obj->object_val.keys = new_keys;

    // Reallocate values array - handle NULL case for first allocation
    json_object_t** new_values;
    if (obj->object_val.values == NULL) {
        new_values = catzilla_request_alloc(sizeof(json_object_t*) * new_count);
    } else {
        new_values = catzilla_request_realloc(obj->object_val.values, sizeof(json_object_t*) * new_count);
    }
    if (!new_values) return -1;
    obj->object_val.values = new_values;

    return 0;
}

static int catzilla_json_find_key(json_object_t* obj, const char* key) {
    if (obj->type != JSON_OBJECT || !key) return -1;

    for (int i = 0; i < obj->object_val.count; i++) {
        if (obj->object_val.keys[i] && strcmp(obj->object_val.keys[i], key) == 0) {
            return i;
        }
    }
    return -1;
}

int catzilla_json_add_string(json_object_t* obj, const char* key, const char* value) {
    if (!obj || !key || obj->type != JSON_OBJECT) return -1;

    // Check if key already exists
    int existing_index = catzilla_json_find_key(obj, key);
    if (existing_index >= 0) {
        // Replace existing value
        catzilla_free_json_object(obj->object_val.values[existing_index]);
        obj->object_val.values[existing_index] = catzilla_create_json_string(value);
        return obj->object_val.values[existing_index] ? 0 : -1;
    }

    // Add new key-value pair
    if (catzilla_json_resize_object(obj, obj->object_val.count + 1) != 0) return -1;

    // Allocate and copy key
    size_t key_len = strlen(key);
    obj->object_val.keys[obj->object_val.count] = catzilla_request_alloc(key_len + 1);
    if (!obj->object_val.keys[obj->object_val.count]) return -1;
    strcpy(obj->object_val.keys[obj->object_val.count], key);

    // Create value
    obj->object_val.values[obj->object_val.count] = catzilla_create_json_string(value);
    if (!obj->object_val.values[obj->object_val.count]) {
        catzilla_request_free(obj->object_val.keys[obj->object_val.count]);
        return -1;
    }

    obj->object_val.count++;
    return 0;
}

int catzilla_json_add_int(json_object_t* obj, const char* key, long value) {
    if (!obj || !key || obj->type != JSON_OBJECT) return -1;

    // Check if key already exists
    int existing_index = catzilla_json_find_key(obj, key);
    if (existing_index >= 0) {
        // Replace existing value
        catzilla_free_json_object(obj->object_val.values[existing_index]);
        obj->object_val.values[existing_index] = catzilla_create_json_int(value);
        return obj->object_val.values[existing_index] ? 0 : -1;
    }

    // Add new key-value pair
    if (catzilla_json_resize_object(obj, obj->object_val.count + 1) != 0) return -1;

    // Allocate and copy key
    size_t key_len = strlen(key);
    obj->object_val.keys[obj->object_val.count] = catzilla_request_alloc(key_len + 1);
    if (!obj->object_val.keys[obj->object_val.count]) return -1;
    strcpy(obj->object_val.keys[obj->object_val.count], key);

    // Create value
    obj->object_val.values[obj->object_val.count] = catzilla_create_json_int(value);
    if (!obj->object_val.values[obj->object_val.count]) {
        catzilla_request_free(obj->object_val.keys[obj->object_val.count]);
        return -1;
    }

    obj->object_val.count++;
    return 0;
}

int catzilla_json_add_bool(json_object_t* obj, const char* key, int value) {
    if (!obj || !key || obj->type != JSON_OBJECT) return -1;

    // Check if key already exists
    int existing_index = catzilla_json_find_key(obj, key);
    if (existing_index >= 0) {
        // Replace existing value
        catzilla_free_json_object(obj->object_val.values[existing_index]);
        obj->object_val.values[existing_index] = catzilla_create_json_bool(value);
        return obj->object_val.values[existing_index] ? 0 : -1;
    }

    // Add new key-value pair
    if (catzilla_json_resize_object(obj, obj->object_val.count + 1) != 0) return -1;

    // Allocate and copy key
    size_t key_len = strlen(key);
    obj->object_val.keys[obj->object_val.count] = catzilla_request_alloc(key_len + 1);
    if (!obj->object_val.keys[obj->object_val.count]) return -1;
    strcpy(obj->object_val.keys[obj->object_val.count], key);

    // Create value
    obj->object_val.values[obj->object_val.count] = catzilla_create_json_bool(value);
    if (!obj->object_val.values[obj->object_val.count]) {
        catzilla_request_free(obj->object_val.keys[obj->object_val.count]);
        return -1;
    }

    obj->object_val.count++;
    return 0;
}

int catzilla_json_add_null(json_object_t* obj, const char* key) {
    if (!obj || !key || obj->type != JSON_OBJECT) return -1;

    // Check if key already exists
    int existing_index = catzilla_json_find_key(obj, key);
    if (existing_index >= 0) {
        // Replace existing value
        catzilla_free_json_object(obj->object_val.values[existing_index]);
        obj->object_val.values[existing_index] = catzilla_create_json_null();
        return obj->object_val.values[existing_index] ? 0 : -1;
    }

    // Add new key-value pair
    if (catzilla_json_resize_object(obj, obj->object_val.count + 1) != 0) return -1;

    // Allocate and copy key
    size_t key_len = strlen(key);
    obj->object_val.keys[obj->object_val.count] = catzilla_request_alloc(key_len + 1);
    if (!obj->object_val.keys[obj->object_val.count]) return -1;
    strcpy(obj->object_val.keys[obj->object_val.count], key);

    // Create value
    obj->object_val.values[obj->object_val.count] = catzilla_create_json_null();
    if (!obj->object_val.values[obj->object_val.count]) {
        catzilla_request_free(obj->object_val.keys[obj->object_val.count]);
        return -1;
    }

    obj->object_val.count++;
    return 0;
}

char* catzilla_json_get_string(json_object_t* obj, const char* key) {
    if (!obj || !key || obj->type != JSON_OBJECT) return NULL;

    int index = catzilla_json_find_key(obj, key);
    if (index < 0) return NULL;

    json_object_t* value = obj->object_val.values[index];
    if (!value || value->type != JSON_STRING) return NULL;

    return value->string_val;
}

long catzilla_json_get_int(json_object_t* obj, const char* key) {
    if (!obj || !key || obj->type != JSON_OBJECT) return 0;

    int index = catzilla_json_find_key(obj, key);
    if (index < 0) return 0;

    json_object_t* value = obj->object_val.values[index];
    if (!value || value->type != JSON_INT) return 0;

    return value->int_val;
}

int catzilla_json_get_bool(json_object_t* obj, const char* key) {
    if (!obj || !key || obj->type != JSON_OBJECT) return 0;

    int index = catzilla_json_find_key(obj, key);
    if (index < 0) return 0;

    json_object_t* value = obj->object_val.values[index];
    if (!value || value->type != JSON_BOOL) return 0;

    return value->bool_val;
}
