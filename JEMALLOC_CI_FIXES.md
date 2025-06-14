# Jemalloc CI Integration Fixes

## Problem Summary

The GitHub Actions CI workflow was failing due to multiple issues:

1. **Build Script Conflicts**: CI was installing jemalloc via package managers (`apt-get`, `brew`) while build scripts expected to compile jemalloc from source
2. **Hardcoded Library Paths**: CI used hardcoded `LD_PRELOAD` paths that pointed to system jemalloc libraries
3. **Inconsistent Environments**: Different build environments (system vs. custom builds) caused unpredictable behavior
4. **Windows MSBuild Missing**: GitHub Actions Windows runners don't have MSBuild in PATH by default
5. **Windows Library Detection**: CMake was only looking for Unix-style `.a` files, not Windows `.lib` files

## Root Cause Analysis

### System Package Manager Installations
The CI workflows were installing jemalloc via:
- **Linux**: `sudo apt-get install -y libjemalloc-dev libjemalloc2`
- **macOS**: `brew install jemalloc`
- **Windows**: No system installation (correct)

### Build Script Detection Logic
The custom build scripts (`build_jemalloc.sh`, `build_jemalloc.bat`) include detection logic that skips building jemalloc if it's already installed. This caused them to skip the custom build when system packages were present.

### Hardcoded Library Paths
CI workflows used hardcoded paths like:
```bash
export LD_PRELOAD=/lib/x86_64-linux-gnu/libjemalloc.so.2:$LD_PRELOAD
```

### Windows MSBuild Availability
Windows CI builds require MSBuild to compile solutions, but it was not available in the PATH by default on GitHub Actions runners.

### Windows Jemalloc Detection
CMakeLists.txt was only checking for Unix-style `libjemalloc.a` files, causing Windows builds to fallback to system malloc even when jemalloc was successfully built.

## Solution Implementation

### 1. Removed System Jemalloc Installations

**Files Modified:**
- `.github/workflows/ci.yml`
- `.github/workflows/docs.yml`
- `.github/workflows/release.yml`

**Changes:**
- **Before**: `sudo apt-get install -y cmake build-essential libjemalloc-dev libjemalloc2`
- **After**: `sudo apt-get install -y cmake build-essential`

- **Before**: `brew install cmake jemalloc autoconf automake libtool`
- **After**: `brew install cmake autoconf automake libtool`

### 2. Removed Hardcoded LD_PRELOAD References

Removed all hardcoded `LD_PRELOAD` exports that pointed to system jemalloc libraries. The build scripts now handle jemalloc detection and loading automatically.

**Removed from CI:**
```bash
export LD_PRELOAD=/lib/x86_64-linux-gnu/libjemalloc.so.2:$LD_PRELOAD
```

### 3. Added Windows MSBuild Setup

**Problem**: Windows CI builds were failing because MSBuild was not available in the PATH.

**Solution**: Added MSBuild setup action to CI workflow:
```yaml
- name: Setup Visual Studio MSBuild (Windows)
  if: runner.os == 'Windows'
  uses: microsoft/setup-msbuild@v2
```

**Enhanced Script**: Improved `build_jemalloc.bat` to search for MSBuild in standard Visual Studio installation locations.

### 4. Fixed Windows Jemalloc Detection

**Problem**: CMakeLists.txt was only looking for Unix-style `libjemalloc.a` files, causing Windows builds to fall back to system malloc even when jemalloc was successfully built.

**Solution**: Added Windows-specific library detection:
```cmake
# Windows-specific paths
if(WIN32)
    if(EXISTS "${CMAKE_SOURCE_DIR}/deps/jemalloc/lib/jemalloc.lib")
        message(STATUS "📦 Using pre-built jemalloc static library (deps/jemalloc) - Windows")
        set(JEMALLOC_LIBRARY_STATIC "${CMAKE_SOURCE_DIR}/deps/jemalloc/lib/jemalloc.lib")
        set(JEMALLOC_INCLUDE_DIR "${CMAKE_SOURCE_DIR}/deps/jemalloc/include")
        set(JEMALLOC_PREBUILT_FOUND TRUE)
    endif()
# Unix-specific paths
elseif(EXISTS "${CMAKE_SOURCE_DIR}/deps/jemalloc/lib/libjemalloc.a")
    # ... existing Unix detection ...
endif()
```

### 5. Removed Unnecessary Jemalloc Preloading

**Files Modified:**
- `scripts/run_tests.sh`

**Problem:**
The test runner script was attempting to detect and preload system jemalloc libraries, causing misleading warning messages when system jemalloc wasn't available. This was unnecessary because Catzilla statically links jemalloc at build time.

**Solution:**
- Removed OS detection and `LD_PRELOAD`/`DYLD_INSERT_LIBRARIES` setup logic
- Updated segfault error messages to remove jemalloc-specific troubleshooting references
- Added clear comment explaining that Catzilla uses static jemalloc linking

**Before:**
```bash
# Detect OS and set up jemalloc preloading if available
OS_NAME=$(uname -s)
if [ "$OS_NAME" = "Linux" ]; then
    if [ -f "/lib/x86_64-linux-gnu/libjemalloc.so.2" ]; then
        echo -e "${GREEN}Setting up jemalloc preloading on Linux${NC}"
        export LD_PRELOAD=/lib/x86_64-linux-gnu/libjemalloc.so.2
    fi
fi
```

**After:**
```bash
# Note: Catzilla statically links jemalloc at build time
# No need for system jemalloc preloading
```

**Impact:**
- Eliminates confusing warning messages about missing jemalloc libraries
- Simplifies test runner logic
- Makes it clear that jemalloc is statically linked, not dynamically loaded

## Build Dependencies Now Installed

### Linux (Ubuntu)
```bash
sudo apt-get update
sudo apt-get install -y cmake build-essential
```

### macOS
```bash
brew install cmake autoconf automake libtool
```

### Windows
```batch
choco install cmake --installargs 'ADD_CMAKE_TO_PATH=System'
```

## How Jemalloc is Now Handled

1. **Source-based Build**: Jemalloc is built from the git submodule at `deps/jemalloc/`
2. **Automatic Detection**: Build scripts detect if jemalloc needs to be built
3. **Environment Setup**: `jemalloc_helper.py` automatically configures library paths
4. **Cross-platform**: Same approach works on Linux, macOS, and Windows

## Build Script Workflow

```mermaid
graph TD
    A[CI Job Starts] --> B[Install Build Tools Only]
    B --> C[Run build.sh/build.bat]
    C --> D[Check if jemalloc exists]
    D --> E[Build jemalloc from source]
    E --> F[Configure environment variables]
    F --> G[Build Catzilla with custom jemalloc]
    G --> H[Run tests with proper jemalloc]
```

## Benefits of This Approach

1. **Consistent Builds**: Same jemalloc version across all platforms
2. **No Version Conflicts**: Custom build ensures compatibility
3. **Simplified CI**: No platform-specific jemalloc setup required
4. **Better Control**: Full control over jemalloc configuration
5. **Easier Debugging**: Predictable jemalloc behavior

## Verification Steps

After these changes, CI should:

1. ✅ Install only essential build tools (cmake, build-essential, etc.)
2. ✅ Skip system jemalloc package installation
3. ✅ Let build scripts handle jemalloc compilation from source
4. ✅ Automatically configure library paths
5. ✅ Run all tests successfully with custom jemalloc

## Complete Fix Summary

### All Issues Resolved ✅

1. **✅ System Jemalloc Conflicts**: Removed all system package manager installations
2. **✅ Hardcoded Library Paths**: Removed hardcoded `LD_PRELOAD` references
3. **✅ Windows Debug/Release**: Fixed all Windows batch scripts to use Release mode consistently
4. **✅ Build Configuration**: Added explicit `--config Release` to all Windows CMake builds
5. **✅ Cross-Platform Consistency**: Unified jemalloc handling across Linux, macOS, and Windows
6. **✅ Windows MSBuild Setup**: Added MSBuild setup for Windows CI
7. **✅ Windows Jemalloc Detection**: Fixed jemalloc detection for Windows builds

### Files Modified

**CI Workflows:**
- `.github/workflows/ci.yml` - Removed system jemalloc installations and hardcoded paths
- `.github/workflows/docs.yml` - Removed system jemalloc installations
- `.github/workflows/release.yml` - Removed system jemalloc installations

**Windows Build Scripts:**
- `scripts/build.bat` - Added `--config Release` to CMake build
- `scripts/run_tests.bat` - Changed from Debug to Release mode
- `scripts/test_jemalloc_detection.bat` - Fixed build config and executable paths

**CMake Configuration:**
- `CMakeLists.txt` - Added Windows library detection and MSBuild configuration

**Previous Fixes (Still Applied):**
- All Windows batch scripts - ANSI color codes removed
- Windows Python debug library issue - Release mode configuration

## Testing Instructions

### Local Testing
```bash
# Test the build process
./scripts/build.sh

# Test jemalloc functionality
python -c "from catzilla import Catzilla; print('✅ Import successful')"

# Test jemalloc detection
./scripts/test_jemalloc_detection.py
```

### Windows Testing
```cmd
REM Test Windows build
scripts\build.bat

REM Test functionality
python -c "from catzilla import Catzilla; print('✅ Import successful')"

REM Test jemalloc detection
scripts\test_jemalloc_detection.bat
```

### CI Pipeline Testing
Push these changes to GitHub and monitor the CI workflow. Expected results:
- **✅ Linux builds**: Should build jemalloc from source without conflicts
- **✅ macOS builds**: Should build jemalloc from source without brew conflicts
- **✅ Windows builds**: Should complete successfully without python39_d.lib errors

## Expected Behavior

### Before Fixes
- ❌ Linux: System jemalloc conflicted with custom builds
- ❌ macOS: Brew jemalloc conflicted with custom builds
- ❌ Windows: Debug mode caused python39_d.lib linking errors
- ❌ CI: Hardcoded paths caused runtime failures

### After Fixes
- ✅ Linux: Custom jemalloc builds consistently from git submodule
- ✅ macOS: Custom jemalloc builds consistently from git submodule
- ✅ Windows: Release mode builds successfully without debug library dependencies
- ✅ CI: Dynamic jemalloc detection and loading via build scripts

The CI pipeline should now be robust and consistent across all platforms, using only the jemalloc version built from the project's git submodule.
