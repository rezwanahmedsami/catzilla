# 📋 Static File Server Quick Reference

## Basic Usage

```python
from catzilla import Catzilla

app = Catzilla()
app.mount_static("/static", "./static")
```

## Common Configurations

### Web Assets (CSS, JS, Images)
```python
app.mount_static("/static", "./static",
    cache_size_mb=200,
    cache_ttl_seconds=3600,      # 1 hour
    enable_compression=True,
    compression_level=8
)
```

### Media Streaming (Videos, Audio)
```python
app.mount_static("/media", "./uploads",
    cache_size_mb=500,
    enable_compression=False,    # Don't compress media
    enable_range_requests=True,  # For streaming
    max_file_size=1024*1024*1024  # 1GB
)
```

### CDN-Style (Maximum Performance)
```python
app.mount_static("/cdn", "./dist",
    cache_size_mb=1000,
    cache_ttl_seconds=86400,     # 24 hours
    compression_level=9          # Max compression
)
```

### Development Mode
```python
app.mount_static("/files", "./files",
    enable_hot_cache=False,      # No caching
    enable_directory_listing=True,  # Browse directories
    enable_hidden_files=True     # Show .dotfiles
)
```

## Security Settings

```python
# Production Security
app.mount_static("/public", "./public",
    enable_directory_listing=False,  # No browsing
    enable_hidden_files=False,       # Hide .dotfiles
    max_file_size=10*1024*1024       # 10MB limit
)
```

## Parameter Quick Reference

| Parameter | Default | Range | Description |
|-----------|---------|-------|-------------|
| `mount_path` | *required* | Must start with "/" | URL path prefix |
| `directory` | *required* | Must exist | Local directory path |
| `index_file` | `"index.html"` | Any filename | Default file for directories |
| `enable_hot_cache` | `True` | True/False | In-memory file caching |
| `cache_size_mb` | `100` | 1-10,240 | Cache memory limit (MB) |
| `cache_ttl_seconds` | `3600` | 1-604,800 | Cache time-to-live |
| `enable_compression` | `True` | True/False | Gzip compression |
| `compression_level` | `6` | 1-9 | Compression level |
| `max_file_size` | `100MB` | 1KB-10GB | Maximum file size |
| `enable_etags` | `True` | True/False | ETag headers |
| `enable_range_requests` | `True` | True/False | HTTP Range support |
| `enable_directory_listing` | `False` | True/False | Directory browsing |
| `enable_hidden_files` | `False` | True/False | Serve .dotfiles |

## Performance Tips

- **High Traffic**: `cache_size_mb=1000+`, `cache_ttl_seconds=86400`
- **Text Files**: `compression_level=8-9`
- **Media Files**: `enable_compression=False`
- **Development**: `enable_hot_cache=False`
- **Streaming**: `enable_range_requests=True`

## Troubleshooting

### 404 Not Found
```python
# ❌ Wrong
app.mount_static("static", "./static")

# ✅ Correct
app.mount_static("/static", "./static")
```

### 403 Forbidden (Directory)
```python
# Add index.html OR enable directory listing
app.mount_static("/static", "./static",
    enable_directory_listing=True)
```

### Files Not Updating
```python
# Disable cache for development
app.mount_static("/static", "./static",
    enable_hot_cache=False)
```

### Debug Mode
```python
import os
os.environ['CATZILLA_C_DEBUG'] = '1'
app = Catzilla(debug=True, log_requests=True)
```

## Performance Benchmarks

- **Hot Cache**: 400,000+ RPS
- **Cold Files**: 250,000+ RPS
- **Memory**: 35% less than alternatives
- **Latency**: Sub-millisecond for cached files
