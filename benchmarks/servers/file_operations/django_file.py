#!/usr/bin/env python3
"""
Django File Operations Benchmark Server
Advanced file upload, download, streaming, and processing capabilities
"""

import os
import sys
import json
import time
import shutil
import hashlib
import mimetypes
import tempfile
import zipfile
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Union, BinaryIO
from threading import Thread, Lock
from queue import Queue
import logging

# Django setup
import django
from django.conf import settings
from django.core.wsgi import get_wsgi_application
from django.http import JsonResponse, HttpResponse, FileResponse, StreamingHttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.urls import path
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.utils.decorators import method_decorator
from django.views import View
import django.core.files.uploadedfile

# Add parent directory to path for shared imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import shared utilities
try:
    from shared.file_endpoints import FILE_ENDPOINTS
    from shared.config import get_port
except ImportError:
    # Fallback if shared modules not available
    FILE_ENDPOINTS = []
    def get_port(framework, category): return 8000

# Configure Django settings
if not settings.configured:
    settings.configure(
        DEBUG=True,
        SECRET_KEY='django-benchmark-secret-key',
        ALLOWED_HOSTS=['*'],
        ROOT_URLCONF=__name__,
        MEDIA_ROOT='/tmp/django_uploads',
        MEDIA_URL='/media/',
        FILE_UPLOAD_MAX_MEMORY_SIZE=100 * 1024 * 1024,  # 100MB
        DATA_UPLOAD_MAX_MEMORY_SIZE=100 * 1024 * 1024,  # 100MB
        USE_TZ=True,
        LOGGING={
            'version': 1,
            'disable_existing_loggers': False,
            'handlers': {
                'console': {
                    'class': 'logging.StreamHandler',
                },
            },
            'root': {
                'handlers': ['console'],
                'level': 'INFO',
            },
        }
    )

django.setup()

# Configure logging
logger = logging.getLogger(__name__)

# Ensure upload directory exists
os.makedirs(settings.MEDIA_ROOT, exist_ok=True)

# Global state for file operations
file_storage: Dict[str, Dict] = {}
storage_lock = Lock()
processing_queue = Queue()
processing_results: Dict[str, Dict] = {}

# Processing stats
stats = {
    'files_uploaded': 0,
    'files_downloaded': 0,
    'files_streamed': 0,
    'files_processed': 0,
    'bytes_transferred': 0,
    'errors': 0,
    'processing_time': 0.0
}
stats_lock = Lock()

def update_stats(key: str, value: Union[int, float] = 1):
    """Thread-safe stats update"""
    with stats_lock:
        if key in stats:
            stats[key] += value

def allowed_file(filename: str, allowed_extensions: set = None) -> bool:
    """Check if file extension is allowed"""
    if allowed_extensions is None:
        allowed_extensions = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'doc', 'docx', 'zip', 'csv', 'json', 'xml'}

    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in allowed_extensions

def get_file_info(file_path: str) -> Dict:
    """Get comprehensive file information"""
    try:
        stat = os.stat(file_path)
        return {
            'filename': os.path.basename(file_path),
            'size': stat.st_size,
            'modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
            'mimetype': mimetypes.guess_type(file_path)[0] or 'application/octet-stream',
            'hash': calculate_file_hash(file_path) if stat.st_size < 10 * 1024 * 1024 else None
        }
    except Exception as e:
        logger.error(f"Error getting file info: {e}")
        return {}

def calculate_file_hash(file_path: str, algorithm: str = 'md5') -> str:
    """Calculate file hash"""
    hash_obj = hashlib.new(algorithm)
    try:
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_obj.update(chunk)
        return hash_obj.hexdigest()
    except Exception as e:
        logger.error(f"Error calculating hash: {e}")
        return ""

def process_file_background(file_id: str, operation: str, params: Dict):
    """Background file processing"""
    try:
        start_time = time.time()

        with storage_lock:
            file_info = file_storage.get(file_id)

        if not file_info:
            processing_results[file_id] = {'error': 'File not found', 'status': 'failed'}
            return

        file_path = file_info['path']
        result = {'status': 'processing', 'progress': 0}

        if operation == 'compress':
            result = compress_file(file_path, params)
        elif operation == 'convert':
            result = convert_file(file_path, params)
        elif operation == 'analyze':
            result = analyze_file(file_path, params)
        elif operation == 'thumbnail':
            result = generate_thumbnail(file_path, params)
        else:
            result = {'error': f'Unknown operation: {operation}', 'status': 'failed'}

        result['processing_time'] = time.time() - start_time
        processing_results[file_id] = result

        update_stats('files_processed')
        update_stats('processing_time', result['processing_time'])

    except Exception as e:
        logger.error(f"Background processing error: {e}")
        processing_results[file_id] = {'error': str(e), 'status': 'failed'}

def compress_file(file_path: str, params: Dict) -> Dict:
    """Compress file to ZIP"""
    try:
        output_path = file_path + '.zip'
        with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            zf.write(file_path, os.path.basename(file_path))

        return {
            'status': 'completed',
            'output_path': output_path,
            'compression_ratio': os.path.getsize(output_path) / os.path.getsize(file_path),
            'original_size': os.path.getsize(file_path),
            'compressed_size': os.path.getsize(output_path)
        }
    except Exception as e:
        return {'error': str(e), 'status': 'failed'}

def convert_file(file_path: str, params: Dict) -> Dict:
    """Mock file conversion"""
    try:
        target_format = params.get('format', 'txt')
        output_path = f"{file_path}.{target_format}"
        shutil.copy2(file_path, output_path)

        return {
            'status': 'completed',
            'output_path': output_path,
            'target_format': target_format,
            'size': os.path.getsize(output_path)
        }
    except Exception as e:
        return {'error': str(e), 'status': 'failed'}

def analyze_file(file_path: str, params: Dict) -> Dict:
    """Analyze file content and metadata"""
    try:
        analysis = {
            'status': 'completed',
            'file_info': get_file_info(file_path),
            'analysis': {
                'line_count': 0,
                'word_count': 0,
                'char_count': 0,
                'encoding': 'unknown'
            }
        }

        if os.path.getsize(file_path) < 1024 * 1024:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    analysis['analysis']['line_count'] = content.count('\n')
                    analysis['analysis']['word_count'] = len(content.split())
                    analysis['analysis']['char_count'] = len(content)
                    analysis['analysis']['encoding'] = 'utf-8'
            except:
                analysis['analysis']['encoding'] = 'binary'

        return analysis
    except Exception as e:
        return {'error': str(e), 'status': 'failed'}

def generate_thumbnail(file_path: str, params: Dict) -> Dict:
    """Mock thumbnail generation"""
    try:
        thumb_path = file_path + '_thumb.jpg'
        shutil.copy2(file_path, thumb_path)

        return {
            'status': 'completed',
            'thumbnail_path': thumb_path,
            'dimensions': params.get('size', '150x150'),
            'size': os.path.getsize(thumb_path)
        }
    except Exception as e:
        return {'error': str(e), 'status': 'failed'}

def streaming_file_response(file_path: str, chunk_size: int = 8192):
    """Generator for streaming file content"""
    try:
        with open(file_path, 'rb') as f:
            while True:
                chunk = f.read(chunk_size)
                if not chunk:
                    break
                yield chunk
    except Exception as e:
        logger.error(f"Stream error: {e}")
        yield b''

# Django Views

def health(request):
    """Health check endpoint"""
    return JsonResponse({
        'status': 'healthy',
        'service': 'Django File Operations Server',
        'timestamp': datetime.now().isoformat(),
        'stats': dict(stats)
    })

@csrf_exempt
@require_http_methods(["POST"])
def upload_file(request):
    """Single file upload"""
    try:
        if 'file' not in request.FILES:
            return JsonResponse({'error': 'No file provided'}, status=400)

        file = request.FILES['file']
        if not file.name:
            return JsonResponse({'error': 'No file selected'}, status=400)

        if not allowed_file(file.name):
            return JsonResponse({'error': 'File type not allowed'}, status=400)

        # Generate unique file ID and save file
        file_id = hashlib.md5(f"{file.name}{time.time()}".encode()).hexdigest()
        filename = file.name
        file_path = os.path.join(settings.MEDIA_ROOT, f"{file_id}_{filename}")

        # Save file
        with open(file_path, 'wb+') as destination:
            for chunk in file.chunks():
                destination.write(chunk)

        file_size = os.path.getsize(file_path)

        # Store file info
        file_info = {
            'id': file_id,
            'filename': filename,
            'path': file_path,
            'size': file_size,
            'uploaded_at': datetime.now().isoformat(),
            'mimetype': file.content_type or mimetypes.guess_type(filename)[0]
        }

        with storage_lock:
            file_storage[file_id] = file_info

        update_stats('files_uploaded')
        update_stats('bytes_transferred', file_size)

        return JsonResponse({
            'success': True,
            'file_id': file_id,
            'filename': filename,
            'size': file_size,
            'message': 'File uploaded successfully'
        })

    except Exception as e:
        logger.error(f"Upload error: {e}")
        update_stats('errors')
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def upload_multiple_files(request):
    """Multiple file upload"""
    try:
        files = request.FILES.getlist('files')
        if not files:
            return JsonResponse({'error': 'No files provided'}, status=400)

        uploaded_files = []
        total_size = 0

        for file in files:
            if file.name and allowed_file(file.name):
                file_id = hashlib.md5(f"{file.name}{time.time()}".encode()).hexdigest()
                filename = file.name
                file_path = os.path.join(settings.MEDIA_ROOT, f"{file_id}_{filename}")

                # Save file
                with open(file_path, 'wb+') as destination:
                    for chunk in file.chunks():
                        destination.write(chunk)

                file_size = os.path.getsize(file_path)

                file_info = {
                    'id': file_id,
                    'filename': filename,
                    'path': file_path,
                    'size': file_size,
                    'uploaded_at': datetime.now().isoformat(),
                    'mimetype': file.content_type or mimetypes.guess_type(filename)[0]
                }

                with storage_lock:
                    file_storage[file_id] = file_info

                uploaded_files.append({
                    'file_id': file_id,
                    'filename': filename,
                    'size': file_size
                })
                total_size += file_size

        update_stats('files_uploaded', len(uploaded_files))
        update_stats('bytes_transferred', total_size)

        return JsonResponse({
            'success': True,
            'files_uploaded': len(uploaded_files),
            'total_size': total_size,
            'files': uploaded_files
        })

    except Exception as e:
        logger.error(f"Multiple upload error: {e}")
        update_stats('errors')
        return JsonResponse({'error': str(e)}, status=500)

def download_file(request, file_id: str):
    """Download file by ID"""
    try:
        with storage_lock:
            file_info = file_storage.get(file_id)

        if not file_info:
            return JsonResponse({'error': 'File not found'}, status=404)

        if not os.path.exists(file_info['path']):
            return JsonResponse({'error': 'File no longer exists'}, status=404)

        update_stats('files_downloaded')
        update_stats('bytes_transferred', file_info['size'])

        response = FileResponse(
            open(file_info['path'], 'rb'),
            as_attachment=True,
            filename=file_info['filename']
        )
        response['Content-Type'] = file_info['mimetype']
        return response

    except Exception as e:
        logger.error(f"Download error: {e}")
        update_stats('errors')
        return JsonResponse({'error': str(e)}, status=500)

def stream_file(request, file_id: str):
    """Stream file content"""
    try:
        with storage_lock:
            file_info = file_storage.get(file_id)

        if not file_info:
            return JsonResponse({'error': 'File not found'}, status=404)

        if not os.path.exists(file_info['path']):
            return JsonResponse({'error': 'File no longer exists'}, status=404)

        update_stats('files_streamed')
        update_stats('bytes_transferred', file_info['size'])

        response = StreamingHttpResponse(
            streaming_file_response(file_info['path']),
            content_type=file_info['mimetype']
        )
        response['Content-Disposition'] = f'attachment; filename="{file_info["filename"]}"'
        response['Content-Length'] = str(file_info['size'])
        return response

    except Exception as e:
        logger.error(f"Stream error: {e}")
        update_stats('errors')
        return JsonResponse({'error': str(e)}, status=500)

def file_info_view(request, file_id: str):
    """Get file information"""
    try:
        with storage_lock:
            file_info = file_storage.get(file_id)

        if not file_info:
            return JsonResponse({'error': 'File not found'}, status=404)

        if os.path.exists(file_info['path']):
            detailed_info = get_file_info(file_info['path'])
            file_info.update(detailed_info)

        return JsonResponse(file_info)

    except Exception as e:
        logger.error(f"File info error: {e}")
        update_stats('errors')
        return JsonResponse({'error': str(e)}, status=500)

def list_files(request):
    """List all uploaded files"""
    try:
        with storage_lock:
            files = []
            for file_id, info in file_storage.items():
                files.append({
                    'file_id': file_id,
                    'filename': info['filename'],
                    'size': info['size'],
                    'uploaded_at': info['uploaded_at'],
                    'exists': os.path.exists(info['path'])
                })

        return JsonResponse({
            'total_files': len(files),
            'files': files
        })

    except Exception as e:
        logger.error(f"List files error: {e}")
        update_stats('errors')
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def process_file_view(request, file_id: str):
    """Start background file processing"""
    try:
        data = json.loads(request.body or '{}')
        operation = data.get('operation', 'analyze')
        params = data.get('params', {})

        with storage_lock:
            if file_id not in file_storage:
                return JsonResponse({'error': 'File not found'}, status=404)

        # Start background processing
        thread = Thread(target=process_file_background, args=(file_id, operation, params))
        thread.daemon = True
        thread.start()

        return JsonResponse({
            'success': True,
            'file_id': file_id,
            'operation': operation,
            'status': 'processing',
            'message': 'Processing started'
        })

    except Exception as e:
        logger.error(f"Process error: {e}")
        update_stats('errors')
        return JsonResponse({'error': str(e)}, status=500)

def process_status_view(request, file_id: str):
    """Get processing status"""
    try:
        result = processing_results.get(file_id, {'status': 'not_found'})
        return JsonResponse(result)

    except Exception as e:
        logger.error(f"Status error: {e}")
        update_stats('errors')
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["DELETE"])
def delete_file_view(request, file_id: str):
    """Delete file"""
    try:
        with storage_lock:
            file_info = file_storage.pop(file_id, None)

        if not file_info:
            return JsonResponse({'error': 'File not found'}, status=404)

        # Delete file from disk
        try:
            if os.path.exists(file_info['path']):
                os.remove(file_info['path'])
        except Exception as e:
            logger.warning(f"Could not delete file from disk: {e}")

        processing_results.pop(file_id, None)

        return JsonResponse({
            'success': True,
            'message': 'File deleted successfully'
        })

    except Exception as e:
        logger.error(f"Delete error: {e}")
        update_stats('errors')
        return JsonResponse({'error': str(e)}, status=500)

def get_stats_view(request):
    """Get server statistics"""
    with stats_lock:
        return JsonResponse({
            'stats': dict(stats),
            'active_files': len(file_storage),
            'processing_queue_size': processing_queue.qsize(),
            'pending_results': len(processing_results)
        })

@csrf_exempt
@require_http_methods(["POST"])
def cleanup_view(request):
    """Clean up old files and processing results"""
    try:
        cleaned_files = 0
        cleaned_results = 0

        with storage_lock:
            to_remove = []
            for file_id, info in file_storage.items():
                if not os.path.exists(info['path']):
                    to_remove.append(file_id)

            for file_id in to_remove:
                file_storage.pop(file_id, None)
                cleaned_files += 1

        for file_id in list(processing_results.keys()):
            if file_id not in file_storage:
                processing_results.pop(file_id, None)
                cleaned_results += 1

        return JsonResponse({
            'success': True,
            'cleaned_files': cleaned_files,
            'cleaned_results': cleaned_results,
            'message': 'Cleanup completed'
        })

    except Exception as e:
        logger.error(f"Cleanup error: {e}")
        update_stats('errors')
        return JsonResponse({'error': str(e)}, status=500)

# URL patterns
urlpatterns = [
    path('health/', health),
    path('upload/', upload_file),
    path('upload/multiple/', upload_multiple_files),
    path('download/<str:file_id>/', download_file),
    path('stream/<str:file_id>/', stream_file),
    path('info/<str:file_id>/', file_info_view),
    path('list/', list_files),
    path('process/<str:file_id>/', process_file_view),
    path('process/status/<str:file_id>/', process_status_view),
    path('delete/<str:file_id>/', delete_file_view),
    path('stats/', get_stats_view),
    path('cleanup/', cleanup_view),
]

application = get_wsgi_application()

if __name__ == '__main__':
    import argparse
    from django.core.management import execute_from_command_line

    parser = argparse.ArgumentParser(description='Django File Operations Benchmark Server')
    parser.add_argument('--port', type=int, default=None,
                        help='Port to run the server on')
    parser.add_argument('--host', type=str, default='127.0.0.1',
                        help='Host to bind the server to')

    args = parser.parse_args()

    # Get port from config or argument
    port = args.port or get_port('django', 'file_operations')

    print(f"Starting Django File Operations Benchmark Server on {args.host}:{port}")
    print(f"Upload folder: {settings.MEDIA_ROOT}")
    print("Available endpoints:")
    print("  POST   /upload/                - Single file upload")
    print("  POST   /upload/multiple/       - Multiple file upload")
    print("  GET    /download/<file_id>/    - Download file")
    print("  GET    /stream/<file_id>/      - Stream file")
    print("  GET    /info/<file_id>/        - Get file info")
    print("  GET    /list/                  - List all files")
    print("  POST   /process/<file_id>/     - Start file processing")
    print("  GET    /process/status/<id>/   - Get processing status")
    print("  DELETE /delete/<file_id>/      - Delete file")
    print("  GET    /stats/                 - Get server stats")
    print("  POST   /cleanup/               - Cleanup old files")
    print("  GET    /health/                - Health check")

    # Use Django's runserver command
    sys.argv = ['manage.py', 'runserver', f'{args.host}:{port}']
    execute_from_command_line(sys.argv)

# Create WSGI application instance for external servers like gunicorn
application = get_wsgi_application()
