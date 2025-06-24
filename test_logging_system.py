#!/usr/bin/env python3
"""
Test script for Catzilla's beautiful startup banner and logging system
"""

from catzilla import Catzilla, JSONResponse, Path
import time

# Create development app with logging enabled
app = Catzilla(
    production=True,  # Development mode
    show_banner=True,
    log_requests=False,
    enable_colors=True,
    show_request_details=True
)

@app.get("/")
def hello(request):
    """Simple hello endpoint"""
    return JSONResponse({"message": "Hello, Catzilla!", "version": "0.1.0"})

@app.get("/users/{user_id}")
def get_user(request, user_id: str = Path(...)):
    """Get user by ID"""
    if user_id == "404":
        return JSONResponse({"error": "User not found"}, status_code=404)
    return JSONResponse({"user_id": user_id, "name": f"User {user_id}"})

@app.post("/users")
def create_user(request):
    """Create a new user"""
    return JSONResponse({"message": "User created", "id": 123}, status_code=201)

@app.put("/users/{user_id}")
def update_user(request, user_id: str = Path(...)):
    """Update user"""
    if user_id == "500":
        raise ValueError("Simulated server error")
    return JSONResponse({"message": f"User {user_id} updated"})

@app.delete("/users/{user_id}")
def delete_user(request, user_id: str = Path(...)):
    """Delete user"""
    return JSONResponse({"message": f"User {user_id} deleted"}, status_code=204)

if __name__ == "__main__":
    print("🧪 Testing Catzilla's Beautiful Startup Banner & Logging System")
    print("=" * 60)
    print()

    # Test startup banner
    print("Starting development server with beautiful banner...")
    print()

    try:
        # Start the server (this will show the banner)
        app.listen(host="127.0.0.1", port=8000)
    except KeyboardInterrupt:
        print("\n👋 Server stopped by user")
    except Exception as e:
        print(f"❌ Error: {e}")
