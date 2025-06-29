# 🚀 **Catzilla Revolutionary File Upload System - Engineering Plan**

## 🎯 **Vision: Unbeatable Performance + FastAPI-Style Developer Experience**

### **Core Innovation: "Zero-Copy Streaming with jemalloc Optimization"**

This document outlines the implementation plan for Catzilla's revolutionary C-native file upload system that will deliver 10-100x performance improvements over existing Python frameworks while maintaining superior developer experience.

---

## 📋 **Target Developer API**

### **Basic Usage (Catzilla Style)**
```python
from catzilla import Catzilla, File, UploadFile

app = Catzilla()

@app.post("/upload/")
def upload_file(request, file: UploadFile = File(...)):
    # Zero-copy streaming with C-native performance
    contents = file.read()  # C-native streaming
    return {
        "filename": file.filename,
        "content_type": file.content_type,
        "size": len(contents),
        "upload_speed": file.upload_speed_mbps  # Unique to Catzilla!
    }
```

### **Advanced Streaming**
```python
@app.post("/upload/stream/")
def upload_stream(request, file: UploadFile = File(max_size="100MB")):
    # Stream directly to disk without loading into memory
    saved_path = file.save_to("/uploads/", stream=True)
    return {"saved_to": saved_path, "chunks_processed": file.chunks_count}
```

### **Advanced Validation & Security**
```python
@app.post("/upload/image/")
def upload_image(
    request,
    file: UploadFile = File(
        max_size="10MB",
        allowed_types=["image/jpeg", "image/png"],
        validate_signature=True,  # Magic number verification
        virus_scan=True          # Real-time virus scanning
    )
):
    # File is pre-validated and processed by C layer
    saved_path = file.save_to("/uploads/")
    return {"file": file.filename, "path": saved_path}
```

### **Batch Upload Support**
```python
@app.post("/upload/batch/")
def upload_multiple(request, files: List[UploadFile] = File(..., max_files=10)):
    # Parallel processing in C thread pool - handled automatically by Catzilla
    results = []
    for file in files:
        saved_path = file.save_to("/uploads/", stream=True)
        results.append(saved_path)
    return {"uploaded": len(results)}
```

---

## 🏗️ **Architecture Overview**

### **1. Core Components**

#### **A. C-Native Multipart Parser**
- **Location**: `src/core/upload_parser.c`, `src/core/upload_parser.h`
- **Purpose**: Ultra-fast multipart/form-data parsing with libuv
- **Features**: Zero-copy streaming, jemalloc optimization, performance tracking

#### **B. File Upload Manager**
- **Location**: `src/core/upload_manager.c`, `src/core/upload_manager.h`
- **Purpose**: Manages upload lifecycle, memory, and streaming
- **Features**: Arena allocation, parallel processing, security validation

#### **C. Python Integration Layer**
- **Location**: `python/catzilla/uploads.py`
- **Purpose**: FastAPI-compatible Python API with advanced features
- **Features**: UploadFile class, validation decorators, async support

### **2. Memory Architecture**
```c
// Dedicated jemalloc arena for uploads
typedef struct {
    size_t small_files_arena;    // < 1MB files
    size_t medium_files_arena;   // 1-50MB files
    size_t large_files_arena;    // > 50MB files (streaming only)
    size_t metadata_arena;       // Headers, filenames, etc.
} upload_memory_manager_t;
```

### **3. Core Data Structures**
```c
// Main upload file structure
typedef struct {
    char* filename;
    char* content_type;
    uint64_t size;
    uint64_t max_size;

    // Zero-copy streaming
    uv_stream_t* stream;
    uv_fs_t file_handle;

    // Performance tracking
    uint64_t upload_start_time;
    uint64_t bytes_received;
    double upload_speed_mbps;

    // Memory optimization
    catzilla_atomic_uint64_t chunks_processed;
    size_t buffer_size;
    char* streaming_buffer;  // jemalloc arena

    // Security features
    bool signature_validated;
    bool virus_scanned;
    char* allowed_types[10];
} catzilla_upload_file_t;
```

---

## 📊 **Performance Targets**

### **Memory Usage**
- **90% less memory** than traditional Python frameworks for large files
- **Zero memory copying** for streaming uploads
- **jemalloc optimization** reduces fragmentation by 60%

### **Speed Metrics**
- **10x faster** multipart parsing than FastAPI
- **Direct disk streaming** at network line speed
- **Parallel processing** of multiple files

### **Scalability**
- **1000+ concurrent uploads** with minimal memory overhead
- **GB-sized files** handled without memory issues
- **Real-time progress** tracking for all uploads

---

## 🛠️ **Implementation Phases**

### **Phase 1: Core Multipart Parser (C Implementation)**
**Duration**: 1 week
**Priority**: Critical

#### **Files to Create/Modify:**
- `src/core/upload_parser.c`
- `src/core/upload_parser.h`
- `src/core/multipart.c`
- `src/core/multipart.h`

#### **Key Functions:**
```c
// Core parsing functions
int catzilla_multipart_parse_init(multipart_parser_t* parser);
int catzilla_multipart_parse_chunk(multipart_parser_t* parser, const char* data, size_t len);
int catzilla_multipart_parse_complete(multipart_parser_t* parser);

// File handling
catzilla_upload_file_t* catzilla_upload_file_create(const char* filename, const char* content_type);
int catzilla_upload_file_write_chunk(catzilla_upload_file_t* file, const char* data, size_t len);
int catzilla_upload_file_finalize(catzilla_upload_file_t* file);
```

#### **Deliverables:**
- [x] Basic multipart/form-data parsing
- [x] File metadata extraction (filename, content-type, size)
- [x] Simple in-memory file storage
- [x] Integration with existing request handler

### **Phase 2: Streaming & Performance Optimization**
**Duration**: 1 week
**Priority**: High

#### **Files to Create/Modify:**
- `src/core/upload_stream.c`
- `src/core/upload_stream.h`
- `src/core/upload_memory.c`
- `src/core/upload_memory.h`

#### **Key Features:**
```c
// Zero-copy streaming
int catzilla_upload_stream_to_disk(catzilla_upload_file_t* file, const char* path);
int catzilla_upload_stream_to_memory(catzilla_upload_file_t* file);

// Performance monitoring
double catzilla_upload_get_speed_mbps(catzilla_upload_file_t* file);
uint64_t catzilla_upload_get_bytes_processed(catzilla_upload_file_t* file);

// Memory management
upload_memory_manager_t* catzilla_upload_memory_init(void);
void* catzilla_upload_memory_alloc(upload_memory_manager_t* mgr, size_t size, upload_size_class_t class);
```

#### **Deliverables:**
- [x] Zero-copy streaming to disk
- [x] jemalloc arena optimization
- [x] Performance monitoring integration
- [x] Adaptive buffer sizing

### **Phase 3: Python Integration Layer**
**Duration**: 1 week
**Priority**: High

#### **Files to Create/Modify:**
- `python/catzilla/uploads.py`
- `python/catzilla/file_types.py`
- `python/catzilla/validation.py`
- `python/catzilla/exceptions.py` (NEW - Upload-specific exceptions)

#### **Exception Classes:**
```python
# python/catzilla/exceptions.py
class UploadError(Exception):
    """Base class for all upload-related errors"""
    def __init__(self, message: str, error_code: int = None, details: dict = None):
        super().__init__(message)
        self.error_code = error_code
        self.details = details or {}

class FileSizeError(UploadError):
    """Raised when file exceeds size limit"""
    def __init__(self, max_size: int, actual_size: int, **kwargs):
        self.max_size = max_size
        self.actual_size = actual_size
        self.size_mb = actual_size / (1024 * 1024)
        super().__init__(f"File size {actual_size} exceeds limit {max_size}", **kwargs)

class MimeTypeError(UploadError):
    """Raised when file type is not allowed"""
    def __init__(self, allowed_types: list, actual_type: str, **kwargs):
        self.allowed_types = allowed_types
        self.actual_type = actual_type
        super().__init__(f"File type {actual_type} not in allowed types {allowed_types}", **kwargs)

class FileSignatureError(UploadError):
    """Raised when file signature doesn't match MIME type"""
    pass

class VirusScanError(UploadError):
    """Raised when virus is detected in file"""
    def __init__(self, threat_name: str, **kwargs):
        self.threat_name = threat_name
        super().__init__(f"Virus detected: {threat_name}", **kwargs)

class DiskSpaceError(UploadError):
    """Raised when insufficient disk space for upload"""
    pass

class UploadTimeoutError(UploadError):
    """Raised when upload takes too long"""
    pass

class VirusScannerUnavailableError(UploadError):
    """Raised when virus scanning is requested but ClamAV is not available"""
    def __init__(self, install_instructions: dict = None):
        self.install_instructions = install_instructions or {}
        super().__init__("ClamAV not found. Install ClamAV to enable virus scanning.")
```

#### **Python Classes:**
```python
class CatzillaUploadFile(UploadFile):
    """Revolutionary upload file with C-native performance"""

    # Performance metrics (unique to Catzilla)
    @property
    def upload_speed_mbps(self) -> float:
        """Real-time upload speed in MB/s"""

    @property
    def estimated_time_remaining(self) -> float:
        """Estimated seconds until upload complete"""

    # Advanced streaming (synchronous - handled by C layer)
    def save_to(self, path: str, stream: bool = True) -> str:
        """Zero-copy streaming to disk"""

    def stream_chunks(self, chunk_size: int = 8192):
        """Generator for processing large files in chunks"""

    # Security features
    def validate_signature(self) -> bool:
        """C-native file signature validation"""

def File(
    max_size: Union[int, str] = None,
    allowed_types: List[str] = None,
    validate_signature: bool = False,
    virus_scan: bool = False
) -> Any:
    """Advanced file upload parameter with C-native validation"""
```

#### **Deliverables:**
- [x] Catzilla-compatible UploadFile class (synchronous)
- [x] Advanced File() parameter function
- [x] C-native async handling (no Python async/await needed)
- [x] Integration with existing Catzilla app

### **Phase 4: Advanced Security & Validation**
**Duration**: 1 week
**Priority**: Medium

#### **Files to Create/Modify:**
- `src/core/upload_security.c`
- `src/core/upload_security.h`
- `src/core/file_validation.c`
- `src/core/file_validation.h`

#### **Security Features:**
```c
// File signature validation
bool catzilla_validate_file_signature(const char* filename, const char* data, size_t len);

// MIME type validation
bool catzilla_validate_mime_type(const char* content_type, const char* allowed_types[], size_t count);

// Virus scanning integration
typedef bool (*virus_scan_callback_t)(const char* file_path);
int catzilla_upload_set_virus_scanner(virus_scan_callback_t callback);

// Path traversal protection
bool catzilla_validate_file_path(const char* path);
```

#### **Deliverables:**
- [x] File signature validation (magic numbers)
- [x] MIME type validation
- [x] Path traversal protection
- [x] Virus scanning hooks
- [x] File size limits enforcement

---

## 🔥 **Revolutionary Features**

### **1. Zero-Copy Streaming**
- **Direct disk writing** without loading entire file into memory
- **libuv async I/O** for non-blocking file operations
- **Configurable chunk size** optimized for different file types

### **2. Performance Monitoring**
- **Real-time upload speed** tracking (unique feature)
- **Memory usage optimization** with jemalloc arenas
- **Automatic performance profiling**

### **3. Advanced Security**
- **C-level MIME type validation**
- **File signature verification** (magic numbers)
- **Path traversal protection**
- **Virus scanning integration** hooks

### **4. Smart Buffer Management**
- **Adaptive buffer sizing** based on file size and network speed
- **Memory pool reuse** for frequent uploads
- **Automatic garbage collection** when upload completes

### **5. Parallel Processing**
```c
// Background thread pool for file processing
typedef struct {
    uv_work_t work_req;
    catzilla_upload_file_t* upload;

    // Parallel operations
    bool (*virus_scan)(const char* file_path);
    bool (*metadata_extract)(const char* file_path);
} upload_processor_t;
```

---

## 🎯 **Competitive Advantages**

### **vs FastAPI:**
- ✅ **10x faster** multipart parsing
- ✅ **90% less memory** usage for large files
- ✅ **Real-time performance** metrics
- ✅ **Zero-copy streaming**

### **vs Django:**
- ✅ **100x faster** file upload processing
- ✅ **Built-in virus scanning**
- ✅ **Automatic security validation**
- ✅ **jemalloc optimization**

### **vs Flask:**
- ✅ **Native async support**
- ✅ **C-level performance**
- ✅ **Enterprise security features**
- ✅ **Advanced streaming capabilities**

---

## 🚨 **Exception Handling & Error Management**

### **File Size Limit Handling**
```python
from catzilla import Catzilla, File, UploadFile, ValidationError, FileSizeError

@app.post("/upload/")
def upload_file(request, file: UploadFile = File(max_size="100MB")):
    try:
        # File is automatically validated by C layer before reaching Python
        contents = file.read()
        return {"filename": file.filename, "size": len(contents)}
    except FileSizeError as e:
        # Automatically raised if file exceeds 100MB
        return {"error": "File too large", "max_size": "100MB", "actual_size": e.file_size}
    except ValidationError as e:
        # Other validation failures
        return {"error": "Validation failed", "details": str(e)}
```

### **MIME Type Validation Errors**
```python
@app.post("/upload/image/")
def upload_image(
    request,
    file: UploadFile = File(
        max_size="10MB",
        allowed_types=["image/jpeg", "image/png"]
    )
):
    try:
        saved_path = file.save_to("/uploads/")
        return {"saved": saved_path}
    except MimeTypeError as e:
        # Raised if file is not JPEG or PNG
        return {
            "error": "Invalid file type",
            "allowed": ["image/jpeg", "image/png"],
            "received": e.content_type
        }
    except FileSizeError as e:
        return {"error": "File too large", "max_size": "10MB"}
```

### **Advanced Error Handling**
```python
from catzilla.exceptions import (
    FileSizeError,
    MimeTypeError,
    FileSignatureError,
    VirusScanError,
    DiskSpaceError,
    UploadTimeoutError,
    VirusScannerUnavailableError
)

@app.post("/upload/secure/")
def secure_upload(
    request,
    file: UploadFile = File(
        max_size="50MB",
        allowed_types=["application/pdf", "image/png"],
        validate_signature=True,
        virus_scan=True,
        timeout=30  # 30 second timeout
    )
):
    try:
        # All validation happens automatically in C layer
        saved_path = file.save_to("/secure/uploads/")
        return {"success": True, "path": saved_path}

    except FileSizeError as e:
        return {"error": "file_too_large", "max_size": "50MB", "actual": e.size_mb}

    except MimeTypeError as e:
        return {"error": "invalid_type", "allowed": e.allowed_types, "received": e.actual_type}

    except FileSignatureError as e:
        return {"error": "signature_mismatch", "expected": e.expected_signature, "actual": e.actual_signature}

    except VirusScanError as e:
        return {"error": "virus_detected", "threat": e.threat_name, "action": "quarantined"}

    except DiskSpaceError as e:
        return {"error": "insufficient_space", "required": e.required_mb, "available": e.available_mb}

    except UploadTimeoutError as e:
        return {"error": "upload_timeout", "timeout": "30s", "progress": f"{e.bytes_received}/{e.total_bytes}"}

    except VirusScannerUnavailableError as e:
        return {
            "error": "virus_scanner_unavailable",
            "message": "ClamAV not found. Install it to enable virus scanning.",
            "install_instructions": e.install_instructions
        }

    except Exception as e:
        # Generic fallback
        return {"error": "upload_failed", "details": str(e)}
```

### **Error Handling at C Level**
```c
// Error codes for file upload validation
typedef enum {
    CATZILLA_UPLOAD_SUCCESS = 0,
    CATZILLA_UPLOAD_ERROR_FILE_TOO_LARGE = -1001,
    CATZILLA_UPLOAD_ERROR_INVALID_MIME = -1002,
    CATZILLA_UPLOAD_ERROR_SIGNATURE_MISMATCH = -1003,
    CATZILLA_UPLOAD_ERROR_VIRUS_DETECTED = -1004,
    CATZILLA_UPLOAD_ERROR_DISK_FULL = -1005,
    CATZILLA_UPLOAD_ERROR_TIMEOUT = -1006,
    CATZILLA_UPLOAD_ERROR_CORRUPTED = -1007,
    CATZILLA_UPLOAD_ERROR_PATH_TRAVERSAL = -1008
} catzilla_upload_error_t;

// Validation function that stops upload early
int catzilla_upload_validate_chunk(
    catzilla_upload_file_t* file,
    const char* chunk_data,
    size_t chunk_size
) {
    // Check file size limit before processing chunk
    if (file->bytes_received + chunk_size > file->max_size) {
        LOG_UPLOAD_ERROR("File size limit exceeded: %zu + %zu > %zu",
                        file->bytes_received, chunk_size, file->max_size);
        return CATZILLA_UPLOAD_ERROR_FILE_TOO_LARGE;
    }

    // Validate MIME type from first chunk
    if (file->bytes_received == 0 && file->validate_signature) {
        if (!catzilla_validate_file_signature(chunk_data, chunk_size, file->content_type)) {
            LOG_UPLOAD_ERROR("File signature mismatch for type: %s", file->content_type);
            return CATZILLA_UPLOAD_ERROR_SIGNATURE_MISMATCH;
        }
    }

    return CATZILLA_UPLOAD_SUCCESS;
}
```

### **Early Termination Strategy**
```c
// Stop upload immediately when limits are exceeded
static void on_upload_chunk_received(uv_stream_t* stream, ssize_t nread, const uv_buf_t* buf) {
    catzilla_upload_file_t* file = (catzilla_upload_file_t*)stream->data;

    if (nread < 0) {
        // Network error
        catzilla_upload_set_error(file, CATZILLA_UPLOAD_ERROR_NETWORK, "Network error during upload");
        catzilla_upload_abort(file);
        return;
    }

    // Validate chunk before processing
    int validation_result = catzilla_upload_validate_chunk(file, buf->base, nread);
    if (validation_result != CATZILLA_UPLOAD_SUCCESS) {
        // Stop upload immediately - don't waste bandwidth
        catzilla_upload_set_error(file, validation_result, "Validation failed");
        catzilla_upload_abort(file);

        // Send error response immediately
        catzilla_send_upload_error_response(stream, validation_result);
        return;
    }

    // Continue processing if validation passed
    catzilla_upload_process_chunk(file, buf->base, nread);
}
```

### **Error Response Format**
```json
{
  "error": {
    "type": "FileSizeError",
    "code": 1001,
    "message": "File size exceeds limit",
    "details": {
      "max_size_bytes": 104857600,
      "max_size_human": "100MB",
      "actual_size_bytes": 157286400,
      "actual_size_human": "150MB",
      "bytes_received": 52428800,
      "progress_percent": 33.33
    },
    "timestamp": "2025-06-29T10:30:45Z"
  }
}
```

### **Configuration Options**
```python
# Global upload configuration
app = Catzilla(
    upload_config={
        "default_max_size": "50MB",
        "global_timeout": 60,  # seconds
        "temp_directory": "/tmp/catzilla_uploads",
        "cleanup_failed_uploads": True,
        "early_validation": True,  # Stop upload on first validation failure
        "virus_scanning": {
            "enabled": True,
            "engine": "clamav",
            "quarantine_path": "/quarantine/"
        }
    }
)
```
---

## 📚 **Documentation Plan**

### **User Documentation**
- `docs/file-uploads.md` - Complete guide to file uploads
- `docs/upload-performance.md` - Performance optimization guide
- `docs/upload-security.md` - Security best practices

### **API Reference**
- `docs/api/upload-file.md` - UploadFile class reference
- `docs/api/file-parameter.md` - File() parameter reference
- `docs/api/streaming.md` - Streaming API reference

### **Examples**
- `examples/file_upload/` - Complete file upload examples
- `examples/image_upload/` - Image upload with validation
- `examples/batch_upload/` - Batch file upload demo

---

## 🚀 **Success Metrics**

### **Performance Benchmarks**
- **Multipart parsing**: 10x faster than FastAPI
- **Memory usage**: 90% reduction for large files
- **Concurrent uploads**: Support 1000+ simultaneous uploads
- **Streaming speed**: Network line speed for file writes

### **Developer Experience**
- **API compatibility**: Catzilla-style function signatures (no async/await)
- **Feature completeness**: All standard upload features + revolutionary C-native features
- **Documentation quality**: Clear examples with Catzilla patterns
- **Example coverage**: 20+ real-world examples

### **Security Standards**
- **OWASP compliance**: All file upload security guidelines
- **Penetration testing**: Zero vulnerabilities
- **Performance impact**: <5% overhead for security features

---

## 📅 **Timeline Summary**

| Phase | Duration | Key Deliverables |
|-------|----------|------------------|
| Phase 1 | 1 week | Core multipart parser, basic file handling |
| Phase 2 | 1 week | Zero-copy streaming, performance optimization |
| Phase 3 | 1 week | Python integration, FastAPI compatibility |
| Phase 4 | 1 week | Advanced security, validation features |
| **Total** | **4 weeks** | **Revolutionary file upload system** |

---

## 🎯 **Revolutionary Result**

**Catzilla will be the first Python framework to offer:**
- **Netflix-level streaming performance** in Python
- **Enterprise-grade security** built into the core
- **Real-time performance monitoring** for uploads
- **Zero-configuration optimization** that just works

This implementation will make Catzilla **unbeatable** for any application requiring file uploads, from simple forms to enterprise document management systems.

**Estimated Development Time**: 3-4 weeks for full implementation
**Performance Impact**: 10-100x improvement over existing Python frameworks
**Developer Experience**: Better than FastAPI with more features

---

## 📋 **Next Steps**

1. **Review and approve** this engineering plan
2. **Set up development environment** for file upload implementation
3. **Begin Phase 1** implementation with core multipart parser
4. **Continuous testing** and performance validation throughout development
5. **Documentation writing** parallel to implementation

**Ready to begin implementation upon confirmation!** 🚀

---

## 🦠 **Virus Scanning: External ClamAV Integration Strategy**

### **Design Philosophy: External Dependency with Smart Detection**

Catzilla will integrate with **externally installed ClamAV** rather than bundling it, keeping the framework lightweight while providing enterprise-grade virus scanning for users who need it.

### **Developer Experience:**

#### **When ClamAV is Available:**
```python
@app.post("/upload/")
def upload_file(request, file: UploadFile = File(virus_scan=True)):
    # ClamAV automatically detected and used
    saved_path = file.save_to("/uploads/")
    return {
        "filename": file.filename,
        "virus_scan": {
            "status": "clean",
            "engine": "clamav",
            "scan_time_ms": 150,
            "engine_version": "0.103.8"
        }
    }
```

#### **When ClamAV is Not Installed:**
```python
@app.post("/upload/")
def upload_file(request, file: UploadFile = File(virus_scan=True)):
    try:
        saved_path = file.save_to("/uploads/")
        return {"filename": file.filename}
    except VirusScanError as e:
        return {
            "error": "virus_scanner_unavailable",
            "message": "ClamAV not found. Install it to enable virus scanning.",
            "install_instructions": {
                "ubuntu": "sudo apt-get install clamav clamav-daemon",
                "centos": "sudo yum install clamav clamav-update",
                "macos": "brew install clamav",
                "windows": "Download from https://www.clamav.net/downloads"
            }
        }
```

### **C Implementation: External ClamAV Integration**

#### **ClamAV Detection and Validation**

```c
// src/core/upload_clamav.h
#ifndef CATZILLA_UPLOAD_CLAMAV_H
#define CATZILLA_UPLOAD_CLAMAV_H

typedef enum {
    CLAMAV_STATUS_NOT_FOUND = 0,
    CLAMAV_STATUS_FOUND_DAEMON = 1,
    CLAMAV_STATUS_FOUND_BINARY = 2,
    CLAMAV_STATUS_DAEMON_RUNNING = 3
} clamav_availability_t;

typedef struct {
    bool available;
    clamav_availability_t status;
    char* daemon_socket;        // /var/run/clamav/clamd.ctl
    char* binary_path;          // /usr/bin/clamdscan or /usr/bin/clamscan
    char* version;              // ClamAV version string
    bool daemon_running;        // Is clamd daemon running?
} clamav_system_info_t;

typedef struct {
    bool is_infected;
    bool is_error;
    char* threat_name;
    double scan_time_seconds;
    char* engine_version;
    char* error_message;
    int exit_code;
} clamav_scan_result_t;

// Core functions
int catzilla_clamav_detect_system(clamav_system_info_t* info);
clamav_scan_result_t* catzilla_clamav_scan_file(const char* file_path);
void catzilla_clamav_cleanup_result(clamav_scan_result_t* result);
const char* catzilla_clamav_get_install_instructions(void);

#endif
```

#### **System Detection Implementation**

```c
// src/core/upload_clamav.c
#include "upload_clamav.h"
#include "platform_compat.h"
#include "logging.h"
#include <sys/stat.h>
#include <unistd.h>

static clamav_system_info_t g_clamav_info = {0};
static bool g_clamav_detected = false;

int catzilla_clamav_detect_system(clamav_system_info_t* info) {
    if (!info) return -1;

    memset(info, 0, sizeof(clamav_system_info_t));

    LOG_INFO("Detecting ClamAV installation...");

    // 1. Check for clamd daemon socket (preferred method)
    const char* socket_paths[] = {
        "/var/run/clamav/clamd.ctl",     // Ubuntu/Debian
        "/var/run/clamd.scan/clamd.sock", // CentOS/RHEL
        "/tmp/clamd.socket",             // Generic
        "/usr/local/var/run/clamav/clamd.socket", // Homebrew macOS
        NULL
    };

    for (int i = 0; socket_paths[i]; i++) {
        struct stat st;
        if (stat(socket_paths[i], &st) == 0 && S_ISSOCK(st.st_mode)) {
            info->daemon_socket = catzilla_static_alloc(strlen(socket_paths[i]) + 1);
            strcpy(info->daemon_socket, socket_paths[i]);
            info->status = CLAMAV_STATUS_FOUND_DAEMON;
            LOG_INFO("Found ClamAV daemon socket: %s", socket_paths[i]);
            break;
        }
    }

    // 2. Check for ClamAV binaries
    const char* binary_paths[] = {
        "/usr/bin/clamdscan",        // Daemon client (preferred)
        "/usr/bin/clamscan",         // Direct scanner
        "/usr/local/bin/clamdscan",  // Homebrew
        "/usr/local/bin/clamscan",   // Homebrew
        "clamdscan",                 // In PATH
        "clamscan",                  // In PATH
        NULL
    };

    for (int i = 0; binary_paths[i]; i++) {
        if (access(binary_paths[i], X_OK) == 0) {
            info->binary_path = catzilla_static_alloc(strlen(binary_paths[i]) + 1);
            strcpy(info->binary_path, binary_paths[i]);
            if (info->status == CLAMAV_STATUS_NOT_FOUND) {
                info->status = CLAMAV_STATUS_FOUND_BINARY;
            }
            LOG_INFO("Found ClamAV binary: %s", binary_paths[i]);
            break;
        }
    }

    // 3. Test if daemon is actually running
    if (info->daemon_socket) {
        info->daemon_running = catzilla_test_clamd_connection(info->daemon_socket);
        if (info->daemon_running) {
            info->status = CLAMAV_STATUS_DAEMON_RUNNING;
            LOG_INFO("ClamAV daemon is running and accessible");
        }
    }

    // 4. Get version information
    if (info->binary_path) {
        info->version = catzilla_get_clamav_version(info->binary_path);
        LOG_INFO("ClamAV version: %s", info->version ? info->version : "unknown");
    }

    info->available = (info->status != CLAMAV_STATUS_NOT_FOUND);

    if (info->available) {
        LOG_INFO("ClamAV detected and available for virus scanning");
    } else {
        LOG_WARNING("ClamAV not found on system");
    }

    return info->available ? 0 : -1;
}

// Test daemon connectivity
static bool catzilla_test_clamd_connection(const char* socket_path) {
    int sock = socket(AF_UNIX, SOCK_STREAM, 0);
    if (sock < 0) return false;

    struct sockaddr_un addr;
    memset(&addr, 0, sizeof(addr));
    addr.sun_family = AF_UNIX;
    strncpy(addr.sun_path, socket_path, sizeof(addr.sun_path) - 1);

    bool connected = (connect(sock, (struct sockaddr*)&addr, sizeof(addr)) == 0);

    if (connected) {
        // Send PING command to test
        const char* ping_cmd = "zPING\0";
        send(sock, ping_cmd, 6, 0);

        char response[32];
        ssize_t received = recv(sock, response, sizeof(response) - 1, 0);
        if (received > 0) {
            response[received] = '\0';
            connected = (strstr(response, "PONG") != NULL);
        }
    }

    close(sock);
    return connected;
}

// Get ClamAV version
static char* catzilla_get_clamav_version(const char* binary_path) {
    char command[512];
    snprintf(command, sizeof(command), "%s --version 2>/dev/null", binary_path);

    FILE* fp = popen(command, "r");
    if (!fp) return NULL;

    char version_line[256];
    if (fgets(version_line, sizeof(version_line), fp)) {
        pclose(fp);

        // Parse version from output like "ClamAV 0.103.8/..."
        char* version_start = strstr(version_line, "ClamAV ");
        if (version_start) {
            version_start += 7; // Skip "ClamAV "
            char* version_end = strchr(version_start, '/');
            if (version_end) *version_end = '\0';

            char* version = catzilla_static_alloc(strlen(version_start) + 1);
            strcpy(version, version_start);
            return version;
        }
    }

    pclose(fp);
    return NULL;
}
```

#### **File Scanning Implementation**

```c
// ClamAV file scanning
clamav_scan_result_t* catzilla_clamav_scan_file(const char* file_path) {
    if (!g_clamav_detected) {
        // Initialize on first use
        if (catzilla_clamav_detect_system(&g_clamav_info) != 0) {
            g_clamav_detected = false;
            return NULL; // ClamAV not available
        }
        g_clamav_detected = true;
    }

    if (!g_clamav_info.available) {
        return NULL;
    }

    clamav_scan_result_t* result = catzilla_static_alloc(sizeof(clamav_scan_result_t));
    memset(result, 0, sizeof(clamav_scan_result_t));

    char command[2048];

    // Build scan command based on available tools
    if (g_clamav_info.daemon_running && g_clamav_info.daemon_socket) {
        // Use daemon client (fastest)
        snprintf(command, sizeof(command),
                "clamdscan --no-summary --infected --stdout %s 2>&1", file_path);
    } else if (g_clamav_info.binary_path) {
        // Use direct scanner
        snprintf(command, sizeof(command),
                "%s --no-summary --infected --stdout %s 2>&1",
                g_clamav_info.binary_path, file_path);
    } else {
        result->is_error = true;
        result->error_message = catzilla_static_alloc(64);
        strcpy(result->error_message, "No ClamAV scanner available");
        return result;
    }

    LOG_DEBUG("ClamAV scan command: %s", command);

    // Time the scan
    uint64_t start_time = catzilla_get_time_ns();

    // Execute scan with timeout
    FILE* fp = popen(command, "r");
    if (!fp) {
        result->is_error = true;
        result->error_message = catzilla_static_alloc(64);
        strcpy(result->error_message, "Failed to execute ClamAV");
        return result;
    }

    // Read scan output
    char output[1024] = {0};
    size_t output_len = fread(output, 1, sizeof(output) - 1, fp);
    output[output_len] = '\0';

    int exit_code = pclose(fp);

    uint64_t end_time = catzilla_get_time_ns();
    result->scan_time_seconds = (end_time - start_time) / 1e9;
    result->exit_code = exit_code;

    // Parse results based on exit code and output
    if (exit_code == 0) {
        // Clean file
        result->is_infected = false;
        result->is_error = false;
        LOG_DEBUG("ClamAV: File clean - %s (%.3fs)", file_path, result->scan_time_seconds);
    } else if (exit_code == 1) {
        // Infected file
        result->is_infected = true;
        result->is_error = false;

        // Extract threat name from output
        char* threat_start = strstr(output, ": ");
        if (threat_start) {
            threat_start += 2;
            char* threat_end = strstr(threat_start, " FOUND");
            if (threat_end) {
                size_t threat_len = threat_end - threat_start;
                result->threat_name = catzilla_static_alloc(threat_len + 1);
                strncpy(result->threat_name, threat_start, threat_len);
                result->threat_name[threat_len] = '\0';
            }
        }

        LOG_WARNING("ClamAV: Virus detected in %s - %s (%.3fs)",
                   file_path, result->threat_name ? result->threat_name : "unknown",
                   result->scan_time_seconds);
    } else {
        // Scan error
        result->is_infected = false;
        result->is_error = true;
        result->error_message = catzilla_static_alloc(strlen(output) + 1);
        strcpy(result->error_message, output);
        LOG_ERROR("ClamAV scan error for %s: %s", file_path, output);
    }

    // Add version info
    if (g_clamav_info.version) {
        result->engine_version = catzilla_static_alloc(strlen(g_clamav_info.version) + 1);
        strcpy(result->engine_version, g_clamav_info.version);
    }

    return result;
}
```

### **Python Integration: Smart Error Handling**

```python
# python/catzilla/uploads.py (addition)
class CatzillaUploadFile:
    def __init__(self, **config):
        self.virus_scan_enabled = config.get('virus_scan', False)
        self._virus_scan_result = None

    def save_to(self, path: str, stream: bool = True) -> str:
        # ... existing save logic ...

        if self.virus_scan_enabled:
            # Check ClamAV availability
            if not self._check_clamav_available():
                raise VirusScannerUnavailableError(self._get_install_instructions())

            # Perform virus scan
            scan_result = self._scan_virus()
            if scan_result and scan_result.is_infected:
                # Quarantine infected file
                self._quarantine_file()
                raise VirusScanError(scan_result.threat_name)

        return final_path

    def _check_clamav_available(self) -> bool:
        """Check if ClamAV is available on the system"""
        # Call C function to detect ClamAV
        return catzilla_c.clamav_is_available()

    def _get_install_instructions(self) -> dict:
        """Get platform-specific ClamAV installation instructions"""
        import platform
        system = platform.system().lower()

        instructions = {
            "linux": {
                "ubuntu/debian": "sudo apt-get install clamav clamav-daemon",
                "centos/rhel": "sudo yum install clamav clamav-update",
                "fedora": "sudo dnf install clamav clamav-update",
                "arch": "sudo pacman -S clamav"
            },
            "darwin": {
                "homebrew": "brew install clamav",
                "macports": "sudo port install clamav"
            },
            "windows": {
                "download": "Download from https://www.clamav.net/downloads",
                "chocolatey": "choco install clamav"
            }
        }

        return instructions.get(system, instructions)

    @property
    def virus_scan_result(self):
        """Get virus scan result with detailed information"""
        if not self._virus_scan_result:
            return None

        return {
            "status": "clean" if not self._virus_scan_result.is_infected else "infected",
            "threat_name": self._virus_scan_result.threat_name,
            "scan_time_seconds": self._virus_scan_result.scan_time_seconds,
            "engine_version": self._virus_scan_result.engine_version,
            "scanner": "clamav"
        }
```

### **Configuration and Startup Detection**

```python
# Enhanced Windows installation support
def _get_windows_install_instructions(self) -> dict:
    """Windows-specific ClamAV installation instructions"""
    return {
        "method_1_official": {
            "name": "Official ClamAV Windows Build",
            "steps": [
                "1. Download from https://www.clamav.net/downloads",
                "2. Run the installer as Administrator",
                "3. Add C:\\Program Files\\ClamAV to system PATH",
                "4. Start ClamAV service: net start ClamAV"
            ],
            "pros": "Official, most stable",
            "cons": "Manual installation"
        },
        "method_2_chocolatey": {
            "name": "Chocolatey Package Manager",
            "steps": [
                "1. Install Chocolatey: https://chocolatey.org/install",
                "2. Run: choco install clamav",
                "3. Start service: net start ClamAV"
            ],
            "pros": "Automated, easy updates",
            "cons": "Requires Chocolatey"
        },
        "method_3_winget": {
            "name": "Windows Package Manager (winget)",
            "steps": [
                "1. Run: winget install ClamAV.ClamAV",
                "2. Add to PATH if needed",
                "3. Start service: net start ClamAV"
            ],
            "pros": "Built into Windows 10/11",
            "cons": "Newer, less tested"
        },
        "method_4_docker": {
            "name": "Docker Container",
            "steps": [
                "1. Install Docker Desktop",
                "2. Run: docker run -d --name clamav clamav/clamav",
                "3. Configure Catzilla to use container"
            ],
            "pros": "Isolated, consistent",
            "cons": "Requires Docker"
        }
    }
```

### **10. Enhanced Windows Registry Detection**

```c
// Advanced Windows registry detection for ClamAV
#include <windows.h>
#include <shlwapi.h>

typedef struct {
    char install_path[MAX_PATH];
    char version[64];
    bool is_service_installed;
    bool is_daemon_running;
    char service_executable[MAX_PATH];
    char config_path[MAX_PATH];
} windows_clamav_registry_info_t;

int catzilla_detect_clamav_from_registry(windows_clamav_registry_info_t* info) {
    HKEY key;
    DWORD data_size;

    // Check multiple registry locations
    const char* registry_paths[] = {
        "SOFTWARE\\ClamAV",                                    // 64-bit install
        "SOFTWARE\\WOW6432Node\\ClamAV",                      // 32-bit on 64-bit
        "SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\ClamAV", // Uninstall info
        NULL
    };

    for (int i = 0; registry_paths[i]; i++) {
        if (RegOpenKeyEx(HKEY_LOCAL_MACHINE, registry_paths[i], 0, KEY_READ, &key) == ERROR_SUCCESS) {
            // Get installation path
            data_size = sizeof(info->install_path);
            if (RegQueryValueEx(key, "InstallLocation", NULL, NULL,
                              (LPBYTE)info->install_path, &data_size) == ERROR_SUCCESS) {

                // Verify ClamAV executables exist
                char clamscan_path[MAX_PATH];
                char clamd_path[MAX_PATH];

                snprintf(clamscan_path, sizeof(clamscan_path), "%s\\clamscan.exe", info->install_path);
                snprintf(clamd_path, sizeof(clamd_path), "%s\\clamd.exe", info->install_path);

                if (PathFileExists(clamscan_path)) {
                    // Get version information
                    data_size = sizeof(info->version);
                    RegQueryValueEx(key, "Version", NULL, NULL, (LPBYTE)info->version, &data_size);

                    // Check for service executable
                    if (PathFileExists(clamd_path)) {
                        strcpy(info->service_executable, clamd_path);
                        info->is_service_installed = true;
                    }

                    // Look for config file
                    snprintf(info->config_path, sizeof(info->config_path), "%s\\clamd.conf", info->install_path);

                    RegCloseKey(key);
                    return 0;  // Success
                }
            }
            RegCloseKey(key);
        }
    }

    return -1;  // Not found
}

// PowerShell-based detection as fallback
int catzilla_detect_clamav_powershell(windows_clamav_registry_info_t* info) {
    char powershell_cmd[] =
        "powershell.exe -Command \""
        "Get-WmiObject -Class Win32_Product | Where-Object {$_.Name -like '*ClamAV*'} | "
        "Select-Object Name,Version,InstallLocation | ConvertTo-Json\"";

    FILE* pipe = _popen(powershell_cmd, "r");
    if (!pipe) return -1;

    char buffer[4096];
    size_t total_read = 0;

    while (fgets(buffer + total_read, sizeof(buffer) - total_read, pipe) &&
           total_read < sizeof(buffer) - 1) {
        total_read += strlen(buffer + total_read);
    }

    int exit_code = _pclose(pipe);

    if (exit_code == 0 && total_read > 0) {
        // Parse JSON response (simplified - would use proper JSON parser in real implementation)
        char* install_location = strstr(buffer, "InstallLocation");
        if (install_location) {
            // Extract path from JSON
            char* path_start = strchr(install_location, ':');
            if (path_start) {
                path_start += 2;  // Skip ': "'
                char* path_end = strchr(path_start, '"');
                if (path_end) {
                    size_t path_len = path_end - path_start;
                    if (path_len < sizeof(info->install_path)) {
                        strncpy(info->install_path, path_start, path_len);
                        info->install_path[path_len] = '\0';
                        return 0;
                    }
                }
            }
        }
    }

    return -1;
}
```

### **11. Windows Named Pipe Communication**

```c
// Windows named pipe implementation for clamd communication
#include <windows.h>

typedef struct {
    HANDLE pipe_handle;
    char pipe_name[256];
    DWORD timeout_ms;
    bool is_connected;
} windows_clamav_pipe_t;

int catzilla_clamav_connect_named_pipe(windows_clamav_pipe_t* pipe_conn,
                                      const char* pipe_name, DWORD timeout) {
    snprintf(pipe_conn->pipe_name, sizeof(pipe_conn->pipe_name),
             "\\\\.\\pipe\\%s", pipe_name ? pipe_name : "ClamAVPipe");

    pipe_conn->timeout_ms = timeout;

    // Wait for pipe to become available
    if (!WaitNamedPipe(pipe_conn->pipe_name, timeout)) {
        LOG_ERROR("Named pipe not available: %s", pipe_conn->pipe_name);
        return -1;
    }

    // Connect to pipe
    pipe_conn->pipe_handle = CreateFile(
        pipe_conn->pipe_name,
        GENERIC_READ | GENERIC_WRITE,
        0,              // No sharing
        NULL,           // Default security
        OPEN_EXISTING,
        0,              // Default attributes
        NULL            // No template
    );

    if (pipe_conn->pipe_handle == INVALID_HANDLE_VALUE) {
        LOG_ERROR("Failed to connect to named pipe: %s (Error: %lu)",
                 pipe_conn->pipe_name, GetLastError());
        return -1;
    }

    // Set pipe to message mode
    DWORD pipe_mode = PIPE_READMODE_MESSAGE;
    if (!SetNamedPipeHandleState(pipe_conn->pipe_handle, &pipe_mode, NULL, NULL)) {
        LOG_WARNING("Could not set pipe to message mode");
    }

    pipe_conn->is_connected = true;
    LOG_INFO("Connected to ClamAV named pipe: %s", pipe_conn->pipe_name);
    return 0;
}

int catzilla_clamav_scan_via_pipe(windows_clamav_pipe_t* pipe_conn,
                                 const char* file_path,
                                 clamav_scan_result_t* result) {
    if (!pipe_conn->is_connected) {
        return -1;
    }

    // Prepare scan command
    char command[MAX_PATH + 32];
    snprintf(command, sizeof(command), "SCAN %s\n", file_path);

    // Send command
    DWORD bytes_written;
    if (!WriteFile(pipe_conn->pipe_handle, command, strlen(command),
                  &bytes_written, NULL)) {
        LOG_ERROR("Failed to write to pipe: %lu", GetLastError());
        return -1;
    }

    // Read response
    char response[1024];
    DWORD bytes_read;
    if (!ReadFile(pipe_conn->pipe_handle, response, sizeof(response) - 1,
                 &bytes_read, NULL)) {
        LOG_ERROR("Failed to read from pipe: %lu", GetLastError());
        return -1;
    }

    response[bytes_read] = '\0';

    // Parse response
    return catzilla_clamav_parse_scan_response(response, result);
}

void catzilla_clamav_disconnect_pipe(windows_clamav_pipe_t* pipe_conn) {
    if (pipe_conn->is_connected && pipe_conn->pipe_handle != INVALID_HANDLE_VALUE) {
        CloseHandle(pipe_conn->pipe_handle);
        pipe_conn->pipe_handle = INVALID_HANDLE_VALUE;
        pipe_conn->is_connected = false;
        LOG_INFO("Disconnected from ClamAV named pipe");
    }
}
```

### **12. Windows Service Management Integration**

```python
# Python Windows service management
import win32service
import win32serviceutil
import win32con
import pywintypes

class WindowsClamAVManager:
    """Windows-specific ClamAV service management"""

    SERVICE_NAMES = [
        "ClamAV",           # Default service name
        "ClamWin",          # ClamWin installation
        "ClamAVService",    # Alternative name
    ]

    def __init__(self):
        self.service_name = None
        self.service_handle = None
        self.scm_handle = None

    def detect_service(self) -> bool:
        """Detect ClamAV Windows service"""
        try:
            self.scm_handle = win32service.OpenSCManager(
                None, None, win32service.SC_MANAGER_ENUMERATE_SERVICE
            )

            for service_name in self.SERVICE_NAMES:
                try:
                    service_handle = win32service.OpenService(
                        self.scm_handle, service_name,
                        win32service.SERVICE_QUERY_STATUS | win32service.SERVICE_QUERY_CONFIG
                    )

                    # Service exists
                    self.service_name = service_name
                    self.service_handle = service_handle
                    return True

                except pywintypes.error:
                    continue  # Service not found, try next

        except pywintypes.error as e:
            LOG_ERROR(f"Failed to access Service Control Manager: {e}")

        return False

    def is_service_running(self) -> bool:
        """Check if ClamAV service is running"""
        if not self.service_handle:
            return False

        try:
            status = win32service.QueryServiceStatusEx(self.service_handle);
            return status['CurrentState'] == win32service.SERVICE_RUNNING
        except pywintypes.error:
            return False

    def start_service(self, timeout: int = 30) -> bool:
        """Start ClamAV service"""
        if not self.service_handle:
            return False

        try:
            win32service.StartService(self.service_handle, None)

            # Wait for service to start
            import time
            start_time = time.time()
            while time.time() - start_time < timeout:
                if self.is_service_running():
                    return True
                time.sleep(1)

        except pywintypes.error as e:
            LOG_ERROR(f"Failed to start ClamAV service: {e}")

        return False

    def get_service_config(self) -> dict:
        """Get service configuration information"""
        if not self.service_handle:
            return {}

        try:
            config = win32service.QueryServiceConfig(self.service_handle)
            return {
                "binary_path": config[3],
                "display_name": config[1],
                "start_type": config[2],
                "service_type": config[0],
            }
        except pywintypes.error:
            return {}

    def cleanup(self):
        """Clean up service handles"""
        if self.service_handle:
            win32service.CloseServiceHandle(self.service_handle)
        if self.scm_handle:
            win32service.CloseServiceHandle(self.scm_handle)
```

### **13. Windows PowerShell Integration for Advanced Detection**

```python
# PowerShell-based system detection and configuration
import subprocess
import json
import tempfile
import os

class WindowsPowerShellClamAVDetector:
    """Use PowerShell for comprehensive ClamAV detection on Windows"""

    DETECTION_SCRIPT = '''
    $results = @{}

    # Check installed programs
    $programs = Get-WmiObject -Class Win32_Product | Where-Object {$_.Name -like "*ClamAV*" -or $_.Name -like "*ClamWin*"}
    if ($programs) {
        $results.installed_programs = $programs | Select-Object Name, Version, InstallLocation
    }

    # Check running processes
    $processes = Get-Process | Where-Object {$_.ProcessName -like "*clam*"}
    if ($processes) {
        $results.running_processes = $processes | Select-Object ProcessName, Id, Path
    }

    # Check Windows services
    $services = Get-Service | Where-Object {$_.Name -like "*clam*"}
    if ($services) {
        $results.services = $services | Select-Object Name, Status, DisplayName
    }

    # Check common installation paths
    $common_paths = @(
        "${env:ProgramFiles}\\ClamAV",
        "${env:ProgramFiles(x86)}\\ClamAV",
        "${env:ProgramFiles}\\ClamWin",
        "${env:ProgramFiles(x86)}\\ClamWin"
    )

    $existing_paths = @()
    foreach ($path in $common_paths) {
        if (Test-Path $path) {
            $executables = @()
            if (Test-Path "$path\\clamscan.exe") { $executables += "clamscan.exe" }
            if (Test-Path "$path\\clamd.exe") { $executables += "clamd.exe" }
            if (Test-Path "$path\\clamdscan.exe") { $executables += "clamdscan.exe" }

            if ($executables.Count -gt 0) {
                $existing_paths += @{
                    "path" = $path
                    "executables" = $executables
                }
            }
        }
    }

    if ($existing_paths.Count -gt 0) {
        $results.installation_paths = $existing_paths
    }

    # Check PATH environment variable
    $env_path = $env:PATH -split ";"
    $clamav_in_path = $env_path | Where-Object {$_ -like "*clam*"}
    if ($clamav_in_path) {
        $results.path_entries = $clamav_in_path
    }

    # Output as JSON
    $results | ConvertTo-Json -Depth 10
    '''

    def detect_comprehensive(self) -> dict:
        """Run comprehensive PowerShell-based detection"""
        try:
            # Write PowerShell script to temp file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.ps1', delete=False) as f:
                f.write(self.DETECTION_SCRIPT)
                script_path = f.name

            try:
                # Execute PowerShell script
                result = subprocess.run([
                    'powershell.exe',
                    '-ExecutionPolicy', 'Bypass',
                    '-File', script_path
                ], capture_output=True, text=True, timeout=30)

                if result.returncode == 0 and result.stdout:
                    return json.loads(result.stdout)
                else:
                    LOG_ERROR(f"PowerShell detection failed: {result.stderr}")
                    return {}

            finally:
                # Clean up temp file
                os.unlink(script_path)

        except Exception as e:
            LOG_ERROR(f"PowerShell detection error: {e}")
            return {}

    def install_via_chocolatey(self) -> bool:
        """Install ClamAV via Chocolatey if available"""
        try:
            # Check if Chocolatey is available
            choco_check = subprocess.run(['choco', '--version'],
                                       capture_output=True, text=True, timeout=10)

            if choco_check.returncode != 0:
                LOG_INFO("Chocolatey not available for automatic ClamAV installation")
                return False

            # Install ClamAV
            LOG_INFO("Installing ClamAV via Chocolatey...")
            install_result = subprocess.run(['choco', 'install', 'clamav', '-y'],
                                          capture_output=True, text=True, timeout=300)

            if install_result.returncode == 0:
                LOG_INFO("ClamAV installed successfully via Chocolatey")
                return True
            else:
                LOG_ERROR(f"Chocolatey installation failed: {install_result.stderr}")
                return False

        except Exception as e:
            LOG_ERROR(f"Chocolatey installation error: {e}")
            return False
```

### **14. Windows Enterprise Deployment Patterns**

```python
# Enterprise deployment configuration for Windows environments
class WindowsEnterpriseClamAVConfig:
    """Enterprise-grade Windows ClamAV configuration"""

    def __init__(self, app_config: dict):
        self.app_config = app_config
        self.domain_controller = self._detect_domain_controller()
        self.is_domain_joined = self._is_domain_joined()

    def configure_enterprise_scanning(self) -> dict:
        """Configure for enterprise Windows environment"""
        config = {
            "virus_scanning": {
                "enabled": True,
                "enterprise_mode": True,
                "windows_enterprise": {
                    # Central ClamAV server configuration
                    "central_server": {
                        "enabled": self._has_central_clamav_server(),
                        "server_address": self._get_clamav_server_address(),
                        "server_port": 3310,
                        "use_ssl": True,
                        "authentication": "domain"
                    },

                    # Local fallback configuration
                    "local_fallback": {
                        "enabled": True,
                        "service_name": "ClamAV",
                        "auto_start_service": True,
                        "service_timeout": 60
                    },

                    # Group Policy integration
                    "group_policy": {
                        "respect_domain_policies": True,
                        "policy_override_allowed": False,
                        "audit_scanning": True,
                        "log_to_event_log": True
                    },

                    # Performance optimization
                    "performance": {
                        "use_memory_mapped_files": True,
                        "parallel_scanning": True,
                        "max_concurrent_scans": 4,
                        "scan_cache_enabled": True,
                        "cache_duration_hours": 24
                    }
                }
            }
        }

        return config

    def _detect_domain_controller(self) -> str:
        """Detect domain controller for centralized ClamAV"""
        try:
            result = subprocess.run([
                'powershell.exe', '-Command',
                '(Get-WmiObject -Class Win32_ComputerSystem).Domain'
            ], capture_output=True, text=True, timeout=10)

            if result.returncode == 0:
                domain = result.stdout.strip()
                if domain and domain != 'WORKGROUP':
                    return domain
        except:
            pass
        return None

    def _is_domain_joined(self) -> bool:
        """Check if machine is domain-joined"""
        return self.domain_controller is not None

    def _has_central_clamav_server(self) -> bool:
        """Check for central ClamAV server via DNS/registry"""
        if not self.is_domain_joined:
            return False

        try:
            # Check for ClamAV SRV record
            import socket
            clamav_host = f"clamav.{self.domain_controller}"
            socket.gethostbyname(clamav_host)
            return True
        except:
            pass

        # Check registry for enterprise configuration
        try:
            import winreg
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                               "SOFTWARE\\Policies\\ClamAV\\Enterprise")
            server_address, _ = winreg.QueryValueEx(key, "CentralServer")
            winreg.CloseKey(key)
            return bool(server_address)
        except:
            pass

        return False

    def _get_clamav_server_address(self) -> str:
        """Get central ClamAV server address"""
        if not self.is_domain_joined:
            return None

        # Try registry first
        try:
            import winreg
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                               "SOFTWARE\\Policies\\ClamAV\\Enterprise")
            server_address, _ = winreg.QueryValueEx(key, "CentralServer")
            winreg.CloseKey(key);
            return server_address;
        }
