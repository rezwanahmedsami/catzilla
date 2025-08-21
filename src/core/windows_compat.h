#ifndef CATZILLA_WINDOWS_COMPAT_H
#define CATZILLA_WINDOWS_COMPAT_H

#ifdef _WIN32
    #ifndef WIN32_LEAN_AND_MEAN
        #define WIN32_LEAN_AND_MEAN
    #endif
    #include <windows.h>
    #include <winsock2.h>
    #include <ws2tcpip.h>
    #include <string.h>
    #include <malloc.h>
    #include <io.h>
    #include <direct.h>
    #include <time.h>

    // Ensure Windows socket initialization
    #pragma comment(lib, "ws2_32.lib")

    // ========================================================================
    // TIME COMPATIBILITY FOR WINDOWS
    // ========================================================================

    // Define clock types for Windows compatibility
    #ifndef CLOCK_MONOTONIC
        #define CLOCK_MONOTONIC 1
    #endif

    // Define timespec structure if not available
    // Modern Windows SDK (Visual Studio 2015+ / Windows 10 SDK) includes timespec in time.h
    // We rely on the SDK to provide this structure
    #if !defined(_TIMESPEC_DEFINED) && !defined(__timespec_defined) && defined(_MSC_VER) && _MSC_VER < 1900
        // Only for very old Visual Studio versions (pre-2015)
        #define _TIMESPEC_DEFINED
        struct timespec {
            time_t tv_sec;   // seconds
            long tv_nsec;    // nanoseconds
        };
    #endif

    // NOTE: clock_gettime() implementation moved to platform_compat.h to avoid duplication

    // Function to initialize Windows networking (call once at startup)
    static inline int catzilla_init_windows_networking(void) {
        static int initialized = 0;
        if (!initialized) {
            WSADATA wsaData;
            int result = WSAStartup(MAKEWORD(2, 2), &wsaData);
            if (result == 0) {
                initialized = 1;
                return 0;
            }
            return result;
        }
        return 0;
    }

    // Function to cleanup Windows networking (call at shutdown)
    static inline void catzilla_cleanup_windows_networking(void) {
        WSACleanup();
    }

    // Windows doesn't have strcasecmp/strncasecmp, use _stricmp/_strnicmp instead
    #ifndef strcasecmp
        #define strcasecmp _stricmp
    #endif

    #ifndef strncasecmp
        #define strncasecmp _strnicmp
    #endif

    // Windows doesn't have strtok_r, use strtok_s instead
    #ifndef strtok_r
        #define strtok_r strtok_s
    #endif

    // Windows uses _strdup instead of strdup
    #ifndef strdup
        #define strdup _strdup
    #endif

    // Other common POSIX compatibility
    #ifndef snprintf
        #define snprintf _snprintf
    #endif

    #ifndef access
        #define access _access
    #endif

    #ifndef unlink
        #define unlink _unlink
    #endif

    #ifndef getcwd
        #define getcwd _getcwd
    #endif

    #ifndef chdir
        #define chdir _chdir
    #endif

    #ifndef mkdir
        #define mkdir(path, mode) _mkdir(path)
    #endif

    // File access modes
    #ifndef F_OK
        #define F_OK 0
    #endif
    #ifndef R_OK
        #define R_OK 4
    #endif
    #ifndef W_OK
        #define W_OK 2
    #endif
    #ifndef X_OK
        #define X_OK 1
    #endif

    // Path separator
    #ifndef PATH_SEPARATOR
        #define PATH_SEPARATOR '\\'
    #endif

    // Socket compatibility (if needed)
    #ifndef SHUT_RD
        #define SHUT_RD SD_RECEIVE
    #endif
    #ifndef SHUT_WR
        #define SHUT_WR SD_SEND
    #endif
    #ifndef SHUT_RDWR
        #define SHUT_RDWR SD_BOTH
    #endif

    // ========================================================================
    // REGEX COMPATIBILITY FOR WINDOWS
    // ========================================================================

    // Define regex types and constants for Windows compatibility
    typedef struct {
        char* pattern;
        int flags;
        int compiled;
    } regex_t;

    // Regex flags (simplified subset of POSIX flags)
    #define REG_EXTENDED    1
    #define REG_ICASE       2
    #define REG_NOSUB       4
    #define REG_NEWLINE     8

    // Match result structure (not used in current implementation but for completeness)
    typedef struct {
        int rm_so;  // start offset
        int rm_eo;  // end offset
    } regmatch_t;

    // Regex function declarations
    int regcomp(regex_t* preg, const char* pattern, int cflags);
    int regexec(const regex_t* preg, const char* string, size_t nmatch, regmatch_t pmatch[], int eflags);
    void regfree(regex_t* preg);

    // Simple pattern matching implementation for Windows
    // This is a basic implementation - for production use, consider integrating
    // a more robust regex library like PCRE2 or similar
    static inline int simple_pattern_match(const char* pattern, const char* text) {
        // Basic wildcard matching - supports '*' and '?' wildcards
        // This is a minimal implementation for basic pattern validation

        if (!pattern || !text) return 1; // No match for NULL inputs

        const char* p = pattern;
        const char* t = text;
        const char* star = NULL;
        const char* match = NULL;

        while (*t) {
            if (*p == '*') {
                star = p++;
                match = t;
            } else if (*p == '?' || *p == *t) {
                p++;
                t++;
            } else if (star) {
                p = star + 1;
                t = ++match;
            } else {
                return 1; // No match
            }
        }

        while (*p == '*') p++;
        return (*p == 0) ? 0 : 1; // 0 = match, 1 = no match
    }

#else
    // Unix-like systems
    #ifndef PATH_SEPARATOR
        #define PATH_SEPARATOR '/'
    #endif

    // No-op functions for non-Windows systems
    static inline int catzilla_init_windows_networking(void) { return 0; }
    static inline void catzilla_cleanup_windows_networking(void) { }

#endif // _WIN32

#endif // CATZILLA_WINDOWS_COMPAT_H
