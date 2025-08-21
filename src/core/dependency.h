#ifndef CATZILLA_DEPENDENCY_H
#define CATZILLA_DEPENDENCY_H

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

// Maximum limits for dependency injection
#define CATZILLA_DI_NAME_MAX 128
#define CATZILLA_DI_TYPE_MAX 128
#define CATZILLA_DI_MAX_DEPENDENCIES 32
#define CATZILLA_DI_MAX_SERVICES 1000
#define CATZILLA_DI_CACHE_SIZE 256

// Phase 4: Advanced Memory Optimization Configuration
#define CATZILLA_DI_MEMORY_POOL_SINGLETON_SIZE (64 * 1024)    // 64KB for long-lived singletons
#define CATZILLA_DI_MEMORY_POOL_REQUEST_SIZE (32 * 1024)      // 32KB per request context
#define CATZILLA_DI_MEMORY_POOL_TRANSIENT_SIZE (16 * 1024)    // 16KB for short-lived objects
#define CATZILLA_DI_MEMORY_POOL_FACTORY_SIZE (8 * 1024)       // 8KB for factory instances
#define CATZILLA_DI_MEMORY_POOL_CACHE_SIZE (128 * 1024)       // 128KB for dependency cache
#define CATZILLA_DI_MEMORY_ARENA_COUNT 5                       // Number of specialized arenas
#define CATZILLA_DI_MEMORY_STATS_HISTORY 100                   // Memory usage history samples

// Forward declarations
struct catzilla_di_container_s;
struct catzilla_di_service_s;
struct catzilla_di_context_s;
struct catzilla_di_factory_s;
struct catzilla_di_scope_manager_s;
struct catzilla_di_cache_s;

/**
 * Service scope types for lifecycle management
 */
typedef enum {
    CATZILLA_DI_SCOPE_SINGLETON,     // Single instance shared across application
    CATZILLA_DI_SCOPE_TRANSIENT,     // New instance for each resolution
    CATZILLA_DI_SCOPE_SCOPED,        // Instance per DI context/scope
    CATZILLA_DI_SCOPE_REQUEST        // Instance per HTTP request
} catzilla_di_scope_type_t;

/**
 * Phase 4: Advanced Memory Pool System
 * Specialized memory pools for different dependency lifetimes and patterns
 */

/**
 * Memory pool types for different service lifetimes
 */
typedef enum {
    CATZILLA_DI_POOL_SINGLETON,    // Long-lived singleton instances
    CATZILLA_DI_POOL_REQUEST,      // Request-scoped service instances
    CATZILLA_DI_POOL_TRANSIENT,    // Short-lived transient objects
    CATZILLA_DI_POOL_FACTORY,      // Factory metadata and temporary objects
    CATZILLA_DI_POOL_CACHE         // Dependency resolution cache
} catzilla_di_pool_type_t;

/**
 * Memory pool statistics for monitoring and optimization
 */
typedef struct {
    size_t total_allocated;        // Total bytes allocated from this pool
    size_t currently_used;         // Bytes currently in use
    size_t peak_usage;             // Peak memory usage
    size_t allocation_count;       // Number of allocations
    size_t deallocation_count;     // Number of deallocations
    size_t fragmentation_bytes;    // Estimated fragmentation overhead
    double efficiency_ratio;       // Used / Allocated ratio
    uint64_t last_gc_time;         // Last garbage collection time
} catzilla_di_pool_stats_t;

/**
 * Memory pool configuration for auto-tuning
 */
typedef struct {
    size_t initial_size;           // Initial pool size
    size_t max_size;               // Maximum pool size
    size_t growth_increment;       // Size increment when expanding
    double fragmentation_threshold; // GC trigger threshold (e.g., 0.3 = 30% fragmentation)
    bool auto_tune_enabled;        // Enable automatic size tuning
    uint32_t gc_frequency_ms;      // Garbage collection frequency
} catzilla_di_pool_config_t;

/**
 * Advanced memory pool with lifetime-specific optimization
 */
typedef struct {
    catzilla_di_pool_type_t type;  // Pool type/specialization
    unsigned int arena_id;         // jemalloc arena ID
    void* memory_base;             // Base memory address
    size_t pool_size;              // Current pool size
    size_t allocated_size;         // Currently allocated
    void* next_free;               // Next free memory location

    // Pool configuration and tuning
    catzilla_di_pool_config_t config;
    catzilla_di_pool_stats_t stats;

    // Auto-tuning state
    size_t usage_history[CATZILLA_DI_MEMORY_STATS_HISTORY];
    int history_index;
    uint64_t last_tune_time;

    // Thread safety
    bool is_thread_safe;
    void* lock;                    // Mutex for thread-safe operations
} catzilla_di_memory_pool_t;

/**
 * Comprehensive memory management system for DI container
 */
typedef struct {
    catzilla_di_memory_pool_t* pools[CATZILLA_DI_MEMORY_ARENA_COUNT];

    // Global memory statistics
    size_t total_memory_allocated;
    size_t total_memory_used;
    size_t total_memory_peak;
    double overall_efficiency;

    // Auto-tuning configuration
    bool auto_optimization_enabled;
    uint32_t optimization_interval_ms;
    uint64_t last_optimization_time;

    // Memory pressure detection
    double memory_pressure_threshold;  // Trigger cleanup when exceeded
    bool memory_pressure_detected;
    uint32_t pressure_response_level;  // 0=none, 1=mild, 2=aggressive cleanup

    // Performance monitoring
    uint64_t allocation_performance_ns; // Average allocation time
    uint64_t gc_performance_ns;         // Average GC time
    uint32_t memory_access_patterns[CATZILLA_DI_MEMORY_ARENA_COUNT]; // Access frequency per pool
} catzilla_di_memory_system_t;

/**
 * Service factory function prototype
 * @param dependencies Array of resolved dependency instances
 * @param dependency_count Number of dependencies
 * @param user_data Optional user data passed during registration
 * @return Created service instance or NULL on failure
 */
typedef void* (*catzilla_di_factory_func_t)(void** dependencies, int dependency_count, void* user_data);

/**
 * Service factory configuration
 */
typedef struct catzilla_di_factory_s {
    catzilla_di_factory_func_t create_func;  // Factory function
    void* python_factory;                     // Python factory object reference
    void* user_data;                          // Additional factory data
    bool is_python_factory;                   // Whether to use Python or C factory
} catzilla_di_factory_t;

/**
 * Cache entry for resolved service instances
 */
typedef struct catzilla_di_cache_entry_s {
    char name[CATZILLA_DI_NAME_MAX];
    void* instance;
    uint64_t last_access;
    uint32_t access_count;
    struct catzilla_di_cache_entry_s* next;  // For collision chaining
} catzilla_di_cache_entry_t;

/**
 * High-performance cache for dependency resolution
 */
typedef struct catzilla_di_cache_s {
    catzilla_di_cache_entry_t** buckets;     // Hash table buckets
    int bucket_count;                         // Number of buckets
    int entry_count;                          // Current entry count
    unsigned cache_arena;                     // Memory arena for cache entries
    uint64_t hit_count;                       // Cache hit statistics
    uint64_t miss_count;                      // Cache miss statistics
} catzilla_di_cache_t;

/**
 * Service registration with dependency metadata
 */
typedef struct catzilla_di_service_s {
    char name[CATZILLA_DI_NAME_MAX];         // Service name/key
    char type_name[CATZILLA_DI_TYPE_MAX];    // Type name for validation

    // Service configuration
    catzilla_di_scope_type_t scope;          // Lifecycle scope
    struct catzilla_di_factory_s* factory;          // Instance creation factory

    // Dependencies
    char dependencies[CATZILLA_DI_MAX_DEPENDENCIES][CATZILLA_DI_NAME_MAX];
    int dependency_count;

    // Cached singleton instance
    void* cached_instance;
    bool is_cached;

    // Registration metadata
    uint32_t registration_id;                // Unique registration ID
    uint64_t creation_time;                  // When service was registered
    bool is_circular_dependency_checked;     // Circular dependency validation status
} catzilla_di_service_t;

/**
 * Scope manager for handling different service lifecycles
 */
typedef struct catzilla_di_scope_manager_s {
    struct catzilla_di_cache_s* singleton_cache;    // Cache for singleton instances
    struct catzilla_di_cache_s* scoped_cache;       // Cache for scoped instances
    unsigned scope_arena;                    // Memory arena for scope management
    uint32_t current_scope_id;               // Current scope identifier
} catzilla_di_scope_manager_t;

/**
 * Dependency resolution context (per request/scope)
 */
typedef struct catzilla_di_context_s {
    struct catzilla_di_container_s* container;      // Parent container
    struct catzilla_di_cache_s* resolution_cache;   // Context-local resolution cache
    unsigned context_arena;                  // Memory arena for this context

    // Circular dependency detection
    char resolution_stack[CATZILLA_DI_MAX_DEPENDENCIES][CATZILLA_DI_NAME_MAX];
    int stack_depth;

    // Context metadata
    uint32_t context_id;                     // Unique context ID
    uint64_t creation_time;                  // When context was created
    void* request_data;                      // Associated request data (optional)
} catzilla_di_context_t;

/**
 * Main dependency injection container
 */
typedef struct catzilla_di_container_s {
    // Service storage and lookup
    struct catzilla_route_node_s* service_trie;     // Trie for O(log n) service lookup
    struct catzilla_di_service_s* services[CATZILLA_DI_MAX_SERVICES];
    int service_count;
    int service_capacity;

    // Scope and lifecycle management
    struct catzilla_di_scope_manager_s* scope_manager;

    // Hierarchical container support
    struct catzilla_di_container_s* parent;  // Parent container for delegation

    // Phase 4: Advanced Memory Management System
    catzilla_di_memory_system_t* memory_system;  // Specialized memory pools and optimization

    // Legacy memory management (kept for backward compatibility)
    unsigned container_arena;                // Arena for container metadata
    unsigned service_arena;                  // Arena for service registrations

    // Performance optimization
    struct catzilla_di_cache_s* resolution_cache;   // Container-level resolution cache

    // Container metadata
    uint32_t container_id;                   // Unique container identifier
    uint32_t next_service_id;                // Next service registration ID
    uint64_t creation_time;                  // When container was created
    bool is_initialized;                     // Initialization status
} catzilla_di_container_t;

/**
 * Dependency injection performance statistics
 */
typedef struct catzilla_di_stats_s {
    // Service registration stats
    int total_services;
    int singleton_services;
    int transient_services;
    int scoped_services;

    // Resolution performance
    uint64_t total_resolutions;
    uint64_t cache_hits;
    uint64_t cache_misses;
    double average_resolution_time_ms;

    // Memory usage
    size_t container_memory_usage;
    size_t service_memory_usage;
    size_t cache_memory_usage;
    size_t total_memory_usage;

    // Error tracking
    uint64_t circular_dependency_errors;
    uint64_t service_not_found_errors;
    uint64_t factory_errors;
} catzilla_di_stats_t;

// ============================================================================
// CORE CONTAINER MANAGEMENT API
// ============================================================================

/**
 * Initialize a new dependency injection container
 * @param container Pointer to container structure
 * @param parent Optional parent container for hierarchical DI
 * @return 0 on success, -1 on failure
 */
int catzilla_di_container_init(struct catzilla_di_container_s* container,
                               struct catzilla_di_container_s* parent);

/**
 * Cleanup and free a dependency injection container
 * @param container Pointer to container structure
 */
void catzilla_di_container_cleanup(struct catzilla_di_container_s* container);

/**
 * Create a new dependency injection container (allocates memory)
 * @param parent Optional parent container for hierarchical DI
 * @return New container instance or NULL on failure
 */
struct catzilla_di_container_s* catzilla_di_container_create(struct catzilla_di_container_s* parent);

/**
 * Destroy a dependency injection container (frees memory)
 * @param container Container to destroy
 */
void catzilla_di_container_destroy(struct catzilla_di_container_s* container);

// ============================================================================
// SERVICE REGISTRATION API
// ============================================================================

/**
 * Register a service with the dependency injection container
 * @param container Target container
 * @param name Service name/identifier
 * @param type_name Type name for validation
 * @param scope Service lifecycle scope
 * @param factory Service factory configuration
 * @param dependencies Array of dependency names
 * @param dependency_count Number of dependencies
 * @return 0 on success, -1 on failure
 */
int catzilla_di_register_service(catzilla_di_container_t* container,
                                 const char* name,
                                 const char* type_name,
                                 catzilla_di_scope_type_t scope,
                                 catzilla_di_factory_t* factory,
                                 const char** dependencies,
                                 int dependency_count);

/**
 * Register a service with a C factory function
 * @param container Target container
 * @param name Service name/identifier
 * @param type_name Type name for validation
 * @param scope Service lifecycle scope
 * @param factory_func C factory function
 * @param dependencies Array of dependency names
 * @param dependency_count Number of dependencies
 * @param user_data Optional user data for factory
 * @return 0 on success, -1 on failure
 */
int catzilla_di_register_service_c(catzilla_di_container_t* container,
                                   const char* name,
                                   const char* type_name,
                                   catzilla_di_scope_type_t scope,
                                   catzilla_di_factory_func_t factory_func,
                                   const char** dependencies,
                                   int dependency_count,
                                   void* user_data);

/**
 * Register a service with a Python factory object
 * @param container Target container
 * @param name Service name/identifier
 * @param type_name Type name for validation
 * @param scope Service lifecycle scope
 * @param python_factory Python factory object reference
 * @param dependencies Array of dependency names
 * @param dependency_count Number of dependencies
 * @return 0 on success, -1 on failure
 */
int catzilla_di_register_service_python(catzilla_di_container_t* container,
                                        const char* name,
                                        const char* type_name,
                                        catzilla_di_scope_type_t scope,
                                        void* python_factory,
                                        const char** dependencies,
                                        int dependency_count);

/**
 * Unregister a service from the container
 * @param container Target container
 * @param name Service name to unregister
 * @return 0 on success, -1 if service not found
 */
int catzilla_di_unregister_service(catzilla_di_container_t* container, const char* name);

// ============================================================================
// SERVICE RESOLUTION API
// ============================================================================

/**
 * Resolve a service instance from the container
 * @param container Source container
 * @param name Service name to resolve
 * @param context Optional resolution context (creates one if NULL)
 * @return Service instance or NULL if not found/failed
 */
void* catzilla_di_resolve_service(catzilla_di_container_t* container,
                                  const char* name,
                                  catzilla_di_context_t* context);

/**
 * Resolve multiple services at once (bulk resolution)
 * @param container Source container
 * @param names Array of service names to resolve
 * @param count Number of services to resolve
 * @param context Optional resolution context
 * @param results Output array for resolved instances
 * @return Number of successfully resolved services
 */
int catzilla_di_resolve_services(catzilla_di_container_t* container,
                                 const char** names,
                                 int count,
                                 catzilla_di_context_t* context,
                                 void** results);

/**
 * Check if a service is registered in the container
 * @param container Source container
 * @param name Service name to check
 * @return true if service exists, false otherwise
 */
bool catzilla_di_has_service(catzilla_di_container_t* container, const char* name);

/**
 * Get service metadata without resolving instance
 * @param container Source container
 * @param name Service name
 * @return Service metadata or NULL if not found
 */
catzilla_di_service_t* catzilla_di_get_service(catzilla_di_container_t* container, const char* name);

// ============================================================================
// CONTEXT MANAGEMENT API
// ============================================================================

/**
 * Create a new dependency resolution context
 * @param container Parent container
 * @return New context instance or NULL on failure
 */
catzilla_di_context_t* catzilla_di_create_context(catzilla_di_container_t* container);

/**
 * Cleanup and free a dependency resolution context
 * @param context Context to cleanup
 */
void catzilla_di_cleanup_context(catzilla_di_context_t* context);

/**
 * Associate request data with a resolution context
 * @param context Target context
 * @param request_data Request data to associate
 */
void catzilla_di_context_set_request_data(catzilla_di_context_t* context, void* request_data);

/**
 * Get request data associated with a resolution context
 * @param context Source context
 * @return Associated request data or NULL
 */
void* catzilla_di_context_get_request_data(catzilla_di_context_t* context);

// ============================================================================
// UTILITY AND INTROSPECTION API
// ============================================================================

/**
 * Validate dependency graph for circular dependencies
 * @param container Container to validate
 * @param error_buffer Buffer for error message (optional)
 * @param buffer_size Size of error buffer
 * @return 0 if valid, -1 if circular dependencies found
 */
int catzilla_di_validate_dependencies(catzilla_di_container_t* container,
                                      char* error_buffer,
                                      size_t buffer_size);

/**
 * Get list of all registered service names
 * @param container Source container
 * @param names Output array for service names
 * @param capacity Maximum number of names to return
 * @return Number of service names returned
 */
int catzilla_di_get_service_names(catzilla_di_container_t* container,
                                  char names[][CATZILLA_DI_NAME_MAX],
                                  int capacity);

/**
 * Get dependency injection statistics
 * @param container Source container
 * @param stats Output structure for statistics
 */
void catzilla_di_get_stats(catzilla_di_container_t* container,
                          catzilla_di_stats_t* stats);

/**
 * Reset resolution caches (useful for testing)
 * @param container Target container
 */
void catzilla_di_reset_caches(catzilla_di_container_t* container);

/**
 * Set container-level configuration options
 * @param container Target container
 * @param option Configuration option name
 * @param value Configuration value
 * @return 0 on success, -1 on invalid option
 */
int catzilla_di_set_config(catzilla_di_container_t* container,
                          const char* option,
                          const char* value);

// ============================================================================
// STATISTICS AND MONITORING
// ============================================================================

// ============================================================================
// PHASE 4: ADVANCED MEMORY OPTIMIZATION
// ============================================================================

/**
 * Create and initialize advanced memory system
 * @param container Target container
 * @return 0 on success, -1 on failure
 */
int catzilla_di_init_memory_system(catzilla_di_container_t* container);

/**
 * Destroy and cleanup memory system
 * @param container Target container
 */
void catzilla_di_cleanup_memory_system(catzilla_di_container_t* container);

/**
 * Create a specialized memory pool
 * @param type Pool type/specialization
 * @param config Pool configuration
 * @return Pointer to created pool or NULL on failure
 */
catzilla_di_memory_pool_t* catzilla_di_create_memory_pool(catzilla_di_pool_type_t type,
                                                         const catzilla_di_pool_config_t* config);

/**
 * Destroy a memory pool and free all its resources
 * @param pool Pool to destroy
 */
void catzilla_di_destroy_memory_pool(catzilla_di_memory_pool_t* pool);

/**
 * Allocate memory from a specialized pool
 * @param pool Source pool
 * @param size Bytes to allocate
 * @return Allocated memory or NULL on failure
 */
void* catzilla_di_pool_alloc(catzilla_di_memory_pool_t* pool, size_t size);

/**
 * Free memory back to a specialized pool
 * @param pool Target pool
 * @param ptr Memory to free
 */
void catzilla_di_pool_free(catzilla_di_memory_pool_t* pool, void* ptr);

/**
 * Get memory pool statistics
 * @param pool Target pool
 * @param stats Output statistics structure
 */
void catzilla_di_get_pool_stats(catzilla_di_memory_pool_t* pool,
                               catzilla_di_pool_stats_t* stats);

/**
 * Trigger garbage collection on a memory pool
 * @param pool Target pool
 * @return Bytes freed during GC
 */
size_t catzilla_di_pool_gc(catzilla_di_memory_pool_t* pool);

/**
 * Auto-tune memory pool based on usage patterns
 * @param pool Target pool
 * @return 0 on success, -1 on failure
 */
int catzilla_di_auto_tune_pool(catzilla_di_memory_pool_t* pool);

/**
 * Optimize all memory pools in the system
 * @param container Target container
 * @return Number of pools optimized
 */
int catzilla_di_optimize_memory_pools(catzilla_di_container_t* container);

/**
 * Detect and handle memory pressure
 * @param container Target container
 * @return Pressure level (0=none, 1=mild, 2=severe)
 */
int catzilla_di_detect_memory_pressure(catzilla_di_container_t* container);

/**
 * Get comprehensive memory system statistics
 * @param container Target container
 * @param total_allocated Output: total memory allocated
 * @param total_used Output: total memory currently used
 * @param efficiency_ratio Output: overall memory efficiency
 * @return 0 on success, -1 on failure
 */
int catzilla_di_get_memory_stats(catzilla_di_container_t* container,
                                size_t* total_allocated,
                                size_t* total_used,
                                double* efficiency_ratio);

/**
 * Configure memory system auto-optimization
 * @param container Target container
 * @param enabled Enable/disable auto-optimization
 * @param interval_ms Optimization interval in milliseconds
 * @param pressure_threshold Memory pressure threshold (0.0-1.0)
 * @return 0 on success, -1 on failure
 */
int catzilla_di_configure_memory_optimization(catzilla_di_container_t* container,
                                             bool enabled,
                                             uint32_t interval_ms,
                                             double pressure_threshold);

/**
 * Allocate service instance using optimized memory pool
 * @param container Target container
 * @param service Service being instantiated
 * @param size Memory size needed
 * @return Allocated memory or NULL on failure
 */
void* catzilla_di_alloc_service_memory(catzilla_di_container_t* container,
                                      const catzilla_di_service_t* service,
                                      size_t size);

/**
 * Free service instance memory back to appropriate pool
 * @param container Target container
 * @param service Service being destroyed
 * @param ptr Memory to free
 */
void catzilla_di_free_service_memory(catzilla_di_container_t* container,
                                    const catzilla_di_service_t* service,
                                    void* ptr);

// ============================================================================
// PHASE 5: PRODUCTION FEATURES
// ============================================================================

/**
 * Hierarchical Container Configuration
 * Enables building complex modular DI hierarchies
 */
typedef struct {
    char name[CATZILLA_DI_NAME_MAX];              // Container name for debugging
    struct catzilla_di_container_s* parent;       // Parent container (can be NULL)
    bool inherit_services;                        // Whether to inherit parent services
    bool override_parent_services;                // Allow overriding parent service registrations
    uint32_t isolation_level;                     // 0=full sharing, 1=scoped isolation, 2=full isolation

    // Access control
    char** allowed_service_patterns;              // Glob patterns for allowed services (NULL = all)
    char** denied_service_patterns;               // Glob patterns for denied services (NULL = none)
    int pattern_count;
} catzilla_di_container_config_t;

/**
 * Advanced Factory Pattern Support
 * Supports complex object creation scenarios
 */
typedef enum {
    CATZILLA_DI_FACTORY_SIMPLE,                  // Basic factory function
    CATZILLA_DI_FACTORY_BUILDER,                 // Builder pattern with configuration
    CATZILLA_DI_FACTORY_PROXY,                   // Proxy/wrapper factory
    CATZILLA_DI_FACTORY_CONDITIONAL,             // Conditional creation based on runtime state
    CATZILLA_DI_FACTORY_ASYNC,                   // Asynchronous factory (future support)
} catzilla_di_factory_type_t;

typedef struct catzilla_di_factory_config_s {
    catzilla_di_factory_type_t type;              // Factory type
    catzilla_di_factory_func_t factory_func;     // Primary factory function

    // Builder pattern support
    catzilla_di_factory_func_t builder_func;     // Builder configuration function
    void* builder_config;                        // Builder configuration data

    // Conditional factory support
    bool (*condition_func)(void* context);       // Condition evaluation function
    catzilla_di_factory_func_t alt_factory;      // Alternative factory if condition fails

    // Resource management
    void (*destructor_func)(void* instance);     // Custom destructor
    bool auto_cleanup;                           // Automatic cleanup on scope exit

    // Factory metadata
    char description[256];                       // Factory description for debugging
    uint32_t factory_id;                         // Unique factory identifier
    uint64_t creation_time;                      // When factory was registered
} catzilla_di_factory_config_t;

/**
 * Configuration-Based Service Registration
 * Enables JSON/YAML-based DI configuration
 */
typedef struct {
    char service_name[CATZILLA_DI_NAME_MAX];     // Service name
    char service_type[CATZILLA_DI_TYPE_MAX];     // Service type name
    char scope[32];                              // Scope as string (singleton, transient, etc.)

    // Factory configuration
    char factory_type[32];                       // Factory type (simple, builder, etc.)
    char factory_description[256];               // Factory description

    // Dependencies
    char dependencies[CATZILLA_DI_MAX_DEPENDENCIES][CATZILLA_DI_NAME_MAX];
    int dependency_count;

    // Configuration parameters
    char** config_keys;                          // Configuration parameter names
    char** config_values;                        // Configuration parameter values
    int config_count;

    // Metadata
    bool enabled;                                // Whether service is enabled
    int priority;                                // Service priority (higher = resolved first)
    char tags[16][32];                           // Service tags for grouping/filtering
    int tag_count;
} catzilla_di_service_config_t;

/**
 * Advanced Debugging and Introspection
 */
typedef struct {
    uint32_t service_id;                         // Service identifier
    char service_name[CATZILLA_DI_NAME_MAX];    // Service name
    char service_type[CATZILLA_DI_TYPE_MAX];    // Service type
    catzilla_di_scope_type_t scope;              // Service scope

    // Dependency information
    char dependencies[CATZILLA_DI_MAX_DEPENDENCIES][CATZILLA_DI_NAME_MAX];
    int dependency_count;

    // Runtime statistics
    uint64_t creation_count;                     // How many times service was created
    uint64_t last_access_time;                   // Last time service was accessed
    uint64_t total_resolution_time_ns;           // Total time spent resolving this service
    uint64_t average_resolution_time_ns;         // Average resolution time

    // Memory usage
    size_t instance_memory_size;                 // Memory used by service instances
    size_t metadata_memory_size;                 // Memory used by service metadata

    // Status and health
    bool is_healthy;                             // Service health status
    char last_error[256];                        // Last error message
    uint64_t error_count;                        // Total number of errors
} catzilla_di_service_info_t;

typedef struct {
    uint32_t container_id;                       // Container identifier
    char container_name[CATZILLA_DI_NAME_MAX];  // Container name

    // Hierarchy information
    uint32_t parent_container_id;                // Parent container ID (0 if root)
    uint32_t child_container_ids[16];            // Child container IDs
    int child_count;

    // Service information
    catzilla_di_service_info_t* services;        // Array of service information
    int service_count;

    // Performance metrics
    catzilla_di_stats_t stats;                   // Container statistics

    // Memory system information
    size_t total_memory_allocated;
    size_t total_memory_used;
    double memory_efficiency;

    // Health status
    bool is_healthy;                             // Overall container health
    char health_issues[10][256];                 // Health issue descriptions
    int health_issue_count;
} catzilla_di_container_info_t;

/**
 * Comprehensive Error Handling and Logging
 */
typedef enum {
    CATZILLA_DI_LOG_TRACE,                       // Detailed tracing information
    CATZILLA_DI_LOG_DEBUG,                       // Debug information
    CATZILLA_DI_LOG_INFO,                        // General information
    CATZILLA_DI_LOG_WARN,                        // Warning messages
    CATZILLA_DI_LOG_ERROR,                       // Error messages
    CATZILLA_DI_LOG_FATAL                        // Fatal error messages
} catzilla_di_log_level_t;

typedef struct {
    catzilla_di_log_level_t level;               // Log level
    uint64_t timestamp;                          // Timestamp (nanoseconds since epoch)
    uint32_t container_id;                       // Container that generated the log
    uint32_t context_id;                         // Context that generated the log (0 if none)
    char service_name[CATZILLA_DI_NAME_MAX];    // Service name (if applicable)
    char message[512];                           // Log message
    char file[128];                              // Source file name
    int line;                                    // Source line number
    char function[128];                          // Source function name
} catzilla_di_log_entry_t;

typedef struct {
    catzilla_di_log_entry_t* entries;            // Log entries buffer
    int capacity;                                // Buffer capacity
    int count;                                   // Current number of entries
    int head;                                    // Head index (circular buffer)
    catzilla_di_log_level_t min_level;           // Minimum log level to record

    // Log output configuration
    bool console_output;                         // Output to console
    bool file_output;                            // Output to file
    char log_file_path[256];                     // Log file path

    // Performance
    bool async_logging;                          // Asynchronous logging
    uint32_t flush_interval_ms;                  // Auto-flush interval
} catzilla_di_logger_t;

/**
 * Advanced Error Information
 */
typedef struct {
    int error_code;                              // Error code
    char error_message[512];                     // Human-readable error message
    char service_name[CATZILLA_DI_NAME_MAX];    // Service that caused the error
    char dependency_chain[CATZILLA_DI_MAX_DEPENDENCIES][CATZILLA_DI_NAME_MAX]; // Dependency resolution chain
    int chain_length;

    // Stack trace information
    char stack_trace[2048];                      // Stack trace (if available)

    // Context information
    uint32_t container_id;                       // Container ID
    uint32_t context_id;                         // Context ID
    uint64_t timestamp;                          // When error occurred

    // Debugging aids
    char* debug_info;                            // Additional debug information
    size_t debug_info_size;                      // Size of debug information
} catzilla_di_error_info_t;

// ============================================================================
// PHASE 5: PRODUCTION FEATURES API
// ============================================================================

// Hierarchical Container Management
// ============================================================================

/**
 * Create a child container with hierarchical configuration
 * @param parent Parent container (NULL for root container)
 * @param config Container configuration settings
 * @param child_container Output pointer for created container
 * @return 0 on success, -1 on failure
 */
int catzilla_di_create_child_container(catzilla_di_container_t* parent,
                                      const catzilla_di_container_config_t* config,
                                      catzilla_di_container_t** child_container);

/**
 * Set container configuration
 * @param container Target container
 * @param config Configuration settings
 * @return 0 on success, -1 on failure
 */
int catzilla_di_configure_container(catzilla_di_container_t* container,
                                   const catzilla_di_container_config_t* config);

/**
 * Get list of child containers
 * @param container Parent container
 * @param children Output array for child container pointers
 * @param max_children Maximum number of children to return
 * @return Number of child containers returned
 */
int catzilla_di_get_child_containers(catzilla_di_container_t* container,
                                    catzilla_di_container_t** children,
                                    int max_children);

/**
 * Check if service access is allowed by container policy
 * @param container Target container
 * @param service_name Service name to check
 * @return true if allowed, false if denied
 */
bool catzilla_di_is_service_access_allowed(catzilla_di_container_t* container,
                                          const char* service_name);

// Advanced Factory Pattern Support
// ============================================================================

/**
 * Register an advanced factory with complex configuration
 * @param container Target container
 * @param name Service name
 * @param factory_config Advanced factory configuration
 * @return 0 on success, -1 on failure
 */
int catzilla_di_register_advanced_factory(catzilla_di_container_t* container,
                                         const char* name,
                                         const catzilla_di_factory_config_t* factory_config);

/**
 * Register a builder pattern factory
 * @param container Target container
 * @param name Service name
 * @param builder_func Builder configuration function
 * @param factory_func Final factory function
 * @param builder_config Builder configuration data
 * @return 0 on success, -1 on failure
 */
int catzilla_di_register_builder_factory(catzilla_di_container_t* container,
                                        const char* name,
                                        catzilla_di_factory_func_t builder_func,
                                        catzilla_di_factory_func_t factory_func,
                                        void* builder_config);

/**
 * Register a conditional factory
 * @param container Target container
 * @param name Service name
 * @param condition_func Condition evaluation function
 * @param primary_factory Primary factory (when condition is true)
 * @param fallback_factory Fallback factory (when condition is false)
 * @return 0 on success, -1 on failure
 */
int catzilla_di_register_conditional_factory(catzilla_di_container_t* container,
                                            const char* name,
                                            bool (*condition_func)(void*),
                                            catzilla_di_factory_func_t primary_factory,
                                            catzilla_di_factory_func_t fallback_factory);

/**
 * Update factory configuration at runtime
 * @param container Target container
 * @param name Service name
 * @param factory_config New factory configuration
 * @return 0 on success, -1 on failure
 */
int catzilla_di_update_factory_config(catzilla_di_container_t* container,
                                     const char* name,
                                     const catzilla_di_factory_config_t* factory_config);

// Configuration-Based Service Registration
// ============================================================================

/**
 * Register services from configuration array
 * @param container Target container
 * @param configs Array of service configurations
 * @param config_count Number of configurations
 * @return Number of successfully registered services
 */
int catzilla_di_register_services_from_config(catzilla_di_container_t* container,
                                             const catzilla_di_service_config_t* configs,
                                             int config_count);

/**
 * Load service configuration from JSON string
 * @param container Target container
 * @param json_config JSON configuration string
 * @return 0 on success, -1 on failure
 */
int catzilla_di_load_config_from_json(catzilla_di_container_t* container,
                                     const char* json_config);

/**
 * Load service configuration from file
 * @param container Target container
 * @param config_file_path Path to configuration file
 * @return 0 on success, -1 on failure
 */
int catzilla_di_load_config_from_file(catzilla_di_container_t* container,
                                     const char* config_file_path);

/**
 * Validate service configuration
 * @param config Service configuration to validate
 * @param error_info Output for error information (optional)
 * @return 0 if valid, -1 if invalid
 */
int catzilla_di_validate_service_config(const catzilla_di_service_config_t* config,
                                       catzilla_di_error_info_t* error_info);

/**
 * Export container configuration to JSON
 * @param container Source container
 * @param json_buffer Output buffer for JSON string
 * @param buffer_size Size of output buffer
 * @return Length of JSON string, or -1 on failure
 */
int catzilla_di_export_config_to_json(catzilla_di_container_t* container,
                                     char* json_buffer,
                                     size_t buffer_size);

// Debugging and Introspection Tools
// ============================================================================

/**
 * Get comprehensive container information
 * @param container Target container
 * @param info Output structure for container information
 * @return 0 on success, -1 on failure
 */
int catzilla_di_get_container_info(catzilla_di_container_t* container,
                                  catzilla_di_container_info_t* info);

/**
 * Get detailed service information
 * @param container Target container
 * @param service_name Service name
 * @param info Output structure for service information
 * @return 0 on success, -1 on failure
 */
int catzilla_di_get_service_info(catzilla_di_container_t* container,
                                const char* service_name,
                                catzilla_di_service_info_t* info);

/**
 * Get dependency graph as string representation
 * @param container Target container
 * @param graph_buffer Output buffer for graph string
 * @param buffer_size Size of output buffer
 * @param format Graph format ("dot", "json", "text")
 * @return Length of graph string, or -1 on failure
 */
int catzilla_di_get_dependency_graph(catzilla_di_container_t* container,
                                    char* graph_buffer,
                                    size_t buffer_size,
                                    const char* format);

/**
 * Analyze service dependencies for issues
 * @param container Target container
 * @param issues Output array for detected issues
 * @param max_issues Maximum number of issues to return
 * @return Number of issues found
 */
int catzilla_di_analyze_dependencies(catzilla_di_container_t* container,
                                    catzilla_di_error_info_t* issues,
                                    int max_issues);

/**
 * Generate performance report
 * @param container Target container
 * @param report_buffer Output buffer for performance report
 * @param buffer_size Size of output buffer
 * @return Length of report string, or -1 on failure
 */
int catzilla_di_generate_performance_report(catzilla_di_container_t* container,
                                           char* report_buffer,
                                           size_t buffer_size);

/**
 * Enable/disable debug mode for container
 * @param container Target container
 * @param enabled Enable debug mode
 * @param debug_level Debug level (0-3, higher = more verbose)
 * @return 0 on success, -1 on failure
 */
int catzilla_di_set_debug_mode(catzilla_di_container_t* container,
                              bool enabled,
                              int debug_level);

/**
 * Get service resolution trace
 * @param container Target container
 * @param service_name Service name
 * @param trace_buffer Output buffer for trace information
 * @param buffer_size Size of output buffer
 * @return Length of trace string, or -1 on failure
 */
int catzilla_di_get_resolution_trace(catzilla_di_container_t* container,
                                    const char* service_name,
                                    char* trace_buffer,
                                    size_t buffer_size);

// Comprehensive Error Handling and Logging
// ============================================================================

/**
 * Initialize DI logger
 * @param logger Logger instance to initialize
 * @param config Logger configuration
 * @return 0 on success, -1 on failure
 */
int catzilla_di_logger_init(catzilla_di_logger_t* logger,
                           const catzilla_di_logger_t* config);

/**
 * Log a message with specified level
 * @param logger Logger instance
 * @param level Log level
 * @param container_id Container ID (0 if not applicable)
 * @param service_name Service name (NULL if not applicable)
 * @param message Log message
 * @param file Source file name
 * @param line Source line number
 * @param function Source function name
 * @return 0 on success, -1 on failure
 */
int catzilla_di_log(catzilla_di_logger_t* logger,
                   catzilla_di_log_level_t level,
                   uint32_t container_id,
                   const char* service_name,
                   const char* message,
                   const char* file,
                   int line,
                   const char* function);

/**
 * Get recent log entries
 * @param logger Logger instance
 * @param entries Output array for log entries
 * @param max_entries Maximum number of entries to return
 * @param min_level Minimum log level to include
 * @return Number of entries returned
 */
int catzilla_di_get_log_entries(catzilla_di_logger_t* logger,
                               catzilla_di_log_entry_t* entries,
                               int max_entries,
                               catzilla_di_log_level_t min_level);

/**
 * Clear log entries
 * @param logger Logger instance
 * @return 0 on success, -1 on failure
 */
int catzilla_di_clear_log(catzilla_di_logger_t* logger);

/**
 * Set global error handler
 * @param handler Error handler function
 * @return 0 on success, -1 on failure
 */
int catzilla_di_set_error_handler(void (*handler)(const catzilla_di_error_info_t* error));

/**
 * Get last error information
 * @param container Target container (NULL for global error)
 * @param error_info Output structure for error information
 * @return 0 on success, -1 if no error available
 */
int catzilla_di_get_last_error(catzilla_di_container_t* container,
                              catzilla_di_error_info_t* error_info);

/**
 * Clear error state
 * @param container Target container (NULL for global error)
 * @return 0 on success, -1 on failure
 */
int catzilla_di_clear_error(catzilla_di_container_t* container);

// Health Monitoring and Diagnostics
// ============================================================================

/**
 * Perform health check on container
 * @param container Target container
 * @param check_level Check level (0=basic, 1=detailed, 2=comprehensive)
 * @return Health score (0-100), or -1 on failure
 */
int catzilla_di_health_check(catzilla_di_container_t* container, int check_level);

/**
 * Get health issues
 * @param container Target container
 * @param issues Output array for health issues
 * @param max_issues Maximum number of issues to return
 * @return Number of issues found
 */
int catzilla_di_get_health_issues(catzilla_di_container_t* container,
                                 char issues[][256],
                                 int max_issues);

/**
 * Monitor container performance
 * @param container Target container
 * @param duration_ms Monitoring duration in milliseconds
 * @param stats Output structure for performance statistics
 * @return 0 on success, -1 on failure
 */
int catzilla_di_monitor_performance(catzilla_di_container_t* container,
                                   uint32_t duration_ms,
                                   catzilla_di_stats_t* stats);
#endif // CATZILLA_DEPENDENCY_H
