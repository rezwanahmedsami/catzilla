# Contributing to Catzilla

Welcome to Catzilla! We're excited that you're interested in contributing to this high-performance Python web framework. This guide will help you get up and running for development and testing.

## 🚀 Quick Start for Developers

> **⚠️ IMPORTANT: Virtual Environment Required**
> Before starting any development work on Catzilla, you **MUST** create and activate a Python virtual environment. This is not optional and prevents dependency conflicts. See the [Initial Setup](#initial-setup) section below for detailed instructions.

### Prerequisites

- **macOS/Linux** (Win### Development Features

The Catzilla framework provides a modern development experience:

1. **RouterGroup System**
   - Organize routes with shared prefixes
   - Logical grouping of related endpoints
   - Clean API structure with `include_routes()` method

2. **C-Accelerated Routing**
   - Transparent C acceleration for route matching
   - Efficient path parameter extraction
   - Automatic fallback to Python when needed

3. **Development Setup**
   ```python
   # Standard development setup
   from catzilla import App, RouterGroup

   app = App()
   api = RouterGroup(prefix="/api/v1")

   @api.get("/users/{user_id}")
   def get_user(request):
       user_id = request.path_params["user_id"]
       return {"user_id": user_id}

   app.include_routes(api)
   ```

### Development Environment

- **Python 3.8+** (3.10+ recommended)
- **CMake 3.15+**
- **Compiler**:
  - **Linux/macOS**: GCC or Clang
  - **Windows**: Visual Studio 2019+ or Visual Studio Build Tools
- **Git** with submodule support

#### Windows-Specific Setup

**Prerequisites for Windows:**

1. **Install Visual Studio Build Tools** (if you don't have Visual Studio):
   - Download from: https://visualstudio.microsoft.com/visual-cpp-build-tools/
   - Install "C++ build tools" workload

2. **Install CMake:**
   - Option 1: Download from https://cmake.org/download/
   - Option 2: Use chocolatey: `choco install cmake`
   - Option 3: Use scoop: `scoop install cmake`

3. **Install Git:**
   - Download from https://git-scm.com/download/win
   - Or use chocolatey: `choco install git`

**Note**: All Windows batch scripts (`.bat`) are already provided and work with both Command Prompt and PowerShell.

### Initial Setup

1. **Fork and Clone the Repository**
   ```bash
   git clone https://github.com/rezwanahmedsami/catzilla.git
   cd catzilla
   git submodule update --init --recursive
   ```

2. **⚠️ REQUIRED: Set Up Python Virtual Environment**

   **You MUST use a Python virtual environment before working on Catzilla.** This prevents dependency conflicts and ensures a clean development environment.

   ```bash
   # Create virtual environment
   python -m venv venv

   # Activate virtual environment
   # On macOS/Linux:
   source venv/bin/activate

   # On Windows (Command Prompt):
   venv\Scripts\activate.bat

   # On Windows (PowerShell):
   venv\Scripts\Activate.ps1

   # Install development dependencies
   pip install -r requirements-dev.txt

   # Optional: Install benchmark dependencies (only if running benchmarks)
   # pip install -r requirements-benchmarks.txt
   ```

   **Important Notes:**
   - **Always activate the virtual environment** before running any Python commands
   - **Your terminal prompt should show `(venv)`** when the environment is active
   - **Deactivate with `deactivate`** when you're done working
   - **Never commit the `venv/` folder** - it's already in `.gitignore`
   - **Catzilla has ZERO runtime dependencies** - it uses only Python standard library!

   **Verify your setup:**
   ```bash
   # Check that you're using the virtual environment Python
   # On macOS/Linux:
   which python  # Should show: /path/to/catzilla/venv/bin/python

   # On Windows:
   where python  # Should show: C:\path\to\catzilla\venv\Scripts\python.exe

   # Verify development dependencies are installed
   pip list | grep -E "(pytest|pre-commit)"

   # Test that Catzilla works with minimal dependencies
   python check_dependencies.py
   ```

3. **Install Pre-commit Hooks** (Optional but Recommended)
   ```bash
   pip install pre-commit
   pre-commit install
   ```

### Types of Contributions

Catzilla welcomes various types of contributions:

- **🔧 Core Development** - C/Python code improvements, performance optimizations
- **🧪 Testing** - Unit tests, integration tests, benchmarks
- **📚 Documentation** - User guides, API docs, examples (see [Documentation Contributions](#-contributing-to-documentation))
- **🐛 Bug Reports** - Issues, bug fixes, problem reproduction
- **💡 Feature Requests** - New functionality, enhancements, design suggestions
- **🎯 Examples** - Real-world usage examples, tutorials, demo applications

Each contribution type has specific guidelines covered in the relevant sections below.

## 🔨 Development Workflow

### Before You Start

**Always ensure your virtual environment is activated:**
```bash
# Check if virtual environment is active (should show (venv) in prompt)
echo $VIRTUAL_ENV  # Should show: /path/to/catzilla/venv

# If not active, activate it:
source venv/bin/activate
```

### Dependency Management

Catzilla uses a **zero-dependency architecture** for maximum performance and minimal installation overhead:

#### 📦 **Requirements Structure:**
- **`requirements.txt`** - Empty! (Core has no runtime dependencies)
- **`requirements-dev.txt`** - Development tools (pytest, pre-commit, etc.)
- **`requirements-benchmarks.txt`** - Optional benchmark dependencies (fastapi, django, etc.)

#### 🚀 **Key Benefits:**
- **Lightning fast installation** - No heavy dependencies to download
- **Minimal attack surface** - Fewer dependencies = fewer security risks
- **Better compatibility** - Works in any Python environment
- **Reduced conflicts** - No dependency version conflicts

#### 💻 **Installation Options:**
```bash
# Core development (recommended for contributors)
pip install -r requirements-dev.txt

# Full development with benchmarking capabilities
pip install -r requirements-dev.txt -r requirements-benchmarks.txt

# Production usage (via pip install)
pip install catzilla  # Zero dependencies installed!
```

### Building the Project

Use the provided build script for a clean, reproducible build:

**On macOS/Linux:**
```bash
./scripts/build.sh
```

**On Windows:**
```cmd
scripts\build.bat
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

**On macOS/Linux:**
```bash
./scripts/run_tests.sh
```

**On Windows:**
```cmd
scripts\run_tests.bat
```

#### Run Specific Test Suites

**On macOS/Linux:**
```bash
# Python tests only (62 tests)
./scripts/run_tests.sh --python

# C tests only (28 tests)
./scripts/run_tests.sh --c

# Verbose output for debugging
./scripts/run_tests.sh --verbose
```

**On Windows:**
```cmd
# Python tests only (62 tests)
scripts\run_tests.bat --python

# C tests only (28 tests)
scripts\run_tests.bat --c

# Verbose output for debugging
scripts\run_tests.bat --verbose
```

#### Test Coverage Overview
- **Total Tests: 90**
  - **C Tests: 28** (Basic router: 3, Advanced router: 14, Server integration: 11)
  - **Python Tests: 62** (Advanced routing: 22, HTTP responses: 17, Basic: 10, Requests: 13)

### Development Commands

#### Running Examples

**On macOS/Linux:**
```bash
# Start a development server with an example
./scripts/run_example.sh examples/hello_world/main.py

# Or use the CLI after installation
catzilla run examples/hello_world/main.py:app --reload
```

**On Windows:**
```cmd
# Start a development server with an example
scripts\run_example.bat examples\hello_world\main.py

# Or use the CLI after installation
catzilla run examples/hello_world/main.py:app --reload
```

#### Manual Building (Advanced)

**On macOS/Linux:**
```bash
# Clean build
rm -rf build/ dist/ *.egg-info/ **/*.so **/__pycache__

# Configure with CMake
cmake -S . -B build -DCMAKE_BUILD_TYPE=Debug

# Build (use available CPU cores)
cmake --build build -j$(nproc)

# Install in development mode
pip install -e .
```

**On Windows:**
```cmd
# Clean build
rmdir /s /q build dist
del /s /q *.egg-info
for /r %%i in (*.pyd __pycache__) do if exist "%%i" rmdir /s /q "%%i"

# Configure with CMake
cmake -S . -B build -DCMAKE_BUILD_TYPE=Debug

# Build (use available CPU cores)
cmake --build build -j %NUMBER_OF_PROCESSORS%

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
- **`router_group.py`** - RouterGroup implementation for hierarchical routing
- **`__init__.py`** - Public API and framework interface
- **`params.py`** - Path parameter extraction and validation

### Key Features Implemented

1. **C-Accelerated Hybrid Routing**
   - C core engine for 18.5% faster route matching
   - Zero-copy path parameter extraction
   - Automatic fallback to Python routing when needed
   - Optimized tree traversal for complex routing patterns

2. **RouterGroup System**
   - Hierarchical route organization with prefix support
   - Nested RouterGroups with parameter inheritance
   - HTTP method decorators (@get, @post, @put, @delete, @patch)
   - FastAPI-style route organization and metadata support

3. **Enhanced Path Parameter Extraction**
   - C-accelerated parameter parsing (35% faster)
   - Complex nested route parameter support
   - Type validation and automatic conversion
   - Custom parameter validators and converters

4. **Advanced Dynamic Routing**
   - Trie-based router with O(log n) lookup
   - Dynamic path parameters: `/users/{user_id}`
   - Route conflict detection and warnings
   - Multiple HTTP methods per path

5. **HTTP Status Code Handling**
   - 404 Not Found for missing routes
   - 405 Method Not Allowed with proper Allow headers
   - 415 Unsupported Media Type for parsing errors

6. **Production-Grade Memory Management**
   - Recursive cleanup of trie structures
   - No memory leaks (validated by extensive testing)
   - 42% reduction in memory usage for large RouterGroup hierarchies

7. **Performance Monitoring**
   - Built-in benchmarking and profiling tools
   - Route introspection and debugging APIs
   - Performance metrics and monitoring capabilities

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
from catzilla import App, RouterGroup

def test_new_feature():
    app = App()
    # Your test code here
    assert expected == actual

def test_router_group_feature():
    app = App()
    api = RouterGroup(prefix="/api/v1")

    @api.get("/users/{user_id}")
    def get_user(request):
        user_id = request.path_params["user_id"]
        return {"user_id": user_id}

    app.include_routes(api)
    # Test routing behavior
    # Note: Use actual API methods available in the framework

class TestRouterGroupClass:
    def test_nested_router_groups(self):
        # Test RouterGroup functionality
        app = App()
        api = RouterGroup(prefix="/api")
        app.include_routes(api)

    def test_path_parameters(self):
        # Test path parameter extraction
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

## 🐛 Debug Logging System

Catzilla provides a professional debug logging system designed for contributors while keeping clean output for end users. The system uses environment variables to control debug output across both C and Python components.

### Quick Start

#### For End Users (Clean Output)
```bash
# Normal usage - clean, professional output only
python app.py
./scripts/run_example.sh examples/hello_world/main.py
```

#### For Contributors (Rich Debugging)
```bash
# Enable all debugging (both C and Python)
CATZILLA_C_DEBUG=1 CATZILLA_DEBUG=1 python app.py

# Or use the convenient script flags
./scripts/run_example.sh --debug examples/hello_world/main.py
```

### Debug Environment Variables

| Variable | Component | Description |
|----------|-----------|-------------|
| `CATZILLA_C_DEBUG=1` | C Core | Enables debug logging for server, router, and HTTP components |
| `CATZILLA_DEBUG=1` | Python | Enables debug logging for Python types and application components |

### Script Debug Flags

The `run_example.sh` script provides convenient debug flags:

```bash
# Enable all debugging (C + Python)
./scripts/run_example.sh --debug examples/hello_world/main.py

# Enable only C debugging
./scripts/run_example.sh --debug_c examples/hello_world/main.py

# Enable only Python debugging
./scripts/run_example.sh --debug_py examples/hello_world/main.py

# Normal operation (no debug output)
./scripts/run_example.sh examples/hello_world/main.py
```

### C Debug Logging

The C logging system in `src/core/logging.h` provides color-coded, module-specific logging:

#### Available Macros
```c
// Server module
LOG_SERVER_DEBUG(message, ...);
LOG_SERVER_INFO(message, ...);
LOG_SERVER_WARN(message, ...);
LOG_SERVER_ERROR(message, ...);

// Router module
LOG_ROUTER_DEBUG(message, ...);
LOG_ROUTER_INFO(message, ...);
LOG_ROUTER_WARN(message, ...);
LOG_ROUTER_ERROR(message, ...);

// HTTP module
LOG_HTTP_DEBUG(message, ...);
LOG_HTTP_INFO(message, ...);
LOG_HTTP_WARN(message, ...);
LOG_HTTP_ERROR(message, ...);
```

#### Color Scheme
- **DEBUG**: Cyan - Detailed debugging information
- **INFO**: Green - Important operational information
- **WARN**: Yellow - Warnings and potential issues
- **ERROR**: Red - Error conditions and failures

#### Example Usage in C Code
```c
#include "logging.h"

void example_function() {
    LOG_SERVER_DEBUG("Starting server initialization on port %d", port);

    if (setup_successful) {
        LOG_SERVER_INFO("Server successfully bound to port %d", port);
    } else {
        LOG_SERVER_ERROR("Failed to bind to port %d: %s", port, error_msg);
    }

    LOG_SERVER_WARN("Using default configuration for missing setting");
}
```

#### Performance Impact
- **Zero overhead when disabled** - No performance impact in production
- **Runtime control** - No recompilation needed to enable/disable debugging
- **Module-specific** - Only show logs from components you're debugging

### Python Debug Logging

The Python logging system in `python/catzilla/logging.py` provides matching functionality:

#### Available Functions
```python
# Types module
log_types_debug(message)
log_types_info(message)
log_types_warn(message)
log_types_error(message)

# Application module
log_app_debug(message)
log_app_info(message)
log_app_warn(message)
log_app_error(message)

# Request module
log_request_debug(message)
log_request_info(message)
log_request_warn(message)
log_request_error(message)
```

#### Example Usage in Python Code
```python
from catzilla.logging import log_types_debug, log_types_info, log_types_error

def process_request(request):
    log_types_debug(f"Processing {request.method} request to {request.path}")

    try:
        result = handle_request(request)
        log_types_info(f"Successfully processed request: {result}")
        return result
    except Exception as e:
        log_types_error(f"Request processing failed: {e}")
        raise
```

### Debug Output Examples

#### Clean End User Output
```bash
$ python app.py
Server starting on http://localhost:8000
Press Ctrl+C to stop
```

#### Rich Contributor Debugging
```bash
$ CATZILLA_C_DEBUG=1 CATZILLA_DEBUG=1 python app.py
[DEBUG-C][Server] Initializing server on port 8000
[DEBUG-C][Router] Router initialized with empty route table
[DEBUG-PY-TYPES] Loading application configuration
[DEBUG-C][Server] Setting up libuv event loop
[INFO-C][Server] Server successfully bound to port 8000
[DEBUG-PY-APP] Application startup complete
Server starting on http://localhost:8000
[DEBUG-C][Server] Server listening for connections
Press Ctrl+C to stop
```

### Integration with Development Workflow

#### During Development
1. **Start with clean output** to see the user experience
2. **Enable debugging** when investigating issues or implementing features
3. **Use module-specific debugging** to focus on relevant components
4. **Add logging to new code** using the appropriate macros/functions

#### Example Development Session
```bash
# Test user experience first
./scripts/run_example.sh examples/hello_world/main.py

# Enable debugging to investigate an issue
./scripts/run_example.sh --debug examples/hello_world/main.py

# Focus on just C router debugging
CATZILLA_C_DEBUG=1 python examples/router_groups/main.py

# Focus on just Python types debugging
CATZILLA_DEBUG=1 python examples/hello_world/main.py
```

#### Testing with Debug Logging
```bash
# Test normal operation (clean output)
./scripts/run_tests.sh

# Test with full debugging enabled
CATZILLA_C_DEBUG=1 CATZILLA_DEBUG=1 ./scripts/run_tests.sh

# Debug specific test failures
CATZILLA_C_DEBUG=1 python -m pytest tests/python/test_specific.py -v
```

### Adding Debug Logging to New Code

#### For C Code
1. **Include the logging header**: `#include "logging.h"`
2. **Choose appropriate module**: SERVER, ROUTER, or HTTP
3. **Select appropriate level**: DEBUG, INFO, WARN, or ERROR
4. **Use descriptive messages**: Include relevant context and data

```c
#include "logging.h"

int new_feature_function(const char* param) {
    LOG_SERVER_DEBUG("Starting new feature with param: %s", param);

    if (!param) {
        LOG_SERVER_ERROR("Invalid parameter: param cannot be NULL");
        return -1;
    }

    // Implementation here

    LOG_SERVER_INFO("New feature completed successfully");
    return 0;
}
```

#### For Python Code
1. **Import logging functions**: `from catzilla.logging import log_*_*`
2. **Choose appropriate module**: types, app, or request
3. **Use f-strings for formatting**: More readable and performant
4. **Log at appropriate times**: Entry/exit, errors, important state changes

```python
from catzilla.logging import log_app_debug, log_app_info, log_app_error

def new_feature_function(param):
    log_app_debug(f"Starting new feature with param: {param}")

    try:
        # Implementation here
        result = process_param(param)
        log_app_info(f"New feature completed: {result}")
        return result
    except Exception as e:
        log_app_error(f"New feature failed: {e}")
        raise
```

### Debugging Best Practices

1. **Use appropriate log levels**:
   - **DEBUG**: Verbose information for debugging (loops, state changes)
   - **INFO**: Important milestones (startup, successful operations)
   - **WARN**: Potential issues (using defaults, recoverable errors)
   - **ERROR**: Serious problems (failures, exceptions)

2. **Include context in messages**:
   - Parameter values, state information, error details
   - Module/function names when not obvious
   - Request IDs or identifiers when available

3. **Keep messages concise but informative**:
   - Avoid extremely long messages that clutter output
   - Include the most relevant information for debugging
   - Use consistent formatting within modules

4. **Test both modes**:
   - Always verify clean output for end users
   - Ensure debug output provides useful information
   - Check that logging doesn't impact performance

This professional logging system enables contributors to debug effectively while ensuring end users see only clean, professional output. The environment variable approach allows easy switching between modes without code changes.

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

3. **RouterGroup Organization**
   - Design RouterGroup hierarchies efficiently (< 6 levels deep)
   - Use clear, descriptive prefixes for maintainability
   - Group related routes together logically

4. **C-Accelerated Benefits**
   - C engine handles route matching transparently
   - Python layer manages business logic and handler execution
   - Automatic fallback ensures compatibility across environments

### Performance Testing

```bash
# Run examples to test performance
python examples/c_router_demo/main.py

# Test RouterGroups and examples
python examples/router_groups/main.py

# Test C acceleration
python examples/c_router_demo/main.py

# Run comprehensive tests
./scripts/run_tests.sh
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

## 🔧 Troubleshooting

### Virtual Environment Issues

**Problem: Commands fail with "module not found" errors**
```bash
# Solution: Ensure virtual environment is active
source venv/bin/activate
pip install -r requirements.txt
```

**Problem: `python` command uses system Python instead of venv**
```bash
# Check which Python you're using
which python
# Should show: /path/to/catzilla/venv/bin/python
# If not, reactivate: source venv/bin/activate
```

**Problem: Dependencies seem to be missing after setup**
```bash
# Verify virtual environment and reinstall dependencies
source venv/bin/activate
pip list  # Check installed packages
pip install -r requirements.txt --force-reinstall
```

**Problem: Virtual environment doesn't activate**
```bash
# Try recreating the virtual environment
rm -rf venv
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

**Problem: Build fails with missing dependencies**
```bash
# Ensure you're in virtual environment and have all build dependencies
source venv/bin/activate
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
./scripts/build.sh
```

### Common Development Issues

**Problem: Tests fail unexpectedly**
```bash
# Ensure clean environment and rebuild
source venv/bin/activate
./scripts/build.sh
./scripts/run_tests.sh
```

**Problem: C compilation errors**
```bash
# Check that CMake and compiler are available
cmake --version
gcc --version  # or clang --version
```

## 📚 Contributing to Documentation

The Catzilla documentation is built with Sphinx and hosted as professional-grade docs. We welcome contributions to improve documentation for all users.

### Documentation Structure

The documentation lives in the `docs/` directory with this structure:

- **`index.rst`** - Main documentation homepage
- **`quickstart.rst`** - Getting started guide
- **`advanced.rst`** - Advanced usage patterns
- **`conf.py`** - Sphinx configuration
- **`build_docs.py`** - Build and serve script
- **Reference docs** - Specialized topic guides (`.md` files)

### Setting Up Documentation Environment

1. **Install documentation dependencies:**
   ```bash
   source venv/bin/activate
   pip install -r requirements-dev.txt
   ```

2. **Build documentation locally:**
   ```bash
   cd docs
   python build_docs.py build
   # or
   make html
   ```

3. **Serve documentation locally:**
   ```bash
   python build_docs.py build-serve
   # Opens on http://localhost:8080
   ```

### Documentation Contribution Guidelines

#### Adding New Content

1. **Create new documentation files:**
   - Use `.rst` for main guides (preferred)
   - Use `.md` for specialized topics
   - Follow existing structure and style

2. **Update the table of contents:**
   - Add new files to `index.rst` toctree
   - Organize by appropriate section (Getting Started, User Guide, Reference)

3. **Test your changes:**
   ```bash
   cd docs
   python build_docs.py build
   # Check for warnings and fix any issues
   ```

#### Editing Existing Documentation

1. **Update content files:**
   - Maintain consistent formatting
   - Keep code examples functional and tested
   - Follow the established writing style

2. **Verify examples work:**
   ```bash
   # Test any code examples you modify
   cd examples/
   python your_example.py
   ```

3. **Build and review:**
   ```bash
   cd docs
   python build_docs.py build-serve
   # Review changes in browser
   ```

#### Documentation Standards

**Writing Style:**
- Clear, concise explanations
- Developer-focused content
- Step-by-step instructions for tutorials
- Real-world, practical examples

**Code Examples:**
- All examples must be functional and tested
- Include complete, runnable code when possible
- Follow Python best practices
- Add comments explaining key concepts

**Technical Requirements:**
- Documentation builds without warnings
- Cross-references work correctly
- All links and internal references are valid
- Mobile-responsive and accessible

### Documentation Deployment

#### Automatic Deployment (GitHub Actions)

Documentation is automatically built and deployed when you push changes:

- **Workflow**: `.github/workflows/docs.yml`
- **Triggers**: Changes to `docs/**` or `python/catzilla/**` on main branch
- **Deployment**: GitHub Pages at `https://[username].github.io/catzilla/`

**Before submitting documentation PRs:**

```bash
# Clean and rebuild to catch issues
cd docs
python build_docs.py clean
python build_docs.py build

# Check for warnings or errors in output
# Test locally before pushing
python build_docs.py serve
```

#### Manual Deployment Options

For custom hosting setups:

```bash
# Build for production
cd docs
python build_docs.py build

# Deploy _build/html/ contents to your hosting service
# (Netlify, Vercel, custom server, etc.)
```

### Common Documentation Tasks

#### Adding API Documentation

```bash
# Document new features in quickstart.rst or advanced.rst
# Include practical examples:

@app.get("/api/users/{user_id}")
def get_user(request):
    user_id = request.path_params["user_id"]
    return {"user_id": user_id, "name": "John Doe"}
```

#### Updating Framework Examples

```bash
# Test examples work with current codebase:
cd examples/
python hello_world/app.py

# Update docs to match any API changes
vim docs/quickstart.rst
```

#### Adding Performance Documentation

```bash
# Include benchmarks and performance tips:
cd benchmarks/
./run_all.sh
# Use results to update docs/performance.md
```

### Documentation Deployment

The documentation is automatically deployed via GitHub Actions when changes are merged to main. For local testing:

```bash
# Full documentation workflow:
cd docs
python build_docs.py clean  # if needed
python build_docs.py build
python build_docs.py serve
```

### Documentation Issues

When reporting documentation issues:
1. Specify the exact page/section
2. Include suggested improvements
3. Test with the latest Catzilla version
4. Check that examples work as documented

For documentation questions, see our comprehensive [Documentation README](docs/README.md).

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
