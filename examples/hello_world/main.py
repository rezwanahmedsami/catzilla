"""
Catzilla Hello World Example
"""

from catzilla import App, Response

# Create a new Catzilla application
app = App()

@app.get("/")
def index(request):
    """Handle requests to the root path"""
    return Response(
        status_code=200,
        body="<h1>Hello from Catzilla!</h1><p>The fastest Python web framework with a C core.</p>",
        content_type="text/html"
    )

@app.get("/json")
def json_example(request):
    """Return a JSON response"""
    return Response(
        status_code=200,
        body='{"message": "Hello, World!", "framework": "Catzilla"}',
        content_type="application/json"
    )

@app.post("/echo")
def echo(request):
    """Echo back the request body"""
    return Response(
        status_code=200,
        body=request.body or "No body provided",
        content_type="text/plain"
    )

# Start the server on port 8000
if __name__ == "__main__":
    try:
        app.listen(8000)
    except KeyboardInterrupt:
        print("\nShutting down server...")
        app.stop()