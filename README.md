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

## 📦 Installation

### From GitHub Releases (Recommended for v0.1.0)

Catzilla v0.1.0 is distributed through GitHub Releases with pre-built wheels for multiple platforms and Python versions.

#### Quick Installation

Download and install the appropriate wheel for your platform:

```bash
# For Python 3.10 on Linux (most common)
curl -L -O https://github.com/rezwanahmedsami/catzilla/releases/download/v0.1.0/catzilla-0.1.0-cp310-cp310-linux_x86_64.whl
pip install catzilla-0.1.0-cp310-cp310-linux_x86_64.whl

# For Python 3.10 on macOS
curl -L -O https://github.com/rezwanahmedsami/catzilla/releases/download/v0.1.0/catzilla-0.1.0-cp310-cp310-macosx_10_15_universal2.whl
pip install catzilla-0.1.0-cp310-cp310-macosx_10_15_universal2.whl

# For Python 3.10 on Windows
curl -L -O https://github.com/rezwanahmedsami/catzilla/releases/download/v0.1.0/catzilla-0.1.0-cp310-cp310-win_amd64.whl
pip install catzilla-0.1.0-cp310-cp310-win_amd64.whl
```

#### Platform-Specific Wheels

Visit the [Releases page](https://github.com/rezwanahmedsami/catzilla/releases/tag/v0.1.0) to download wheels for:

- **Python Versions**: 3.8, 3.9, 3.10, 3.11, 3.12
- **Platforms**:
  - **Linux**: `linux_x86_64`
  - **macOS**: `macosx_10_15_universal2`
  - **Windows**: `win_amd64`

#### Installation Verification

```bash
python -c "import catzilla; print(f'Catzilla v{catzilla.__version__} installed successfully!')"
```

### From Source (Development)

For development or if pre-built wheels aren't available for your platform:

```bash
# Clone with submodules
git clone --recursive https://github.com/rezwanahmedsami/catzilla.git
cd catzilla

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install build dependencies
pip install -e ".[dev]"

# Build and install
python -m build
pip install dist/*.whl
```

#### Build Requirements

- **Python 3.8+**
- **CMake 3.15+**
- **C Compiler**: GCC/Clang (Linux/macOS) or MSVC (Windows)

### Future PyPI Distribution

Starting with v1.0.0, Catzilla will be available on PyPI for standard installation:

```bash
# Coming in v1.0.0
pip install catzilla
```

---

## 🖥️ System Compatibility

Catzilla v0.1.0 provides comprehensive cross-platform support with pre-built wheels for all major operating systems and Python versions.

### 📋 Supported Platforms

| Platform | Architecture | Status | Wheel Available |
|----------|-------------|---------|-----------------|
| **Linux** | x86_64 | ✅ Full Support | ✅ manylinux2014 |
| **macOS** | x86_64 (Intel) | ✅ Full Support | ✅ macOS 10.15+ |
| **macOS** | ARM64 (Apple Silicon) | ✅ Full Support | ✅ macOS 11.0+ |
| **Windows** | x86_64 | ✅ Full Support | ✅ Windows 10+ |
| **Linux** | ARM64 | ⚠️ Source Only* | ❌ No pre-built wheel |

*\*ARM64 Linux requires building from source with proper build tools installed.*

### 🐍 Python Version Support

| Python Version | Linux x86_64 | macOS Intel | macOS ARM64 | Windows |
|----------------|--------------|-------------|-------------|---------|
| **3.8** | ✅ | ✅ | ✅ | ✅ |
| **3.9** | ✅ | ✅ | ✅ | ✅ |
| **3.10** | ✅ | ✅ | ✅ | ✅ |
| **3.11** | ✅ | ✅ | ✅ | ✅ |
| **3.12** | ✅ | ✅ | ✅ | ✅ |

### 🔧 Installation Methods by Platform

#### ✅ Pre-built Wheels (Recommended)
- **Instant installation** with zero compilation time
- **No build dependencies** required (CMake, compilers, etc.)
- **Optimized binaries** for maximum performance
- Available for: Linux x86_64, macOS (Intel/ARM64), Windows x86_64

```bash
# Automatic platform detection
pip install <wheel-url-from-releases>
```

#### 🛠️ Source Installation
- **Build from source** when pre-built wheels aren't available
- **Requires build tools**: CMake 3.15+, C compiler, Python headers
- **Longer installation time** due to compilation

```bash
# For ARM64 Linux or custom builds
pip install https://github.com/rezwanahmedsami/catzilla/releases/download/v0.1.0/catzilla-0.1.0.tar.gz
```

### ⚡ Performance Notes

- **Native performance** on all supported platforms
- **Architecture-specific optimizations** in pre-built wheels
- **Cross-platform C core** ensures consistent behavior
- **Platform-specific wheel tags** for optimal compatibility

For detailed compatibility information, see [SYSTEM_COMPATIBILITY.md](SYSTEM_COMPATIBILITY.md).

---

## 📊 Performance Benchmarks

Catzilla v0.1.0 has been extensively benchmarked against other popular Python web frameworks using `wrk` with 100 concurrent connections over 10 seconds on a **real production server**.

### 🏗️ Real Server Environment
**Intel Xeon E3-1245 v5 @ 3.5GHz** | **31GB RAM** | **AlmaLinux 8.10** | **Python 3.8.12**

This is authentic benchmark data collected from a real server environment, not synthetic or optimized conditions.

### 🚀 Exceptional Performance Results

**Massive Throughput Advantage**: Catzilla delivers **extraordinary performance** compared to all competitors:

| Endpoint | Catzilla | FastAPI | Django | Flask | vs FastAPI |
|----------|----------|---------|---------|-------|------------|
| **Hello World** | **24,759** | 2,844 | 2,339 | 2,875 | **+771% faster** |
| **JSON Response** | **15,754** | 2,421 | 2,208 | 2,672 | **+551% faster** |
| **Path Parameters** | **17,590** | 2,341 | 2,219 | 2,624 | **+651% faster** |
| **Query Parameters** | **11,145** | 1,419 | 1,975 | 2,431 | **+685% faster** |
| **Complex JSON** | **14,843** | 2,008 | 2,162 | 2,521 | **+639% faster** |

**Ultra-Low Latency**: Catzilla consistently delivers **significantly lower latency**:
- **Average Latency**: 5.97ms vs FastAPI's 47.69ms (**87% lower**)
- **Hello World**: 4.07ms vs FastAPI's 35.04ms (**88% lower**)
- **Complex JSON**: 6.79ms vs FastAPI's 49.63ms (**86% lower**)

### Performance Summary
- **Average RPS**: 16,818 vs FastAPI's 2,207 (**+662% faster**)
- **Peak Performance**: 24,759 RPS on hello world endpoint
- **Ultra-Low Latency**: Sub-7ms average response times
- **Framework Leadership**: Fastest Python web framework tested by massive margins

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
- **[System Compatibility](SYSTEM_COMPATIBILITY.md)** - Platform support and installation guide
- **[Examples](examples/)** - Real-world example applications
- **[Contributing](CONTRIBUTING.md)** - Development guide for contributors

---

## 🤖 Built with AI

<div align="center">

| **Claude Sonnet 4** | **GitHub Copilot** | **Visual Studio Code** |
|:---:|:---:|:---:|
| <img src="https://claude.ai/images/claude_app_icon.png" width="80" alt="Claude Logo"><br>**Architecture & Design** | <img src="https://raw.githubusercontent.com/rezwanahmedsami/catzilla/main/assets/githubcopilot.svg" width="80" alt="GitHub Copilot Logo"><br>**Code Intelligence** | <img src="https://code.visualstudio.com/assets/images/code-stable.png" width="80" alt="VS Code Logo"><br>**Development Environment** |

</div>

This project was developed using cutting-edge AI-assisted development tools:

- **[Claude Sonnet 4](https://anthropic.com/)** - Advanced technical architecture, debugging, and problem-solving
- **[GitHub Copilot](https://github.com/features/copilot)** - Intelligent code completion and development acceleration
- **[Visual Studio Code](https://code.visualstudio.com/)** - Primary development environment with AI integration

*AI partnership enabled rapid development from an estimated 3-6 months to just 1 week, while maintaining production-grade code quality, comprehensive testing (90 tests), and cross-platform compatibility.*

### Development Workflow
- **Architecture & Design**: Claude Sonnet 4 for system design, C/Python integration strategies, and technical decision-making
- **Code Implementation**: GitHub Copilot for intelligent code suggestions, boilerplate generation, and pattern completion
- **Quality Assurance**: AI-assisted bug detection, performance optimization, and cross-platform compatibility testing
- **Documentation**: AI-powered technical writing for comprehensive documentation and guides

*This represents the future of software development—human creativity enhanced by AI precision.* 🚀

---

## 👤 Author

**Rezwan Ahmed Sami**
📧 [samiahmed0f0@gmail.com](mailto:samiahmed0f0@gmail.com)
📘 [Facebook](https://www.facebook.com/rezwanahmedsami)

---

## 🪪 License

MIT License — See [`LICENSE`](LICENSE) for full details.
