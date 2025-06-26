#!/usr/bin/env python3
"""
Simple test for mount_static functionality
"""

from catzilla import Catzilla

app = Catzilla(show_banner=True, log_requests=True)

# Simple static mount
app.mount_static("/test", "./examples/static_file_server/static")

@app.get("/")
def home(request):
    return {"message": "Server is running", "static_test": "Try /test/app.js"}

if __name__ == "__main__":
    print("🧪 Testing static file serving...")
    app.listen(8001)
