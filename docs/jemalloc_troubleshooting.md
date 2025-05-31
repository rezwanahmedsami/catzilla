# Jemalloc Troubleshooting Guide

## Common Issues with Jemalloc in Catzilla

### TLS Allocation Errors in Linux

One of the most common issues when running Catzilla in Linux environments, especially in CI/CD pipelines, is the following error:

```
ImportError: /lib/x86_64-linux-gnu/libjemalloc.so.2: cannot allocate memory in static TLS block
```

This error occurs when jemalloc is loaded dynamically after other libraries have already consumed the available Thread Local Storage (TLS) space.

## Resolution

### Setting LD_PRELOAD for Linux

On Linux systems, the solution is to preload jemalloc before other libraries are loaded:

```bash
export LD_PRELOAD=/lib/x86_64-linux-gnu/libjemalloc.so.2:$LD_PRELOAD
```

Add this to your environment setup or directly before running Python scripts.

### Setting DYLD_INSERT_LIBRARIES for macOS

On macOS systems:

```bash
# For Intel Macs
export DYLD_INSERT_LIBRARIES=/usr/local/lib/libjemalloc.dylib:$DYLD_INSERT_LIBRARIES

# For Apple Silicon Macs
export DYLD_INSERT_LIBRARIES=/opt/homebrew/lib/libjemalloc.dylib:$DYLD_INSERT_LIBRARIES
```

### For CI/CD Environments

In GitHub Actions or other CI systems, always set the appropriate environment variable before running tests:

```yaml
- name: Run Python tests
  run: |
    export LD_PRELOAD=/lib/x86_64-linux-gnu/libjemalloc.so.2:$LD_PRELOAD
    python -m pytest tests/
```

## Test Execution Recommendations

### Avoiding Segmentation Faults

1. **Use Distributed Testing**: Run tests with `pytest-xdist` to isolate test execution in separate processes.
2. **Limit Memory Usage**: For memory-intensive tests, reduce iterations and data sizes.
3. **Control Garbage Collection**: Reduce the frequency of garbage collection in tests that manipulate large numbers of objects.
4. **Disable Memory Profiling**: Use `memory_profiling=False` when creating Catzilla instances in tests.

### Safe Testing Parameters

* Keep test iterations under 1000 for memory-intensive operations
* Use smaller data structures when testing
* Avoid complex nested structures with circular references

## Technical Background

Jemalloc is a general-purpose memory allocator that focuses on reducing fragmentation and improving concurrency by using thread-specific memory arenas. However, it requires Thread Local Storage (TLS) to store these thread-specific pointers.

Linux has a limited TLS space for dynamically loaded libraries (approximately 1088 bytes on most systems). When jemalloc is loaded after other libraries have used this space, the TLS allocation fails.

By preloading jemalloc with `LD_PRELOAD`, we ensure it gets priority access to the TLS space before other libraries.

## Windows Configuration

Windows handles jemalloc differently as it doesn't use the LD_PRELOAD mechanism. Instead, jemalloc must be installed as a DLL and made available in the system PATH.

### Installation via vcpkg (Recommended)

```batch
# Install vcpkg
git clone https://github.com/Microsoft/vcpkg.git C:\vcpkg
C:\vcpkg\bootstrap-vcpkg.bat

# Install jemalloc
C:\vcpkg\vcpkg.exe install jemalloc:x64-windows

# Configure CMake integration
set CMAKE_TOOLCHAIN_FILE=C:\vcpkg\scripts\buildsystems\vcpkg.cmake
```

### Using the Helper Script

Run the automated configuration script:

```batch
scripts\jemalloc_helper.bat
```

This script will:
1. Detect existing jemalloc installations
2. Install jemalloc via vcpkg if not found
3. Add jemalloc to the system PATH
4. Configure environment variables for Catzilla

### Manual Configuration

If automatic installation fails, you can manually configure jemalloc:

1. **Set Environment Variable**:
   ```batch
   set CATZILLA_JEMALLOC_PATH=C:\path\to\jemalloc.dll
   ```

2. **Add to PATH**:
   ```batch
   set PATH=C:\vcpkg\installed\x64-windows\bin;%PATH%
   ```

3. **Verify Installation**:
   ```batch
   where jemalloc.dll
   ```

### Troubleshooting Windows Issues

**Problem**: "jemalloc.dll not found"
- Solution: Ensure jemalloc.dll is in your PATH or set CATZILLA_JEMALLOC_PATH

**Problem**: "vcpkg command not found"
- Solution: Install vcpkg first, then bootstrap it with `bootstrap-vcpkg.bat`

**Problem**: CMake cannot find jemalloc
- Solution: Set CMAKE_TOOLCHAIN_FILE to vcpkg's CMake integration

**Problem**: Tests still fail on Windows
- Solution: Restart your terminal/IDE after setting environment variables

### Windows CI/CD Configuration

For GitHub Actions or other CI systems:

```yaml
- name: Install jemalloc (Windows)
  run: |
    vcpkg install jemalloc:x64-windows
    echo "CATZILLA_JEMALLOC_PATH=C:/vcpkg/installed/x64-windows/bin/jemalloc.dll" >> $GITHUB_ENV
```
