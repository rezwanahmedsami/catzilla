#!/usr/bin/env python3
"""Debug multipart parsing"""

# Create a simple multipart body manually
boundary = "----WebKitFormBoundary7MA4YWxkTrZu0gW"
content_type = f"multipart/form-data; boundary={boundary}"

body = f"""------WebKitFormBoundary7MA4YWxkTrZu0gW\r
Content-Disposition: form-data; name="name"\r
\r
John Doe\r
------WebKitFormBoundary7MA4YWxkTrZu0gW\r
Content-Disposition: form-data; name="email"\r
\r
john@example.com\r
------WebKitFormBoundary7MA4YWxkTrZu0gW--\r
"""

try:
    from catzilla._catzilla import multipart_parse
    print(f"Content-Type: {content_type}")
    print(f"Body length: {len(body.encode())}")
    print(f"Body:\n{repr(body.encode())}")

    result = multipart_parse(None, content_type, body.encode())
    print(f"Parsing result: {result}")
    print(f"Result type: {type(result)}")

except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
