File Handling
=============

Catzilla provides robust file handling capabilities for both file uploads and static file serving, with built-in optimizations for performance, security, and memory efficiency.

Overview
--------

Catzilla's file handling system provides:

- **Static File Serving** - High-performance static file delivery
- **File Upload Handling** - Secure and efficient file upload processing
- **Image Processing** - Built-in image manipulation and optimization
- **Security Features** - File type validation and virus scanning integration
- **Memory Optimization** - Stream-based processing for large files
- **Caching Integration** - Automatic caching for frequently accessed files
- **Range Request Support** - Partial content delivery for media files

Static File Serving
-------------------

Basic Static Files
~~~~~~~~~~~~~~~~~~

Serve static files with automatic MIME type detection:

.. code-block:: python

   from catzilla import Catzilla, Request, Response, JSONResponse, Path, Query
   from pathlib import Path as PathLib

   app = Catzilla()

   # Mount static files directory using app.mount_static()
   app.mount_static("/static", "static")

   # Alternative: Configure multiple static directories
   app.mount_static("/css", "assets/css")
   app.mount_static("/js", "assets/js")
   app.mount_static("/images", "assets/images")

   @app.get("/")
   def home(request: Request) -> Response:
       """Serve page that uses static files"""
       html_content = """
       <!DOCTYPE html>
       <html>
       <head>
           <link rel="stylesheet" href="/css/style.css">
       </head>
       <body>
           <h1>Welcome to Catzilla</h1>
           <img src="/images/logo.png" alt="Logo">
           <script src="/js/app.js"></script>
       </body>
       </html>
       """
       return Response(
           body=html_content,
           content_type="text/html"
       )

   if __name__ == "__main__":
       print("🚀 Starting static file server...")
       print("Try: http://localhost:8000/")
       app.listen(port=8000)

Advanced Static Configuration
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Configure static files with caching and compression:

.. code-block:: python

   from catzilla import Catzilla, Request, Response, Path, Query
   import mimetypes
   from pathlib import Path as PathLib

   app = Catzilla()

   # Mount static directories with advanced configuration
   app.mount_static(
       "/assets",
       "public",
       index_file="index.html",
       enable_hot_cache=True,
       cache_size_mb=100,
       cache_ttl_seconds=3600,  # Cache for 1 hour
       enable_compression=True,
       enable_etags=True,
       enable_range_requests=True,  # Support for video/audio streaming
       max_file_size=100 * 1024 * 1024,  # 100MB max
       enable_directory_listing=True,
       enable_hidden_files=False
   )

   # Serve single-page applications (SPA)
   @app.get("/app/{path:path}")
   def spa_handler(
       request: Request,
       path: str = Path(..., description="SPA route path")
   ) -> Response:
       """Serve SPA with fallback to index.html"""
       file_path = PathLib("dist") / path

       if file_path.exists() and file_path.is_file():
           # Serve the requested file
           content_type, _ = mimetypes.guess_type(str(file_path))
           with open(file_path, 'rb') as f:
               content = f.read()

           return Response(
               body=content.decode('utf-8', errors='ignore'),
               content_type=content_type or "application/octet-stream",
               headers={"Content-Length": str(len(content))}
           )
       else:
           # Fallback to index.html for SPA routing
           with open("dist/index.html", 'rb') as f:
               content = f.read()
           return Response(
               body=content.decode('utf-8', errors='ignore'),
               content_type="text/html",
               headers={"Content-Length": str(len(content))}
           )

   if __name__ == "__main__":
       print("🚀 Starting advanced static file server...")
       print("Try: http://localhost:8000/assets/")
       app.listen(port=8000)

File Upload Handling
--------------------

Basic File Uploads
~~~~~~~~~~~~~~~~~~

Handle single and multiple file uploads:

.. code-block:: python

   from catzilla import Catzilla, Request, Response, JSONResponse, UploadFile, File, Form, Path, Query
   from pathlib import Path as PathLib
   import uuid
   import mimetypes

   app = Catzilla()

   # Configure upload directory
   UPLOAD_DIR = PathLib("uploads")
   UPLOAD_DIR.mkdir(exist_ok=True)

   @app.post("/upload")
   def upload_file(
       request: Request,
       file: UploadFile = File(max_size="10MB"),
       description: str = Form("")
   ) -> Response:
       """Handle single file upload"""

       # Validate file
       if not file.filename:
           return JSONResponse({"error": "No file selected"}, status_code=400)

       try:
           # Save file using Catzilla's save_to method
           saved_path = file.save_to(str(UPLOAD_DIR), stream=True)

           # Get file content for additional info
           file_content = file.read()

           return JSONResponse({
               "message": "File uploaded successfully",
               "filename": file.filename,
               "size": file.size,
               "content_type": file.content_type,
               "saved_path": saved_path,
               "description": description,
               "upload_speed_mbps": getattr(file, 'upload_speed_mbps', 0)
           })

       except Exception as e:
           return JSONResponse(
               {"error": f"Upload failed: {str(e)}"},
               status_code=500
           )

   @app.post("/upload-multiple")
   def upload_multiple_files(
       request: Request,
       files: list[UploadFile] = File(max_files=5, max_size="10MB"),
       description: str = Form("")
   ) -> Response:
       """Handle multiple file uploads"""

       if not files:
           return JSONResponse({"error": "No files selected"}, status_code=400)

       uploaded_files = []

       for file in files:
           if not file.filename:
               continue

           try:
               # Save file using Catzilla's save_to method
               saved_path = file.save_to(str(UPLOAD_DIR), stream=True)

               uploaded_files.append({
                   "filename": file.filename,
                   "size": file.size,
                   "content_type": file.content_type,
                   "saved_path": saved_path,
                   "upload_speed_mbps": getattr(file, 'upload_speed_mbps', 0)
               })

           except Exception as e:
               uploaded_files.append({
                   "filename": file.filename,
                   "error": str(e)
               })

       return JSONResponse({
           "message": f"Uploaded {len(uploaded_files)} files",
           "files": uploaded_files,
           "description": description
       })

   if __name__ == "__main__":
       print("🚀 Starting file upload server...")
       print("Try: curl -X POST -F 'file=@example.txt' http://localhost:8000/upload")
       app.listen(port=8000)

File Validation and Security
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Implement comprehensive file validation:

.. code-block:: python

   from catzilla import Catzilla, Request, Response, JSONResponse, UploadFile, File, Form, Path, Query
   from catzilla.exceptions import FileSizeError, MimeTypeError
   import hashlib
   from pathlib import Path as PathLib
   import uuid

   app = Catzilla()

   UPLOAD_DIR = PathLib("uploads")
   UPLOAD_DIR.mkdir(exist_ok=True)

   # Allowed file types by category
   ALLOWED_TYPES = {
       "image": ["image/jpeg", "image/png", "image/gif", "image/webp"],
       "document": ["application/pdf", "text/plain", "application/json"],
       "video": ["video/mp4", "video/avi", "video/mov"],
   }

   def validate_file_type(file: UploadFile, category: str) -> bool:
       """Validate file type for category"""
       allowed_types = ALLOWED_TYPES.get(category, [])
       return not allowed_types or file.content_type in allowed_types

   @app.post("/upload-secure")
   def upload_secure_file(
       request: Request,
       file: UploadFile = File(max_size="50MB"),
       category: str = Form("image"),
       description: str = Form("")
   ) -> Response:
       """Upload with comprehensive security validation"""

       # Generate upload ID
       upload_id = str(uuid.uuid4())

       try:
           # Validate file type for category
           if not validate_file_type(file, category):
               return JSONResponse({
                   "success": False,
                   "upload_id": upload_id,
                   "error": f"Content type {file.content_type} not allowed for {category}",
                   "allowed_types": ALLOWED_TYPES.get(category, [])
               }, status_code=415)

           # Save file using Catzilla's save_to method
           saved_path = file.save_to(str(UPLOAD_DIR), stream=True)

           # Get file content for checksum
           file_content = file.read()
           checksum = hashlib.sha256(file_content).hexdigest()

           return JSONResponse({
               "success": True,
               "upload_id": upload_id,
               "filename": file.filename,
               "size": file.size,
               "content_type": file.content_type,
               "category": category,
               "description": description,
               "checksum": checksum,
               "saved_path": saved_path,
               "validation": "passed"
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
           return JSONResponse({
               "success": False,
               "upload_id": upload_id,
               "error": str(e)
           }, status_code=500)

   if __name__ == "__main__":
       print("🚀 Starting secure upload server...")
       print("Try: curl -X POST -F 'file=@example.jpg' -F 'category=image' http://localhost:8000/upload-secure")
       app.listen(port=8000)

Image Processing
----------------

Basic Image Upload and Processing
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Handle image uploads with basic processing:

.. code-block:: python

   from catzilla import Catzilla, Request, Response, JSONResponse, UploadFile, File, Form, Path, Query
   from pathlib import Path as PathLib
   import uuid
   import hashlib
   import mimetypes

   app = Catzilla()

   # Create directories
   UPLOAD_DIR = PathLib("uploads")
   IMAGES_DIR = UPLOAD_DIR / "images"
   IMAGES_DIR.mkdir(parents=True, exist_ok=True)

   # Image file types
   IMAGE_TYPES = ["image/jpeg", "image/png", "image/gif", "image/webp"]

   @app.post("/upload-image")
   def upload_and_process_image(
       request: Request,
       file: UploadFile = File(max_size="10MB"),
       description: str = Form(""),
       public: bool = Form(False)
   ) -> Response:
       """Upload and process image file"""

       # Validate image file
       if file.content_type not in IMAGE_TYPES:
           return JSONResponse({
               "error": f"Content type {file.content_type} not allowed for images",
               "allowed_types": IMAGE_TYPES
           }, status_code=415)

       upload_id = str(uuid.uuid4())

       try:
           # Save image using Catzilla's save_to method
           saved_path = file.save_to(str(IMAGES_DIR), stream=True)

           # Get file content for checksum
           file_content = file.read()
           checksum = hashlib.sha256(file_content).hexdigest()

           # Create image info
           image_info = {
               "upload_id": upload_id,
               "filename": file.filename,
               "size": file.size,
               "content_type": file.content_type,
               "description": description,
               "public": public,
               "checksum": checksum,
               "saved_path": saved_path,
               "upload_speed_mbps": getattr(file, 'upload_speed_mbps', 0)
           }

           return JSONResponse({
               "message": "Image uploaded successfully",
               "image_info": image_info
           })

       except Exception as e:
           return JSONResponse({
               "error": f"Image upload failed: {str(e)}"
           }, status_code=500)

   @app.get("/images/{upload_id}")
   def get_image(
       request: Request,
       upload_id: str = Path(..., description="Image upload ID")
   ) -> Response:
       """Serve uploaded image"""

       # In a real app, you'd look up the file path from database
       # For this example, we'll search the images directory
       for image_file in IMAGES_DIR.glob("*"):
           if upload_id in image_file.name:
               content_type, _ = mimetypes.guess_type(str(image_file))

               with open(image_file, 'rb') as f:
                   image_content = f.read()

               return Response(
                   body=image_content.decode('latin-1'),  # Binary safe encoding
                   content_type=content_type or "image/jpeg",
                   headers={
                       "Content-Length": str(len(image_content)),
                       "X-Upload-ID": upload_id
                   }
               )

       return JSONResponse({"error": "Image not found"}, status_code=404)

   if __name__ == "__main__":
       print("🚀 Starting image upload server...")
       print("Try: curl -X POST -F 'file=@image.jpg' http://localhost:8000/upload-image")
       app.listen(port=8000)

Advanced File Operations
------------------------

File Organization and Management
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Organize uploaded files by category and date:

.. code-block:: python

   from catzilla import Catzilla, Request, Response, JSONResponse, UploadFile, File, Form, Path, Query
   from pathlib import Path as PathLib
   import uuid
   import hashlib
   import mimetypes
   from datetime import datetime
   import json

   app = Catzilla()

   # Create organized upload directories
   UPLOAD_BASE_DIR = PathLib("uploads")
   UPLOAD_DIRS = {
       "images": UPLOAD_BASE_DIR / "images",
       "documents": UPLOAD_BASE_DIR / "documents",
       "videos": UPLOAD_BASE_DIR / "videos",
       "other": UPLOAD_BASE_DIR / "other"
   }

   for dir_path in UPLOAD_DIRS.values():
       dir_path.mkdir(parents=True, exist_ok=True)

   # File tracking
   file_registry = {}

   @app.post("/upload/organized")
   def upload_organized_file(
       request: Request,
       file: UploadFile = File(max_size="50MB"),
       category: str = Form("other"),
       tags: str = Form("[]"),  # JSON array of tags
       description: str = Form("")
   ) -> Response:
       """Upload file with organized storage"""

       # Parse tags
       try:
           tag_list = json.loads(tags) if tags else []
           if not isinstance(tag_list, list):
               tag_list = []
       except:
           tag_list = []

       # Generate file ID
       file_id = str(uuid.uuid4())

       try:
           # Determine storage directory
           storage_dir = UPLOAD_DIRS.get(category, UPLOAD_DIRS["other"])

           # Create date-based subdirectory
           date_dir = storage_dir / datetime.now().strftime("%Y/%m/%d")
           date_dir.mkdir(parents=True, exist_ok=True)

           # Save file using Catzilla's save_to method
           saved_path = file.save_to(str(date_dir), stream=True)

           # Get file content for checksum
           file_content = file.read()
           checksum = hashlib.sha256(file_content).hexdigest()

           # Create file record
           file_record = {
               "file_id": file_id,
               "filename": file.filename,
               "size": file.size,
               "content_type": file.content_type,
               "category": category,
               "tags": tag_list,
               "description": description,
               "checksum": checksum,
               "saved_path": saved_path,
               "uploaded_at": datetime.now().isoformat(),
               "upload_speed_mbps": getattr(file, 'upload_speed_mbps', 0)
           }

           # Store in registry
           file_registry[file_id] = file_record

           return JSONResponse({
               "success": True,
               "file_id": file_id,
               "file_record": file_record
           })

       except Exception as e:
           return JSONResponse({
               "success": False,
               "file_id": file_id,
               "error": str(e)
           }, status_code=500)

   @app.get("/files/{file_id}")
   def get_file_info(
       request: Request,
       file_id: str = Path(..., description="File ID")
   ) -> Response:
       """Get file information"""

       if file_id not in file_registry:
           return JSONResponse({"error": "File not found"}, status_code=404)

       return JSONResponse(file_registry[file_id])

   @app.get("/files")
   def list_files(
       request: Request,
       category: str = Query(None, description="Filter by category"),
       limit: int = Query(50, ge=1, le=100, description="Maximum number of files to return")
   ) -> Response:
       """List uploaded files with filtering"""

       files = []
       for file_record in file_registry.values():
           if category and file_record["category"] != category:
               continue
           files.append(file_record)

       # Sort by upload time (newest first)
       files.sort(key=lambda x: x["uploaded_at"], reverse=True)

       return JSONResponse({
           "files": files[:limit],
           "total_shown": min(len(files), limit),
           "total_files": len(files),
           "filter_category": category
       })

   if __name__ == "__main__":
       print("🚀 Starting organized file upload server...")
       print("Try: curl -X POST -F 'file=@example.txt' -F 'category=documents' http://localhost:8000/upload/organized")
       app.listen(port=8000)

File Download and Serving
--------------------------

Secure File Downloads
~~~~~~~~~~~~~~~~~~~~~

Serve files with access control:

.. code-block:: python

   from catzilla import Catzilla, Request, Response, JSONResponse, Path, Query
   import mimetypes
   from pathlib import Path as PathLib
   import hashlib

   app = Catzilla()

   UPLOAD_DIR = PathLib("uploads")
   UPLOAD_DIR.mkdir(exist_ok=True)

   # File registry for tracking uploaded files
   file_registry = {}

   @app.get("/download/{file_id}")
   def download_file(
       request: Request,
       file_id: str = Path(..., description="File ID to download")
   ) -> Response:
       """Secure file download with access control"""

       # Validate file_id (prevent path traversal)
       if ".." in file_id or "/" in file_id or "\\" in file_id:
           return JSONResponse({"error": "Invalid file ID"}, status_code=400)

       # Look up file in registry
       if file_id not in file_registry:
           return JSONResponse({"error": "File not found"}, status_code=404)

       file_record = file_registry[file_id]
       file_path = PathLib(file_record["saved_path"])

       if not file_path.exists():
           return JSONResponse({"error": "File not found on disk"}, status_code=404)

       # Optional: Check user permissions here
       # if not user_has_access(request.user, file_id):
       #     return JSONResponse({"error": "Access denied"}, status_code=403)

       # Determine content type
       content_type = file_record.get("content_type")
       if not content_type:
           content_type, _ = mimetypes.guess_type(str(file_path))
           content_type = content_type or "application/octet-stream"

       # Read file content
       if content_type.startswith('text/') or content_type == 'application/json':
           with open(file_path, "r", encoding="utf-8") as f:
               file_content = f.read()
           file_bytes = file_content.encode("utf-8")
       else:
           with open(file_path, "rb") as f:
               file_bytes = f.read()
           file_content = file_bytes.decode("utf-8", errors="ignore")

       return Response(
           body=file_content,
           content_type=content_type,
           headers={
               "Content-Disposition": f'attachment; filename="{file_record["filename"]}"',
               "Content-Length": str(len(file_bytes)),
               "X-File-ID": file_id,
               "X-File-Checksum": file_record.get("checksum", "")
           }
       )

   @app.get("/view/{file_id}")
   def view_file(
       request: Request,
       file_id: str = Path(..., description="File ID to view")
   ) -> Response:
       """View file inline (for images, PDFs, etc.)"""

       # Validate file_id
       if ".." in file_id or "/" in file_id:
           return JSONResponse({"error": "Invalid file ID"}, status_code=400)

       # Look up file in registry
       if file_id not in file_registry:
           return JSONResponse({"error": "File not found"}, status_code=404)

       file_record = file_registry[file_id]
       file_path = PathLib(file_record["saved_path"])

       if not file_path.exists():
           return JSONResponse({"error": "File not found on disk"}, status_code=404)

       content_type = file_record.get("content_type", "application/octet-stream")

       # Read file content
       if content_type.startswith('text/') or content_type == 'application/json':
           with open(file_path, "r", encoding="utf-8") as f:
               file_content = f.read()
           file_bytes = file_content.encode("utf-8")
       else:
           with open(file_path, "rb") as f:
               file_bytes = f.read()
           file_content = file_bytes.decode("latin-1")  # Binary safe encoding

       return Response(
           body=file_content,
           content_type=content_type,
           headers={
               "Content-Disposition": f'inline; filename="{file_record["filename"]}"',
               "Content-Length": str(len(file_bytes)),
               "X-File-ID": file_id
           }
       )

   if __name__ == "__main__":
       print("🚀 Starting file download server...")
       print("Try: curl http://localhost:8000/download/{file_id}")
       app.listen(port=8000)

File Management API
~~~~~~~~~~~~~~~~~~~

Complete file management endpoints:

.. code-block:: python

   from catzilla import Catzilla, Request, Response, JSONResponse, Path, Query
   import mimetypes
   from pathlib import Path as PathLib
   from datetime import datetime

   app = Catzilla()

   UPLOAD_DIR = PathLib("uploads")
   file_registry = {}  # In production, use a database

   @app.get("/files")
   def list_files(
       request: Request,
       category: str = Query(None, description="Filter by category"),
       limit: int = Query(50, ge=1, le=100, description="Maximum number of files to return")
   ) -> Response:
       """List uploaded files"""

       files = []
       for file_id, file_record in file_registry.items():
           # Filter by category if specified
           if category and file_record.get("category") != category:
               continue

           # Check if file still exists
           file_path = PathLib(file_record["saved_path"])
           if not file_path.exists():
               continue

           file_stat = file_path.stat()
           files.append({
               "file_id": file_id,
               "filename": file_record["filename"],
               "size": file_record["size"],
               "content_type": file_record["content_type"],
               "category": file_record.get("category", "other"),
               "description": file_record.get("description", ""),
               "uploaded_at": file_record["uploaded_at"],
               "modified": datetime.fromtimestamp(file_stat.st_mtime).isoformat()
           })

       # Sort by upload time (newest first)
       files.sort(key=lambda x: x["uploaded_at"], reverse=True)

       return JSONResponse({
           "files": files[:limit],
           "total_shown": min(len(files), limit),
           "total_files": len(files),
           "filter_category": category
       })

   @app.delete("/files/{file_id}")
   def delete_file(
       request: Request,
       file_id: str = Path(..., description="File ID to delete")
   ) -> Response:
       """Delete uploaded file"""

       # Validate file_id
       if ".." in file_id or "/" in file_id:
           return JSONResponse({"error": "Invalid file ID"}, status_code=400)

       if file_id not in file_registry:
           return JSONResponse({"error": "File not found"}, status_code=404)

       file_record = file_registry[file_id]
       file_path = PathLib(file_record["saved_path"])

       try:
           if file_path.exists():
               file_path.unlink()

           # Remove from registry
           del file_registry[file_id]

           return JSONResponse({
               "message": f"File {file_record['filename']} deleted successfully",
               "file_id": file_id
           })
       except Exception as e:
           return JSONResponse({
               "error": f"Delete failed: {str(e)}"
           }, status_code=500)

   @app.get("/files/{file_id}/info")
   def get_file_info(
       request: Request,
       file_id: str = Path(..., description="File ID")
   ) -> Response:
       """Get detailed file information"""

       # Validate file_id
       if ".." in file_id or "/" in file_id:
           return JSONResponse({"error": "Invalid file ID"}, status_code=400)

       if file_id not in file_registry:
           return JSONResponse({"error": "File not found"}, status_code=404)

       file_record = file_registry[file_id]
       file_path = PathLib(file_record["saved_path"])

       if not file_path.exists():
           return JSONResponse({"error": "File not found on disk"}, status_code=404)

       file_stat = file_path.stat()

       # Additional info for images
       extra_info = {}
       content_type = file_record.get("content_type", "")
       if content_type and content_type.startswith("image/"):
           extra_info["is_image"] = True
           # Note: In a real app, you might use PIL to get image dimensions
           # For this example, we'll just mark it as an image

       return JSONResponse({
           "file_id": file_id,
           "filename": file_record["filename"],
           "size": file_record["size"],
           "content_type": content_type,
           "category": file_record.get("category", "other"),
           "description": file_record.get("description", ""),
           "tags": file_record.get("tags", []),
           "checksum": file_record.get("checksum", ""),
           "uploaded_at": file_record["uploaded_at"],
           "modified": datetime.fromtimestamp(file_stat.st_mtime).isoformat(),
           "file_path": str(file_path),
           **extra_info
       })

   if __name__ == "__main__":
       print("🚀 Starting file management server...")
       print("Try: curl http://localhost:8000/files")
       app.listen(port=8000)

Best Practices
--------------

Security Guidelines
~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from catzilla import UploadFile, File, Form, Path, Query
   from catzilla.exceptions import FileSizeError, MimeTypeError
   import uuid
   from pathlib import Path as PathLib

   # ✅ Good: Validate file types and use constraints
   def upload_with_validation(
       file: UploadFile = File(max_size="10MB"),
       category: str = Form("image")
   ):
       # Catzilla automatically validates file size
       # Additional content type validation
       allowed_types = {
           "image": ["image/jpeg", "image/png", "image/gif"],
           "document": ["application/pdf", "text/plain"]
       }

       if category in allowed_types and file.content_type not in allowed_types[category]:
           raise MimeTypeError(f"Invalid file type for {category}")

       return file.save_to(f"uploads/{category}", stream=True)

   # ✅ Good: Use unique filenames and organized storage
   def save_file_securely(file: UploadFile, category: str = "uploads"):
       file_id = str(uuid.uuid4())
       file_extension = PathLib(file.filename).suffix

       # Create date-based directory structure
       from datetime import datetime
       date_path = datetime.now().strftime("%Y/%m/%d")
       storage_path = f"uploads/{category}/{date_path}"

       return file.save_to(storage_path, stream=True)

   # ✅ Good: Handle file upload exceptions
   try:
       saved_path = file.save_to("uploads", stream=True)
   except FileSizeError as e:
       return JSONResponse({"error": "File too large"}, status_code=413)
   except MimeTypeError as e:
       return JSONResponse({"error": "Invalid file type"}, status_code=415)
   except Exception as e:
       return JSONResponse({"error": str(e)}, status_code=500)

Performance Tips
~~~~~~~~~~~~~~~~

.. code-block:: python

   # ✅ Good: Use streaming for large files
   from catzilla import UploadFile, File

   def upload_large_file(file: UploadFile = File(max_size="100MB")):
       # Catzilla automatically streams large files when stream=True
       saved_path = file.save_to("uploads/large", stream=True)

       # Access upload performance metrics
       upload_speed = getattr(file, 'upload_speed_mbps', 0)
       chunks_processed = getattr(file, 'chunks_count', 0)

       return {
           "saved_path": saved_path,
           "upload_speed_mbps": upload_speed,
           "chunks_processed": chunks_processed
       }

   # ✅ Good: Configure static files with caching
   app.mount_static(
       "/static",
       "static",
       enable_hot_cache=True,
       cache_size_mb=100,
       cache_ttl_seconds=3600,  # 1 hour
       enable_compression=True,
       enable_etags=True
   )

   # ✅ Good: Use appropriate file constraints
   # For images
   image_file: UploadFile = File(max_size="10MB")

   # For documents
   document_file: UploadFile = File(max_size="50MB")

   # For multiple files
   files: list[UploadFile] = File(max_files=10, max_size="25MB")

This comprehensive file handling system provides secure, efficient, and scalable file operations for your Catzilla applications.
