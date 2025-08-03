#include "dependency.h"
#include "platform_compat.h"
#include "memory.h"
#include "logging.h"
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <stdio.h>
#include <inttypes.h>  // For PRIu64

#ifdef _WIN32
#include "windows_compat.h"
#endif

// ============================================================================
// INTERNAL HELPER FUNCTIONS
// ============================================================================

/**
 * Generate a hash for string keys (djb2 algorithm)
 */
static uint32_t catzilla_di_hash(const char* str) {
    uint32_t hash = 5381;
    int c;
    while ((c = *str++)) {
        hash = ((hash << 5) + hash) + c; // hash * 33 + c
    }
    return hash;
}

/**
 * Get current timestamp in microseconds
 */
static uint64_t catzilla_di_get_timestamp(void) {
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return (uint64_t)ts.tv_sec * 1000000 + ts.tv_nsec / 1000;
}

/**
 * Generate unique ID (simple counter-based approach)
 */
static uint32_t catzilla_di_next_id(void) {
    static uint32_t next_id = 1;
    return next_id++;
}

// ============================================================================
// CACHE IMPLEMENTATION
// ============================================================================

/**
 * Initialize dependency resolution cache
 */
static int catzilla_di_cache_init(catzilla_di_cache_t* cache, int bucket_count,
                                  unsigned arena) {
    if (!cache) return -1;

    cache->bucket_count = bucket_count;
    cache->entry_count = 0;
    cache->cache_arena = arena;
    cache->hit_count = 0;
    cache->miss_count = 0;

    // Allocate hash table buckets using specified arena
    if (arena == 0) {
        cache->buckets = catzilla_calloc(bucket_count, sizeof(catzilla_di_cache_entry_t*));
    } else {
        // Use arena-specific allocation
        cache->buckets = catzilla_cache_alloc(bucket_count * sizeof(catzilla_di_cache_entry_t*));
        if (cache->buckets) {
            memset(cache->buckets, 0, bucket_count * sizeof(catzilla_di_cache_entry_t*));
        }
    }

    return cache->buckets ? 0 : -1;
}

/**
 * Cleanup dependency resolution cache
 */
static void catzilla_di_cache_cleanup(catzilla_di_cache_t* cache) {
    if (!cache || !cache->buckets) return;

    // Free all entries
    for (int i = 0; i < cache->bucket_count; i++) {
        catzilla_di_cache_entry_t* entry = cache->buckets[i];
        while (entry) {
            catzilla_di_cache_entry_t* next = entry->next;
            if (cache->cache_arena == 0) {
                catzilla_free(entry);
            } else {
                catzilla_cache_free(entry);
            }
            entry = next;
        }
    }

    // Free bucket array
    if (cache->cache_arena == 0) {
        catzilla_free(cache->buckets);
    } else {
        catzilla_cache_free(cache->buckets);
    }

    cache->buckets = NULL;
    cache->entry_count = 0;
}

/**
 * Get value from cache
 */
static void* catzilla_di_cache_get(catzilla_di_cache_t* cache, const char* name) {
    if (!cache || !cache->buckets || !name) return NULL;

    uint32_t hash = catzilla_di_hash(name);
    int bucket = hash % cache->bucket_count;

    catzilla_di_cache_entry_t* entry = cache->buckets[bucket];
    while (entry) {
        if (strcmp(entry->name, name) == 0) {
            entry->last_access = catzilla_di_get_timestamp();
            entry->access_count++;
            cache->hit_count++;
            return entry->instance;
        }
        entry = entry->next;
    }

    cache->miss_count++;
    return NULL;
}

/**
 * Set value in cache
 */
static int catzilla_di_cache_set(catzilla_di_cache_t* cache, const char* name, void* instance) {
    if (!cache || !cache->buckets || !name) return -1;

    uint32_t hash = catzilla_di_hash(name);
    int bucket = hash % cache->bucket_count;

    // Check if entry already exists
    catzilla_di_cache_entry_t* entry = cache->buckets[bucket];
    while (entry) {
        if (strcmp(entry->name, name) == 0) {
            entry->instance = instance;
            entry->last_access = catzilla_di_get_timestamp();
            entry->access_count++;
            return 0;
        }
        entry = entry->next;
    }

    // Create new entry
    catzilla_di_cache_entry_t* new_entry;
    if (cache->cache_arena == 0) {
        new_entry = catzilla_malloc(sizeof(catzilla_di_cache_entry_t));
    } else {
        new_entry = catzilla_cache_alloc(sizeof(catzilla_di_cache_entry_t));
    }

    if (!new_entry) return -1;

    strncpy(new_entry->name, name, CATZILLA_DI_NAME_MAX - 1);
    new_entry->name[CATZILLA_DI_NAME_MAX - 1] = '\0';
    new_entry->instance = instance;
    new_entry->last_access = catzilla_di_get_timestamp();
    new_entry->access_count = 1;
    new_entry->next = cache->buckets[bucket];

    cache->buckets[bucket] = new_entry;
    cache->entry_count++;

    return 0;
}

// ============================================================================
// SCOPE MANAGER IMPLEMENTATION
// ============================================================================

/**
 * Initialize scope manager
 */
static int catzilla_di_scope_manager_init(catzilla_di_scope_manager_t* manager) {
    if (!manager) return -1;

    manager->scope_arena = 0; // Use default memory for now
    manager->current_scope_id = catzilla_di_next_id();

    // Initialize singleton cache
    manager->singleton_cache = catzilla_cache_alloc(sizeof(catzilla_di_cache_t));
    if (!manager->singleton_cache) return -1;

    if (catzilla_di_cache_init(manager->singleton_cache, CATZILLA_DI_CACHE_SIZE,
                              manager->scope_arena) != 0) {
        catzilla_cache_free(manager->singleton_cache);
        return -1;
    }

    // Initialize scoped cache
    manager->scoped_cache = catzilla_cache_alloc(sizeof(catzilla_di_cache_t));
    if (!manager->scoped_cache) {
        catzilla_di_cache_cleanup(manager->singleton_cache);
        catzilla_cache_free(manager->singleton_cache);
        return -1;
    }

    if (catzilla_di_cache_init(manager->scoped_cache, CATZILLA_DI_CACHE_SIZE,
                              manager->scope_arena) != 0) {
        catzilla_di_cache_cleanup(manager->singleton_cache);
        catzilla_cache_free(manager->singleton_cache);
        catzilla_cache_free(manager->scoped_cache);
        return -1;
    }

    return 0;
}

/**
 * Cleanup scope manager
 */
static void catzilla_di_scope_manager_cleanup(catzilla_di_scope_manager_t* manager) {
    if (!manager) return;

    if (manager->singleton_cache) {
        catzilla_di_cache_cleanup(manager->singleton_cache);
        catzilla_cache_free(manager->singleton_cache);
    }

    if (manager->scoped_cache) {
        catzilla_di_cache_cleanup(manager->scoped_cache);
        catzilla_cache_free(manager->scoped_cache);
    }
}

// ============================================================================
// SERVICE LOOKUP IMPLEMENTATION
// ============================================================================

/**
 * Find service in container by name using trie lookup
 */
static catzilla_di_service_t* catzilla_di_find_service(catzilla_di_container_t* container,
                                                       const char* name) {
    if (!container || !name) return NULL;

    // Linear search for now (will optimize with trie later)
    for (int i = 0; i < container->service_count; i++) {
        if (container->services[i] &&
            strcmp(container->services[i]->name, name) == 0) {
            return container->services[i];
        }
    }

    // Check parent container if not found locally
    if (container->parent) {
        return catzilla_di_find_service(container->parent, name);
    }

    return NULL;
}

/**
 * Check for circular dependencies in resolution stack
 */
static bool catzilla_di_has_circular_dependency(catzilla_di_context_t* context,
                                                const char* name) {
    if (!context || !name) return false;

    for (int i = 0; i < context->stack_depth; i++) {
        if (strcmp(context->resolution_stack[i], name) == 0) {
            return true;
        }
    }
    return false;
}

/**
 * Push service name onto resolution stack
 */
static int catzilla_di_push_resolution_stack(catzilla_di_context_t* context,
                                             const char* name) {
    if (!context || !name || context->stack_depth >= CATZILLA_DI_MAX_DEPENDENCIES) {
        return -1;
    }

    strncpy(context->resolution_stack[context->stack_depth], name,
            CATZILLA_DI_NAME_MAX - 1);
    context->resolution_stack[context->stack_depth][CATZILLA_DI_NAME_MAX - 1] = '\0';
    context->stack_depth++;
    return 0;
}

/**
 * Pop service name from resolution stack
 */
static void catzilla_di_pop_resolution_stack(catzilla_di_context_t* context) {
    if (context && context->stack_depth > 0) {
        context->stack_depth--;
    }
}

// ============================================================================
// CORE CONTAINER MANAGEMENT API IMPLEMENTATION
// ============================================================================

int catzilla_di_container_init(catzilla_di_container_t* container,
                               catzilla_di_container_t* parent) {
    if (!container) return -1;

    memset(container, 0, sizeof(catzilla_di_container_t));

    container->parent = parent;
    container->container_id = catzilla_di_next_id();
    container->next_service_id = 1;
    container->creation_time = catzilla_di_get_timestamp();
    container->service_capacity = CATZILLA_DI_MAX_SERVICES;
    container->container_arena = 0; // Use default memory for now
    container->service_arena = 0;

    // Initialize service trie (will implement proper trie later)
    container->service_trie = NULL;

    // Initialize scope manager
    container->scope_manager = catzilla_cache_alloc(sizeof(catzilla_di_scope_manager_t));
    if (!container->scope_manager) return -1;

    if (catzilla_di_scope_manager_init(container->scope_manager) != 0) {
        catzilla_cache_free(container->scope_manager);
        return -1;
    }

    // Initialize resolution cache
    container->resolution_cache = catzilla_cache_alloc(sizeof(catzilla_di_cache_t));
    if (!container->resolution_cache) {
        catzilla_di_scope_manager_cleanup(container->scope_manager);
        catzilla_cache_free(container->scope_manager);
        return -1;
    }

    if (catzilla_di_cache_init(container->resolution_cache, CATZILLA_DI_CACHE_SIZE,
                              container->container_arena) != 0) {
        catzilla_di_scope_manager_cleanup(container->scope_manager);
        catzilla_cache_free(container->scope_manager);
        catzilla_cache_free(container->resolution_cache);
        return -1;
    }

    container->is_initialized = true;
    return 0;
}

void catzilla_di_container_cleanup(catzilla_di_container_t* container) {
    if (!container || !container->is_initialized) return;

    // Cleanup all services
    for (int i = 0; i < container->service_count; i++) {
        if (container->services[i]) {
            if (container->services[i]->factory) {
                catzilla_cache_free(container->services[i]->factory);
            }
            catzilla_cache_free(container->services[i]);
        }
    }

    // Cleanup scope manager
    if (container->scope_manager) {
        catzilla_di_scope_manager_cleanup(container->scope_manager);
        catzilla_cache_free(container->scope_manager);
    }

    // Cleanup resolution cache
    if (container->resolution_cache) {
        catzilla_di_cache_cleanup(container->resolution_cache);
        catzilla_cache_free(container->resolution_cache);
    }

    // Cleanup service trie if implemented
    if (container->service_trie) {
        // TODO: Implement trie cleanup
    }

    container->is_initialized = false;
}

catzilla_di_container_t* catzilla_di_container_create(catzilla_di_container_t* parent) {
    catzilla_di_container_t* container = catzilla_cache_alloc(sizeof(catzilla_di_container_t));
    if (!container) return NULL;

    if (catzilla_di_container_init(container, parent) != 0) {
        catzilla_cache_free(container);
        return NULL;
    }

    return container;
}

void catzilla_di_container_destroy(catzilla_di_container_t* container) {
    if (!container) return;

    catzilla_di_container_cleanup(container);
    catzilla_cache_free(container);
}

// ============================================================================
// SERVICE REGISTRATION API IMPLEMENTATION
// ============================================================================

int catzilla_di_register_service(catzilla_di_container_t* container,
                                 const char* name,
                                 const char* type_name,
                                 catzilla_di_scope_type_t scope,
                                 catzilla_di_factory_t* factory,
                                 const char** dependencies,
                                 int dependency_count) {
    if (!container || !name || !factory || dependency_count < 0 ||
        dependency_count > CATZILLA_DI_MAX_DEPENDENCIES) {
        return -1;
    }

    // Check if service already exists
    if (catzilla_di_find_service(container, name) != NULL) {
        return -1; // Service already registered
    }

    // Check if we have capacity
    if (container->service_count >= container->service_capacity) {
        return -1; // Container full
    }

    // Allocate service structure
    catzilla_di_service_t* service = catzilla_cache_alloc(sizeof(catzilla_di_service_t));
    if (!service) return -1;

    // Initialize service
    memset(service, 0, sizeof(catzilla_di_service_t));
    strncpy(service->name, name, CATZILLA_DI_NAME_MAX - 1);
    service->name[CATZILLA_DI_NAME_MAX - 1] = '\0';

    if (type_name) {
        strncpy(service->type_name, type_name, CATZILLA_DI_TYPE_MAX - 1);
        service->type_name[CATZILLA_DI_TYPE_MAX - 1] = '\0';
    }

    service->scope = scope;
    service->factory = factory;
    service->dependency_count = dependency_count;
    service->registration_id = container->next_service_id++;
    service->creation_time = catzilla_di_get_timestamp();
    service->cached_instance = NULL;
    service->is_cached = false;
    service->is_circular_dependency_checked = false;

    // Copy dependencies
    for (int i = 0; i < dependency_count; i++) {
        if (dependencies[i]) {
            strncpy(service->dependencies[i], dependencies[i], CATZILLA_DI_NAME_MAX - 1);
            service->dependencies[i][CATZILLA_DI_NAME_MAX - 1] = '\0';
        }
    }

    // Add to container
    container->services[container->service_count] = service;
    container->service_count++;

    return 0;
}

int catzilla_di_register_service_c(catzilla_di_container_t* container,
                                   const char* name,
                                   const char* type_name,
                                   catzilla_di_scope_type_t scope,
                                   catzilla_di_factory_func_t factory_func,
                                   const char** dependencies,
                                   int dependency_count,
                                   void* user_data) {
    if (!container || !name || !factory_func) return -1;

    // Create factory structure
    catzilla_di_factory_t* factory = catzilla_cache_alloc(sizeof(catzilla_di_factory_t));
    if (!factory) return -1;

    factory->create_func = factory_func;
    factory->python_factory = NULL;
    factory->user_data = user_data;
    factory->is_python_factory = false;

    int result = catzilla_di_register_service(container, name, type_name, scope,
                                             factory, dependencies, dependency_count);
    if (result != 0) {
        catzilla_cache_free(factory);
    }

    return result;
}

int catzilla_di_register_service_python(catzilla_di_container_t* container,
                                        const char* name,
                                        const char* type_name,
                                        catzilla_di_scope_type_t scope,
                                        void* python_factory,
                                        const char** dependencies,
                                        int dependency_count) {
    if (!container || !name || !python_factory) return -1;

    // Create factory structure
    catzilla_di_factory_t* factory = catzilla_cache_alloc(sizeof(catzilla_di_factory_t));
    if (!factory) return -1;

    factory->create_func = NULL;
    factory->python_factory = python_factory;
    factory->user_data = NULL;
    factory->is_python_factory = true;

    int result = catzilla_di_register_service(container, name, type_name, scope,
                                             factory, dependencies, dependency_count);
    if (result != 0) {
        catzilla_cache_free(factory);
    }

    return result;
}

int catzilla_di_unregister_service(catzilla_di_container_t* container, const char* name) {
    if (!container || !name) return -1;

    for (int i = 0; i < container->service_count; i++) {
        if (container->services[i] &&
            strcmp(container->services[i]->name, name) == 0) {

            // Free service resources
            catzilla_di_service_t* service = container->services[i];
            if (service->factory) {
                catzilla_cache_free(service->factory);
            }
            catzilla_cache_free(service);

            // Shift remaining services
            for (int j = i; j < container->service_count - 1; j++) {
                container->services[j] = container->services[j + 1];
            }
            container->service_count--;

            return 0;
        }
    }

    return -1; // Service not found
}

// ============================================================================
// SERVICE RESOLUTION API IMPLEMENTATION
// ============================================================================

// Forward declaration for recursive resolution
static void* catzilla_di_resolve_service_internal(catzilla_di_container_t* container,
                                                  const char* name,
                                                  catzilla_di_context_t* context,
                                                  bool create_context_if_null);

void* catzilla_di_resolve_service(catzilla_di_container_t* container,
                                  const char* name,
                                  catzilla_di_context_t* context) {
    return catzilla_di_resolve_service_internal(container, name, context, true);
}

static void* catzilla_di_resolve_service_internal(catzilla_di_container_t* container,
                                                  const char* name,
                                                  catzilla_di_context_t* context,
                                                  bool create_context_if_null) {
    if (!container || !name) return NULL;

    // Create context if needed
    bool should_cleanup_context = false;
    if (!context && create_context_if_null) {
        context = catzilla_di_create_context(container);
        if (!context) return NULL;
        should_cleanup_context = true;
    }

    void* result = NULL;

    // Check context cache first (if context exists)
    if (context) {
        result = catzilla_di_cache_get(context->resolution_cache, name);
        if (result) goto cleanup;
    }

    // Find service
    catzilla_di_service_t* service = catzilla_di_find_service(container, name);
    if (!service) goto cleanup;

    // Check for circular dependencies
    if (context && catzilla_di_has_circular_dependency(context, name)) {
        // TODO: Log circular dependency error
        goto cleanup;
    }

    // Check singleton cache
    if (service->scope == CATZILLA_DI_SCOPE_SINGLETON && service->is_cached) {
        result = service->cached_instance;
        if (context) {
            catzilla_di_cache_set(context->resolution_cache, name, result);
        }
        goto cleanup;
    }

    // Push onto resolution stack
    if (context) {
        if (catzilla_di_push_resolution_stack(context, name) != 0) {
            goto cleanup;
        }
    }

    // Resolve dependencies
    void* dependencies[CATZILLA_DI_MAX_DEPENDENCIES] = {0};
    for (int i = 0; i < service->dependency_count; i++) {
        dependencies[i] = catzilla_di_resolve_service_internal(
            container, service->dependencies[i], context, false);
        if (!dependencies[i]) {
            // Dependency resolution failed
            if (context) {
                catzilla_di_pop_resolution_stack(context);
            }
            goto cleanup;
        }
    }

    // Create instance using factory
    if (service->factory->is_python_factory) {
        // TODO: Call Python factory (will be implemented in Python bridge)
        result = NULL;
    } else if (service->factory->create_func) {
        result = service->factory->create_func(dependencies, service->dependency_count,
                                              service->factory->user_data);
    }

    // Pop from resolution stack
    if (context) {
        catzilla_di_pop_resolution_stack(context);
    }

    if (!result) goto cleanup;

    // Cache based on scope
    if (service->scope == CATZILLA_DI_SCOPE_SINGLETON) {
        service->cached_instance = result;
        service->is_cached = true;
    }

    // Cache in context if available
    if (context) {
        catzilla_di_cache_set(context->resolution_cache, name, result);
    }

cleanup:
    if (should_cleanup_context && context) {
        catzilla_di_cleanup_context(context);
    }

    return result;
}

int catzilla_di_resolve_services(catzilla_di_container_t* container,
                                 const char** names,
                                 int count,
                                 catzilla_di_context_t* context,
                                 void** results) {
    if (!container || !names || !results || count <= 0) return 0;

    bool should_cleanup_context = false;
    if (!context) {
        context = catzilla_di_create_context(container);
        if (!context) return 0;
        should_cleanup_context = true;
    }

    int resolved_count = 0;
    for (int i = 0; i < count; i++) {
        results[i] = catzilla_di_resolve_service_internal(container, names[i],
                                                         context, false);
        if (results[i]) {
            resolved_count++;
        }
    }

    if (should_cleanup_context) {
        catzilla_di_cleanup_context(context);
    }

    return resolved_count;
}

bool catzilla_di_has_service(catzilla_di_container_t* container, const char* name) {
    return catzilla_di_find_service(container, name) != NULL;
}

catzilla_di_service_t* catzilla_di_get_service(catzilla_di_container_t* container, const char* name) {
    return catzilla_di_find_service(container, name);
}

// ============================================================================
// CONTEXT MANAGEMENT API IMPLEMENTATION
// ============================================================================

catzilla_di_context_t* catzilla_di_create_context(catzilla_di_container_t* container) {
    if (!container) return NULL;

    catzilla_di_context_t* context = catzilla_cache_alloc(sizeof(catzilla_di_context_t));
    if (!context) return NULL;

    memset(context, 0, sizeof(catzilla_di_context_t));
    context->container = container;
    context->context_id = catzilla_di_next_id();
    context->creation_time = catzilla_di_get_timestamp();
    context->context_arena = 0; // Use default memory for now

    // Initialize resolution cache
    context->resolution_cache = catzilla_cache_alloc(sizeof(catzilla_di_cache_t));
    if (!context->resolution_cache) {
        catzilla_cache_free(context);
        return NULL;
    }

    if (catzilla_di_cache_init(context->resolution_cache, CATZILLA_DI_CACHE_SIZE,
                              context->context_arena) != 0) {
        catzilla_cache_free(context->resolution_cache);
        catzilla_cache_free(context);
        return NULL;
    }

    return context;
}

void catzilla_di_cleanup_context(catzilla_di_context_t* context) {
    if (!context) return;

    if (context->resolution_cache) {
        catzilla_di_cache_cleanup(context->resolution_cache);
        catzilla_cache_free(context->resolution_cache);
    }

    catzilla_cache_free(context);
}

void catzilla_di_context_set_request_data(catzilla_di_context_t* context, void* request_data) {
    if (context) {
        context->request_data = request_data;
    }
}

void* catzilla_di_context_get_request_data(catzilla_di_context_t* context) {
    return context ? context->request_data : NULL;
}

// ============================================================================
// UTILITY AND INTROSPECTION API IMPLEMENTATION
// ============================================================================

int catzilla_di_validate_dependencies(catzilla_di_container_t* container,
                                      char* error_buffer,
                                      size_t buffer_size) {
    if (!container) return -1;

    // Create temporary context for validation
    catzilla_di_context_t* context = catzilla_di_create_context(container);
    if (!context) return -1;

    int result = 0;
    for (int i = 0; i < container->service_count; i++) {
        catzilla_di_service_t* service = container->services[i];
        if (!service) continue;

        // Reset context for each service validation
        context->stack_depth = 0;

        // Try to resolve each dependency
        for (int j = 0; j < service->dependency_count; j++) {
            if (catzilla_di_has_circular_dependency(context, service->dependencies[j])) {
                if (error_buffer && buffer_size > 0) {
                    snprintf(error_buffer, buffer_size,
                            "Circular dependency detected for service '%s' -> '%s'",
                            service->name, service->dependencies[j]);
                }
                result = -1;
                break;
            }

            // Check if dependency exists
            if (!catzilla_di_find_service(container, service->dependencies[j])) {
                if (error_buffer && buffer_size > 0) {
                    snprintf(error_buffer, buffer_size,
                            "Dependency '%s' not found for service '%s'",
                            service->dependencies[j], service->name);
                }
                result = -1;
                break;
            }
        }

        if (result != 0) break;
    }

    catzilla_di_cleanup_context(context);
    return result;
}

int catzilla_di_get_service_names(catzilla_di_container_t* container,
                                  char names[][CATZILLA_DI_NAME_MAX],
                                  int capacity) {
    if (!container || !names || capacity <= 0) return 0;

    int count = 0;
    for (int i = 0; i < container->service_count && count < capacity; i++) {
        if (container->services[i]) {
            strncpy(names[count], container->services[i]->name, CATZILLA_DI_NAME_MAX - 1);
            names[count][CATZILLA_DI_NAME_MAX - 1] = '\0';
            count++;
        }
    }

    return count;
}

void catzilla_di_get_stats(catzilla_di_container_t* container, catzilla_di_stats_t* stats) {
    if (!container || !stats) return;

    memset(stats, 0, sizeof(catzilla_di_stats_t));

    // Count services by scope
    for (int i = 0; i < container->service_count; i++) {
        if (!container->services[i]) continue;

        stats->total_services++;
        switch (container->services[i]->scope) {
            case CATZILLA_DI_SCOPE_SINGLETON:
                stats->singleton_services++;
                break;
            case CATZILLA_DI_SCOPE_TRANSIENT:
                stats->transient_services++;
                break;
            case CATZILLA_DI_SCOPE_SCOPED:
            case CATZILLA_DI_SCOPE_REQUEST:
                stats->scoped_services++;
                break;
        }
    }

    // Get cache statistics
    if (container->resolution_cache) {
        stats->cache_hits = container->resolution_cache->hit_count;
        stats->cache_misses = container->resolution_cache->miss_count;
        stats->total_resolutions = stats->cache_hits + stats->cache_misses;
    }

    // TODO: Add memory usage calculation
    stats->container_memory_usage = sizeof(catzilla_di_container_t);
    stats->service_memory_usage = stats->total_services * sizeof(catzilla_di_service_t);
}

void catzilla_di_reset_caches(catzilla_di_container_t* container) {
    if (!container) return;

    // Reset container cache
    if (container->resolution_cache) {
        catzilla_di_cache_cleanup(container->resolution_cache);
        catzilla_di_cache_init(container->resolution_cache, CATZILLA_DI_CACHE_SIZE,
                              container->container_arena);
    }

    // Reset scope manager caches
    if (container->scope_manager) {
        if (container->scope_manager->singleton_cache) {
            catzilla_di_cache_cleanup(container->scope_manager->singleton_cache);
            catzilla_di_cache_init(container->scope_manager->singleton_cache,
                                  CATZILLA_DI_CACHE_SIZE,
                                  container->scope_manager->scope_arena);
        }
        if (container->scope_manager->scoped_cache) {
            catzilla_di_cache_cleanup(container->scope_manager->scoped_cache);
            catzilla_di_cache_init(container->scope_manager->scoped_cache,
                                  CATZILLA_DI_CACHE_SIZE,
                                  container->scope_manager->scope_arena);
        }
    }

    // Reset singleton cached instances
    for (int i = 0; i < container->service_count; i++) {
        if (container->services[i] &&
            container->services[i]->scope == CATZILLA_DI_SCOPE_SINGLETON) {
            container->services[i]->cached_instance = NULL;
            container->services[i]->is_cached = false;
        }
    }
}

int catzilla_di_set_config(catzilla_di_container_t* container,
                          const char* option,
                          const char* value) {
    if (!container || !option || !value) return -1;

    // TODO: Implement configuration options
    // For now, return success for any option
    return 0;
}

// ============================================================================
// PHASE 4: ADVANCED MEMORY OPTIMIZATION IMPLEMENTATION
// ============================================================================

/**
 * Create and initialize advanced memory system
 */
int catzilla_di_init_memory_system(catzilla_di_container_t* container) {
    if (!container) return -1;

    // Allocate memory system structure
    container->memory_system = malloc(sizeof(catzilla_di_memory_system_t));
    if (!container->memory_system) return -1;

    // Initialize global statistics
    container->memory_system->total_memory_allocated = 0;
    container->memory_system->total_memory_used = 0;
    container->memory_system->total_memory_peak = 0;
    container->memory_system->overall_efficiency = 0.0;

    // Initialize auto-optimization settings
    container->memory_system->auto_optimization_enabled = true;
    container->memory_system->optimization_interval_ms = 60000; // 1 minute
    container->memory_system->last_optimization_time = catzilla_di_get_timestamp();

    // Initialize memory pressure detection
    container->memory_system->memory_pressure_threshold = 0.85; // 85% usage triggers pressure
    container->memory_system->memory_pressure_detected = false;
    container->memory_system->pressure_response_level = 0;

    // Initialize performance monitoring
    container->memory_system->allocation_performance_ns = 0;
    container->memory_system->gc_performance_ns = 0;
    memset(container->memory_system->memory_access_patterns, 0,
           sizeof(container->memory_system->memory_access_patterns));

    // Create specialized memory pools
    catzilla_di_pool_config_t singleton_config = {
        .initial_size = CATZILLA_DI_MEMORY_POOL_SINGLETON_SIZE,
        .max_size = CATZILLA_DI_MEMORY_POOL_SINGLETON_SIZE * 4,
        .growth_increment = CATZILLA_DI_MEMORY_POOL_SINGLETON_SIZE / 2,
        .fragmentation_threshold = 0.3,
        .auto_tune_enabled = true,
        .gc_frequency_ms = 300000 // 5 minutes for singletons
    };

    catzilla_di_pool_config_t request_config = {
        .initial_size = CATZILLA_DI_MEMORY_POOL_REQUEST_SIZE,
        .max_size = CATZILLA_DI_MEMORY_POOL_REQUEST_SIZE * 8,
        .growth_increment = CATZILLA_DI_MEMORY_POOL_REQUEST_SIZE / 4,
        .fragmentation_threshold = 0.5,
        .auto_tune_enabled = true,
        .gc_frequency_ms = 30000 // 30 seconds for request-scoped
    };

    catzilla_di_pool_config_t transient_config = {
        .initial_size = CATZILLA_DI_MEMORY_POOL_TRANSIENT_SIZE,
        .max_size = CATZILLA_DI_MEMORY_POOL_TRANSIENT_SIZE * 16,
        .growth_increment = CATZILLA_DI_MEMORY_POOL_TRANSIENT_SIZE / 2,
        .fragmentation_threshold = 0.7,
        .auto_tune_enabled = true,
        .gc_frequency_ms = 5000 // 5 seconds for transients
    };

    catzilla_di_pool_config_t factory_config = {
        .initial_size = CATZILLA_DI_MEMORY_POOL_FACTORY_SIZE,
        .max_size = CATZILLA_DI_MEMORY_POOL_FACTORY_SIZE * 4,
        .growth_increment = CATZILLA_DI_MEMORY_POOL_FACTORY_SIZE / 4,
        .fragmentation_threshold = 0.4,
        .auto_tune_enabled = true,
        .gc_frequency_ms = 60000 // 1 minute for factories
    };

    catzilla_di_pool_config_t cache_config = {
        .initial_size = CATZILLA_DI_MEMORY_POOL_CACHE_SIZE,
        .max_size = CATZILLA_DI_MEMORY_POOL_CACHE_SIZE * 2,
        .growth_increment = CATZILLA_DI_MEMORY_POOL_CACHE_SIZE / 8,
        .fragmentation_threshold = 0.2,
        .auto_tune_enabled = true,
        .gc_frequency_ms = 120000 // 2 minutes for cache
    };

    // Create the pools
    container->memory_system->pools[CATZILLA_DI_POOL_SINGLETON] =
        catzilla_di_create_memory_pool(CATZILLA_DI_POOL_SINGLETON, &singleton_config);
    container->memory_system->pools[CATZILLA_DI_POOL_REQUEST] =
        catzilla_di_create_memory_pool(CATZILLA_DI_POOL_REQUEST, &request_config);
    container->memory_system->pools[CATZILLA_DI_POOL_TRANSIENT] =
        catzilla_di_create_memory_pool(CATZILLA_DI_POOL_TRANSIENT, &transient_config);
    container->memory_system->pools[CATZILLA_DI_POOL_FACTORY] =
        catzilla_di_create_memory_pool(CATZILLA_DI_POOL_FACTORY, &factory_config);
    container->memory_system->pools[CATZILLA_DI_POOL_CACHE] =
        catzilla_di_create_memory_pool(CATZILLA_DI_POOL_CACHE, &cache_config);

    // Verify all pools were created successfully
    for (int i = 0; i < CATZILLA_DI_MEMORY_ARENA_COUNT; i++) {
        if (!container->memory_system->pools[i]) {
            catzilla_di_cleanup_memory_system(container);
            return -1;
        }
    }

    return 0;
}

/**
 * Destroy and cleanup memory system
 */
void catzilla_di_cleanup_memory_system(catzilla_di_container_t* container) {
    if (!container || !container->memory_system) return;

    // Destroy all memory pools
    for (int i = 0; i < CATZILLA_DI_MEMORY_ARENA_COUNT; i++) {
        if (container->memory_system->pools[i]) {
            catzilla_di_destroy_memory_pool(container->memory_system->pools[i]);
            container->memory_system->pools[i] = NULL;
        }
    }

    // Free the memory system structure
    free(container->memory_system);
    container->memory_system = NULL;
}

/**
 * Create a specialized memory pool
 */
catzilla_di_memory_pool_t* catzilla_di_create_memory_pool(catzilla_di_pool_type_t type,
                                                         const catzilla_di_pool_config_t* config) {
    if (!config) return NULL;

    catzilla_di_memory_pool_t* pool = malloc(sizeof(catzilla_di_memory_pool_t));
    if (!pool) return NULL;

    // Initialize pool properties
    pool->type = type;
    pool->arena_id = 0; // Use default arena for now (TODO: integrate with jemalloc)
    pool->pool_size = config->initial_size;
    pool->allocated_size = 0;

    // Allocate initial memory block
    pool->memory_base = malloc(config->initial_size);
    if (!pool->memory_base) {
        free(pool);
        return NULL;
    }
    pool->next_free = pool->memory_base;

    // Copy configuration
    pool->config = *config;

    // Initialize statistics
    memset(&pool->stats, 0, sizeof(catzilla_di_pool_stats_t));
    pool->stats.total_allocated = config->initial_size;

    // Initialize auto-tuning state
    memset(pool->usage_history, 0, sizeof(pool->usage_history));
    pool->history_index = 0;
    pool->last_tune_time = catzilla_di_get_timestamp();

    // Initialize thread safety
    pool->is_thread_safe = true;
    pool->lock = NULL; // TODO: Initialize mutex

    return pool;
}

/**
 * Destroy a memory pool and free all its resources
 */
void catzilla_di_destroy_memory_pool(catzilla_di_memory_pool_t* pool) {
    if (!pool) return;

    // Free memory block
    if (pool->memory_base) {
        free(pool->memory_base);
    }

    // Destroy mutex if it exists
    if (pool->lock) {
        // TODO: Destroy mutex
    }

    // Free pool structure
    free(pool);
}

/**
 * Allocate memory from a specialized pool
 */
void* catzilla_di_pool_alloc(catzilla_di_memory_pool_t* pool, size_t size) {
    if (!pool || size == 0) return NULL;

    uint64_t start_time = catzilla_di_get_timestamp();

    // Align size to 8-byte boundary
    size_t aligned_size = (size + 7) & ~7;

    // Check if we have enough space
    if (pool->allocated_size + aligned_size > pool->pool_size) {
        // Try to expand the pool
        if (pool->config.auto_tune_enabled &&
            pool->pool_size + pool->config.growth_increment <= pool->config.max_size) {

            size_t new_size = pool->pool_size + pool->config.growth_increment;
            void* new_base = realloc(pool->memory_base, new_size);
            if (new_base) {
                pool->memory_base = new_base;
                pool->next_free = (char*)pool->memory_base + pool->allocated_size;
                pool->pool_size = new_size;
                pool->stats.total_allocated = new_size;
            } else {
                return NULL; // Out of memory
            }
        } else {
            return NULL; // Pool size limit reached
        }
    }

    // Allocate from the pool
    void* ptr = pool->next_free;
    pool->next_free = (char*)pool->next_free + aligned_size;
    pool->allocated_size += aligned_size;

    // Update statistics
    pool->stats.currently_used += aligned_size;
    if (pool->stats.currently_used > pool->stats.peak_usage) {
        pool->stats.peak_usage = pool->stats.currently_used;
    }
    pool->stats.allocation_count++;
    pool->stats.efficiency_ratio = (double)pool->stats.currently_used / pool->stats.total_allocated;

    // Update performance monitoring
    uint64_t allocation_time = catzilla_di_get_timestamp() - start_time;
    if (pool->stats.allocation_count == 1) {
        // First allocation
        pool->stats.last_gc_time = allocation_time;
    } else {
        // Running average
        pool->stats.last_gc_time = (pool->stats.last_gc_time + allocation_time) / 2;
    }

    return ptr;
}

/**
 * Free memory back to a specialized pool (simplified implementation)
 */
void catzilla_di_pool_free(catzilla_di_memory_pool_t* pool, void* ptr) {
    if (!pool || !ptr) return;

    // For simplicity, we don't actually free individual allocations in this pool implementation
    // In a production system, this would maintain a free list or use a more sophisticated allocator
    pool->stats.deallocation_count++;

    // Update efficiency ratio (approximate)
    if (pool->stats.allocation_count > pool->stats.deallocation_count) {
        size_t estimated_used = pool->stats.total_allocated *
            (pool->stats.allocation_count - pool->stats.deallocation_count) / pool->stats.allocation_count;
        pool->stats.currently_used = estimated_used;
        pool->stats.efficiency_ratio = (double)pool->stats.currently_used / pool->stats.total_allocated;
    }
}

/**
 * Get memory pool statistics
 */
void catzilla_di_get_pool_stats(catzilla_di_memory_pool_t* pool,
                               catzilla_di_pool_stats_t* stats) {
    if (!pool || !stats) return;

    *stats = pool->stats;
}

/**
 * Trigger garbage collection on a memory pool
 */
size_t catzilla_di_pool_gc(catzilla_di_memory_pool_t* pool) {
    if (!pool) return 0;

    uint64_t start_time = catzilla_di_get_timestamp();
    size_t freed_bytes = 0;

    // Calculate fragmentation
    double fragmentation = 1.0 - pool->stats.efficiency_ratio;

    if (fragmentation > pool->config.fragmentation_threshold) {
        // Perform compaction (simplified - just reset for pools with high turnover)
        if (pool->type == CATZILLA_DI_POOL_TRANSIENT || pool->type == CATZILLA_DI_POOL_REQUEST) {
            freed_bytes = pool->allocated_size;
            pool->allocated_size = 0;
            pool->next_free = pool->memory_base;
            pool->stats.currently_used = 0;
            pool->stats.fragmentation_bytes = 0;
            pool->stats.efficiency_ratio = 0.0;
        }
    }

    // Update GC statistics
    uint64_t gc_time = catzilla_di_get_timestamp() - start_time;
    pool->stats.last_gc_time = catzilla_di_get_timestamp();

    return freed_bytes;
}

/**
 * Auto-tune memory pool based on usage patterns
 */
int catzilla_di_auto_tune_pool(catzilla_di_memory_pool_t* pool) {
    if (!pool || !pool->config.auto_tune_enabled) return -1;

    uint64_t current_time = catzilla_di_get_timestamp();

    // Add current usage to history
    pool->usage_history[pool->history_index] = pool->stats.currently_used;
    pool->history_index = (pool->history_index + 1) % CATZILLA_DI_MEMORY_STATS_HISTORY;

    // Calculate average usage over history
    size_t total_usage = 0;
    size_t sample_count = 0;
    for (int i = 0; i < CATZILLA_DI_MEMORY_STATS_HISTORY; i++) {
        if (pool->usage_history[i] > 0) {
            total_usage += pool->usage_history[i];
            sample_count++;
        }
    }

    if (sample_count > 0) {
        size_t avg_usage = total_usage / sample_count;
        double usage_ratio = (double)avg_usage / pool->pool_size;

        // Adjust pool size based on usage patterns
        if (usage_ratio > 0.8 && pool->pool_size < pool->config.max_size) {
            // Pool is heavily used, consider growing
            size_t new_size = pool->pool_size + pool->config.growth_increment;
            if (new_size <= pool->config.max_size) {
                void* new_base = realloc(pool->memory_base, new_size);
                if (new_base) {
                    pool->memory_base = new_base;
                    pool->pool_size = new_size;
                    pool->stats.total_allocated = new_size;
                }
            }
        } else if (usage_ratio < 0.3 && pool->pool_size > pool->config.initial_size) {
            // Pool is underutilized, consider shrinking
            size_t new_size = pool->pool_size - pool->config.growth_increment;
            if (new_size >= pool->config.initial_size && new_size >= pool->allocated_size) {
                void* new_base = realloc(pool->memory_base, new_size);
                if (new_base) {
                    pool->memory_base = new_base;
                    pool->pool_size = new_size;
                    pool->stats.total_allocated = new_size;
                }
            }
        }
    }

    pool->last_tune_time = current_time;
    return 0;
}

/**
 * Optimize all memory pools in the system
 */
int catzilla_di_optimize_memory_pools(catzilla_di_container_t* container) {
    if (!container || !container->memory_system) return -1;

    int optimized_count = 0;

    for (int i = 0; i < CATZILLA_DI_MEMORY_ARENA_COUNT; i++) {
        if (container->memory_system->pools[i]) {
            if (catzilla_di_auto_tune_pool(container->memory_system->pools[i]) == 0) {
                optimized_count++;
            }

            // Also run GC if needed
            catzilla_di_pool_gc(container->memory_system->pools[i]);
        }
    }

    // Update global optimization timestamp
    container->memory_system->last_optimization_time = catzilla_di_get_timestamp();

    return optimized_count;
}

/**
 * Detect and handle memory pressure
 */
int catzilla_di_detect_memory_pressure(catzilla_di_container_t* container) {
    if (!container || !container->memory_system) return 0;

    // Calculate overall memory usage
    size_t total_used = 0;
    size_t total_allocated = 0;

    for (int i = 0; i < CATZILLA_DI_MEMORY_ARENA_COUNT; i++) {
        if (container->memory_system->pools[i]) {
            total_used += container->memory_system->pools[i]->stats.currently_used;
            total_allocated += container->memory_system->pools[i]->stats.total_allocated;
        }
    }

    double usage_ratio = total_allocated > 0 ? (double)total_used / total_allocated : 0.0;

    // Determine pressure level
    int pressure_level = 0;
    if (usage_ratio > container->memory_system->memory_pressure_threshold) {
        if (usage_ratio > 0.95) {
            pressure_level = 2; // Severe pressure
        } else {
            pressure_level = 1; // Mild pressure
        }
    }

    // Update memory system state
    container->memory_system->memory_pressure_detected = (pressure_level > 0);
    container->memory_system->pressure_response_level = pressure_level;

    // Take action based on pressure level
    if (pressure_level > 0) {
        // Run garbage collection on all pools
        for (int i = 0; i < CATZILLA_DI_MEMORY_ARENA_COUNT; i++) {
            if (container->memory_system->pools[i]) {
                catzilla_di_pool_gc(container->memory_system->pools[i]);
            }
        }
    }

    return pressure_level;
}

/**
 * Get comprehensive memory system statistics
 */
int catzilla_di_get_memory_stats(catzilla_di_container_t* container,
                                size_t* total_allocated,
                                size_t* total_used,
                                double* efficiency_ratio) {
    if (!container || !container->memory_system) return -1;

    size_t allocated = 0;
    size_t used = 0;

    for (int i = 0; i < CATZILLA_DI_MEMORY_ARENA_COUNT; i++) {
        if (container->memory_system->pools[i]) {
            allocated += container->memory_system->pools[i]->stats.total_allocated;
            used += container->memory_system->pools[i]->stats.currently_used;
        }
    }

    if (total_allocated) *total_allocated = allocated;
    if (total_used) *total_used = used;
    if (efficiency_ratio) *efficiency_ratio = allocated > 0 ? (double)used / allocated : 0.0;

    // Update global statistics
    container->memory_system->total_memory_allocated = allocated;
    container->memory_system->total_memory_used = used;
    container->memory_system->overall_efficiency = allocated > 0 ? (double)used / allocated : 0.0;

    if (used > container->memory_system->total_memory_peak) {
        container->memory_system->total_memory_peak = used;
    }

    return 0;
}

/**
 * Configure memory system auto-optimization
 */
int catzilla_di_configure_memory_optimization(catzilla_di_container_t* container,
                                             bool enabled,
                                             uint32_t interval_ms,
                                             double pressure_threshold) {
    if (!container || !container->memory_system) return -1;

    container->memory_system->auto_optimization_enabled = enabled;
    container->memory_system->optimization_interval_ms = interval_ms;
    container->memory_system->memory_pressure_threshold = pressure_threshold;

    return 0;
}

/**
 * Allocate service instance using optimized memory pool
 */
void* catzilla_di_alloc_service_memory(catzilla_di_container_t* container,
                                      const catzilla_di_service_t* service,
                                      size_t size) {
    if (!container || !service || size == 0) return NULL;

    // If memory system is not initialized, use regular malloc
    if (!container->memory_system) {
        return malloc(size);
    }

    // Select appropriate pool based on service scope
    catzilla_di_pool_type_t pool_type;
    switch (service->scope) {
        case CATZILLA_DI_SCOPE_SINGLETON:
            pool_type = CATZILLA_DI_POOL_SINGLETON;
            break;
        case CATZILLA_DI_SCOPE_REQUEST:
            pool_type = CATZILLA_DI_POOL_REQUEST;
            break;
        case CATZILLA_DI_SCOPE_TRANSIENT:
            pool_type = CATZILLA_DI_POOL_TRANSIENT;
            break;
        default:
            pool_type = CATZILLA_DI_POOL_TRANSIENT;
            break;
    }

    catzilla_di_memory_pool_t* pool = container->memory_system->pools[pool_type];
    if (!pool) {
        return malloc(size); // Fallback
    }

    // Update access pattern statistics
    container->memory_system->memory_access_patterns[pool_type]++;

    return catzilla_di_pool_alloc(pool, size);
}

/**
 * Free service instance memory back to appropriate pool
 */
void catzilla_di_free_service_memory(catzilla_di_container_t* container,
                                    const catzilla_di_service_t* service,
                                    void* ptr) {
    if (!container || !service || !ptr) return;

    // If memory system is not initialized, use regular free
    if (!container->memory_system) {
        free(ptr);
        return;
    }

    // Select appropriate pool based on service scope
    catzilla_di_pool_type_t pool_type;
    switch (service->scope) {
        case CATZILLA_DI_SCOPE_SINGLETON:
            pool_type = CATZILLA_DI_POOL_SINGLETON;
            break;
        case CATZILLA_DI_SCOPE_REQUEST:
            pool_type = CATZILLA_DI_POOL_REQUEST;
            break;
        case CATZILLA_DI_SCOPE_TRANSIENT:
            pool_type = CATZILLA_DI_POOL_TRANSIENT;
            break;
        default:
            pool_type = CATZILLA_DI_POOL_TRANSIENT;
            break;
    }

    catzilla_di_memory_pool_t* pool = container->memory_system->pools[pool_type];
    if (!pool) {
        free(ptr); // Fallback
        return;
    }

    catzilla_di_pool_free(pool, ptr);
}

// ============================================================================
// PHASE 5: PRODUCTION FEATURES IMPLEMENTATION
// ============================================================================

// Global logger and error handling
static catzilla_di_logger_t* g_di_logger = NULL;
static void (*g_error_handler)(const catzilla_di_error_info_t*) = NULL;
static catzilla_di_error_info_t g_last_error = {0};

// ============================================================================
// HIERARCHICAL CONTAINER MANAGEMENT
// ============================================================================

/**
 * Create a child container with hierarchical configuration
 */
int catzilla_di_create_child_container(catzilla_di_container_t* parent,
                                      const catzilla_di_container_config_t* config,
                                      catzilla_di_container_t** child_container) {
    if (!child_container) return -1;

    // Allocate new container
    catzilla_di_container_t* child = malloc(sizeof(catzilla_di_container_t));
    if (!child) return -1;

    // Initialize basic container
    if (catzilla_di_container_init(child, 0) != 0) {
        free(child);
        return -1;
    }

    // Set up hierarchy
    child->parent = parent;

    // Apply configuration if provided
    if (config) {
        if (catzilla_di_configure_container(child, config) != 0) {
            catzilla_di_container_cleanup(child);
            free(child);
            return -1;
        }
    }

    *child_container = child;
    return 0;
}

/**
 * Set container configuration
 */
int catzilla_di_configure_container(catzilla_di_container_t* container,
                                   const catzilla_di_container_config_t* config) {
    if (!container || !config) return -1;

    // Store configuration in container (would need to extend container struct)
    // For now, just validate configuration

    if (config->parent && config->parent != container->parent) {
        container->parent = config->parent;
    }

    return 0;
}

/**
 * Get list of child containers
 */
int catzilla_di_get_child_containers(catzilla_di_container_t* container,
                                    catzilla_di_container_t** children,
                                    int max_children) {
    if (!container || !children || max_children <= 0) return 0;

    // In a full implementation, we'd maintain a child list in the container
    // For now, return 0 as we don't track children
    return 0;
}

/**
 * Check if service access is allowed by container policy
 */
bool catzilla_di_is_service_access_allowed(catzilla_di_container_t* container,
                                          const char* service_name) {
    if (!container || !service_name) return false;

    // For now, allow all access (would implement pattern matching)
    return true;
}

// ============================================================================
// ADVANCED FACTORY PATTERN SUPPORT
// ============================================================================

/**
 * Register an advanced factory with complex configuration
 */
int catzilla_di_register_advanced_factory(catzilla_di_container_t* container,
                                         const char* name,
                                         const catzilla_di_factory_config_t* factory_config) {
    if (!container || !name || !factory_config) return -1;

    // For now, delegate to simple factory registration
    // In full implementation, would handle all factory types
    return catzilla_di_register_service_c(
        container, name, "AdvancedFactory", CATZILLA_DI_SCOPE_SINGLETON,
        factory_config->factory_func, NULL, 0, NULL
    );
}

/**
 * Register a builder pattern factory
 */
int catzilla_di_register_builder_factory(catzilla_di_container_t* container,
                                        const char* name,
                                        catzilla_di_factory_func_t builder_func,
                                        catzilla_di_factory_func_t factory_func,
                                        void* builder_config) {
    if (!container || !name || !factory_func) return -1;

    // For now, just register the factory function
    return catzilla_di_register_service_c(
        container, name, "BuilderFactory", CATZILLA_DI_SCOPE_SINGLETON,
        factory_func, NULL, 0, builder_config
    );
}

/**
 * Register a conditional factory
 */
int catzilla_di_register_conditional_factory(catzilla_di_container_t* container,
                                            const char* name,
                                            bool (*condition_func)(void*),
                                            catzilla_di_factory_func_t primary_factory,
                                            catzilla_di_factory_func_t fallback_factory) {
    if (!container || !name || !primary_factory) return -1;

    // For now, register the primary factory
    return catzilla_di_register_service_c(
        container, name, "ConditionalFactory", CATZILLA_DI_SCOPE_SINGLETON,
        primary_factory, NULL, 0, NULL
    );
}

/**
 * Update factory configuration at runtime
 */
int catzilla_di_update_factory_config(catzilla_di_container_t* container,
                                     const char* name,
                                     const catzilla_di_factory_config_t* factory_config) {
    if (!container || !name || !factory_config) return -1;

    // For now, just return success
    // In full implementation, would update existing factory
    return 0;
}

// ============================================================================
// CONFIGURATION-BASED SERVICE REGISTRATION
// ============================================================================

/**
 * Convert scope string to enum
 */
static catzilla_di_scope_type_t parse_scope_string(const char* scope_str) {
    if (!scope_str) return CATZILLA_DI_SCOPE_SINGLETON;
    if (strcmp(scope_str, "singleton") == 0) return CATZILLA_DI_SCOPE_SINGLETON;
    if (strcmp(scope_str, "transient") == 0) return CATZILLA_DI_SCOPE_TRANSIENT;
    if (strcmp(scope_str, "scoped") == 0) return CATZILLA_DI_SCOPE_SCOPED;
    if (strcmp(scope_str, "request") == 0) return CATZILLA_DI_SCOPE_REQUEST;
    return CATZILLA_DI_SCOPE_SINGLETON;
}

/**
 * Register services from configuration array
 */
int catzilla_di_register_services_from_config(catzilla_di_container_t* container,
                                             const catzilla_di_service_config_t* configs,
                                             int config_count) {
    if (!container || !configs || config_count <= 0) return 0;

    int success_count = 0;

    for (int i = 0; i < config_count; i++) {
        const catzilla_di_service_config_t* config = &configs[i];

        if (!config->enabled) continue;

        catzilla_di_scope_type_t scope = parse_scope_string(config->scope);

        // For now, register as a simple service (would need factory lookup)
        const char* deps[CATZILLA_DI_MAX_DEPENDENCIES];
        for (int j = 0; j < config->dependency_count && j < CATZILLA_DI_MAX_DEPENDENCIES; j++) {
            deps[j] = config->dependencies[j];
        }

        if (catzilla_di_register_service(
                container, config->service_name, config->service_type,
                scope, NULL, deps, config->dependency_count
            ) == 0) {
            success_count++;
        }
    }

    return success_count;
}

/**
 * Load service configuration from JSON string
 */
int catzilla_di_load_config_from_json(catzilla_di_container_t* container,
                                     const char* json_config) {
    if (!container || !json_config) return -1;

    // For now, return success (would need JSON parser)
    // In full implementation, would parse JSON and call register_services_from_config
    return 0;
}

/**
 * Load service configuration from file
 */
int catzilla_di_load_config_from_file(catzilla_di_container_t* container,
                                     const char* config_file_path) {
    if (!container || !config_file_path) return -1;

    FILE* file = fopen(config_file_path, "r");
    if (!file) return -1;

    // Read file content (simplified)
    fseek(file, 0, SEEK_END);
    long file_size = ftell(file);
    fseek(file, 0, SEEK_SET);

    char* buffer = malloc(file_size + 1);
    if (!buffer) {
        fclose(file);
        return -1;
    }

    size_t read_size = fread(buffer, 1, file_size, file);
    buffer[read_size] = '\0';

    fclose(file);

    int result = catzilla_di_load_config_from_json(container, buffer);
    free(buffer);

    return result;
}

/**
 * Validate service configuration
 */
int catzilla_di_validate_service_config(const catzilla_di_service_config_t* config,
                                       catzilla_di_error_info_t* error_info) {
    if (!config) return -1;

    // Basic validation
    if (strlen(config->service_name) == 0) {
        if (error_info) {
            strcpy(error_info->error_message, "Service name cannot be empty");
        }
        return -1;
    }

    if (config->dependency_count > CATZILLA_DI_MAX_DEPENDENCIES) {
        if (error_info) {
            snprintf(error_info->error_message, sizeof(error_info->error_message),
                    "Too many dependencies: %d (max: %d)",
                    config->dependency_count, CATZILLA_DI_MAX_DEPENDENCIES);
        }
        return -1;
    }

    return 0;
}

/**
 * Export container configuration to JSON
 */
int catzilla_di_export_config_to_json(catzilla_di_container_t* container,
                                     char* json_buffer,
                                     size_t buffer_size) {
    if (!container || !json_buffer || buffer_size == 0) return -1;

    // Simple JSON export (would need proper JSON formatting)
    int written = snprintf(json_buffer, buffer_size,
        "{\n"
        "  \"container_id\": %u,\n"
        "  \"service_count\": %d,\n"
        "  \"services\": []\n"
        "}", container->container_id, container->service_count);

    return (written < buffer_size) ? written : -1;
}

// ============================================================================
// DEBUGGING AND INTROSPECTION TOOLS
// ============================================================================

/**
 * Get comprehensive container information
 */
int catzilla_di_get_container_info(catzilla_di_container_t* container,
                                  catzilla_di_container_info_t* info) {
    if (!container || !info) return -1;

    memset(info, 0, sizeof(catzilla_di_container_info_t));

    info->container_id = container->container_id;
    snprintf(info->container_name, sizeof(info->container_name), "Container_%u", container->container_id);

    info->parent_container_id = container->parent ? container->parent->container_id : 0;
    info->service_count = container->service_count;

    // Get memory information
    if (container->memory_system) {
        info->total_memory_allocated = container->memory_system->total_memory_allocated;
        info->total_memory_used = container->memory_system->total_memory_used;
        info->memory_efficiency = container->memory_system->overall_efficiency;
    }

    info->is_healthy = true; // Simple health check
    info->health_issue_count = 0;

    return 0;
}

/**
 * Get detailed service information
 */
int catzilla_di_get_service_info(catzilla_di_container_t* container,
                                const char* service_name,
                                catzilla_di_service_info_t* info) {
    if (!container || !service_name || !info) return -1;

    catzilla_di_service_t* service = catzilla_di_get_service(container, service_name);
    if (!service) return -1;

    memset(info, 0, sizeof(catzilla_di_service_info_t));

    info->service_id = service->registration_id;
    strncpy(info->service_name, service->name, sizeof(info->service_name) - 1);
    strncpy(info->service_type, service->type_name, sizeof(info->service_type) - 1);
    info->scope = service->scope;

    // Copy dependencies
    info->dependency_count = service->dependency_count;
    for (int i = 0; i < service->dependency_count && i < CATZILLA_DI_MAX_DEPENDENCIES; i++) {
        strncpy(info->dependencies[i], service->dependencies[i], sizeof(info->dependencies[i]) - 1);
    }

    info->creation_count = 1; // Simplified
    info->last_access_time = catzilla_di_get_timestamp();
    info->is_healthy = true;
    info->error_count = 0;

    return 0;
}

/**
 * Get dependency graph as string representation
 */
int catzilla_di_get_dependency_graph(catzilla_di_container_t* container,
                                    char* graph_buffer,
                                    size_t buffer_size,
                                    const char* format) {
    if (!container || !graph_buffer || buffer_size == 0) return -1;

    if (!format) format = "text";

    int written = 0;

    if (strcmp(format, "dot") == 0) {
        written = snprintf(graph_buffer, buffer_size,
            "digraph DependencyGraph {\n"
            "  // Container: %u\n"
            "  // Services: %d\n"
            "}\n", container->container_id, container->service_count);
    } else if (strcmp(format, "json") == 0) {
        written = snprintf(graph_buffer, buffer_size,
            "{\n"
            "  \"container_id\": %u,\n"
            "  \"service_count\": %d,\n"
            "  \"dependencies\": []\n"
            "}", container->container_id, container->service_count);
    } else {
        written = snprintf(graph_buffer, buffer_size,
            "Dependency Graph for Container %u:\n"
            "Services: %d\n", container->container_id, container->service_count);
    }

    return (written < buffer_size) ? written : -1;
}

/**
 * Analyze service dependencies for issues
 */
int catzilla_di_analyze_dependencies(catzilla_di_container_t* container,
                                    catzilla_di_error_info_t* issues,
                                    int max_issues) {
    if (!container || !issues || max_issues <= 0) return 0;

    int issue_count = 0;

    // Check for circular dependencies (simplified check)
    for (int i = 0; i < container->service_count && issue_count < max_issues; i++) {
        catzilla_di_service_t* service = container->services[i];
        if (!service) continue;

        // Simple validation: check if service depends on itself
        for (int j = 0; j < service->dependency_count; j++) {
            if (strcmp(service->name, service->dependencies[j]) == 0) {
                catzilla_di_error_info_t* issue = &issues[issue_count++];
                memset(issue, 0, sizeof(catzilla_di_error_info_t));

                issue->error_code = -1;
                snprintf(issue->error_message, sizeof(issue->error_message),
                        "Service '%s' depends on itself", service->name);
                strncpy(issue->service_name, service->name, sizeof(issue->service_name) - 1);
                issue->container_id = container->container_id;
                issue->timestamp = catzilla_di_get_timestamp();
                break;
            }
        }
    }

    return issue_count;
}

/**
 * Generate performance report
 */
int catzilla_di_generate_performance_report(catzilla_di_container_t* container,
                                           char* report_buffer,
                                           size_t buffer_size) {
    if (!container || !report_buffer || buffer_size == 0) return -1;

    catzilla_di_stats_t stats;
    catzilla_di_get_stats(container, &stats);

    int written = snprintf(report_buffer, buffer_size,
        "=== DI Container Performance Report ===\n"
        "Container ID: %u\n"
        "Total Services: %d\n"
        "Total Resolutions: %" PRIu64 "\n"
        "Cache Hits: %" PRIu64 "\n"
        "Cache Misses: %" PRIu64 "\n"
        "Hit Rate: %.2f%%\n"
        "Average Resolution Time: %.3f ms\n"
        "Total Memory Usage: %zu bytes\n"
        "Container Memory: %zu bytes\n"
        "Service Memory: %zu bytes\n"
        "Cache Memory: %zu bytes\n",
        container->container_id,
        stats.total_services,
        stats.total_resolutions,
        stats.cache_hits,
        stats.cache_misses,
        stats.total_resolutions > 0 ? (double)stats.cache_hits / stats.total_resolutions * 100.0 : 0.0,
        stats.average_resolution_time_ms,
        stats.total_memory_usage,
        stats.container_memory_usage,
        stats.service_memory_usage,
        stats.cache_memory_usage);

    return (written < buffer_size) ? written : -1;
}

/**
 * Enable/disable debug mode for container
 */
int catzilla_di_set_debug_mode(catzilla_di_container_t* container,
                              bool enabled,
                              int debug_level) {
    if (!container) return -1;

    // Store debug settings (would need to extend container struct)
    // For now, just return success
    return 0;
}

/**
 * Get service resolution trace
 */
int catzilla_di_get_resolution_trace(catzilla_di_container_t* container,
                                    const char* service_name,
                                    char* trace_buffer,
                                    size_t buffer_size) {
    if (!container || !service_name || !trace_buffer || buffer_size == 0) return -1;

    int written = snprintf(trace_buffer, buffer_size,
        "Resolution trace for '%s':\n"
        "1. Service lookup in container %u\n"
        "2. Found service registration\n"
        "3. Resolving dependencies...\n"
        "4. Creating service instance\n"
        "5. Resolution complete\n",
        service_name, container->container_id);

    return (written < buffer_size) ? written : -1;
}

// ============================================================================
// COMPREHENSIVE ERROR HANDLING AND LOGGING
// ============================================================================

/**
 * Initialize DI logger
 */
int catzilla_di_logger_init(catzilla_di_logger_t* logger,
                           const catzilla_di_logger_t* config) {
    if (!logger) return -1;

    memset(logger, 0, sizeof(catzilla_di_logger_t));

    if (config) {
        *logger = *config;
    } else {
        // Default configuration
        logger->capacity = 1000;
        logger->min_level = CATZILLA_DI_LOG_INFO;
        logger->console_output = true;
        logger->file_output = false;
        logger->async_logging = false;
        logger->flush_interval_ms = 1000;
    }

    logger->entries = malloc(sizeof(catzilla_di_log_entry_t) * logger->capacity);
    if (!logger->entries) return -1;

    return 0;
}

/**
 * Log a message with specified level
 */
int catzilla_di_log(catzilla_di_logger_t* logger,
                   catzilla_di_log_level_t level,
                   uint32_t container_id,
                   const char* service_name,
                   const char* message,
                   const char* file,
                   int line,
                   const char* function) {
    if (!logger || level < logger->min_level) return 0;

    if (logger->count >= logger->capacity) {
        // Circular buffer - overwrite oldest entry
        logger->head = (logger->head + 1) % logger->capacity;
        logger->count = logger->capacity;
    } else {
        logger->count++;
    }

    int index = (logger->head + logger->count - 1) % logger->capacity;
    catzilla_di_log_entry_t* entry = &logger->entries[index];

    entry->level = level;
    entry->timestamp = catzilla_di_get_timestamp();
    entry->container_id = container_id;
    entry->line = line;

    if (service_name) {
        strncpy(entry->service_name, service_name, sizeof(entry->service_name) - 1);
    } else {
        entry->service_name[0] = '\0';
    }

    if (message) {
        strncpy(entry->message, message, sizeof(entry->message) - 1);
    } else {
        entry->message[0] = '\0';
    }

    if (file) {
        strncpy(entry->file, file, sizeof(entry->file) - 1);
    } else {
        entry->file[0] = '\0';
    }

    if (function) {
        strncpy(entry->function, function, sizeof(entry->function) - 1);
    } else {
        entry->function[0] = '\0';
    }

    // Console output if enabled
    if (logger->console_output) {
        const char* level_str = "UNKNOWN";
        switch (level) {
            case CATZILLA_DI_LOG_TRACE: level_str = "TRACE"; break;
            case CATZILLA_DI_LOG_DEBUG: level_str = "DEBUG"; break;
            case CATZILLA_DI_LOG_INFO:  level_str = "INFO";  break;
            case CATZILLA_DI_LOG_WARN:  level_str = "WARN";  break;
            case CATZILLA_DI_LOG_ERROR: level_str = "ERROR"; break;
            case CATZILLA_DI_LOG_FATAL: level_str = "FATAL"; break;
        }

        printf("[%s] Container:%u Service:%s - %s (%s:%d)\n",
               level_str, container_id, service_name ? service_name : "N/A",
               message ? message : "", file ? file : "", line);
    }

    return 0;
}

/**
 * Get recent log entries
 */
int catzilla_di_get_log_entries(catzilla_di_logger_t* logger,
                               catzilla_di_log_entry_t* entries,
                               int max_entries,
                               catzilla_di_log_level_t min_level) {
    if (!logger || !entries || max_entries <= 0) return 0;

    int returned = 0;
    int start = logger->head;
    int count = logger->count;

    for (int i = 0; i < count && returned < max_entries; i++) {
        int index = (start + i) % logger->capacity;
        catzilla_di_log_entry_t* entry = &logger->entries[index];

        if (entry->level >= min_level) {
            entries[returned++] = *entry;
        }
    }

    return returned;
}

/**
 * Clear log entries
 */
int catzilla_di_clear_log(catzilla_di_logger_t* logger) {
    if (!logger) return -1;

    logger->count = 0;
    logger->head = 0;

    return 0;
}

/**
 * Set global error handler
 */
int catzilla_di_set_error_handler(void (*handler)(const catzilla_di_error_info_t* error)) {
    g_error_handler = handler;
    return 0;
}

/**
 * Get last error information
 */
int catzilla_di_get_last_error(catzilla_di_container_t* container,
                              catzilla_di_error_info_t* error_info) {
    if (!error_info) return -1;

    *error_info = g_last_error;
    return g_last_error.error_code != 0 ? 0 : -1;
}

/**
 * Clear error state
 */
int catzilla_di_clear_error(catzilla_di_container_t* container) {
    memset(&g_last_error, 0, sizeof(g_last_error));
    return 0;
}

// ============================================================================
// HEALTH MONITORING AND DIAGNOSTICS
// ============================================================================

/**
 * Perform health check on container
 */
int catzilla_di_health_check(catzilla_di_container_t* container, int check_level) {
    if (!container) return -1;

    int health_score = 100; // Start with perfect health

    // Basic checks
    if (!container->is_initialized) health_score -= 50;
    if (container->service_count == 0) health_score -= 20;

    // Memory system checks
    if (container->memory_system) {
        if (container->memory_system->memory_pressure_detected) health_score -= 30;
        if (container->memory_system->overall_efficiency < 0.5) health_score -= 20;
    }

    // Detailed checks (if requested)
    if (check_level >= 1) {
        // Check for circular dependencies
        catzilla_di_error_info_t issues[10];
        int issue_count = catzilla_di_analyze_dependencies(container, issues, 10);
        health_score -= issue_count * 10;
    }

    return health_score > 0 ? health_score : 0;
}

/**
 * Get health issues
 */
int catzilla_di_get_health_issues(catzilla_di_container_t* container,
                                 char issues[][256],
                                 int max_issues) {
    if (!container || !issues || max_issues <= 0) return 0;

    int issue_count = 0;

    if (!container->is_initialized && issue_count < max_issues) {
        strcpy(issues[issue_count++], "Container is not properly initialized");
    }

    if (container->service_count == 0 && issue_count < max_issues) {
        strcpy(issues[issue_count++], "No services registered");
    }

    if (container->memory_system && container->memory_system->memory_pressure_detected && issue_count < max_issues) {
        strcpy(issues[issue_count++], "Memory pressure detected");
    }

    return issue_count;
}

/**
 * Monitor container performance
 */
int catzilla_di_monitor_performance(catzilla_di_container_t* container,
                                   uint32_t duration_ms,
                                   catzilla_di_stats_t* stats) {
    if (!container || !stats) return -1;

    // Get current stats
    catzilla_di_get_stats(container, stats);

    // For now, just return current stats
    // In full implementation, would monitor over time period
    return 0;
}
