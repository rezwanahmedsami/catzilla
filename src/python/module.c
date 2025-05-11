#define PY_SSIZE_T_CLEAN
#include <Python.h>
#include "server.h"           // Provides catzilla_server_t, catzilla_server_init, etc.
#include <uv.h>               // For uv_stream_t
#include <stdio.h>
#include <string.h>

// Structure to hold Python callback and routing table
typedef struct {
    PyObject *callback;
    PyObject *routes;
} PyRouteData;

// Forward declaration of shim that C core will call
typedef void (*c_request_cb)(uv_stream_t *client,
                             const char *method,
                             const char *path,
                             const char *body,
                             void *user_data);
static void c_request_shim(uv_stream_t *client,
                           const char *method,
                           const char *path,
                           const char *body,
                           void *user_data);

// Internal helper: invoke Python handler (assumes GIL held)
PyObject* handle_request(PyObject *callback,
                                PyObject *client_capsule,
                                const char *method,
                                const char *path,
                                const char *body){
    printf("[DEBUG] handle_request: %s %s", method, path);
    if (body && body[0]) {
        printf("[DEBUG] Body: %s", body);
    }
    // Call Python callback: signature (client_capsule, method, path, body)
    PyObject *result = PyObject_CallFunction(callback, "Osss",
                                              client_capsule,
                                              method,
                                              path,
                                              body ? body : "");
    if (!result) {
        PyErr_Print();
        printf("[ERROR] Callback exception");
    }
    return result;
}
    // Call Python callback: signature (client_capsule, method, path, body)
//     PyObject *result = PyObject_CallFunction(callback, "Osss",
//                                               client_capsule,
//                                               method,
//                                               path,
//                                               body ? body : "");
//     if (!result) {
//         PyErr_Print();
//         printf("[ERROR] Callback exception\n");
//     }
//     return result;
// }

// Shim called by C core on each HTTP request
static void c_request_shim(uv_stream_t *client,
                           const char *method,
                           const char *path,
                           const char *body,
                           void *user_data)
{
    PyRouteData *ud = (PyRouteData*)user_data;

    // Acquire GIL for Python C-API use
    PyGILState_STATE gstate = PyGILState_Ensure();

    // Wrap the client pointer in a Python capsule
    PyObject *capsule = PyCapsule_New((void*)client, "catzilla.client", NULL);
    if (!capsule) {
        PyErr_Print();
        goto cleanup_gil;
    }

    // Call Python handler
    PyObject *py_resp = handle_request(ud->callback, capsule, method, path, body);
    Py_XDECREF(py_resp);
    Py_DECREF(capsule);

cleanup_gil:
    PyGILState_Release(gstate);
}

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

    // Register route with C core, using our shim
    if (catzilla_server_add_route(&self->server,
                                  method,
                                  path,
                                  (void*)c_request_shim,
                                  self->route_data) != 0)
    {
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
