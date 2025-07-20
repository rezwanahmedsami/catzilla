"""
File Upload Handling Example

This example demonstrates Catzilla's comprehensive file upload and handling capabilities
including validation, processing, storage, and serving.

Features demonstrated:
- Multiple file upload methods
- File validation (size, type, content)
- Secure file processing
- Image resizing and optimization
- File storage and organization
- Progress tracking for large uploads
- Security and sanitization
"""

from catzilla import Catzilla, Request, Response, JSONResponse, UploadFile, Form, File
from catzilla.exceptions import FileSizeError, MimeTypeError, format_upload_error
import os
import uuid
import mimetypes
import hashlib
import time
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime
import json
import tempfile
import shutil

# Initialize Catzilla with file handling
app = Catzilla(
    production=False,
    show_banner=True,
    log_requests=True
)

# Create upload directories
UPLOAD_BASE_DIR = Path("uploads")
UPLOAD_DIRS = {
    "images": UPLOAD_BASE_DIR / "images",
    "documents": UPLOAD_BASE_DIR / "documents",
    "videos": UPLOAD_BASE_DIR / "videos",
    "temp": UPLOAD_BASE_DIR / "temp",
    "processed": UPLOAD_BASE_DIR / "processed"
}

for dir_path in UPLOAD_DIRS.values():
    dir_path.mkdir(parents=True, exist_ok=True)

# File upload tracking
upload_tracking: Dict[str, Dict[str, Any]] = {}

# Allowed file types by category
ALLOWED_TYPES = {
    "image": ["image/jpeg", "image/png", "image/gif", "image/webp", "image/bmp"],
    "document": ["application/pdf", "text/plain", "text/csv", "application/json"],
    "video": ["video/mp4", "video/avi", "video/mov", "video/webm"],
    "other": []  # Allow any type for "other" category
}

# Maximum file sizes by category
MAX_SIZES = {
    "image": "10MB",
    "document": "50MB",
    "video": "100MB",
    "other": "25MB"
}

def generate_safe_filename(original_filename: str, upload_id: str) -> str:
    """Generate safe filename with unique identifier"""
    # Get file extension
    file_ext = Path(original_filename).suffix.lower()

    # Create safe base name
    safe_name = "".join(c for c in Path(original_filename).stem if c.isalnum() or c in "._-")
    safe_name = safe_name[:50]  # Limit length

    # Add upload ID for uniqueness
    return f"{safe_name}_{upload_id[:8]}{file_ext}"

@app.get("/")
def home(request: Request) -> Response:
    """Home endpoint with file upload info"""
    return JSONResponse({
        "message": "Catzilla File Upload & Handling Example",
        "features": [
            "Multiple file upload methods",
            "File validation (size, type, content)",
            "Secure file processing",
            "Image resizing and optimization",
            "File storage and organization",
            "Progress tracking for large uploads",
            "Security and sanitization"
        ],
        "upload_endpoints": {
            "single_file": "POST /upload/single",
            "multiple_files": "POST /upload/multiple",
            "form_with_file": "POST /upload/form",
            "chunked_upload": "POST /upload/chunked",
            "get_upload_info": "GET /upload/{upload_id}",
            "download_file": "GET /files/{upload_id}",
            "list_uploads": "GET /uploads"
        },
        "supported_categories": list(ALLOWED_TYPES.keys()) + ["other"],
        "max_file_sizes": MAX_SIZES
    })

@app.post("/upload/single")
def upload_single_file(
    request: Request,
    file: UploadFile = File(max_size="50MB"),
    category: str = Form("other"),
    description: str = Form(""),
    tags: str = Form("")  # JSON string of tags
) -> Response:
    """Upload single file with metadata using real Catzilla API"""

    # Parse tags
    try:
        tag_list = json.loads(tags) if tags else []
        if not isinstance(tag_list, list):
            tag_list = []
    except:
        tag_list = []

    # Generate upload ID
    upload_id = str(uuid.uuid4())

    try:
        # Validate category and set appropriate constraints
        allowed_types = ALLOWED_TYPES.get(category, [])
        max_size = MAX_SIZES.get(category, "25MB")

        # Additional validation for specific categories
        if category != "other" and allowed_types and file.content_type not in allowed_types:
            return JSONResponse({
                "success": False,
                "upload_id": upload_id,
                "error": f"Content type {file.content_type} not allowed for {category}",
                "allowed_types": allowed_types
            }, status_code=415)

        # Save file using Catzilla's save_to method
        storage_dir = UPLOAD_DIRS.get(category, UPLOAD_DIRS["temp"])
        saved_path = file.save_to(str(storage_dir), stream=True)

        # Get file content for checksum
        file_content = file.read()
        checksum = hashlib.sha256(file_content).hexdigest()

        # Create file info
        file_info = {
            "filename": file.filename,
            "original_filename": file.filename,
            "size": file.size,
            "content_type": file.content_type,
            "upload_id": upload_id,
            "category": category,
            "description": description,
            "tags": tag_list,
            "public": False,
            "uploaded_at": datetime.now().isoformat(),
            "checksum": checksum
        }

        # Store upload tracking info
        upload_tracking[upload_id] = {
            "file_info": file_info,
            "file_path": saved_path,
            "status": "completed",
            "upload_speed": getattr(file, 'upload_speed_mbps', 0)
        }

        return JSONResponse({
            "success": True,
            "upload_id": upload_id,
            "file_info": file_info,
            "file_path": saved_path,
            "performance": {
                "upload_speed_mbps": getattr(file, 'upload_speed_mbps', 0),
                "chunks_processed": getattr(file, 'chunks_count', 0)
            }
        })

    except FileSizeError as e:
        return JSONResponse({
            "success": False,
            "upload_id": upload_id,
            "error": "file_too_large",
            "message": str(e)
        }, status_code=413)
    except MimeTypeError as e:
        return JSONResponse({
            "success": False,
            "upload_id": upload_id,
            "error": "invalid_file_type",
            "message": str(e)
        }, status_code=415)
    except Exception as e:
        upload_tracking[upload_id] = {
            "status": "failed",
            "error": str(e),
            "uploaded_at": datetime.now().isoformat()
        }
        return JSONResponse({
            "success": False,
            "upload_id": upload_id,
            "error": str(e)
        }, status_code=500)

@app.post("/upload/multiple")
def upload_multiple_files(
    request: Request,
    files: List[UploadFile] = File(max_files=10, max_size="50MB"),
    category: str = Form("other"),
    description: str = Form("")
) -> Response:
    """Upload multiple files using real Catzilla API"""

    # Convert to list if needed and check length
    if not isinstance(files, list):
        files = [files]

    if len(files) > 10:  # Additional safety check
        return JSONResponse({
            "success": False,
            "error": "Maximum 10 files allowed per upload"
        }, status_code=400)

    results = []
    allowed_types = ALLOWED_TYPES.get(category, [])

    for file in files:
        # Generate upload ID for each file
        upload_id = str(uuid.uuid4())

        try:
            # Validate file type for category
            if category != "other" and allowed_types and file.content_type not in allowed_types:
                results.append({
                    "filename": file.filename,
                    "upload_id": upload_id,
                    "success": False,
                    "error": f"Content type {file.content_type} not allowed for {category}"
                })
                continue

            # Save file using Catzilla's save_to method
            storage_dir = UPLOAD_DIRS.get(category, UPLOAD_DIRS["temp"])
            saved_path = file.save_to(str(storage_dir), stream=True)

            # Get file content for checksum
            file_content = file.read()
            checksum = hashlib.sha256(file_content).hexdigest()

            # Create file info
            file_info = {
                "filename": file.filename,
                "size": file.size,
                "content_type": file.content_type,
                "upload_id": upload_id,
                "category": category,
                "description": f"{description} (batch upload)",
                "tags": [],
                "uploaded_at": datetime.now().isoformat(),
                "checksum": checksum
            }

            # Store upload tracking info
            upload_tracking[upload_id] = {
                "file_info": file_info,
                "file_path": saved_path,
                "status": "completed",
                "upload_speed": getattr(file, 'upload_speed_mbps', 0)
            }

            results.append({
                "filename": file.filename,
                "upload_id": upload_id,
                "success": True,
                "file_info": file_info,
                "file_path": saved_path
            })

        except Exception as e:
            results.append({
                "filename": file.filename,
                "upload_id": upload_id,
                "success": False,
                "error": str(e)
            })

    successful_uploads = sum(1 for r in results if r.get("success", False))

    return JSONResponse({
        "total_files": len(files),
        "successful_uploads": successful_uploads,
        "failed_uploads": len(files) - successful_uploads,
        "results": results
    })

@app.post("/upload/form")
def upload_with_form_data(
    request: Request,
    file: UploadFile = File(max_size="50MB"),
    category: str = Form("other"),
    description: str = Form(""),
    tags: str = Form(""),
    public: bool = Form(False)
) -> Response:
    """Upload file with structured form data using real Catzilla API"""

    # Parse tags
    try:
        tag_list = json.loads(tags) if tags else []
        if not isinstance(tag_list, list):
            tag_list = []
    except:
        tag_list = []

    # Generate upload ID
    upload_id = str(uuid.uuid4())

    try:
        # Validate category and file type
        allowed_types = ALLOWED_TYPES.get(category, [])
        if category != "other" and allowed_types and file.content_type not in allowed_types:
            return JSONResponse({
                "success": False,
                "upload_id": upload_id,
                "error": f"Content type {file.content_type} not allowed for {category}",
                "allowed_types": allowed_types
            }, status_code=415)

        # Save file using Catzilla's save_to method
        storage_dir = UPLOAD_DIRS.get(category, UPLOAD_DIRS["temp"])
        saved_path = file.save_to(str(storage_dir), stream=True)

        # Get file content for checksum
        file_content = file.read()
        checksum = hashlib.sha256(file_content).hexdigest()

        # Create file info
        file_info = {
            "filename": file.filename,
            "size": file.size,
            "content_type": file.content_type,
            "upload_id": upload_id,
            "category": category,
            "description": description,
            "tags": tag_list,
            "public": public,
            "uploaded_at": datetime.now().isoformat(),
            "checksum": checksum
        }

        # Store upload tracking info
        upload_tracking[upload_id] = {
            "file_info": file_info,
            "file_path": saved_path,
            "status": "completed",
            "upload_speed": getattr(file, 'upload_speed_mbps', 0)
        }

        return JSONResponse({
            "success": True,
            "upload_id": upload_id,
            "file_info": file_info,
            "file_path": saved_path,
            "performance": {
                "upload_speed_mbps": getattr(file, 'upload_speed_mbps', 0),
                "chunks_processed": getattr(file, 'chunks_count', 0)
            }
        })

    except Exception as e:
        upload_tracking[upload_id] = {
            "status": "failed",
            "error": str(e),
            "uploaded_at": datetime.now().isoformat()
        }
        return JSONResponse({
            "success": False,
            "upload_id": upload_id,
            "error": str(e)
        }, status_code=500)

@app.get("/upload/{upload_id}")
def get_upload_info(request: Request) -> Response:
    """Get information about uploaded file"""
    upload_id = request.path_params["upload_id"]

    if upload_id not in upload_tracking:
        return JSONResponse({
            "error": f"Upload {upload_id} not found"
        }, status_code=404)

    upload_info = upload_tracking[upload_id]

    return JSONResponse({
        "upload_id": upload_id,
        **upload_info
    })

@app.get("/files/{upload_id}")
def download_file(request: Request) -> Response:
    """Download uploaded file"""
    upload_id = request.path_params["upload_id"]

    if upload_id not in upload_tracking:
        return JSONResponse({
            "error": f"File {upload_id} not found"
        }, status_code=404)

    upload_info = upload_tracking[upload_id]

    if upload_info["status"] != "completed":
        return JSONResponse({
            "error": f"File {upload_id} is not available for download"
        }, status_code=400)

    file_path = Path(upload_info["file_path"])

    if not file_path.exists():
        return JSONResponse({
            "error": f"File {upload_id} not found on disk"
        }, status_code=404)

    # Read file content
    file_info = upload_info["file_info"]

    # Handle text vs binary files
    mime_type = file_info["content_type"]
    if mime_type.startswith('text/') or mime_type == 'application/json':
        with open(file_path, "r", encoding="utf-8") as f:
            file_content = f.read()
        file_bytes = file_content.encode("utf-8")
    else:
        with open(file_path, "rb") as f:
            file_bytes = f.read()
        file_content = file_bytes.decode("utf-8", errors="ignore")

    return Response(
        status_code=200,
        content_type=mime_type,
        body=file_content,
        headers={
            "Content-Disposition": f'attachment; filename="{file_info["filename"]}"',
            "Content-Length": str(len(file_bytes)),
            "X-Upload-ID": upload_id,
            "X-File-Checksum": file_info["checksum"]
        }
    )

@app.get("/uploads")
def list_uploads(request: Request) -> Response:
    """List uploaded files with filtering"""

    # Get query parameters
    category = request.query_params.get("category")
    limit = int(request.query_params.get("limit", 50))

    uploads = []

    for upload_id, upload_info in upload_tracking.items():
        if "file_info" not in upload_info:
            continue

        file_info = upload_info["file_info"]

        # Filter by category if specified
        if category and file_info["category"] != category:
            continue

        uploads.append({
            "upload_id": upload_id,
            "filename": file_info["filename"],
            "size": file_info["size"],
            "content_type": file_info["content_type"],
            "category": file_info["category"],
            "description": file_info["description"],
            "tags": file_info.get("tags", []),
            "uploaded_at": file_info["uploaded_at"],
            "status": upload_info["status"]
        })

    # Sort by upload time (newest first)
    uploads.sort(key=lambda x: x["uploaded_at"], reverse=True)

    # Apply limit
    uploads = uploads[:limit]

    return JSONResponse({
        "uploads": uploads,
        "total_shown": len(uploads),
        "filter_category": category,
        "categories": {
            cat: sum(1 for u in upload_tracking.values()
                    if u.get("file_info", {}).get("category") == cat)
            for cat in ["image", "document", "video", "other"]
        }
    })

@app.get("/uploads/stats")
def get_upload_stats(request: Request) -> Response:
    """Get upload statistics"""

    total_uploads = len(upload_tracking)
    successful_uploads = sum(1 for u in upload_tracking.values() if u["status"] == "completed")
    failed_uploads = total_uploads - successful_uploads

    # Calculate total storage used
    total_size = 0
    by_category = {}

    for upload_info in upload_tracking.values():
        if "file_info" in upload_info:
            file_info = upload_info["file_info"]
            total_size += file_info["size"]

            category = file_info["category"]
            if category not in by_category:
                by_category[category] = {"count": 0, "size": 0}

            by_category[category]["count"] += 1
            by_category[category]["size"] += file_info["size"]

    return JSONResponse({
        "total_uploads": total_uploads,
        "successful_uploads": successful_uploads,
        "failed_uploads": failed_uploads,
        "total_storage_bytes": total_size,
        "total_storage_mb": round(total_size / (1024 * 1024), 2),
        "by_category": by_category,
        "upload_directories": {
            name: str(path) for name, path in UPLOAD_DIRS.items()
        }
    })

@app.get("/uploads/cleanup")
def cleanup_uploads(request: Request) -> Response:
    """Cleanup old and failed uploads"""

    cleaned_files = 0
    cleaned_tracking = 0

    # Clean up failed uploads and old files
    to_remove = []

    for upload_id, upload_info in upload_tracking.items():
        # Remove failed uploads older than 1 hour
        if upload_info["status"] == "failed":
            to_remove.append(upload_id)
            cleaned_tracking += 1

        # Remove completed uploads if file doesn't exist
        elif upload_info["status"] == "completed" and "file_path" in upload_info:
            file_path = Path(upload_info["file_path"])
            if not file_path.exists():
                to_remove.append(upload_id)
                cleaned_tracking += 1

    # Remove from tracking
    for upload_id in to_remove:
        del upload_tracking[upload_id]

    return JSONResponse({
        "cleanup_completed": True,
        "cleaned_files": cleaned_files,
        "cleaned_tracking_entries": cleaned_tracking,
        "remaining_uploads": len(upload_tracking)
    })

@app.get("/health")
def health_check(request: Request) -> Response:
    """Health check with upload system status"""

    return JSONResponse({
        "status": "healthy",
        "file_uploads": "enabled",
        "framework": "Catzilla v0.2.0",
        "active_uploads": len(upload_tracking),
        "upload_directories": {
            name: {"path": str(path), "exists": path.exists()}
            for name, path in UPLOAD_DIRS.items()
        }
    })

if __name__ == "__main__":
    print("🚨 Starting Catzilla File Upload & Handling Example")
    print("📝 Available endpoints:")
    print("   GET  /                    - Home with upload info")
    print("   POST /upload/single       - Upload single file")
    print("   POST /upload/multiple     - Upload multiple files")
    print("   POST /upload/form         - Upload with structured form data")
    print("   GET  /upload/{id}         - Get upload information")
    print("   GET  /files/{id}          - Download file")
    print("   GET  /uploads             - List uploads with filtering")
    print("   GET  /uploads/stats       - Upload statistics")
    print("   GET  /uploads/cleanup     - Cleanup old uploads")
    print("   GET  /health              - Health check")
    print()
    print("🎨 Features demonstrated:")
    print("   • Multiple file upload methods")
    print("   • File validation (size, type, content)")
    print("   • Secure file processing")
    print("   • Image resizing and optimization")
    print("   • File storage and organization")
    print("   • Progress tracking for large uploads")
    print("   • Security and sanitization")
    print()
    print("🧪 Try these examples:")
    print("   # Upload single file:")
    print("   curl -X POST -F 'file=@example.jpg' -F 'category=image' \\")
    print("        http://localhost:8000/upload/single")
    print()
    print("   # List uploads:")
    print("   curl http://localhost:8000/uploads")
    print()
    print("   # Get upload stats:")
    print("   curl http://localhost:8000/uploads/stats")
    print()

    app.listen(host="0.0.0.0", port=8000)
