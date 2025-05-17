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

1. **Clone the repo**:

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
   catzilla run examples/hello_world/main.py:app --reload
   ```

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