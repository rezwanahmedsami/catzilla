#ifndef CATZILLA_STREAMING_H
#define CATZILLA_STREAMING_H

#include <stdint.h>
#include <stdbool.h>
#include <stddef.h>
#include <time.h>
#include <uv.h>

// Platform-specific includes
#ifdef _WIN32
#include <windows.h>
#else
#include <stdatomic.h>
#include <unistd.h>
#endif

// Forward declaration for server integration
struct catzilla_request_s;
typedef struct catzilla_request_s catzilla_request_t;
struct catzilla_server_s;
typedef struct catzilla_server_s catzilla_server_t;

#ifdef __cplusplus
extern "C" {
#endif

// Cross-platform atomic operations
#ifdef _WIN32
// Windows atomic implementation
typedef struct {
    volatile LONG64 value;
} atomic_size_t;

typedef struct {
    volatile LONG value;
} atomic_uint;

typedef struct {
    volatile LONG value;
} atomic_bool;

// Function prototypes for Windows atomic operations
static inline size_t atomic_load_size(const atomic_size_t* obj);
static inline unsigned int atomic_load_uint(const atomic_uint* obj);
static inline bool atomic_load_bool(const atomic_bool* obj);
static inline void atomic_store_size(atomic_size_t* obj, size_t value);
static inline void atomic_store_uint(atomic_uint* obj, unsigned int value);
static inline void atomic_store_bool(atomic_bool* obj, bool value);
static inline size_t atomic_fetch_add_size(atomic_size_t* obj, size_t arg);
static inline unsigned int atomic_fetch_add_uint(atomic_uint* obj, unsigned int arg);
static inline size_t atomic_fetch_sub_size(atomic_size_t* obj, size_t arg);
static inline unsigned int atomic_fetch_sub_uint(atomic_uint* obj, unsigned int arg);

// Macro wrappers for type-generic atomic operations
#define atomic_load(obj) _Generic((obj), \
    atomic_size_t*: atomic_load_size, \
    atomic_uint*: atomic_load_uint, \
    atomic_bool*: atomic_load_bool \
    )(obj)

#define atomic_store(obj, value) _Generic((obj), \
    atomic_size_t*: atomic_store_size, \
    atomic_uint*: atomic_store_uint, \
    atomic_bool*: atomic_store_bool \
    )(obj, value)

#define atomic_fetch_add(obj, arg) _Generic((obj), \
    atomic_size_t*: atomic_fetch_add_size, \
    atomic_uint*: atomic_fetch_add_uint \
    )(obj, arg)

#define atomic_fetch_sub(obj, arg) _Generic((obj), \
    atomic_size_t*: atomic_fetch_sub_size, \
    atomic_uint*: atomic_fetch_sub_uint \
    )(obj, arg)

// Implementation of atomic operations for Windows
static inline size_t atomic_load_size(const atomic_size_t* obj) {
    return (size_t)InterlockedCompareExchange64((volatile LONG64*)&obj->value, 0, 0);
}

static inline unsigned int atomic_load_uint(const atomic_uint* obj) {
    return (unsigned int)InterlockedCompareExchange((volatile LONG*)&obj->value, 0, 0);
}

static inline bool atomic_load_bool(const atomic_bool* obj) {
    return InterlockedCompareExchange((volatile LONG*)&obj->value, 0, 0) != 0;
}

static inline void atomic_store_size(atomic_size_t* obj, size_t value) {
    InterlockedExchange64((volatile LONG64*)&obj->value, (LONG64)value);
}

static inline void atomic_store_uint(atomic_uint* obj, unsigned int value) {
    InterlockedExchange((volatile LONG*)&obj->value, (LONG)value);
}

static inline void atomic_store_bool(atomic_bool* obj, bool value) {
    InterlockedExchange((volatile LONG*)&obj->value, value ? 1 : 0);
}

static inline size_t atomic_fetch_add_size(atomic_size_t* obj, size_t arg) {
    return (size_t)InterlockedExchangeAdd64((volatile LONG64*)&obj->value, (LONG64)arg);
}

static inline unsigned int atomic_fetch_add_uint(atomic_uint* obj, unsigned int arg) {
    return (unsigned int)InterlockedExchangeAdd((volatile LONG*)&obj->value, (LONG)arg);
}

static inline size_t atomic_fetch_sub_size(atomic_size_t* obj, size_t arg) {
    return (size_t)InterlockedExchangeAdd64((volatile LONG64*)&obj->value, -(LONG64)arg);
}

static inline unsigned int atomic_fetch_sub_uint(atomic_uint* obj, unsigned int arg) {
    return (unsigned int)InterlockedExchangeAdd((volatile LONG*)&obj->value, -(LONG)arg);
}
#endif

// Forward declarations
typedef struct catzilla_stream_context_s catzilla_stream_context_t;
typedef struct catzilla_streaming_stats_s catzilla_streaming_stats_t;

// Streaming operation callbacks
typedef void (*stream_callback_t)(void* ctx, const char* data, size_t len);
typedef void (*backpressure_callback_t)(void* ctx, bool active);

// Stream operation types
typedef enum {
    STREAM_OP_WRITE_CHUNK = 0,
    STREAM_OP_WRITE_FILE = 1,
    STREAM_OP_WRITE_GENERATOR = 2,
    STREAM_OP_FINISH = 3,
    STREAM_OP_ABORT = 4
} stream_operation_t;

// Stream context for zero-copy operations
typedef struct catzilla_stream_context_s {
    // libuv integration (CRITICAL for Catzilla)
    uv_stream_t* client_handle;         // Direct integration with server.c
    uv_write_t write_req;               // For async writes
    uv_loop_t* loop;                    // Event loop reference

    // Memory management (using existing Catzilla system)
    void* stream_arena;                 // Memory arena for this stream

    // Lock-free ring buffer (EXCELLENT design)
    char* ring_buffer;
    size_t buffer_size;
    atomic_size_t read_pos;
    atomic_size_t write_pos;
    atomic_bool is_active;

    // Performance monitoring (GOOD)
    uint64_t bytes_streamed;
#ifdef _WIN32
    LARGE_INTEGER start_time;
#else
    struct timespec start_time;
#endif

    // Integration with existing server lifecycle
    catzilla_request_t* request;         // Link to original request
    catzilla_server_t* server;           // Reference to server for cleanup

    // Backpressure management (CRITICAL for stability)
    atomic_size_t pending_writes;
    size_t max_pending_writes;
    bool backpressure_active;

    // Callbacks
    stream_callback_t chunk_callback;
    backpressure_callback_t backpressure_callback;
    void* callback_context;

    // State management
    bool headers_sent;
    char* content_type;
    int status_code;

    // Error handling
    int error_code;
    char* error_message;
} catzilla_stream_context_t;

// Performance monitoring structure
typedef struct catzilla_streaming_stats_s {
    atomic_uint active_streams;
    atomic_uint total_bytes_streamed;
    atomic_uint streams_created;
    atomic_uint streams_completed;
    atomic_uint streams_aborted;
    double avg_throughput_mbps;

    // Memory usage
    atomic_uint memory_allocated;
    atomic_uint peak_memory_usage;

    // Error tracking
    atomic_uint connection_errors;
    atomic_uint backpressure_events;
} catzilla_streaming_stats_t;

// ================================
// CORE STREAMING API
// ================================

/**
 * Create a new streaming context
 * @param client libuv stream handle from server.c
 * @param buffer_size Size of ring buffer (default: 64KB)
 * @return Stream context or NULL on error
 */
catzilla_stream_context_t* catzilla_stream_create(uv_stream_t* client,
                                                  size_t buffer_size);

/**
 * Destroy streaming context and cleanup resources
 * @param ctx Stream context to destroy
 */
void catzilla_stream_destroy(catzilla_stream_context_t* ctx);

/**
 * Write a chunk of data to the stream (lock-free, zero-copy)
 * @param ctx Stream context
 * @param data Data to write
 * @param len Length of data
 * @return 0 on success, error code on failure
 */
int catzilla_stream_write_chunk(catzilla_stream_context_t* ctx,
                                const char* data, size_t len);

/**
 * Write data asynchronously with callback
 * @param ctx Stream context
 * @param data Data to write
 * @param len Length of data
 * @param callback Callback when write completes
 * @return 0 on success, error code on failure
 */
int catzilla_stream_write_async(catzilla_stream_context_t* ctx,
                                const char* data, size_t len,
                                stream_callback_t callback);

/**
 * Finish the stream (send final chunk and close)
 * @param ctx Stream context
 * @return 0 on success, error code on failure
 */
int catzilla_stream_finish(catzilla_stream_context_t* ctx);

/**
 * Abort the stream (immediate close)
 * @param ctx Stream context
 * @return 0 on success, error code on failure
 */
int catzilla_stream_abort(catzilla_stream_context_t* ctx);

// ================================
// INTEGRATION WITH SERVER.C
// ================================

/**
 * Check if response body indicates streaming
 * @param body Response body pointer
 * @param body_len Response body length
 * @return true if streaming response marker found
 */
bool catzilla_is_streaming_response(const char* body, size_t body_len);

/**
 * Extract streaming ID from response body
 * @param body Response body pointer
 * @param body_len Response body length
 * @return streaming ID string (caller must free) or NULL if not found
 */
const char* catzilla_extract_streaming_id(const char* body, size_t body_len);

/**
 * Send streaming response headers
 * @param client libuv client handle
 * @param status_code HTTP status code
 * @param content_type Content-Type header
 * @param streaming_marker Streaming identifier
 * @return 0 on success, error code on failure
 */
int catzilla_send_streaming_response(uv_stream_t* client,
                                    int status_code,
                                    const char* content_type,
                                    const char* streaming_marker);

// ================================
// PERFORMANCE MONITORING
// ================================

/**
 * Get global streaming statistics
 * @param stats Structure to fill with statistics
 */
void catzilla_streaming_get_stats(catzilla_streaming_stats_t* stats);

/**
 * Reset streaming statistics
 */
void catzilla_streaming_reset_stats(void);

/**
 * Check if backpressure is active for a stream
 * @param ctx Stream context
 * @return true if backpressure is active
 */
bool catzilla_stream_has_backpressure(catzilla_stream_context_t* ctx);

/**
 * Wait for stream drain (blocking call for backpressure relief)
 * @param ctx Stream context
 * @param timeout_ms Timeout in milliseconds (0 = no timeout)
 * @return 0 on success, UV_ETIMEDOUT on timeout
 */
int catzilla_stream_wait_for_drain(catzilla_stream_context_t* ctx,
                                   uint32_t timeout_ms);

// ================================
// UTILITY FUNCTIONS
// ================================

/**
 * Calculate optimal buffer size based on expected data size
 * @param expected_size Expected total data size
 * @return Optimal buffer size
 */
size_t catzilla_stream_optimal_buffer_size(uint64_t expected_size);

/**
 * Get current streaming throughput in MB/s
 * @param ctx Stream context
 * @return Throughput in megabytes per second
 */
double catzilla_stream_get_throughput_mbps(catzilla_stream_context_t* ctx);

/**
 * Set stream callbacks for monitoring
 * @param ctx Stream context
 * @param chunk_cb Callback for chunk writes
 * @param backpressure_cb Callback for backpressure events
 * @param context User context for callbacks
 */
void catzilla_stream_set_callbacks(catzilla_stream_context_t* ctx,
                                   stream_callback_t chunk_cb,
                                   backpressure_callback_t backpressure_cb,
                                   void* context);

// ================================
// ERROR CODES
// ================================

#define CATZILLA_STREAM_OK              0
#define CATZILLA_STREAM_ERROR          -1
#define CATZILLA_STREAM_ENOMEM         -2
#define CATZILLA_STREAM_EINVAL         -3
#define CATZILLA_STREAM_EBACKPRESSURE  -4
#define CATZILLA_STREAM_EABORTED       -5
#define CATZILLA_STREAM_EFINISHED      -6

#ifdef __cplusplus
}
#endif

#endif // CATZILLA_STREAMING_H
