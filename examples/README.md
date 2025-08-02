# Catzilla Framework Examples

Welcome to the comprehensive examples collection for **Catzilla v0.2.0** - a high-performance Python web framework with C-accelerated routing using libuv for async operations.

## 🚀 Framework Overview

Catzilla is designed for maximum performance with:
- **C-accelerated routing** for ultra-fast request handling
- **Zero-allocation middleware** system for minimal overhead
- **Built-in async operations** handled by libuv in C (no `async def` needed!)
- **Multi-layer caching** with memory, Redis, and disk support
- **Advanced validation** and data modeling

## 📁 Examples Structure

This directory contains **18 comprehensive examples** organized into **9 categories**, each demonstrating different aspects of the Catzilla framework:

### 🏗️ Core Examples (`core/`)
Essential framework features and basic patterns.

| File | Description | Key Features |
|------|-------------|--------------|
| **`debug_logging.py`** | Comprehensive debugging and logging system | Custom loggers, request tracing, performance monitoring, structured logging |
| **`router_groups.py`** | Advanced routing patterns and URL groups | Route groups, nested routing, parameter validation, middleware per group |

### ✅ Validation Examples (`validation/`)
Data validation and model definitions.

| File | Description | Key Features |
|------|-------------|--------------|
| **`models_and_fields.py`** | Data models and field validation | Pydantic-style models, custom validators, type checking, serialization |
| **`query_header_form.py`** | Request validation patterns | Query parameter validation, header validation, form data processing |

### ⚡ Background Tasks Examples (`background_tasks/`)
Asynchronous task processing and scheduling.

| File | Description | Key Features |
|------|-------------|--------------|
| **`scheduling.py`** | Task scheduling and cron-like operations | Scheduled tasks, periodic jobs, task queues, retry logic |
| **`monitoring.py`** | Task monitoring and health tracking | Task status tracking, performance metrics, failure handling |

### 🔌 Dependency Injection Examples (`dependency_injection/`)
Service management and dependency patterns.

| File | Description | Key Features |
|------|-------------|--------------|
| **`scoped_services.py`** | Service scoping and lifecycle management | Singleton services, request-scoped services, service lifetimes |
| **`factories.py`** | Dynamic service factories and providers | Factory patterns, service providers, dynamic configuration |

### �️ Cache Examples (`cache/`)
Smart caching system with multi-level storage.

| File | Description | Key Features |
|------|-------------|--------------|
| **`basic_cache_example.py`** | Basic Smart Cache usage and function caching | @cached decorator, direct cache operations, TTL management, statistics |
| **`smart_cache_example.py`** | Advanced multi-level caching with middleware | Memory/Redis/Disk caching, cache middleware, conditional rules, monitoring |
| **`cache_configurations.py`** | Different cache configuration patterns | Memory-only, persistent, distributed configs, performance comparison |

### �🔗 Middleware Examples (`middleware/`)
Request/response processing middleware.

| File | Description | Key Features |
|------|-------------|--------------|
| **`ordering.py`** | Middleware execution order and priorities | Middleware priorities, execution chains, order control |
| **`custom_hooks.py`** | Custom middleware with lifecycle hooks | Custom middleware creation, request/response hooks, error handling |

### 📡 Streaming Examples (`streaming/`)
HTTP streaming and real-time data.

| File | Description | Key Features |
|------|-------------|--------------|
| **`response_streams.py`** | HTTP response streaming | Chunked responses, server-sent events, data streaming |
| **`connection_management.py`** | Connection pooling and management | Connection pools, keep-alive, connection optimization |

### 📁 Files Examples (`files/`)
File handling and static content serving.

| File | Description | Key Features |
|------|-------------|--------------|
| **`upload_handling.py`** | File upload processing and validation | Multipart uploads, file validation, image processing, storage |
| **`static_serving.py`** | Static file serving with optimization | Static file serving, caching, compression, CDN integration |

### 🗄️ Cache Examples (`cache/`)
Multi-layer caching strategies.

| File | Description | Key Features |
|------|-------------|--------------|
| **`multi_layer.py`** | Multi-layer caching (memory, Redis, disk) | Cache layers, fallback strategies, cache warming, metrics |
| **`performance_optimization.py`** | Cache optimization strategies | Performance optimization, cache analytics, predictive caching |

### 🍳 Recipes Examples (`recipes/`)
Common patterns and real-world solutions.

| File | Description | Key Features |
|------|-------------|--------------|
| **`rest_api_patterns.py`** | Complete REST API with CRUD operations | REST patterns, CRUD operations, pagination, filtering, error handling |
| **`auth_patterns.py`** | Authentication & authorization patterns | JWT auth, API keys, RBAC, rate limiting, session management |

## 🚀 Getting Started

### Prerequisites

```bash
# Install Catzilla framework
pip install catzilla

# Optional dependencies for advanced examples
pip install redis psutil pillow jwt
```

### Running Examples

Each example is a standalone application. To run any example:

```bash
# Navigate to the examples directory
cd examples/

# Run a specific example
python core/debug_logging.py
python validation/models_and_fields.py
python recipes/rest_api_patterns.py
```

Most examples run on `http://localhost:8000` and include:
- 📖 **API documentation** at the root endpoint (`/`)
- 🔍 **Interactive examples** with curl commands
- 🏥 **Health check** endpoint (`/health`)
- 📊 **Metrics and monitoring** endpoints

## 🧪 Example Categories Explained

### 🏗️ **Core Examples** - Start Here!
Perfect for beginners to understand Catzilla's basic concepts and routing system.

**Try first:**
```bash
python core/debug_logging.py
# Visit http://localhost:8000 for documentation
```

### ✅ **Validation Examples** - Data Safety
Learn how to validate and process incoming data safely.

**Key concepts:**
- Model-based validation
- Custom field validators
- Request data processing

### ⚡ **Background Tasks** - Async Processing
Handle long-running tasks without blocking requests.

**Use cases:**
- Email sending
- Image processing
- Data synchronization
- Scheduled maintenance

### 🔌 **Dependency Injection** - Clean Architecture
Manage services and dependencies cleanly.

**Benefits:**
- Testable code
- Service isolation
- Configuration management
- Lifecycle control

### 🔗 **Middleware** - Request Processing
Intercept and modify requests/responses.

**Common middleware:**
- Authentication
- Logging
- Rate limiting
- CORS handling

### 📡 **Streaming** - Real-time Data
Handle large responses and real-time data efficiently.

**Applications:**
- File downloads
- Live data feeds
- Server-sent events
- Progress tracking

### 📁 **Files** - File Operations
Handle file uploads, downloads, and static content.

**Features:**
- Secure file uploads
- Image processing
- Static file optimization
- CDN integration

### 🗄️ **Cache** - Performance Optimization
Implement multi-layer caching for better performance.

**Cache layers:**
- Memory (fastest)
- Redis (distributed)
- Disk (persistent)

### 🍳 **Recipes** - Real-world Patterns
Production-ready patterns for common use cases.

**Essential patterns:**
- REST API design
- Authentication flows
- Error handling
- API documentation

### 🔬 **Advanced** - Enterprise Features
Complex features for large-scale applications.

**Enterprise needs:**
- Real-time streaming
- Connection management
- Background task coordination
- Performance monitoring

## 📚 Learning Path

### 1. **Beginner Path** (Start here)
```
core/debug_logging.py
↓
core/router_groups.py
↓
validation/models_and_fields.py
↓
recipes/rest_api_patterns.py
```

### 2. **Intermediate Path**
```
middleware/custom_hooks.py
↓
cache/multi_layer.py
↓
files/upload_handling.py
↓
recipes/auth_patterns.py
```

### 3. **Advanced Path**
```
streaming/response_streams.py
↓
background_tasks/scheduling.py
↓
streaming/connection_management.py
```

## 🎯 Key Features by Example

### Authentication & Security
- **JWT Authentication**: `recipes/auth_patterns.py`
- **API Key Management**: `recipes/auth_patterns.py`
- **Role-based Access Control**: `recipes/auth_patterns.py`
- **Rate Limiting**: `recipes/auth_patterns.py`

### Performance Optimization
- **Caching Strategies**: `cache/multi_layer.py`, `cache/performance_optimization.py`
- **Connection Pooling**: `streaming/connection_management.py`

### Real-time Features
- **Server-sent Events**: `streaming/response_streams.py`
- **Live Data Streaming**: `streaming/response_streams.py`

### Data Processing
- **File Uploads**: `files/upload_handling.py`
- **Image Processing**: `files/upload_handling.py`
- **Data Validation**: `validation/models_and_fields.py`, `validation/query_header_form.py`
- **Background Tasks**: `background_tasks/scheduling.py`, `background_tasks/monitoring.py`

### Enterprise Patterns
- **Health Monitoring**: `background_tasks/monitoring.py`
- **Distributed Tracing**: `core/debug_logging.py`

## 🔧 Important Syntax Notes

### ⚠️ Catzilla Async Handling
Catzilla uses **C-accelerated async operations with libuv**, which means:

```python
# ✅ CORRECT - Use regular def (not async def)
@app.get("/users")
def get_users(request: Request) -> Response:
    data = request.json()  # ✅ Synchronous call
    return JSONResponse(data)

# ❌ WRONG - Don't use async def
async def get_users(request: Request) -> Response:
    data = await request.json()  # ❌ Don't await
    return JSONResponse(data)
```

**Why?** Catzilla handles all async operations internally in C using libuv, making your Python code simpler and faster!

## 🧪 Testing Examples

Each example includes comprehensive testing patterns:

```bash
# Run example with test data
python recipes/rest_api_patterns.py

# Use curl to test endpoints
curl http://localhost:8000/
curl http://localhost:8000/health
curl -X POST -H "Content-Type: application/json" \
     -d '{"name":"test"}' \
     http://localhost:8000/api/users
```

## 🤝 Contributing

Found an issue or want to improve an example?

1. **Report Issues**: Open an issue describing the problem
2. **Suggest Improvements**: Propose enhancements or new examples
3. **Submit PRs**: Follow the existing code style and patterns

## 📖 Documentation

- **Framework Docs**: [Catzilla Documentation](https://github.com/rezwanahmedsami/catzilla)
- **API Reference**: Check the framework's main documentation
- **Example Issues**: Report example-specific issues in the main repository

## 🎉 What's Next?

After exploring these examples:

1. **Build Your Application**: Use the patterns in your own projects
2. **Performance Tuning**: Apply caching and optimization strategies
3. **Production Deployment**: Use microservices and monitoring patterns
4. **Community**: Share your Catzilla applications with the community!

---

**Happy coding with Catzilla! 🚀**

*These examples demonstrate the power and simplicity of building high-performance web applications with Catzilla's C-accelerated framework.*
