Real-World Recipes
==================

This section provides practical, production-ready patterns and recipes for common web development scenarios using Catzilla. These examples are based on real-world use cases and demonstrate best practices.

Authentication Patterns
-----------------------

JWT Authentication
~~~~~~~~~~~~~~~~~~

Implement secure JWT-based authentication:

.. code-block:: python

   from catzilla import Catzilla, Request, Response, JSONResponse, BaseModel, Field
   import time
   import hashlib
   import hmac
   import secrets
   import json
   import base64
   from typing import Optional, List, Dict, Any
   from datetime import datetime, timedelta
   from dataclasses import dataclass
   from enum import Enum
   import uuid

   app = Catzilla(production=False, show_banner=True, log_requests=True)

   # Configuration
   AUTH_CONFIG = {
       "jwt_secret": "your-super-secret-jwt-key-change-in-production",
       "jwt_algorithm": "HS256",
       "jwt_expiry_hours": 24,
       "password_salt_rounds": 12,
       "max_login_attempts": 5,
       "lockout_duration_minutes": 15
   }

   # User roles
   class UserRole(str, Enum):
       ADMIN = "admin"
       USER = "user"
       READONLY = "readonly"

   # Data models
   class LoginModel(BaseModel):
       email: str = Field(regex=r'^[^@]+@[^@]+\.[^@]+$', description="Email address")
       password: str = Field(min_length=6, description="Password")

   class RegisterModel(BaseModel):
       name: str = Field(min_length=2, max_length=50, description="Full name")
       email: str = Field(regex=r'^[^@]+@[^@]+\.[^@]+$', description="Email address")
       password: str = Field(min_length=6, description="Password")
       role: UserRole = UserRole.USER

   @dataclass
   class User:
       id: str
       name: str
       email: str
       password_hash: str
       role: UserRole
       is_active: bool = True
       login_attempts: int = 0
       locked_until: Optional[datetime] = None
       created_at: datetime = None

       def __post_init__(self):
           if self.created_at is None:
               self.created_at = datetime.now()

   # In-memory storage
   users_db: Dict[str, User] = {}

   # Utility functions
   def hash_password(password: str) -> str:
       """Hash password with salt"""
       salt = secrets.token_hex(16)
       password_hash = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
       return f"{salt}:{password_hash.hex()}"

   def verify_password(password: str, password_hash: str) -> bool:
       """Verify password against hash"""
       try:
           salt, hash_hex = password_hash.split(':')
           password_hash_check = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
           return hmac.compare_digest(hash_hex, password_hash_check.hex())
       except ValueError:
           return False

   def generate_jwt(user: User) -> str:
       """Generate JWT token for user (simplified for demo)"""
       payload = {
           'user_id': user.id,
           'email': user.email,
           'role': user.role.value,
           'exp': (datetime.utcnow() + timedelta(hours=AUTH_CONFIG["jwt_expiry_hours"])).timestamp(),
           'iat': datetime.utcnow().timestamp()
       }
       return base64.b64encode(json.dumps(payload).encode()).decode()

   def verify_jwt(token: str) -> Optional[Dict[str, Any]]:
       """Verify and decode JWT token (simplified for demo)"""
       try:
           payload = json.loads(base64.b64decode(token.encode()).decode())
           if payload.get('exp') and payload['exp'] < datetime.utcnow().timestamp():
               return None
           return payload
       except:
           return None

   # Authentication middleware
   @app.middleware(priority=20, pre_route=True, name="authentication")
   def authentication_middleware(request: Request) -> Optional[Response]:
       """JWT authentication middleware"""
       # Public paths that don't require auth
       public_paths = {'/', '/auth/login', '/auth/register', '/health'}

       if request.path in public_paths:
           return None

       # Try JWT authentication
       auth_header = request.headers.get('Authorization', '')
       if auth_header.startswith('Bearer '):
           token = auth_header[7:]
           payload = verify_jwt(token)
           if payload:
               user_id = payload['user_id']
               if user_id in users_db:
                   user = users_db[user_id]
                   if user.is_active:
                       if not hasattr(request, 'context'):
                           request.context = {}
                       request.context['user'] = user
                       request.context['auth_payload'] = payload
                       return None

           return JSONResponse({"error": "Invalid or expired token"}, status_code=401)

       return JSONResponse({"error": "Authentication required"}, status_code=401)

   # Authentication endpoints
   @app.post("/auth/register")
   def register(request: Request, user_data: RegisterModel) -> Response:
       """Register new user"""
       # Check if email already exists
       for user in users_db.values():
           if user.email == user_data.email:
               return JSONResponse({"error": "Email already registered"}, status_code=409)

       # Create new user
       user_id = str(uuid.uuid4())
       password_hash = hash_password(user_data.password)

       user = User(
           id=user_id,
           name=user_data.name,
           email=user_data.email,
           password_hash=password_hash,
           role=user_data.role
       )

       users_db[user_id] = user

       # Generate JWT token
       token = generate_jwt(user)

       return JSONResponse({
           "user": {
               "id": user.id,
               "name": user.name,
               "email": user.email,
               "role": user.role.value
           },
           "token": token,
           "expires_in": AUTH_CONFIG["jwt_expiry_hours"] * 3600
       }, status_code=201)

   @app.post("/auth/login")
   def login(request: Request, login_data: LoginModel) -> Response:
       """Login user"""
       # Find user by email
       user = None
       for u in users_db.values():
           if u.email == login_data.email:
               user = u
               break

       if not user:
           return JSONResponse({"error": "Invalid email or password"}, status_code=401)

       # Check if account is locked
       if user.locked_until and datetime.now() < user.locked_until:
           minutes_left = (user.locked_until - datetime.now()).total_seconds() / 60
           return JSONResponse(
               {"error": f"Account locked. Try again in {int(minutes_left)} minutes"},
               status_code=423
           )

       # Verify password
       if not verify_password(login_data.password, user.password_hash):
           user.login_attempts += 1
           if user.login_attempts >= AUTH_CONFIG["max_login_attempts"]:
               user.locked_until = datetime.now() + timedelta(minutes=AUTH_CONFIG["lockout_duration_minutes"])
               return JSONResponse(
                   {"error": f"Too many failed attempts. Account locked for {AUTH_CONFIG['lockout_duration_minutes']} minutes"},
                   status_code=423
               )
           return JSONResponse({"error": "Invalid email or password"}, status_code=401)

       # Check if account is active
       if not user.is_active:
           return JSONResponse({"error": "Account deactivated"}, status_code=403)

       # Reset login attempts on successful login
       user.login_attempts = 0
       user.locked_until = None

       # Generate JWT token
       token = generate_jwt(user)

       return JSONResponse({
           "user": {
               "id": user.id,
               "name": user.name,
               "email": user.email,
               "role": user.role.value
           },
           "token": token,
           "expires_in": AUTH_CONFIG["jwt_expiry_hours"] * 3600
       })

   @app.get("/auth/profile")
   def get_profile(request: Request) -> Response:
       """Get user profile"""
       user = getattr(request, 'context', {}).get('user')
       return JSONResponse({
           "id": user.id,
           "name": user.name,
           "email": user.email,
           "role": user.role.value,
           "is_active": user.is_active,
           "created_at": user.created_at.isoformat()
       })

   # Protected endpoint example
   @app.get("/api/protected")
   def protected_endpoint(request: Request) -> Response:
       """Protected endpoint requiring authentication"""
       user = getattr(request, 'context', {}).get('user')
       return JSONResponse({
           "message": "Access granted to protected resource",
           "user": {
               "id": user.id,
               "name": user.name,
               "role": user.role.value
           }
       })

   if __name__ == "__main__":
       # Seed admin user for testing
       admin_id = str(uuid.uuid4())
       admin_user = User(
           id=admin_id,
           name="System Admin",
           email="admin@example.com",
           password_hash=hash_password("admin123"),
           role=UserRole.ADMIN
       )
       users_db[admin_id] = admin_user

       print("🔐 Admin user created:")
       print("   Email: admin@example.com")
       print("   Password: admin123")

       app.listen(port=8000)

Session-Based Authentication
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Alternative session-based authentication:

.. code-block:: python

   from catzilla import Catzilla, Request, Response, JSONResponse, BaseModel, Field
   import uuid
   import time
   from datetime import datetime, timedelta
   from typing import Optional, Dict

   app = Catzilla(production=False, show_banner=True, log_requests=True)

   # Session storage (use Redis in production)
   sessions: Dict[str, Dict] = {}

   class LoginModel(BaseModel):
       username: str = Field(min_length=3, max_length=20, description="Username")
       password: str = Field(min_length=6, description="Password")

   class SessionManager:
       def __init__(self, session_timeout_minutes: int = 30):
           self.session_timeout = timedelta(minutes=session_timeout_minutes)

       def create_session(self, user_data: dict) -> str:
           """Create new user session"""
           session_id = str(uuid.uuid4())

           sessions[session_id] = {
               "user": user_data,
               "created_at": datetime.utcnow(),
               "last_accessed": datetime.utcnow()
           }

           return session_id

       def get_session(self, session_id: str) -> Optional[dict]:
           """Get user from session"""
           session = sessions.get(session_id)

           if not session:
               return None

           # Check if session expired
           if datetime.utcnow() - session["last_accessed"] > self.session_timeout:
               del sessions[session_id]
               return None

           # Update last accessed time
           session["last_accessed"] = datetime.utcnow()

           return session["user"]

       def destroy_session(self, session_id: str):
           """Destroy user session"""
           sessions.pop(session_id, None)

   session_manager = SessionManager()

   # Mock user database
   users_db = {
       "admin": {"username": "admin", "password": "admin123", "email": "admin@example.com"},
       "user": {"username": "user", "password": "user123", "email": "user@example.com"}
   }

   def authenticate_user(username: str, password: str) -> Optional[dict]:
       """Simple authentication"""
       user_data = users_db.get(username)
       if user_data and user_data["password"] == password:
           return {"username": user_data["username"], "email": user_data["email"]}
       return None

   @app.post("/session-login")
   def session_login(request: Request, login_data: LoginModel) -> Response:
       """Session-based login"""
       user = authenticate_user(login_data.username, login_data.password)
       if not user:
           return JSONResponse({"error": "Invalid credentials"}, status_code=401)

       session_id = session_manager.create_session(user)

       response = JSONResponse({
           "message": "Login successful",
           "user": user
       })

       # Set session cookie (simplified - in production use secure settings)
       response.headers["Set-Cookie"] = f"session_id={session_id}; Path=/; Max-Age=1800; HttpOnly"

       return response

   @app.post("/session-logout")
   def session_logout(request: Request) -> Response:
       """Session-based logout"""
       # Get session ID from cookie header
       cookie_header = request.headers.get("Cookie", "")
       session_id = None

       if cookie_header:
           # Simple cookie parsing (in production use proper cookie parser)
           for part in cookie_header.split(";"):
               if "session_id=" in part:
                   session_id = part.split("session_id=")[1].strip()
                   break

       if session_id:
           session_manager.destroy_session(session_id)

       response = JSONResponse({"message": "Logout successful"})
       response.headers["Set-Cookie"] = "session_id=; Path=/; Max-Age=0; HttpOnly"

       return response

   @app.get("/session-profile")
   def session_profile(request: Request) -> Response:
       """Get profile using session"""
       # Get session ID from cookie
       cookie_header = request.headers.get("Cookie", "")
       session_id = None

       if cookie_header:
           for part in cookie_header.split(";"):
               if "session_id=" in part:
                   session_id = part.split("session_id=")[1].strip()
                   break

       if not session_id:
           return JSONResponse({"error": "No session found"}, status_code=401)

       user = session_manager.get_session(session_id)
       if not user:
           return JSONResponse({"error": "Invalid or expired session"}, status_code=401)

       return JSONResponse({"user": user, "session_active": True})

   if __name__ == "__main__":
       app.listen(port=8000)

REST API Patterns
-----------------

RESTful Resource Management
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Complete CRUD operations with validation:

.. code-block:: python

   from catzilla import Catzilla, Request, Response, JSONResponse, BaseModel, Field, Query, Path
   from typing import Optional, List, Dict, Any
   from datetime import datetime
   from dataclasses import dataclass
   from enum import Enum
   import uuid

   app = Catzilla(production=False, show_banner=True, log_requests=True)

   # Data models
   class UserStatus(str, Enum):
       ACTIVE = "active"
       INACTIVE = "inactive"
       SUSPENDED = "suspended"

   class TaskCreate(BaseModel):
       title: str = Field(min_length=1, max_length=200, description="Task title")
       description: Optional[str] = Field(None, max_length=1000, description="Task description")
       priority: int = Field(1, ge=1, le=5, description="Priority level")
       due_date: Optional[str] = None

   class TaskUpdate(BaseModel):
       title: Optional[str] = Field(None, min_length=1, max_length=200)
       description: Optional[str] = Field(None, max_length=1000)
       priority: Optional[int] = Field(None, ge=1, le=5)
       due_date: Optional[str] = None
       completed: Optional[bool] = None

   @dataclass
   class Task:
       id: str
       title: str
       description: Optional[str]
       priority: int
       due_date: Optional[str]
       completed: bool = False
       created_at: datetime = None
       updated_at: datetime = None

       def __post_init__(self):
           if self.created_at is None:
               self.created_at = datetime.utcnow()
           if self.updated_at is None:
               self.updated_at = datetime.utcnow()

   # Mock database
   tasks_db: Dict[str, Task] = {}

   class TaskService:
       @staticmethod
       def create_task(task_data: TaskCreate) -> Task:
           """Create new task"""
           task_id = str(uuid.uuid4())
           task = Task(
               id=task_id,
               title=task_data.title,
               description=task_data.description,
               priority=task_data.priority,
               due_date=task_data.due_date
           )
           tasks_db[task_id] = task
           return task

       @staticmethod
       def get_task(task_id: str) -> Optional[Task]:
           """Get task by ID"""
           return tasks_db.get(task_id)

       @staticmethod
       def update_task(task_id: str, task_data: TaskUpdate) -> Optional[Task]:
           """Update existing task"""
           task = tasks_db.get(task_id)
           if not task:
               return None

           if task_data.title is not None:
               task.title = task_data.title
           if task_data.description is not None:
               task.description = task_data.description
           if task_data.priority is not None:
               task.priority = task_data.priority
           if task_data.due_date is not None:
               task.due_date = task_data.due_date
           if task_data.completed is not None:
               task.completed = task_data.completed

           task.updated_at = datetime.utcnow()
           return task

       @staticmethod
       def delete_task(task_id: str) -> bool:
           """Delete task"""
           return tasks_db.pop(task_id, None) is not None

       @staticmethod
       def list_tasks(skip: int = 0, limit: int = 100, completed: Optional[bool] = None) -> List[Task]:
           """List tasks with pagination and filtering"""
           all_tasks = list(tasks_db.values())

           if completed is not None:
               all_tasks = [t for t in all_tasks if t.completed == completed]

           all_tasks.sort(key=lambda x: x.created_at, reverse=True)
           return all_tasks[skip:skip + limit]

   def serialize_task(task: Task) -> Dict[str, Any]:
       """Serialize task for JSON response"""
       return {
           "id": task.id,
           "title": task.title,
           "description": task.description,
           "priority": task.priority,
           "due_date": task.due_date,
           "completed": task.completed,
           "created_at": task.created_at.isoformat(),
           "updated_at": task.updated_at.isoformat()
       }

   # REST API endpoints
   @app.get("/api/tasks")
   def list_tasks(
       request: Request,
       skip: int = Query(0, ge=0, description="Number of tasks to skip"),
       limit: int = Query(10, ge=1, le=100, description="Number of tasks to return"),
       completed: Optional[bool] = Query(None, description="Filter by completion status")
   ) -> Response:
       """List all tasks with pagination and filtering"""
       tasks = TaskService.list_tasks(skip=skip, limit=limit, completed=completed)

       return JSONResponse({
           "tasks": [serialize_task(task) for task in tasks],
           "pagination": {
               "skip": skip,
               "limit": limit,
               "total": len(tasks_db),
               "returned": len(tasks)
           },
           "filters": {"completed": completed}
       })

   @app.post("/api/tasks")
   def create_task(request: Request, task: TaskCreate) -> Response:
       """Create a new task"""
       new_task = TaskService.create_task(task)
       return JSONResponse(
           {"task": serialize_task(new_task), "message": "Task created successfully"},
           status_code=201
       )

   @app.get("/api/tasks/{task_id}")
   def get_task(request: Request, task_id: str = Path(..., description="Task ID")) -> Response:
       """Get a specific task by ID"""
       task = TaskService.get_task(task_id)

       if not task:
           return JSONResponse({"error": "Task not found"}, status_code=404)

       return JSONResponse({"task": serialize_task(task)})

   @app.put("/api/tasks/{task_id}")
   def update_task(
       request: Request,
       task_id: str = Path(..., description="Task ID"),
       task_update: TaskUpdate = None
   ) -> Response:
       """Update an existing task"""
       updated_task = TaskService.update_task(task_id, task_update)

       if not updated_task:
           return JSONResponse({"error": "Task not found"}, status_code=404)

       return JSONResponse({
           "task": serialize_task(updated_task),
           "message": "Task updated successfully"
       })

   @app.delete("/api/tasks/{task_id}")
   def delete_task(request: Request, task_id: str = Path(..., description="Task ID")) -> Response:
       """Delete a task"""
       deleted = TaskService.delete_task(task_id)

       if not deleted:
           return JSONResponse({"error": "Task not found"}, status_code=404)

       return JSONResponse({"message": "Task deleted successfully"})

   # Bulk operations
   @app.post("/api/tasks/bulk")
   def bulk_create_tasks(request: Request, tasks: List[TaskCreate]) -> Response:
       """Create multiple tasks"""
       if len(tasks) > 50:
           return JSONResponse({"error": "Maximum 50 tasks per bulk operation"}, status_code=400)

       created_tasks = []
       errors = []

       for i, task_data in enumerate(tasks):
           try:
               new_task = TaskService.create_task(task_data)
               created_tasks.append(serialize_task(new_task))
           except Exception as e:
               errors.append({"index": i, "error": str(e)})

       return JSONResponse({
           "created": created_tasks,
           "errors": errors,
           "summary": {
               "total_submitted": len(tasks),
               "successful": len(created_tasks),
               "failed": len(errors)
           }
       })

   if __name__ == "__main__":
       app.listen(port=8000)

API Versioning
~~~~~~~~~~~~~~

Implement API versioning strategies:

.. code-block:: python

   from catzilla import Catzilla, Request, Response, JSONResponse, Path
   from catzilla.router import RouterGroup

   app = Catzilla(production=False, show_banner=True, log_requests=True)

   # URL path versioning with RouterGroups
   v1_router = RouterGroup(prefix="/api/v1")
   v2_router = RouterGroup(prefix="/api/v2")

   @v1_router.get("/users/{user_id}")
   def get_user_v1(request: Request, user_id: str = Path(..., description="User ID")) -> Response:
       """Version 1 of user API"""
       return JSONResponse({
           "id": user_id,
           "name": f"User {user_id}",
           "version": "1.0"
       })

   @v2_router.get("/users/{user_id}")
   def get_user_v2(request: Request, user_id: str = Path(..., description="User ID")) -> Response:
       """Version 2 of user API with additional fields"""
       return JSONResponse({
           "id": user_id,
           "name": f"User {user_id}",
           "email": f"user{user_id}@example.com",
           "profile": {
               "created_at": "2023-01-01",
               "last_login": "2024-01-01"
           },
           "version": "2.0"
       })

   # Header-based versioning
   def get_api_version(request: Request) -> str:
       """Extract API version from headers"""
       return request.headers.get("API-Version", "v1")

   @app.get("/api/users/{user_id}")
   def get_user_versioned(request: Request, user_id: str = Path(..., description="User ID")) -> Response:
       """Versioned user endpoint using headers"""
       version = get_api_version(request)

       base_data = {
           "id": user_id,
           "name": f"User {user_id}"
       }

       if version == "v2":
           return JSONResponse({
               **base_data,
               "email": f"user{user_id}@example.com",
               "profile": {
                   "created_at": "2023-01-01",
                   "last_login": "2024-01-01"
               },
               "version": "2.0"
           })
       else:
           return JSONResponse({
               **base_data,
               "version": "1.0"
           })

   # Content negotiation versioning
   @app.get("/api/data/{item_id}")
   def get_data_with_content_negotiation(request: Request, item_id: str = Path(..., description="Item ID")) -> Response:
       """API versioning through content negotiation"""
       accept_header = request.headers.get("Accept", "application/json")

       base_data = {
           "id": item_id,
           "name": f"Item {item_id}"
       }

       if "application/vnd.api.v2+json" in accept_header:
           # Version 2 format
           return JSONResponse({
               "data": {
                   **base_data,
                   "metadata": {
                       "created_at": "2023-01-01",
                       "updated_at": "2024-01-01"
                   }
               },
               "version": "2.0"
           })
       else:
           # Version 1 format (default)
           return JSONResponse({
               **base_data,
               "version": "1.0"
           })

   # Register router groups
   app.include_routes(v1_router)
   app.include_routes(v2_router)

   if __name__ == "__main__":
       app.listen(port=8000)

Error Handling Patterns
-----------------------

Comprehensive Error Handling
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Structured error responses and logging:

.. code-block:: python

   from catzilla import Catzilla, Request, Response, JSONResponse, BaseModel, Field, Path
   import uuid
   import time
   from enum import Enum
   from typing import Optional, Dict, Any

   app = Catzilla(production=False, show_banner=True, log_requests=True)

   class ErrorCode(Enum):
       VALIDATION_ERROR = "VALIDATION_ERROR"
       NOT_FOUND = "NOT_FOUND"
       UNAUTHORIZED = "UNAUTHORIZED"
       FORBIDDEN = "FORBIDDEN"
       INTERNAL_ERROR = "INTERNAL_ERROR"
       RATE_LIMITED = "RATE_LIMITED"

   class APIError(Exception):
       def __init__(self, code: ErrorCode, message: str, details: dict = None, status_code: int = 400):
           self.code = code
           self.message = message
           self.details = details or {}
           self.status_code = status_code
           super().__init__(self.message)

   class UserCreate(BaseModel):
       name: str = Field(min_length=2, max_length=50, description="User name")
       email: str = Field(regex=r'^[^@]+@[^@]+\.[^@]+$', description="Email address")

   # Custom exception handlers
   def validation_error_handler(request: Request, exc: Exception) -> Response:
       """Handle validation errors"""
       return JSONResponse({
           "error": "validation_error",
           "message": str(exc),
           "status_code": 422,
           "request_id": f"req_{int(time.time() * 1000)}"
       }, status_code=422)

   def api_error_handler(request: Request, exc: APIError) -> Response:
       """Handle custom API errors"""
       return JSONResponse({
           "error": exc.code.value,
           "message": exc.message,
           "details": exc.details,
           "status_code": exc.status_code,
           "request_id": f"req_{int(time.time() * 1000)}"
       }, status_code=exc.status_code)

   # Register exception handlers
   app.set_exception_handler(APIError, api_error_handler)
   app.set_exception_handler(ValueError, validation_error_handler)

   # Custom 404 handler
   @app.set_not_found_handler
   def custom_404_handler(request: Request) -> Response:
       """Custom 404 handler"""
       return JSONResponse({
           "error": "not_found",
           "message": f"Endpoint {request.path} not found",
           "method": request.method,
           "path": request.path,
           "available_endpoints": [
               "/api/users/{user_id}",
               "/api/validation-error",
               "/api/server-error",
               "/api/protected"
           ]
       }, status_code=404)

   # Custom 500 handler
   @app.set_internal_error_handler
   def custom_500_handler(request: Request, exc: Exception) -> Response:
       """Custom internal server error handler"""
       if app.production:
           return JSONResponse({
               "error": "internal_server_error",
               "message": "An internal error occurred",
               "status_code": 500,
               "request_id": f"req_{int(time.time() * 1000)}"
           }, status_code=500)
       else:
           return JSONResponse({
               "error": "internal_server_error",
               "message": str(exc),
               "type": type(exc).__name__,
               "status_code": 500,
               "path": request.path,
               "method": request.method
           }, status_code=500)

   # Routes that demonstrate error handling
   @app.get("/api/users/{user_id}")
   def get_user(request: Request, user_id: str = Path(..., description="User ID")) -> Response:
       """Get user - demonstrates NotFoundError"""
       if user_id == "999":
           raise APIError(
               ErrorCode.NOT_FOUND,
               f"User {user_id} not found",
               {"resource": "User", "resource_id": user_id},
               status_code=404
           )

       return JSONResponse({
           "id": user_id,
           "name": f"User {user_id}",
           "email": f"user{user_id}@example.com"
       })

   @app.post("/api/users")
   def create_user(request: Request, user_data: UserCreate) -> Response:
       """Create user - demonstrates auto-validation with BaseModel"""
       return JSONResponse({
           "message": "User created successfully",
           "user": {
               "id": str(uuid.uuid4()),
               "name": user_data.name,
               "email": user_data.email
           }
       }, status_code=201)

   @app.get("/api/validation-error")
   def trigger_validation_error(request: Request) -> Response:
       """Endpoint to test validation error handling"""
       raise APIError(
           ErrorCode.VALIDATION_ERROR,
           "This is a test validation error",
           {"field": "test_field"},
           status_code=422
       )

   @app.get("/api/server-error")
   def trigger_server_error(request: Request) -> Response:
       """Endpoint to test server error handling"""
       result = 1 / 0  # This will trigger a ZeroDivisionError
       return JSONResponse({"result": result})

   @app.get("/api/protected")
   def protected_endpoint(request: Request) -> Response:
       """Protected endpoint - demonstrates authentication error"""
       auth_header = request.headers.get("Authorization", "")

       if not auth_header.startswith("Bearer "):
           raise APIError(
               ErrorCode.UNAUTHORIZED,
               "Authentication required",
               {"required_header": "Authorization: Bearer <token>"},
               status_code=401
           )

       token = auth_header[7:]
       if token != "valid-token":
           raise APIError(
               ErrorCode.UNAUTHORIZED,
               "Invalid token",
               {"token": token},
               status_code=401
           )

       return JSONResponse({
           "message": "Access granted to protected resource",
           "user": "authenticated_user"
       })

   @app.get("/health")
   def health_check(request: Request) -> Response:
       """Health check with error handling info"""
       return JSONResponse({
           "status": "healthy",
           "error_handling": {
               "production_mode": app.production,
               "custom_handlers": ["APIError", "ValueError"],
               "custom_404": True,
               "custom_500": True
           }
       })

   if __name__ == "__main__":
       app.listen(port=8000)

Rate Limiting and Throttling
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Implement rate limiting for API protection:

.. code-block:: python

   from catzilla import Catzilla, Request, Response, JSONResponse, Path
   import time
   from collections import defaultdict
   from typing import Dict, Tuple, Optional

   app = Catzilla(production=False, show_banner=True, log_requests=True)

   class RateLimiter:
       def __init__(self):
           self.requests: Dict[str, list] = defaultdict(list)
           self.limits = {
               "default": {"count": 100, "window": 3600},  # 100 requests per hour
               "premium": {"count": 1000, "window": 3600},  # 1000 requests per hour
               "admin": {"count": 10000, "window": 3600}    # 10000 requests per hour
           }

       def is_allowed(self, identifier: str, tier: str = "default") -> Tuple[bool, dict]:
           """Check if request is allowed"""
           now = time.time()
           limit_config = self.limits.get(tier, self.limits["default"])
           window_start = now - limit_config["window"]

           # Clean old requests
           self.requests[identifier] = [
               req_time for req_time in self.requests[identifier]
               if req_time > window_start
           ]

           current_count = len(self.requests[identifier])
           allowed = current_count < limit_config["count"]

           if allowed:
               self.requests[identifier].append(now)

           return allowed, {
               "limit": limit_config["count"],
               "remaining": limit_config["count"] - current_count - (1 if allowed else 0),
               "reset_time": window_start + limit_config["window"],
               "window": limit_config["window"]
           }

   rate_limiter = RateLimiter()

   def rate_limit_middleware(tier: str = "default"):
       """Rate limiting middleware factory"""
       def middleware_func(request: Request) -> Optional[Response]:
           # Identify client (could use IP, user ID, API key, etc.)
           client_id = request.headers.get("X-Forwarded-For", "127.0.0.1")
           api_key = request.headers.get("X-API-Key")

           # Determine tier based on API key
           if api_key == "premium-key":
               tier = "premium"
           elif api_key == "admin-key":
               tier = "admin"
           else:
               tier = "default"

           # Check rate limit
           allowed, limit_info = rate_limiter.is_allowed(client_id, tier)

           if not allowed:
               return JSONResponse({
                   "error": "Rate limit exceeded",
                   "limit": limit_info["limit"],
                   "window": limit_info["window"],
                   "retry_after": int(limit_info["reset_time"] - time.time())
               }, status_code=429, headers={
                   "X-RateLimit-Limit": str(limit_info["limit"]),
                   "X-RateLimit-Remaining": "0",
                   "X-RateLimit-Reset": str(int(limit_info["reset_time"])),
                   "Retry-After": str(int(limit_info["reset_time"] - time.time()))
               })

           # Add rate limit info to request context
           if not hasattr(request, 'context'):
               request.context = {}
           request.context['rate_limit'] = limit_info

           return None  # Continue to next middleware/handler

       return middleware_func

   # Apply rate limiting to different endpoint groups
   @app.get("/api/public/data", middleware=[rate_limit_middleware("default")])
   def public_data_endpoint(request: Request) -> Response:
       """Public endpoint with default rate limiting"""
       rate_limit = getattr(request, 'context', {}).get('rate_limit', {})
       response = JSONResponse({"data": "public information"})

       # Add rate limit headers to response
       if rate_limit:
           response.headers.update({
               "X-RateLimit-Limit": str(rate_limit["limit"]),
               "X-RateLimit-Remaining": str(rate_limit["remaining"]),
               "X-RateLimit-Reset": str(int(rate_limit["reset_time"]))
           })

       return response

   @app.get("/api/premium/analytics", middleware=[rate_limit_middleware("premium")])
   def premium_analytics_endpoint(request: Request) -> Response:
       """Premium endpoint with higher rate limits"""
       rate_limit = getattr(request, 'context', {}).get('rate_limit', {})
       response = JSONResponse({"analytics": "premium data"})

       if rate_limit:
           response.headers.update({
               "X-RateLimit-Limit": str(rate_limit["limit"]),
               "X-RateLimit-Remaining": str(rate_limit["remaining"]),
               "X-RateLimit-Reset": str(int(rate_limit["reset_time"]))
           })

       return response

   @app.get("/api/rate-limit-status")
   def rate_limit_status(request: Request) -> Response:
       """Get current rate limit status"""
       client_id = request.headers.get("X-Forwarded-For", "127.0.0.1")

       status = {}
       for tier_name, tier_config in rate_limiter.limits.items():
           allowed, limit_info = rate_limiter.is_allowed(client_id, tier_name)
           status[tier_name] = {
               "allowed": allowed,
               "limit": limit_info["limit"],
               "remaining": limit_info["remaining"],
               "reset_time": limit_info["reset_time"]
           }

       return JSONResponse({
           "client_id": client_id,
           "rate_limits": status
       })

   if __name__ == "__main__":
       app.listen(port=8000)

Performance Monitoring
~~~~~~~~~~~~~~~~~~~~~~

Monitor API performance and health:

.. code-block:: python

   from catzilla import Catzilla, Request, Response, JSONResponse
   import time
   import psutil
   from collections import deque
   from dataclasses import dataclass
   from typing import Dict, Any

   app = Catzilla(production=False, show_banner=True, log_requests=True)

   @dataclass
   class PerformanceMetrics:
       request_count: int = 0
       error_count: int = 0
       total_response_time: float = 0.0
       start_time: float = None

       def __post_init__(self):
           if self.start_time is None:
               self.start_time = time.time()

   class PerformanceMonitor:
       def __init__(self, max_samples: int = 1000):
           self.request_times = deque(maxlen=max_samples)
           self.metrics = PerformanceMetrics()

       def record_request(self, duration: float, status_code: int):
           """Record request metrics"""
           self.request_times.append(duration)
           self.metrics.request_count += 1
           self.metrics.total_response_time += duration

           if status_code >= 400:
               self.metrics.error_count += 1

       def get_metrics(self) -> Dict[str, Any]:
           """Get current performance metrics"""
           if not self.request_times:
               return {"message": "No requests recorded yet"}

           avg_response_time = sum(self.request_times) / len(self.request_times)
           uptime = time.time() - self.metrics.start_time

           # System metrics
           try:
               cpu_percent = psutil.cpu_percent(interval=None)
               memory = psutil.virtual_memory()
           except:
               cpu_percent = 0.0
               memory = None

           return {
               "performance": {
                   "avg_response_time_ms": round(avg_response_time * 1000, 3),
                   "total_requests": self.metrics.request_count,
                   "error_rate_percent": round((self.metrics.error_count / max(self.metrics.request_count, 1)) * 100, 2),
                   "requests_per_second": round(self.metrics.request_count / max(uptime, 1), 2),
                   "uptime_seconds": round(uptime, 2)
               },
               "system": {
                   "cpu_percent": cpu_percent,
                   "memory_percent": memory.percent if memory else 0,
                   "memory_available_mb": round(memory.available / 1024 / 1024, 2) if memory else 0
               }
           }

   performance_monitor = PerformanceMonitor()

   @app.middleware(priority=5, pre_route=True, name="performance_monitor")
   def performance_monitoring_middleware(request: Request) -> None:
       """Performance monitoring middleware"""
       if not hasattr(request, 'context'):
           request.context = {}
       request.context['start_time'] = time.time()
       return None

   @app.middleware(priority=5, pre_route=False, post_route=True, name="performance_recorder")
   def performance_recording_middleware(request: Request) -> None:
       """Record performance metrics after request"""
       start_time = getattr(request, 'context', {}).get('start_time')
       if start_time:
           duration = time.time() - start_time
           # Simulate status code (in real implementation, get from response)
           status_code = 200  # Default success
           performance_monitor.record_request(duration, status_code)
       return None

   @app.get("/api/health")
   def health_check(request: Request) -> Response:
       """Comprehensive health check endpoint"""
       metrics = performance_monitor.get_metrics()

       # Determine health status
       health_status = "healthy"
       issues = []

       if "performance" in metrics:
           if metrics["performance"]["avg_response_time_ms"] > 1000:
               issues.append("High response time")
               health_status = "degraded"

           if metrics["performance"]["error_rate_percent"] > 5:
               issues.append("High error rate")
               health_status = "degraded"

           if metrics["system"]["cpu_percent"] > 80:
               issues.append("High CPU usage")
               health_status = "degraded"

           if metrics["system"]["memory_percent"] > 85:
               issues.append("High memory usage")
               health_status = "degraded"

       return JSONResponse({
           "status": health_status,
           "timestamp": time.time(),
           "issues": issues,
           "metrics": metrics
       })

   @app.get("/api/metrics")
   def get_metrics(request: Request) -> Response:
       """Get detailed performance metrics"""
       return JSONResponse(performance_monitor.get_metrics())

   @app.get("/api/slow-endpoint")
   def slow_endpoint(request: Request) -> Response:
       """Endpoint that simulates slow processing"""
       time.sleep(0.5)  # Simulate slow operation
       return JSONResponse({"message": "This endpoint is intentionally slow"})

   @app.get("/api/error-endpoint")
   def error_endpoint(request: Request) -> Response:
       """Endpoint that returns an error for testing"""
       return JSONResponse({"error": "This is a test error"}, status_code=500)

   @app.get("/api/fast-endpoint")
   def fast_endpoint(request: Request) -> Response:
       """Fast endpoint for comparison"""
       return JSONResponse({"message": "This endpoint is fast", "timestamp": time.time()})

   if __name__ == "__main__":
       app.listen(port=8000)

These real-world recipes provide production-ready patterns that you can adapt and extend for your specific use cases with Catzilla. All examples use actual Catzilla APIs and demonstrate best practices for building high-performance web applications.
