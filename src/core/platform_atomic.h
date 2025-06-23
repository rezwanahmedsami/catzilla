#ifndef PLATFORM_ATOMIC_H
#define PLATFORM_ATOMIC_H

/*
 * Cross-platform atomic operations for Catzilla
 * Provides unified interface for GCC/Clang builtins and Windows Interlocked functions
 */

#include <stdint.h>

#ifdef _WIN32
    // Windows implementation
    #include <windows.h>
    #include <intrin.h>

    typedef volatile uint64_t catzilla_atomic_uint64_t;
    typedef volatile size_t catzilla_atomic_size_t;
    typedef volatile void* catzilla_atomic_ptr_t;
    typedef volatile double catzilla_atomic_double_t;

    // Atomic type aliases for task_system.h compatibility
    typedef catzilla_atomic_ptr_t atomic_ptr_t;
    typedef catzilla_atomic_uint64_t atomic_uint64_t;
    typedef catzilla_atomic_double_t atomic_double_t;

    #define catzilla_atomic_load(ptr) (*(ptr))
    #define catzilla_atomic_store(ptr, val) (*(ptr) = (val))
    #define catzilla_atomic_fetch_add(ptr, val) InterlockedAdd64((LONGLONG*)(ptr), (val))
    #define catzilla_atomic_fetch_sub(ptr, val) InterlockedAdd64((LONGLONG*)(ptr), -(val))

#else
    // Unix/Linux/macOS implementation
    typedef uint64_t catzilla_atomic_uint64_t;
    typedef size_t catzilla_atomic_size_t;

    #define catzilla_atomic_load(ptr) (*(ptr))
    #define catzilla_atomic_store(ptr, val) (*(ptr) = (val))
    #define catzilla_atomic_fetch_add(ptr, val) __sync_fetch_and_add(ptr, val)
    #define catzilla_atomic_fetch_sub(ptr, val) __sync_fetch_and_sub(ptr, val)

#endif

#endif // PLATFORM_ATOMIC_H
