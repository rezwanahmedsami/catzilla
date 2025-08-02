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

   from catzilla import Catzilla
   from pathlib import Path

   app = Catzilla()

   # Mount static files directory using app.mount_static()
   app.mount_static("/static", "static")

   # Alternative: Configure multiple static directories
   app.mount_static("/css", "assets/css")
   app.mount_static("/js", "assets/js")
   app.mount_static("/images", "assets/images")
           "/js": "assets/js",
           "/images": "assets/images"
       }
   )

   @app.get("/")
   def home(request):
       """Serve page that uses static files"""
       return HTMLResponse("""
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
       """)

Advanced Static Configuration
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Configure static files with caching and compression:

.. code-block:: python

   from catzilla import Catzilla

   app = Catzilla()

   # Mount static directories using app.mount_static()
   app.mount_static(
       "/assets",
       "public",
       index_file="index.html",
       cache_max_age=86400,  # Cache for 24 hours
       enable_compression=True,
       compression_types=["text/css", "text/javascript", "application/json"],
       enable_etag=True,
       enable_range_requests=True,  # Support for video/audio streaming
       security_headers={
           "X-Content-Type-Options": "nosniff",
           "X-Frame-Options": "DENY"
       }
   )

   # Serve single-page applications (SPA)
   @app.get("/app/{path:path}")
   def spa_handler(request, path: str):
       """Serve SPA with fallback to index.html"""
       file_path = Path("dist") / path

       if file_path.exists() and file_path.is_file():
           # Note: FileResponse not available in current Catzilla v0.2.0
           # Use Response with file content and appropriate headers
           with open(file_path, 'rb') as f:
               content = f.read()
           return Response(
               body=content,
               content_type=get_content_type(file_path),
               headers={"Content-Length": str(len(content))}
           )
       else:
           # Fallback to index.html for SPA routing
           with open("dist/index.html", 'rb') as f:
               content = f.read()
           return Response(
               body=content,
               content_type="text/html",
               headers={"Content-Length": str(len(content))}
           )

File Upload Handling
--------------------

Basic File Uploads
~~~~~~~~~~~~~~~~~~

Handle single and multiple file uploads:

.. code-block:: python

   from catzilla import Catzilla, Request, JSONResponse, UploadFile, File
   from pathlib import Path
   import uuid
   import mimetypes

   app = Catzilla()

   # Configure upload directory
   UPLOAD_DIR = Path("uploads")
   UPLOAD_DIR.mkdir(exist_ok=True)

   @app.post("/upload")
   async def upload_file(request: Request, file: UploadFile = File(...)):
       """Handle single file upload"""

       # Validate file
       if not file.filename:
           return JSONResponse({"error": "No file selected"}, status_code=400)

       # Generate unique filename
       file_extension = Path(file.filename).suffix
       unique_filename = f"{uuid.uuid4()}{file_extension}"
       file_path = UPLOAD_DIR / unique_filename

       # Save file
       try:
           with open(file_path, "wb") as buffer:
               content = await file.read()
               buffer.write(content)

           return JSONResponse({
               "message": "File uploaded successfully",
               "filename": unique_filename,
               "original_name": file.filename,
               "size": len(content),
               "content_type": file.content_type
           })

       except Exception as e:
           return JSONResponse(
               {"error": f"Upload failed: {str(e)}"},
               status_code=500
           )

   @app.post("/upload-multiple")
   async def upload_multiple_files(request: Request, files: list[UploadFile] = File(...)):
       """Handle multiple file uploads"""

       if not files or all(not file.filename for file in files):
           return JSONResponse({"error": "No files selected"}, status_code=400)

       uploaded_files = []

       for file in files:
           if not file.filename:
               continue

           # Generate unique filename
           file_extension = Path(file.filename).suffix
           unique_filename = f"{uuid.uuid4()}{file_extension}"
           file_path = UPLOAD_DIR / unique_filename

           # Save file
           try:
               content = await file.read()
               with open(file_path, "wb") as buffer:
                   buffer.write(content)

               uploaded_files.append({
                   "filename": unique_filename,
                   "original_name": file.filename,
                   "size": len(content),
                   "content_type": file.content_type
               })

           except Exception as e:
               uploaded_files.append({
                   "original_name": file.filename,
                   "error": str(e)
               })

       return JSONResponse({
           "message": f"Uploaded {len(uploaded_files)} files",
           "files": uploaded_files
       })

File Validation and Security
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Implement comprehensive file validation:

.. code-block:: python

   import magic
   from PIL import Image
   import io

   class FileValidator:
       def __init__(self):
           self.allowed_extensions = {
               "images": [".jpg", ".jpeg", ".png", ".gif", ".webp"],
               "documents": [".pdf", ".doc", ".docx", ".txt", ".rtf"],
               "archives": [".zip", ".tar", ".gz", ".7z"],
               "videos": [".mp4", ".avi", ".mov", ".wmv"]
           }

           self.max_file_sizes = {
               "images": 10 * 1024 * 1024,      # 10MB
               "documents": 50 * 1024 * 1024,   # 50MB
               "archives": 100 * 1024 * 1024,   # 100MB
               "videos": 500 * 1024 * 1024      # 500MB
           }

       def validate_file(self, file: UploadFile, category: str = "images"):
           """Validate uploaded file"""
           errors = []

           # Check filename
           if not file.filename:
               errors.append("Filename is required")
               return errors

           file_extension = Path(file.filename).suffix.lower()

           # Check file extension
           if file_extension not in self.allowed_extensions.get(category, []):
               errors.append(f"File type {file_extension} not allowed for {category}")

           # Check file size (if content is available)
           if hasattr(file, 'size') and file.size:
               max_size = self.max_file_sizes.get(category, 10 * 1024 * 1024)
               if file.size > max_size:
                   errors.append(f"File size exceeds maximum allowed size ({max_size} bytes)")

           return errors

       async def validate_file_content(self, file_content: bytes, expected_type: str = "image"):
           """Validate file content using magic numbers"""
           try:
               # Detect actual file type
               file_type = magic.from_buffer(file_content, mime=True)

               if expected_type == "image" and not file_type.startswith("image/"):
                   return ["File is not a valid image"]

               # Additional image validation
               if expected_type == "image":
                   try:
                       with Image.open(io.BytesIO(file_content)) as img:
                           # Check image dimensions
                           if img.width > 5000 or img.height > 5000:
                               return ["Image dimensions too large (max 5000x5000)"]

                           # Check for malicious content (basic check)
                           if img.mode not in ["RGB", "RGBA", "L", "P"]:
                               return ["Unsupported image mode"]

                   except Exception:
                       return ["Invalid or corrupted image file"]

               return []

           except Exception as e:
               return [f"File validation error: {str(e)}"]

   validator = FileValidator()

   @app.post("/upload-secure")
   async def upload_secure_file(request: Request, file: UploadFile = File(...)):
       """Upload with comprehensive security validation"""

       # Basic validation
       errors = validator.validate_file(file, "images")
       if errors:
           return JSONResponse({"errors": errors}, status_code=400)

       # Read file content
       content = await file.read()

       # Content validation
       content_errors = await validator.validate_file_content(content, "image")
       if content_errors:
           return JSONResponse({"errors": content_errors}, status_code=400)

       # Save validated file
       file_extension = Path(file.filename).suffix
       unique_filename = f"{uuid.uuid4()}{file_extension}"
       file_path = UPLOAD_DIR / unique_filename

       with open(file_path, "wb") as buffer:
           buffer.write(content)

       return JSONResponse({
           "message": "Secure file upload successful",
           "filename": unique_filename,
           "size": len(content),
           "validation": "passed"
       })

Image Processing
----------------

Image Optimization and Manipulation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Process uploaded images with PIL/Pillow:

.. code-block:: python

   from PIL import Image, ImageOps
   import io

   class ImageProcessor:
       def __init__(self):
           self.thumbnail_sizes = {
               "small": (150, 150),
               "medium": (300, 300),
               "large": (800, 600)
           }

       def create_thumbnails(self, image_path: Path):
           """Create multiple thumbnail sizes"""
           thumbnails = {}

           try:
               with Image.open(image_path) as img:
                   # Convert to RGB if necessary (for JPEG compatibility)
                   if img.mode in ("RGBA", "P"):
                       img = img.convert("RGB")

                   for size_name, dimensions in self.thumbnail_sizes.items():
                       # Create thumbnail preserving aspect ratio
                       thumbnail = img.copy()
                       thumbnail.thumbnail(dimensions, Image.Resampling.LANCZOS)

                       # Save thumbnail
                       thumb_filename = f"{image_path.stem}_{size_name}{image_path.suffix}"
                       thumb_path = image_path.parent / "thumbnails" / thumb_filename
                       thumb_path.parent.mkdir(exist_ok=True)

                       thumbnail.save(thumb_path, quality=85, optimize=True)
                       thumbnails[size_name] = {
                           "filename": thumb_filename,
                           "size": dimensions,
                           "path": str(thumb_path)
                       }

               return thumbnails

           except Exception as e:
               print(f"Thumbnail creation failed: {e}")
               return {}

       def optimize_image(self, image_path: Path, quality: int = 85):
           """Optimize image for web delivery"""
           try:
               with Image.open(image_path) as img:
                   # Convert to RGB for JPEG
                   if img.mode in ("RGBA", "P"):
                       img = img.convert("RGB")

                   # Optimize and save
                   optimized_path = image_path.parent / f"optimized_{image_path.name}"
                   img.save(optimized_path, "JPEG", quality=quality, optimize=True)

                   return optimized_path

           except Exception as e:
               print(f"Image optimization failed: {e}")
               return image_path

   image_processor = ImageProcessor()

   @app.post("/upload-image")
   async def upload_and_process_image(request: Request, file: UploadFile = File(...)):
       """Upload and automatically process image"""

       # Validate image file
       errors = validator.validate_file(file, "images")
       if errors:
           return JSONResponse({"errors": errors}, status_code=400)

       content = await file.read()
       content_errors = await validator.validate_file_content(content, "image")
       if content_errors:
           return JSONResponse({"errors": content_errors}, status_code=400)

       # Save original image
       file_extension = Path(file.filename).suffix
       unique_filename = f"{uuid.uuid4()}{file_extension}"
       original_path = UPLOAD_DIR / unique_filename

       with open(original_path, "wb") as buffer:
           buffer.write(content)

       # Process image
       thumbnails = image_processor.create_thumbnails(original_path)
       optimized_path = image_processor.optimize_image(original_path)

       return JSONResponse({
           "message": "Image uploaded and processed",
           "original": {
               "filename": unique_filename,
               "size": len(content)
           },
           "thumbnails": thumbnails,
           "optimized": {
               "filename": optimized_path.name,
               "path": str(optimized_path)
           }
       })

Advanced File Operations
------------------------

Chunked Upload for Large Files
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Handle large file uploads with chunking:

.. code-block:: python

   import hashlib
   import tempfile

   class ChunkedUploadManager:
       def __init__(self):
           self.active_uploads = {}
           self.chunk_size = 1024 * 1024  # 1MB chunks

       def start_upload(self, file_id: str, total_size: int, filename: str):
           """Initialize chunked upload"""
           temp_file = tempfile.NamedTemporaryFile(delete=False)

           self.active_uploads[file_id] = {
               "temp_file": temp_file,
               "temp_path": temp_file.name,
               "filename": filename,
               "total_size": total_size,
               "uploaded_size": 0,
               "chunks_received": 0,
               "hash": hashlib.sha256()
           }

           return {"status": "upload_initiated", "file_id": file_id}

       async def upload_chunk(self, file_id: str, chunk_data: bytes, chunk_number: int):
           """Upload a file chunk"""
           if file_id not in self.active_uploads:
               return {"error": "Upload session not found"}

           upload_info = self.active_uploads[file_id]

           # Write chunk to temp file
           upload_info["temp_file"].write(chunk_data)
           upload_info["uploaded_size"] += len(chunk_data)
           upload_info["chunks_received"] += 1
           upload_info["hash"].update(chunk_data)

           progress = (upload_info["uploaded_size"] / upload_info["total_size"]) * 100

           return {
               "status": "chunk_received",
               "chunk_number": chunk_number,
               "progress": round(progress, 2),
               "uploaded_size": upload_info["uploaded_size"],
               "total_size": upload_info["total_size"]
           }

       def complete_upload(self, file_id: str):
           """Complete chunked upload"""
           if file_id not in self.active_uploads:
               return {"error": "Upload session not found"}

           upload_info = self.active_uploads[file_id]

           # Close temp file
           upload_info["temp_file"].close()

           # Move to final location
           final_filename = f"{uuid.uuid4()}_{upload_info['filename']}"
           final_path = UPLOAD_DIR / final_filename

           import shutil
           shutil.move(upload_info["temp_path"], final_path)

           # Calculate final hash
           file_hash = upload_info["hash"].hexdigest()

           # Cleanup
           del self.active_uploads[file_id]

           return {
               "status": "upload_complete",
               "filename": final_filename,
               "size": upload_info["uploaded_size"],
               "hash": file_hash
           }

   upload_manager = ChunkedUploadManager()

   @app.post("/upload/start")
   async def start_chunked_upload(request: Request):
       """Start chunked upload session"""
       data = await request.json()

       file_id = str(uuid.uuid4())
       result = upload_manager.start_upload(
           file_id,
           data["total_size"],
           data["filename"]
       )

       result["file_id"] = file_id
       return JSONResponse(result)

   @app.post("/upload/chunk/{file_id}")
   async def upload_chunk(request: Request, file_id: str):
       """Upload file chunk"""
       form = await request.form()
       chunk_data = await form["chunk"].read()
       chunk_number = int(form["chunk_number"])

       result = await upload_manager.upload_chunk(file_id, chunk_data, chunk_number)
       return JSONResponse(result)

   @app.post("/upload/complete/{file_id}")
   async def complete_chunked_upload(request: Request, file_id: str):
       """Complete chunked upload"""
       result = upload_manager.complete_upload(file_id)
       return JSONResponse(result)

File Download and Serving
--------------------------

Secure File Downloads
~~~~~~~~~~~~~~~~~~~~~

Serve files with access control:

.. code-block:: python

   from catzilla import Response
   import mimetypes

   @app.get("/download/{filename}")
   async def download_file(request: Request, filename: str):
       """Secure file download with access control"""

       # Validate filename (prevent path traversal)
       if ".." in filename or "/" in filename or "\\" in filename:
           return JSONResponse({"error": "Invalid filename"}, status_code=400)

       file_path = UPLOAD_DIR / filename

       if not file_path.exists():
           return JSONResponse({"error": "File not found"}, status_code=404)

       # Optional: Check user permissions here
       # if not user_has_access(request.user, filename):
       #     return JSONResponse({"error": "Access denied"}, status_code=403)

       # Determine content type
       content_type, _ = mimetypes.guess_type(str(file_path))
       if content_type is None:
           content_type = "application/octet-stream"

       # Read file content and return as Response
       with open(file_path, 'rb') as f:
           content = f.read()

       return Response(
           body=content,
           content_type=content_type,
           headers={
               "Content-Disposition": f"attachment; filename={filename}",
               "Content-Length": str(len(content))
           }
       )

   @app.get("/view/{filename}")
   async def view_file(request: Request, filename: str):
       """View file inline (for images, PDFs, etc.)"""

       # Validate filename
       if ".." in filename or "/" in filename:
           return JSONResponse({"error": "Invalid filename"}, status_code=400)

       file_path = UPLOAD_DIR / filename

       if not file_path.exists():
           return JSONResponse({"error": "File not found"}, status_code=404)

       content_type, _ = mimetypes.guess_type(str(file_path))
       if content_type is None:
           content_type = "application/octet-stream"

       # Read file content and return as Response
       with open(file_path, 'rb') as f:
           content = f.read()

       return Response(
           body=content,
           content_type=content_type,
           headers={
               "Content-Disposition": f"inline; filename={filename}",
               "Content-Length": str(len(content))
           }
       )

File Management API
~~~~~~~~~~~~~~~~~~~

Complete file management endpoints:

.. code-block:: python

   @app.get("/files")
   async def list_files(request: Request):
       """List uploaded files"""

       files = []
       for file_path in UPLOAD_DIR.iterdir():
           if file_path.is_file():
               stat = file_path.stat()
               files.append({
                   "filename": file_path.name,
                   "size": stat.st_size,
                   "created": stat.st_ctime,
                   "modified": stat.st_mtime,
                   "content_type": mimetypes.guess_type(str(file_path))[0]
               })

       return JSONResponse({
           "files": sorted(files, key=lambda x: x["modified"], reverse=True),
           "total_count": len(files)
       })

   @app.delete("/files/{filename}")
   async def delete_file(request: Request, filename: str):
       """Delete uploaded file"""

       # Validate filename
       if ".." in filename or "/" in filename:
           return JSONResponse({"error": "Invalid filename"}, status_code=400)

       file_path = UPLOAD_DIR / filename

       if not file_path.exists():
           return JSONResponse({"error": "File not found"}, status_code=404)

       try:
           file_path.unlink()
           return JSONResponse({"message": f"File {filename} deleted successfully"})
       except Exception as e:
           return JSONResponse({"error": f"Delete failed: {str(e)}"}, status_code=500)

   @app.get("/files/{filename}/info")
   async def get_file_info(request: Request, filename: str):
       """Get detailed file information"""

       # Validate filename
       if ".." in filename or "/" in filename:
           return JSONResponse({"error": "Invalid filename"}, status_code=400)

       file_path = UPLOAD_DIR / filename

       if not file_path.exists():
           return JSONResponse({"error": "File not found"}, status_code=404)

       stat = file_path.stat()
       content_type, encoding = mimetypes.guess_type(str(file_path))

       # Additional info for images
       extra_info = {}
       if content_type and content_type.startswith("image/"):
           try:
               with Image.open(file_path) as img:
                   extra_info.update({
                       "width": img.width,
                       "height": img.height,
                       "format": img.format,
                       "mode": img.mode
                   })
           except Exception:
               pass

       return JSONResponse({
           "filename": filename,
           "size": stat.st_size,
           "content_type": content_type,
           "encoding": encoding,
           "created": stat.st_ctime,
           "modified": stat.st_mtime,
           "is_image": content_type and content_type.startswith("image/") if content_type else False,
           **extra_info
       })

Best Practices
--------------

Security Guidelines
~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # ✅ Good: Validate file types and content
   def validate_upload(file: UploadFile):
       # Check extension
       allowed_extensions = [".jpg", ".png", ".pdf"]
       if not any(file.filename.endswith(ext) for ext in allowed_extensions):
           return False

       # Check MIME type
       content = file.read()
       file_type = magic.from_buffer(content, mime=True)
       return file_type in ["image/jpeg", "image/png", "application/pdf"]

   # ✅ Good: Use unique filenames
   unique_filename = f"{uuid.uuid4()}_{secure_filename(file.filename)}"

   # ✅ Good: Limit file sizes
   MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
   if len(content) > MAX_FILE_SIZE:
       raise ValueError("File too large")

Performance Tips
~~~~~~~~~~~~~~~~

.. code-block:: python

   # ✅ Good: Stream large files
   async def stream_upload(file: UploadFile):
       with open("large_file.dat", "wb") as f:
           while chunk := await file.read(8192):  # 8KB chunks
               f.write(chunk)

   # ✅ Good: Use async file operations
   import aiofiles

   async def async_file_save(content: bytes, path: Path):
       async with aiofiles.open(path, "wb") as f:
           await f.write(content)

   # ✅ Good: Implement caching for static files
   from catzilla import StaticFiles

   app.mount("/static", StaticFiles(
       directory="static",
       cache_max_age=86400,  # 24 hours
       enable_compression=True
   ))

This comprehensive file handling system provides secure, efficient, and scalable file operations for your Catzilla applications.
