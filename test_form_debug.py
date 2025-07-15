#!/usr/bin/env python3
"""Simple test server to debug form data flow"""

from catzilla import Catzilla, Request, Response

app = Catzilla()

@app.post("/debug-form")
def debug_form(request: Request) -> Response:
    """Debug form data parsing"""
    print(f"📨 Method: {request.method}")
    print(f"📋 Content-Type: {request.headers.get('content-type', 'Not set')}")
    print(f"📊 Body type: {type(request.body)}")
    print(f"📏 Body length: {len(request.body) if request.body else 0}")

    # Try to access form data
    try:
        form_data = request.form()  # Call the method
        print(f"✅ Form data: {form_data}")
        print(f"🔢 Form field count: {len(form_data)}")
        for key, value in form_data.items():
            print(f"   {key} = {value}")
    except Exception as e:
        print(f"❌ Form parsing error: {e}")
        import traceback
        traceback.print_exc()

    # Also check files to see what we get
    try:
        files_data = request.files()
        print(f"📁 Files data: {files_data}")
        print(f"📂 Files type: {type(files_data)}")
        if isinstance(files_data, dict):
            for key, value in files_data.items():
                print(f"   File {key}: {value}")
                if isinstance(value, dict):
                    for k, v in value.items():
                        print(f"     {k}: {v} (type: {type(v)})")
    except Exception as e:
        print(f"❌ Files access error: {e}")
        import traceback
        traceback.print_exc()

    # Also try direct C function access
    try:
        from catzilla._catzilla import get_form_field
        print(f"🔍 Direct C form field access:")
        for field_name in ['name', 'email', 'age']:
            value = get_form_field(request.request_capsule, field_name)
            print(f"   {field_name} = {value}")
    except Exception as e:
        print(f"❌ Direct C access error: {e}")

    return Response(body="Form debug complete", content_type="text/plain")

if __name__ == "__main__":
    print("🚀 Starting form debug server...")
    print("📝 Test with:")
    print("   curl -X POST -F 'name=John' -F 'email=john@test.com' http://localhost:8001/debug-form")
    app.listen(host="0.0.0.0", port=8001)
