#include "static_server.h"
#include "platform_compat.h"
#include "memory.h"
#include "logging.h"
#include <string.h>
#include <stdio.h>
#include <stdlib.h>
#include <sys/stat.h>
#ifndef _WIN32
#include <unistd.h>
#endif
#include <errno.h>

// Forward declarations for internal functions
static void on_file_stat(uv_fs_t* req);
static void on_file_open(uv_fs_t* req);
static void on_file_fstat(uv_fs_t* req);
static void on_file_read(uv_fs_t* req);
static void on_sendfile_complete(uv_fs_t* req);
static void cache_cleanup_timer_cb(uv_timer_t* timer);
static uint32_t hash_path(const char* path);
static int catzilla_static_serve_cached_file(static_file_context_t* ctx);

// External function declarations
extern void catzilla_static_cache_remove_unlocked(hot_cache_t* cache, const char* file_path);
extern int catzilla_static_send_cached_response(uv_stream_t* client, hot_cache_entry_t* cache_entry);

// Default MIME type mappings
static const struct {
    const char* extension;
    const char* mime_type;
    bool compressible;
} mime_types[] = {
    {".html", "text/html; charset=utf-8", true},
    {".css", "text/css; charset=utf-8", true},
    {".js", "application/javascript; charset=utf-8", true},
    {".json", "application/json; charset=utf-8", true},
    {".xml", "application/xml; charset=utf-8", true},
    {".png", "image/png", false},
    {".jpg", "image/jpeg", false},
    {".jpeg", "image/jpeg", false},
    {".gif", "image/gif", false},
    {".svg", "image/svg+xml", true},
    {".webp", "image/webp", false},
    {".ico", "image/x-icon", false},
    {".woff", "font/woff", false},
    {".woff2", "font/woff2", false},
    {".ttf", "font/ttf", false},
    {".otf", "font/otf", false},
    {".mp4", "video/mp4", false},
    {".mp3", "audio/mpeg", false},
    {".pdf", "application/pdf", false},
    {".zip", "application/zip", false},
    {".tar", "application/x-tar", false},
    {".gz", "application/gzip", false},
    {"", "application/octet-stream", false}  // Default
};

int catzilla_static_server_init(catzilla_static_server_t* server,
                                static_server_config_t* config) {
    if (!server || !config) return -1;

    // Copy configuration
    server->config = *config;
    server->loop = config->loop;

    // Initialize statistics
    catzilla_atomic_store(&server->requests_served, 0);
    catzilla_atomic_store(&server->bytes_served, 0);
    catzilla_atomic_store(&server->cache_hits, 0);
    catzilla_atomic_store(&server->cache_misses, 0);
    catzilla_atomic_store(&server->sendfile_operations, 0);

    // Initialize cache if enabled
    if (config->enable_hot_cache) {
        server->cache = catzilla_static_alloc(sizeof(hot_cache_t));
        if (!server->cache) return -1;

        if (catzilla_static_cache_init(server->cache, config->cache_size_mb * 1024 * 1024) != 0) {
            catzilla_free(server->cache);
            server->cache = NULL;
            return -1;
        }

        // Setup cache cleanup timer
        if (uv_timer_init(server->loop, &server->cache_cleanup_timer) != 0) {
            catzilla_static_cache_cleanup(server->cache);
            catzilla_free(server->cache);
            server->cache = NULL;
            return -1;
        }

        server->cache_cleanup_timer.data = server;
        uv_timer_start(&server->cache_cleanup_timer, cache_cleanup_timer_cb,
                       60000, 60000);  // Cleanup every minute
    } else {
        server->cache = NULL;
    }

    // Initialize security configuration
    server->security = catzilla_static_alloc(sizeof(static_security_config_t));
    if (!server->security) {
        if (server->cache) {
            catzilla_static_cache_cleanup(server->cache);
            catzilla_free(server->cache);
        }
        return -1;
    }

    // Copy security settings from config
    server->security->allowed_extensions = config->allowed_extensions;
    server->security->blocked_extensions = config->blocked_extensions;
    server->security->max_file_size = config->max_file_size;
    server->security->allow_symlinks = false;  // Always disabled for security
    server->security->enable_directory_listing = config->enable_directory_listing;
    server->security->enable_hidden_files = config->enable_hidden_files;

    return 0;
}

void catzilla_static_server_cleanup(catzilla_static_server_t* server) {
    if (!server) return;

    // Cleanup cache
    if (server->cache) {
        uv_timer_stop(&server->cache_cleanup_timer);
        uv_close((uv_handle_t*)&server->cache_cleanup_timer, NULL);
        catzilla_static_cache_cleanup(server->cache);
        catzilla_free(server->cache);
    }

    // Cleanup security config
    if (server->security) {
        catzilla_free(server->security);
    }
}

int catzilla_server_mount_static(catzilla_server_t* server,
                                 const char* mount_path,
                                 const char* directory,
                                 static_server_config_t* config) {
    LOG_STATIC_DEBUG("Attempting to mount static: path='%s', directory='%s'",
                     mount_path ? mount_path : "NULL",
                     directory ? directory : "NULL");

    if (!server || !mount_path || !directory) {
        LOG_STATIC_ERROR("Invalid parameters: server=%p, mount_path=%p, directory=%p",
                         server, mount_path, directory);
        return -1;
    }

    // Create mount structure
    catzilla_server_mount_t* mount = catzilla_static_alloc(sizeof(catzilla_server_mount_t));
    if (!mount) {
        LOG_STATIC_ERROR("Failed to allocate memory for mount structure");
        return -1;
    }

    // Copy mount path and directory
    strncpy(mount->mount_path, mount_path, CATZILLA_PATH_MAX - 1);
    mount->mount_path[CATZILLA_PATH_MAX - 1] = '\0';
    strncpy(mount->directory_path, directory, CATZILLA_PATH_MAX - 1);
    mount->directory_path[CATZILLA_PATH_MAX - 1] = '\0';

    LOG_STATIC_DEBUG("Mount paths copied: mount='%s', directory='%s'",
                     mount->mount_path, mount->directory_path);

    // Create static server instance for this mount
    mount->static_server = catzilla_static_alloc(sizeof(catzilla_static_server_t));
    if (!mount->static_server) {
        LOG_STATIC_ERROR("Failed to allocate memory for static server");
        catzilla_free(mount);
        return -1;
    }

    // Use server's event loop if config doesn't specify one
    if (!config->loop) {
        config->loop = server->loop;
        LOG_STATIC_DEBUG("Using server's event loop for static server");
    }

    // Initialize static server
    LOG_STATIC_DEBUG("Initializing static server with config");
    if (catzilla_static_server_init(mount->static_server, config) != 0) {
        LOG_STATIC_ERROR("Failed to initialize static server");
        catzilla_free(mount->static_server);
        catzilla_free(mount);
        return -1;
    }

    // Add to server's mount list (we need to add static_mounts to server structure)
    mount->next = server->static_mounts;
    server->static_mounts = mount;
    server->static_mount_count++;

    LOG_STATIC_INFO("Successfully mounted static path '%s' -> '%s' (total mounts: %d)",
                    mount_path, directory, server->static_mount_count);

    return 0;
}

bool catzilla_is_static_request(catzilla_server_t* server,
                                const char* request_path,
                                catzilla_server_mount_t** mount_out,
                                char* relative_path_out) {
    LOG_STATIC_DEBUG("Checking if request is static: path='%s'",
                     request_path ? request_path : "NULL");

    if (!server || !request_path || !mount_out || !relative_path_out) {
        LOG_STATIC_ERROR("Invalid parameters for static request check");
        return false;
    }

    LOG_STATIC_DEBUG("Checking against %d mounted static paths", server->static_mount_count);

    catzilla_server_mount_t* mount = server->static_mounts;

    while (mount) {
        size_t mount_len = strlen(mount->mount_path);
        LOG_STATIC_DEBUG("Checking mount: '%s' (len=%zu) against path '%s'",
                         mount->mount_path, mount_len, request_path);

        // Fast prefix check
        if (strncmp(request_path, mount->mount_path, mount_len) == 0) {
            // Extract relative path
            const char* relative = request_path + mount_len;
            if (*relative == '/' || *relative == '\0') {
                strcpy(relative_path_out, relative[0] ? relative : "/");
                *mount_out = mount;
                LOG_STATIC_INFO("Static request matched: mount='%s', relative='%s'",
                               mount->mount_path, relative_path_out);
                return true;
            }
        }
        mount = mount->next;
    }

    LOG_STATIC_DEBUG("No static mount found for path: '%s'", request_path);
    return false;
}

int catzilla_static_serve_file_async(catzilla_server_t* server,
                                     catzilla_request_t* request,
                                     catzilla_server_mount_t* mount,
                                     const char* relative_path) {
    LOG_STATIC_DEBUG("Serving static file: mount='%s', relative='%s'",
                     mount ? mount->mount_path : "NULL",
                     relative_path ? relative_path : "NULL");

    if (!server || !request || !mount || !relative_path) {
        LOG_STATIC_ERROR("Invalid parameters for static file serving");
        return -1;
    }

    // Create file context
    static_file_context_t* ctx = catzilla_static_alloc(sizeof(static_file_context_t));
    if (!ctx) {
        LOG_STATIC_ERROR("Failed to allocate file context");
        return -1;
    }

    ctx->request = request;
    ctx->mount = mount;
    ctx->start_time = uv_hrtime();
    ctx->file_descriptor = -1;  // Initialize to invalid file descriptor
    ctx->file_buffer = NULL;    // Initialize buffer pointer
    ctx->file_size = 0;         // Initialize file size
    ctx->is_head_request = (strcmp(request->method, "HEAD") == 0);
    ctx->is_range_request = false;

    // Copy relative path
    strncpy(ctx->relative_path, relative_path, CATZILLA_PATH_MAX - 1);
    ctx->relative_path[CATZILLA_PATH_MAX - 1] = '\0';

    // Build full file path
    snprintf(ctx->full_file_path, CATZILLA_PATH_MAX, "%s%s",
             mount->directory_path, relative_path);

    LOG_STATIC_DEBUG("Full file path constructed: '%s'", ctx->full_file_path);

    // Validate path for security
    if (!catzilla_static_validate_path(ctx->full_file_path, mount->directory_path)) {
        LOG_STATIC_WARN("Path validation failed for: '%s'", ctx->full_file_path);
        catzilla_static_send_error_response(ctx->client, 403, "Forbidden");
        catzilla_static_free(ctx);
        return -1;
    }

    LOG_STATIC_DEBUG("Path validation passed for: '%s'", ctx->full_file_path);

    // Check cache first if enabled
    if (mount->static_server->cache) {
        ctx->cache_entry = catzilla_static_cache_get(mount->static_server->cache,
                                                     ctx->relative_path);
        if (ctx->cache_entry) {
            // Serve from cache
            catzilla_atomic_fetch_add(&mount->static_server->cache_hits, 1);
            return catzilla_static_serve_cached_file(ctx);
        }
        catzilla_atomic_fetch_add(&mount->static_server->cache_misses, 1);
    }

    // Start async file operations
    ctx->fs_req.data = ctx;
    return uv_fs_stat(server->loop, &ctx->fs_req, ctx->full_file_path, on_file_stat);
}

int catzilla_static_serve_file_with_client(catzilla_server_t* server,
                                          catzilla_request_t* request,
                                          catzilla_server_mount_t* mount,
                                          const char* relative_path,
                                          uv_stream_t* client) {
    LOG_STATIC_DEBUG("Serving static file with client: mount='%s', relative='%s', client=%p",
                     mount ? mount->mount_path : "NULL",
                     relative_path ? relative_path : "NULL",
                     client);

    if (!server || !request || !mount || !relative_path || !client) {
        LOG_STATIC_ERROR("Invalid parameters for static file serving with client");
        return -1;
    }

    // Create file context
    static_file_context_t* ctx = catzilla_static_alloc(sizeof(static_file_context_t));
    if (!ctx) {
        LOG_STATIC_ERROR("Failed to allocate file context for client serving");
        return -1;
    }

    ctx->request = request;
    ctx->client = client;  // Set the client stream
    ctx->mount = mount;
    ctx->start_time = uv_hrtime();
    ctx->file_descriptor = -1;  // Initialize to invalid file descriptor
    ctx->file_buffer = NULL;    // Initialize buffer pointer
    ctx->file_size = 0;         // Initialize file size
    ctx->is_head_request = (strcmp(request->method, "HEAD") == 0);
    ctx->is_range_request = false;

    // Copy relative path
    strncpy(ctx->relative_path, relative_path, CATZILLA_PATH_MAX - 1);
    ctx->relative_path[CATZILLA_PATH_MAX - 1] = '\0';

    // Build full file path
    snprintf(ctx->full_file_path, CATZILLA_PATH_MAX, "%s%s",
             mount->directory_path, relative_path);

    LOG_STATIC_DEBUG("Full file path constructed: '%s'", ctx->full_file_path);

    // Validate path for security
    if (!catzilla_static_validate_path(ctx->full_file_path, mount->directory_path)) {
        LOG_STATIC_WARN("Path validation failed for: '%s'", ctx->full_file_path);
        catzilla_static_send_error_response(ctx->client, 403, "Forbidden");
        catzilla_static_free(ctx);
        return -1;
    }

    LOG_STATIC_DEBUG("Path validation passed for: '%s'", ctx->full_file_path);

    // Check cache first if enabled
    if (mount->static_server->cache) {
        LOG_STATIC_DEBUG("Checking cache for file: '%s'", ctx->relative_path);
        ctx->cache_entry = catzilla_static_cache_get(mount->static_server->cache,
                                                     ctx->relative_path);
        if (ctx->cache_entry) {
            LOG_STATIC_DEBUG("Found cached entry for: '%s'", ctx->relative_path);
            // Serve from cache
            catzilla_atomic_fetch_add(&mount->static_server->cache_hits, 1);
            return catzilla_static_serve_cached_file(ctx);
        } else {
            LOG_STATIC_DEBUG("No cached entry found for: '%s'", ctx->relative_path);
        }
        catzilla_atomic_fetch_add(&mount->static_server->cache_misses, 1);
    } else {
        LOG_STATIC_DEBUG("Cache not enabled for this mount");
    }

    // Start async file operations
    LOG_STATIC_DEBUG("Starting async file stat for: '%s'", ctx->full_file_path);
    ctx->fs_req.data = ctx;
    int result = uv_fs_stat(server->loop, &ctx->fs_req, ctx->full_file_path, on_file_stat);
    LOG_STATIC_DEBUG("uv_fs_stat returned: %d", result);
    return result;
}

// Static file serving function (synchronous version for compatibility)
int catzilla_static_serve_file(uv_stream_t* client,
                               catzilla_server_mount_t* mount,
                               const char* relative_path) {
    if (!client || !mount || !relative_path) return -1;

    // Create a minimal request structure
    catzilla_request_t request;
    memset(&request, 0, sizeof(request));
    strcpy(request.method, "GET");
    strcpy(request.path, relative_path);

    // Use the async version internally
    return catzilla_static_serve_file_with_client(NULL, &request, mount, relative_path, client);
}

// Simple wrapper function for testing
int catzilla_static_serve_file_from_context(static_file_context_t* ctx) {
    if (!ctx || !ctx->mount || !ctx->client) return -1;

    // Use the existing async file serving function
    return catzilla_static_serve_file_with_client(NULL, ctx->request, ctx->mount,
                                                 ctx->relative_path, ctx->client);
}

// Internal callback functions

static void on_file_stat(uv_fs_t* req) {
    static_file_context_t* ctx = (static_file_context_t*)req->data;

    LOG_STATIC_DEBUG("File stat callback: result=%d, path='%s'",
                     (int)req->result, ctx ? ctx->full_file_path : "NULL");

    if (req->result != 0) {
        // File not found
        LOG_STATIC_WARN("File stat failed: %s (error: %d)",
                        ctx->full_file_path, (int)req->result);
        catzilla_static_send_error_response(ctx->client, 404, "Not Found");
        catzilla_static_free(ctx);
        uv_fs_req_cleanup(req);
        return;
    }

    uv_stat_t* stat = &req->statbuf;

    LOG_STATIC_DEBUG("File stat success: size=%ld, path='%s'",
                     (long)stat->st_size, ctx->full_file_path);

    // Check if it's a directory
    if (S_ISDIR(stat->st_mode)) {
        LOG_STATIC_DEBUG("Path is a directory: %s", ctx->full_file_path);

        // Try to serve index.html from the directory
        char index_path[CATZILLA_PATH_MAX];
        snprintf(index_path, sizeof(index_path), "%s/index.html", ctx->full_file_path);

        LOG_STATIC_DEBUG("Trying to serve index file: %s", index_path);

        // Check if index.html exists by doing a quick stat
        uv_fs_t index_stat_req;
        int index_stat_result = uv_fs_stat(NULL, &index_stat_req, index_path, NULL);

        if (index_stat_result != 0) {
            // index.html doesn't exist - return 403 Forbidden
            LOG_STATIC_WARN("Directory access forbidden (no index.html): %s", ctx->full_file_path);
            catzilla_static_send_error_response(ctx->client, 403, "Forbidden");
            catzilla_static_free(ctx);
            uv_fs_req_cleanup(req);
            uv_fs_req_cleanup(&index_stat_req);
            return;
        }

        uv_fs_req_cleanup(&index_stat_req);

        // Update context to point to index.html
        strncpy(ctx->full_file_path, index_path, CATZILLA_PATH_MAX - 1);
        ctx->full_file_path[CATZILLA_PATH_MAX - 1] = '\0';

        // Update relative path too
        snprintf(ctx->relative_path, CATZILLA_PATH_MAX, "%s/index.html",
                strcmp(ctx->relative_path, "/") == 0 ? "" : ctx->relative_path);

        uv_fs_req_cleanup(req);

        // Start fresh stat for index.html
        LOG_STATIC_DEBUG("Starting stat for index file: %s", ctx->full_file_path);
        int stat_result = uv_fs_stat(ctx->mount->static_server->loop, &ctx->fs_req,
                                    ctx->full_file_path, on_file_stat);
        LOG_STATIC_DEBUG("uv_fs_stat for index returned: %d", stat_result);
        return;
    }

    // Check file size limits
    if (ctx->mount->static_server->security->max_file_size > 0 &&
        stat->st_size > ctx->mount->static_server->security->max_file_size) {
        LOG_STATIC_WARN("File too large: %ld > %ld",
                        (long)stat->st_size,
                        (long)ctx->mount->static_server->security->max_file_size);
        catzilla_static_send_error_response(ctx->client, 413, "Payload Too Large");
        catzilla_static_free(ctx);
        uv_fs_req_cleanup(req);
        return;
    }

    // Check file extension
    if (!catzilla_static_check_extension(ctx->full_file_path,
                                         ctx->mount->static_server->security)) {
        LOG_STATIC_WARN("Extension not allowed for file: %s", ctx->full_file_path);
        catzilla_static_send_error_response(ctx->client, 403, "Forbidden");
        catzilla_static_free(ctx);
        uv_fs_req_cleanup(req);
        return;
    }

    LOG_STATIC_DEBUG("All checks passed, proceeding to open file: %s", ctx->full_file_path);

    uv_fs_req_cleanup(req);

    // Open file for reading
    LOG_STATIC_DEBUG("Starting async file open for: %s", ctx->full_file_path);
    int open_result = uv_fs_open(ctx->mount->static_server->loop, &ctx->fs_req,
                                ctx->full_file_path, O_RDONLY, 0, on_file_open);
    LOG_STATIC_DEBUG("uv_fs_open returned: %d", open_result);
}

static void on_file_open(uv_fs_t* req) {
    static_file_context_t* ctx = (static_file_context_t*)req->data;

    LOG_STATIC_DEBUG("File open callback: result=%d, path='%s'",
                     (int)req->result, ctx ? ctx->full_file_path : "NULL");

    if (req->result < 0) {
        LOG_STATIC_ERROR("File open failed: %s (error: %d)",
                        ctx->full_file_path, (int)req->result);
        catzilla_static_send_error_response(ctx->client, 500, "Internal Server Error");
        catzilla_static_free(ctx);
        uv_fs_req_cleanup(req);
        return;
    }

    ctx->file_descriptor = (int)req->result;
    LOG_STATIC_DEBUG("File opened successfully: fd=%d, path='%s'",
                     ctx->file_descriptor, ctx->full_file_path);

    uv_fs_req_cleanup(req);

    // Get file size for reading
    LOG_STATIC_DEBUG("Starting file fstat for fd=%d", ctx->file_descriptor);
    int fstat_result = uv_fs_fstat(ctx->mount->static_server->loop, &ctx->fs_req,
                                   ctx->file_descriptor, on_file_fstat);
    LOG_STATIC_DEBUG("uv_fs_fstat returned: %d", fstat_result);
}

static void on_file_fstat(uv_fs_t* req) {
    static_file_context_t* ctx = (static_file_context_t*)req->data;

    LOG_STATIC_DEBUG("File fstat callback: result=%d, fd=%d",
                     (int)req->result, ctx ? ctx->file_descriptor : -1);

    if (req->result != 0) {
        LOG_STATIC_ERROR("File fstat failed: error=%d, fd=%d",
                        (int)req->result, ctx->file_descriptor);
        catzilla_static_send_error_response(ctx->client, 500, "Internal Server Error");
        catzilla_static_free(ctx);
        uv_fs_req_cleanup(req);
        return;
    }

    uv_stat_t* stat = &req->statbuf;
    size_t file_size = stat->st_size;
    LOG_STATIC_DEBUG("File fstat success: file_size=%zu, fd=%d",
                     file_size, ctx->file_descriptor);

    uv_fs_req_cleanup(req);

    // Allocate buffer for file content and store in context
    LOG_STATIC_DEBUG("Allocating buffer for file content: %zu bytes", file_size);
    void* buffer = catzilla_static_alloc(file_size);
    if (!buffer) {
        LOG_STATIC_ERROR("Failed to allocate buffer for file content: %zu bytes", file_size);
        catzilla_static_send_error_response(ctx->client, 500, "Internal Server Error");
        catzilla_static_free(ctx);
        return;
    }

    // Store buffer and file size in context for callback access
    ctx->file_buffer = buffer;
    ctx->file_size = file_size;

    LOG_STATIC_DEBUG("Buffer allocated successfully, preparing to read file fd=%d",
                     ctx->file_descriptor);

    // Read file content
    uv_buf_t buf = uv_buf_init(buffer, file_size);
    LOG_STATIC_DEBUG("Starting async file read: fd=%d, size=%zu",
                     ctx->file_descriptor, file_size);

    // Initialize the read request and set context
    ctx->read_req.data = ctx;
    int read_result = uv_fs_read(ctx->mount->static_server->loop, &ctx->read_req,
                                ctx->file_descriptor, &buf, 1, 0, on_file_read);
    LOG_STATIC_DEBUG("uv_fs_read returned: %d", read_result);
}

static void on_file_read(uv_fs_t* req) {
    static_file_context_t* ctx = (static_file_context_t*)req->data;

    LOG_STATIC_DEBUG("File read callback: result=%d, fd=%d",
                     (int)req->result, ctx ? ctx->file_descriptor : -1);

    if (req->result < 0) {
        LOG_STATIC_ERROR("File read failed: error=%d, fd=%d",
                        (int)req->result, ctx->file_descriptor);
        catzilla_static_send_error_response(ctx->client, 500, "Internal Server Error");
        catzilla_static_free(ctx);
        uv_fs_req_cleanup(req);
        return;
    }

    size_t bytes_read = req->result;
    LOG_STATIC_DEBUG("File read callback step 1: bytes_read=%zu", bytes_read);

    // Use file data from context instead of req->bufs (which might be NULL)
    void* file_data = ctx->file_buffer;
    size_t expected_size = ctx->file_size;

    LOG_STATIC_DEBUG("File read callback step 2: file_data=%p, expected_size=%zu",
                     file_data, expected_size);

    // Validate that we read the expected amount
    if (bytes_read != expected_size) {
        LOG_STATIC_ERROR("File read size mismatch: expected=%zu, actual=%zu",
                        expected_size, bytes_read);
        catzilla_static_send_error_response(ctx->client, 500, "Internal Server Error");
        catzilla_static_free(file_data);
        catzilla_static_free(ctx);
        uv_fs_req_cleanup(req);
        return;
    }

    LOG_STATIC_DEBUG("File read callback step 3: validation passed");
    LOG_STATIC_DEBUG("File read success: bytes_read=%zu, fd=%d, buffer=%p",
                     bytes_read, ctx->file_descriptor, file_data);

    // Close the file descriptor
    uv_fs_req_cleanup(req);

    LOG_STATIC_DEBUG("About to close file descriptor: %d", ctx->file_descriptor);
    uv_fs_close(ctx->mount->static_server->loop, &ctx->fs_req,
                ctx->file_descriptor, NULL);

    // Validate buffer and data
    if (!file_data) {
        LOG_STATIC_ERROR("File data buffer is NULL after read");
        catzilla_static_send_error_response(ctx->client, 500, "Internal Server Error");
        catzilla_static_free(ctx);
        return;
    }

    LOG_STATIC_DEBUG("File data validation passed, buffer=%p, size=%zu",
                     file_data, bytes_read);

    // Get MIME type
    const char* mime_type = catzilla_static_get_content_type(ctx->full_file_path);
    LOG_STATIC_DEBUG("MIME type determined: %s", mime_type ? mime_type : "NULL");

    // Build HTTP headers
    static_http_headers_t headers;
    memset(&headers, 0, sizeof(headers));
    strncpy(headers.content_type, mime_type, STATIC_MAX_MIME_TYPE_LEN - 1);
    snprintf(headers.content_length, sizeof(headers.content_length), "%zu", bytes_read);

    // Add cache headers if enabled
    if (ctx->mount->static_server->config.enable_etags) {
        char* etag = catzilla_static_generate_etag(ctx->full_file_path,
                                                   time(NULL),  // Use current time for now
                                                   bytes_read);
        if (etag) {
            strncpy(headers.etag, etag, STATIC_MAX_ETAG_LEN - 1);
            catzilla_static_free(etag);
        }
    }

    LOG_STATIC_DEBUG("Sending file response: client=%p, bytes=%zu, mime=%s",
                     ctx->client, bytes_read, mime_type);

    // Send response
    int result = catzilla_static_send_file_response(ctx->client, file_data, bytes_read,
                                                    mime_type, &headers);

    LOG_STATIC_DEBUG("File response send result: %d", result);

    // Update statistics
    if (result == 0) {
        catzilla_atomic_fetch_add(&ctx->mount->static_server->requests_served, 1);
        catzilla_atomic_fetch_add(&ctx->mount->static_server->bytes_served, bytes_read);
        LOG_STATIC_DEBUG("Statistics updated successfully");
    }

    // Cache file if enabled and appropriate size
    if (ctx->mount->static_server->cache &&
        bytes_read <= STATIC_CACHE_MAX_FILE_SIZE) {
        LOG_STATIC_DEBUG("Adding file to cache: %zu bytes", bytes_read);
        catzilla_static_cache_put(ctx->mount->static_server->cache,
                                  ctx->relative_path, file_data, bytes_read,
                                  time(NULL));
    } else {
        LOG_STATIC_DEBUG("Freeing file data buffer (not cached)");
        catzilla_static_free(file_data);  // Use matching free function
    }

    LOG_STATIC_DEBUG("Cleaning up file context");
    catzilla_static_free(ctx);  // Use matching free function
}

static void cache_cleanup_timer_cb(uv_timer_t* timer) {
    catzilla_static_server_t* server = (catzilla_static_server_t*)timer->data;
    if (server && server->cache) {
        catzilla_static_cache_cleanup(server->cache);
    }
}

// Hash function for file paths
static uint32_t hash_path(const char* path) {
    uint32_t hash = 5381;
    int c;
    while ((c = *path++)) {
        hash = ((hash << 5) + hash) + c;
    }
    return hash % STATIC_CACHE_HASH_BUCKETS;
}

static int catzilla_static_serve_cached_file(static_file_context_t* ctx) {
    if (!ctx || !ctx->cache_entry) return -1;

    // Get MIME type from file path
    const char* mime_type = catzilla_static_get_content_type(ctx->cache_entry->file_path);

    // Build headers for cached response
    static_http_headers_t headers;
    memset(&headers, 0, sizeof(headers));
    strncpy(headers.content_type, mime_type, STATIC_MAX_MIME_TYPE_LEN - 1);
    snprintf(headers.content_length, sizeof(headers.content_length),
             "%zu", ctx->cache_entry->content_size);

    // Generate ETag from cached data
    snprintf(headers.etag, STATIC_MAX_ETAG_LEN, "%lx",
             (unsigned long)ctx->cache_entry->etag_hash);

    // Add cache control
    strcpy(headers.cache_control, "public, max-age=3600");

    // Add security headers
    strcpy(headers.x_content_type_options, "nosniff");
    strcpy(headers.x_frame_options, "DENY");
    strcpy(headers.x_xss_protection, "1; mode=block");
    strcpy(headers.accept_ranges, "bytes");

    // Send response
    int result = catzilla_static_send_file_response(ctx->client,
                                                    ctx->cache_entry->file_content,
                                                    ctx->cache_entry->content_size,
                                                    mime_type, &headers);

    // Update statistics
    if (result == 0) {
        catzilla_atomic_fetch_add(&ctx->mount->static_server->requests_served, 1);
        catzilla_atomic_fetch_add(&ctx->mount->static_server->bytes_served, ctx->cache_entry->content_size);
    }

    catzilla_static_free(ctx);
    return result;
}
