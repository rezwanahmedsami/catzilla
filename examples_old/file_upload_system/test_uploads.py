#!/usr/bin/env python3
"""
Simple test script for the revolutionary file upload system.
Creates test files and uploads them to demonstrate functionality.
"""

import os
import tempfile
import requests
import json
from pathlib import Path

def create_test_files():
    """Create test files for upload testing."""
    test_dir = Path("./test_files")
    test_dir.mkdir(exist_ok=True)

    # Create a simple text file
    with open(test_dir / "test.txt", "w") as f:
        f.write("This is a test file for Catzilla's revolutionary upload system!\n")
        f.write("Features:\n")
        f.write("- C-native multipart parsing (10-100x faster)\n")
        f.write("- Zero-copy streaming\n")
        f.write("- Real-time performance monitoring\n")
        f.write("- Enterprise-grade security\n")

    # Create a fake image file (for testing - not a real image)
    with open(test_dir / "fake_image.jpg", "wb") as f:
        # JPEG header
        f.write(b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01')
        f.write(b'Test image data for upload testing' * 100)
        # JPEG footer
        f.write(b'\xff\xd9')

    # Create a PDF-like file
    with open(test_dir / "document.pdf", "w") as f:
        f.write("%PDF-1.4\n")
        f.write("1 0 obj\n<< /Type /Catalog >>\nendobj\n")
        f.write("This is a fake PDF for testing upload validation.\n")
        f.write("In production, this would be a real PDF document.\n")

    print(f"✅ Created test files in {test_dir}/")
    return test_dir

def test_upload_endpoint(url, files_dict, description):
    """Test an upload endpoint with the given files."""
    print(f"\n🧪 Testing: {description}")
    print(f"📡 POST {url}")

    try:
        response = requests.post(url, files=files_dict, timeout=30)

        if response.status_code == 200:
            result = response.json()
            print("✅ Success!")
            if result.get("performance"):
                perf = result["performance"]
                print(f"   📊 Upload speed: {perf.get('upload_speed_mbps', 0):.2f} MB/s")
                print(f"   🔢 Chunks processed: {perf.get('chunks_processed', 0)}")
            if result.get("size"):
                print(f"   📁 File size: {result['size']:,} bytes")
        else:
            print(f"❌ Failed with status {response.status_code}")
            try:
                error_data = response.json()
                print(f"   Error: {error_data.get('error', 'Unknown error')}")
            except:
                print(f"   Raw response: {response.text[:200]}")

    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

def main():
    """Run upload tests."""
    print("🚀 Catzilla Revolutionary File Upload System - Test Script")
    print("=" * 60)

    # Check if server is running
    try:
        response = requests.get("http://localhost:8000/upload/stats", timeout=5)
        if response.status_code != 200:
            print("❌ Server not responding properly")
            return
    except:
        print("❌ Server not running! Please start the upload example first:")
        print("   ./scripts/run_example.sh examples/file_upload_system/main.py")
        return

    print("✅ Server is running")

    # Create test files
    test_dir = create_test_files()

    # Test single file upload
    with open(test_dir / "test.txt", "rb") as f:
        test_upload_endpoint(
            "http://localhost:8000/upload/single",
            {"file": f},
            "Single file upload"
        )

    # Test image upload
    with open(test_dir / "fake_image.jpg", "rb") as f:
        test_upload_endpoint(
            "http://localhost:8000/upload/image",
            {"image": f},
            "Image upload with validation"
        )

    # Test multiple file upload
    files_to_open = []
    try:
        profile_file = open(test_dir / "fake_image.jpg", "rb")
        doc_file = open(test_dir / "document.pdf", "rb")
        attach_file = open(test_dir / "test.txt", "rb")

        files_to_open = [profile_file, doc_file, attach_file]

        test_upload_endpoint(
            "http://localhost:8000/upload/multiple",
            {
                "profile_image": profile_file,
                "document": doc_file,
                "attachments": attach_file
            },
            "Multiple files upload"
        )
    finally:
        for f in files_to_open:
            f.close()

    # Test performance stats
    print(f"\n🧪 Testing: Performance statistics")
    print(f"📡 GET http://localhost:8000/upload/stats")
    try:
        response = requests.get("http://localhost:8000/upload/stats")
        if response.status_code == 200:
            stats = response.json()
            print("✅ Success!")
            print(f"   📊 Upload system stats available")
            print(f"   🧠 Memory optimization: {stats.get('memory_stats', {}).get('memory_optimization', 'unknown')}")
            print(f"   ⚡ C-native enabled: {stats.get('upload_system_stats', {}).get('c_native_enabled', False)}")
        else:
            print(f"❌ Failed with status {response.status_code}")
    except Exception as e:
        print(f"❌ Error: {e}")

    print(f"\n🎉 Upload testing complete!")
    print(f"🌐 Visit http://localhost:8000 for the web demo interface")
    print(f"📁 Test files created in: {test_dir}/")

if __name__ == "__main__":
    main()
