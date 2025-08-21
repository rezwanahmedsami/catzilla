#ifndef CATZILLA_UPLOAD_PARSER_H
#define CATZILLA_UPLOAD_PARSER_H

#include <stdint.h>
#include <stdbool.h>
#include <stddef.h>
#include <uv.h>

#ifdef __cplusplus
extern "C" {
#endif

// Forward declarations
typedef struct catzilla_upload_file_s catzilla_upload_file_t;
typedef struct multipart_parser_s multipart_parser_t;
typedef struct upload_memory_manager_s upload_memory_manager_t;

// Upload size classifications for memory optimization
typedef enum {
    UPLOAD_SIZE_SMALL = 0,    // < 1MB files
    UPLOAD_SIZE_MEDIUM = 1,   // 1-50MB files
    UPLOAD_SIZE_LARGE = 2,    // > 50MB files (streaming only)
    UPLOAD_SIZE_METADATA = 3  // Headers, filenames, etc.
} upload_size_class_t;

// Streaming thresholds for memory optimization
#define UPLOAD_STREAMING_THRESHOLD_BYTES (50 * 1024 * 1024)  // 50MB - stream to temp files above this
#define UPLOAD_MEMORY_LIMIT_BYTES (1024 * 1024 * 1024)       // 1GB - absolute max file size

// Error codes for file upload validation
typedef enum {
    CATZILLA_UPLOAD_SUCCESS = 0,
    CATZILLA_UPLOAD_ERROR_FILE_TOO_LARGE = -1001,
    CATZILLA_UPLOAD_ERROR_INVALID_MIME = -1002,
    CATZILLA_UPLOAD_ERROR_SIGNATURE_MISMATCH = -1003,
    CATZILLA_UPLOAD_ERROR_VIRUS_DETECTED = -1004,
    CATZILLA_UPLOAD_ERROR_DISK_FULL = -1005,
    CATZILLA_UPLOAD_ERROR_TIMEOUT = -1006,
    CATZILLA_UPLOAD_ERROR_CORRUPTED = -1007,
    CATZILLA_UPLOAD_ERROR_PATH_TRAVERSAL = -1008,
    CATZILLA_UPLOAD_ERROR_MEMORY = -1009,
    CATZILLA_UPLOAD_ERROR_NETWORK = -1010
} catzilla_upload_error_t;

// Upload file state
typedef enum {
    UPLOAD_STATE_INITIALIZING = 0,
    UPLOAD_STATE_RECEIVING = 1,
    UPLOAD_STATE_VALIDATING = 2,
    UPLOAD_STATE_SCANNING = 3,
    UPLOAD_STATE_COMPLETE = 4,
    UPLOAD_STATE_ERROR = 5,
    UPLOAD_STATE_ABORTED = 6
} upload_state_t;

// Atomic counter for thread-safe operations
typedef struct {
    volatile uint64_t value;
} catzilla_upload_atomic_uint64_t;

// Main upload file structure
typedef struct catzilla_upload_file_s {
    // Basic file information
    char* field_name;        // Form field name (e.g., "file", "image")
    char* filename;
    char* content_type;
    char* content;           // File content in memory
    uint64_t size;
    uint64_t max_size;
    upload_state_t state;

    // Zero-copy streaming
    uv_stream_t* stream;
    uv_fs_t file_handle;
    char* temp_file_path;

    // Performance tracking
    uint64_t upload_start_time;
    uint64_t bytes_received;
    double upload_speed_mbps;

    // Memory optimization with jemalloc
    catzilla_upload_atomic_uint64_t chunks_processed;
    size_t buffer_size;
    char* streaming_buffer;
    upload_size_class_t size_class;

    // Security features
    bool signature_validated;
    bool virus_scanned;
    char* allowed_types[10];
    size_t allowed_types_count;
    bool validate_signature;
    bool virus_scan_enabled;

    // Error handling
    catzilla_upload_error_t error_code;
    char* error_message;

    // Reference counting for cleanup
    int ref_count;

    // Callbacks
    void (*on_chunk_received)(catzilla_upload_file_t* file, const char* data, size_t len);
    void (*on_complete)(catzilla_upload_file_t* file);
    void (*on_error)(catzilla_upload_file_t* file, catzilla_upload_error_t error);
} catzilla_upload_file_t;

// Multipart parser state
typedef enum {
    MULTIPART_STATE_INIT = 0,
    MULTIPART_STATE_BOUNDARY = 1,
    MULTIPART_STATE_HEADERS = 2,
    MULTIPART_STATE_DATA = 3,
    MULTIPART_STATE_END = 4,
    MULTIPART_STATE_ERROR = 5
} multipart_state_t;

// Multipart parser structure
typedef struct multipart_parser_s {
    // Parser state
    multipart_state_t state;
    char* boundary;
    size_t boundary_len;

    // Current parsing position
    char* buffer;
    size_t buffer_size;
    size_t buffer_pos;

    // Current file being parsed
    catzilla_upload_file_t* current_file;

    // All files in this multipart request
    catzilla_upload_file_t** files;
    size_t files_count;
    size_t files_capacity;

    // Parser configuration
    uint64_t max_total_size;
    size_t max_files;

    // Memory management
    upload_memory_manager_t* memory_manager;

    // Callbacks
    void (*on_file_start)(multipart_parser_t* parser, catzilla_upload_file_t* file);
    void (*on_file_data)(multipart_parser_t* parser, catzilla_upload_file_t* file, const char* data, size_t len);
    void (*on_file_end)(multipart_parser_t* parser, catzilla_upload_file_t* file);
    void (*on_parse_complete)(multipart_parser_t* parser);
    void (*on_parse_error)(multipart_parser_t* parser, catzilla_upload_error_t error);
} multipart_parser_t;

// Core parsing functions
int catzilla_multipart_parse_init(multipart_parser_t* parser, const char* content_type);
int catzilla_multipart_parse_chunk(multipart_parser_t* parser, const char* data, size_t len);
int catzilla_multipart_parse_complete(multipart_parser_t* parser);
void catzilla_multipart_parser_cleanup(multipart_parser_t* parser);

// File handling functions
catzilla_upload_file_t* catzilla_upload_file_create(const char* field_name, const char* filename, const char* content_type);
int catzilla_upload_file_write_chunk(catzilla_upload_file_t* file, const char* data, size_t len);
int catzilla_upload_file_finalize(catzilla_upload_file_t* file);
void catzilla_upload_file_cleanup(catzilla_upload_file_t* file);

// Reference counting
void catzilla_upload_file_ref(catzilla_upload_file_t* file);
void catzilla_upload_file_unref(catzilla_upload_file_t* file);

// Validation functions
int catzilla_upload_validate_chunk(catzilla_upload_file_t* file, const char* chunk_data, size_t chunk_size);
bool catzilla_upload_validate_filename(const char* filename);
bool catzilla_upload_validate_content_type(const char* content_type, char* allowed_types[], size_t count);

// Error handling
void catzilla_upload_set_error(catzilla_upload_file_t* file, catzilla_upload_error_t error, const char* message);
void catzilla_upload_abort(catzilla_upload_file_t* file);
const char* catzilla_upload_error_string(catzilla_upload_error_t error);

// Performance monitoring
double catzilla_upload_get_speed_mbps(catzilla_upload_file_t* file);
uint64_t catzilla_upload_get_bytes_processed(catzilla_upload_file_t* file);
uint64_t catzilla_get_time_ns(void);

// Atomic operations
void catzilla_atomic_increment(catzilla_upload_atomic_uint64_t* counter);
uint64_t catzilla_atomic_get(catzilla_upload_atomic_uint64_t* counter);

// Utility functions
char* catzilla_extract_boundary(const char* content_type);
char* catzilla_parse_content_disposition(const char* header, const char* param);
size_t catzilla_parse_size_string(const char* size_str);

#ifdef __cplusplus
}
#endif

#endif // CATZILLA_UPLOAD_PARSER_H
