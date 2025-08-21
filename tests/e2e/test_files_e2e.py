#!/usr/bin/env python3
"""
E2E Tests for File Operations

Tests file upload, download, static serving, and file management functionality
via real HTTP requests to a live Catzilla server instance.
"""
import pytest
import pytest_asyncio
import httpx
import asyncio
import tempfile
import io
from pathlib import Path

from tests.e2e.utils.server_manager import get_server_manager

# Server configuration
FILES_SERVER_HOST = "127.0.0.1"
FILES_SERVER_PORT = 8106

@pytest_asyncio.fixture(scope="module")
async def files_server():
    """Start and manage files E2E test server"""
    server_manager = get_server_manager()

    # Start the files server
    success = await server_manager.start_server("files", FILES_SERVER_PORT, FILES_SERVER_HOST)
    if not success:
        pytest.fail("Failed to start files test server")

    # Return server URL
    yield f"http://{FILES_SERVER_HOST}:{FILES_SERVER_PORT}"

    # Cleanup
    await server_manager.stop_server("files")

@pytest.mark.asyncio
async def test_files_health_check(files_server):
    """Test files server health check"""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{files_server}/health")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "healthy"
        assert data["server"] == "files_e2e_test"
        assert "upload_directory" in data
        assert "static_directory" in data
        assert "operations_count" in data

@pytest.mark.asyncio
async def test_files_home_info(files_server):
    """Test files server info endpoint"""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{files_server}/")
        assert response.status_code == 200

        data = response.json()
        assert "File Operations" in data["message"]
        assert "features" in data
        assert "endpoints" in data
        assert "upload_directory" in data
        assert "static_directory" in data

@pytest.mark.asyncio
async def test_static_file_serving(files_server):
    """Test static file serving"""
    async with httpx.AsyncClient() as client:
        # Test text file
        response = await client.get(f"{files_server}/static/test.txt")
        assert response.status_code == 200
        assert "test file" in response.text.lower()

        # Test JSON file
        response = await client.get(f"{files_server}/static/data.json")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data

        # Test CSS file
        response = await client.get(f"{files_server}/static/style.css")
        assert response.status_code == 200
        assert "body" in response.text

        # Test non-existent file
        response = await client.get(f"{files_server}/static/nonexistent.txt")
        assert response.status_code == 404

@pytest.mark.asyncio
async def test_file_upload_text(files_server):
    """Test text file upload"""
    async with httpx.AsyncClient() as client:
        # Create test file content
        file_content = "This is a test file for upload"
        file_data = {"file": ("test_upload.txt", io.BytesIO(file_content.encode()), "text/plain")}

        response = await client.post(f"{files_server}/upload", files=file_data)
        assert response.status_code == 201

        data = response.json()
        assert data["success"] is True
        assert data["filename"] == "test_upload.txt"
        assert data["size"] == len(file_content)
        assert "upload_time" in data

@pytest.mark.asyncio
async def test_file_upload_binary(files_server):
    """Test binary file upload"""
    async with httpx.AsyncClient() as client:
        # Create test binary content
        binary_content = b"\x00\x01\x02\x03\xFF\xFE\xFD"
        file_data = {"file": ("binary_test.bin", io.BytesIO(binary_content), "application/octet-stream")}

        response = await client.post(f"{files_server}/upload", files=file_data)
        assert response.status_code == 201

        data = response.json()
        assert data["success"] is True
        assert data["filename"] == "binary_test.bin"
        assert data["size"] == len(binary_content)

@pytest.mark.asyncio
async def test_file_upload_no_file(files_server):
    """Test file upload without file"""
    async with httpx.AsyncClient() as client:
        response = await client.post(f"{files_server}/upload")
        assert response.status_code == 400

        data = response.json()
        assert "error" in data
        assert "No file uploaded" in data["error"]

@pytest.mark.asyncio
async def test_file_listing(files_server):
    """Test file listing"""
    async with httpx.AsyncClient() as client:
        # First, upload a test file
        file_content = "Test file for listing"
        file_data = {"file": ("list_test.txt", io.BytesIO(file_content.encode()), "text/plain")}
        await client.post(f"{files_server}/upload", files=file_data)

        # List files
        response = await client.get(f"{files_server}/files")
        assert response.status_code == 200

        data = response.json()
        assert "files" in data
        assert "total_files" in data
        assert "upload_directory" in data
        assert data["total_files"] >= 1

        # Check if our uploaded file is in the list
        filenames = [f["filename"] for f in data["files"]]
        assert "list_test.txt" in filenames

@pytest.mark.asyncio
async def test_file_download(files_server):
    """Test file download"""
    async with httpx.AsyncClient() as client:
        # First, upload a test file
        file_content = "Content for download test"
        file_data = {"file": ("download_test.txt", io.BytesIO(file_content.encode()), "text/plain")}
        await client.post(f"{files_server}/upload", files=file_data)

        # Download the file
        response = await client.get(f"{files_server}/download/download_test.txt")
        print(f"DEBUG: Status={response.status_code}, Response={response.text}")
        assert response.status_code == 200
        assert response.text == file_content
        assert "application/octet-stream" in response.headers.get("content-type", "").lower()

@pytest.mark.asyncio
async def test_file_download_not_found(files_server):
    """Test downloading non-existent file"""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{files_server}/download/nonexistent.txt")
        assert response.status_code == 404

        data = response.json()
        assert "error" in data
        assert "File not found" in data["error"]

@pytest.mark.asyncio
async def test_file_metadata(files_server):
    """Test file metadata retrieval"""
    async with httpx.AsyncClient() as client:
        # First, upload a test file
        file_content = "Metadata test content"
        file_data = {"file": ("metadata_test.txt", io.BytesIO(file_content.encode()), "text/plain")}
        await client.post(f"{files_server}/upload", files=file_data)

        # Get file metadata
        response = await client.get(f"{files_server}/files/metadata_test.txt/info")
        assert response.status_code == 200

        data = response.json()
        assert data["filename"] == "metadata_test.txt"
        assert data["size"] == len(file_content)
        assert data["content_type"] == "text/plain"
        assert data["exists"] is True
        assert "created" in data
        assert "modified" in data

@pytest.mark.asyncio
async def test_file_metadata_not_found(files_server):
    """Test metadata for non-existent file"""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{files_server}/files/nonexistent.txt/info")
        assert response.status_code == 404

        data = response.json()
        assert "error" in data
        assert "File not found" in data["error"]

@pytest.mark.asyncio
async def test_file_deletion(files_server):
    """Test file deletion"""
    async with httpx.AsyncClient() as client:
        # First, upload a test file
        file_content = "File to be deleted"
        file_data = {"file": ("delete_test.txt", io.BytesIO(file_content.encode()), "text/plain")}
        await client.post(f"{files_server}/upload", files=file_data)

        # Verify file exists
        response = await client.get(f"{files_server}/files/delete_test.txt/info")
        assert response.status_code == 200

        # Delete the file
        response = await client.delete(f"{files_server}/files/delete_test.txt")
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True
        assert data["filename"] == "delete_test.txt"

        # Verify file is deleted
        response = await client.get(f"{files_server}/files/delete_test.txt/info")
        assert response.status_code == 404

@pytest.mark.asyncio
async def test_file_deletion_not_found(files_server):
    """Test deleting non-existent file"""
    async with httpx.AsyncClient() as client:
        response = await client.delete(f"{files_server}/files/nonexistent.txt")
        assert response.status_code == 404

        data = response.json()
        assert "error" in data
        assert "File not found" in data["error"]

@pytest.mark.asyncio
async def test_operations_tracking(files_server):
    """Test file operations tracking"""
    async with httpx.AsyncClient() as client:
        # Clear operations history first
        await client.post(f"{files_server}/operations/clear")

        # Upload a file
        file_content = "Operations tracking test"
        file_data = {"file": ("ops_test.txt", io.BytesIO(file_content.encode()), "text/plain")}
        await client.post(f"{files_server}/upload", files=file_data)

        # Download the file
        await client.get(f"{files_server}/download/ops_test.txt")

        # Delete the file
        await client.delete(f"{files_server}/files/ops_test.txt")

        # Check operations
        response = await client.get(f"{files_server}/operations")
        assert response.status_code == 200

        data = response.json()
        assert "operations" in data
        assert "total_operations" in data
        assert "operations_by_type" in data
        assert data["total_operations"] == 3
        assert data["operations_by_type"]["upload"] == 1
        assert data["operations_by_type"]["download"] == 1
        assert data["operations_by_type"]["delete"] == 1

@pytest.mark.asyncio
async def test_operations_clearing(files_server):
    """Test clearing operations history"""
    async with httpx.AsyncClient() as client:
        # Upload a file to generate operations
        file_content = "Clear test"
        file_data = {"file": ("clear_test.txt", io.BytesIO(file_content.encode()), "text/plain")}
        await client.post(f"{files_server}/upload", files=file_data)

        # Verify operations exist
        response = await client.get(f"{files_server}/operations")
        data = response.json()
        assert data["total_operations"] > 0

        # Clear operations
        response = await client.post(f"{files_server}/operations/clear")
        assert response.status_code == 200

        clear_data = response.json()
        assert clear_data["message"] == "Operations history cleared"
        assert clear_data["cleared_operations"] > 0

        # Verify operations are cleared
        response = await client.get(f"{files_server}/operations")
        data = response.json()
        assert data["total_operations"] == 0

@pytest.mark.asyncio
async def test_multiple_file_uploads(files_server):
    """Test uploading multiple files"""
    async with httpx.AsyncClient() as client:
        # Upload multiple files
        files_to_upload = [
            ("multi1.txt", "First file content"),
            ("multi2.txt", "Second file content"),
            ("multi3.txt", "Third file content")
        ]

        uploaded_files = []
        for filename, content in files_to_upload:
            file_data = {"file": (filename, io.BytesIO(content.encode()), "text/plain")}
            response = await client.post(f"{files_server}/upload", files=file_data)
            assert response.status_code == 201
            uploaded_files.append(filename)

        # List files and verify all are present
        response = await client.get(f"{files_server}/files")
        data = response.json()
        filenames = [f["filename"] for f in data["files"]]

        for filename in uploaded_files:
            assert filename in filenames

@pytest.mark.asyncio
async def test_concurrent_file_operations(files_server):
    """Test concurrent file operations"""
    async with httpx.AsyncClient() as client:
        # Upload multiple files concurrently
        async def upload_file(filename, content):
            file_data = {"file": (filename, io.BytesIO(content.encode()), "text/plain")}
            return await client.post(f"{files_server}/upload", files=file_data)

        tasks = []
        for i in range(3):
            filename = f"concurrent_{i}.txt"
            content = f"Concurrent content {i}"
            tasks.append(upload_file(filename, content))

        # Execute uploads concurrently
        responses = await asyncio.gather(*tasks)

        # All uploads should succeed
        for response in responses:
            assert response.status_code == 201
            data = response.json()
            assert data["success"] is True

@pytest.mark.asyncio
async def test_large_file_handling(files_server):
    """Test handling of larger files"""
    async with httpx.AsyncClient() as client:
        # Create a larger file (1KB)
        large_content = "A" * 1024
        file_data = {"file": ("large_test.txt", io.BytesIO(large_content.encode()), "text/plain")}

        # Upload large file
        response = await client.post(f"{files_server}/upload", files=file_data)
        assert response.status_code == 201

        data = response.json()
        assert data["success"] is True
        assert data["size"] == 1024

        # Download and verify
        response = await client.get(f"{files_server}/download/large_test.txt")
        assert response.status_code == 200
        assert len(response.text) == 1024
        assert response.text == large_content
