#include "task_system.h"
#include "memory.h"
#include <stdlib.h>
#include <stdio.h>
#include <string.h>

#ifdef _WIN32
// Windows implementation stubs
#include <windows.h>

// Windows timing utilities
static uint64_t get_nanoseconds(void) {
    LARGE_INTEGER frequency, counter;
    QueryPerformanceFrequency(&frequency);
    QueryPerformanceCounter(&counter);
    return (uint64_t)((counter.QuadPart * 1000000000ULL) / frequency.QuadPart);
}

static uint64_t get_thread_id(void) {
    return (uint64_t)GetCurrentThreadId();
}

// Atomic operation helpers for Windows
#define ATOMIC_LOAD(ptr) (*(ptr))
#define ATOMIC_STORE(ptr, val) (*(ptr) = (val))
#define ATOMIC_CAS(ptr, expected, desired) \
    (InterlockedCompareExchangePointer((volatile PVOID*)(ptr), (PVOID)(desired), (PVOID)(*expected)) == (PVOID)(*expected) ? ((*expected) = (desired), true) : false)

// Windows stub implementations
uint64_t catzilla_get_nanoseconds(void) {
    return get_nanoseconds();
}

// Task engine stubs
task_engine_t* catzilla_task_engine_create(
    int initial_workers,
    int min_workers,
    int max_workers,
    size_t queue_size,
    bool enable_auto_scaling,
    size_t memory_pool_mb
) {
    return NULL; // Stub
}

void catzilla_task_engine_destroy(task_engine_t* engine) {
    // Stub
}

bool catzilla_schedule_task(task_engine_t* engine, catzilla_task_func_t func, void* data, catzilla_task_priority_t priority) {
    return false; // Stub
}

// Queue operation stubs
lock_free_queue_t* catzilla_queue_create(const char* name, size_t max_size, int memory_type) {
    return NULL; // Stub
}

bool catzilla_queue_enqueue(lock_free_queue_t* queue, catzilla_task_t* task) {
    return false; // Stub
}

catzilla_task_t* catzilla_queue_dequeue(lock_free_queue_t* queue) {
    return NULL; // Stub
}

bool catzilla_queue_is_empty(lock_free_queue_t* queue) {
    return true; // Stub
}

uint64_t catzilla_queue_size(lock_free_queue_t* queue) {
    return 0; // Stub
}

void catzilla_queue_destroy(lock_free_queue_t* queue) {
    // Stub
}

// Task management stubs
catzilla_task_t* catzilla_task_create(int priority, uint64_t delay_ms, int max_retries, int memory_type) {
    return NULL; // Stub
}

void catzilla_task_destroy(catzilla_task_t* task) {
    // Stub
}

void catzilla_task_update_stats(catzilla_task_t* task) {
    // Stub
}

task_engine_stats_t catzilla_task_engine_get_stats(task_engine_t* engine) {
    task_engine_stats_t stats = {0};
    // Windows stub - return basic stats only
    stats.uptime_seconds = 0;
    stats.total_tasks_processed = 0;
    stats.engine_cpu_usage = 0.0;
    stats.engine_memory_usage = 0;
    return stats;
}

int catzilla_task_engine_start(task_engine_t* engine) {
    return -1; // Stub - not implemented on Windows
}

int catzilla_task_engine_stop(task_engine_t* engine, bool wait_for_completion) {
    return 0; // Stub - always "succeeds"
}

uint64_t catzilla_task_add_c(
    task_engine_t* engine,
    void (*c_func)(void* data, void* result),
    void* data,
    size_t data_size,
    int priority,
    uint64_t delay_ms,
    int max_retries
) {
    return 0; // Stub - return invalid task ID
}

#else
// Task system implementation - Unix/Linux/macOS only
#include <unistd.h>
#include <errno.h>
#include <sys/time.h>
#include <assert.h>
#include <pthread.h>

// Platform-specific includes
#ifdef __linux__
#include <sys/syscall.h>
#include <linux/futex.h>
#endif

// Atomic operation helpers
#define ATOMIC_LOAD(ptr) atomic_load_explicit(ptr, memory_order_acquire)
#define ATOMIC_STORE(ptr, val) atomic_store_explicit(ptr, val, memory_order_release)
#define ATOMIC_CAS(ptr, expected, desired) \
    atomic_compare_exchange_weak_explicit(ptr, expected, desired, \
                                        memory_order_release, memory_order_relaxed)

// Performance utilities
static uint64_t get_nanoseconds(void) {
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return (uint64_t)ts.tv_sec * 1000000000ULL + (uint64_t)ts.tv_nsec;
}

static uint64_t get_thread_id(void) {
#ifdef __linux__
    return (uint64_t)syscall(SYS_gettid);
#else
    return (uint64_t)pthread_self();
#endif
}

// ============================================================================
// LOCK-FREE QUEUE IMPLEMENTATION
// ============================================================================

lock_free_queue_t* catzilla_queue_create(const char* name, size_t max_size, catzilla_memory_type_t memory_type) {
    lock_free_queue_t* queue = catzilla_task_alloc(sizeof(lock_free_queue_t));
    if (!queue) return NULL;

    // Initialize atomic pointers to NULL
    atomic_init(&queue->head, NULL);
    atomic_init(&queue->tail, NULL);
    atomic_init(&queue->size, 0);

    queue->max_size = max_size;
    queue->queue_memory_type = memory_type;

    // Initialize performance counters
    atomic_init(&queue->enqueue_count, 0);
    atomic_init(&queue->dequeue_count, 0);
    atomic_init(&queue->contention_count, 0);
    atomic_init(&queue->overflow_count, 0);

    strncpy(queue->name, name, sizeof(queue->name) - 1);
    queue->name[sizeof(queue->name) - 1] = '\0';

    return queue;
}

bool catzilla_queue_enqueue(lock_free_queue_t* queue, catzilla_task_t* task) {
    if (!queue || !task) return false;

    // Check queue capacity
    uint64_t current_size = ATOMIC_LOAD(&queue->size);
    if (current_size >= queue->max_size) {
        atomic_fetch_add(&queue->overflow_count, 1);
        return false;
    }

    // Initialize task's next pointer
    ATOMIC_STORE(&task->next, NULL);

    // Michael & Scott lock-free queue algorithm
    while (true) {
        catzilla_task_t* tail = ATOMIC_LOAD(&queue->tail);
        catzilla_task_t* head = ATOMIC_LOAD(&queue->head);

        if (tail == NULL) {
            // Empty queue case
            catzilla_task_t* expected = NULL;
            if (ATOMIC_CAS(&queue->head, &expected, task)) {
                ATOMIC_STORE(&queue->tail, task);
                atomic_fetch_add(&queue->size, 1);
                atomic_fetch_add(&queue->enqueue_count, 1);
                return true;
            }
        } else {
            // Non-empty queue case
            catzilla_task_t* next = ATOMIC_LOAD(&tail->next);
            if (tail == ATOMIC_LOAD(&queue->tail)) {  // tail hasn't changed
                if (next == NULL) {
                    // Try to link task at the end of the list
                    if (ATOMIC_CAS(&tail->next, &next, task)) {
                        // Enqueue is done, try to swing tail to the inserted node
                        ATOMIC_CAS(&queue->tail, &tail, task);
                        atomic_fetch_add(&queue->size, 1);
                        atomic_fetch_add(&queue->enqueue_count, 1);
                        return true;
                    }
                } else {
                    // Tail is lagging, try to advance it
                    ATOMIC_CAS(&queue->tail, &tail, next);
                }
            }
        }

        // Brief pause to reduce contention
        atomic_fetch_add(&queue->contention_count, 1);
        sched_yield();
    }
}

catzilla_task_t* catzilla_queue_dequeue(lock_free_queue_t* queue) {
    if (!queue) return NULL;

    while (true) {
        catzilla_task_t* head = ATOMIC_LOAD(&queue->head);
        catzilla_task_t* tail = ATOMIC_LOAD(&queue->tail);

        if (head == NULL) {
            // Empty queue
            return NULL;
        }

        catzilla_task_t* next = ATOMIC_LOAD(&head->next);

        if (head == ATOMIC_LOAD(&queue->head)) {  // head hasn't changed
            if (head == tail) {
                if (next == NULL) {
                    // Queue is empty
                    return NULL;
                } else {
                    // Tail is lagging, advance it
                    ATOMIC_CAS(&queue->tail, &tail, next);
                }
            } else {
                if (next != NULL) {
                    // Try to swing head to the next node
                    if (ATOMIC_CAS(&queue->head, &head, next)) {
                        atomic_fetch_sub(&queue->size, 1);
                        atomic_fetch_add(&queue->dequeue_count, 1);
                        return head;
                    }
                }
            }
        }

        // Brief pause to reduce contention
        atomic_fetch_add(&queue->contention_count, 1);
        sched_yield();
    }
}

bool catzilla_queue_is_empty(lock_free_queue_t* queue) {
    return queue ? ATOMIC_LOAD(&queue->size) == 0 : true;
}

uint64_t catzilla_queue_size(lock_free_queue_t* queue) {
    return queue ? ATOMIC_LOAD(&queue->size) : 0;
}

void catzilla_queue_destroy(lock_free_queue_t* queue) {
    if (!queue) return;

    // Drain remaining tasks
    catzilla_task_t* task;
    while ((task = catzilla_queue_dequeue(queue)) != NULL) {
        catzilla_task_destroy(task);
    }

    // Memory will be freed when arena is destroyed
}

// ============================================================================
// TASK MANAGEMENT
// ============================================================================

catzilla_task_t* catzilla_task_create(
    task_priority_t priority,
    uint64_t delay_ms,
    int max_retries,
    catzilla_memory_type_t memory_type
) {
    catzilla_task_t* task = catzilla_task_alloc(sizeof(catzilla_task_t));
    if (!task) return NULL;

    // Generate unique task ID (timestamp + random)
    static atomic_uint64_t task_counter = ATOMIC_VAR_INIT(0);
    task->task_id = (get_nanoseconds() << 16) | atomic_fetch_add(&task_counter, 1);

    task->priority = priority;
    task->status = TASK_STATUS_PENDING;
    task->created_at = get_nanoseconds();
    task->scheduled_at = task->created_at + (delay_ms * 1000000ULL);
    task->delay_ms = delay_ms;
    task->timeout_ms = 30000; // Default 30 second timeout
    task->max_retries = max_retries;
    task->current_retries = 0;
    task->retry_backoff_factor = 2.0;

    task->memory_type = memory_type;
    task->arena_ptr = NULL;
    task->total_size = sizeof(catzilla_task_t);

    task->result_data = NULL;
    task->result_size = 0;
    task->on_success = NULL;
    task->on_failure = NULL;
    task->on_retry = NULL;
    task->callback_context = NULL;

    task->execution_start = 0;
    task->execution_end = 0;
    task->memory_peak = 0;

    atomic_init(&task->next, NULL);
    atomic_init(&task->prev, NULL);

    return task;
}

void catzilla_task_destroy(catzilla_task_t* task) {
    if (!task) return;

    // Free any allocated result data
    if (task->result_data) {
        catzilla_task_free(task->result_data);
    }

    // Task memory will be freed when appropriate
}

static void execute_c_task(catzilla_task_t* task) {
    if (!task || !task->c_task.c_func) return;

    task->execution_start = get_nanoseconds();
    task->status = TASK_STATUS_RUNNING;

    // Allocate result buffer if needed
    if (task->result_size == 0) {
        task->result_size = 1024; // Default result buffer size
    }

    task->result_data = catzilla_task_alloc(task->result_size);

    // Execute the C function
    task->c_task.c_func(task->c_task.c_data, task->result_data);

    task->execution_end = get_nanoseconds();
    task->status = TASK_STATUS_COMPLETED;

    // Call success callback if provided
    if (task->on_success) {
        task->on_success(task->result_data, task->callback_context);
    }
}

// ============================================================================
// WORKER THREAD IMPLEMENTATION
// ============================================================================

static void* worker_thread_main(void* arg) {
    worker_thread_t* worker = (worker_thread_t*)arg;
    worker_pool_t* pool = (worker_pool_t*)worker->callback_context;

    // Set thread name for debugging
    char thread_name[16];
    snprintf(thread_name, sizeof(thread_name), "catzilla_w%d", worker->worker_id);
#ifdef __APPLE__
    // pthread_setname_np may not be available on all macOS versions
    // Skipping thread naming for compatibility
#elif defined(__linux__)
    pthread_setname_np(pthread_self(), thread_name);
#endif

    // Initialize thread-local memory management
    worker->local_memory_type = CATZILLA_MEMORY_TASK;
    worker->thread_local_buffer = catzilla_task_alloc(64 * 1024); // 64KB buffer
    worker->buffer_size = 64 * 1024;

    ATOMIC_STORE(&worker->is_active, true);

    uint64_t idle_start = get_nanoseconds();

    while (!ATOMIC_LOAD(&worker->should_stop)) {
        catzilla_task_t* task = NULL;
        bool found_task = false;

        // Check priority queues in order (critical -> high -> normal -> low)
        for (int priority = 0; priority < 4; priority++) {
            task = catzilla_queue_dequeue(pool->queues[priority]);
            if (task) {
                found_task = true;
                break;
            }
        }

        if (found_task) {
            // Update idle time
            uint64_t now = get_nanoseconds();
            atomic_fetch_add(&worker->idle_time, now - idle_start);

            // Execute task
            worker->current_task = task;
            worker->task_start_time = now;

            // Check if task should be executed now
            if (now >= task->scheduled_at) {
                if (task->c_task.c_func) {
                    execute_c_task(task);
                } else {
                    // TODO: Execute Python task
                    task->status = TASK_STATUS_FAILED;
                }

                atomic_fetch_add(&worker->tasks_processed, 1);
                uint64_t execution_time = get_nanoseconds() - worker->task_start_time;
                atomic_fetch_add(&worker->total_execution_time, execution_time);
            } else {
                // Task is scheduled for future, put it back
                catzilla_queue_enqueue(pool->queues[task->priority], task);
            }

            worker->current_task = NULL;
            idle_start = get_nanoseconds();
        } else {
            // No tasks available, wait for work
            pthread_mutex_lock(&pool->pool_mutex);

            // Double-check for tasks while holding the lock
            bool has_work = false;
            for (int priority = 0; priority < 4; priority++) {
                if (!catzilla_queue_is_empty(pool->queues[priority])) {
                    has_work = true;
                    break;
                }
            }

            if (!has_work && !ATOMIC_LOAD(&worker->should_stop)) {
                // Wait for work with timeout
                struct timespec timeout;
                clock_gettime(CLOCK_REALTIME, &timeout);
                timeout.tv_nsec += 100000000; // 100ms timeout
                if (timeout.tv_nsec >= 1000000000) {
                    timeout.tv_sec += 1;
                    timeout.tv_nsec -= 1000000000;
                }

                pthread_cond_timedwait(&pool->work_available, &pool->pool_mutex, &timeout);
            }

            pthread_mutex_unlock(&pool->pool_mutex);
        }
    }

    // Cleanup
    ATOMIC_STORE(&worker->is_active, false);
    if (worker->thread_local_buffer) {
        catzilla_task_free(worker->thread_local_buffer);
    }

    return NULL;
}

// ============================================================================
// WORKER POOL MANAGEMENT
// ============================================================================

static worker_pool_t* worker_pool_create(
    int initial_workers,
    int min_workers,
    int max_workers,
    size_t queue_size,
    catzilla_memory_type_t memory_type
) {
    worker_pool_t* pool = catzilla_task_alloc(sizeof(worker_pool_t));
    if (!pool) return NULL;

    // Initialize worker array
    pool->workers = catzilla_task_alloc(sizeof(worker_thread_t) * max_workers);
    if (!pool->workers) {
        return NULL;
    }

    atomic_init(&pool->worker_count, 0);
    pool->max_workers = max_workers;
    pool->min_workers = min_workers;

    // Create priority queues
    for (int i = 0; i < 4; i++) {
        char queue_name[32];
        snprintf(queue_name, sizeof(queue_name), "priority_%d", i);
        pool->queues[i] = catzilla_queue_create(queue_name, queue_size, memory_type);
        if (!pool->queues[i]) {
            return NULL;
        }
    }

    // Initialize synchronization
    pthread_mutex_init(&pool->pool_mutex, NULL);
    pthread_cond_init(&pool->work_available, NULL);
    pthread_cond_init(&pool->worker_idle, NULL);
    atomic_init(&pool->shutdown_requested, false);

    // Initialize auto-scaling
    atomic_init(&pool->total_queue_size, 0);
    atomic_init(&pool->queue_pressure, 0.0);
    pool->scale_up_threshold = 80;   // 80% queue utilization
    pool->scale_down_threshold = 20; // 20% queue utilization
    pool->last_scale_time = get_nanoseconds();
    pool->scale_cooldown_ms = 30000; // 30 second cooldown

    // Initialize performance tracking
    atomic_init(&pool->tasks_per_second, 0);
    atomic_init(&pool->avg_response_time, 0.0);
    atomic_init(&pool->p95_response_time, 0.0);
    atomic_init(&pool->p99_response_time, 0.0);

    pool->worker_memory_type = memory_type;

    // Start initial workers
    for (int i = 0; i < initial_workers; i++) {
        worker_thread_t* worker = &pool->workers[i];
        worker->worker_id = i;
        atomic_init(&worker->is_active, false);
        atomic_init(&worker->should_stop, false);
        atomic_init(&worker->tasks_processed, 0);
        atomic_init(&worker->total_execution_time, 0);
        atomic_init(&worker->idle_time, 0);
        worker->last_task_time = get_nanoseconds();
        worker->current_task = NULL;
        worker->callback_context = pool;

        if (pthread_create(&worker->thread, NULL, worker_thread_main, worker) == 0) {
            atomic_fetch_add(&pool->worker_count, 1);
        }
    }

    return pool;
}

static void worker_pool_destroy(worker_pool_t* pool) {
    if (!pool) return;

    // Signal shutdown
    ATOMIC_STORE(&pool->shutdown_requested, true);

    // Wake up all workers
    pthread_mutex_lock(&pool->pool_mutex);
    pthread_cond_broadcast(&pool->work_available);
    pthread_mutex_unlock(&pool->pool_mutex);

    // Stop all workers
    int worker_count = ATOMIC_LOAD(&pool->worker_count);
    for (int i = 0; i < worker_count; i++) {
        worker_thread_t* worker = &pool->workers[i];
        ATOMIC_STORE(&worker->should_stop, true);
        pthread_join(worker->thread, NULL);
    }

    // Destroy queues
    for (int i = 0; i < 4; i++) {
        catzilla_queue_destroy(pool->queues[i]);
    }

    // Cleanup synchronization
    pthread_mutex_destroy(&pool->pool_mutex);
    pthread_cond_destroy(&pool->work_available);
    pthread_cond_destroy(&pool->worker_idle);
}

// ============================================================================
// TASK ENGINE IMPLEMENTATION
// ============================================================================

task_engine_t* catzilla_task_engine_create(
    int initial_workers,
    int min_workers,
    int max_workers,
    size_t queue_size,
    bool enable_auto_scaling,
    size_t memory_pool_mb
) {
    // Create main task engine
    task_engine_t* engine = catzilla_task_alloc(sizeof(task_engine_t));
    if (!engine) return NULL;

    // Initialize memory types for different purposes
    engine->task_memory_type = CATZILLA_MEMORY_TASK;
    engine->result_memory_type = CATZILLA_MEMORY_TASK;
    engine->temp_memory_type = CATZILLA_MEMORY_TASK;

    // Create worker pool
    engine->pool = worker_pool_create(
        initial_workers, min_workers, max_workers,
        queue_size, CATZILLA_MEMORY_TASK
    );

    if (!engine->pool) {
        catzilla_task_engine_destroy(engine);
        return NULL;
    }

    // Configure engine
    engine->enable_auto_scaling = enable_auto_scaling;
    engine->enable_performance_monitoring = true;
    engine->enable_c_compilation = true;

    // Initialize statistics
    atomic_init(&engine->total_tasks_queued, 0);
    atomic_init(&engine->total_tasks_completed, 0);
    atomic_init(&engine->total_tasks_failed, 0);
    atomic_init(&engine->total_execution_time, 0);
    atomic_init(&engine->is_running, false);

    engine->start_time = get_nanoseconds();
    engine->compiled_tasks = NULL;
    engine->compiled_tasks_count = 0;

    return engine;
}

int catzilla_task_engine_start(task_engine_t* engine) {
    if (!engine) return -1;

    ATOMIC_STORE(&engine->is_running, true);
    return 0;
}

int catzilla_task_engine_stop(task_engine_t* engine, bool wait_for_completion) {
    if (!engine) return -1;

    ATOMIC_STORE(&engine->is_running, false);

    if (wait_for_completion) {
        // Wait for all queues to be empty
        bool all_empty = false;
        while (!all_empty) {
            all_empty = true;
            for (int i = 0; i < 4; i++) {
                if (!catzilla_queue_is_empty(engine->pool->queues[i])) {
                    all_empty = false;
                    break;
                }
            }
            if (!all_empty) {
                usleep(10000); // 10ms
            }
        }
    }

    return 0;
}

void catzilla_task_engine_destroy(task_engine_t* engine) {
    if (!engine) return;

    catzilla_task_engine_stop(engine, true);

    if (engine->pool) {
        worker_pool_destroy(engine->pool);
    }

    // Memory cleanup is handled by typed deallocations
    catzilla_task_free(engine);
}

uint64_t catzilla_task_add_c(
    task_engine_t* engine,
    void (*c_func)(void* data, void* result),
    void* data,
    size_t data_size,
    task_priority_t priority,
    uint64_t delay_ms,
    int max_retries
) {
    if (!engine || !c_func) return 0;

    catzilla_task_t* task = catzilla_task_create(priority, delay_ms, max_retries, engine->task_memory_type);
    if (!task) return 0;

    // Copy task data
    if (data && data_size > 0) {
        task->c_task.c_data = catzilla_task_alloc(data_size);
        if (task->c_task.c_data) {
            memcpy(task->c_task.c_data, data, data_size);
            task->c_task.data_size = data_size;
        }
    } else {
        task->c_task.c_data = NULL;
        task->c_task.data_size = 0;
    }

    task->c_task.c_func = c_func;

    // Add to appropriate priority queue
    if (catzilla_queue_enqueue(engine->pool->queues[priority], task)) {
        atomic_fetch_add(&engine->total_tasks_queued, 1);

        // Signal workers
        pthread_mutex_lock(&engine->pool->pool_mutex);
        pthread_cond_broadcast(&engine->pool->work_available);
        pthread_mutex_unlock(&engine->pool->pool_mutex);

        return task->task_id;
    }

    // Failed to enqueue
    catzilla_task_destroy(task);
    return 0;
}

task_engine_stats_t catzilla_task_engine_get_stats(task_engine_t* engine) {
    task_engine_stats_t stats = {0};

    if (!engine) return stats;

    // Queue metrics
    stats.critical_queue_size = catzilla_queue_size(engine->pool->queues[0]);
    stats.high_queue_size = catzilla_queue_size(engine->pool->queues[1]);
    stats.normal_queue_size = catzilla_queue_size(engine->pool->queues[2]);
    stats.low_queue_size = catzilla_queue_size(engine->pool->queues[3]);
    stats.total_queued = stats.critical_queue_size + stats.high_queue_size +
                        stats.normal_queue_size + stats.low_queue_size;

    // Worker metrics
    int active_workers = 0;
    int idle_workers = 0;
    uint64_t total_tasks_processed = 0;
    uint64_t total_execution_time = 0;

    int worker_count = ATOMIC_LOAD(&engine->pool->worker_count);
    for (int i = 0; i < worker_count; i++) {
        worker_thread_t* worker = &engine->pool->workers[i];
        if (ATOMIC_LOAD(&worker->is_active)) {
            if (worker->current_task) {
                active_workers++;
            } else {
                idle_workers++;
            }
            total_tasks_processed += ATOMIC_LOAD(&worker->tasks_processed);
            total_execution_time += ATOMIC_LOAD(&worker->total_execution_time);
        }
    }

    stats.active_workers = active_workers;
    stats.idle_workers = idle_workers;
    stats.total_workers = worker_count;

    // Performance metrics
    uint64_t uptime_ns = get_nanoseconds() - engine->start_time;
    if (uptime_ns > 0) {
        stats.tasks_per_second = (total_tasks_processed * 1000000000ULL) / uptime_ns;
    }

    if (total_tasks_processed > 0) {
        stats.avg_execution_time_ms = (double)total_execution_time / (total_tasks_processed * 1000000.0);
    }

    // Engine metrics
    stats.uptime_seconds = uptime_ns / 1000000000ULL;
    stats.total_tasks_processed = ATOMIC_LOAD(&engine->total_tasks_completed);
    stats.failed_tasks = ATOMIC_LOAD(&engine->total_tasks_failed);

    if (stats.total_tasks_processed > 0) {
        stats.error_rate = (double)stats.failed_tasks / stats.total_tasks_processed;
    }

    return stats;
}

// Public utility function for nanosecond timing
uint64_t catzilla_get_nanoseconds(void) {
    return get_nanoseconds();
}

#endif // _WIN32
