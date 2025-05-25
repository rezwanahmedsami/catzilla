#ifndef CATZILLA_LOGGING_H
#define CATZILLA_LOGGING_H

#include <stdio.h>
#include <stdlib.h>

/**
 * Catzilla Professional Logging System
 *
 * This logging system is designed for Catzilla contributors and developers only.
 * End users will never see these logs unless they explicitly enable debug mode.
 *
 * Usage:
 *   - Contributors: CATZILLA_C_DEBUG=1 python app.py
 *   - End users: python app.py (clean output, no C logs)
 *
 * Log levels:
 *   - LOG_DEBUG: Detailed debugging information
 *   - LOG_INFO: General information about operations
 *   - LOG_ERROR: Error conditions that need attention
 */

static inline int catzilla_debug_enabled() {
    static int checked = 0;
    static int enabled = 0;
    if (!checked) {
        enabled = getenv("CATZILLA_C_DEBUG") != NULL;
        checked = 1;
    }
    return enabled;
}

// ANSI color codes for better visibility
#define ANSI_RESET   "\033[0m"
#define ANSI_CYAN    "\033[36m"  // DEBUG
#define ANSI_GREEN   "\033[32m"  // INFO
#define ANSI_RED     "\033[31m"  // ERROR
#define ANSI_YELLOW  "\033[33m"  // WARNING

#define LOG_DEBUG(module, fmt, ...) \
    do { if (catzilla_debug_enabled()) \
        fprintf(stderr, ANSI_CYAN "[DEBUG-C][%s]" ANSI_RESET " " fmt "\n", module, ##__VA_ARGS__); } while(0)

#define LOG_INFO(module, fmt, ...) \
    do { if (catzilla_debug_enabled()) \
        fprintf(stderr, ANSI_GREEN "[INFO-C][%s]" ANSI_RESET " " fmt "\n", module, ##__VA_ARGS__); } while(0)

#define LOG_ERROR(module, fmt, ...) \
    do { if (catzilla_debug_enabled()) \
        fprintf(stderr, ANSI_RED "[ERROR-C][%s]" ANSI_RESET " " fmt "\n", module, ##__VA_ARGS__); } while(0)

#define LOG_WARN(module, fmt, ...) \
    do { if (catzilla_debug_enabled()) \
        fprintf(stderr, ANSI_YELLOW "[WARN-C][%s]" ANSI_RESET " " fmt "\n", module, ##__VA_ARGS__); } while(0)

// Convenience macros for common modules
#define LOG_SERVER_DEBUG(fmt, ...) LOG_DEBUG("Server", fmt, ##__VA_ARGS__)
#define LOG_SERVER_INFO(fmt, ...)  LOG_INFO("Server", fmt, ##__VA_ARGS__)
#define LOG_SERVER_ERROR(fmt, ...) LOG_ERROR("Server", fmt, ##__VA_ARGS__)
#define LOG_SERVER_WARN(fmt, ...)  LOG_WARN("Server", fmt, ##__VA_ARGS__)

#define LOG_ROUTER_DEBUG(fmt, ...) LOG_DEBUG("Router", fmt, ##__VA_ARGS__)
#define LOG_ROUTER_INFO(fmt, ...)  LOG_INFO("Router", fmt, ##__VA_ARGS__)
#define LOG_ROUTER_ERROR(fmt, ...) LOG_ERROR("Router", fmt, ##__VA_ARGS__)
#define LOG_ROUTER_WARN(fmt, ...)  LOG_WARN("Router", fmt, ##__VA_ARGS__)

#define LOG_HTTP_DEBUG(fmt, ...)   LOG_DEBUG("HTTP", fmt, ##__VA_ARGS__)
#define LOG_HTTP_INFO(fmt, ...)    LOG_INFO("HTTP", fmt, ##__VA_ARGS__)
#define LOG_HTTP_ERROR(fmt, ...)   LOG_ERROR("HTTP", fmt, ##__VA_ARGS__)
#define LOG_HTTP_WARN(fmt, ...)    LOG_WARN("HTTP", fmt, ##__VA_ARGS__)

#endif // CATZILLA_LOGGING_H
