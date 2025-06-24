#!/usr/bin/env python3
"""
Test script for Catzilla's production mode banner
"""

from catzilla import Catzilla, JSONResponse

# Create production app
app = Catzilla(
    production=True,  # Production mode
    show_banner=True,
    log_requests=False,  # Disabled in production
    enable_colors=False  # Disabled for production logs
)

@app.get("/")
def hello():
    """Simple hello endpoint"""
    return JSONResponse({"message": "Hello, Production Catzilla!", "version": "0.1.0"})

@app.get("/health")
def health():
    """Health check endpoint"""
    return JSONResponse({"status": "healthy", "timestamp": "2025-06-24T23:59:00Z"})

@app.get("/api/users/{user_id}")
def get_user(user_id: str):
    """Get user by ID"""
    return JSONResponse({"user_id": user_id, "name": f"User {user_id}", "environment": "production"})

if __name__ == "__main__":
    print("🚀 Testing Catzilla's Production Mode Banner")
    print("=" * 50)
    print()

    try:
        # Start the production server (should show minimal banner)
        app.listen(8000, "0.0.0.0")
    except KeyboardInterrupt:
        print("\n👋 Production server stopped")
    except Exception as e:
        print(f"❌ Error: {e}")
