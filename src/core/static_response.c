#include "static_server.h"
#include "memory.h"
#include "logging.h"  // Add logging header
#include <string.h>
#include <stdio.h>
#include <stdlib.h>

// HTTP status text mapping
static const char* get_status_text(int status_code) {
    switch (status_code) {
        case 200: return "OK";
        case 206: return "Partial Content";
        case 304: return "Not Modified";
        case 400: return "Bad Request";
        case 403: return "Forbidden";
        case 404: return "Not Found";
        case 413: return "Payload Too Large";
        case 416: return "Range Not Satisfiable";
        case 500: return "Internal Server Error";
        default: return "Unknown";
    }
}

// Build HTTP response headers
static char* build_http_response(int status_code,
                                static_http_headers_t* headers,
                                const char* body,
                                size_t body_len,
                                size_t* total_len_out) {
    char status_line[128];
    snprintf(status_line, sizeof(status_line), "HTTP/1.1 %d %s\r\n",
             status_code, get_status_text(status_code));

    // Calculate approximate header size
    size_t header_size = strlen(status_line) + 512; // Conservative estimate

    // Add body length to total
    size_t total_size = header_size + body_len;
    char* response = catzilla_response_alloc(total_size);
    if (!response) return NULL;

    size_t offset = 0;

    // Add status line
    offset += snprintf(response + offset, total_size - offset, "%s", status_line);

    // Add content type
    if (headers && headers->content_type[0]) {
        offset += snprintf(response + offset, total_size - offset,
                          "Content-Type: %s\r\n", headers->content_type);
    }

    // Add content length
    if (headers && headers->content_length[0]) {
        offset += snprintf(response + offset, total_size - offset,
                          "Content-Length: %s\r\n", headers->content_length);
    } else {
        offset += snprintf(response + offset, total_size - offset,
                          "Content-Length: %zu\r\n", body_len);
    }

    // Add ETag if present
    if (headers && headers->etag[0]) {
        offset += snprintf(response + offset, total_size - offset,
                          "ETag: \"%s\"\r\n", headers->etag);
    }

    // Add Last-Modified if present
    if (headers && headers->last_modified[0]) {
        offset += snprintf(response + offset, total_size - offset,
                          "Last-Modified: %s\r\n", headers->last_modified);
    }

    // Add Cache-Control if present
    if (headers && headers->cache_control[0]) {
        offset += snprintf(response + offset, total_size - offset,
                          "Cache-Control: %s\r\n", headers->cache_control);
    }

    // Add Accept-Ranges if present
    if (headers && headers->accept_ranges[0]) {
        offset += snprintf(response + offset, total_size - offset,
                          "Accept-Ranges: %s\r\n", headers->accept_ranges);
    }

    // Add Content-Range if present (for range requests)
    if (headers && headers->content_range[0]) {
        offset += snprintf(response + offset, total_size - offset,
                          "Content-Range: %s\r\n", headers->content_range);
    }

    // Add security headers
    if (headers) {
        if (headers->x_content_type_options[0]) {
            offset += snprintf(response + offset, total_size - offset,
                              "X-Content-Type-Options: %s\r\n",
                              headers->x_content_type_options);
        }
        if (headers->x_frame_options[0]) {
            offset += snprintf(response + offset, total_size - offset,
                              "X-Frame-Options: %s\r\n", headers->x_frame_options);
        }
        if (headers->x_xss_protection[0]) {
            offset += snprintf(response + offset, total_size - offset,
                              "X-XSS-Protection: %s\r\n", headers->x_xss_protection);
        }
    }

    // Add connection header
    offset += snprintf(response + offset, total_size - offset,
                      "Connection: keep-alive\r\n");

    // End headers
    offset += snprintf(response + offset, total_size - offset, "\r\n");

    // Add body if present
    if (body && body_len > 0) {
        memcpy(response + offset, body, body_len);
        offset += body_len;
    }

    *total_len_out = offset;
    return response;
}

// Write callback for libuv
static void on_write_complete(uv_write_t* req, int status) {
    if (req->data) {
        catzilla_response_free(req->data);  // Free response buffer
    }
    catzilla_response_free(req);  // Free write request
}

int catzilla_static_send_file_response(uv_stream_t* client,
                                       void* file_data,
                                       size_t file_size,
                                       const char* mime_type,
                                       static_http_headers_t* headers) {
    LOG_STATIC_DEBUG("send_file_response: client=%p, file_data=%p, file_size=%zu, mime_type=%s",
                     client, file_data, file_size, mime_type ? mime_type : "NULL");

    if (!client || !file_data || file_size == 0) {
        LOG_STATIC_ERROR("send_file_response: Invalid parameters - client=%p, file_data=%p, file_size=%zu",
                        client, file_data, file_size);
        return -1;
    }

    // Build headers with default values if not provided
    static_http_headers_t default_headers;
    if (!headers) {
        memset(&default_headers, 0, sizeof(default_headers));
        strncpy(default_headers.content_type, mime_type ? mime_type : "application/octet-stream",
                STATIC_MAX_MIME_TYPE_LEN - 1);
        snprintf(default_headers.content_length, sizeof(default_headers.content_length),
                "%zu", file_size);

        // Add default security headers
        strcpy(default_headers.x_content_type_options, "nosniff");
        strcpy(default_headers.x_frame_options, "DENY");
        strcpy(default_headers.x_xss_protection, "1; mode=block");

        // Add accept ranges for file serving
        strcpy(default_headers.accept_ranges, "bytes");

        headers = &default_headers;
    }

    // Build HTTP response
    size_t response_len;
    LOG_STATIC_DEBUG("Building HTTP response for %zu bytes of file data", file_size);
    char* response = build_http_response(200, headers, (const char*)file_data,
                                        file_size, &response_len);
    if (!response) {
        LOG_STATIC_ERROR("Failed to build HTTP response");
        return -1;
    }

    LOG_STATIC_DEBUG("HTTP response built successfully: response=%p, response_len=%zu",
                     response, response_len);

    // Create write request
    uv_write_t* write_req = catzilla_response_alloc(sizeof(uv_write_t));
    if (!write_req) {
        catzilla_response_free(response);
        return -1;
    }

    write_req->data = response;  // Store response buffer for cleanup

    uv_buf_t buf = uv_buf_init(response, response_len);
    int result = uv_write(write_req, client, &buf, 1, on_write_complete);

    if (result != 0) {
        catzilla_response_free(response);
        catzilla_response_free(write_req);
        return result;
    }

    return 0;
}

int catzilla_static_send_error_response(uv_stream_t* client,
                                        int status_code,
                                        const char* message) {
    if (!client) return -1;

    const char* default_message = get_status_text(status_code);
    if (!message) message = default_message;

    // Create simple HTML error page
    char error_body[512];
    snprintf(error_body, sizeof(error_body),
             "<!DOCTYPE html>\n"
             "<html><head><title>%d %s</title></head>\n"
             "<body><h1>%d %s</h1><p>%s</p></body></html>\n",
             status_code, default_message, status_code, default_message, message);

    // Build headers for error response
    static_http_headers_t headers;
    memset(&headers, 0, sizeof(headers));
    strcpy(headers.content_type, "text/html; charset=utf-8");
    snprintf(headers.content_length, sizeof(headers.content_length),
             "%zu", strlen(error_body));

    // Add security headers
    strcpy(headers.x_content_type_options, "nosniff");
    strcpy(headers.x_frame_options, "DENY");
    strcpy(headers.x_xss_protection, "1; mode=block");

    // Build HTTP response
    size_t response_len;
    char* response = build_http_response(status_code, &headers, error_body,
                                        strlen(error_body), &response_len);
    if (!response) return -1;

    // Create write request
    uv_write_t* write_req = catzilla_response_alloc(sizeof(uv_write_t));
    if (!write_req) {
        catzilla_response_free(response);
        return -1;
    }

    write_req->data = response;  // Store response buffer for cleanup

    uv_buf_t buf = uv_buf_init(response, response_len);
    int result = uv_write(write_req, client, &buf, 1, on_write_complete);

    if (result != 0) {
        catzilla_response_free(response);
        catzilla_response_free(write_req);
        return result;
    }

    return 0;
}

int catzilla_static_send_cached_response(uv_stream_t* client,
                                         hot_cache_entry_t* cache_entry) {
    if (!client || !cache_entry) return -1;

    // Build headers for cached response
    static_http_headers_t headers;
    memset(&headers, 0, sizeof(headers));

    // Get MIME type from file path
    const char* mime_type = catzilla_static_get_content_type(cache_entry->file_path);
    strncpy(headers.content_type, mime_type, STATIC_MAX_MIME_TYPE_LEN - 1);

    snprintf(headers.content_length, sizeof(headers.content_length),
             "%zu", cache_entry->content_size);

    // Generate ETag from cached data
    snprintf(headers.etag, STATIC_MAX_ETAG_LEN, "%lx",
             (unsigned long)cache_entry->etag_hash);

    // Add cache control
    strcpy(headers.cache_control, "public, max-age=3600");

    // Add security headers
    strcpy(headers.x_content_type_options, "nosniff");
    strcpy(headers.x_frame_options, "DENY");
    strcpy(headers.x_xss_protection, "1; mode=block");
    strcpy(headers.accept_ranges, "bytes");

    return catzilla_static_send_file_response(client, cache_entry->file_content,
                                              cache_entry->content_size,
                                              mime_type, &headers);
}

int catzilla_static_send_head_response(uv_stream_t* client,
                                       size_t file_size,
                                       const char* mime_type,
                                       static_http_headers_t* headers) {
    if (!client) return -1;

    // For HEAD requests, send headers without body
    return catzilla_static_send_file_response(client, "", 0, mime_type, headers);
}
