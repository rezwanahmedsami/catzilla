#include "static_server.h"
#include "memory.h"
#include <string.h>
#include <stdio.h>
#include <stdlib.h>
#include <time.h>

// Forward declaration for internal function
static void catzilla_static_cache_remove_unlocked(hot_cache_t* cache, const char* file_path);

// Hash function for file paths
static uint32_t hash_path(const char* path) {
    uint32_t hash = 5381;
    int c;
    while ((c = *path++)) {
        hash = ((hash << 5) + hash) + c;
    }
    return hash % STATIC_CACHE_HASH_BUCKETS;
}

// LRU list management
static void lru_add_to_head(hot_cache_t* cache, hot_cache_entry_t* entry) {
    entry->lru_next = cache->lru_head;
    entry->lru_prev = NULL;

    if (cache->lru_head) {
        cache->lru_head->lru_prev = entry;
    }

    cache->lru_head = entry;

    if (!cache->lru_tail) {
        cache->lru_tail = entry;
    }
}

static void lru_remove(hot_cache_t* cache, hot_cache_entry_t* entry) {
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

    entry->lru_prev = entry->lru_next = NULL;
}

static void lru_move_to_head(hot_cache_t* cache, hot_cache_entry_t* entry) {
    lru_remove(cache, entry);
    lru_add_to_head(cache, entry);
}

int catzilla_static_cache_init(hot_cache_t* cache, size_t max_memory) {
    if (!cache) return -1;

    memset(cache, 0, sizeof(hot_cache_t));

    cache->max_memory_bytes = max_memory;
    cache->current_memory_usage = 0;
    cache->total_entries = 0;
    cache->lru_head = NULL;
    cache->lru_tail = NULL;

    // Initialize hash table buckets
    for (int i = 0; i < STATIC_CACHE_HASH_BUCKETS; i++) {
        cache->buckets[i] = NULL;
    }

    // Initialize atomic counters
    catzilla_atomic_store(&cache->cache_hits, 0);
    catzilla_atomic_store(&cache->cache_misses, 0);
    catzilla_atomic_store(&cache->evictions, 0);

    // Initialize read-write lock
    int result = uv_rwlock_init(&cache->cache_lock);
    if (result != 0) {
        return result;
    }

    return 0;
}

hot_cache_entry_t* catzilla_static_cache_get(hot_cache_t* cache, const char* file_path) {
    if (!cache || !file_path) return NULL;

    uint32_t hash = hash_path(file_path);
    time_t now = time(NULL);

    uv_rwlock_rdlock(&cache->cache_lock);

    hot_cache_entry_t* entry = cache->buckets[hash];
    while (entry) {
        if (strcmp(entry->file_path, file_path) == 0) {
            // Check if entry has expired
            if (entry->expires_at > 0 && entry->expires_at < now) {
                uv_rwlock_rdunlock(&cache->cache_lock);

                // Upgrade to write lock to remove expired entry
                uv_rwlock_wrlock(&cache->cache_lock);
                catzilla_static_cache_remove_unlocked(cache, file_path);
                uv_rwlock_wrunlock(&cache->cache_lock);
                return NULL;
            }

            // Update access time and move to head of LRU
            entry->last_accessed = now;
            entry->access_count++;

            uv_rwlock_rdunlock(&cache->cache_lock);

            // Upgrade to write lock for LRU update
            uv_rwlock_wrlock(&cache->cache_lock);
            lru_move_to_head(cache, entry);
            uv_rwlock_wrunlock(&cache->cache_lock);

            return entry;
        }
        entry = entry->next;
    }

    uv_rwlock_rdunlock(&cache->cache_lock);
    return NULL;
}

int catzilla_static_cache_put(hot_cache_t* cache, const char* file_path,
                              void* content, size_t size, time_t mtime) {
    if (!cache || !file_path || !content || size == 0) return -1;

    // Don't cache files that are too large
    if (size > STATIC_CACHE_MAX_FILE_SIZE) return -1;

    uv_rwlock_wrlock(&cache->cache_lock);

    // Check if we need to evict entries to make space
    size_t required_memory = size + strlen(file_path) + 1 + sizeof(hot_cache_entry_t);
    while (cache->current_memory_usage + required_memory > cache->max_memory_bytes &&
           cache->lru_tail) {
        // Evict least recently used entry
        hot_cache_entry_t* victim = cache->lru_tail;
        catzilla_static_cache_remove_unlocked(cache, victim->file_path);
        catzilla_atomic_fetch_add(&cache->evictions, 1);
    }

    // Create new entry
    hot_cache_entry_t* entry = catzilla_static_alloc(sizeof(hot_cache_entry_t));
    if (!entry) {
        uv_rwlock_wrunlock(&cache->cache_lock);
        return -1;
    }

    // Allocate and copy file path
    entry->file_path = catzilla_static_alloc(strlen(file_path) + 1);
    if (!entry->file_path) {
        catzilla_free(entry);
        uv_rwlock_wrunlock(&cache->cache_lock);
        return -1;
    }
    strcpy(entry->file_path, file_path);

    // Set entry data
    entry->file_content = content;  // Take ownership of content
    entry->content_size = size;
    entry->last_accessed = time(NULL);
    entry->expires_at = entry->last_accessed + STATIC_CACHE_DEFAULT_TTL;
    entry->file_mtime = mtime;
    entry->access_count = 1;
    entry->is_compressed = false;
    entry->compressed_content = NULL;
    entry->compressed_size = 0;

    // Generate ETag hash
    entry->etag_hash = hash_path(file_path) ^ (uint64_t)mtime ^ (uint64_t)size;

    // Add to hash table
    uint32_t hash = hash_path(file_path);
    entry->next = cache->buckets[hash];
    cache->buckets[hash] = entry;

    // Add to LRU list at head
    lru_add_to_head(cache, entry);

    // Update cache statistics
    cache->current_memory_usage += required_memory;
    cache->total_entries++;

    uv_rwlock_wrunlock(&cache->cache_lock);
    return 0;
}

static void catzilla_static_cache_remove_unlocked(hot_cache_t* cache, const char* file_path) {
    if (!cache || !file_path) return;

    uint32_t hash = hash_path(file_path);
    hot_cache_entry_t* entry = cache->buckets[hash];
    hot_cache_entry_t* prev = NULL;

    while (entry) {
        if (strcmp(entry->file_path, file_path) == 0) {
            // Remove from hash table
            if (prev) {
                prev->next = entry->next;
            } else {
                cache->buckets[hash] = entry->next;
            }

            // Remove from LRU list
            lru_remove(cache, entry);

            // Update memory usage
            size_t entry_memory = entry->content_size + strlen(entry->file_path) + 1 +
                                 sizeof(hot_cache_entry_t);
            if (entry->compressed_content) {
                entry_memory += entry->compressed_size;
            }
            cache->current_memory_usage -= entry_memory;
            cache->total_entries--;

            // Free entry memory
            catzilla_free(entry->file_content);
            if (entry->compressed_content) {
                catzilla_free(entry->compressed_content);
            }
            catzilla_free(entry->file_path);
            catzilla_free(entry);
            return;
        }
        prev = entry;
        entry = entry->next;
    }
}

void catzilla_static_cache_remove(hot_cache_t* cache, const char* file_path) {
    if (!cache || !file_path) return;

    uv_rwlock_wrlock(&cache->cache_lock);
    catzilla_static_cache_remove_unlocked(cache, file_path);
    uv_rwlock_wrunlock(&cache->cache_lock);
}

void catzilla_static_cache_cleanup(hot_cache_t* cache) {
    if (!cache) return;

    uv_rwlock_wrlock(&cache->cache_lock);

    time_t now = time(NULL);

    // Check all buckets for expired entries
    for (int i = 0; i < STATIC_CACHE_HASH_BUCKETS; i++) {
        hot_cache_entry_t* entry = cache->buckets[i];
        hot_cache_entry_t* prev = NULL;

        while (entry) {
            hot_cache_entry_t* next = entry->next;

            if (entry->expires_at > 0 && entry->expires_at < now) {
                // Entry has expired, remove it
                if (prev) {
                    prev->next = next;
                } else {
                    cache->buckets[i] = next;
                }

                // Remove from LRU list
                lru_remove(cache, entry);

                // Update memory usage
                size_t entry_memory = entry->content_size + strlen(entry->file_path) + 1 +
                                     sizeof(hot_cache_entry_t);
                if (entry->compressed_content) {
                    entry_memory += entry->compressed_size;
                }
                cache->current_memory_usage -= entry_memory;
                cache->total_entries--;

                // Free entry memory
                catzilla_free(entry->file_content);
                if (entry->compressed_content) {
                    catzilla_free(entry->compressed_content);
                }
                catzilla_free(entry->file_path);
                catzilla_free(entry);
            } else {
                prev = entry;
            }

            entry = next;
        }
    }

    uv_rwlock_wrunlock(&cache->cache_lock);
}

void catzilla_static_cache_destroy(hot_cache_t* cache) {
    if (!cache) return;

    // Remove all entries
    for (int i = 0; i < STATIC_CACHE_HASH_BUCKETS; i++) {
        hot_cache_entry_t* entry = cache->buckets[i];
        while (entry) {
            hot_cache_entry_t* next = entry->next;

            catzilla_free(entry->file_content);
            if (entry->compressed_content) {
                catzilla_free(entry->compressed_content);
            }
            catzilla_free(entry->file_path);
            catzilla_free(entry);

            entry = next;
        }
        cache->buckets[i] = NULL;
    }

    // Destroy lock
    uv_rwlock_destroy(&cache->cache_lock);

    cache->lru_head = NULL;
    cache->lru_tail = NULL;
    cache->current_memory_usage = 0;
    cache->total_entries = 0;
}
