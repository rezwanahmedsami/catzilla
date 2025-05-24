# Contributing to Catzilla

Welcome to Catzilla! We're excited that you're interested in contributing to this high-performance Python web framework. This guide will help you get up and running for development and testing.

## 🚀 Quick Start for Developers

### Prerequisites

- **macOS/Linux** (Windows support coming soon)
- **Python 3.8+** (3.10+ recommended)
- **CMake 3.10+**
- **GCC/Clang** compiler
- **Git** with submodule support

### Initial Setup

1. **Fork and Clone the Repository**
   ```bash
   git clone https://github.com/rezwanahmedsami/catzilla.git
   cd catzilla
   git submodule update --init --recursive
   ```

2. **Set Up Python Virtual Environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On macOS/Linux
   pip install -r requirements.txt
   ```

3. **Install Pre-commit Hooks** (Optional but Recommended)
   ```bash
   pip install pre-commit
   pre-commit install
   ```

## 🔨 Development Workflow

### Building the Project

Use the provided build script for a clean, reproducible build:

```bash
./scripts/build.sh
```

This script will:
- Clean all previous build artifacts
- Set up CMake in Debug mode with proper flags
- Build the C core and Python extension
- Install the package in development mode

**Build Output Structure:**
```
build/
├── libcatzilla_core.a      # Core C library
├── _catzilla.so            # Python C extension
├── catzilla-server         # Standalone server executable
├── test_router             # C test executable
├── test_advanced_router    # Advanced router tests
└── test_server_integration # Server integration tests
```

### Running Tests

Catzilla has a comprehensive test suite covering both C and Python components:

#### Run All Tests (Recommended)
```bash
./scripts/run_tests.sh
```

#### Run Specific Test Suites
```bash
# Python tests only (62 tests)
./scripts/run_tests.sh --python

# C tests only (28 tests)
./scripts/run_tests.sh --c

# Verbose output for debugging
./scripts/run_tests.sh --verbose
```

#### Test Coverage Overview
- **Total Tests: 90**
  - **C Tests: 28** (Basic router: 3, Advanced router: 14, Server integration: 11)
  - **Python Tests: 62** (Advanced routing: 22, HTTP responses: 17, Basic: 10, Requests: 13)

### Development Commands

#### Running Examples
```bash
# Start a development server with an example
./scripts/run_example.sh examples/hello_world/main.py

# Or use the CLI after installation
catzilla run examples/hello_world/main.py:app --reload
```

#### Manual Building (Advanced)
```bash
# Clean build
rm -rf build/ dist/ *.egg-info/ **/*.so **/__pycache__

# Configure with CMake
cmake -S . -B build -DCMAKE_BUILD_TYPE=Debug

# Build
cmake --build build -j$(nproc)

# Install in development mode
pip install -e .
```

## 🏗️ Project Architecture

### Core Components

#### C Core (`src/core/`)
- **`server.c/h`** - Main HTTP server implementation with libuv
- **`router.c/h`** - Advanced trie-based routing engine
- **Memory management** - Zero-leak design with proper cleanup

#### Python Integration (`src/python/`)
- **`module.c`** - CPython extension bridging C core to Python
- **GIL handling** - Proper threading and concurrency support

#### Python Layer (`python/catzilla/`)
- **`routing.py`** - High-level Router class with method normalization
- **`__init__.py`** - Public API and framework interface

### Key Features Implemented

1. **Advanced Dynamic Routing**
   - Trie-based router with O(log n) lookup
   - Dynamic path parameters: `/users/{user_id}`
   - Route conflict detection and warnings
   - Multiple HTTP methods per path

2. **HTTP Status Code Handling**
   - 404 Not Found for missing routes
   - 405 Method Not Allowed with proper Allow headers
   - 415 Unsupported Media Type for parsing errors

3. **Production-Grade Memory Management**
   - Recursive cleanup of trie structures
   - No memory leaks (validated by extensive testing)
   - Efficient allocation strategies

4. **Route Introspection**
   - Route counting and inspection APIs
   - Debugging utilities for development
   - Performance monitoring capabilities

## 🧪 Testing Guidelines

### Writing C Tests

C tests use the Unity testing framework. Add new tests to `tests/c/`:

```c
#include "unity.h"
#include "../../src/core/router.h"

void test_new_router_feature(void) {
    catzilla_router_t router;
    catzilla_router_init(&router);

    // Your test code here
    TEST_ASSERT_EQUAL(EXPECTED, actual);

    catzilla_router_cleanup(&router);
}
```

**Register tests in CMakeLists.txt:**
```cmake
add_executable(test_new_feature tests/c/test_new_feature.c)
target_link_libraries(test_new_feature catzilla_core unity)
```

### Writing Python Tests

Python tests use pytest. Add tests to `tests/python/`:

```python
import pytest
from catzilla import Router

def test_new_feature():
    router = Router()
    # Your test code here
    assert expected == actual

class TestNewFeatureClass:
    def test_specific_behavior(self):
        # Grouped tests for related functionality
        pass
```

### Test Best Practices

1. **Always test cleanup** - Ensure no memory leaks in C tests
2. **Test edge cases** - Empty inputs, large datasets, invalid parameters
3. **Use descriptive names** - `test_router_handles_dynamic_paths_with_multiple_parameters`
4. **Group related tests** - Use test classes or separate files for feature areas
5. **Mock external dependencies** - Keep tests isolated and fast

## 🔍 Debugging

### Debug Builds

The build script creates debug builds by default with:
- Debug symbols (`-g`)
- Memory debugging tools compatibility
- Verbose logging enabled

### Logging

The codebase includes comprehensive logging:
```c
// In C code
LOG_DEBUG("Router", "Adding route: %s %s", method, path);
LOG_INFO("Server", "Server started on port %d", port);
LOG_ERROR("Router", "Failed to add route: %s", error_msg);
```

### Memory Debugging

Use tools like Valgrind on Linux or AddressSanitizer:
```bash
# AddressSanitizer (recommended)
export CFLAGS="-fsanitize=address -g"
./scripts/build.sh
./scripts/run_tests.sh

# Valgrind (Linux)
valgrind --leak-check=full ./build/test_router
```

## 📁 Code Organization

### Directory Structure
```
catzilla/
├── src/core/           # C core implementation
├── src/python/         # Python C extension
├── python/catzilla/    # Python package
├── tests/c/           # C unit tests
├── tests/python/      # Python tests
├── examples/          # Example applications
├── scripts/           # Development scripts
└── docs/             # Documentation
```

### File Naming Conventions
- **C files**: `snake_case.c/.h`
- **Python files**: `snake_case.py`
- **Test files**: `test_*.c` or `test_*.py`
- **Example files**: Descriptive names in subdirectories

## 🚀 Performance Considerations

### Optimization Guidelines

1. **Memory Allocation**
   - Minimize malloc/free calls in hot paths
   - Use object pools for frequently allocated structures
   - Prefer stack allocation for small, short-lived objects

2. **Routing Performance**
   - Trie structure provides O(log n) average case lookup
   - Static routes are optimized separately from dynamic routes
   - Route compilation happens at startup, not per-request

3. **Python Integration**
   - Minimize GIL acquisition/release cycles
   - Use efficient data structures for parameter passing
   - Cache Python objects where appropriate

### Benchmarking

```bash
# Run performance examples
./scripts/run_example.sh examples/benchmark/stress_test.py

# Profile C code
valgrind --tool=callgrind ./build/catzilla-server
```

## 🤝 Contribution Guidelines

### Pull Request Process

1. **Fork the repository** and create a feature branch
2. **Write tests** for your changes (both C and Python if applicable)
3. **Ensure all tests pass**: `./scripts/run_tests.sh`
4. **Follow code style** (pre-commit hooks help with this)
5. **Write clear commit messages** describing your changes
6. **Submit a pull request** with a detailed description

### Code Style

#### C Code
- **Indentation**: 4 spaces (no tabs)
- **Naming**: `snake_case` for functions and variables
- **Structs**: `typedef struct { ... } name_t;`
- **Error handling**: Always check return values
- **Memory**: Every malloc must have a corresponding free

#### Python Code
- **Follow PEP 8** (enforced by pre-commit hooks)
- **Type hints**: Use them for public APIs
- **Docstrings**: Document all public functions and classes
- **Import order**: isort handles this automatically

### Bug Reports

When filing bug reports, please include:
1. **Catzilla version** and platform
2. **Minimal reproduction case**
3. **Expected vs actual behavior**
4. **Full error output** with stack traces
5. **Environment details** (Python version, OS, etc.)

### Feature Requests

For new features:
1. **Check existing issues** to avoid duplicates
2. **Describe the use case** and motivation
3. **Provide examples** of the proposed API
4. **Consider backward compatibility**
5. **Discuss implementation approach** if you plan to contribute

## 🆘 Getting Help

- **GitHub Issues**: For bugs and feature requests
- **GitHub Discussions**: For questions and community discussion
- **Discord/Slack**: Coming soon for real-time chat
- **Email**: [samiahmed0f0@gmail.com](mailto:samiahmed0f0@gmail.com) for direct contact

## 📚 Additional Resources

### Learning Resources
- **libuv Documentation**: https://docs.libuv.org/
- **llhttp**: https://github.com/nodejs/llhttp
- **CPython Extending**: https://docs.python.org/3/extending/
- **Unity Testing**: https://github.com/ThrowTheSwitch/Unity

### Development Tools
- **IDE Setup**: VS Code with C/C++ and Python extensions
- **Debugging**: GDB, LLDB, or IDE debuggers
- **Profiling**: Valgrind, perf, or platform-specific tools
- **Static Analysis**: clang-static-analyzer, cppcheck

Thank you for contributing to Catzilla! Your efforts help make this framework faster, more reliable, and more useful for the entire Python community. 🚀
