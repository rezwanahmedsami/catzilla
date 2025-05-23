# Catzilla Examples

This guide provides practical examples of common use cases with Catzilla.

## Basic Examples

### Hello World

```python
from catzilla import App

app = App()

@app.get("/")
def hello(request):
    return "<h1>Hello, World!</h1>"

if __name__ == "__main__":
    app.listen(8080)
```

### JSON API

```python
from catzilla import App, JSONResponse

app = App()

@app.get("/api/users")
def list_users(request):
    users = [
        {"id": 1, "name": "Alice"},
        {"id": 2, "name": "Bob"}
    ]
    return {"users": users}

@app.get("/api/users/{id}")
def get_user(request):
    user_id = request.query_params.get("id")
    return {
        "id": user_id,
        "name": f"User {user_id}"
    }

if __name__ == "__main__":
    app.listen(8080)
```

## Form Handling

### Simple Form

```python
from catzilla import App, HTMLResponse

app = App()

@app.get("/form")
def show_form(request):
    return HTMLResponse("""
        <!DOCTYPE html>
        <html>
            <head>
                <title>Contact Form</title>
                <style>
                    body { font-family: Arial; margin: 40px; }
                    form { max-width: 400px; }
                    input, textarea { width: 100%; margin: 8px 0; }
                </style>
            </head>
            <body>
                <h1>Contact Us</h1>
                <form method="POST" action="/submit">
                    <div>
                        <label>Name:</label>
                        <input type="text" name="name" required>
                    </div>
                    <div>
                        <label>Email:</label>
                        <input type="email" name="email" required>
                    </div>
                    <div>
                        <label>Message:</label>
                        <textarea name="message" rows="4" required></textarea>
                    </div>
                    <button type="submit">Send</button>
                </form>
            </body>
        </html>
    """)

@app.post("/submit")
def handle_form(request):
    form = request.form()
    name = form.get("name", "")
    email = form.get("email", "")
    message = form.get("message", "")

    return HTMLResponse(f"""
        <h1>Thank You!</h1>
        <p>We received your message:</p>
        <ul>
            <li>Name: {name}</li>
            <li>Email: {email}</li>
            <li>Message: {message}</li>
        </ul>
        <p><a href="/form">Back to form</a></p>
    """)

if __name__ == "__main__":
    app.listen(8080)
```

## Cookie Management

### Session Example

```python
from catzilla import App, JSONResponse
import uuid

app = App()

# Simulate session storage
sessions = {}

@app.post("/login")
def login(request):
    data = request.json()
    username = data.get("username")
    password = data.get("password")

    # Simple authentication (demo only)
    if username == "demo" and password == "password":
        # Create session
        session_id = str(uuid.uuid4())
        sessions[session_id] = {"username": username}

        response = JSONResponse({
            "message": "Login successful",
            "username": username
        })

        # Set session cookie
        response.set_cookie(
            "session_id",
            session_id,
            httponly=True,
            max_age=3600
        )

        return response

    return JSONResponse(
        {"error": "Invalid credentials"},
        status_code=401
    )

@app.get("/profile")
def profile(request):
    # Get session ID from cookie
    session_id = request.headers.get("cookie", "").split("session_id=")[-1].split(";")[0]
    session = sessions.get(session_id)

    if not session:
        return JSONResponse(
            {"error": "Not authenticated"},
            status_code=401
        )

    return {
        "username": session["username"],
        "profile": "User profile data"
    }

@app.post("/logout")
def logout(request):
    response = JSONResponse({"message": "Logged out"})
    response.set_cookie(
        "session_id",
        "",
        max_age=0
    )
    return response

if __name__ == "__main__":
    app.listen(8080)
```

## Error Handling

### API Error Handling

```python
from catzilla import App, JSONResponse

app = App()

class NotFoundError(Exception):
    pass

class ValidationError(Exception):
    pass

# Simulated database
items = {
    "1": {"name": "Item 1", "price": 10.99},
    "2": {"name": "Item 2", "price": 20.99}
}

@app.get("/api/items/{id}")
def get_item(request):
    try:
        item_id = request.query_params.get("id")

        if not item_id:
            raise ValidationError("Item ID is required")

        item = items.get(item_id)
        if not item:
            raise NotFoundError(f"Item {item_id} not found")

        return {"item": item}

    except ValidationError as e:
        return JSONResponse(
            {"error": str(e)},
            status_code=400
        )
    except NotFoundError as e:
        return JSONResponse(
            {"error": str(e)},
            status_code=404
        )
    except Exception as e:
        return JSONResponse(
            {"error": "Internal server error"},
            status_code=500
        )

if __name__ == "__main__":
    app.listen(8080)
```

## Custom Headers

### CORS Example

```python
from catzilla import App, JSONResponse

app = App()

def cors_headers():
    return {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type"
    }

@app.options("/api/data")
def handle_options(request):
    return JSONResponse(
        {},
        headers=cors_headers()
    )

@app.get("/api/data")
def get_data(request):
    return JSONResponse(
        {"message": "This is CORS-enabled data"},
        headers=cors_headers()
    )

@app.post("/api/data")
def post_data(request):
    data = request.json()
    return JSONResponse(
        {"received": data},
        headers=cors_headers()
    )

if __name__ == "__main__":
    app.listen(8080)
```

## File Upload (Coming Soon)

```python
from catzilla import App, JSONResponse

app = App()

@app.get("/upload")
def upload_form(request):
    return """
        <form method="POST" action="/upload" enctype="multipart/form-data">
            <input type="file" name="file">
            <button type="submit">Upload</button>
        </form>
    """

@app.post("/upload")
def handle_upload(request):
    # File upload handling coming in future release
    return {"message": "Upload successful"}

if __name__ == "__main__":
    app.listen(8080)
```

## API Documentation Example

```python
from catzilla import App, HTMLResponse
import json

app = App()

# API Documentation
API_DOCS = {
    "openapi": "3.0.0",
    "info": {
        "title": "Sample API",
        "version": "1.0.0"
    },
    "paths": {
        "/api/items": {
            "get": {
                "summary": "List items",
                "responses": {
                    "200": {
                        "description": "Successful response",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "items": {
                                            "type": "array",
                                            "items": {
                                                "type": "object",
                                                "properties": {
                                                    "id": {"type": "string"},
                                                    "name": {"type": "string"}
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }
}

@app.get("/api-docs")
def api_docs(request):
    return HTMLResponse("""
        <!DOCTYPE html>
        <html>
            <head>
                <title>API Documentation</title>
                <script src="https://unpkg.com/swagger-ui-dist@latest/swagger-ui-bundle.js"></script>
                <link rel="stylesheet" href="https://unpkg.com/swagger-ui-dist@latest/swagger-ui.css">
            </head>
            <body>
                <div id="swagger-ui"></div>
                <script>
                    window.onload = () => {
                        SwaggerUIBundle({
                            spec: %s,
                            dom_id: '#swagger-ui'
                        });
                    };
                </script>
            </body>
        </html>
    """ % json.dumps(API_DOCS))

if __name__ == "__main__":
    app.listen(8080)
```

## Testing Example

```python
# test_app.py
import pytest
from catzilla import App, Request

def test_hello_endpoint():
    app = App()

    @app.get("/hello")
    def hello(request):
        return {"message": "Hello, World!"}

    # Create test request
    request = Request(
        method="GET",
        path="/hello",
        body="",
        client=None,
        request_capsule=None
    )

    # Get response
    response = hello(request)

    # Assert response
    assert response == {"message": "Hello, World!"}

def test_echo_endpoint():
    app = App()

    @app.post("/echo")
    def echo(request):
        return request.json()

    # Create test request with JSON body
    request = Request(
        method="POST",
        path="/echo",
        body='{"test": "data"}',
        client=None,
        request_capsule=None,
        headers={"content-type": "application/json"}
    )

    # Get response
    response = echo(request)

    # Assert response
    assert response == {"test": "data"}
```
