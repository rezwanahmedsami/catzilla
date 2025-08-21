#ifndef CATZILLA_STATIC_SERVER_H
#define CATZILLA_STATIC_SERVER_H

#include <stdbool.h>
#include <stdint.h>
#include <time.h>
#include <sys/stat.h>
#include <uv.h>
#include "server.h"
#include "memory.h"
#include "platform_atomic.h"

#ifdef __cplusplus
extern "C" {
#endif

// Forward declarations
typedef struct catzilla_static_server catzilla_static_server_t;
typedef struct static_server_config static_server_config_t;
typedef struct catzilla_server_mount catzilla_server_mount_t;
typedef struct static_file_context static_file_context_t;
typedef struct catzilla_static_response catzilla_static_response_t;
typedef struct hot_cache hot_cache_t;
typedef struct hot_cache_entry hot_cache_entry_t;

// Configuration and limits
#define STATIC_CACHE_HASH_BUCKETS 1024
#define STATIC_CACHE_DEFAULT_TTL 3600
#define STATIC_CACHE_MAX_FILE_SIZE (10 * 1024 * 1024)  // 10MB max per file
#define STATIC_MAX_MIME_TYPE_LEN 128
#define STATIC_MAX_ETAG_LEN 64
#define STATIC_MAX_HEADER_LEN 256

// Static server configuration
typedef struct static_server_config {
    char* mount_path;                    // e.g., "/static"
    char* directory;                     // e.g., "./static"
    char* index_file;                    // Default: "index.html"

    // libuv-specific settings
    uv_loop_t* loop;                     // Shared event loop with main server
    int fs_thread_pool_size;             // Thread pool size for file operations
    bool use_sendfile;                   // Enable zero-copy sendfile

    // Performance settings
    bool enable_hot_cache;               // Cache frequently accessed files
    size_t cache_size_mb;               // Hot cache size (default: 100MB)
    int cache_ttl_seconds;              // Cache TTL (default: 3600)

    // Compression settings
    bool enable_compression;            // Gzip compression
    int compression_level;              // 1-9 (default: 6)
    size_t compression_min_size;        // Min size to compress (default: 1024)

    // Security settings
    bool enable_path_validation;        // Path traversal protection
    bool enable_hidden_files;           // Serve .hidden files (default: false)
    char** allowed_extensions;          // Whitelist extensions
    char** blocked_extensions;          // Blacklist extensions
    size_t max_file_size;              // Max file size (default: 100MB)

    // HTTP features
    bool enable_etags;                  // ETag generation
    bool enable_last_modified;          // Last-Modified headers
    bool enable_range_requests;         // HTTP Range support
    bool enable_directory_listing;      // Auto-index (default: false)
} static_server_config_t;

// HTTP headers structure
typedef struct static_http_headers {
    char content_type[STATIC_MAX_MIME_TYPE_LEN];       // MIME type
    char content_length[32];      // File size
    char last_modified[64];       // RFC 2822 format
    char etag[STATIC_MAX_ETAG_LEN];               // ETag for caching
    char cache_control[128];     // Cache directives
    char accept_ranges[16];      // "bytes" for range support
    char content_range[64];      // For range requests

    // Security headers
    char x_content_type_options[16];  // "nosniff"
    char x_frame_options[16];         // "DENY"
    char x_xss_protection[32];        // "1; mode=block"
} static_http_headers_t;

// HTTP status codes
typedef enum {
    STATIC_HTTP_200_OK = 200,
    STATIC_HTTP_206_PARTIAL_CONTENT = 206,
    STATIC_HTTP_304_NOT_MODIFIED = 304,
    STATIC_HTTP_400_BAD_REQUEST = 400,
    STATIC_HTTP_403_FORBIDDEN = 403,
    STATIC_HTTP_404_NOT_FOUND = 404,
    STATIC_HTTP_413_PAYLOAD_TOO_LARGE = 413,
    STATIC_HTTP_416_RANGE_NOT_SATISFIABLE = 416,
    STATIC_HTTP_500_INTERNAL_SERVER_ERROR = 500
} static_http_status_t;

// Error types
typedef enum {
    STATIC_ERROR_NONE = 0,
    STATIC_ERROR_FILE_NOT_FOUND,
    STATIC_ERROR_PERMISSION_DENIED,
    STATIC_ERROR_FILE_TOO_LARGE,
    STATIC_ERROR_INVALID_PATH,
    STATIC_ERROR_IO_ERROR,
    STATIC_ERROR_MEMORY_ERROR,
    STATIC_ERROR_INVALID_RANGE,
    STATIC_ERROR_UNSUPPORTED_METHOD
} static_error_t;

// Security configuration
typedef struct static_security_config {
    char** allowed_extensions;    // [".js", ".css", ".png", NULL]
    char** blocked_extensions;    // [".exe", ".php", ".py", NULL]
    size_t max_file_size;        // Maximum file size in bytes
    bool allow_symlinks;         // Symlink following policy
    bool enable_directory_listing; // Directory browsing
    bool enable_hidden_files;    // Serve .hidden files
    char** blocked_patterns;     // Blocked filename patterns
} static_security_config_t;

// Cache entry structure
typedef struct hot_cache_entry {
    char* file_path;              // Key (relative path)
    void* file_content;           // File data
    size_t content_size;          // File size in bytes
    time_t last_accessed;         // For LRU eviction
    time_t expires_at;            // TTL expiration
    time_t file_mtime;            // File modification time
    uint64_t etag_hash;           // For HTTP ETag generation
    uint32_t access_count;        // Access frequency tracking
    bool is_compressed;           // Has compressed version
    void* compressed_content;     // Gzipped content
    size_t compressed_size;       // Compressed size
    struct hot_cache_entry* next; // Hash collision chain
    struct hot_cache_entry* lru_prev; // LRU doubly-linked list
    struct hot_cache_entry* lru_next;
} hot_cache_entry_t;

// Hot cache structure
typedef struct hot_cache {
    hot_cache_entry_t* buckets[STATIC_CACHE_HASH_BUCKETS];
    hot_cache_entry_t* lru_head;  // Most recently used
    hot_cache_entry_t* lru_tail;  // Least recently used
    size_t max_memory_bytes;      // Memory limit
    size_t current_memory_usage;  // Current usage
    uint32_t total_entries;       // Entry count
    uv_rwlock_t cache_lock;       // Thread safety
    uv_timer_t cleanup_timer;     // TTL cleanup timer

    // Statistics
    catzilla_atomic_uint64_t cache_hits;
    catzilla_atomic_uint64_t cache_misses;
    catzilla_atomic_uint64_t evictions;
} hot_cache_t;

// File context for serving
typedef struct static_file_context {
    catzilla_request_t* request;
    uv_stream_t* client;
    catzilla_server_mount_t* mount;
    char relative_path[CATZILLA_PATH_MAX];
    char full_file_path[CATZILLA_PATH_MAX];
    uv_fs_t fs_req;                       // libuv file operation (stat, open, fstat)
    uv_fs_t read_req;                     // libuv file read operation
    int file_descriptor;                  // File descriptor from open operation
    void* file_buffer;                    // Buffer for file content
    size_t file_size;                     // Size of file to read
    hot_cache_entry_t* cache_entry;       // Cache entry if exists
    static_http_headers_t http_headers;    // HTTP response headers
    bool is_head_request;                 // HEAD vs GET request
    size_t range_start;                   // Range request start
    size_t range_end;                     // Range request end
    bool is_range_request;                // Range request flag
    uint64_t start_time;                  // Request start time
} static_file_context_t;

// Server mount structure
typedef struct catzilla_server_mount {
    char mount_path[CATZILLA_PATH_MAX];           // Mount point (e.g., "/static")
    char directory_path[CATZILLA_PATH_MAX];       // Local directory (e.g., "./static")
    catzilla_static_server_t* static_server;      // Static server instance
    struct catzilla_server_mount* next;           // Linked list of mounts
} catzilla_server_mount_t;

// Static server instance
typedef struct catzilla_static_server {
    static_server_config_t config;

    // libuv integration
    uv_loop_t* loop;                    // Shared event loop
    uv_timer_t cache_cleanup_timer;     // Periodic cache cleanup

    // Hot file cache
    hot_cache_t* cache;                 // LRU cache with hash table

    // Security context
    static_security_config_t* security; // Security configuration

    // Performance statistics
    catzilla_atomic_uint64_t requests_served;
    catzilla_atomic_uint64_t bytes_served;
    catzilla_atomic_uint64_t cache_hits;
    catzilla_atomic_uint64_t cache_misses;
    catzilla_atomic_uint64_t sendfile_operations;
} catzilla_static_server_t;

// Core API functions
int catzilla_static_server_init(catzilla_static_server_t* server,
                                static_server_config_t* config);

int catzilla_static_server_serve_async(catzilla_static_server_t* server,
                                       const char* request_path,
                                       uv_stream_t* client,
                                       catzilla_request_t* request);

void catzilla_static_server_cleanup(catzilla_static_server_t* server);

// Mount management
int catzilla_server_mount_static(catzilla_server_t* server,
                                 const char* mount_path,
                                 const char* directory,
                                 static_server_config_t* config);

bool catzilla_is_static_request(catzilla_server_t* server,
                                const char* request_path,
                                catzilla_server_mount_t** mount_out,
                                char* relative_path_out);

// File serving functions
int catzilla_static_serve_file_async(catzilla_server_t* server,
                                     catzilla_request_t* request,
                                     catzilla_server_mount_t* mount,
                                     const char* relative_path);

int catzilla_static_serve_file_with_client(catzilla_server_t* server,
                                          catzilla_request_t* request,
                                          catzilla_server_mount_t* mount,
                                          const char* relative_path,
                                          uv_stream_t* client);

// Function declaration for compatibility
int catzilla_static_serve_file(uv_stream_t* client,
                               catzilla_server_mount_t* mount,
                               const char* relative_path);

int catzilla_static_serve_file_async_with_client(uv_stream_t* client,
                                                 catzilla_request_t* request,
                                                 catzilla_server_mount_t* mount,
                                                 const char* relative_path);

// Response functions
int catzilla_static_send_file_response(uv_stream_t* client,
                                       void* file_data,
                                       size_t file_size,
                                       const char* mime_type,
                                       static_http_headers_t* headers);

int catzilla_static_send_error_response(uv_stream_t* client,
                                        int status_code,
                                        const char* message);

// Cache management
int catzilla_static_cache_init(hot_cache_t* cache, size_t max_memory);
hot_cache_entry_t* catzilla_static_cache_get(hot_cache_t* cache, const char* file_path);
int catzilla_static_cache_put(hot_cache_t* cache, const char* file_path,
                              void* content, size_t size, time_t mtime);
void catzilla_static_cache_remove(hot_cache_t* cache, const char* file_path);
void catzilla_static_cache_cleanup(hot_cache_t* cache);

// Security functions
bool catzilla_static_validate_path(const char* requested_path, const char* base_dir);
bool catzilla_static_check_extension(const char* filename, static_security_config_t* config);

// HTTP utility functions
const char* catzilla_static_get_content_type(const char* file_path);
char* catzilla_static_generate_etag(const char* file_path, time_t last_modified, size_t file_size);
int catzilla_static_parse_range_header(const char* range_header, size_t file_size,
                                       size_t* start_out, size_t* end_out);

#ifdef __cplusplus
}
#endif

#endif // CATZILLA_STATIC_SERVER_H
