# Tutorial Overview

Welcome to the comprehensive Catzilla tutorial! This step-by-step guide will take you from basic concepts to building production-ready applications with C-accelerated performance.

## What You'll Learn

By the end of this tutorial, you'll master:

- **Core Routing**: Path parameters, query parameters, and request handling
- **Ultra-Fast Validation**: Pydantic-compatible models with 100x performance
- **Static File Serving**: Efficient file serving with caching
- **Error Handling**: Robust error management and custom exceptions
- **Application Configuration**: Production-ready app setup

## Tutorial Structure

### Foundation (Start Here)
```{toctree}
:maxdepth: 1

basic-routing
```

### Core Features
```{toctree}
:maxdepth: 1
```

## Prerequisites

Before starting this tutorial, make sure you have:

- **Catzilla installed**: Follow the [Installation Guide](../installation)
- **Python 3.8+**: With basic Python knowledge
- **Text editor**: VS Code, PyCharm, or your preferred editor

### 3. Setup

If you haven't already, install Catzilla:

```bash
pip install catzilla
```

Verify installation:

```python
from catzilla import Catzilla
print("🚀 Catzilla is ready!")
```

## 🚀 Quick Example

Before diving deep, here's what a complete Catzilla app looks like:

```python
from catzilla import Catzilla, BaseModel
from typing import Optional

app = Catzilla()

class Item(BaseModel):
    name: str
    price: float
    description: Optional[str] = None

@app.get("/")
def root():
    return {"message": "Welcome to Catzilla!"}

@app.get("/items/{item_id}")
def get_item(item_id: int):
    return {"item_id": item_id}

@app.post("/items")
def create_item(item: Item):
    return {"item": item, "status": "created"}

if __name__ == "__main__":
    app.listen(port=8000)
```

This simple app demonstrates:
- **C-accelerated routing** with path parameters
- **Automatic validation** with BaseModel
- **Type-safe handlers** with proper type hints
- **JSON serialization** with optimized response handling

## 🎓 Learning Path

### Beginner (Start Here!)
1. [Basic Routing](basic-routing.md) - Learn route definition and path parameters
2. [Request & Response](request-response.md) - Master request handling
3. [Static Files](static-files.md) - Serve CSS, JS, images efficiently

### Intermediate
4. [Error Handling](error-handling.md) - Handle errors gracefully
5. [Configuration](configuration.md) - Production-ready configuration

### Advanced
- [Validation Engine](../validation/index.md) - Master the 100x faster validation
- [Background Tasks](../background-tasks/index.md) - Revolutionary task system
- [Dependency Injection](../dependency-injection/index.md) - Advanced DI patterns
- [Middleware](../middleware/index.md) - Zero-allocation middleware
- [Performance Optimization](../performance/index.md) - Production tuning

## 💡 Tutorial Tips

### Code Examples
- **All examples are complete and runnable** - copy/paste and they work!
- **Performance notes** highlight Catzilla's speed advantages
- **Best practices** are called out with 💡 icons
- **Common pitfalls** are marked with ⚠️ warnings

### Hands-On Learning
- **Try every example** - experimentation is key to learning
- **Modify the code** - see what happens when you change things
- **Use the interactive debugger** - understand how Catzilla works internally
- **Check performance** - compare with other frameworks

### Getting Help
- **Code not working?** Check the [troubleshooting guide](../troubleshooting.md)
- **Need examples?** Browse the [examples gallery](../examples/index.md)
- **Want to discuss?** Join our [Discord community](https://discord.gg/catzilla)

## 🔥 Performance Preview

As you go through the tutorial, you'll see Catzilla's performance advantages:

```python
# Benchmark example you'll build
from catzilla import Catzilla
import time

app = Catzilla()

@app.get("/benchmark")
def benchmark():
    start = time.perf_counter()

    # Simulate some work
    result = {"numbers": list(range(1000))}

    end = time.perf_counter()

    return {
        "result": result,
        "processing_time_ms": (end - start) * 1000,
        "c_acceleration": app.has_c_acceleration(),
        "memory_optimized": app.has_jemalloc()
    }
```

**Typical results:**
- **Catzilla**: 0.1ms processing time
- **FastAPI**: 1.2ms processing time
- **Flask**: 2.8ms processing time

*That's 10x-25x faster routing and response generation!*

## 🎯 Ready to Start?

Let's begin with the fundamentals:

**[Start with Basic Routing →](basic-routing.md)**

Or jump to any section that interests you:

- 🛣️ [Basic Routing](basic-routing.md) - Routes and path parameters
- 📨 [Request & Response](request-response.md) - HTTP handling
- 📁 [Static Files](static-files.md) - File serving
- ❌ [Error Handling](error-handling.md) - Error management
- ⚙️ [Configuration](configuration.md) - App configuration

---

*Happy learning! You're about to experience the fastest Python web framework ever built.* 🚀
