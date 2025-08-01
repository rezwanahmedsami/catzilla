#!/usr/bin/env python3
"""
Shared file operation endpoint definitions for consistent benchmarking across frameworks.

This module defines file operation test scenarios that each framework will implement
to ensure fair performance comparisons for file handling capabilities.
"""

import json
import time
import base64
from typing import Dict, Any, List
from pathlib import Path

def get_file_endpoints():
    """
    Returns file operation endpoint definitions for benchmarking.
    Each endpoint tests different aspects of file handling performance.
    """
    return {
        # Single file upload
        "upload_single": {
            "method": "POST",
            "path": "/upload/single",
            "description": "Single file upload performance",
            "content_type": "multipart/form-data"
        },

        # Multiple file upload
        "upload_multiple": {
            "method": "POST",
            "path": "/upload/multiple",
            "description": "Multiple file upload performance",
            "content_type": "multipart/form-data"
        },

        # Chunked upload
        "upload_chunked": {
            "method": "POST",
            "path": "/upload/chunked",
            "description": "Chunked file upload performance",
            "content_type": "multipart/form-data"
        },

        # Static file serving
        "static_small": {
            "method": "GET",
            "path": "/static/small.txt",
            "description": "Small static file serving (1KB)"
        },

        "static_medium": {
            "method": "GET",
            "path": "/static/medium.txt",
            "description": "Medium static file serving (100KB)"
        },

        "static_large": {
            "method": "GET",
            "path": "/static/large.txt",
            "description": "Large static file serving (1MB)"
        },

        "static_json": {
            "method": "GET",
            "path": "/static/test.json",
            "description": "JSON static file serving"
        },

        "static_html": {
            "method": "GET",
            "path": "/static/test.html",
            "description": "HTML static file serving"
        },

        "static_binary": {
            "method": "GET",
            "path": "/static/binary.bin",
            "description": "Binary static file serving"
        },

        # Range requests
        "static_range": {
            "method": "GET",
            "path": "/static-range/large.txt",
            "description": "Static file serving with range requests",
            "headers": {"Range": "bytes=0-1023"}
        },

        # File streaming
        "stream_file": {
            "method": "GET",
            "path": "/stream/file/medium.txt",
            "description": "File streaming performance"
        },

        "stream_generated_1mb": {
            "method": "GET",
            "path": "/stream/generated/1",
            "description": "Generated data streaming (1MB)"
        },

        "stream_generated_10mb": {
            "method": "GET",
            "path": "/stream/generated/10",
            "description": "Generated data streaming (10MB)"
        },

        # File processing
        "process_validate_checksum": {
            "method": "POST",
            "path": "/process/validate",
            "description": "File validation with checksum",
            "content_type": "multipart/form-data"
        },

        "process_validate_content": {
            "method": "POST",
            "path": "/process/validate",
            "description": "File validation with content analysis",
            "content_type": "multipart/form-data"
        },

        "process_transform_uppercase": {
            "method": "POST",
            "path": "/process/transform",
            "description": "File transformation (uppercase)",
            "content_type": "multipart/form-data"
        },

        "process_transform_base64": {
            "method": "POST",
            "path": "/process/transform",
            "description": "File transformation (base64 encoding)",
            "content_type": "multipart/form-data"
        },

        # File management
        "list_files": {
            "method": "GET",
            "path": "/files/list",
            "description": "File listing performance"
        },

        "list_files_uploads": {
            "method": "GET",
            "path": "/files/list?directory=uploads&limit=50",
            "description": "Upload directory listing"
        },

        "list_files_static": {
            "method": "GET",
            "path": "/files/list?directory=static&limit=50",
            "description": "Static directory listing"
        }
    }


# Test file generators for different sizes
def generate_test_file_content(size_kb: int = 1) -> bytes:
    """Generate test file content of specified size in KB"""
    content = "Test file content for benchmarking. " * (size_kb * 30)  # Approximate 1KB per 30 repetitions
    return content.encode('utf-8')[:size_kb * 1024]  # Ensure exact size

def generate_binary_test_file(size_kb: int = 1) -> bytes:
    """Generate binary test file content"""
    return bytes(range(256)) * (size_kb * 4)  # 256 bytes * 4 = 1KB per repetition

def generate_json_test_file(records: int = 100) -> str:
    """Generate JSON test file with specified number of records"""
    data = {
        "metadata": {
            "generated_at": time.time(),
            "record_count": records,
            "purpose": "file_operations_benchmark"
        },
        "records": [
            {
                "id": i,
                "name": f"Record {i}",
                "value": i * 10,
                "active": i % 2 == 0,
                "tags": [f"tag{j}" for j in range(i % 5)],
                "data": {
                    "x": i * 1.1,
                    "y": i * 2.2,
                    "z": i * 3.3
                }
            }
            for i in range(1, records + 1)
        ]
    }
    return json.dumps(data, indent=2)

def generate_csv_test_file(rows: int = 1000) -> str:
    """Generate CSV test file with specified number of rows"""
    lines = ["id,name,email,age,salary,department"]
    for i in range(1, rows + 1):
        lines.append(f"{i},User{i},user{i}@example.com,{25 + (i % 40)},{30000 + (i * 100)},Dept{i % 10}")
    return "\n".join(lines)

def generate_html_test_file(elements: int = 100) -> str:
    """Generate HTML test file with specified number of elements"""
    html = """<!DOCTYPE html>
<html>
<head>
    <title>File Operations Benchmark Test</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .item { border: 1px solid #ccc; margin: 10px; padding: 10px; }
        .header { background-color: #f0f0f0; font-weight: bold; }
    </style>
</head>
<body>
    <h1>File Operations Benchmark Test Page</h1>
    <p>This HTML file is generated for testing file operations performance.</p>
    <div class="items">
"""

    for i in range(1, elements + 1):
        html += f"""
        <div class="item">
            <div class="header">Item {i}</div>
            <p>This is item number {i} in the test file.</p>
            <ul>
                <li>ID: {i}</li>
                <li>Value: {i * 10}</li>
                <li>Status: {'Active' if i % 2 == 0 else 'Inactive'}</li>
            </ul>
        </div>"""

    html += """
    </div>
    <script>
        console.log('File operations benchmark test page loaded');
        document.querySelectorAll('.item').forEach((item, index) => {
            item.addEventListener('click', () => {
                console.log(`Clicked item ${index + 1}`);
            });
        });
    </script>
</body>
</html>"""

    return html

# Predefined test file configurations
TEST_FILES = {
    "text_small": {
        "name": "small.txt",
        "content": generate_test_file_content(1),  # 1KB
        "content_type": "text/plain"
    },
    "text_medium": {
        "name": "medium.txt",
        "content": generate_test_file_content(100),  # 100KB
        "content_type": "text/plain"
    },
    "text_large": {
        "name": "large.txt",
        "content": generate_test_file_content(1024),  # 1MB
        "content_type": "text/plain"
    },
    "json_small": {
        "name": "test.json",
        "content": generate_json_test_file(10).encode('utf-8'),
        "content_type": "application/json"
    },
    "json_large": {
        "name": "large.json",
        "content": generate_json_test_file(1000).encode('utf-8'),
        "content_type": "application/json"
    },
    "csv_medium": {
        "name": "test.csv",
        "content": generate_csv_test_file(1000).encode('utf-8'),
        "content_type": "text/csv"
    },
    "html_small": {
        "name": "test.html",
        "content": generate_html_test_file(50).encode('utf-8'),
        "content_type": "text/html"
    },
    "binary_medium": {
        "name": "binary.bin",
        "content": generate_binary_test_file(256),  # 256KB
        "content_type": "application/octet-stream"
    }
}

def get_test_file(file_type: str) -> Dict[str, Any]:
    """Get test file configuration by type"""
    return TEST_FILES.get(file_type, TEST_FILES["text_small"])

def create_temp_test_file(file_type: str, temp_dir: Path) -> Path:
    """Create a temporary test file for uploading"""
    file_config = get_test_file(file_type)
    file_path = temp_dir / file_config["name"]
    file_path.write_bytes(file_config["content"])
    return file_path
