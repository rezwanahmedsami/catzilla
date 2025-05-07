# Catzilla

> A high-performance Python web framework with a lean C core  
> **Experimental / Under Development**

<table>
<tr>
<td>

## Overview

Catzilla combines the raw speed of a minimal C HTTP engine (powered by libuv and llhttp) with a clean, decorator-based Python API.  
It’s designed for AI-heavy, high-throughput workloads where low latency and high concurrency matter.

</td>
<td><img src="https://raw.githubusercontent.com/your-username/catzilla/main/catzilla/logo.png" width="400"/></td>
</tr>
</table>


## Features

- **Hybrid C/Python Core**: Event-driven I/O in C, exposed via Python decorators  
- **Zero Boilerplate**: Simple `@app.get(...)` syntax for routes, automatic OpenAPI docs  
- **Scalable**: Worker processes, GIL-aware C bindings, support for WebSockets and streaming  
- **Modular**: Easy to extend with middleware, plugins, and custom protocols

## Project Structure

```bash
catzilla/
├── CMakeLists.txt                # Top-level CMake configuration
├── setup.py                      # Python package setup (builds C code via CMake)
├── .gitmodules                   # Git submodules for libuv and llhttp
├── deps/                         # External dependencies
│   ├── libuv/                    # libuv submodule
│   └── llhttp/                   # llhttp submodule
├── src/                          # C core source code
│   ├── core/                     # Event loop and server core
│   │   ├── server.c
│   │   └── uv_loop.c
│   ├── http/                     # HTTP parsing and routing
│   │   ├── router.c
│   │   └── llhttp_wrapper.c
│   └── python/                   # Python extension (CPython bindings)
│       ├── module.c
│       └── py_router.c
├── python/                       # High-level Python package
│   └── catzilla/
│       ├── __init__.py           # Main package exports
│       ├── app.py                # Decorator API (Catzilla class)
│       ├── types.py              # Pydantic models and type hints
│       └── _native.*             # Built C extension (auto-generated)
├── tests/                        # Unit and integration tests
│   ├── c/                        # C unit tests (using Check)
│   └── python/                   # Python pytest tests
├── examples/                     # Example applications
├── docs/                         # Documentation (Sphinx)
├── scripts/                      # Build and utility scripts
└── .github/                      # CI/CD workflows
````

## Getting Started

1. **Clone the repo**:

   ```bash
   git clone https://github.com/rezwanahmedsami/catzilla.git
   cd catzilla
   git submodule update --init --recursive
   ```

2. **Build & install**:

   ```bash
   pip install .
   ```

3. **Run examples**:

   ```bash
   catzilla run examples/hello_world/main.py:app --reload
   ```

## Author

**Rezwan Ahmed Sami**

* Facebook: [rezwanahmedsami](https://www.facebook.com/rezwanahmedsami)
* Email: [samiahmed0f0@gmail.com](mailto:samiahmed0f0@gmail.com)

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.