"""
Example comparing error responses in production vs development mode
"""

from catzilla import App, Request, JSONResponse

def create_development_app():
    """Create app in development mode (default)"""
    app = App(production=False)  # Development mode - shows detailed errors

    @app.get("/crash")
    def crash_handler(request: Request):
        raise ValueError("This is a test error with sensitive info: database_password=secret123")

    @app.get("/missing")
    def missing_handler(request: Request):
        # This route doesn't exist at runtime, but the path does
        raise FileNotFoundError("/etc/sensitive/config.txt not found")

    return app

def create_production_app():
    """Create app in production mode"""
    app = App(production=True)  # Production mode - clean JSON errors

    @app.get("/crash")
    def crash_handler(request: Request):
        raise ValueError("This is a test error with sensitive info: database_password=secret123")

    @app.get("/missing")
    def missing_handler(request: Request):
        raise FileNotFoundError("/etc/sensitive/config.txt not found")

    return app

if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "production":
        print("Starting Catzilla server in PRODUCTION mode")
        print("Error responses will be clean JSON without sensitive details")
        app = create_production_app()
    else:
        print("Starting Catzilla server in DEVELOPMENT mode")
        print("Error responses will include full details and stack traces")
        app = create_development_app()

    print("\nTest these endpoints to see the difference:")
    print("  GET /crash    - Triggers ValueError")
    print("  GET /missing  - Triggers FileNotFoundError")
    print("  GET /404      - Triggers 404 Not Found")
    print("\nRun with 'python production_vs_development.py production' for production mode")

    app.listen(8080)
