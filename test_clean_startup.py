#!/usr/bin/env python3
"""
Clean test of the Catzilla banner and logging system.
"""

import sys
import os

# Add the python directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'python'))

from catzilla import Catzilla

def test_clean_startup():
    """Test clean startup experience"""

    # Create app with clean startup
    app = Catzilla(production=False, show_banner=True)

    @app.get("/")
    def hello():
        return {"message": "Hello, World!"}

    @app.get("/users/{user_id}")
    def get_user(user_id: int):
        return {"user_id": user_id}

    @app.post("/users")
    def create_user():
        return {"status": "created"}

    @app.put("/users/{user_id}")
    def update_user(user_id: int):
        return {"user_id": user_id, "status": "updated"}

    @app.delete("/users/{user_id}")
    def delete_user(user_id: int):
        return {"user_id": user_id, "status": "deleted"}

    # Start server - this will show clean banner then routes
    try:
        app.listen("127.0.0.1", 8000)
    except KeyboardInterrupt:
        print("\nServer stopped")
    except Exception as e:
        print(f"\nServer test completed: {e}")

if __name__ == "__main__":
    test_clean_startup()
