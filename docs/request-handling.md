# Request Handling

Catzilla provides a powerful Request object that gives you easy access to all aspects of the HTTP request.

## Request Properties

### Basic Properties

```python
@app.get("/request-info")
def request_info(request):
    return {
        "method": request.method,  # GET, POST, etc.
        "path": request.path,      # URL path
        "client_ip": request.client_ip,  # Client's IP address
        "headers": request.headers  # Request headers
    }
```

### Query Parameters

Access URL query parameters using `query_params`:

```python
@app.get("/search")
def search(request):
    query = request.query_params.get("q", "")
    page = request.query_params.get("page", "1")
    limit = request.query_params.get("limit", "10")

    return {
        "query": query,
        "page": int(page),
        "limit": int(limit)
    }
```

### Request Body

#### JSON Data

For JSON requests, use the `json()` method:

```python
@app.post("/api/data")
def handle_json(request):
    if request.content_type == "application/json":
        data = request.json()
        return {
            "received": data,
            "type": "json"
        }
    return {"error": "Expected JSON"}, 400
```

#### Form Data

For form submissions, use the `form()` method:

```python
@app.post("/submit-form")
def handle_form(request):
    if request.content_type == "application/x-www-form-urlencoded":
        form_data = request.form()
        return {
            "received": form_data,
            "type": "form"
        }
    return {"error": "Expected form data"}, 400
```

#### Raw Body

Access the raw request body using `text()`:

```python
@app.post("/raw")
def handle_raw(request):
    raw_data = request.text()
    return {
        "received": raw_data,
        "length": len(raw_data)
    }
```

### Content Type

Check the request's content type:

```python
@app.post("/content-type")
def check_content(request):
    content_type = request.content_type

    if content_type == "application/json":
        return {"type": "json", "data": request.json()}
    elif content_type == "application/x-www-form-urlencoded":
        return {"type": "form", "data": request.form()}
    else:
        return {"type": "other", "data": request.text()}
```

## Request Headers

Access request headers (case-insensitive):

```python
@app.get("/headers")
def get_headers(request):
    return {
        "user_agent": request.headers.get("user-agent"),
        "accept": request.headers.get("accept"),
        "authorization": request.headers.get("authorization"),
        "all_headers": dict(request.headers)
    }
```

## Client Information

Get client IP address and other info:

```python
@app.get("/client-info")
def client_info(request):
    return {
        "ip": request.client_ip,
        "forwarded_for": request.headers.get("x-forwarded-for"),
        "real_ip": request.headers.get("x-real-ip")
    }
```

## Best Practices

### 1. Content Type Validation

Always validate content type before processing:

```python
@app.post("/api/data")
def handle_data(request):
    if request.content_type != "application/json":
        return JSONResponse(
            {"error": "Content-Type must be application/json"},
            status_code=415  # Unsupported Media Type
        )

    try:
        data = request.json()
        # Process data...
        return {"success": True, "data": data}
    except Exception as e:
        return JSONResponse(
            {"error": "Invalid JSON"},
            status_code=400
        )
```

### 2. Query Parameter Validation

Validate and convert query parameters:

```python
@app.get("/api/items")
def get_items(request):
    try:
        page = int(request.query_params.get("page", "1"))
        limit = int(request.query_params.get("limit", "10"))

        if page < 1 or limit < 1:
            raise ValueError("Invalid page or limit")

        return {"page": page, "limit": limit}
    except ValueError:
        return JSONResponse(
            {"error": "Invalid parameters"},
            status_code=400
        )
```

### 3. Form Data Handling

Handle form data safely:

```python
@app.post("/submit")
def submit_form(request):
    if request.content_type != "application/x-www-form-urlencoded":
        return JSONResponse(
            {"error": "Expected form data"},
            status_code=415
        )

    form = request.form()
    required_fields = ["name", "email"]

    for field in required_fields:
        if field not in form:
            return JSONResponse(
                {"error": f"Missing required field: {field}"},
                status_code=400
            )

    return {"success": True, "data": form}
```

### 4. Security Considerations

- Validate input data
- Check content types
- Validate content length
- Be careful with file uploads
- Sanitize user input
- Use appropriate status codes
- Handle errors gracefully

## Error Handling

Handle common request errors:

```python
@app.post("/api/data")
def handle_data(request):
    try:
        # Validate content type
        if request.content_type != "application/json":
            return JSONResponse(
                {"error": "Expected JSON"},
                status_code=415
            )

        # Parse JSON
        data = request.json()

        # Validate required fields
        if "name" not in data:
            return JSONResponse(
                {"error": "Missing required field: name"},
                status_code=400
            )

        # Process valid request
        return {"success": True, "name": data["name"]}

    except Exception as e:
        return JSONResponse(
            {"error": "Internal server error"},
            status_code=500
        )
```
