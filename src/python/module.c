#define PY_SSIZE_T_CLEAN
#include <Python.h>
#include "server.h"           // Provides catzilla_server_t, catzilla_server_init, etc.
#include <uv.h>               // For uv_stream_t
#include <stdio.h>
#include <string.h>
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
} CatzillaServerObject;

// Deallocate
static void CatzillaServer_dealloc(CatzillaServerObject *self)
{
    if (self->route_data) {
        Py_XDECREF(self->route_data->callback);
        Py_XDECREF(self->route_data->routes);
        free(self->route_data);
    }
    catzilla_server_cleanup(&self->server);
    Py_TYPE(self)->tp_free((PyObject*)self);
}

// __new__
static PyObject* CatzillaServer_new(PyTypeObject *type, PyObject *args, PyObject *kwds)
{
    CatzillaServerObject *self = (CatzillaServerObject*)type->tp_alloc(type, 0);
    if (self) {
        memset(&self->server, 0, sizeof(self->server));
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

    // Allocate routing data
    self->route_data = malloc(sizeof(PyRouteData));
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
    return 0;
}

// listen(port, host="0.0.0.0")
static PyObject* CatzillaServer_listen(CatzillaServerObject *self, PyObject *args)
{
    const char *host = "0.0.0.0";
    int port;
    if (!PyArg_ParseTuple(args, "i|s", &port, &host))
        return NULL;

    printf("[DEBUG] Listening on %s:%d\n", host, port);
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

    // Register route with C core
    if (catzilla_server_add_route(&self->server, method, path, NULL, NULL) != 0) {
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

// send_response(client_capsule, status, content_type, body)
static PyObject* send_response(PyObject *self, PyObject *args)
{
    PyObject *capsule;
    int status;
    const char *ctype, *body;
    if (!PyArg_ParseTuple(args, "Oiss", &capsule, &status, &ctype, &body))
        return NULL;

    uv_stream_t *client = PyCapsule_GetPointer(capsule, "catzilla.client");
    if (!client) {
        PyErr_SetString(PyExc_TypeError, "Invalid client capsule");
        return NULL;
    }
    catzilla_send_response(client, status, ctype, body, strlen(body));
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

// Method tables and module definition
static PyMethodDef CatzillaServer_methods[] = {
    {"listen",    (PyCFunction)CatzillaServer_listen,   METH_VARARGS, "Start listening"},
    {"add_route", (PyCFunction)CatzillaServer_add_route, METH_VARARGS, "Add HTTP route"},
    {"stop",      (PyCFunction)CatzillaServer_stop,      METH_NOARGS,  "Stop server"},
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
    {NULL}
};

static struct PyModuleDef catzilla_module = {
    PyModuleDef_HEAD_INIT,
    "catzilla._catzilla",
    "Catzilla HTTP server module",
    -1,
    module_methods
};

PyMODINIT_FUNC PyInit__catzilla(void)
{
    if (PyType_Ready(&CatzillaServerType) < 0)
        return NULL;

    PyObject *m = PyModule_Create(&catzilla_module);
    if (!m) return NULL;

    Py_INCREF(&CatzillaServerType);
    if (PyModule_AddObject(m, "Server", (PyObject*)&CatzillaServerType) < 0) {
        Py_DECREF(&CatzillaServerType);
        Py_DECREF(m);
        return NULL;
    }
    PyModule_AddStringConstant(m, "VERSION", "0.1.0");
    return m;
}
