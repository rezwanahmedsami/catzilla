"""
Multiple Response Types Example

This example demonstrates Catzilla's support for various response types
including JSON, HTML, plain text, and custom responses.

Features demonstrated:
- JSONResponse for API endpoints
- HTMLResponse for web pages
- Plain text responses
- Custom headers and status codes
- Response streaming preparation
"""

from catzilla import Catzilla, Request, Response, JSONResponse, HTMLResponse, Path, BaseModel
from typing import List

# Data models for auto-validation
class ProcessData(BaseModel):
    """Data processing model"""
    items: List[str]

class LoginData(BaseModel):
    """Login data model"""
    username: str

# Initialize Catzilla
app = Catzilla(
    production=False,
    show_banner=True,
    log_requests=True
)

# JSON Response (most common for APIs)
@app.get("/api/user/{user_id}")
def get_user_json(request: Request, user_id: int = Path(...)) -> JSONResponse:
    """Return user data as JSON"""
    return JSONResponse({
        "id": user_id,
        "name": f"User {user_id}",
        "email": f"user{user_id}@example.com",
        "role": "member",
        "created_at": "2025-01-14T10:00:00Z",
        "settings": {
            "theme": "dark",
            "notifications": True,
            "language": "en"
        }
    })

# HTML Response for web pages
@app.get("/user/{user_id}")
def get_user_html(request: Request, user_id: int = Path(...)) -> HTMLResponse:
    """Return user profile as HTML page"""
    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>User {user_id} Profile</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }}
            .profile {{ background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
            .header {{ color: #333; border-bottom: 2px solid #007acc; padding-bottom: 10px; }}
            .info {{ margin: 20px 0; }}
            .label {{ font-weight: bold; color: #555; }}
            .badge {{ background: #007acc; color: white; padding: 4px 8px; border-radius: 4px; font-size: 12px; }}
        </style>
    </head>
    <body>
        <div class="profile">
            <h1 class="header">User Profile</h1>
            <div class="info">
                <p><span class="label">ID:</span> {user_id}</p>
                <p><span class="label">Name:</span> User {user_id}</p>
                <p><span class="label">Email:</span> user{user_id}@example.com</p>
                <p><span class="label">Role:</span> <span class="badge">Member</span></p>
                <p><span class="label">Joined:</span> January 14, 2025</p>
            </div>
            <p><a href="/api/user/{user_id}">View JSON Data</a></p>
        </div>
    </body>
    </html>
    """

    return HTMLResponse(html_content)

# Plain text response
@app.get("/text/{message}")
def plain_text_response(request: Request, message: str = Path(...)) -> Response:
    """Return plain text response"""
    content = f"""
    Catzilla Plain Text Response
    ===========================

    Message: {message}
    Timestamp: 2025-01-14 10:00:00 UTC
    Framework: Catzilla v0.2.0
    Router: C-Accelerated

    This is a plain text response demonstrating
    Catzilla's flexibility in response types.
    """

    response = Response(
        status_code=200,
        content_type="text/plain; charset=utf-8",
        body=content.strip()
    )
    return response

# CSV Response for data export
@app.get("/export/users")
def export_users_csv(request: Request) -> Response:
    """Export users as CSV"""
    csv_content = """id,name,email,role,created_at
1,John Doe,john@example.com,admin,2025-01-01
2,Jane Smith,jane@example.com,member,2025-01-02
3,Bob Johnson,bob@example.com,member,2025-01-03
4,Alice Brown,alice@example.com,moderator,2025-01-04
5,Charlie Wilson,charlie@example.com,member,2025-01-05"""

    return Response(
        status_code=200,
        content_type="text/csv",
        body=csv_content,
        headers={"Content-Disposition": "attachment; filename=users.csv"}
    )

# JSON response with custom status code and headers
@app.post("/api/process")
def process_data(request: Request, data: ProcessData) -> JSONResponse:
    """Process data with custom response headers"""
    processed_count = len(data.items)

    return JSONResponse(
        {
            "status": "success",
            "processed_items": processed_count,
            "processing_time_ms": 42,
            "batch_id": "batch_001"
        },
        status_code=202,  # Accepted
        headers={
            "X-Processing-Time": "42ms",
            "X-Batch-ID": "batch_001",
            "X-Rate-Limit": "100",
            "X-Rate-Remaining": "95"
        }
    )

# XML Response for legacy systems
@app.get("/api/user/{user_id}/xml")
def get_user_xml(request: Request, user_id: int = Path(...)) -> Response:
    """Return user data as XML"""
    xml_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<user>
    <id>{user_id}</id>
    <name>User {user_id}</name>
    <email>user{user_id}@example.com</email>
    <role>member</role>
    <created_at>2025-01-14T10:00:00Z</created_at>
    <settings>
        <theme>dark</theme>
        <notifications>true</notifications>
        <language>en</language>
    </settings>
</user>"""

    return Response(
        status_code=200,
        content_type="application/xml; charset=utf-8",
        body=xml_content
    )

# Response with custom cookies
@app.post("/auth/login")
def login(request: Request, login_data: LoginData) -> JSONResponse:
    """Login endpoint with session cookie"""
    if login_data.username:
        response = JSONResponse({
            "status": "success",
            "message": f"Welcome back, {login_data.username}!",
            "session_id": "sess_abc123",
            "expires_in": 3600
        })

        # Add session cookie
        response.set_cookie(
            "session_id",
            "sess_abc123",
            max_age=3600,
            httponly=True,
            secure=False  # Set to True in production with HTTPS
        )

        return response
    else:
        return JSONResponse(
            {"status": "error", "message": "Username required"},
            status_code=400
        )

# Empty response (204 No Content)
@app.delete("/api/cache")
def clear_cache(request: Request) -> Response:
    """Clear cache - returns empty response"""
    # Simulate cache clearing
    return Response(status_code=204)  # No Content

# Redirect response
@app.get("/old-page")
def redirect_to_new(request: Request) -> Response:
    """Redirect to new page"""
    return Response(
        status_code=301,  # Permanent redirect
        headers={"Location": "/user/1"}
    )

if __name__ == "__main__":
    print("🎨 Starting Catzilla Response Types Example")
    print("📝 Available endpoints:")
    print("   GET  /api/user/{user_id}        - JSON response")
    print("   GET  /user/{user_id}            - HTML response")
    print("   GET  /text/{message}            - Plain text response")
    print("   GET  /export/users              - CSV response")
    print("   POST /api/process               - JSON with custom headers")
    print("   GET  /api/user/{user_id}/xml    - XML response")
    print("   POST /auth/login                - Response with cookies")
    print("   DELETE /api/cache               - Empty response (204)")
    print("   GET  /old-page                  - Redirect response")
    print("\n🎭 Multiple response types supported!")
    print("🌐 Server will start on http://localhost:8000")

    app.listen(port=8000, host="0.0.0.0")
