#include <Python.h>
#include <stdbool.h>
#include <string.h>
#include <stdlib.h>
#include "../core/streaming.h"
#include "../core/server.h"

// Define the Python StreamingResponse object structure
typedef struct {
    PyObject_HEAD
    catzilla_stream_context_t* stream_ctx;
    PyObject* iterator;          // Python generator or iterator
    PyObject* content_type;      // Content-type header
    int status_code;             // HTTP status code
    bool closed;                 // Has the stream been closed?
    PyObject* on_close_callback; // Optional callback to call when stream closes
} StreamingResponse;

// Forward declarations
static PyObject* StreamingResponse_new(PyTypeObject* type, PyObject* args, PyObject* kwds);
static void StreamingResponse_dealloc(StreamingResponse* self);
static int StreamingResponse_init(StreamingResponse* self, PyObject* args, PyObject* kwds);
static PyObject* StreamingResponse_write(StreamingResponse* self, PyObject* args);
static PyObject* StreamingResponse_close(StreamingResponse* self, PyObject* args);
static PyObject* StreamingResponse_flush(StreamingResponse* self, PyObject* args);

// Callback handlers
static void stream_chunk_callback(void* ctx, const char* data, size_t len);
static void stream_backpressure_callback(void* ctx, bool active);

// StreamingResponse Python methods
static PyMethodDef StreamingResponse_methods[] = {
    {"write", (PyCFunction)StreamingResponse_write, METH_VARARGS,
     "Write data to the streaming response"},
    {"close", (PyCFunction)StreamingResponse_close, METH_NOARGS,
     "Close the streaming response"},
    {"flush", (PyCFunction)StreamingResponse_flush, METH_NOARGS,
     "Flush any buffered data to the client"},
    {NULL}  // Sentinel
};

// StreamingResponse Python Type
static PyTypeObject StreamingResponseType = {
    PyVarObject_HEAD_INIT(NULL, 0)
    .tp_name = "catzilla.StreamingResponse",
    .tp_doc = "HTTP Streaming Response",
    .tp_basicsize = sizeof(StreamingResponse),
    .tp_itemsize = 0,
    .tp_flags = Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE,
    .tp_new = StreamingResponse_new,
    .tp_init = (initproc)StreamingResponse_init,
    .tp_dealloc = (destructor)StreamingResponse_dealloc,
    .tp_methods = StreamingResponse_methods,
};

// Create a new StreamingResponse object
static PyObject* StreamingResponse_new(PyTypeObject* type, PyObject* args, PyObject* kwds) {
    StreamingResponse* self = (StreamingResponse*)type->tp_alloc(type, 0);
    if (self != NULL) {
        self->stream_ctx = NULL;
        self->iterator = NULL;
        self->content_type = NULL;
        self->status_code = 200;
        self->closed = false;
        self->on_close_callback = NULL;
    }
    return (PyObject*)self;
}

// Initialize a StreamingResponse object
static int StreamingResponse_init(StreamingResponse* self, PyObject* args, PyObject* kwds) {
    static char* kwlist[] = {"iterator", "content_type", "status_code", NULL};
    PyObject* iterator = NULL;
    PyObject* content_type = NULL;
    int status_code = 200;

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "O|Si", kwlist,
                                     &iterator, &content_type, &status_code))
        return -1;

    // Check if iterator is iterable
    if (!PyIter_Check(iterator) && !PyCallable_Check(iterator)) {
        PyErr_SetString(PyExc_TypeError, "First argument must be an iterator or callable");
        return -1;
    }

    // Set the content type if provided, otherwise default to "text/plain"
    if (content_type == NULL) {
        content_type = PyUnicode_FromString("text/plain");
        if (content_type == NULL)
            return -1;
    } else {
        Py_INCREF(content_type);
    }

    // Clean up any existing objects
    Py_XDECREF(self->iterator);
    Py_XDECREF(self->content_type);

    // Set the new values
    self->iterator = iterator;
    Py_INCREF(iterator);
    self->content_type = content_type;
    self->status_code = status_code;

    return 0;
}

// Deallocate a StreamingResponse object
static void StreamingResponse_dealloc(StreamingResponse* self) {
    // Call close if not already closed
    if (!self->closed && self->stream_ctx) {
        catzilla_stream_finish(self->stream_ctx);
        self->closed = true;
    }

    // Clean up the stream context
    if (self->stream_ctx) {
        catzilla_stream_destroy(self->stream_ctx);
        self->stream_ctx = NULL;
    }

    // Call the on_close callback if set
    if (self->on_close_callback) {
        PyObject* result = PyObject_CallObject(self->on_close_callback, NULL);
        Py_XDECREF(result);
        Py_DECREF(self->on_close_callback);
        self->on_close_callback = NULL;
    }

    // Release Python objects
    Py_XDECREF(self->iterator);
    Py_XDECREF(self->content_type);

    Py_TYPE(self)->tp_free((PyObject*)self);
}

// Write data to the streaming response
static PyObject* StreamingResponse_write(StreamingResponse* self, PyObject* args) {
    const char* data;
    Py_ssize_t data_len;

    if (!PyArg_ParseTuple(args, "s#", &data, &data_len))
        return NULL;

    if (self->closed) {
        PyErr_SetString(PyExc_RuntimeError, "Cannot write to closed StreamingResponse");
        return NULL;
    }

    // Make sure stream context exists
    if (!self->stream_ctx) {
        PyErr_SetString(PyExc_RuntimeError, "StreamingResponse not connected to a client");
        return NULL;
    }

    // Write data to the stream
    int result = catzilla_stream_write_chunk(self->stream_ctx, data, data_len);
    if (result != CATZILLA_STREAM_OK) {
        if (result == CATZILLA_STREAM_EBACKPRESSURE) {
            // Handle backpressure by waiting
            catzilla_stream_wait_for_drain(self->stream_ctx, 0);  // Wait indefinitely

            // Try again after backpressure is relieved
            result = catzilla_stream_write_chunk(self->stream_ctx, data, data_len);
        }

        if (result != CATZILLA_STREAM_OK) {
            PyErr_Format(PyExc_IOError, "Failed to write to stream: error code %d", result);
            return NULL;
        }
    }

    Py_RETURN_NONE;
}

// Close the streaming response
static PyObject* StreamingResponse_close(StreamingResponse* self, PyObject* args) {
    if (!self->closed && self->stream_ctx) {
        catzilla_stream_finish(self->stream_ctx);
        self->closed = true;

        // Call the on_close callback if set
        if (self->on_close_callback) {
            PyObject* result = PyObject_CallObject(self->on_close_callback, NULL);
            Py_XDECREF(result);
            Py_DECREF(self->on_close_callback);
            self->on_close_callback = NULL;
        }
    }

    Py_RETURN_NONE;
}

// Flush any buffered data
static PyObject* StreamingResponse_flush(StreamingResponse* self, PyObject* args) {
    // No explicit flush needed with current implementation
    // The data is written to the client as soon as possible
    Py_RETURN_NONE;
}

// Callback for monitoring chunk writes
static void stream_chunk_callback(void* ctx, const char* data, size_t len) {
    // This could be enhanced to call back into Python for monitoring
    // Currently not used
}

// Callback for backpressure events
static void stream_backpressure_callback(void* ctx, bool active) {
    // This could be enhanced to call back into Python for monitoring
    // Currently not used
}

// Function to initialize a streaming response for a client
static PyObject* py_create_streaming_response(PyObject* self, PyObject* args, PyObject* kwds) {
    PyObject* client_capsule;
    PyObject* iterator;
    PyObject* content_type = NULL;
    int status_code = 200;
    PyObject* on_close_callback = NULL;

    static char* kwlist[] = {"client", "iterator", "content_type", "status_code", "on_close", NULL};

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "OO|SiO", kwlist,
                                    &client_capsule, &iterator, &content_type,
                                    &status_code, &on_close_callback))
        return NULL;

    // Check if client is a valid PyCapsule
    if (!PyCapsule_CheckExact(client_capsule)) {
        PyErr_SetString(PyExc_TypeError, "client must be a PyCapsule");
        return NULL;
    }

    // Extract client handle from capsule
    uv_stream_t* client = PyCapsule_GetPointer(client_capsule, "uv_stream_t");
    if (!client) {
        PyErr_SetString(PyExc_ValueError, "Invalid client capsule");
        return NULL;
    }

    // Set default content type if not provided
    if (content_type == NULL) {
        content_type = PyUnicode_FromString("text/plain");
        if (content_type == NULL)
            return NULL;
    }

    // Check on_close callback
    if (on_close_callback && !PyCallable_Check(on_close_callback)) {
        PyErr_SetString(PyExc_TypeError, "on_close must be callable");
        return NULL;
    }

    // Create Python StreamingResponse object
    PyObject* response_args = Py_BuildValue("(OSi)", iterator, content_type, status_code);
    if (!response_args)
        return NULL;

    PyObject* response_obj = PyObject_Call((PyObject*)&StreamingResponseType, response_args, NULL);
    Py_DECREF(response_args);

    if (!response_obj)
        return NULL;

    // Set up the C streaming context
    StreamingResponse* response = (StreamingResponse*)response_obj;

    // Create streaming context
    response->stream_ctx = catzilla_stream_create(client, 0);  // Use default buffer size
    if (!response->stream_ctx) {
        Py_DECREF(response_obj);
        PyErr_SetString(PyExc_RuntimeError, "Failed to create streaming context");
        return NULL;
    }

    // Set callbacks
    catzilla_stream_set_callbacks(response->stream_ctx,
                                stream_chunk_callback,
                                stream_backpressure_callback,
                                response);

    // Save on_close callback
    if (on_close_callback) {
        response->on_close_callback = on_close_callback;
        Py_INCREF(on_close_callback);
    }

    // Send initial headers with streaming marker
    const char* streaming_marker = "___CATZILLA_STREAMING___";
    const char* content_type_str = PyUnicode_AsUTF8(content_type);
    catzilla_send_streaming_response(client, status_code, content_type_str, streaming_marker);

    return response_obj;
}

// Create a streaming response connected to a client
static PyObject* py_connect_streaming_response(PyObject* self, PyObject* args) {
    PyObject* client_capsule;
    const char* streaming_id;

    if (!PyArg_ParseTuple(args, "Os", &client_capsule, &streaming_id))
        return NULL;

    // Check if client is a valid PyCapsule
    if (!PyCapsule_CheckExact(client_capsule)) {
        PyErr_SetString(PyExc_TypeError, "client must be a PyCapsule");
        return NULL;
    }

    // Extract client handle from capsule
    uv_stream_t* client = PyCapsule_GetPointer(client_capsule, "catzilla.client");
    if (!client) {
        PyErr_SetString(PyExc_ValueError, "Invalid client capsule");
        return NULL;
    }

    // Find the Python StreamingResponse by ID
    PyObject* catzilla_module = PyImport_ImportModule("catzilla.streaming");
    if (!catzilla_module) {
        return NULL;
    }

    PyObject* get_func = PyObject_GetAttrString(catzilla_module, "_get_streaming_response");
    if (!get_func) {
        Py_DECREF(catzilla_module);
        return NULL;
    }

    PyObject* id_arg = PyUnicode_FromString(streaming_id);
    if (!id_arg) {
        Py_DECREF(get_func);
        Py_DECREF(catzilla_module);
        return NULL;
    }

    PyObject* py_response = PyObject_CallFunctionObjArgs(get_func, id_arg, NULL);
    Py_DECREF(id_arg);
    Py_DECREF(get_func);
    // Don't decref catzilla_module yet - we need it later

    if (!py_response || py_response == Py_None) {
        Py_XDECREF(py_response);
        Py_DECREF(catzilla_module);
        PyErr_SetString(PyExc_ValueError, "StreamingResponse not found for given ID");
        return NULL;
    }

    // Get the content generator from the Python StreamingResponse
    PyObject* content = PyObject_GetAttrString(py_response, "_content");
    if (!content) {
        Py_DECREF(py_response);
        Py_DECREF(catzilla_module);
        PyErr_SetString(PyExc_AttributeError, "StreamingResponse missing _content attribute");
        return NULL;
    }

    // Get content type and status
    PyObject* content_type = PyObject_GetAttrString(py_response, "_content_type");
    PyObject* status_code = PyObject_GetAttrString(py_response, "_status_code");

    if (!content_type || !status_code) {
        Py_XDECREF(content);
        Py_XDECREF(content_type);
        Py_XDECREF(status_code);
        Py_DECREF(py_response);
        Py_DECREF(catzilla_module);
        PyErr_SetString(PyExc_AttributeError, "StreamingResponse missing required attributes");
        return NULL;
    }

    int status = PyLong_AsLong(status_code);
    const char* content_type_str = PyUnicode_AsUTF8(content_type);

    // Get headers from the StreamingResponse
    PyObject* headers_obj = PyObject_GetAttrString(py_response, "_headers");

    // Check if custom headers already include Connection header
    bool has_connection_header = false;
    if (headers_obj && PyDict_Check(headers_obj)) {
        PyObject* connection_key = PyUnicode_FromString("connection");
        if (connection_key) {
            has_connection_header = PyDict_Contains(headers_obj, connection_key);
            Py_DECREF(connection_key);
        }
    }

    // Build the response headers string
    char response_headers[2048];  // Increased buffer size
    int offset = snprintf(response_headers, sizeof(response_headers),
        "HTTP/1.1 %d OK\r\n"
        "Content-Type: %s\r\n"
        "Transfer-Encoding: chunked\r\n",
        status, content_type_str);

    // Add Connection header only if not already in custom headers
    if (!has_connection_header) {
        offset += snprintf(response_headers + offset,
                          sizeof(response_headers) - offset,
                          "Connection: keep-alive\r\n");
    }

    // Add custom headers if present
    if (headers_obj && PyDict_Check(headers_obj)) {
        PyObject* key, *value;
        Py_ssize_t pos = 0;

        while (PyDict_Next(headers_obj, &pos, &key, &value)) {
            const char* key_str = PyUnicode_AsUTF8(key);
            const char* value_str = PyUnicode_AsUTF8(value);

            if (key_str && value_str && offset < sizeof(response_headers) - 100) {
                offset += snprintf(response_headers + offset,
                                 sizeof(response_headers) - offset,
                                 "%s: %s\r\n", key_str, value_str);
            }
        }
    }

    // Add final CRLF to separate headers from body
    if (offset < sizeof(response_headers) - 3) {
        strcpy(response_headers + offset, "\r\n");
        offset += 2;
    }

    // Clean up Python object reference
    Py_XDECREF(headers_obj);

    // Send response headers using uv_write
    uv_buf_t header_buf = uv_buf_init(response_headers, offset);
    uv_write_t* header_req = malloc(sizeof(uv_write_t));
    if (header_req) {
        uv_write(header_req, client, &header_buf, 1, NULL);  // Fire and forget for now
    }

    // Start streaming the content
    PyObject* iterator = content;

    // Check if content is callable, and call it if so
    if (PyCallable_Check(iterator)) {
        PyObject* iter_result = PyObject_CallObject(iterator, NULL);
        if (!iter_result) {
            Py_DECREF(content);
            Py_DECREF(content_type);
            Py_DECREF(status_code);
            Py_DECREF(py_response);
            Py_DECREF(catzilla_module);
            return NULL;
        }
        iterator = iter_result;
    } else {
        Py_INCREF(iterator);
    }

    // Get the iterator and stream chunks
    PyObject* iter = PyObject_GetIter(iterator);
    Py_DECREF(iterator);

    if (!iter) {
        Py_DECREF(content);
        Py_DECREF(content_type);
        Py_DECREF(status_code);
        Py_DECREF(py_response);
        Py_DECREF(catzilla_module);
        return NULL;
    }

    // Stream each chunk with HTTP chunked encoding
    PyObject* item;
    while ((item = PyIter_Next(iter)) != NULL) {
        const char* data;
        Py_ssize_t data_len;

        if (PyUnicode_Check(item)) {
            data = PyUnicode_AsUTF8AndSize(item, &data_len);
        } else if (PyBytes_Check(item)) {
            PyBytes_AsStringAndSize(item, (char**)&data, &data_len);
        } else {
            Py_DECREF(item);
            Py_DECREF(iter);
            Py_DECREF(content);
            Py_DECREF(content_type);
            Py_DECREF(status_code);
            Py_DECREF(py_response);
            Py_DECREF(catzilla_module);
            PyErr_SetString(PyExc_TypeError, "Iterator must yield strings or bytes");
            return NULL;
        }

        if (data && data_len > 0) {
            // Create chunk: size in hex + CRLF + data + CRLF
            char* full_chunk = malloc(data_len + 64);  // Extra space for headers
            if (full_chunk) {
                int header_len = snprintf(full_chunk, 32, "%lx\r\n", (unsigned long)data_len);
                memcpy(full_chunk + header_len, data, data_len);
                memcpy(full_chunk + header_len + data_len, "\r\n", 2);

                size_t total_len = header_len + data_len + 2;

                // Send chunk using uv_write
                uv_buf_t chunk_buf = uv_buf_init(full_chunk, total_len);
                uv_write_t* chunk_req = malloc(sizeof(uv_write_t));
                if (chunk_req) {
                    chunk_req->data = full_chunk;  // Store pointer for cleanup
                    uv_write(chunk_req, client, &chunk_buf, 1, NULL);  // Fire and forget for now
                }
            }
        }

        Py_DECREF(item);
    }

    Py_DECREF(iter);

    // Check for iteration error
    if (PyErr_Occurred()) {
        Py_DECREF(content);
        Py_DECREF(content_type);
        Py_DECREF(status_code);
        Py_DECREF(py_response);
        Py_DECREF(catzilla_module);
        return NULL;
    }

    // Send final chunk to end the stream
    char* end_chunk = strdup("0\r\n\r\n");
    if (end_chunk) {
        uv_buf_t end_buf = uv_buf_init(end_chunk, 5);
        uv_write_t* end_req = malloc(sizeof(uv_write_t));
        if (end_req) {
            end_req->data = end_chunk;
            uv_write(end_req, client, &end_buf, 1, NULL);
        }
    }

    // Cleanup
    Py_DECREF(content);
    Py_DECREF(content_type);
    Py_DECREF(status_code);
    Py_DECREF(py_response);

    // Unregister the streaming response
    PyObject* unregister_func = PyObject_GetAttrString(catzilla_module, "_unregister_streaming_response");
    if (unregister_func) {
        PyObject* id_arg2 = PyUnicode_FromString(streaming_id);
        PyObject_CallFunctionObjArgs(unregister_func, id_arg2, NULL);
        Py_DECREF(id_arg2);
        Py_DECREF(unregister_func);
    }
    Py_DECREF(catzilla_module);

    Py_RETURN_NONE;
}

static PyMethodDef streaming_methods[] = {
    {"create_streaming_response", (PyCFunction)py_create_streaming_response,
     METH_VARARGS | METH_KEYWORDS, "Create a streaming response for a client"},
    {"connect_streaming_response", (PyCFunction)py_connect_streaming_response,
     METH_VARARGS, "Connect a streaming response to a client by ID"},
    {NULL, NULL, 0, NULL}  // Sentinel
};

// Module initialization function
PyObject* init_streaming(void) {
    // Initialize the StreamingResponseType
    if (PyType_Ready(&StreamingResponseType) < 0)
        return NULL;

    // Create the module
    static struct PyModuleDef moduledef = {
        PyModuleDef_HEAD_INIT,
        "catzilla._streaming",
        "Catzilla streaming module",
        -1,
        streaming_methods,
    };

    PyObject* module = PyModule_Create(&moduledef);

    if (module == NULL)
        return NULL;

    // Add the StreamingResponse type to the module
    Py_INCREF(&StreamingResponseType);
    if (PyModule_AddObject(module, "StreamingResponse", (PyObject*)&StreamingResponseType) < 0) {
        Py_DECREF(&StreamingResponseType);
        Py_DECREF(module);
        return NULL;
    }

    return module;
}
