#ifndef CATZILLA_WINDOWS_COMPAT_H
#define CATZILLA_WINDOWS_COMPAT_H

#ifdef _WIN32
    #define WIN32_LEAN_AND_MEAN
    #include <windows.h>
    #include <winsock2.h>
    #include <ws2tcpip.h>
    #include <string.h>
    #include <malloc.h>
    #include <io.h>
    #include <direct.h>

    // Ensure Windows socket initialization
    #pragma comment(lib, "ws2_32.lib")

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
