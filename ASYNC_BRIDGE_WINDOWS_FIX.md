# Windows Compatibility Fix for Catzilla Async Bridge

## Issue
The Windows build was failing because `async_bridge.c` was using POSIX-specific pthread functions and headers that are not available on Windows.

## Error
```
async_bridge.c(15,1): error C1083: Cannot open include file: 'pthread.h': No such file or directory
```

## Solution
Replaced all pthread dependencies with libuv's cross-platform threading primitives, which work on both Windows and Unix-like systems.

## Changes Made

### 1. Header Includes
**Before:**
```c
#include <pthread.h>
#include <unistd.h>
```

**After:**
```c
// Platform-specific includes
#ifdef _WIN32
    #include <windows.h>
    #include <io.h>
#else
    #include <unistd.h>
    #include <pthread.h>
#endif
```

### 2. Data Types
**Before:**
```c
pthread_mutex_t state_mutex;
pthread_mutex_t bridge_mutex;
pthread_cond_t shutdown_cond;
pthread_once_t bridge_init_once = PTHREAD_ONCE_INIT;
```

**After:**
```c
uv_mutex_t state_mutex;        // Cross-platform mutex
uv_mutex_t bridge_mutex;       // Cross-platform mutex
uv_cond_t shutdown_cond;       // Cross-platform condition variable
uv_once_t bridge_init_once = UV_ONCE_INIT;
```

### 3. Function Calls
**Before:**
```c
pthread_once(&bridge_init_once, init_async_bridge_once);
pthread_mutex_init(&mutex, NULL);
pthread_mutex_lock(&mutex);
pthread_mutex_unlock(&mutex);
pthread_mutex_destroy(&mutex);
pthread_cond_init(&cond, NULL);
pthread_cond_destroy(&cond);
pthread_create(&thread, NULL, func, arg);
pthread_join(thread, NULL);
```

**After:**
```c
uv_once(&bridge_init_once, init_async_bridge_once);
uv_mutex_init(&mutex);
uv_mutex_lock(&mutex);
uv_mutex_unlock(&mutex);
uv_mutex_destroy(&mutex);
uv_cond_init(&cond);
uv_cond_destroy(&cond);
uv_thread_create(&thread, func, arg);
uv_thread_join(&thread);
```

### 4. Thread Function Signature
**Before:**
```c
static void* asyncio_thread_main(void* arg);
```

**After:**
```c
static void asyncio_thread_main(void* arg);  // libuv threads return void
```

## Benefits
1. **Cross-platform compatibility**: Works on Windows, macOS, Linux, and other platforms
2. **Consistent API**: Uses the same threading library (libuv) as the rest of Catzilla
3. **No additional dependencies**: libuv is already a required dependency
4. **Same performance**: libuv's threading primitives are thin wrappers around OS-native functions

## Testing
Added `async_bridge_windows_test.c` to verify that the libuv threading primitives compile and work correctly on Windows.

## Files Modified
- `src/python/async_bridge.c` - Main fix
- `src/python/async_bridge_windows_test.c` - Test file (new)

## Build Status
✅ Windows build should now succeed
✅ All existing functionality preserved
✅ Cross-platform compatibility achieved
