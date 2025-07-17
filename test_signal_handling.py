#!/usr/bin/env python3
"""
Test script to verify signal handling works correctly
"""

import sys
import os
import time
import signal
import subprocess

def test_signal_handling():
    """Test that Catzilla handles SIGINT gracefully"""
    print("🧪 Testing Catzilla signal handling...")

    # Start the server
    print("📡 Starting server...")
    proc = subprocess.Popen([
        sys.executable, "examples/middleware/basic_middleware.py"
    ], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)

    # Wait for server to start
    time.sleep(3)

    # Test that server is running
    result = subprocess.run([
        "curl", "-s", "-I", "http://localhost:8000/"
    ], capture_output=True, text=True)

    if result.returncode == 0:
        print("✅ Server is running and responding")
    else:
        print("❌ Server failed to start")
        proc.terminate()
        return False

    # Send SIGINT signal
    print("🔄 Sending SIGINT signal...")
    proc.send_signal(signal.SIGINT)

    # Wait for graceful shutdown
    try:
        stdout, _ = proc.communicate(timeout=5)
        print("📜 Server output:")
        print(stdout)
    except subprocess.TimeoutExpired:
        print("⚠️  Server didn't shut down within 5 seconds, forcing termination")
        proc.kill()
        stdout, _ = proc.communicate()
        print("📜 Server output:")
        print(stdout)
        return False

    # Verify server stopped
    result = subprocess.run([
        "curl", "-s", "-I", "http://localhost:8000/"
    ], capture_output=True, text=True)

    if result.returncode != 0:
        print("✅ Server stopped successfully")
        return True
    else:
        print("❌ Server is still running")
        return False

if __name__ == "__main__":
    success = test_signal_handling()
    if success:
        print("\n🎉 Signal handling test PASSED!")
        sys.exit(0)
    else:
        print("\n💥 Signal handling test FAILED!")
        sys.exit(1)
