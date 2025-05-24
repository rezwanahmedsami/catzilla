# Error Handling Examples

This directory contains examples demonstrating Catzilla's comprehensive error handling capabilities.

## Features Demonstrated

### 1. Production Mode Clean JSON Responses
- Set `App(production=True)` for clean JSON error responses without stack traces
- Automatically formats errors as JSON instead of plain text
- Hides implementation details in production

### 2. Custom Exception Handlers
- Register handlers for specific exception types using `@app.set_exception_handler(ExceptionType)`
- Handle different errors with appropriate HTTP status codes and messages
- Provides graceful degradation when handlers fail

### 3. Global 404 and 500 Handlers
- Custom 404 handler with `@app.set_not_found_handler`
- Custom 500 handler with `@app.set_internal_error_handler`
- Consistent error response format across all error types

## Files

- `comprehensive_error_handling.py` - Complete example showing all error handling features
- `production_vs_development.py` - Comparison of error responses in production vs development mode
- `simple_error_handling.py` - Basic error handling setup

## Testing the Examples

Run any example and test different error scenarios:

```bash
python comprehensive_error_handling.py
```

Then test with curl:
```bash
# Test successful request
curl http://localhost:8080/api/health

# Test ValueError handler
curl http://localhost:8080/api/divide/10/0

# Test custom 404 handler
curl http://localhost:8080/api/nonexistent

# Test method not allowed (405)
curl -X POST http://localhost:8080/api/health

# Test internal server error (500)
curl http://localhost:8080/api/crash
```

## Expected Benefits

1. **Consistent Error Format**: All errors return JSON in the same format
2. **Security**: Production mode hides sensitive error details
3. **User Experience**: Clear, actionable error messages
4. **Debugging**: Development mode shows full error details
5. **Maintainability**: Centralized error handling reduces code duplication
