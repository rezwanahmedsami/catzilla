#!/usr/bin/env python3
"""
Test the complete Catzilla banner and logging system with psutil.
"""

import sys
import os

# Add the python directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'python'))

from catzilla import Catzilla

def test_banner_with_psutil():
    """Test the complete banner system with psutil"""
    print("=== Testing Catzilla Banner with psutil ===\n")

    # Create app with banner enabled (use production=False instead of debug=True)
    app = Catzilla(production=False, show_banner=True)

    @app.route("/test")
    def test_handler():
        return {"message": "Hello, World!"}

    @app.route("/users/{user_id}")
    def get_user(user_id: int):
        return {"user_id": user_id}

    @app.post("/data")
    def post_data():
        return {"status": "created"}

    print("Routes registered. Starting server to show banner...")

    # This will show the banner with psutil-powered system info
    try:
        app.listen("127.0.0.1", 8000)
    except KeyboardInterrupt:
        print("\nServer stopped by user")
    except Exception as e:
        print(f"\nServer test completed (expected): {e}")

if __name__ == "__main__":
    test_banner_with_psutil()
