#include "server_stats.h"
#include "server.h"
#include <string.h>
#ifndef _WIN32
#include <unistd.h>
#endif
#include <time.h>

#ifdef JEMALLOC_ENABLED
#include <jemalloc/jemalloc.h>
#endif

// Version string - will be updated by build system
#ifndef CATZILLA_VERSION
#define CATZILLA_VERSION "0.1.0"
#endif

int catzilla_server_stats_init(catzilla_server_stats_t* stats) {
    if (!stats) return -1;

    // Initialize all fields to safe defaults
    memset(stats, 0, sizeof(catzilla_server_stats_t));

    // Set version
    strncpy(stats->version, CATZILLA_VERSION, sizeof(stats->version) - 1);

    // Set defaults
    stats->worker_count = 1;  // Single-threaded for now
    stats->jemalloc_enabled = catzilla_server_stats_check_jemalloc();
    stats->debug_mode = false;  // Will be set by application
    stats->profiling_enabled = false;
    stats->profiling_interval = 60;
    stats->pid = getpid();
    stats->start_time = (uint64_t)time(NULL);

    // Get allocator name
    catzilla_server_stats_get_allocator(stats->allocator_name, sizeof(stats->allocator_name));

    return 0;
}

int catzilla_server_collect_stats(void* server_ptr, catzilla_server_stats_t* stats) {
    if (!stats) return -1;

    // Initialize with defaults
    catzilla_server_stats_init(stats);

    // If server pointer is provided, extract server-specific stats
    if (server_ptr) {
        catzilla_server_t* server = (catzilla_server_t*)server_ptr;

        // Get route count from advanced router
        stats->route_count = catzilla_server_get_route_count(server);

        // Set debug mode based on some heuristic or global flag
        // For now, we'll assume debug mode if not explicitly set to production
        // This will be overridden by Python layer
        stats->debug_mode = true;  // Default to debug, Python will override
    }

    return 0;
}

void catzilla_server_stats_set_route_count(catzilla_server_stats_t* stats, int route_count) {
    if (stats) {
        stats->route_count = route_count;
    }
}

void catzilla_server_stats_set_bind_info(catzilla_server_stats_t* stats, const char* host, int port) {
    if (!stats) return;

    if (host) {
        strncpy(stats->bind_host, host, sizeof(stats->bind_host) - 1);
        stats->bind_host[sizeof(stats->bind_host) - 1] = '\0';
    }

    stats->bind_port = port;
}

bool catzilla_server_stats_check_jemalloc(void) {
#ifdef JEMALLOC_ENABLED
    // Check if jemalloc is actually active
    const char* version = malloc_conf;
    (void)version; // Suppress unused variable warning

    // Try to get jemalloc stats to verify it's working
    size_t allocated = 0;
    size_t len = sizeof(allocated);

    // Use mallctl to check if jemalloc is responding
    if (mallctl("stats.allocated", &allocated, &len, NULL, 0) == 0) {
        return true;
    }
#endif
    return false;
}

int catzilla_server_stats_get_allocator(char* buffer, size_t buffer_size) {
    if (!buffer || buffer_size == 0) return -1;

    if (catzilla_server_stats_check_jemalloc()) {
        strncpy(buffer, "jemalloc", buffer_size - 1);
    } else {
        strncpy(buffer, "malloc", buffer_size - 1);
    }

    buffer[buffer_size - 1] = '\0';
    return 0;
}
