# Quick Start Guide

Get up and running with Catzilla in under 5 minutes. This guide will walk you through installation, creating your first app, and exploring key features.

## Prerequisites

- Python 3.8 or higher
- pip package manager

## Installation

Install Catzilla using pip:

```bash
pip install catzilla
```

For development with additional tools:

```bash
pip install catzilla[dev]
```

## Your First Catzilla App

Create a new file called `main.py`:

```python
from catzilla import Catzilla

# Create Catzilla app instance
app = Catzilla()

@app.get("/")
def read_root(request):
    return {"message": "Hello, Catzilla! 🚀", "framework": "catzilla"}

@app.get("/items/{item_id}")
def read_item(request, item_id: int):
    return {"item_id": item_id}

if __name__ == "__main__":
    app.listen(host="0.0.0.0", port=8000)
```

## Run Your App

```bash
python main.py
```

Your API is now running! Open your browser and visit:
- **API Endpoint**: http://localhost:8000
- **Interactive Docs**: http://localhost:8000/docs
- **Alternative Docs**: http://localhost:8000/redoc

## Adding Request Validation

Catzilla includes ultra-fast validation compatible with Pydantic:

```python
from catzilla import Catzilla
from catzilla.validation import BaseModel

app = Catzilla()

class User(BaseModel):
    id: int
    name: str
    email: str

@app.post("/users/")
def create_user(request, user: User):
    return {"user": user.name, "status": "created"}

@app.get("/users/{user_id}")
def get_user(request, user_id: int):
    return {
        "user_id": user_id,
        "name": f"User {user_id}",
        "email": f"user{user_id}@example.com"
    }

if __name__ == "__main__":
    app.listen(host="0.0.0.0", port=8000)
```
    app.listen(port=8000)
```

**Try it:**
- `GET /users/123` → `{"user_id": 123, "type": "int"}`
- `GET /hello/Alice` → `{"message": "Hello, Alice!"}`

## Step 3: Add Auto-Validation

Catzilla includes a **100x faster** validation engine that's fully compatible with Pydantic:

```python
from catzilla import Catzilla, BaseModel
from typing import Optional

app = Catzilla()

class User(BaseModel):
    name: str
    age: int
    email: Optional[str] = None
    is_active: bool = True

class UserResponse(BaseModel):
    user: User
    status: str
    user_id: int

@app.post("/users")
def create_user(request, user: User):
    # Validation happens automatically at C-speed!
    return UserResponse(
        user=user,
        status="created",
        user_id=12345
    )

@app.get("/users/{user_id}")
def get_user(request, user_id: int):
    return User(
        name=f"User {user_id}",
        age=25,
        email=f"user{user_id}@example.com"
    )

if __name__ == "__main__":
    app.listen(port=8000)
```

**Test the validation:**

```bash
# Valid request
curl -X POST http://localhost:8000/users \
  -H "Content-Type: application/json" \
  -d '{"name": "Alice", "age": 30, "email": "alice@example.com"}'

# Invalid request (missing name)
curl -X POST http://localhost:8000/users \
  -H "Content-Type: application/json" \
  -d '{"age": 30}'
```

## Step 4: Add Background Tasks

Catzilla's revolutionary background task system automatically compiles tasks to C for maximum performance:

```python
from catzilla import Catzilla, BaseModel, TaskPriority
import time

app = Catzilla(enable_background_tasks=True)

class User(BaseModel):
    name: str
    email: str

def send_welcome_email(user_email: str, user_name: str):
    """This function will be automatically compiled to C for speed!"""
    time.sleep(0.1)  # Simulate email sending
    return f"Welcome email sent to {user_name} at {user_email}"

def process_user_analytics(user_id: int):
    """Heavy computation that benefits from C-speed execution"""
    time.sleep(0.5)  # Simulate analytics processing
    return f"Analytics processed for user {user_id}"

@app.post("/users")
def create_user(request, user: User):
    # Add background tasks with different priorities
    email_task = app.add_task(
        send_welcome_email,
        user.email,
        user.name,
        priority=TaskPriority.HIGH
    )

    analytics_task = app.add_task(
        process_user_analytics,
        12345,
        priority=TaskPriority.NORMAL
    )

    return {
        "user": user,
        "status": "created",
        "background_tasks": {
            "email_task": email_task.task_id,
            "analytics_task": analytics_task.task_id
        }
    }

@app.get("/tasks/{task_id}/status")
def get_task_status(request, task_id: str):
    # Check task status (this would integrate with the task system)
    return {"task_id": task_id, "status": "completed"}

if __name__ == "__main__":
    app.listen(port=8000)
```

## Step 5: Add Dependency Injection

Catzilla includes a powerful dependency injection system with C-optimized resolution:

```python
from catzilla import Catzilla, BaseModel, service, Depends

app = Catzilla(enable_di=True)

# Define services using decorators
@service("database")
class DatabaseService:
    def __init__(self):
        self.users = {}
        self.next_id = 1

    def create_user(self, user_data):
        user_id = self.next_id
        self.next_id += 1
        self.users[user_id] = user_data
        return user_id

    def get_user(self, user_id):
        return self.users.get(user_id)

@service("logger")
class LoggerService:
    def __init__(self):
        self.logs = []

    def log(self, message):
        self.logs.append(f"[{time.time()}] {message}")

class User(BaseModel):
    name: str
    email: str

@app.post("/users")
def create_user(
    user: User,
    db: DatabaseService = Depends("database"),
    logger: LoggerService = Depends("logger")
):
    # Dependencies are automatically injected at C-speed!
    user_id = db.create_user(user.dict())
    logger.log(f"Created user {user_id}: {user.name}")

    return {"user_id": user_id, "user": user, "status": "created"}

@app.get("/users/{user_id}")
def get_user(
    user_id: int,
    db: DatabaseService = Depends("database"),
    logger: LoggerService = Depends("logger")
):
    user_data = db.get_user(user_id)
    logger.log(f"Retrieved user {user_id}")

    if not user_data:
        return {"error": "User not found"}, 404

    return {"user_id": user_id, "user": user_data}

@app.get("/logs")
def get_logs(logger: LoggerService = Depends("logger")):
    return {"logs": logger.logs[-10:]}  # Last 10 logs

if __name__ == "__main__":
    app.listen(port=8000)
```

## Step 6: Add Static File Serving

Serve static files with Catzilla's high-performance static server:

```python
from catzilla import Catzilla

app = Catzilla()

# Mount static files - uses C-accelerated serving with hot caching
app.mount_static("/static", directory="./static")
app.mount_static("/assets", directory="./assets")

@app.get("/")
def home(request):
    return {
        "message": "Welcome to Catzilla!",
        "static_files": {
            "css": "/static/style.css",
            "js": "/static/app.js",
            "images": "/assets/logo.png"
        }
    }

if __name__ == "__main__":
    app.listen(port=8000)
```

Create some static files:

```bash
mkdir static assets
echo "body { font-family: Arial; }" > static/style.css
echo "console.log('Catzilla rocks!');" > static/app.js
# Add any image as assets/logo.png
```

## Step 7: Complete Example

Here's a complete example showcasing all of Catzilla's features:

```python
from catzilla import Catzilla, BaseModel, service, Depends, TaskPriority
from typing import Optional, List
import time

# Initialize Catzilla with all features enabled
app = Catzilla(
    enable_background_tasks=True,
    enable_di=True,
    enable_jemalloc=True  # 30% memory optimization
)

# Mount static files
app.mount_static("/static", directory="./static")

# Data Models
class User(BaseModel):
    name: str
    email: str
    age: Optional[int] = None
    is_active: bool = True

class UserResponse(BaseModel):
    user_id: int
    user: User
    status: str
    created_at: float

# Services
@service("database")
class DatabaseService:
    def __init__(self):
        self.users = {}
        self.next_id = 1

    def create_user(self, user: User) -> int:
        user_id = self.next_id
        self.next_id += 1
        self.users[user_id] = user
        return user_id

    def get_user(self, user_id: int) -> Optional[User]:
        return self.users.get(user_id)

    def get_all_users(self) -> List[User]:
        return list(self.users.values())

@service("email")
class EmailService:
    def send_welcome_email(self, email: str, name: str):
        time.sleep(0.1)  # Simulate email sending
        return f"Welcome email sent to {name} at {email}"

# Background Tasks
def process_user_onboarding(user_email: str, user_name: str):
    """This will be compiled to C automatically for maximum performance!"""
    time.sleep(0.5)  # Simulate complex onboarding process
    return f"Onboarding completed for {user_name}"

# Routes
@app.get("/")
def home(request):
    return {
        "message": "🚀 Welcome to Catzilla!",
        "features": [
            "C-Accelerated Routing",
            "100x Faster Validation",
            "Revolutionary Background Tasks",
            "Advanced Dependency Injection",
            "30% Memory Optimization"
        ],
        "docs": "/docs",
        "health": "/health"
    }

@app.post("/users")
def create_user(
    user: User,
    db: DatabaseService = Depends("database"),
    email_service: EmailService = Depends("email")
) -> UserResponse:
    # Create user in database
    user_id = db.create_user(user)

    # Send welcome email as background task (C-speed execution)
    app.add_task(
        email_service.send_welcome_email,
        user.email,
        user.name,
        priority=TaskPriority.HIGH
    )

    # Process onboarding as background task
    app.add_task(
        process_user_onboarding,
        user.email,
        user.name,
        priority=TaskPriority.NORMAL
    )

    return UserResponse(
        user_id=user_id,
        user=user,
        status="created",
        created_at=time.time()
    )

@app.get("/users/{user_id}")
def get_user(user_id: int, db: DatabaseService = Depends("database")):
    user = db.get_user(user_id)
    if not user:
        return {"error": "User not found"}, 404
    return {"user_id": user_id, "user": user}

@app.get("/users")
def list_users(db: DatabaseService = Depends("database")):
    users = db.get_all_users()
    return {"users": users, "count": len(users)}

@app.get("/health")
def health_check(request):
    return {
        "status": "healthy",
        "c_acceleration": app.has_c_acceleration(),
        "jemalloc": app.has_jemalloc(),
        "background_tasks": app.background_tasks_enabled(),
        "dependency_injection": app.di_enabled(),
        "timestamp": time.time()
    }

if __name__ == "__main__":
    print("🚀 Starting Catzilla with all features enabled...")
    print(f"✅ C Acceleration: {app.has_c_acceleration()}")
    print(f"✅ jemalloc: {app.has_jemalloc()}")
    print(f"✅ Background Tasks: {app.background_tasks_enabled()}")
    print(f"✅ Dependency Injection: {app.di_enabled()}")

    app.listen(host="0.0.0.0", port=8000)
```

## Testing Your App

```bash
# Test basic endpoint
curl http://localhost:8000/

# Create a user (with validation)
curl -X POST http://localhost:8000/users \
  -H "Content-Type: application/json" \
  -d '{"name": "Alice", "email": "alice@example.com", "age": 30}'

# Get user
curl http://localhost:8000/users/1

# List all users
curl http://localhost:8000/users

# Check health
curl http://localhost:8000/health
```

## Test Your API

### Using curl

```bash
# Test GET endpoint
curl http://localhost:8000/users/123

# Test POST endpoint
curl -X POST "http://localhost:8000/users/" \
     -H "Content-Type: application/json" \
     -d '{"id": 1, "name": "Alice", "email": "alice@example.com", "age": 30}'
```

### Using Python requests

```python
import requests

# Test GET
response = requests.get("http://localhost:8000/users/123")
print(response.json())

# Test POST
user_data = {
    "id": 1,
    "name": "Alice",
    "email": "alice@example.com",
    "age": 30
}
response = requests.post("http://localhost:8000/users/", json=user_data)
print(response.json())
```

## Adding Background Tasks

Catzilla's revolutionary background task system makes async processing simple:

```python
from catzilla import Catzilla
from catzilla.background_tasks import TaskPriority

app = Catzilla()

# Enable background tasks
app.enable_background_tasks()

def send_notification(user_id: int, message: str):
    # Simulate sending notification
    print(f"Sending notification to user {user_id}: {message}")
    return f"Notification sent to user {user_id}"

@app.post("/notify/{user_id}")
def notify_user(user_id: int, message: str):
    # Add background task
    task_result = app.add_task(
        send_notification,
        user_id,
        message,
        priority=TaskPriority.HIGH
    )

    return {
        "message": "Notification queued",
        "task_id": task_result.task_id,
        "user_id": user_id
    }

if __name__ == "__main__":
    app.listen(host="0.0.0.0", port=8000)
```

## Static File Serving

Serve static files efficiently:

```python
from catzilla import Catzilla

app = Catzilla()

# Mount static files
app.mount_static("/static", directory="./static")

@app.get("/")
def read_root():
    return {"message": "Static files available at /static/"}

if __name__ == "__main__":
    app.listen(host="0.0.0.0", port=8000)
```

Create a `static` directory and add some files:

```bash
mkdir static
echo "<h1>Hello from Static!</h1>" > static/index.html
```

Now visit http://localhost:8000/static/index.html

## Performance Features

### Enable Memory Optimization

```python
from catzilla import Catzilla

# Enable jemalloc for 30% memory reduction
app = Catzilla(enable_jemalloc=True)
```

### Enable C-Acceleration

```python
from catzilla import Catzilla

app = Catzilla(
    enable_jemalloc=True,
    c_acceleration=True,  # Enable C-accelerated routing
    router_type="c_accelerated"  # Use C router
)
```

## What's Next?

Now that you have a basic Catzilla app running, explore these guides:

### Essential Topics
- **[Tutorial](tutorial/index)** - Complete step-by-step tutorial
- **[Request and Response Handling](tutorial/request-response)** - Learn request/response patterns
- **[Auto-Validation](validation/index)** - Master Catzilla's validation system

### Advanced Features
- **[Background Tasks](background-tasks/index)** - Build scalable async applications
- **[Dependency Injection](dependency-injection/index)** - Organize your code with DI
- **[Middleware](middleware/index)** - Add custom middleware

### Production
- **[Performance Optimization](performance/index)** - Maximize your app's speed
- **[Deployment](deployment/index)** - Deploy to production

## Performance Tip

For maximum performance in production, ensure C-acceleration is enabled:

```python
from catzilla import Catzilla

app = Catzilla(
    enable_jemalloc=True,
    c_acceleration=True,
    router_type="c_accelerated",
    enable_background_tasks=True
)
```

This configuration provides:
- **100x faster validation**
- **30% memory reduction**
- **C-speed routing**
- **Lock-free background tasks**

Congratulations! You now have a high-performance Catzilla application running. Ready to build something amazing? 🚀

---

*Join our [Discord community](https://discord.gg/catzilla) for help and discussions*
