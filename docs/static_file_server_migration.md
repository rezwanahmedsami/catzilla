# 🔄 Static File Server Migration Guide

## From Flask to Catzilla

### Flask Static Files
```python
# Flask (basic)
from flask import Flask, send_from_directory

app = Flask(__name__, static_folder='static')

@app.route('/static/<path:filename>')
def static_files(filename):
    return send_from_directory('static', filename)
```

### Catzilla Equivalent
```python
# Catzilla (high-performance)
from catzilla import Catzilla

app = Catzilla()
app.mount_static("/static", "./static")  # 400,000+ RPS!
```

**Benefits of migration:**
- 🚀 **8x faster** performance (400k vs 50k RPS)
- 🧠 **Smart caching** with automatic LRU eviction
- 🗜️ **Built-in compression** (60-80% bandwidth savings)
- ⚡ **Zero configuration** - works out of the box

---

## From FastAPI to Catzilla

### FastAPI Static Files
```python
# FastAPI
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
```

### Catzilla Equivalent
```python
# Catzilla (C-native performance)
from catzilla import Catzilla

app = Catzilla()
app.mount_static("/static", "./static")
```

**Performance comparison:**
- **FastAPI**: ~30,000 RPS, 150MB memory usage
- **Catzilla**: ~400,000 RPS, 97MB memory usage (35% less)

---

## From Express.js to Catzilla

### Express.js Static Files
```javascript
// Express.js
const express = require('express');
const app = express();

app.use('/static', express.static('public'));
app.use('/uploads', express.static('uploads', {
    maxAge: '1d',
    etag: true
}));
```

### Catzilla Equivalent
```python
# Catzilla
from catzilla import Catzilla

app = Catzilla()

# Basic static files
app.mount_static("/static", "./public")

# Advanced configuration (like Express options)
app.mount_static("/uploads", "./uploads",
    cache_ttl_seconds=86400,  # maxAge: 1 day
    enable_etags=True         # etag: true
)
```

---

## From Nginx to Catzilla

### Nginx Configuration
```nginx
# nginx.conf
server {
    listen 80;

    # Static files
    location /static/ {
        alias /var/www/static/;
        expires 1h;
        gzip on;
        gzip_comp_level 6;
    }

    # Media files
    location /media/ {
        alias /var/www/media/;
        expires 1d;
        gzip off;
    }
}
```

### Catzilla Equivalent
```python
# Catzilla (single file, same performance!)
from catzilla import Catzilla

app = Catzilla()

# Static files (equivalent to nginx config)
app.mount_static("/static", "/var/www/static",
    cache_ttl_seconds=3600,   # expires 1h
    enable_compression=True,  # gzip on
    compression_level=6       # gzip_comp_level 6
)

# Media files
app.mount_static("/media", "/var/www/media",
    cache_ttl_seconds=86400,  # expires 1d
    enable_compression=False  # gzip off
)
```

**Why choose Catzilla over Nginx:**
- 🎯 **Single deployment** - no reverse proxy needed
- 🚀 **Higher performance** - 400k RPS vs Nginx's ~200k
- 🛠️ **Easier configuration** - Python code vs config files
- 🔄 **Hot reloading** - instant updates during development

---

## From Apache to Catzilla

### Apache Configuration
```apache
# .htaccess or httpd.conf
<Directory "/var/www/static">
    ExpiresActive On
    ExpiresByType text/css "access plus 1 hour"
    ExpiresByType application/javascript "access plus 1 hour"
    ExpiresByType image/* "access plus 1 day"
</Directory>

<Location "/static">
    SetOutputFilter DEFLATE
    SetEnvIfNoCase Request_URI \
        \.(?:gif|jpe?g|png)$ no-gzip dont-vary
</Location>
```

### Catzilla Equivalent
```python
# Catzilla (much simpler!)
from catzilla import Catzilla

app = Catzilla()

# CSS and JS files
app.mount_static("/css", "./static/css",
    cache_ttl_seconds=3600,   # 1 hour
    enable_compression=True
)

app.mount_static("/js", "./static/js",
    cache_ttl_seconds=3600,   # 1 hour
    enable_compression=True
)

# Images (no compression, longer cache)
app.mount_static("/images", "./static/images",
    cache_ttl_seconds=86400,  # 1 day
    enable_compression=False  # Don't compress images
)
```

---

## Common Migration Patterns

### Pattern 1: Basic Web Application

**Before (any framework):**
```
/static/css/
/static/js/
/static/images/
/uploads/
```

**After (Catzilla):**
```python
app = Catzilla()

# Web assets with aggressive caching
app.mount_static("/static", "./static",
    cache_ttl_seconds=3600,
    enable_compression=True,
    compression_level=8
)

# User uploads with security
app.mount_static("/uploads", "./uploads",
    enable_directory_listing=False,  # Security
    max_file_size=10*1024*1024       # 10MB limit
)
```

### Pattern 2: Media Streaming Platform

**Before:**
```javascript
// Multiple servers for different quality
app.use('/video/hd', express.static('media/hd'));
app.use('/video/sd', express.static('media/sd'));
```

**After (Catzilla):**
```python
# HD videos with large cache
app.mount_static("/video/hd", "./media/hd",
    cache_size_mb=2000,           # 2GB cache
    enable_range_requests=True,   # For streaming
    max_file_size=5*1024*1024*1024  # 5GB files
)

# SD videos with smaller cache
app.mount_static("/video/sd", "./media/sd",
    cache_size_mb=500,
    enable_range_requests=True
)
```

### Pattern 3: CDN-Style Distribution

**Before:**
```python
# Multiple CDN endpoints
app.mount("/cdn/v1", StaticFiles(directory="dist/v1"))
app.mount("/cdn/v2", StaticFiles(directory="dist/v2"))
```

**After (Catzilla):**
```python
# Version-specific CDN endpoints
app.mount_static("/cdn/v1", "./dist/v1",
    cache_ttl_seconds=86400*7,    # 7 days
    compression_level=9           # Maximum compression
)

app.mount_static("/cdn/v2", "./dist/v2",
    cache_ttl_seconds=86400*7,
    compression_level=9
)
```

---

## Performance Migration Checklist

### ✅ Before Migration (Profile Current Setup)
- [ ] Measure current RPS with `ab -n 10000 -c 100`
- [ ] Check memory usage with `top` or `htop`
- [ ] Test file sizes and compression ratios
- [ ] Document current cache hit rates

### ✅ After Migration (Verify Improvements)
- [ ] Re-run same performance tests
- [ ] Compare memory usage (expect 35% reduction)
- [ ] Verify cache effectiveness with debug logs
- [ ] Test all file types (CSS, JS, images, videos)

### ✅ Production Deployment
- [ ] Set `enable_hot_cache=True` for production
- [ ] Configure appropriate `cache_size_mb` for your server
- [ ] Set long `cache_ttl_seconds` for stable assets
- [ ] Disable `enable_directory_listing` for security
- [ ] Monitor performance with Catzilla's built-in profiling

---

## Configuration Equivalents

| Framework | Catzilla Parameter | Description |
|-----------|-------------------|-------------|
| **Nginx `expires`** | `cache_ttl_seconds` | Cache duration |
| **Nginx `gzip_comp_level`** | `compression_level` | Compression level |
| **Apache `ExpiresActive`** | `enable_hot_cache` | Enable caching |
| **Express `maxAge`** | `cache_ttl_seconds` | Cache max age |
| **Express `etag`** | `enable_etags` | ETag headers |
| **Express `index`** | `index_file` | Directory index |

---

## Migration Benefits Summary

### 🚀 Performance Gains
- **400,000+ RPS** vs competitors' 30-50k RPS
- **35% less memory** usage compared to Python alternatives
- **Sub-millisecond latency** for hot cached files

### 🛠️ Operational Benefits
- **Single binary deployment** - no complex server configurations
- **Hot reloading** - instant updates during development
- **Unified logging** - all requests in one place
- **Built-in monitoring** - performance metrics included

### 💰 Cost Savings
- **Fewer servers needed** due to higher performance
- **Reduced bandwidth** costs from built-in compression
- **Lower operational overhead** with simplified deployment

**Ready to migrate?** Start with our [Quick Start Guide](static_file_server.md#quick-start) and see the performance difference immediately!
