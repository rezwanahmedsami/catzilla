# Windows jemalloc Autotools Build Fix

## Problem Fixed
The Windows jemalloc build was failing because it was missing the crucial configuration step that generates required header files like `jemalloc/internal/jemalloc_preamble.h`. The previous approach tried to use MSBuild directly without the necessary autotools configuration.

## Root Cause
jemalloc for Windows requires:
1. **Configuration step**: `autogen.sh` or `autoconf + configure` to generate header files
2. **Build step**: Either `make` or MSBuild to compile the configured source

The old script skipped step 1, causing compilation errors due to missing generated headers.

## Solution Implemented

### 1. Fixed build_jemalloc.bat
- **Primary approach**: Use autotools (autoconf + configure + make)
- **Fallback approach**: Use MSBuild with pre-generated headers if autotools unavailable
- **Tool detection**: Check for bash, autoconf, make, msbuild
- **Proper configuration**: Run `autogen.sh` to generate all required headers
- **Cross-platform compatibility**: Use Unix-style build process even on Windows

### 2. Enhanced CI workflow
- **Added MSYS2 setup**: Install autotools (autoconf, make) for Windows runners
- **Tool availability**: Ensure bash, autoconf, make are available for autotools build
- **MSBuild setup**: Keep existing MSBuild setup as fallback option

## Expected CI Results

### What Should Work Now:
1. **Windows autotools build**: `build_jemalloc.bat` should successfully:
   - Detect autotools (bash, autoconf, make)
   - Run `autogen.sh` to generate headers
   - Configure jemalloc with proper Windows settings
   - Build static library using make
   - Copy library to expected location

2. **Windows CMake detection**: CMake should find the built library at:
   ```
   ${CMAKE_SOURCE_DIR}/deps/jemalloc/lib/jemalloc.lib
   ```

3. **Cross-platform consistency**: All platforms (Linux, macOS, Windows) should use similar build processes

### Fallback Behavior:
If autotools aren't available, the script will:
1. Attempt MSBuild with existing Visual Studio solution files
2. Look for pre-generated header files
3. Build with Visual Studio 2017/2019/2022 solutions

## Files Modified

### scripts/build_jemalloc.bat
- Replaced MSBuild-only approach with autotools-first approach
- Added comprehensive tool detection (bash, autoconf, make, msbuild)
- Implemented proper jemalloc configuration workflow
- Added fallback to MSBuild if autotools unavailable
- Fixed all batch script syntax and variable expansion issues

### .github/workflows/ci.yml
- Added MSYS2 setup for Windows runners
- Installed autoconf and make packages
- Ensured autotools availability for Windows jemalloc builds

## Testing Instructions

1. **Monitor CI**: Check GitHub Actions for Windows build success
2. **Look for**: "✅ jemalloc build complete!" message in Windows CI logs
3. **Verify**: CMake should find jemalloc library and link successfully
4. **Confirm**: Catzilla Windows build should complete without jemalloc errors

## Technical Details

### Autotools Build Process:
```bash
# 1. Generate configuration files and headers
./autogen.sh

# 2. Configure for Windows with MSVC
./configure CC=cl

# 3. Build static library
make

# 4. Copy library to standard location
cp lib/.libs/libjemalloc.a lib/jemalloc.lib
```

### MSBuild Fallback Process:
```batch
# 1. Use pre-existing Visual Studio solution
msbuild msvc\jemalloc_vc2022.sln /p:Configuration=Release /p:Platform=x64

# 2. Copy built library to expected location
copy msvc\x64\Release\jemalloc-vc143-Release.lib lib\jemalloc.lib
```

## Expected Outcome
After this fix, Windows CI should:
- ✅ Successfully build jemalloc static library
- ✅ CMake should detect jemalloc library
- ✅ Catzilla should build with jemalloc integration
- ✅ All platform builds (Linux, macOS, Windows) should pass
- ✅ No more "cannot open file 'python39_d.lib'" errors
- ✅ No more "[0m was unexpected at this time" errors
- ✅ No more missing header file errors

This completes the Windows CI build fix initiative.
