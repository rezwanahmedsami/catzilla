"""
Example demonstrating Catzilla's production mode startup banner
"""

from catzilla import Catzilla
from catzilla.types import JSONResponse, Request


# Create app with production mode enabled
app = Catzilla(
    production=True,  # Enable production mode
    show_banner=True,  # Show startup banner (minimal in production)
    log_requests=False,  # Disable request logging for performance
    enable_colors=False,  # Disable colors for production logs
)


@app.get("/")
def home(request: Request):
    """Homepage"""
    return {"message": "Welcome to Catzilla Production!", "status": "running"}


@app.get("/health")
def health_check(request: Request):
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": "2025-06-24T10:30:15Z"}


@app.get("/api/users/{user_id}")
def get_user(request: Request):
    """Get user by ID"""
    user_id = request.path_params.get("user_id")
    return {"user_id": user_id, "name": f"User {user_id}"}


if __name__ == "__main__":
    # Start server in production mode
    app.listen(8000, "0.0.0.0")
