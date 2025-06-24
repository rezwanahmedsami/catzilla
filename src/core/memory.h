#ifndef CATZILLA_MEMORY_H
#define CATZILLA_MEMORY_H

#include <stddef.h>
#include <stdint.h>
#include <stdbool.h>

// ============================================================================
// 🚀 CATZILLA MEMORY SYSTEM - CONDITIONAL JEMALLOC SUPPORT
// ============================================================================

// Memory allocator backend selection
typedef enum {
    CATZILLA_ALLOCATOR_MALLOC,   // Standard malloc/free
    CATZILLA_ALLOCATOR_JEMALLOC  // jemalloc (if available)
} catzilla_allocator_type_t;

// Include jemalloc headers if available
#ifdef CATZILLA_HAS_JEMALLOC
#include <jemalloc/jemalloc.h>
#endif

/**
 * Memory system statistics
 */
typedef struct {
    // Specialized arenas for different allocation patterns
    unsigned request_arena;      // Short-lived request objects
    unsigned response_arena;     // Medium-lived response data
    unsigned cache_arena;        // Long-lived cache entries
    unsigned static_arena;       // Static file caching
    unsigned task_arena;         // Background task data

    // Memory statistics
    size_t allocated;
    size_t active;
    size_t metadata;
    size_t resident;
    size_t peak_allocated;
    double fragmentation_ratio;
    uint64_t allocation_count;
    uint64_t deallocation_count;

    // Arena-specific usage
    size_t request_arena_usage;
    size_t response_arena_usage;
    size_t cache_arena_usage;
    size_t static_arena_usage;
    size_t task_arena_usage;

    // Performance metrics
    double memory_efficiency_score;
    uint64_t cache_hits;
    uint64_t cache_misses;
} catzilla_memory_stats_t;

/**
 * Memory allocation types for different use cases
 */
typedef enum {
    CATZILLA_MEMORY_REQUEST,   // Request processing allocations
    CATZILLA_MEMORY_RESPONSE,  // Response building allocations
    CATZILLA_MEMORY_CACHE,     // Caching system allocations
    CATZILLA_MEMORY_STATIC,    // Static file serving allocations
    CATZILLA_MEMORY_TASK,      // Background task allocations
    CATZILLA_MEMORY_GENERAL    // General purpose allocations
} catzilla_memory_type_t;

// Core memory allocation functions
void* catzilla_malloc(size_t size);
void* catzilla_calloc(size_t count, size_t size);
void* catzilla_realloc(void* ptr, size_t size);
void catzilla_free(void* ptr);

// Typed memory allocation functions for optimal performance
void* catzilla_request_alloc(size_t size);   // Uses request arena
void* catzilla_response_alloc(size_t size);  // Uses response arena
void* catzilla_cache_alloc(size_t size);     // Uses cache arena
void* catzilla_static_alloc(size_t size);    // Uses static arena
void* catzilla_task_alloc(size_t size);      // Uses task arena

// Typed memory reallocation functions
void* catzilla_request_realloc(void* ptr, size_t size);
void* catzilla_response_realloc(void* ptr, size_t size);
void* catzilla_cache_realloc(void* ptr, size_t size);
void* catzilla_static_realloc(void* ptr, size_t size);
void* catzilla_task_realloc(void* ptr, size_t size);

// Typed memory deallocation functions
void catzilla_request_free(void* ptr);
void catzilla_response_free(void* ptr);
void catzilla_cache_free(void* ptr);
void catzilla_static_free(void* ptr);
void catzilla_task_free(void* ptr);

// Python-safe allocation functions (never use jemalloc for these)
void* catzilla_python_safe_alloc(size_t size);
void* catzilla_python_safe_calloc(size_t count, size_t size);
void* catzilla_python_safe_realloc(void* ptr, size_t size);
void catzilla_python_safe_free(void* ptr);

// Memory management functions
int catzilla_memory_init(void);
int catzilla_memory_init_quiet(int quiet);
int catzilla_memory_init_with_allocator(catzilla_allocator_type_t allocator);
void catzilla_memory_cleanup(void);
void catzilla_memory_get_stats(catzilla_memory_stats_t* stats);
void catzilla_memory_optimize(void);
bool catzilla_memory_has_jemalloc(void);
catzilla_allocator_type_t catzilla_memory_get_current_allocator(void);

// Conditional jemalloc runtime support
bool catzilla_memory_jemalloc_available(void);
int catzilla_memory_set_allocator(catzilla_allocator_type_t allocator);

// Memory profiling and optimization
int catzilla_memory_enable_profiling(void);
void catzilla_memory_disable_profiling(void);
void catzilla_memory_reset_stats(void);
void catzilla_memory_auto_optimize(void);

// Arena management
int catzilla_memory_purge_arena(catzilla_memory_type_t type);
int catzilla_memory_get_arena_stats(catzilla_memory_type_t type, size_t* allocated, size_t* active);

// Memory debugging (debug builds only)
#ifdef DEBUG
void catzilla_memory_dump_stats(void);
void catzilla_memory_check_leaks(void);
void catzilla_memory_track_allocation(void* ptr, size_t size, const char* file, int line);
void catzilla_memory_track_deallocation(void* ptr, const char* file, int line);

#define CATZILLA_MALLOC(size) catzilla_memory_track_alloc(catzilla_malloc(size), size, __FILE__, __LINE__)
#define CATZILLA_FREE(ptr) do { catzilla_memory_track_deallocation(ptr, __FILE__, __LINE__); catzilla_free(ptr); } while(0)
#else
#define CATZILLA_MALLOC(size) catzilla_malloc(size)
#define CATZILLA_FREE(ptr) catzilla_free(ptr)
#endif

#endif // CATZILLA_MEMORY_H
