#include "startup_banner.h"
#include <stdio.h>
#include <string.h>
#include <stdlib.h>

#ifdef _WIN32
#include <windows.h>
#include <io.h>
#define isatty _isatty
#define fileno _fileno
#else
#include <unistd.h>
#endif

// Unicode box drawing characters
#define BOX_TOP_LEFT     "╔"
#define BOX_TOP_RIGHT    "╗"
#define BOX_BOTTOM_LEFT  "╚"
#define BOX_BOTTOM_RIGHT "╝"
#define BOX_HORIZONTAL   "═"
#define BOX_VERTICAL     "║"

// ASCII fallback characters
#define ASCII_TOP_LEFT     "+"
#define ASCII_TOP_RIGHT    "+"
#define ASCII_BOTTOM_LEFT  "+"
#define ASCII_BOTTOM_RIGHT "+"
#define ASCII_HORIZONTAL   "="
#define ASCII_VERTICAL     "|"

void catzilla_print_startup_banner(const catzilla_server_stats_t* stats, bool production_mode) {
    if (!stats) return;

    bool use_unicode = catzilla_terminal_supports_unicode();
    int width = catzilla_calculate_banner_width(stats, production_mode);

    char line_buffer[512];
    char content_buffer[256];

    // Print top border
    catzilla_render_box_line(line_buffer, sizeof(line_buffer), width, true, use_unicode);
    printf("%s\n", line_buffer);

    // Print title line
    const char* mode_str = production_mode ? "PRODUCTION" : "DEVELOPMENT";
    snprintf(content_buffer, sizeof(content_buffer), "🐱 Catzilla v%s - %s", stats->version, mode_str);
    catzilla_render_content_line(line_buffer, sizeof(line_buffer), width, content_buffer, use_unicode);
    printf("%s\n", line_buffer);

    // Print URL line
    snprintf(content_buffer, sizeof(content_buffer), "http://%s:%d", stats->bind_host, stats->bind_port);
    catzilla_render_content_line(line_buffer, sizeof(line_buffer), width, content_buffer, use_unicode);
    printf("%s\n", line_buffer);

    // Print bind info line
    snprintf(content_buffer, sizeof(content_buffer), "(bound on host %s and port %d)", stats->bind_host, stats->bind_port);
    catzilla_render_content_line(line_buffer, sizeof(line_buffer), width, content_buffer, use_unicode);
    printf("%s\n", line_buffer);

    // Print empty line
    catzilla_render_content_line(line_buffer, sizeof(line_buffer), width, "", use_unicode);
    printf("%s\n", line_buffer);

    // Print statistics
    snprintf(content_buffer, sizeof(content_buffer), "%d", stats->route_count);
    catzilla_render_kv_line(line_buffer, sizeof(line_buffer), width, "Routes", content_buffer, use_unicode);
    printf("%s\n", line_buffer);

    snprintf(content_buffer, sizeof(content_buffer), "%d", stats->worker_count);
    catzilla_render_kv_line(line_buffer, sizeof(line_buffer), width, "Workers", content_buffer, use_unicode);
    printf("%s\n", line_buffer);

    const char* jemalloc_status = stats->jemalloc_enabled ? "Enabled" : "Disabled";
    catzilla_render_kv_line(line_buffer, sizeof(line_buffer), width, "jemalloc", jemalloc_status, use_unicode);
    printf("%s\n", line_buffer);

    // Development-only fields
    if (!production_mode) {
        if (stats->di_service_count > 0) {
            snprintf(content_buffer, sizeof(content_buffer), "Enabled (%d services)", stats->di_service_count);
            catzilla_render_kv_line(line_buffer, sizeof(line_buffer), width, "DI Container", content_buffer, use_unicode);
            printf("%s\n", line_buffer);
        }

        const char* validation_status = stats->auto_validation ? "Enabled" : "Disabled";
        catzilla_render_kv_line(line_buffer, sizeof(line_buffer), width, "Auto Validation", validation_status, use_unicode);
        printf("%s\n", line_buffer);

        if (stats->profiling_enabled) {
            snprintf(content_buffer, sizeof(content_buffer), "Enabled (interval: %ds)", stats->profiling_interval);
            catzilla_render_kv_line(line_buffer, sizeof(line_buffer), width, "Profiling", content_buffer, use_unicode);
            printf("%s\n", line_buffer);
        }

        catzilla_render_kv_line(line_buffer, sizeof(line_buffer), width, "Debug Mode", "ON", use_unicode);
        printf("%s\n", line_buffer);
    }

    snprintf(content_buffer, sizeof(content_buffer), "%d", (int)stats->pid);
    catzilla_render_kv_line(line_buffer, sizeof(line_buffer), width, "PID", content_buffer, use_unicode);
    printf("%s\n", line_buffer);

    // Print bottom border
    catzilla_render_box_line(line_buffer, sizeof(line_buffer), width, false, use_unicode);
    printf("%s\n", line_buffer);

    // Print newline for spacing
    printf("\n");
}

void catzilla_render_box_line(char* buffer, size_t buffer_size, int width, bool top_border, bool use_unicode) {
    if (!buffer || buffer_size == 0 || width < 3) return;

    const char* left_char = use_unicode ?
        (top_border ? BOX_TOP_LEFT : BOX_BOTTOM_LEFT) :
        (top_border ? ASCII_TOP_LEFT : ASCII_BOTTOM_LEFT);
    const char* right_char = use_unicode ?
        (top_border ? BOX_TOP_RIGHT : BOX_BOTTOM_RIGHT) :
        (top_border ? ASCII_TOP_RIGHT : ASCII_BOTTOM_RIGHT);
    const char* fill_char = use_unicode ? BOX_HORIZONTAL : ASCII_HORIZONTAL;

    int pos = 0;

    // Left border
    pos += snprintf(buffer + pos, buffer_size - pos, "%s", left_char);

    // Fill middle
    for (int i = 0; i < width - 2 && pos < (int)buffer_size - 1; i++) {
        pos += snprintf(buffer + pos, buffer_size - pos, "%s", fill_char);
    }

    // Right border
    if (pos < (int)buffer_size - 1) {
        snprintf(buffer + pos, buffer_size - pos, "%s", right_char);
    }
}

void catzilla_render_content_line(char* buffer, size_t buffer_size, int width, const char* content, bool use_unicode) {
    if (!buffer || buffer_size == 0 || width < 3) return;

    const char* border_char = use_unicode ? BOX_VERTICAL : ASCII_VERTICAL;

    // Calculate padding
    int content_len = content ? (int)strlen(content) : 0;
    int available_space = width - 4; // 2 for borders, 2 for padding
    int left_padding = 1;
    int right_padding = available_space - content_len - left_padding;

    if (right_padding < 0) {
        right_padding = 0;
        content_len = available_space - left_padding;
    }

    snprintf(buffer, buffer_size, "%s%*s%.*s%*s%s",
             border_char,
             left_padding, "",
             content_len, content ? content : "",
             right_padding, "",
             border_char);
}

void catzilla_render_kv_line(char* buffer, size_t buffer_size, int width, const char* key, const char* value, bool use_unicode) {
    if (!buffer || buffer_size == 0 || width < 3 || !key || !value) return;

    const char* border_char = use_unicode ? BOX_VERTICAL : ASCII_VERTICAL;

    // Calculate spacing
    int key_len = (int)strlen(key);
    int value_len = (int)strlen(value);
    int available_space = width - 4; // 2 for borders, 2 for padding
    int dots_space = available_space - key_len - value_len - 2; // 2 for spaces around dots

    if (dots_space < 3) dots_space = 3; // Minimum dots

    char dots[64];
    memset(dots, '.', sizeof(dots) - 1);
    dots[dots_space < 63 ? dots_space : 63] = '\0';

    snprintf(buffer, buffer_size, "%s %s %s %s %s",
             border_char, key, dots, value, border_char);
}

bool catzilla_terminal_supports_unicode(void) {
    // Check if we're writing to a terminal
    if (!isatty(fileno(stdout))) {
        return false;
    }

#ifdef _WIN32
    // On Windows, check console mode and codepage
    HANDLE hConsole = GetStdHandle(STD_OUTPUT_HANDLE);
    if (hConsole == INVALID_HANDLE_VALUE) return false;

    CONSOLE_SCREEN_BUFFER_INFO csbi;
    if (!GetConsoleScreenBufferInfo(hConsole, &csbi)) return false;

    // Check if we're in a modern Windows terminal
    DWORD mode;
    if (GetConsoleMode(hConsole, &mode)) {
        // Check for virtual terminal sequences support
        if (mode & ENABLE_VIRTUAL_TERMINAL_PROCESSING) {
            return true;
        }
    }

    // Check codepage for UTF-8 support
    return GetConsoleOutputCP() == CP_UTF8;
#else
    // On Unix-like systems, check environment variables
    const char* term = getenv("TERM");
    const char* lang = getenv("LANG");
    const char* lc_all = getenv("LC_ALL");

    // Most modern terminals support Unicode
    if (term && (strstr(term, "xterm") || strstr(term, "screen") ||
                strstr(term, "tmux") || strstr(term, "rxvt"))) {
        return true;
    }

    // Check locale for UTF-8
    if ((lang && strstr(lang, "UTF-8")) || (lc_all && strstr(lc_all, "UTF-8"))) {
        return true;
    }

    // Conservative fallback
    return false;
#endif
}

int catzilla_calculate_banner_width(const catzilla_server_stats_t* stats, bool production_mode) {
    if (!stats) return 60;

    // Calculate width based on content
    int min_width = 60;

    // Check various content lengths
    char temp_buffer[256];

    // Title line
    snprintf(temp_buffer, sizeof(temp_buffer), "🐱 Catzilla v%s - %s",
             stats->version, production_mode ? "PRODUCTION" : "DEVELOPMENT");
    int title_width = (int)strlen(temp_buffer) + 4; // 2 borders + 2 padding

    // URL line
    snprintf(temp_buffer, sizeof(temp_buffer), "http://%s:%d", stats->bind_host, stats->bind_port);
    int url_width = (int)strlen(temp_buffer) + 4;

    // Bind info line
    snprintf(temp_buffer, sizeof(temp_buffer), "(bound on host %s and port %d)", stats->bind_host, stats->bind_port);
    int bind_width = (int)strlen(temp_buffer) + 4;

    // Find maximum width needed
    int max_width = min_width;
    if (title_width > max_width) max_width = title_width;
    if (url_width > max_width) max_width = url_width;
    if (bind_width > max_width) max_width = bind_width;

    // Cap at reasonable maximum
    if (max_width > 100) max_width = 100;

    return max_width;
}
