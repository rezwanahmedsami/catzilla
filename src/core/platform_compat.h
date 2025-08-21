#ifndef CATZILLA_PLATFORM_COMPAT_H
#define CATZILLA_PLATFORM_COMPAT_H

/*
 * 🌪️ Catzilla Platform Compatibility Header
 *
 * This header provides C11 features with MSVC fallbacks
 * for maximum performance and portability.
 */

#include <stddef.h>

// Platform-specific headers
#ifdef _WIN32
    #include <windows.h>
    #include <process.h>
    #include <io.h>
    #include <direct.h>
    // Windows doesn't have pthread.h or unistd.h
    // We'll provide compatibility definitions where needed

    // Define missing types on Windows
    typedef SSIZE_T ssize_t;
    typedef int mode_t;
#else
    #include <pthread.h>
    #include <unistd.h>
    #include <sys/types.h>
#endif

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

// Windows pthread compatibility
#ifdef _WIN32
    #include <time.h>

    // ========================================================================
    // TIME COMPATIBILITY FOR WINDOWS
    // ========================================================================

    // Define clock types for Windows compatibility
    #ifndef CLOCK_MONOTONIC
        #define CLOCK_MONOTONIC 1
    #endif

    // Windows implementation of clock_gettime
    static inline int clock_gettime(int clk_id, struct timespec *tp) {
        if (!tp) return -1;

        if (clk_id == CLOCK_MONOTONIC) {
            static LARGE_INTEGER frequency = {0};
            LARGE_INTEGER counter;

            // Initialize frequency once
            if (frequency.QuadPart == 0) {
                if (!QueryPerformanceFrequency(&frequency)) {
                    return -1;
                }
            }

            // Get the current counter value
            if (!QueryPerformanceCounter(&counter)) {
                return -1;
            }

            // Convert to seconds and nanoseconds
            tp->tv_sec = (time_t)(counter.QuadPart / frequency.QuadPart);
            tp->tv_nsec = (long)(((counter.QuadPart % frequency.QuadPart) * 1000000000LL) / frequency.QuadPart);

            return 0;
        }

        // For other clock types, fall back to regular time
        time_t t = time(NULL);
        tp->tv_sec = t;
        tp->tv_nsec = 0;
        return 0;
    }

    // Define minimal pthread types for Windows compatibility
    typedef HANDLE pthread_t;
    typedef CRITICAL_SECTION pthread_mutex_t;
    typedef SRWLOCK pthread_rwlock_t;
    typedef struct {
        int dummy;
    } pthread_attr_t;
    typedef struct {
        int dummy;
    } pthread_mutexattr_t;
    typedef struct {
        int dummy;
    } pthread_rwlockattr_t;

    // pthread function stubs (to be implemented if needed)
    #define pthread_mutex_init(mutex, attr) InitializeCriticalSection(mutex)
    #define pthread_mutex_destroy(mutex) DeleteCriticalSection(mutex)
    #define pthread_mutex_lock(mutex) EnterCriticalSection(mutex)
    #define pthread_mutex_unlock(mutex) LeaveCriticalSection(mutex)

    // For now, just provide minimal compatibility
    // Full pthread emulation can be added later if needed
#endif

// ========================================================================
// PATH LENGTH COMPATIBILITY
// ========================================================================

#ifdef _WIN32
    // Windows uses MAX_PATH instead of PATH_MAX
    #ifndef PATH_MAX
        #define PATH_MAX MAX_PATH
    #endif

    // Windows path separator
    #define CATZILLA_PATH_SEPARATOR '\\'
    #define CATZILLA_PATH_SEPARATOR_STR "\\"

    // Windows equivalent of realpath - use _fullpath directly
    // Note: _fullpath is already declared in <stdlib.h> on Windows
    #define realpath(path, resolved) _fullpath(resolved, path, PATH_MAX)

    // Windows file stat compatibility
    #include <sys/stat.h>
    #ifndef S_ISDIR
        #define S_ISDIR(mode) (((mode) & _S_IFMT) == _S_IFDIR)
    #endif
    #ifndef S_ISREG
        #define S_ISREG(mode) (((mode) & _S_IFMT) == _S_IFREG)
    #endif

    // Helper function to check if character is a path separator
    static inline int catzilla_is_path_separator(char c) {
        return (c == '/' || c == '\\');
    }
#else
    // Unix-like systems typically define PATH_MAX in limits.h
    #include <limits.h>
    #ifndef PATH_MAX
        // Fallback for systems that don't define PATH_MAX
        #define PATH_MAX 4096
    #endif

    // Unix path separator
    #define CATZILLA_PATH_SEPARATOR '/'
    #define CATZILLA_PATH_SEPARATOR_STR "/"

    // Unix-like systems have realpath natively

    // Helper function to check if character is a path separator
    static inline int catzilla_is_path_separator(char c) {
        return (c == '/');
    }
#endif

// ========================================================================
// STRING FUNCTION COMPATIBILITY
// ========================================================================

#ifdef _WIN32
    #include <string.h>

    // Windows string comparison functions
    #ifndef strncasecmp
        #define strncasecmp _strnicmp
    #endif

    #ifndef strcasecmp
        #define strcasecmp _stricmp
    #endif
#endif

// ========================================================================
// FORMAT STRING COMPATIBILITY FOR uint64_t
// ========================================================================

#include <inttypes.h>

// Use portable format macros for printf family functions
#ifndef PRIu64
    #ifdef _WIN32
        #define PRIu64 "I64u"
    #else
        #define PRIu64 "llu"
    #endif
#endif

#ifndef PRId64
    #ifdef _WIN32
        #define PRId64 "I64d"
    #else
        #define PRId64 "lld"
    #endif
#endif

// Memory alignment validation
CATZILLA_STATIC_ASSERT(sizeof(void*) >= 4, "Pointer size must be at least 4 bytes");
CATZILLA_STATIC_ASSERT(sizeof(size_t) >= 4, "size_t must be at least 4 bytes");

#endif // CATZILLA_PLATFORM_COMPAT_H
