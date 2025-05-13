#include "server.h"
#include <stdlib.h>
#include <string.h>
#include <stdio.h>
#include <signal.h>
#include <Python.h>

typedef struct {
    uv_write_t req;
    uv_buf_t buf;
} write_req_t;

typedef struct {
    llhttp_t parser;
    uv_tcp_t client;
    catzilla_server_t* server;
    char url[CATZILLA_PATH_MAX];
    char method[CATZILLA_METHOD_MAX];
    char* body;
    size_t body_length;
    size_t body_size;
} client_context_t;

// Forward declarations
static void on_connection(uv_stream_t* server, int status);
static void alloc_buffer(uv_handle_t* handle, size_t suggested_size, uv_buf_t* buf);
static void on_read(uv_stream_t* client, ssize_t nread, const uv_buf_t* buf);
static void on_close(uv_handle_t* handle);
static void after_write(uv_write_t* req, int status);
static void signal_handler(uv_signal_t* handle, int signum);

// Global reference to the active server for signal handling
static catzilla_server_t* active_server = NULL;

static int on_message_begin(llhttp_t* parser) {
    client_context_t* context = (client_context_t*)parser->data;
    context->url[0] = '\0';
    context->method[0] = '\0';
    free(context->body);
    context->body = NULL;
    context->body_length = 0;
    context->body_size = 0;
    return 0;
}

static int on_url(llhttp_t* parser, const char* at, size_t length) {
    client_context_t* context = (client_context_t*)parser->data;
    if (length >= CATZILLA_PATH_MAX) length = CATZILLA_PATH_MAX - 1;
    memcpy(context->url, at, length);
    context->url[length] = '\0';
    return 0;
}

static int on_header_field(llhttp_t* parser, const char* at, size_t length) { return 0; }
static int on_header_value(llhttp_t* parser, const char* at, size_t length) { return 0; }

static int on_headers_complete(llhttp_t* parser) {
    client_context_t* context = (client_context_t*)parser->data;
    const char* method = llhttp_method_name(parser->method);
    size_t method_len = strlen(method);
    if (method_len >= CATZILLA_METHOD_MAX) method_len = CATZILLA_METHOD_MAX - 1;
    memcpy(context->method, method, method_len);
    context->method[method_len] = '\0';
    return 0;
}

static int on_body(llhttp_t* parser, const char* at, size_t length) {
    client_context_t* context = (client_context_t*)parser->data;
    if (context->body == NULL) {
        context->body_size = length > 1024 ? length : 1024;
        context->body = malloc(context->body_size + 1);
        if (!context->body) return -1;
        context->body_length = 0;
    } else if (context->body_length + length > context->body_size) {
        size_t new_size = context->body_size * 2;
        char* new_body = realloc(context->body, new_size + 1);
        if (!new_body) return -1;
        context->body = new_body;
        context->body_size = new_size;
    }
    memcpy(context->body + context->body_length, at, length);
    context->body_length += length;
    context->body[context->body_length] = '\0';
    return 0;
}

// Python callback helper
extern PyObject* handle_request_in_server(PyObject* callback, PyObject* client_capsule, const char* method, const char* path, const char* body);

static int on_message_complete(llhttp_t* parser) {
    client_context_t* context = (client_context_t*)parser->data;
    catzilla_server_t* server = context->server;

    fprintf(stderr, "[DEBUG] HTTP message complete\n");
    fprintf(stderr, "[INFO] Received request: Method=%s, URL=%s\n", context->method, context->url);
    
    // 1) If Python callback is set, hand off to Python and return
    if (server->py_request_callback != NULL) {
        PyGILState_STATE gstate = PyGILState_Ensure();
        PyObject* client_capsule = PyCapsule_New((void*)&context->client, "catzilla.client", NULL);
        if (!client_capsule) {
            PyErr_Print();
            catzilla_send_response((uv_stream_t*)&context->client, 500, "text/plain", "500 Internal Server Error", strlen("500 Internal Server Error"));
        } else {
            PyObject* result = handle_request_in_server(
                server->py_request_callback,
                client_capsule,
                context->method,
                context->url,
                context->body ? context->body : ""  // Handle NULL body case
            );
            Py_XDECREF(result);
            Py_DECREF(client_capsule);
        }
        PyGILState_Release(gstate);
        return 0;
    }

    // 2) Local C route dispatch
    catzilla_route_t* matched = NULL;
    for (int i = 0; i < server->route_count; i++) {
        catzilla_route_t* route = &server->routes[i];
        bool method_ok = (route->method[0] == '*' || strcmp(route->method, context->method) == 0);
        bool path_ok   = (route->path[0]   == '*' || strcmp(route->path, context->url) == 0);
        if (method_ok && path_ok) {
            matched = route;
            break;
        }
    }

    if (matched) {
        // Call the handler
        void (*handler_fn)(uv_stream_t*) = matched->handler;
        if (handler_fn != NULL) {
            handler_fn((uv_stream_t*)&context->client);
        } else {
            // Handler is NULL
            const char* body = "500 Internal Server Error: NULL handler";
            catzilla_send_response((uv_stream_t*)&context->client, 500, "text/plain", body, strlen(body));
        }
    } else {
        // No route → 404
        const char* body = "404 Not Found";
        catzilla_send_response((uv_stream_t*)&context->client, 404, "text/plain", body, strlen(body));
    }

    return 0;
}

int catzilla_server_init(catzilla_server_t* server) {
    memset(server, 0, sizeof(*server));
    server->loop = uv_default_loop();
    if (!server->loop) return -1;

    int rc = uv_tcp_init(server->loop, &server->server);
    if (rc) return rc;
    server->server.data = server;

    // Initialize signal handler
    rc = uv_signal_init(server->loop, &server->sig_handle);
    if (rc) return rc;
    server->sig_handle.data = server;

    llhttp_settings_init(&server->parser_settings);
    server->parser_settings.on_message_begin  = on_message_begin;
    server->parser_settings.on_url            = on_url;
    server->parser_settings.on_header_field   = on_header_field;
    server->parser_settings.on_header_value   = on_header_value;
    server->parser_settings.on_headers_complete = on_headers_complete;
    server->parser_settings.on_body           = on_body;
    server->parser_settings.on_message_complete = on_message_complete;

    server->route_count = 0;
    server->is_running = false;
    server->py_request_callback = NULL;
    
    // Set global reference for signal handling
    active_server = server;
    
    return 0;
}

void signal_handler(uv_signal_t* handle, int signum) {
    fprintf(stderr, "\n[INFO] Signal %d received, stopping server...\n", signum);
    catzilla_server_t* server = (catzilla_server_t*)handle->data;
    catzilla_server_stop(server);
}

void catzilla_server_cleanup(catzilla_server_t* server) {
    server->is_running = false;
    uv_close((uv_handle_t*)&server->server, NULL);
    uv_close((uv_handle_t*)&server->sig_handle, NULL);
    uv_run(server->loop, UV_RUN_DEFAULT);
    active_server = NULL;
}

int catzilla_server_listen(catzilla_server_t* server, const char* host, int port) {
    struct sockaddr_in addr;
    int rc = uv_ip4_addr(host, port, &addr);
    if (rc) {
        fprintf(stderr, "[ERROR] Failed to resolve %s:%d: %s\n", host, port, uv_strerror(rc));
        return rc;
    }
    rc = uv_tcp_bind(&server->server, (const struct sockaddr*)&addr, 0);
    if (rc) {
        fprintf(stderr, "[ERROR] Bind %s:%d: %s\n", host, port, uv_strerror(rc));
        return rc;
    }
    rc = uv_listen((uv_stream_t*)&server->server, 128, on_connection);
    if (rc) {
        fprintf(stderr, "[ERROR] Listen %s:%d: %s\n", host, port, uv_strerror(rc));
        return rc;
    }
    
    // Set up signal handler for graceful shutdown
    rc = uv_signal_start(&server->sig_handle, signal_handler, SIGINT);
    if (rc) {
        fprintf(stderr, "[ERROR] Failed to set up signal handler: %s\n", uv_strerror(rc));
        return rc;
    }
    
    fprintf(stderr, "[INFO] Catzilla server listening on %s:%d\n", host, port);
    fprintf(stderr, "[INFO] Press Ctrl+C to stop the server\n");
    
    server->is_running = true;
    return uv_run(server->loop, UV_RUN_DEFAULT);
}


void catzilla_server_stop(catzilla_server_t* server) {
    if (!server->is_running) return;
    
    fprintf(stderr, "[INFO] Stopping Catzilla server...\n");
    server->is_running = false;
    
    //  Stop the loop so the outer uv_run in listen() will exit
    uv_stop(server->loop);
    
    // Stop the signal handler but don't close it yet
    uv_signal_stop(&server->sig_handle);
    fprintf(stderr, "[INFO] Stopped signal handler...\n");
    
    // Walk and close all active handles
    // This will include server->server and server->sig_handle
    uv_walk(server->loop, (uv_walk_cb)uv_close, NULL);
    fprintf(stderr, "[INFO] Closing all active handles...\n");
    
    // Run the loop so that each close callback fires
    uv_run(server->loop, UV_RUN_DEFAULT);

    // 5) Finally, close the loop itself
    if (uv_loop_close(server->loop) != 0) {
        fprintf(stderr, "[WARN] uv_loop_close returned busy\n");
    }
    
    fprintf(stderr, "[INFO] Server stopped\n");
}

int catzilla_server_add_route(catzilla_server_t* server,
                             const char* method,
                             const char* path,
                             void* handler,
                             void* user_data) {
    if (server->route_count >= CATZILLA_MAX_ROUTES) return -1;
    catzilla_route_t* route = &server->routes[server->route_count++];
    strncpy(route->method, method, CATZILLA_METHOD_MAX-1);
    route->method[CATZILLA_METHOD_MAX-1] = '\0';
    strncpy(route->path, path,   CATZILLA_PATH_MAX-1);
    route->path[CATZILLA_PATH_MAX-1] = '\0';
    route->handler = handler;
    route->user_data = user_data;
    return 0;
}

void catzilla_server_set_request_callback(catzilla_server_t* server, void* callback) {
    server->py_request_callback = callback;
}

void catzilla_send_response(uv_stream_t* client,
                           int status_code,
                           const char* content_type,
                           const char* body,
                           size_t body_len) {
    write_req_t* req = malloc(sizeof(*req));
    if (!req) return;
    const char* status_text;
    switch (status_code) {
        case 200: status_text="OK";break;
        case 201: status_text="Created";break;
        case 204: status_text="No Content";break;
        case 400: status_text="Bad Request";break;
        case 404: status_text="Not Found";break;
        case 500: status_text="Internal Server Error";break;
        default:  status_text="Unknown";break;
    }
    char header[512];
    int header_len = snprintf(header, sizeof(header),
        "HTTP/1.1 %d %s\r\n"
        "Content-Type: %s\r\n"
        "Content-Length: %zu\r\n"
        "Connection: close\r\n\r\n",
        status_code, status_text,
        content_type, body_len);
    char* response = malloc(header_len + body_len);
    if (!response) { free(req); return; }
    memcpy(response, header, header_len);
    memcpy(response+header_len, body, body_len);

    req->buf = uv_buf_init(response, header_len + body_len);
    uv_write(&req->req, client, &req->buf, 1, after_write);
}

static void on_connection(uv_stream_t* server, int status) {
    if (status < 0) {
        fprintf(stderr, "[DEBUG] Connection error: %s\n", uv_strerror(status));
        return;
    }
    fprintf(stderr, "[DEBUG] New connection received\n");
    catzilla_server_t* srv = server->data;

    client_context_t* ctx = malloc(sizeof(*ctx));
    if (!ctx) return;
    memset(ctx, 0, sizeof(*ctx));
    ctx->server = srv;

    if (uv_tcp_init(srv->loop, &ctx->client) != 0) {
        free(ctx);
        return;
    }
    ctx->client.data = ctx;
    llhttp_init(&ctx->parser, HTTP_REQUEST, &srv->parser_settings);
    ctx->parser.data = ctx;

    if (uv_accept(server, (uv_stream_t*)&ctx->client) != 0) {
        uv_close((uv_handle_t*)&ctx->client, on_close);
        return;
    }
    uv_read_start((uv_stream_t*)&ctx->client, alloc_buffer, on_read);
}

static void alloc_buffer(uv_handle_t* handle, size_t suggested_size, uv_buf_t* buf) {
    buf->base = malloc(suggested_size);
    buf->len  = buf->base ? suggested_size : 0;
}

static void on_read(uv_stream_t* client, ssize_t nread, const uv_buf_t* buf) {
    client_context_t* ctx = client->data;
    if (nread > 0) {
        llhttp_errno_t err = llhttp_execute(&ctx->parser, buf->base, nread);
        if (err != HPE_OK) {
            fprintf(stderr, "HTTP parsing error: %s\n", llhttp_errno_name(err));
            catzilla_send_response(client, 400, "text/plain", "400 Bad Request", strlen("400 Bad Request"));
            uv_close((uv_handle_t*)client, on_close);
        }
    } else if (nread < 0 && nread != UV_EOF) {
        fprintf(stderr, "Read error: %s\n", uv_strerror(nread));
    }
    free(buf->base);
    if (nread < 0) uv_close((uv_handle_t*)client, on_close);
}

static void on_close(uv_handle_t* handle) {
    client_context_t* ctx = handle->data;
    free(ctx->body);
    free(ctx);
}

static void after_write(uv_write_t* req, int status) {
    if (status < 0) fprintf(stderr, "[DEBUG] Write error: %s\n", uv_strerror(status));
    write_req_t* wr = (write_req_t*)req;
    uv_close((uv_handle_t*)req->handle, on_close);
    free(wr->buf.base);
    free(wr);
}

// ----------------------------------------------------------------------------
// Python bridge helper – make sure this lives in server.c so the symbol
// actually gets compiled into _catzilla.so
// ----------------------------------------------------------------------------
PyObject* handle_request_in_server(PyObject* callback,
    PyObject* client_capsule,
    const char* method,
    const char* path,
    const char* body)
{
    if (!callback || !PyCallable_Check(callback)) {
        PyErr_SetString(PyExc_TypeError, "Callback is not callable");
        return NULL;
    }

    // Build arguments tuple: (client_capsule, method, path, body)
    PyObject* args = Py_BuildValue("(Osss)", client_capsule, method, path, body ? body : "");
    if (!args) {
        PyErr_Print();
        return NULL;
    }

    // Call the Python function
    PyObject* result = PyObject_CallObject(callback, args);
    Py_DECREF(args);

    if (!result) {
        PyErr_Print();
        return NULL;
    }
    return result;
}