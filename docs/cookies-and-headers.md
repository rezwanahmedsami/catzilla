# Cookies and Headers

Catzilla provides comprehensive support for managing cookies and HTTP headers.

## Cookie Management

### Setting Cookies

Use the `set_cookie()` method on any response object to set cookies:

```python
@app.get("/set-cookie")
def set_cookie(request):
    response = JSONResponse({"message": "Cookie set"})

    # Basic cookie
    response.set_cookie("user_id", "123")

    # Cookie with options
    response.set_cookie(
        name="session",
        value="abc123",
        max_age=3600,  # 1 hour
        path="/",
        domain=None,  # current domain
        secure=True,  # HTTPS only
        httponly=True,  # Not accessible via JavaScript
        samesite="Lax"
    )

    return response
```

### Cookie Options

| Option | Description | Default |
|--------|-------------|---------|
| `name` | Cookie name | Required |
| `value` | Cookie value | Required |
| `max_age` | Lifetime in seconds | None |
| `expires` | Expiration date string | None |
| `path` | Cookie path | "/" |
| `domain` | Cookie domain | None |
| `secure` | HTTPS only | False |
| `httponly` | Block JavaScript access | False |
| `samesite` | SameSite policy | None |

### Cookie Examples

```python
@app.get("/cookie-examples")
def cookie_examples(request):
    response = JSONResponse({"status": "ok"})

    # Session cookie (expires when browser closes)
    response.set_cookie("session", "temp123")

    # Persistent cookie (1 day)
    response.set_cookie(
        "persistent",
        "value123",
        max_age=86400
    )

    # Secure cookie for sensitive data
    response.set_cookie(
        "auth",
        "secret123",
        secure=True,
        httponly=True,
        samesite="Strict"
    )

    # Path-specific cookie
    response.set_cookie(
        "api_token",
        "token123",
        path="/api"
    )

    return response
```

## Header Management

### Setting Headers

Headers can be set in two ways:

1. During response creation:
```python
@app.get("/with-headers")
def with_headers(request):
    return JSONResponse(
        {"data": "value"},
        headers={
            "X-Custom": "value",
            "Cache-Control": "no-cache"
        }
    )
```

2. Using `set_header()` method:
```python
@app.get("/set-headers")
def set_headers(request):
    response = JSONResponse({"data": "value"})
    response.set_header("X-Custom", "value")
    response.set_header("Cache-Control", "no-cache")
    return response
```

### Common Headers

Examples of commonly used headers:

```python
@app.get("/common-headers")
def common_headers(request):
    return JSONResponse(
        {"data": "value"},
        headers={
            # Cache control
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0",

            # CORS
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, OPTIONS",

            # Security
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",

            # Custom headers
            "X-API-Version": "1.0",
            "X-Request-ID": "unique-id-123"
        }
    )
```

### Header Normalization

Headers are automatically normalized:
- Keys are converted to lowercase
- Leading/trailing whitespace is stripped
- Multiple Set-Cookie headers are handled properly

```python
response = Response()
response.set_header("CONTENT-TYPE", "text/plain")  # normalized to "content-type"
response.set_header(" X-Custom ", "value")  # normalized to "x-custom"
```

### Reading Request Headers

Access request headers through the `headers` dictionary:

```python
@app.get("/echo-headers")
def echo_headers(request):
    user_agent = request.headers.get("user-agent", "Unknown")
    content_type = request.headers.get("content-type")

    return {
        "user_agent": user_agent,
        "content_type": content_type,
        "all_headers": request.headers
    }
```

## Best Practices

### Cookies
1. Use `httponly` for sensitive cookies
2. Set appropriate expiration times
3. Use `secure` flag in production
4. Consider SameSite policies
5. Limit cookie size and number

### Headers
1. Set security headers in production
2. Use appropriate cache control
3. Include CORS headers when needed
4. Normalize custom header names
5. Don't expose sensitive information in headers

## Security Considerations

### Cookie Security
- Use `secure` flag for HTTPS
- Use `httponly` to prevent XSS
- Set appropriate `samesite` policy
- Don't store sensitive data in cookies

### Header Security
- Set security headers
- Validate incoming headers
- Be careful with CORS headers
- Don't expose internal details
