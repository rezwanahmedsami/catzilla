# Catzilla v0.1.0
Blazing-fast Python web framework with production-grade routing backed by a minimal, event-driven C core

[![CI](https://github.com/rezwanahmedsami/catzilla/actions/workflows/ci.yml/badge.svg)](https://github.com/rezwanahmedsami/catzilla/actions)
[![PyPI version](https://img.shields.io/pypi/v/catzilla.svg)](https://pypi.org/project/catzilla/)
[![Python versions](https://img.shields.io/pypi/pyversions/catzilla.svg)](https://pypi.org/project/catzilla/)

> [!NOTE]
>
> 🚀 **Catzilla v0.1.0 is feature-complete with advanced routing capabilities!** The core routing system is production-ready with comprehensive test coverage (90 tests passing).

---

## Overview
<img align="right" src="https://raw.githubusercontent.com/rezwanahmedsami/catzilla/main/logo.png" width="250px" alt="Catzilla Logo" />

Catzilla is a modern Python web framework purpose-built for extreme performance and developer productivity.
At its heart is a sophisticated C HTTP engine—built using **libuv** and **llhttp**—featuring an advanced **trie-based routing system** that delivers O(log n) route lookup performance.

By exposing its speed-focused C core through a clean, Pythonic decorator API, Catzilla gives developers full control with minimal overhead.
Whether you're building **real-time AI applications**, **low-latency APIs**, or **high-throughput microservices**, Catzilla is engineered to deliver maximum efficiency with minimal boilerplate.

<br>


## ✨ Features

### Core Performance
- ⚡ **Hybrid C/Python Core** — Event-driven I/O in C, exposed to Python
- 🔥 **Advanced Trie-Based Routing** — O(log n) lookup with dynamic path parameters
- 🧱 **Zero Boilerplate** — Decorator-style routing: `@app.get(...)`
- 🔁 **Concurrency First** — GIL-aware bindings, supports streaming & WebSockets
- 📦 **Zero Dependencies** — Uses only Python standard library (no pydantic, no bloat!)

### Advanced Routing System
- 🛣️ **Dynamic Path Parameters** — `/users/{user_id}`, `/posts/{post_id}/comments/{comment_id}`
- 🚦 **HTTP Status Code Handling** — 404, 405 Method Not Allowed, 415 Unsupported Media Type
- 🔍 **Route Introspection** — Debug routes, detect conflicts, performance monitoring
- 📊 **Production-Grade Memory Management** — Zero memory leaks, efficient allocation

### Developer Experience
- 🧩 **Modular Architecture** — Add plugins, middleware, or extend protocols easily
- 🧪 **Comprehensive Testing** — 90 tests covering C core and Python integration
- 📖 **Developer-Friendly** — Clear documentation and contribution guidelines
- 🔧 **Method Normalization** — Case-insensitive HTTP methods (`get` → `GET`)

---

## 📊 Performance Benchmarks

Catzilla v0.1.0 has been extensively benchmarked against other popular Python web frameworks using `wrk` with 100 concurrent connections over 10 seconds.

### 🚀 Exceptional Performance Results

**Massive Throughput Advantage**: Catzilla delivers **extraordinary performance** compared to all competitors:

| Endpoint | Catzilla | FastAPI | Django | Flask | vs FastAPI |
|----------|----------|---------|---------|-------|------------|
| **Hello World** | **10,313** | 1,734 | 576 | 974 | **+495% faster** |
| **JSON Response** | **10,390** | 1,603 | 628 | 68 | **+548% faster** |
| **Path Parameters** | **8,235** | 1,868 | N/A | 988 | **+341% faster** |
| **Query Parameters** | **8,634** | 946 | 380 | 341 | **+813% faster** |
| **Complex JSON** | **11,962** | 1,703 | 673 | 34 | **+602% faster** |

**Ultra-Low Latency**: Catzilla consistently delivers **significantly lower latency**:
- **Average Latency**: 13.8ms vs FastAPI's 68.3ms (**79% lower**)
- **Complex JSON**: 9.85ms vs FastAPI's 58.51ms (**83% lower**)
- **Best Performance**: Sub-10ms response times on optimal endpoints

### Performance Summary
- **Average RPS**: 9,907 vs FastAPI's 1,571 (**+530% faster**)
- **Peak Performance**: 11,962 RPS on complex JSON endpoints
- **Ultra-Low Latency**: Sub-15ms average response times
- **Framework Leadership**: Fastest Python web framework tested

> 📋 **[View Complete Performance Report](./PERFORMANCE_REPORT_v0.1.0.md)** - Detailed analysis with technical insights

### 📈 Performance Visualizations

*Performance charts and detailed analysis available in the [Complete Performance Report](./PERFORMANCE_REPORT_v0.1.0.md)*

![Requests per Second Comparison](https://raw.githubusercontent.com/rezwanahmedsami/catzilla/main/benchmarks/results/requests_per_second.png)

![Latency Comparison](https://raw.githubusercontent.com/rezwanahmedsami/catzilla/main/benchmarks/results/latency_comparison.png)

### When to Choose Catzilla
- ⚡ **High-throughput requirements** (API gateways, microservices, data pipelines)
- 🎯 **Low-latency critical** applications (real-time APIs, financial trading, gaming backends)
- 🧬 **Resource efficiency** (cloud computing, embedded systems, edge computing)
- 🚀 **C-level performance** with Python developer experience

*Note: Comprehensive benchmark suite with automated testing available in `benchmarks/` directory.*

---

## 🗂️ Project Structure

```bash
catzilla/
├── CMakeLists.txt                # CMake build config
├── setup.py                      # Python package build entry (uses CMake)
├── CONTRIBUTING.md               # Comprehensive development guide
├── .gitmodules                   # Git submodules: libuv, llhttp
├── deps/                         # External C dependencies
│   ├── libuv/                    # Event loop lib
│   └── unity/                    # C testing framework
├── src/                          # C core source
│   ├── core/                     # Event loop, server & advanced router
│   │   ├── server.c/h           # Main HTTP server implementation
│   │   └── router.c/h           # Trie-based routing engine
│   └── python/                   # CPython bindings
│       └── module.c             # Python C extension
├── python/                       # Python package (catzilla/)
│   └── catzilla/
│       ├── __init__.py          # Public API
│       └── routing.py           # High-level Router class
├── tests/                        # Comprehensive test suite (90 tests)
│   ├── c/                       # C unit tests (28 tests)
│   │   ├── test_router.c        # Basic router tests
│   │   ├── test_advanced_router.c # Advanced routing features
│   │   └── test_server_integration.c # Server integration
│   └── python/                  # Python tests (62 tests)
│       ├── test_advanced_routing.py # Python routing tests
│       ├── test_http_responses.py   # HTTP response handling
│       ├── test_basic.py           # Basic functionality
│       └── test_request.py         # Request handling
├── examples/                     # Example applications
├── scripts/                      # Development scripts
│   ├── build.sh                 # Complete build script
│   ├── run_tests.sh             # Unified test runner
│   └── run_example.sh           # Example runner
├── docs/                         # Sphinx-based docs
└── .github/                      # CI/CD workflows
````

---

## 🚀 Getting Started

### Quick Start

1. **Clone the repository**:
   ```bash
   git clone https://github.com/rezwanahmedsami/catzilla.git
   cd catzilla
   git submodule update --init --recursive
   ```

2. **Build and install**:
   ```bash
   ./scripts/build.sh
   ```

3. **Run an example**:
   ```bash
   ./scripts/run_example.sh examples/hello_world/main.py
   ```

### Advanced Routing Examples

```python
from catzilla import Router

app = Router()

# Static routes
@app.get("/")
def home():
    return "Welcome to Catzilla!"

# Dynamic path parameters
@app.get("/users/{user_id}")
def get_user(request, user_id):
    return f"User ID: {user_id}"

# Multiple parameters
@app.get("/users/{user_id}/posts/{post_id}")
def get_user_post(request, user_id, post_id):
    return f"User {user_id}, Post {post_id}"

# Multiple HTTP methods on same path
@app.get("/api/data")
def get_data():
    return {"method": "GET"}

@app.post("/api/data")
def create_data():
    return {"method": "POST"}

# HTTP status codes are handled automatically:
# - 404 Not Found for missing routes
# - 405 Method Not Allowed for wrong methods (includes Allow header)
# - 415 Unsupported Media Type for parsing errors
```

## 🔧 Development

For detailed development instructions, see [CONTRIBUTING.md](CONTRIBUTING.md).

### Build System

```bash
# Complete build (recommended)
./scripts/build.sh

# Manual CMake build
cmake -S . -B build -DCMAKE_BUILD_TYPE=Debug
cmake --build build -j$(nproc)
pip install -e .
```

### Testing

The test suite includes 90 comprehensive tests covering both C and Python components:

```bash
# Run all tests (90 tests: 28 C + 62 Python)
./scripts/run_tests.sh

# Run specific test suites
./scripts/run_tests.sh --python  # Python tests only (62 tests)
./scripts/run_tests.sh --c       # C tests only (28 tests)
./scripts/run_tests.sh --verbose # Detailed output

# Test results overview:
# ✅ C Tests: 28/28 PASSING
#   - Basic router: 3 tests
#   - Advanced router: 14 tests
#   - Server integration: 11 tests
# ✅ Python Tests: 62/62 PASSING
#   - Advanced routing: 22 tests
#   - HTTP responses: 17 tests
#   - Basic functionality: 10 tests
#   - Request handling: 13 tests
```

### Performance Features

- **Trie-Based Routing**: O(log n) average case lookup performance
- **Memory Efficient**: Zero memory leaks, optimized allocation patterns
- **Route Conflict Detection**: Warns about potentially overlapping routes during development
- **Method Normalization**: Case-insensitive HTTP methods with automatic uppercase conversion
- **Parameter Injection**: Automatic extraction and injection of path parameters to handlers

## 🎯 Performance Characteristics

- **Route Lookup**: O(log n) average case with advanced trie data structure
- **Memory Management**: Zero memory leaks with efficient recursive cleanup
- **Scalability**: Tested with 100+ routes without performance degradation
- **Concurrency**: Thread-safe design ready for production workloads
- **HTTP Processing**: Built on libuv and llhttp for maximum throughput

## 🤝 Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines on:

- Setting up the development environment
- Building and testing the project
- Code style and conventions
- Submitting pull requests
- Debugging and performance optimization

## 📚 Documentation

- **[Getting Started Guide](docs/getting-started.md)** - Quick start tutorial
- **[API Reference](docs/api-reference.md)** - Complete API documentation
- **[Routing Guide](docs/routing.md)** - Advanced routing features
- **[Examples](examples/)** - Real-world example applications
- **[Contributing](CONTRIBUTING.md)** - Development guide for contributors

---

## 👤 Author

**Rezwan Ahmed Sami**
📧 [samiahmed0f0@gmail.com](mailto:samiahmed0f0@gmail.com)
📘 [Facebook](https://www.facebook.com/rezwanahmedsami)

---

## 🪪 License

MIT License — See [`LICENSE`](LICENSE) for full details.
