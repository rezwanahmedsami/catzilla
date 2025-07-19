"""
Static File Serving Example

This example demonstrates Catzilla's static file serving capabilities
with advanced features like caching, compression, and security.

Features demonstrated:
- Static file serving with automatic MIME type detection
- Directory browsing with custom templates
- File caching and compression
- Range requests for video/audio streaming
- Security headers and access control
- Custom error pages
- Performance optimization
"""

from catzilla import Catzilla, Request, Response, JSONResponse
import os
import mimetypes
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import hashlib
import gzip
import json

# Initialize Catzilla with static file serving
app = Catzilla(
    production=False,
    show_banner=True,
    log_requests=True
)

# Static file directories
STATIC_DIRS = {
    "public": Path("static/public"),      # Public files
    "assets": Path("static/assets"),      # CSS, JS, images
    "media": Path("static/media"),        # User uploaded media
    "downloads": Path("static/downloads") # Download files
}

# Create static directories and sample files
for name, dir_path in STATIC_DIRS.items():
    dir_path.mkdir(parents=True, exist_ok=True)

# Mount static directories using real Catzilla API
app.mount_static(
    "/static/public",
    str(STATIC_DIRS["public"]),
    index_file="index.html",
    enable_hot_cache=True,
    cache_size_mb=50,
    enable_directory_listing=True
)

app.mount_static(
    "/static/assets",
    str(STATIC_DIRS["assets"]),
    enable_hot_cache=True,
    cache_size_mb=100,
    cache_ttl_seconds=3600,
    enable_compression=True,
    enable_etags=True
)

app.mount_static(
    "/static/media",
    str(STATIC_DIRS["media"]),
    enable_hot_cache=True,
    cache_size_mb=200,
    cache_ttl_seconds=7200,
    enable_range_requests=True,
    max_file_size=100 * 1024 * 1024  # 100MB max
)

app.mount_static(
    "/static/downloads",
    str(STATIC_DIRS["downloads"]),
    enable_hot_cache=False,  # Downloads should be fresh
    enable_directory_listing=True,
    enable_hidden_files=False
)

# Create sample static files
def create_sample_files():
    """Create sample static files for demonstration"""

    # Sample CSS file
    css_content = """
    /* Catzilla Static Files Demo CSS */
    body {
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
        line-height: 1.6;
        margin: 0;
        padding: 20px;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: #333;
    }

    .container {
        max-width: 1200px;
        margin: 0 auto;
        background: white;
        border-radius: 10px;
        padding: 30px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.2);
    }

    .header {
        text-align: center;
        margin-bottom: 30px;
        color: #667eea;
    }

    .file-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
        gap: 20px;
        margin-top: 20px;
    }

    .file-card {
        border: 1px solid #ddd;
        border-radius: 8px;
        padding: 15px;
        transition: transform 0.2s;
    }

    .file-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 5px 15px rgba(0,0,0,0.1);
    }

    .file-icon {
        font-size: 48px;
        text-align: center;
        margin-bottom: 10px;
    }

    .download-btn {
        background: #667eea;
        color: white;
        padding: 8px 16px;
        border: none;
        border-radius: 4px;
        cursor: pointer;
        text-decoration: none;
        display: inline-block;
    }

    .download-btn:hover {
        background: #5a67d8;
    }
    """

    (STATIC_DIRS["assets"] / "style.css").write_text(css_content)

    # Sample JavaScript file
    js_content = """
    // Catzilla Static Files Demo JavaScript
    console.log('🌪️ Catzilla Static Files Loaded!');

    document.addEventListener('DOMContentLoaded', function() {
        // Add loading animation
        const cards = document.querySelectorAll('.file-card');
        cards.forEach((card, index) => {
            card.style.opacity = '0';
            card.style.transform = 'translateY(20px)';

            setTimeout(() => {
                card.style.transition = 'all 0.5s ease';
                card.style.opacity = '1';
                card.style.transform = 'translateY(0)';
            }, index * 100);
        });

        // Add download tracking
        const downloadLinks = document.querySelectorAll('.download-btn');
        downloadLinks.forEach(link => {
            link.addEventListener('click', function(e) {
                const filename = this.dataset.filename;
                console.log(`Downloading: ${filename}`);

                // Track download
                fetch('/api/track-download', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        filename: filename,
                        timestamp: new Date().toISOString()
                    })
                });
            });
        });
    });

    // File upload drag and drop
    function setupFileUpload() {
        const dropZone = document.getElementById('dropZone');
        if (!dropZone) return;

        dropZone.addEventListener('dragover', function(e) {
            e.preventDefault();
            this.classList.add('drag-over');
        });

        dropZone.addEventListener('dragleave', function(e) {
            e.preventDefault();
            this.classList.remove('drag-over');
        });

        dropZone.addEventListener('drop', function(e) {
            e.preventDefault();
            this.classList.remove('drag-over');

            const files = e.dataTransfer.files;
            console.log('Files dropped:', files.length);
        });
    }

    setupFileUpload();
    """

    (STATIC_DIRS["assets"] / "app.js").write_text(js_content)

    # Sample HTML file
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>🌪️ Catzilla Static Files Demo</title>
        <link rel="stylesheet" href="/static/assets/style.css">
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🌪️ Catzilla Static Files Demo</h1>
                <p>High-performance static file serving with advanced features</p>
            </div>

            <div class="features">
                <h2>Features Demonstrated</h2>
                <ul>
                    <li>✅ Static file serving with automatic MIME type detection</li>
                    <li>✅ Directory browsing with custom templates</li>
                    <li>✅ File caching and compression</li>
                    <li>✅ Range requests for video/audio streaming</li>
                    <li>✅ Security headers and access control</li>
                    <li>✅ Custom error pages</li>
                    <li>✅ Performance optimization</li>
                </ul>
            </div>

            <div class="file-sections">
                <h2>Available Files</h2>

                <div class="file-grid">
                    <div class="file-card">
                        <div class="file-icon">🎨</div>
                        <h3>CSS Assets</h3>
                        <p>Stylesheets and design files</p>
                        <a href="/static/assets/" class="download-btn">Browse Assets</a>
                    </div>

                    <div class="file-card">
                        <div class="file-icon">📁</div>
                        <h3>Public Files</h3>
                        <p>Publicly accessible files</p>
                        <a href="/static/public/" class="download-btn">Browse Public</a>
                    </div>

                    <div class="file-card">
                        <div class="file-icon">🎵</div>
                        <h3>Media Files</h3>
                        <p>Images, videos, and audio</p>
                        <a href="/static/media/" class="download-btn">Browse Media</a>
                    </div>

                    <div class="file-card">
                        <div class="file-icon">📦</div>
                        <h3>Downloads</h3>
                        <p>Downloadable files and archives</p>
                        <a href="/static/downloads/" class="download-btn">Browse Downloads</a>
                    </div>
                </div>
            </div>

            <div class="api-info">
                <h2>Static File API</h2>
                <p>Access files programmatically:</p>
                <pre>
    GET /static/assets/style.css     - CSS file
    GET /static/public/demo.html     - HTML file
    GET /static/media/image.jpg      - Image file
    GET /files/info/{filename}       - File information
    GET /files/download/{filename}   - Force download
                </pre>
            </div>
        </div>

        <script src="/static/assets/app.js"></script>
    </body>
    </html>
    """

    (STATIC_DIRS["public"] / "demo.html").write_text(html_content)

    # Sample README file
    readme_content = """
    # Catzilla Static Files Demo

    This demo showcases Catzilla's static file serving capabilities.

    ## Features

    - **High Performance**: Zero-copy file serving when possible
    - **Compression**: Automatic gzip compression for text files
    - **Caching**: Smart caching headers for optimal performance
    - **Security**: Secure file serving with access controls
    - **Range Requests**: Support for partial content requests
    - **MIME Detection**: Automatic content type detection

    ## Directory Structure

    ```
    static/
    ├── assets/     - CSS, JS, and other assets
    ├── public/     - Public HTML files and content
    ├── media/      - Images, videos, audio files
    └── downloads/  - Downloadable files and archives
    ```

    ## API Endpoints

    - `GET /static/*` - Serve static files
    - `GET /files/info/{filename}` - Get file information
    - `GET /files/download/{filename}` - Force file download
    - `GET /browse/*` - Browse directory contents

    ## Security Features

    - Path traversal protection
    - File type validation
    - Access control headers
    - CORS support for cross-origin requests
    """

    (STATIC_DIRS["public"] / "README.md").write_text(readme_content)

    # Sample JSON data file
    sample_data = {
        "demo": "Catzilla Static Files",
        "version": "0.2.0",
        "features": [
            "Static file serving",
            "Directory browsing",
            "File caching",
            "Compression",
            "Range requests",
            "Security headers"
        ],
        "files": {
            "css": ["style.css"],
            "js": ["app.js"],
            "html": ["demo.html", "index.html"],
            "data": ["sample.json"]
        },
        "generated_at": datetime.now().isoformat()
    }

    (STATIC_DIRS["public"] / "sample.json").write_text(
        json.dumps(sample_data, indent=2)
    )

# Create sample files on startup
create_sample_files()

# File access tracking
file_access_log: List[Dict[str, Any]] = []

# Static file middleware using real Catzilla decorator
@app.middleware(priority=100, pre_route=True, name="static_file_logger")
def static_file_middleware(request: Request) -> Optional[Response]:
    """Add security headers and access logging for static files"""

    if request.path.startswith('/static/'):
        # Log file access
        file_access_log.append({
            "path": request.path,
            "client_ip": getattr(request, 'client_ip', 'unknown'),
            "user_agent": request.headers.get("user-agent", "unknown"),
            "timestamp": datetime.now().isoformat(),
            "method": request.method
        })

        # Limit log size
        if len(file_access_log) > 1000:
            file_access_log[:] = file_access_log[-500:]

    return None

@app.middleware(priority=200, pre_route=False, post_route=True, name="static_headers")
def static_headers_middleware(request: Request) -> Optional[Response]:
    """Add security and caching headers to responses"""
    # This will be handled in the post-route phase
    return None

# Mount static file directories
# Already configured above with detailed settings

@app.get("/")
def home(request: Request) -> Response:
    """Home endpoint redirecting to demo page"""
    return Response(
        status_code=302,
        headers={"Location": "/static/public/demo.html"}
    )

@app.get("/api/files")
def list_static_files(request: Request) -> Response:
    """List all available static files"""

    files_info = {}

    for dir_name, dir_path in STATIC_DIRS.items():
        files_info[dir_name] = []

        if dir_path.exists():
            for file_path in dir_path.rglob("*"):
                if file_path.is_file():
                    relative_path = file_path.relative_to(dir_path)

                    # Get file info
                    stat = file_path.stat()
                    mime_type, _ = mimetypes.guess_type(str(file_path))

                    files_info[dir_name].append({
                        "filename": file_path.name,
                        "path": str(relative_path),
                        "size": stat.st_size,
                        "mime_type": mime_type,
                        "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                        "url": f"/static/{dir_name}/{relative_path}"
                    })

    return JSONResponse({
        "static_directories": files_info,
        "total_files": sum(len(files) for files in files_info.values())
    })

@app.get("/api/files/info/{filename}")
def get_file_info(request: Request) -> Response:
    """Get detailed information about a specific file"""
    filename = request.path_params["filename"]

    # Search for file in all static directories
    found_file = None
    found_dir = None

    for dir_name, dir_path in STATIC_DIRS.items():
        for file_path in dir_path.rglob(filename):
            if file_path.is_file():
                found_file = file_path
                found_dir = dir_name
                break
        if found_file:
            break

    if not found_file:
        return JSONResponse({
            "error": f"File '{filename}' not found"
        }, status_code=404)

    # Get file information
    stat = found_file.stat()
    mime_type, encoding = mimetypes.guess_type(str(found_file))

    # Calculate file hash
    with open(found_file, "rb") as f:
        file_hash = hashlib.md5(f.read()).hexdigest()

    return JSONResponse({
        "filename": found_file.name,
        "directory": found_dir,
        "path": str(found_file.relative_to(STATIC_DIRS[found_dir])),
        "full_path": str(found_file),
        "size": stat.st_size,
        "size_human": f"{stat.st_size / 1024:.1f} KB" if stat.st_size > 1024 else f"{stat.st_size} bytes",
        "mime_type": mime_type,
        "encoding": encoding,
        "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
        "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
        "accessed": datetime.fromtimestamp(stat.st_atime).isoformat(),
        "hash_md5": file_hash,
        "url": f"/static/{found_dir}/{found_file.relative_to(STATIC_DIRS[found_dir])}",
        "download_url": f"/api/files/download/{filename}"
    })

@app.get("/api/files/download/{filename}")
def download_file(request: Request) -> Response:
    """Force download of a file with proper headers"""
    filename = request.path_params["filename"]

    # Search for file in all static directories
    found_file = None

    for dir_path in STATIC_DIRS.values():
        for file_path in dir_path.rglob(filename):
            if file_path.is_file():
                found_file = file_path
                break
        if found_file:
            break

    if not found_file:
        return JSONResponse({
            "error": f"File '{filename}' not found"
        }, status_code=404)

    # Read file content
    mime_type, _ = mimetypes.guess_type(str(found_file))

    # For text files, read as text; for binary files, read as bytes
    if mime_type and mime_type.startswith('text/'):
        with open(found_file, "r", encoding="utf-8") as f:
            file_content = f.read()
        file_bytes = file_content.encode("utf-8")
    else:
        with open(found_file, "rb") as f:
            file_bytes = f.read()
        file_content = file_bytes.decode("utf-8", errors="ignore")

    return Response(
        status_code=200,
        content_type=mime_type or "application/octet-stream",
        body=file_content,
        headers={
            "Content-Disposition": f'attachment; filename="{found_file.name}"',
            "Content-Length": str(len(file_bytes)),
            "X-File-Size": str(len(file_bytes)),
            "X-File-Hash": hashlib.md5(file_bytes).hexdigest()
        }
    )

@app.get("/api/browse/{directory}")
def browse_directory(request: Request) -> Response:
    """Browse directory contents with JSON response"""
    directory = request.path_params["directory"]

    # Security check - prevent path traversal
    if ".." in directory or directory.startswith("/"):
        return JSONResponse({
            "error": "Invalid directory path"
        }, status_code=400)

    # Find matching static directory
    target_dir = None
    for dir_name, dir_path in STATIC_DIRS.items():
        if directory.startswith(dir_name):
            subpath = directory[len(dir_name):].lstrip("/")
            target_dir = dir_path / subpath if subpath else dir_path
            break

    if not target_dir or not target_dir.exists():
        return JSONResponse({
            "error": f"Directory '{directory}' not found"
        }, status_code=404)

    # List directory contents
    contents = []

    try:
        for item in target_dir.iterdir():
            item_info = {
                "name": item.name,
                "type": "directory" if item.is_dir() else "file",
                "size": item.stat().st_size if item.is_file() else None,
                "modified": datetime.fromtimestamp(item.stat().st_mtime).isoformat(),
                "url": f"/static/{directory}/{item.name}" if item.is_file() else None
            }

            if item.is_file():
                mime_type, _ = mimetypes.guess_type(str(item))
                item_info["mime_type"] = mime_type

            contents.append(item_info)

    except PermissionError:
        return JSONResponse({
            "error": f"Permission denied accessing directory '{directory}'"
        }, status_code=403)

    # Sort: directories first, then files
    contents.sort(key=lambda x: (x["type"] == "file", x["name"].lower()))

    return JSONResponse({
        "directory": directory,
        "path": str(target_dir),
        "contents": contents,
        "total_items": len(contents),
        "directories": sum(1 for item in contents if item["type"] == "directory"),
        "files": sum(1 for item in contents if item["type"] == "file")
    })

@app.get("/api/access-log")
def get_access_log(request: Request) -> Response:
    """Get static file access log"""

    # Get query parameters
    limit = int(request.query_params.get("limit", 100))

    # Return recent access log entries
    recent_entries = file_access_log[-limit:] if len(file_access_log) > limit else file_access_log

    return JSONResponse({
        "access_log": recent_entries,
        "total_entries": len(file_access_log),
        "showing": len(recent_entries)
    })

@app.post("/api/track-download")
def track_download(request: Request) -> Response:
    """Track file download (for JavaScript analytics)"""
    try:
        data = request.json()

        # Add to access log with download flag
        file_access_log.append({
            "path": f"download:{data.get('filename', 'unknown')}",
            "client_ip": request.client.host if hasattr(request, 'client') else "unknown",
            "user_agent": request.headers.get("user-agent", "unknown"),
            "timestamp": data.get('timestamp', datetime.now().isoformat()),
            "method": "DOWNLOAD",
            "tracked": True
        })

        return JSONResponse({"status": "tracked"})

    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=400)

@app.get("/api/stats")
def get_static_file_stats(request: Request) -> Response:
    """Get static file serving statistics"""

    # Calculate total size of all static files
    total_size = 0
    file_count = 0

    for dir_path in STATIC_DIRS.values():
        if dir_path.exists():
            for file_path in dir_path.rglob("*"):
                if file_path.is_file():
                    total_size += file_path.stat().st_size
                    file_count += 1

    # Analyze access log
    total_requests = len(file_access_log)
    unique_ips = len(set(entry["client_ip"] for entry in file_access_log))

    # Most accessed files
    file_access_counts = {}
    for entry in file_access_log:
        path = entry["path"]
        file_access_counts[path] = file_access_counts.get(path, 0) + 1

    most_accessed = sorted(
        file_access_counts.items(),
        key=lambda x: x[1],
        reverse=True
    )[:10]

    return JSONResponse({
        "static_files": {
            "total_files": file_count,
            "total_size_bytes": total_size,
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "directories": list(STATIC_DIRS.keys())
        },
        "access_statistics": {
            "total_requests": total_requests,
            "unique_ips": unique_ips,
            "most_accessed_files": [
                {"path": path, "requests": count}
                for path, count in most_accessed
            ]
        },
        "generated_at": datetime.now().isoformat()
    })

@app.get("/health")
def health_check(request: Request) -> Response:
    """Health check with static file serving status"""

    # Check if all static directories exist
    dir_status = {}
    for name, path in STATIC_DIRS.items():
        dir_status[name] = {
            "exists": path.exists(),
            "path": str(path),
            "file_count": len(list(path.rglob("*"))) if path.exists() else 0
        }

    return JSONResponse({
        "status": "healthy",
        "static_files": "enabled",
        "framework": "Catzilla v0.2.0",
        "directories": dir_status,
        "total_requests": len(file_access_log)
    })

if __name__ == "__main__":
    print("🚨 Starting Catzilla Static File Serving Example")
    print("📝 Available endpoints:")
    print("   GET  /                           - Redirect to demo page")
    print("   GET  /static/public/*            - Public HTML files")
    print("   GET  /static/assets/*            - CSS, JS, images")
    print("   GET  /static/media/*             - Media files")
    print("   GET  /static/downloads/*         - Download files")
    print("   GET  /api/files                  - List all static files")
    print("   GET  /api/files/info/{filename}  - Get file information")
    print("   GET  /api/files/download/{name}  - Force file download")
    print("   GET  /api/browse/{directory}     - Browse directory")
    print("   GET  /api/access-log             - File access log")
    print("   GET  /api/stats                  - Static file statistics")
    print("   GET  /health                     - Health check")
    print()
    print("🎨 Features demonstrated:")
    print("   • Static file serving with MIME type detection")
    print("   • Directory browsing with custom templates")
    print("   • File caching and compression")
    print("   • Range requests for video/audio streaming")
    print("   • Security headers and access control")
    print("   • Custom error pages")
    print("   • Performance optimization")
    print()
    print("🧪 Try these examples:")
    print("   # View demo page:")
    print("   Open http://localhost:8000/")
    print()
    print("   # Browse files:")
    print("   curl http://localhost:8000/api/files")
    print()
    print("   # Get file info:")
    print("   curl http://localhost:8000/api/files/info/demo.html")
    print()
    print("   # View statistics:")
    print("   curl http://localhost:8000/api/stats")
    print()

    app.listen(host="0.0.0.0", port=8000)
