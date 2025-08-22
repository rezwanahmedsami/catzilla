#include "upload_parser.h"
#include "upload_memory.h"
#include "logging.h"
#include "platform_compat.h"
#include <string.h>
#ifndef _WIN32
#include <strings.h>  // For strncasecmp on POSIX systems
#endif
#include <stdlib.h>
#include <stdio.h>
#include <ctype.h>
#include <time.h>

// Platform-specific includes
#ifdef _WIN32
#include <windows.h>
#include <winsock2.h>  // Must include winsock2.h before windows.h for timeval
#include <io.h>

// Windows implementation of gettimeofday (struct timeval is already defined in winsock2.h)
static int gettimeofday(struct timeval *tv, struct timezone *tz) {
    FILETIME ft;
    unsigned __int64 tmpres = 0;
    static int tzflag = 0;

    if (NULL != tv) {
        GetSystemTimeAsFileTime(&ft);
        tmpres |= ft.dwHighDateTime;
        tmpres <<= 32;
        tmpres |= ft.dwLowDateTime;
        tmpres /= 10;  // convert into microseconds
        tmpres -= 11644473600000000ULL; // UNIX epoch start
        tv->tv_sec = (long)(tmpres / 1000000UL);
        tv->tv_usec = (long)(tmpres % 1000000UL);
    }
    return 0;
}
#else
#include <unistd.h>
#include <sys/time.h>
#endif

// Platform compatibility: strcasestr may not be available on all systems
#ifndef _GNU_SOURCE
static char* strcasestr(const char* haystack, const char* needle) {
    size_t len = strlen(needle);
    while (*haystack) {
        if (strncasecmp(haystack, needle, len) == 0) {
            return (char*)haystack;
        }
        haystack++;
    }
    return NULL;
}
#endif

// Windows compatibility: strncasecmp
#ifdef _WIN32
#define strncasecmp _strnicmp
#endif

// Static function declarations
static int parse_multipart_boundary(multipart_parser_t* parser, const char* data, size_t len);
static int parse_multipart_headers(multipart_parser_t* parser, const char* data, size_t len);
static int parse_multipart_data(multipart_parser_t* parser, const char* data, size_t len);
static int find_boundary_in_buffer(const char* buffer, size_t len, const char* boundary, size_t boundary_len);
static char* extract_header_value(const char* headers, const char* header_name);
static void cleanup_upload_file_internal(catzilla_upload_file_t* file);

// Global time initialization
static uint64_t g_start_time_ns = 0;

// Initialize multipart parser
int catzilla_multipart_parse_init(multipart_parser_t* parser, const char* content_type) {
    if (!parser || !content_type) {
        LOG_PARSER_ERROR("Invalid parameters for multipart parser init");
        return -1;
    }

    // Initialize parser structure
    memset(parser, 0, sizeof(multipart_parser_t));
    parser->state = MULTIPART_STATE_INIT;

    // Extract boundary from Content-Type header
    parser->boundary = catzilla_extract_boundary(content_type);
    if (!parser->boundary) {
        LOG_PARSER_ERROR("Failed to extract boundary from Content-Type: %s", content_type);
        return -1;
    }

    parser->boundary_len = strlen(parser->boundary);
    LOG_PARSER_DEBUG("Extracted boundary: %s (length: %zu)", parser->boundary, parser->boundary_len);

    // Initialize buffer for parsing
    parser->buffer_size = 8192; // 8KB initial buffer
    parser->buffer = malloc(parser->buffer_size);
    if (!parser->buffer) {
        LOG_PARSER_ERROR("Failed to allocate parser buffer");
        free(parser->boundary);
        return -1;
    }

    // Initialize files array
    parser->files_capacity = 16; // Start with capacity for 16 files
    parser->files = malloc(sizeof(catzilla_upload_file_t*) * parser->files_capacity);
    if (!parser->files) {
        LOG_PARSER_ERROR("Failed to allocate files array");
        free(parser->boundary);
        free(parser->buffer);
        return -1;
    }

    // Set default limits
    parser->max_total_size = 1024 * 1024 * 1024; // 1GB default
    parser->max_files = 100; // 100 files default

    // Initialize memory manager
    parser->memory_manager = catzilla_upload_memory_init();
    if (!parser->memory_manager) {
        LOG_MEMORY_WARN("Failed to initialize memory manager, using standard malloc");
    }

    parser->state = MULTIPART_STATE_BOUNDARY;
    LOG_PARSER_INFO("Multipart parser initialized successfully");
    return 0;
}

// Parse chunk of multipart data
int catzilla_multipart_parse_chunk(multipart_parser_t* parser, const char* data, size_t len) {
    if (!parser || !data || len == 0) {
        LOG_PARSER_ERROR("Invalid parameters for multipart parse chunk");
        return -1;
    }

    if (parser->state == MULTIPART_STATE_ERROR) {
        LOG_PARSER_ERROR("Parser is in error state, cannot continue");
        return -1;
    }

    // Ensure buffer has enough space
    if (parser->buffer_pos + len > parser->buffer_size) {
        size_t new_size = parser->buffer_size;
        while (new_size < parser->buffer_pos + len) {
            new_size *= 2;
        }

        char* new_buffer = realloc(parser->buffer, new_size);
        if (!new_buffer) {
            LOG_PARSER_ERROR("Failed to reallocate parser buffer to %zu bytes", new_size);
            parser->state = MULTIPART_STATE_ERROR;
            return -1;
        }

        parser->buffer = new_buffer;
        parser->buffer_size = new_size;
        LOG_PARSER_DEBUG("Reallocated parser buffer to %zu bytes", new_size);
    }

    // Copy data to buffer
    memcpy(parser->buffer + parser->buffer_pos, data, len);
    parser->buffer_pos += len;

    // Process buffer based on current state
    int result = 0;
    while (parser->buffer_pos > 0 && parser->state != MULTIPART_STATE_ERROR && parser->state != MULTIPART_STATE_END) {
        switch (parser->state) {
            case MULTIPART_STATE_BOUNDARY:
                result = parse_multipart_boundary(parser, parser->buffer, parser->buffer_pos);
                break;

            case MULTIPART_STATE_HEADERS:
                result = parse_multipart_headers(parser, parser->buffer, parser->buffer_pos);
                break;

            case MULTIPART_STATE_DATA:
                result = parse_multipart_data(parser, parser->buffer, parser->buffer_pos);
                break;

            default:
                LOG_PARSER_ERROR("Unknown multipart parser state: %d", parser->state);
                parser->state = MULTIPART_STATE_ERROR;
                result = -1;
        }

        if (result < 0) {
            parser->state = MULTIPART_STATE_ERROR;
            break;
        }

        if (result == 0) {
            // Need more data
            break;
        }
    }

    return (parser->state == MULTIPART_STATE_ERROR) ? -1 : 0;
}

// Complete multipart parsing
int catzilla_multipart_parse_complete(multipart_parser_t* parser) {
    if (!parser) {
        return -1;
    }

    if (parser->state == MULTIPART_STATE_ERROR) {
        LOG_PARSER_ERROR("Cannot complete parsing - parser is in error state");
        return -1;
    }

    // Finalize current file if any
    if (parser->current_file) {
        if (catzilla_upload_file_finalize(parser->current_file) != 0) {
            LOG_PARSER_ERROR("Failed to finalize current upload file");
            return -1;
        }

        if (parser->on_file_end) {
            parser->on_file_end(parser, parser->current_file);
        }

        parser->current_file = NULL;
    }

    // Call completion callback
    if (parser->on_parse_complete) {
        parser->on_parse_complete(parser);
    }

    parser->state = MULTIPART_STATE_END;
    LOG_PARSER_INFO("Multipart parsing completed successfully. Processed %zu files", parser->files_count);
    return 0;
}

// Parse boundary state
static int parse_multipart_boundary(multipart_parser_t* parser, const char* data, size_t len) {
    // Look for the boundary
    int boundary_pos = find_boundary_in_buffer(data, len, parser->boundary, parser->boundary_len);

    if (boundary_pos < 0) {
        // Boundary not found, need more data
        return 0;
    }

    // Found boundary, check if it's the end boundary
    size_t total_boundary_len = 2 + parser->boundary_len; // "--" + boundary
    if (boundary_pos + total_boundary_len + 2 < len) {
        if (data[boundary_pos + total_boundary_len] == '-' &&
            data[boundary_pos + total_boundary_len + 1] == '-') {
            // End boundary found
            parser->state = MULTIPART_STATE_END;
            return 1;
        }
    }

    // Regular boundary, move to headers
    size_t consumed = boundary_pos + total_boundary_len;

    // Skip CRLF after boundary
    if (consumed + 1 < len && data[consumed] == '\r' && data[consumed + 1] == '\n') {
        consumed += 2;
    } else if (consumed < len && data[consumed] == '\n') {
        consumed += 1;
    }

    // Move remaining data to beginning of buffer
    if (consumed < len) {
        memmove(parser->buffer, data + consumed, len - consumed);
        parser->buffer_pos = len - consumed;
    } else {
        parser->buffer_pos = 0;
    }

    parser->state = MULTIPART_STATE_HEADERS;
    return 1;
}

// Parse headers state
static int parse_multipart_headers(multipart_parser_t* parser, const char* data, size_t len) {
    // Look for double CRLF (end of headers)
    char* header_end = NULL;
    size_t header_end_len = 0;

    for (size_t i = 0; i < len - 3; i++) {
        if (data[i] == '\r' && data[i + 1] == '\n' &&
            data[i + 2] == '\r' && data[i + 3] == '\n') {
            header_end = (char*)(data + i);
            header_end_len = 4;
            break;
        } else if (data[i] == '\n' && data[i + 1] == '\n') {
            header_end = (char*)(data + i);
            header_end_len = 2;
            break;
        }
    }

    if (!header_end) {
        // Headers not complete, need more data
        return 0;
    }

    // Extract headers
    size_t headers_len = header_end - data;
    char* headers = malloc(headers_len + 1);
    if (!headers) {
        LOG_PARSER_ERROR("Failed to allocate memory for headers");
        return -1;
    }

    memcpy(headers, data, headers_len);
    headers[headers_len] = '\0';

    LOG_PARSER_DEBUG("Parsed headers (%zu bytes): %s", headers_len, headers);

    // Parse Content-Disposition header for filename and field name
    char* content_disposition = extract_header_value(headers, "Content-Disposition");
    char* filename = NULL;
    char* field_name = NULL;
    char* content_type = NULL;

    if (content_disposition) {
        filename = catzilla_parse_content_disposition(content_disposition, "filename");
        field_name = catzilla_parse_content_disposition(content_disposition, "name");
        free(content_disposition);
    }

    // Parse Content-Type header
    content_type = extract_header_value(headers, "Content-Type");
    if (!content_type) {
        content_type = strdup("application/octet-stream"); // Default type
    }

    free(headers);

    // Create new upload file
    parser->current_file = catzilla_upload_file_create(field_name, filename, content_type);
    if (!parser->current_file) {
        LOG_PARSER_ERROR("Failed to create upload file");
        free(field_name);
        free(filename);
        free(content_type);
        return -1;
    }

    // Add to files array
    if (parser->files_count >= parser->files_capacity) {
        size_t new_capacity = parser->files_capacity * 2;
        catzilla_upload_file_t** new_files = realloc(parser->files,
                                                    sizeof(catzilla_upload_file_t*) * new_capacity);
        if (!new_files) {
            LOG_PARSER_ERROR("Failed to expand files array");
            catzilla_upload_file_cleanup(parser->current_file);
            parser->current_file = NULL;
            free(field_name);
            free(filename);
            free(content_type);
            return -1;
        }
        parser->files = new_files;
        parser->files_capacity = new_capacity;
    }

    parser->files[parser->files_count++] = parser->current_file;
    catzilla_upload_file_ref(parser->current_file); // Add reference for array

    // Call file start callback
    if (parser->on_file_start) {
        parser->on_file_start(parser, parser->current_file);
    }

    // Move to data parsing state
    size_t consumed = headers_len + header_end_len;
    if (consumed < len) {
        memmove(parser->buffer, data + consumed, len - consumed);
        parser->buffer_pos = len - consumed;
    } else {
        parser->buffer_pos = 0;
    }

    parser->state = MULTIPART_STATE_DATA;

    free(field_name);
    free(filename);
    free(content_type);
    return 1;
}

// Parse data state
static int parse_multipart_data(multipart_parser_t* parser, const char* data, size_t len) {
    if (!parser->current_file) {
        LOG_PARSER_ERROR("No current file for data parsing");
        return -1;
    }

    // Look for next boundary
    int boundary_pos = find_boundary_in_buffer(data, len, parser->boundary, parser->boundary_len);

    if (boundary_pos < 0) {
        // No boundary found, all data belongs to current file
        if (len > 0) {
            int result = catzilla_upload_file_write_chunk(parser->current_file, data, len);
            if (result != 0) {
                LOG_PARSER_ERROR("Failed to write chunk to upload file");
                return -1;
            }

            if (parser->on_file_data) {
                parser->on_file_data(parser, parser->current_file, data, len);
            }
        }

        parser->buffer_pos = 0; // All data consumed
        return 0; // Need more data
    }

    // Found boundary, write data before boundary to current file
    if (boundary_pos > 0) {
        // Remove trailing CRLF before boundary
        size_t data_len = boundary_pos;
        if (data_len >= 2 && data[data_len - 2] == '\r' && data[data_len - 1] == '\n') {
            data_len -= 2;
        } else if (data_len >= 1 && data[data_len - 1] == '\n') {
            data_len -= 1;
        }

        if (data_len > 0) {
            int result = catzilla_upload_file_write_chunk(parser->current_file, data, data_len);
            if (result != 0) {
                LOG_PARSER_ERROR("Failed to write final chunk to upload file");
                return -1;
            }

            if (parser->on_file_data) {
                parser->on_file_data(parser, parser->current_file, data, data_len);
            }
        }
    }

    // Finalize current file
    if (catzilla_upload_file_finalize(parser->current_file) != 0) {
        LOG_PARSER_ERROR("Failed to finalize upload file");
        return -1;
    }

    if (parser->on_file_end) {
        parser->on_file_end(parser, parser->current_file);
    }

    parser->current_file = NULL;

    // Move remaining data to beginning of buffer
    if (boundary_pos < len) {
        memmove(parser->buffer, data + boundary_pos, len - boundary_pos);
        parser->buffer_pos = len - boundary_pos;
    } else {
        parser->buffer_pos = 0;
    }

    parser->state = MULTIPART_STATE_BOUNDARY;
    return 1;
}

// Find boundary in buffer
static int find_boundary_in_buffer(const char* buffer, size_t len, const char* boundary, size_t boundary_len) {
    if (len < boundary_len + 2) {
        return -1; // Not enough data for boundary
    }

    for (size_t i = 0; i <= len - boundary_len - 2; i++) {
        if (buffer[i] == '-' && buffer[i + 1] == '-' &&
            memcmp(buffer + i + 2, boundary, boundary_len) == 0) {
            return i;
        }
    }

    return -1;
}

// Extract header value
static char* extract_header_value(const char* headers, const char* header_name) {
    char* header_start = strcasestr(headers, header_name);
    if (!header_start) {
        return NULL;
    }

    char* colon = strchr(header_start, ':');
    if (!colon) {
        return NULL;
    }

    char* value_start = colon + 1;
    while (*value_start == ' ' || *value_start == '\t') {
        value_start++;
    }

    char* value_end = strchr(value_start, '\r');
    if (!value_end) {
        value_end = strchr(value_start, '\n');
    }
    if (!value_end) {
        value_end = value_start + strlen(value_start);
    }

    size_t value_len = value_end - value_start;
    char* value = malloc(value_len + 1);
    if (!value) {
        return NULL;
    }

    memcpy(value, value_start, value_len);
    value[value_len] = '\0';

    // Trim trailing whitespace
    while (value_len > 0 && (value[value_len - 1] == ' ' || value[value_len - 1] == '\t')) {
        value[--value_len] = '\0';
    }

    return value;
}

// Create upload file
catzilla_upload_file_t* catzilla_upload_file_create(const char* field_name, const char* filename, const char* content_type) {
    catzilla_upload_file_t* file = malloc(sizeof(catzilla_upload_file_t));
    if (!file) {
        LOG_PARSER_ERROR("Failed to allocate memory for upload file");
        return NULL;
    }

    memset(file, 0, sizeof(catzilla_upload_file_t));

    // Set basic properties
    if (field_name) {
        file->field_name = strdup(field_name);
        if (!file->field_name) {
            LOG_PARSER_ERROR("Failed to allocate memory for field_name");
            free(file);
            return NULL;
        }
    }

    if (filename) {
        file->filename = strdup(filename);
        if (!file->filename) {
            LOG_PARSER_ERROR("Failed to allocate memory for filename");
            free(file->field_name);
            free(file);
            return NULL;
        }
    }

    if (content_type) {
        file->content_type = strdup(content_type);
        if (!file->content_type) {
            LOG_PARSER_ERROR("Failed to allocate memory for content_type");
            free(file->field_name);
            free(file->filename);
            free(file);
            return NULL;
        }
    }

    // Initialize defaults - use maximum possible size, let Python validation handle limits
    file->max_size = UPLOAD_MEMORY_LIMIT_BYTES; // 1GB max (defined in upload_parser.h)
    file->state = UPLOAD_STATE_INITIALIZING;
    file->upload_start_time = catzilla_get_time_ns();
    file->ref_count = 1;
    file->buffer_size = 8192; // 8KB default buffer

    // Determine size class for memory optimization
    file->size_class = UPLOAD_SIZE_SMALL; // Will be updated as data comes in

    LOG_PARSER_DEBUG("Created upload file: field_name=%s, filename=%s, content_type=%s",
              file->field_name ? file->field_name : "unknown",
              file->filename ? file->filename : "unknown",
              file->content_type ? file->content_type : "unknown");

    return file;
}

// Write chunk to upload file
int catzilla_upload_file_write_chunk(catzilla_upload_file_t* file, const char* data, size_t len) {
    if (!file || !data || len == 0) {
        return -1;
    }

    // Update state if initializing
    if (file->state == UPLOAD_STATE_INITIALIZING) {
        file->state = UPLOAD_STATE_RECEIVING;
    }

    // Validate chunk before processing
    int validation_result = catzilla_upload_validate_chunk(file, data, len);
    if (validation_result != CATZILLA_UPLOAD_SUCCESS) {
        catzilla_upload_set_error(file, validation_result, "Chunk validation failed");
        return -1;
    }

    // Update size and performance metrics
    file->bytes_received += len;
    catzilla_atomic_increment(&file->chunks_processed);

    // Update size class based on current size
    if (file->bytes_received > 50 * 1024 * 1024) {
        file->size_class = UPLOAD_SIZE_LARGE;
    } else if (file->bytes_received > 1024 * 1024) {
        file->size_class = UPLOAD_SIZE_MEDIUM;
    }

    // Calculate upload speed
    uint64_t current_time = catzilla_get_time_ns();
    if (current_time > file->upload_start_time) {
        double elapsed_seconds = (current_time - file->upload_start_time) / 1e9;
        double mb_received = file->bytes_received / (1024.0 * 1024.0);
        file->upload_speed_mbps = mb_received / elapsed_seconds;
    }

    // Check if this is a text file that should be null-terminated
    bool is_text_file = false;
    if (file->content_type) {
        is_text_file = (strncmp(file->content_type, "text/", 5) == 0) ||
                       (strstr(file->content_type, "json") != NULL) ||
                       (strstr(file->content_type, "xml") != NULL) ||
                       (strstr(file->content_type, "javascript") != NULL) ||
                       (strstr(file->content_type, "css") != NULL);
    }

    // Store data in memory
    if (!file->content) {
        // First chunk - allocate initial buffer (extra byte only for text files)
        size_t alloc_size = len + (is_text_file ? 1 : 0);
        file->content = malloc(alloc_size);
        if (!file->content) {
            LOG_PARSER_ERROR("Failed to allocate memory for file content");
            return -1;
        }
        memcpy(file->content, data, len);
        if (is_text_file) {
            file->content[len] = '\0';  // Null terminate only for text files
        }
    } else {
        // Subsequent chunks - reallocate buffer (extra byte only for text files)
        size_t alloc_size = file->bytes_received + len + (is_text_file ? 1 : 0);
        char* new_content = realloc(file->content, alloc_size);
        if (!new_content) {
            LOG_PARSER_ERROR("Failed to reallocate memory for file content");
            return -1;
        }
        file->content = new_content;
        memcpy(file->content + file->bytes_received, data, len);
        if (is_text_file) {
            file->content[file->bytes_received + len] = '\0';  // Null terminate only for text files
        }
    }

    // Update total size to include the new data
    file->size = file->bytes_received + len;

    LOG_PARSER_DEBUG("Wrote %zu bytes to upload file (total: %" PRIu64 " bytes, speed: %.2f MB/s)",
              len, file->size, file->upload_speed_mbps);

    return 0;
}

// Finalize upload file
int catzilla_upload_file_finalize(catzilla_upload_file_t* file) {
    if (!file) {
        return -1;
    }

    file->state = UPLOAD_STATE_COMPLETE;
    file->size = file->bytes_received;

    LOG_PARSER_INFO("Finalized upload file: %s (%" PRIu64 " bytes, %.2f MB/s)",
             file->filename ? file->filename : "unknown",
             file->size, file->upload_speed_mbps);

    return 0;
}

// Cleanup parser
void catzilla_multipart_parser_cleanup(multipart_parser_t* parser) {
    if (!parser) {
        return;
    }

    // Cleanup boundary
    if (parser->boundary) {
        free(parser->boundary);
        parser->boundary = NULL;
    }

    // Cleanup buffer
    if (parser->buffer) {
        free(parser->buffer);
        parser->buffer = NULL;
    }

    // Cleanup files
    if (parser->files) {
        for (size_t i = 0; i < parser->files_count; i++) {
            if (parser->files[i]) {
                catzilla_upload_file_unref(parser->files[i]);
                parser->files[i] = NULL;
            }
        }
        free(parser->files);
        parser->files = NULL;
    }

    // Cleanup current file
    if (parser->current_file) {
        catzilla_upload_file_unref(parser->current_file);
        parser->current_file = NULL;
    }

    // Cleanup memory manager
    if (parser->memory_manager) {
        catzilla_upload_memory_cleanup(parser->memory_manager);
        parser->memory_manager = NULL;
    }

    LOG_PARSER_DEBUG("Multipart parser cleanup completed");
}

// Reference counting for upload files
void catzilla_upload_file_ref(catzilla_upload_file_t* file) {
    if (file) {
        file->ref_count++;
    }
}

void catzilla_upload_file_unref(catzilla_upload_file_t* file) {
    if (!file) {
        return;
    }

    file->ref_count--;
    if (file->ref_count <= 0) {
        cleanup_upload_file_internal(file);
    }
}

// Internal cleanup function
static void cleanup_upload_file_internal(catzilla_upload_file_t* file) {
    if (!file) {
        return;
    }

    free(file->field_name);
    free(file->filename);
    free(file->content_type);
    free(file->content);
    free(file->error_message);
    free(file->temp_file_path);
    free(file->streaming_buffer);

    // Cleanup allowed types
    for (size_t i = 0; i < file->allowed_types_count && i < 10; i++) {
        free(file->allowed_types[i]);
    }

    free(file);
    LOG_PARSER_DEBUG("Upload file cleanup completed");
}

// Public cleanup function
void catzilla_upload_file_cleanup(catzilla_upload_file_t* file) {
    catzilla_upload_file_unref(file);
}

// Get time in nanoseconds
uint64_t catzilla_get_time_ns(void) {
    if (g_start_time_ns == 0) {
        // Initialize on first call
        struct timeval tv;
        gettimeofday(&tv, NULL);
        g_start_time_ns = tv.tv_sec * 1000000000ULL + tv.tv_usec * 1000ULL;
    }

    struct timeval tv;
    gettimeofday(&tv, NULL);
    return tv.tv_sec * 1000000000ULL + tv.tv_usec * 1000ULL;
}

// Atomic operations
void catzilla_atomic_increment(catzilla_upload_atomic_uint64_t* counter) {
    if (counter) {
#ifdef _WIN32
        InterlockedIncrement64((volatile LONG64*)&counter->value);
#else
        __sync_fetch_and_add(&counter->value, 1);
#endif
    }
}

uint64_t catzilla_atomic_get(catzilla_upload_atomic_uint64_t* counter) {
    return counter ? counter->value : 0;
}

// Validation functions
int catzilla_upload_validate_chunk(catzilla_upload_file_t* file, const char* chunk_data, size_t chunk_size) {
    if (!file) {
        return CATZILLA_UPLOAD_ERROR_MEMORY;
    }

    // Check file size limit before processing chunk
    if (file->bytes_received + chunk_size > file->max_size) {
        LOG_PARSER_ERROR("File size limit exceeded: %" PRIu64 " + %zu > %" PRIu64,
                 file->bytes_received, chunk_size, file->max_size);
        return CATZILLA_UPLOAD_ERROR_FILE_TOO_LARGE;
    }

    // Additional validation will be added in Phase 4
    return CATZILLA_UPLOAD_SUCCESS;
}

// Error handling
void catzilla_upload_set_error(catzilla_upload_file_t* file, catzilla_upload_error_t error, const char* message) {
    if (!file) {
        return;
    }

    file->error_code = error;
    file->state = UPLOAD_STATE_ERROR;

    if (message) {
        free(file->error_message);
        file->error_message = strdup(message);
    }

    LOG_PARSER_ERROR("Upload error for file %s: %s (code: %d)",
              file->filename ? file->filename : "unknown",
              message ? message : "unknown error", error);
}

void catzilla_upload_abort(catzilla_upload_file_t* file) {
    if (!file) {
        return;
    }

    file->state = UPLOAD_STATE_ABORTED;
    LOG_MEMORY_WARN("Upload aborted for file: %s", file->filename ? file->filename : "unknown");
}

const char* catzilla_upload_error_string(catzilla_upload_error_t error) {
    switch (error) {
        case CATZILLA_UPLOAD_SUCCESS: return "Success";
        case CATZILLA_UPLOAD_ERROR_FILE_TOO_LARGE: return "File too large";
        case CATZILLA_UPLOAD_ERROR_INVALID_MIME: return "Invalid MIME type";
        case CATZILLA_UPLOAD_ERROR_SIGNATURE_MISMATCH: return "File signature mismatch";
        case CATZILLA_UPLOAD_ERROR_VIRUS_DETECTED: return "Virus detected";
        case CATZILLA_UPLOAD_ERROR_DISK_FULL: return "Disk full";
        case CATZILLA_UPLOAD_ERROR_TIMEOUT: return "Upload timeout";
        case CATZILLA_UPLOAD_ERROR_CORRUPTED: return "File corrupted";
        case CATZILLA_UPLOAD_ERROR_PATH_TRAVERSAL: return "Path traversal attempt";
        case CATZILLA_UPLOAD_ERROR_MEMORY: return "Memory error";
        case CATZILLA_UPLOAD_ERROR_NETWORK: return "Network error";
        default: return "Unknown error";
    }
}

// Performance monitoring
double catzilla_upload_get_speed_mbps(catzilla_upload_file_t* file) {
    return file ? file->upload_speed_mbps : 0.0;
}

uint64_t catzilla_upload_get_bytes_processed(catzilla_upload_file_t* file) {
    return file ? file->bytes_received : 0;
}

// Utility functions
char* catzilla_extract_boundary(const char* content_type) {
    if (!content_type) {
        return NULL;
    }

    char* boundary_start = strcasestr(content_type, "boundary=");
    if (!boundary_start) {
        return NULL;
    }

    boundary_start += 9; // Skip "boundary="

    // Handle quoted boundary
    if (*boundary_start == '"') {
        boundary_start++;
        char* boundary_end = strchr(boundary_start, '"');
        if (!boundary_end) {
            return NULL;
        }

        size_t boundary_len = boundary_end - boundary_start;
        char* boundary = malloc(boundary_len + 1);
        if (!boundary) {
            return NULL;
        }

        memcpy(boundary, boundary_start, boundary_len);
        boundary[boundary_len] = '\0';
        return boundary;
    } else {
        // Unquoted boundary - find end
        char* boundary_end = boundary_start;
        while (*boundary_end && *boundary_end != ' ' && *boundary_end != ';' &&
               *boundary_end != '\r' && *boundary_end != '\n') {
            boundary_end++;
        }

        size_t boundary_len = boundary_end - boundary_start;
        char* boundary = malloc(boundary_len + 1);
        if (!boundary) {
            return NULL;
        }

        memcpy(boundary, boundary_start, boundary_len);
        boundary[boundary_len] = '\0';
        return boundary;
    }
}

char* catzilla_parse_content_disposition(const char* header, const char* param) {
    if (!header || !param) {
        return NULL;
    }

    char param_search[256];
    snprintf(param_search, sizeof(param_search), "%s=", param);

    char* param_start = strcasestr(header, param_search);
    if (!param_start) {
        return NULL;
    }

    param_start += strlen(param_search);

    // Handle quoted parameter
    if (*param_start == '"') {
        param_start++;
        char* param_end = strchr(param_start, '"');
        if (!param_end) {
            return NULL;
        }

        size_t param_len = param_end - param_start;
        char* param_value = malloc(param_len + 1);
        if (!param_value) {
            return NULL;
        }

        memcpy(param_value, param_start, param_len);
        param_value[param_len] = '\0';
        return param_value;
    } else {
        // Unquoted parameter
        char* param_end = param_start;
        while (*param_end && *param_end != ' ' && *param_end != ';' &&
               *param_end != '\r' && *param_end != '\n') {
            param_end++;
        }

        size_t param_len = param_end - param_start;
        char* param_value = malloc(param_len + 1);
        if (!param_value) {
            return NULL;
        }

        memcpy(param_value, param_start, param_len);
        param_value[param_len] = '\0';
        return param_value;
    }
}
