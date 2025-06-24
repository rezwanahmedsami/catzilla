#ifndef CATZILLA_STARTUP_BANNER_H
#define CATZILLA_STARTUP_BANNER_H

#include "server_stats.h"
#include <stdbool.h>
#include <stddef.h>

#ifdef __cplusplus
extern "C" {
#endif

/**
 * Print the startup banner with server statistics
 * @param stats Server statistics structure
 * @param production_mode Whether running in production mode
 */
void catzilla_print_startup_banner(const catzilla_server_stats_t* stats, bool production_mode);

/**
 * Render a horizontal line for the banner box
 * @param buffer Output buffer
 * @param buffer_size Size of output buffer
 * @param width Width of the line
 * @param top_border Whether this is the top border (true) or bottom (false)
 * @param use_unicode Whether to use Unicode box drawing characters
 */
void catzilla_render_box_line(char* buffer, size_t buffer_size, int width, bool top_border, bool use_unicode);

/**
 * Render a content line for the banner box
 * @param buffer Output buffer
 * @param buffer_size Size of output buffer
 * @param width Total width of the box
 * @param content Content to display in the line
 * @param use_unicode Whether to use Unicode box drawing characters
 */
void catzilla_render_content_line(char* buffer, size_t buffer_size, int width, const char* content, bool use_unicode);

/**
 * Render a key-value line for the banner box
 * @param buffer Output buffer
 * @param buffer_size Size of output buffer
 * @param width Total width of the box
 * @param key Key name
 * @param value Value string
 * @param use_unicode Whether to use Unicode box drawing characters
 */
void catzilla_render_kv_line(char* buffer, size_t buffer_size, int width, const char* key, const char* value, bool use_unicode);

/**
 * Check if the current terminal supports Unicode
 * @return true if Unicode is supported, false otherwise
 */
bool catzilla_terminal_supports_unicode(void);

/**
 * Get the optimal banner width based on content
 * @param stats Server statistics
 * @param production_mode Whether in production mode
 * @return Optimal width for the banner
 */
int catzilla_calculate_banner_width(const catzilla_server_stats_t* stats, bool production_mode);

#ifdef __cplusplus
}
#endif

#endif // CATZILLA_STARTUP_BANNER_H
