#include "upload_stream.h"
#include "upload_memory.h"
#include "logging.h"
#include "platform_compat.h"
#include <string.h>
#include <stdlib.h>
#include <stdio.h>
#include <errno.h>
#include <time.h>

// Platform-specific includes
#ifdef _WIN32
#include <windows.h>
#include <io.h>
#include <fcntl.h>
#include <sys/stat.h>
// Windows equivalents for Unix functions
#define access _access
#define close _close
#define read _read
#define write _write
#define lseek _lseek
#define fileno _fileno
#define open _open
// Windows file mode constants and types
typedef int mode_t;
typedef SSIZE_T ssize_t;
#ifndef S_IRUSR
#define S_IRUSR _S_IREAD
#define S_IWUSR _S_IWRITE
#define S_IRGRP _S_IREAD
#define S_IROTH _S_IREAD
#endif
#else
#include <unistd.h>
#include <fcntl.h>
#include <sys/stat.h>
#endif

// Platform-specific file operations
#ifdef __linux__
#include <sys/sendfile.h>
#include <linux/fs.h>
#endif

#ifdef __APPLE__
#include <copyfile.h>
#include <sys/fcntl.h>
#endif

#ifdef _WIN32
#include <windows.h>
#include <io.h>
#endif

// Static function declarations
static void optimize_stream_for_file_size(catzilla_stream_context_t* ctx, uint64_t file_size);
static int create_optimized_file_handle(const char* path, uint64_t expected_size, bool direct_io);
static int catzilla_stream_write_data_to_file(catzilla_stream_context_t* ctx, const char* data, size_t len);
static int catzilla_stream_write_data_to_memory(catzilla_stream_context_t* ctx, const char* data, size_t len);
static void update_stream_performance_metrics(catzilla_stream_context_t* ctx, size_t bytes_written);

// Create stream context
catzilla_stream_context_t* catzilla_stream_context_create(catzilla_upload_file_t* file) {
    if (!file) {
        LOG_STREAM_ERROR("Cannot create stream context without upload file");
        return NULL;
    }

    catzilla_stream_context_t* ctx = malloc(sizeof(catzilla_stream_context_t));
    if (!ctx) {
        LOG_STREAM_ERROR("Failed to allocate stream context");
        return NULL;
    }

    memset(ctx, 0, sizeof(catzilla_stream_context_t));

    // Initialize default configuration
    ctx->buffer_size = catzilla_upload_optimal_buffer_size(file->max_size);
    ctx->max_buffers = 4; // Allow up to 4 buffers for async operations
    ctx->direct_io = catzilla_stream_should_use_direct_io(file->max_size);
    ctx->sync_writes = false; // Async by default for better performance

    // Reference the upload file
    ctx->upload_file = file;
    catzilla_upload_file_ref(file);

    // Initialize performance tracking
    ctx->start_time = catzilla_get_time_ns();

    LOG_STREAM_DEBUG("Created stream context for file: %s (buffer_size: %zu, direct_io: %s)",
              file->filename ? file->filename : "unknown",
              ctx->buffer_size,
              ctx->direct_io ? "enabled" : "disabled");

    return ctx;
}

// Cleanup stream context
void catzilla_stream_context_cleanup(catzilla_stream_context_t* ctx) {
    if (!ctx) {
        return;
    }

    // Close file if open
    if (ctx->file_opened) {
        catzilla_stream_close_file(ctx);
    }

    // Cleanup buffers
    upload_stream_buffer_t* buffer = ctx->buffers;
    while (buffer) {
        upload_stream_buffer_t* next = buffer->next;
        catzilla_stream_buffer_cleanup(buffer);
        buffer = next;
    }

    // Cleanup file path
    free(ctx->file_path);

    // Release upload file reference
    if (ctx->upload_file) {
        catzilla_upload_file_unref(ctx->upload_file);
    }

    LOG_STREAM_DEBUG("Stream context cleanup completed (bytes_written: %" PRIu64 ", operations: %" PRIu64 ", avg_speed: %.2f MB/s)",
              ctx->bytes_written, ctx->write_operations, ctx->avg_write_speed_mbps);

    free(ctx);
}

// Stream to disk with zero-copy optimization
int catzilla_upload_stream_to_disk(catzilla_upload_file_t* file, const char* path) {
    if (!file || !path) {
        LOG_STREAM_ERROR("Invalid parameters for stream to disk");
        return -1;
    }

    // Create stream context
    catzilla_stream_context_t* ctx = catzilla_stream_context_create(file);
    if (!ctx) {
        return -1;
    }

    // Open target file
    int result = catzilla_stream_open_file(ctx, path);
    if (result != 0) {
        LOG_STREAM_ERROR("Failed to open target file for streaming: %s", path);
        catzilla_stream_context_cleanup(ctx);
        return -1;
    }

    // Store context in upload file for chunk processing
    file->temp_file_path = strdup(path);

    LOG_STREAM_INFO("Initialized streaming to disk: %s", path);
    return 0;
}

// Stream to memory
int catzilla_upload_stream_to_memory(catzilla_upload_file_t* file) {
    if (!file) {
        LOG_STREAM_ERROR("Invalid parameters for stream to memory");
        return -1;
    }

    // Create stream context for memory operations
    catzilla_stream_context_t* ctx = catzilla_stream_context_create(file);
    if (!ctx) {
        return -1;
    }

    // Allocate initial buffer based on expected size
    size_t initial_size = (file->max_size > 0 && file->max_size < 10 * 1024 * 1024) ?
                         file->max_size : 1024 * 1024; // 1MB default

    upload_stream_buffer_t* buffer = catzilla_stream_buffer_create(initial_size);
    if (!buffer) {
        LOG_STREAM_ERROR("Failed to create initial memory buffer");
        catzilla_stream_context_cleanup(ctx);
        return -1;
    }

    ctx->buffers = buffer;
    ctx->current_buffer = buffer;
    ctx->buffer_count = 1;

    LOG_STREAM_INFO("Initialized streaming to memory (initial_size: %zu bytes)", initial_size);
    return 0;
}

// Process chunk for streaming
int catzilla_upload_stream_chunk(catzilla_stream_context_t* ctx, const char* data, size_t len) {
    if (!ctx || !data || len == 0) {
        return -1;
    }

    // Update performance metrics
    update_stream_performance_metrics(ctx, len);

    if (ctx->file_opened) {
        // Streaming to disk
        return catzilla_stream_write_data_to_file(ctx, data, len);
    } else {
        // Streaming to memory
        return catzilla_stream_write_data_to_memory(ctx, data, len);
    }
}

// Open file for streaming
int catzilla_stream_open_file(catzilla_stream_context_t* ctx, const char* path) {
    if (!ctx || !path) {
        return -1;
    }

    // Store file path
    ctx->file_path = strdup(path);
    if (!ctx->file_path) {
        LOG_STREAM_ERROR("Failed to allocate memory for file path");
        return -1;
    }

    // Optimize stream settings based on expected file size
    if (ctx->upload_file && ctx->upload_file->max_size > 0) {
        optimize_stream_for_file_size(ctx, ctx->upload_file->max_size);
    }

    // Create file handle with optimization flags
    int fd = create_optimized_file_handle(path, ctx->upload_file ? ctx->upload_file->max_size : 0, ctx->direct_io);
    if (fd < 0) {
        LOG_STREAM_ERROR("Failed to create optimized file handle: %s", strerror(errno));
        return -1;
    }

    // Initialize libuv file handle
    ctx->file_handle = fd;
    ctx->file_opened = true;

    LOG_STREAM_DEBUG("Opened file for streaming: %s (fd: %d, direct_io: %s)",
              path, fd, ctx->direct_io ? "enabled" : "disabled");

    return 0;
}

// Write data to file
static int catzilla_stream_write_data_to_file(catzilla_stream_context_t* ctx, const char* data, size_t len) {
    if (!ctx->file_opened) {
        LOG_STREAM_ERROR("File not opened for writing");
        return -1;
    }

    // For large writes, use direct write
    if (len >= ctx->buffer_size) {
        ssize_t written = write(ctx->file_handle, data, len);
        if (written < 0) {
            LOG_STREAM_ERROR("Direct write failed: %s", strerror(errno));
            return -1;
        }

        if ((size_t)written != len) {
            LOG_STREAM_WARN("Partial write: %zd/%zu bytes", written, len);
            // TODO: Handle partial writes
        }

        ctx->bytes_written += written;
        ctx->write_operations++;
        return 0;
    }

    // For small writes, use buffering
    if (!ctx->current_buffer) {
        ctx->current_buffer = catzilla_stream_buffer_create(ctx->buffer_size);
        if (!ctx->current_buffer) {
            LOG_STREAM_ERROR("Failed to create stream buffer");
            return -1;
        }

        ctx->buffers = ctx->current_buffer;
        ctx->buffer_count = 1;
    }

    // Try to append to current buffer
    if (catzilla_stream_buffer_append(ctx->current_buffer, data, len) == 0) {
        ctx->total_buffered += len;

        // Flush buffer if it's getting full
        if (ctx->current_buffer->position >= ctx->current_buffer->capacity * 0.8) {
            return catzilla_stream_flush_buffers(ctx);
        }

        return 0;
    }

    // Buffer is full, flush and create new one
    int flush_result = catzilla_stream_flush_buffers(ctx);
    if (flush_result != 0) {
        return flush_result;
    }

    // Try again with new buffer
    return catzilla_stream_buffer_append(ctx->current_buffer, data, len);
}

// Write data to memory
static int catzilla_stream_write_data_to_memory(catzilla_stream_context_t* ctx, const char* data, size_t len) {
    if (!ctx->current_buffer) {
        LOG_STREAM_ERROR("No memory buffer available");
        return -1;
    }

    // Try to append to current buffer
    if (catzilla_stream_buffer_append(ctx->current_buffer, data, len) == 0) {
        ctx->total_buffered += len;
        return 0;
    }

    // Buffer is full, create a new one
    upload_stream_buffer_t* new_buffer = catzilla_stream_buffer_create(ctx->buffer_size);
    if (!new_buffer) {
        LOG_STREAM_ERROR("Failed to create new memory buffer");
        return -1;
    }

    // Link new buffer
    ctx->current_buffer->next = new_buffer;
    ctx->current_buffer = new_buffer;
    ctx->buffer_count++;

    // Try to append to new buffer
    if (catzilla_stream_buffer_append(new_buffer, data, len) == 0) {
        ctx->total_buffered += len;
        return 0;
    }

    LOG_STREAM_ERROR("Failed to append data to new buffer");
    return -1;
}

// Flush buffers to disk
int catzilla_stream_flush_buffers(catzilla_stream_context_t* ctx) {
    if (!ctx || !ctx->file_opened) {
        return -1;
    }

    upload_stream_buffer_t* buffer = ctx->buffers;
    while (buffer) {
        if (buffer->position > 0) {
            int result = catzilla_stream_buffer_write_to_file(buffer, ctx->file_handle);
            if (result != 0) {
                LOG_STREAM_ERROR("Failed to write buffer to file");
                return -1;
            }

            ctx->bytes_written += buffer->position;
            ctx->write_operations++;
            buffer->position = 0; // Reset buffer for reuse
        }
        buffer = buffer->next;
    }

    ctx->total_buffered = 0;

    // Sync to disk if required
    if (ctx->sync_writes) {
        if (fsync(ctx->file_handle) != 0) {
            LOG_STREAM_WARN("File sync failed: %s", strerror(errno));
        }
    }

    return 0;
}

// Close file
void catzilla_stream_close_file(catzilla_stream_context_t* ctx) {
    if (!ctx || !ctx->file_opened) {
        return;
    }

    // Flush any remaining buffers
    if (ctx->total_buffered > 0) {
        catzilla_stream_flush_buffers(ctx);
    }

    // Close file handle
    if (ctx->file_handle >= 0) {
        close(ctx->file_handle);
        ctx->file_handle = -1;
    }

    ctx->file_opened = false;

    LOG_STREAM_DEBUG("Closed stream file: %s (total_written: %" PRIu64 " bytes)",
              ctx->file_path ? ctx->file_path : "unknown", ctx->bytes_written);
}

// Create stream buffer
upload_stream_buffer_t* catzilla_stream_buffer_create(size_t size) {
    upload_stream_buffer_t* buffer = malloc(sizeof(upload_stream_buffer_t));
    if (!buffer) {
        LOG_STREAM_ERROR("Failed to allocate stream buffer structure");
        return NULL;
    }

    memset(buffer, 0, sizeof(upload_stream_buffer_t));

    // Allocate data buffer
    buffer->data = malloc(size);
    if (!buffer->data) {
        LOG_STREAM_ERROR("Failed to allocate stream buffer data (%zu bytes)", size);
        free(buffer);
        return NULL;
    }

    buffer->capacity = size;
    buffer->position = 0;
    buffer->is_static = false;

    LOG_STREAM_DEBUG("Created stream buffer: %zu bytes", size);
    return buffer;
}

// Cleanup stream buffer
void catzilla_stream_buffer_cleanup(upload_stream_buffer_t* buffer) {
    if (!buffer) {
        return;
    }

    if (!buffer->is_static && buffer->data) {
        free(buffer->data);
    }

    free(buffer);
}

// Append data to buffer
int catzilla_stream_buffer_append(upload_stream_buffer_t* buffer, const char* data, size_t len) {
    if (!buffer || !data || len == 0) {
        return -1;
    }

    // Check if buffer has enough space
    if (buffer->position + len > buffer->capacity) {
        LOG_STREAM_DEBUG("Buffer full: %zu + %zu > %zu", buffer->position, len, buffer->capacity);
        return -1;
    }

    // Copy data to buffer
    memcpy(buffer->data + buffer->position, data, len);
    buffer->position += len;

    return 0;
}

// Write buffer to file
int catzilla_stream_buffer_write_to_file(upload_stream_buffer_t* buffer, uv_file file) {
    if (!buffer || buffer->position == 0) {
        return 0;
    }

    ssize_t written = write(file, buffer->data, buffer->position);
    if (written < 0) {
        LOG_STREAM_ERROR("Buffer write to file failed: %s", strerror(errno));
        return -1;
    }

    if ((size_t)written != buffer->position) {
        LOG_STREAM_WARN("Partial buffer write: %zd/%zu bytes", written, buffer->position);
        // TODO: Handle partial writes
    }

    return 0;
}

// Optimize stream settings for file size
static void optimize_stream_for_file_size(catzilla_stream_context_t* ctx, uint64_t file_size) {
    // Adjust buffer size based on file size
    if (file_size < 1024 * 1024) {
        // Small files: 4KB buffer
        ctx->buffer_size = 4096;
        ctx->direct_io = false;
    } else if (file_size < 10 * 1024 * 1024) {
        // Medium files: 64KB buffer
        ctx->buffer_size = 65536;
        ctx->direct_io = false;
    } else if (file_size < 100 * 1024 * 1024) {
        // Large files: 1MB buffer
        ctx->buffer_size = 1024 * 1024;
        ctx->direct_io = true;
    } else {
        // Very large files: 4MB buffer
        ctx->buffer_size = 4 * 1024 * 1024;
        ctx->direct_io = true;
        ctx->sync_writes = false; // Async for very large files
    }

    LOG_STREAM_DEBUG("Optimized stream for file size %" PRIu64 ": buffer_size=%zu, direct_io=%s",
              file_size, ctx->buffer_size, ctx->direct_io ? "enabled" : "disabled");
}

// Create optimized file handle
static int create_optimized_file_handle(const char* path, uint64_t expected_size, bool direct_io) {
    int flags = O_WRONLY | O_CREAT | O_TRUNC;

    // Add optimization flags
    if (direct_io && expected_size > 10 * 1024 * 1024) {
#ifdef O_DIRECT
        flags |= O_DIRECT;
#endif
    }

#ifdef O_LARGEFILE
    if (expected_size > 2ULL * 1024 * 1024 * 1024) {
        flags |= O_LARGEFILE;
    }
#endif

    mode_t mode = S_IRUSR | S_IWUSR | S_IRGRP | S_IROTH; // 644

    int fd = open(path, flags, mode);
    if (fd < 0) {
        LOG_STREAM_ERROR("Failed to open file %s: %s", path, strerror(errno));
        return -1;
    }

    // Pre-allocate space for large files
    if (expected_size > 1024 * 1024) {
#ifdef __linux__
        // Use fallocate on Linux
        if (fallocate(fd, 0, 0, expected_size) == 0) {
            LOG_STREAM_DEBUG("Pre-allocated %" PRIu64 " bytes for file", expected_size);
        }
#elif defined(__APPLE__)
        // Use ftruncate on macOS (simpler approach)
        if (ftruncate(fd, expected_size) == 0) {
            LOG_STREAM_DEBUG("Pre-allocated %" PRIu64 " bytes for file", expected_size);
        }
#endif
    }

    return fd;
}

// Update performance metrics
static void update_stream_performance_metrics(catzilla_stream_context_t* ctx, size_t bytes_written) {
    uint64_t current_time = catzilla_get_time_ns();
    uint64_t elapsed_ns = current_time - ctx->start_time;

    if (elapsed_ns > 0) {
        double elapsed_seconds = elapsed_ns / 1e9;
        double total_mb = (ctx->bytes_written + bytes_written) / (1024.0 * 1024.0);
        ctx->avg_write_speed_mbps = total_mb / elapsed_seconds;
    }
}

// Get optimal buffer size for file uploads
size_t catzilla_upload_optimal_buffer_size(uint64_t file_size) {
    if (file_size < 1024 * 1024) {
        return 4096;        // 4KB for small files
    } else if (file_size < 10 * 1024 * 1024) {
        return 65536;       // 64KB for medium files
    } else if (file_size < 100 * 1024 * 1024) {
        return 1024 * 1024; // 1MB for large files
    } else {
        return 4 * 1024 * 1024; // 4MB for very large files
    }
}

// Check if direct I/O should be used
bool catzilla_stream_should_use_direct_io(uint64_t file_size) {
    return file_size > 10 * 1024 * 1024; // Use direct I/O for files > 10MB
}

// Performance monitoring functions
double catzilla_stream_get_write_speed_mbps(catzilla_stream_context_t* ctx) {
    return ctx ? ctx->avg_write_speed_mbps : 0.0;
}

uint64_t catzilla_stream_get_bytes_written(catzilla_stream_context_t* ctx) {
    return ctx ? ctx->bytes_written : 0;
}

double catzilla_stream_get_efficiency_ratio(catzilla_stream_context_t* ctx) {
    if (!ctx || ctx->write_operations == 0) {
        return 0.0;
    }

    // Calculate efficiency as bytes per operation
    return (double)ctx->bytes_written / (double)ctx->write_operations;
}

// Create temporary file
int catzilla_stream_create_temp_file(char* template_path, size_t template_size) {
    char temp_template[] = "/tmp/catzilla_upload_XXXXXX";

    int fd = mkstemp(temp_template);
    if (fd < 0) {
        LOG_STREAM_ERROR("Failed to create temporary file: %s", strerror(errno));
        return -1;
    }

    if (strlen(temp_template) >= template_size) {
        LOG_STREAM_ERROR("Template buffer too small");
        close(fd);
        unlink(temp_template);
        return -1;
    }

    strcpy(template_path, temp_template);
    LOG_STREAM_DEBUG("Created temporary file: %s (fd: %d)", template_path, fd);

    return fd;
}
