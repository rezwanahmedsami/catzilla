#ifndef CATZILLA_MIDDLEWARE_H
#define CATZILLA_MIDDLEWARE_H

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>
#include "memory.h"
#include "router.h"
#include "server.h"
#include "dependency.h"

// ============================================================================
// 🌪️ CATZILLA ZERO-ALLOCATION MIDDLEWARE SYSTEM
// ============================================================================

#define CATZILLA_MAX_MIDDLEWARES 64
#define CATZILLA_MIDDLEWARE_NAME_MAX 64
#define CATZILLA_MAX_RESPONSE_HEADERS 32
#define CATZILLA_MAX_MIDDLEWARE_TIMINGS 64

// Forward declarations
typedef struct catzilla_middleware_context_s catzilla_middleware_context_t;
typedef struct catzilla_middleware_registration_s catzilla_middleware_registration_t;
typedef struct catzilla_middleware_chain_s catzilla_middleware_chain_t;
typedef struct catzilla_request_s catzilla_request_t;

// Middleware execution flags
typedef enum {
    CATZILLA_MIDDLEWARE_PRE_ROUTE   = 1 << 0,  // Execute before route handler
    CATZILLA_MIDDLEWARE_POST_ROUTE  = 1 << 1,  // Execute after route handler
    CATZILLA_MIDDLEWARE_ERROR       = 1 << 2,  // Execute on error
    CATZILLA_MIDDLEWARE_ALWAYS      = 1 << 3   // Always execute
} catzilla_middleware_flags_t;

// Middleware execution return codes
typedef enum {
    CATZILLA_MIDDLEWARE_CONTINUE = 0,      // Continue to next middleware
    CATZILLA_MIDDLEWARE_SKIP_ROUTE = 1,    // Skip route handler
    CATZILLA_MIDDLEWARE_STOP = 2,          // Stop middleware chain
    CATZILLA_MIDDLEWARE_ERROR_CODE = -1    // Error occurred
} catzilla_middleware_result_t;

/**
 * Middleware function signature - pure C execution
 * @param ctx Middleware execution context
 * @return CATZILLA_MIDDLEWARE_* result code
 */
typedef int (*catzilla_middleware_fn_t)(catzilla_middleware_context_t* ctx);

/**
 * Response header structure
 */
typedef struct {
    char name[128];
    char value[512];
} catzilla_response_header_t;

/**
 * Middleware registration record
 */
typedef struct catzilla_middleware_registration_s {
    catzilla_middleware_fn_t c_function;       // C-compiled middleware function
    char name[CATZILLA_MIDDLEWARE_NAME_MAX];   // Middleware identifier
    uint32_t priority;                         // Execution order (lower = earlier)
    uint32_t flags;                            // Execution flags
    void* python_metadata;                     // Optional Python registration data
    size_t context_size;                       // Memory needed for middleware-specific context
    bool is_builtin;                           // True for built-in C middleware
} catzilla_middleware_registration_t;

/**
 * Global middleware chain (C-compiled)
 */
typedef struct catzilla_middleware_chain_s {
    catzilla_middleware_registration_t* middlewares[CATZILLA_MAX_MIDDLEWARES];
    int middleware_count;

    // Optimized execution chains (pre-computed)
    catzilla_middleware_fn_t* pre_route_chain;
    catzilla_middleware_fn_t* post_route_chain;
    catzilla_middleware_fn_t* error_chain;
    int pre_route_count;
    int post_route_count;
    int error_count;

    // Memory pool for middleware contexts
    catzilla_di_memory_pool_t* context_pool;

    // Performance metrics
    uint64_t total_executions;
    uint64_t total_execution_time_ns;
    uint64_t fastest_execution_ns;
    uint64_t slowest_execution_ns;

    // Chain optimization state
    bool chains_compiled;
    uint64_t last_compilation_time;
} catzilla_middleware_chain_t;

/**
 * Per-request middleware execution context
 */
typedef struct catzilla_middleware_context_s {
    // Request data (zero-copy references)
    catzilla_request_t* request;
    catzilla_route_match_t* route_match;

    // Middleware execution state
    int current_middleware_index;
    bool should_continue;
    bool should_skip_route;
    int response_status_override;

    // Memory management
    void* context_memory;                       // Arena-allocated context pool
    size_t context_size;

    // DI integration
    catzilla_di_container_t* di_container;
    void* di_context;                           // C-level DI context

    // Performance tracking
    uint64_t execution_start_time;
    uint64_t middleware_timings[CATZILLA_MAX_MIDDLEWARES];

    // Response building (if middleware handles response)
    char* response_body;
    size_t response_body_length;
    char* response_content_type;
    int response_status;

    // Response headers
    catzilla_response_header_t response_headers[CATZILLA_MAX_RESPONSE_HEADERS];
    int response_header_count;

    // Error handling
    char* error_message;
    int error_code;

    // Python bridge (for business logic fallback)
    void* python_context;                       // Only allocated if needed

    // Middleware-specific context data
    void* middleware_data[CATZILLA_MAX_MIDDLEWARES];
} catzilla_middleware_context_t;

/**
 * Middleware performance statistics
 */
typedef struct {
    char name[CATZILLA_MIDDLEWARE_NAME_MAX];
    uint64_t execution_count;
    uint64_t total_time_ns;
    uint64_t average_time_ns;
    uint64_t min_time_ns;
    uint64_t max_time_ns;
    double cpu_usage_percent;
} catzilla_middleware_stats_t;

// ============================================================================
// CORE MIDDLEWARE ENGINE FUNCTIONS
// ============================================================================

/**
 * Initialize a new middleware chain
 * @param chain Pointer to middleware chain structure
 * @return 0 on success, -1 on failure
 */
int catzilla_middleware_chain_init(catzilla_middleware_chain_t* chain);

/**
 * Create a new middleware chain
 * @return Pointer to new middleware chain or NULL on failure
 */
catzilla_middleware_chain_t* catzilla_middleware_create_chain(void);

/**
 * Destroy middleware chain and free all resources
 * @param chain Pointer to middleware chain
 */
void catzilla_middleware_destroy_chain(catzilla_middleware_chain_t* chain);

/**
 * Clean up middleware chain resources
 * @param chain Pointer to middleware chain structure
 */
void catzilla_middleware_chain_cleanup(catzilla_middleware_chain_t* chain);

/**
 * Register a middleware with the chain
 * @param chain Middleware chain
 * @param middleware_fn C middleware function
 * @param name Middleware name
 * @param priority Execution priority (lower = earlier)
 * @param flags Execution flags
 * @return 0 on success, -1 on failure
 */
int catzilla_middleware_register(catzilla_middleware_chain_t* chain,
                                catzilla_middleware_fn_t middleware_fn,
                                const char* name,
                                uint32_t priority,
                                uint32_t flags);

/**
 * Compile middleware chains for optimized execution
 * @param chain Middleware chain
 * @return 0 on success, -1 on failure
 */
int catzilla_middleware_compile_chains(catzilla_middleware_chain_t* chain);

/**
 * Execute middleware chain for a request
 * @param chain Middleware chain
 * @param request Request object
 * @param route_match Route match result
 * @param di_container DI container
 * @return 0 on success, -1 on error
 */
int catzilla_execute_middleware_chain(catzilla_middleware_chain_t* chain,
                                     catzilla_request_t* request,
                                     catzilla_route_match_t* route_match,
                                     catzilla_di_container_t* di_container);

/**
 * Get middleware execution statistics
 * @param chain Middleware chain
 * @param stats Output array for statistics
 * @param max_stats Maximum number of stats to return
 * @return Number of middleware stats returned
 */
int catzilla_middleware_get_stats(catzilla_middleware_chain_t* chain,
                                 catzilla_middleware_stats_t* stats,
                                 int max_stats);

/**
 * Reset middleware performance statistics
 * @param chain Middleware chain
 */
void catzilla_middleware_reset_stats(catzilla_middleware_chain_t* chain);

// ============================================================================
// MIDDLEWARE CONTEXT UTILITIES
// ============================================================================

/**
 * Set response status in middleware context
 * @param ctx Middleware context
 * @param status HTTP status code
 */
void catzilla_middleware_set_status(catzilla_middleware_context_t* ctx, int status);

/**
 * Set response header in middleware context
 * @param ctx Middleware context
 * @param name Header name
 * @param value Header value
 * @return 0 on success, -1 if header limit reached
 */
int catzilla_middleware_set_header(catzilla_middleware_context_t* ctx,
                                  const char* name,
                                  const char* value);

/**
 * Set response body in middleware context
 * @param ctx Middleware context
 * @param body Response body
 * @param content_type Content type
 * @return 0 on success, -1 on failure
 */
int catzilla_middleware_set_body(catzilla_middleware_context_t* ctx,
                                const char* body,
                                const char* content_type);

/**
 * Set error status and message in middleware context
 * @param ctx Middleware context
 * @param status HTTP error status code
 * @param message Error message
 */
void catzilla_middleware_set_error(catzilla_middleware_context_t* ctx,
                                  int status,
                                  const char* message);

/**
 * Get request header value
 * @param ctx Middleware context
 * @param name Header name
 * @return Header value or NULL if not found
 */
const char* catzilla_middleware_get_header(catzilla_middleware_context_t* ctx,
                                          const char* name);

/**
 * Set middleware-specific context data
 * @param ctx Middleware context
 * @param middleware_index Index of middleware
 * @param data Data to store
 */
void catzilla_middleware_set_data(catzilla_middleware_context_t* ctx,
                                 int middleware_index,
                                 void* data);

/**
 * Get middleware-specific context data
 * @param ctx Middleware context
 * @param middleware_index Index of middleware
 * @return Stored data or NULL
 */
void* catzilla_middleware_get_data(catzilla_middleware_context_t* ctx,
                                  int middleware_index);

// ============================================================================
// DI INTEGRATION FOR MIDDLEWARE
// ============================================================================

/**
 * Resolve dependency in middleware context
 * @param ctx Middleware context
 * @param service_name Service name to resolve
 * @param service_instance Output pointer for resolved service
 * @return 0 on success, -1 on failure
 */
int catzilla_middleware_resolve_dependency(catzilla_middleware_context_t* ctx,
                                         const char* service_name,
                                         void** service_instance);

/**
 * Set context value in DI system
 * @param ctx Middleware context
 * @param key Context key
 * @param value Context value
 * @return 0 on success, -1 on failure
 */
int catzilla_middleware_set_di_context(catzilla_middleware_context_t* ctx,
                                      const char* key,
                                      void* value);

/**
 * Get context value from DI system
 * @param ctx Middleware context
 * @param key Context key
 * @return Context value or NULL if not found
 */
void* catzilla_middleware_get_di_context(catzilla_middleware_context_t* ctx,
                                        const char* key);

// ============================================================================
// TIMING UTILITIES
// ============================================================================

/**
 * Get high-resolution timestamp
 * @return Timestamp in nanoseconds
 */
uint64_t catzilla_middleware_get_timestamp(void);

/**
 * Calculate duration between timestamps
 * @param start_time Start timestamp
 * @param end_time End timestamp
 * @return Duration in nanoseconds
 */
uint64_t catzilla_middleware_calculate_duration(uint64_t start_time, uint64_t end_time);

// ============================================================================
// PER-ROUTE MIDDLEWARE FUNCTIONS
// ============================================================================

/**
 * Execute per-route middleware chain for a specific route
 * Zero-allocation execution of route-specific middleware
 *
 * @param route_middleware The per-route middleware chain to execute
 * @param ctx The middleware context for execution
 * @param di_container Optional DI container for dependency injection
 * @return 0 on success, -1 on error
 */
int catzilla_middleware_execute_per_route(catzilla_route_middleware_t* route_middleware,
                                         catzilla_middleware_context_t* ctx,
                                         catzilla_di_container_t* di_container);

/**
 * Initialize per-route middleware chain
 * Zero-allocation initialization for route-specific middleware
 *
 * @param route_middleware The middleware chain to initialize
 * @param initial_capacity Initial capacity for middleware functions
 * @return 0 on success, -1 on error
 */
int catzilla_route_middleware_init(catzilla_route_middleware_t* route_middleware, int initial_capacity);

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
                                 uint32_t priority);

/**
 * Cleanup per-route middleware chain
 * Zero-allocation cleanup that only frees the allocated arrays
 *
 * @param route_middleware The middleware chain to cleanup
 */
void catzilla_route_middleware_cleanup(catzilla_route_middleware_t* route_middleware);

#endif /* CATZILLA_MIDDLEWARE_H */
