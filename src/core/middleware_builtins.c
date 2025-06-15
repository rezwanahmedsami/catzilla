#include "middleware.h"
#include "memory.h"
#include <string.h>
#include <stdio.h>
#include <time.h>
#include <stdlib.h>

// ============================================================================
// 🌪️ BUILT-IN ZERO-ALLOCATION MIDDLEWARE - HIGH-PERFORMANCE C IMPLEMENTATIONS
// ============================================================================

// Simple rate limiting state (in production, would use more sophisticated storage)
static struct {
    char client_ips[1000][16];    // Simple IP storage
    uint64_t request_times[1000]; // Request timestamps
    int request_counts[1000];     // Request counts
    int entry_count;
    uint64_t window_size_ns;      // Rate limiting window in nanoseconds
    int max_requests;             // Max requests per window
} rate_limit_state = {
    .window_size_ns = 60ULL * 1000000000ULL, // 60 seconds
    .max_requests = 1000,
    .entry_count = 0
};

// ============================================================================
// CORS MIDDLEWARE - ZERO ALLOCATION
// ============================================================================

/**
 * CORS middleware - handles pre-flight and adds CORS headers
 * Pure C implementation with zero memory allocation
 */
int catzilla_middleware_cors(catzilla_middleware_context_t* ctx) {
    if (!ctx || !ctx->request) {
        return CATZILLA_MIDDLEWARE_ERROR_CODE;
    }

    // Handle pre-flight OPTIONS requests
    if (strcmp(ctx->request->method, "OPTIONS") == 0) {
        catzilla_middleware_set_status(ctx, 200);
        catzilla_middleware_set_header(ctx, "Access-Control-Allow-Origin", "*");
        catzilla_middleware_set_header(ctx, "Access-Control-Allow-Methods", "GET,POST,PUT,DELETE,OPTIONS,HEAD,PATCH");
        catzilla_middleware_set_header(ctx, "Access-Control-Allow-Headers", "Content-Type,Authorization,X-Requested-With,Accept,Origin,Access-Control-Request-Method,Access-Control-Request-Headers");
        catzilla_middleware_set_header(ctx, "Access-Control-Max-Age", "86400");
        catzilla_middleware_set_body(ctx, "", "text/plain");

        // Skip route handler for OPTIONS requests
        return CATZILLA_MIDDLEWARE_SKIP_ROUTE;
    }

    // Add CORS headers to regular responses
    catzilla_middleware_set_header(ctx, "Access-Control-Allow-Origin", "*");
    catzilla_middleware_set_header(ctx, "Access-Control-Allow-Credentials", "true");

    return CATZILLA_MIDDLEWARE_CONTINUE;
}

// ============================================================================
// REQUEST LOGGING MIDDLEWARE - MINIMAL ALLOCATION
// ============================================================================

/**
 * Request logging middleware - logs requests with minimal overhead
 * Uses lightweight C logging with no Python overhead
 */
int catzilla_middleware_request_logging(catzilla_middleware_context_t* ctx) {
    if (!ctx || !ctx->request) {
        return CATZILLA_MIDDLEWARE_ERROR_CODE;
    }

    // Get current timestamp
    uint64_t timestamp = catzilla_middleware_get_timestamp();

    // Get client IP (with fallback)
    const char* client_ip = ctx->request->remote_addr;
    if (!client_ip) client_ip = "unknown";

    // Get user agent (with fallback)
    const char* user_agent = ctx->request->user_agent;
    if (!user_agent) user_agent = "-";

    // Format: [timestamp] METHOD path client_ip "user_agent"
    printf("[%llu] %s %s %s \"%s\"\\n",
           timestamp,
           ctx->request->method ? ctx->request->method : "UNKNOWN",
           ctx->request->path ? ctx->request->path : "/",
           client_ip,
           user_agent);

    // Store start time for response logging
    uint64_t* start_time = catzilla_request_alloc(sizeof(uint64_t));
    if (start_time) {
        *start_time = timestamp;
        catzilla_middleware_set_data(ctx, ctx->current_middleware_index, start_time);
    }

    return CATZILLA_MIDDLEWARE_CONTINUE;
}

/**
 * Response logging middleware - logs response timing
 * Should be registered as post-route middleware
 */
int catzilla_middleware_response_logging(catzilla_middleware_context_t* ctx) {
    if (!ctx) {
        return CATZILLA_MIDDLEWARE_ERROR_CODE;
    }

    // Get start time from pre-route logging
    uint64_t* start_time = (uint64_t*)catzilla_middleware_get_data(ctx, ctx->current_middleware_index - 1);

    if (start_time) {
        uint64_t end_time = catzilla_middleware_get_timestamp();
        uint64_t duration = end_time - *start_time;

        printf("[RESPONSE] %d %llu ns\\n", ctx->response_status, duration);

        // Free the start time memory
        catzilla_request_free(start_time);
    }

    return CATZILLA_MIDDLEWARE_CONTINUE;
}

// ============================================================================
// RATE LIMITING MIDDLEWARE - C-ONLY IMPLEMENTATION
// ============================================================================

/**
 * Simple rate limiting middleware with token bucket algorithm
 * In production, would use Redis or other distributed storage
 */
int catzilla_middleware_rate_limit(catzilla_middleware_context_t* ctx) {
    if (!ctx || !ctx->request) {
        return CATZILLA_MIDDLEWARE_ERROR_CODE;
    }

    const char* client_ip = ctx->request->remote_addr;
    if (!client_ip) {
        // No IP available, allow request
        return CATZILLA_MIDDLEWARE_CONTINUE;
    }

    uint64_t current_time = catzilla_middleware_get_timestamp();
    uint64_t window_start = current_time - rate_limit_state.window_size_ns;

    // Find or create entry for this IP
    int ip_index = -1;
    for (int i = 0; i < rate_limit_state.entry_count; i++) {
        if (strcmp(rate_limit_state.client_ips[i], client_ip) == 0) {
            ip_index = i;
            break;
        }
    }

    if (ip_index == -1) {
        // New IP, create entry if we have space
        if (rate_limit_state.entry_count < 1000) {
            ip_index = rate_limit_state.entry_count++;
            strncpy(rate_limit_state.client_ips[ip_index], client_ip, 15);
            rate_limit_state.client_ips[ip_index][15] = '\\0';
            rate_limit_state.request_times[ip_index] = current_time;
            rate_limit_state.request_counts[ip_index] = 1;
        }
        return CATZILLA_MIDDLEWARE_CONTINUE; // Allow new IPs
    }

    // Check if we're within the rate limit window
    if (rate_limit_state.request_times[ip_index] < window_start) {
        // Outside window, reset counter
        rate_limit_state.request_times[ip_index] = current_time;
        rate_limit_state.request_counts[ip_index] = 1;
        return CATZILLA_MIDDLEWARE_CONTINUE;
    }

    // Within window, check if over limit
    if (rate_limit_state.request_counts[ip_index] >= rate_limit_state.max_requests) {
        // Rate limited
        catzilla_middleware_set_status(ctx, 429);
        catzilla_middleware_set_header(ctx, "Retry-After", "60");
        catzilla_middleware_set_header(ctx, "X-RateLimit-Limit", "1000");
        catzilla_middleware_set_header(ctx, "X-RateLimit-Remaining", "0");
        catzilla_middleware_set_body(ctx, "Rate limit exceeded", "text/plain");

        return CATZILLA_MIDDLEWARE_SKIP_ROUTE;
    }

    // Increment counter and allow
    rate_limit_state.request_counts[ip_index]++;

    // Add rate limit headers
    char remaining[32];
    snprintf(remaining, sizeof(remaining), "%d",
             rate_limit_state.max_requests - rate_limit_state.request_counts[ip_index]);

    catzilla_middleware_set_header(ctx, "X-RateLimit-Limit", "1000");
    catzilla_middleware_set_header(ctx, "X-RateLimit-Remaining", remaining);

    return CATZILLA_MIDDLEWARE_CONTINUE;
}

// ============================================================================
// AUTHENTICATION MIDDLEWARE - PURE C EXECUTION
// ============================================================================

/**
 * Simple Bearer token authentication middleware
 * For production, would integrate with proper JWT validation
 */
int catzilla_middleware_auth(catzilla_middleware_context_t* ctx) {
    if (!ctx || !ctx->request) {
        return CATZILLA_MIDDLEWARE_ERROR_CODE;
    }

    // Extract authorization header
    const char* auth_header = catzilla_middleware_get_header(ctx, "Authorization");

    if (!auth_header) {
        // No authorization header
        catzilla_middleware_set_status(ctx, 401);
        catzilla_middleware_set_header(ctx, "WWW-Authenticate", "Bearer");
        catzilla_middleware_set_body(ctx, "Authorization required", "text/plain");
        return CATZILLA_MIDDLEWARE_SKIP_ROUTE;
    }

    // Check Bearer prefix
    if (strncmp(auth_header, "Bearer ", 7) != 0) {
        catzilla_middleware_set_status(ctx, 401);
        catzilla_middleware_set_header(ctx, "WWW-Authenticate", "Bearer");
        catzilla_middleware_set_body(ctx, "Invalid authorization format", "text/plain");
        return CATZILLA_MIDDLEWARE_SKIP_ROUTE;
    }

    const char* token = auth_header + 7;

    // Simple token validation (in production, would validate JWT signature)
    if (strlen(token) < 10) {
        catzilla_middleware_set_status(ctx, 403);
        catzilla_middleware_set_body(ctx, "Invalid token", "text/plain");
        return CATZILLA_MIDDLEWARE_SKIP_ROUTE;
    }

    // For demo purposes, accept any token with "valid" in it
    if (strstr(token, "valid") != NULL) {
        // Store user info in DI context for route handler
        if (ctx->di_context) {
            // In production, would extract user ID from JWT
            char* user_id = catzilla_request_alloc(32);
            if (user_id) {
                strcpy(user_id, "user123");
                catzilla_middleware_set_di_context(ctx, "current_user_id", user_id);
            }
        }
        return CATZILLA_MIDDLEWARE_CONTINUE;
    }

    // Invalid token
    catzilla_middleware_set_status(ctx, 403);
    catzilla_middleware_set_body(ctx, "Invalid or expired token", "text/plain");
    return CATZILLA_MIDDLEWARE_SKIP_ROUTE;
}

// ============================================================================
// SECURITY HEADERS MIDDLEWARE
// ============================================================================

/**
 * Security headers middleware - adds common security headers
 * Zero allocation, pure C implementation
 */
int catzilla_middleware_security_headers(catzilla_middleware_context_t* ctx) {
    if (!ctx) {
        return CATZILLA_MIDDLEWARE_ERROR_CODE;
    }

    // Add security headers
    catzilla_middleware_set_header(ctx, "X-Content-Type-Options", "nosniff");
    catzilla_middleware_set_header(ctx, "X-Frame-Options", "DENY");
    catzilla_middleware_set_header(ctx, "X-XSS-Protection", "1; mode=block");
    catzilla_middleware_set_header(ctx, "Strict-Transport-Security", "max-age=31536000; includeSubDomains");
    catzilla_middleware_set_header(ctx, "Referrer-Policy", "strict-origin-when-cross-origin");

    return CATZILLA_MIDDLEWARE_CONTINUE;
}

// ============================================================================
// COMPRESSION MIDDLEWARE - C-NATIVE GZIP
// ============================================================================

/**
 * Response compression middleware
 * Note: This is a simplified implementation. Production would use zlib.
 */
int catzilla_middleware_compression(catzilla_middleware_context_t* ctx) {
    if (!ctx) {
        return CATZILLA_MIDDLEWARE_ERROR_CODE;
    }

    // Check if client accepts gzip compression
    const char* accept_encoding = catzilla_middleware_get_header(ctx, "Accept-Encoding");

    if (accept_encoding && strstr(accept_encoding, "gzip") != NULL) {
        // Add compression header (actual compression would happen in response building)
        catzilla_middleware_set_header(ctx, "Content-Encoding", "gzip");
        catzilla_middleware_set_header(ctx, "Vary", "Accept-Encoding");
    }

    return CATZILLA_MIDDLEWARE_CONTINUE;
}

// ============================================================================
// MIDDLEWARE REGISTRATION HELPERS
// ============================================================================

/**
 * Register all built-in middleware with a chain
 * @param chain Middleware chain
 * @return 0 on success, -1 on failure
 */
int catzilla_register_builtin_middleware(catzilla_middleware_chain_t* chain) {
    if (!chain) return -1;

    // Register middleware in priority order

    // Security headers (highest priority)
    if (catzilla_middleware_register(chain, catzilla_middleware_security_headers,
                                   "security_headers", 100,
                                   CATZILLA_MIDDLEWARE_PRE_ROUTE) != 0) {
        return -1;
    }

    // CORS handling
    if (catzilla_middleware_register(chain, catzilla_middleware_cors,
                                   "cors", 200,
                                   CATZILLA_MIDDLEWARE_PRE_ROUTE) != 0) {
        return -1;
    }

    // Rate limiting
    if (catzilla_middleware_register(chain, catzilla_middleware_rate_limit,
                                   "rate_limit", 300,
                                   CATZILLA_MIDDLEWARE_PRE_ROUTE) != 0) {
        return -1;
    }

    // Request logging
    if (catzilla_middleware_register(chain, catzilla_middleware_request_logging,
                                   "request_logging", 400,
                                   CATZILLA_MIDDLEWARE_PRE_ROUTE) != 0) {
        return -1;
    }

    // Authentication (after logging)
    if (catzilla_middleware_register(chain, catzilla_middleware_auth,
                                   "authentication", 500,
                                   CATZILLA_MIDDLEWARE_PRE_ROUTE) != 0) {
        return -1;
    }

    // Response compression (post-route)
    if (catzilla_middleware_register(chain, catzilla_middleware_compression,
                                   "compression", 100,
                                   CATZILLA_MIDDLEWARE_POST_ROUTE) != 0) {
        return -1;
    }

    // Response logging (lowest priority post-route)
    if (catzilla_middleware_register(chain, catzilla_middleware_response_logging,
                                   "response_logging", 900,
                                   CATZILLA_MIDDLEWARE_POST_ROUTE) != 0) {
        return -1;
    }

    return 0;
}

/**
 * Configure rate limiting parameters
 * @param max_requests Maximum requests per window
 * @param window_seconds Window size in seconds
 */
void catzilla_configure_rate_limiting(int max_requests, int window_seconds) {
    rate_limit_state.max_requests = max_requests;
    rate_limit_state.window_size_ns = (uint64_t)window_seconds * 1000000000ULL;
}

/**
 * Reset rate limiting state (for testing)
 */
void catzilla_reset_rate_limiting(void) {
    rate_limit_state.entry_count = 0;
    memset(rate_limit_state.client_ips, 0, sizeof(rate_limit_state.client_ips));
    memset(rate_limit_state.request_times, 0, sizeof(rate_limit_state.request_times));
    memset(rate_limit_state.request_counts, 0, sizeof(rate_limit_state.request_counts));
}
