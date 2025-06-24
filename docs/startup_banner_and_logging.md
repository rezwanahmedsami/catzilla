# Catzilla Startup Banner & Development Logging

This document describes Catzilla's beautiful startup banner and development logging system that provides an excellent developer experience while maintaining production performance.

## 🎨 Beautiful Startup Banner

Catzilla displays a gorgeous startup banner that shows essential server information at startup.

### Development Mode Banner

```
╔══════════════════════════════════════════════════════════╗
║ 🐱 Catzilla v0.1.0 - DEVELOPMENT                        ║
║ http://127.0.0.1:8000                                   ║
║ (bound on host 127.0.0.1 and port 8000)                ║
║                                                         ║
║ Environment ........ Development                        ║
║ Debug .............. Enabled                            ║
║ Hot Reload ......... Enabled                            ║
║                                                         ║
║ Routes ............. 13                                 ║
║ Workers ............ 4                                  ║
║ Prefork ............ Disabled                           ║
║ jemalloc ........... Enabled                            ║
║ Cache .............. In-Memory                          ║
║ Profiling .......... Enabled (60s interval)            ║
║                                                         ║
║ PID ................ 12345                              ║
║ Memory ............. 45.2 MB                            ║
║ Started ............ 2025-06-24 10:30:15                ║
║                                                         ║
║ 💡 Request logging enabled - watching for changes...    ║
╚══════════════════════════════════════════════════════════╝
```

### Production Mode Banner

```
╔══════════════════════════════════════════════════════════╗
║ 🐱 Catzilla v0.1.0 - PRODUCTION                         ║
║ https://api.example.com                                  ║
║ (bound on host 0.0.0.0 and port 443)                   ║
║                                                         ║
║ Routes ............. 47                                 ║
║ Workers ............ 16                                 ║
║ Prefork ............ Enabled (4 processes)              ║
║ jemalloc ........... Enabled                            ║
║ Cache .............. Redis Cluster (3 nodes)            ║
║                                                         ║
║ PID ................ 12345                              ║
║ Memory ............. 128.4 MB                           ║
║ Started ............ 2025-06-24 10:30:15                ║
║                                                         ║
║ 🚀 Production mode - optimized for performance          ║
╚══════════════════════════════════════════════════════════╝
```

## 🌈 Development Request Logging

In development mode, Catzilla logs each request with beautiful colors and detailed information:

```
[10:30:23] GET    /api/users          200  12ms   1.2KB → 127.0.0.1
[10:30:24] POST   /api/users          201  45ms   0.8KB → 127.0.0.1
[10:30:25] GET    /api/users/123      404   2ms   0.1KB → 127.0.0.1
[10:30:26] PUT    /api/users/123      500  89ms   0.3KB → 127.0.0.1
[10:30:27] DELETE /api/users/123      204   5ms   0.0KB → 127.0.0.1
```

### Color Coding

- **HTTP Methods:**
  - `GET` → Bright Green
  - `POST` → Bright Blue
  - `PUT` → Bright Yellow
  - `DELETE` → Bright Red
  - `PATCH` → Bright Magenta
  - `OPTIONS` → Bright Cyan

- **Status Codes:**
  - `2xx` → Green (success)
  - `3xx` → Yellow (redirect)
  - `4xx` → Red (client error)
  - `5xx` → Bright Red (server error)

- **Response Times:**
  - `< 10ms` → Green (fast)
  - `10-50ms` → Yellow (normal)
  - `50-200ms` → Orange (slow)
  - `> 200ms` → Red (very slow)

## 🔧 Configuration Options

### Basic Usage

```python
from catzilla import Catzilla

# Development mode with full logging
app = Catzilla(
    production=False,          # Enable development mode
    show_banner=True,          # Show startup banner
    log_requests=True,         # Log individual requests
    enable_colors=True,        # Enable colorized output
    show_request_details=True  # Show detailed request info
)

# Production mode with minimal logging
app = Catzilla(
    production=True,           # Enable production mode
    show_banner=True,          # Show startup banner (minimal)
    log_requests=False,        # Disable request logging
    enable_colors=False        # Disable colors
)
```

### Advanced Configuration

```python
app = Catzilla(
    production=False,

    # Banner settings
    show_banner=True,

    # Logging settings
    log_requests=True,         # Auto-disabled in production
    enable_colors=True,        # Auto-detect TTY
    show_request_details=True, # Show User-Agent, etc.

    # Memory and performance
    use_jemalloc=True,
    memory_profiling=True,
    auto_memory_tuning=True,
    memory_stats_interval=60,

    # Features
    auto_validation=True,
    enable_di=True
)
```

## 📊 Route Registration Logging

In development mode, Catzilla logs route registration as they're defined:

```python
@app.get("/users")
def get_users(request):
    return {"users": []}
```

Output:
```
📍 GET     /users                → get_users
```

## 🔥 Error Logging

When errors occur in development mode, Catzilla provides detailed error information:

```
[10:30:26] PUT    /api/users/123      500  89ms   0.3KB → 127.0.0.1
           ❌ ValidationError: Invalid email format
           ├─ Field: email
           └─ Value: "invalid-email"
```

## ⚡ Performance Features

### Production Mode
- ✅ Zero overhead when logging disabled
- ✅ Single banner display on startup
- ✅ No string formatting for disabled logs
- ✅ Minimal memory allocation
- ✅ No color processing overhead

### Development Mode
- ✅ Buffered logging for performance
- ✅ Lazy evaluation of log messages
- ✅ Configurable verbosity levels
- ✅ Optional request body logging
- ✅ Sampling for high-traffic scenarios

## 🎯 Why This is Amazing

### Developer Experience Benefits
1. **Immediate Feedback** - See server status at a glance
2. **Debug Information** - Colorized logs make debugging faster
3. **Performance Awareness** - Response times visible in real-time
4. **Configuration Validation** - See what features are enabled
5. **Professional Feel** - Matches expectations from other frameworks

### Production Benefits
1. **Zero Performance Impact** - Completely disabled in production
2. **Essential Information** - Still shows critical startup info
3. **Monitoring Integration** - Can hook into APM tools
4. **Security** - No sensitive information in logs

## 📖 Examples

### Development Server Example

```python
from catzilla import Catzilla
from catzilla.types import JSONResponse, Request

# Create development app
app = Catzilla(production=False)

@app.get("/")
def home(request: Request):
    return {"message": "Welcome to Catzilla!"}

@app.get("/users/{user_id}")
def get_user(request: Request):
    user_id = request.path_params.get("user_id")
    return {"user_id": user_id, "name": f"User {user_id}"}

@app.post("/users")
def create_user(request: Request):
    return {"message": "User created", "id": 123}

if __name__ == "__main__":
    app.listen(8000, "127.0.0.1")
```

### Production Server Example

```python
from catzilla import Catzilla

# Create production app
app = Catzilla(production=True)

@app.get("/health")
def health_check(request):
    return {"status": "healthy"}

@app.get("/api/users/{user_id}")
def get_user(request):
    user_id = request.path_params.get("user_id")
    return {"user_id": user_id, "name": f"User {user_id}"}

if __name__ == "__main__":
    app.listen(8000, "0.0.0.0")
```

## 🔧 System Requirements

- Python 3.7+
- Optional: `psutil` for enhanced system information (automatically installed)
- Terminal with color support (auto-detected)

## 🤝 Integration with Existing Features

The logging system seamlessly integrates with Catzilla's existing features:

- ✅ C-accelerated routing
- ✅ Zero-allocation middleware
- ✅ Dependency injection system
- ✅ Auto-validation
- ✅ Background tasks
- ✅ Memory optimization (jemalloc)
- ✅ Error handling

This creates a cohesive, professional development experience that scales from development to production.
