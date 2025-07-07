#!/usr/bin/env python3
"""
Test streaming with fallback mode (C streaming disabled)
"""
import sys
sys.path.insert(0, 'python')

# Monkey patch to disable C streaming for testing
import python.catzilla.streaming as streaming_module
streaming_module._HAS_C_STREAMING = False
streaming_module._catzilla_streaming = None

from catzilla import Catzilla, StreamingResponse

def test_fallback_streaming():
    """Test streaming with fallback mode"""
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

    print("Starting server with C streaming disabled...")
    print(f"C streaming enabled: {streaming_module._HAS_C_STREAMING}")

    # Test the response first
    response = StreamingResponse(lambda: ["test ", "data"], content_type="text/plain")
    print(f"Fallback response body: '{response.body}'")
    print(f"Is streaming: {response.is_streaming()}")

    try:
        app.listen(8002, "0.0.0.0")
    except Exception as e:
        print(f"Server error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_fallback_streaming()
