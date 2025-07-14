"""
Debug Logging Example

This example demonstrates Catzilla's beautiful debug logging system
with request/response tracking, performance metrics, and colored output.

Features demonstrated:
- Beautiful debug logging with colors
- Request/response timing
- Custom log levels and formatting
- Performance metrics integration
- Production vs development logging
"""

from catzilla import (
    Catzilla, Request, Response, JSONResponse,
    Query, Header, Path, Form, ValidationError
)
import time
import logging

# Initialize Catzilla with debug logging enabled
app = Catzilla(
    production=False,      # Enable development features and detailed logging
    show_banner=True,      # Show beautiful startup banner
    log_requests=True      # Log all incoming requests
)

@app.get("/")
def home(request: Request) -> Response:
    """Simple home endpoint to test logging"""
    print("🏠 Home endpoint accessed")

    return JSONResponse({
        "message": "Debug logging example",
        "timestamp": time.time(),
        "path": request.path
    })

@app.get("/slow-operation")
def slow_operation(request: Request) -> Response:
    """Endpoint that simulates slow processing to show timing logs"""
    print("🐌 Starting slow operation")

    # Simulate some processing time
    time.sleep(0.5)

    print("✅ Slow operation completed")

    return JSONResponse({
        "message": "Operation completed",
        "processing_time": "500ms",
        "status": "success"
    })

@app.get("/api/data/{data_id}")
def get_data(request, data_id: str = Path(..., description="Data ID")) -> Response:
    """API endpoint with path parameters to demonstrate detailed logging"""

    print(f"📊 Fetching data for ID: {data_id}")

    # Log request details
    print(f"🔍 Request method: {request.method}")
    print(f"🔍 Request path: {request.path}")
    print(f"🔍 Query params: {dict(request.query_params)}")

    if data_id == "error":
        print("❌ Simulated error for testing")
        return JSONResponse(
            {"error": "Data not found", "data_id": data_id},
            status_code=404
        )

    print(f"✅ Successfully retrieved data for ID: {data_id}")

    return JSONResponse({
        "data_id": data_id,
        "data": f"Sample data for {data_id}",
        "logged": True
    })

@app.post("/api/logs/custom")
def custom_log_levels(request: Request) -> Response:
    """Demonstrate different log levels and custom formatting"""

    # Different log levels using print statements with emoji indicators
    print("🔍 DEBUG: This is detailed debugging information")
    print("ℹ️  INFO: General information about operation")
    print("⚠️  WARNING: Something needs attention")
    print("❌ ERROR: Something went wrong but handled")

    # Structured logging simulation
    print("📈 PERFORMANCE: Response time: 125.5ms for /api/logs/custom")

    return JSONResponse({
        "message": "Log levels demonstrated",
        "logged_levels": ["debug", "info", "warning", "error"],
        "structured_logging": True
    })

@app.get("/health")
def health_check(request: Request) -> Response:
    """Health check endpoint for monitoring"""
    print("💚 Health check requested")

    return JSONResponse({
        "status": "healthy",
        "framework": "Catzilla v0.2.0",
        "logging": "enabled",
        "debug_mode": not app.production
    })

if __name__ == "__main__":
    print("🚨 Starting Catzilla Debug Logging Example")
    print("📝 Available endpoints:")
    print("   GET  /                    - Home with basic logging")
    print("   GET  /slow-operation      - Slow operation with timing logs")
    print("   GET  /api/data/{data_id}  - Data endpoint with detailed logging")
    print("   POST /api/logs/custom     - Custom log levels demonstration")
    print("   GET  /health              - Health check")
    print()
    print("🎨 Features demonstrated:")
    print("   • Beautiful colored debug output")
    print("   • Request/response timing")
    print("   • Different log levels (debug, info, warning, error)")
    print("   • Structured logging with extra fields")
    print("   • Production vs development logging modes")
    print()
    print("🧪 Try these examples:")
    print("   curl http://localhost:8000/")
    print("   curl http://localhost:8000/slow-operation")
    print("   curl http://localhost:8000/api/data/123")
    print("   curl http://localhost:8000/api/data/error")
    print("   curl -X POST http://localhost:8000/api/logs/custom")
    print()

    app.listen(host="0.0.0.0", port=8000)
