# Windows Batch Script Fixes

This document summarizes the fixes made to resolve Windows batch script issues in GitHub Actions CI.

## Problem

The original issue was that Windows batch scripts were using ANSI color codes like `[32m`, `[31m`, `[0m` which caused errors in GitHub Actions with messages like:
```
[0m was unexpected at this time.
```

## Root Cause

Windows batch files were using ANSI escape sequences for colors that aren't properly supported in all Windows terminal environments, particularly in GitHub Actions CI runners.

## Files Fixed

### Core Build Scripts
- `scripts/build.bat` - Main Windows build script
- `scripts/build_jemalloc.bat` - jemalloc Windows build script
- `scripts/jemalloc_helper.bat` - jemalloc configuration helper

### Test Scripts
- `scripts/run_tests.bat` - Test runner
- `scripts/run_example.bat` - Example runner
- `scripts/test_jemalloc_detection.bat` - jemalloc detection test
- `scripts/verify_segfault_fix_windows.bat` - Segfault verification

## Changes Made

### 1. Removed ANSI Color Codes
**Before:**
```bat
set GREEN=[32m
set RED=[31m
set NC=[0m
echo %GREEN%Success!%NC%
```

**After:**
```bat
REM Colors disabled for compatibility
set GREEN=
set RED=
set NC=
echo Success!
```

### 2. Fixed Python Debug Library Issue
**Problem:** Windows builds were failing with `LINK : fatal error LNK1104: cannot open file 'python39_d.lib'`

**Root Cause:** Debug builds require Python debug libraries (`python39_d.lib`) which are not available in GitHub Actions Python installations.

**Solution:** Changed build configuration from Debug to Release mode:
```bat
REM Before (Debug - causes linking errors)
cmake .. -DCMAKE_BUILD_TYPE=Debug -DPython3_EXECUTABLE="%PYTHON_EXE%"

REM After (Release - works with standard Python installations)
cmake .. -DCMAKE_BUILD_TYPE=Release -DPython3_EXECUTABLE="%PYTHON_EXE%"
```

**Benefits of Release Mode:**
- ✅ Compatible with standard Python installations (no debug libraries required)
- ✅ Faster compilation and runtime performance
- ✅ Optimized code suitable for production and CI environments
- ✅ Consistent behavior across different Python installation types

### 3. Simplified Output Messages
- Removed color formatting from all echo statements
- Kept emojis and meaningful symbols (✅, ❌, ⚠️) for visual distinction
- Maintained clear messaging without color dependencies

### 4. Enhanced Error Handling
- Improved error messages with actionable tips
- Added compatibility checks for required tools
- Better fallback mechanisms

### 5. Script Structure Alignment
Made Windows batch scripts functionally equivalent to their Unix shell counterparts:

**build.bat** now matches **build.sh**:
1. Build jemalloc (if needed)
2. Clean previous builds
3. Create build directory
4. Configure with CMake
5. Build with parallel compilation
6. Install in development mode

**build_jemalloc.bat** now matches **build_jemalloc.sh**:
1. Check for existing library
2. Clean previous artifacts
3. Configure build environment
4. Build with appropriate tools
5. Verify output

## Testing

Since these are Windows-specific scripts, testing must be done in a Windows environment or GitHub Actions CI. The changes have been designed to:

1. **Maintain Functionality** - All core functionality preserved
2. **Improve Compatibility** - Work across different Windows terminal environments
3. **Enhance Reliability** - Better error handling and messaging

## Verification Commands

To verify the fixes work, run these in a Windows environment:

```batch
REM Test main build
scripts\build.bat

REM Test jemalloc build
scripts\build_jemalloc.bat

REM Test example execution
scripts\run_example.bat examples\hello_world\main.py

REM Run tests
scripts\run_tests.bat
```

## GitHub Actions Integration

These fixes specifically target the GitHub Actions Windows runner environment where:

1. **ANSI codes were causing script failures** - Resolved by removing color formatting
2. **Python debug libraries were missing** - Resolved by switching to Release build mode
3. **Scripts needed cross-platform consistency** - Resolved by aligning functionality

The scripts should now:

1. Execute without terminal-specific formatting errors
2. Provide clear output without color dependencies
3. Maintain cross-platform consistency

## Future Considerations

For future Windows batch script development:

1. **Avoid ANSI Codes** - Use plain text with meaningful symbols
2. **Test Cross-Platform** - Ensure scripts work in various Windows environments
3. **Maintain Parity** - Keep batch scripts functionally equivalent to shell scripts
4. **Error Handling** - Provide clear, actionable error messages

## Related Files

- `cmake/DetectJemallocPrefix.cmake` - Cross-platform jemalloc detection
- `src/core/memory.c` - Dynamic jemalloc symbol resolution
- `.github/workflows/` - CI configuration files
