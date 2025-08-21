#include "memory.h"
#include <stdlib.h>
#include <string.h>

// Stub implementations for memory functions
void* catzilla_malloc(size_t size) { return malloc(size); }
void* catzilla_calloc(size_t count, size_t size) { return calloc(count, size); }
void* catzilla_realloc(void* ptr, size_t size) { return realloc(ptr, size); }
void catzilla_free(void* ptr) { free(ptr); }

// Typed allocation stubs
void* catzilla_cache_alloc(size_t size) { return malloc(size); }
void* catzilla_request_alloc(size_t size) { return malloc(size); }
void* catzilla_response_alloc(size_t size) { return malloc(size); }
void* catzilla_static_alloc(size_t size) { return malloc(size); }
void* catzilla_task_alloc(size_t size) { return malloc(size); }

// Typed free stubs
void catzilla_cache_free(void* ptr) { free(ptr); }
void catzilla_request_free(void* ptr) { free(ptr); }
void catzilla_response_free(void* ptr) { free(ptr); }
void catzilla_static_free(void* ptr) { free(ptr); }
void catzilla_task_free(void* ptr) { free(ptr); }
