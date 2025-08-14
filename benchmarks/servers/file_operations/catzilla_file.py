#!/usr/bin/env python3
"""
Catzilla File Operations Benchmark Server

High-performance file operations benchmarks using Catzilla's optimized file handling.
Tests file uploads, static file serving, streaming, and file processing.

Features:
- Optimized file upload system with memory pooling
- Zero-copy static file serving
- Streaming file responses
- File validation and processing
- Memory-efficient large file handling
"""

import sys
import os
import json
import time
import argparse
import tempfile
import hashlib
from typing import Optional, List, Dict, Any
from pathlib import Path
import mimetypes

# Add the catzilla package to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', 'python'))

from catzilla import (
    Catzilla, BaseModel, Field,
    JSONResponse, Response,
    Query, Path as PathParam, Header, Form, File, UploadFile
)

from catzilla import (
    Catzilla, BaseModel, Field,
    JSONResponse, Response,
    Query, Path as PathParam, Header, Form, File, UploadFile
)


# =====================================================
# FILE OPERATION MODELS
# =====================================================

class FileUploadResponse(BaseModel):
    """File upload response model"""
    uploaded: bool
    filename: str
    size: int
    content_type: str
    upload_time_ms: float
    checksum: Optional[str] = None

class FileListResponse(BaseModel):
    """File list response model"""
    files: List[Dict[str, Any]]
    total_count: int
    total_size: int

class FileProcessingRequest(BaseModel):
    """File processing request model"""
    operation: str = Field(regex=r'^(resize|compress|convert|validate)$')
    parameters: Dict[str, Any] = {}


def create_catzilla_file_server():
    """Create Catzilla server optimized for file operations"""

    app = Catzilla(
        production=True,
        use_jemalloc=True,           # Memory optimization for file operations
        auto_validation=True,        # Enable auto-validation
        memory_profiling=False,      # Disable for benchmarks
        auto_memory_tuning=True,     # Adaptive memory management
        show_banner=False
    )

    # Create upload directory
    upload_dir = Path("/tmp/catzilla_uploads")
    upload_dir.mkdir(exist_ok=True)

    # Create test static files
    static_dir = Path("/tmp/catzilla_static")
    static_dir.mkdir(exist_ok=True)

    # Generate test files
    create_test_files(static_dir)

    # endpoints = get_file_endpoints()  # Not needed for actual endpoints

    # ==========================================
    # FILE UPLOAD BENCHMARKS
    # ==========================================

    @app.post("/upload/single")
    def upload_single_file(
        request,
        file: UploadFile = File(...),
        description: Optional[str] = Form(None)
    ) -> Response:
        """Single file upload benchmark"""
        start_time = time.perf_counter()

        # Save uploaded file
        filename = file.filename or "uploaded_file"
        filepath = upload_dir / filename

        # Read and save file content
        content = file.file.read()
        with open(filepath, "wb") as f:
            f.write(content)

        # Calculate checksum
        checksum = hashlib.md5(content).hexdigest()

        upload_time = (time.perf_counter() - start_time) * 1000

        return JSONResponse({
            "uploaded": True,
            "filename": filename,
            "size": len(content),
            "content_type": file.content_type or "application/octet-stream",
            "upload_time_ms": round(upload_time, 3),
            "checksum": checksum,
            "framework": "catzilla",
            "description": description
        })

    @app.post("/upload/multiple")
    def upload_multiple_files(
        request,
        files: List[UploadFile] = File(...)
    ) -> Response:
        """Multiple file upload benchmark"""
        start_time = time.perf_counter()

        uploaded_files = []
        total_size = 0

        for file in files:
            filename = file.filename or f"uploaded_file_{len(uploaded_files)}"
            filepath = upload_dir / filename

            content = file.file.read()
            with open(filepath, "wb") as f:
                f.write(content)

            checksum = hashlib.md5(content).hexdigest()
            total_size += len(content)

            uploaded_files.append({
                "filename": filename,
                "size": len(content),
                "content_type": file.content_type or "application/octet-stream",
                "checksum": checksum
            })

        upload_time = (time.perf_counter() - start_time) * 1000

        return JSONResponse({
            "uploaded": True,
            "file_count": len(uploaded_files),
            "files": uploaded_files,
            "total_size": total_size,
            "upload_time_ms": round(upload_time, 3),
            "throughput_mb_per_sec": round((total_size / (1024 * 1024)) / (upload_time / 1000), 3),
            "framework": "catzilla"
        })

    @app.post("/upload/chunked")
    def upload_chunked_file(
        request,
        chunk: UploadFile = File(...),
        chunk_index: int = Form(...),
        total_chunks: int = Form(...),
        file_id: str = Form(...)
    ) -> Response:
        """Chunked file upload benchmark"""
        start_time = time.perf_counter()

        chunk_dir = upload_dir / "chunks" / file_id
        chunk_dir.mkdir(parents=True, exist_ok=True)

        chunk_path = chunk_dir / f"chunk_{chunk_index}"
        content = chunk.file.read()

        with open(chunk_path, "wb") as f:
            f.write(content)

        upload_time = (time.perf_counter() - start_time) * 1000

        # Check if all chunks are uploaded
        uploaded_chunks = len(list(chunk_dir.glob("chunk_*")))
        is_complete = uploaded_chunks == total_chunks

        return JSONResponse({
            "chunk_uploaded": True,
            "chunk_index": chunk_index,
            "total_chunks": total_chunks,
            "uploaded_chunks": uploaded_chunks,
            "is_complete": is_complete,
            "chunk_size": len(content),
            "upload_time_ms": round(upload_time, 3),
            "framework": "catzilla"
        })

    # ==========================================
    # STATIC FILE SERVING BENCHMARKS
    # ==========================================

    @app.get("/static/{filename}")
    def serve_static_file(request, filename: str = PathParam(...)) -> Response:
        """Static file serving benchmark"""
        filepath = static_dir / filename

        if not filepath.exists():
            return JSONResponse({"error": "File not found"}, status_code=404)

        # Read file content
        mime_type = mimetypes.guess_type(filename)[0] or "application/octet-stream"

        # Handle text vs binary files
        if mime_type.startswith('text/'):
            with open(filepath, "r", encoding="utf-8") as f:
                file_content = f.read()
        else:
            with open(filepath, "rb") as f:
                file_bytes = f.read()
            file_content = file_bytes.decode("utf-8", errors="ignore")

        return Response(
            status_code=200,
            content_type=mime_type,
            body=file_content,
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"'
            }
        )

    @app.get("/static-range/{filename}")
    def serve_static_file_range(
        request,
        filename: str = PathParam(...),
        range_header: Optional[str] = Header(None, alias="Range")
    ) -> Response:
        """Static file serving with range support benchmark"""
        filepath = static_dir / filename

        if not filepath.exists():
            return JSONResponse({"error": "File not found"}, status_code=404)

        # Simple range support (for benchmarking)
        if range_header and range_header.startswith("bytes="):
            try:
                range_spec = range_header[6:]  # Remove "bytes="
                start, end = range_spec.split("-")
                start = int(start) if start else 0

                with open(filepath, "rb") as f:
                    f.seek(start)
                    if end:
                        content = f.read(int(end) - start + 1)
                    else:
                        content = f.read()

                return Response(
                    content=content,
                    status_code=206,
                    headers={
                        "Content-Range": f"bytes {start}-{start + len(content) - 1}/{filepath.stat().st_size}",
                        "Accept-Ranges": "bytes"
                    }
                )
            except (ValueError, IndexError):
                pass

        # Read full file content
        mime_type = mimetypes.guess_type(filename)[0] or "application/octet-stream"

        # Handle text vs binary files
        if mime_type.startswith('text/'):
            with open(filepath, "r", encoding="utf-8") as f:
                file_content = f.read()
        else:
            with open(filepath, "rb") as f:
                file_bytes = f.read()
            file_content = file_bytes.decode("utf-8", errors="ignore")

        return Response(
            status_code=200,
            content_type=mime_type,
            body=file_content,
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"'
            }
        )

    # ==========================================
    # STREAMING BENCHMARKS
    # ==========================================

    @app.get("/stream/file/{filename}")
    def stream_file(request, filename: str = PathParam(...)) -> Response:
        """File streaming benchmark"""
        filepath = static_dir / filename

        if not filepath.exists():
            return JSONResponse({"error": "File not found"}, status_code=404)

        # Read file content
        mime_type = mimetypes.guess_type(filename)[0] or "application/octet-stream"

        # Handle text vs binary files
        if mime_type.startswith('text/'):
            with open(filepath, "r", encoding="utf-8") as f:
                file_content = f.read()
        else:
            with open(filepath, "rb") as f:
                file_bytes = f.read()
            file_content = file_bytes.decode("utf-8", errors="ignore")

        return Response(
            status_code=200,
            content_type=mime_type,
            body=file_content,
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )

    @app.get("/stream/generated/{size_mb}")
    def stream_generated_data(request, size_mb: int = PathParam(...)) -> Response:
        """Generated data streaming benchmark"""
        total_bytes = size_mb * 1024 * 1024

        # Generate the data at once (simplified for Catzilla)
        content = "A" * total_bytes

        return Response(
            status_code=200,
            content_type="application/octet-stream",
            body=content,
            headers={
                "Content-Length": str(total_bytes),
                "Content-Disposition": f"attachment; filename=generated_{size_mb}mb.txt"
            }
        )

    # ==========================================
    # FILE PROCESSING BENCHMARKS
    # ==========================================

    @app.post("/process/validate")
    def validate_file(
        request,
        file: UploadFile = File(...),
        validation_type: str = Form("checksum")
    ) -> Response:
        """File validation benchmark"""
        start_time = time.perf_counter()

        content = file.file.read()
        file_size = len(content)

        validation_result = {}

        if validation_type == "checksum":
            validation_result["md5"] = hashlib.md5(content).hexdigest()
            validation_result["sha1"] = hashlib.sha1(content).hexdigest()
        elif validation_type == "content":
            # Simple content validation
            validation_result["is_text"] = content.isascii() if content else False
            validation_result["line_count"] = content.count(b'\n') if content else 0
        elif validation_type == "size":
            validation_result["size_bytes"] = file_size
            validation_result["size_mb"] = round(file_size / (1024 * 1024), 3)

        processing_time = (time.perf_counter() - start_time) * 1000

        return JSONResponse({
            "validated": True,
            "filename": file.filename,
            "size": file_size,
            "validation_type": validation_type,
            "validation_result": validation_result,
            "processing_time_ms": round(processing_time, 3),
            "throughput_mb_per_sec": round((file_size / (1024 * 1024)) / (processing_time / 1000), 3) if processing_time > 0 else 0,
            "framework": "catzilla"
        })

    @app.post("/process/transform")
    def transform_file(
        request,
        file: UploadFile = File(...),
        operation: str = Form("uppercase")
    ) -> Response:
        """File transformation benchmark"""
        start_time = time.perf_counter()

        content = file.file.read()

        if operation == "uppercase":
            transformed = content.upper()
        elif operation == "lowercase":
            transformed = content.lower()
        elif operation == "reverse":
            transformed = content[::-1]
        elif operation == "base64":
            import base64
            transformed = base64.b64encode(content)
        else:
            transformed = content

        processing_time = (time.perf_counter() - start_time) * 1000

        return JSONResponse({
            "transformed": True,
            "filename": file.filename,
            "original_size": len(content),
            "transformed_size": len(transformed),
            "operation": operation,
            "processing_time_ms": round(processing_time, 3),
            "throughput_mb_per_sec": round((len(content) / (1024 * 1024)) / (processing_time / 1000), 3) if processing_time > 0 else 0,
            "framework": "catzilla"
        })

    # ==========================================
    # FILE LISTING AND MANAGEMENT
    # ==========================================

    @app.get("/files/list")
    def list_files(
        request,
        directory: str = Query("uploads", description="Directory to list"),
        limit: int = Query(100, ge=1, le=1000),
        offset: int = Query(0, ge=0)
    ) -> Response:
        """File listing benchmark"""
        start_time = time.perf_counter()

        if directory == "uploads":
            target_dir = upload_dir
        elif directory == "static":
            target_dir = static_dir
        else:
            return JSONResponse({"error": "Invalid directory"}, status_code=400)

        files = []
        total_size = 0

        if target_dir.exists():
            all_files = [f for f in target_dir.iterdir() if f.is_file()]
            paginated_files = all_files[offset:offset + limit]

            for filepath in paginated_files:
                stat = filepath.stat()
                files.append({
                    "name": filepath.name,
                    "size": stat.st_size,
                    "modified": stat.st_mtime,
                    "content_type": mimetypes.guess_type(str(filepath))[0]
                })
                total_size += stat.st_size

        processing_time = (time.perf_counter() - start_time) * 1000

        return JSONResponse({
            "files": files,
            "total_count": len(files),
            "total_size": total_size,
            "directory": directory,
            "limit": limit,
            "offset": offset,
            "processing_time_ms": round(processing_time, 3),
            "framework": "catzilla"
        })

    @app.delete("/files/{filename}")
    def delete_file(request, filename: str = PathParam(...)) -> Response:
        """File deletion benchmark"""
        start_time = time.perf_counter()

        filepath = upload_dir / filename

        if not filepath.exists():
            return JSONResponse({"error": "File not found"}, status_code=404)

        file_size = filepath.stat().st_size
        filepath.unlink()

        processing_time = (time.perf_counter() - start_time) * 1000

        return JSONResponse({
            "deleted": True,
            "filename": filename,
            "size": file_size,
            "processing_time_ms": round(processing_time, 3),
            "framework": "catzilla"
        })

    @app.get("/health")
    def health(request) -> Response:
        """Health check endpoint"""
        return JSONResponse({
            "status": "healthy",
            "framework": "catzilla",
            "file_operations": "optimized",
            "memory_optimization": "jemalloc_enabled",
            "upload_dir": str(upload_dir),
            "static_dir": str(static_dir)
        })

    return app


def create_test_files(static_dir: Path):
    """Create test files for static serving benchmarks"""
    test_files = {
        "small.txt": "A" * 1024,  # 1KB
        "medium.txt": "B" * (100 * 1024),  # 100KB
        "large.txt": "C" * (1024 * 1024),  # 1MB
        "test.json": json.dumps({"message": "Hello, World!", "timestamp": time.time()}),
        "test.html": "<html><body><h1>Test HTML File</h1></body></html>",
        "binary.bin": bytes(range(256)) * 1024  # 256KB binary file
    }

    for filename, content in test_files.items():
        filepath = static_dir / filename
        if isinstance(content, str):
            filepath.write_text(content)
        else:
            filepath.write_bytes(content)


def main():
    parser = argparse.ArgumentParser(description='Catzilla file operations benchmark server')
    parser.add_argument('--host', default='127.0.0.1', help='Host to bind to')
    parser.add_argument('--port', type=int, default=8200, help='Port to bind to')
    parser.add_argument('--workers', type=int, default=1, help='Number of workers')

    args = parser.parse_args()

    app = create_catzilla_file_server()

    print(f"🚀 Starting Catzilla file operations benchmark server on {args.host}:{args.port}")
    print("File operation endpoints:")
    print("  POST /upload/single             - Single file upload")
    print("  POST /upload/multiple           - Multiple file upload")
    print("  POST /upload/chunked            - Chunked file upload")
    print("  GET  /static/{filename}         - Static file serving")
    print("  GET  /static-range/{filename}   - Static file with range support")
    print("  GET  /stream/file/{filename}    - File streaming")
    print("  GET  /stream/generated/{size}   - Generated data streaming")
    print("  POST /process/validate          - File validation")
    print("  POST /process/transform         - File transformation")
    print("  GET  /files/list                - File listing")
    print("  DELETE /files/{filename}        - File deletion")
    print("  GET  /health                    - Health check")
    print()

    try:
        app.listen(args.port, args.host)
    except KeyboardInterrupt:
        print("\n👋 Catzilla file operations benchmark server stopped")


if __name__ == "__main__":
    main()
