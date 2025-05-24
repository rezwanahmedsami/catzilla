# Catzilla Error Handling Implementation

This document describes the completed error handling features for Catzilla framework v0.1.0.

## ✅ Completed Features

### 1. Production-Mode Clean JSON Error Responses

Catzilla automatically provides clean, user-friendly error responses in production mode while offering detailed debugging information in development mode.

**Usage:**
```python
# Production mode - clean JSON errors
app = App(production=True)

# Development mode - detailed error information
app = App(production=False)
```

**Example responses:**

**Production mode (production=True):**
```json
{
  "error": "Not found"
}
```

**Development mode (production=False):**
```json
{
  "error": "Not found",
  "detail": "Additional debugging information"
}
```

### 2. Central Exception Handler Support

Register custom handlers for specific exception types using `set_exception_handler()`.

**Usage:**
```python
def handle_value_error(request, exc):
    return JSONResponse({
        "error": "Invalid Value",
        "message": str(exc),
        "path": request.path
    }, status_code=400)

app.set_exception_handler(ValueError, handle_value_error)
```

**Features:**
- Handlers receive `(request, exception)` parameters
- Must return a `Response` object
- Automatic fallback if custom handler fails
- Supports any exception type hierarchy

### 3. Global Fallback 404 and 500 Handlers

Set custom handlers for common HTTP error scenarios.

**404 Not Found Handler:**
```python
def custom_404_handler(request):
    return JSONResponse({
        "error": "Route Not Found",
        "path": request.path,
        "available_routes": ["/", "/api/users"]
    }, status_code=404)

app.set_not_found_handler(custom_404_handler)
```

**500 Internal Server Error Handler:**
```python
def custom_500_handler(request, exc):
    return JSONResponse({
        "error": "Internal Server Error",
        "exception_type": type(exc).__name__
    }, status_code=500)

app.set_internal_error_handler(custom_500_handler)
```

## Implementation Details

### Error Response Flow

1. **Route Handler Exception** → Check custom exception handlers → Use internal error handler → Default 500
2. **Route Not Found** → Use custom 404 handler → Default 404
3. **Method Not Allowed** → Default 405 with allowed methods

### Production vs Development Mode

| Feature | Production Mode | Development Mode |
|---------|----------------|------------------|
| Error detail | Hidden | Shown |
| Stack traces | Hidden | Printed to console |
| Error messages | Generic | Specific |
| Response format | Clean JSON | Detailed JSON/text |

### Fallback Behavior

If any custom error handler fails, Catzilla automatically falls back to safe default responses:

- **Custom exception handler fails** → Default 500 error
- **Custom 404 handler fails** → Default 404 error
- **Custom 500 handler fails** → Default 500 error

This ensures the application never crashes due to faulty error handling code.

## Example Implementation

See `examples/error_handling_demo.py` for a complete working example that demonstrates:

- Custom exception handlers for `ValueError` and `ZeroDivisionError`
- Custom 404 handler with helpful route suggestions
- Custom 500 handler with conditional detail exposure
- Production vs development mode behavior

## API Reference

### App Class Methods

#### `App(production: bool = False)`
Create a new Catzilla application.
- `production`: If True, return clean JSON errors without sensitive details

#### `set_exception_handler(exception_type: type, handler: Callable)`
Register a custom exception handler.
- `exception_type`: Exception class to handle (e.g., `ValueError`)
- `handler`: Function `(request, exception) -> Response`

#### `set_not_found_handler(handler: Callable)`
Set global 404 Not Found handler.
- `handler`: Function `(request) -> Response`

#### `set_internal_error_handler(handler: Callable)`
Set global 500 Internal Server Error handler.
- `handler`: Function `(request, exception) -> Response`

## Performance Impact

The error handling system is designed for minimal performance overhead:

- Exception handlers use dictionary lookup (O(1))
- No reflection or dynamic inspection
- Fallback responses are pre-computed
- Production mode optimizes for speed over debugging

## Thread Safety

All error handling mechanisms are thread-safe:

- Handler dictionaries are immutable after registration
- No shared mutable state during request processing
- Each request gets its own error handling context

## Best Practices

1. **Always register exception handlers** for common business logic exceptions
2. **Use production mode in deployment** to avoid leaking sensitive information
3. **Keep error handlers simple** to avoid cascading failures
4. **Test error scenarios** to ensure handlers work correctly
5. **Log detailed errors server-side** while returning clean responses to clients
