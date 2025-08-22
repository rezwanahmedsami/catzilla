#define PY_SSIZE_T_CLEAN

// Platform compatibility
#include "../core/platform_compat.h"

// System headers
#include <stdint.h>           // For uintptr_t

// Python headers
#include <Python.h>

// Third-party headers
#include <uv.h>               // For uv_stream_t

// Project headers
#include "../core/server.h"           // Provides catzilla_server_t, catzilla_server_init, etc.
#include "../core/logging.h"
#include "../core/router.h"           // Provides catzilla_router_t, catzilla_router_match, etc.
#include "../core/memory.h"           // Provides memory system functions
#include "../core/validation.h"       // Provides ultra-fast validation engine
#include "../core/static_server.h"    // Provides static file server functionality
#include "../core/windows_compat.h"   // Windows compatibility
#include <stdio.h>
#include <string.h>
#ifndef _WIN32
#include <strings.h>          // For strcasecmp on POSIX systems
#endif
#include <stdlib.h>           // For malloc, free
#include <math.h>             // For HUGE_VAL
#ifdef _WIN32
#include <process.h>          // For _getpid() on Windows
#define getpid _getpid
#else
#include <unistd.h>           // For getpid() on Unix
#endif
#include <time.h>             // For time()
#include <yyjson.h>
#include "../core/cache_engine.h"

// Forward declarations for submodules
PyObject* init_streaming(void);

// Include async bridge for hybrid sync/async execution
#include "async_bridge.h"

// Structure to hold Python callback and routing table
typedef struct {
    PyObject *callback;
    PyObject *routes;
} PyRouteData;

// ============================================================================
// MIDDLEWARE REGISTRATION SYSTEM
// ============================================================================

// Global middleware registry
static PyObject *g_middleware_registry = NULL;  // Dict: middleware_id -> PyObject*
static int g_next_middleware_id = 1;

// Global router for module-level functions
static catzilla_router_t global_router;
static bool global_router_initialized = false;

// Middleware execution context
typedef struct {
    PyObject *request;
    PyObject *response;
    int middleware_id;
} middleware_context_t;

// Initialize middleware registry
static int init_middleware_registry(void) {
    if (!g_middleware_registry) {
        g_middleware_registry = PyDict_New();
        if (!g_middleware_registry) {
            return -1;
        }
    }
    return 0;
}

// Cleanup middleware registry
static void cleanup_middleware_registry(void) {
    // Check if Python is still available and GIL can be acquired
    if (Py_IsInitialized()) {
        PyGILState_STATE gstate = PyGILState_Ensure();

        // Safely clean up Python objects
        if (g_middleware_registry) {
            PyDict_Clear(g_middleware_registry);
            Py_CLEAR(g_middleware_registry);
        }

        PyGILState_Release(gstate);
    }

    // Reset static variables safely
    g_middleware_registry = NULL;
    g_next_middleware_id = 1;
}

// Safe cleanup for module exit
static void safe_module_cleanup(void) {
    // Only do cleanup if Python interpreter is still active
    if (Py_IsInitialized()) {
        cleanup_middleware_registry();

        // Cleanup global router if it was initialized
        if (global_router_initialized) {
            catzilla_router_cleanup(&global_router);
            global_router_initialized = false;
        }

        // Cleanup async bridge system
        catzilla_async_bridge_shutdown();
    }
}

// Register a Python middleware function and return its ID
static PyObject* register_middleware_function(PyObject *self, PyObject *args) {
    PyObject *middleware_func;

    if (!PyArg_ParseTuple(args, "O", &middleware_func)) {
        return NULL;
    }

    if (!PyCallable_Check(middleware_func)) {
        PyErr_SetString(PyExc_TypeError, "Middleware must be callable");
        return NULL;
    }

    // Initialize registry if needed
    if (init_middleware_registry() < 0) {
        return NULL;
    }

    // Get next middleware ID
    int middleware_id = g_next_middleware_id++;
    PyObject *id_obj = PyLong_FromLong(middleware_id);
    if (!id_obj) {
        return NULL;
    }

    // Store middleware function in registry
    Py_INCREF(middleware_func);
    if (PyDict_SetItem(g_middleware_registry, id_obj, middleware_func) < 0) {
        Py_DECREF(middleware_func);
        Py_DECREF(id_obj);
        return NULL;
    }

    // Return the middleware ID
    return id_obj;
}

// Execute a middleware function by ID
static PyObject* execute_middleware_by_id(PyObject *self, PyObject *args) {
    int middleware_id;
    PyObject *request, *response = Py_None;

    if (!PyArg_ParseTuple(args, "iO|O", &middleware_id, &request, &response)) {
        return NULL;
    }

    if (!g_middleware_registry) {
        PyErr_SetString(PyExc_RuntimeError, "Middleware registry not initialized");
        return NULL;
    }

    // Get middleware function from registry
    PyObject *id_obj = PyLong_FromLong(middleware_id);
    if (!id_obj) {
        return NULL;
    }

    PyObject *middleware_func = PyDict_GetItem(g_middleware_registry, id_obj);
    Py_DECREF(id_obj);

    if (!middleware_func) {
        PyErr_Format(PyExc_KeyError, "Middleware ID %d not found", middleware_id);
        return NULL;
    }

    // Call the middleware function
    PyObject *args_tuple;
    if (response == Py_None) {
        // Pre-route middleware: middleware(request)
        args_tuple = PyTuple_Pack(1, request);
    } else {
        // Post-route middleware: middleware(request, response)
        args_tuple = PyTuple_Pack(2, request, response);
    }

    if (!args_tuple) {
        return NULL;
    }

    PyObject *result = PyObject_CallObject(middleware_func, args_tuple);
    Py_DECREF(args_tuple);

    return result;
}

// Python middleware execution bridge for C middleware system
// This function is called by the C middleware system to execute Python middleware
static int execute_python_middleware_bridge(int middleware_id, void* request_ctx, void* response_ctx) {
    // Ensure we have the GIL
    PyGILState_STATE gstate = PyGILState_Ensure();

    int result = 0;  // Default: continue

    if (!g_middleware_registry) {
        PyGILState_Release(gstate);
        return -1;  // Error
    }

    // Get middleware function from registry
    PyObject *id_obj = PyLong_FromLong(middleware_id);
    if (!id_obj) {
        PyGILState_Release(gstate);
        return -1;
    }

    PyObject *middleware_func = PyDict_GetItem(g_middleware_registry, id_obj);
    Py_DECREF(id_obj);

    if (!middleware_func) {
        PyGILState_Release(gstate);
        return -1;  // Error: middleware not found
    }

    // Create Python request object from context
    // For now, create a minimal request object - this would need to be enhanced
    // to properly convert the C request context to a Python Request object
    PyObject *request = PyCapsule_New(request_ctx, "catzilla.request", NULL);
    if (!request) {
        PyGILState_Release(gstate);
        return -1;
    }

    // Call the middleware function with just the request for now
    PyObject *args_tuple = PyTuple_Pack(1, request);
    if (!args_tuple) {
        Py_DECREF(request);
        PyGILState_Release(gstate);
        return -1;
    }

    PyObject *middleware_result = PyObject_CallObject(middleware_func, args_tuple);
    Py_DECREF(args_tuple);
    Py_DECREF(request);

    if (middleware_result) {
        // Check the result type
        if (middleware_result == Py_None) {
            result = 0;  // Continue processing
        } else {
            // If middleware returns a Response object, stop processing
            result = 1;  // Stop processing (short-circuit)
        }
        Py_DECREF(middleware_result);
    } else {
        // Exception occurred
        PyErr_Clear();  // Clear the error for now
        result = -1;    // Error
    }

    PyGILState_Release(gstate);
    return result;
}

// Set the Python middleware execution bridge for the C middleware system
static PyObject* set_python_middleware_bridge(PyObject *self, PyObject *args) {
    // This function would register the execute_python_middleware_bridge function
    // with the C middleware system so it can call Python middleware functions

    // For now, just return success - the actual integration would depend on
    // the C middleware system API
    Py_RETURN_NONE;
}

// Convert middleware function list to middleware ID list
static PyObject* convert_middleware_to_ids(PyObject *self, PyObject *args) {
    PyObject *middleware_list;

    if (!PyArg_ParseTuple(args, "O", &middleware_list)) {
        return NULL;
    }

    if (!PyList_Check(middleware_list)) {
        PyErr_SetString(PyExc_TypeError, "Expected list of middleware functions");
        return NULL;
    }

    Py_ssize_t count = PyList_Size(middleware_list);
    PyObject *id_list = PyList_New(count);
    if (!id_list) {
        return NULL;
    }        for (Py_ssize_t i = 0; i < count; i++) {
            PyObject *middleware_func = PyList_GetItem(middleware_list, i);

            if (!PyCallable_Check(middleware_func)) {
                PyErr_Format(PyExc_TypeError, "Middleware item %zd is not callable", i);
                Py_DECREF(id_list);
                return NULL;
            }

            // Register the middleware and get its ID
            PyObject *register_args = PyTuple_Pack(1, middleware_func);
            if (!register_args) {
                Py_DECREF(id_list);
                return NULL;
            }

            PyObject *middleware_id = register_middleware_function(self, register_args);
            Py_DECREF(register_args);

            if (!middleware_id) {
                Py_DECREF(id_list);
                return NULL;
            }

            PyList_SET_ITEM(id_list, i, middleware_id);  // Steals reference
        }

    return id_list;
}

// Python CatzillaServer object
typedef struct {
    PyObject_HEAD
    catzilla_server_t server;
    PyRouteData *route_data;
    catzilla_router_t py_router;  // Python-accessible C router
} CatzillaServerObject;

// Python Validator object
typedef struct {
    PyObject_HEAD
    validator_t *validator;
} CatzillaValidatorObject;

// Python Model object
typedef struct {
    PyObject_HEAD
    model_spec_t *model;
    validation_context_t *context;
} CatzillaModelObject;

// Python Cache object
typedef struct {
    PyObject_HEAD
    catzilla_cache_t *cache;
} CatzillaCacheObject;

// Python CacheResult object
typedef struct {
    PyObject_HEAD
    PyObject *data;
    int hit;
} CatzillaCacheResultObject;

// Forward declarations for type objects
static PyTypeObject CatzillaValidatorType;
static PyTypeObject CatzillaModelType;
static PyTypeObject CatzillaServerType;
static PyTypeObject CatzillaCacheType;
static PyTypeObject CatzillaCacheResultType;

// Deallocate
static void CatzillaServer_dealloc(CatzillaServerObject *self)
{
    if (self->route_data) {
        Py_XDECREF(self->route_data->callback);
        Py_XDECREF(self->route_data->routes);
        catzilla_cache_free(self->route_data);
    }
    catzilla_router_cleanup(&self->py_router);
    catzilla_server_cleanup(&self->server);
    Py_TYPE(self)->tp_free((PyObject*)self);
}

// __new__
static PyObject* CatzillaServer_new(PyTypeObject *type, PyObject *args, PyObject *kwds)
{
    CatzillaServerObject *self = (CatzillaServerObject*)type->tp_alloc(type, 0);
    if (self) {
        memset(&self->server, 0, sizeof(self->server));
        memset(&self->py_router, 0, sizeof(self->py_router));
        self->route_data = NULL;
    }
    return (PyObject*)self;
}

// __init__
static int CatzillaServer_init(CatzillaServerObject *self, PyObject *args, PyObject *kwds)
{
    // Ensure the GIL and interpreter are initialized
    if (!Py_IsInitialized()) {
        Py_Initialize();
    }

    // Allocate routing data using cache arena (persists across requests)
    self->route_data = catzilla_cache_alloc(sizeof(PyRouteData));
    if (!self->route_data) {
        PyErr_NoMemory();
        return -1;
    }
    self->route_data->routes = PyDict_New();
    if (!self->route_data->routes) {
        free(self->route_data);
        return -1;
    }
    self->route_data->callback = NULL;

    // Initialize the C server
    if (catzilla_server_init(&self->server) != 0) {
        PyErr_SetString(PyExc_RuntimeError, "Server initialization failed");
        Py_CLEAR(self->route_data->routes);
        free(self->route_data);
        return -1;
    }

    // Initialize the Python-accessible C router
    if (catzilla_router_init(&self->py_router) != 0) {
        PyErr_SetString(PyExc_RuntimeError, "Router initialization failed");
        catzilla_server_cleanup(&self->server);
        Py_CLEAR(self->route_data->routes);
        free(self->route_data);
        return -1;
    }
    return 0;
}

// listen(port, host="0.0.0.0")
static PyObject* CatzillaServer_listen(CatzillaServerObject *self, PyObject *args)
{
    const char *host = "0.0.0.0";
    int port;
    if (!PyArg_ParseTuple(args, "i|s", &port, &host))
        return NULL;


    int rc = catzilla_server_listen(&self->server, host, port);
    if (rc != 0) {
        PyErr_Format(PyExc_RuntimeError, "Listen error: %s", uv_strerror(rc));
        return NULL;
    }
    Py_RETURN_NONE;
}

// add_route(method, path, handler)
static PyObject* CatzillaServer_add_route(CatzillaServerObject *self, PyObject *args)
{
    const char *method, *path;
    PyObject *handler;
    if (!PyArg_ParseTuple(args, "ssO", &method, &path, &handler))
        return NULL;
    if (!PyCallable_Check(handler)) {
        PyErr_SetString(PyExc_TypeError, "Handler must be callable");
        return NULL;
    }

    // Replace previous callback
    Py_XINCREF(handler);
    Py_XDECREF(self->route_data->callback);
    self->route_data->callback = handler;

    // Store in routes dict
    if (PyDict_SetItemString(self->route_data->routes, path, handler) < 0)
        return NULL;

    // CRITICAL FIX: Register the Python callback with the C server
    catzilla_server_set_request_callback(&self->server, self->route_data->callback);

    // Register route with C core - use universal Python handler
    if (catzilla_server_add_route(&self->server, method, path, catzilla_python_route_handler, (void*)handler) != 0) {
        PyErr_SetString(PyExc_RuntimeError, "Failed to add route");
        return NULL;
    }
    Py_RETURN_NONE;
}

// stop()
static PyObject* CatzillaServer_stop(CatzillaServerObject *self, PyObject *Py_UNUSED(ignored))
{
    catzilla_server_stop(&self->server);
    Py_RETURN_NONE;
}

// match_route(method, path) - Use C router for fast route matching
static PyObject* CatzillaServer_match_route(CatzillaServerObject *self, PyObject *args)
{
    const char *method, *path;
    if (!PyArg_ParseTuple(args, "ss", &method, &path))
        return NULL;

    catzilla_route_match_t match;
    int result = catzilla_router_match(&self->py_router, method, path, &match);

    // Create Python dict with match results
    PyObject *match_dict = PyDict_New();
    if (!match_dict) {
        return NULL;
    }

    PyDict_SetItemString(match_dict, "matched", PyBool_FromLong(result == 0));
    PyDict_SetItemString(match_dict, "status_code", PyLong_FromLong(match.status_code));

    if (result == 0 && match.route) {
        PyDict_SetItemString(match_dict, "method", PyUnicode_FromString(match.route->method));
        PyDict_SetItemString(match_dict, "path", PyUnicode_FromString(match.route->path));
        PyDict_SetItemString(match_dict, "route_id", PyLong_FromLong(match.route->id));

        // Add path parameters
        PyObject *params_dict = PyDict_New();
        for (int i = 0; i < match.param_count; i++) {
            PyDict_SetItemString(params_dict, match.params[i].name,
                                PyUnicode_FromString(match.params[i].value));
        }
        PyDict_SetItemString(match_dict, "path_params", params_dict);
    } else {
        PyDict_SetItemString(match_dict, "path_params", PyDict_New());
    }

    if (match.has_allowed_methods) {
        PyDict_SetItemString(match_dict, "allowed_methods",
                            PyUnicode_FromString(match.allowed_methods));
    } else {
        Py_INCREF(Py_None);
        PyDict_SetItemString(match_dict, "allowed_methods", Py_None);
    }

    return match_dict;
}

// add_c_route(method, path, route_id) - Add route to C router for matching
static PyObject* CatzillaServer_add_c_route(CatzillaServerObject *self, PyObject *args)
{
    const char *method, *path;
    long route_id;
    if (!PyArg_ParseTuple(args, "ssl", &method, &path, &route_id))
        return NULL;

    // Add route to C router with route_id as user_data
    uint32_t c_route_id = catzilla_router_add_route(&self->py_router, method, path,
                                                   (void*)(uintptr_t)route_id, NULL, false);

    if (c_route_id == 0) {
        PyErr_SetString(PyExc_RuntimeError, "Failed to add route to C router");
        return NULL;
    }

    return PyLong_FromLong(c_route_id);
}

// add_c_route_with_middleware(method, path, route_id, middleware_ids, middleware_priorities) - Add route to C router with middleware
static PyObject* CatzillaServer_add_c_route_with_middleware(CatzillaServerObject *self, PyObject *args)
{
    const char *method, *path;
    long route_id;
    PyObject *middleware_list = NULL;
    PyObject *priority_list = NULL;

    if (!PyArg_ParseTuple(args, "ssl|OO", &method, &path, &route_id, &middleware_list, &priority_list))
        return NULL;

    // Prepare middleware arrays
    void** middleware_functions = NULL;
    uint32_t* middleware_priorities = NULL;
    int middleware_count = 0;
    PyObject *middleware_ids = NULL;  // Declare at function scope

    if (middleware_list && PyList_Check(middleware_list)) {
        middleware_count = PyList_Size(middleware_list);

        if (middleware_count > 0) {
            // Convert Python functions to IDs if needed
            bool need_conversion = false;

            // Check if we have function objects that need conversion
            for (int i = 0; i < middleware_count; i++) {
                PyObject *middleware_item = PyList_GetItem(middleware_list, i);
                if (!PyLong_Check(middleware_item)) {
                    need_conversion = true;
                    break;
                }
            }

            if (need_conversion) {
                // Convert middleware functions to IDs
                PyObject *convert_args = PyTuple_Pack(1, middleware_list);
                if (!convert_args) {
                    return NULL;
                }
                middleware_ids = convert_middleware_to_ids(NULL, convert_args);
                Py_DECREF(convert_args);

                if (!middleware_ids) {
                    return NULL;
                }
                middleware_list = middleware_ids;  // Use converted list
            }

            // Allocate middleware arrays
            middleware_functions = catzilla_cache_alloc(sizeof(void*) * middleware_count);
            middleware_priorities = catzilla_cache_alloc(sizeof(uint32_t) * middleware_count);

            if (!middleware_functions || !middleware_priorities) {
                if (middleware_functions) catzilla_cache_free(middleware_functions);
                if (middleware_priorities) catzilla_cache_free(middleware_priorities);
                Py_XDECREF(middleware_ids);
                PyErr_NoMemory();
                return NULL;
            }

            // Extract middleware function IDs and priorities
            for (int i = 0; i < middleware_count; i++) {
                PyObject *middleware_item = PyList_GetItem(middleware_list, i);
                if (!PyLong_Check(middleware_item)) {
                    catzilla_cache_free(middleware_functions);
                    catzilla_cache_free(middleware_priorities);
                    Py_XDECREF(middleware_ids);
                    PyErr_SetString(PyExc_TypeError, "Middleware conversion failed - expected integer IDs");
                    return NULL;
                }

                long middleware_id = PyLong_AsLong(middleware_item);
                middleware_functions[i] = (void*)(uintptr_t)middleware_id;

                // Set priority from priority_list or use default
                if (priority_list && PyList_Check(priority_list) && i < PyList_Size(priority_list)) {
                    PyObject *priority_item = PyList_GetItem(priority_list, i);
                    if (PyLong_Check(priority_item)) {
                        middleware_priorities[i] = (uint32_t)PyLong_AsLong(priority_item);
                    } else {
                        middleware_priorities[i] = 1000 + i;  // Default priority
                    }
                } else {
                    middleware_priorities[i] = 1000 + i;  // Default priority
                }
            }
        }
    }

    // Add route to C router with middleware and route_id as user_data
    uint32_t c_route_id = catzilla_router_add_route_with_middleware(&self->py_router, method, path,
                                                                    (void*)(uintptr_t)route_id, NULL, false,
                                                                    middleware_functions, middleware_count, middleware_priorities);

    // Cleanup middleware arrays (they are copied internally)
    if (middleware_functions) catzilla_cache_free(middleware_functions);
    if (middleware_priorities) catzilla_cache_free(middleware_priorities);
    Py_XDECREF(middleware_ids);  // Clean up converted middleware IDs if any

    if (c_route_id == 0) {
        PyErr_SetString(PyExc_RuntimeError, "Failed to add route with middleware to C router");
        return NULL;
    }

    return PyLong_FromLong(c_route_id);
}

// CatzillaServer.mount_static(mount_path, directory, **options)
static PyObject* CatzillaServer_mount_static(CatzillaServerObject *self, PyObject *args, PyObject *kwargs)
{
    const char *mount_path, *directory;

    // Default configuration options
    static char *kwlist[] = {
        "mount_path", "directory", "index_file", "enable_hot_cache", "cache_size_mb",
        "cache_ttl_seconds", "enable_compression", "compression_level",
        "max_file_size", "enable_etags", "enable_range_requests",
        "enable_directory_listing", "enable_hidden_files", NULL
    };

    // Default values
    const char *index_file = "index.html";
    int enable_hot_cache = 1;
    int cache_size_mb = 100;
    int cache_ttl_seconds = 3600;
    int enable_compression = 1;
    int compression_level = 6;
    long max_file_size = 100 * 1024 * 1024;  // 100MB
    int enable_etags = 1;
    int enable_range_requests = 1;
    int enable_directory_listing = 0;
    int enable_hidden_files = 0;

    // Parse arguments with keyword support
    if (!PyArg_ParseTupleAndKeywords(args, kwargs, "ss|siiiiiLiiii", kwlist,
                                     &mount_path, &directory, &index_file,
                                     &enable_hot_cache, &cache_size_mb, &cache_ttl_seconds,
                                     &enable_compression, &compression_level, &max_file_size,
                                     &enable_etags, &enable_range_requests,
                                     &enable_directory_listing, &enable_hidden_files)) {
        return NULL;
    }

    // Validate mount path
    if (!mount_path || strlen(mount_path) == 0 || mount_path[0] != '/') {
        PyErr_SetString(PyExc_ValueError, "mount_path must start with '/'");
        return NULL;
    }

    // Validate directory path
    if (!directory || strlen(directory) == 0) {
        PyErr_SetString(PyExc_ValueError, "directory path cannot be empty");
        return NULL;
    }

    // Create static server configuration
    static_server_config_t *config = catzilla_cache_alloc(sizeof(static_server_config_t));
    if (!config) {
        PyErr_NoMemory();
        return NULL;
    }

    // Initialize configuration with Python values
    memset(config, 0, sizeof(static_server_config_t));

    // Basic paths - allocate and copy strings
    config->mount_path = catzilla_cache_alloc(strlen(mount_path) + 1);
    config->directory = catzilla_cache_alloc(strlen(directory) + 1);
    config->index_file = catzilla_cache_alloc(strlen(index_file) + 1);

    if (!config->mount_path || !config->directory || !config->index_file) {
        if (config->mount_path) catzilla_cache_free(config->mount_path);
        if (config->directory) catzilla_cache_free(config->directory);
        if (config->index_file) catzilla_cache_free(config->index_file);
        catzilla_cache_free(config);
        PyErr_NoMemory();
        return NULL;
    }

    strcpy(config->mount_path, mount_path);
    strcpy(config->directory, directory);
    strcpy(config->index_file, index_file);

    // libuv settings - use the server's event loop
    config->loop = self->server.loop;
    config->fs_thread_pool_size = 4;
    config->use_sendfile = true;

    // Performance settings
    config->enable_hot_cache = enable_hot_cache ? true : false;
    config->cache_size_mb = cache_size_mb > 0 ? cache_size_mb : 100;
    config->cache_ttl_seconds = cache_ttl_seconds > 0 ? cache_ttl_seconds : 3600;

    // Compression settings
    config->enable_compression = enable_compression ? true : false;
    config->compression_level = (compression_level >= 1 && compression_level <= 9) ? compression_level : 6;
    config->compression_min_size = 1024;  // Compress files > 1KB

    // Security settings
    config->enable_path_validation = true;  // Always enable security
    config->enable_hidden_files = enable_hidden_files ? true : false;
    config->max_file_size = max_file_size > 0 ? max_file_size : 100 * 1024 * 1024;

    // HTTP features
    config->enable_etags = enable_etags ? true : false;
    config->enable_last_modified = true;
    config->enable_range_requests = enable_range_requests ? true : false;
    config->enable_directory_listing = enable_directory_listing ? true : false;

    // Call the C function to mount the static directory
    int result = catzilla_server_mount_static(&self->server, mount_path, directory, config);

    // The C function takes ownership of the config, so we don't free it here

    if (result != 0) {
        PyErr_Format(PyExc_RuntimeError, "Failed to mount static directory: %s -> %s (error code: %d)",
                     mount_path, directory, result);
        return NULL;
    }

    // Return success
    Py_RETURN_NONE;
}

// send_response(client_capsule, status, headers, body)
static PyObject* send_response(PyObject *self, PyObject *args)
{
    PyObject *capsule;
    int status;
    const char *headers, *body;
    if (!PyArg_ParseTuple(args, "Oiss", &capsule, &status, &headers, &body))
        return NULL;

    uv_stream_t *client = PyCapsule_GetPointer(capsule, "catzilla.client");
    if (!client) {
        PyErr_SetString(PyExc_TypeError, "Invalid client capsule");
        return NULL;
    }

    // Check if this is a streaming response
    if (body && strncmp(body, "___CATZILLA_STREAMING___", 24) == 0) {
        // Extract streaming ID from marker: ___CATZILLA_STREAMING___<uuid>___
        const char* id_start = body + 24;  // Skip marker prefix
        const char* id_end = strstr(id_start, "___");  // Find end marker

        if (id_end) {
            // Extract the streaming ID
            size_t id_len = id_end - id_start;
            char* streaming_id = malloc(id_len + 1);
            if (!streaming_id) {
                PyErr_SetString(PyExc_MemoryError, "Failed to allocate memory for streaming ID");
                return NULL;
            }

            strncpy(streaming_id, id_start, id_len);
            streaming_id[id_len] = '\0';

            // Connect to streaming response via the streaming module
            PyObject* catzilla_module = PyImport_ImportModule("catzilla._catzilla");
            if (!catzilla_module) {
                free(streaming_id);
                return NULL;
            }

            PyObject* streaming_attr = PyObject_GetAttrString(catzilla_module, "_streaming");
            if (!streaming_attr) {
                Py_DECREF(catzilla_module);
                free(streaming_id);
                return NULL;
            }

            PyObject* connect_func = PyObject_GetAttrString(streaming_attr, "connect_streaming_response");
            if (!connect_func) {
                Py_DECREF(streaming_attr);
                Py_DECREF(catzilla_module);
                free(streaming_id);
                return NULL;
            }

            // Call connect_streaming_response(client_capsule, streaming_id)
            PyObject* id_str = PyUnicode_FromString(streaming_id);
            PyObject* result = PyObject_CallFunctionObjArgs(connect_func, capsule, id_str, NULL);

            // Cleanup
            free(streaming_id);
            Py_DECREF(id_str);
            Py_DECREF(connect_func);
            Py_DECREF(streaming_attr);
            Py_DECREF(catzilla_module);

            if (!result) {
                return NULL;
            }

            Py_DECREF(result);
            Py_RETURN_NONE;
        }
    }

    // Regular response handling
    catzilla_send_response(client, status, headers, body, strlen(body));
    Py_RETURN_NONE;
}

// Convert yyjson value to Python object
static PyObject* yyjson_to_python(yyjson_val* val) {
    if (!val) return Py_None;

    switch (yyjson_get_type(val)) {
        case YYJSON_TYPE_NULL:
            Py_RETURN_NONE;

        case YYJSON_TYPE_BOOL:
            return PyBool_FromLong(yyjson_get_bool(val));

        case YYJSON_TYPE_NUM:
            if (yyjson_is_int(val))
                return PyLong_FromLongLong(yyjson_get_int(val));
            else
                return PyFloat_FromDouble(yyjson_get_real(val));

        case YYJSON_TYPE_STR:
            return PyUnicode_FromString(yyjson_get_str(val));

        case YYJSON_TYPE_ARR: {
            size_t idx, max;
            yyjson_val *item;
            PyObject *list = PyList_New(yyjson_arr_size(val));
            if (!list) return NULL;

            yyjson_arr_foreach(val, idx, max, item) {
                PyObject *item_obj = yyjson_to_python(item);
                if (!item_obj) {
                    Py_DECREF(list);
                    return NULL;
                }
                PyList_SET_ITEM(list, idx, item_obj);
            }
            return list;
        }

        case YYJSON_TYPE_OBJ: {
            size_t idx, max;
            yyjson_val *key, *value;
            PyObject *dict = PyDict_New();
            if (!dict) return NULL;

            yyjson_obj_foreach(val, idx, max, key, value) {
                PyObject *key_obj = PyUnicode_FromString(yyjson_get_str(key));
                PyObject *value_obj = yyjson_to_python(value);
                if (!key_obj || !value_obj) {
                    Py_XDECREF(key_obj);
                    Py_XDECREF(value_obj);
                    Py_DECREF(dict);
                    return NULL;
                }
                PyDict_SetItem(dict, key_obj, value_obj);
                Py_DECREF(key_obj);
                Py_DECREF(value_obj);
            }
            return dict;
        }

        default:
            PyErr_SetString(PyExc_ValueError, "Unknown JSON type");
            return NULL;
    }
}

// ============================================================================
// ULTRA-FAST VALIDATION ENGINE - PYTHON INTEGRATION
// ============================================================================

// Convert Python object to JSON object for C validation
static json_object_t* python_to_json_object(PyObject* obj) {
    if (!obj || obj == Py_None) {
        json_object_t* json_obj = catzilla_request_alloc(sizeof(json_object_t));
        if (!json_obj) return NULL;
        json_obj->type = JSON_NULL;
        return json_obj;
    }

    json_object_t* json_obj = catzilla_request_alloc(sizeof(json_object_t));
    if (!json_obj) return NULL;

    if (PyBool_Check(obj)) {
        json_obj->type = JSON_BOOL;
        json_obj->bool_val = (obj == Py_True) ? 1 : 0;
    }
    else if (PyLong_Check(obj)) {
        json_obj->type = JSON_INT;
        json_obj->int_val = PyLong_AsLong(obj);
    }
    else if (PyFloat_Check(obj)) {
        json_obj->type = JSON_FLOAT;
        json_obj->float_val = PyFloat_AsDouble(obj);
    }
    else if (PyUnicode_Check(obj)) {
        json_obj->type = JSON_STRING;
        const char* str = PyUnicode_AsUTF8(obj);
        // Use request arena for temporary string storage
        size_t len = strlen(str) + 1;
        json_obj->string_val = catzilla_request_alloc(len);
        if (json_obj->string_val) {
            strcpy(json_obj->string_val, str);
        }
    }
    else if (PyList_Check(obj)) {
        json_obj->type = JSON_ARRAY;
        Py_ssize_t size = PyList_Size(obj);
        json_obj->array_val.count = size;
        json_obj->array_val.items = catzilla_request_alloc(sizeof(json_object_t*) * size);

        for (Py_ssize_t i = 0; i < size; i++) {
            PyObject* item = PyList_GetItem(obj, i);
            json_obj->array_val.items[i] = python_to_json_object(item);
        }
    }
    else if (PyDict_Check(obj)) {
        json_obj->type = JSON_OBJECT;
        PyObject* keys = PyDict_Keys(obj);
        Py_ssize_t size = PyList_Size(keys);

        json_obj->object_val.count = size;
        json_obj->object_val.keys = catzilla_request_alloc(sizeof(char*) * size);
        json_obj->object_val.values = catzilla_request_alloc(sizeof(json_object_t*) * size);

        for (Py_ssize_t i = 0; i < size; i++) {
            PyObject* key = PyList_GetItem(keys, i);
            PyObject* value = PyDict_GetItem(obj, key);

            const char* key_str = PyUnicode_AsUTF8(key);
            size_t key_len = strlen(key_str) + 1;
            json_obj->object_val.keys[i] = catzilla_request_alloc(key_len);
            if (json_obj->object_val.keys[i]) {
                strcpy(json_obj->object_val.keys[i], key_str);
            }
            json_obj->object_val.values[i] = python_to_json_object(value);
        }
        Py_DECREF(keys);
    }
    else {
        catzilla_request_free(json_obj);
        return NULL;
    }

    return json_obj;
}

// Convert JSON object back to Python object
static PyObject* json_object_to_python(json_object_t* obj) {
    if (!obj) {
        Py_RETURN_NONE;
    }

    switch (obj->type) {
        case JSON_NULL:
            Py_RETURN_NONE;
        case JSON_BOOL:
            return PyBool_FromLong(obj->bool_val);
        case JSON_INT:
            return PyLong_FromLong(obj->int_val);
        case JSON_FLOAT:
            return PyFloat_FromDouble(obj->float_val);
        case JSON_STRING:
            return PyUnicode_FromString(obj->string_val);
        case JSON_ARRAY: {
            PyObject* list = PyList_New(obj->array_val.count);
            for (int i = 0; i < obj->array_val.count; i++) {
                PyObject* item = json_object_to_python(obj->array_val.items[i]);
                PyList_SetItem(list, i, item);
            }
            return list;
        }
        case JSON_OBJECT: {
            PyObject* dict = PyDict_New();
            for (int i = 0; i < obj->object_val.count; i++) {
                PyObject* key = PyUnicode_FromString(obj->object_val.keys[i]);
                PyObject* value = json_object_to_python(obj->object_val.values[i]);
                PyDict_SetItem(dict, key, value);
                Py_DECREF(key);
                Py_DECREF(value);
            }
            return dict;
        }
    }
    Py_RETURN_NONE;
}

// ============================================================================
// VALIDATOR OBJECT IMPLEMENTATION
// ============================================================================

// Validator object deallocation
static void CatzillaValidator_dealloc(CatzillaValidatorObject *self) {
    if (self->validator) {
        catzilla_free_validator(self->validator);
    }
    Py_TYPE(self)->tp_free((PyObject*)self);
}

// Validator object new
static PyObject* CatzillaValidator_new(PyTypeObject *type, PyObject *args, PyObject *kwds) {
    CatzillaValidatorObject *self = (CatzillaValidatorObject*)type->tp_alloc(type, 0);
    if (self) {
        self->validator = NULL;
    }
    return (PyObject*)self;
}

// Create integer validator: IntValidator(min=None, max=None)
static PyObject* create_int_validator(PyObject *self, PyObject *args, PyObject *kwargs) {
    static char *kwlist[] = {"min", "max", NULL};
    PyObject *min_obj = NULL, *max_obj = NULL;

    if (!PyArg_ParseTupleAndKeywords(args, kwargs, "|OO", kwlist, &min_obj, &max_obj)) {
        return NULL;
    }

    long min_val = LONG_MIN, max_val = LONG_MAX;
    int has_min = 0, has_max = 0;

    if (min_obj && min_obj != Py_None) {
        min_val = PyLong_AsLong(min_obj);
        has_min = 1;
    }
    if (max_obj && max_obj != Py_None) {
        max_val = PyLong_AsLong(max_obj);
        has_max = 1;
    }

    CatzillaValidatorObject *validator_obj = (CatzillaValidatorObject*)CatzillaValidator_new(&CatzillaValidatorType, NULL, NULL);
    if (!validator_obj) return NULL;

    validator_obj->validator = catzilla_create_int_validator(min_val, max_val, has_min, has_max);
    if (!validator_obj->validator) {
        Py_DECREF(validator_obj);
        PyErr_SetString(PyExc_RuntimeError, "Failed to create integer validator");
        return NULL;
    }

    return (PyObject*)validator_obj;
}

// Create string validator: StringValidator(min_len=None, max_len=None, pattern=None)
static PyObject* create_string_validator(PyObject *self, PyObject *args, PyObject *kwargs) {
    static char *kwlist[] = {"min_len", "max_len", "pattern", NULL};
    PyObject *min_len_obj = NULL, *max_len_obj = NULL, *pattern_obj = NULL;

    if (!PyArg_ParseTupleAndKeywords(args, kwargs, "|OOO", kwlist, &min_len_obj, &max_len_obj, &pattern_obj)) {
        return NULL;
    }

    int min_len = -1, max_len = -1;
    const char *pattern = NULL;

    if (min_len_obj && min_len_obj != Py_None) {
        min_len = PyLong_AsLong(min_len_obj);
    }
    if (max_len_obj && max_len_obj != Py_None) {
        max_len = PyLong_AsLong(max_len_obj);
    }
    if (pattern_obj && pattern_obj != Py_None) {
        pattern = PyUnicode_AsUTF8(pattern_obj);
    }

    CatzillaValidatorObject *validator_obj = (CatzillaValidatorObject*)CatzillaValidator_new(&CatzillaValidatorType, NULL, NULL);
    if (!validator_obj) return NULL;

    validator_obj->validator = catzilla_create_string_validator(min_len, max_len, pattern);
    if (!validator_obj->validator) {
        Py_DECREF(validator_obj);
        PyErr_SetString(PyExc_RuntimeError, "Failed to create string validator");
        return NULL;
    }

    return (PyObject*)validator_obj;
}

// Create float validator: FloatValidator(min=None, max=None)
static PyObject* create_float_validator(PyObject *self, PyObject *args, PyObject *kwargs) {
    static char *kwlist[] = {"min", "max", NULL};
    PyObject *min_obj = NULL, *max_obj = NULL;

    if (!PyArg_ParseTupleAndKeywords(args, kwargs, "|OO", kwlist, &min_obj, &max_obj)) {
        return NULL;
    }

    double min_val = -HUGE_VAL, max_val = HUGE_VAL;
    int has_min = 0, has_max = 0;

    if (min_obj && min_obj != Py_None) {
        min_val = PyFloat_AsDouble(min_obj);
        has_min = 1;
    }
    if (max_obj && max_obj != Py_None) {
        max_val = PyFloat_AsDouble(max_obj);
        has_max = 1;
    }

    CatzillaValidatorObject *validator_obj = (CatzillaValidatorObject*)CatzillaValidator_new(&CatzillaValidatorType, NULL, NULL);
    if (!validator_obj) return NULL;

    validator_obj->validator = catzilla_create_float_validator(min_val, max_val, has_min, has_max);
    if (!validator_obj->validator) {
        Py_DECREF(validator_obj);
        PyErr_SetString(PyExc_RuntimeError, "Failed to create float validator");
        return NULL;
    }

    return (PyObject*)validator_obj;
}

// Validate method for validator: validator.validate(value)
static PyObject* CatzillaValidator_validate(CatzillaValidatorObject *self, PyObject *args) {
    PyObject *value;
    if (!PyArg_ParseTuple(args, "O", &value)) {
        return NULL;
    }

    // Convert Python value to JSON object
    json_object_t *json_value = python_to_json_object(value);
    if (!json_value) {
        PyErr_SetString(PyExc_ValueError, "Failed to convert Python value to JSON");
        return NULL;
    }

    // Create validation context
    validation_context_t *ctx = catzilla_create_validation_context();
    if (!ctx) {
        catzilla_free_json_object(json_value);
        PyErr_SetString(PyExc_RuntimeError, "Failed to create validation context");
        return NULL;
    }

    // Perform validation
    validation_result_t result = catzilla_validate_value(self->validator, json_value, ctx);

    // Clean up
    catzilla_free_json_object(json_value);

    if (result == VALIDATION_SUCCESS) {
        catzilla_free_validation_context(ctx);
        Py_RETURN_TRUE;
    } else {
        // Get error message
        char *error_msg = catzilla_get_validation_errors(ctx);
        PyObject *error = PyUnicode_FromString(error_msg ? error_msg : "Validation failed");
        catzilla_free_validation_context(ctx);

        PyErr_SetObject(PyExc_ValueError, error);
        Py_DECREF(error);
        return NULL;
    }
}

// ============================================================================
// MODEL OBJECT IMPLEMENTATION
// ============================================================================

// Model object deallocation
static void CatzillaModel_dealloc(CatzillaModelObject *self) {
    if (self->model) {
        catzilla_free_model_spec(self->model);
    }
    if (self->context) {
        catzilla_free_validation_context(self->context);
    }
    Py_TYPE(self)->tp_free((PyObject*)self);
}

// Model object new
static PyObject* CatzillaModel_new(PyTypeObject *type, PyObject *args, PyObject *kwds) {
    CatzillaModelObject *self = (CatzillaModelObject*)type->tp_alloc(type, 0);
    if (self) {
        self->model = NULL;
        self->context = NULL;
    }
    return (PyObject*)self;
}

// Create model: Model(name, fields_dict)
static PyObject* create_model(PyObject *self, PyObject *args, PyObject *kwargs) {
    static char *kwlist[] = {"name", "fields", NULL};
    const char *name;
    PyObject *fields_dict;

    if (!PyArg_ParseTupleAndKeywords(args, kwargs, "sO", kwlist, &name, &fields_dict)) {
        return NULL;
    }

    if (!PyDict_Check(fields_dict)) {
        PyErr_SetString(PyExc_TypeError, "fields must be a dictionary");
        return NULL;
    }

    Py_ssize_t field_count = PyDict_Size(fields_dict);

    CatzillaModelObject *model_obj = (CatzillaModelObject*)CatzillaModel_new(&CatzillaModelType, NULL, NULL);
    if (!model_obj) return NULL;

    // Create model specification
    model_obj->model = catzilla_create_model_spec(name, field_count);
    if (!model_obj->model) {
        Py_DECREF(model_obj);
        PyErr_SetString(PyExc_RuntimeError, "Failed to create model specification");
        return NULL;
    }

    // Create validation context
    model_obj->context = catzilla_create_validation_context();
    if (!model_obj->context) {
        Py_DECREF(model_obj);
        PyErr_SetString(PyExc_RuntimeError, "Failed to create validation context");
        return NULL;
    }

    // Add fields to model
    PyObject *keys = PyDict_Keys(fields_dict);
    for (Py_ssize_t i = 0; i < field_count; i++) {
        PyObject *field_name = PyList_GetItem(keys, i);
        PyObject *field_spec = PyDict_GetItem(fields_dict, field_name);

        const char *field_name_str = PyUnicode_AsUTF8(field_name);

        // Field spec is now a tuple: (validator, required)
        if (!PyTuple_Check(field_spec) || PyTuple_Size(field_spec) != 2) {
            Py_DECREF(keys);
            Py_DECREF(model_obj);
            PyErr_SetString(PyExc_TypeError, "Field specification must be a tuple (validator, required)");
            return NULL;
        }

        PyObject *validator_obj_py = PyTuple_GetItem(field_spec, 0);
        PyObject *required_obj = PyTuple_GetItem(field_spec, 1);

        if (!PyObject_IsInstance(validator_obj_py, (PyObject*)&CatzillaValidatorType)) {
            Py_DECREF(keys);
            Py_DECREF(model_obj);
            PyErr_SetString(PyExc_TypeError, "First element of field specification must be a validator");
            return NULL;
        }

        if (!PyBool_Check(required_obj)) {
            Py_DECREF(keys);
            Py_DECREF(model_obj);
            PyErr_SetString(PyExc_TypeError, "Second element of field specification must be a boolean");
            return NULL;
        }

        CatzillaValidatorObject *validator_obj = (CatzillaValidatorObject*)validator_obj_py;
        int required = (required_obj == Py_True) ? 1 : 0;

        int result = catzilla_add_field_spec(model_obj->model, field_name_str, validator_obj->validator, required, NULL);

        if (result < 0) {
            Py_DECREF(keys);
            Py_DECREF(model_obj);
            PyErr_SetString(PyExc_RuntimeError, "Failed to add field to model");
            return NULL;
        }
    }
    Py_DECREF(keys);

    // Compile model for optimal performance
    if (catzilla_compile_model_spec(model_obj->model) != 0) {
        Py_DECREF(model_obj);
        PyErr_SetString(PyExc_RuntimeError, "Failed to compile model specification");
        return NULL;
    }

    return (PyObject*)model_obj;
}

// Validate method for model: model.validate(data)
static PyObject* CatzillaModel_validate(CatzillaModelObject *self, PyObject *args) {
    // printf("[DEBUG] CatzillaModel_validate: Starting validation call\n");
    // fflush(stdout);

    PyObject *data;
    if (!PyArg_ParseTuple(args, "O", &data)) {
        // printf("[DEBUG] CatzillaModel_validate: Failed to parse arguments\n");
        // fflush(stdout);
        return NULL;
    }

    // printf("[DEBUG] CatzillaModel_validate: Arguments parsed successfully\n");
    // fflush(stdout);

    // Convert Python data to JSON object
    json_object_t *json_data = python_to_json_object(data);
    if (!json_data) {
        PyErr_SetString(PyExc_ValueError, "Failed to convert Python data to JSON");
        return NULL;
    }

    // Clear previous validation errors
    catzilla_clear_validation_errors(self->context);

    // Prepare for validation
    json_object_t *validated_data = NULL;
    validation_result_t result;

    // Perform model validation with careful error handling
    Py_BEGIN_ALLOW_THREADS
    result = catzilla_validate_model(self->model, json_data, &validated_data, self->context);
    Py_END_ALLOW_THREADS

    // Clean up input data immediately
    catzilla_free_json_object(json_data);

    if (result == VALIDATION_SUCCESS && validated_data != NULL) {
        // Success case - we have valid data
        PyObject *py_validated = json_object_to_python(validated_data);
        catzilla_free_json_object(validated_data);
        return py_validated;
    } else {
        // Error case - get error messages
        char *error_msg = catzilla_get_validation_errors(self->context);
        PyObject *error = PyUnicode_FromString(error_msg ? error_msg : "Model validation failed");

        // Set Python exception
        PyErr_SetObject(PyExc_ValueError, error);
        Py_DECREF(error);

        // Double check validated_data is cleaned up
        if (validated_data != NULL) {
            catzilla_free_json_object(validated_data);
            validated_data = NULL;
        }
        return NULL;
    }
}

// Get validation statistics
static PyObject* get_validation_stats(PyObject *self, PyObject *args) {
    validation_stats_t *stats = catzilla_get_validation_stats();
    if (!stats) {
        Py_RETURN_NONE;
    }

    PyObject *stats_dict = PyDict_New();
    PyDict_SetItemString(stats_dict, "validations_performed", PyLong_FromUnsignedLong(stats->validations_performed));
    PyDict_SetItemString(stats_dict, "total_time_ns", PyLong_FromUnsignedLong(stats->total_time_ns));
    PyDict_SetItemString(stats_dict, "memory_used_bytes", PyLong_FromUnsignedLong(stats->memory_used_bytes));
    PyDict_SetItemString(stats_dict, "cache_hits", PyLong_FromUnsignedLong(stats->cache_hits));
    PyDict_SetItemString(stats_dict, "cache_misses", PyLong_FromUnsignedLong(stats->cache_misses));

    return stats_dict;
}

// Reset validation statistics
static PyObject* reset_validation_stats(PyObject *self, PyObject *args) {
    catzilla_reset_validation_stats();
    Py_RETURN_NONE;
}

// Parse JSON from request
static PyObject* parse_json(PyObject *self, PyObject *args) {
    catzilla_request_t* request;
    PyObject* capsule;

    if (!PyArg_ParseTuple(args, "O", &capsule))
        return NULL;

    request = (catzilla_request_t*)PyCapsule_GetPointer(capsule, "catzilla.request");
    if (!request) {
        PyErr_SetString(PyExc_TypeError, "Invalid request capsule");
        return NULL;
    }

    if (catzilla_parse_json(request) != 0) {
        Py_RETURN_NONE;
    }

    return yyjson_to_python(request->json_root);
}

// Parse form data from request
static PyObject* parse_form(PyObject *self, PyObject *args) {
    catzilla_request_t* request;
    PyObject* capsule;

    if (!PyArg_ParseTuple(args, "O", &capsule))
        return NULL;

    request = (catzilla_request_t*)PyCapsule_GetPointer(capsule, "catzilla.request");
    if (!request) {
        PyErr_SetString(PyExc_TypeError, "Invalid request capsule");
        return NULL;
    }

    if (catzilla_parse_form(request) != 0) {
        Py_RETURN_NONE;
    }

    PyObject* form_dict = PyDict_New();
    if (!form_dict) return NULL;

    for (int i = 0; i < request->form_field_count; i++) {
        PyObject* key = PyUnicode_FromString(request->form_fields[i]);
        PyObject* value = PyUnicode_FromString(request->form_values[i]);
        if (!key || !value) {
            Py_XDECREF(key);
            Py_XDECREF(value);
            Py_DECREF(form_dict);
            return NULL;
        }
        PyDict_SetItem(form_dict, key, value);
        Py_DECREF(key);
        Py_DECREF(value);
    }

    return form_dict;
}

// Get parsed JSON from request
static PyObject* get_json(PyObject *self, PyObject *args) {
    catzilla_request_t* request;
    PyObject* capsule;

    if (!PyArg_ParseTuple(args, "O", &capsule))
        return NULL;

    request = (catzilla_request_t*)PyCapsule_GetPointer(capsule, "catzilla.request");
    if (!request) {
        PyErr_SetString(PyExc_TypeError, "Invalid request capsule");
        return NULL;
    }

    yyjson_val* json = catzilla_get_json(request);
    if (!json) {
        return PyDict_New();  // Return empty dict if no JSON
    }

    return yyjson_to_python(json);
}

// Get form field value
static PyObject* get_form_field(PyObject *self, PyObject *args) {
    catzilla_request_t* request;
    PyObject* capsule;
    const char* field;

    if (!PyArg_ParseTuple(args, "Os", &capsule, &field))
        return NULL;

    request = (catzilla_request_t*)PyCapsule_GetPointer(capsule, "catzilla.request");
    if (!request) {
        PyErr_SetString(PyExc_TypeError, "Invalid request capsule");
        return NULL;
    }

    const char* value = catzilla_get_form_field(request, field);
    if (!value) {
        Py_RETURN_NONE;
    }

    return PyUnicode_FromString(value);
}

// Get header value from request
static PyObject* get_header(PyObject *self, PyObject *args) {
    catzilla_request_t* request;
    PyObject* capsule;
    const char* header_name;

    if (!PyArg_ParseTuple(args, "Os", &capsule, &header_name))
        return NULL;

    request = (catzilla_request_t*)PyCapsule_GetPointer(capsule, "catzilla.request");
    if (!request) {
        PyErr_SetString(PyExc_TypeError, "Invalid request capsule");
        return NULL;
    }

    // Search through headers array (case-insensitive)
    for (int i = 0; i < request->header_count; i++) {
        if (request->headers[i].name && strcasecmp(request->headers[i].name, header_name) == 0) {
            return PyUnicode_FromString(request->headers[i].value ? request->headers[i].value : "");
        }
    }

    Py_RETURN_NONE;
}

// Get content type from request
static PyObject* get_content_type(PyObject* self, PyObject* args) {
    PyObject* capsule;
    if (!PyArg_ParseTuple(args, "O", &capsule))
        return NULL;

    catzilla_request_t* request = PyCapsule_GetPointer(capsule, "catzilla.request");
    if (!request) {
        PyErr_SetString(PyExc_RuntimeError, "Invalid request capsule");
        return NULL;
    }

    const char* content_type = catzilla_get_content_type_str(request);
    LOG_HTTP_DEBUG("get_content_type_str: passed, moved to unicode conversion");
    return PyUnicode_FromString(content_type);
}

// get_query_param(request_capsule, param_name)
static PyObject* get_query_param(PyObject *self, PyObject *args)
{
    PyObject *capsule;
    const char *param;
    if (!PyArg_ParseTuple(args, "Os", &capsule, &param))
        return NULL;

    catzilla_request_t *request = PyCapsule_GetPointer(capsule, "catzilla.request");
    if (!request) {
        PyErr_SetString(PyExc_TypeError, "Invalid request capsule");
        return NULL;
    }

    const char *value = catzilla_get_query_param(request, param);
    if (!value) {
        Py_RETURN_NONE;
    }
    return PyUnicode_FromString(value);
}

// Get uploaded files from request
static PyObject* get_files(PyObject *self, PyObject *args) {
    catzilla_request_t* request;
    PyObject* capsule;

    LOG_DEBUG("Bridge", "get_files() called");

    if (!PyArg_ParseTuple(args, "O", &capsule)) {
        LOG_DEBUG("Bridge", "Failed to parse args");
        return NULL;
    }

    LOG_DEBUG("Bridge", "Getting request from capsule");
    request = (catzilla_request_t*)PyCapsule_GetPointer(capsule, "catzilla.request");
    if (!request) {
        LOG_DEBUG("Bridge", "Invalid request capsule");
        PyErr_SetString(PyExc_TypeError, "Invalid request capsule");
        return NULL;
    }

    LOG_DEBUG("Bridge", "Request valid, has_files=%d, file_count=%d",
           request->has_files, request->file_count);

    PyObject* files_dict = PyDict_New();
    if (!files_dict) {
        LOG_DEBUG("Bridge", "Failed to create dict");
        return NULL;
    }

    LOG_DEBUG("Bridge", "Created files dictionary");

    if (request->has_files && request->file_count > 0) {
        LOG_DEBUG("Bridge", "Processing %d files", request->file_count);
        for (int i = 0; i < request->file_count; i++) {
            LOG_DEBUG("Bridge", "Processing file %d/%d", i+1, request->file_count);

            catzilla_upload_file_t* file = request->files[i];
            if (!file) {
                LOG_DEBUG("Bridge", "File %d is NULL, skipping", i);
                continue;
            }

            LOG_DEBUG("Bridge", "File %d: field_name=%s, filename=%s, size=%llu",
                   i, file->field_name ? file->field_name : "NULL",
                   file->filename ? file->filename : "NULL",
                   (unsigned long long)file->size);

            // Create a file info dict for each file
            LOG_DEBUG("Bridge", "Creating file info dict for file %d", i);
            PyObject* file_info = PyDict_New();
            if (!file_info) {
                LOG_DEBUG("Bridge", "Failed to create file_info dict");
                Py_DECREF(files_dict);
                return NULL;
            }

            LOG_DEBUG("Bridge", "Adding field_name to dict");
            // Add field name
            if (file->field_name) {
                PyDict_SetItemString(file_info, "field_name", PyUnicode_FromString(file->field_name));
            } else {
                PyDict_SetItemString(file_info, "field_name", Py_None);
            }

            LOG_DEBUG("Bridge", "Adding filename to dict");
            // Add filename
            if (file->filename) {
                PyDict_SetItemString(file_info, "filename", PyUnicode_FromString(file->filename));
            } else {
                PyDict_SetItemString(file_info, "filename", Py_None);
            }

            LOG_DEBUG("Bridge", "Adding content_type to dict");
            // Add content type
            if (file->content_type) {
                PyDict_SetItemString(file_info, "content_type", PyUnicode_FromString(file->content_type));
            } else {
                PyDict_SetItemString(file_info, "content_type", Py_None);
            }

            LOG_DEBUG("Bridge", "About to process content (size=%llu, pointer=%p)",
                   (unsigned long long)file->size, (void*)file->content);

            // Add content - use temp_path for large files, content for smaller files
            if (file->temp_file_path && strlen(file->temp_file_path) > 0) {
                // Large file streamed to temp file - provide temp_path instead of content
                LOG_DEBUG("Bridge", "Large file streamed to temp file: %s (size=%llu)",
                       file->temp_file_path, (unsigned long long)file->size);
                PyDict_SetItemString(file_info, "content", Py_None);
                PyDict_SetItemString(file_info, "temp_path", PyUnicode_FromString(file->temp_file_path));
                PyDict_SetItemString(file_info, "is_streamed", Py_True);
            } else if (file->content && file->size > 0) {
                // Regular file content in memory
                LOG_DEBUG("Bridge", "Processing file content in memory: field_name=%s, filename=%s, size=%llu",
                       file->field_name ? file->field_name : "NULL",
                       file->filename ? file->filename : "NULL",
                       (unsigned long long)file->size);

                PyObject* content_bytes = PyBytes_FromStringAndSize(file->content, (Py_ssize_t)file->size);
                if (content_bytes) {
                    LOG_DEBUG("Bridge", "Successfully created PyBytes object for file content");
                    PyDict_SetItemString(file_info, "content", content_bytes);
                    Py_DECREF(content_bytes);
                    PyDict_SetItemString(file_info, "temp_path", Py_None);
                    PyDict_SetItemString(file_info, "is_streamed", Py_False);
                } else {
                    // PyBytes creation failed (likely too large) - create temp file instead
                    LOG_DEBUG("Bridge", "PyBytes creation failed for large file - creating temp file");

                    // Create temporary file for large upload
                    char temp_path[256];
                    snprintf(temp_path, sizeof(temp_path), "/tmp/catzilla_upload_%d_%llu.tmp",
                             getpid(), (unsigned long long)time(NULL));

                    FILE* temp_file = fopen(temp_path, "wb");
                    if (temp_file && file->content) {
                        size_t written = fwrite(file->content, 1, file->size, temp_file);
                        fclose(temp_file);

                        if (written == file->size) {
                            LOG_DEBUG("Bridge", "Successfully wrote large file to temp path: %s", temp_path);
                            PyDict_SetItemString(file_info, "content", Py_None);
                            PyDict_SetItemString(file_info, "temp_path", PyUnicode_FromString(temp_path));
                            PyDict_SetItemString(file_info, "is_streamed", Py_True);
                        } else {
                            LOG_DEBUG("Bridge", "Failed to write complete file to temp path");
                            PyDict_SetItemString(file_info, "content", Py_None);
                            PyDict_SetItemString(file_info, "temp_path", Py_None);
                            PyDict_SetItemString(file_info, "is_streamed", Py_False);
                        }
                    } else {
                        LOG_DEBUG("Bridge", "Failed to create temp file for large upload");
                        PyDict_SetItemString(file_info, "content", Py_None);
                        PyDict_SetItemString(file_info, "temp_path", Py_None);
                        PyDict_SetItemString(file_info, "is_streamed", Py_False);
                    }
                }
            } else if (file->size == 0) {
                LOG_DEBUG("Bridge", "Zero-size file, setting content to empty bytes");
                PyDict_SetItemString(file_info, "content", PyBytes_FromStringAndSize("", 0));
            } else {
                LOG_DEBUG("Bridge", "No content pointer for file");
                PyDict_SetItemString(file_info, "content", Py_None);
            }

            // Add size
            PyDict_SetItemString(file_info, "size", PyLong_FromUnsignedLongLong(file->size));

            // Add temp file path
            if (file->temp_file_path) {
                PyDict_SetItemString(file_info, "temp_path", PyUnicode_FromString(file->temp_file_path));
            } else {
                PyDict_SetItemString(file_info, "temp_path", Py_None);
            }

            // Add state
            PyDict_SetItemString(file_info, "state", PyLong_FromLong(file->state));

            // Use field_name as key, fallback to filename, or file_N if neither
            const char* key = file->field_name;
            char default_key[32];
            if (!key) {
                key = file->filename;
                if (!key) {
                    snprintf(default_key, sizeof(default_key), "file_%d", i);
                    key = default_key;
                }
            }

            PyDict_SetItemString(files_dict, key, file_info);
            Py_DECREF(file_info);
        }
    }

    return files_dict;
}

// router_match(method, path) - Expose C router matching to Python
static PyObject* router_match(PyObject *self, PyObject *args)
{
    const char *method, *path;
    if (!PyArg_ParseTuple(args, "ss", &method, &path))
        return NULL;

    // Initialize global router if needed
    if (!global_router_initialized) {
        if (catzilla_router_init(&global_router) != 0) {
            PyErr_SetString(PyExc_RuntimeError, "Failed to initialize global router");
            return NULL;
        }
        global_router_initialized = true;
    }

    catzilla_route_match_t match;
    int result = catzilla_router_match(&global_router, method, path, &match);

    // Create Python dict with match results
    PyObject *match_dict = PyDict_New();
    if (!match_dict) {
        return NULL;
    }

    PyDict_SetItemString(match_dict, "matched", PyBool_FromLong(result == 0));
    PyDict_SetItemString(match_dict, "status_code", PyLong_FromLong(match.status_code));

    if (result == 0 && match.route) {
        PyDict_SetItemString(match_dict, "method", PyUnicode_FromString(match.route->method));
        PyDict_SetItemString(match_dict, "path", PyUnicode_FromString(match.route->path));
        PyDict_SetItemString(match_dict, "route_id", PyLong_FromLong(match.route->id));

        // Add path parameters
        PyObject *params_dict = PyDict_New();
        for (int i = 0; i < match.param_count; i++) {
            PyDict_SetItemString(params_dict, match.params[i].name,
                                PyUnicode_FromString(match.params[i].value));
        }
        PyDict_SetItemString(match_dict, "path_params", params_dict);
    } else {
        PyDict_SetItemString(match_dict, "path_params", PyDict_New());
    }

    if (match.has_allowed_methods) {
        PyDict_SetItemString(match_dict, "allowed_methods",
                            PyUnicode_FromString(match.allowed_methods));
    } else {
        Py_INCREF(Py_None);
        PyDict_SetItemString(match_dict, "allowed_methods", Py_None);
    }

    return match_dict;
}

// router_add_route(method, path, handler_id) - Add route to C router
static PyObject* router_add_route(PyObject *self, PyObject *args)
{
    const char *method, *path;
    long handler_id;
    if (!PyArg_ParseTuple(args, "ssl", &method, &path, &handler_id))
        return NULL;

    // Initialize global router if needed
    if (!global_router_initialized) {
        if (catzilla_router_init(&global_router) != 0) {
            PyErr_SetString(PyExc_RuntimeError, "Failed to initialize global router");
            return NULL;
        }
        global_router_initialized = true;
    }

    // Add route to global router
    uint32_t route_id = catzilla_router_add_route(&global_router, method, path,
                                                 (void*)(uintptr_t)handler_id, NULL, false);

    if (route_id == 0) {
        PyErr_SetString(PyExc_RuntimeError, "Failed to add route to router");
        return NULL;
    }

    return PyLong_FromLong(route_id);
}

// router_add_route_with_middleware(method, path, handler_id, middleware_ids, middleware_priorities) - Add route to C router with middleware
static PyObject* router_add_route_with_middleware(PyObject *self, PyObject *args)
{
    const char *method, *path;
    long handler_id;
    PyObject *middleware_list = NULL;
    PyObject *priority_list = NULL;

    if (!PyArg_ParseTuple(args, "ssl|OO", &method, &path, &handler_id, &middleware_list, &priority_list))
        return NULL;

    // Initialize global router if needed
    if (!global_router_initialized) {
        if (catzilla_router_init(&global_router) != 0) {
            PyErr_SetString(PyExc_RuntimeError, "Failed to initialize global router");
            return NULL;
        }
        global_router_initialized = true;
    }

    // Prepare middleware arrays
    void** middleware_functions = NULL;
    uint32_t* middleware_priorities = NULL;
    int middleware_count = 0;

    if (middleware_list && PyList_Check(middleware_list)) {
        middleware_count = PyList_Size(middleware_list);

        if (middleware_count > 0) {
            // Allocate middleware arrays
            middleware_functions = catzilla_cache_alloc(sizeof(void*) * middleware_count);
            middleware_priorities = catzilla_cache_alloc(sizeof(uint32_t) * middleware_count);

            if (!middleware_functions || !middleware_priorities) {
                if (middleware_functions) catzilla_cache_free(middleware_functions);
                if (middleware_priorities) catzilla_cache_free(middleware_priorities);
                PyErr_NoMemory();
                return NULL;
            }

            // Extract middleware function pointers and priorities
            for (int i = 0; i < middleware_count; i++) {
                PyObject *middleware_item = PyList_GetItem(middleware_list, i);
                if (!PyLong_Check(middleware_item)) {
                    catzilla_cache_free(middleware_functions);
                    catzilla_cache_free(middleware_priorities);
                    PyErr_SetString(PyExc_TypeError, "Middleware list must contain function IDs (integers)");
                    return NULL;
                }

                long middleware_id = PyLong_AsLong(middleware_item);
                middleware_functions[i] = (void*)(uintptr_t)middleware_id;

                // Set priority from priority_list or use default
                if (priority_list && PyList_Check(priority_list) && i < PyList_Size(priority_list)) {
                    PyObject *priority_item = PyList_GetItem(priority_list, i);
                    if (PyLong_Check(priority_item)) {
                        middleware_priorities[i] = (uint32_t)PyLong_AsLong(priority_item);
                    } else {
                        middleware_priorities[i] = 1000 + i;  // Default priority
                    }
                } else {
                    middleware_priorities[i] = 1000 + i;  // Default priority
                }
            }
        }
    }

    // Add route to global router with middleware
    uint32_t route_id = catzilla_router_add_route_with_middleware(&global_router, method, path,
                                                                  (void*)(uintptr_t)handler_id, NULL, false,
                                                                  middleware_functions, middleware_count, middleware_priorities);

    // Cleanup middleware arrays (they are copied internally)
    if (middleware_functions) catzilla_cache_free(middleware_functions);
    if (middleware_priorities) catzilla_cache_free(middleware_priorities);

    if (route_id == 0) {
        PyErr_SetString(PyExc_RuntimeError, "Failed to add route with middleware to router");
        return NULL;
    }

    return PyLong_FromLong(route_id);
}

// Check if jemalloc is available
static PyObject* has_jemalloc(PyObject *self, PyObject *args)
{
    return PyBool_FromLong(catzilla_memory_has_jemalloc());
}

// Check if jemalloc is available at runtime
static PyObject* jemalloc_available(PyObject *self, PyObject *args)
{
    return PyBool_FromLong(catzilla_memory_jemalloc_available());
}

// Get current allocator type
static PyObject* get_current_allocator(PyObject *self, PyObject *args)
{
    catzilla_allocator_type_t allocator = catzilla_memory_get_current_allocator();
    const char* allocator_name = (allocator == CATZILLA_ALLOCATOR_JEMALLOC) ? "jemalloc" : "malloc";
    return PyUnicode_FromString(allocator_name);
}

// Set allocator type before initialization
static PyObject* set_allocator(PyObject *self, PyObject *args)
{
    const char* allocator_name;
    if (!PyArg_ParseTuple(args, "s", &allocator_name)) {
        return NULL;
    }

    catzilla_allocator_type_t allocator;
    if (strcmp(allocator_name, "jemalloc") == 0) {
        allocator = CATZILLA_ALLOCATOR_JEMALLOC;
    } else if (strcmp(allocator_name, "malloc") == 0) {
        allocator = CATZILLA_ALLOCATOR_MALLOC;
    } else {
        PyErr_SetString(PyExc_ValueError, "Invalid allocator type. Use 'jemalloc' or 'malloc'");
        return NULL;
    }

    int result = catzilla_memory_set_allocator(allocator);
    if (result == -1) {
        PyErr_SetString(PyExc_RuntimeError, "Cannot change allocator after memory system initialization");
        return NULL;
    } else if (result == -2) {
        PyErr_SetString(PyExc_RuntimeError, "jemalloc not available in this build");
        return NULL;
    }

    Py_RETURN_NONE;
}

// Initialize memory system
static PyObject* init_memory_system(PyObject *self, PyObject *args)
{
    int quiet = 0;  // Default to verbose
    if (!PyArg_ParseTuple(args, "|i", &quiet)) {
        return NULL;
    }

    int result = catzilla_memory_init_quiet(quiet);
    if (result != 0) {
        PyErr_SetString(PyExc_RuntimeError, "Failed to initialize memory system");
        return NULL;
    }
    Py_RETURN_NONE;
}

// Initialize memory system with specific allocator
static PyObject* init_memory_with_allocator(PyObject *self, PyObject *args)
{
    const char* allocator_name;
    if (!PyArg_ParseTuple(args, "s", &allocator_name)) {
        return NULL;
    }

    catzilla_allocator_type_t allocator;
    if (strcmp(allocator_name, "jemalloc") == 0) {
        allocator = CATZILLA_ALLOCATOR_JEMALLOC;
    } else if (strcmp(allocator_name, "malloc") == 0) {
        allocator = CATZILLA_ALLOCATOR_MALLOC;
    } else {
        PyErr_SetString(PyExc_ValueError, "Invalid allocator type. Use 'jemalloc' or 'malloc'");
        return NULL;
    }

    int result = catzilla_memory_init_with_allocator(allocator);
    if (result != 0) {
        PyErr_SetString(PyExc_RuntimeError, "Failed to initialize memory system with specified allocator");
        return NULL;
    }
    Py_RETURN_NONE;
}

// Get memory statistics
static PyObject* get_memory_stats(PyObject *self, PyObject *args)
{
    catzilla_memory_stats_t stats;
    catzilla_memory_get_stats(&stats);

    return Py_BuildValue("{s:K,s:K,s:K,s:K,s:d,s:K,s:K,s:d,s:K,s:K,s:K,s:K,s:K,s:K}",
        "allocated", (unsigned long long)stats.allocated,
        "active", (unsigned long long)stats.active,
        "metadata", (unsigned long long)stats.metadata,
        "resident", (unsigned long long)stats.resident,
                             "fragmentation_ratio", stats.fragmentation_ratio,
        "allocation_count", (unsigned long long)stats.allocation_count,
        "deallocation_count", (unsigned long long)stats.deallocation_count,
        "memory_efficiency_score", stats.memory_efficiency_score,
        "peak_allocated", (unsigned long long)stats.peak_allocated,
        "request_arena_usage", (unsigned long long)stats.request_arena_usage,
        "response_arena_usage", (unsigned long long)stats.response_arena_usage,
        "cache_arena_usage", (unsigned long long)stats.cache_arena_usage,
        "static_arena_usage", (unsigned long long)stats.static_arena_usage,
        "task_arena_usage", (unsigned long long)stats.task_arena_usage
    );
}

// Parse multipart form data from request
static PyObject* multipart_parse(PyObject *self, PyObject *args) {
    PyObject* manager_capsule = NULL;  // Not used for now, keep for compatibility
    const char* content_type;
    const char* data;
    Py_ssize_t data_len;

    if (!PyArg_ParseTuple(args, "Oss#", &manager_capsule, &content_type, &data, &data_len))
        return NULL;

    if (!content_type || !data) {
        PyErr_SetString(PyExc_ValueError, "Invalid content type or data");
        return NULL;
    }

    // Create a temporary request structure for parsing
    catzilla_request_t temp_request = {0};
    temp_request.content_type = CONTENT_TYPE_MULTIPART;
    temp_request.body = (char*)data;
    temp_request.body_length = data_len;

    // Create a dummy client context for parsing with content type
    struct {
        const char* content_type_header;
    } dummy_context;
    dummy_context.content_type_header = content_type;

    // Parse multipart data
    int parse_result = catzilla_parse_multipart_with_context(&temp_request, &dummy_context);

    PyObject* result_dict = PyDict_New();
    if (!result_dict) {
        return NULL;
    }

    if (parse_result == 0) {
        // Extract form fields from parsed data
        for (int i = 0; i < temp_request.form_field_count; i++) {
            PyObject* key = PyUnicode_FromString(temp_request.form_fields[i]);
            PyObject* value = PyUnicode_FromString(temp_request.form_values[i]);
            if (key && value) {
                PyDict_SetItem(result_dict, key, value);
            }
            Py_XDECREF(key);
            Py_XDECREF(value);
        }
    }

    // No need to cleanup allocated memory since we use the original content_type string

    return result_dict;
}

// ============================================================================
// VALIDATOR ENGINE TYPE DEFINITIONS
// ============================================================================

// Validator methods
static PyMethodDef CatzillaValidator_methods[] = {
    {"validate", (PyCFunction)CatzillaValidator_validate, METH_VARARGS, "Validate a value"},
    {NULL}
};

static PyTypeObject CatzillaValidatorType = {
    PyVarObject_HEAD_INIT(NULL, 0)
    .tp_name      = "catzilla._catzilla.Validator",
    .tp_basicsize = sizeof(CatzillaValidatorObject),
    .tp_flags     = Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE,
    .tp_new       = CatzillaValidator_new,
    .tp_dealloc   = (destructor)CatzillaValidator_dealloc,
    .tp_methods   = CatzillaValidator_methods,
    .tp_doc       = "Ultra-fast C-accelerated field validator"
};

// Model methods
static PyMethodDef CatzillaModel_methods[] = {
    {"validate", (PyCFunction)CatzillaModel_validate, METH_VARARGS, "Validate data against model"},
    {NULL}
};

static PyTypeObject CatzillaModelType = {
    PyVarObject_HEAD_INIT(NULL, 0)
    .tp_name      = "catzilla._catzilla.Model",
    .tp_basicsize = sizeof(CatzillaModelObject),
    .tp_flags     = Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE,
    .tp_new       = CatzillaModel_new,
    .tp_dealloc   = (destructor)CatzillaModel_dealloc,
    .tp_methods   = CatzillaModel_methods,
    .tp_doc       = "Ultra-fast C-accelerated model validator"
};

// CacheResult deallocation
static void CatzillaCacheResult_dealloc(CatzillaCacheResultObject *self) {
    Py_XDECREF(self->data);
    Py_TYPE(self)->tp_free((PyObject*)self);
}

// CacheResult data property
static PyObject* CatzillaCacheResult_get_data(CatzillaCacheResultObject *self, void *closure) {
    Py_INCREF(self->data);
    return self->data;
}

// CacheResult hit property
static PyObject* CatzillaCacheResult_get_hit(CatzillaCacheResultObject *self, void *closure) {
    return PyBool_FromLong(self->hit);
}

// CacheResult properties
static PyGetSetDef CatzillaCacheResult_getsets[] = {
    {"data", (getter)CatzillaCacheResult_get_data, NULL, "Cache data", NULL},
    {"hit", (getter)CatzillaCacheResult_get_hit, NULL, "Cache hit", NULL},
    {NULL}  // Sentinel
};

// CacheResult type definition
static PyTypeObject CatzillaCacheResultType = {
    PyVarObject_HEAD_INIT(NULL, 0)
    .tp_name = "catzilla.CacheResult",
    .tp_doc = "Catzilla Cache Result object",
    .tp_basicsize = sizeof(CatzillaCacheResultObject),
    .tp_itemsize = 0,
    .tp_flags = Py_TPFLAGS_DEFAULT,
    .tp_dealloc = (destructor)CatzillaCacheResult_dealloc,
    .tp_getset = CatzillaCacheResult_getsets,
};

// Cache deallocation
static void CatzillaCache_dealloc(CatzillaCacheObject *self) {
    if (self->cache) {
        catzilla_cache_destroy(self->cache);
    }
    Py_TYPE(self)->tp_free((PyObject*)self);
}

// Cache creation
static PyObject* CatzillaCache_new(PyTypeObject *type, PyObject *args, PyObject *kwds) {
    CatzillaCacheObject *self;
    self = (CatzillaCacheObject*)type->tp_alloc(type, 0);
    if (self != NULL) {
        self->cache = NULL;
    }
    return (PyObject*)self;
}

// Cache initialization
static int CatzillaCache_init(CatzillaCacheObject *self, PyObject *args, PyObject *kwds) {
    size_t capacity = 10000;
    size_t bucket_count = 0;

    static char *kwlist[] = {"capacity", "bucket_count", NULL};

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "|nn", kwlist, &capacity, &bucket_count)) {
        return -1;
    }

    self->cache = catzilla_cache_create(capacity, bucket_count);
    if (!self->cache) {
        PyErr_SetString(PyExc_RuntimeError, "Failed to create cache");
        return -1;
    }

    return 0;
}

// Cache set method
static PyObject* CatzillaCache_set(CatzillaCacheObject *self, PyObject *args, PyObject *kwds) {
    const char *key;
    PyObject *value;
    uint32_t ttl = 0;

    static char *kwlist[] = {"key", "value", "ttl", NULL};

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "sO|I", kwlist, &key, &value, &ttl)) {
        return NULL;
    }

    // Serialize Python object using pickle
    PyObject *pickle_module = PyImport_ImportModule("pickle");
    if (!pickle_module) {
        return NULL;
    }

    PyObject *pickled = PyObject_CallMethod(pickle_module, "dumps", "O", value);
    Py_DECREF(pickle_module);
    if (!pickled) {
        return NULL;
    }

    char *data = PyBytes_AsString(pickled);
    Py_ssize_t size = PyBytes_Size(pickled);

    int result = catzilla_cache_set(self->cache, key, data, size, ttl);
    Py_DECREF(pickled);

    if (result != 0) {
        PyErr_SetString(PyExc_RuntimeError, "Failed to set cache value");
        return NULL;
    }

    Py_RETURN_NONE;
}

// Cache get method
static PyObject* CatzillaCache_get(CatzillaCacheObject *self, PyObject *args) {
    const char *key;

    if (!PyArg_ParseTuple(args, "s", &key)) {
        return NULL;
    }

    cache_result_t result = catzilla_cache_get(self->cache, key);

    CatzillaCacheResultObject *py_result = (CatzillaCacheResultObject*)CatzillaCacheResultType.tp_alloc(&CatzillaCacheResultType, 0);
    if (!py_result) {
        return NULL;
    }

    py_result->hit = result.found ? 1 : 0;

    if (result.found) {
        // Deserialize the pickled data
        PyObject *bytes_obj = PyBytes_FromStringAndSize((const char*)result.data, result.size);
        if (!bytes_obj) {
            Py_DECREF(py_result);
            return NULL;
        }

        PyObject *pickle_module = PyImport_ImportModule("pickle");
        if (!pickle_module) {
            Py_DECREF(bytes_obj);
            Py_DECREF(py_result);
            return NULL;
        }

        PyObject *unpickled = PyObject_CallMethod(pickle_module, "loads", "O", bytes_obj);
        Py_DECREF(pickle_module);
        Py_DECREF(bytes_obj);

        if (!unpickled) {
            Py_DECREF(py_result);
            return NULL;
        }

        py_result->data = unpickled;
    } else {
        Py_INCREF(Py_None);
        py_result->data = Py_None;
    }

    return (PyObject*)py_result;
}

// Cache delete method
static PyObject* CatzillaCache_delete(CatzillaCacheObject *self, PyObject *args) {
    const char *key;

    if (!PyArg_ParseTuple(args, "s", &key)) {
        return NULL;
    }

    int result = catzilla_cache_delete(self->cache, key);
    return PyBool_FromLong(result == 0);
}

// Cache clear method
static PyObject* CatzillaCache_clear(CatzillaCacheObject *self, PyObject *args) {
    catzilla_cache_clear(self->cache);
    Py_RETURN_NONE;
}

// Cache stats method
static PyObject* CatzillaCache_get_stats(CatzillaCacheObject *self, PyObject *args) {
    cache_statistics_t stats = catzilla_cache_get_stats(self->cache);

    return Py_BuildValue("{s:K,s:K,s:K,s:K,s:K}",
                         "hits", (unsigned long long)stats.hits,
                         "misses", (unsigned long long)stats.misses,
                         "evictions", (unsigned long long)stats.evictions,
                         "memory_usage", (unsigned long long)stats.memory_usage,
                         "total_requests", (unsigned long long)stats.total_requests);
}

// Cache exists method
static PyObject* CatzillaCache_exists(CatzillaCacheObject *self, PyObject *args) {
    const char *key;

    if (!PyArg_ParseTuple(args, "s", &key)) {
        return NULL;
    }

    bool exists = catzilla_cache_exists(self->cache, key);
    return PyBool_FromLong(exists);
}

// Cache methods
static PyMethodDef CatzillaCache_methods[] = {
    {"set", (PyCFunction)CatzillaCache_set, METH_VARARGS | METH_KEYWORDS, "Set a cache value"},
    {"get", (PyCFunction)CatzillaCache_get, METH_VARARGS, "Get a cache value"},
    {"delete", (PyCFunction)CatzillaCache_delete, METH_VARARGS, "Delete a cache value"},
    {"clear", (PyCFunction)CatzillaCache_clear, METH_NOARGS, "Clear all cache values"},
    {"get_stats", (PyCFunction)CatzillaCache_get_stats, METH_NOARGS, "Get cache statistics"},
    {"exists", (PyCFunction)CatzillaCache_exists, METH_VARARGS, "Check if key exists"},
    {NULL}  // Sentinel
};

// Cache type definition
static PyTypeObject CatzillaCacheType = {
    PyVarObject_HEAD_INIT(NULL, 0)
    .tp_name = "catzilla.Cache",
    .tp_doc = "Catzilla Cache object",
    .tp_basicsize = sizeof(CatzillaCacheObject),
    .tp_itemsize = 0,
    .tp_flags = Py_TPFLAGS_DEFAULT,
    .tp_new = CatzillaCache_new,
    .tp_init = (initproc)CatzillaCache_init,
    .tp_dealloc = (destructor)CatzillaCache_dealloc,
    .tp_methods = CatzillaCache_methods,
};

// Method tables and module definition
static PyMethodDef CatzillaServer_methods[] = {
    {"listen",    (PyCFunction)CatzillaServer_listen,   METH_VARARGS, "Start listening"},
    {"add_route", (PyCFunction)CatzillaServer_add_route, METH_VARARGS, "Add HTTP route"},
    {"stop",      (PyCFunction)CatzillaServer_stop,      METH_NOARGS,  "Stop server"},
    {"match_route", (PyCFunction)CatzillaServer_match_route, METH_VARARGS, "Match route using C router"},
    {"add_c_route", (PyCFunction)CatzillaServer_add_c_route, METH_VARARGS, "Add route to C router"},
    {"add_c_route_with_middleware", (PyCFunction)CatzillaServer_add_c_route_with_middleware, METH_VARARGS, "Add route to C router with per-route middleware"},
    {"add_c_route_with_middleware", (PyCFunction)CatzillaServer_add_c_route_with_middleware, METH_VARARGS, "Add route to C router with middleware"},
    {"mount_static", (PyCFunction)CatzillaServer_mount_static, METH_VARARGS | METH_KEYWORDS, "Mount a static directory"},
    {NULL}
};

static PyTypeObject CatzillaServerType = {
    PyVarObject_HEAD_INIT(NULL, 0)
    .tp_name      = "catzilla._catzilla.Server",
    .tp_basicsize = sizeof(CatzillaServerObject),
    .tp_flags     = Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE,
    .tp_new       = CatzillaServer_new,
    .tp_init      = (initproc)CatzillaServer_init,
    .tp_dealloc   = (destructor)CatzillaServer_dealloc,
    .tp_methods   = CatzillaServer_methods,
};

static PyMethodDef module_methods[] = {
    {"send_response", send_response, METH_VARARGS, "Send HTTP response"},
    {"parse_json", parse_json, METH_VARARGS, "Parse JSON from request"},
    {"get_json", get_json, METH_VARARGS, "Get parsed JSON from request"},
    {"parse_form", parse_form, METH_VARARGS, "Parse form data from request"},
    {"multipart_parse", multipart_parse, METH_VARARGS, "Parse multipart form data"},
    {"get_form_field", get_form_field, METH_VARARGS, "Get form field value"},
    {"get_header", get_header, METH_VARARGS, "Get header value from request"},
    {"get_files", get_files, METH_VARARGS, "Get uploaded files from request"},
    {"get_content_type", get_content_type, METH_VARARGS, "Get content type from request"},
    {"get_query_param", get_query_param, METH_VARARGS, "Get query parameter value"},
    {"router_match", router_match, METH_VARARGS, "Match route using C router"},
    {"router_add_route", router_add_route, METH_VARARGS, "Add route to C router"},
    {"router_add_route_with_middleware", router_add_route_with_middleware, METH_VARARGS, "Add route to C router with per-route middleware"},
    {"router_add_route_with_middleware", router_add_route_with_middleware, METH_VARARGS, "Add route to C router with middleware"},
    {"has_jemalloc", has_jemalloc, METH_NOARGS, "Check if jemalloc is available"},
    {"jemalloc_available", jemalloc_available, METH_NOARGS, "Check if jemalloc is available at runtime"},
    {"get_current_allocator", get_current_allocator, METH_NOARGS, "Get current allocator type"},
    {"set_allocator", set_allocator, METH_VARARGS, "Set allocator type before initialization"},
    {"get_memory_stats", get_memory_stats, METH_NOARGS, "Get memory statistics"},
    {"init_memory_system", init_memory_system, METH_VARARGS, "Initialize memory system"},
    {"init_memory_with_allocator", init_memory_with_allocator, METH_VARARGS, "Initialize memory system with specific allocator"},

    // Ultra-fast validation engine functions
    {"create_int_validator", (PyCFunction)create_int_validator, METH_VARARGS | METH_KEYWORDS, "Create integer validator"},
    {"create_string_validator", (PyCFunction)create_string_validator, METH_VARARGS | METH_KEYWORDS, "Create string validator"},
    {"create_float_validator", (PyCFunction)create_float_validator, METH_VARARGS | METH_KEYWORDS, "Create float validator"},
    {"create_model", (PyCFunction)create_model, METH_VARARGS | METH_KEYWORDS, "Create validation model"},
    {"get_validation_stats", get_validation_stats, METH_NOARGS, "Get validation performance statistics"},
    {"reset_validation_stats", reset_validation_stats, METH_NOARGS, "Reset validation statistics"},

    // Middleware functions
    {"register_middleware_function", register_middleware_function, METH_VARARGS, "Register a middleware function"},
    {"execute_middleware_by_id", execute_middleware_by_id, METH_VARARGS, "Execute a middleware function by ID"},
    {"convert_middleware_to_ids", convert_middleware_to_ids, METH_VARARGS, "Convert middleware function list to middleware ID list"},
    {"set_python_middleware_bridge", set_python_middleware_bridge, METH_VARARGS, "Set Python middleware execution bridge"},

    {NULL}
};

static struct PyModuleDef catzilla_module = {
    PyModuleDef_HEAD_INIT,
    "catzilla._catzilla",
    "Catzilla HTTP server module",
    -1,
    module_methods,
    NULL, NULL, NULL,
    NULL  // Module cleanup function (we'll handle cleanup manually)
};

PyMODINIT_FUNC PyInit__catzilla(void)
{
    // Initialize validation engine types
    if (PyType_Ready(&CatzillaValidatorType) < 0)
        return NULL;
    if (PyType_Ready(&CatzillaModelType) < 0)
        return NULL;
    if (PyType_Ready(&CatzillaServerType) < 0)
        return NULL;
    if (PyType_Ready(&CatzillaCacheType) < 0)
        return NULL;
    if (PyType_Ready(&CatzillaCacheResultType) < 0)
        return NULL;

    PyObject *m = PyModule_Create(&catzilla_module);
    if (!m) return NULL;

    // Initialize streaming submodule
    PyObject* streaming_m = init_streaming();
    if (streaming_m) {
        if (PyModule_AddObject(m, "_streaming", streaming_m) < 0) {
            Py_DECREF(streaming_m);
            Py_DECREF(m);
            return NULL;
        }
    }

    // Add Server type
    Py_INCREF(&CatzillaServerType);
    if (PyModule_AddObject(m, "Server", (PyObject*)&CatzillaServerType) < 0) {
        Py_DECREF(&CatzillaServerType);
        Py_DECREF(m);
        return NULL;
    }

    // Add Validator type
    Py_INCREF(&CatzillaValidatorType);
    if (PyModule_AddObject(m, "Validator", (PyObject*)&CatzillaValidatorType) < 0) {
        Py_DECREF(&CatzillaValidatorType);
        Py_DECREF(m);
        return NULL;
    }

    // Add Model type
    Py_INCREF(&CatzillaModelType);
    if (PyModule_AddObject(m, "Model", (PyObject*)&CatzillaModelType) < 0) {
        Py_DECREF(&CatzillaModelType);
        Py_DECREF(m);
        return NULL;
    }

    // Add Cache type
    Py_INCREF(&CatzillaCacheType);
    if (PyModule_AddObject(m, "Cache", (PyObject*)&CatzillaCacheType) < 0) {
        Py_DECREF(&CatzillaCacheType);
        Py_DECREF(m);
        return NULL;
    }

    // Add CacheResult type
    Py_INCREF(&CatzillaCacheResultType);
    if (PyModule_AddObject(m, "CacheResult", (PyObject*)&CatzillaCacheResultType) < 0) {
        Py_DECREF(&CatzillaCacheResultType);
        Py_DECREF(m);
        return NULL;
    }

    PyModule_AddStringConstant(m, "VERSION", "0.1.0");

    // Initialize middleware registry
    if (init_middleware_registry() < 0) {
        Py_DECREF(m);
        return NULL;
    }

    // Register cleanup function
    if (Py_AtExit(safe_module_cleanup) < 0) {
        Py_DECREF(m);
        return NULL;
    }

    // Initialize and add streaming module
    PyObject* streaming_module = init_streaming();
    if (streaming_module) {
        if (PyModule_AddObject(m, "_streaming", streaming_module) < 0) {
            Py_DECREF(streaming_module);
            Py_DECREF(m);
            return NULL;
        }
    } else {
        // Log warning but don't fail - streaming is an optional feature
        LOG_WARN("Module", "Failed to initialize streaming module");
    }

    // Initialize async bridge system for hybrid sync/async execution
    if (catzilla_async_bridge_init(uv_default_loop()) < 0) {
        LOG_ERROR("Module", "Failed to initialize async bridge system");
        // Don't fail the module init - async support is optional
    } else {
        LOG_INFO("Module", "Async bridge system initialized successfully");
    }

    return m;
}
