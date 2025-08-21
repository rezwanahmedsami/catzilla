#!/usr/bin/env python3
"""
E2E Test Server for Dependency Injection Functionality

This server mirrors examples/dependency_injection/ for E2E testing.
It provides DI functionality to be tested via HTTP.
"""
import sys
import argparse
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from catzilla import Catzilla, Request, Response, JSONResponse, Path as PathParam, BaseModel
from typing import Optional, List
import time

# Initialize Catzilla for E2E testing
app = Catzilla(
    production=False,
    show_banner=False,
    log_requests=False
)

# Simple services for E2E testing (without actual DI for simplicity)
class DatabaseService:
    """Mock database service"""
    def __init__(self):
        self.users = [
            {"id": 1, "name": "Alice", "email": "alice@example.com"},
            {"id": 2, "name": "Bob", "email": "bob@example.com"},
            {"id": 3, "name": "Carol", "email": "carol@example.com"}
        ]
        self.created_at = time.time()

    def get_users(self):
        return self.users

    def get_user(self, user_id: int):
        return next((u for u in self.users if u["id"] == user_id), None)

    def create_user(self, user_data: dict):
        new_id = max([u["id"] for u in self.users]) + 1
        new_user = {"id": new_id, **user_data}
        self.users.append(new_user)
        return new_user

class GreetingService:
    """Mock greeting service"""
    def __init__(self):
        self.created_at = time.time()

    def greet(self, name: str) -> str:
        return f"Hello, {name}! Welcome to Catzilla DI testing."

    def farewell(self, name: str) -> str:
        return f"Goodbye, {name}! Thanks for testing Catzilla DI."

class EmailService:
    """Mock email service"""
    def __init__(self):
        self.sent_emails = []
        self.created_at = time.time()

    def send_email(self, to: str, subject: str, body: str):
        email = {
            "to": to,
            "subject": subject,
            "body": body,
            "sent_at": time.time()
        }
        self.sent_emails.append(email)
        return email

    def get_sent_emails(self):
        return self.sent_emails

# Service instances (normally injected via DI)
db_service = DatabaseService()
greeting_service = GreetingService()
email_service = EmailService()

# Pydantic models for request validation
class UserCreate(BaseModel):
    """User creation model"""
    name: str
    email: str

class EmailRequest(BaseModel):
    """Email sending model"""
    to: str
    subject: str
    body: str

class WelcomeRequest(BaseModel):
    """Welcome user model"""
    name: str
    email: str

# Health check
@app.get("/health")
def health_check(request: Request) -> Response:
    """Health check endpoint"""
    return JSONResponse({
        "status": "healthy",
        "server": "di_e2e_test",
        "timestamp": time.time(),
        "services": {
            "database": "active",
            "greeting": "active",
            "email": "active"
        }
    })

# Basic info
@app.get("/")
def home(request: Request) -> Response:
    """DI test server info"""
    return JSONResponse({
        "message": "Catzilla E2E Dependency Injection Test Server",
        "features": [
            "Service injection",
            "Service lifecycle",
            "Multiple services",
            "Service interaction"
        ],
        "endpoints": [
            "GET /di/users",
            "GET /di/users/{user_id}",
            "POST /di/users",
            "GET /di/greet/{name}",
            "POST /di/send-email",
            "GET /di/emails",
            "GET /di/services"
        ],
        "services": {
            "database": {"users_count": len(db_service.users)},
            "greeting": {"active": True},
            "email": {"sent_count": len(email_service.sent_emails)}
        }
    })

# Database service endpoints
@app.get("/di/users")
def get_users(request: Request) -> Response:
    """Get all users using database service"""
    users = db_service.get_users()

    return JSONResponse({
        "users": users,
        "count": len(users),
        "service": "database",
        "timestamp": time.time()
    })

@app.get("/di/users/{user_id}")
def get_user(request: Request, user_id: int = PathParam(..., description="User ID")) -> Response:
    """Get user by ID using database service"""
    user = db_service.get_user(user_id)

    if user:
        return JSONResponse({
            "user": user,
            "service": "database",
            "timestamp": time.time()
        })
    else:
        return JSONResponse({
            "error": "User not found",
            "user_id": user_id,
            "service": "database"
        }, status_code=404)

@app.post("/di/users")
def create_user(request: Request, user_data: UserCreate) -> Response:
    """Create user using database service"""
    user_dict = {"name": user_data.name, "email": user_data.email}
    new_user = db_service.create_user(user_dict)

    return JSONResponse({
        "message": "User created successfully",
        "user": new_user,
        "service": "database",
        "timestamp": time.time()
    }, status_code=201)

# Greeting service endpoints
@app.get("/di/greet/{name}")
def greet_user(request: Request, name: str = PathParam(..., description="Name to greet")) -> Response:
    """Greet user using greeting service"""
    greeting = greeting_service.greet(name)

    return JSONResponse({
        "greeting": greeting,
        "name": name,
        "service": "greeting",
        "timestamp": time.time()
    })

@app.get("/di/farewell/{name}")
def farewell_user(request: Request, name: str = PathParam(..., description="Name to say farewell")) -> Response:
    """Say farewell using greeting service"""
    farewell = greeting_service.farewell(name)

    return JSONResponse({
        "farewell": farewell,
        "name": name,
        "service": "greeting",
        "timestamp": time.time()
    })

# Email service endpoints
@app.post("/di/send-email")
def send_email(request: Request, email_data: EmailRequest) -> Response:
    """Send email using email service"""
    sent_email = email_service.send_email(email_data.to, email_data.subject, email_data.body)

    return JSONResponse({
        "message": "Email sent successfully",
        "email": sent_email,
        "service": "email",
        "timestamp": time.time()
    }, status_code=201)

@app.get("/di/emails")
def get_sent_emails(request: Request) -> Response:
    """Get all sent emails using email service"""
    emails = email_service.get_sent_emails()

    return JSONResponse({
        "emails": emails,
        "count": len(emails),
        "service": "email",
        "timestamp": time.time()
    })

# Service status endpoint
@app.get("/di/services")
def get_services_status(request: Request) -> Response:
    """Get status of all injected services"""
    return JSONResponse({
        "services": {
            "database": {
                "status": "active",
                "users_count": len(db_service.users),
                "created_at": db_service.created_at
            },
            "greeting": {
                "status": "active",
                "created_at": greeting_service.created_at
            },
            "email": {
                "status": "active",
                "sent_count": len(email_service.sent_emails),
                "created_at": email_service.created_at
            }
        },
        "total_services": 3,
        "timestamp": time.time()
    })

# Combined service interaction
@app.post("/di/welcome-user")
def welcome_new_user(request: Request, welcome_data: WelcomeRequest) -> Response:
    """Welcome new user using multiple services"""
    # Create user (database service)
    user_dict = {"name": welcome_data.name, "email": welcome_data.email}
    new_user = db_service.create_user(user_dict)

    # Generate greeting (greeting service)
    greeting = greeting_service.greet(welcome_data.name)

    # Send welcome email (email service)
    welcome_email = email_service.send_email(
        to=welcome_data.email,
        subject="Welcome to Catzilla!",
        body=f"Hello {welcome_data.name}! Welcome to our platform."
    )

    return JSONResponse({
        "message": "User welcomed successfully",
        "user": new_user,
        "greeting": greeting,
        "email_sent": welcome_email,
        "services_used": ["database", "greeting", "email"],
        "timestamp": time.time()
    }, status_code=201)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Catzilla E2E DI Test Server")
    parser.add_argument("--port", type=int, default=8103, help="Port to run server on")
    parser.add_argument("--host", type=str, default="127.0.0.1", help="Host to bind to")

    args = parser.parse_args()

    print(f"🚀 Starting Catzilla E2E DI Test Server")
    print(f"📍 Server: http://{args.host}:{args.port}")
    print(f"🏥 Health: http://{args.host}:{args.port}/health")

    app.listen(port=args.port, host=args.host)
