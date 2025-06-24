# Catzilla Logging Quick Reference

## 🚀 Quick Start

### Development Mode
```python
from catzilla import Catzilla

app = Catzilla(production=False)  # Enables banner + request logging
app.listen(host="127.0.0.1", port=8000)
```

### Production Mode
```python
from catzilla import Catzilla

app = Catzilla(production=True)   # Minimal banner, no request logging
app.listen(host="127.0.0.1", port=8000)
```

## 🎨 Configuration Options

| Parameter | Default | Description |
|-----------|---------|-------------|
| `production` | `False` | Enable production mode (disables request logging) |
| `show_banner` | `True` | Display startup banner |
| `log_requests` | `None` | Log requests (auto-disabled in production) |
| `enable_colors` | `True` | Enable colorized output |
| `show_request_details` | `True` | Show detailed request information |

## 🌈 Color Codes

### HTTP Methods
- 🟢 **GET** - Bright Green
- 🔵 **POST** - Bright Blue
- 🟡 **PUT** - Bright Yellow
- 🔴 **DELETE** - Bright Red
- 🟣 **PATCH** - Bright Magenta
- 🟠 **OPTIONS** - Bright Cyan

### Status Codes
- 🟢 **2xx** - Success (Green)
- 🟡 **3xx** - Redirect (Yellow)
- 🔴 **4xx** - Client Error (Red)
- 🔴 **5xx** - Server Error (Bright Red)

### Response Times
- 🟢 **< 10ms** - Fast (Green)
- 🟡 **10-50ms** - Normal (Yellow)
- 🟠 **50-200ms** - Slow (Orange)
- 🔴 **> 200ms** - Very Slow (Red)

## 📊 Log Format

```
[HH:MM:SS] METHOD  /path              STATUS  TIME   SIZE → IP
[10:30:23] GET     /api/users         200     12ms   1.2KB → 127.0.0.1
```

## 🔧 Performance Impact

| Mode | Banner | Request Logging | Overhead |
|------|--------|----------------|----------|
| Development | ✅ Full | ✅ Enabled | ~1ms per request |
| Production | ✅ Minimal | ❌ Disabled | ~0ms (zero overhead) |

## 💡 Pro Tips

1. **Auto-detection**: Colors automatically disabled on non-TTY outputs
2. **Zero overhead**: Production mode has no performance impact
3. **Graceful degradation**: Missing dependencies don't break functionality
4. **Memory efficient**: Uses minimal memory for logging
5. **Thread-safe**: Safe for multi-threaded applications

## 🐛 Troubleshooting

### No colors showing?
- Check if terminal supports colors
- Verify `enable_colors=True`
- Try `force_color=True` if needed

### Banner not showing?
- Check `show_banner=True`
- Verify no import errors in logging modules
- Check if terminal width is sufficient (62+ chars)

### Performance issues?
- Use `production=True` for production
- Set `log_requests=False` for high traffic
- Consider `log_sampling_rate < 1.0` for sampling

## 📖 Examples

### Custom Configuration
```python
app = Catzilla(
    production=False,
    show_banner=True,
    log_requests=True,
    enable_colors=True,
    show_request_details=False,  # Hide User-Agent, etc.
    use_jemalloc=True,
    memory_profiling=True
)
```

### Conditional Logging
```python
import os

app = Catzilla(
    production=os.getenv("ENVIRONMENT") == "production",
    enable_colors=os.getenv("COLORTERM") is not None,
    log_requests=os.getenv("LOG_REQUESTS", "true").lower() == "true"
)
```

### Docker-friendly
```python
app = Catzilla(
    production=True,
    enable_colors=False,  # Disable colors for Docker logs
    show_banner=True
)
```
