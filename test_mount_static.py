#!/usr/bin/env python3
"""
Test script for the new app.mount_static() functionality
"""

import os
import tempfile
from pathlib import Path

# Add the python directory to the path
import sys
sys.path.insert(0, 'python')

from catzilla import Catzilla

def test_mount_static():
    """Test the mount_static functionality"""

    # Create a temporary directory and test files
    with tempfile.TemporaryDirectory() as temp_dir:
        static_dir = Path(temp_dir) / "static"
        static_dir.mkdir()

        # Create a test HTML file
        test_html = static_dir / "index.html"
        test_html.write_text("""
<!DOCTYPE html>
<html>
<head>
    <title>Test Static File</title>
</head>
<body>
    <h1>Hello from Catzilla Static Server!</h1>
    <p>This file is served by the C-native static file server.</p>
</body>
</html>
        """.strip())

        # Create a test CSS file
        test_css = static_dir / "style.css"
        test_css.write_text("""
body {
    font-family: Arial, sans-serif;
    background-color: #f0f0f0;
    margin: 0;
    padding: 20px;
}

h1 {
    color: #333;
    text-align: center;
}
        """.strip())

        # Create a test JSON file
        test_json = static_dir / "data.json"
        test_json.write_text('{"message": "Hello from JSON!", "timestamp": "2025-01-01T00:00:00Z"}')

        print(f"✅ Created test files in: {static_dir}")
        print(f"   - {test_html}")
        print(f"   - {test_css}")
        print(f"   - {test_json}")

        # Create Catzilla app
        app = Catzilla(show_banner=False, log_requests=True)

        print("\n🔧 Testing mount_static functionality...")

        try:
            # Test basic mounting
            app.mount_static("/static", str(static_dir))
            print("✅ Basic mount successful: /static -> " + str(static_dir))

            # Test mounting with custom options
            app.mount_static(
                "/assets",
                str(static_dir),
                enable_hot_cache=True,
                cache_size_mb=50,
                enable_compression=True,
                compression_level=9,
                enable_etags=True,
                enable_range_requests=True
            )
            print("✅ Advanced mount successful: /assets -> " + str(static_dir))

            # Test mounting with security options
            app.mount_static(
                "/secure",
                str(static_dir),
                enable_directory_listing=False,
                enable_hidden_files=False,
                max_file_size=10 * 1024 * 1024  # 10MB
            )
            print("✅ Secure mount successful: /secure -> " + str(static_dir))

        except Exception as e:
            print(f"❌ Error during mounting: {e}")
            return False

        print("\n🎯 Testing parameter validation...")

        # Test invalid mount paths
        try:
            app.mount_static("invalid", str(static_dir))
            print("❌ Should have failed for invalid mount path")
            return False
        except ValueError as e:
            print(f"✅ Correctly rejected invalid mount path: {e}")

        # Test non-existent directory
        try:
            app.mount_static("/test", "/nonexistent/directory")
            print("❌ Should have failed for non-existent directory")
            return False
        except OSError as e:
            print(f"✅ Correctly rejected non-existent directory: {e}")

        # Test invalid parameters
        try:
            app.mount_static("/test", str(static_dir), cache_size_mb=-1)
            print("❌ Should have failed for invalid cache size")
            return False
        except ValueError as e:
            print(f"✅ Correctly rejected invalid cache size: {e}")

        print("\n🚀 All tests passed! mount_static is working correctly.")
        return True

if __name__ == "__main__":
    print("🐱 Testing Catzilla mount_static functionality\n")

    success = test_mount_static()

    if success:
        print("\n✅ SUCCESS: mount_static implementation is complete and working!")
        print("\n📖 Usage Examples:")
        print("```python")
        print("from catzilla import Catzilla")
        print("")
        print("app = Catzilla()")
        print("")
        print("# Basic static file serving")
        print("app.mount_static('/static', './static')")
        print("")
        print("# High-performance media serving")
        print("app.mount_static('/media', './uploads',")
        print("                 cache_size_mb=500,")
        print("                 enable_range_requests=True)")
        print("")
        print("# CDN-style serving with aggressive caching")
        print("app.mount_static('/cdn', './dist',")
        print("                 cache_ttl_seconds=86400,  # 24 hours")
        print("                 enable_compression=True,")
        print("                 compression_level=9)")
        print("")
        print("app.listen(8000)")
        print("```")
    else:
        print("\n❌ FAILURE: There were issues with the mount_static implementation.")
        sys.exit(1)
