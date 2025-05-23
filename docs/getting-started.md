# Getting Started with Catzilla

This guide will help you get started with Catzilla, a high-performance Python web framework with a C core.

## Installation

```bash
pip install catzilla
```

## Quick Start

Create a new file `app.py`:

```python
from catzilla import App, response

app = App()

@app.get("/")
def home(request):
    return response.html("<h1>Hello, Catzilla!</h1>")

if __name__ == "__main__":
    app.listen(8080)
```

Run your application:

```bash
python app.py
```

Visit `http://localhost:8080` in your browser to see your first Catzilla app!

## Basic Examples

### 1. JSON API with Fluent Response

```python
from catzilla import App, response

app = App()

@app.get("/api/hello")
def hello_api(request):
    name = request.query_params.get("name", "World")
    return (response
        .status(200)
        .set_header("X-API-Version", "1.0")
        .json({
            "message": f"Hello, {name}!",
            "timestamp": "2024-03-21T12:00:00Z"
        }))

@app.post("/api/echo")
def echo(request):
    return (response
        .status(200)
        .json({
            "received": request.json(),
            "headers": dict(request.headers)
        }))

if __name__ == "__main__":
    app.listen(8080)
```

### 2. HTML Pages with Cookies

```python
from catzilla import App, response

app = App()

@app.get("/")
def home(request):
    return (response
        .set_cookie("visited", "true", max_age=3600)
        .html("""
            <!DOCTYPE html>
            <html>
                <head>
                    <title>Catzilla Demo</title>
                    <style>
                        body { font-family: Arial; margin: 40px; }
                    </style>
                </head>
                <body>
                    <h1>Welcome to Catzilla</h1>
                    <p>A high-performance Python web framework.</p>
                </body>
            </html>
        """))

if __name__ == "__main__":
    app.listen(8080)
```

### 3. Form Handling with Status Codes

```python
from catzilla import App, response

app = App()

@app.get("/form")
def show_form(request):
    return response.html("""
        <form method="POST" action="/submit">
            <input type="text" name="message">
            <button type="submit">Send</button>
        </form>
    """)

@app.post("/submit")
def handle_form(request):
    form_data = request.form()
    message = form_data.get("message", "")
    if not message:
        return (response
            .status(400)
            .json({"error": "Message is required"}))

    return (response
        .status(201)
        .set_header("X-Custom", "value")
        .html(f"<h1>Received: {message}</h1>"))

if __name__ == "__main__":
    app.listen(8080)
```

## Core Features

### 1. Route Decorators

```python
@app.get("/path")      # Handle GET requests
@app.post("/path")     # Handle POST requests
@app.put("/path")      # Handle PUT requests
@app.delete("/path")   # Handle DELETE requests
@app.patch("/path")    # Handle PATCH requests
```

### 2. Request Object

```python
request.method          # HTTP method
request.path           # URL path
request.query_params   # Query parameters
request.headers        # Request headers
request.content_type   # Content type
request.client_ip      # Client IP address
request.json()         # Parse JSON body
request.form()         # Parse form data
request.text()         # Raw body text
```

### 3. Response Building (Express.js Style)

```python
# HTML Response
return response.html("<h1>Hello</h1>")

# JSON Response with status
return response.status(201).json({"key": "value"})

# Response with headers and cookies
return (response
    .status(200)
    .set_header("X-Custom", "value")
    .set_cookie("session", "abc123", httponly=True)
    .json({"data": "value"}))

# Plain text response
return response.send("Custom content")
```

## Project Structure

Recommended project structure:

```
myapp/
├── app.py              # Main application file
├── routes/
│   ├── __init__.py
│   ├── api.py         # API routes
│   └── views.py       # View routes
├── templates/         # HTML templates
├── static/           # Static files
└── requirements.txt  # Dependencies
```

Example `app.py`:

```python
from catzilla import App
from routes.api import api_routes
from routes.views import view_routes

app = App()

# Register routes
api_routes(app)
view_routes(app)

if __name__ == "__main__":
    app.listen(8080)
```

## Next Steps

1. Read the [Core Concepts](./core-concepts.md) guide
2. Explore [Response Types](./response-types.md)
3. Learn about [Request Handling](./request-handling.md)
4. Check out [Cookies and Headers](./cookies-and-headers.md)
5. See more [Examples](./examples.md)

## Common Issues

### 1. Import Errors

If you see import errors, make sure:
- Catzilla is installed (`pip install catzilla`)
- You're using the correct import statements
- Your Python environment is activated

### 2. Port In Use

If port 8080 is in use:
```python
if __name__ == "__main__":
    app.listen(3000)  # Use a different port
```

### 3. Content Type Issues

Always set the correct content type:
```python
# For JSON APIs
return JSONResponse(data, headers={"Content-Type": "application/json"})

# For HTML pages
return HTMLResponse(html, headers={"Content-Type": "text/html"})
```

## Getting Help

- Check the [documentation](./README.md)
- Look at the [examples](./examples.md)
- Report issues on GitHub
- Join the community chat
