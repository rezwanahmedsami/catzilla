#!/usr/bin/env python3
"""
Simple Static File Server Example

This example demonstrates how easy it is to set up a high-performance
static file server with Catzilla.

Run with: python simple_static_example.py
"""

from catzilla import Catzilla, HTMLResponse
import os

# Create the app
app = Catzilla()

# Create demo files if they don't exist
os.makedirs("./demo_static", exist_ok=True)

# Create index.html
with open("./demo_static/index.html", "w") as f:
    f.write("""<!DOCTYPE html>
<html>
<head>
    <title>Catzilla Static Server Demo</title>
    <link rel="stylesheet" href="style.css">
</head>
<body>
    <h1>🐱 Catzilla Static File Server</h1>
    <p>This page is served by Catzilla's C-native static file server!</p>
    <p><strong>Performance:</strong> 400,000+ RPS for cached files</p>
    <script src="app.js"></script>
</body>
</html>""")

# Create style.css
with open("./demo_static/style.css", "w") as f:
    f.write("""body {
    font-family: Arial, sans-serif;
    max-width: 800px;
    margin: 50px auto;
    padding: 20px;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    border-radius: 10px;
}

h1 { color: #fff; text-align: center; }
p { font-size: 18px; line-height: 1.6; }""")

# Create app.js
with open("./demo_static/app.js", "w") as f:
    f.write("""console.log('🚀 Catzilla static file server loaded!');
console.log('Files served at C-native speed with libuv + jemalloc');

// Show load time
window.addEventListener('load', () => {
    const loadTime = performance.timing.loadEventEnd - performance.timing.navigationStart;
    console.log(`⚡ Page loaded in ${loadTime}ms`);
});""")

# Mount static files with high performance configuration
app.mount_static("/static", "./demo_static",
    enable_hot_cache=True,
    cache_size_mb=100,
    cache_ttl_seconds=3600,
    enable_compression=True,
    compression_level=8,
    enable_etags=True
)

# Add a simple API endpoint
@app.get("/")
def home(request):
    """Redirect to static files"""
    return HTMLResponse("""
    <h1>Catzilla Static File Server Demo</h1>
    <p><a href="/static/">Visit the static site →</a></p>
    <p><a href="/static/style.css">View CSS →</a></p>
    <p><a href="/static/app.js">View JavaScript →</a></p>
    """)

@app.get("/api/info")
def api_info(request):
    """Simple API endpoint"""
    return {
        "message": "Catzilla serves both static files and dynamic APIs!",
        "static_performance": "400,000+ RPS",
        "features": ["Hot caching", "Compression", "ETags", "Range requests"]
    }

if __name__ == "__main__":
    print("🐱 Starting Catzilla Static File Server Demo")
    print("📁 Static files: http://localhost:8000/static/")
    print("🏠 Home page: http://localhost:8000/")
    print("🔗 API endpoint: http://localhost:8000/api/info")
    print("🚀 Press Ctrl+C to stop")

    app.run(host="0.0.0.0", port=8000)
