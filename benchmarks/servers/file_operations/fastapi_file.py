#!/usr/bin/env python3
"""
FastAPI File Operations Benchmark Server

Comprehensive file operations using FastAPI with async support.
Tests file upload, download, streaming, and processing performance.

Features:
- File upload with validation and chunked processing
- Static file serving with caching
- File streaming responses
- Image processing workflows
- Batch file operations
- Background file processing
"""

import sys
import os
import json
import time
import argparse
import uuid
import hashlib
import mimetypes
import asyncio
from typing import Optional, List, Dict, Any, Union
from datetime import datetime
import random
from pathlib import Path
import aiofiles
from concurrent.futures import ThreadPoolExecutor

# FastAPI imports
from fastapi import FastAPI, Query, Path as PathParam, Header, Form, File, UploadFile, Depends
from fastapi.responses import JSONResponse, FileResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.background import BackgroundTasks
from pydantic import BaseModel, Field
import uvicorn

# Import shared file endpoints
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'shared'))
from file_endpoints import get_file_endpoints


def create_fastapi_file_server():
    """Create FastAPI server with file operations"""

    app = FastAPI(
        title="FastAPI File Operations Benchmark",
        description="File operations performance testing with FastAPI",
        version="1.0.0"
    )

    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Thread pool for CPU-intensive tasks
    executor = ThreadPoolExecutor(max_workers=4)

    # File storage (in production, use cloud storage)
    UPLOAD_DIR = Path("uploads")
    UPLOAD_DIR.mkdir(exist_ok=True)

    file_store = {
        "uploaded_files": {},
        "processing_queue": [],
        "download_stats": {}
    }

    endpoints = get_file_endpoints()

    # ==========================================
    # FILE UPLOAD ENDPOINTS
    # ==========================================

    @app.post("/upload/single")
    async def upload_single_file(
        background_tasks: BackgroundTasks,
        file: UploadFile = File(...),
        category: Optional[str] = Form("general"),
        description: Optional[str] = Form(None),
        auto_process: bool = Form(True)
    ):
        """Upload single file with optional background processing"""
        start_time = time.perf_counter()

        # Validate file
        if file.size > 50 * 1024 * 1024:  # 50MB limit
            return JSONResponse({"error": "File too large"}, status_code=413)

        # Generate unique filename
        file_id = str(uuid.uuid4())
        file_extension = Path(file.filename).suffix
        new_filename = f"{file_id}{file_extension}"
        file_path = UPLOAD_DIR / new_filename

        # Read and save file
        content = await file.read()
        async with aiofiles.open(file_path, 'wb') as f:
            await f.write(content)

        # Calculate file hash
        file_hash = hashlib.sha256(content).hexdigest()

        # Store file metadata
        file_info = {
            "id": file_id,
            "filename": new_filename,
            "original_name": file.filename,
            "size": len(content),
            "content_type": file.content_type,
            "category": category,
            "description": description,
            "hash": file_hash,
            "upload_time": datetime.now().isoformat(),
            "processed": False,
            "download_count": 0
        }

        file_store["uploaded_files"][file_id] = file_info

        # Schedule background processing
        if auto_process:
            background_tasks.add_task(process_uploaded_file, file_id, file_path)

        processing_time = (time.perf_counter() - start_time) * 1000

        return JSONResponse({
            "upload_successful": True,
            "file": file_info,
            "processing_time_ms": round(processing_time, 3),
            "framework": "fastapi"
        })

    @app.post("/upload/multiple")
    async def upload_multiple_files(
        background_tasks: BackgroundTasks,
        files: List[UploadFile] = File(...),
        category: Optional[str] = Form("general"),
        batch_process: bool = Form(True)
    ):
        """Upload multiple files with batch processing"""
        start_time = time.perf_counter()

        if len(files) > 20:
            return JSONResponse({"error": "Too many files"}, status_code=413)

        uploaded_files = []
        total_size = 0

        for file in files:
            # Validate individual file
            if file.size > 10 * 1024 * 1024:  # 10MB per file in batch
                continue

            # Generate unique filename
            file_id = str(uuid.uuid4())
            file_extension = Path(file.filename).suffix
            new_filename = f"{file_id}{file_extension}"
            file_path = UPLOAD_DIR / new_filename

            # Read and save file
            content = await file.read()
            total_size += len(content)

            async with aiofiles.open(file_path, 'wb') as f:
                await f.write(content)

            # Calculate file hash
            file_hash = hashlib.sha256(content).hexdigest()

            # Store file metadata
            file_info = {
                "id": file_id,
                "filename": new_filename,
                "original_name": file.filename,
                "size": len(content),
                "content_type": file.content_type,
                "category": category,
                "hash": file_hash,
                "upload_time": datetime.now().isoformat(),
                "processed": False,
                "download_count": 0
            }

            file_store["uploaded_files"][file_id] = file_info
            uploaded_files.append(file_info)

        # Schedule batch processing
        if batch_process and uploaded_files:
            file_ids = [f["id"] for f in uploaded_files]
            background_tasks.add_task(process_file_batch, file_ids)

        processing_time = (time.perf_counter() - start_time) * 1000

        return JSONResponse({
            "upload_successful": True,
            "files": uploaded_files,
            "total_files": len(uploaded_files),
            "total_size": total_size,
            "processing_time_ms": round(processing_time, 3),
            "framework": "fastapi"
        })

    # ==========================================
    # FILE DOWNLOAD ENDPOINTS
    # ==========================================

    @app.get("/download/{file_id}")
    async def download_file(
        file_id: str = PathParam(...),
        as_attachment: bool = Query(False)
    ):
        """Download file by ID"""
        start_time = time.perf_counter()

        if file_id not in file_store["uploaded_files"]:
            return JSONResponse({"error": "File not found"}, status_code=404)

        file_info = file_store["uploaded_files"][file_id]
        file_path = UPLOAD_DIR / file_info["filename"]

        if not file_path.exists():
            return JSONResponse({"error": "File not found on disk"}, status_code=404)

        # Update download stats
        file_info["download_count"] += 1
        file_store["download_stats"][file_id] = file_store["download_stats"].get(file_id, 0) + 1

        # Determine response headers
        media_type = file_info["content_type"] or "application/octet-stream"
        filename = file_info["original_name"]

        headers = {}
        if as_attachment:
            headers["Content-Disposition"] = f'attachment; filename="{filename}"'

        processing_time = (time.perf_counter() - start_time) * 1000
        headers["X-Processing-Time"] = str(round(processing_time, 3))
        headers["X-Framework"] = "fastapi"

        return FileResponse(
            path=file_path,
            media_type=media_type,
            filename=filename if as_attachment else None,
            headers=headers
        )

    @app.get("/stream/{file_id}")
    async def stream_file(
        file_id: str = PathParam(...),
        chunk_size: int = Query(8192, ge=1024, le=1048576)
    ):
        """Stream file in chunks"""
        start_time = time.perf_counter()

        if file_id not in file_store["uploaded_files"]:
            return JSONResponse({"error": "File not found"}, status_code=404)

        file_info = file_store["uploaded_files"][file_id]
        file_path = UPLOAD_DIR / file_info["filename"]

        if not file_path.exists():
            return JSONResponse({"error": "File not found on disk"}, status_code=404)

        async def generate():
            async with aiofiles.open(file_path, 'rb') as f:
                while chunk := await f.read(chunk_size):
                    yield chunk

        # Update download stats
        file_info["download_count"] += 1

        processing_time = (time.perf_counter() - start_time) * 1000

        headers = {
            "X-Processing-Time": str(round(processing_time, 3)),
            "X-Framework": "fastapi",
            "X-Chunk-Size": str(chunk_size)
        }

        return StreamingResponse(
            generate(),
            media_type=file_info["content_type"] or "application/octet-stream",
            headers=headers
        )

    # ==========================================
    # FILE MANAGEMENT ENDPOINTS
    # ==========================================

    @app.get("/files")
    async def list_files(
        category: Optional[str] = Query(None),
        limit: int = Query(50, ge=1, le=1000),
        offset: int = Query(0, ge=0)
    ):
        """List uploaded files with filtering"""
        start_time = time.perf_counter()

        files = list(file_store["uploaded_files"].values())

        # Apply category filter
        if category:
            files = [f for f in files if f.get("category") == category]

        # Sort by upload time (newest first)
        files.sort(key=lambda x: x.get("upload_time", ""), reverse=True)

        # Apply pagination
        total_count = len(files)
        paginated_files = files[offset:offset + limit]

        processing_time = (time.perf_counter() - start_time) * 1000

        return JSONResponse({
            "files": paginated_files,
            "total": total_count,
            "limit": limit,
            "offset": offset,
            "processing_time_ms": round(processing_time, 3),
            "framework": "fastapi"
        })

    @app.get("/files/{file_id}/info")
    async def get_file_info(file_id: str = PathParam(...)):
        """Get detailed file information"""
        start_time = time.perf_counter()

        if file_id not in file_store["uploaded_files"]:
            return JSONResponse({"error": "File not found"}, status_code=404)

        file_info = file_store["uploaded_files"][file_id].copy()
        file_path = UPLOAD_DIR / file_info["filename"]

        # Add file system info
        if file_path.exists():
            stat = file_path.stat()
            file_info["disk_size"] = stat.st_size
            file_info["last_modified"] = datetime.fromtimestamp(stat.st_mtime).isoformat()
            file_info["exists_on_disk"] = True
        else:
            file_info["exists_on_disk"] = False

        # Add download stats
        file_info["download_stats"] = file_store["download_stats"].get(file_id, 0)

        processing_time = (time.perf_counter() - start_time) * 1000

        return JSONResponse({
            "file": file_info,
            "processing_time_ms": round(processing_time, 3),
            "framework": "fastapi"
        })

    @app.delete("/files/{file_id}")
    async def delete_file(file_id: str = PathParam(...)):
        """Delete file"""
        start_time = time.perf_counter()

        if file_id not in file_store["uploaded_files"]:
            return JSONResponse({"error": "File not found"}, status_code=404)

        file_info = file_store["uploaded_files"][file_id]
        file_path = UPLOAD_DIR / file_info["filename"]

        # Remove from disk
        deleted_from_disk = False
        if file_path.exists():
            file_path.unlink()
            deleted_from_disk = True

        # Remove from store
        del file_store["uploaded_files"][file_id]
        if file_id in file_store["download_stats"]:
            del file_store["download_stats"][file_id]

        processing_time = (time.perf_counter() - start_time) * 1000

        return JSONResponse({
            "deleted": True,
            "file_id": file_id,
            "deleted_from_disk": deleted_from_disk,
            "processing_time_ms": round(processing_time, 3),
            "framework": "fastapi"
        })

    # ==========================================
    # FILE PROCESSING ENDPOINTS
    # ==========================================

    @app.post("/process/{file_id}")
    async def process_file(
        background_tasks: BackgroundTasks,
        file_id: str = PathParam(...),
        operation: str = Query(..., regex=r'^(resize|compress|convert|analyze)$'),
        params: Optional[str] = Query(None)
    ):
        """Process file with specified operation"""
        start_time = time.perf_counter()

        if file_id not in file_store["uploaded_files"]:
            return JSONResponse({"error": "File not found"}, status_code=404)

        file_info = file_store["uploaded_files"][file_id]
        file_path = UPLOAD_DIR / file_info["filename"]

        if not file_path.exists():
            return JSONResponse({"error": "File not found on disk"}, status_code=404)

        # Parse processing parameters
        processing_params = {}
        if params:
            try:
                processing_params = json.loads(params)
            except:
                processing_params = {"raw_params": params}

        # Schedule processing
        task_id = str(uuid.uuid4())
        background_tasks.add_task(
            process_file_operation,
            file_id, file_path, operation, processing_params, task_id
        )

        processing_time = (time.perf_counter() - start_time) * 1000

        return JSONResponse({
            "processing_started": True,
            "task_id": task_id,
            "operation": operation,
            "file_id": file_id,
            "processing_time_ms": round(processing_time, 3),
            "framework": "fastapi"
        })

    @app.get("/stats")
    async def get_file_stats():
        """Get file operation statistics"""
        start_time = time.perf_counter()

        files = list(file_store["uploaded_files"].values())

        stats = {
            "total_files": len(files),
            "total_size": sum(f.get("size", 0) for f in files),
            "processed_files": len([f for f in files if f.get("processed", False)]),
            "total_downloads": sum(file_store["download_stats"].values()),
            "categories": {},
            "content_types": {},
            "recent_uploads": []
        }

        # Category breakdown
        for file_info in files:
            category = file_info.get("category", "unknown")
            stats["categories"][category] = stats["categories"].get(category, 0) + 1

        # Content type breakdown
        for file_info in files:
            content_type = file_info.get("content_type", "unknown")
            stats["content_types"][content_type] = stats["content_types"].get(content_type, 0) + 1

        # Recent uploads (last 10)
        recent_files = sorted(files, key=lambda x: x.get("upload_time", ""), reverse=True)[:10]
        stats["recent_uploads"] = [
            {
                "id": f["id"],
                "original_name": f["original_name"],
                "size": f["size"],
                "upload_time": f["upload_time"]
            }
            for f in recent_files
        ]

        processing_time = (time.perf_counter() - start_time) * 1000

        return JSONResponse({
            "stats": stats,
            "processing_time_ms": round(processing_time, 3),
            "framework": "fastapi"
        })

    @app.get("/health")
    async def health():
        """Health check"""
        return JSONResponse({
            "status": "healthy",
            "framework": "fastapi",
            "features": ["file_upload", "file_download", "file_streaming", "background_processing"],
            "upload_dir": str(UPLOAD_DIR),
            "file_count": len(file_store["uploaded_files"])
        })

    return app


# =====================================================
# BACKGROUND PROCESSING FUNCTIONS
# =====================================================

async def process_uploaded_file(file_id: str, file_path: Path):
    """Background task: Process uploaded file"""
    # Simulate file processing
    # Removed artificial delay for benchmarking

    if file_id in file_store["uploaded_files"]:
        file_store["uploaded_files"][file_id]["processed"] = True
        file_store["uploaded_files"][file_id]["processing_completed"] = datetime.now().isoformat()

    print(f"File processed: {file_id}")

async def process_file_batch(file_ids: List[str]):
    """Background task: Process batch of files"""
    # Simulate batch processing
    # Removed artificial delay for benchmarking)

    for file_id in file_ids:
        if file_id in file_store["uploaded_files"]:
            file_store["uploaded_files"][file_id]["processed"] = True
            file_store["uploaded_files"][file_id]["batch_processed"] = True

    print(f"Batch processed: {len(file_ids)} files")

async def process_file_operation(file_id: str, file_path: Path, operation: str, params: dict, task_id: str):
    """Background task: Process file with specific operation"""
    # Simulate different processing times for different operations
    processing_times = {
        "resize": 1,
        "compress": 3,
        "convert": 5,
        "analyze": 2
    }

    # Removed artificial delay for benchmarking)

    if file_id in file_store["uploaded_files"]:
        file_info = file_store["uploaded_files"][file_id]
        if "processing_history" not in file_info:
            file_info["processing_history"] = []

        file_info["processing_history"].append({
            "task_id": task_id,
            "operation": operation,
            "params": params,
            "completed_at": datetime.now().isoformat()
        })

    print(f"File operation completed: {operation} on {file_id}")


def main():
    parser = argparse.ArgumentParser(description='FastAPI file operations benchmark server')
    parser.add_argument('--host', default='127.0.0.1', help='Host to bind to')
    parser.add_argument('--port', type=int, default=8301, help='Port to bind to')
    parser.add_argument('--workers', type=int, default=1, help='Number of workers')

    args = parser.parse_args()

    app = create_fastapi_file_server()

    print(f"🚀 Starting FastAPI file operations benchmark server on {args.host}:{args.port}")
    print("File operation endpoints:")
    print("  POST /upload/single            - Upload single file")
    print("  POST /upload/multiple          - Upload multiple files")
    print("  GET  /download/{file_id}       - Download file")
    print("  GET  /stream/{file_id}         - Stream file")
    print("  GET  /files                    - List files")
    print("  GET  /files/{file_id}/info     - Get file info")
    print("  DELETE /files/{file_id}        - Delete file")
    print("  POST /process/{file_id}        - Process file")
    print("  GET  /stats                    - File statistics")
    print("  GET  /health                   - Health check")
    print()

    uvicorn.run(app, host=args.host, port=args.port, workers=args.workers)


if __name__ == "__main__":
    main()

# Create app instance for ASGI servers like uvicorn
app = create_fastapi_file_server()
