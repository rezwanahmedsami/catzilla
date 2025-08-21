#ifndef CATZILLA_TASK_SYSTEM_H
#define CATZILLA_TASK_SYSTEM_H

#include <stdint.h>
#include <stdbool.h>
#include <time.h>
#include "memory.h"
#include "platform_atomic.h"

#ifndef _WIN32
#include <pthread.h>
#include <stdatomic.h>
// For non-Windows, use standard atomic types
typedef _Atomic(void*) atomic_ptr_t;
typedef _Atomic(uint64_t) atomic_uint64_t;
typedef _Atomic(double) atomic_double_t;
#endif

#ifdef __cplusplus
extern "C" {
#endif

// Task priorities - optimized for different use cases
typedef enum {
    TASK_PRIORITY_CRITICAL = 0,    // Real-time tasks: <1ms target
    TASK_PRIORITY_HIGH = 1,        // User-facing: <10ms target
    TASK_PRIORITY_NORMAL = 2,      // Background: <100ms target
    TASK_PRIORITY_LOW = 3          // Maintenance: <1s target
} task_priority_t;

// Task execution status
typedef enum {
    TASK_STATUS_PENDING = 0,
    TASK_STATUS_RUNNING = 1,
    TASK_STATUS_COMPLETED = 2,
    TASK_STATUS_FAILED = 3,
    TASK_STATUS_CANCELLED = 4,
    TASK_STATUS_RETRYING = 5
} task_status_t;

// Forward declarations
typedef struct catzilla_task catzilla_task_t;

#ifndef _WIN32
// Full implementation for Unix/Linux/macOS
typedef struct lock_free_queue lock_free_queue_t;
typedef struct worker_thread worker_thread_t;
typedef struct worker_pool worker_pool_t;
typedef struct task_engine task_engine_t;

// Task structure with zero-copy optimization
struct catzilla_task {
    // Task identification and metadata
    uint64_t task_id;                    // Unique identifier
    task_priority_t priority;            // Task priority level
    task_status_t status;                // Current status

    // Execution context - union for memory efficiency
    union {
        struct {
            void (*c_func)(void* data, void* result);
            void* c_data;
            size_t data_size;
        } c_task;
        struct {
            void* py_func;               // PyObject* - opaque for C
            void* py_args;               // PyObject* - opaque for C
            void* py_kwargs;             // PyObject* - opaque for C
        } py_task;
    };

    // Scheduling information
    uint64_t created_at;                 // Creation timestamp (nanoseconds)
    uint64_t scheduled_at;               // When to execute (nanoseconds)
    uint64_t delay_ms;                   // Delay before execution
    uint64_t timeout_ms;                 // Execution timeout

    // Retry configuration
    int max_retries;                     // Maximum retry attempts
    int current_retries;                 // Current retry count
    double retry_backoff_factor;         // Exponential backoff factor

    // Memory management with jemalloc optimization
    catzilla_memory_type_t memory_type;      // Memory allocation type for this task
    void* arena_ptr;                         // Arena-allocated memory pointer
    size_t total_size;                       // Total allocated size

    // Result handling
    void* result_data;                   // Result storage
    size_t result_size;                  // Result data size
    void (*on_success)(void* result, void* context);
    void (*on_failure)(void* error, void* context);
    void (*on_retry)(int attempt, void* context);
    void* callback_context;              // Context for callbacks

    // Performance metrics
    uint64_t execution_start;            // Execution start time
    uint64_t execution_end;              // Execution end time
    uint64_t memory_peak;                // Peak memory usage

    // Linked list for queue management
    atomic_ptr_t next;                   // Next task in queue (atomic for lock-free)
    atomic_ptr_t prev;                   // Previous task (for removal)
};

// Lock-free queue with atomic operations
struct lock_free_queue {
    atomic_ptr_t head;                   // Queue head (atomic)
    atomic_ptr_t tail;                   // Queue tail (atomic)
    atomic_uint64_t size;                // Current queue size
    uint64_t max_size;                   // Maximum capacity

    // Performance metrics
    atomic_uint64_t enqueue_count;       // Total enqueued tasks
    atomic_uint64_t dequeue_count;       // Total dequeued tasks
    atomic_uint64_t contention_count;    // Lock contention events
    atomic_uint64_t overflow_count;      // Queue overflow events

    // Memory management
    catzilla_memory_type_t queue_memory_type; // Memory type for queue nodes

    // Queue name for debugging
    char name[64];
};

// Worker thread with thread-local optimization
struct worker_thread {
    pthread_t thread;                    // OS thread handle
    int worker_id;                       // Unique worker identifier
    atomic_bool is_active;               // Worker active state
    atomic_bool should_stop;             // Shutdown signal

    // Context and memory management
    void* callback_context;              // Reference to parent pool

    // Performance metrics
    atomic_uint64_t tasks_processed;     // Total tasks processed
    atomic_uint64_t total_execution_time; // Total execution time (ns)
    atomic_uint64_t idle_time;           // Total idle time (ns)
    uint64_t last_task_time;             // Last task completion time

    // Thread-local memory optimization
    catzilla_memory_type_t local_memory_type; // Thread-local memory type
    void* thread_local_buffer;           // Pre-allocated buffer
    size_t buffer_size;                  // Buffer size

    // Current task context
    catzilla_task_t* current_task;       // Currently executing task
    uint64_t task_start_time;            // Current task start time

    // Worker statistics
    double cpu_utilization;              // CPU usage percentage
    uint64_t memory_usage;               // Current memory usage
    uint64_t peak_memory;                // Peak memory usage
};

// Worker pool with auto-scaling capabilities
struct worker_pool {
    worker_thread_t* workers;            // Worker thread array
    atomic_int worker_count;             // Current number of workers
    int max_workers;                     // Maximum allowed workers
    int min_workers;                     // Minimum required workers

    // Priority queues - one per priority level
    lock_free_queue_t* queues[4];        // Priority-based queues

    // Synchronization primitives
    pthread_mutex_t pool_mutex;          // Pool state protection
    pthread_cond_t work_available;       // Work availability signal
    pthread_cond_t worker_idle;          // Worker idle signal
    atomic_bool shutdown_requested;      // Shutdown flag

    // Auto-scaling metrics
    atomic_uint64_t total_queue_size;    // Combined queue size
    atomic_double_t queue_pressure;      // Queue pressure metric (0.0-1.0)
    uint64_t scale_up_threshold;         // Scale up when pressure > threshold
    uint64_t scale_down_threshold;       // Scale down when pressure < threshold
    uint64_t last_scale_time;            // Last scaling operation time
    uint64_t scale_cooldown_ms;          // Cooldown period between scaling

    // Performance tracking
    atomic_uint64_t tasks_per_second;    // Current throughput
    atomic_double_t avg_response_time;   // Average task response time
    atomic_double_t p95_response_time;   // 95th percentile response time
    atomic_double_t p99_response_time;   // 99th percentile response time

    // Memory pool for workers
    catzilla_memory_type_t worker_memory_type; // Memory type for worker-related allocations
};

// Main task engine
struct task_engine {
    worker_pool_t* pool;                 // Worker pool

    // Engine configuration
    bool enable_auto_scaling;            // Auto-scaling enabled
    bool enable_performance_monitoring;  // Performance monitoring enabled
    bool enable_c_compilation;           // C task compilation enabled

    // Global memory management
    catzilla_memory_type_t task_memory_type;    // Memory type for task objects
    catzilla_memory_type_t result_memory_type;  // Memory type for task results
    catzilla_memory_type_t temp_memory_type;    // Memory type for temporary data

    // Engine statistics
    atomic_uint64_t total_tasks_queued;  // Total tasks added to queues
    atomic_uint64_t total_tasks_completed; // Total completed tasks
    atomic_uint64_t total_tasks_failed;  // Total failed tasks
    atomic_uint64_t total_execution_time; // Total execution time across all tasks

    // Engine state
    atomic_bool is_running;              // Engine running state
    uint64_t start_time;                 // Engine start time

    // Performance optimization
    void* compiled_tasks;                // Cache for compiled C tasks
    size_t compiled_tasks_count;         // Number of compiled tasks
};

// Core API functions

// Engine lifecycle
task_engine_t* catzilla_task_engine_create(
    int initial_workers,
    int min_workers,
    int max_workers,
    size_t queue_size,
    bool enable_auto_scaling,
    size_t memory_pool_mb
);

int catzilla_task_engine_start(task_engine_t* engine);
int catzilla_task_engine_stop(task_engine_t* engine, bool wait_for_completion);
void catzilla_task_engine_destroy(task_engine_t* engine);

// Task management
uint64_t catzilla_task_add_c(
    task_engine_t* engine,
    void (*c_func)(void* data, void* result),
    void* data,
    size_t data_size,
    task_priority_t priority,
    uint64_t delay_ms,
    int max_retries
);

uint64_t catzilla_task_add_python(
    task_engine_t* engine,
    void* py_func,
    void* py_args,
    void* py_kwargs,
    task_priority_t priority,
    uint64_t delay_ms,
    int max_retries
);

bool catzilla_task_cancel(task_engine_t* engine, uint64_t task_id);
task_status_t catzilla_task_get_status(task_engine_t* engine, uint64_t task_id);

// Result handling
bool catzilla_task_wait_for_result(
    task_engine_t* engine,
    uint64_t task_id,
    void** result,
    size_t* result_size,
    uint64_t timeout_ms
);

// Performance monitoring
typedef struct {
    // Queue metrics
    uint64_t critical_queue_size;
    uint64_t high_queue_size;
    uint64_t normal_queue_size;
    uint64_t low_queue_size;
    uint64_t total_queued;
    double queue_pressure;

    // Worker metrics
    int active_workers;
    int idle_workers;
    int total_workers;
    double avg_worker_utilization;
    double worker_cpu_usage;
    uint64_t worker_memory_usage;

    // Performance metrics
    uint64_t tasks_per_second;
    double avg_execution_time_ms;
    double p95_execution_time_ms;
    double p99_execution_time_ms;
    uint64_t memory_usage_mb;
    double memory_efficiency;

    // Error metrics
    uint64_t failed_tasks;
    uint64_t retry_count;
    uint64_t timeout_count;
    double error_rate;

    // Engine metrics
    uint64_t uptime_seconds;
    uint64_t total_tasks_processed;
    double engine_cpu_usage;
    uint64_t engine_memory_usage;
} task_engine_stats_t;

task_engine_stats_t catzilla_task_engine_get_stats(task_engine_t* engine);

// Worker pool management
int catzilla_worker_pool_scale_up(worker_pool_t* pool, int additional_workers);
int catzilla_worker_pool_scale_down(worker_pool_t* pool, int workers_to_remove);
int catzilla_worker_pool_get_optimal_size(worker_pool_t* pool);

// Queue operations
lock_free_queue_t* catzilla_queue_create(const char* name, size_t max_size, catzilla_memory_type_t memory_type);
bool catzilla_queue_enqueue(lock_free_queue_t* queue, catzilla_task_t* task);
catzilla_task_t* catzilla_queue_dequeue(lock_free_queue_t* queue);
bool catzilla_queue_is_empty(lock_free_queue_t* queue);
uint64_t catzilla_queue_size(lock_free_queue_t* queue);
void catzilla_queue_destroy(lock_free_queue_t* queue);

// Task creation and management
catzilla_task_t* catzilla_task_create(
    task_priority_t priority,
    uint64_t delay_ms,
    int max_retries,
    catzilla_memory_type_t memory_type
);
void catzilla_task_destroy(catzilla_task_t* task);

// Memory and performance utilities
uint64_t catzilla_get_nanoseconds(void);
void catzilla_task_update_stats(catzilla_task_t* task);

#else
// Windows stub declarations
typedef struct task_engine task_engine_t;
typedef struct catzilla_task catzilla_task_t;
typedef struct lock_free_queue lock_free_queue_t;
typedef struct worker_thread worker_thread_t;
typedef struct worker_pool worker_pool_t;

// Minimal task structure for Windows
struct catzilla_task {
    uint64_t task_id;
    int priority;
    int status;
    void* result_data;
    size_t result_size;
    uint64_t created_at;
    uint64_t scheduled_at;
    uint64_t delay_ms;
    uint64_t timeout_ms;
    int max_retries;
    int current_retries;
    double retry_backoff_factor;
    int memory_type;
    void* arena_ptr;
    size_t total_size;
    void (*on_success)(void* result, void* context);
    void (*on_failure)(void* error, void* context);
    void (*on_retry)(int attempt, void* context);
    void* callback_context;
    uint64_t execution_start;
    uint64_t execution_end;
    uint64_t memory_peak;
    atomic_ptr_t next;
    atomic_ptr_t prev;
    union {
        struct {
            void (*c_func)(void* data, void* result);
            void* c_data;
            size_t data_size;
        } c_task;
        struct {
            void* py_func;
            void* py_args;
            void* py_kwargs;
        } py_task;
    };
};

// Minimal queue structure for Windows
struct lock_free_queue {
    atomic_ptr_t head;
    atomic_ptr_t tail;
    atomic_uint64_t size;
    uint64_t max_size;
    atomic_uint64_t enqueue_count;
    atomic_uint64_t dequeue_count;
    atomic_uint64_t contention_count;
    atomic_uint64_t overflow_count;
    int queue_memory_type;
    char name[64];
};

// Minimal engine structure for Windows
struct task_engine {
    void* placeholder;
};

// Function type definitions
typedef void (*catzilla_task_func_t)(void* data);
typedef int catzilla_task_priority_t;

// Statistics structure
typedef struct {
    uint64_t uptime_seconds;
    uint64_t total_tasks_processed;
    double engine_cpu_usage;
    uint64_t engine_memory_usage;
} task_engine_stats_t;

// Minimal function declarations for Windows
task_engine_t* catzilla_task_engine_create(
    int initial_workers,
    int min_workers,
    int max_workers,
    size_t queue_size,
    bool enable_auto_scaling,
    size_t memory_pool_mb
);
void catzilla_task_engine_destroy(task_engine_t* engine);
bool catzilla_schedule_task(task_engine_t* engine, catzilla_task_func_t func, void* data, catzilla_task_priority_t priority);
task_engine_stats_t catzilla_task_engine_get_stats(task_engine_t* engine);
int catzilla_task_engine_start(task_engine_t* engine);
int catzilla_task_engine_stop(task_engine_t* engine, bool wait_for_completion);
uint64_t catzilla_task_add_c(
    task_engine_t* engine,
    void (*c_func)(void* data, void* result),
    void* data,
    size_t data_size,
    int priority,
    uint64_t delay_ms,
    int max_retries
);

// Queue operations
lock_free_queue_t* catzilla_queue_create(const char* name, size_t max_size, int memory_type);
bool catzilla_queue_enqueue(lock_free_queue_t* queue, catzilla_task_t* task);
catzilla_task_t* catzilla_queue_dequeue(lock_free_queue_t* queue);
bool catzilla_queue_is_empty(lock_free_queue_t* queue);
uint64_t catzilla_queue_size(lock_free_queue_t* queue);
void catzilla_queue_destroy(lock_free_queue_t* queue);

// Task management
catzilla_task_t* catzilla_task_create(int priority, uint64_t delay_ms, int max_retries, int memory_type);
void catzilla_task_destroy(catzilla_task_t* task);

// Utility functions
uint64_t catzilla_get_nanoseconds(void);
void catzilla_task_update_stats(catzilla_task_t* task);

#endif // _WIN32

#ifdef __cplusplus
}
#endif

#endif // CATZILLA_TASK_SYSTEM_H
