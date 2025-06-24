# Catzilla Startup Banner & Logging Design

## 🎨 Visual Design Specifications

### 1. Startup Banner Layouts

#### Development Mode Banner
```
╔══════════════════════════════════════════════════════════╗
║ 🐱 Catzilla v0.1.0 - DEVELOPMENT MODE                   ║
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
║ Cache .............. Redis (connected)                  ║
║ Profiling .......... Enabled (60s interval)            ║
║                                                         ║
║ PID ................ 12345                              ║
║ Memory ............. 45.2 MB                            ║
║ Started ............ 2025-06-24 10:30:15                ║
║                                                         ║
║ 💡 Request logging enabled - watching for changes...    ║
╚══════════════════════════════════════════════════════════╝
```

#### Production Mode Banner
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

### 2. Development Request Logging

#### Standard Request Log Format
```
[10:30:23] GET    /api/users          200  12ms   1.2KB → 127.0.0.1
[10:30:24] POST   /api/users          201  45ms   0.8KB → 127.0.0.1
[10:30:25] GET    /api/users/123      404   2ms   0.1KB → 127.0.0.1
[10:30:26] PUT    /api/users/123      500  89ms   0.3KB → 127.0.0.1
[10:30:27] DELETE /api/users/123      204   5ms   0.0KB → 127.0.0.1
```

#### Detailed Request Log Format (with headers)
```
[10:30:23] GET    /api/users?page=1   200  12ms   1.2KB → 127.0.0.1
           ├─ User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X)
           └─ Content-Type: application/json
```

#### Error Request Log Format
```
[10:30:26] PUT    /api/users/123      500  89ms   0.3KB → 127.0.0.1
           ❌ ValidationError: Invalid email format
           ├─ Field: email
           └─ Value: "invalid-email"
```

### 3. Color Scheme

#### HTTP Methods
- `GET` → Bright Green `\033[92m`
- `POST` → Bright Blue `\033[94m`
- `PUT` → Bright Yellow `\033[93m`
- `DELETE` → Bright Red `\033[91m`
- `PATCH` → Bright Magenta `\033[95m`
- `OPTIONS` → Bright Cyan `\033[96m`
- `HEAD` → White `\033[97m`

#### Status Codes
- `2xx` → Green `\033[32m`
- `3xx` → Yellow `\033[33m`
- `4xx` → Red `\033[31m`
- `5xx` → Bright Red `\033[91m`

#### Response Times
- `< 10ms` → Green `\033[32m`
- `10-50ms` → Yellow `\033[33m`
- `50-200ms` → Orange `\033[38;5;208m`
- `> 200ms` → Red `\033[31m`

#### Banner Elements
- Title → Bright Cyan `\033[96m`
- Mode (DEV) → Bright Yellow `\033[93m`
- Mode (PROD) → Bright Green `\033[92m`
- Values → White `\033[97m`
- Labels → Gray `\033[37m`

## 🏗️ Component Architecture

### Banner System Components

```python
class BannerRenderer:
    """Renders the startup banner with server information"""

    def render(self, info: ServerInfo, mode: str) -> str:
        """Render the complete banner"""

    def _render_header(self, info: ServerInfo, mode: str) -> str:
        """Render banner header with title and URL"""

    def _render_config_section(self, info: ServerInfo) -> str:
        """Render configuration section"""

    def _render_system_section(self, info: ServerInfo) -> str:
        """Render system information section"""

    def _render_footer(self, mode: str) -> str:
        """Render banner footer with mode-specific message"""
```

```python
class ServerInfoCollector:
    """Collects server configuration and runtime information"""

    def collect(self) -> ServerInfo:
        """Collect all server information"""

    def _get_route_count(self) -> int:
        """Get total number of registered routes"""

    def _get_worker_count(self) -> int:
        """Get configured worker count"""

    def _get_memory_usage(self) -> str:
        """Get current memory usage"""

    def _get_feature_status(self) -> Dict[str, str]:
        """Get status of various features (jemalloc, cache, etc.)"""
```

### Logging System Components

```python
class DevLogger:
    """Development request logger with colorized output"""

    def log_request(self, request: Request, response: Response,
                   duration: float) -> None:
        """Log a single request/response cycle"""

    def _format_request_line(self, request: Request, response: Response,
                           duration: float) -> str:
        """Format the main request log line"""

    def _format_method(self, method: str) -> str:
        """Format HTTP method with color"""

    def _format_status(self, status: int) -> str:
        """Format status code with color"""

    def _format_duration(self, duration: float) -> str:
        """Format response time with performance color"""
```

## 📊 Data Models

```python
@dataclass
class ServerInfo:
    """Container for server information displayed in banner"""
    version: str
    host: str
    port: int
    protocol: str
    route_count: int
    worker_count: int
    prefork_enabled: bool
    prefork_processes: int
    jemalloc_enabled: bool
    cache_info: str
    profiling_enabled: bool
    profiling_interval: int
    pid: int
    memory_usage: str
    start_time: datetime
    mode: str  # "development" or "production"
    debug_enabled: bool
    hot_reload_enabled: bool

@dataclass
class RequestLogEntry:
    """Container for request log information"""
    timestamp: datetime
    method: str
    path: str
    status_code: int
    duration_ms: float
    response_size: int
    client_ip: str
    user_agent: Optional[str] = None
    error_message: Optional[str] = None
```

## ⚙️ Configuration Schema

```python
class LoggingConfig:
    """Configuration for logging and banner system"""

    # Banner settings
    show_banner: bool = True
    banner_style: str = "box"  # "box", "minimal", "none"

    # Development logging
    log_requests: bool = True  # Auto-disabled in production
    log_format: str = "dev"    # "dev", "simple", "json"
    log_level: str = "INFO"
    show_client_info: bool = True
    show_response_size: bool = True
    show_request_headers: bool = False
    show_response_headers: bool = False

    # Color settings
    color_output: bool = True  # Auto-detect TTY
    force_color: bool = False

    # Performance settings
    log_buffer_size: int = 1000
    log_sampling_rate: float = 1.0  # For high traffic
    max_log_line_length: int = 200

    # Error logging
    log_stack_traces: bool = True
    log_request_body_on_error: bool = False
```

## 🔧 Integration Points

### App.py Integration
```python
class Catzilla:
    def __init__(self, debug: bool = False, **kwargs):
        self.debug = debug
        self.logging_config = LoggingConfig(**kwargs)
        self.banner_renderer = BannerRenderer()
        self.dev_logger = DevLogger() if debug else None

    def listen(self, host: str, port: int):
        # Collect server info
        server_info = self._collect_server_info(host, port)

        # Show startup banner
        if self.logging_config.show_banner:
            banner = self.banner_renderer.render(
                server_info,
                "development" if self.debug else "production"
            )
            print(banner)

        # Start server with logging middleware
        if self.dev_logger:
            self._add_logging_middleware()

        # Start the actual server
        self._start_server(host, port)
```

This design provides a comprehensive, performant, and beautiful logging experience that enhances developer productivity while maintaining production efficiency.
