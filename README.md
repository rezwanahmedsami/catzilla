# Catzilla

> A high-performance Python web framework with a lean C core  
> ⚠️ **Experimental – Under Heavy Development**

![Logo](https://raw.githubusercontent.com/rezwanahmedsami/catzilla/main/logo.png#right)

---

## Overview

Catzilla combines the raw speed of a minimal C HTTP engine (powered by libuv and llhttp)  
with a clean, decorator-based Python API.

It’s designed for **AI-heavy**, **low-latency**, **high-concurrency** workloads.

---

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

## 👤 Author

**Rezwan Ahmed Sami**
📧 [samiahmed0f0@gmail.com](mailto:samiahmed0f0@gmail.com)
📘 [Facebook](https://www.facebook.com/rezwanahmedsami)

---

## 🪪 License

MIT License — See [`LICENSE`](LICENSE) for full details.
