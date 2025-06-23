/*
 * Catzilla Smart Cache Engine
 * Ultra-High Performance C-Level Caching with jemalloc Optimization
 *
 * This implements a revolutionary multi-level caching system that operates
 * at C-level speeds with enterprise-grade features:
 * - Hash table with LRU eviction
 * - jemalloc arena-based memory management
 * - Thread-safe operations with minimal locking
 * - Real-time statistics collection
 * - Zero-copy operations where possible
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <stdbool.h>
#include <time.h>
#include "platform_threading.h"

#ifdef _WIN32
#include <windows.h>
#endif

#ifdef JEMALLOC_ENABLED
#include <jemalloc/jemalloc.h>
#endif

#include "cache_engine.h"

// Hash function for cache keys (FNV-1a algorithm)
static uint32_t hash_key(const char* key, size_t len) {
    uint32_t hash = 2166136261u;
    for (size_t i = 0; i < len; i++) {
        hash ^= (uint8_t)key[i];
        hash *= 16777619u;
    }
    return hash;
}

// Get current timestamp in microseconds
static uint64_t get_timestamp_us() {
#ifdef _WIN32
    LARGE_INTEGER freq, counter;
    QueryPerformanceFrequency(&freq);
    QueryPerformanceCounter(&counter);
    return (uint64_t)((counter.QuadPart * 1000000ULL) / freq.QuadPart);
#else
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return (uint64_t)ts.tv_sec * 1000000 + ts.tv_nsec / 1000;
#endif
}

// Move entry to front of LRU list (most recently used)
static void lru_move_to_front(catzilla_cache_t* cache, cache_entry_t* entry) {
    if (entry == cache->lru_head) {
        return; // Already at front
    }

    // Remove from current position
    if (entry->lru_prev) {
        entry->lru_prev->lru_next = entry->lru_next;
    }
    if (entry->lru_next) {
        entry->lru_next->lru_prev = entry->lru_prev;
    }
    if (entry == cache->lru_tail) {
        cache->lru_tail = entry->lru_prev;
    }

    // Add to front
    entry->lru_prev = NULL;
    entry->lru_next = cache->lru_head;
    if (cache->lru_head) {
        cache->lru_head->lru_prev = entry;
    }
    cache->lru_head = entry;

    if (!cache->lru_tail) {
        cache->lru_tail = entry;
    }
}

// Remove entry from LRU list
static void lru_remove(catzilla_cache_t* cache, cache_entry_t* entry) {
    if (entry->lru_prev) {
        entry->lru_prev->lru_next = entry->lru_next;
    } else {
        cache->lru_head = entry->lru_next;
    }

    if (entry->lru_next) {
        entry->lru_next->lru_prev = entry->lru_prev;
    } else {
        cache->lru_tail = entry->lru_prev;
    }
}

// Evict least recently used entry
static void evict_lru(catzilla_cache_t* cache) {
    if (!cache->lru_tail) {
        return;
    }

    cache_entry_t* entry = cache->lru_tail;

    // Remove from hash table
    uint32_t bucket_index = entry->hash % cache->bucket_count;
    cache_entry_t** current = &cache->buckets[bucket_index];

    while (*current && *current != entry) {
        current = &(*current)->next;
    }

    if (*current) {
        *current = entry->next;
    }

    // Remove from LRU list
    lru_remove(cache, entry);

    // Free memory using jemalloc if available
#ifdef JEMALLOC_ENABLED
    dallocx(entry->key, MALLOCX_ARENA(cache->arena_index));
    dallocx(entry->value, MALLOCX_ARENA(cache->arena_index));
    dallocx(entry, MALLOCX_ARENA(cache->arena_index));
#else
    free(entry->key);
    free(entry->value);
    free(entry);
#endif

    catzilla_atomic_fetch_sub(&cache->size, 1);
    catzilla_atomic_fetch_add(&cache->stats.evictions, 1);
}

// Create a new cache instance
catzilla_cache_t* catzilla_cache_create(size_t capacity, size_t bucket_count) {
    catzilla_cache_t* cache = malloc(sizeof(catzilla_cache_t));
    if (!cache) {
        return NULL;
    }

    // Initialize hash table
    cache->buckets = calloc(bucket_count, sizeof(cache_entry_t*));
    if (!cache->buckets) {
        free(cache);
        return NULL;
    }

    cache->bucket_count = bucket_count;
    cache->capacity = capacity;
    catzilla_atomic_store(&cache->size, 0);

    // Initialize LRU list
    cache->lru_head = NULL;
    cache->lru_tail = NULL;

    // Initialize jemalloc arena if available
#ifdef JEMALLOC_ENABLED
    size_t arena_index_size = sizeof(unsigned);
    if (mallctl("arenas.create", &cache->arena_index, &arena_index_size, NULL, 0) != 0) {
        cache->arena_index = 0; // Fall back to default arena
    }
#else
    cache->arena_index = 0;
#endif

    // Initialize statistics
    catzilla_atomic_store(&cache->stats.hits, 0);
    catzilla_atomic_store(&cache->stats.misses, 0);
    catzilla_atomic_store(&cache->stats.evictions, 0);
    catzilla_atomic_store(&cache->stats.memory_usage, 0);
    catzilla_atomic_store(&cache->stats.total_requests, 0);
    cache->stats.hit_ratio = 0.0;

    // Initialize thread safety
    catzilla_rwlock_init(&cache->rwlock);

    // Configuration defaults
    cache->default_ttl = 3600; // 1 hour
    cache->max_value_size = 100 * 1024 * 1024; // 100MB
    cache->compression_enabled = false;

    return cache;
}

// Set a value in the cache
int catzilla_cache_set(catzilla_cache_t* cache, const char* key, const void* value,
                       size_t value_size, uint32_t ttl) {
    if (!cache || !key || !value || value_size > cache->max_value_size) {
        return -1;
    }

    size_t key_len = strlen(key);
    uint32_t hash = hash_key(key, key_len);
    uint32_t bucket_index = hash % cache->bucket_count;
    uint64_t now = get_timestamp_us();
    uint64_t expires_at = now + (uint64_t)ttl * 1000000; // Convert to microseconds

    catzilla_rwlock_wrlock(&cache->rwlock);

    // Check if key already exists
    cache_entry_t* existing = cache->buckets[bucket_index];
    while (existing) {
        if (existing->hash == hash && strcmp(existing->key, key) == 0) {
            // Update existing entry
#ifdef JEMALLOC_ENABLED
            dallocx(existing->value, MALLOCX_ARENA(cache->arena_index));
            existing->value = mallocx(value_size, MALLOCX_ARENA(cache->arena_index));
#else
            free(existing->value);
            existing->value = malloc(value_size);
#endif
            if (!existing->value) {
                catzilla_rwlock_unlock(&cache->rwlock);
                return -1;
            }

            memcpy(existing->value, value, value_size);
            existing->value_size = value_size;
            existing->expires_at = expires_at;
            existing->last_access = now;
            existing->access_count++;

            lru_move_to_front(cache, existing);
            catzilla_rwlock_unlock(&cache->rwlock);
            return 0;
        }
        existing = existing->next;
    }

    // Evict entries if at capacity
    while (catzilla_atomic_load(&cache->size) >= cache->capacity) {
        evict_lru(cache);
    }

    // Create new entry
#ifdef JEMALLOC_ENABLED
    cache_entry_t* entry = mallocx(sizeof(cache_entry_t), MALLOCX_ARENA(cache->arena_index));
    entry->key = mallocx(key_len + 1, MALLOCX_ARENA(cache->arena_index));
    entry->value = mallocx(value_size, MALLOCX_ARENA(cache->arena_index));
#else
    cache_entry_t* entry = malloc(sizeof(cache_entry_t));
    entry->key = malloc(key_len + 1);
    entry->value = malloc(value_size);
#endif

    if (!entry || !entry->key || !entry->value) {
        if (entry) {
#ifdef JEMALLOC_ENABLED
            if (entry->key) dallocx(entry->key, MALLOCX_ARENA(cache->arena_index));
            if (entry->value) dallocx(entry->value, MALLOCX_ARENA(cache->arena_index));
            dallocx(entry, MALLOCX_ARENA(cache->arena_index));
#else
            if (entry->key) free(entry->key);
            if (entry->value) free(entry->value);
            free(entry);
#endif
        }
        catzilla_rwlock_unlock(&cache->rwlock);
        return -1;
    }

    // Initialize entry
    strcpy(entry->key, key);
    memcpy(entry->value, value, value_size);
    entry->value_size = value_size;
    entry->created_at = now;
    entry->expires_at = expires_at;
    entry->access_count = 1;
    entry->last_access = now;
    entry->hash = hash;

    // Add to hash table
    entry->next = cache->buckets[bucket_index];
    cache->buckets[bucket_index] = entry;

    // Add to front of LRU list
    entry->lru_prev = NULL;
    entry->lru_next = cache->lru_head;
    if (cache->lru_head) {
        cache->lru_head->lru_prev = entry;
    }
    cache->lru_head = entry;

    if (!cache->lru_tail) {
        cache->lru_tail = entry;
    }

    catzilla_atomic_fetch_add(&cache->size, 1);
    catzilla_atomic_fetch_add(&cache->stats.memory_usage, value_size + key_len + sizeof(cache_entry_t));

    catzilla_rwlock_unlock(&cache->rwlock);
    return 0;
}

// Get a value from the cache
cache_result_t catzilla_cache_get(catzilla_cache_t* cache, const char* key) {
    cache_result_t result = {NULL, 0, false};

    if (!cache || !key) {
        catzilla_atomic_fetch_add(&cache->stats.misses, 1);
        return result;
    }

    size_t key_len = strlen(key);
    uint32_t hash = hash_key(key, key_len);
    uint32_t bucket_index = hash % cache->bucket_count;
    uint64_t now = get_timestamp_us();

    catzilla_rwlock_rdlock(&cache->rwlock);

    cache_entry_t* entry = cache->buckets[bucket_index];
    while (entry) {
        if (entry->hash == hash && strcmp(entry->key, key) == 0) {
            // Check if expired
            if (now > entry->expires_at) {
                catzilla_rwlock_unlock(&cache->rwlock);

                // Remove expired entry (requires write lock)
                catzilla_rwlock_wrlock(&cache->rwlock);
                // Re-find entry in case it was removed by another thread
                cache_entry_t** current = &cache->buckets[bucket_index];
                while (*current && (*current != entry || strcmp((*current)->key, key) != 0)) {
                    current = &(*current)->next;
                }
                if (*current) {
                    *current = entry->next;
                    lru_remove(cache, entry);
#ifdef JEMALLOC_ENABLED
                    dallocx(entry->key, MALLOCX_ARENA(cache->arena_index));
                    dallocx(entry->value, MALLOCX_ARENA(cache->arena_index));
                    dallocx(entry, MALLOCX_ARENA(cache->arena_index));
#else
                    free(entry->key);
                    free(entry->value);
                    free(entry);
#endif
                    catzilla_atomic_fetch_sub(&cache->size, 1);
                }
                catzilla_rwlock_unlock(&cache->rwlock);

                catzilla_atomic_fetch_add(&cache->stats.misses, 1);
                return result;
            }

            // Found valid entry
            entry->access_count++;
            entry->last_access = now;

            result.data = entry->value;
            result.size = entry->value_size;
            result.found = true;

            catzilla_rwlock_unlock(&cache->rwlock);

            // Move to front of LRU (requires write lock)
            catzilla_rwlock_wrlock(&cache->rwlock);
            lru_move_to_front(cache, entry);
            catzilla_rwlock_unlock(&cache->rwlock);

            catzilla_atomic_fetch_add(&cache->stats.hits, 1);
            catzilla_atomic_fetch_add(&cache->stats.total_requests, 1);

            // Update hit ratio
            uint64_t total_hits = catzilla_atomic_load(&cache->stats.hits);
            uint64_t total_requests = catzilla_atomic_load(&cache->stats.total_requests);
            cache->stats.hit_ratio = (double)total_hits / total_requests;

            return result;
        }
        entry = entry->next;
    }

    catzilla_rwlock_unlock(&cache->rwlock);
    catzilla_atomic_fetch_add(&cache->stats.misses, 1);
    catzilla_atomic_fetch_add(&cache->stats.total_requests, 1);

    return result;
}

// Delete a key from the cache
int catzilla_cache_delete(catzilla_cache_t* cache, const char* key) {
    if (!cache || !key) {
        return -1;
    }

    size_t key_len = strlen(key);
    uint32_t hash = hash_key(key, key_len);
    uint32_t bucket_index = hash % cache->bucket_count;

    catzilla_rwlock_wrlock(&cache->rwlock);

    cache_entry_t** current = &cache->buckets[bucket_index];
    while (*current) {
        if ((*current)->hash == hash && strcmp((*current)->key, key) == 0) {
            cache_entry_t* entry = *current;
            *current = entry->next;

            lru_remove(cache, entry);

#ifdef JEMALLOC_ENABLED
            dallocx(entry->key, MALLOCX_ARENA(cache->arena_index));
            dallocx(entry->value, MALLOCX_ARENA(cache->arena_index));
            dallocx(entry, MALLOCX_ARENA(cache->arena_index));
#else
            free(entry->key);
            free(entry->value);
            free(entry);
#endif

            catzilla_atomic_fetch_sub(&cache->size, 1);
            catzilla_rwlock_unlock(&cache->rwlock);
            return 0;
        }
        current = &(*current)->next;
    }

    catzilla_rwlock_unlock(&cache->rwlock);
    return -1; // Key not found
}

// Get cache statistics
cache_statistics_t catzilla_cache_get_stats(catzilla_cache_t* cache) {
    cache_statistics_t stats = {0};

    if (!cache) {
        return stats;
    }

    stats.hits = catzilla_atomic_load(&cache->stats.hits);
    stats.misses = catzilla_atomic_load(&cache->stats.misses);
    stats.evictions = catzilla_atomic_load(&cache->stats.evictions);
    stats.memory_usage = catzilla_atomic_load(&cache->stats.memory_usage);
    stats.total_requests = catzilla_atomic_load(&cache->stats.total_requests);
    stats.hit_ratio = cache->stats.hit_ratio;
    stats.size = catzilla_atomic_load(&cache->size);
    stats.capacity = cache->capacity;

    return stats;
}

// Clear all entries from the cache
void catzilla_cache_clear(catzilla_cache_t* cache) {
    if (!cache) {
        return;
    }

    catzilla_rwlock_wrlock(&cache->rwlock);

    for (size_t i = 0; i < cache->bucket_count; i++) {
        cache_entry_t* entry = cache->buckets[i];
        while (entry) {
            cache_entry_t* next = entry->next;
#ifdef JEMALLOC_ENABLED
            dallocx(entry->key, MALLOCX_ARENA(cache->arena_index));
            dallocx(entry->value, MALLOCX_ARENA(cache->arena_index));
            dallocx(entry, MALLOCX_ARENA(cache->arena_index));
#else
            free(entry->key);
            free(entry->value);
            free(entry);
#endif
            entry = next;
        }
        cache->buckets[i] = NULL;
    }

    cache->lru_head = NULL;
    cache->lru_tail = NULL;
    catzilla_atomic_store(&cache->size, 0);
    catzilla_atomic_store(&cache->stats.memory_usage, 0);

    catzilla_rwlock_unlock(&cache->rwlock);
}

// Destroy the cache and free all memory
void catzilla_cache_destroy(catzilla_cache_t* cache) {
    if (!cache) {
        return;
    }

    catzilla_cache_clear(cache);

    catzilla_rwlock_destroy(&cache->rwlock);
    free(cache->buckets);

#ifdef JEMALLOC_ENABLED
    // Destroy jemalloc arena
    if (cache->arena_index > 0) {
        char arena_destroy_cmd[32];
        snprintf(arena_destroy_cmd, sizeof(arena_destroy_cmd), "arena.%u.destroy", cache->arena_index);
        mallctl(arena_destroy_cmd, NULL, NULL, NULL, 0);
    }
#endif

    free(cache);
}

// Check if a key exists without retrieving the value
bool catzilla_cache_exists(catzilla_cache_t* cache, const char* key) {
    if (!cache || !key) {
        return false;
    }

    size_t key_len = strlen(key);
    uint32_t hash = hash_key(key, key_len);
    uint32_t bucket_index = hash % cache->bucket_count;
    uint64_t now = get_timestamp_us();

    catzilla_rwlock_rdlock(&cache->rwlock);

    cache_entry_t* entry = cache->buckets[bucket_index];
    while (entry) {
        if (entry->hash == hash && strcmp(entry->key, key) == 0) {
            bool exists = (now <= entry->expires_at);
            catzilla_rwlock_unlock(&cache->rwlock);
            return exists;
        }
        entry = entry->next;
    }

    catzilla_rwlock_unlock(&cache->rwlock);
    return false;
}

// Create cache with custom configuration
catzilla_cache_t* catzilla_cache_create_with_config(const cache_config_t* config) {
    if (!config) {
        return NULL;
    }

    size_t bucket_count = config->bucket_count;
    if (bucket_count == 0) {
        bucket_count = config->capacity / 4;
        if (bucket_count < 16) bucket_count = 16;
    }

    catzilla_cache_t* cache = catzilla_cache_create(config->capacity, bucket_count);
    if (!cache) {
        return NULL;
    }

    cache->default_ttl = config->default_ttl;
    cache->max_value_size = config->max_value_size;
    cache->compression_enabled = config->compression_enabled;

    return cache;
}

// Expire entries that have exceeded their TTL
size_t catzilla_cache_expire_entries(catzilla_cache_t* cache) {
    if (!cache) {
        return 0;
    }

    size_t expired_count = 0;
    uint64_t now = get_timestamp_us();

    catzilla_rwlock_wrlock(&cache->rwlock);

    for (size_t i = 0; i < cache->bucket_count; i++) {
        cache_entry_t** current = &cache->buckets[i];

        while (*current) {
            if (now > (*current)->expires_at) {
                cache_entry_t* entry = *current;
                *current = entry->next;

                lru_remove(cache, entry);

#ifdef JEMALLOC_ENABLED
                dallocx(entry->key, MALLOCX_ARENA(cache->arena_index));
                dallocx(entry->value, MALLOCX_ARENA(cache->arena_index));
                dallocx(entry, MALLOCX_ARENA(cache->arena_index));
#else
                free(entry->key);
                free(entry->value);
                free(entry);
#endif

                catzilla_atomic_fetch_sub(&cache->size, 1);
                expired_count++;
            } else {
                current = &(*current)->next;
            }
        }
    }

    catzilla_rwlock_unlock(&cache->rwlock);
    return expired_count;
}

// Get cache memory usage
size_t catzilla_cache_memory_usage(catzilla_cache_t* cache) {
    if (!cache) {
        return 0;
    }
    return catzilla_atomic_load(&cache->stats.memory_usage);
}

// Resize cache capacity
int catzilla_cache_resize(catzilla_cache_t* cache, size_t new_capacity) {
    if (!cache) {
        return -1;
    }

    catzilla_rwlock_wrlock(&cache->rwlock);

    // If reducing capacity, evict entries as needed
    while (catzilla_atomic_load(&cache->size) > new_capacity) {
        evict_lru(cache);
    }

    cache->capacity = new_capacity;
    catzilla_rwlock_unlock(&cache->rwlock);

    return 0;
}

// Generate cache key from request components
int catzilla_cache_generate_key(const char* method, const char* path,
                                const char* query_string, uint32_t headers_hash,
                                char* key_buffer, size_t buffer_size) {
    if (!method || !path || !key_buffer || buffer_size == 0) {
        return -1;
    }

    int written;
    if (query_string && strlen(query_string) > 0) {
        written = snprintf(key_buffer, buffer_size, "%s:%s?%s:%08x",
                          method, path, query_string, headers_hash);
    } else {
        written = snprintf(key_buffer, buffer_size, "%s:%s:%08x",
                          method, path, headers_hash);
    }

    if (written < 0 || (size_t)written >= buffer_size) {
        return -1; // Buffer too small
    }

    return written;
}

// Expose hash function for testing
uint32_t catzilla_cache_hash_key(const char* key, size_t len) {
    return hash_key(key, len);
}

// Expose timestamp function
uint64_t catzilla_cache_get_timestamp(void) {
    return get_timestamp_us();
}

// Configure cache parameters
int catzilla_cache_configure(catzilla_cache_t* cache, const cache_config_t* config) {
    if (!cache || !config) {
        return -1;
    }

    catzilla_rwlock_wrlock(&cache->rwlock);

    cache->default_ttl = config->default_ttl;
    cache->max_value_size = config->max_value_size;
    cache->compression_enabled = config->compression_enabled;

    // Resize if needed
    if (config->capacity != cache->capacity) {
        while (catzilla_atomic_load(&cache->size) > config->capacity) {
            evict_lru(cache);
        }
        cache->capacity = config->capacity;
    }

    catzilla_rwlock_unlock(&cache->rwlock);
    return 0;
}
