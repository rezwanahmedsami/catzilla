# Catzilla
Blazing-fast Python web framework backed by a minimal, event-driven C core

> [!CAUTION]
>
> ⚠️ **This project is experimental and actively under development – <span style="color: red;">Don't use it until the first version is released.</span>**

---

## Overview
<img align="right" src="https://raw.githubusercontent.com/rezwanahmedsami/catzilla/main/logo.png" width="250px" alt="Catzilla Logo" />

Catzilla is a modern Python web framework purpose-built for extreme performance.
At its heart is a lightweight C HTTP engine—built using **libuv** and **llhttp**—that powers the underlying event loop and request processing pipeline.

By exposing its speed-focused C core through a clean, Pythonic decorator API, Catzilla gives developers full control with minimal overhead.
Whether you're building **real-time AI applications**, **low-latency APIs**, or **high-throughput microservices**, Catzilla is engineered to deliver maximum efficiency with minimal boilerplate.

<br>


## ✨ Features

- ⚡ **Hybrid C/Python Core** — Event-driven I/O in C, exposed to Python
- 🧱 **Zero Boilerplate** — Decorator-style routing: `@app.get(...)`
- 🔁 **Concurrency First** — GIL-aware bindings, supports streaming & WebSockets
- 🧩 **Modular** — Add plugins, middleware, or extend protocols easily

---

## 🗂️ Project Structure

```bash
catzilla/
├── CMakeLists.txt                # CMake build config
├── setup.py                      # Python package build entry (uses CMake)
├── .gitmodules                   # Git submodules: libuv, llhttp
├── deps/                         # External C dependencies
│   ├── libuv/                    # Event loop lib
│   └── llhttp/                   # HTTP parser
├── src/                          # C core source
│   ├── core/                     # Event loop & server logic
│   ├── http/                     # Router & parser integration
│   └── python/                   # CPython bindings
├── python/                       # Python package (catzilla/)
├── tests/                        # C & Python tests
├── examples/                     # Example apps
├── docs/                         # Sphinx-based docs
├── scripts/                      # Helper scripts
└── .github/                      # CI/CD workflows
````

---

## 🚀 Getting Started

### Development Setup

1. **Install pre-commit hooks**:
   ```bash
   pip install pre-commit
   pre-commit install
   ```
   This will automatically:
   - Format code with black
   - Sort imports with isort
   - Check for syntax errors with flake8
   - Fix common issues (trailing whitespace, file endings)

2. **Clone the repo**:

   ```bash
   git clone https://github.com/rezwanahmedsami/catzilla.git
   cd catzilla
   git submodule update --init --recursive
   ```

2. **Build and install locally**:

   ```bash
   pip install .
   ```

3. **Run an example app**:

   ```bash
   # Using the example runner script (recommended)
   ./scripts/run_example.sh examples/hello_world/main.py

   # Or using the CLI tool (after installing)
   catzilla run examples/hello_world/main.py:app --reload
   ```

---

## 🧪 Testing

Catzilla uses a hybrid test suite that includes both C and Python tests. The test runner script provides a unified interface to run all tests.

### Running Tests

Use the test runner script in the `scripts` directory:

```bash
# Run all tests (both C and Python)
./scripts/run_tests.sh

# Run only Python tests
./scripts/run_tests.sh --python

# Run only C tests
./scripts/run_tests.sh --c

# Run tests with verbose output
./scripts/run_tests.sh --verbose

# Show all options
./scripts/run_tests.sh --help
```

### Test Structure

```bash
tests/
├── python/                    # Python test files
│   └── test_basic.py         # Basic functionality tests
└── c/                        # C test files
    └── test_router.c         # Router implementation tests
```

The test suite uses:
- **Python**: pytest for Python component testing
- **C**: Unity test framework for C core testing

### Writing Tests

1. **Python Tests**:
   - Add test files in `tests/python/`
   - Use pytest fixtures and assertions
   - Tests are automatically discovered

2. **C Tests**:
   - Add test files in `tests/c/`
   - Use Unity test framework macros
   - Register tests in CMakeLists.txt

---

### Build cmake:
```bash
# Initialize libuv submodule
git submodule update --init --recursive
# Create build directory and configure
mkdir -p build && cd build
cmake .. -DCMAKE_BUILD_TYPE=Release

# Compile the server
make -j$(sysctl -n hw.logicalcpu)

# Run the server (from build directory)
./catzilla-server
```
2
```bash
rm -rf build dist *.egg-info
find . -name "*.so" -delete
python3 -m pip uninstall catzilla -y
python3 -m pip install --user --verbose .

python examples/hello_world/main.py
```

### to test bin:
```bash
cmake -S . -B build

cmake --build build
```

# for benchmark:
```bash
wrk -t12 -c100 -d10s http://127.0.0.1:8000/
wrk -t12 -c100 -d10s http://127.0.0.1:8080/
```

## 👤 Author

**Rezwan Ahmed Sami**
📧 [samiahmed0f0@gmail.com](mailto:samiahmed0f0@gmail.com)
📘 [Facebook](https://www.facebook.com/rezwanahmedsami)

---

## 🪪 License

MIT License — See [`LICENSE`](LICENSE) for full details.
