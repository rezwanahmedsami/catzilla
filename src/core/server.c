#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <uv.h>

#define PORT 8080
#define RESPONSE "HTTP/1.1 200 OK\r\n" \
                 "Content-Type: text/plain\r\n" \
                 "Content-Length: 13\r\n" \
                 "\r\n" \
                 "Hello Catzilla!"

uv_loop_t *loop;

// Custom buffer allocator
void alloc_buffer(uv_handle_t *handle, size_t suggested_size, uv_buf_t *buf) {
    buf->base = malloc(suggested_size);
    buf->len = suggested_size;
}

void on_write(uv_write_t *req, int status) {
    if (status < 0) fprintf(stderr, "Write error: %s\n", uv_strerror(status));
    uv_close((uv_handle_t*)req->handle, NULL);
    free(req);
}

void on_read(uv_stream_t *client, ssize_t nread, const uv_buf_t *buf) {
    if (nread < 0) {
        uv_close((uv_handle_t*) client, NULL);
        return;
    }
    
    if (nread > 0) {
        uv_write_t *req = malloc(sizeof(uv_write_t));
        uv_buf_t res_buf = uv_buf_init(RESPONSE, strlen(RESPONSE));
        uv_write(req, client, &res_buf, 1, on_write);
    }
    
    if (buf->base) free(buf->base);
}

void on_new_connection(uv_stream_t *server, int status) {
    if (status < 0) {
        fprintf(stderr, "Connection error: %s\n", uv_strerror(status));
        return;
    }

    uv_tcp_t *client = malloc(sizeof(uv_tcp_t));
    uv_tcp_init(loop, client);
    
    if (uv_accept(server, (uv_stream_t*) client) != 0) {
        uv_close((uv_handle_t*) client, NULL);
        return;
    }

    uv_read_start((uv_stream_t*) client, alloc_buffer, on_read);
}

int main() {
    loop = uv_default_loop();

    uv_tcp_t server;
    uv_tcp_init(loop, &server);

    struct sockaddr_in addr;
    uv_ip4_addr("0.0.0.0", PORT, &addr);

    uv_tcp_bind(&server, (const struct sockaddr*)&addr, 0);
    int err = uv_listen((uv_stream_t*) &server, 128, on_new_connection);
    
    if (err) {
        fprintf(stderr, "Listen error: %s\n", uv_strerror(err));
        return 1;
    }

    printf("Catzilla server running on port %d\n", PORT);
    return uv_run(loop, UV_RUN_DEFAULT);
}