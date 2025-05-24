#!/usr/bin/env python3
"""
Test script to verify advanced routing features work correctly
"""

from catzilla import App, JSONResponse

def main():
    app = App()

    # Test basic routes
    @app.get("/")
    def home(req):
        return JSONResponse({"message": "Welcome to Catzilla!"})

    # Test dynamic path parameters
    @app.get("/users/{user_id}")
    def get_user(req):
        user_id = req.path_params.get("user_id", "unknown")
        return JSONResponse({"user_id": user_id, "action": "get"})

    @app.post("/users/{user_id}/posts")
    def create_post(req):
        user_id = req.path_params.get("user_id", "unknown")
        return JSONResponse({"user_id": user_id, "action": "create_post"})

    # Test nested parameters
    @app.get("/users/{user_id}/posts/{post_id}")
    def get_post(req):
        user_id = req.path_params.get("user_id", "unknown")
        post_id = req.path_params.get("post_id", "unknown")
        return JSONResponse({
            "user_id": user_id,
            "post_id": post_id,
            "action": "get_post"
        })

    print("=== Registered Routes ===")
    for route in app.routes():
        print(f"{route['method']:6} {route['path']:30} -> {route['handler_name']}")

    print("\n=== Starting Server ===")
    print("Testing routes with dynamic parameters:")
    print("  GET  /users/123")
    print("  POST /users/123/posts")
    print("  GET  /users/123/posts/456")
    print("\nUse curl or your browser to test the routes above.")
    print("Press Ctrl+C to stop the server.")

    try:
        app.listen(8000)
    except KeyboardInterrupt:
        print("\nServer stopped.")

if __name__ == "__main__":
    main()
