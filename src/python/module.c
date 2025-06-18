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
#include "../core/windows_compat.h"   // Windows compatibility
#include <stdio.h>
#include <string.h>
#include <math.h>             // For HUGE_VAL
#include <yyjson.h>

// Structure to hold Python callback and routing table
typedef struct {
    PyObject *callback;
    PyObject *routes;
} PyRouteData;

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

// Forward declarations for type objects
static PyTypeObject CatzillaValidatorType;
static PyTypeObject CatzillaModelType;
static PyTypeObject CatzillaServerType;

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

    // Add route to C router with middleware and route_id as user_data
    uint32_t c_route_id = catzilla_router_add_route_with_middleware(&self->py_router, method, path,
                                                                    (void*)(uintptr_t)route_id, NULL, false,
                                                                    middleware_functions, middleware_count, middleware_priorities);

    // Cleanup middleware arrays (they are copied internally)
    if (middleware_functions) catzilla_cache_free(middleware_functions);
    if (middleware_priorities) catzilla_cache_free(middleware_priorities);

    if (c_route_id == 0) {
        PyErr_SetString(PyExc_RuntimeError, "Failed to add route with middleware to C router");
        return NULL;
    }

    return PyLong_FromLong(c_route_id);
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

// Global router for module-level functions
static catzilla_router_t global_router;
static bool global_router_initialized = false;

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
    int result = catzilla_memory_init();
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

// ============================================================================
// VALIDATION ENGINE TYPE DEFINITIONS
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

// Method tables and module definition
static PyMethodDef CatzillaServer_methods[] = {
    {"listen",    (PyCFunction)CatzillaServer_listen,   METH_VARARGS, "Start listening"},
    {"add_route", (PyCFunction)CatzillaServer_add_route, METH_VARARGS, "Add HTTP route"},
    {"stop",      (PyCFunction)CatzillaServer_stop,      METH_NOARGS,  "Stop server"},
    {"match_route", (PyCFunction)CatzillaServer_match_route, METH_VARARGS, "Match route using C router"},
    {"add_c_route", (PyCFunction)CatzillaServer_add_c_route, METH_VARARGS, "Add route to C router"},
    {"add_c_route_with_middleware", (PyCFunction)CatzillaServer_add_c_route_with_middleware, METH_VARARGS, "Add route to C router with per-route middleware"},
    {"add_c_route_with_middleware", (PyCFunction)CatzillaServer_add_c_route_with_middleware, METH_VARARGS, "Add route to C router with middleware"},
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
    {"get_form_field", get_form_field, METH_VARARGS, "Get form field value"},
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
    {"init_memory_system", init_memory_system, METH_NOARGS, "Initialize memory system"},
    {"init_memory_with_allocator", init_memory_with_allocator, METH_VARARGS, "Initialize memory system with specific allocator"},

    // Ultra-fast validation engine functions
    {"create_int_validator", (PyCFunction)create_int_validator, METH_VARARGS | METH_KEYWORDS, "Create integer validator"},
    {"create_string_validator", (PyCFunction)create_string_validator, METH_VARARGS | METH_KEYWORDS, "Create string validator"},
    {"create_float_validator", (PyCFunction)create_float_validator, METH_VARARGS | METH_KEYWORDS, "Create float validator"},
    {"create_model", (PyCFunction)create_model, METH_VARARGS | METH_KEYWORDS, "Create validation model"},
    {"get_validation_stats", get_validation_stats, METH_NOARGS, "Get validation performance statistics"},
    {"reset_validation_stats", reset_validation_stats, METH_NOARGS, "Reset validation statistics"},

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

    PyObject *m = PyModule_Create(&catzilla_module);
    if (!m) return NULL;

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

    PyModule_AddStringConstant(m, "VERSION", "0.1.0");
    return m;
}
