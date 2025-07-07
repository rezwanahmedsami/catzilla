#include "streaming.h"
#include "server.h"
#include <stdlib.h>
#include <string.h>
#include <stdio.h>
#include <assert.h>

#ifndef _WIN32
#include <unistd.h>
#endif

// Global streaming statistics
static catzilla_streaming_stats_t g_streaming_stats = {0};

// Streaming response marker for detection
#define STREAMING_MARKER "___CATZILLA_STREAMING___"
#define STREAMING_MARKER_LEN 24
#define STREAMING_MARKER_LEN 24

// Default buffer sizes
#define DEFAULT_RING_BUFFER_SIZE    (64 * 1024)    // 64KB
#define MAX_RING_BUFFER_SIZE        (1024 * 1024)  // 1MB
#define MAX_PENDING_WRITES          100
#define BACKPRESSURE_THRESHOLD      50

// ================================
// INTERNAL HELPER FUNCTIONS
// ================================

static void on_stream_write_complete(uv_write_t* req, int status);
static void stream_process_ring_buffer(catzilla_stream_context_t* ctx);
static size_t stream_ring_buffer_available_write(catzilla_stream_context_t* ctx);
static size_t stream_ring_buffer_available_read(catzilla_stream_context_t* ctx);
static int stream_ring_buffer_write(catzilla_stream_context_t* ctx,
                                   const char* data, size_t len);
static int stream_ring_buffer_read(catzilla_stream_context_t* ctx,
                                  char* buffer, size_t max_len, size_t* actual_len);

// ================================
// CORE STREAMING IMPLEMENTATION
// ================================

catzilla_stream_context_t* catzilla_stream_create(uv_stream_t* client,
                                                  size_t buffer_size) {
    if (!client) {
        return NULL;
    }

    // Validate buffer size
    if (buffer_size == 0) {
        buffer_size = DEFAULT_RING_BUFFER_SIZE;
    }
    if (buffer_size > MAX_RING_BUFFER_SIZE) {
        buffer_size = MAX_RING_BUFFER_SIZE;
    }

    // Allocate stream context
    catzilla_stream_context_t* ctx = calloc(1, sizeof(catzilla_stream_context_t));
    if (!ctx) {
        return NULL;
    }

    // Allocate ring buffer
    ctx->ring_buffer = malloc(buffer_size);
    if (!ctx->ring_buffer) {
        free(ctx);
        return NULL;
    }

    // Initialize context
    ctx->client_handle = client;
    ctx->loop = client->loop;
    ctx->buffer_size = buffer_size;
    ctx->write_req.data = ctx;  // Link write request to context

    // Initialize atomic variables
    atomic_store(&ctx->read_pos, 0);
    atomic_store(&ctx->write_pos, 0);
    atomic_store(&ctx->is_active, true);
    atomic_store(&ctx->pending_writes, 0);

    // Set defaults
    ctx->max_pending_writes = MAX_PENDING_WRITES;
    ctx->backpressure_active = false;
    ctx->headers_sent = false;
    ctx->status_code = 200;
    ctx->content_type = strdup("text/plain");

    // Record start time
#ifdef _WIN32
    QueryPerformanceCounter(&ctx->start_time);
#else
    clock_gettime(CLOCK_MONOTONIC, &ctx->start_time);
#endif

    // Update global statistics
    atomic_fetch_add(&g_streaming_stats.active_streams, 1);
    atomic_fetch_add(&g_streaming_stats.streams_created, 1);
    atomic_fetch_add(&g_streaming_stats.memory_allocated,
                     sizeof(catzilla_stream_context_t) + buffer_size);

    return ctx;
}

void catzilla_stream_destroy(catzilla_stream_context_t* ctx) {
    if (!ctx) {
        return;
    }

    // Mark as inactive
    atomic_store(&ctx->is_active, false);

    // Clean up resources
    if (ctx->ring_buffer) {
        free(ctx->ring_buffer);
    }
    if (ctx->content_type) {
        free(ctx->content_type);
    }
    if (ctx->error_message) {
        free(ctx->error_message);
    }

    // Update global statistics
    atomic_fetch_sub(&g_streaming_stats.active_streams, 1);
    atomic_fetch_add(&g_streaming_stats.streams_completed, 1);
    atomic_fetch_sub(&g_streaming_stats.memory_allocated,
                     sizeof(catzilla_stream_context_t) + ctx->buffer_size);

    free(ctx);
}

int catzilla_stream_write_chunk(catzilla_stream_context_t* ctx,
                                const char* data, size_t len) {
    if (!ctx || !data || len == 0) {
        return CATZILLA_STREAM_EINVAL;
    }

    if (!atomic_load(&ctx->is_active)) {
        return CATZILLA_STREAM_EABORTED;
    }

    // Check for backpressure
    size_t pending = atomic_load(&ctx->pending_writes);
    if (pending >= ctx->max_pending_writes) {
        ctx->backpressure_active = true;
        atomic_fetch_add(&g_streaming_stats.backpressure_events, 1);

        if (ctx->backpressure_callback) {
            ctx->backpressure_callback(ctx->callback_context, true);
        }

        return CATZILLA_STREAM_EBACKPRESSURE;
    }

    // Try to write to ring buffer
    int result = stream_ring_buffer_write(ctx, data, len);
    if (result != CATZILLA_STREAM_OK) {
        return result;
    }

    // Process the ring buffer (send data via libuv)
    stream_process_ring_buffer(ctx);

    // Update statistics
    ctx->bytes_streamed += len;
    atomic_fetch_add(&g_streaming_stats.total_bytes_streamed, len);

    // Call chunk callback if set
    if (ctx->chunk_callback) {
        ctx->chunk_callback(ctx->callback_context, data, len);
    }

    return CATZILLA_STREAM_OK;
}

int catzilla_stream_write_async(catzilla_stream_context_t* ctx,
                                const char* data, size_t len,
                                stream_callback_t callback) {
    // Set temporary callback
    stream_callback_t old_callback = ctx->chunk_callback;
    ctx->chunk_callback = callback;

    int result = catzilla_stream_write_chunk(ctx, data, len);

    // Restore old callback
    ctx->chunk_callback = old_callback;

    return result;
}

int catzilla_stream_finish(catzilla_stream_context_t* ctx) {
    if (!ctx) {
        return CATZILLA_STREAM_EINVAL;
    }

    if (!atomic_load(&ctx->is_active)) {
        return CATZILLA_STREAM_EFINISHED;
    }

    // Mark as finished
    atomic_store(&ctx->is_active, false);

    // Send any remaining data in ring buffer
    stream_process_ring_buffer(ctx);

    // Send final chunk (empty chunk indicates end)
    const char* final_chunk = "0\r\n\r\n";  // HTTP chunked encoding terminator

    uv_buf_t buf = uv_buf_init((char*)final_chunk, strlen(final_chunk));
    int result = uv_write(&ctx->write_req, ctx->client_handle, &buf, 1,
                         on_stream_write_complete);

    if (result != 0) {
        return CATZILLA_STREAM_ERROR;
    }

    return CATZILLA_STREAM_OK;
}

int catzilla_stream_abort(catzilla_stream_context_t* ctx) {
    if (!ctx) {
        return CATZILLA_STREAM_EINVAL;
    }

    // Mark as aborted
    atomic_store(&ctx->is_active, false);
    ctx->error_code = CATZILLA_STREAM_EABORTED;

    // Update statistics
    atomic_fetch_add(&g_streaming_stats.streams_aborted, 1);

    // Close the connection immediately
    if (ctx->client_handle && !uv_is_closing((uv_handle_t*)ctx->client_handle)) {
        uv_close((uv_handle_t*)ctx->client_handle, NULL);
    }

    return CATZILLA_STREAM_OK;
}

// ================================
// INTEGRATION WITH SERVER.C
// ================================

bool catzilla_is_streaming_response(const char* body, size_t body_len) {
    if (!body || body_len < STREAMING_MARKER_LEN) {
        return false;
    }

    // Check for streaming marker at the beginning of the response body
    return memcmp(body, STREAMING_MARKER, STREAMING_MARKER_LEN) == 0;
}

// Extract streaming ID from the response body
const char* catzilla_extract_streaming_id(const char* body, size_t body_len) {
    if (!body || body_len < STREAMING_MARKER_LEN + 3) {  // Need at least marker + delimiter
        return NULL;
    }

    // Check for streaming marker
    if (memcmp(body, STREAMING_MARKER, STREAMING_MARKER_LEN) != 0) {
        return NULL;
    }

    // Look for the streaming ID after the marker
    const char* id_start = body + STREAMING_MARKER_LEN;
    const char* id_end = strstr(id_start, "___");

    if (!id_end || id_end == id_start) {
        return NULL;  // No valid ID found
    }

    // Allocate and return the ID string
    size_t id_len = id_end - id_start;
    char* streaming_id = malloc(id_len + 1);
    if (!streaming_id) {
        return NULL;
    }

    memcpy(streaming_id, id_start, id_len);
    streaming_id[id_len] = '\0';

    return streaming_id;
}

int catzilla_send_streaming_response(uv_stream_t* client,
                                    int status_code,
                                    const char* content_type,
                                    const char* streaming_marker) {
    if (!client || !content_type) {
        return CATZILLA_STREAM_EINVAL;
    }

    // Build HTTP response headers for streaming
    char response_headers[1024];
    snprintf(response_headers, sizeof(response_headers),
             "HTTP/1.1 %d OK\r\n"
             "Content-Type: %s\r\n"
             "Transfer-Encoding: chunked\r\n"
             "Cache-Control: no-cache\r\n"
             "Connection: keep-alive\r\n"
             "\r\n",
             status_code, content_type);

    // Send headers immediately
    uv_buf_t buf = uv_buf_init(response_headers, strlen(response_headers));
    int result = uv_write(NULL, client, &buf, 1, NULL);

    if (result != 0) {
        return CATZILLA_STREAM_ERROR;
    }

    return CATZILLA_STREAM_OK;
}

// ================================
// RING BUFFER IMPLEMENTATION
// ================================

static size_t stream_ring_buffer_available_write(catzilla_stream_context_t* ctx) {
    size_t read_pos = atomic_load(&ctx->read_pos);
    size_t write_pos = atomic_load(&ctx->write_pos);

    if (write_pos >= read_pos) {
        return ctx->buffer_size - (write_pos - read_pos) - 1;
    } else {
        return read_pos - write_pos - 1;
    }
}

static size_t stream_ring_buffer_available_read(catzilla_stream_context_t* ctx) {
    size_t read_pos = atomic_load(&ctx->read_pos);
    size_t write_pos = atomic_load(&ctx->write_pos);

    if (write_pos >= read_pos) {
        return write_pos - read_pos;
    } else {
        return ctx->buffer_size - (read_pos - write_pos);
    }
}

static int stream_ring_buffer_write(catzilla_stream_context_t* ctx,
                                   const char* data, size_t len) {
    size_t available = stream_ring_buffer_available_write(ctx);
    if (len > available) {
        return CATZILLA_STREAM_EBACKPRESSURE;
    }

    size_t write_pos = atomic_load(&ctx->write_pos);

    // Handle wrap-around
    if (write_pos + len <= ctx->buffer_size) {
        // No wrap-around needed
        memcpy(ctx->ring_buffer + write_pos, data, len);
    } else {
        // Split write due to wrap-around
        size_t first_part = ctx->buffer_size - write_pos;
        size_t second_part = len - first_part;

        memcpy(ctx->ring_buffer + write_pos, data, first_part);
        memcpy(ctx->ring_buffer, data + first_part, second_part);
    }

    // Update write position atomically
    atomic_store(&ctx->write_pos, (write_pos + len) % ctx->buffer_size);

    return CATZILLA_STREAM_OK;
}

static int stream_ring_buffer_read(catzilla_stream_context_t* ctx,
                                  char* buffer, size_t max_len, size_t* actual_len) {
    size_t available = stream_ring_buffer_available_read(ctx);
    if (available == 0) {
        *actual_len = 0;
        return CATZILLA_STREAM_OK;
    }

    size_t to_read = (available < max_len) ? available : max_len;
    size_t read_pos = atomic_load(&ctx->read_pos);

    // Handle wrap-around
    if (read_pos + to_read <= ctx->buffer_size) {
        // No wrap-around needed
        memcpy(buffer, ctx->ring_buffer + read_pos, to_read);
    } else {
        // Split read due to wrap-around
        size_t first_part = ctx->buffer_size - read_pos;
        size_t second_part = to_read - first_part;

        memcpy(buffer, ctx->ring_buffer + read_pos, first_part);
        memcpy(buffer + first_part, ctx->ring_buffer, second_part);
    }

    // Update read position atomically
    atomic_store(&ctx->read_pos, (read_pos + to_read) % ctx->buffer_size);

    *actual_len = to_read;
    return CATZILLA_STREAM_OK;
}

static void stream_process_ring_buffer(catzilla_stream_context_t* ctx) {
    // Check if there's data to send
    size_t available = stream_ring_buffer_available_read(ctx);
    if (available == 0) {
        return;
    }

    // Don't send if we have too many pending writes
    size_t pending = atomic_load(&ctx->pending_writes);
    if (pending >= ctx->max_pending_writes) {
        return;
    }

    // Read data from ring buffer
    char temp_buffer[8192];  // 8KB temporary buffer
    size_t to_read = (available < sizeof(temp_buffer)) ? available : sizeof(temp_buffer);
    size_t actual_read;

    int result = stream_ring_buffer_read(ctx, temp_buffer, to_read, &actual_read);
    if (result != CATZILLA_STREAM_OK || actual_read == 0) {
        return;
    }

    // Format as HTTP chunked encoding
    char chunk_header[32];
    snprintf(chunk_header, sizeof(chunk_header), "%zx\r\n", actual_read);

    // Prepare buffers for libuv write
    uv_buf_t buffers[3];
    buffers[0] = uv_buf_init(chunk_header, strlen(chunk_header));
    buffers[1] = uv_buf_init(temp_buffer, actual_read);
    buffers[2] = uv_buf_init("\r\n", 2);

    // Increment pending writes counter
    atomic_fetch_add(&ctx->pending_writes, 1);

    // Send via libuv
    result = uv_write(&ctx->write_req, ctx->client_handle, buffers, 3,
                     on_stream_write_complete);

    if (result != 0) {
        // Write failed, decrement counter
        atomic_fetch_sub(&ctx->pending_writes, 1);
        ctx->error_code = result;
    }
}

static void on_stream_write_complete(uv_write_t* req, int status) {
    catzilla_stream_context_t* ctx = (catzilla_stream_context_t*)req->data;
    if (!ctx) {
        return;
    }

    // Decrement pending writes counter
    size_t pending = atomic_fetch_sub(&ctx->pending_writes, 1);

    // Check for errors
    if (status != 0) {
        ctx->error_code = status;
        atomic_fetch_add(&g_streaming_stats.connection_errors, 1);
        return;
    }

    // Clear backpressure if write queue is manageable
    if (pending <= BACKPRESSURE_THRESHOLD && ctx->backpressure_active) {
        ctx->backpressure_active = false;

        if (ctx->backpressure_callback) {
            ctx->backpressure_callback(ctx->callback_context, false);
        }
    }

    // Continue processing ring buffer if there's more data
    if (atomic_load(&ctx->is_active)) {
        stream_process_ring_buffer(ctx);
    }
}

// ================================
// PERFORMANCE MONITORING
// ================================

void catzilla_streaming_get_stats(catzilla_streaming_stats_t* stats) {
    if (!stats) {
        return;
    }

    memcpy(stats, &g_streaming_stats, sizeof(catzilla_streaming_stats_t));

    // Calculate average throughput
    uint64_t total_bytes = atomic_load(&stats->total_bytes_streamed);
    uint64_t total_streams = atomic_load(&stats->streams_completed);

    if (total_streams > 0) {
        stats->avg_throughput_mbps = (double)total_bytes / (1024.0 * 1024.0 * total_streams);
    } else {
        stats->avg_throughput_mbps = 0.0;
    }
}

void catzilla_streaming_reset_stats(void) {
    memset(&g_streaming_stats, 0, sizeof(catzilla_streaming_stats_t));
}

bool catzilla_stream_has_backpressure(catzilla_stream_context_t* ctx) {
    if (!ctx) {
        return false;
    }

    return ctx->backpressure_active;
}

int catzilla_stream_wait_for_drain(catzilla_stream_context_t* ctx,
                                   uint32_t timeout_ms) {
    if (!ctx) {
        return CATZILLA_STREAM_EINVAL;
    }

#ifdef _WIN32
    LARGE_INTEGER start_time, current_time, frequency;
    QueryPerformanceFrequency(&frequency);
    QueryPerformanceCounter(&start_time);
#else
    struct timespec start_time, current_time;
    clock_gettime(CLOCK_MONOTONIC, &start_time);
#endif

    // Poll until backpressure is relieved or timeout
    while (ctx->backpressure_active) {
        // Check timeout
        if (timeout_ms > 0) {
#ifdef _WIN32
            QueryPerformanceCounter(&current_time);
            uint64_t elapsed_ms = (uint64_t)(((current_time.QuadPart - start_time.QuadPart) * 1000) /
                                  frequency.QuadPart);
#else
            clock_gettime(CLOCK_MONOTONIC, &current_time);
            uint64_t elapsed_ms = (current_time.tv_sec - start_time.tv_sec) * 1000 +
                                 (current_time.tv_nsec - start_time.tv_nsec) / 1000000;
#endif

            if (elapsed_ms >= timeout_ms) {
                return UV_ETIMEDOUT;
            }
        }

        // Run one iteration of the event loop
        uv_run(ctx->loop, UV_RUN_NOWAIT);

        // Small sleep to prevent busy waiting
#ifdef _WIN32
        Sleep(1);      // 1ms on Windows
#else
        usleep(1000);  // 1ms on Unix
#endif
    }

    return CATZILLA_STREAM_OK;
}

// ================================
// UTILITY FUNCTIONS
// ================================

size_t catzilla_stream_optimal_buffer_size(uint64_t expected_size) {
    if (expected_size < 1024) {
        return 1024;  // 1KB minimum
    } else if (expected_size < 64 * 1024) {
        return 8 * 1024;  // 8KB for small streams
    } else if (expected_size < 1024 * 1024) {
        return 64 * 1024;  // 64KB for medium streams
    } else {
        return 256 * 1024;  // 256KB for large streams
    }
}

double catzilla_stream_get_throughput_mbps(catzilla_stream_context_t* ctx) {
    if (!ctx || ctx->bytes_streamed == 0) {
        return 0.0;
    }

    double elapsed_seconds = 0.0;

#ifdef _WIN32
    LARGE_INTEGER current_time, frequency;
    QueryPerformanceCounter(&current_time);
    QueryPerformanceFrequency(&frequency);

    elapsed_seconds = (double)(current_time.QuadPart - ctx->start_time.QuadPart) /
                     (double)frequency.QuadPart;
#else
    struct timespec current_time;
    clock_gettime(CLOCK_MONOTONIC, &current_time);

    elapsed_seconds = (current_time.tv_sec - ctx->start_time.tv_sec) +
                     (current_time.tv_nsec - ctx->start_time.tv_nsec) / 1e9;
#endif

    if (elapsed_seconds <= 0.0) {
        return 0.0;
    }

    double bytes_per_second = ctx->bytes_streamed / elapsed_seconds;
    return bytes_per_second / (1024.0 * 1024.0);  // Convert to MB/s
}

void catzilla_stream_set_callbacks(catzilla_stream_context_t* ctx,
                                   stream_callback_t chunk_cb,
                                   backpressure_callback_t backpressure_cb,
                                   void* context) {
    if (!ctx) {
        return;
    }

    ctx->chunk_callback = chunk_cb;
    ctx->backpressure_callback = backpressure_cb;
    ctx->callback_context = context;
}
