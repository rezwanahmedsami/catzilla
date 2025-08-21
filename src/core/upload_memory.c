#include "upload_memory.h"
#include "logging.h"
#include "platform_compat.h"
#include <stdlib.h>
#include <string.h>
#include <stdio.h>

// Platform-specific threading includes
#ifndef _WIN32
// Unix systems use standard pthread
#include <pthread.h>
#endif
// Windows systems use the pthread emulation from platform_compat.h

// Platform-specific includes for jemalloc detection
#ifdef __linux__
#include <dlfcn.h>
#elif defined(__APPLE__)
#include <dlfcn.h>
#elif defined(_WIN32)
#include <windows.h>
#endif

// jemalloc function pointers
static void* (*je_malloc)(size_t size) = NULL;
static void (*je_free)(void* ptr) = NULL;
static void* (*je_realloc)(void* ptr, size_t size) = NULL;
static int (*je_mallctl)(const char* name, void* oldp, size_t* oldlenp, void* newp, size_t newlen) = NULL;
static bool g_jemalloc_initialized = false;

// Thread safety for memory manager
#ifdef _WIN32
static CRITICAL_SECTION g_memory_mutex;
static bool g_memory_mutex_initialized = false;

static void ensure_memory_mutex_init(void) {
    if (!g_memory_mutex_initialized) {
        InitializeCriticalSection(&g_memory_mutex);
        g_memory_mutex_initialized = true;
    }
}

#define MEMORY_MUTEX_LOCK() do { ensure_memory_mutex_init(); EnterCriticalSection(&g_memory_mutex); } while(0)
#define MEMORY_MUTEX_UNLOCK() LeaveCriticalSection(&g_memory_mutex)
#else
static pthread_mutex_t g_memory_mutex = PTHREAD_MUTEX_INITIALIZER;
#define MEMORY_MUTEX_LOCK() pthread_mutex_lock(&g_memory_mutex)
#define MEMORY_MUTEX_UNLOCK() pthread_mutex_unlock(&g_memory_mutex)
#endif

// Initialize upload memory manager
upload_memory_manager_t* catzilla_upload_memory_init(void) {
    upload_memory_manager_t* mgr = malloc(sizeof(upload_memory_manager_t));
    if (!mgr) {
        LOG_MEMORY_ERROR("Failed to allocate memory manager");
        return NULL;
    }

    memset(mgr, 0, sizeof(upload_memory_manager_t));

    // Initialize configuration
    mgr->max_pool_size = 100; // Max 100 buffers per pool
    mgr->enable_pooling = true;
    mgr->enable_jemalloc_optimization = true;

    // Detect and initialize jemalloc
    mgr->jemalloc_available = catzilla_jemalloc_detect();
    if (mgr->jemalloc_available && mgr->enable_jemalloc_optimization) {
        if (catzilla_jemalloc_create_arenas(&mgr->arenas) == 0) {
            LOG_MEMORY_INFO("jemalloc arenas created for upload optimization");
        } else {
            LOG_MEMORY_WARN("Failed to create jemalloc arenas, using standard allocation");
            mgr->jemalloc_available = false;
        }
    }

    if (!mgr->jemalloc_available) {
        LOG_MEMORY_INFO("jemalloc not available, using standard memory allocation");
    }

    // Initialize memory pools
    if (mgr->enable_pooling) {
        mgr->small_pool = catzilla_memory_pool_create(8192, 20);    // 8KB buffers
        mgr->medium_pool = catzilla_memory_pool_create(65536, 10);  // 64KB buffers
        mgr->large_pool = catzilla_memory_pool_create(1048576, 5);  // 1MB buffers

        if (!mgr->small_pool || !mgr->medium_pool || !mgr->large_pool) {
            LOG_MEMORY_WARN("Failed to create some memory pools, disabling pooling");
            mgr->enable_pooling = false;
        } else {
            LOG_MEMORY_INFO("Memory pools initialized successfully");
        }
    }

    LOG_MEMORY_INFO("Upload memory manager initialized (jemalloc: %s, pooling: %s)",
             mgr->jemalloc_available ? "enabled" : "disabled",
             mgr->enable_pooling ? "enabled" : "disabled");

    return mgr;
}

// Cleanup memory manager
void catzilla_upload_memory_cleanup(upload_memory_manager_t* mgr) {
    if (!mgr) {
        return;
    }

    MEMORY_MUTEX_LOCK();

    // Cleanup memory pools
    if (mgr->small_pool) {
        catzilla_memory_pool_destroy(mgr->small_pool);
    }
    if (mgr->medium_pool) {
        catzilla_memory_pool_destroy(mgr->medium_pool);
    }
    if (mgr->large_pool) {
        catzilla_memory_pool_destroy(mgr->large_pool);
    }

    // Cleanup jemalloc arenas
    if (mgr->jemalloc_available) {
        catzilla_jemalloc_destroy_arenas(&mgr->arenas);
    }

    // Log final statistics
    LOG_MEMORY_INFO("Memory manager cleanup - Total allocated: %" PRIu64 " bytes, "
             "Total freed: %" PRIu64 " bytes, Peak usage: %" PRIu64 " bytes, "
             "Pool hits: %" PRIu64 ", Pool misses: %" PRIu64,
             mgr->total_allocated, mgr->total_freed, mgr->peak_usage,
             mgr->pool_hits, mgr->pool_misses);

    free(mgr);

    MEMORY_MUTEX_UNLOCK();
}

// Allocate memory with arena optimization
void* catzilla_upload_memory_alloc(upload_memory_manager_t* mgr, size_t size, upload_size_class_t class) {
    if (!mgr || size == 0) {
        return NULL;
    }

    MEMORY_MUTEX_LOCK();

    void* ptr = NULL;

    // Try memory pool first
    if (mgr->enable_pooling) {
        ptr = catzilla_memory_pool_get(mgr, size);
        if (ptr) {
            mgr->pool_hits++;
            mgr->total_allocated += size;
            mgr->allocations_count++;

            if (mgr->total_allocated - mgr->total_freed > mgr->peak_usage) {
                mgr->peak_usage = mgr->total_allocated - mgr->total_freed;
            }

            MEMORY_MUTEX_UNLOCK();
            return ptr;
        }
        mgr->pool_misses++;
    }

    // Use jemalloc arena if available
    if (mgr->jemalloc_available && je_malloc) {
        // TODO: Implement arena-specific allocation based on class
        // For now, use standard jemalloc
        ptr = je_malloc(size);
    } else {
        ptr = malloc(size);
    }

    if (ptr) {
        mgr->total_allocated += size;
        mgr->allocations_count++;

        if (mgr->total_allocated - mgr->total_freed > mgr->peak_usage) {
            mgr->peak_usage = mgr->total_allocated - mgr->total_freed;
        }
    }

    MEMORY_MUTEX_UNLOCK();

    if (!ptr) {
        LOG_MEMORY_ERROR("Failed to allocate %zu bytes", size);
    }

    return ptr;
}

// Reallocate memory
void* catzilla_upload_memory_realloc(upload_memory_manager_t* mgr, void* ptr, size_t old_size, size_t new_size, upload_size_class_t class) {
    if (!mgr) {
        return realloc(ptr, new_size);
    }

    MEMORY_MUTEX_LOCK();

    void* new_ptr = NULL;

    // Use jemalloc if available
    if (mgr->jemalloc_available && je_realloc) {
        new_ptr = je_realloc(ptr, new_size);
    } else {
        new_ptr = realloc(ptr, new_size);
    }

    if (new_ptr) {
        mgr->total_allocated += (new_size - old_size);
        mgr->allocations_count++;

        if (mgr->total_allocated - mgr->total_freed > mgr->peak_usage) {
            mgr->peak_usage = mgr->total_allocated - mgr->total_freed;
        }
    }

    MEMORY_MUTEX_UNLOCK();

    return new_ptr;
}

// Free memory
void catzilla_upload_memory_free(upload_memory_manager_t* mgr, void* ptr, size_t size, upload_size_class_t class) {
    if (!mgr || !ptr) {
        return;
    }

    MEMORY_MUTEX_LOCK();

    // Try to return to pool first
    if (mgr->enable_pooling) {
        catzilla_memory_pool_return(mgr, ptr, size);
        mgr->total_freed += size;
        mgr->frees_count++;
        MEMORY_MUTEX_UNLOCK();
        return;
    }

    // Use jemalloc if available
    if (mgr->jemalloc_available && je_free) {
        je_free(ptr);
    } else {
        free(ptr);
    }

    mgr->total_freed += size;
    mgr->frees_count++;

    MEMORY_MUTEX_UNLOCK();
}

// Get buffer from memory pool
void* catzilla_memory_pool_get(upload_memory_manager_t* mgr, size_t size) {
    if (!mgr->enable_pooling) {
        return NULL;
    }

    memory_pool_t* pool = NULL;

    // Select appropriate pool based on size
    if (size <= 8192) {
        pool = mgr->small_pool;
    } else if (size <= 65536) {
        pool = mgr->medium_pool;
    } else if (size <= 1048576) {
        pool = mgr->large_pool;
    } else {
        // Too large for pooling
        return NULL;
    }

    if (!pool) {
        return NULL;
    }

    return catzilla_memory_pool_acquire(pool);
}

// Return buffer to memory pool
void catzilla_memory_pool_return(upload_memory_manager_t* mgr, void* buffer, size_t size) {
    if (!mgr->enable_pooling || !buffer) {
        return;
    }

    memory_pool_t* pool = NULL;

    // Select appropriate pool based on size
    if (size <= 8192) {
        pool = mgr->small_pool;
    } else if (size <= 65536) {
        pool = mgr->medium_pool;
    } else if (size <= 1048576) {
        pool = mgr->large_pool;
    }

    if (pool) {
        catzilla_memory_pool_release(pool, buffer);
    } else {
        // Not pooled, free directly
        if (mgr->jemalloc_available && je_free) {
            je_free(buffer);
        } else {
            free(buffer);
        }
    }
}

// Detect jemalloc availability
bool catzilla_jemalloc_detect(void) {
    if (g_jemalloc_initialized) {
        return je_malloc != NULL;
    }

    g_jemalloc_initialized = true;

#if defined(__linux__) || defined(__APPLE__)
    // Try to load jemalloc functions
    void* handle = dlopen("libjemalloc.so.2", RTLD_LAZY);
    if (!handle) {
        handle = dlopen("libjemalloc.so.1", RTLD_LAZY);
    }
    if (!handle) {
        handle = dlopen("libjemalloc.dylib", RTLD_LAZY);
    }

    if (handle) {
        je_malloc = dlsym(handle, "je_malloc");
        je_free = dlsym(handle, "je_free");
        je_realloc = dlsym(handle, "je_realloc");
        je_mallctl = dlsym(handle, "je_mallctl");

        if (je_malloc && je_free && je_realloc) {
            LOG_MEMORY_INFO("jemalloc detected and loaded successfully");
            return true;
        } else {
            LOG_MEMORY_WARN("jemalloc library found but functions not available");
            dlclose(handle);
        }
    }
#elif defined(_WIN32)
    // Try to load jemalloc DLL on Windows
    HMODULE handle = LoadLibraryA("jemalloc.dll");
    if (handle) {
        je_malloc = (void*(*)(size_t))GetProcAddress(handle, "je_malloc");
        je_free = (void(*)(void*))GetProcAddress(handle, "je_free");
        je_realloc = (void*(*)(void*, size_t))GetProcAddress(handle, "je_realloc");
        je_mallctl = (int(*)(const char*, void*, size_t*, void*, size_t))GetProcAddress(handle, "je_mallctl");

        if (je_malloc && je_free && je_realloc) {
            LOG_MEMORY_INFO("jemalloc detected and loaded successfully");
            return true;
        } else {
            LOG_MEMORY_WARN("jemalloc library found but functions not available");
            FreeLibrary(handle);
        }
    }
#endif

    LOG_MEMORY_INFO("jemalloc not available, using standard malloc");
    return false;
}

// Create jemalloc arenas
int catzilla_jemalloc_create_arenas(upload_memory_arenas_t* arenas) {
    if (!arenas || !je_mallctl) {
        return -1;
    }

    // Create arenas for different upload sizes
    size_t arena_index;
    size_t arena_index_len = sizeof(arena_index);

    // Small files arena
    if (je_mallctl("arenas.create", &arena_index, &arena_index_len, NULL, 0) == 0) {
        arenas->small_files_arena = arena_index;
        LOG_MEMORY_DEBUG("Created jemalloc arena %zu for small files", arena_index);
    } else {
        LOG_MEMORY_ERROR("Failed to create jemalloc arena for small files");
        return -1;
    }

    // Medium files arena
    if (je_mallctl("arenas.create", &arena_index, &arena_index_len, NULL, 0) == 0) {
        arenas->medium_files_arena = arena_index;
        LOG_MEMORY_DEBUG("Created jemalloc arena %zu for medium files", arena_index);
    } else {
        LOG_MEMORY_ERROR("Failed to create jemalloc arena for medium files");
        return -1;
    }

    // Large files arena
    if (je_mallctl("arenas.create", &arena_index, &arena_index_len, NULL, 0) == 0) {
        arenas->large_files_arena = arena_index;
        LOG_MEMORY_DEBUG("Created jemalloc arena %zu for large files", arena_index);
    } else {
        LOG_MEMORY_ERROR("Failed to create jemalloc arena for large files");
        return -1;
    }

    // Metadata arena
    if (je_mallctl("arenas.create", &arena_index, &arena_index_len, NULL, 0) == 0) {
        arenas->metadata_arena = arena_index;
        LOG_MEMORY_DEBUG("Created jemalloc arena %zu for metadata", arena_index);
    } else {
        LOG_MEMORY_ERROR("Failed to create jemalloc arena for metadata");
        return -1;
    }

    return 0;
}

// Destroy jemalloc arenas
void catzilla_jemalloc_destroy_arenas(upload_memory_arenas_t* arenas) {
    if (!arenas || !je_mallctl) {
        return;
    }

    // TODO: jemalloc doesn't have arena destruction in current API
    // Arenas will be cleaned up when the process exits
    LOG_MEMORY_DEBUG("jemalloc arenas cleanup (automatic on process exit)");
}

// Create memory pool
memory_pool_t* catzilla_memory_pool_create(size_t buffer_size, size_t initial_capacity) {
    memory_pool_t* pool = malloc(sizeof(memory_pool_t));
    if (!pool) {
        LOG_MEMORY_ERROR("Failed to allocate memory pool");
        return NULL;
    }

    memset(pool, 0, sizeof(memory_pool_t));

    pool->buffer_size = buffer_size;
    pool->capacity = initial_capacity;

    // Allocate arrays for tracking buffers
    pool->buffers = malloc(sizeof(void*) * initial_capacity);
    pool->buffer_sizes = malloc(sizeof(size_t) * initial_capacity);
    pool->in_use = malloc(sizeof(bool) * initial_capacity);

    if (!pool->buffers || !pool->buffer_sizes || !pool->in_use) {
        LOG_MEMORY_ERROR("Failed to allocate memory pool arrays");
        free(pool->buffers);
        free(pool->buffer_sizes);
        free(pool->in_use);
        free(pool);
        return NULL;
    }

    // Initialize arrays
    for (size_t i = 0; i < initial_capacity; i++) {
        pool->buffers[i] = malloc(buffer_size);
        pool->buffer_sizes[i] = buffer_size;
        pool->in_use[i] = false;

        if (!pool->buffers[i]) {
            LOG_MEMORY_WARN("Failed to pre-allocate buffer %zu in pool", i);
            continue;
        }
        pool->count++;
    }

    LOG_MEMORY_DEBUG("Created memory pool: %zu byte buffers, %zu/%zu allocated",
              buffer_size, pool->count, initial_capacity);

    return pool;
}

// Destroy memory pool
void catzilla_memory_pool_destroy(memory_pool_t* pool) {
    if (!pool) {
        return;
    }

    // Free all buffers
    if (pool->buffers) {
        for (size_t i = 0; i < pool->capacity; i++) {
            if (pool->buffers[i]) {
                free(pool->buffers[i]);
            }
        }
        free(pool->buffers);
    }

    free(pool->buffer_sizes);
    free(pool->in_use);
    free(pool);

    LOG_MEMORY_DEBUG("Memory pool destroyed");
}

// Acquire buffer from pool
void* catzilla_memory_pool_acquire(memory_pool_t* pool) {
    if (!pool) {
        return NULL;
    }

    // Find available buffer
    for (size_t i = 0; i < pool->capacity; i++) {
        if (pool->buffers[i] && !pool->in_use[i]) {
            pool->in_use[i] = true;
            return pool->buffers[i];
        }
    }

    // No available buffer, allocate new one
    void* new_buffer = malloc(pool->buffer_size);
    if (!new_buffer) {
        LOG_MEMORY_ERROR("Failed to allocate new buffer for pool");
        return NULL;
    }

    LOG_MEMORY_DEBUG("Memory pool miss - allocated new %zu byte buffer", pool->buffer_size);
    return new_buffer;
}

// Release buffer back to pool
void catzilla_memory_pool_release(memory_pool_t* pool, void* buffer) {
    if (!pool || !buffer) {
        return;
    }

    // Find buffer in pool
    for (size_t i = 0; i < pool->capacity; i++) {
        if (pool->buffers[i] == buffer) {
            pool->in_use[i] = false;
            return;
        }
    }

    // Buffer not in pool, free it
    free(buffer);
}

// Get memory statistics
void catzilla_upload_memory_stats(upload_memory_manager_t* mgr, char* buffer, size_t buffer_size) {
    if (!mgr || !buffer || buffer_size == 0) {
        return;
    }

    MEMORY_MUTEX_LOCK();

    snprintf(buffer, buffer_size,
             "Memory Statistics:\n"
             "  Total allocated: %" PRIu64 " bytes\n"
             "  Total freed: %" PRIu64 " bytes\n"
             "  Current usage: %" PRIu64 " bytes\n"
             "  Peak usage: %" PRIu64 " bytes\n"
             "  Allocations: %" PRIu64 "\n"
             "  Frees: %" PRIu64 "\n"
             "  Pool hits: %" PRIu64 "\n"
             "  Pool misses: %" PRIu64 "\n"
             "  jemalloc: %s\n"
             "  Pooling: %s\n",
             mgr->total_allocated,
             mgr->total_freed,
             mgr->total_allocated - mgr->total_freed,
             mgr->peak_usage,
             mgr->allocations_count,
             mgr->frees_count,
             mgr->pool_hits,
             mgr->pool_misses,
             mgr->jemalloc_available ? "enabled" : "disabled",
             mgr->enable_pooling ? "enabled" : "disabled");

    MEMORY_MUTEX_UNLOCK();
}

// Get current memory usage
size_t catzilla_upload_memory_usage(upload_memory_manager_t* mgr) {
    if (!mgr) {
        return 0;
    }

    MEMORY_MUTEX_LOCK();
    size_t usage = mgr->total_allocated - mgr->total_freed;
    MEMORY_MUTEX_UNLOCK();

    return usage;
}

// Calculate memory fragmentation ratio
double catzilla_upload_memory_fragmentation(upload_memory_manager_t* mgr) {
    if (!mgr || mgr->allocations_count == 0) {
        return 0.0;
    }

    MEMORY_MUTEX_LOCK();
    double fragmentation = (double)mgr->pool_misses / (double)(mgr->pool_hits + mgr->pool_misses);
    MEMORY_MUTEX_UNLOCK();

    return fragmentation;
}
