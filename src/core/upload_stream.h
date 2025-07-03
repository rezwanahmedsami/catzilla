#ifndef CATZILLA_UPLOAD_STREAM_H
#define CATZILLA_UPLOAD_STREAM_H

#include <stdint.h>
#include <stdbool.h>
#include <stddef.h>
#include <uv.h>
#include "upload_parser.h"

#ifdef __cplusplus
extern "C" {
#endif

// Forward declarations
typedef struct catzilla_stream_context_s catzilla_stream_context_t;
typedef struct upload_stream_buffer_s upload_stream_buffer_t;

// Stream operation types
typedef enum {
    STREAM_OP_WRITE_DISK = 0,
    STREAM_OP_WRITE_MEMORY = 1,
    STREAM_OP_PROCESS_CHUNKS = 2,
    STREAM_OP_VALIDATE = 3
} stream_operation_t;

// Stream buffer for zero-copy operations
typedef struct upload_stream_buffer_s {
    char* data;
    size_t size;
    size_t capacity;
    size_t position;
    bool is_static;         // True if buffer should not be freed
    upload_stream_buffer_t* next;
} upload_stream_buffer_t;

// Stream write context
typedef struct catzilla_stream_context_s {
    // File operations
    uv_fs_t file_req;
    uv_file file_handle;
    char* file_path;
    bool file_opened;

    // Stream buffers
    upload_stream_buffer_t* buffers;
    upload_stream_buffer_t* current_buffer;
    size_t buffer_count;
    size_t total_buffered;

    // Configuration
    size_t buffer_size;
    size_t max_buffers;
    bool direct_io;         // Use O_DIRECT for large files
    bool sync_writes;       // Use O_SYNC for immediate writes

    // Performance tracking
    uint64_t bytes_written;
    uint64_t write_operations;
    uint64_t start_time;
    double avg_write_speed_mbps;

    // Callbacks
    void (*on_write_complete)(catzilla_stream_context_t* ctx, size_t bytes_written);
    void (*on_write_error)(catzilla_stream_context_t* ctx, int error_code);
    void (*on_buffer_full)(catzilla_stream_context_t* ctx);

    // Reference to upload file
    catzilla_upload_file_t* upload_file;
} catzilla_stream_context_t;

// Stream initialization and cleanup
catzilla_stream_context_t* catzilla_stream_context_create(catzilla_upload_file_t* file);
void catzilla_stream_context_cleanup(catzilla_stream_context_t* ctx);

// Zero-copy streaming functions
int catzilla_upload_stream_to_disk(catzilla_upload_file_t* file, const char* path);
int catzilla_upload_stream_to_memory(catzilla_upload_file_t* file);
int catzilla_upload_stream_chunk(catzilla_stream_context_t* ctx, const char* data, size_t len);

// File operations
int catzilla_stream_open_file(catzilla_stream_context_t* ctx, const char* path);
int catzilla_stream_write_buffer(catzilla_stream_context_t* ctx, upload_stream_buffer_t* buffer);
int catzilla_stream_flush_buffers(catzilla_stream_context_t* ctx);
void catzilla_stream_close_file(catzilla_stream_context_t* ctx);

// Buffer management
upload_stream_buffer_t* catzilla_stream_buffer_create(size_t size);
void catzilla_stream_buffer_cleanup(upload_stream_buffer_t* buffer);
int catzilla_stream_buffer_append(upload_stream_buffer_t* buffer, const char* data, size_t len);
int catzilla_stream_buffer_write_to_file(upload_stream_buffer_t* buffer, uv_file file);

// Performance optimization
void catzilla_stream_optimize_for_size(catzilla_stream_context_t* ctx, uint64_t expected_size);
void catzilla_stream_enable_direct_io(catzilla_stream_context_t* ctx, bool enable);
void catzilla_stream_set_buffer_size(catzilla_stream_context_t* ctx, size_t buffer_size);

// Performance monitoring
double catzilla_stream_get_write_speed_mbps(catzilla_stream_context_t* ctx);
uint64_t catzilla_stream_get_bytes_written(catzilla_stream_context_t* ctx);
double catzilla_stream_get_efficiency_ratio(catzilla_stream_context_t* ctx);

// Async write operations
typedef struct {
    uv_work_t work_req;
    catzilla_stream_context_t* stream_ctx;
    upload_stream_buffer_t* buffer;
    int result;
} stream_write_work_t;

void catzilla_stream_async_write(catzilla_stream_context_t* ctx, upload_stream_buffer_t* buffer);
void stream_write_worker(uv_work_t* req);
void stream_write_after_work(uv_work_t* req, int status);

// Utility functions
size_t catzilla_upload_optimal_buffer_size(uint64_t file_size);
bool catzilla_stream_should_use_direct_io(uint64_t file_size);
int catzilla_stream_create_temp_file(char* template_path, size_t template_size);

#ifdef __cplusplus
}
#endif

#endif // CATZILLA_UPLOAD_STREAM_H
