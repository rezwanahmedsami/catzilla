# Installation Guide

This guide covers different ways to install Catzilla and get your development environment set up.

## Requirements

### Minimum Requirements
- **Python**: 3.8 or higher
- **pip**: Latest version recommended
- **Operating System**: Linux, macOS, or Windows

### Recommended Requirements
- **Python**: 3.11+ (for optimal performance)
- **Memory**: 4GB RAM minimum, 8GB+ recommended
- **CPU**: x64 architecture for C-acceleration support

## Quick Installation

### Using pip (Recommended)

```bash
pip install catzilla
```

### Using pip with extras

```bash
# Install with all optional dependencies
pip install catzilla[all]

# Install with development dependencies
pip install catzilla[dev]

# Install with performance monitoring
pip install catzilla[monitoring]
```

## Verify Installation

Create a simple test file:

```python
# test_install.py
from catzilla import Catzilla

app = Catzilla()

@app.get("/")
def hello():
    return {"message": "Catzilla is working!"}

if __name__ == "__main__":
    print("🚀 Starting Catzilla...")
    app.listen(port=8000)
```

Run the test:

```bash
python test_install.py
```

Visit `http://localhost:8000` - you should see:
```json
{"message": "Catzilla is working!"}
```

## Advanced Installation

### From Source (Development)

```bash
# Clone the repository
git clone https://github.com/rezwanahmedsami/catzilla.git
cd catzilla

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install development dependencies
pip install -r requirements-dev.txt

# Build C extensions
python setup.py build_ext --inplace

# Install in development mode
pip install -e .
```

### Docker Installation

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install Catzilla
RUN pip install catzilla

# Copy your application
COPY . .

EXPOSE 8000

CMD ["python", "main.py"]
```

## Performance Optimization Setup

### jemalloc Configuration (Recommended)

For maximum performance, configure jemalloc:

```bash
# Ubuntu/Debian
sudo apt-get install libjemalloc2

# macOS
brew install jemalloc

# Run your app with jemalloc
LD_PRELOAD=/usr/lib/x86_64-linux-gnu/libjemalloc.so.2 python main.py
```

### Environment Variables

```bash
# Enable all performance optimizations
export CATZILLA_ENABLE_JEMALLOC=1
export CATZILLA_ENABLE_C_ACCELERATION=1
export CATZILLA_MEMORY_POOL_SIZE=512MB

# Production settings
export CATZILLA_LOG_LEVEL=WARNING
export CATZILLA_WORKER_PROCESSES=4
```

## Installation Troubleshooting

### Common Issues

#### ImportError: No module named '_catzilla'

```bash
# Rebuild C extensions
python setup.py build_ext --inplace
pip install --force-reinstall catzilla
```

#### Performance Issues

```bash
# Verify C acceleration is enabled
python -c "import catzilla; print(catzilla.has_c_acceleration())"
# Should print: True

# Check jemalloc
python -c "import catzilla; print(catzilla.has_jemalloc())"
# Should print: True
```

#### Memory Usage Issues

```bash
# Install with memory debugging
pip install catzilla[debug]

# Run with memory profiling
CATZILLA_MEMORY_DEBUG=1 python main.py
```

### Platform-Specific Notes

#### Linux (Ubuntu/Debian)
```bash
# Required system packages
sudo apt-get update
sudo apt-get install build-essential python3-dev libuv1-dev
pip install catzilla
```

#### macOS
```bash
# Install Xcode command line tools
xcode-select --install

# Install with Homebrew dependencies
brew install libuv
pip install catzilla
```

#### Windows (WSL2 Recommended)
```bash
# In WSL2 Ubuntu
sudo apt-get update
sudo apt-get install build-essential python3-dev
pip install catzilla
```

## Validation

### Test All Features

```python
# comprehensive_test.py
from catzilla import Catzilla, BaseModel, BackgroundTasks
from catzilla.dependency_injection import service, Depends

app = Catzilla(
    enable_background_tasks=True,
    enable_di=True,
    enable_jemalloc=True
)

class TestModel(BaseModel):
    name: str
    count: int

@service("test_service")
class TestService:
    def get_data(self):
        return "Service working!"

@app.get("/")
def root():
    return {"status": "All systems operational"}

@app.post("/validate")
def validate_data(data: TestModel):
    return {"received": data, "validation": "passed"}

@app.get("/di-test")
def di_test(service: TestService = Depends("test_service")):
    return {"service_response": service.get_data()}

@app.get("/background-task")
def background_test():
    result = app.add_task(lambda: "Background task completed!")
    return {"task_id": result.task_id}

if __name__ == "__main__":
    print("🧪 Running comprehensive test...")
    print("✅ C Acceleration:", app.has_c_acceleration())
    print("✅ jemalloc:", app.has_jemalloc())
    print("✅ Background Tasks:", app.background_tasks_enabled())
    print("✅ Dependency Injection:", app.di_enabled())

    app.listen(port=8000)
```

If all features work correctly, you're ready to build with Catzilla! 🚀

## Next Steps

- [Quick Start Tutorial](quick-start.md)
- [First Steps Guide](first-steps.md)
- [Core Tutorial](tutorial/index.md)

---

*Need help? Join our [Discord community](https://discord.gg/catzilla) or check [GitHub Issues](https://github.com/rezwanahmedsami/catzilla/issues)*
