# 🌪️ Catzilla Middleware System Overview

Welcome to Catzilla's powerful middleware system! This overview helps you understand what's available and where to start.

## 📚 Documentation Structure

### 🎯 **Start Here**: [Middleware Guide](middleware_guide.md)
**Perfect for beginners** - A practical, easy-to-follow guide with real examples you can copy and paste.

- ✅ Quick start examples
- ✅ Step-by-step tutorials
- ✅ Common patterns (auth, CORS, logging)
- ✅ Best practices and common mistakes
- ✅ Testing your middleware

### 🏗️ **Advanced**: [Zero-Allocation Middleware System](middleware.md)
**For production optimization** - Complete technical reference for the zero-allocation system.

- ⚡ Performance optimization
- 🔧 Built-in C middleware
- 📊 Memory pool management
- 🎛️ Advanced configuration

### 💡 **Examples**: [examples/middleware/](../examples/middleware/)
**Working code samples** - Complete, runnable examples for different use cases.

- 📁 [`basic_middleware.py`](../examples/middleware/basic_middleware.py) - Simple auth, CORS, logging
- 📁 [`production_api.py`](../examples/middleware/production_api.py) - Production-ready API with full middleware stack
- 📁 [`di_integration.py`](../examples/middleware/di_integration.py) - Dependency injection patterns

## � Quick Decision Guide

**👋 "I'm new to Catzilla middleware"**
→ Start with [Middleware Guide](middleware_guide.md)

**⚡ "I need maximum performance"**
→ Read [Zero-Allocation Middleware System](middleware.md)

**🔍 "I want working examples"**
→ Check [examples/middleware/](../examples/middleware/)

**🔧 "I'm migrating from FastAPI/Flask"**
→ See [Migration from FastAPI](migration_from_fastapi.md#middleware-migration)

**🧪 "I want to test my middleware"**
→ Follow [Testing Guide](middleware_guide.md#testing-middleware)

## 🎯 Core Concepts (Quick Recap)

### What is Middleware?
Code that runs **before** and **after** your route handlers:

```
Request → Middleware 1 → Middleware 2 → Route Handler → Response
```

### Registration
```python
@app.middleware(priority=50, pre_route=True)
def my_middleware(request):
    # Your logic here
    return None  # Continue, or return Response() to stop
```

### Key Features
- **🏎️ High Performance**: C-accelerated execution
- **🎛️ Priority Control**: Control execution order
- **🔄 Pre/Post Route**: Run before or after handlers
- **📡 Context Sharing**: Share data between middleware
- **⚠️ Error Handling**: Graceful error responses

## 🛠️ Common Use Cases

| Use Case | Priority Range | Description |
|----------|----------------|-------------|
| **Request Setup** | 1-10 | CORS, request logging, ID generation |
| **Authentication** | 20-40 | Token validation, user loading |
| **Authorization** | 41-50 | Permission checking, role validation |
| **Validation** | 51-70 | Input validation, rate limiting |
| **Business Logic** | 71-90 | Custom business middleware |
| **Response Processing** | 91-99 | Response headers, logging, formatting |

## 🔗 Integration Points

### With Dependency Injection
```python
@app.middleware(priority=50)
def di_middleware(request, auth_service: AuthService = Depends("auth")):
    # Use injected services
    pass
```

### With Route Groups
```python
api_group = app.router_group("/api")

@api_group.middleware(priority=50)
def api_specific_middleware(request):
    # Only applies to /api/* routes
    pass
```
  - Testing and debugging
  - Performance tips
  - Migration from other frameworks

### 🔧 Technical Reference
- **[Middleware Technical Reference](middleware.md)** - Complete technical documentation for advanced features
  - C compilation details
  - Memory pool optimization
  - Built-in middleware
  - Performance benchmarks
  - Advanced configuration

### 🏗️ Implementation Details
- **[Engineering Plan](../plan/zero_allocation_middleware_system_plan.md)** - Technical architecture and implementation details
  - System architecture
  - C-bridge integration
  - Memory management
  - Performance targets

## 📊 Performance Characteristics

| Middleware Type | Execution Time | Memory Usage | Best For |
|-----------------|----------------|--------------|----------|
| **Simple Python** | ~5-10μs | Low | Development, simple logic |
| **C-Optimized** | ~0.1-1μs | Very Low | Production, high throughput |
| **Built-in C** | ~0.05μs | Minimal | Maximum performance |

## 🎓 Learning Path

1. **Start**: Read [Middleware Guide](middleware_guide.md) (15 minutes)
2. **Practice**: Try [basic_middleware.py](../examples/middleware/basic_middleware.py) (10 minutes)
3. **Build**: Create your own auth middleware (30 minutes)
4. **Optimize**: Learn [Zero-Allocation System](middleware.md) (advanced)
5. **Production**: Study [production_api.py](../examples/middleware/production_api.py)

## 🚨 Quick Troubleshooting

**"My middleware isn't running"**
- Check priority order (lower numbers run first)
- Ensure you're returning `None` to continue
- Verify middleware is registered before `app.run()`

**"Getting wrong response format"**
- Use `Response(content, status_code=200)` not `Response(status=200, body=content)`
- Check [Response API](middleware_guide.md#returning-responses)

**"Performance is slow"**
- Use lower priority numbers for critical middleware
- Consider [C-optimized patterns](middleware.md#performance-optimization)
- Profile with built-in middleware stats

**"Testing issues"**
- Use `TestClient` from `catzilla.testing`
- Test middleware independently with different scenarios
- Check [Testing Guide](middleware_guide.md#testing-middleware)

## 🔍 Need Help?

1. **Documentation Issues**: Check if examples work in [`examples/middleware/`](../examples/middleware/)
2. **Performance Questions**: See [Performance Benchmarks](performance-benchmarks.md)
3. **Migration Help**: Read [Migration Guide](migration_from_fastapi.md)
4. **Advanced Features**: Review [Technical Plan](../plan/zero_allocation_middleware_system_plan.md)

---

*Choose your path and start building high-performance middleware with Catzilla!* 🚀
