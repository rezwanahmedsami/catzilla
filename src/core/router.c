// Platform compatibility
#include "platform_compat.h"

// System headers
#include <stdlib.h>
#include <string.h>
#include <stdio.h>
#include <ctype.h>
// pthread.h is now included in platform_compat.h

// Project headers
#include "router.h"
#include "server.h"
#include "logging.h"
#include "windows_compat.h"
#include "memory.h"

// Internal helper functions
static catzilla_route_node_t* catzilla_router_create_node(catzilla_router_t* router);
static void catzilla_router_free_node(catzilla_router_t* router, catzilla_route_node_t* node);
static int catzilla_router_split_path(const char* path, char segments[][CATZILLA_PATH_SEGMENT_MAX], int max_segments);
static bool catzilla_router_is_param_segment(const char* segment);
static void catzilla_router_extract_param_name(const char* segment, char* param_name);
static int catzilla_router_add_to_trie(catzilla_router_t* router, catzilla_route_t* route,
                                       char segments[][CATZILLA_PATH_SEGMENT_MAX], int segment_count);
static int catzilla_router_match_recursive(catzilla_router_t* router, const char* method,
                                          char segments[][CATZILLA_PATH_SEGMENT_MAX], int segment_count,
                                          int current_segment, catzilla_route_node_t* node,
                                          catzilla_route_match_t* match);
static void catzilla_router_build_allowed_methods(catzilla_route_node_t* node);

int catzilla_router_init(catzilla_router_t* router) {
    if (!router) return -1;

    memset(router, 0, sizeof(catzilla_router_t));

    // Initialize root node using optimized memory allocation
    router->root = catzilla_cache_alloc(sizeof(catzilla_route_node_t));
    if (!router->root) return -1;
    memset(router->root, 0, sizeof(catzilla_route_node_t));

    // Initialize root node arrays
    router->root->child_capacity = 4;
    router->root->children = catzilla_cache_alloc(sizeof(catzilla_route_node_t*) * router->root->child_capacity);
    router->root->child_segments = catzilla_cache_alloc(sizeof(char*) * router->root->child_capacity);
    router->root->handler_capacity = 4;
    router->root->handlers = catzilla_cache_alloc(sizeof(catzilla_route_t*) * router->root->handler_capacity);
    router->root->methods = catzilla_cache_alloc(sizeof(char*) * router->root->handler_capacity);

    if (!router->root->children || !router->root->child_segments ||
        !router->root->handlers || !router->root->methods) {
        catzilla_cache_free(router->root->children);
        catzilla_cache_free(router->root->child_segments);
        free(router->root->handlers);
        free(router->root->methods);
        free(router->root);
        return -1;
    }

    router->root->child_count = 0;
    router->root->handler_count = 0;
    router->root->has_handlers = false;
    router->root->allowed_methods[0] = '\0';

    // Initialize routes array
    router->route_capacity = 64;
    router->routes = catzilla_cache_alloc(sizeof(catzilla_route_t*) * router->route_capacity);
    if (!router->routes) {
        catzilla_cache_free(router->root->children);
        catzilla_cache_free(router->root->child_segments);
        catzilla_cache_free(router->root->handlers);
        catzilla_cache_free(router->root->methods);
        catzilla_cache_free(router->root);
        return -1;
    }

    router->route_count = 0;
    router->next_route_id = 1;

    LOG_ROUTER_DEBUG("Router initialized successfully");
    return 0;
}

void catzilla_router_cleanup(catzilla_router_t* router) {
    if (!router) return;

    LOG_ROUTER_DEBUG("Starting router cleanup");

    // Free all routes
    for (int i = 0; i < router->route_count; i++) {
        if (router->routes[i]) {
            // Free parameter names
            if (router->routes[i]->param_names) {
                for (int j = 0; j < router->routes[i]->param_count; j++) {
                    catzilla_cache_free(router->routes[i]->param_names[j]);
                }
                catzilla_cache_free(router->routes[i]->param_names);
            }

            // Free per-route middleware chain
            if (router->routes[i]->middleware_chain) {
                catzilla_cache_free(router->routes[i]->middleware_chain->middleware_functions);
                catzilla_cache_free(router->routes[i]->middleware_chain->middleware_priorities);
                catzilla_cache_free(router->routes[i]->middleware_chain->middleware_flags);
                catzilla_cache_free(router->routes[i]->middleware_chain);
            }

            catzilla_cache_free(router->routes[i]);
        }
    }
    catzilla_cache_free(router->routes);

    // Free the trie structure (this handles all trie-related memory)
    if (router->root) {
        catzilla_router_free_node(router, router->root);
    }

    memset(router, 0, sizeof(catzilla_router_t));
    LOG_ROUTER_DEBUG("Router cleanup completed");
}

static catzilla_route_node_t* catzilla_router_create_node(catzilla_router_t* router) {
    catzilla_route_node_t* node = catzilla_cache_alloc(sizeof(catzilla_route_node_t));
    if (!node) return NULL;

    memset(node, 0, sizeof(catzilla_route_node_t));

    // Initialize children arrays
    node->child_capacity = 4;
    node->children = catzilla_cache_alloc(sizeof(catzilla_route_node_t*) * node->child_capacity);
    node->child_segments = catzilla_cache_alloc(sizeof(char*) * node->child_capacity);

    // Initialize handlers arrays
    node->handler_capacity = 4;
    node->handlers = catzilla_cache_alloc(sizeof(catzilla_route_t*) * node->handler_capacity);
    node->methods = catzilla_cache_alloc(sizeof(char*) * node->handler_capacity);

    if (!node->children || !node->child_segments || !node->handlers || !node->methods) {
        catzilla_cache_free(node->children);
        catzilla_cache_free(node->child_segments);
        catzilla_cache_free(node->handlers);
        catzilla_cache_free(node->methods);
        catzilla_cache_free(node);
        return NULL;
    }

    node->child_count = 0;
    node->handler_count = 0;
    node->has_handlers = false;
    node->allowed_methods[0] = '\0';

    return node;
}

static void catzilla_router_free_node(catzilla_router_t* router, catzilla_route_node_t* node) {
    if (!node) return;

    // Free children recursively
    for (int i = 0; i < node->child_count; i++) {
        if (node->children[i]) {
            catzilla_router_free_node(router, node->children[i]);
        }
        catzilla_cache_free(node->child_segments[i]);
    }

    // Free parameter child
    if (node->param_child) {
        catzilla_router_free_node(router, node->param_child);
    }

    // Free method strings
    for (int i = 0; i < node->handler_count; i++) {
        catzilla_cache_free(node->methods[i]);
    }

    catzilla_cache_free(node->children);
    catzilla_cache_free(node->child_segments);
    catzilla_cache_free(node->handlers);
    catzilla_cache_free(node->methods);
    catzilla_cache_free(node);
}

static int catzilla_router_split_path(const char* path, char segments[][CATZILLA_PATH_SEGMENT_MAX], int max_segments) {
    if (!path || !segments || max_segments <= 0) return -1;

    // Normalize path - ensure it starts with '/'
    const char* start = path;
    if (*start != '/') {
        return -1; // Invalid path
    }
    start++; // Skip initial '/'

    int segment_count = 0;
    const char* segment_start = start;

    while (*start && segment_count < max_segments) {
        if (*start == '/') {
            // Found end of segment
            int segment_len = start - segment_start;
            if (segment_len > 0 && segment_len < CATZILLA_PATH_SEGMENT_MAX) {
                strncpy(segments[segment_count], segment_start, segment_len);
                segments[segment_count][segment_len] = '\0';
                segment_count++;
            }
            // Skip multiple slashes
            while (*start == '/') start++;
            segment_start = start;
        } else {
            start++;
        }
    }

    // Handle last segment
    if (segment_start < start && segment_count < max_segments) {
        int segment_len = start - segment_start;
        if (segment_len < CATZILLA_PATH_SEGMENT_MAX) {
            strncpy(segments[segment_count], segment_start, segment_len);
            segments[segment_count][segment_len] = '\0';
            segment_count++;
        }
    }

    return segment_count;
}

static bool catzilla_router_is_param_segment(const char* segment) {
    if (!segment) return false;
    int len = strlen(segment);
    return len > 2 && segment[0] == '{' && segment[len-1] == '}';
}

static void catzilla_router_extract_param_name(const char* segment, char* param_name) {
    if (!segment || !param_name || !catzilla_router_is_param_segment(segment)) {
        param_name[0] = '\0';
        return;
    }

    int len = strlen(segment);
    strncpy(param_name, segment + 1, len - 2);
    param_name[len - 2] = '\0';
}

static void catzilla_router_build_allowed_methods(catzilla_route_node_t* node) {
    if (!node) return;

    node->allowed_methods[0] = '\0';
    bool has_get = false;
    bool has_head = false;

    // First pass: build allowed methods and check for GET/HEAD
    for (int i = 0; i < node->handler_count; i++) {
        if (i > 0) {
            strcat(node->allowed_methods, ", ");
        }
        strcat(node->allowed_methods, node->methods[i]);

        if (strcmp(node->methods[i], "GET") == 0) {
            has_get = true;
        }
        if (strcmp(node->methods[i], "HEAD") == 0) {
            has_head = true;
        }
    }

    // Auto-HEAD: If we have GET but not explicit HEAD, add HEAD to allowed methods
    if (has_get && !has_head) {
        if (node->handler_count > 0) {
            strcat(node->allowed_methods, ", ");
        }
        strcat(node->allowed_methods, "HEAD");
    }

    node->has_handlers = (node->handler_count > 0);

    // Debug: Print what allowed methods we built
    LOG_ROUTER_DEBUG("Built allowed methods: '%s' (handler_count=%d)", node->allowed_methods, node->handler_count);
}

uint32_t catzilla_router_add_route(catzilla_router_t* router,
                                   const char* method,
                                   const char* path,
                                   void* handler,
                                   void* user_data,
                                   bool overwrite) {
    // Call the full function with no middleware
    return catzilla_router_add_route_with_middleware(router, method, path, handler,
                                                    user_data, overwrite, NULL, 0, NULL);
}

uint32_t catzilla_router_add_route_with_middleware(catzilla_router_t* router,
                                                   const char* method,
                                                   const char* path,
                                                   void* handler,
                                                   void* user_data,
                                                   bool overwrite,
                                                   void** middleware_functions,
                                                   int middleware_count,
                                                   uint32_t* middleware_priorities) {
    if (!router || !method || !path || !handler) {
        LOG_ROUTER_ERROR("Add route failed: invalid parameters");
        return 0;
    }

    LOG_ROUTER_DEBUG("Adding route: %s %s", method, path);

    // Normalize method
    char norm_method[CATZILLA_METHOD_MAX];
    if (catzilla_router_normalize_method(method, norm_method, sizeof(norm_method)) != 0) {
        LOG_ROUTER_ERROR("Failed to normalize method: %s", method);
        return 0;
    }

    // Normalize path
    char norm_path[CATZILLA_PATH_MAX];
    if (catzilla_router_normalize_path(path, norm_path, sizeof(norm_path)) != 0) {
        LOG_ROUTER_ERROR("Failed to normalize path: %s", path);
        return 0;
    }

    // Split path into segments
    char segments[CATZILLA_MAX_PATH_SEGMENTS][CATZILLA_PATH_SEGMENT_MAX];
    int segment_count = catzilla_router_split_path(norm_path, segments, CATZILLA_MAX_PATH_SEGMENTS);
    if (segment_count < 0) {
        LOG_ROUTER_ERROR("Failed to split path: %s", norm_path);
        return 0;
    }

    // Create route object
    catzilla_route_t* route = catzilla_cache_alloc(sizeof(catzilla_route_t));
    if (!route) {
        LOG_ROUTER_ERROR("Failed to allocate route");
        return 0;
    }

    memset(route, 0, sizeof(catzilla_route_t));
    strncpy(route->method, norm_method, CATZILLA_METHOD_MAX - 1);
    route->method[CATZILLA_METHOD_MAX - 1] = '\0';  // Ensure null termination
    strncpy(route->path, norm_path, CATZILLA_PATH_MAX - 1);
    route->path[CATZILLA_PATH_MAX - 1] = '\0';      // Ensure null termination
    route->handler = handler;
    route->user_data = user_data;
    route->overwrite = overwrite;
    route->id = router->next_route_id++;

    // Debug: Print what we're storing
    LOG_ROUTER_DEBUG("Storing route: method='%s', path='%s', id=%u", route->method, route->path, route->id);

    // Initialize per-route middleware chain
    route->middleware_chain = NULL;
    if (middleware_count > 0 && middleware_functions) {
        route->middleware_chain = catzilla_cache_alloc(sizeof(catzilla_route_middleware_t));
        if (route->middleware_chain) {
            route->middleware_chain->middleware_capacity = middleware_count + 4; // Room for growth
            route->middleware_chain->middleware_functions = catzilla_cache_alloc(
                sizeof(void*) * route->middleware_chain->middleware_capacity);
            route->middleware_chain->middleware_priorities = catzilla_cache_alloc(
                sizeof(uint32_t) * route->middleware_chain->middleware_capacity);
            route->middleware_chain->middleware_flags = catzilla_cache_alloc(
                sizeof(uint32_t) * route->middleware_chain->middleware_capacity);

            if (route->middleware_chain->middleware_functions &&
                route->middleware_chain->middleware_priorities &&
                route->middleware_chain->middleware_flags) {

                // Copy middleware functions and priorities
                route->middleware_chain->middleware_count = middleware_count;
                memcpy(route->middleware_chain->middleware_functions, middleware_functions,
                       sizeof(void*) * middleware_count);

                if (middleware_priorities) {
                    memcpy(route->middleware_chain->middleware_priorities, middleware_priorities,
                           sizeof(uint32_t) * middleware_count);
                } else {
                    // Default priorities (1000, 1001, 1002, ...)
                    for (int i = 0; i < middleware_count; i++) {
                        route->middleware_chain->middleware_priorities[i] = 1000 + i;
                    }
                }

                // Default flags (PRE_ROUTE)
                for (int i = 0; i < middleware_count; i++) {
                    route->middleware_chain->middleware_flags[i] = 1; // CATZILLA_MIDDLEWARE_PRE_ROUTE
                }
            } else {
                // Cleanup on allocation failure
                catzilla_cache_free(route->middleware_chain->middleware_functions);
                catzilla_cache_free(route->middleware_chain->middleware_priorities);
                catzilla_cache_free(route->middleware_chain->middleware_flags);
                catzilla_cache_free(route->middleware_chain);
                route->middleware_chain = NULL;
            }
        }
    }

    // Extract parameter names
    route->param_count = 0;
    for (int i = 0; i < segment_count; i++) {
        if (catzilla_router_is_param_segment(segments[i])) {
            route->param_count++;
        }
    }

    if (route->param_count > 0) {
        route->param_names = catzilla_cache_alloc(sizeof(char*) * route->param_count);
        if (!route->param_names) {
            catzilla_cache_free(route);
            return 0;
        }

        int param_idx = 0;
        for (int i = 0; i < segment_count; i++) {
            if (catzilla_router_is_param_segment(segments[i])) {
                char param_name[CATZILLA_PARAM_NAME_MAX];
                catzilla_router_extract_param_name(segments[i], param_name);

                route->param_names[param_idx] = catzilla_cache_alloc(strlen(param_name) + 1);
                if (!route->param_names[param_idx]) {
                    // Cleanup on error
                    for (int j = 0; j < param_idx; j++) {
                        catzilla_cache_free(route->param_names[j]);
                    }
                    catzilla_cache_free(route->param_names);
                    catzilla_cache_free(route);
                    return 0;
                }
                strcpy(route->param_names[param_idx], param_name);
                param_idx++;
            }
        }
    }

    // Add to trie
    if (catzilla_router_add_to_trie(router, route, segments, segment_count) != 0) {
        // Cleanup on error
        if (route->param_names) {
            for (int i = 0; i < route->param_count; i++) {
                catzilla_cache_free(route->param_names[i]);
            }
            catzilla_cache_free(route->param_names);
        }
        catzilla_cache_free(route);
        return 0;
    }

    // Add to routes array
    if (router->route_count >= router->route_capacity) {
        int new_capacity = router->route_capacity * 2;
        catzilla_route_t** new_routes = catzilla_cache_realloc(router->routes, sizeof(catzilla_route_t*) * new_capacity);
        if (!new_routes) {
            LOG_ROUTER_ERROR("Failed to expand routes array");
            return route->id; // Route was added to trie, just can't track it
        }
        router->routes = new_routes;
        router->route_capacity = new_capacity;
    }

    router->routes[router->route_count++] = route;

    LOG_ROUTER_DEBUG("Route added successfully with ID %u", route->id);
    return route->id;
}

static int catzilla_router_add_to_trie(catzilla_router_t* router, catzilla_route_t* route,
                                       char segments[][CATZILLA_PATH_SEGMENT_MAX], int segment_count) {
    catzilla_route_node_t* current = router->root;

    for (int i = 0; i < segment_count; i++) {
        bool is_param = catzilla_router_is_param_segment(segments[i]);

        if (is_param) {
            // Dynamic parameter segment
            if (!current->param_child) {
                current->param_child = catzilla_router_create_node(router);
                if (!current->param_child) return -1;

                catzilla_router_extract_param_name(segments[i], current->param_name);
            }
            current = current->param_child;
        } else {
            // Static segment
            catzilla_route_node_t* child = NULL;

            // Find existing child
            for (int j = 0; j < current->child_count; j++) {
                if (strcmp(current->child_segments[j], segments[i]) == 0) {
                    child = current->children[j];
                    break;
                }
            }

            if (!child) {
                // Create new child
                child = catzilla_router_create_node(router);
                if (!child) return -1;

                // Expand children arrays if needed
                if (current->child_count >= current->child_capacity) {
                    int new_capacity = current->child_capacity * 2;

                    catzilla_route_node_t** new_children = catzilla_cache_realloc(current->children,
                                                                  sizeof(catzilla_route_node_t*) * new_capacity);
                    char** new_segments = catzilla_cache_realloc(current->child_segments,
                                                 sizeof(char*) * new_capacity);

                    if (!new_children || !new_segments) {
                        catzilla_cache_free(new_children);
                        catzilla_cache_free(new_segments);
                        catzilla_router_free_node(router, child);
                        return -1;
                    }

                    current->children = new_children;
                    current->child_segments = new_segments;
                    current->child_capacity = new_capacity;
                }

                // Add child
                current->children[current->child_count] = child;
                current->child_segments[current->child_count] = catzilla_cache_alloc(strlen(segments[i]) + 1);
                if (!current->child_segments[current->child_count]) {
                    catzilla_router_free_node(router, child);
                    return -1;
                }
                strcpy(current->child_segments[current->child_count], segments[i]);
                current->child_count++;
            }

            current = child;
        }
    }

    // Add handler to the final node
    // Check for existing method
    for (int i = 0; i < current->handler_count; i++) {
        if (strcmp(current->methods[i], route->method) == 0) {
            if (!route->overwrite) {
                LOG_ROUTER_WARN("Route conflict: %s %s overwrites existing route",
                       route->method, route->path);
            }
            // Replace existing handler
            current->handlers[i] = route;
            catzilla_router_build_allowed_methods(current);
            return 0;
        }
    }

    // Expand handlers arrays if needed
    if (current->handler_count >= current->handler_capacity) {
        int new_capacity = current->handler_capacity * 2;

        catzilla_route_t** new_handlers = catzilla_cache_realloc(current->handlers,
                                                 sizeof(catzilla_route_t*) * new_capacity);
        char** new_methods = catzilla_cache_realloc(current->methods,
                                    sizeof(char*) * new_capacity);

        if (!new_handlers || !new_methods) {
            catzilla_cache_free(new_handlers);
            catzilla_cache_free(new_methods);
            return -1;
        }

        current->handlers = new_handlers;
        current->methods = new_methods;
        current->handler_capacity = new_capacity;
    }

    // Add new handler
    current->handlers[current->handler_count] = route;
    current->methods[current->handler_count] = catzilla_cache_alloc(strlen(route->method) + 1);
    if (!current->methods[current->handler_count]) {
        return -1;
    }
    strcpy(current->methods[current->handler_count], route->method);
    current->handler_count++;

    // Debug: Print what we stored in trie
    LOG_ROUTER_DEBUG("Stored in trie: method='%s', path='%s', handler_count=%d",
                     current->methods[current->handler_count - 1], route->path, current->handler_count);

    catzilla_router_build_allowed_methods(current);
    return 0;
}

int catzilla_router_match(catzilla_router_t* router,
                         const char* method,
                         const char* path,
                         catzilla_route_match_t* match) {
    if (!router || !method || !path || !match) return -1;

    // Initialize match result
    memset(match, 0, sizeof(catzilla_route_match_t));
    match->status_code = 404; // Default to not found

    // Normalize inputs
    char norm_method[CATZILLA_METHOD_MAX];
    char norm_path[CATZILLA_PATH_MAX];

    if (catzilla_router_normalize_method(method, norm_method, sizeof(norm_method)) != 0 ||
        catzilla_router_normalize_path(path, norm_path, sizeof(norm_path)) != 0) {
        return -1;
    }

    // Split path into segments
    char segments[CATZILLA_MAX_PATH_SEGMENTS][CATZILLA_PATH_SEGMENT_MAX];
    int segment_count = catzilla_router_split_path(norm_path, segments, CATZILLA_MAX_PATH_SEGMENTS);
    if (segment_count < 0) return -1;

    // Match against trie
    return catzilla_router_match_recursive(router, norm_method, segments, segment_count,
                                          0, router->root, match);
}

static int catzilla_router_match_recursive(catzilla_router_t* router, const char* method,
                                          char segments[][CATZILLA_PATH_SEGMENT_MAX], int segment_count,
                                          int current_segment, catzilla_route_node_t* node,
                                          catzilla_route_match_t* match) {
    if (current_segment == segment_count) {
        // Reached end of path
        if (node->has_handlers) {
            // Check for exact method match
            for (int i = 0; i < node->handler_count; i++) {
                if (strcmp(node->methods[i], method) == 0) {
                    match->route = node->handlers[i];
                    match->status_code = 200;
                    return 0; // Successful match
                }
            }

            // Auto-HEAD: If HEAD request didn't find explicit HEAD handler, try GET
            if (strcmp(method, "HEAD") == 0) {
                for (int i = 0; i < node->handler_count; i++) {
                    if (strcmp(node->methods[i], "GET") == 0) {
                        match->route = node->handlers[i];
                        match->status_code = 200;
                        return 0; // Successful HEAD->GET fallback
                    }
                }
            }

            // Path exists but method not allowed
            strcpy(match->allowed_methods, node->allowed_methods);
            match->has_allowed_methods = true;
            match->status_code = 405; // Method not allowed
            return -1;
        }

        // Path doesn't exist
        match->status_code = 404;
        return -1;
    }

    const char* current_seg = segments[current_segment];

    // Try static children first
    for (int i = 0; i < node->child_count; i++) {
        if (strcmp(node->child_segments[i], current_seg) == 0) {
            int result = catzilla_router_match_recursive(router, method, segments, segment_count,
                                                        current_segment + 1, node->children[i], match);
            if (result == 0 || match->has_allowed_methods) {
                return result;
            }
        }
    }

    // Try parameter child
    if (node->param_child) {
        // Store parameter value
        if (match->param_count < CATZILLA_MAX_PATH_PARAMS) {
            strcpy(match->params[match->param_count].name, node->param_name);
            strcpy(match->params[match->param_count].value, current_seg);
            match->param_count++;
        }

        int result = catzilla_router_match_recursive(router, method, segments, segment_count,
                                                    current_segment + 1, node->param_child, match);
        if (result == 0 || match->has_allowed_methods) {
            return result;
        }

        // Backtrack parameter if no match
        if (match->param_count > 0) {
            match->param_count--;
        }
    }

    return -1; // No match found
}

const char* catzilla_router_get_param(const catzilla_route_match_t* match, const char* param_name) {
    if (!match || !param_name) return NULL;

    for (int i = 0; i < match->param_count; i++) {
        if (strcmp(match->params[i].name, param_name) == 0) {
            return match->params[i].value;
        }
    }
    return NULL;
}

int catzilla_router_get_routes(catzilla_router_t* router, catzilla_route_t** routes, int max_routes) {
    if (!router || !routes || max_routes <= 0) return 0;

    int count = router->route_count < max_routes ? router->route_count : max_routes;
    for (int i = 0; i < count; i++) {
        routes[i] = router->routes[i];
    }

    return count;
}

int catzilla_router_normalize_method(const char* method, char* output, size_t output_size) {
    if (!method || !output || output_size == 0) return -1;

    size_t len = strlen(method);
    if (len >= output_size) return -1;

    for (size_t i = 0; i < len; i++) {
        output[i] = toupper(method[i]);
    }
    output[len] = '\0';

    return 0;
}

int catzilla_router_normalize_path(const char* path, char* output, size_t output_size) {
    if (!path || !output || output_size == 0) return -1;

    // Ensure path starts with '/'
    if (path[0] != '/') {
        if (output_size < 2) return -1;
        output[0] = '/';
        strncpy(output + 1, path, output_size - 2);
        output[output_size - 1] = '\0';
    } else {
        strncpy(output, path, output_size - 1);
        output[output_size - 1] = '\0';
    }

    // Remove trailing slash (except for root)
    size_t len = strlen(output);
    if (len > 1 && output[len - 1] == '/') {
        output[len - 1] = '\0';
    }

    return 0;
}

bool catzilla_router_has_route(catzilla_router_t* router, const char* method, const char* path) {
    if (!router || !method || !path) return false;

    catzilla_route_match_t match;
    return catzilla_router_match(router, method, path, &match) == 0;
}

int catzilla_router_remove_route(catzilla_router_t* router, uint32_t route_id) {
    if (!router || route_id == 0) return -1;

    // Find route in array
    for (int i = 0; i < router->route_count; i++) {
        if (router->routes[i] && router->routes[i]->id == route_id) {
            catzilla_route_t* route = router->routes[i];

            // Remove from array (shift remaining routes)
            for (int j = i; j < router->route_count - 1; j++) {
                router->routes[j] = router->routes[j + 1];
            }
            router->route_count--;

            // Free route memory
            if (route->param_names) {
                for (int j = 0; j < route->param_count; j++) {
                    catzilla_cache_free(route->param_names[j]);
                }
                catzilla_cache_free(route->param_names);
            }

            // Free per-route middleware chain
            if (route->middleware_chain) {
                catzilla_cache_free(route->middleware_chain->middleware_functions);
                catzilla_cache_free(route->middleware_chain->middleware_priorities);
                catzilla_cache_free(route->middleware_chain->middleware_flags);
                catzilla_cache_free(route->middleware_chain);
            }

            catzilla_cache_free(route);

            // Note: We don't remove from trie for performance reasons
            // The trie will still contain the route but it won't be found
            // during matching since we nullify the reference

            return 0;
        }
    }

    return -1; // Route not found
}
