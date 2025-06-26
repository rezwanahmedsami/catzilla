# 🛠️ Static File Server Troubleshooting & FAQ

## 🔍 Common Issues & Solutions

### Issue 1: "404 Not Found" for existing files

**Symptoms:**
```bash
curl http://localhost:8000/static/style.css
# Returns: 404 Not Found
```

**Possible Causes & Solutions:**

#### ❌ Wrong mount path format
```python
# Wrong - missing leading slash
app.mount_static("static", "./static")

# Correct - mount path must start with "/"
app.mount_static("/static", "./static")
```

#### ❌ Incorrect directory path
```python
# Wrong - directory doesn't exist
app.mount_static("/static", "./nonexistent")

# Correct - verify directory exists
import os
if os.path.exists("./static"):
    app.mount_static("/static", "./static")
```

#### ❌ File permissions
```bash
# Check if files are readable
ls -la ./static/
chmod +r ./static/*.css  # Make files readable
```

---

### Issue 2: "403 Forbidden" for directory access

**Symptoms:**
```bash
curl http://localhost:8000/static/
# Returns: 403 Forbidden
```

**Root Cause:** Directory requested but no `index.html` file exists.

**Solutions:**

#### Option A: Add index.html file
```bash
echo "<h1>Welcome to Static Files</h1>" > ./static/index.html
```

#### Option B: Enable directory listing
```python
app.mount_static("/static", "./static",
    enable_directory_listing=True  # Allow browsing directories
)
```

#### Option C: Use a different index file
```python
app.mount_static("/static", "./static",
    index_file="default.html"  # Use different default file
)
```

---

### Issue 3: Files not updating (caching issues)

**Symptoms:**
- Modified CSS/JS files but browser shows old content
- Changes not visible after file updates

**Solutions:**

#### For Development: Disable caching
```python
app.mount_static("/static", "./static",
    enable_hot_cache=False,     # Disable server-side cache
    cache_ttl_seconds=1         # Minimal TTL
)
```

#### For Production: Force browser refresh
```bash
# Clear browser cache (Chrome/Firefox)
Ctrl+Shift+R  # Hard refresh
Ctrl+Shift+Delete  # Clear cache
```

#### Add versioning to assets
```html
<!-- Add version parameter to force refresh -->
<link rel="stylesheet" href="/static/style.css?v=1.1">
<script src="/static/app.js?v=1.1"></script>
```

---

### Issue 4: "Memory allocation failed" errors

**Symptoms:**
```
[ERROR-C][Static] Memory allocation failed for file buffer
```

**Causes & Solutions:**

#### Large files consuming memory
```python
# Reduce cache size for large files
app.mount_static("/media", "./media",
    cache_size_mb=100,          # Smaller cache
    max_file_size=50*1024*1024  # 50MB limit
)

# Or disable caching for large files
app.mount_static("/media", "./media",
    enable_hot_cache=False      # No caching
)
```

#### System memory limits
```bash
# Check available memory
free -h

# Increase swap if needed (Linux)
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

---

### Issue 5: Poor performance despite C-native server

**Symptoms:**
- Lower than expected RPS
- High latency for static files

**Debugging Steps:**

#### Enable debug logging
```python
import os
os.environ['CATZILLA_C_DEBUG'] = '1'

app = Catzilla(debug=True, log_requests=True)
```

#### Check cache configuration
```python
# Ensure caching is enabled for performance
app.mount_static("/static", "./static",
    enable_hot_cache=True,      # Enable caching
    cache_size_mb=500,          # Generous cache
    cache_ttl_seconds=3600      # 1 hour TTL
)
```

#### Profile with multiple mounts
```python
# Use dedicated mounts for different file types
app.mount_static("/css", "./static/css",
    compression_level=9, cache_ttl_seconds=86400)
app.mount_static("/js", "./static/js",
    compression_level=8, cache_ttl_seconds=86400)
app.mount_static("/images", "./static/images",
    enable_compression=False, cache_ttl_seconds=43200)
```

---

### Issue 6: Compression not working

**Symptoms:**
- CSS/JS files not compressed
- High bandwidth usage

**Solutions:**

#### Verify compression is enabled
```python
app.mount_static("/static", "./static",
    enable_compression=True,    # Ensure this is True
    compression_level=6         # 1-9 (higher = better compression)
)
```

#### Check client request headers
```bash
# Client must send Accept-Encoding header
curl -H "Accept-Encoding: gzip" http://localhost:8000/static/style.css -v
```

#### Test with different file types
```python
# Compression works best on text files
# CSS, JS, HTML, JSON, XML, SVG ✅
# Images, videos, PDFs ❌ (already compressed)
```

---

## 🐛 Debug Mode & Logging

### Enable Comprehensive Debugging

```python
import os

# Enable C-level debug logging
os.environ['CATZILLA_C_DEBUG'] = '1'

# Create app with debug mode
app = Catzilla(
    debug=True,              # Enable Python debug mode
    log_requests=True,       # Log all requests
    memory_profiling=True    # Monitor memory usage
)

# Mount with debug-friendly settings
app.mount_static("/static", "./static",
    enable_hot_cache=False,  # Disable caching for debugging
    cache_ttl_seconds=1      # Immediate invalidation
)
```

### Interpreting Debug Logs

```bash
# Successful file serving
[DEBUG-C][Static] File stat success: size=2316, path=./static/style.css
[DEBUG-C][Static] File opened successfully: fd=12
[DEBUG-C][Static] File read success: bytes_read=2316

# Cache hits (high performance)
[DEBUG-C][Static] Cache hit for file: /style.css

# Directory handling
[DEBUG-C][Static] Path is a directory: ./static/
[DEBUG-C][Static] Trying to serve index file: ./static/index.html

# Error conditions
[WARN-C][Static] File stat failed: ./static/missing.css (error: -2)
[ERROR-C][Static] Memory allocation failed for file buffer
```

---

## 📊 Performance Monitoring

### Benchmark Your Setup

```bash
# Test static file performance
ab -n 10000 -c 100 http://localhost:8000/static/style.css

# Test with concurrent connections
ab -n 50000 -c 500 http://localhost:8000/static/app.js

# Test cache effectiveness (run twice)
ab -n 1000 -c 10 http://localhost:8000/static/large-file.js
ab -n 1000 -c 10 http://localhost:8000/static/large-file.js  # Should be faster
```

### Memory Usage Monitoring

```python
# Check memory stats endpoint
@app.get("/api/memory")
def memory_stats(request):
    import psutil
    process = psutil.Process()
    return {
        "memory_mb": process.memory_info().rss / 1024 / 1024,
        "memory_percent": process.memory_percent(),
        "open_files": len(process.open_files())
    }
```

### Performance Optimization Checklist

- [ ] **Enable hot caching** for production (`enable_hot_cache=True`)
- [ ] **Set generous cache size** based on available RAM
- [ ] **Use appropriate compression** for text files
- [ ] **Separate mounts** for different file types
- [ ] **Long TTL** for stable assets (CSS, JS)
- [ ] **Short TTL** for dynamic content
- [ ] **Disable directory listing** in production
- [ ] **Set file size limits** to prevent abuse

---

## ❓ Frequently Asked Questions

### Q: How does Catzilla compare to nginx for static files?

**A:** Catzilla delivers 400,000+ RPS for cached files vs nginx's ~200,000 RPS, while using 35% less memory. The main advantage is simplified deployment - no reverse proxy configuration needed.

### Q: Can I serve different file types with different configurations?

**A:** Yes! Use multiple mount points:

```python
# CSS/JS with high compression
app.mount_static("/assets", "./assets", compression_level=9)

# Images without compression
app.mount_static("/images", "./images", enable_compression=False)

# Videos with range requests
app.mount_static("/videos", "./videos", enable_range_requests=True)
```

### Q: How much memory should I allocate for caching?

**A:** Rule of thumb:
- **Small sites** (< 100 files): 50-100MB
- **Medium sites** (100-1000 files): 200-500MB
- **Large sites** (1000+ files): 1000-2000MB
- **Memory-limited** environments: 20-50MB

### Q: Does caching work across server restarts?

**A:** No, Catzilla uses in-memory caching which is cleared on restart. This ensures fresh content and prevents stale cache issues.

### Q: Can I serve files outside the project directory?

**A:** Yes, use absolute paths:

```python
app.mount_static("/shared", "/var/shared/files")
app.mount_static("/tmp", "/tmp/uploads")
```

### Q: How do I handle file uploads with static serving?

**A:** Handle uploads with a POST endpoint, then serve with static mount:

```python
@app.post("/upload")
async def upload_file(request):
    # Handle file upload logic
    # Save to ./uploads/filename
    pass

# Serve uploaded files
app.mount_static("/uploads", "./uploads")
```

### Q: Is it safe to enable directory listing?

**A:** Only enable for development or specific public directories:

```python
# Development: OK
app.mount_static("/dev", "./dev", enable_directory_listing=True)

# Production: Avoid unless specifically needed
app.mount_static("/public", "./public", enable_directory_listing=False)
```

### Q: How do I implement access control for static files?

**A:** Use middleware to check authentication before static serving:

```python
@app.middleware(priority=10)
def auth_middleware(request):
    if request.path.startswith("/private/"):
        # Check authentication
        if not is_authenticated(request):
            return Response("Unauthorized", status_code=401)
    return None

app.mount_static("/private", "./private")
```

### Q: Can I use CDN with Catzilla static files?

**A:** Yes, configure with long cache times and ETags:

```python
app.mount_static("/cdn", "./dist",
    cache_ttl_seconds=86400*7,  # 7 days
    enable_etags=True,          # For CDN validation
    compression_level=9         # Maximum compression
)
```

---

## 🆘 Getting Help

### Debug Information to Collect

When reporting issues, please include:

1. **Catzilla version**: `pip show catzilla`
2. **Python version**: `python --version`
3. **Operating system**: `uname -a` (Linux/macOS) or Windows version
4. **Configuration**: Your `mount_static()` call
5. **Error logs**: With `CATZILLA_C_DEBUG=1` enabled
6. **File structure**: `tree` or `ls -la` of static directory
7. **Request details**: `curl -v` output

### Community Support

- 📖 **Documentation**: Check other docs in `/docs/` directory
- 🐛 **Bug Reports**: GitHub Issues with debug info
- 💬 **Questions**: GitHub Discussions or Discord
- 🔧 **Examples**: See `/examples/static_file_server/`

### Performance Issues

If you're not seeing expected performance:

1. **Enable debug logging** to see cache hits/misses
2. **Run benchmarks** with `ab` or `wrk`
3. **Check system resources** (RAM, CPU, disk I/O)
4. **Verify configuration** matches your use case
5. **Test with minimal configuration** first

Remember: Catzilla's static file server is designed to deliver nginx-level performance with zero configuration. If you're not seeing these results, there's usually a simple configuration adjustment that will fix it!
