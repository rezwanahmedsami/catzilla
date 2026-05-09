# Catzilla
Blazing-fast Python web framework with production-grade routing backed by a minimal, event-driven C core

[![CI](https://github.com/rezwanahmedsami/catzilla/actions/workflows/ci.yml/badge.svg)](https://github.com/rezwanahmedsami/catzilla/actions)
[![PyPI version](https://img.shields.io/pypi/v/catzilla.svg)](https://pypi.org/project/catzilla/)
[![Python versions](https://img.shields.io/pypi/pyversions/catzilla.svg)](https://pypi.org/project/catzilla/)
[![Documentation](https://img.shields.io/badge/docs-catzilla.rezwanahmedsami.com-blue)](https://catzilla.rezwanahmedsami.com/)

---

## Overview
<img align="right" src="https://raw.githubusercontent.com/rezwanahmedsami/catzilla/main/logo.png" width="250px" alt="Catzilla Logo" />

Catzilla is a high-performance Python web framework built for teams that want Python ergonomics without paying the usual runtime tax.
Its HTTP engine lives in C, uses **libuv** and **llhttp**, and exposes a clean decorator-based API that feels familiar to Python developers while keeping request handling tight and predictable.

It is designed for **low-latency APIs**, **high-throughput services**, **streaming workloads**, and systems where memory usage matters just as much as raw throughput.

### Why Catzilla

- **Fast where it matters**: C-backed request parsing, routing, and response dispatch
- **Pythonic to use**: `@app.get(...)`, typed parameters, validation, and clean handler code
- **Built for production**: middleware, background tasks, uploads, streaming, caching, and DI
- **Memory-aware by default**: jemalloc-backed allocation strategy where available
- **Portable**: supports Linux, macOS, and Windows with source and wheel-based workflows

<br>

## 🏆 Performance Snapshot

In the benchmark suite included in this repository, Catzilla currently leads FastAPI, Flask, and Django in direct localhost HTTP benchmarks for both single-worker and 10-worker runs.
These numbers should be read as **framework-overhead and runtime-efficiency comparisons**, not as universal production guarantees.
The current published artifact set covers the **basic direct HTTP suite**: hello world, JSON response, complex JSON, path parameters, and query parameters.

### Single / 1 Worker

- **Average throughput**: **50,610 req/s**
- **Best endpoint**: **`basic_hello_world` at 72,249 req/s**
- **Average latency**: **2.22ms**
- **Average peak memory**: **28.26MB**
- **Lead over FastAPI**: **5.9x average throughput**

![Catzilla single-worker benchmark summary](https://raw.githubusercontent.com/rezwanahmedsami/catzilla/v0.2.2/benchmarks/results/overall_single_1w_performance_summary.png)

### Multi / 10 Workers

- **Average throughput**: **180,023 req/s**
- **Best endpoint**: **`basic_hello_world` at 212,426 req/s**
- **Average latency**: **6.03ms**
- **Average peak memory**: **303.53MB**
- **Lead over FastAPI**: **4.2x average throughput**

![Catzilla 10-worker benchmark summary](https://raw.githubusercontent.com/rezwanahmedsami/catzilla/v0.2.2/benchmarks/results/overall_multi_10w_performance_summary.png)

Current benchmark docs and artifacts:

- **Versioned report:** [PERFORMANCE_REPORT_v0.2.2.md](PERFORMANCE_REPORT_v0.2.2.md)
- **Transparent generated report:** [benchmarks/results/transparent_performance_report.md](benchmarks/results/transparent_performance_report.md)
- **Methodology and reproduction guide:** [benchmarks/README.md](benchmarks/README.md)


## ✨ Features

### Core Runtime

- ⚡ **Hybrid C/Python architecture** for low-overhead request handling
- 🔥 **Trie-based routing** with dynamic path parameters and fast lookup
- 🧱 **Minimal API surface** with familiar decorator-style routing
- 🔁 **Sync and async handlers** with native deferred async response support
- 📦 **Lean dependency model** focused on the standard library and native code

### Web Framework Features

- 🛣️ **Dynamic path and query parameters** with typed extraction
- ✅ **Validation layer** for request models and parameter constraints
- 🧩 **Dependency injection** and middleware composition
- 📤 **Streaming responses**, file uploads, background tasks, and static file serving
- 🚦 **HTTP error handling** for 404, 405, 415, and framework-level exceptions

### Developer Experience

- 📖 **Readable Python handlers** on top of a high-performance core
- 🧪 **Comprehensive unit and end-to-end validation** across Python and C layers
- 🔧 **Cross-platform build and packaging support**
- 🧰 **Benchmark suite included** so performance claims are reproducible

## 🚀 Memory Architecture

Catzilla ships with a memory strategy tuned for long-running services, including jemalloc integration where available.
The goal is simple: keep throughput high while reducing fragmentation and avoiding the typical memory blow-up that shows up under sustained load.

### Memory Features
```python
app = Catzilla()

# Real-time memory statistics
stats = app.get_memory_stats()
print(f"Memory efficiency: {stats['fragmentation_percent']:.1f}%")
print(f"Allocated: {stats['allocated_mb']:.2f} MB")
```

### Allocator Strategy
- **Request Arena**: Optimized for short-lived request processing
- **Response Arena**: Efficient response building and serialization
- **Cache Arena**: Long-lived data with minimal fragmentation
- **Static Arena**: Static file serving with memory pooling
- **Task Arena**: Background operations with isolated allocation

---

## 📦 Installation

### Quick Start (Recommended)

Install Catzilla from PyPI:

```bash
pip install catzilla
```

**System Requirements:**
- Python 3.9+ (3.10+ recommended)
- Windows, macOS, or Linux
- No additional dependencies required

**Platform-Specific Features:**
- **Linux/macOS**: jemalloc memory allocator (high performance)
- **Windows**: Standard malloc (reliable performance)
- See [Platform Support Guide](docs/platform_support.md) for details

### Installation Verification

```bash
python -c "import catzilla; print(f'Catzilla v{catzilla.__version__} installed successfully!')"
```

### Alternative Installation Methods

#### From GitHub Releases
For specific versions or if PyPI is unavailable:

```bash
# Download specific wheel for your platform from:
# https://github.com/rezwanahmedsami/catzilla/releases/latest
pip install <downloaded-wheel-file>
```

#### From Source (Development)
For development or contributing:

```bash
# Clone with submodules
git clone --recursive https://github.com/rezwanahmedsami/catzilla.git
cd catzilla

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in development mode
pip install -e .
```

**Build Requirements (Source Only):**
- **Python 3.9-3.13**
- **CMake 3.15+**
- **C Compiler**: GCC/Clang (Linux/macOS) or MSVC (Windows)

---

## 🚀 Quick Start

Create a small application with sync routes, async routes, and typed parameters:

```python
# app.py
from typing import Optional
import asyncio

from catzilla import BaseModel, Catzilla, JSONResponse, Path, Query, Request, Response

app = Catzilla(
    production=False,
    show_banner=True,
    log_requests=True,
)

class UserCreate(BaseModel):
    id: Optional[int] = None
    name: str
    email: Optional[str] = None

@app.get("/")
def home(request: Request) -> Response:
    return JSONResponse({
        "framework": "catzilla",
        "message": "Hello from Catzilla",
        "mode": "sync",
    })

@app.get("/health")
async def health(request: Request) -> Response:
    await asyncio.sleep(0)
    return JSONResponse({
        "status": "ok",
        "mode": "async",
    })

@app.get("/users/{user_id}")
def get_user(request: Request, user_id: int = Path(..., ge=1)) -> Response:
    return JSONResponse({
        "user_id": user_id,
        "message": f"Retrieved user {user_id}",
    })

@app.get("/search")
def search(
    request: Request,
    q: str = Query(""),
    limit: int = Query(10, ge=1, le=100),
) -> Response:
    return JSONResponse({
        "query": q,
        "limit": limit,
        "results": [{"id": index, "title": f"Result {index}"} for index in range(limit)],
    })

@app.post("/users")
def create_user(request: Request, user: UserCreate) -> Response:
    return JSONResponse({
        "message": "User created successfully",
        "user": {"id": user.id, "name": user.name, "email": user.email},
    }, status_code=201)

if __name__ == "__main__":
    app.listen(port=8000, host="127.0.0.1")
```

Run your app:

```bash
python app.py
```

Then visit `http://127.0.0.1:8000`.

### Backward Compatibility

Existing code works unchanged (App is an alias for Catzilla):

```python
from catzilla import App  # Still works!
app = App()  # Same memory benefits
```

---

## 🖥️ System Compatibility

Catzilla provides comprehensive cross-platform support with pre-built wheels for all major operating systems and Python versions.

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
| **3.9** | ✅ | ✅ | ✅ | ✅ |
| **3.10** | ✅ | ✅ | ✅ | ✅ |
| **3.11** | ✅ | ✅ | ✅ | ✅ |
| **3.12** | ✅ | ✅ | ✅ | ✅ |
| **3.13** | ✅ | ✅ | ✅ | ✅ |

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
pip install https://github.com/rezwanahmedsami/catzilla/releases/download/vx.x.x/catzilla-x.x.x.tar.gz
```

### ⚡ Performance Notes

- **Native performance** on all supported platforms
- **Architecture-specific optimizations** in pre-built wheels
- **Cross-platform C core** ensures consistent behavior
- **Platform-specific wheel tags** for optimal compatibility

For detailed compatibility information, see [SYSTEM_COMPATIBILITY.md](SYSTEM_COMPATIBILITY.md).

---

## 📊 Performance Benchmarks

Catzilla includes a benchmark harness that compares it against FastAPI, Flask, and Django across direct HTTP paths and feature-specific slices.
The current published benchmark artifacts in this repository cover the **basic direct HTTP suite** in two modes: **Single / 1 worker** and **Multi / 10 workers**.

### 🏗️ Real Server Environment
**Direct localhost server benchmarking** | **wrk** | **macOS arm64** | **10s duration**

This is real benchmark data collected from the repository benchmark runner. It is useful for comparing framework overhead and implementation efficiency on the same machine and workload shape.

### Current Benchmark Highlights

#### Framework Averages

| Mode | Catzilla | FastAPI | Flask | Django |
|------|----------|---------|-------|--------|
| **Single / 1 worker avg RPS** | **50,610** | 8,537 | 3,004 | 2,780 |
| **Single / 1 worker avg latency** | **2.22ms** | 12.74ms | 48.91ms | 54.80ms |
| **Single / 1 worker avg peak memory** | **28.26MB** | 31.50MB | 46.45MB | 52.92MB |
| **Multi / 10 workers avg RPS** | **180,023** | 42,890 | 5,488 | 5,549 |
| **Multi / 10 workers avg latency** | **6.03ms** | 25.26ms | 177.89ms | 175.11ms |
| **Multi / 10 workers avg peak memory** | **303.53MB** | 350.71MB | 288.68MB | 349.75MB |

### Endpoint Highlights

- **Best current result:** `basic_hello_world` at **72,249 req/s** single-worker and **212,426 req/s** at 10 workers.
- **Lowest current Catzilla result in the published basic suite:** `basic_query_params` at **31,707 req/s** single-worker and **137,966 req/s** at 10 workers.
- **Catzilla leads every published endpoint in both worker modes** in the current direct HTTP dataset.

### Benchmark Links

- [PERFORMANCE_REPORT_v0.2.2.md](PERFORMANCE_REPORT_v0.2.2.md): release-facing benchmark report for the current stable version
- [benchmarks/results/basic_performance_report.md](benchmarks/results/basic_performance_report.md): generated detailed table for the latest basic run
- [benchmarks/results/transparent_performance_report.md](benchmarks/results/transparent_performance_report.md): generated artifact summary with embedded charts
- [benchmarks/README.md](benchmarks/README.md): methodology, commands, and interpretation notes

### 📈 Performance Visualizations

![Overall performance comparison - single worker](https://raw.githubusercontent.com/rezwanahmedsami/catzilla/v0.2.2/benchmarks/results/overall_single_1w_performance_summary.png)

![Overall performance comparison - 10 workers](https://raw.githubusercontent.com/rezwanahmedsami/catzilla/v0.2.2/benchmarks/results/overall_multi_10w_performance_summary.png)

![Requests per second heatmap - single worker](https://raw.githubusercontent.com/rezwanahmedsami/catzilla/v0.2.2/benchmarks/results/overall_single_1w_performance_heatmap.png)

![Requests per second heatmap - 10 workers](https://raw.githubusercontent.com/rezwanahmedsami/catzilla/v0.2.2/benchmarks/results/overall_multi_10w_performance_heatmap.png)

*📋 **[View Complete Performance Report](./PERFORMANCE_REPORT_v0.2.2.md)** - Detailed analysis with current charts and endpoint-by-endpoint data*

### When to Choose Catzilla
- ⚡ **High-throughput requirements** (API gateways, microservices, data pipelines)
- 🎯 **Low-latency critical** applications (real-time APIs, financial trading, gaming backends)
- 🧬 **Resource efficiency** (cloud computing, embedded systems, edge computing)
- 🚀 **C-level performance** with Python developer experience

*Note: Comprehensive benchmark suite with automated testing available in `benchmarks/` directory.*

---

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

The project includes C tests, Python unit tests, and end-to-end validation:

```bash
# Run all tests ( C + Python Unit + e2e)
./scripts/run_tests.sh

# Run specific test suites
./scripts/run_tests.sh --python  # Python Unit tests only
./scripts/run_tests.sh --c       # C tests only
./scripts/run_tests.sh --e2e       # e2e tests only
./scripts/run_tests.sh --verbose # Detailed output
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

📖 **[Complete Documentation](https://catzilla.rezwanahmedsami.com/)** - Comprehensive guides, API reference, and tutorials

### Quick References
- **[Getting Started Guide](docs/getting-started/quickstart.rst)** - Quick start tutorial
- **[System Compatibility](SYSTEM_COMPATIBILITY.md)** - Platform support and installation guide
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
