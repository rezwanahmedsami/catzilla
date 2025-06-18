#ifndef CATZILLA_ROUTER_H
#define CATZILLA_ROUTER_H

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

#define CATZILLA_MAX_PATH_SEGMENTS 32
#define CATZILLA_MAX_PATH_PARAMS 16
#define CATZILLA_ROUTER_MAX_ROUTES 1000
#define CATZILLA_PARAM_NAME_MAX 64
#define CATZILLA_PATH_SEGMENT_MAX 128
#define CATZILLA_PATH_MAX 256
#define CATZILLA_METHOD_MAX 32

// Forward declarations
typedef struct catzilla_route_s catzilla_route_t;
typedef struct catzilla_router_s catzilla_router_t;
typedef struct catzilla_route_node_s catzilla_route_node_t;
typedef struct catzilla_route_match_s catzilla_route_match_t;

/**
 * Route parameter structure for dynamic path segments
 */
typedef struct catzilla_route_param_s {
    char name[CATZILLA_PARAM_NAME_MAX];
    char value[CATZILLA_PATH_SEGMENT_MAX];
} catzilla_route_param_t;

/**
 * Route match result
 */
struct catzilla_route_match_s {
    catzilla_route_t* route;                          // Matched route or NULL
    catzilla_route_param_t params[CATZILLA_MAX_PATH_PARAMS]; // Path parameters
    int param_count;                                  // Number of path parameters
    char allowed_methods[256];                        // Comma-separated allowed methods
    bool has_allowed_methods;                         // Whether path exists but method mismatched
    int status_code;                                  // Suggested HTTP status code
};

/**
 * Route node in the trie structure
 */
struct catzilla_route_node_s {
    // Static path segment children
    struct catzilla_route_node_s** children;
    char** child_segments;
    int child_count;
    int child_capacity;

    // Dynamic parameter child
    struct catzilla_route_node_s* param_child;
    char param_name[CATZILLA_PARAM_NAME_MAX];

    // Route handlers for this node (one per HTTP method)
    catzilla_route_t** handlers;
    char** methods;
    int handler_count;
    int handler_capacity;

    // All allowed methods for this path (for 405 responses)
    char allowed_methods[256];
    bool has_handlers;
};

/**
 * Per-route middleware chain for zero-allocation execution
 */
typedef struct catzilla_route_middleware_s {
    void** middleware_functions;       // Array of C-compiled middleware functions
    int middleware_count;             // Number of middleware functions
    int middleware_capacity;          // Current capacity
    uint32_t* middleware_priorities;  // Execution priorities (sorted)
    uint32_t* middleware_flags;       // Per-middleware execution flags
} catzilla_route_middleware_t;

/**
 * Route definition
 */
struct catzilla_route_s {
    char method[CATZILLA_METHOD_MAX];
    char path[CATZILLA_PATH_MAX];
    void* handler;                    // Python handler function
    void* user_data;                  // Additional user data

    // Route metadata
    char** param_names;               // Parameter names for dynamic segments
    int param_count;                  // Number of parameters
    bool overwrite;                   // Whether this route can overwrite existing ones
    uint32_t id;                      // Unique route ID

    // Per-route middleware (NEW!)
    catzilla_route_middleware_t* middleware_chain;  // Per-route middleware
};

/**
 * Advanced router with trie-based routing
 */
struct catzilla_router_s {
    catzilla_route_node_t* root;      // Root of the routing trie
    catzilla_route_t** routes;        // Array of all routes for introspection
    int route_count;                  // Number of registered routes
    int route_capacity;               // Current capacity of routes array
    uint32_t next_route_id;           // Next route ID to assign
};

/**
 * Initialize a new router
 * @param router Pointer to router structure
 * @return 0 on success, -1 on failure
 */
int catzilla_router_init(catzilla_router_t* router);

/**
 * Clean up router resources
 * @param router Pointer to router structure
 */
void catzilla_router_cleanup(catzilla_router_t* router);

/**
 * Add a route to the router with per-route middleware support
 * @param router Pointer to router structure
 * @param method HTTP method (e.g., "GET", "POST")
 * @param path URL path pattern (e.g., "/users/{user_id}")
 * @param handler Function pointer to route handler
 * @param user_data Optional user data
 * @param overwrite Whether to allow overwriting existing routes
 * @param middleware_functions Array of middleware function pointers (can be NULL)
 * @param middleware_count Number of middleware functions
 * @param middleware_priorities Array of priorities for middleware (can be NULL for default)
 * @return Route ID on success, 0 on failure
 */
uint32_t catzilla_router_add_route_with_middleware(catzilla_router_t* router,
                                                   const char* method,
                                                   const char* path,
                                                   void* handler,
                                                   void* user_data,
                                                   bool overwrite,
                                                   void** middleware_functions,
                                                   int middleware_count,
                                                   uint32_t* middleware_priorities);

/**
 * Add a route to the router
 * @param router Pointer to router structure
 * @param method HTTP method (e.g., "GET", "POST")
 * @param path URL path pattern (e.g., "/users/{user_id}")
 * @param handler Function pointer to route handler
 * @param user_data Optional user data
 * @param overwrite Whether to allow overwriting existing routes
 * @return Route ID on success, 0 on failure
 */
uint32_t catzilla_router_add_route(catzilla_router_t* router,
                                   const char* method,
                                   const char* path,
                                   void* handler,
                                   void* user_data,
                                   bool overwrite);

/**
 * Match a request against registered routes
 * @param router Pointer to router structure
 * @param method HTTP method
 * @param path Request path
 * @param match Pointer to match result structure
 * @return 0 on successful match, -1 on no match
 */
int catzilla_router_match(catzilla_router_t* router,
                         const char* method,
                         const char* path,
                         catzilla_route_match_t* match);

/**
 * Get all registered routes for introspection
 * @param router Pointer to router structure
 * @param routes Output array of route pointers
 * @param max_routes Maximum number of routes to return
 * @return Number of routes returned
 */
int catzilla_router_get_routes(catzilla_router_t* router,
                              catzilla_route_t** routes,
                              int max_routes);

/**
 * Remove a route by ID
 * @param router Pointer to router structure
 * @param route_id Route ID to remove
 * @return 0 on success, -1 if route not found
 */
int catzilla_router_remove_route(catzilla_router_t* router, uint32_t route_id);

/**
 * Check if a route exists for the given method and path
 * @param router Pointer to router structure
 * @param method HTTP method
 * @param path URL path
 * @return true if route exists, false otherwise
 */
bool catzilla_router_has_route(catzilla_router_t* router,
                              const char* method,
                              const char* path);

/**
 * Parse path parameters from a URL path
 * @param path_pattern Route path pattern (e.g., "/users/{id}")
 * @param request_path Actual request path (e.g., "/users/123")
 * @param params Output array for parameters
 * @param max_params Maximum number of parameters
 * @return Number of parameters extracted
 */
int catzilla_router_parse_params(const char* path_pattern,
                                const char* request_path,
                                catzilla_route_param_t* params,
                                int max_params);

/**
 * Get a route parameter value by name
 * @param match Route match result
 * @param param_name Parameter name
 * @return Parameter value or NULL if not found
 */
const char* catzilla_router_get_param(const catzilla_route_match_t* match,
                                     const char* param_name);

/**
 * Normalize HTTP method (uppercase)
 * @param method Input method string
 * @param output Output buffer
 * @param output_size Size of output buffer
 * @return 0 on success, -1 on failure
 */
int catzilla_router_normalize_method(const char* method, char* output, size_t output_size);

/**
 * Normalize URL path (handle double slashes, etc.)
 * @param path Input path string
 * @param output Output buffer
 * @param output_size Size of output buffer
 * @return 0 on success, -1 on failure
 */
int catzilla_router_normalize_path(const char* path, char* output, size_t output_size);

#endif /* CATZILLA_ROUTER_H */
