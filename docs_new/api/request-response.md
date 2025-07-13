# 🌐 Request & Response API

Catzilla's **high-performance HTTP objects** with **C-accelerated parsing** and **zero-copy operations**. Handle requests and responses at maximum speed with minimal memory overhead.

## Request Object

```python
from catzilla import Request

class Request:
    """
    High-performance HTTP request object with C-accelerated parsing.

    Features:
    - C-accelerated header parsing
    - Zero-copy URL parameter extraction
    - Streaming body parsing
    - Memory-efficient file upload handling
    - Fast JSON/form parsing
    """
```

### Request Properties

#### Basic Properties

```python
@property
def method(self) -> str:
    """HTTP method (GET, POST, PUT, DELETE, etc.)"""

@property
def url(self) -> URL:
    """Complete request URL object"""

@property
def path(self) -> str:
    """URL path component"""

@property
def query_string(self) -> str:
    """Raw query string"""

@property
def headers(self) -> Headers:
    """HTTP headers with C-accelerated parsing"""

@property
def client(self) -> Optional[str]:
    """Client IP address"""

@property
def scheme(self) -> str:
    """URL scheme (http/https)"""

@property
def server(self) -> Tuple[str, int]:
    """Server host and port"""
```

**Example:**

```python
from catzilla import Catzilla, Request

app = Catzilla()

@app.get("/info")
def request_info(request: Request):
    """Examine request properties"""
    return {
        "method": request.method,                 # "GET"
        "path": request.path,                     # "/info"
        "query_string": request.query_string,     # "param1=value1&param2=value2"
        "client_ip": request.client,              # "192.168.1.100"
        "scheme": request.scheme,                 # "https"
        "server": request.server,                 # ("localhost", 8000)
        "headers": dict(request.headers),         # {"user-agent": "...", ...}
        "url": str(request.url)                   # "https://localhost:8000/info?param1=value1"
    }
```

### Path Parameters

```python
@property
def path_params(self) -> Dict[str, str]:
    """Path parameters extracted from URL pattern (C-accelerated)"""
```

**Example:**

```python
@app.get("/users/{user_id}/posts/{post_id}")
def get_user_post(request: Request):
    # Path parameters automatically extracted at C speed
    user_id = request.path_params["user_id"]
    post_id = request.path_params["post_id"]

    return {
        "user_id": user_id,
        "post_id": post_id,
        "all_params": request.path_params
    }

# For URL: /users/123/posts/456
# request.path_params = {"user_id": "123", "post_id": "456"}
```

### Query Parameters

```python
@property
def query_params(self) -> QueryParams:
    """Query parameters with C-accelerated parsing"""

class QueryParams:
    """C-accelerated query parameter container"""

    def get(self, key: str, default: Any = None) -> Any:
        """Get single parameter value"""

    def getlist(self, key: str) -> List[str]:
        """Get list of values for parameter"""

    def items(self) -> Iterator[Tuple[str, str]]:
        """Iterate over all parameter pairs"""

    def keys(self) -> Iterator[str]:
        """Iterate over parameter names"""

    def values(self) -> Iterator[str]:
        """Iterate over parameter values"""
```

**Example:**

```python
@app.get("/search")
def search(request: Request):
    # C-accelerated query parameter parsing
    query = request.query_params.get("q", "")
    page = int(request.query_params.get("page", "1"))
    per_page = int(request.query_params.get("per_page", "20"))

    # Handle multiple values
    tags = request.query_params.getlist("tags")  # ?tags=python&tags=web

    # Get all parameters
    all_params = dict(request.query_params.items())

    return {
        "query": query,
        "page": page,
        "per_page": per_page,
        "tags": tags,
        "all_params": all_params
    }

# For URL: /search?q=catzilla&page=2&tags=python&tags=web&per_page=10
# query_params = {
#   "q": "catzilla",
#   "page": "2",
#   "per_page": "10",
#   "tags": ["python", "web"]
# }
```

### Headers

```python
@property
def headers(self) -> Headers:
    """HTTP headers with C-accelerated parsing"""

class Headers:
    """C-accelerated header container"""

    def get(self, key: str, default: str = None) -> Optional[str]:
        """Get header value (case-insensitive)"""

    def getlist(self, key: str) -> List[str]:
        """Get list of values for header"""

    def items(self) -> Iterator[Tuple[str, str]]:
        """Iterate over header pairs"""

    def keys(self) -> Iterator[str]:
        """Iterate over header names"""

    def values(self) -> Iterator[str]:
        """Iterate over header values"""

    def __contains__(self, key: str) -> bool:
        """Check if header exists"""
```

**Example:**

```python
@app.post("/api/data")
def handle_data(request: Request):
    # C-accelerated header access
    content_type = request.headers.get("content-type", "application/json")
    user_agent = request.headers.get("user-agent")
    auth_header = request.headers.get("authorization")

    # Check for specific headers
    has_auth = "authorization" in request.headers

    # Custom headers
    api_key = request.headers.get("x-api-key")
    request_id = request.headers.get("x-request-id")

    # Multiple values (rare but possible)
    accept_encodings = request.headers.getlist("accept-encoding")

    return {
        "content_type": content_type,
        "user_agent": user_agent,
        "has_auth": has_auth,
        "api_key": api_key,
        "request_id": request_id,
        "accept_encodings": accept_encodings
    }
```

### Request Body

#### JSON Body

```python
async def json(self) -> Any:
    """Parse JSON body with C-accelerated parsing"""

# Synchronous version (if not in async context)
def json_sync(self) -> Any:
    """Parse JSON body synchronously"""
```

**Example:**

```python
from catzilla import BaseModel

class UserData(BaseModel):
    name: str
    email: str
    age: int

@app.post("/users")
async def create_user(request: Request):
    # C-accelerated JSON parsing
    user_data = await request.json()

    # Or use sync version in non-async handler
    # user_data = request.json_sync()

    # Validate with Catzilla's 100x faster validation
    user = UserData.parse_obj(user_data)

    return {"message": f"Created user {user.name}"}

# Alternative: Direct model injection (recommended)
@app.post("/users/direct")
def create_user_direct(user: UserData):
    """JSON automatically parsed and validated at C speed"""
    return {"message": f"Created user {user.name}"}
```

#### Form Data

```python
async def form(self) -> FormData:
    """Parse form data with C-accelerated parsing"""

class FormData:
    """C-accelerated form data container"""

    def get(self, key: str, default: Any = None) -> Any:
        """Get form field value"""

    def getlist(self, key: str) -> List[str]:
        """Get list of values for field"""

    def items(self) -> Iterator[Tuple[str, str]]:
        """Iterate over form field pairs"""
```

**Example:**

```python
@app.post("/contact")
async def contact_form(request: Request):
    # C-accelerated form parsing
    form_data = await request.form()

    name = form_data.get("name", "")
    email = form_data.get("email", "")
    message = form_data.get("message", "")

    # Handle multiple selections
    interests = form_data.getlist("interests")  # Multiple checkboxes

    return {
        "name": name,
        "email": email,
        "message": message,
        "interests": interests
    }
```

#### File Uploads

```python
async def files(self) -> Dict[str, UploadFile]:
    """Parse uploaded files with streaming"""

class UploadFile:
    """High-performance file upload handler"""

    @property
    def filename(self) -> Optional[str]:
        """Original filename"""

    @property
    def content_type(self) -> Optional[str]:
        """File content type"""

    @property
    def size(self) -> Optional[int]:
        """File size in bytes"""

    async def read(self, size: int = -1) -> bytes:
        """Read file content"""

    async def seek(self, offset: int) -> None:
        """Seek to position in file"""

    async def close(self) -> None:
        """Close file handle"""
```

**Example:**

```python
import os

@app.post("/upload")
async def upload_files(request: Request):
    # C-accelerated file upload parsing
    files = await request.files()

    uploaded_files = []

    for field_name, upload_file in files.items():
        if upload_file.filename:
            # Save file efficiently
            file_path = f"uploads/{upload_file.filename}"

            with open(file_path, "wb") as f:
                content = await upload_file.read()
                f.write(content)

            uploaded_files.append({
                "field_name": field_name,
                "filename": upload_file.filename,
                "content_type": upload_file.content_type,
                "size": upload_file.size,
                "saved_to": file_path
            })

    return {"uploaded_files": uploaded_files}

# Alternative: Direct file injection (recommended)
@app.post("/upload/direct")
async def upload_direct(file: UploadFile):
    """File automatically parsed from multipart form"""
    content = await file.read()

    return {
        "filename": file.filename,
        "size": len(content),
        "content_type": file.content_type
    }
```

#### Raw Body

```python
async def body(self) -> bytes:
    """Get raw request body as bytes"""

async def text(self) -> str:
    """Get request body as text"""
```

**Example:**

```python
@app.post("/webhook")
async def webhook_handler(request: Request):
    # Get raw body for custom parsing
    raw_body = await request.body()

    # Or get as text
    text_body = await request.text()

    # Custom parsing logic
    if request.headers.get("content-type") == "application/xml":
        # Parse XML
        parsed_data = parse_xml(text_body)
    else:
        # Handle other formats
        parsed_data = {"raw": text_body}

    return {"received": len(raw_body), "data": parsed_data}
```

### Request State

```python
@property
def state(self) -> RequestState:
    """Request-scoped state object for middleware and dependencies"""

class RequestState:
    """Request-scoped state container"""

    def __setattr__(self, name: str, value: Any) -> None:
        """Set state attribute"""

    def __getattr__(self, name: str) -> Any:
        """Get state attribute"""

    def __contains__(self, name: str) -> bool:
        """Check if attribute exists"""
```

**Example:**

```python
# Middleware setting request state
class AuthMiddleware:
    async def process_request(self, request: Request):
        token = request.headers.get("authorization")
        if token:
            user = decode_token(token)
            request.state.user = user
            request.state.authenticated = True
        else:
            request.state.authenticated = False

@app.get("/profile")
def get_profile(request: Request):
    # Access state set by middleware
    if request.state.authenticated:
        user = request.state.user
        return {"user": user.username, "email": user.email}
    else:
        return {"error": "Not authenticated"}, 401
```

## Response Classes

### Base Response

```python
from catzilla import Response

class Response:
    """
    High-performance HTTP response with C-accelerated serialization.

    Features:
    - C-accelerated header handling
    - Zero-copy content streaming
    - Efficient memory management
    - Fast status code handling
    """

    def __init__(
        self,
        content: Any = None,
        status_code: int = 200,
        headers: Optional[Dict[str, str]] = None,
        media_type: Optional[str] = None
    ) -> None: ...
```

**Example:**

```python
@app.get("/basic")
def basic_response():
    return Response(
        content="Hello, World!",
        status_code=200,
        headers={"X-Custom-Header": "value"},
        media_type="text/plain"
    )
```

### JSON Response

```python
from catzilla import JSONResponse

class JSONResponse(Response):
    """C-accelerated JSON response with ultra-fast serialization"""

    def __init__(
        self,
        content: Any,
        status_code: int = 200,
        headers: Optional[Dict[str, str]] = None,
        json_encoder: Optional[Callable] = None
    ) -> None: ...
```

**Example:**

```python
@app.get("/users/{user_id}")
def get_user(user_id: int):
    user_data = {
        "id": user_id,
        "name": f"User {user_id}",
        "email": f"user{user_id}@example.com",
        "metadata": {
            "created_at": "2024-01-01T00:00:00Z",
            "last_login": "2024-01-15T10:30:00Z"
        }
    }

    # C-accelerated JSON serialization
    return JSONResponse(
        content=user_data,
        status_code=200,
        headers={"Cache-Control": "max-age=300"}
    )

# Shorthand (automatically creates JSONResponse)
@app.get("/users/{user_id}/short")
def get_user_short(user_id: int):
    # Returns JSONResponse automatically
    return {"id": user_id, "name": f"User {user_id}"}
```

### HTML Response

```python
from catzilla import HTMLResponse

class HTMLResponse(Response):
    """Optimized HTML response with template support"""

    def __init__(
        self,
        content: str,
        status_code: int = 200,
        headers: Optional[Dict[str, str]] = None
    ) -> None: ...
```

**Example:**

```python
@app.get("/page")
def serve_page():
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Catzilla App</title>
    </head>
    <body>
        <h1>Welcome to Catzilla!</h1>
        <p>Ultra-fast Python web framework</p>
    </body>
    </html>
    """

    return HTMLResponse(
        content=html_content,
        headers={"Cache-Control": "public, max-age=3600"}
    )

# Template rendering (if template engine is configured)
@app.get("/template")
def serve_template(request: Request):
    return HTMLResponse(
        content=render_template("index.html", {
            "title": "Catzilla",
            "user": request.state.user
        })
    )
```

### File Response

```python
from catzilla import FileResponse

class FileResponse(Response):
    """High-performance file serving with C-accelerated streaming"""

    def __init__(
        self,
        path: str,
        status_code: int = 200,
        headers: Optional[Dict[str, str]] = None,
        media_type: Optional[str] = None,
        filename: Optional[str] = None,
        download: bool = False
    ) -> None: ...
```

**Example:**

```python
@app.get("/download/{filename}")
def download_file(filename: str):
    file_path = f"files/{filename}"

    # C-accelerated file streaming
    return FileResponse(
        path=file_path,
        media_type="application/octet-stream",
        filename=filename,
        download=True  # Force download
    )

@app.get("/images/{image_name}")
def serve_image(image_name: str):
    # Serve image with appropriate content type
    return FileResponse(
        path=f"images/{image_name}",
        media_type="image/jpeg",
        headers={"Cache-Control": "public, max-age=86400"}  # 24 hours
    )
```

### Streaming Response

```python
from catzilla import StreamingResponse

class StreamingResponse(Response):
    """C-accelerated streaming response for large content"""

    def __init__(
        self,
        content: Callable[[], Iterator[bytes]],
        status_code: int = 200,
        headers: Optional[Dict[str, str]] = None,
        media_type: Optional[str] = None
    ) -> None: ...
```

**Example:**

```python
import json
import time

@app.get("/stream/data")
def stream_data():
    def generate_data():
        # Stream large dataset
        for i in range(10000):
            data = {"id": i, "value": f"item_{i}"}
            yield f"data: {json.dumps(data)}\n".encode()

            # Simulate processing delay
            if i % 100 == 0:
                time.sleep(0.01)

    return StreamingResponse(
        content=generate_data,
        media_type="text/plain",
        headers={"X-Total-Items": "10000"}
    )

@app.get("/stream/csv")
def stream_csv():
    def generate_csv():
        # Stream CSV data
        yield b"id,name,email\n"

        for i in range(100000):
            line = f"{i},User{i},user{i}@example.com\n"
            yield line.encode()

    return StreamingResponse(
        content=generate_csv,
        media_type="text/csv",
        headers={
            "Content-Disposition": "attachment; filename=users.csv",
            "X-Total-Records": "100000"
        }
    )

# Server-Sent Events (SSE)
@app.get("/events")
def stream_events():
    def event_stream():
        event_id = 0
        while True:
            # Generate event data
            event_data = {
                "timestamp": time.time(),
                "message": f"Event {event_id}",
                "type": "notification"
            }

            # SSE format
            yield f"id: {event_id}\n".encode()
            yield f"event: notification\n".encode()
            yield f"data: {json.dumps(event_data)}\n\n".encode()

            event_id += 1
            time.sleep(1)  # 1 second intervals

    return StreamingResponse(
        content=event_stream,
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive"
        }
    )
```

### Redirect Response

```python
from catzilla import RedirectResponse

class RedirectResponse(Response):
    """HTTP redirect response"""

    def __init__(
        self,
        url: str,
        status_code: int = 307,  # Temporary redirect
        headers: Optional[Dict[str, str]] = None
    ) -> None: ...
```

**Example:**

```python
@app.get("/old-path")
def redirect_old_path():
    # Permanent redirect
    return RedirectResponse(
        url="/new-path",
        status_code=301
    )

@app.get("/login")
def login_redirect(request: Request):
    # Redirect with query parameters
    return_url = request.query_params.get("return_url", "/dashboard")

    return RedirectResponse(
        url=f"/auth/login?return_url={return_url}",
        status_code=302  # Temporary redirect
    )
```

## Advanced Features

### Custom Response Classes

```python
class XMLResponse(Response):
    """Custom XML response"""

    def __init__(
        self,
        content: str,
        status_code: int = 200,
        headers: Optional[Dict[str, str]] = None
    ):
        super().__init__(
            content=content,
            status_code=status_code,
            headers=headers,
            media_type="application/xml"
        )

@app.get("/api/data.xml")
def get_xml_data():
    xml_content = """<?xml version="1.0" encoding="UTF-8"?>
    <data>
        <item id="1">Value 1</item>
        <item id="2">Value 2</item>
    </data>"""

    return XMLResponse(content=xml_content)
```

### Response Middleware

```python
class ResponseMiddleware:
    async def process_response(self, request: Request, response: Response):
        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"

        # Add performance headers
        response.headers["X-Response-Time"] = f"{response.processing_time_ms}ms"

        return response

app.add_middleware(ResponseMiddleware)
```

### Content Negotiation

```python
@app.get("/api/data")
def get_data(request: Request):
    data = {"message": "Hello, World!", "timestamp": time.time()}

    # Content negotiation based on Accept header
    accept = request.headers.get("accept", "application/json")

    if "application/json" in accept:
        return JSONResponse(content=data)
    elif "application/xml" in accept:
        xml = f"""<?xml version="1.0"?>
        <response>
            <message>{data['message']}</message>
            <timestamp>{data['timestamp']}</timestamp>
        </response>"""
        return XMLResponse(content=xml)
    elif "text/html" in accept:
        html = f"""
        <html>
            <body>
                <h1>{data['message']}</h1>
                <p>Timestamp: {data['timestamp']}</p>
            </body>
        </html>"""
        return HTMLResponse(content=html)
    else:
        # Default to JSON
        return JSONResponse(content=data)
```

## Complete Example

```python
from catzilla import (
    Catzilla, Request, Response, JSONResponse, HTMLResponse,
    FileResponse, StreamingResponse, RedirectResponse,
    BaseModel, UploadFile
)
from typing import List, Optional
import json
import os
import time

# Create high-performance app
app = Catzilla(enable_c_acceleration=True)

# Data models
class UserProfile(BaseModel):
    username: str
    email: str
    bio: Optional[str] = None

class ApiResponse(BaseModel):
    success: bool
    data: dict
    message: str

# Request handling examples
@app.get("/")
def home_page(request: Request):
    """Serve homepage with request info"""

    # Extract client information
    client_info = {
        "ip": request.client,
        "user_agent": request.headers.get("user-agent", "Unknown"),
        "method": request.method,
        "path": request.path,
        "scheme": request.scheme
    }

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Catzilla - Ultra-Fast Python Web Framework</title>
    </head>
    <body>
        <h1>Welcome to Catzilla!</h1>
        <p>Your request information:</p>
        <ul>
            <li>IP: {client_info['ip']}</li>
            <li>User Agent: {client_info['user_agent']}</li>
            <li>Method: {client_info['method']}</li>
            <li>Path: {client_info['path']}</li>
            <li>Scheme: {client_info['scheme']}</li>
        </ul>
        <p><a href="/api/status">Check API Status</a></p>
    </body>
    </html>
    """

    return HTMLResponse(content=html_content)

@app.get("/api/status")
def api_status():
    """JSON API endpoint"""
    return JSONResponse(
        content={
            "status": "healthy",
            "version": "1.0.0",
            "features": {
                "c_acceleration": True,
                "jemalloc": True,
                "background_tasks": True
            },
            "timestamp": time.time()
        },
        headers={"X-API-Version": "1.0"}
    )

@app.post("/api/users")
async def create_user(request: Request):
    """Create user with manual JSON parsing"""
    try:
        # C-accelerated JSON parsing
        user_data = await request.json()

        # Validate with 100x faster validation
        user = UserProfile.parse_obj(user_data)

        # Simulate user creation
        user_id = hash(user.username) % 10000

        return JSONResponse(
            content={
                "success": True,
                "user_id": user_id,
                "message": f"User {user.username} created successfully"
            },
            status_code=201
        )

    except Exception as e:
        return JSONResponse(
            content={
                "success": False,
                "error": str(e),
                "message": "Failed to create user"
            },
            status_code=400
        )

@app.post("/api/users/direct")
def create_user_direct(user: UserProfile):
    """Create user with automatic validation (recommended)"""
    # user is already validated at C speed
    user_id = hash(user.username) % 10000

    return {
        "success": True,
        "user_id": user_id,
        "message": f"User {user.username} created successfully"
    }

@app.get("/search")
def search(request: Request):
    """Search with query parameters"""
    # C-accelerated query parameter parsing
    query = request.query_params.get("q", "")
    page = int(request.query_params.get("page", "1"))
    per_page = min(int(request.query_params.get("per_page", "20")), 100)

    # Simulate search results
    results = []
    for i in range(per_page):
        results.append({
            "id": (page - 1) * per_page + i,
            "title": f"Result {i + 1} for '{query}'",
            "snippet": f"This is a search result snippet for query '{query}'"
        })

    return JSONResponse(
        content={
            "query": query,
            "page": page,
            "per_page": per_page,
            "total_results": 10000,  # Simulated total
            "results": results
        },
        headers={"X-Search-Time": "2ms"}  # Simulated search time
    )

@app.post("/upload")
async def upload_file(request: Request):
    """File upload handling"""
    try:
        # C-accelerated multipart parsing
        files = await request.files()
        form_data = await request.form()

        uploaded_files = []

        for field_name, upload_file in files.items():
            if upload_file.filename:
                # Ensure upload directory exists
                os.makedirs("uploads", exist_ok=True)

                # Save file
                file_path = f"uploads/{upload_file.filename}"
                content = await upload_file.read()

                with open(file_path, "wb") as f:
                    f.write(content)

                uploaded_files.append({
                    "field_name": field_name,
                    "filename": upload_file.filename,
                    "content_type": upload_file.content_type,
                    "size": len(content),
                    "saved_to": file_path
                })

        return JSONResponse(
            content={
                "success": True,
                "message": f"Uploaded {len(uploaded_files)} files",
                "files": uploaded_files,
                "form_data": dict(form_data.items())
            }
        )

    except Exception as e:
        return JSONResponse(
            content={
                "success": False,
                "error": str(e),
                "message": "File upload failed"
            },
            status_code=400
        )

@app.get("/download/{filename}")
def download_file(filename: str):
    """File download with C-accelerated streaming"""
    file_path = f"uploads/{filename}"

    if os.path.exists(file_path):
        return FileResponse(
            path=file_path,
            filename=filename,
            download=True,
            headers={"X-Download-Source": "catzilla"}
        )
    else:
        return JSONResponse(
            content={"error": "File not found"},
            status_code=404
        )

@app.get("/stream/logs")
def stream_logs():
    """Stream server logs in real-time"""
    def log_generator():
        log_id = 0
        while True:
            # Simulate log entries
            log_entry = {
                "id": log_id,
                "timestamp": time.time(),
                "level": "INFO",
                "message": f"Server log entry {log_id}",
                "source": "catzilla"
            }

            yield f"data: {json.dumps(log_entry)}\n\n".encode()
            log_id += 1
            time.sleep(1)  # 1 second intervals

    return StreamingResponse(
        content=log_generator,
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache",
            "X-Stream-Type": "logs"
        }
    )

@app.get("/redirect-demo")
def redirect_demo():
    """Redirect demonstration"""
    return RedirectResponse(
        url="/api/status",
        status_code=302
    )

# Error handling
@app.exception_handler(404)
def not_found_handler(request: Request, exc):
    if request.headers.get("accept", "").startswith("application/json"):
        return JSONResponse(
            content={"error": "Resource not found", "path": request.path},
            status_code=404
        )
    else:
        return HTMLResponse(
            content=f"""
            <html>
                <body>
                    <h1>404 - Page Not Found</h1>
                    <p>The page '{request.path}' was not found.</p>
                    <p><a href="/">Go home</a></p>
                </body>
            </html>
            """,
            status_code=404
        )

if __name__ == "__main__":
    print("Starting Catzilla server with C-accelerated request/response handling...")
    app.listen(host="0.0.0.0", port=8000)
```

---

*Handle HTTP requests and responses at C speed with zero-copy operations!* 🌐
