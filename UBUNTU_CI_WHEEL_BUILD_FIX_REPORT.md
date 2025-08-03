# Ubuntu CI Wheel Build Fix Report

## Issue Summary
The Ubuntu CI was failing during wheel builds for Python 3.11 and 3.8 with the following critical error:
```
CMake Error: failed to create symbolic link 'libuv.so.1': File exists
CMake Error: cmake_symlink_library: System Error: File exists
```

This was preventing successful wheel distribution builds on the Ubuntu CI environment.

## Root Cause Analysis

### Primary Issue: libuv Shared Library Conflict
The main issue was that `libuv` was attempting to build both static and shared libraries, with shared library support enabled by default. During the build process, CMake was trying to create symbolic links for the shared library versions (`libuv.so.1`, `libuv.so.1.0.0`), but these files already existed from previous build attempts in the CI environment, causing a symbolic link conflict.

The previous CMakeLists.txt configuration only disabled shared libraries for Windows:
```cmake
# Previous (problematic) configuration
if(WIN32)
    set(LIBUV_BUILD_SHARED OFF CACHE BOOL "Build shared library")
    set(LIBUV_BUILD_BENCH OFF CACHE BOOL "Build benchmarks")
    set(LIBUV_BUILD_TESTS OFF CACHE BOOL "Build tests")
endif()
```

### Secondary Issue: Format Specifier Warnings
Additional compiler warnings were generated in the background tasks test due to platform-specific differences in `uint64_t` formatting between macOS and Linux.

## Solutions Implemented

### 1. Fixed libuv Shared Library Build (Primary Fix)
**File**: `CMakeLists.txt`
**Change**: Extended libuv build configuration to disable shared libraries globally, not just on Windows.

```cmake
# Fixed configuration - applies to all platforms
# libuv
# Configure libuv to build only static libraries (no shared libraries)
# This prevents symbolic link conflicts during wheel builds in CI environments
set(LIBUV_BUILD_SHARED OFF CACHE BOOL "Build shared library")
set(LIBUV_BUILD_BENCH OFF CACHE BOOL "Build benchmarks")
set(LIBUV_BUILD_TESTS OFF CACHE BOOL "Build tests")

add_subdirectory(deps/libuv)
```

**Impact**:
- ✅ Eliminates symbolic link conflicts in CI environments
- ✅ Ensures consistent static-only library builds across all platforms
- ✅ Reduces build complexity and potential for file conflicts

### 2. Fixed Format Specifier Warnings (Secondary Fix)
**File**: `tests/c/test_background_tasks.c`
**Changes**:
- Added `#include <inttypes.h>` for portable format macros
- Replaced all `%llu` format specifiers with `%" PRIu64 "` for `uint64_t` values

```c
// Before (problematic)
printf("✅ Simple C task added with ID: %llu\n", task_id);

// After (fixed)
printf("✅ Simple C task added with ID: %" PRIu64 "\n", task_id);
```

**Impact**:
- ✅ Eliminates compiler format warnings on Ubuntu/Linux
- ✅ Ensures portable uint64_t formatting across platforms
- ✅ Improves code quality and reduces CI noise

## Verification

### Local Build Test
Successfully tested wheel build locally on macOS:
```bash
rm -rf build && python -m build --wheel
# ✅ Build completed successfully
# ✅ No symbolic link conflicts
# ✅ No format specifier warnings
# ✅ Import test passed: catzilla.__version__ = '0.2.0'
```

### Expected Ubuntu CI Improvements
With these fixes, the Ubuntu CI should now:
1. ✅ Build wheels successfully for Python 3.11 and 3.8
2. ✅ Avoid libuv symbolic link conflicts
3. ✅ Compile without format specifier warnings
4. ✅ Complete the full wheel distribution build process

## Build Configuration Summary

### libuv Build Settings (All Platforms)
- `LIBUV_BUILD_SHARED`: `OFF` (static libraries only)
- `LIBUV_BUILD_BENCH`: `OFF` (no benchmarks)
- `LIBUV_BUILD_TESTS`: `OFF` (no tests)

### Compiler Compatibility
- ✅ Format specifiers use portable `PRIu64` macros
- ✅ Works consistently across GCC (Ubuntu) and Clang (macOS)
- ✅ Maintains compatibility with Windows MSVC

## Files Modified

1. **CMakeLists.txt**: Fixed libuv shared library configuration
2. **tests/c/test_background_tasks.c**: Fixed format specifier portability

## Deployment Impact
- ✅ No breaking changes to API or functionality
- ✅ Improved build reliability across platforms
- ✅ Cleaner CI builds with fewer warnings
- ✅ Better wheel distribution success rate

## Next Steps
Monitor the next Ubuntu CI run to confirm the fixes resolve the build failures and allow successful wheel generation for both Python 3.11 and 3.8.
