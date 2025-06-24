#ifndef CATZILLA_SERVER_STATS_H
#define CATZILLA_SERVER_STATS_H

#include <stdbool.h>
#include <stdint.h>
#include <sys/types.h>
#include <time.h>

#ifdef __cplusplus
extern "C" {
#endif

/**
 * Server statistics structure for startup banner and monitoring
 */
typedef struct {
    char version[32];           // Catzilla version string
    int route_count;           // Number of registered routes
    int worker_count;          // Number of worker threads
    bool jemalloc_enabled;     // Whether jemalloc is active
    bool debug_mode;           // Development vs production mode
    bool profiling_enabled;    // Whether profiling is active
    int profiling_interval;    // Profiling interval in seconds
    pid_t pid;                 // Process ID
    uint64_t start_time;       // Server start timestamp
    char bind_host[256];       // Bound host address
    int bind_port;             // Bound port number

    // Extended stats for advanced features
    int di_service_count;      // Number of DI services registered
    bool auto_validation;      // Whether auto-validation is enabled
    bool background_tasks;     // Whether background task system is enabled
    char allocator_name[32];   // Current memory allocator name
} catzilla_server_stats_t;

/**
 * Initialize server statistics structure
 * @param stats Pointer to stats structure to initialize
 * @return 0 on success, -1 on failure
 */
int catzilla_server_stats_init(catzilla_server_stats_t* stats);

/**
 * Collect current server statistics
 * @param server Pointer to server structure
 * @param stats Pointer to stats structure to fill
 * @return 0 on success, -1 on failure
 */
int catzilla_server_collect_stats(void* server, catzilla_server_stats_t* stats);

/**
 * Update route count in statistics
 * @param stats Pointer to stats structure
 * @param route_count New route count
 */
void catzilla_server_stats_set_route_count(catzilla_server_stats_t* stats, int route_count);

/**
 * Update bind information in statistics
 * @param stats Pointer to stats structure
 * @param host Host address
 * @param port Port number
 */
void catzilla_server_stats_set_bind_info(catzilla_server_stats_t* stats, const char* host, int port);

/**
 * Check if jemalloc is available and active
 * @return true if jemalloc is active, false otherwise
 */
bool catzilla_server_stats_check_jemalloc(void);

/**
 * Get current memory allocator name
 * @param buffer Buffer to store allocator name
 * @param buffer_size Size of buffer
 * @return 0 on success, -1 on failure
 */
int catzilla_server_stats_get_allocator(char* buffer, size_t buffer_size);

#ifdef __cplusplus
}
#endif

#endif // CATZILLA_SERVER_STATS_H
