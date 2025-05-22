// main.c
#include "server.h"
#include <stdio.h>
#include <stdlib.h>

// Route handlers in pure C
static void handle_root(uv_stream_t* client) {
    const char* body = "<html><body><h1>Welcome to Catzilla Server</h1></body></html>";
    catzilla_send_response(client, 200, "text/html", body, strlen(body));
}

static void handle_about(uv_stream_t* client) {
    const char* body = "<html><body><h1>About Catzilla Server</h1><p>This is a lightweight HTTP server.</p></body></html>";
    catzilla_send_response(client, 200, "text/html", body, strlen(body));
}

static void handle_health(uv_stream_t* client) {
    const char* body = "{\"status\": \"healthy\"}";
    catzilla_send_response(client, 200, "application/json", body, strlen(body));
}

static void handle_default(uv_stream_t* client) {
    const char* body = "<html><body><h1>404 Not Found</h1><p>The requested resource was not found on this server.</p></body></html>";
    catzilla_send_response(client, 404, "text/html", body, strlen(body));
}

int main(int argc, char** argv) {
    catzilla_server_t server;

    if (catzilla_server_init(&server) != 0) {
        fprintf(stderr, "Failed to initialize server\n");
        return EXIT_FAILURE;
    }

    // Register C routes
    catzilla_server_add_route(&server, "GET", "/",       handle_root,    NULL);
    catzilla_server_add_route(&server, "GET", "/about",  handle_about,   NULL);
    catzilla_server_add_route(&server, "GET", "/health", handle_health,  NULL);
    catzilla_server_add_route(&server, "*",   "*",       handle_default, NULL);

    const char* host = "127.0.0.1";
    int port = 8080;
    if (catzilla_server_listen(&server, host, port) != 0) {
        fprintf(stderr, "Failed to start server on %s:%d\n", host, port);
        catzilla_server_cleanup(&server);
        return EXIT_FAILURE;
    }

    printf("Server running on %s:%d\n", host, port);
    catzilla_server_cleanup(&server);
    return EXIT_SUCCESS;
}
