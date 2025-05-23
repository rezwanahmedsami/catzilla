# Response Types

Catzilla provides flexible response handling with automatic type conversion and multiple response classes.

## Express.js-style Fluent API

Catzilla provides an Express.js-inspired fluent API for building responses:

```python
from catzilla import response

# JSON response with status and headers
@app.post("/api/create")
def create(request):
    return (response
        .status(201)
        .set_header("X-API-Version", "1.0")
        .json({"created": True}))

# HTML response with cookies
@app.get("/welcome")
def welcome(request):
    return (response
        .set_cookie("session", "abc123", httponly=True)
        .html("<h1>Welcome!</h1>"))

# Plain text response
@app.get("/health")
def health(request):
    return response.send("OK")
```

### Available Methods

- `status(code: int)` - Set response status code
- `json(data: dict)` - Send JSON response
- `html(content: str)` - Send HTML response
- `send(text: str)` - Send plain text response
- `set_header(key: str, value: str)` - Set custom header
- `set_cookie(...)` - Set response cookie

All methods (except final response methods) support chaining.

## Basic Response Types

### HTMLResponse

Used for returning HTML content. You can return HTML in two ways:

```python
# 1. Direct string return (automatically converted to HTMLResponse)
@app.get("/hello")
def hello(request):
    return "<h1>Hello World</h1>"

# 2. Explicit HTMLResponse
@app.get("/hello-explicit")
def hello_explicit(request):
    return HTMLResponse(
        "<h1>Hello World</h1>",
        status_code=200,
        headers={"X-Custom": "value"}
    )
```

### JSONResponse

Used for returning JSON data. You can return JSON in two ways:

```python
# 1. Direct dict return (automatically converted to JSONResponse)
@app.get("/api/data")
def get_data(request):
    return {
        "message": "Success",
        "data": {"key": "value"}
    }

# 2. Explicit JSONResponse
@app.get("/api/data-explicit")
def get_data_explicit(request):
    return JSONResponse(
        {"message": "Success"},
        status_code=200,
        headers={"X-API-Version": "1.0"}
    )
```

### Response (Base Class)

The base Response class for custom response types:

```python
@app.get("/custom")
def custom(request):
    return Response(
        body="Custom response",
        status_code=200,
        content_type="text/plain",
        headers={"X-Custom": "value"}
    )
```

## Automatic Type Conversion

Catzilla automatically converts return values from your handlers:

| Return Type | Conversion |
|------------|------------|
| `str` | Converted to `HTMLResponse` |
| `dict` | Converted to `JSONResponse` |
| `Response` | Used as-is |
| Others | Raises `TypeError` |

Example:
```python
@app.get("/demo")
def demo(request):
    # These all work:
    if request.query_params.get("type") == "html":
        return "<h1>HTML</h1>"  # -> HTMLResponse
    elif request.query_params.get("type") == "json":
        return {"type": "json"}  # -> JSONResponse
    elif request.query_params.get("type") == "custom":
        return Response(body="custom")  # -> Used as-is
    else:
        return 123  # -> TypeError: unsupported return type
```

## Status Codes

All response types support custom status codes:

```python
# Created - 201
@app.post("/resource")
def create(request):
    return JSONResponse({"id": "new"}, status_code=201)

# Not Found - 404
@app.get("/resource/{id}")
def get(request):
    return JSONResponse(
        {"error": "Not found"},
        status_code=404
    )
```

## Headers

All response types support custom headers:

```python
@app.get("/with-headers")
def with_headers(request):
    return JSONResponse(
        {"data": "value"},
        headers={
            "X-Custom": "value",
            "Cache-Control": "no-cache",
            "X-Rate-Limit": "100"
        }
    )
```

## Content Type

Content type is automatically set based on the response type:

- `HTMLResponse`: `text/html`
- `JSONResponse`: `application/json`
- `Response`: Defaults to `text/plain` but can be customized

```python
# Custom content type
@app.get("/download")
def download(request):
    return Response(
        body="file content",
        content_type="application/octet-stream",
        headers={"Content-Disposition": "attachment; filename=data.bin"}
    )
```

## Best Practices

1. Use automatic conversion for simple responses
2. Use explicit response classes when you need custom headers or status codes
3. Set appropriate status codes for different scenarios
4. Include relevant headers for caching, security, etc.
5. Use proper content types for different response data

## Error Handling

When returning error responses, include appropriate status codes and error details:

```python
@app.get("/api/resource")
def get_resource(request):
    try:
        # ... resource fetching logic ...
        return {"data": "value"}
    except ResourceNotFound:
        return JSONResponse(
            {"error": "Resource not found"},
            status_code=404
        )
    except UnauthorizedAccess:
        return JSONResponse(
            {"error": "Unauthorized"},
            status_code=401
        )
```
