#ifndef CATZILLA_SERVER_H
#define CATZILLA_SERVER_H

#include <stdbool.h>
#include <uv.h>
#include <llhttp.h>
#include <yyjson.h>
#include "router.h"
#include "upload_parser.h"

// Forward declaration for streaming support
typedef struct catzilla_stream_context_s catzilla_stream_context_t;
struct catzilla_stream_context_s;

// Function declarations for streaming support
bool catzilla_is_streaming_response(const char* body, size_t body_len);
int catzilla_send_streaming_response(uv_stream_t* client,
                                    int status_code,
                                    const char* content_type,
                                    const char* streaming_marker);
catzilla_stream_context_t* catzilla_stream_create(uv_stream_t* client, size_t buffer_size);

#define CATZILLA_MAX_ROUTES 100
#define CATZILLA_PATH_MAX 256
#define CATZILLA_METHOD_MAX 32
#define CATZILLA_MAX_HEADERS 50
#define CATZILLA_MAX_FORM_FIELDS 50
#define CATZILLA_MAX_QUERY_PARAMS 50
#define CATZILLA_MAX_FILES 20

// Forward declaration
struct catzilla_server_s;

typedef enum {
    CONTENT_TYPE_NONE = 0,
    CONTENT_TYPE_JSON = 1,
    CONTENT_TYPE_FORM = 2,
    CONTENT_TYPE_MULTIPART = 3
} content_type_t;

typedef struct catzilla_header_s {
    char* name;
    char* value;
} catzilla_header_t;

typedef struct catzilla_request_s {
    char method[CATZILLA_METHOD_MAX];
    char path[CATZILLA_PATH_MAX];
    char* body;
    size_t body_length;
    content_type_t content_type;
    catzilla_header_t headers[CATZILLA_MAX_HEADERS];
    int header_count;
    yyjson_doc* json_doc;  // Parsed JSON document
    yyjson_val* json_root; // Root value of JSON document
    bool is_json_parsed;
    char* form_fields[CATZILLA_MAX_FORM_FIELDS];
    char* form_values[CATZILLA_MAX_FORM_FIELDS];
    int form_field_count;
    bool is_form_parsed;
    // Query parameter support
    char* query_params[CATZILLA_MAX_QUERY_PARAMS];
    char* query_values[CATZILLA_MAX_QUERY_PARAMS];
    int query_param_count;
    bool has_query_params;
    // Path parameter support
    catzilla_route_param_t path_params[CATZILLA_MAX_PATH_PARAMS];
    int path_param_count;
    bool has_path_params;
    // File upload support
    catzilla_upload_file_t* files[CATZILLA_MAX_FILES];
    int file_count;
    bool has_files;
} catzilla_request_t;

// Forward declaration for static file mounts
struct catzilla_server_mount;

typedef struct catzilla_server_s {
    // libuv
    uv_loop_t* loop;
    uv_tcp_t server;
    uv_signal_t sig_handle;  // For SIGINT handling
    uv_signal_t sigterm_handle;  // For SIGTERM handling

    // HTTP parser
    llhttp_settings_t parser_settings;

    // Advanced router
    catzilla_router_t router;

    // Legacy route table (for backward compatibility)
    catzilla_route_t routes[CATZILLA_MAX_ROUTES];
    int route_count;

    // Static file serving
    struct catzilla_server_mount* static_mounts;  // Linked list of static mounts
    int static_mount_count;                       // Number of static mounts

    // State
    bool is_running;

    // Python request callback
    void* py_request_callback;
} catzilla_server_t;

/**
 * Initialize a server
 * @param server Pointer to server structure
 * @return 0 on success, error code on failure
 */
int catzilla_server_init(catzilla_server_t* server);

/**
 * Clean up server resources
 * @param server Pointer to server structure
 */
void catzilla_server_cleanup(catzilla_server_t* server);

/**
 * Universal Python route handler for advanced router
 * @param client Client connection
 */
void catzilla_python_route_handler(uv_stream_t* client);

/**
 * Parse JSON from request body
 * @param request Pointer to request structure
 * @return 0 on success, error code on failure
 */
int catzilla_parse_json(catzilla_request_t* request);

/**
 * Parse form data from request body
 * @param request Pointer to request structure
 * @return 0 on success, error code on failure
 */
int catzilla_parse_form(catzilla_request_t* request);

/**
 * Parse multipart form data from request body
 * @param request Pointer to request structure
 * @return 0 on success, error code on failure
 */
int catzilla_parse_multipart(catzilla_request_t* request);

/**
 * Get JSON value from request
 * @param request Pointer to request structure
 * @return Pointer to yyjson_val or NULL if not JSON request
 */
yyjson_val* catzilla_get_json(catzilla_request_t* request);

/**
 * Get form field value
 * @param request Pointer to request structure
 * @param field Field name to look up
 * @return Field value or NULL if not found
 */
const char* catzilla_get_form_field(catzilla_request_t* request, const char* field);

/**
 * Get query parameter value
 * @param request Pointer to request structure
 * @param param Parameter name to look up
 * @return Parameter value or NULL if not found
 */
const char* catzilla_get_query_param(catzilla_request_t* request, const char* param);

/**
 * Get path parameter value
 * @param request Pointer to request structure
 * @param param Parameter name to look up
 * @return Parameter value or NULL if not found
 */
const char* catzilla_get_path_param(catzilla_request_t* request, const char* param);

/**
 * Start listening on the given address
 * @param server Pointer to server structure
 * @param host Host address (e.g. "127.0.0.1")
 * @param port Port number
 * @return 0 on success, error code on failure
 */
int catzilla_server_listen(catzilla_server_t* server, const char* host, int port);

/**
 * Stop the server
 * @param server Pointer to server structure
 */
void catzilla_server_stop(catzilla_server_t* server);

/**
 * Add a route to the server
 * @param server Pointer to server structure
 * @param method HTTP method (e.g. "GET", "POST") or "*" for any
 * @param path URL path (e.g. "/users") or "*" for any
 * @param handler Function pointer to route handler
 * @param user_data User data pointer passed to handler
 * @return 0 on success, error code on failure
 */
int catzilla_server_add_route(catzilla_server_t* server,
                             const char* method,
                             const char* path,
                             void* handler,
                             void* user_data);

/**
 * Set the Python request callback
 * @param server Pointer to server structure
 * @param callback Python callable object
 */
void catzilla_server_set_request_callback(catzilla_server_t* server, void* callback);

/**
 * Send an HTTP response
 * @param client Client connection
 * @param status_code HTTP status code
 * @param content_type Content type header value
 * @param body Response body content
 * @param body_len Length of body in bytes
 */
void catzilla_send_response(uv_stream_t* client,
                           int status_code,
                           const char* content_type,
                           const char* body,
                           size_t body_len);

// Get content type as string
const char* catzilla_get_content_type_str(catzilla_request_t* request);

// Helper function for URL decoding
void url_decode(const char* src, char* dst);

/**
 * Print all registered routes for debugging
 * @param server Pointer to server structure
 */
void catzilla_server_print_routes(catzilla_server_t* server);

/**
 * Get count of registered routes in advanced router
 * @param server Pointer to server structure
 * @return Number of routes registered
 */
int catzilla_server_get_route_count(catzilla_server_t* server);

/**
 * Check if a route exists for the given method and path
 * @param server Pointer to server structure
 * @param method HTTP method
 * @param path URL path
 * @return 1 if route exists, 0 if not found, -1 on error
 */
int catzilla_server_has_route(catzilla_server_t* server, const char* method, const char* path);

/**
 * Get detailed route match information for debugging
 * @param server Pointer to server structure
 * @param method HTTP method
 * @param path URL path
 * @param match_info Output buffer for match information
 * @param buffer_size Size of output buffer
 * @return 0 on success, -1 on error
 */
int catzilla_server_get_route_info(catzilla_server_t* server,
                                   const char* method,
                                   const char* path,
                                   char* match_info,
                                   size_t buffer_size);

/**
 * Check for route conflicts and emit warnings
 * @param server Pointer to server structure
 * @param method HTTP method of new route
 * @param path URL path of new route
 */
void catzilla_server_check_route_conflicts(catzilla_server_t* server, const char* method, const char* path);

/**
 * Parse multipart form data with context for boundary extraction
 * @param request Pointer to request structure
 * @param context Pointer to client context containing full Content-Type header
 * @return 0 on success, error code on failure
 */
int catzilla_parse_multipart_with_context(catzilla_request_t* request, void* context);

#endif /* CATZILLA_SERVER_H */
