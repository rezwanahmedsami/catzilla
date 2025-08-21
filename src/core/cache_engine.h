/*
 * Catzilla Smart Cache Engine - Header File
 * Ultra-High Performance C-Level Caching with jemalloc Optimization
 */

#ifndef CATZILLA_CACHE_ENGINE_H
#define CATZILLA_CACHE_ENGINE_H

#include <stdint.h>
#include <stdbool.h>
#include "platform_threading.h"
#include "platform_atomic.h"

// Remove old atomic definitions - now using platform_atomic.h

#ifdef __cplusplus
extern "C" {
#endif

// Forward declarations
typedef struct cache_entry cache_entry_t;
typedef struct catzilla_cache catzilla_cache_t;

// Cache entry structure
struct cache_entry {
    char* key;                    // Cache key (jemalloc allocated)
    void* value;                  // Serialized response data
    size_t value_size;           // Size of cached data
    uint64_t created_at;         // Creation timestamp (microseconds)
    uint64_t expires_at;         // Expiration timestamp (microseconds)
    uint32_t access_count;       // LRU tracking
    uint64_t last_access;        // Last access time (microseconds)
    uint32_t hash;               // Pre-computed hash for fast lookup
    struct cache_entry* next;    // Hash table chaining
    struct cache_entry* lru_prev; // LRU doubly-linked list
    struct cache_entry* lru_next;
};

// Cache statistics structure
typedef struct cache_statistics {
    catzilla_atomic_uint64_t hits;
    catzilla_atomic_uint64_t misses;
    catzilla_atomic_uint64_t evictions;
    catzilla_atomic_uint64_t memory_usage;
    catzilla_atomic_uint64_t total_requests;
    double hit_ratio;
    uint64_t size;              // Current number of entries
    uint64_t capacity;          // Maximum number of entries
} cache_statistics_t;

// Cache result structure
typedef struct cache_result {
    void* data;                 // Pointer to cached data (do not free!)
    size_t size;               // Size of cached data
    bool found;                // Whether the key was found
} cache_result_t;

// Main cache structure
struct catzilla_cache {
    cache_entry_t** buckets;     // Hash table buckets
    size_t bucket_count;         // Number of hash table buckets
    size_t capacity;             // Maximum number of entries
    catzilla_atomic_size_t size; // Current number of entries

    // LRU list management
    cache_entry_t* lru_head;     // Most recently used
    cache_entry_t* lru_tail;     // Least recently used

    // Thread safety
    catzilla_rwlock_t rwlock;     // Reader-writer lock for thread safety

    // jemalloc integration
    unsigned arena_index;        // jemalloc arena index for this cache

    // Configuration
    uint32_t default_ttl;        // Default TTL in seconds
    size_t max_value_size;       // Maximum size of a single cached value
    bool compression_enabled;    // Whether to compress large values

    // Statistics
    cache_statistics_t stats;
};

// Cache configuration structure
typedef struct cache_config {
    size_t capacity;             // Maximum number of entries (default: 10000)
    size_t bucket_count;         // Number of hash buckets (default: capacity/4)
    uint32_t default_ttl;        // Default TTL in seconds (default: 3600)
    size_t max_value_size;       // Max value size in bytes (default: 100MB)
    bool compression_enabled;    // Enable compression for large values
    bool jemalloc_enabled;       // Use jemalloc arena allocation
} cache_config_t;

// Cache tier types for multi-level caching
typedef enum cache_tier {
    CACHE_TIER_MEMORY = 0,      // C-level memory cache
    CACHE_TIER_REDIS = 1,       // Redis cache
    CACHE_TIER_DISK = 2         // Disk-based cache
} cache_tier_t;

// Multi-level cache coordinator
typedef struct multi_cache {
    catzilla_cache_t* memory_cache;  // L1: Memory cache
    void* redis_connection;          // L2: Redis cache (opaque pointer)
    char* disk_cache_path;           // L3: Disk cache directory
    bool redis_enabled;
    bool disk_enabled;
    uint32_t memory_ttl;            // TTL for memory cache
    uint32_t redis_ttl;             // TTL for Redis cache
    uint32_t disk_ttl;              // TTL for disk cache
} multi_cache_t;

// ============================================================================
// Core Cache API
// ============================================================================

/**
 * Create a new cache instance with default configuration
 * @param capacity Maximum number of entries to store
 * @param bucket_count Number of hash table buckets (0 for auto)
 * @return New cache instance or NULL on failure
 */
catzilla_cache_t* catzilla_cache_create(size_t capacity, size_t bucket_count);

/**
 * Create a new cache instance with custom configuration
 * @param config Cache configuration structure
 * @return New cache instance or NULL on failure
 */
catzilla_cache_t* catzilla_cache_create_with_config(const cache_config_t* config);

/**
 * Store a value in the cache
 * @param cache Cache instance
 * @param key Cache key (null-terminated string)
 * @param value Value to store
 * @param value_size Size of the value in bytes
 * @param ttl Time-to-live in seconds (0 for default TTL)
 * @return 0 on success, -1 on failure
 */
int catzilla_cache_set(catzilla_cache_t* cache, const char* key, const void* value,
                       size_t value_size, uint32_t ttl);

/**
 * Retrieve a value from the cache
 * @param cache Cache instance
 * @param key Cache key to look up
 * @return Cache result structure (check .found field)
 */
cache_result_t catzilla_cache_get(catzilla_cache_t* cache, const char* key);

/**
 * Delete a key from the cache
 * @param cache Cache instance
 * @param key Cache key to delete
 * @return 0 on success, -1 if key not found
 */
int catzilla_cache_delete(catzilla_cache_t* cache, const char* key);

/**
 * Check if a key exists in the cache without retrieving the value
 * @param cache Cache instance
 * @param key Cache key to check
 * @return true if key exists and is not expired, false otherwise
 */
bool catzilla_cache_exists(catzilla_cache_t* cache, const char* key);

/**
 * Get current cache statistics
 * @param cache Cache instance
 * @return Cache statistics structure
 */
cache_statistics_t catzilla_cache_get_stats(catzilla_cache_t* cache);

/**
 * Clear all entries from the cache
 * @param cache Cache instance
 */
void catzilla_cache_clear(catzilla_cache_t* cache);

/**
 * Destroy the cache and free all memory
 * @param cache Cache instance
 */
void catzilla_cache_destroy(catzilla_cache_t* cache);

// ============================================================================
// Advanced Cache Operations
// ============================================================================

/**
 * Set cache configuration parameters
 * @param cache Cache instance
 * @param config New configuration
 * @return 0 on success, -1 on failure
 */
int catzilla_cache_configure(catzilla_cache_t* cache, const cache_config_t* config);

/**
 * Expire entries that have exceeded their TTL
 * @param cache Cache instance
 * @return Number of entries expired
 */
size_t catzilla_cache_expire_entries(catzilla_cache_t* cache);

/**
 * Get cache memory usage in bytes
 * @param cache Cache instance
 * @return Memory usage in bytes
 */
size_t catzilla_cache_memory_usage(catzilla_cache_t* cache);

/**
 * Resize the cache capacity
 * @param cache Cache instance
 * @param new_capacity New maximum capacity
 * @return 0 on success, -1 on failure
 */
int catzilla_cache_resize(catzilla_cache_t* cache, size_t new_capacity);

// ============================================================================
// Multi-Level Cache API
// ============================================================================

/**
 * Create a multi-level cache system
 * @param memory_config Memory cache configuration
 * @param redis_url Redis connection URL (NULL to disable)
 * @param disk_path Disk cache directory (NULL to disable)
 * @return Multi-cache instance or NULL on failure
 */
multi_cache_t* multi_cache_create(const cache_config_t* memory_config,
                                  const char* redis_url, const char* disk_path);

/**
 * Get value from multi-level cache (checks all tiers)
 * @param cache Multi-cache instance
 * @param key Cache key
 * @return Cache result from the first tier that has the key
 */
cache_result_t multi_cache_get(multi_cache_t* cache, const char* key);

/**
 * Set value in multi-level cache (stores in all enabled tiers)
 * @param cache Multi-cache instance
 * @param key Cache key
 * @param value Value to store
 * @param value_size Size of value
 * @param ttl Time-to-live in seconds
 * @return 0 on success, -1 on failure
 */
int multi_cache_set(multi_cache_t* cache, const char* key, const void* value,
                    size_t value_size, uint32_t ttl);

/**
 * Delete key from all cache tiers
 * @param cache Multi-cache instance
 * @param key Cache key to delete
 * @return 0 on success, -1 on failure
 */
int multi_cache_delete(multi_cache_t* cache, const char* key);

/**
 * Destroy multi-level cache
 * @param cache Multi-cache instance
 */
void multi_cache_destroy(multi_cache_t* cache);

// ============================================================================
// Utility Functions
// ============================================================================

/**
 * Generate cache key from request components
 * @param method HTTP method
 * @param path Request path
 * @param query_string Query string (can be NULL)
 * @param headers_hash Hash of relevant headers
 * @param key_buffer Buffer to store generated key
 * @param buffer_size Size of key buffer
 * @return Length of generated key or -1 on failure
 */
int catzilla_cache_generate_key(const char* method, const char* path,
                                const char* query_string, uint32_t headers_hash,
                                char* key_buffer, size_t buffer_size);

/**
 * Hash function for cache keys (exposed for testing)
 * @param key Key string
 * @param len Length of key
 * @return 32-bit hash value
 */
uint32_t catzilla_cache_hash_key(const char* key, size_t len);

/**
 * Get current timestamp in microseconds
 * @return Timestamp in microseconds since epoch
 */
uint64_t catzilla_cache_get_timestamp(void);

#ifdef __cplusplus
}
#endif

#endif // CATZILLA_CACHE_ENGINE_H
