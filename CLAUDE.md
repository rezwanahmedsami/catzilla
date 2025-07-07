
<!--
Claude: Use this guide as project context for all coding, debugging, and architectural tasks. Prioritize performance, FastAPI compatibility, and cross-platform stability. Always validate changes with benchmarks and ./scripts/run_tests.sh. Never add unnecessary dependencies.
-->

# CLAUDE.md — Catzilla Project AI Agent Guide

## 🤖 Claude Code Instructions

- Assume you are a C/Python performance engineer working on Catzilla.
- Your primary goals:
  1. Maintain FastAPI-style API in Python
  2. Maximize C-side performance and safety
  3. Ensure jemalloc memory efficiency
  4. Maintain cross-platform build compatibility
- Never suggest adding unnecessary Python dependencies.
- Use only standard library + CPython extensions unless explicitly told otherwise.
- Always validate your changes with benchmarks and `./scripts/run_tests.sh`.
- Use this document as your complete reference while developing inside this project.

## Summary for AI Agents

When working on Catzilla, always remember:

1. **Performance is King**: Every change must maintain or improve performance
2. **FastAPI Compatibility**: Maintain 95% syntax compatibility
3. **Memory Efficiency**: Use jemalloc properly for 30-35% savings
4. **Cross-Platform**: Code must work on Windows, macOS, and Linux
5. **Test Everything**: Comprehensive testing is non-negotiable
6. **Document Changes**: User-facing changes need documentation
7. **Security First**: Validate inputs and handle errors properly
8. **Virtual Environments**: Always use venv for development

**Key Performance Targets:**
- Maintain 6.5-24x performance advantage over FastAPI
- Keep memory usage 30-35% lower than baseline
- Ensure zero memory leaks in C code
- Support 400,000+ RPS for static files
- Achieve sub-7ms average response times

**Critical Files to Understand:**
- `python/catzilla/app.py` - Main application class
- `src/core/router.c` - Core routing engine
- `src/core/memory.c` - Memory management
- `CMakeLists.txt` - Build configuration
- `docs/` - Comprehensive documentation

---

## 📋 Table of Contents

- [Project Overview](#project-overview)
- [Core Architecture](#core-architecture)
- [Technology Stack](#technology-stack)
- [Project Structure](#project-structure)
- [Development Guidelines](#development-guidelines)
- [Build System](#build-system)
- [Testing Framework](#testing-framework)
- [Performance Requirements](#performance-requirements)
- [Memory Management](#memory-management)
- [Feature Systems](#feature-systems)
- [Documentation Standards](#documentation-standards)
- [Code Quality Standards](#code-quality-standards)
- [File Patterns](#file-patterns)
- [Common Development Tasks](#common-development-tasks)
- [Error Handling](#error-handling)
- [Platform Compatibility](#platform-compatibility)
- [Security Considerations](#security-considerations)

---


## Project Overview

Catzilla is a Python web framework focused on:
- Extreme performance (6.5–24x faster than FastAPI)
- jemalloc-based memory efficiency (30–35% savings)
- C-accelerated core (libuv, llhttp, trie routing)
- FastAPI compatibility (95%+ syntax match)
- Zero dependencies (uses only Python standard library)

**Status:** Production ready (v0.2.0, 9/11 features complete)

**Mission:** Deliver maximum performance and developer productivity with minimal boilerplate, while maintaining FastAPI-style API and cross-platform support.

---

## Core Architecture

### Hybrid C/Python Design

```
┌─────────────────────────────────────────────────┐
│                Python Layer                     │
│  - Developer API (FastAPI-style)                │
│  - Request/Response handling                     │
│  - Business logic integration                    │
└─────────────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────┐
│               Python C Extension                │
│  - CPython bindings                             │
│  - Memory management bridge                     │
│  - Type conversion and safety                   │
└─────────────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────┐
│                 C Core Engine                   │
│  - libuv event loop                             │
│  - llhttp parser                                │
│  - Trie-based routing (O(log n))                │
│  - jemalloc memory optimization                 │
│  - Thread-safe operations                       │
└─────────────────────────────────────────────────┘
```

### Key Design Principles

1. **Performance First**: Every component optimized for maximum throughput
2. **Memory Efficiency**: jemalloc arena specialization for 30-35% savings
3. **Zero Overhead**: Minimal abstraction layers between Python and C
4. **FastAPI Compatibility**: Drop-in replacement with identical syntax
5. **Production Ready**: Enterprise-grade error handling and security
6. **Platform Agnostic**: Windows, macOS, Linux support with optimizations

---

## Technology Stack

### Core Dependencies

**C Dependencies** (bundled as git submodules):
- `libuv` - Cross-platform asynchronous I/O
- `llhttp` - Fast HTTP/1.x parser
- `jemalloc` - Memory allocator (optional, performance critical)
- `unity` - C testing framework

**Python Dependencies** (minimal):
- `psutil>=5.9.0` - System monitoring (only runtime dependency)

**Build Dependencies**:
- `CMake 3.15+` - Build system
- `Python 3.8+` - Runtime (3.10+ recommended)
- C Compiler (GCC/Clang/MSVC)

### Platform Support Matrix

| Platform | Architecture | Status | Pre-built Wheels |
|----------|-------------|---------|------------------|
| Linux | x86_64 | ✅ Full Support | ✅ manylinux2014 |
| macOS | x86_64 (Intel) | ✅ Full Support | ✅ macOS 10.15+ |
| macOS | ARM64 (Apple Silicon) | ✅ Full Support | ✅ macOS 11.0+ |
| Windows | x86_64 | ✅ Full Support | ✅ Windows 10+ |
| Linux | ARM64 | ⚠️ Source Only | ❌ No pre-built wheel |

**Python Versions**: 3.8, 3.9, 3.10, 3.11, 3.12, 3.13

---

## Project Structure

```
catzilla/
├── 📦 Package Management
│   ├── setup.py                     # Python package build (uses CMake)
│   ├── pyproject.toml               # Modern Python packaging (PEP 621)
│   ├── requirements.txt             # Runtime dependencies (minimal)
│   ├── requirements-dev.txt         # Development dependencies
│   └── requirements-benchmarks.txt  # Performance testing tools
│
├── 🏗️ Build System
│   ├── CMakeLists.txt               # Main CMake configuration
│   ├── Makefile                     # Alternative build interface
│   └── cmake/                       # CMake modules and utilities
│       └── DetectJemallocPrefix.cmake
│
├── 🔧 C Core Implementation
│   └── src/core/                    # All C source files
│       ├── server.c/h              # Main HTTP server (libuv-based)
│       ├── router.c/h              # Trie-based routing engine
│       ├── memory.c/h              # jemalloc integration
│       ├── validation.c/h          # C-accelerated validation
│       ├── dependency.c/h          # C-compiled dependency injection
│       ├── middleware.c/h          # Zero-allocation middleware
│       ├── task_system.c/h         # Background task thread pool
│       ├── cache_engine.c/h        # Smart caching system
│       ├── static_server.c/h       # C-native static file server
│       ├── upload_parser.c/h       # File upload system
│       ├── streaming.c/h           # HTTP streaming support
│       └── platform_*.h           # Cross-platform compatibility
│
├── 🐍 Python Package
│   └── python/catzilla/            # Main Python package
│       ├── __init__.py             # Public API exports
│       ├── app.py                  # Main Catzilla class (1659 lines)
│       ├── routing.py              # High-level Router and RouterGroup
│       ├── types.py                # Request/Response types
│       ├── dependency_injection.py # DI system Python layer
│       ├── auto_validation.py      # FastAPI-style validation
│       ├── middleware.py           # Middleware system
│       ├── background_tasks.py     # Background task Python API
│       ├── smart_cache.py          # Caching system
│       ├── uploads.py              # File upload system
│       ├── streaming.py            # Streaming response support
│       ├── memory.py               # Memory management utilities
│       └── logging/                # Logging and startup banners
│
├── 📚 Documentation
│   └── docs/                       # Comprehensive documentation
│       ├── index.rst               # Sphinx main page
│       ├── quickstart.rst          # Getting started guide
│       ├── advanced.rst            # Advanced usage patterns
│       ├── auto-validation*.md     # Validation system docs (4 files)
│       ├── dependency_injection*.md # DI system docs (5 files)
│       ├── static_file_server*.md  # Static server docs (4 files)
│       ├── smart_caching_system.md # Caching documentation
│       ├── middleware*.md          # Middleware system docs
│       ├── file-upload-system.md   # Upload system documentation
│       └── c-accelerated-routing.md # Technical routing details
│
├── 🧪 Testing
│   └── tests/                      # Comprehensive test suite (90+ tests)
│       ├── c/                      # C unit tests (28 tests)
│       ├── python/                 # Python tests (62+ tests)
│       └── integration/            # Integration tests
│
├── 💡 Examples
│   └── examples/                   # Real-world example applications
│       ├── hello_world/            # Basic usage
│       ├── simple_di/              # Dependency injection basics
│       ├── advanced_di/            # Enterprise DI features
│       ├── static_file_server/     # Static file serving
│       ├── file_upload_system/     # File upload examples
│       ├── middleware/             # Middleware examples
│       ├── validation_engine/      # Validation examples
│       ├── router_groups/          # Route organization
│       └── background_tasks/       # Background processing
│
├── 🚀 Development Tools
│   └── scripts/                    # Development automation
│       ├── build.sh                # Complete build script
│       ├── run_tests.sh            # Unified test runner
│       ├── run_example.sh          # Example runner
│       └── bump_version.sh         # Version management
│
├── 📋 Planning & Status
│   ├── plan/                       # Engineering plans (9 files)
│   ├── summary/                    # Implementation summaries
│   └── *.md                        # Various status reports
│
├── 🏭 CI/CD & Deployment
│   ├── .github/workflows/          # GitHub Actions
│   ├── docker/                     # Docker configurations
│   └── benchmarks/                 # Performance testing
│
└── 📦 Dependencies (Git Submodules)
    └── deps/                       # External C libraries
        ├── libuv/                  # Event loop library
        ├── jemalloc/               # Memory allocator
        └── unity/                  # C testing framework
```

---

## Development Guidelines

### Critical Requirements

1. **Virtual Environment Mandatory**: All development MUST use Python virtual environments
2. **Submodule Initialization**: Always run `git submodule update --init --recursive`
3. **CMake Build**: Never bypass CMake - it handles complex C compilation
4. **Memory Safety**: All C code must be leak-free and thread-safe
5. **Performance First**: Every change must consider performance impact
6. **FastAPI Compatibility**: Maintain 95% syntax compatibility
7. **Cross-Platform**: Code must work on Windows, macOS, and Linux

### Development Workflow

```bash
# 1. Setup (REQUIRED)
git clone --recursive https://github.com/rezwanahmedsami/catzilla.git
cd catzilla
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows

# 2. Install dependencies
pip install -r requirements-dev.txt

# 3. Build (CRITICAL)
./scripts/build.sh  # or scripts\build.bat on Windows

# 4. Test before changes
./scripts/run_tests.sh

# 5. Make changes...

# 6. Test after changes
./scripts/run_tests.sh

# 7. Performance validation
python -m pytest tests/python/test_validation_performance.py -v
```

### Code Style Guidelines

**Python Code**:
- Follow PEP 8 with 100-character line limit
- Use type hints for all public APIs
- Document all public functions with docstrings
- Prefer composition over inheritance
- Use descriptive variable names

**C Code**:
- Follow ANSI C11 standard
- Prefix all public functions with `catzilla_`
- Use `snake_case` for functions and variables
- Include comprehensive error handling
- Document complex algorithms
- Thread-safe by default

---

## Build System

### CMake Configuration

The build system is sophisticated and handles:

- **Cross-platform compilation** (Windows MSVC, macOS Clang, Linux GCC)
- **jemalloc integration** (static linking with runtime detection)
- **Dependency management** (libuv, llhttp from submodules)
- **Python extension building** (CPython C API)
- **Optimization flags** (Release builds with O3)

### Key CMake Variables

```cmake
# Memory allocator options
CATZILLA_USE_JEMALLOC=ON         # Enable jemalloc (recommended)
CATZILLA_BUILD_JEMALLOC=ON       # Build from source
CATZILLA_JEMALLOC_DEBUG=OFF      # Debug features

# Build configuration
CMAKE_BUILD_TYPE=Release         # Release/Debug
CATZILLA_ENABLE_TESTS=ON         # Build C tests
CATZILLA_ENABLE_BENCHMARKS=ON    # Build benchmarks
```

### Build Commands

```bash
# Standard build (recommended)
./scripts/build.sh

# Manual CMake build
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build -j$(nproc)
pip install -e .

# Clean rebuild
rm -rf build/
./scripts/build.sh
```

---

## Testing Framework

### Test Structure (90+ Tests Total)

**C Tests** (28 tests):
- `tests/c/test_router.c` - Basic router functionality
- `tests/c/test_advanced_router.c` - Advanced routing features (14 tests)
- `tests/c/test_server_integration.c` - Server integration (11 tests)

**Python Tests** (62+ tests):
- `test_advanced_routing.py` - Python routing layer (22 tests)
- `test_http_responses.py` - HTTP response handling (17 tests)
- `test_basic.py` - Basic functionality (10 tests)
- `test_request.py` - Request handling (13 tests)
- `test_validation_engine.py` - Validation system
- `test_dependency_injection.py` - DI system
- `test_middleware.py` - Middleware system
- `test_background_tasks.py` - Background tasks
- `test_static_file_server.py` - Static file serving
- `test_upload_system.py` - File upload system
- `test_smart_cache.py` - Caching system
- `test_streaming.py` - Streaming responses

### Running Tests

```bash
# All tests (recommended)
./scripts/run_tests.sh

# Specific test suites
./scripts/run_tests.sh --python    # Python tests only
./scripts/run_tests.sh --c         # C tests only
./scripts/run_tests.sh --verbose   # Detailed output

# Individual test files
python -m pytest tests/python/test_validation_engine.py -v
python -m pytest tests/python/test_dependency_injection.py -v
```

### Test Requirements

- **All new features** must have comprehensive tests
- **C code** must have unit tests in `tests/c/`
- **Python code** must have pytest tests in `tests/python/`
- **Integration tests** must verify end-to-end functionality
- **Performance tests** must validate speed improvements
- **Memory tests** must ensure no leaks

---

## Performance Requirements

### Benchmarking Standards

Catzilla maintains strict performance benchmarks:

| Metric | Catzilla Target | FastAPI Baseline | Improvement |
|--------|----------------|------------------|-------------|
| Hello World | 24,759 RPS | 2,844 RPS | +771% |
| JSON Response | 15,754 RPS | 2,421 RPS | +551% |
| Path Parameters | 17,590 RPS | 2,341 RPS | +651% |
| Average Latency | <7ms | 47.69ms | 87% lower |
| Memory Usage | -30% to -35% | Baseline | jemalloc |

### Performance Testing

```bash
# Run benchmarks
cd benchmarks/
./run_all.sh

# Specific performance tests
python -m pytest tests/python/test_validation_performance.py -v
python -m pytest tests/python/test_dependency_injection.py::test_performance -v

# Memory profiling
python -c "
from catzilla import Catzilla
app = Catzilla()
stats = app.get_memory_stats()
print(f'Memory efficiency: {stats[\"fragmentation_percent\"]:.1f}%')
"
```

### Performance Monitoring

- **Real-time memory statistics** available via `app.get_memory_stats()`
- **Request/response metrics** collected automatically
- **Benchmark regression testing** in CI/CD
- **Memory leak detection** in all tests

---

## Memory Management

### jemalloc Integration

Catzilla's "Memory Revolution" provides 30-35% efficiency through jemalloc:

**Arena Specialization**:
- **Request Arena**: Short-lived request processing
- **Response Arena**: Response building and serialization
- **Cache Arena**: Long-lived data with minimal fragmentation
- **Static Arena**: Static file serving with memory pooling
- **Task Arena**: Background operations with isolated allocation

**Configuration**:
```python
from catzilla import Catzilla

# Automatic jemalloc optimization (recommended)
app = Catzilla()  # Memory revolution activated!

# Memory statistics
stats = app.get_memory_stats()
print(f"Allocated: {stats['allocated_mb']:.2f} MB")
print(f"Fragmentation: {stats['fragmentation_percent']:.1f}%")
```

### Memory Safety Requirements

1. **No Memory Leaks**: All C code must pass Valgrind/AddressSanitizer
2. **Bounded Allocation**: Prevent unbounded memory growth
3. **Arena Isolation**: Use appropriate jemalloc arenas
4. **Automatic Cleanup**: RAII patterns in C code
5. **Thread Safety**: All memory operations must be thread-safe

---

## Feature Systems

### 1. Ultra-Fast Validation Engine

**Performance**: 90,000+ validations/sec, 20x faster than FastAPI

**Usage**:
```python
from catzilla import Catzilla, BaseModel, Field, Query, Path

app = Catzilla()

class UserModel(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    age: int = Field(ge=0, le=150)
    email: str = Field(regex=r'^[^@]+@[^@]+\.[^@]+$')

@app.post("/users")
def create_user(request, user: UserModel):
    return {"created": user.dict()}

@app.get("/users/{user_id}")
def get_user(request, user_id: int = Path(ge=1)):
    return {"user_id": user_id}
```

**Implementation Files**:
- `src/core/validation.c/.h` - C validation engine
- `python/catzilla/auto_validation.py` - Python API
- `docs/auto-validation*.md` - Documentation (4 files)

### 2. Revolutionary Dependency Injection

**Performance**: 6.5x faster dependency resolution than FastAPI

**Usage**:
```python
from catzilla import Catzilla, Depends

app = Catzilla()

class DatabaseService:
    def get_connection(self):
        return "database_connection"

def get_database() -> DatabaseService:
    return DatabaseService()

@app.get("/data")
def get_data(request, db: DatabaseService = Depends(get_database)):
    return {"connection": db.get_connection()}
```

**Implementation Files**:
- `src/core/dependency.c/.h` - C dependency resolution
- `python/catzilla/dependency_injection.py` - Python DI system
- `docs/dependency_injection*.md` - Documentation (5 files)

### 3. Zero-Allocation Middleware System

**Performance**: 10-15x faster, 40-50% memory reduction

**Usage**:
```python
from catzilla import Catzilla, ZeroAllocMiddleware

app = Catzilla()

def timing_middleware(request, call_next):
    start_time = time.time()
    response = call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response

# Per-route middleware (FastAPI-style)
@app.get("/api/data", middleware=[timing_middleware])
def get_data(request):
    return {"data": "example"}
```

**Implementation Files**:
- `src/core/middleware.c/.h` - C middleware execution
- `python/catzilla/middleware.py` - Python middleware API

### 4. C-Native Static File Server

**Performance**: 400,000+ RPS for cached files, nginx-level performance

**Usage**:
```python
from catzilla import Catzilla

app = Catzilla()

# Mount static files
app.mount_static("/static", "./static")
app.mount_static("/assets", "./assets", cache_control="max-age=31536000")

# Advanced configuration
app.mount_static("/files", "./files", config={
    "enable_compression": True,
    "compression_level": 6,
    "cache_size_mb": 100,
    "enable_etags": True,
    "enable_range_requests": True
})
```

**Implementation Files**:
- `src/core/static_server.c/.h` - C static file engine
- `docs/static_file_server*.md` - Documentation (4 files)

### 5. Revolutionary File Upload System

**Performance**: 10-100x faster than FastAPI for large files

**Usage**:
```python
from catzilla import Catzilla, UploadFile, File

app = Catzilla()

@app.post("/upload")
def upload_file(request, file: UploadFile = File(...)):
    # C-native parsing, zero-copy streaming
    saved_path = file.save("/uploads/")
    return {"filename": file.filename, "size": file.size}

@app.post("/upload/multiple")
def upload_multiple(request, files: List[UploadFile] = File(...)):
    results = []
    for file in files:
        saved_path = file.save("/uploads/")
        results.append({"filename": file.filename, "path": saved_path})
    return {"uploaded": len(results), "files": results}
```

**Implementation Files**:
- `src/core/upload_parser.c/.h` - C multipart parser
- `python/catzilla/uploads.py` - Python upload API

### 6. Background Task System

**Performance**: 81,466 tasks/second submission rate

**Usage**:
```python
from catzilla import Catzilla, BackgroundTasks

app = Catzilla()

def send_email(to: str, subject: str, body: str):
    # Heavy email sending operation
    time.sleep(2)
    print(f"Email sent to {to}")

@app.post("/send-notification")
def send_notification(request, background_tasks: BackgroundTasks):
    background_tasks.add_task(send_email, "user@example.com", "Hello", "World")
    return {"message": "Notification queued"}
```

**Implementation Files**:
- `src/core/task_system.c/.h` - C thread pool
- `python/catzilla/background_tasks.py` - Python task API

### 7. Smart Caching System

**Performance**: 10-50x faster response times for cached content

**Usage**:
```python
from catzilla import Catzilla
from catzilla.smart_cache import cache, CacheConfig

app = Catzilla()

@app.get("/expensive-data")
@cache(ttl=300, key_func=lambda request: f"data:{request.query_params.get('id')}")
def get_expensive_data(request):
    # Expensive computation
    return {"data": "expensive_result"}

# Configure caching
app.configure_cache(CacheConfig(
    l1_size_mb=50,      # C-level memory cache
    l2_redis_url="redis://localhost",  # Optional Redis
    l3_disk_path="/tmp/cache"          # Optional disk cache
))
```

**Implementation Files**:
- `src/core/cache_engine.c/.h` - C caching engine
- `python/catzilla/smart_cache.py` - Python caching API

### 8. HTTP Streaming Support

**Features**: True incremental streaming with chunked transfer encoding

**Usage**:
```python
from catzilla import Catzilla, StreamingResponse

app = Catzilla()

@app.get("/stream")
def stream_data(request):
    def generate():
        for i in range(1000):
            yield f"Chunk {i}\n"
            time.sleep(0.1)  # Simulate real-time data

    return StreamingResponse(generate(), content_type="text/plain")

# AI/LLM streaming example
@app.post("/chat/stream")
def chat_stream(request):
    def generate_ai_response():
        # Simulate AI token streaming
        tokens = ["Hello", " ", "world", "!", " How", " can", " I", " help", "?"]
        for token in tokens:
            yield f"data: {token}\n\n"
            time.sleep(0.1)

    return StreamingResponse(generate_ai_response(), content_type="text/plain")
```

**Implementation Files**:
- `src/core/streaming.c/.h` - C streaming engine
- `python/catzilla/streaming.py` - Python streaming API

---

## Documentation Standards

### Documentation Structure

Catzilla maintains comprehensive, user-friendly documentation:

1. **Getting Started**: Quick setup and basic usage
2. **Feature Guides**: Detailed guides for each major feature
3. **API Reference**: Complete Python and C API documentation
4. **Migration Guides**: FastAPI to Catzilla migration
5. **Performance Guides**: Optimization techniques
6. **Troubleshooting**: Common issues and solutions

### Documentation Requirements

**For New Features**:
- **User Guide**: Step-by-step tutorial with examples
- **API Reference**: Complete function/class documentation
- **Performance Metrics**: Benchmarks and comparisons
- **Migration Guide**: How to upgrade existing code
- **Troubleshooting**: Common issues and solutions

**Documentation Files**:
- Create markdown files in `docs/` directory
- Use descriptive filenames (e.g., `feature-name-guide.md`)
- Include performance metrics and code examples
- Cross-reference related documentation

**Example Documentation Structure**:
```markdown
# Feature Name Guide

## Overview
Brief description of the feature and its benefits.

## Quick Start
Minimal working example (5-10 lines).

## API Reference
Complete function/class documentation.

## Performance
Benchmarks and optimization tips.

## Examples
Real-world usage examples.

## Migration
How to upgrade existing code.

## Troubleshooting
Common issues and solutions.
```

---

## Code Quality Standards

### Code Review Checklist

**Performance**:
- [ ] No performance regressions
- [ ] Memory usage optimized
- [ ] Benchmark tests pass
- [ ] C code is leak-free

**Compatibility**:
- [ ] FastAPI syntax maintained
- [ ] Cross-platform compatibility
- [ ] Python 3.8+ support
- [ ] Backward compatibility preserved

**Testing**:
- [ ] Unit tests for all new code
- [ ] Integration tests for features
- [ ] Performance tests included
- [ ] Memory leak tests pass

**Documentation**:
- [ ] User-facing changes documented
- [ ] API documentation updated
- [ ] Examples provided
- [ ] Migration guide updated

**Code Quality**:
- [ ] Type hints for Python code
- [ ] Error handling comprehensive
- [ ] Thread safety considerations
- [ ] Security best practices

### Static Analysis Tools

```bash
# Code quality checks
flake8 python/catzilla/          # Python linting
bandit python/catzilla/          # Security analysis
safety check                     # Dependency vulnerability scan
pre-commit run --all-files       # Pre-commit hooks

# C code analysis (if available)
cppcheck src/core/               # Static analysis
valgrind --tool=memcheck         # Memory leak detection
```

---

## File Patterns

### Python Module Patterns

**Core Modules** (`python/catzilla/`):
- `app.py` - Main Catzilla class (1659 lines)
- `routing.py` - Router and RouterGroup classes
- `types.py` - Request/Response/Handler types
- `exceptions.py` - Custom exception classes
- `decorators.py` - Decorator utilities

**Feature Modules**:
- `auto_validation.py` - Validation system
- `dependency_injection.py` - DI system
- `middleware.py` - Middleware system
- `background_tasks.py` - Background task system
- `smart_cache.py` - Caching system
- `uploads.py` - File upload system
- `streaming.py` - Streaming responses
- `memory.py` - Memory management utilities

### C Source Patterns

**Core C Files** (`src/core/`):
- `server.c/.h` - Main HTTP server
- `router.c/.h` - Routing engine
- `memory.c/.h` - Memory management
- Platform compatibility headers: `platform_*.h`

**Feature C Files**:
- `validation.c/.h` - Validation engine
- `dependency.c/.h` - Dependency injection
- `middleware.c/.h` - Middleware system
- `task_system.c/.h` - Background tasks
- `cache_engine.c/.h` - Caching system
- `static_server.c/.h` - Static file server
- `upload_parser.c/.h` - File upload parser
- `streaming.c/.h` - Streaming support

### Test Patterns

**C Tests** (`tests/c/`):
- `test_*.c` - Unit tests for C modules
- Use Unity testing framework
- Follow `test_function_name` convention

**Python Tests** (`tests/python/`):
- `test_*.py` - pytest-based tests
- `test_*_performance.py` - Performance tests
- `test_*_integration.py` - Integration tests

---

## Common Development Tasks

### Adding a New Feature

1. **Planning**:
   ```bash
   # Create feature plan
   touch plan/new_feature_engineering_plan.md
   # Document architecture, performance targets, API design
   ```

2. **C Implementation**:
   ```bash
   # Create C source files
   touch src/core/new_feature.c src/core/new_feature.h
   # Implement core functionality
   # Add to CMakeLists.txt
   ```

3. **Python Integration**:
   ```bash
   # Create Python module
   touch python/catzilla/new_feature.py
   # Add to __init__.py exports
   ```

4. **Testing**:
   ```bash
   # Create tests
   touch tests/c/test_new_feature.c
   touch tests/python/test_new_feature.py
   # Run tests
   ./scripts/run_tests.sh
   ```

5. **Documentation**:
   ```bash
   # Create user guide
   touch docs/new-feature-guide.md
   # Update main documentation
   ```

### Performance Optimization

1. **Measure Current Performance**:
   ```bash
   # Run benchmarks
   cd benchmarks/
   ./run_all.sh

   # Profile specific features
   python -m pytest tests/python/test_*_performance.py -v
   ```

2. **Optimize C Code**:
   - Use profiler (gprof, perf, Instruments)
   - Focus on hot paths
   - Minimize memory allocations
   - Use jemalloc arenas appropriately

3. **Validate Improvements**:
   ```bash
   # Compare before/after
   ./scripts/run_tests.sh --performance
   # Ensure no regressions
   ```

### Adding FastAPI Compatibility

1. **Analyze FastAPI Feature**:
   - Study FastAPI documentation
   - Identify core functionality
   - Design Catzilla equivalent

2. **Implement Compatibility Layer**:
   ```python
   # In appropriate module
   def fastapi_compatible_function(*args, **kwargs):
       # Convert FastAPI semantics to Catzilla
       return catzilla_native_function(*args, **kwargs)
   ```

3. **Test Compatibility**:
   ```python
   # Create migration tests
   def test_fastapi_migration():
       # Test identical syntax works
       assert fastapi_code_works_in_catzilla()
   ```

### Memory Optimization

1. **Identify Memory Issues**:
   ```bash
   # Memory profiling
   python -c "
   from catzilla import Catzilla
   app = Catzilla()
   stats = app.get_memory_stats()
   print('Before optimization:', stats)
   "
   ```

2. **Apply jemalloc Optimization**:
   ```c
   // Use appropriate arena
   void* ptr = je_mallocx(size, MALLOCX_ARENA(CATZILLA_REQUEST_ARENA));
   // ... use memory ...
   je_dallocx(ptr, MALLOCX_ARENA(CATZILLA_REQUEST_ARENA));
   ```

3. **Validate Improvements**:
   ```bash
   # Test memory efficiency
   python -m pytest tests/python/test_critical_memory_leaks.py -v
   ```

---

## Error Handling

### Error Handling Patterns

**C Code Error Handling**:
```c
int catzilla_function(catzilla_context_t* ctx, const char* input) {
    if (!ctx || !input) {
        return CATZILLA_ERROR_INVALID_ARGS;
    }

    // Perform operation
    int result = some_operation(input);
    if (result < 0) {
        ctx->error_code = CATZILLA_ERROR_OPERATION_FAILED;
        snprintf(ctx->error_message, sizeof(ctx->error_message),
                "Operation failed with code: %d", result);
        return CATZILLA_ERROR_OPERATION_FAILED;
    }

    return CATZILLA_SUCCESS;
}
```

**Python Error Handling**:
```python
from catzilla.exceptions import CatzillaError, ValidationError

def catzilla_function(data):
    try:
        # Validate input
        if not isinstance(data, dict):
            raise ValidationError("Expected dict input")

        # Perform operation
        result = c_native_operation(data)
        return result

    except CatzillaError:
        # Re-raise Catzilla errors
        raise
    except Exception as e:
        # Wrap other exceptions
        raise CatzillaError(f"Unexpected error: {e}") from e
```

### Error Code Conventions

**C Error Codes** (`src/core/common.h`):
```c
#define CATZILLA_SUCCESS                  0
#define CATZILLA_ERROR_INVALID_ARGS      -1
#define CATZILLA_ERROR_MEMORY_ALLOCATION -2
#define CATZILLA_ERROR_OPERATION_FAILED  -3
#define CATZILLA_ERROR_THREAD_SAFETY     -4
#define CATZILLA_ERROR_VALIDATION        -5
```

**Python Exceptions** (`python/catzilla/exceptions.py`):
- `CatzillaError` - Base exception
- `ValidationError` - Input validation failures
- `RoutingError` - Routing-related errors
- `MemoryError` - Memory allocation failures
- `ConfigurationError` - Configuration issues

---

## Platform Compatibility

### Cross-Platform Considerations

**Windows Compatibility**:
- Use `platform_compat.h` for Windows-specific code
- Handle different path separators
- Use MSVC-compatible C code (no VLA, different pragmas)
- Unicode handling for file paths

**macOS Compatibility**:
- Support both Intel and Apple Silicon
- Handle different library paths for jemalloc
- Use proper Mach-O linking flags

**Linux Compatibility**:
- Support various distributions (Ubuntu, CentOS, etc.)
- Handle different library versions
- Use manylinux wheels for compatibility

### Platform-Specific Files

- `src/core/platform_compat.h` - Cross-platform compatibility
- `src/core/platform_threading.h` - Threading primitives
- `src/core/platform_atomic.h` - Atomic operations
- `src/core/windows_compat.h` - Windows-specific compatibility

---

## Security Considerations

### Security Best Practices

**Input Validation**:
- Validate all user input in C validation engine
- Prevent buffer overflows and memory corruption
- Use safe string handling functions
- Implement proper bounds checking

**Memory Safety**:
- Use jemalloc for memory safety features
- Implement proper cleanup in error paths
- Prevent use-after-free vulnerabilities
- Use static analysis tools

**HTTP Security**:
- Implement proper header validation
- Prevent HTTP response splitting
- Handle malformed requests safely
- Implement rate limiting support

**File System Security**:
- Validate file paths in static server
- Prevent directory traversal attacks
- Implement proper access controls
- Sanitize file uploads

### Security Testing

```bash
# Security analysis
bandit python/catzilla/                # Python security scan
safety check                          # Dependency vulnerabilities

# Memory safety (if available)
valgrind --tool=memcheck ./catzilla_tests
clang -fsanitize=address               # Address sanitizer
```

---

## Summary for AI Agents

When working on Catzilla, always remember:

1. **Performance is King**: Every change must maintain or improve performance
2. **FastAPI Compatibility**: Maintain 95% syntax compatibility
3. **Memory Efficiency**: Use jemalloc properly for 30-35% savings
4. **Cross-Platform**: Code must work on Windows, macOS, and Linux
5. **Test Everything**: Comprehensive testing is non-negotiable
6. **Document Changes**: User-facing changes need documentation
7. **Security First**: Validate inputs and handle errors properly
8. **Virtual Environments**: Always use venv for development

**Key Performance Targets**:
- Maintain 6.5-24x performance advantage over FastAPI
- Keep memory usage 30-35% lower than baseline
- Ensure zero memory leaks in C code
- Support 400,000+ RPS for static files
- Achieve sub-7ms average response times

**Critical Files to Understand**:
- `python/catzilla/app.py` - Main application class
- `src/core/router.c` - Core routing engine
- `src/core/memory.c` - Memory management
- `CMakeLists.txt` - Build configuration
- `docs/` - Comprehensive documentation

This guide provides everything needed to understand and contribute to Catzilla effectively. The project represents a breakthrough in Python web framework performance while maintaining developer productivity and FastAPI compatibility.
