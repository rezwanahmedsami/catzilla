# Windows jemalloc Integration Fix

This document describes how we fixed issues with jemalloc detection on Windows CI builds.

## Problem

The Windows CI build was correctly installing jemalloc via vcpkg, but CMake wasn't detecting it properly during the build process. The log showed:

```
[32mFound jemalloc via vcpkg[0m
[32mConfiguring jemalloc for Catzilla...[0m
[33mJemalloc path: C:\vcpkg\installed\x64-windows\bin\jemalloc.dll[0m
[32mAdded jemalloc directory to PATH[0m
[32mJemalloc configuration complete[0m
```

But later, the CMake configuration showed:

```
⚠️ jemalloc not found, falling back to standard malloc
```

## Solution

We fixed this by implementing several improvements:

1. **Enhanced Environment Variable Passing**: Updated the CI workflow to explicitly set `JEMALLOC_LIBRARY` and `JEMALLOC_INCLUDE_DIR` environment variables.

2. **Improved jemalloc_helper.bat**: Modified the helper script to properly set environment variables that CMake can use.

3. **CMakeLists.txt Updates**: Enhanced the jemalloc detection logic in CMakeLists.txt to check multiple potential locations and handle Windows-specific paths better.

4. **build.bat Script Updates**: Modified the build script to explicitly pass jemalloc paths to CMake when available.

## Implementation Details

### Environment Variables

The following environment variables are now set for Windows builds:

- `CATZILLA_JEMALLOC_PATH`: Path to the jemalloc DLL file (e.g., `C:/vcpkg/installed/x64-windows/bin/jemalloc.dll`)
- `JEMALLOC_LIBRARY`: Path to the jemalloc library file (e.g., `C:/vcpkg/installed/x64-windows/lib/jemalloc.lib`)
- `JEMALLOC_INCLUDE_DIR`: Path to the jemalloc include directory (e.g., `C:/vcpkg/installed/x64-windows/include`)

### File Changes

- **CMakeLists.txt**: Enhanced jemalloc detection to check explicit paths and environment variables
- **scripts/jemalloc_helper.bat**: Now sets environment variables for CMake
- **scripts/build.bat**: Passes jemalloc variables to CMake when available
- **.github/workflows/ci.yml**: Sets environment variables and verifies file existence

## Testing

To test this fix:

1. Run the build script on a Windows machine with vcpkg installed:
   ```
   scripts\build.bat
   ```

2. Verify that the jemalloc detection message shows:
   ```
   ✅ jemalloc found: C:/vcpkg/installed/x64-windows/lib/jemalloc.lib
   ```

3. Run tests to ensure jemalloc is properly integrated:
   ```
   scripts\run_tests.bat
   ```

## Troubleshooting

If jemalloc still isn't detected properly:

1. Check if the environment variables are set correctly:
   ```
   echo %CATZILLA_JEMALLOC_PATH%
   echo %JEMALLOC_LIBRARY%
   echo %JEMALLOC_INCLUDE_DIR%
   ```

2. Verify jemalloc files exist at the expected paths:
   ```
   dir C:\vcpkg\installed\x64-windows\bin\jemalloc.dll
   dir C:\vcpkg\installed\x64-windows\lib\jemalloc.lib
   dir C:\vcpkg\installed\x64-windows\include\jemalloc
   ```

3. Try running the jemalloc helper script directly:
   ```
   scripts\jemalloc_helper.bat
   ```
