#!/usr/bin/env python3
"""Test multipart form data validation with C-level parsing - simple version"""

from catzilla import Catzilla, Request, Response

app = Catzilla()

@app.post("/form-test")
def test_multipart_form(request: Request) -> Response:
    """Test endpoint for multipart form data"""
    print(f"📨 Request method: {request.method}")
    print(f"📋 Content-Type: {request.headers.get('content-type', 'Not set')}")

    # Test the C-level multipart parsing
    try:
        from catzilla._catzilla import parse_multipart

        content_type = request.headers.get('content-type', '')
        body = request.body if hasattr(request, 'body') else b''

        if 'multipart/form-data' in content_type:
            print(f"🔍 Attempting C-level multipart parsing...")
            print(f"   Content-Type: {content_type}")
            print(f"   Body length: {len(body)}")

            # Try the C multipart parser
            result = parse_multipart(body, content_type)
            print(f"✅ C-level parsing result: {result}")

            return Response(
                content=f"Multipart parsing successful: {result}",
                content_type="text/plain"
            )
        else:
            return Response(
                content=f"Not multipart data. Content-Type: {content_type}",
                content_type="text/plain"
            )

    except Exception as e:
        print(f"❌ Error in multipart parsing: {e}")
        return Response(
            content=f"Error: {str(e)}",
            content_type="text/plain",
            status_code=500
        )

if __name__ == "__main__":
    print("🚀 Starting Catzilla multipart test server...")
    print("📝 Test with:")
    print("   curl -X POST -F 'name=John Doe' -F 'age=25' http://localhost:8000/form-test")

    app.run(host="0.0.0.0", port=8000)
