# 🌪️ Zero-Allocation Middleware System Examples

This directory contains comprehensive examples demonstrating Catzilla's revolutionary Zero-Allocation Middleware System - executing middleware chains entirely in C with Python flexibility.

> 📖 **Getting Started?** Check out the [**Middleware User Guide**](../../docs/middleware_user_guide.md) for step-by-step tutorials and practical patterns.

## 📁 Example Structure

### Basic Examples
- **[`basic_middleware.py`](basic_middleware.py)** - Simple middleware registration and execution
- **[`builtin_middleware.py`](builtin_middleware.py)** - Using built-in C middleware (CORS, auth, rate limiting)
- **[`custom_c_middleware.py`](custom_c_middleware.py)** - Writing high-performance C middleware

### Advanced Examples
- **[`di_integration.py`](di_integration.py)** - Dependency injection in middleware
- **[`performance_optimization.py`](performance_optimization.py)** - Performance tuning and metrics
- **[`migration_example.py`](migration_example.py)** - Migrating from legacy middleware

### Production Examples
- **[`production_api.py`](production_api.py)** - Complete production API with full middleware stack
- **[`microservice_middleware.py`](microservice_middleware.py)** - Microservice-specific middleware patterns

## 🚀 Quick Start

```python
from catzilla import Catzilla

app = Catzilla()

# Zero-allocation middleware - compiled to C automatically
@app.middleware(priority=100, pre_route=True)
def auth_middleware(request):
    if not request.headers.get('Authorization'):
        return Response(status=401, body="Unauthorized")
    return None  # Continue

# Built-in C middleware for maximum performance
app.enable_builtin_middleware(['cors', 'rate_limit', 'security_headers'])

@app.route('/api/users')
def get_users():
    return {"users": ["alice", "bob"]}

if __name__ == '__main__':
    app.run(port=8000)
```

## 🎯 Performance Benefits

The Zero-Allocation Middleware System provides:

- **10-15x faster** middleware execution vs Python-only chains
- **40-50% memory reduction** through zero-allocation patterns
- **Sub-microsecond latency** for typical middleware chains
- **Zero performance degradation** for non-middleware routes

## 🧪 Benchmarking

Each example includes performance benchmarks comparing:
- Zero-allocation C middleware vs Python middleware
- Built-in C middleware vs custom implementations
- Memory usage and allocation patterns
- Execution time under load

## 📖 Documentation

For complete documentation see:
- **[Middleware Overview](../../docs/middleware_overview.md)** - Choose the right documentation for your needs
- **[Middleware Guide](../../docs/middleware_guide.md)** - **START HERE** for practical tutorials and examples
- **[Zero-Allocation Middleware System](../../docs/middleware.md)** - Advanced technical documentation
- [Zero-Allocation Middleware System Plan](../../plan/zero_allocation_middleware_system_plan.md) - Engineering implementation details
- [Migration Guide](migration_guide.md) - Framework migration patterns
- [Performance Tuning Guide](performance_guide.md) - Optimization techniques

## 🎯 Quick Reference

**New to middleware?** → [Middleware Guide](../../docs/middleware_guide.md)
**Need examples?** → Browse the files in this directory
**Want performance?** → [Zero-Allocation System](../../docs/middleware.md)
**Migrating?** → [Migration Guide](migration_guide.md)
