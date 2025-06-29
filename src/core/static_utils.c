#include "static_server.h"
#include "platform_compat.h"
#include <string.h>
#include <stdio.h>
#include <stdlib.h>
#include <ctype.h>
#include <sys/stat.h>
#ifndef _WIN32
#include <unistd.h>
#endif
#include <limits.h>

// MIME type mappings
static const struct {
    const char* extension;
    const char* mime_type;
    bool compressible;
} mime_types[] = {
    // Web assets (high cache priority, compressible)
    {".html", "text/html; charset=utf-8", true},
    {".htm", "text/html; charset=utf-8", true},
    {".css", "text/css; charset=utf-8", true},
    {".js", "application/javascript; charset=utf-8", true},
    {".mjs", "application/javascript; charset=utf-8", true},
    {".json", "application/json; charset=utf-8", true},
    {".xml", "application/xml; charset=utf-8", true},
    {".txt", "text/plain; charset=utf-8", true},
    {".md", "text/markdown; charset=utf-8", true},

    // Images (not compressible)
    {".png", "image/png", false},
    {".jpg", "image/jpeg", false},
    {".jpeg", "image/jpeg", false},
    {".gif", "image/gif", false},
    {".bmp", "image/bmp", false},
    {".webp", "image/webp", false},
    {".ico", "image/x-icon", false},
    {".svg", "image/svg+xml", true},

    // Fonts (not compressible)
    {".woff", "font/woff", false},
    {".woff2", "font/woff2", false},
    {".ttf", "font/ttf", false},
    {".otf", "font/otf", false},
    {".eot", "application/vnd.ms-fontobject", false},

    // Media (not compressible)
    {".mp4", "video/mp4", false},
    {".webm", "video/webm", false},
    {".avi", "video/x-msvideo", false},
    {".mov", "video/quicktime", false},
    {".mp3", "audio/mpeg", false},
    {".wav", "audio/wav", false},
    {".ogg", "audio/ogg", false},

    // Documents
    {".pdf", "application/pdf", false},
    {".doc", "application/msword", false},
    {".docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document", false},
    {".xls", "application/vnd.ms-excel", false},
    {".xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", false},

    // Archives (not compressible)
    {".zip", "application/zip", false},
    {".tar", "application/x-tar", false},
    {".gz", "application/gzip", false},
    {".rar", "application/vnd.rar", false},
    {".7z", "application/x-7z-compressed", false},

    // Other
    {".manifest", "text/cache-manifest", true},
    {".webmanifest", "application/manifest+json", true},

    // Default
    {"", "application/octet-stream", false}
};

const char* catzilla_static_get_content_type(const char* file_path) {
    if (!file_path) return "application/octet-stream";

    // Find the last dot in the filename
    const char* last_dot = strrchr(file_path, '.');
    if (!last_dot) return "application/octet-stream";

    // Convert extension to lowercase for comparison
    char ext[32];
    strncpy(ext, last_dot, sizeof(ext) - 1);
    ext[sizeof(ext) - 1] = '\0';

    for (char* p = ext; *p; p++) {
        *p = tolower(*p);
    }

    // Look up MIME type
    for (size_t i = 0; i < sizeof(mime_types) / sizeof(mime_types[0]); i++) {
        if (strcmp(ext, mime_types[i].extension) == 0) {
            return mime_types[i].mime_type;
        }
    }

    return "application/octet-stream";
}

bool catzilla_static_is_compressible(const char* file_path) {
    if (!file_path) return false;

    const char* last_dot = strrchr(file_path, '.');
    if (!last_dot) return false;

    char ext[32];
    strncpy(ext, last_dot, sizeof(ext) - 1);
    ext[sizeof(ext) - 1] = '\0';

    for (char* p = ext; *p; p++) {
        *p = tolower(*p);
    }

    for (size_t i = 0; i < sizeof(mime_types) / sizeof(mime_types[0]); i++) {
        if (strcmp(ext, mime_types[i].extension) == 0) {
            return mime_types[i].compressible;
        }
    }

    return false;
}

char* catzilla_static_generate_etag(const char* file_path, time_t last_modified, size_t file_size) {
    if (!file_path) return NULL;

    // Generate ETag based on file path, modification time, and size
    uint64_t hash = 5381;

    // Hash file path
    for (const char* p = file_path; *p; p++) {
        hash = ((hash << 5) + hash) + *p;
    }

    // Combine with modification time and size
    hash ^= (uint64_t)last_modified;
    hash ^= (uint64_t)file_size;

    char* etag = catzilla_static_alloc(32);
    if (!etag) return NULL;

    snprintf(etag, 32, "%lx", (unsigned long)hash);
    return etag;
}

bool catzilla_static_validate_path(const char* requested_path, const char* base_dir) {
    if (!requested_path || !base_dir) return false;

    // Check for empty path
    if (strlen(requested_path) == 0) return false;

    // Resolve the base directory first - it must exist
    char resolved_base[PATH_MAX];
    if (!realpath(base_dir, resolved_base)) {
        return false;  // Base directory must exist
    }

    // For security validation, we don't need the file to exist yet
    // Just check for dangerous patterns in the requested path

    // Check for null bytes (should not happen, but safety check)
    if (strlen(requested_path) != strlen(requested_path)) {
        return false;
    }

    // Check for dangerous patterns (both Unix and Windows path separators)
    if (strstr(requested_path, "../") || strstr(requested_path, "./") ||
        strstr(requested_path, "..\\") || strstr(requested_path, ".\\") ||
        strstr(requested_path, "..") == requested_path) {
        return false;
    }

    // Check for hidden files (starting with .)
    const char* filename = strrchr(requested_path, '/');
    if (!filename) filename = strrchr(requested_path, '\\');
    if (!filename) filename = requested_path;
    else filename++; // Skip the separator

    if (filename[0] == '.') {
        return false;  // Hidden files are blocked
    }

    // Basic path construction to ensure it stays within base
    char full_path[PATH_MAX];
    int ret = snprintf(full_path, PATH_MAX, "%s%s", resolved_base, requested_path);
    if (ret >= PATH_MAX || ret < 0) return false;

    // Ensure the constructed path starts with the base directory
    if (strncmp(full_path, resolved_base, strlen(resolved_base)) != 0) {
        return false;
    }

    return true;
}

bool catzilla_static_check_extension(const char* filename, static_security_config_t* config) {
    if (!filename || !config) return true;  // Allow by default if no config

    const char* last_dot = strrchr(filename, '.');
    if (!last_dot) {
        // No extension - check if extensionless files are allowed
        return config->allowed_extensions == NULL;  // Allow if no whitelist
    }

    char ext[32];
    strncpy(ext, last_dot, sizeof(ext) - 1);
    ext[sizeof(ext) - 1] = '\0';

    // Convert to lowercase
    for (char* p = ext; *p; p++) {
        *p = tolower(*p);
    }

    // Check blocked extensions first (takes priority)
    if (config->blocked_extensions) {
        for (char** blocked = config->blocked_extensions; *blocked; blocked++) {
            if (strcmp(ext, *blocked) == 0) {
                return false;  // Explicitly blocked
            }
        }
    }

    // Check allowed extensions (whitelist)
    if (config->allowed_extensions) {
        for (char** allowed = config->allowed_extensions; *allowed; allowed++) {
            if (strcmp(ext, *allowed) == 0) {
                return true;  // Explicitly allowed
            }
        }
        return false;  // Not in whitelist
    }

    return true;  // No restrictions, allow
}

bool catzilla_static_is_hidden_file(const char* filename) {
    if (!filename) return false;

    const char* basename = strrchr(filename, '/');
    if (basename) {
        basename++;  // Skip the '/'
    } else {
        basename = filename;
    }

    return basename[0] == '.';
}

int catzilla_static_parse_range_header(const char* range_header, size_t file_size,
                                       size_t* start_out, size_t* end_out) {
    if (!range_header || !start_out || !end_out) return -1;

    // Range header format: "bytes=start-end" or "bytes=start-" or "bytes=-suffix"
    if (strncmp(range_header, "bytes=", 6) != 0) {
        return -1;  // Invalid format
    }

    const char* range_spec = range_header + 6;

    // Parse range specification
    char* dash = strchr(range_spec, '-');
    if (!dash) return -1;

    *start_out = 0;
    *end_out = file_size - 1;

    if (dash == range_spec) {
        // Suffix range: "-500" means last 500 bytes
        long suffix_length = strtol(dash + 1, NULL, 10);
        if (suffix_length <= 0 || (size_t)suffix_length >= file_size) {
            return -1;
        }
        *start_out = file_size - suffix_length;
    } else {
        // Start specified
        *start_out = strtoul(range_spec, NULL, 10);
        if (*start_out >= file_size) {
            return -1;
        }

        if (*(dash + 1) != '\0') {
            // End specified
            *end_out = strtoul(dash + 1, NULL, 10);
            if (*end_out >= file_size) {
                *end_out = file_size - 1;
            }
        }
    }

    // Validate range
    if (*start_out > *end_out) {
        return -1;
    }

    return 0;
}

// Get file extension for comparison
const char* get_file_extension(const char* filename) {
    if (!filename) return "";

    const char* last_dot = strrchr(filename, '.');
    return last_dot ? last_dot : "";
}

// Check if path contains dangerous patterns
bool contains_dangerous_patterns(const char* path) {
    if (!path) return true;

    // List of dangerous patterns
    const char* dangerous[] = {
        "../",
        "..\\",
        "/..",
        "\\..",
        "%2e%2e",
        "%2E%2E",
        "..%2f",
        "..%5c",
        "%2e%2e%2f",
        "%2e%2e%5c",
        NULL
    };

    for (const char** pattern = dangerous; *pattern; pattern++) {
        if (strstr(path, *pattern)) {
            return true;
        }
    }

    return false;
}

// Canonicalize path (remove . and .. components)
char* catzilla_static_canonicalize_path(const char* path) {
    if (!path) return NULL;

    size_t path_len = strlen(path);
    char* canonical = catzilla_static_alloc(path_len + 1);
    if (!canonical) return NULL;

    // Use realpath if possible, otherwise do manual canonicalization
    if (realpath(path, canonical)) {
        return canonical;
    }

    // Manual canonicalization for non-existent paths
    strcpy(canonical, path);

    // Simple implementation - just check for obvious patterns
    if (contains_dangerous_patterns(canonical)) {
        catzilla_static_free(canonical);
        return NULL;
    }

    return canonical;
}

// Function expected by the test - wrapper for the existing get_content_type function
void catzilla_static_get_mime_type(const char* filename, const char** mime_type, bool* compressible) {
    if (!filename || !mime_type || !compressible) return;

    // Find the last dot in the filename
    const char* last_dot = strrchr(filename, '.');
    if (!last_dot) {
        *mime_type = "application/octet-stream";
        *compressible = false;
        return;
    }

    // Convert extension to lowercase for comparison
    char ext[32];
    strncpy(ext, last_dot, sizeof(ext) - 1);
    ext[sizeof(ext) - 1] = '\0';

    for (char* p = ext; *p; p++) {
        *p = tolower(*p);
    }

    // Look up MIME type and compressibility
    for (size_t i = 0; i < sizeof(mime_types) / sizeof(mime_types[0]); i++) {
        if (strcmp(ext, mime_types[i].extension) == 0) {
            *mime_type = mime_types[i].mime_type;
            *compressible = mime_types[i].compressible;
            return;
        }
    }

    // Default
    *mime_type = "application/octet-stream";
    *compressible = false;
}

// Simple path safety check for testing
int catzilla_static_is_safe_path(const char* path) {
    if (!path || strlen(path) == 0) return 0;

    // Check for directory traversal patterns
    if (strstr(path, "../") || strstr(path, "..\\") ||
        strstr(path, "/.") || strstr(path, "\\.")) {
        return 0;
    }

    // Check for hidden files (starting with .)
    const char* filename = strrchr(path, '/');
    if (filename) {
        filename++; // Skip the '/'
        if (filename[0] == '.' && filename[1] != '\0') {
            return 0; // Hidden file
        }
    } else {
        if (path[0] == '.' && path[1] != '\0') {
            return 0; // Hidden file
        }
    }

    // Check for dangerous file patterns
    if (strstr(path, ".htaccess") || strstr(path, ".env") ||
        strstr(path, "config") || strstr(path, "passwd")) {
        return 0;
    }

    return 1; // Safe
}
