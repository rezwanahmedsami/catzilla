/*
 * Catzilla Async Bridge - C-Python AsyncIO Integration
 *
 * This module provides a safe bridge between libuv (C) and Python's asyncio,
 * enabling seamless execution of async Python handlers within Catzilla's
 * high-performance C event loop.
 *
 * Thread Safety: All operations are designed to be GIL-safe and race-condition free.
 * Performance: Minimal overhead bridge that preserves Catzilla's speed advantages.
 */

#include <Python.h>
#include <uv.h>
#include <stdbool.h>
#include <assert.h>
#include <inttypes.h>  // For PRIu64
#include <stdarg.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

// Platform-specific includes
#ifdef _WIN32
    #include <windows.h>
    #include <io.h>
#else
    #include <unistd.h>
    #include <pthread.h>
#endif

#include "async_bridge.h"

// For older Python versions that don't have PyCoroutine_Check
#ifndef PyCoroutine_Check
#define PyCoroutine_Check(obj) PyObject_TypeCheck(obj, &PyCoro_Type)
#endif

// Forward declarations
typedef struct async_bridge_task_s async_bridge_task_t;
typedef struct async_bridge_s async_bridge_t;

// Task states for thread-safe state management
typedef enum {
    ASYNC_TASK_PENDING = 0,
    ASYNC_TASK_RUNNING = 1,
    ASYNC_TASK_COMPLETED = 2,
    ASYNC_TASK_ERROR = 3,
    ASYNC_TASK_CANCELLED = 4
} async_task_state_t;

// Async task structure - represents one async handler execution
struct async_bridge_task_s {
    // libuv integration
    uv_async_t uv_async;           // libuv async handle for cross-thread communication
    uv_loop_t* uv_loop;           // Reference to main libuv loop

    // Python objects (all access must be GIL-protected)
    PyObject* py_coroutine;        // The async handler coroutine
    PyObject* py_future;           // asyncio.Future for result communication
    PyObject* py_request;          // Request object passed to handler
    PyObject* py_result;           // Handler result (Response object)
    PyObject* py_exception;        // Exception if handler failed

    // Thread safety and state management
    uv_mutex_t state_mutex;        // Protects state changes (cross-platform)
    async_task_state_t state;      // Current task state
    int ref_count;                 // Reference counting for safe cleanup

    // Timing and debugging
    uint64_t start_time;           // When task was created
    uint64_t completion_time;      // When task completed
    char debug_info[256];          // Debug information for troubleshooting

    // Callback context
    void* user_data;               // User-provided context
    void (*completion_callback)(async_bridge_task_t* task, void* user_data);
};

// Main async bridge structure - manages the asyncio event loop
struct async_bridge_s {
    // AsyncIO event loop management
    PyObject* asyncio_loop;        // Reference to asyncio event loop
    PyObject* asyncio_module;      // Reference to asyncio module
    PyObject* asyncio_future_class; // Reference to asyncio.Future class

    // libuv integration
    uv_loop_t* main_loop;          // Main libuv event loop
    uv_thread_t asyncio_thread;    // Dedicated thread for asyncio loop

    // Thread safety (using libuv cross-platform primitives)
    uv_mutex_t bridge_mutex;       // Protects bridge state
    uv_cond_t shutdown_cond;       // Condition variable for shutdown
    bool is_running;               // Bridge running state
    bool shutdown_requested;       // Shutdown flag
    bool loop_ready;               // Whether the asyncio loop is ready to accept work
    bool loop_initialization_complete; // Whether loop initialization has finished

    // Task management
    async_bridge_task_t** active_tasks;  // Array of active tasks
    size_t active_task_count;            // Number of active tasks
    size_t max_concurrent_tasks;         // Maximum concurrent tasks

    // Performance monitoring
    uint64_t total_tasks_executed;       // Total tasks processed
    uint64_t total_execution_time;       // Total execution time
    uint64_t peak_concurrent_tasks;      // Peak concurrent task count
};

// Global bridge instance (singleton for simplicity)
static async_bridge_t* g_async_bridge = NULL;
static uv_once_t bridge_init_once = UV_ONCE_INIT;

// ============================================================================
// FORWARD DECLARATIONS
// ============================================================================

// Bridge lifecycle
static void init_async_bridge_once(void);
static int async_bridge_init(async_bridge_t* bridge, uv_loop_t* main_loop);
static void async_bridge_cleanup(async_bridge_t* bridge);
static void asyncio_thread_main(void* arg);

// Task management
static async_bridge_task_t* async_task_create(PyObject* coroutine, PyObject* request);
static void async_task_destroy(async_bridge_task_t* task);
static void async_task_ref(async_bridge_task_t* task);
static void async_task_unref(async_bridge_task_t* task);

// libuv callbacks
static void on_async_completion(uv_async_t* handle);
static void on_task_timeout(uv_timer_t* timer);
static void on_async_handle_closed(uv_handle_t* handle);
static PyObject* on_coroutine_done(PyObject* self, PyObject* future);
static PyObject* start_coroutine_on_loop(PyObject* self, PyObject* ignored);

// Python/asyncio integration
static PyObject* execute_coroutine_in_asyncio(PyObject* coroutine);
static void schedule_coroutine_completion(async_bridge_task_t* task);

// Error handling and logging
static void log_async_error(const char* format, ...);
static const char* task_state_to_string(async_task_state_t state);

static PyMethodDef coroutine_done_callback_method = {
    "_catzilla_async_done",
    on_coroutine_done,
    METH_O,
    NULL,
};

static PyMethodDef coroutine_start_callback_method = {
    "_catzilla_async_start",
    (PyCFunction)start_coroutine_on_loop,
    METH_NOARGS,
    NULL,
};

// ============================================================================
// PUBLIC API IMPLEMENTATION
// ============================================================================

/**
 * Initialize the async bridge system
 * This must be called once during Catzilla startup
 */
int catzilla_async_bridge_init(uv_loop_t* main_loop) {
    if (g_async_bridge != NULL) {
        return 0; // Already initialized
    }

    uv_once(&bridge_init_once, init_async_bridge_once);

    if (g_async_bridge == NULL) {
        log_async_error("Failed to initialize async bridge");
        return -1;
    }

    return async_bridge_init(g_async_bridge, main_loop);
}

/**
 * Execute an async Python handler
 * This is the main entry point for async handler execution
 *
 * @param coroutine Python coroutine object (async def handler)
 * @param request Request object to pass to the handler
 * @param callback Completion callback (called when handler finishes)
 * @param user_data User data passed to completion callback
 * @return async_bridge_task_t* Task handle, or NULL on error
 */
async_bridge_task_t* catzilla_execute_async_handler(
    PyObject* coroutine,
    PyObject* request,
    void (*callback)(async_bridge_task_t* task, void* user_data),
    void* user_data
) {
    if (!g_async_bridge || !g_async_bridge->is_running) {
        log_async_error("Async bridge not initialized or not running");
        return NULL;
    }

    if (!coroutine || !PyCoroutine_Check(coroutine)) {
        log_async_error("Invalid coroutine object");
        return NULL;
    }

    // Create new task
    async_bridge_task_t* task = async_task_create(coroutine, request);
    if (!task) {
        log_async_error("Failed to create async task");
        return NULL;
    }

    // Set callback
    task->completion_callback = callback;
    task->user_data = user_data;

    // Check concurrent task limit
    uv_mutex_lock(&g_async_bridge->bridge_mutex);
    if (g_async_bridge->active_task_count >= g_async_bridge->max_concurrent_tasks) {
        uv_mutex_unlock(&g_async_bridge->bridge_mutex);
        log_async_error("Maximum concurrent tasks exceeded");
        async_task_destroy(task);
        return NULL;
    }

    // Add to active tasks
    g_async_bridge->active_tasks[g_async_bridge->active_task_count] = task;
    g_async_bridge->active_task_count++;

    // Update peak concurrent tasks
    if (g_async_bridge->active_task_count > g_async_bridge->peak_concurrent_tasks) {
        g_async_bridge->peak_concurrent_tasks = g_async_bridge->active_task_count;
    }

    uv_mutex_unlock(&g_async_bridge->bridge_mutex);

    // Schedule coroutine execution in asyncio loop
    schedule_coroutine_completion(task);

    return task;
}

/**
 * Get the result from a completed async task
 * This should only be called after the completion callback is invoked
 */
PyObject* catzilla_async_task_get_result(async_bridge_task_t* task) {
    if (!task) {
        return NULL;
    }

    uv_mutex_lock(&task->state_mutex);

    if (task->state != ASYNC_TASK_COMPLETED) {
        uv_mutex_unlock(&task->state_mutex);
        return NULL;
    }

    PyObject* result = task->py_result;
    Py_XINCREF(result); // Caller owns the reference

    uv_mutex_unlock(&task->state_mutex);

    return result;
}

/**
 * Get the exception from a failed async task
 */
PyObject* catzilla_async_task_get_exception(async_bridge_task_t* task) {
    if (!task) {
        return NULL;
    }

    uv_mutex_lock(&task->state_mutex);

    if (task->state != ASYNC_TASK_ERROR) {
        uv_mutex_unlock(&task->state_mutex);
        return NULL;
    }

    PyObject* exception = task->py_exception;
    Py_XINCREF(exception); // Caller owns the reference

    uv_mutex_unlock(&task->state_mutex);

    return exception;
}

/**
 * Get task execution statistics
 */
uint64_t catzilla_async_task_get_duration(async_bridge_task_t* task) {
    if (!task) {
        return 0;
    }

    uv_mutex_lock(&task->state_mutex);
    uint64_t duration = task->completion_time - task->start_time;
    uv_mutex_unlock(&task->state_mutex);

    return duration;
}

/**
 * Cleanup async bridge on shutdown
 */
void catzilla_async_bridge_shutdown(void) {
    if (!g_async_bridge) {
        return;
    }

    uv_mutex_lock(&g_async_bridge->bridge_mutex);
    g_async_bridge->shutdown_requested = true;
    uv_mutex_unlock(&g_async_bridge->bridge_mutex);

    PyGILState_STATE gstate = PyGILState_Ensure();
    if (g_async_bridge->asyncio_loop) {
        PyObject* stop_method = PyObject_GetAttrString(g_async_bridge->asyncio_loop, "stop");
        PyObject* call_soon_threadsafe = PyObject_GetAttrString(
            g_async_bridge->asyncio_loop,
            "call_soon_threadsafe"
        );

        if (stop_method && call_soon_threadsafe) {
            PyObject* stop_result = PyObject_CallFunctionObjArgs(
                call_soon_threadsafe,
                stop_method,
                NULL
            );
            Py_XDECREF(stop_result);
        } else {
            PyErr_Clear();
        }

        Py_XDECREF(stop_method);
        Py_XDECREF(call_soon_threadsafe);
    }
    PyGILState_Release(gstate);

    // Wait for asyncio thread to shutdown
    uv_thread_join(&g_async_bridge->asyncio_thread);

    async_bridge_cleanup(g_async_bridge);
    free(g_async_bridge);
    g_async_bridge = NULL;
}

// ============================================================================
// INTERNAL IMPLEMENTATION
// ============================================================================

static void init_async_bridge_once(void) {
    g_async_bridge = calloc(1, sizeof(async_bridge_t));
    if (!g_async_bridge) {
        log_async_error("Failed to allocate async bridge");
        return;
    }

    // Initialize mutex (libuv cross-platform)
    if (uv_mutex_init(&g_async_bridge->bridge_mutex) != 0) {
        free(g_async_bridge);
        g_async_bridge = NULL;
        log_async_error("Failed to initialize bridge mutex");
        return;
    }

    // Initialize condition variable (libuv cross-platform)
    if (uv_cond_init(&g_async_bridge->shutdown_cond) != 0) {
        uv_mutex_destroy(&g_async_bridge->bridge_mutex);
        free(g_async_bridge);
        g_async_bridge = NULL;
        log_async_error("Failed to initialize shutdown condition");
        return;
    }

    // Set defaults
    g_async_bridge->max_concurrent_tasks = 1000; // Configurable limit
    g_async_bridge->is_running = false;
    g_async_bridge->shutdown_requested = false;
    g_async_bridge->loop_ready = false;
    g_async_bridge->loop_initialization_complete = false;
}

static int async_bridge_init(async_bridge_t* bridge, uv_loop_t* main_loop) {
    assert(bridge != NULL);
    assert(main_loop != NULL);

    // Store main loop reference
    bridge->main_loop = main_loop;

    // Initialize Python/asyncio references (must be called with GIL held)
    PyGILState_STATE gstate = PyGILState_Ensure();

    // Import asyncio module
    bridge->asyncio_module = PyImport_ImportModule("asyncio");
    if (!bridge->asyncio_module) {
        PyGILState_Release(gstate);
        log_async_error("Failed to import asyncio module");
        return -1;
    }

    // Get Future class
    bridge->asyncio_future_class = PyObject_GetAttrString(bridge->asyncio_module, "Future");
    if (!bridge->asyncio_future_class) {
        PyGILState_Release(gstate);
        log_async_error("Failed to get asyncio.Future class");
        return -1;
    }

    PyGILState_Release(gstate);

    // Allocate active tasks array
    bridge->active_tasks = calloc(bridge->max_concurrent_tasks, sizeof(async_bridge_task_t*));
    if (!bridge->active_tasks) {
        log_async_error("Failed to allocate active tasks array");
        return -1;
    }

    // Start asyncio thread (libuv cross-platform)
    if (uv_thread_create(&bridge->asyncio_thread, asyncio_thread_main, bridge) != 0) {
        log_async_error("Failed to create asyncio thread");
        return -1;
    }

    bridge->is_running = true;

    return 0;
}

static void async_bridge_cleanup(async_bridge_t* bridge) {
    if (!bridge) return;

    // Acquire GIL for cleanup
    PyGILState_STATE gstate = PyGILState_Ensure();

    // Cleanup Python objects
    Py_XDECREF(bridge->asyncio_module);
    Py_XDECREF(bridge->asyncio_loop);
    Py_XDECREF(bridge->asyncio_future_class);

    // Cleanup pending tasks
    // Note: In production, we'd walk the pending tasks and clean them up
    if (bridge->active_tasks) {
        free(bridge->active_tasks);
        bridge->active_tasks = NULL;
    }

    // Destroy synchronization primitives
    uv_mutex_destroy(&bridge->bridge_mutex);
    uv_cond_destroy(&bridge->shutdown_cond);

    PyGILState_Release(gstate);
}

static void asyncio_thread_main(void* arg) {
    async_bridge_t* bridge = (async_bridge_t*)arg;
    assert(bridge != NULL);

    // Acquire GIL for this thread
    PyGILState_STATE gstate = PyGILState_Ensure();

    PyObject* new_loop_func = PyObject_GetAttrString(bridge->asyncio_module, "new_event_loop");
    if (new_loop_func) {
        bridge->asyncio_loop = PyObject_CallObject(new_loop_func, NULL);
        Py_DECREF(new_loop_func);
    }

    if (!bridge->asyncio_loop) {
        uv_mutex_lock(&bridge->bridge_mutex);
        bridge->loop_ready = false;
        bridge->loop_initialization_complete = true;
        uv_cond_signal(&bridge->shutdown_cond);
        uv_mutex_unlock(&bridge->bridge_mutex);
        PyGILState_Release(gstate);
        return;
    }

    // Set event loop for this thread
    PyObject* set_event_loop_func = PyObject_GetAttrString(bridge->asyncio_module, "set_event_loop");
    if (set_event_loop_func) {
        PyObject* args = PyTuple_Pack(1, bridge->asyncio_loop);
        PyObject_CallObject(set_event_loop_func, args);
        Py_DECREF(args);
        Py_DECREF(set_event_loop_func);
    }

    uv_mutex_lock(&bridge->bridge_mutex);
    bridge->loop_ready = true;
    bridge->loop_initialization_complete = true;
    uv_cond_signal(&bridge->shutdown_cond);
    uv_mutex_unlock(&bridge->bridge_mutex);

    // Run event loop until shutdown
    PyObject* run_forever_func = PyObject_GetAttrString(bridge->asyncio_loop, "run_forever");
    if (run_forever_func) {
        PyObject_CallObject(run_forever_func, NULL);
        Py_DECREF(run_forever_func);
    }

    PyGILState_Release(gstate);
}

static async_bridge_task_t* async_task_create(PyObject* coroutine, PyObject* request) {
    async_bridge_task_t* task = calloc(1, sizeof(async_bridge_task_t));
    if (!task) {
        return NULL;
    }

    // Initialize mutex (libuv cross-platform)
    if (uv_mutex_init(&task->state_mutex) != 0) {
        free(task);
        return NULL;
    }

    // Initialize libuv async handle
    task->uv_loop = g_async_bridge->main_loop;
    uv_async_init(task->uv_loop, &task->uv_async, on_async_completion);
    task->uv_async.data = task; // Store task reference in handle

    // Store Python objects (increment references)
    task->py_coroutine = coroutine;
    Py_INCREF(coroutine);

    if (request) {
        task->py_request = request;
        Py_INCREF(request);
    }

    // Initialize state
    task->state = ASYNC_TASK_PENDING;
    task->ref_count = 1; // Initial reference
    task->start_time = uv_hrtime(); // High-resolution timestamp

    // Debug info
    snprintf(task->debug_info, sizeof(task->debug_info),
             "Task created at %" PRIu64, task->start_time);

    return task;
}

static void async_task_destroy(async_bridge_task_t* task) {
    if (!task) {
        return;
    }

    if (!uv_is_closing((uv_handle_t*)&task->uv_async)) {
        uv_close((uv_handle_t*)&task->uv_async, on_async_handle_closed);
    }
}

static void on_async_handle_closed(uv_handle_t* handle) {
    async_bridge_task_t* task = (async_bridge_task_t*)handle->data;
    if (!task) {
        return;
    }

    PyGILState_STATE gstate = PyGILState_Ensure();
    Py_XDECREF(task->py_coroutine);
    Py_XDECREF(task->py_future);
    Py_XDECREF(task->py_request);
    Py_XDECREF(task->py_result);
    Py_XDECREF(task->py_exception);
    PyGILState_Release(gstate);

    uv_mutex_destroy(&task->state_mutex);
    free(task);
}

static void async_task_ref(async_bridge_task_t* task) {
    if (!task) {
        return;
    }

    uv_mutex_lock(&task->state_mutex);
    task->ref_count++;
    uv_mutex_unlock(&task->state_mutex);
}

static void async_task_unref(async_bridge_task_t* task) {
    if (!task) {
        return;
    }

    uv_mutex_lock(&task->state_mutex);
    task->ref_count--;
    int should_destroy = (task->ref_count == 0);
    uv_mutex_unlock(&task->state_mutex);

    if (should_destroy) {
        async_task_destroy(task);
    }
}

static void on_async_completion(uv_async_t* handle) {
    async_bridge_task_t* task = (async_bridge_task_t*)handle->data;
    assert(task != NULL);

    // Call completion callback if set
    if (task->completion_callback) {
        task->completion_callback(task, task->user_data);
    }

    // Remove from active tasks
    uv_mutex_lock(&g_async_bridge->bridge_mutex);
    for (size_t i = 0; i < g_async_bridge->active_task_count; i++) {
        if (g_async_bridge->active_tasks[i] == task) {
            // Shift remaining tasks
            memmove(&g_async_bridge->active_tasks[i],
                    &g_async_bridge->active_tasks[i + 1],
                    (g_async_bridge->active_task_count - i - 1) * sizeof(async_bridge_task_t*));
            g_async_bridge->active_task_count--;
            break;
        }
    }
    uv_mutex_unlock(&g_async_bridge->bridge_mutex);

    // Release reference (may destroy task)
    async_task_unref(task);
}

static PyObject* on_coroutine_done(PyObject* self, PyObject* future) {
    async_bridge_task_t* task = (async_bridge_task_t*)PyCapsule_GetPointer(
        self,
        "catzilla.async_task"
    );
    if (!task) {
        PyErr_Clear();
        Py_RETURN_NONE;
    }

    PyObject* result_method = PyObject_GetAttrString(future, "result");
    PyObject* result = NULL;
    PyObject* exc_type = NULL;
    PyObject* exc_value = NULL;
    PyObject* exc_traceback = NULL;

    if (result_method) {
        result = PyObject_CallObject(result_method, NULL);
        Py_DECREF(result_method);
    }

    uv_mutex_lock(&task->state_mutex);

    if (result) {
        task->py_result = result;
        task->state = ASYNC_TASK_COMPLETED;
    } else {
        PyErr_Fetch(&exc_type, &exc_value, &exc_traceback);
        PyErr_NormalizeException(&exc_type, &exc_value, &exc_traceback);
        Py_XDECREF(exc_type);
        Py_XDECREF(exc_traceback);

        if (!exc_value) {
            exc_value = PyUnicode_FromString("Async handler failed");
        }

        task->py_exception = exc_value;
        task->state = ASYNC_TASK_ERROR;
    }

    task->completion_time = uv_hrtime();
    uv_mutex_unlock(&task->state_mutex);

    uv_async_send(&task->uv_async);
    async_task_unref(task);

    Py_RETURN_NONE;
}

static PyObject* start_coroutine_on_loop(PyObject* self, PyObject* ignored) {
    async_bridge_task_t* task = (async_bridge_task_t*)PyCapsule_GetPointer(
        self,
        "catzilla.async_task"
    );
    if (!task) {
        PyErr_Clear();
        Py_RETURN_NONE;
    }

    PyObject* created_task = PyObject_CallMethod(g_async_bridge->asyncio_loop, "create_task", "O", task->py_coroutine);
    if (!created_task) {
        goto start_error;
    }

    task->py_future = created_task;

    PyObject* task_capsule = PyCapsule_New(task, "catzilla.async_task", NULL);
    if (!task_capsule) {
        goto start_error;
    }

    PyObject* done_callback = PyCFunction_NewEx(
        &coroutine_done_callback_method,
        task_capsule,
        NULL
    );
    Py_DECREF(task_capsule);
    if (!done_callback) {
        goto start_error;
    }

    PyObject* add_done_callback = PyObject_GetAttrString(created_task, "add_done_callback");
    if (!add_done_callback) {
        Py_DECREF(done_callback);
        goto start_error;
    }

    async_task_ref(task);
    PyObject* add_result = PyObject_CallFunctionObjArgs(add_done_callback, done_callback, NULL);
    Py_DECREF(add_done_callback);
    Py_DECREF(done_callback);
    if (!add_result) {
        async_task_unref(task);
        goto start_error;
    }
    Py_DECREF(add_result);

    uv_mutex_lock(&task->state_mutex);
    task->state = ASYNC_TASK_RUNNING;
    uv_mutex_unlock(&task->state_mutex);

    Py_RETURN_NONE;

start_error:
    if (PyErr_Occurred()) {
        PyObject* exc_type = NULL;
        PyObject* exc_value = NULL;
        PyObject* exc_traceback = NULL;
        PyErr_Fetch(&exc_type, &exc_value, &exc_traceback);
        PyErr_NormalizeException(&exc_type, &exc_value, &exc_traceback);
        Py_XDECREF(exc_type);
        Py_XDECREF(exc_traceback);

        uv_mutex_lock(&task->state_mutex);
        task->py_exception = exc_value ? exc_value : PyUnicode_FromString("Failed to start async handler");
        task->state = ASYNC_TASK_ERROR;
        task->completion_time = uv_hrtime();
        uv_mutex_unlock(&task->state_mutex);
    }

    uv_async_send(&task->uv_async);
    Py_RETURN_NONE;
}

static void schedule_coroutine_completion(async_bridge_task_t* task) {
    PyGILState_STATE gstate = PyGILState_Ensure();

    uv_mutex_lock(&g_async_bridge->bridge_mutex);
    bool loop_ready = g_async_bridge->loop_ready;
    uv_mutex_unlock(&g_async_bridge->bridge_mutex);

    if (!loop_ready || !g_async_bridge->asyncio_loop) {
        PyErr_SetString(PyExc_RuntimeError, "Asyncio bridge loop is not ready");
        goto schedule_error;
    }

    PyObject* call_soon_threadsafe = PyObject_GetAttrString(
        g_async_bridge->asyncio_loop,
        "call_soon_threadsafe"
    );
    if (!call_soon_threadsafe) {
        goto schedule_error;
    }

    PyObject* task_capsule = PyCapsule_New(task, "catzilla.async_task", NULL);
    if (!task_capsule) {
        Py_DECREF(call_soon_threadsafe);
        goto schedule_error;
    }

    PyObject* start_callback = PyCFunction_NewEx(
        &coroutine_start_callback_method,
        task_capsule,
        NULL
    );
    Py_DECREF(task_capsule);
    if (!start_callback) {
        Py_DECREF(call_soon_threadsafe);
        goto schedule_error;
    }

    PyObject* schedule_result = PyObject_CallFunctionObjArgs(
        call_soon_threadsafe,
        start_callback,
        NULL
    );
    Py_DECREF(call_soon_threadsafe);
    Py_DECREF(start_callback);
    if (!schedule_result) {
        goto schedule_error;
    }
    Py_DECREF(schedule_result);

    PyGILState_Release(gstate);
    return;

schedule_error:
    if (PyErr_Occurred()) {
        PyObject* exc_type = NULL;
        PyObject* exc_value = NULL;
        PyObject* exc_traceback = NULL;
        PyErr_Fetch(&exc_type, &exc_value, &exc_traceback);
        PyErr_NormalizeException(&exc_type, &exc_value, &exc_traceback);
        Py_XDECREF(exc_type);
        Py_XDECREF(exc_traceback);

        uv_mutex_lock(&task->state_mutex);
        task->py_exception = exc_value ? exc_value : PyUnicode_FromString("Failed to schedule async handler");
        task->state = ASYNC_TASK_ERROR;
        task->completion_time = uv_hrtime();
        uv_mutex_unlock(&task->state_mutex);
    }

    PyGILState_Release(gstate);
    uv_async_send(&task->uv_async);
}

static void log_async_error(const char* format, ...) {
    va_list args;
    va_start(args, format);
    fprintf(stderr, "[CATZILLA ASYNC ERROR] ");
    vfprintf(stderr, format, args);
    fprintf(stderr, "\n");
    va_end(args);
}

static const char* task_state_to_string(async_task_state_t state) {
    switch (state) {
        case ASYNC_TASK_PENDING: return "PENDING";
        case ASYNC_TASK_RUNNING: return "RUNNING";
        case ASYNC_TASK_COMPLETED: return "COMPLETED";
        case ASYNC_TASK_ERROR: return "ERROR";
        case ASYNC_TASK_CANCELLED: return "CANCELLED";
        default: return "UNKNOWN";
    }
}

// Additional safety and cleanup functions would be implemented here...

/**
 * Cleanup the async bridge system.
 * Should be called during module shutdown.
 */
void catzilla_async_bridge_cleanup(void) {
    if (g_async_bridge) {
        catzilla_async_bridge_shutdown();
    }
}
