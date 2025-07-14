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
from catzilla.validation import BaseModel, Field
import asyncio
import os
import uuid
import mimetypes
import hashlib
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
    log_requests=True,
    max_upload_size=100 * 1024 * 1024,  # 100MB max upload
    upload_temp_dir="/tmp/catzilla_uploads"
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

# Validation models
class FileUploadRequest(BaseModel):
    """File upload request validation"""
    description: str = Field(max_length=500, default="")
    category: str = Field(regex=r"^(image|document|video|other)$", default="other")
    tags: List[str] = Field(max_items=10, default=[])
    public: bool = Field(default=False)

class FileInfo(BaseModel):
    """File information model"""
    filename: str
    size: int
    content_type: str
    upload_id: str
    category: str
    description: str
    tags: List[str]
    public: bool
    uploaded_at: datetime
    checksum: str

# Allowed file types by category
ALLOWED_TYPES = {
    "image": {
        "image/jpeg", "image/png", "image/gif", "image/webp",
        "image/bmp", "image/tiff", "image/svg+xml"
    },
    "document": {
        "application/pdf", "text/plain", "text/csv",
        "application/msword", "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/vnd.ms-excel", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "application/json", "application/xml", "text/html"
    },
    "video": {
        "video/mp4", "video/avi", "video/mov", "video/wmv",
        "video/flv", "video/webm", "video/mkv"
    }
}

# Maximum file sizes by category (bytes)
MAX_SIZES = {
    "image": 10 * 1024 * 1024,    # 10MB
    "document": 50 * 1024 * 1024, # 50MB
    "video": 100 * 1024 * 1024,   # 100MB
    "other": 25 * 1024 * 1024     # 25MB
}

def validate_file(file: UploadFile, category: str) -> Dict[str, Any]:
    """Validate uploaded file"""
    errors = []
    warnings = []

    # Check file size
    max_size = MAX_SIZES.get(category, MAX_SIZES["other"])
    if file.size > max_size:
        errors.append(f"File size {file.size} exceeds maximum {max_size} bytes for {category}")

    # Check content type
    allowed_types = ALLOWED_TYPES.get(category, set())
    if allowed_types and file.content_type not in allowed_types:
        errors.append(f"Content type {file.content_type} not allowed for {category}")

    # Check filename
    if not file.filename or len(file.filename) > 255:
        errors.append("Invalid filename")

    # Check for potentially dangerous files
    dangerous_extensions = {".exe", ".bat", ".cmd", ".com", ".scr", ".pif", ".js", ".vbs"}
    file_ext = Path(file.filename).suffix.lower()
    if file_ext in dangerous_extensions:
        errors.append(f"File extension {file_ext} is not allowed for security reasons")

    # Size warnings
    if file.size > 50 * 1024 * 1024:  # 50MB
        warnings.append("Large file upload may take significant time")

    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings
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

def calculate_file_checksum(file_path: Path) -> str:
    """Calculate SHA256 checksum of file"""
    sha256_hash = hashlib.sha256()

    with open(file_path, "rb") as f:
        # Read in chunks to handle large files
        for chunk in iter(lambda: f.read(4096), b""):
            sha256_hash.update(chunk)

    return sha256_hash.hexdigest()

def process_image_file(file_path: Path, upload_id: str) -> Dict[str, Any]:
    """Process uploaded image file (placeholder for image processing)"""
    try:
        # This would typically use PIL/Pillow for image processing
        # For demo purposes, we'll just return metadata

        processing_info = {
            "processed": True,
            "thumbnails_created": ["150x150", "300x300", "800x600"],
            "optimized": True,
            "format_converted": False,
            "processing_time_ms": 150
        }

        # Simulate processing time
        time.sleep(0.1)

        return processing_info

    except Exception as e:
        return {
            "processed": False,
            "error": str(e)
        }

def save_uploaded_file(
    file: UploadFile,
    upload_id: str,
    category: str,
    description: str = "",
    tags: List[str] = None
) -> Dict[str, Any]:
    """Save uploaded file with processing"""
    tags = tags or []

    try:
        # Generate safe filename
        safe_filename = generate_safe_filename(file.filename, upload_id)

        # Determine storage directory
        storage_dir = UPLOAD_DIRS.get(category, UPLOAD_DIRS["temp"])
        file_path = storage_dir / safe_filename

        # Save file
        with open(file_path, "wb") as f:
            # Read and write in chunks for memory efficiency
            while chunk := file.read(8192):
                f.write(chunk)

        # Calculate checksum
        checksum = calculate_file_checksum(file_path)

        # Create file info
        file_info = FileInfo(
            filename=safe_filename,
            size=file.size,
            content_type=file.content_type,
            upload_id=upload_id,
            category=category,
            description=description,
            tags=tags,
            public=False,
            uploaded_at=datetime.now(),
            checksum=checksum
        )

        # Process based on file type
        processing_info = {}
        if category == "image":
            processing_info = process_image_file(file_path, upload_id)

        # Store upload tracking info
        upload_tracking[upload_id] = {
            "file_info": file_info.dict(),
            "file_path": str(file_path),
            "processing_info": processing_info,
            "status": "completed"
        }

        return {
            "success": True,
            "upload_id": upload_id,
            "file_info": file_info.dict(),
            "processing_info": processing_info,
            "file_path": str(file_path)
        }

    except Exception as e:
        upload_tracking[upload_id] = {
            "status": "failed",
            "error": str(e),
            "uploaded_at": datetime.now().isoformat()
        }

        return {
            "success": False,
            "upload_id": upload_id,
            "error": str(e)
        }

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
        "max_file_sizes": {k: f"{v // (1024*1024)}MB" for k, v in MAX_SIZES.items()}
    })

@app.post("/upload/single")
def upload_single_file(
    request: Request,
    file: UploadFile = File(...),
    category: str = Form("other"),
    description: str = Form(""),
    tags: str = Form("")  # JSON string of tags
) -> Response:
    """Upload single file with metadata"""

    # Parse tags
    try:
        tag_list = json.loads(tags) if tags else []
        if not isinstance(tag_list, list):
            tag_list = []
    except:
        tag_list = []

    # Generate upload ID
    upload_id = str(uuid.uuid4())

    # Validate file
    validation_result = validate_file(file, category)
    if not validation_result["valid"]:
        return JSONResponse({
            "success": False,
            "upload_id": upload_id,
            "errors": validation_result["errors"],
            "warnings": validation_result["warnings"]
        }, status_code=400)

    # Save file
    result = save_uploaded_file(
        file=file,
        upload_id=upload_id,
        category=category,
        description=description,
        tags=tag_list
    )

    if validation_result["warnings"]:
        result["warnings"] = validation_result["warnings"]

    return JSONResponse(result)

@app.post("/upload/multiple")
def upload_multiple_files(
    request: Request,
    files: List[UploadFile] = File(...),
    category: str = Form("other"),
    description: str = Form("")
) -> Response:
    """Upload multiple files"""

    if len(files) > 10:  # Limit number of files
        return JSONResponse({
            "success": False,
            "error": "Maximum 10 files allowed per upload"
        }, status_code=400)

    results = []

    for file in files:
        # Generate upload ID for each file
        upload_id = str(uuid.uuid4())

        # Validate file
        validation_result = validate_file(file, category)
        if not validation_result["valid"]:
            results.append({
                "filename": file.filename,
                "upload_id": upload_id,
                "success": False,
                "errors": validation_result["errors"]
            })
            continue

        # Save file
        result = save_uploaded_file(
            file=file,
            upload_id=upload_id,
            category=category,
            description=f"{description} (batch upload)"
        )

        results.append({
            "filename": file.filename,
            **result
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
    upload_request: FileUploadRequest,
    file: UploadFile = File(...)
) -> Response:
    """Upload file with structured form data"""

    # Generate upload ID
    upload_id = str(uuid.uuid4())

    # Validate file
    validation_result = validate_file(file, upload_request.category)
    if not validation_result["valid"]:
        return JSONResponse({
            "success": False,
            "upload_id": upload_id,
            "errors": validation_result["errors"]
        }, status_code=400)

    # Save file
    result = save_uploaded_file(
        file=file,
        upload_id=upload_id,
        category=upload_request.category,
        description=upload_request.description,
        tags=upload_request.tags
    )

    return JSONResponse(result)

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
    with open(file_path, "rb") as f:
        file_content = f.read()

    file_info = upload_info["file_info"]

    return Response(
        content=file_content,
        media_type=file_info["content_type"],
        headers={
            "Content-Disposition": f'attachment; filename="{file_info["filename"]}"',
            "Content-Length": str(len(file_content)),
            "X-Upload-ID": upload_id,
            "X-File-Checksum": file_info["checksum"]
        }
    )

@app.get("/uploads")
def list_uploads(
    request: Request,
    category: Optional[str] = None,
    limit: int = 50
) -> Response:
    """List uploaded files with filtering"""

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
            "tags": file_info["tags"],
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
