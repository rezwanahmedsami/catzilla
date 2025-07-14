#!/usr/bin/env python3
"""
🚀 Catzilla Simple Dependency Injection Example

This demonstrates Catzilla's DI system with FastAPI-identical syntax.
Perfect for developers migrating from FastAPI or learning DI basics.

Features:
- FastAPI-identical syntax with Depends()
- Automatic service registration
- Zero boilerplate setup
- Copy-paste migration from FastAPI

"""

from catzilla import Catzilla, service, Depends, Path
from catzilla.dependency_injection import set_default_container

# Create app with DI enabled
app = Catzilla(enable_di=True)

# Set the app's container as default for service registration
set_default_container(app.di_container)

# ============================================================================
# SERVICES - Simple and Clean
# ============================================================================

@service("database")
class DatabaseService:
    """Simple database service"""

    def __init__(self):
        self.users = [
            {"id": 1, "name": "Alice", "email": "alice@example.com"},
            {"id": 2, "name": "Bob", "email": "bob@example.com"},
            {"id": 3, "name": "Carol", "email": "carol@example.com"}
        ]
        print("💾 Database service initialized")

    def get_users(self):
        return self.users

    def get_user(self, user_id: int):
        return next((u for u in self.users if u["id"] == user_id), None)

@service("greeting")
class GreetingService:
    """Simple greeting service"""

    def __init__(self):
        print("👋 Greeting service initialized")

    def greet(self, name: str):
        return f"Hello {name} from Catzilla DI! 🚀"

@service("logger")
class LoggerService:
    """Simple logging service"""

    def __init__(self):
        self.logs = []
        print("📝 Logger service initialized")

    def log(self, message: str):
        self.logs.append(f"[{len(self.logs)}] {message}")

    def get_logs(self):
        return self.logs

# ============================================================================
# ROUTES - FastAPI-Identical Syntax
# ============================================================================

@app.get("/")
def home(request, greeter: GreetingService = Depends("greeting")):
    """Home page with dependency injection"""
    return {
        "message": greeter.greet("World"),
        "di_system": "Catzilla v0.2.0",
        "syntax": "FastAPI-identical"
    }

@app.get("/users")
def get_users(request,
              db: DatabaseService = Depends("database"),
              logger: LoggerService = Depends("logger")):
    """Get all users - demonstrates multiple dependencies"""
    logger.log("Fetching all users")
    users = db.get_users()

    return {
        "users": users,
        "count": len(users),
        "logs": logger.get_logs()
    }

@app.get("/users/{user_id}")
def get_user(request,
             user_id: int = Path(...),
             db: DatabaseService = Depends("database"),
             logger: LoggerService = Depends("logger")):
    """Get specific user"""
    logger.log(f"Fetching user {user_id}")
    user = db.get_user(user_id)

    if not user:
        return {"error": f"User {user_id} not found", "status": 404}

    return {
        "user": user,
        "logs": logger.get_logs()
    }

@app.get("/hello/{name}")
def hello(request,
          name: str = Path(...),
          greeter: GreetingService = Depends("greeting"),
          logger: LoggerService = Depends("logger")):
    """Personalized greeting"""
    logger.log(f"Greeting {name}")
    message = greeter.greet(name)

    return {
        "message": message,
        "logs": logger.get_logs()
    }

# ============================================================================
# APPLICATION STARTUP
# ============================================================================

if __name__ == "__main__":
    print("\n🚀 Catzilla Simple DI Example")
    print("=" * 40)
    print("FastAPI-identical syntax with 6.5x better performance!")
    print("\nEndpoints:")
    print("  GET /                 - Home with DI demo")
    print("  GET /users            - List all users")
    print("  GET /users/{user_id}  - Get specific user")
    print("  GET /hello/{name}     - Personalized greeting")
    print("\n🎯 Try:")
    print("  curl http://localhost:8000/")
    print("  curl http://localhost:8000/users")
    print("  curl http://localhost:8000/hello/FastAPI-Dev")

    print(f"\n🚀 Server starting on http://localhost:8000")
    app.listen(host="127.0.0.1", port=8000)
