from catzilla import Catzilla, Request, Response, JSONResponse
from typing import Optional

app = Catzilla()

def example_middleware(request: Request) -> Optional[Response]:
    """
    Example middleware that modifies the response.
    This middleware adds a custom header to the response.
    """
    print("Example Middleware executed")
    return None

def auth_middleware(request: Request) -> Optional[Response]:
    """
    Authentication middleware that checks for a specific header.
    If the header is missing, it returns an error response.
    """
    if 'Authorization' not in request.headers:
        print("Authentication failed: Missing Authorization header")
        return JSONResponse({"error": "Unauthorized"}, status_code=401)

    print("Authentication successful")
    return None  # Continue to route handler

@app.get("/", middleware=[example_middleware])
def index(request: Request):
    """
    Example route that returns a simple response.
    The middleware will modify this response.
    """
    return "Hello, World!"


@app.get("/protected", middleware=[auth_middleware])
def protected_route(request: Request):
    """
    Protected route that requires authentication.
    The auth_middleware will check for the Authorization header.
    """
    print("Accessing protected route")
    return "Protected content accessed!"

if __name__ == "__main__":
    print("Server is running on http://localhost:8000")
    app.listen(port=8000)
