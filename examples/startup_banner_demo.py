"""
Example demonstrating Catzilla's beautiful startup banner and development logging
"""

from catzilla import Catzilla
from catzilla.types import JSONResponse, Request


# Create app with development mode enabled
app = Catzilla(
    production=False,  # Enable development mode
    show_banner=True,  # Show beautiful startup banner
    log_requests=True,  # Enable request logging
    enable_colors=True,  # Enable colorized output
    show_request_details=True  # Show detailed request info
)


@app.get("/")
def home(request: Request):
    """Homepage"""
    return {"message": "Welcome to Catzilla!", "status": "running"}


@app.get("/users/{user_id}")
def get_user(request: Request):
    """Get user by ID"""
    user_id = request.path_params.get("user_id")
    return {"user_id": user_id, "name": f"User {user_id}"}


@app.post("/users")
def create_user(request: Request):
    """Create a new user"""
    return {"message": "User created", "id": 123}, 201


@app.put("/users/{user_id}")
def update_user(request: Request):
    """Update user"""
    user_id = request.path_params.get("user_id")
    return {"user_id": user_id, "message": "User updated"}


@app.delete("/users/{user_id}")
def delete_user(request: Request):
    """Delete user"""
    return JSONResponse({"message": "User deleted"}, status_code=204)


@app.get("/error")
def error_endpoint(request: Request):
    """Test error handling"""
    raise ValueError("This is a test error")


if __name__ == "__main__":
    # Start server with beautiful startup banner and development logging
    app.listen(8000, "127.0.0.1")
