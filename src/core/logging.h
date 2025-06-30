#ifndef CATZILLA_LOGGING_H
#define CATZILLA_LOGGING_H

#include <stdio.h>
#include <stdlib.h>

// Windows-specific includes for console color support
#ifdef _WIN32
    #include <windows.h>
    #include <io.h>
    #define isatty _isatty
    #define fileno _fileno
#else
    #include <unistd.h>
#endif

/**
 * Catzilla Professional Logging System
 *
 * This logging system is designed for Catzilla contributors and developers only.
 * End users will never see these logs unless they explicitly enable debug mode.
 *
 * Cross-platform color support:
 *   - Unix/Linux/macOS: ANSI escape codes
 *   - Windows: Console API (Windows 10+) or fallback to no colors
 *
 * Usage:
 *   - Contributors: CATZILLA_C_DEBUG=1 python app.py
 *   - End users: python app.py (clean output, no C logs)
 *
 * Log levels:
 *   - LOG_DEBUG: Detailed debugging information
 *   - LOG_INFO: General information about operations
 *   - LOG_WARN: Warning conditions
 *   - LOG_ERROR: Error conditions that need attention
 */

// Initialize Windows console for color support (Windows 10+)
static inline void catzilla_init_console_colors() {
#ifdef _WIN32
    static int initialized = 0;
    if (!initialized) {
        HANDLE hOut = GetStdHandle(STD_OUTPUT_HANDLE);
        DWORD dwMode = 0;
        if (GetConsoleMode(hOut, &dwMode)) {
            dwMode |= ENABLE_VIRTUAL_TERMINAL_PROCESSING;
            SetConsoleMode(hOut, dwMode);
        }
        initialized = 1;
    }
#endif
}

static inline int catzilla_debug_enabled() {
    static int checked = 0;
    static int enabled = 0;
    if (!checked) {
        enabled = getenv("CATZILLA_C_DEBUG") != NULL;
        if (enabled) {
            catzilla_init_console_colors();
        }
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

// 🚀 REVOLUTIONARY: Validation engine logging macros
#define LOG_VALIDATION_DEBUG(fmt, ...) LOG_DEBUG("Validation", fmt, ##__VA_ARGS__)
#define LOG_VALIDATION_INFO(fmt, ...)  LOG_INFO("Validation", fmt, ##__VA_ARGS__)
#define LOG_VALIDATION_ERROR(fmt, ...) LOG_ERROR("Validation", fmt, ##__VA_ARGS__)
#define LOG_VALIDATION_WARN(fmt, ...)  LOG_WARN("Validation", fmt, ##__VA_ARGS__)

// 🚀 C-NATIVE: Static file server logging macros
#define LOG_STATIC_DEBUG(fmt, ...)     LOG_DEBUG("Static", fmt, ##__VA_ARGS__)
#define LOG_STATIC_INFO(fmt, ...)      LOG_INFO("Static", fmt, ##__VA_ARGS__)
#define LOG_STATIC_ERROR(fmt, ...)     LOG_ERROR("Static", fmt, ##__VA_ARGS__)
#define LOG_STATIC_WARN(fmt, ...)      LOG_WARN("Static", fmt, ##__VA_ARGS__)

// 🚀 REVOLUTIONARY: File upload system logging macros
#define LOG_UPLOAD_DEBUG(fmt, ...)     LOG_DEBUG("Upload", fmt, ##__VA_ARGS__)
#define LOG_UPLOAD_INFO(fmt, ...)      LOG_INFO("Upload", fmt, ##__VA_ARGS__)
#define LOG_UPLOAD_ERROR(fmt, ...)     LOG_ERROR("Upload", fmt, ##__VA_ARGS__)
#define LOG_UPLOAD_WARN(fmt, ...)      LOG_WARN("Upload", fmt, ##__VA_ARGS__)

#define LOG_PARSER_DEBUG(fmt, ...)     LOG_DEBUG("Parser", fmt, ##__VA_ARGS__)
#define LOG_PARSER_INFO(fmt, ...)      LOG_INFO("Parser", fmt, ##__VA_ARGS__)
#define LOG_PARSER_ERROR(fmt, ...)     LOG_ERROR("Parser", fmt, ##__VA_ARGS__)
#define LOG_PARSER_WARN(fmt, ...)      LOG_WARN("Parser", fmt, ##__VA_ARGS__)

#define LOG_MEMORY_DEBUG(fmt, ...)     LOG_DEBUG("Memory", fmt, ##__VA_ARGS__)
#define LOG_MEMORY_INFO(fmt, ...)      LOG_INFO("Memory", fmt, ##__VA_ARGS__)
#define LOG_MEMORY_ERROR(fmt, ...)     LOG_ERROR("Memory", fmt, ##__VA_ARGS__)
#define LOG_MEMORY_WARN(fmt, ...)      LOG_WARN("Memory", fmt, ##__VA_ARGS__)

#define LOG_STREAM_DEBUG(fmt, ...)     LOG_DEBUG("Stream", fmt, ##__VA_ARGS__)
#define LOG_STREAM_INFO(fmt, ...)      LOG_INFO("Stream", fmt, ##__VA_ARGS__)
#define LOG_STREAM_ERROR(fmt, ...)     LOG_ERROR("Stream", fmt, ##__VA_ARGS__)
#define LOG_STREAM_WARN(fmt, ...)      LOG_WARN("Stream", fmt, ##__VA_ARGS__)

#define LOG_SECURITY_DEBUG(fmt, ...)   LOG_DEBUG("Security", fmt, ##__VA_ARGS__)
#define LOG_SECURITY_INFO(fmt, ...)    LOG_INFO("Security", fmt, ##__VA_ARGS__)
#define LOG_SECURITY_ERROR(fmt, ...)   LOG_ERROR("Security", fmt, ##__VA_ARGS__)
#define LOG_SECURITY_WARN(fmt, ...)    LOG_WARN("Security", fmt, ##__VA_ARGS__)

#define LOG_CLAMAV_DEBUG(fmt, ...)     LOG_DEBUG("ClamAV", fmt, ##__VA_ARGS__)
#define LOG_CLAMAV_INFO(fmt, ...)      LOG_INFO("ClamAV", fmt, ##__VA_ARGS__)
#define LOG_CLAMAV_ERROR(fmt, ...)     LOG_ERROR("ClamAV", fmt, ##__VA_ARGS__)
#define LOG_CLAMAV_WARN(fmt, ...)      LOG_WARN("ClamAV", fmt, ##__VA_ARGS__)

#define LOG_PERF_DEBUG(fmt, ...)       LOG_DEBUG("Performance", fmt, ##__VA_ARGS__)
#define LOG_PERF_INFO(fmt, ...)        LOG_INFO("Performance", fmt, ##__VA_ARGS__)
#define LOG_PERF_ERROR(fmt, ...)       LOG_ERROR("Performance", fmt, ##__VA_ARGS__)
#define LOG_PERF_WARN(fmt, ...)        LOG_WARN("Performance", fmt, ##__VA_ARGS__)

// Missing function declaration for compatibility
#ifndef strcasestr
char* strcasestr(const char* haystack, const char* needle);
#endif

#endif // CATZILLA_LOGGING_H
