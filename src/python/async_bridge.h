/*
 * Catzilla Async Bridge Header
 *
 * Public API for the C-Python AsyncIO bridge system.
 * Provides thread-safe, high-performance integration between libuv and Python asyncio.
 */

#ifndef CATZILLA_ASYNC_BRIDGE_H
#define CATZILLA_ASYNC_BRIDGE_H

#include <Python.h>
#include <uv.h>
#include <stdint.h>
#include <stdbool.h>

#ifdef __cplusplus
extern "C" {
#endif

// Opaque types for public API
typedef struct async_bridge_task_s async_bridge_task_t;

// Task completion callback signature
typedef void (*async_completion_callback_t)(async_bridge_task_t* task, void* user_data);

// Bridge statistics structure
typedef struct {
    uint64_t total_tasks_executed;
    uint64_t total_execution_time_ns;
    uint64_t peak_concurrent_tasks;
    uint64_t current_active_tasks;
    uint64_t average_execution_time_ns;
    bool is_running;
} async_bridge_stats_t;

// ============================================================================
// PUBLIC API
// ============================================================================

/**
 * Initialize the async bridge system.
 * Must be called once during module initialization.
 *
 * @param main_loop The main libuv event loop (can be NULL to create default loop)
 * @return 0 on success, -1 on failure
 */
int catzilla_async_bridge_init(uv_loop_t* main_loop);

/**
 * Cleanup the async bridge system.
 * Should be called during module shutdown.
 */
void catzilla_async_bridge_cleanup(void);

/**
 * Execute an async Python handler
 *
 * @param coroutine Python coroutine object (result of calling async def function)
 * @param request Request object to pass to the handler
 * @param callback Completion callback (called when handler finishes)
 * @param user_data User data passed to completion callback
 * @return Task handle, or NULL on error
 */
async_bridge_task_t* catzilla_execute_async_handler(
    PyObject* coroutine,
    PyObject* request,
    async_completion_callback_t callback,
    void* user_data
);

/**
 * Get the result from a completed async task
 * Should only be called after completion callback is invoked
 *
 * @param task The completed task
 * @return Python object result, or NULL if not completed/failed
 */
PyObject* catzilla_async_task_get_result(async_bridge_task_t* task);

/**
 * Get the exception from a failed async task
 *
 * @param task The failed task
 * @return Python exception object, or NULL if not failed
 */
PyObject* catzilla_async_task_get_exception(async_bridge_task_t* task);

/**
 * Get task execution duration in nanoseconds
 *
 * @param task The task
 * @return Duration in nanoseconds, or 0 if not completed
 */
uint64_t catzilla_async_task_get_duration(async_bridge_task_t* task);

/**
 * Get bridge statistics
 *
 * @param stats Output structure for statistics
 * @return 0 on success, -1 on error
 */
int catzilla_async_bridge_get_stats(async_bridge_stats_t* stats);

/**
 * Check if a Python object is a coroutine
 *
 * @param obj Python object to check
 * @return true if object is a coroutine, false otherwise
 */
bool catzilla_is_coroutine(PyObject* obj);

/**
 * Shutdown the async bridge system
 * Should be called during Catzilla shutdown
 */
void catzilla_async_bridge_shutdown(void);

#ifdef __cplusplus
}
#endif

#endif // CATZILLA_ASYNC_BRIDGE_H
