#!/usr/bin/env python3
"""
Debug script to test streaming functionality step by step
"""
import sys
sys.path.insert(0, 'python')

from catzilla import Catzilla, StreamingResponse

def test_streaming_detection():
    """Test if streaming is properly detected"""
    from python.catzilla.streaming import _HAS_C_STREAMING, _catzilla_streaming
    print(f"C streaming available: {_HAS_C_STREAMING}")
    print(f"C streaming module: {_catzilla_streaming}")
    return _HAS_C_STREAMING

def test_streaming_response():
    """Test StreamingResponse creation"""
    def simple_generator():
        for i in range(3):
            yield f"Data {i}\n"

    response = StreamingResponse(simple_generator(), content_type="text/plain")
    print(f"StreamingResponse created")
    print(f"Is streaming: {response.is_streaming()}")
    print(f"Body preview: {response.body[:50]}")
    return response

def test_simple_server():
    """Test with a very simple server"""
    app = Catzilla()

    @app.get("/test")
    def simple_test(request):
        return "Simple test works"

    @app.get("/stream")
    def stream_test(request):
        def gen():
            yield "Hello "
            yield "streaming "
            yield "world!"
        return StreamingResponse(gen(), content_type="text/plain")

    print("Starting simple server...")
    try:
        app.listen(8002, "0.0.0.0")
    except Exception as e:
        print(f"Server error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("=== Streaming Debug Test ===")

    print("\n1. Testing streaming detection...")
    has_streaming = test_streaming_detection()

    print("\n2. Testing StreamingResponse...")
    response = test_streaming_response()

    print("\n3. Testing simple server...")
    test_simple_server()
