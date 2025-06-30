#ifndef CATZILLA_UPLOAD_MEMORY_H
#define CATZILLA_UPLOAD_MEMORY_H

#include <stdint.h>
#include <stddef.h>
#include <stdbool.h>
#include "upload_parser.h"

#ifdef __cplusplus
extern "C" {
#endif

// Memory arena configuration for different upload sizes
typedef struct {
    size_t small_files_arena;    // < 1MB files
    size_t medium_files_arena;   // 1-50MB files
    size_t large_files_arena;    // > 50MB files (streaming only)
    size_t metadata_arena;       // Headers, filenames, etc.
} upload_memory_arenas_t;

// Memory pool for reusing buffers
typedef struct memory_pool_s {
    void** buffers;
    size_t* buffer_sizes;
    bool* in_use;
    size_t capacity;
    size_t count;
    size_t buffer_size;
    struct memory_pool_s* next;
} memory_pool_t;

// Upload memory manager structure
typedef struct upload_memory_manager_s {
    // jemalloc arena configuration
    upload_memory_arenas_t arenas;
    bool jemalloc_available;

    // Memory pools for different sizes
    memory_pool_t* small_pool;    // 1KB - 64KB buffers
    memory_pool_t* medium_pool;   // 64KB - 1MB buffers
    memory_pool_t* large_pool;    // 1MB+ buffers

    // Statistics
    uint64_t total_allocated;
    uint64_t total_freed;
    uint64_t peak_usage;
    uint64_t allocations_count;
    uint64_t frees_count;
    uint64_t pool_hits;
    uint64_t pool_misses;

    // Configuration
    size_t max_pool_size;
    bool enable_pooling;
    bool enable_jemalloc_optimization;
} upload_memory_manager_t;

// Memory allocation functions
upload_memory_manager_t* catzilla_upload_memory_init(void);
void catzilla_upload_memory_cleanup(upload_memory_manager_t* mgr);

// Allocation functions with arena optimization
void* catzilla_upload_memory_alloc(upload_memory_manager_t* mgr, size_t size, upload_size_class_t class);
void* catzilla_upload_memory_realloc(upload_memory_manager_t* mgr, void* ptr, size_t old_size, size_t new_size, upload_size_class_t class);
void catzilla_upload_memory_free(upload_memory_manager_t* mgr, void* ptr, size_t size, upload_size_class_t class);

// Buffer pool management
void* catzilla_memory_pool_get(upload_memory_manager_t* mgr, size_t size);
void catzilla_memory_pool_return(upload_memory_manager_t* mgr, void* buffer, size_t size);

// Statistics and monitoring
void catzilla_upload_memory_stats(upload_memory_manager_t* mgr, char* buffer, size_t buffer_size);
size_t catzilla_upload_memory_usage(upload_memory_manager_t* mgr);
double catzilla_upload_memory_fragmentation(upload_memory_manager_t* mgr);

// jemalloc integration
bool catzilla_jemalloc_detect(void);
int catzilla_jemalloc_create_arenas(upload_memory_arenas_t* arenas);
void catzilla_jemalloc_destroy_arenas(upload_memory_arenas_t* arenas);

// Memory pool functions
memory_pool_t* catzilla_memory_pool_create(size_t buffer_size, size_t initial_capacity);
void catzilla_memory_pool_destroy(memory_pool_t* pool);
void* catzilla_memory_pool_acquire(memory_pool_t* pool);
void catzilla_memory_pool_release(memory_pool_t* pool, void* buffer);

// Static allocator for small, persistent strings
void* catzilla_static_alloc(size_t size);
void catzilla_static_cleanup(void);

#ifdef __cplusplus
}
#endif

#endif // CATZILLA_UPLOAD_MEMORY_H
