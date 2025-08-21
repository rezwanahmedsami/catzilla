"""
Upload-specific exceptions for Catzilla's file upload system.

These exceptions provide detailed error information and handling
for the revolutionary C-native upload system.
"""

from typing import Any, Dict, List, Optional


class UploadError(Exception):
    """Base class for all upload-related errors."""

    def __init__(self, message: str, error_code: int = None, details: dict = None):
        super().__init__(message)
        self.error_code = error_code
        self.details = details or {}
        self.timestamp = None

        # Add timestamp for error tracking
        import time

        self.timestamp = time.time()


class FileSizeError(UploadError):
    """Raised when file exceeds size limit."""

    def __init__(self, max_size: int, actual_size: int, **kwargs):
        self.max_size = max_size
        self.actual_size = actual_size
        self.size_mb = actual_size / (1024 * 1024)
        self.max_size_mb = max_size / (1024 * 1024)

        message = f"File size {self._format_size(actual_size)} exceeds limit {self._format_size(max_size)}"

        details = {
            "max_size_bytes": max_size,
            "max_size_human": self._format_size(max_size),
            "actual_size_bytes": actual_size,
            "actual_size_human": self._format_size(actual_size),
            "excess_bytes": actual_size - max_size,
            "excess_human": self._format_size(actual_size - max_size),
        }

        super().__init__(message, error_code=1001, details=details, **kwargs)

    @staticmethod
    def _format_size(size_bytes: int) -> str:
        """Format byte size to human readable string."""
        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} PB"


class MimeTypeError(UploadError):
    """Raised when file type is not allowed."""

    def __init__(
        self, allowed_types: List[str], actual_type: str, filename: str = None, **kwargs
    ):
        self.allowed_types = allowed_types
        self.actual_type = actual_type
        self.filename = filename

        message = f"File type '{actual_type}' not in allowed types {allowed_types}"
        if filename:
            message = f"File '{filename}' has type '{actual_type}' not in allowed types {allowed_types}"

        details = {
            "allowed_types": allowed_types,
            "actual_type": actual_type,
            "filename": filename,
            "suggestion": self._suggest_correct_type(actual_type, allowed_types),
        }

        super().__init__(message, error_code=1002, details=details, **kwargs)

    @staticmethod
    def _suggest_correct_type(
        actual_type: str, allowed_types: List[str]
    ) -> Optional[str]:
        """Suggest the closest allowed type."""
        # Simple suggestion logic - could be enhanced
        if actual_type.startswith("image/") and any(
            t.startswith("image/") for t in allowed_types
        ):
            return next(t for t in allowed_types if t.startswith("image/"))
        if actual_type.startswith("application/") and any(
            t.startswith("application/") for t in allowed_types
        ):
            return next(t for t in allowed_types if t.startswith("application/"))
        return None


class FileSignatureError(UploadError):
    """Raised when file signature doesn't match MIME type."""

    def __init__(
        self, expected_type: str, actual_signature: str, filename: str = None, **kwargs
    ):
        self.expected_type = expected_type
        self.actual_signature = actual_signature
        self.filename = filename

        message = f"File signature mismatch: expected {expected_type}, detected {actual_signature}"
        if filename:
            message = f"File '{filename}' signature mismatch: expected {expected_type}, detected {actual_signature}"

        details = {
            "expected_type": expected_type,
            "actual_signature": actual_signature,
            "filename": filename,
            "security_risk": "File extension/type may not match actual file content",
        }

        super().__init__(message, error_code=1003, details=details, **kwargs)


class VirusScanError(UploadError):
    """Raised when virus is detected in file."""

    def __init__(
        self,
        threat_name: str,
        filename: str = None,
        scan_engine: str = "clamav",
        **kwargs,
    ):
        self.threat_name = threat_name
        self.filename = filename
        self.scan_engine = scan_engine

        message = f"Virus detected: {threat_name}"
        if filename:
            message = f"Virus detected in '{filename}': {threat_name}"

        details = {
            "threat_name": threat_name,
            "filename": filename,
            "scan_engine": scan_engine,
            "action_taken": "File quarantined or deleted",
            "security_level": "CRITICAL",
        }

        super().__init__(message, error_code=1004, details=details, **kwargs)


class DiskSpaceError(UploadError):
    """Raised when insufficient disk space for upload."""

    def __init__(
        self, required_mb: float, available_mb: float, path: str = None, **kwargs
    ):
        self.required_mb = required_mb
        self.available_mb = available_mb
        self.path = path

        message = f"Insufficient disk space: need {required_mb:.1f} MB, only {available_mb:.1f} MB available"
        if path:
            message += f" at {path}"

        details = {
            "required_mb": required_mb,
            "available_mb": available_mb,
            "deficit_mb": required_mb - available_mb,
            "path": path,
        }

        super().__init__(message, error_code=1005, details=details, **kwargs)


class UploadTimeoutError(UploadError):
    """Raised when upload takes too long."""

    def __init__(
        self,
        timeout_seconds: int,
        elapsed_seconds: float,
        bytes_received: int = 0,
        total_bytes: int = 0,
        **kwargs,
    ):
        self.timeout_seconds = timeout_seconds
        self.elapsed_seconds = elapsed_seconds
        self.bytes_received = bytes_received
        self.total_bytes = total_bytes

        message = f"Upload timeout: {elapsed_seconds:.1f}s exceeded limit of {timeout_seconds}s"

        progress = 0.0
        if total_bytes > 0:
            progress = (bytes_received / total_bytes) * 100
            message += f" (progress: {progress:.1f}%)"

        details = {
            "timeout_seconds": timeout_seconds,
            "elapsed_seconds": elapsed_seconds,
            "bytes_received": bytes_received,
            "total_bytes": total_bytes,
            "progress_percent": progress,
        }

        super().__init__(message, error_code=1006, details=details, **kwargs)


class VirusScannerUnavailableError(UploadError):
    """Raised when virus scanning is requested but ClamAV is not available."""

    def __init__(self, install_instructions: Dict[str, Any] = None, **kwargs):
        self.install_instructions = install_instructions or {}

        message = "ClamAV not found. Install ClamAV to enable virus scanning."

        details = {
            "scanner": "clamav",
            "install_instructions": self.install_instructions,
            "help_url": "https://docs.clamav.net/manual/Installing.html",
        }

        super().__init__(message, error_code=1007, details=details, **kwargs)


class UploadCorruptedError(UploadError):
    """Raised when uploaded file is corrupted or invalid."""

    def __init__(self, corruption_type: str, filename: str = None, **kwargs):
        self.corruption_type = corruption_type
        self.filename = filename

        message = f"File corruption detected: {corruption_type}"
        if filename:
            message = f"File '{filename}' corruption detected: {corruption_type}"

        details = {
            "corruption_type": corruption_type,
            "filename": filename,
            "recommended_action": "Request file re-upload",
        }

        super().__init__(message, error_code=1008, details=details, **kwargs)


class PathTraversalError(UploadError):
    """Raised when path traversal attack is detected."""

    def __init__(self, attempted_path: str, **kwargs):
        self.attempted_path = attempted_path

        message = f"Path traversal attempt detected: {attempted_path}"

        details = {
            "attempted_path": attempted_path,
            "security_risk": "CRITICAL - Path traversal attack attempt",
            "action_taken": "Upload blocked",
        }

        super().__init__(message, error_code=1009, details=details, **kwargs)


class UploadNetworkError(UploadError):
    """Raised when network issues occur during upload."""

    def __init__(self, network_error: str, bytes_received: int = 0, **kwargs):
        self.network_error = network_error
        self.bytes_received = bytes_received

        message = f"Network error during upload: {network_error}"

        details = {
            "network_error": network_error,
            "bytes_received": bytes_received,
            "recovery_possible": bytes_received > 0,
        }

        super().__init__(message, error_code=1010, details=details, **kwargs)


class UploadMemoryError(UploadError):
    """Raised when memory allocation fails during upload."""

    def __init__(self, allocation_size: int, operation: str = None, **kwargs):
        self.allocation_size = allocation_size
        self.operation = operation

        message = f"Memory allocation failed: {allocation_size} bytes"
        if operation:
            message += f" during {operation}"

        details = {
            "allocation_size": allocation_size,
            "operation": operation,
            "suggestion": "Reduce upload size or increase available memory",
        }

        super().__init__(message, error_code=1011, details=details, **kwargs)


class TooManyFilesError(UploadError):
    """Raised when too many files are uploaded at once."""

    def __init__(self, max_files: int, actual_files: int, **kwargs):
        self.max_files = max_files
        self.actual_files = actual_files

        message = f"Too many files: {actual_files} exceeds limit of {max_files}"

        details = {
            "max_files": max_files,
            "actual_files": actual_files,
            "excess_files": actual_files - max_files,
        }

        super().__init__(message, error_code=1012, details=details, **kwargs)


# Utility functions for error handling
def format_upload_error(error: UploadError) -> Dict[str, Any]:
    """
    Format upload error for JSON response.

    Args:
        error: Upload error instance

    Returns:
        Formatted error dictionary
    """
    return {
        "error": {
            "type": error.__class__.__name__,
            "code": error.error_code,
            "message": str(error),
            "details": error.details,
            "timestamp": error.timestamp,
        }
    }


def is_recoverable_error(error: UploadError) -> bool:
    """
    Check if an upload error is recoverable.

    Args:
        error: Upload error instance

    Returns:
        True if error is recoverable (retry possible)
    """
    recoverable_errors = [
        UploadTimeoutError,
        UploadNetworkError,
        DiskSpaceError,
        UploadMemoryError,
    ]

    return any(isinstance(error, err_type) for err_type in recoverable_errors)


def get_error_suggestion(error: UploadError) -> str:
    """
    Get user-friendly suggestion for fixing the error.

    Args:
        error: Upload error instance

    Returns:
        Suggestion string
    """
    suggestions = {
        FileSizeError: "Please reduce the file size or split into smaller files.",
        MimeTypeError: "Please ensure the file is in an allowed format.",
        FileSignatureError: "The file may be corrupted or renamed. Please verify the file.",
        VirusScanError: "Please scan the file with antivirus software before uploading.",
        DiskSpaceError: "Please free up disk space or contact system administrator.",
        UploadTimeoutError: "Please try uploading again with a more stable connection.",
        VirusScannerUnavailableError: "Please install ClamAV or disable virus scanning.",
        TooManyFilesError: "Please upload fewer files at once.",
    }

    return suggestions.get(type(error), "Please try again or contact support.")


# Exception mapping for C error codes
C_ERROR_CODE_MAPPING = {
    -1001: FileSizeError,
    -1002: MimeTypeError,
    -1003: FileSignatureError,
    -1004: VirusScanError,
    -1005: DiskSpaceError,
    -1006: UploadTimeoutError,
    -1007: UploadCorruptedError,
    -1008: PathTraversalError,
    -1009: UploadMemoryError,
    -1010: UploadNetworkError,
}


def create_exception_from_c_error(
    error_code: int, message: str, details: Dict[str, Any] = None
) -> UploadError:
    """
    Create appropriate Python exception from C error code.

    Args:
        error_code: C error code
        message: Error message
        details: Additional error details

    Returns:
        Appropriate UploadError subclass instance
    """
    exception_class = C_ERROR_CODE_MAPPING.get(error_code, UploadError)

    # Create exception with appropriate parameters based on type
    if exception_class == FileSizeError and details:
        return FileSizeError(
            max_size=details.get("max_size", 0),
            actual_size=details.get("actual_size", 0),
        )
    elif exception_class == MimeTypeError and details:
        return MimeTypeError(
            allowed_types=details.get("allowed_types", []),
            actual_type=details.get("actual_type", "unknown"),
            filename=details.get("filename"),
        )
    elif exception_class == VirusScanError and details:
        return VirusScanError(
            threat_name=details.get("threat_name", "Unknown"),
            filename=details.get("filename"),
        )
    else:
        return exception_class(message, details=details)
