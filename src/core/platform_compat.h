#ifndef CATZILLA_PLATFORM_COMPAT_H
#define CATZILLA_PLATFORM_COMPAT_H

/*
 * 🌪️ Catzilla Platform Compatibility Header
 *
 * This header provides C11 features with MSVC fallbacks
 * for maximum performance and portability.
 */

#include <stddef.h>

// Feature detection
#ifdef __STDC_VERSION__
    #if __STDC_VERSION__ >= 201112L
        #define CATZILLA_HAS_C11 1
    #endif
#endif

// MSVC compatibility
#ifdef _MSC_VER
    #define CATZILLA_MSVC 1
    // MSVC doesn't support VLA even in C11 mode
    #ifndef CATZILLA_NO_VLA
        #define CATZILLA_NO_VLA 1
    #endif
#endif

// Variable Length Array support
#ifdef CATZILLA_NO_VLA
    #define CATZILLA_VLA(type, name, size) \
        type* name = (type*)alloca((size) * sizeof(type))
    #include <malloc.h>  // For alloca on MSVC
#else
    #define CATZILLA_VLA(type, name, size) \
        type name[size]
#endif

// Static assertions
#ifdef CATZILLA_HAS_C11
    #define CATZILLA_STATIC_ASSERT(expr, msg) _Static_assert(expr, msg)
#else
    #define CATZILLA_STATIC_ASSERT(expr, msg) \
        typedef char static_assertion_##__LINE__[(expr) ? 1 : -1]
#endif

// Alignment
#ifdef CATZILLA_HAS_C11
    #define CATZILLA_ALIGNAS(n) _Alignas(n)
    #define CATZILLA_ALIGNOF(type) _Alignof(type)
#else
    #ifdef _MSC_VER
        #define CATZILLA_ALIGNAS(n) __declspec(align(n))
        #define CATZILLA_ALIGNOF(type) __alignof(type)
    #else
        #define CATZILLA_ALIGNAS(n) __attribute__((aligned(n)))
        #define CATZILLA_ALIGNOF(type) __alignof__(type)
    #endif
#endif

// Thread-local storage
#ifdef CATZILLA_HAS_C11
    #define CATZILLA_THREAD_LOCAL _Thread_local
#else
    #ifdef _MSC_VER
        #define CATZILLA_THREAD_LOCAL __declspec(thread)
    #else
        #define CATZILLA_THREAD_LOCAL __thread
    #endif
#endif

// Inline functions
#ifdef CATZILLA_HAS_C11
    #define CATZILLA_INLINE inline
#else
    #ifdef _MSC_VER
        #define CATZILLA_INLINE __inline
    #else
        #define CATZILLA_INLINE __inline__
    #endif
#endif

// Restrict keyword
#ifdef CATZILLA_HAS_C11
    #define CATZILLA_RESTRICT restrict
#else
    #ifdef _MSC_VER
        #define CATZILLA_RESTRICT __restrict
    #else
        #define CATZILLA_RESTRICT __restrict__
    #endif
#endif

// Function attributes
#ifdef _MSC_VER
    #define CATZILLA_NOINLINE __declspec(noinline)
    #define CATZILLA_FORCEINLINE __forceinline
    #define CATZILLA_NORETURN __declspec(noreturn)
#else
    #define CATZILLA_NOINLINE __attribute__((noinline))
    #define CATZILLA_FORCEINLINE __attribute__((always_inline)) inline
    #define CATZILLA_NORETURN __attribute__((noreturn))
#endif

// Memory alignment validation
CATZILLA_STATIC_ASSERT(sizeof(void*) >= 4, "Pointer size must be at least 4 bytes");
CATZILLA_STATIC_ASSERT(sizeof(size_t) >= 4, "size_t must be at least 4 bytes");

#endif // CATZILLA_PLATFORM_COMPAT_H
