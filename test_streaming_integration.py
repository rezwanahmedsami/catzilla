#!/usr/bin/env python3
"""
Simple streaming test script to validate the C extension integration.
"""

import sys
import time

# Add the project root to the path
sys.path.insert(0, 'python')

from catzilla import StreamingResponse
from catzilla.streaming import _HAS_C_STREAMING, _catzilla_streaming

def main():
    print("=== Catzilla Streaming Test ===")
    print(f"C streaming available: {_HAS_C_STREAMING}")

    if _HAS_C_STREAMING:
        print(f"C streaming module: {_catzilla_streaming}")
        print("Available functions:", [attr for attr in dir(_catzilla_streaming) if not attr.startswith('_')])

    print("\n=== Testing StreamingResponse ===")

    def test_generator():
        for i in range(3):
            yield f"Test chunk {i}\n"
            time.sleep(0.1)

    response = StreamingResponse(test_generator(), content_type='text/plain')

    print(f"Response created:")
    print(f"  - Is streaming: {response.is_streaming()}")
    print(f"  - Streaming ID: {getattr(response, '_streaming_id', 'None')}")
    print(f"  - Body preview: {response.body[:50]}...")
    print(f"  - Content type: {response.content_type}")
    print(f"  - Status code: {response.status_code}")

    print("\n=== Streaming Response Registry ===")
    from catzilla.streaming import _streaming_responses
    print(f"Registered responses: {len(_streaming_responses)}")

    if response._streaming_id:
        from catzilla.streaming import _get_streaming_response
        retrieved = _get_streaming_response(response._streaming_id)
        print(f"Registry lookup works: {retrieved is response}")

    print("\n✅ Basic streaming setup is working!")

    # Test what happens when we simulate server interaction
    if _HAS_C_STREAMING:
        print("\n=== Testing C Extension Functions ===")
        try:
            # Test function access
            connect_func = _catzilla_streaming.connect_streaming_response
            create_func = _catzilla_streaming.create_streaming_response
            print("✓ C extension functions are accessible")
            print(f"  - connect_streaming_response: {connect_func}")
            print(f"  - create_streaming_response: {create_func}")
        except Exception as e:
            print(f"✗ Error accessing C extension functions: {e}")

    print("\n=== Test Complete ===")

if __name__ == "__main__":
    main()
