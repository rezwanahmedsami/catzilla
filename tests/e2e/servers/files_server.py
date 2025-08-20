#!/usr/bin/env python3
"""
E2E Test Server for File Operations

This server mirrors examples/files/ for E2E testing.
It provides file upload, download, and serving functionality to be tested via HTTP.
"""
import sys
import argparse
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from catzilla import Catzilla, Request, Response, JSONResponse, BaseModel
from typing import Optional
import time
import json

# Initialize Catzilla for E2E testing
app = Catzilla(
    production=False,
    show_banner=False,
    log_requests=False
)

# File operations tracking
file_operations = []
upload_directory = Path(__file__).parent / "uploads"
upload_directory.mkdir(exist_ok=True)

# Pydantic models
class FileInfo(BaseModel):
    """File information model"""
    filename: str
    size: int
    content_type: str = "application/octet-stream"

class UploadResponse(BaseModel):
    """File upload response model"""
    success: bool
    filename: str
    size: int
    path: str
    upload_time: float

# ============================================================================
# STATIC FILE SERVING
# ============================================================================

# Configure static file serving
static_dir = Path(__file__).parent / "static"
static_dir.mkdir(exist_ok=True)

# Create some test static files
(static_dir / "test.txt").write_text("This is a test file for static serving")
(static_dir / "data.json").write_text('{"message": "Hello from static JSON file"}')
(static_dir / "style.css").write_text("body { color: blue; }")

# Set up static file serving
app.mount_static("/static", str(static_dir))

# ============================================================================
# ROUTES
# ============================================================================

# Health check
@app.get("/health")
def health_check(request: Request) -> Response:
    """Health check endpoint"""
    return JSONResponse({
        "status": "healthy",
        "server": "files_e2e_test",
        "timestamp": time.time(),
        "upload_directory": str(upload_directory),
        "static_directory": str(static_dir),
        "operations_count": len(file_operations)
    })

# Basic info
@app.get("/")
def home(request: Request) -> Response:
    """File operations test server info"""
    return JSONResponse({
        "message": "Catzilla E2E File Operations Test Server",
        "features": [
            "Static file serving",
            "File upload",
            "File download",
            "File listing",
            "File metadata"
        ],
        "endpoints": [
            "GET /static/<path> (static files)",
            "POST /upload (file upload)",
            "GET /files (list files)",
            "GET /files/<filename> (download file)",
            "GET /files/<filename>/info (file metadata)",
            "DELETE /files/<filename> (delete file)"
        ],
        "upload_directory": str(upload_directory),
        "static_directory": str(static_dir)
    })

# ============================================================================
# FILE UPLOAD
# ============================================================================

@app.post("/upload")
def upload_file(request: Request) -> Response:
    """Upload a file"""
    try:
        # Get uploaded files from request
        files = request.files

        if not files:
            return JSONResponse({
                "error": "No file uploaded",
                "message": "Request must contain a file"
            }, status_code=400)

        # Get the file info from the 'file' field
        file_info = files.get('file')
        if not file_info:
            return JSONResponse({
                "error": "No file in request",
                "message": f"Request must contain a 'file' field. Available fields: {list(files.keys())}"
            }, status_code=400)

        # Extract file details
        filename = file_info.get('filename') or "unnamed_file"
        content_type = file_info.get('content_type', 'application/octet-stream')
        is_streamed = file_info.get('is_streamed', False)

        # Get file content
        if is_streamed:
            # Large file in temp path
            temp_path = file_info.get('temp_path')
            if not temp_path or not Path(temp_path).exists():
                return JSONResponse({
                    "error": "Temp file not found",
                    "message": "Streamed file temp path is invalid"
                }, status_code=500)

            # Copy from temp file
            file_path = upload_directory / filename
            with open(temp_path, 'rb') as src, open(file_path, 'wb') as dst:
                content = src.read()
                dst.write(content)
        else:
            # Small file in memory
            content = file_info.get('content')
            if content is None:
                return JSONResponse({
                    "error": "No file content",
                    "message": "File content is empty"
                }, status_code=400)

            # Save the file
            file_path = upload_directory / filename
            file_path.write_bytes(content)

        # Track operation
        operation = {
            "type": "upload",
            "filename": filename,
            "size": len(content),
            "timestamp": time.time(),
            "path": str(file_path),
            "content_type": content_type
        }
        file_operations.append(operation)

        return JSONResponse({
            "success": True,
            "message": "File uploaded successfully",
            "filename": filename,
            "size": len(content),
            "path": str(file_path.relative_to(upload_directory)),
            "upload_time": operation["timestamp"]
        }, status_code=201)

    except Exception as e:
        return JSONResponse({
            "error": "Upload failed",
            "message": str(e)
        }, status_code=500)

# ============================================================================
# FILE LISTING
# ============================================================================

@app.get("/files")
def list_files(request: Request) -> Response:
    """List all uploaded files"""
    try:
        files = []
        for file_path in upload_directory.iterdir():
            if file_path.is_file():
                stat = file_path.stat()
                files.append({
                    "filename": file_path.name,
                    "size": stat.st_size,
                    "modified": stat.st_mtime,
                    "path": str(file_path.relative_to(upload_directory))
                })

        return JSONResponse({
            "files": files,
            "total_files": len(files),
            "upload_directory": str(upload_directory)
        })

    except Exception as e:
        return JSONResponse({
            "error": "Failed to list files",
            "message": str(e)
        }, status_code=500)

# ============================================================================
# FILE DOWNLOAD
# ============================================================================

@app.get("/download/{filename}")
def download_file(request):
    filename = request.path_params.get("filename")
    file_path = upload_directory / filename

    if not file_path.exists():
        return JSONResponse({"error": "File not found"}, status_code=404)

    with open(file_path, "rb") as f:
        content = f.read()

    # For Catzilla, we need to handle bytes properly
    # Convert bytes to string for text files, or use base64 for binary
    try:
        # Try to decode as text first
        content_str = content.decode('utf-8')
    except UnicodeDecodeError:
        # If it's binary, we need a different approach
        import base64
        content_str = base64.b64encode(content).decode('ascii')
        headers = {
            "Content-Disposition": f"attachment; filename={filename}",
            "Content-Transfer-Encoding": "base64"
        }
    else:
        headers = {"Content-Disposition": f"attachment; filename={filename}"}

    # Track download operation
    operation = {
        "type": "download",
        "filename": filename,
        "size": len(content),
        "timestamp": time.time()
    }
    file_operations.append(operation)

    return Response(
        status_code=200,
        content_type="application/octet-stream",
        body=content_str,
        headers=headers
    )

# ============================================================================
# FILE METADATA
# ============================================================================

@app.get("/files/{filename}/info")
def file_info(request) -> Response:
    """Get file metadata"""
    try:
        filename = request.path_params.get("filename")
        file_path = upload_directory / filename

        if not file_path.exists():
            return JSONResponse({
                "error": "File not found",
                "filename": filename
            }, status_code=404)

        stat = file_path.stat()

        # Determine content type
        content_type = "application/octet-stream"
        if filename.endswith('.txt'):
            content_type = "text/plain"
        elif filename.endswith('.json'):
            content_type = "application/json"
        elif filename.endswith('.html'):
            content_type = "text/html"

        return JSONResponse({
            "filename": filename,
            "size": stat.st_size,
            "content_type": content_type,
            "created": stat.st_ctime,
            "modified": stat.st_mtime,
            "path": str(file_path.relative_to(upload_directory)),
            "exists": True
        })

    except Exception as e:
        return JSONResponse({
            "error": "Failed to get file info",
            "message": str(e)
        }, status_code=500)

# ============================================================================
# FILE DELETION
# ============================================================================

@app.delete("/files/{filename}")
def delete_file(request) -> Response:
    """Delete a specific file"""
    try:
        filename = request.path_params.get("filename")
        file_path = upload_directory / filename

        if not file_path.exists():
            return JSONResponse({
                "error": "File not found",
                "filename": filename
            }, status_code=404)

        # Get file size before deletion
        file_size = file_path.stat().st_size

        # Delete the file
        file_path.unlink()

        # Track operation
        operation = {
            "type": "delete",
            "filename": filename,
            "size": file_size,
            "timestamp": time.time()
        }
        file_operations.append(operation)

        return JSONResponse({
            "success": True,
            "message": "File deleted successfully",
            "filename": filename,
            "size": file_size
        })

    except Exception as e:
        return JSONResponse({
            "error": "Delete failed",
            "message": str(e)
        }, status_code=500)

# ============================================================================
# OPERATIONS TRACKING
# ============================================================================

@app.get("/operations")
def get_operations(request: Request) -> Response:
    """Get file operations history"""
    return JSONResponse({
        "operations": file_operations,
        "total_operations": len(file_operations),
        "operations_by_type": {
            "upload": len([op for op in file_operations if op["type"] == "upload"]),
            "download": len([op for op in file_operations if op["type"] == "download"]),
            "delete": len([op for op in file_operations if op["type"] == "delete"])
        }
    })

@app.post("/operations/clear")
def clear_operations(request: Request) -> Response:
    """Clear operations history"""
    global file_operations

    cleared_count = len(file_operations)
    file_operations.clear()

    return JSONResponse({
        "message": "Operations history cleared",
        "cleared_operations": cleared_count,
        "timestamp": time.time()
    })

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Catzilla E2E File Operations Test Server")
    parser.add_argument("--port", type=int, default=8106, help="Port to run server on")
    parser.add_argument("--host", type=str, default="127.0.0.1", help="Host to bind to")

    args = parser.parse_args()

    print(f"🚀 Starting Catzilla E2E File Operations Test Server")
    print(f"📍 Server: http://{args.host}:{args.port}")
    print(f"🏥 Health: http://{args.host}:{args.port}/health")
    print(f"📁 Upload Dir: {upload_directory}")
    print(f"📂 Static Dir: {static_dir}")

    app.listen(port=args.port, host=args.host)
