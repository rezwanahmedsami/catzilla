// filepath: /home/rezwan/devwork/catzilla/src/core/memory.c

// Platform compatibility
#include "platform_compat.h"

// System headers
// sys/types.h and unistd.h are now included in platform_compat.h

#include "memory.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <assert.h>
#include <time.h>

// ============================================================================
// 🚀 CATZILLA MEMORY SYSTEM - CONDITIONAL JEMALLOC SUPPORT
// ============================================================================

// Cross-platform atomic operations
#ifdef _WIN32
    #include <windows.h>
    #define ATOMIC_ADD(ptr, value) InterlockedExchangeAdd((LONG volatile*)(ptr), (LONG)(value))
#else
    // GCC/Clang atomic builtins
    #define ATOMIC_ADD(ptr, value) __sync_fetch_and_add((ptr), (value))
#endif

// Conditional jemalloc inclusion
#ifdef CATZILLA_HAS_JEMALLOC
#define JEMALLOC_MANGLE
#include <jemalloc/jemalloc.h>

// Cross-platform jemalloc compatibility layer with dynamic prefix detection
#ifndef CATZILLA_JEMALLOC_PREFIX
    #define CATZILLA_JEMALLOC_PREFIX ""  // Default to no prefix if not defined
#endif

// Helper macro to concatenate prefix with function name
#define JEMALLOC_CONCAT(prefix, name) prefix##name
#define JEMALLOC_FUNC(prefix, name) JEMALLOC_CONCAT(prefix, name)

// Conditional function mapping based on detected prefix
#if CATZILLA_JEMALLOC_USES_PREFIX == 1
    // Use je_ prefixed functions (typical on RPM-based Linux)
    #define JEMALLOC_MALLOCX    je_mallocx
    #define JEMALLOC_DALLOCX    je_dallocx
    #define JEMALLOC_RALLOCX    je_rallocx
    #define JEMALLOC_MALLCTL    je_mallctl
    #define JEMALLOC_MALLOC     je_malloc
    #define JEMALLOC_CALLOC     je_calloc
    #define JEMALLOC_REALLOC    je_realloc
    #define JEMALLOC_FREE       je_free
#else
    // Use direct function names (typical on macOS Homebrew and some Linux builds)
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

// Global memory state
static catzilla_memory_stats_t g_memory_stats = {0};
static bool g_memory_initialized = false;
static bool g_profiling_enabled = false;
static catzilla_allocator_type_t g_current_allocator = CATZILLA_ALLOCATOR_MALLOC;

// ============================================================================
// CONDITIONAL JEMALLOC RUNTIME FUNCTIONS
// ============================================================================

bool catzilla_memory_jemalloc_available(void) {
#ifdef CATZILLA_HAS_JEMALLOC
    return true;
#else
    return false;
#endif
}

catzilla_allocator_type_t catzilla_memory_get_current_allocator(void) {
    return g_current_allocator;
}

int catzilla_memory_set_allocator(catzilla_allocator_type_t allocator) {
    if (g_memory_initialized) {
        // Cannot change allocator after initialization
        return -1;
    }

    if (allocator == CATZILLA_ALLOCATOR_JEMALLOC && !catzilla_memory_jemalloc_available()) {
        // jemalloc requested but not available
        return -2;
    }

    g_current_allocator = allocator;
    return 0;
}

// ============================================================================
// MEMORY ALLOCATION FUNCTIONS (CONDITIONAL BACKEND)
// ============================================================================

void* catzilla_malloc(size_t size) {
#ifdef CATZILLA_HAS_JEMALLOC
    if (g_current_allocator == CATZILLA_ALLOCATOR_JEMALLOC) {
        void* ptr = JEMALLOC_MALLOCX(size, MALLOCX_ARENA(g_memory_stats.cache_arena));
        if (ptr && g_profiling_enabled) {
            ATOMIC_ADD(&g_memory_stats.allocation_count, 1);
        }
        return ptr;
    }
#endif
    // Fallback to standard malloc
    void* ptr = malloc(size);
    if (ptr && g_profiling_enabled) {
        ATOMIC_ADD(&g_memory_stats.allocation_count, 1);
    }
    return ptr;
}

void* catzilla_calloc(size_t count, size_t size) {
#ifdef CATZILLA_HAS_JEMALLOC
    if (g_current_allocator == CATZILLA_ALLOCATOR_JEMALLOC) {
        size_t total_size = count * size;
        void* ptr = JEMALLOC_MALLOCX(total_size, MALLOCX_ARENA(g_memory_stats.cache_arena) | MALLOCX_ZERO);
        if (ptr && g_profiling_enabled) {
            ATOMIC_ADD(&g_memory_stats.allocation_count, 1);
        }
        return ptr;
    }
#endif
    // Fallback to standard calloc
    void* ptr = calloc(count, size);
    if (ptr && g_profiling_enabled) {
        ATOMIC_ADD(&g_memory_stats.allocation_count, 1);
    }
    return ptr;
}

void* catzilla_realloc(void* ptr, size_t size) {
#ifdef CATZILLA_HAS_JEMALLOC
    if (g_current_allocator == CATZILLA_ALLOCATOR_JEMALLOC) {
        void* new_ptr = JEMALLOC_REALLOC(ptr, size);
        if (new_ptr && !ptr && g_profiling_enabled) {
            ATOMIC_ADD(&g_memory_stats.allocation_count, 1);
        }
        return new_ptr;
    }
#endif
    // Fallback to standard realloc
    void* new_ptr = realloc(ptr, size);
    if (new_ptr && !ptr && g_profiling_enabled) {
        ATOMIC_ADD(&g_memory_stats.allocation_count, 1);
    }
    return new_ptr;
}

void catzilla_free(void* ptr) {
    if (!ptr) return;

#ifdef CATZILLA_HAS_JEMALLOC
    if (g_current_allocator == CATZILLA_ALLOCATOR_JEMALLOC) {
        JEMALLOC_FREE(ptr);
        if (g_profiling_enabled) {
            ATOMIC_ADD(&g_memory_stats.deallocation_count, 1);
        }
        return;
    }
#endif
    // Fallback to standard free
    free(ptr);
    if (g_profiling_enabled) {
        ATOMIC_ADD(&g_memory_stats.deallocation_count, 1);
    }
}

// ============================================================================
// ARENA-SPECIFIC ALLOCATION FUNCTIONS (CONDITIONAL BACKEND)
// ============================================================================

void* catzilla_request_alloc(size_t size) {
#ifdef CATZILLA_HAS_JEMALLOC
    if (g_current_allocator == CATZILLA_ALLOCATOR_JEMALLOC) {
        void* ptr = JEMALLOC_MALLOCX(size, MALLOCX_ARENA(g_memory_stats.request_arena));
        if (ptr && g_profiling_enabled) {
            ATOMIC_ADD(&g_memory_stats.allocation_count, 1);
            ATOMIC_ADD(&g_memory_stats.request_arena_usage, size);
        }
        return ptr;
    }
#endif
    return catzilla_malloc(size);
}

void* catzilla_response_alloc(size_t size) {
#ifdef CATZILLA_HAS_JEMALLOC
    if (g_current_allocator == CATZILLA_ALLOCATOR_JEMALLOC) {
        void* ptr = JEMALLOC_MALLOCX(size, MALLOCX_ARENA(g_memory_stats.response_arena));
        if (ptr && g_profiling_enabled) {
            ATOMIC_ADD(&g_memory_stats.allocation_count, 1);
            ATOMIC_ADD(&g_memory_stats.response_arena_usage, size);
        }
        return ptr;
    }
#endif
    return catzilla_malloc(size);
}

void* catzilla_cache_alloc(size_t size) {
#ifdef CATZILLA_HAS_JEMALLOC
    if (g_current_allocator == CATZILLA_ALLOCATOR_JEMALLOC) {
        void* ptr = JEMALLOC_MALLOCX(size, MALLOCX_ARENA(g_memory_stats.cache_arena));
        if (ptr && g_profiling_enabled) {
            ATOMIC_ADD(&g_memory_stats.allocation_count, 1);
            ATOMIC_ADD(&g_memory_stats.cache_arena_usage, size);
        }
        return ptr;
    }
#endif
    return catzilla_malloc(size);
}

void* catzilla_static_alloc(size_t size) {
#ifdef CATZILLA_HAS_JEMALLOC
    if (g_current_allocator == CATZILLA_ALLOCATOR_JEMALLOC) {
        void* ptr = JEMALLOC_MALLOCX(size, MALLOCX_ARENA(g_memory_stats.static_arena));
        if (ptr && g_profiling_enabled) {
            ATOMIC_ADD(&g_memory_stats.allocation_count, 1);
            ATOMIC_ADD(&g_memory_stats.static_arena_usage, size);
        }
        return ptr;
    }
#endif
    return catzilla_malloc(size);
}

void* catzilla_task_alloc(size_t size) {
#ifdef CATZILLA_HAS_JEMALLOC
    if (g_current_allocator == CATZILLA_ALLOCATOR_JEMALLOC) {
        void* ptr = JEMALLOC_MALLOCX(size, MALLOCX_ARENA(g_memory_stats.task_arena));
        if (ptr && g_profiling_enabled) {
            ATOMIC_ADD(&g_memory_stats.allocation_count, 1);
            ATOMIC_ADD(&g_memory_stats.task_arena_usage, size);
        }
        return ptr;
    }
#endif
    return catzilla_malloc(size);
}

// ============================================================================
// ARENA-SPECIFIC DEALLOCATION FUNCTIONS (CONDITIONAL BACKEND)
// ============================================================================

void catzilla_request_free(void* ptr) {
    if (!ptr) return;

#ifdef CATZILLA_HAS_JEMALLOC
    if (g_current_allocator == CATZILLA_ALLOCATOR_JEMALLOC) {
        JEMALLOC_DALLOCX(ptr, MALLOCX_ARENA(g_memory_stats.request_arena));
        if (g_profiling_enabled) {
            ATOMIC_ADD(&g_memory_stats.deallocation_count, 1);
        }
        return;
    }
#endif
    catzilla_free(ptr);
}

void catzilla_response_free(void* ptr) {
    if (!ptr) return;

#ifdef CATZILLA_HAS_JEMALLOC
    if (g_current_allocator == CATZILLA_ALLOCATOR_JEMALLOC) {
        JEMALLOC_DALLOCX(ptr, MALLOCX_ARENA(g_memory_stats.response_arena));
        if (g_profiling_enabled) {
            ATOMIC_ADD(&g_memory_stats.deallocation_count, 1);
        }
        return;
    }
#endif
    catzilla_free(ptr);
}

void catzilla_cache_free(void* ptr) {
    if (!ptr) return;

#ifdef CATZILLA_HAS_JEMALLOC
    if (g_current_allocator == CATZILLA_ALLOCATOR_JEMALLOC) {
        JEMALLOC_DALLOCX(ptr, MALLOCX_ARENA(g_memory_stats.cache_arena));
        if (g_profiling_enabled) {
            ATOMIC_ADD(&g_memory_stats.deallocation_count, 1);
        }
        return;
    }
#endif
    catzilla_free(ptr);
}

void catzilla_static_free(void* ptr) {
    if (!ptr) return;

#ifdef CATZILLA_HAS_JEMALLOC
    if (g_current_allocator == CATZILLA_ALLOCATOR_JEMALLOC) {
        JEMALLOC_DALLOCX(ptr, MALLOCX_ARENA(g_memory_stats.static_arena));
        if (g_profiling_enabled) {
            ATOMIC_ADD(&g_memory_stats.deallocation_count, 1);
        }
        return;
    }
#endif
    catzilla_free(ptr);
}

void catzilla_task_free(void* ptr) {
    if (!ptr) return;

#ifdef CATZILLA_HAS_JEMALLOC
    if (g_current_allocator == CATZILLA_ALLOCATOR_JEMALLOC) {
        JEMALLOC_DALLOCX(ptr, MALLOCX_ARENA(g_memory_stats.task_arena));
        if (g_profiling_enabled) {
            ATOMIC_ADD(&g_memory_stats.deallocation_count, 1);
        }
        return;
    }
#endif
    catzilla_free(ptr);
}

// ============================================================================
// ARENA-SPECIFIC REALLOCATION FUNCTIONS (CONDITIONAL BACKEND)
// ============================================================================

void* catzilla_request_realloc(void* ptr, size_t size) {
#ifdef CATZILLA_HAS_JEMALLOC
    if (g_current_allocator == CATZILLA_ALLOCATOR_JEMALLOC) {
        void* new_ptr = JEMALLOC_RALLOCX(ptr, size, MALLOCX_ARENA(g_memory_stats.request_arena));
        if (new_ptr && g_profiling_enabled) {
            ATOMIC_ADD(&g_memory_stats.allocation_count, 1);
            ATOMIC_ADD(&g_memory_stats.request_arena_usage, size);
        }
        return new_ptr;
    }
#endif
    return catzilla_realloc(ptr, size);
}

void* catzilla_response_realloc(void* ptr, size_t size) {
#ifdef CATZILLA_HAS_JEMALLOC
    if (g_current_allocator == CATZILLA_ALLOCATOR_JEMALLOC) {
        void* new_ptr = JEMALLOC_RALLOCX(ptr, size, MALLOCX_ARENA(g_memory_stats.response_arena));
        if (new_ptr && g_profiling_enabled) {
            ATOMIC_ADD(&g_memory_stats.allocation_count, 1);
            ATOMIC_ADD(&g_memory_stats.response_arena_usage, size);
        }
        return new_ptr;
    }
#endif
    return catzilla_realloc(ptr, size);
}

void* catzilla_cache_realloc(void* ptr, size_t size) {
#ifdef CATZILLA_HAS_JEMALLOC
    if (g_current_allocator == CATZILLA_ALLOCATOR_JEMALLOC) {
        void* new_ptr = JEMALLOC_RALLOCX(ptr, size, MALLOCX_ARENA(g_memory_stats.cache_arena));
        if (new_ptr && g_profiling_enabled) {
            ATOMIC_ADD(&g_memory_stats.allocation_count, 1);
            ATOMIC_ADD(&g_memory_stats.cache_arena_usage, size);
        }
        return new_ptr;
    }
#endif
    return catzilla_realloc(ptr, size);
}

void* catzilla_static_realloc(void* ptr, size_t size) {
#ifdef CATZILLA_HAS_JEMALLOC
    if (g_current_allocator == CATZILLA_ALLOCATOR_JEMALLOC) {
        void* new_ptr = JEMALLOC_RALLOCX(ptr, size, MALLOCX_ARENA(g_memory_stats.static_arena));
        if (new_ptr && g_profiling_enabled) {
            ATOMIC_ADD(&g_memory_stats.allocation_count, 1);
            ATOMIC_ADD(&g_memory_stats.static_arena_usage, size);
        }
        return new_ptr;
    }
#endif
    return catzilla_realloc(ptr, size);
}

void* catzilla_task_realloc(void* ptr, size_t size) {
#ifdef CATZILLA_HAS_JEMALLOC
    if (g_current_allocator == CATZILLA_ALLOCATOR_JEMALLOC) {
        void* new_ptr = JEMALLOC_RALLOCX(ptr, size, MALLOCX_ARENA(g_memory_stats.task_arena));
        if (new_ptr && g_profiling_enabled) {
            ATOMIC_ADD(&g_memory_stats.allocation_count, 1);
            ATOMIC_ADD(&g_memory_stats.task_arena_usage, size);
        }
        return new_ptr;
    }
#endif
    return catzilla_realloc(ptr, size);
}

// ============================================================================
// MEMORY INITIALIZATION FUNCTIONS (CONDITIONAL BACKEND)
// ============================================================================

// Global arena tracking - arenas persist for process lifetime
static bool g_arenas_created = false;

int catzilla_memory_init_with_allocator(catzilla_allocator_type_t allocator) {
    if (g_memory_initialized) {
        return 0; // Already initialized
    }

    // Set the allocator before initialization
    if (catzilla_memory_set_allocator(allocator) != 0) {
        return -1; // Invalid allocator or jemalloc not available
    }

    return catzilla_memory_init();
}

int catzilla_memory_init(void) {
    if (g_memory_initialized) {
        return 0; // Already initialized
    }

    // Auto-detect and use jemalloc if available and no allocator explicitly set
    if (g_current_allocator == CATZILLA_ALLOCATOR_MALLOC && catzilla_memory_jemalloc_available()) {
        g_current_allocator = CATZILLA_ALLOCATOR_JEMALLOC;
    }

#ifdef CATZILLA_HAS_JEMALLOC
    if (g_current_allocator == CATZILLA_ALLOCATOR_JEMALLOC) {
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
#endif

    // Standard malloc fallback
    g_memory_initialized = true;
    printf("⚠️  Catzilla running with standard malloc (jemalloc not available)\n");
    return 0;
}

// Initialize memory system with quiet option
int catzilla_memory_init_quiet(int quiet) {
    if (g_memory_initialized) {
        return 0; // Already initialized
    }

    // Auto-detect and use jemalloc if available and no allocator explicitly set
    if (g_current_allocator == CATZILLA_ALLOCATOR_MALLOC && catzilla_memory_jemalloc_available()) {
        g_current_allocator = CATZILLA_ALLOCATOR_JEMALLOC;
    }

#ifdef CATZILLA_HAS_JEMALLOC
    if (g_current_allocator == CATZILLA_ALLOCATOR_JEMALLOC) {
        // Initialize jemalloc arenas for performance optimization
        if (!g_arenas_created) {
            size_t sz = sizeof(unsigned);

            // Request arena - optimized for request/response data
            if (JEMALLOC_MALLCTL("arenas.create", &g_memory_stats.request_arena, &sz, NULL, 0) != 0) {
                fprintf(stderr, "Error: Failed to create request arena\n");
                return -1;
            }

            // Response arena - optimized for response construction
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

        // Only print if not quiet
        if (!quiet) {
            printf("✅ Catzilla initialized with jemalloc (arenas: req=%u, res=%u, cache=%u, static=%u, task=%u)\n",
                   g_memory_stats.request_arena, g_memory_stats.response_arena,
                   g_memory_stats.cache_arena, g_memory_stats.static_arena, g_memory_stats.task_arena);
        }

        return 0;
    }
#endif

    // Standard malloc fallback
    g_memory_initialized = true;
    if (!quiet) {
        printf("⚠️  Catzilla running with standard malloc (jemalloc not available)\n");
    }
    return 0;
}

void catzilla_memory_get_stats(catzilla_memory_stats_t* stats) {
    if (!stats) return;

#ifdef CATZILLA_HAS_JEMALLOC
    if (g_current_allocator == CATZILLA_ALLOCATOR_JEMALLOC) {
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
        return;
    }
#endif

    // Fallback for standard malloc
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
#ifdef CATZILLA_HAS_JEMALLOC
    if (g_current_allocator == CATZILLA_ALLOCATOR_JEMALLOC) {
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
#endif
    // No-op with standard malloc
}

bool catzilla_memory_has_jemalloc(void) {
#ifdef CATZILLA_HAS_JEMALLOC
    return true;
#else
    return false;
#endif
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

// ============================================================================
// COMMON UTILITY FUNCTIONS
// ============================================================================

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
#ifdef CATZILLA_HAS_JEMALLOC
    if (g_current_allocator == CATZILLA_ALLOCATOR_JEMALLOC) {
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
    }
#endif
    return 0; // No-op for standard malloc
}

int catzilla_memory_get_arena_stats(catzilla_memory_type_t type, size_t* allocated, size_t* active) {
#ifdef CATZILLA_HAS_JEMALLOC
    if (g_current_allocator == CATZILLA_ALLOCATOR_JEMALLOC) {
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
    }
#endif
    if (allocated) *allocated = 0;
    if (active) *active = 0;
    return 0;
}

#ifdef DEBUG
void catzilla_memory_dump_stats(void) {
    catzilla_memory_stats_t stats;
    catzilla_memory_get_stats(&stats);

    printf("\n=== Catzilla Memory Statistics ===\n");
    printf("jemalloc available: %s\n", catzilla_memory_has_jemalloc() ? "YES" : "NO");
    printf("Current allocator: %s\n",
           g_current_allocator == CATZILLA_ALLOCATOR_JEMALLOC ? "jemalloc" : "malloc");
    printf("Allocated: %.2f MB\n", stats.allocated / (1024.0 * 1024.0));
    printf("Active: %.2f MB\n", stats.active / (1024.0 * 1024.0));
    printf("Metadata: %.2f MB\n", stats.metadata / (1024.0 * 1024.0));
    printf("Resident: %.2f MB\n", stats.resident / (1024.0 * 1024.0));
    printf("Peak: %.2f MB\n", stats.peak_allocated / (1024.0 * 1024.0));
    printf("Fragmentation: %.2f%%\n", (1.0 - stats.fragmentation_ratio) * 100.0);
    printf("Efficiency Score: %.2f\n", stats.memory_efficiency_score);
    printf("Allocations: %lu\n", stats.allocation_count);
    printf("Deallocations: %lu\n", stats.deallocation_count);

    if (catzilla_memory_has_jemalloc() && g_current_allocator == CATZILLA_ALLOCATOR_JEMALLOC) {
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
