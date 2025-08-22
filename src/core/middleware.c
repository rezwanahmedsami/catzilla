#include "middleware.h"
#include "platform_compat.h"
#include "memory.h"
#include "dependency.h"
#include <string.h>
#ifndef _WIN32
#include <strings.h>  // For strcasecmp on POSIX systems
#endif
#include <stdlib.h>
#include <stdio.h>
#include <time.h>

#ifdef _WIN32
#include "windows_compat.h"
#endif

// ============================================================================
// 🌪️ CATZILLA ZERO-ALLOCATION MIDDLEWARE SYSTEM - CORE IMPLEMENTATION
// ============================================================================

/**
 * Internal utility to get high-resolution timestamp
 */
static uint64_t get_timestamp_ns(void) {
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return (uint64_t)ts.tv_sec * 1000000000ULL + (uint64_t)ts.tv_nsec;
}

/**
 * Compare middleware registrations for sorting by priority
 */
static int compare_middleware_priority(const void* a, const void* b) {
    const catzilla_middleware_registration_t* mid_a = *(const catzilla_middleware_registration_t**)a;
    const catzilla_middleware_registration_t* mid_b = *(const catzilla_middleware_registration_t**)b;

    if (mid_a->priority < mid_b->priority) return -1;
    if (mid_a->priority > mid_b->priority) return 1;
    return 0;
}

// ============================================================================
// CORE MIDDLEWARE ENGINE IMPLEMENTATION
// ============================================================================

int catzilla_middleware_chain_init(catzilla_middleware_chain_t* chain) {
    if (!chain) return -1;

    // Initialize chain structure
    memset(chain, 0, sizeof(catzilla_middleware_chain_t));

    // Initialize performance metrics
    chain->fastest_execution_ns = UINT64_MAX;
    chain->slowest_execution_ns = 0;

    return 0;
}

catzilla_middleware_chain_t* catzilla_middleware_create_chain(void) {
    catzilla_middleware_chain_t* chain = catzilla_malloc(sizeof(catzilla_middleware_chain_t));
    if (!chain) return NULL;

    if (catzilla_middleware_chain_init(chain) != 0) {
        catzilla_free(chain);
        return NULL;
    }

    return chain;
}

void catzilla_middleware_destroy_chain(catzilla_middleware_chain_t* chain) {
    if (!chain) return;

    // Free middleware registrations
    for (int i = 0; i < chain->middleware_count; i++) {
        if (chain->middlewares[i]) {
            catzilla_free(chain->middlewares[i]);
        }
    }

    // Free execution chains
    if (chain->pre_route_chain) catzilla_free(chain->pre_route_chain);
    if (chain->post_route_chain) catzilla_free(chain->post_route_chain);
    if (chain->error_chain) catzilla_free(chain->error_chain);

    catzilla_free(chain);
}

void catzilla_middleware_chain_cleanup(catzilla_middleware_chain_t* chain) {
    if (!chain) return;

    // Free middleware registrations
    for (int i = 0; i < chain->middleware_count; i++) {
        if (chain->middlewares[i]) {
            catzilla_free(chain->middlewares[i]);
        }
    }

    // Free execution chains
    if (chain->pre_route_chain) {
        catzilla_free(chain->pre_route_chain);
    }
    if (chain->post_route_chain) {
        catzilla_free(chain->post_route_chain);
    }
    if (chain->error_chain) {
        catzilla_free(chain->error_chain);
    }

    // Clean up memory pool
    if (chain->context_pool) {
        catzilla_di_destroy_memory_pool(chain->context_pool);
    }

    memset(chain, 0, sizeof(catzilla_middleware_chain_t));
}

int catzilla_middleware_register(catzilla_middleware_chain_t* chain,
                                catzilla_middleware_fn_t middleware_fn,
                                const char* name,
                                uint32_t priority,
                                uint32_t flags) {
    if (!chain || !middleware_fn || !name) return -1;

    if (chain->middleware_count >= CATZILLA_MAX_MIDDLEWARES) {
        return -1; // Too many middleware
    }

    // Allocate new middleware registration
    catzilla_middleware_registration_t* registration =
        catzilla_malloc(sizeof(catzilla_middleware_registration_t));

    if (!registration) return -1;

    // Initialize registration
    registration->c_function = middleware_fn;
    strncpy(registration->name, name, CATZILLA_MIDDLEWARE_NAME_MAX - 1);
    registration->name[CATZILLA_MIDDLEWARE_NAME_MAX - 1] = '\0';
    registration->priority = priority;
    registration->flags = flags;
    registration->python_metadata = NULL;
    registration->context_size = 0;
    registration->is_builtin = true; // Default to builtin for C middleware

    // Add to chain
    chain->middlewares[chain->middleware_count] = registration;
    chain->middleware_count++;

    // Mark chains as needing recompilation
    chain->chains_compiled = false;

    return 0;
}

int catzilla_middleware_compile_chains(catzilla_middleware_chain_t* chain) {
    if (!chain) return -1;

    if (chain->middleware_count == 0) {
        chain->chains_compiled = true;
        return 0;
    }

    // Sort middleware by priority
    qsort(chain->middlewares, chain->middleware_count,
          sizeof(catzilla_middleware_registration_t*), compare_middleware_priority);

    // Count middleware for each phase
    int pre_route_count = 0;
    int post_route_count = 0;
    int error_count = 0;

    for (int i = 0; i < chain->middleware_count; i++) {
        uint32_t flags = chain->middlewares[i]->flags;

        if (flags & CATZILLA_MIDDLEWARE_PRE_ROUTE) pre_route_count++;
        if (flags & CATZILLA_MIDDLEWARE_POST_ROUTE) post_route_count++;
        if (flags & CATZILLA_MIDDLEWARE_ERROR) error_count++;
    }

    // Allocate execution chains
    if (pre_route_count > 0) {
        chain->pre_route_chain = catzilla_malloc(sizeof(catzilla_middleware_fn_t) * pre_route_count);
        if (!chain->pre_route_chain) return -1;
    }

    if (post_route_count > 0) {
        chain->post_route_chain = catzilla_malloc(sizeof(catzilla_middleware_fn_t) * post_route_count);
        if (!chain->post_route_chain) return -1;
    }

    if (error_count > 0) {
        chain->error_chain = catzilla_malloc(sizeof(catzilla_middleware_fn_t) * error_count);
        if (!chain->error_chain) return -1;
    }

    // Build execution chains
    int pre_idx = 0, post_idx = 0, error_idx = 0;

    for (int i = 0; i < chain->middleware_count; i++) {
        catzilla_middleware_registration_t* reg = chain->middlewares[i];
        uint32_t flags = reg->flags;

        if (flags & CATZILLA_MIDDLEWARE_PRE_ROUTE) {
            chain->pre_route_chain[pre_idx++] = reg->c_function;
        }
        if (flags & CATZILLA_MIDDLEWARE_POST_ROUTE) {
            chain->post_route_chain[post_idx++] = reg->c_function;
        }
        if (flags & CATZILLA_MIDDLEWARE_ERROR) {
            chain->error_chain[error_idx++] = reg->c_function;
        }
    }

    chain->pre_route_count = pre_route_count;
    chain->post_route_count = post_route_count;
    chain->error_count = error_count;

    chain->chains_compiled = true;
    chain->last_compilation_time = get_timestamp_ns();

    return 0;
}

int catzilla_execute_middleware_chain(catzilla_middleware_chain_t* chain,
                                     catzilla_request_t* request,
                                     catzilla_route_match_t* route_match,
                                     catzilla_di_container_t* di_container) {
    if (!chain || !request) return -1;

    // Compile chains if needed
    if (!chain->chains_compiled) {
        if (catzilla_middleware_compile_chains(chain) != 0) {
            return -1;
        }
    }

    uint64_t start_time = get_timestamp_ns();

    // Allocate middleware context from specialized pool
    catzilla_middleware_context_t* ctx =
        catzilla_di_pool_alloc(chain->context_pool, sizeof(catzilla_middleware_context_t));

    if (!ctx) return -1;

    // Initialize context (zero-copy where possible)
    memset(ctx, 0, sizeof(catzilla_middleware_context_t));
    ctx->request = request;                 // Zero-copy reference
    ctx->route_match = route_match;         // Zero-copy reference
    ctx->di_container = di_container;
    ctx->should_continue = true;
    ctx->should_skip_route = false;
    ctx->response_status = 200;
    ctx->execution_start_time = start_time;

    // Create DI context if container is provided
    if (di_container) {
        ctx->di_context = catzilla_di_create_context(di_container);
    }

    int result = 0;

    // Execute pre-route middleware chain
    for (int i = 0; i < chain->pre_route_count && ctx->should_continue; i++) {
        ctx->current_middleware_index = i;

        uint64_t middleware_start = get_timestamp_ns();
        int middleware_result = chain->pre_route_chain[i](ctx);
        ctx->middleware_timings[i] = get_timestamp_ns() - middleware_start;

        if (middleware_result != CATZILLA_MIDDLEWARE_CONTINUE) {
            if (middleware_result == CATZILLA_MIDDLEWARE_SKIP_ROUTE) {
                ctx->should_skip_route = true;
                break;
            } else if (middleware_result == CATZILLA_MIDDLEWARE_STOP) {
                ctx->should_continue = false;
                break;
            } else if (middleware_result == CATZILLA_MIDDLEWARE_ERROR_CODE) {
                result = -1;
                goto cleanup;
            }
        }
    }

    // Execute route handler (if not skipped by middleware)
    // Note: Route handler execution would be integrated with existing router system

    // Execute post-route middleware chain (always execute, even if route was skipped)
    for (int i = 0; i < chain->post_route_count; i++) {
        ctx->current_middleware_index = chain->pre_route_count + i;

        uint64_t middleware_start = get_timestamp_ns();
        int middleware_result = chain->post_route_chain[i](ctx);
        ctx->middleware_timings[chain->pre_route_count + i] = get_timestamp_ns() - middleware_start;

        // Post-route middleware can't stop execution, but can modify response
        if (middleware_result == CATZILLA_MIDDLEWARE_ERROR_CODE) {
            result = -1;
            // Continue executing remaining post-route middleware
        }
    }

cleanup:
    // Update performance metrics
    chain->total_executions++;
    uint64_t total_time = get_timestamp_ns() - start_time;
    chain->total_execution_time_ns += total_time;

    if (total_time < chain->fastest_execution_ns) {
        chain->fastest_execution_ns = total_time;
    }
    if (total_time > chain->slowest_execution_ns) {
        chain->slowest_execution_ns = total_time;
    }

    // Clean up DI context if created
    if (ctx->di_context && di_container) {
        catzilla_di_cleanup_context(ctx->di_context);
    }

    // Clean up context memory
    catzilla_di_pool_free(chain->context_pool, ctx);

    return result;
}

int catzilla_middleware_get_stats(catzilla_middleware_chain_t* chain,
                                 catzilla_middleware_stats_t* stats,
                                 int max_stats) {
    if (!chain || !stats) return 0;

    int stats_count = 0;
    for (int i = 0; i < chain->middleware_count && stats_count < max_stats; i++) {
        catzilla_middleware_registration_t* reg = chain->middlewares[i];
        catzilla_middleware_stats_t* stat = &stats[stats_count];

        strncpy(stat->name, reg->name, CATZILLA_MIDDLEWARE_NAME_MAX - 1);
        stat->name[CATZILLA_MIDDLEWARE_NAME_MAX - 1] = '\0';

        // Basic stats (would be enhanced with per-middleware tracking)
        stat->execution_count = chain->total_executions;
        stat->total_time_ns = chain->total_execution_time_ns / chain->middleware_count;
        stat->average_time_ns = stat->total_time_ns / (stat->execution_count > 0 ? stat->execution_count : 1);
        stat->min_time_ns = chain->fastest_execution_ns;
        stat->max_time_ns = chain->slowest_execution_ns;
        stat->cpu_usage_percent = 0.0; // Would be calculated based on system metrics

        stats_count++;
    }

    return stats_count;
}

void catzilla_middleware_reset_stats(catzilla_middleware_chain_t* chain) {
    if (!chain) return;

    chain->total_executions = 0;
    chain->total_execution_time_ns = 0;
    chain->fastest_execution_ns = UINT64_MAX;
    chain->slowest_execution_ns = 0;
}

// ============================================================================
// MIDDLEWARE CONTEXT UTILITIES
// ============================================================================

void catzilla_middleware_set_status(catzilla_middleware_context_t* ctx, int status) {
    if (ctx) {
        ctx->response_status = status;
    }
}

int catzilla_middleware_set_header(catzilla_middleware_context_t* ctx,
                                  const char* name,
                                  const char* value) {
    if (!ctx || !name || !value) return -1;

    if (ctx->response_header_count >= CATZILLA_MAX_RESPONSE_HEADERS) {
        return -1; // Header limit reached
    }

    catzilla_response_header_t* header = &ctx->response_headers[ctx->response_header_count];

    strncpy(header->name, name, sizeof(header->name) - 1);    header->name[sizeof(header->name) - 1] = '\0';
    strncpy(header->value, value, sizeof(header->value) - 1);
    header->value[sizeof(header->value) - 1] = '\0';

    ctx->response_header_count++;
    return 0;
}

int catzilla_middleware_set_body(catzilla_middleware_context_t* ctx,
                                const char* body,
                                const char* content_type) {
    if (!ctx || !body) return -1;

    size_t body_len = strlen(body);

    // Allocate memory for response body from response arena
    ctx->response_body = catzilla_response_alloc(body_len + 1);
    if (!ctx->response_body) return -1;

    strcpy(ctx->response_body, body);
    ctx->response_body_length = body_len;

    if (content_type) {
        ctx->response_content_type = catzilla_response_alloc(strlen(content_type) + 1);
        if (ctx->response_content_type) {
            strcpy(ctx->response_content_type, content_type);
        }
    }

    return 0;
}

const char* catzilla_middleware_get_header(catzilla_middleware_context_t* ctx,
                                          const char* name) {
    if (!ctx || !ctx->request || !name) return NULL;

    for (int i = 0; i < ctx->request->header_count; i++) {
        if (strcasecmp(ctx->request->headers[i].name, name) == 0) {
            return ctx->request->headers[i].value;
        }
    }

    return NULL;
}

void catzilla_middleware_set_error(catzilla_middleware_context_t* ctx,
                                  int status,
                                  const char* message) {
    if (!ctx) return;

    ctx->response_status = status;
    ctx->error_code = status;

    if (message) {
        size_t msg_len = strlen(message);
        // Allocate memory for error message from context pool
        ctx->error_message = catzilla_malloc(msg_len + 1);
        if (ctx->error_message) {
            strcpy(ctx->error_message, message);
        }
    }
}

void catzilla_middleware_set_data(catzilla_middleware_context_t* ctx,
                                 int middleware_index,
                                 void* data) {
    if (ctx && middleware_index >= 0 && middleware_index < CATZILLA_MAX_MIDDLEWARES) {
        ctx->middleware_data[middleware_index] = data;
    }
}

void* catzilla_middleware_get_data(catzilla_middleware_context_t* ctx,
                                  int middleware_index) {
    if (ctx && middleware_index >= 0 && middleware_index < CATZILLA_MAX_MIDDLEWARES) {
        return ctx->middleware_data[middleware_index];
    }
    return NULL;
}

// ============================================================================
// DI INTEGRATION FOR MIDDLEWARE
// ============================================================================

int catzilla_middleware_resolve_dependency(catzilla_middleware_context_t* ctx,
                                         const char* service_name,
                                         void** service_instance) {
    if (!ctx || !service_name || !service_instance) return -1;

    if (!ctx->di_container) return -1;

    // Use existing DI container resolution in C
    *service_instance = catzilla_di_resolve_service(ctx->di_container, service_name, NULL);

    return (*service_instance != NULL) ? 0 : -1;
}

int catzilla_middleware_set_di_context(catzilla_middleware_context_t* ctx,
                                      const char* key,
                                      void* value) {
    if (!ctx || !key || !ctx->di_context) return -1;

    // TODO: Implement DI context value setting when API is available
    // return catzilla_di_set_context_value(ctx->di_context, key, value);
    return 0; // Success for now
}

void* catzilla_middleware_get_di_context(catzilla_middleware_context_t* ctx,
                                        const char* key) {
    if (!ctx || !key || !ctx->di_context) return NULL;

    // TODO: Implement DI context value getting when API is available
    // return catzilla_di_get_context_value(ctx->di_context, key);
    return NULL; // Not implemented yet
}

// ============================================================================
// TIMING UTILITIES
// ============================================================================

uint64_t catzilla_middleware_get_timestamp(void) {
    return get_timestamp_ns();
}

uint64_t catzilla_middleware_calculate_duration(uint64_t start_time, uint64_t end_time) {
    return (end_time > start_time) ? (end_time - start_time) : 0;
}

// ============================================================================
// PER-ROUTE MIDDLEWARE EXECUTION
// ============================================================================

/**
 * Execute per-route middleware chain for a specific route
 * This function provides zero-allocation execution of route-specific middleware
 *
 * @param route_middleware The per-route middleware chain to execute
 * @param ctx The middleware context for execution
 * @param di_container Optional DI container for dependency injection
 * @return 0 on success, -1 on error
 */
int catzilla_middleware_execute_per_route(catzilla_route_middleware_t* route_middleware,
                                         catzilla_middleware_context_t* ctx,
                                         catzilla_di_container_t* di_container) {
    if (!route_middleware || !ctx) {
        return -1;
    }

    // If no middleware is configured, continue with route execution
    if (route_middleware->middleware_count == 0) {
        return 0;
    }

    uint64_t start_time = get_timestamp_ns();

    // Create DI context if container is provided
    if (di_container && !ctx->di_context) {
        ctx->di_context = catzilla_di_create_context(di_container);
    }

    int result = 0;

    // Execute per-route middleware chain in priority order
    for (int i = 0; i < route_middleware->middleware_count && ctx->should_continue; i++) {
        ctx->current_middleware_index = i;

        // Get middleware function pointer
        catzilla_middleware_fn_t middleware_fn = (catzilla_middleware_fn_t)route_middleware->middleware_functions[i];
        if (!middleware_fn) {
            continue; // Skip NULL middleware functions
        }

        uint64_t middleware_start = get_timestamp_ns();
        int middleware_result = middleware_fn(ctx);

        // Track timing if we have space (avoid allocation)
        if (i < CATZILLA_MAX_MIDDLEWARE_TIMINGS) {
            ctx->middleware_timings[i] = get_timestamp_ns() - middleware_start;
        }

        // Handle middleware execution results
        if (middleware_result != CATZILLA_MIDDLEWARE_CONTINUE) {
            if (middleware_result == CATZILLA_MIDDLEWARE_SKIP_ROUTE) {
                ctx->should_skip_route = true;
                break;
            } else if (middleware_result == CATZILLA_MIDDLEWARE_STOP) {
                ctx->should_continue = false;
                break;
            } else if (middleware_result == CATZILLA_MIDDLEWARE_ERROR_CODE) {
                result = -1;
                goto cleanup;
            }
        }
    }

cleanup:
    // Update performance metrics (zero-allocation tracking)
    {
        uint64_t total_time = get_timestamp_ns() - start_time;
        if (route_middleware->middleware_count > 0) {
            // Track execution stats without allocation
            route_middleware->middleware_flags[0] |= 0x1; // Mark as executed
        }
    }

    return result;
}

/**
 * Initialize per-route middleware chain
 * Zero-allocation initialization for route-specific middleware
 *
 * @param route_middleware The middleware chain to initialize
 * @param initial_capacity Initial capacity for middleware functions
 * @return 0 on success, -1 on error
 */
int catzilla_route_middleware_init(catzilla_route_middleware_t* route_middleware, int initial_capacity) {
    if (!route_middleware) {
        return -1;
    }

    memset(route_middleware, 0, sizeof(catzilla_route_middleware_t));

    if (initial_capacity <= 0) {
        initial_capacity = 4; // Default capacity
    }

    // Allocate arrays using cache allocator for zero fragmentation
    route_middleware->middleware_functions = catzilla_cache_alloc(sizeof(void*) * initial_capacity);
    route_middleware->middleware_priorities = catzilla_cache_alloc(sizeof(uint32_t) * initial_capacity);
    route_middleware->middleware_flags = catzilla_cache_alloc(sizeof(uint32_t) * initial_capacity);

    if (!route_middleware->middleware_functions ||
        !route_middleware->middleware_priorities ||
        !route_middleware->middleware_flags) {
        catzilla_route_middleware_cleanup(route_middleware);
        return -1;
    }

    route_middleware->middleware_capacity = initial_capacity;
    route_middleware->middleware_count = 0;

    // Zero-initialize arrays
    memset(route_middleware->middleware_functions, 0, sizeof(void*) * initial_capacity);
    memset(route_middleware->middleware_priorities, 0, sizeof(uint32_t) * initial_capacity);
    memset(route_middleware->middleware_flags, 0, sizeof(uint32_t) * initial_capacity);

    return 0;
}

/**
 * Add middleware to per-route chain
 * Zero-allocation addition with priority-based ordering
 *
 * @param route_middleware The middleware chain to add to
 * @param middleware_fn The middleware function to add
 * @param priority The execution priority (lower = earlier)
 * @return 0 on success, -1 on error
 */
int catzilla_route_middleware_add(catzilla_route_middleware_t* route_middleware,
                                 catzilla_middleware_fn_t middleware_fn,
                                 uint32_t priority) {
    if (!route_middleware || !middleware_fn) {
        return -1;
    }

    // Check if we need to expand capacity
    if (route_middleware->middleware_count >= route_middleware->middleware_capacity) {
        int new_capacity = route_middleware->middleware_capacity * 2;

        // Reallocate arrays
        void** new_functions = catzilla_cache_alloc(sizeof(void*) * new_capacity);
        uint32_t* new_priorities = catzilla_cache_alloc(sizeof(uint32_t) * new_capacity);
        uint32_t* new_flags = catzilla_cache_alloc(sizeof(uint32_t) * new_capacity);

        if (!new_functions || !new_priorities || !new_flags) {
            if (new_functions) catzilla_cache_free(new_functions);
            if (new_priorities) catzilla_cache_free(new_priorities);
            if (new_flags) catzilla_cache_free(new_flags);
            return -1;
        }

        // Copy existing data
        memcpy(new_functions, route_middleware->middleware_functions,
               sizeof(void*) * route_middleware->middleware_count);
        memcpy(new_priorities, route_middleware->middleware_priorities,
               sizeof(uint32_t) * route_middleware->middleware_count);
        memcpy(new_flags, route_middleware->middleware_flags,
               sizeof(uint32_t) * route_middleware->middleware_count);

        // Free old arrays
        catzilla_cache_free(route_middleware->middleware_functions);
        catzilla_cache_free(route_middleware->middleware_priorities);
        catzilla_cache_free(route_middleware->middleware_flags);

        // Update to new arrays
        route_middleware->middleware_functions = new_functions;
        route_middleware->middleware_priorities = new_priorities;
        route_middleware->middleware_flags = new_flags;
        route_middleware->middleware_capacity = new_capacity;

        // Zero-initialize new slots
        memset(&new_functions[route_middleware->middleware_count], 0,
               sizeof(void*) * (new_capacity - route_middleware->middleware_count));
        memset(&new_priorities[route_middleware->middleware_count], 0,
               sizeof(uint32_t) * (new_capacity - route_middleware->middleware_count));
        memset(&new_flags[route_middleware->middleware_count], 0,
               sizeof(uint32_t) * (new_capacity - route_middleware->middleware_count));
    }

    // Find insertion point to maintain priority order
    int insert_pos = route_middleware->middleware_count;
    for (int i = 0; i < route_middleware->middleware_count; i++) {
        if (priority < route_middleware->middleware_priorities[i]) {
            insert_pos = i;
            break;
        }
    }

    // Shift existing middleware to make room
    if (insert_pos < route_middleware->middleware_count) {
        memmove(&route_middleware->middleware_functions[insert_pos + 1],
                &route_middleware->middleware_functions[insert_pos],
                sizeof(void*) * (route_middleware->middleware_count - insert_pos));
        memmove(&route_middleware->middleware_priorities[insert_pos + 1],
                &route_middleware->middleware_priorities[insert_pos],
                sizeof(uint32_t) * (route_middleware->middleware_count - insert_pos));
        memmove(&route_middleware->middleware_flags[insert_pos + 1],
                &route_middleware->middleware_flags[insert_pos],
                sizeof(uint32_t) * (route_middleware->middleware_count - insert_pos));
    }

    // Insert new middleware
    route_middleware->middleware_functions[insert_pos] = (void*)middleware_fn;
    route_middleware->middleware_priorities[insert_pos] = priority;
    route_middleware->middleware_flags[insert_pos] = 0; // Initialize flags
    route_middleware->middleware_count++;

    return 0;
}

/**
 * Cleanup per-route middleware chain
 * Zero-allocation cleanup that only frees the allocated arrays
 *
 * @param route_middleware The middleware chain to cleanup
 */
void catzilla_route_middleware_cleanup(catzilla_route_middleware_t* route_middleware) {
    if (!route_middleware) {
        return;
    }

    if (route_middleware->middleware_functions) {
        catzilla_cache_free(route_middleware->middleware_functions);
        route_middleware->middleware_functions = NULL;
    }

    if (route_middleware->middleware_priorities) {
        catzilla_cache_free(route_middleware->middleware_priorities);
        route_middleware->middleware_priorities = NULL;
    }

    if (route_middleware->middleware_flags) {
        catzilla_cache_free(route_middleware->middleware_flags);
        route_middleware->middleware_flags = NULL;
    }

    route_middleware->middleware_count = 0;
    route_middleware->middleware_capacity = 0;
}
