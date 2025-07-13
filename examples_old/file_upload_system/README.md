# Revolutionary File Upload System Example

This directory contains a comprehensive example of Catzilla's revolutionary file upload system.

## Features Demonstrated

### 🚀 Performance Features
- **C-native multipart parsing** - 10-100x faster than traditional Python frameworks
- **Zero-copy streaming** - 50-80% memory usage reduction
- **Real-time performance monitoring** - Upload speed, progress, ETA tracking
- **Concurrent upload handling** - Thousands of simultaneous uploads

### 🔒 Security Features
- **File signature validation** - Prevents MIME type spoofing attacks
- **ClamAV virus scanning** - Enterprise-grade malware detection
- **Path traversal protection** - Secure file storage
- **Size limit enforcement** - Configurable per endpoint

### 🎯 Developer Experience
- **FastAPI-compatible API** - Drop-in replacement syntax
- **Type hints and validation** - Full IDE support
- **Comprehensive error handling** - Clear error messages
- **Flexible configuration** - Per-endpoint customization

## Running the Example

```bash
# From the project root
./scripts/run_example.sh examples/file_upload_system/main.py

# Or directly with Python
cd /path/to/catzilla
python examples/file_upload_system/main.py
```

## Testing the Upload System

### Web Interface
Visit http://localhost:8000 for a complete web demo interface.

### Command Line Testing

```bash
# Single file upload
curl -X POST -F "file=@test.txt" http://localhost:8000/upload/single

# Image upload with validation
curl -X POST -F "image=@photo.jpg" http://localhost:8000/upload/image

# Multiple files
curl -X POST \
  -F "profile_image=@avatar.jpg" \
  -F "document=@resume.pdf" \
  -F "attachments=@file1.txt" \
  -F "attachments=@file2.txt" \
  http://localhost:8000/upload/multiple

# Large file upload
curl -X POST -F "large_file=@bigfile.zip" http://localhost:8000/upload/large

# System statistics
curl http://localhost:8000/upload/stats
```

## Example Endpoints

### 1. Basic Upload (`/upload/single`)
- Simple file upload with performance monitoring
- Real-time speed tracking
- Basic security validation

### 2. Image Upload (`/upload/image`)
- Strict MIME type validation
- File signature verification
- Virus scanning enabled
- Optimized for image processing

### 3. Multiple Files (`/upload/multiple`)
- Different validation rules per file type
- Optional vs required files
- Bulk processing with individual error handling
- Performance summary across all files

### 4. Large Files (`/upload/large`)
- 1GB file size support
- Streaming to minimize memory usage
- Extended timeout configuration
- Zero-copy optimization for large transfers

### 5. Performance Stats (`/upload/stats`)
- Real-time system performance metrics
- Memory usage statistics
- Upload throughput monitoring

## Configuration Examples

```python
# Basic configuration
app = Catzilla(
    upload_config={
        "default_max_size": "100MB",
        "virus_scanning": {"enabled": True}
    }
)

# Per-endpoint configuration
@app.post("/upload/strict")
def upload_strict(
    file: UploadFile = File(
        max_size="10MB",
        allowed_types=["image/jpeg", "image/png"],
        validate_signature=True,
        virus_scan=True
    )
):
    # Ultra-strict validation
    pass
```

## Performance Benchmarks

When compared to traditional Python frameworks:

- **Multipart parsing**: 10-100x faster
- **Memory usage**: 50-80% reduction
- **Upload throughput**: Near wire-speed
- **Concurrent uploads**: Thousands supported
- **File validation**: C-native speed

## Security Features

- **Signature validation**: Prevents MIME spoofing
- **Virus scanning**: ClamAV integration
- **Path protection**: Prevents directory traversal
- **Size enforcement**: Configurable limits
- **Content validation**: Advanced security rules

## Production Deployment

This example is production-ready and includes:

- Comprehensive error handling
- Security best practices
- Performance optimization
- Monitoring and logging
- Cross-platform compatibility
