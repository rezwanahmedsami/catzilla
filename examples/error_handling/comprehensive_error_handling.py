"""
Example demonstrating Catzilla's comprehensive error handling features
"""

from catzilla import Catzilla, Request, Response, JSONResponse

# Create app in production mode for clean JSON errors
app = Catzilla(production=True, auto_validation=True, memory_profiling=False)

# Example 1: Custom exception handlers for specific exception types
@app.set_exception_handler(ValueError)
def handle_value_error(request: Request, exc: ValueError) -> Response:
    """Handle ValueError with a clean 400 response"""
    return JSONResponse({
        "error": "Invalid input",
        "message": str(exc),
        "path": request.path
    }, status_code=400)

@app.set_exception_handler(FileNotFoundError)
def handle_file_not_found(request: Request, exc: FileNotFoundError) -> Response:
    """Handle FileNotFoundError with a clean 404 response"""
    return JSONResponse({
        "error": "Resource not found",
        "message": "The requested file does not exist",
        "path": request.path
    }, status_code=404)

@app.set_exception_handler(PermissionError)
def handle_permission_error(request: Request, exc: PermissionError) -> Response:
    """Handle PermissionError with a clean 403 response"""
    return JSONResponse({
        "error": "Access denied",
        "message": "You don't have permission to access this resource",
        "path": request.path
    }, status_code=403)

# Example 2: Custom 404 handler
@app.set_not_found_handler
def custom_404_handler(request: Request) -> Response:
    """Custom 404 handler with helpful information"""
    return JSONResponse({
        "error": "Endpoint not found",
        "message": f"The endpoint '{request.path}' does not exist",
        "method": request.method,
        "suggestions": [
            "Check the URL for typos",
            "Verify the HTTP method is correct",
            "See API documentation for available endpoints"
        ]
    }, status_code=404)

# Example 3: Custom 500 handler for unhandled exceptions
@app.set_internal_error_handler
def custom_500_handler(request: Request, exc: Exception) -> Response:
    """Custom 500 handler that logs errors and returns clean response"""
    # In production, log the error but don't expose details
    print(f"Internal error on {request.method} {request.path}: {exc}")

    return JSONResponse({
        "error": "Internal server error",
        "message": "An unexpected error occurred",
        "request_id": id(request),  # Simple request ID for tracking
        "support": "Contact support with the request ID"
    }, status_code=500)

# Demo routes that trigger different types of errors

@app.get("/api/divide/{a}/{b}")
def divide_numbers(request: Request) -> Response:
    """Route that can trigger ValueError for invalid numbers or ZeroDivisionError"""
    try:
        a = float(request.path_params["a"])
        b = float(request.path_params["b"])
        result = a / b
        return JSONResponse({"result": result})
    except ZeroDivisionError:
        # This will be caught by the general exception handler since no specific handler is registered
        raise ValueError("Division by zero is not allowed")
    except ValueError as e:
        # This will be caught by our ValueError handler
        raise e

@app.get("/api/file/{filename}")
def read_file(request: Request) -> Response:
    """Route that can trigger FileNotFoundError"""
    filename = request.path_params["filename"]

    # Simulate file reading that might fail
    if filename == "missing.txt":
        raise FileNotFoundError(f"File '{filename}' not found")
    elif filename == "secret.txt":
        raise PermissionError(f"Access denied to '{filename}'")
    else:
        return JSONResponse({"content": f"Contents of {filename}"})

@app.post("/api/data")
def process_data(request: Request) -> Response:
    """Route that validates JSON data and can trigger various errors"""
    try:
        data = request.json()

        # Validate required fields
        if "name" not in data:
            raise ValueError("Missing required field: name")

        if "age" not in data:
            raise ValueError("Missing required field: age")

        # Validate age
        age = int(data["age"])
        if age < 0 or age > 150:
            raise ValueError("Age must be between 0 and 150")

        return JSONResponse({
            "success": True,
            "message": f"Hello {data['name']}, age {age}"
        })

    except (TypeError, KeyError) as e:
        raise ValueError("Invalid JSON data format")

@app.get("/api/crash")
def intentional_crash(request: Request) -> Response:
    """Route that intentionally crashes to test 500 handler"""
    # This will trigger the internal error handler
    raise RuntimeError("This is an intentional crash for testing")

@app.get("/api/health")
def health_check(request: Request) -> Response:
    """Simple health check that should always work"""
    return JSONResponse({"status": "healthy", "version": "1.0.0"})

if __name__ == "__main__":
    print("Starting Catzilla server with comprehensive error handling...")
    print("\nTest these endpoints:")
    print("  GET  /api/health                    - Should work")
    print("  GET  /api/divide/10/2               - Should work")
    print("  GET  /api/divide/10/0               - Triggers ValueError handler")
    print("  GET  /api/divide/abc/2              - Triggers ValueError handler")
    print("  GET  /api/file/test.txt             - Should work")
    print("  GET  /api/file/missing.txt          - Triggers FileNotFoundError handler")
    print("  GET  /api/file/secret.txt           - Triggers PermissionError handler")
    print("  POST /api/data                      - Send JSON: {'name': 'Alice', 'age': 25}")
    print("  POST /api/data                      - Send invalid JSON to trigger ValueError")
    print("  GET  /api/crash                     - Triggers internal error handler")
    print("  GET  /api/nonexistent               - Triggers custom 404 handler")
    print("  POST /api/health                    - Triggers 405 method not allowed")

    app.listen(8080)
