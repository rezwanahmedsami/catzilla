#ifndef CATZILLA_SERVER_H
#define CATZILLA_SERVER_H

#include <uv.h>
#include <llhttp.h>
#include <stdbool.h>

#define CATZILLA_MAX_ROUTES 100
#define CATZILLA_PATH_MAX 256
#define CATZILLA_METHOD_MAX 16

typedef struct {
    char method[CATZILLA_METHOD_MAX];
    char path[CATZILLA_PATH_MAX];
    void* handler;  // Python callable object
    void* user_data;  // Additional data to pass to handler
} catzilla_route_t;

typedef struct {
    uv_loop_t* loop;
    uv_tcp_t server;
    llhttp_settings_t parser_settings;
    catzilla_route_t routes[CATZILLA_MAX_ROUTES];
    int route_count;
    bool is_running;
    
    // Python references
    void* py_request_callback;  // Python callback for handling requests
} catzilla_server_t;

// Initialize the server
int catzilla_server_init(catzilla_server_t* server);

// Clean up server resources
void catzilla_server_cleanup(catzilla_server_t* server);

// Start the server on a given port
int catzilla_server_listen(catzilla_server_t* server, const char* host, int port);

// Stop the server
void catzilla_server_stop(catzilla_server_t* server);

// Add a route handler
int catzilla_server_add_route(catzilla_server_t* server, 
                             const char* method, 
                             const char* path, 
                             void* handler,
                             void* user_data);

// Set the Python request callback
void catzilla_server_set_request_callback(catzilla_server_t* server, void* callback);

// Send HTTP response
void catzilla_send_response(uv_stream_t* client,
                           int status_code, 
                           const char* content_type, 
                           const char* body, 
                           size_t body_len);

#endif /* CATZILLA_SERVER_H */