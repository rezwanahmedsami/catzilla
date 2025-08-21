#!/usr/bin/env python3
"""
Flask File Operations Benchmark Server

Comprehensive file operations using Flask with Werkzeug support.
Tests file upload, download, streaming, and processing performance.

Features:
- File upload with validation and chunked processing
- Static file serving with caching
- File streaming responses
- Image processing workflows
- Batch file operations
- Background file processing with RQ
"""

import sys
import os
import json
import time
import argparse
import uuid
import hashlib
import mimetypes
from typing import Optional, List, Dict, Any, Union
from datetime import datetime
import random
from pathlib import Path
import threading
from concurrent.futures import ThreadPoolExecutor

# Flask imports
from flask import Flask, request, jsonify, send_file, Response, stream_template
from werkzeug.utils import secure_filename
from werkzeug.datastructures import FileStorage
import werkzeug.exceptions

# Import shared file endpoints
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'shared'))
from file_endpoints import get_file_endpoints


def create_flask_file_server():
    """Create Flask server with file operations"""

    app = Flask(__name__)
    app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB max
    app.config['UPLOAD_FOLDER'] = 'uploads'

    # Thread pool for background tasks
    executor = ThreadPoolExecutor(max_workers=4)

    # File storage (in production, use cloud storage)
    UPLOAD_DIR = Path(app.config['UPLOAD_FOLDER'])
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

    @app.route('/upload/single', methods=['POST'])
    def upload_single_file():
        """Upload single file with optional background processing"""
        start_time = time.perf_counter()

        if 'file' not in request.files:
            return jsonify({"error": "No file provided"}), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({"error": "No file selected"}), 400

        # Get form data
        category = request.form.get('category', 'general')
        description = request.form.get('description')
        auto_process = request.form.get('auto_process', 'true').lower() == 'true'

        # Validate file size
        file.seek(0, 2)  # Seek to end
        file_size = file.tell()
        file.seek(0)  # Reset to beginning

        if file_size > 50 * 1024 * 1024:  # 50MB limit
            return jsonify({"error": "File too large"}), 413

        # Generate unique filename
        file_id = str(uuid.uuid4())
        original_filename = secure_filename(file.filename)
        file_extension = Path(original_filename).suffix
        new_filename = f"{file_id}{file_extension}"
        file_path = UPLOAD_DIR / new_filename

        # Save file
        file.save(file_path)

        # Calculate file hash
        with open(file_path, 'rb') as f:
            file_hash = hashlib.sha256(f.read()).hexdigest()

        # Store file metadata
        file_info = {
            "id": file_id,
            "filename": new_filename,
            "original_name": original_filename,
            "size": file_size,
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
            executor.submit(process_uploaded_file, file_id, file_path, file_store)

        processing_time = (time.perf_counter() - start_time) * 1000

        return jsonify({
            "upload_successful": True,
            "file": file_info,
            "processing_time_ms": round(processing_time, 3),
            "framework": "flask"
        })

    @app.route('/upload/multiple', methods=['POST'])
    def upload_multiple_files():
        """Upload multiple files with batch processing"""
        start_time = time.perf_counter()

        files = request.files.getlist('files')
        if not files or len(files) == 0:
            return jsonify({"error": "No files provided"}), 400

        if len(files) > 20:
            return jsonify({"error": "Too many files"}), 413

        # Get form data
        category = request.form.get('category', 'general')
        batch_process = request.form.get('batch_process', 'true').lower() == 'true'

        uploaded_files = []
        total_size = 0

        for file in files:
            if file.filename == '':
                continue

            # Validate individual file size
            file.seek(0, 2)
            file_size = file.tell()
            file.seek(0)

            if file_size > 10 * 1024 * 1024:  # 10MB per file in batch
                continue

            # Generate unique filename
            file_id = str(uuid.uuid4())
            original_filename = secure_filename(file.filename)
            file_extension = Path(original_filename).suffix
            new_filename = f"{file_id}{file_extension}"
            file_path = UPLOAD_DIR / new_filename

            # Save file
            file.save(file_path)
            total_size += file_size

            # Calculate file hash
            with open(file_path, 'rb') as f:
                file_hash = hashlib.sha256(f.read()).hexdigest()

            # Store file metadata
            file_info = {
                "id": file_id,
                "filename": new_filename,
                "original_name": original_filename,
                "size": file_size,
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
            executor.submit(process_file_batch, file_ids, file_store)

        processing_time = (time.perf_counter() - start_time) * 1000

        return jsonify({
            "upload_successful": True,
            "files": uploaded_files,
            "total_files": len(uploaded_files),
            "total_size": total_size,
            "processing_time_ms": round(processing_time, 3),
            "framework": "flask"
        })

    # ==========================================
    # FILE DOWNLOAD ENDPOINTS
    # ==========================================

    @app.route('/download/<file_id>')
    def download_file(file_id):
        """Download file by ID"""
        start_time = time.perf_counter()

        if file_id not in file_store["uploaded_files"]:
            return jsonify({"error": "File not found"}), 404

        file_info = file_store["uploaded_files"][file_id]
        file_path = UPLOAD_DIR / file_info["filename"]

        if not file_path.exists():
            return jsonify({"error": "File not found on disk"}), 404

        # Update download stats
        file_info["download_count"] += 1
        file_store["download_stats"][file_id] = file_store["download_stats"].get(file_id, 0) + 1

        # Get query parameters
        as_attachment = request.args.get('as_attachment', 'false').lower() == 'true'

        processing_time = (time.perf_counter() - start_time) * 1000

        return send_file(
            file_path,
            as_attachment=as_attachment,
            download_name=file_info["original_name"] if as_attachment else None,
            mimetype=file_info["content_type"]
        )

    @app.route('/stream/<file_id>')
    def stream_file(file_id):
        """Stream file in chunks"""
        start_time = time.perf_counter()

        if file_id not in file_store["uploaded_files"]:
            return jsonify({"error": "File not found"}), 404

        file_info = file_store["uploaded_files"][file_id]
        file_path = UPLOAD_DIR / file_info["filename"]

        if not file_path.exists():
            return jsonify({"error": "File not found on disk"}), 404

        # Get chunk size from query params
        chunk_size = int(request.args.get('chunk_size', 8192))
        chunk_size = max(1024, min(chunk_size, 1048576))  # Between 1KB and 1MB

        def generate():
            with open(file_path, 'rb') as f:
                while True:
                    chunk = f.read(chunk_size)
                    if not chunk:
                        break
                    yield chunk

        # Update download stats
        file_info["download_count"] += 1

        processing_time = (time.perf_counter() - start_time) * 1000

        return Response(
            generate(),
            mimetype=file_info["content_type"] or "application/octet-stream",
            headers={
                "X-Processing-Time": str(round(processing_time, 3)),
                "X-Framework": "flask",
                "X-Chunk-Size": str(chunk_size)
            }
        )

    # ==========================================
    # FILE MANAGEMENT ENDPOINTS
    # ==========================================

    @app.route('/files')
    def list_files():
        """List uploaded files with filtering"""
        start_time = time.perf_counter()

        # Get query parameters
        category = request.args.get('category')
        limit = int(request.args.get('limit', 50))
        offset = int(request.args.get('offset', 0))

        limit = max(1, min(limit, 1000))
        offset = max(0, offset)

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

        return jsonify({
            "files": paginated_files,
            "total": total_count,
            "limit": limit,
            "offset": offset,
            "processing_time_ms": round(processing_time, 3),
            "framework": "flask"
        })

    @app.route('/files/<file_id>/info')
    def get_file_info(file_id):
        """Get detailed file information"""
        start_time = time.perf_counter()

        if file_id not in file_store["uploaded_files"]:
            return jsonify({"error": "File not found"}), 404

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

        return jsonify({
            "file": file_info,
            "processing_time_ms": round(processing_time, 3),
            "framework": "flask"
        })

    @app.route('/files/<file_id>', methods=['DELETE'])
    def delete_file(file_id):
        """Delete file"""
        start_time = time.perf_counter()

        if file_id not in file_store["uploaded_files"]:
            return jsonify({"error": "File not found"}), 404

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

        return jsonify({
            "deleted": True,
            "file_id": file_id,
            "deleted_from_disk": deleted_from_disk,
            "processing_time_ms": round(processing_time, 3),
            "framework": "flask"
        })

    # ==========================================
    # FILE PROCESSING ENDPOINTS
    # ==========================================

    @app.route('/process/<file_id>', methods=['POST'])
    def process_file(file_id):
        """Process file with specified operation"""
        start_time = time.perf_counter()

        if file_id not in file_store["uploaded_files"]:
            return jsonify({"error": "File not found"}), 404

        file_info = file_store["uploaded_files"][file_id]
        file_path = UPLOAD_DIR / file_info["filename"]

        if not file_path.exists():
            return jsonify({"error": "File not found on disk"}), 404

        # Get processing parameters
        operation = request.args.get('operation')
        if operation not in ['resize', 'compress', 'convert', 'analyze']:
            return jsonify({"error": "Invalid operation"}), 400

        params_str = request.args.get('params')
        processing_params = {}
        if params_str:
            try:
                processing_params = json.loads(params_str)
            except:
                processing_params = {"raw_params": params_str}

        # Schedule processing
        task_id = str(uuid.uuid4())
        executor.submit(
            process_file_operation,
            file_id, file_path, operation, processing_params, task_id, file_store
        )

        processing_time = (time.perf_counter() - start_time) * 1000

        return jsonify({
            "processing_started": True,
            "task_id": task_id,
            "operation": operation,
            "file_id": file_id,
            "processing_time_ms": round(processing_time, 3),
            "framework": "flask"
        })

    @app.route('/stats')
    def get_file_stats():
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

        return jsonify({
            "stats": stats,
            "processing_time_ms": round(processing_time, 3),
            "framework": "flask"
        })

    @app.route('/health')
    def health():
        """Health check"""
        return jsonify({
            "status": "healthy",
            "framework": "flask",
            "features": ["file_upload", "file_download", "file_streaming", "background_processing"],
            "upload_dir": str(UPLOAD_DIR),
            "file_count": len(file_store["uploaded_files"])
        })

    # Error handlers
    @app.errorhandler(413)
    def request_entity_too_large(error):
        return jsonify({"error": "File too large"}), 413

    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({"error": "Bad request"}), 400

    @app.errorhandler(404)
    def not_found(error):
        return jsonify({"error": "Not found"}), 404

    return app


# =====================================================
# BACKGROUND PROCESSING FUNCTIONS
# =====================================================

def process_uploaded_file(file_id: str, file_path: Path, file_store: Dict):
    """Background task: Process uploaded file"""
    # Simulate file processing
    # Removed artificial delay for benchmarking

    if file_id in file_store["uploaded_files"]:
        file_store["uploaded_files"][file_id]["processed"] = True
        file_store["uploaded_files"][file_id]["processing_completed"] = datetime.now().isoformat()

    print(f"File processed: {file_id}")

def process_file_batch(file_ids: List[str], file_store: Dict):
    """Background task: Process batch of files"""
    # Simulate batch processing
    # Removed artificial delay for benchmarking)

    for file_id in file_ids:
        if file_id in file_store["uploaded_files"]:
            file_store["uploaded_files"][file_id]["processed"] = True
            file_store["uploaded_files"][file_id]["batch_processed"] = True

    print(f"Batch processed: {len(file_ids)} files")

def process_file_operation(file_id: str, file_path: Path, operation: str, params: dict, task_id: str, file_store: Dict):
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
    parser = argparse.ArgumentParser(description='Flask file operations benchmark server')
    parser.add_argument('--host', default='127.0.0.1', help='Host to bind to')
    parser.add_argument('--port', type=int, default=8302, help='Port to bind to')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')

    args = parser.parse_args()

    app = create_flask_file_server()

    print(f"🚀 Starting Flask file operations benchmark server on {args.host}:{args.port}")
    print("File operation endpoints:")
    print("  POST /upload/single            - Upload single file")
    print("  POST /upload/multiple          - Upload multiple files")
    print("  GET  /download/<file_id>       - Download file")
    print("  GET  /stream/<file_id>         - Stream file")
    print("  GET  /files                    - List files")
    print("  GET  /files/<file_id>/info     - Get file info")
    print("  DELETE /files/<file_id>        - Delete file")
    print("  POST /process/<file_id>        - Process file")
    print("  GET  /stats                    - File statistics")
    print("  GET  /health                   - Health check")
    print()

    app.run(host=args.host, port=args.port, debug=args.debug, threaded=True)


if __name__ == "__main__":
    main()

# Create app instance for WSGI servers like gunicorn
app = create_flask_file_server()
