#include "memory.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <assert.h>
#include <time.h>

// Cross-platform atomic operations
#ifdef _WIN32
    #include <windows.h>
    #define ATOMIC_ADD(ptr, value) InterlockedExchangeAdd((LONG volatile*)(ptr), (LONG)(value))
#else
    // GCC/Clang atomic builtins
    #define ATOMIC_ADD(ptr, value) __sync_fetch_and_add((ptr), (value))
#endif

#ifdef CATZILLA_USE_JEMALLOC
#include <jemalloc/jemalloc.h>

// Cross-platform jemalloc compatibility layer
// Handle different naming conventions across platforms:
// - macOS/Homebrew: direct function names (mallocx, dallocx, etc.)
// - Linux RPM systems: prefixed functions (je_mallocx, je_dallocx, etc.)
// - Windows: potentially different conventions in the future

#ifdef JEMALLOC_USES_PREFIX
    // Use je_ prefixed functions (typical for RPM-based Linux distributions)
    #define JEMALLOC_MALLOCX    je_mallocx
    #define JEMALLOC_DALLOCX    je_dallocx
    #define JEMALLOC_RALLOCX    je_rallocx
    #define JEMALLOC_MALLCTL    je_mallctl
    #define JEMALLOC_MALLOC     je_malloc
    #define JEMALLOC_CALLOC     je_calloc
    #define JEMALLOC_REALLOC    je_realloc
    #define JEMALLOC_FREE       je_free
#else
    // Use direct function names (typical for Homebrew on macOS, some Linux builds)
    #define JEMALLOC_MALLOCX    mallocx
    #define JEMALLOC_DALLOCX    dallocx
    #define JEMALLOC_RALLOCX    rallocx
    #define JEMALLOC_MALLCTL    mallctl
    #define JEMALLOC_MALLOC     malloc
    #define JEMALLOC_CALLOC     calloc
    #define JEMALLOC_REALLOC    realloc
    #define JEMALLOC_FREE       free
#endif

#endif

// Global memory statistics
static catzilla_memory_stats_t g_memory_stats = {0};
static bool g_memory_initialized = false;
static bool g_profiling_enabled = false;

#ifdef CATZILLA_USE_JEMALLOC

// jemalloc-specific implementation

void* catzilla_malloc(size_t size) {
    // Use jemalloc's mallocx with a specific arena to avoid interfering with Python's allocator
    void* ptr = JEMALLOC_MALLOCX(size, MALLOCX_ARENA(g_memory_stats.cache_arena));
    if (ptr && g_profiling_enabled) {
        ATOMIC_ADD(&g_memory_stats.allocation_count, 1);
    }
    return ptr;
}

void* catzilla_calloc(size_t count, size_t size) {
    // Use arena-specific allocation instead of system calloc
    size_t total_size = count * size;
    void* ptr = JEMALLOC_MALLOCX(total_size, MALLOCX_ARENA(g_memory_stats.cache_arena) | MALLOCX_ZERO);
    if (ptr && g_profiling_enabled) {
        ATOMIC_ADD(&g_memory_stats.allocation_count, 1);
    }
    return ptr;
}

void* catzilla_realloc(void* ptr, size_t size) {
    void* new_ptr = JEMALLOC_REALLOC(ptr, size);
    if (new_ptr && !ptr && g_profiling_enabled) {
        ATOMIC_ADD(&g_memory_stats.allocation_count, 1);
    }
    return new_ptr;
}

void catzilla_free(void* ptr) {
    if (ptr) {
        JEMALLOC_FREE(ptr);
        if (g_profiling_enabled) {
            ATOMIC_ADD(&g_memory_stats.deallocation_count, 1);
        }
    }
}

void* catzilla_request_alloc(size_t size) {
    void* ptr = JEMALLOC_MALLOCX(size, MALLOCX_ARENA(g_memory_stats.request_arena));
    if (ptr && g_profiling_enabled) {
        ATOMIC_ADD(&g_memory_stats.allocation_count, 1);
        ATOMIC_ADD(&g_memory_stats.request_arena_usage, size);
    }
    return ptr;
}

void* catzilla_response_alloc(size_t size) {
    void* ptr = JEMALLOC_MALLOCX(size, MALLOCX_ARENA(g_memory_stats.response_arena));
    if (ptr && g_profiling_enabled) {
        ATOMIC_ADD(&g_memory_stats.allocation_count, 1);
        ATOMIC_ADD(&g_memory_stats.response_arena_usage, size);
    }
    return ptr;
}

void* catzilla_cache_alloc(size_t size) {
    void* ptr = JEMALLOC_MALLOCX(size, MALLOCX_ARENA(g_memory_stats.cache_arena));
    if (ptr && g_profiling_enabled) {
        ATOMIC_ADD(&g_memory_stats.allocation_count, 1);
        ATOMIC_ADD(&g_memory_stats.cache_arena_usage, size);
    }
    return ptr;
}

void* catzilla_static_alloc(size_t size) {
    void* ptr = JEMALLOC_MALLOCX(size, MALLOCX_ARENA(g_memory_stats.static_arena));
    if (ptr && g_profiling_enabled) {
        ATOMIC_ADD(&g_memory_stats.allocation_count, 1);
        ATOMIC_ADD(&g_memory_stats.static_arena_usage, size);
    }
    return ptr;
}

void* catzilla_task_alloc(size_t size) {
    void* ptr = JEMALLOC_MALLOCX(size, MALLOCX_ARENA(g_memory_stats.task_arena));
    if (ptr && g_profiling_enabled) {
        ATOMIC_ADD(&g_memory_stats.allocation_count, 1);
        ATOMIC_ADD(&g_memory_stats.task_arena_usage, size);
    }
    return ptr;
}

void catzilla_request_free(void* ptr) {
    if (ptr) {
        JEMALLOC_DALLOCX(ptr, MALLOCX_ARENA(g_memory_stats.request_arena));
        if (g_profiling_enabled) {
            ATOMIC_ADD(&g_memory_stats.deallocation_count, 1);
        }
    }
}

void catzilla_response_free(void* ptr) {
    if (ptr) {
        JEMALLOC_DALLOCX(ptr, MALLOCX_ARENA(g_memory_stats.response_arena));
        if (g_profiling_enabled) {
            ATOMIC_ADD(&g_memory_stats.deallocation_count, 1);
        }
    }
}

void catzilla_cache_free(void* ptr) {
    if (ptr) {
        JEMALLOC_DALLOCX(ptr, MALLOCX_ARENA(g_memory_stats.cache_arena));
        if (g_profiling_enabled) {
            ATOMIC_ADD(&g_memory_stats.deallocation_count, 1);
        }
    }
}

void catzilla_static_free(void* ptr) {
    if (ptr) {
        JEMALLOC_DALLOCX(ptr, MALLOCX_ARENA(g_memory_stats.static_arena));
        if (g_profiling_enabled) {
            ATOMIC_ADD(&g_memory_stats.deallocation_count, 1);
        }
    }
}

void catzilla_task_free(void* ptr) {
    if (ptr) {
        JEMALLOC_DALLOCX(ptr, MALLOCX_ARENA(g_memory_stats.task_arena));
        if (g_profiling_enabled) {
            ATOMIC_ADD(&g_memory_stats.deallocation_count, 1);
        }
    }
}

// Typed reallocation functions for optimal arena management
void* catzilla_request_realloc(void* ptr, size_t size) {
    void* new_ptr = JEMALLOC_RALLOCX(ptr, size, MALLOCX_ARENA(g_memory_stats.request_arena));
    if (new_ptr && g_profiling_enabled) {
        ATOMIC_ADD(&g_memory_stats.allocation_count, 1);
        ATOMIC_ADD(&g_memory_stats.request_arena_usage, size);
    }
    return new_ptr;
}

void* catzilla_response_realloc(void* ptr, size_t size) {
    void* new_ptr = JEMALLOC_RALLOCX(ptr, size, MALLOCX_ARENA(g_memory_stats.response_arena));
    if (new_ptr && g_profiling_enabled) {
        ATOMIC_ADD(&g_memory_stats.allocation_count, 1);
        ATOMIC_ADD(&g_memory_stats.response_arena_usage, size);
    }
    return new_ptr;
}

void* catzilla_cache_realloc(void* ptr, size_t size) {
    void* new_ptr = JEMALLOC_RALLOCX(ptr, size, MALLOCX_ARENA(g_memory_stats.cache_arena));
    if (new_ptr && g_profiling_enabled) {
        ATOMIC_ADD(&g_memory_stats.allocation_count, 1);
        ATOMIC_ADD(&g_memory_stats.cache_arena_usage, size);
    }
    return new_ptr;
}

void* catzilla_static_realloc(void* ptr, size_t size) {
    void* new_ptr = JEMALLOC_RALLOCX(ptr, size, MALLOCX_ARENA(g_memory_stats.static_arena));
    if (new_ptr && g_profiling_enabled) {
        ATOMIC_ADD(&g_memory_stats.allocation_count, 1);
        ATOMIC_ADD(&g_memory_stats.static_arena_usage, size);
    }
    return new_ptr;
}

void* catzilla_task_realloc(void* ptr, size_t size) {
    void* new_ptr = JEMALLOC_RALLOCX(ptr, size, MALLOCX_ARENA(g_memory_stats.task_arena));
    if (new_ptr && g_profiling_enabled) {
        ATOMIC_ADD(&g_memory_stats.allocation_count, 1);
        ATOMIC_ADD(&g_memory_stats.task_arena_usage, size);
    }
    return new_ptr;
}

// Global arena tracking - arenas persist for process lifetime
static bool g_arenas_created = false;

int catzilla_memory_init(void) {
    if (g_memory_initialized) {
        return 0; // Already initialized
    }

    // Note: jemalloc configuration should ideally be done via environment variable:
    // export MALLOC_CONF="background_thread:true,metadata_thp:auto,dirty_decay_ms:10000,muzzy_decay_ms:30000"
    // The config.malloc_conf mallctl is read-only at runtime

    // Try to set some runtime options that are configurable
    bool background_thread = true;
    if (JEMALLOC_MALLCTL("background_thread", NULL, NULL, &background_thread, sizeof(background_thread)) != 0) {
        // This is not critical, continue
    }

    // Set dirty decay for runtime optimization
    ssize_t dirty_decay_ms = 10000;  // 10 seconds
    if (JEMALLOC_MALLCTL("arenas.dirty_decay_ms", NULL, NULL, &dirty_decay_ms, sizeof(dirty_decay_ms)) != 0) {
        // This is not critical for functionality
    }

    // Create specialized arenas only once per process (many jemalloc versions don't support arena destruction)
    if (!g_arenas_created) {
        size_t sz = sizeof(unsigned);

        // Request arena - optimized for short-lived allocations
        if (JEMALLOC_MALLCTL("arenas.create", &g_memory_stats.request_arena, &sz, NULL, 0) != 0) {
            fprintf(stderr, "Error: Failed to create request arena\n");
            return -1;
        }

        // Response arena - optimized for medium-lived allocations
        if (JEMALLOC_MALLCTL("arenas.create", &g_memory_stats.response_arena, &sz, NULL, 0) != 0) {
            fprintf(stderr, "Error: Failed to create response arena\n");
            return -1;
        }

        // Cache arena - optimized for long-lived allocations
        if (JEMALLOC_MALLCTL("arenas.create", &g_memory_stats.cache_arena, &sz, NULL, 0) != 0) {
            fprintf(stderr, "Error: Failed to create cache arena\n");
            return -1;
        }

        // Static arena - optimized for static file caching
        if (JEMALLOC_MALLCTL("arenas.create", &g_memory_stats.static_arena, &sz, NULL, 0) != 0) {
            fprintf(stderr, "Error: Failed to create static arena\n");
            return -1;
        }

        // Task arena - optimized for background task data
        if (JEMALLOC_MALLCTL("arenas.create", &g_memory_stats.task_arena, &sz, NULL, 0) != 0) {
            fprintf(stderr, "Error: Failed to create task arena\n");
            return -1;
        }

        g_arenas_created = true;
    }

    g_memory_initialized = true;
    printf("✅ Catzilla initialized with jemalloc (arenas: req=%u, res=%u, cache=%u, static=%u, task=%u)\n",
           g_memory_stats.request_arena, g_memory_stats.response_arena,
           g_memory_stats.cache_arena, g_memory_stats.static_arena, g_memory_stats.task_arena);

    return 0;
}

void catzilla_memory_get_stats(catzilla_memory_stats_t* stats) {
    if (!stats) return;

    size_t sz = sizeof(size_t);

    // Get jemalloc statistics
    if (JEMALLOC_MALLCTL("stats.allocated", &stats->allocated, &sz, NULL, 0) != 0) {
        stats->allocated = 0;
    }
    if (JEMALLOC_MALLCTL("stats.active", &stats->active, &sz, NULL, 0) != 0) {
        stats->active = 0;
    }
    if (JEMALLOC_MALLCTL("stats.metadata", &stats->metadata, &sz, NULL, 0) != 0) {
        stats->metadata = 0;
    }
    if (JEMALLOC_MALLCTL("stats.resident", &stats->resident, &sz, NULL, 0) != 0) {
        stats->resident = 0;
    }

    // Calculate fragmentation ratio
    if (stats->resident > 0) {
        stats->fragmentation_ratio = (double)stats->active / stats->resident;
    } else {
        stats->fragmentation_ratio = 1.0;
    }

    // Copy arena-specific stats
    stats->request_arena = g_memory_stats.request_arena;
    stats->response_arena = g_memory_stats.response_arena;
    stats->cache_arena = g_memory_stats.cache_arena;
    stats->static_arena = g_memory_stats.static_arena;
    stats->task_arena = g_memory_stats.task_arena;

    stats->request_arena_usage = g_memory_stats.request_arena_usage;
    stats->response_arena_usage = g_memory_stats.response_arena_usage;
    stats->cache_arena_usage = g_memory_stats.cache_arena_usage;
    stats->static_arena_usage = g_memory_stats.static_arena_usage;
    stats->task_arena_usage = g_memory_stats.task_arena_usage;

    stats->allocation_count = g_memory_stats.allocation_count;
    stats->deallocation_count = g_memory_stats.deallocation_count;

    // Calculate efficiency score
    if (stats->allocation_count > 0) {
        double leak_ratio = (double)(stats->allocation_count - stats->deallocation_count) / stats->allocation_count;
        stats->memory_efficiency_score = (1.0 - leak_ratio) * stats->fragmentation_ratio;
    } else {
        stats->memory_efficiency_score = 1.0;
    }

    // Update peak allocated
    if (stats->allocated > g_memory_stats.peak_allocated) {
        g_memory_stats.peak_allocated = stats->allocated;
    }
    stats->peak_allocated = g_memory_stats.peak_allocated;
}

void catzilla_memory_optimize(void) {
    // Trigger jemalloc cleanup for all arenas
    char arena_cmd[64];

    // Purge request arena
    snprintf(arena_cmd, sizeof(arena_cmd), "arena.%u.purge", g_memory_stats.request_arena);
    JEMALLOC_MALLCTL(arena_cmd, NULL, NULL, NULL, 0);

    // Purge response arena
    snprintf(arena_cmd, sizeof(arena_cmd), "arena.%u.purge", g_memory_stats.response_arena);
    JEMALLOC_MALLCTL(arena_cmd, NULL, NULL, NULL, 0);

    // Purge cache arena (less aggressive)
    snprintf(arena_cmd, sizeof(arena_cmd), "arena.%u.decay", g_memory_stats.cache_arena);
    JEMALLOC_MALLCTL(arena_cmd, NULL, NULL, NULL, 0);

    // Purge static arena (least aggressive)
    snprintf(arena_cmd, sizeof(arena_cmd), "arena.%u.decay", g_memory_stats.static_arena);
    JEMALLOC_MALLCTL(arena_cmd, NULL, NULL, NULL, 0);

    // Purge task arena
    snprintf(arena_cmd, sizeof(arena_cmd), "arena.%u.purge", g_memory_stats.task_arena);
    JEMALLOC_MALLCTL(arena_cmd, NULL, NULL, NULL, 0);

    // Global decay
    JEMALLOC_MALLCTL("arenas.dirty_decay", NULL, NULL, NULL, 0);
    JEMALLOC_MALLCTL("arenas.muzzy_decay", NULL, NULL, NULL, 0);
}

bool catzilla_memory_has_jemalloc(void) {
    return true;
}

// Python-safe allocation functions - NEVER use jemalloc for these
// These are specifically for objects that may be accessed by Python's garbage collector
void* catzilla_python_safe_alloc(size_t size) {
    // Always use standard malloc for Python-accessible objects
    return malloc(size);
}

void* catzilla_python_safe_calloc(size_t count, size_t size) {
    // Always use standard calloc for Python-accessible objects
    return calloc(count, size);
}

void* catzilla_python_safe_realloc(void* ptr, size_t size) {
    // Always use standard realloc for Python-accessible objects
    return realloc(ptr, size);
}

void catzilla_python_safe_free(void* ptr) {
    // Always use standard free for Python-accessible objects
    if (ptr) {
        free(ptr);
    }
}

#else // Standard malloc fallback

void* catzilla_malloc(size_t size) {
    void* ptr = malloc(size);
    if (ptr && g_profiling_enabled) {
        ATOMIC_ADD(&g_memory_stats.allocation_count, 1);
    }
    return ptr;
}

void* catzilla_calloc(size_t count, size_t size) {
    void* ptr = calloc(count, size);
    if (ptr && g_profiling_enabled) {
        ATOMIC_ADD(&g_memory_stats.allocation_count, 1);
    }
    return ptr;
}

void* catzilla_realloc(void* ptr, size_t size) {
    void* new_ptr = realloc(ptr, size);
    if (new_ptr && !ptr && g_profiling_enabled) {
        ATOMIC_ADD(&g_memory_stats.allocation_count, 1);
    }
    return new_ptr;
}

void catzilla_free(void* ptr) {
    if (ptr) {
        free(ptr);
        if (g_profiling_enabled) {
            ATOMIC_ADD(&g_memory_stats.deallocation_count, 1);
        }
    }
}

// Fallback implementations (use standard malloc)
void* catzilla_request_alloc(size_t size) { return catzilla_malloc(size); }
void* catzilla_response_alloc(size_t size) { return catzilla_malloc(size); }
void* catzilla_cache_alloc(size_t size) { return catzilla_malloc(size); }
void* catzilla_static_alloc(size_t size) { return catzilla_malloc(size); }
void* catzilla_task_alloc(size_t size) { return catzilla_malloc(size); }

void* catzilla_request_realloc(void* ptr, size_t size) { return catzilla_realloc(ptr, size); }
void* catzilla_response_realloc(void* ptr, size_t size) { return catzilla_realloc(ptr, size); }
void* catzilla_cache_realloc(void* ptr, size_t size) { return catzilla_realloc(ptr, size); }
void* catzilla_static_realloc(void* ptr, size_t size) { return catzilla_realloc(ptr, size); }
void* catzilla_task_realloc(void* ptr, size_t size) { return catzilla_realloc(ptr, size); }

void catzilla_request_free(void* ptr) { catzilla_free(ptr); }
void catzilla_response_free(void* ptr) { catzilla_free(ptr); }
void catzilla_cache_free(void* ptr) { catzilla_free(ptr); }
void catzilla_static_free(void* ptr) { catzilla_free(ptr); }
void catzilla_task_free(void* ptr) { catzilla_free(ptr); }

int catzilla_memory_init(void) {
    g_memory_initialized = true;
    printf("⚠️  Catzilla running with standard malloc (jemalloc not available)\n");
    return 0;
}

void catzilla_memory_get_stats(catzilla_memory_stats_t* stats) {
    if (!stats) return;

    // Basic stats only with standard malloc
    stats->allocated = 0;  // Not available
    stats->active = 0;     // Not available
    stats->metadata = 0;   // Not available
    stats->resident = 0;   // Not available
    stats->fragmentation_ratio = 1.0;
    stats->allocation_count = g_memory_stats.allocation_count;
    stats->deallocation_count = g_memory_stats.deallocation_count;
    stats->memory_efficiency_score = 0.5; // Estimate
    stats->peak_allocated = g_memory_stats.peak_allocated;

    // Arena usage not available
    stats->request_arena_usage = 0;
    stats->response_arena_usage = 0;
    stats->cache_arena_usage = 0;
    stats->static_arena_usage = 0;
    stats->task_arena_usage = 0;
}

void catzilla_memory_optimize(void) {
    // No-op with standard malloc
}

bool catzilla_memory_has_jemalloc(void) {
    return false;
}

// Python-safe allocation functions - use standard malloc (same as fallback)
void* catzilla_python_safe_alloc(size_t size) {
    return malloc(size);
}

void* catzilla_python_safe_calloc(size_t count, size_t size) {
    return calloc(count, size);
}

void* catzilla_python_safe_realloc(void* ptr, size_t size) {
    return realloc(ptr, size);
}

void catzilla_python_safe_free(void* ptr) {
    if (ptr) {
        free(ptr);
    }
}

#endif

// Common implementations
void catzilla_memory_cleanup(void) {
    if (!g_memory_initialized) {
        return; // Nothing to cleanup
    }

    // Note: Many jemalloc versions don't support arena destruction
    // Arenas will persist for the lifetime of the process, which is acceptable
    // for most applications. The memory will be freed when the process exits.

    g_memory_initialized = false;
    g_profiling_enabled = false;

    // Reset counters but keep arena IDs for potential reuse
    catzilla_memory_reset_stats();
}

int catzilla_memory_enable_profiling(void) {
    g_profiling_enabled = true;
    return 0;
}

void catzilla_memory_disable_profiling(void) {
    g_profiling_enabled = false;
}

void catzilla_memory_reset_stats(void) {
    g_memory_stats.allocation_count = 0;
    g_memory_stats.deallocation_count = 0;
    g_memory_stats.peak_allocated = 0;
    g_memory_stats.request_arena_usage = 0;
    g_memory_stats.response_arena_usage = 0;
    g_memory_stats.cache_arena_usage = 0;
    g_memory_stats.static_arena_usage = 0;
    g_memory_stats.task_arena_usage = 0;
    g_memory_stats.cache_hits = 0;
    g_memory_stats.cache_misses = 0;
}

void catzilla_memory_auto_optimize(void) {
    static time_t last_optimize = 0;
    time_t now = time(NULL);

    // Auto-optimize every 60 seconds
    if (now - last_optimize >= 60) {
        catzilla_memory_optimize();
        last_optimize = now;
    }
}

int catzilla_memory_purge_arena(catzilla_memory_type_t type) {
#ifdef CATZILLA_USE_JEMALLOC
    char arena_cmd[64];
    unsigned arena_id = 0;

    switch (type) {
        case CATZILLA_MEMORY_REQUEST:
            arena_id = g_memory_stats.request_arena;
            break;
        case CATZILLA_MEMORY_RESPONSE:
            arena_id = g_memory_stats.response_arena;
            break;
        case CATZILLA_MEMORY_CACHE:
            arena_id = g_memory_stats.cache_arena;
            break;
        case CATZILLA_MEMORY_STATIC:
            arena_id = g_memory_stats.static_arena;
            break;
        case CATZILLA_MEMORY_TASK:
            arena_id = g_memory_stats.task_arena;
            break;
        default:
            return -1;
    }

    snprintf(arena_cmd, sizeof(arena_cmd), "arena.%u.purge", arena_id);
    return JEMALLOC_MALLCTL(arena_cmd, NULL, NULL, NULL, 0);
#else
    return 0; // No-op for standard malloc
#endif
}

int catzilla_memory_get_arena_stats(catzilla_memory_type_t type, size_t* allocated, size_t* active) {
#ifdef CATZILLA_USE_JEMALLOC
    char arena_cmd[64];
    unsigned arena_id = 0;
    size_t sz = sizeof(size_t);

    switch (type) {
        case CATZILLA_MEMORY_REQUEST:
            arena_id = g_memory_stats.request_arena;
            break;
        case CATZILLA_MEMORY_RESPONSE:
            arena_id = g_memory_stats.response_arena;
            break;
        case CATZILLA_MEMORY_CACHE:
            arena_id = g_memory_stats.cache_arena;
            break;
        case CATZILLA_MEMORY_STATIC:
            arena_id = g_memory_stats.static_arena;
            break;
        case CATZILLA_MEMORY_TASK:
            arena_id = g_memory_stats.task_arena;
            break;
        default:
            return -1;
    }

    snprintf(arena_cmd, sizeof(arena_cmd), "stats.arenas.%u.allocated", arena_id);
    JEMALLOC_MALLCTL(arena_cmd, allocated, &sz, NULL, 0);

    snprintf(arena_cmd, sizeof(arena_cmd), "stats.arenas.%u.active", arena_id);
    JEMALLOC_MALLCTL(arena_cmd, active, &sz, NULL, 0);

    return 0;
#else
    if (allocated) *allocated = 0;
    if (active) *active = 0;
    return 0;
#endif
}

#ifdef DEBUG
void catzilla_memory_dump_stats(void) {
    catzilla_memory_stats_t stats;
    catzilla_memory_get_stats(&stats);

    printf("\n=== Catzilla Memory Statistics ===\n");
    printf("jemalloc available: %s\n", catzilla_memory_has_jemalloc() ? "YES" : "NO");
    printf("Allocated: %.2f MB\n", stats.allocated / (1024.0 * 1024.0));
    printf("Active: %.2f MB\n", stats.active / (1024.0 * 1024.0));
    printf("Metadata: %.2f MB\n", stats.metadata / (1024.0 * 1024.0));
    printf("Resident: %.2f MB\n", stats.resident / (1024.0 * 1024.0));
    printf("Peak: %.2f MB\n", stats.peak_allocated / (1024.0 * 1024.0));
    printf("Fragmentation: %.2f%%\n", (1.0 - stats.fragmentation_ratio) * 100.0);
    printf("Efficiency Score: %.2f\n", stats.memory_efficiency_score);
    printf("Allocations: %lu\n", stats.allocation_count);
    printf("Deallocations: %lu\n", stats.deallocation_count);

    if (catzilla_memory_has_jemalloc()) {
        printf("\nArena Usage:\n");
        printf("  Request: %.2f MB\n", stats.request_arena_usage / (1024.0 * 1024.0));
        printf("  Response: %.2f MB\n", stats.response_arena_usage / (1024.0 * 1024.0));
        printf("  Cache: %.2f MB\n", stats.cache_arena_usage / (1024.0 * 1024.0));
        printf("  Static: %.2f MB\n", stats.static_arena_usage / (1024.0 * 1024.0));
        printf("  Task: %.2f MB\n", stats.task_arena_usage / (1024.0 * 1024.0));
    }

    printf("==================================\n\n");
}

void catzilla_memory_check_leaks(void) {
    catzilla_memory_stats_t stats;
    catzilla_memory_get_stats(&stats);

    if (stats.allocation_count != stats.deallocation_count) {
        printf("⚠️  MEMORY LEAK DETECTED: %lu allocations, %lu deallocations\n",
               stats.allocation_count, stats.deallocation_count);
    } else {
        printf("✅ No memory leaks detected\n");
    }
}
#endif
