Real-World Recipes
==================

This section provides practical, production-ready patterns and recipes for common web development scenarios using Catzilla. These examples are based on real-world use cases and demonstrate best practices.

Authentication Patterns
-----------------------

JWT Authentication
~~~~~~~~~~~~~~~~~~

Implement secure JWT-based authentication:

.. code-block:: python

   from catzilla import Catzilla, Request, JSONResponse, Depends
   import jwt
   from datetime import datetime, timedelta
   from passlib.context import CryptContext
   from typing import Optional

   app = Catzilla()

   # Configuration
   SECRET_KEY = "your-secret-key-change-in-production"
   ALGORITHM = "HS256"
   ACCESS_TOKEN_EXPIRE_MINUTES = 30

   # Password hashing
   pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

   # Mock user database
   users_db = {
       "admin": {
           "username": "admin",
           "email": "admin@example.com",
           "hashed_password": pwd_context.hash("admin123"),
           "is_active": True,
           "roles": ["admin"]
       },
       "user": {
           "username": "user",
           "email": "user@example.com",
           "hashed_password": pwd_context.hash("user123"),
           "is_active": True,
           "roles": ["user"]
       }
   }

   class TokenData:
       def __init__(self, username: str = None):
           self.username = username

   class User:
       def __init__(self, username: str, email: str, is_active: bool, roles: list):
           self.username = username
           self.email = email
           self.is_active = is_active
           self.roles = roles

   def verify_password(plain_password: str, hashed_password: str) -> bool:
       """Verify password against hash"""
       return pwd_context.verify(plain_password, hashed_password)

   def authenticate_user(username: str, password: str) -> Optional[User]:
       """Authenticate user credentials"""
       user_data = users_db.get(username)
       if not user_data:
           return None

       if not verify_password(password, user_data["hashed_password"]):
           return None

       return User(**user_data)

   def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
       """Create JWT access token"""
       to_encode = data.copy()

       if expires_delta:
           expire = datetime.utcnow() + expires_delta
       else:
           expire = datetime.utcnow() + timedelta(minutes=15)

       to_encode.update({"exp": expire})
       encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

       return encoded_jwt

   def get_current_user(request: Request) -> User:
       """Get current user from JWT token"""
       def credentials_error():
           return JSONResponse(
               {"error": "Could not validate credentials"},
               status_code=401,
               headers={"WWW-Authenticate": "Bearer"}
           )

       # Get token from Authorization header
       authorization = request.headers.get("Authorization")
       if not authorization:
           raise credentials_exception

       try:
           scheme, token = authorization.split()
           if scheme.lower() != "bearer":
               raise credentials_exception
       except ValueError:
           raise credentials_exception

       try:
           payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
           username: str = payload.get("sub")
           if username is None:
               raise credentials_exception

           token_data = TokenData(username=username)
       except jwt.PyJWTError:
           raise credentials_exception

       user_data = users_db.get(token_data.username)
       if user_data is None:
           raise credentials_exception

       return User(**user_data)

   def require_roles(required_roles: list):
       """Decorator to require specific roles"""
       def decorator(func):
           def wrapper(request: Request, *args, **kwargs):
               current_user = get_current_user(request)

               if not any(role in current_user.roles for role in required_roles):
                   return JSONResponse(
                       {"error": "Insufficient permissions"},
                       status_code=403
                   )

               return func(request, current_user=current_user, *args, **kwargs)
           return wrapper
       return decorator

   # Authentication endpoints
   @app.post("/login")
   async def login(request: Request):
       """User login endpoint"""
       form_data = await request.form()
       username = form_data.get("username")
       password = form_data.get("password")

       user = authenticate_user(username, password)
       if not user:
           return JSONResponse(
               {"error": "Incorrect username or password"},
               status_code=401,
               headers={"WWW-Authenticate": "Bearer"}
           )

       access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
       access_token = create_access_token(
           data={"sub": user.username},
           expires_delta=access_token_expires
       )

       return JSONResponse({
           "access_token": access_token,
           "token_type": "bearer",
           "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,
           "user": {
               "username": user.username,
               "email": user.email,
               "roles": user.roles
           }
       })

   @app.get("/me")
   def get_current_user_info(request: Request, current_user: User = Depends(get_current_user)):
       """Get current user information"""
       return JSONResponse({
           "username": current_user.username,
           "email": current_user.email,
           "is_active": current_user.is_active,
           "roles": current_user.roles
       })

   @app.get("/admin-only")
   @require_roles(["admin"])
   def admin_only_endpoint(request: Request, current_user: User):
       """Admin-only endpoint"""
       return JSONResponse({
           "message": "Welcome to admin area",
           "user": current_user.username,
           "admin_data": "sensitive admin information"
       })

Session-Based Authentication
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Alternative session-based authentication:

.. code-block:: python

   import uuid
   from datetime import datetime, timedelta

   # Session storage (use Redis in production)
   sessions = {}

   class SessionManager:
       def __init__(self, session_timeout_minutes: int = 30):
           self.session_timeout = timedelta(minutes=session_timeout_minutes)

       def create_session(self, user: User) -> str:
           """Create new user session"""
           session_id = str(uuid.uuid4())

           sessions[session_id] = {
               "user": user,
               "created_at": datetime.utcnow(),
               "last_accessed": datetime.utcnow()
           }

           return session_id

       def get_session(self, session_id: str) -> Optional[User]:
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

   @app.post("/session-login")
   async def session_login(request: Request):
       """Session-based login"""
       form_data = await request.form()
       username = form_data.get("username")
       password = form_data.get("password")

       user = authenticate_user(username, password)
       if not user:
           return JSONResponse({"error": "Invalid credentials"}, status_code=401)

       session_id = session_manager.create_session(user)

       response = JSONResponse({
           "message": "Login successful",
           "user": {"username": user.username, "email": user.email}
       })

       # Set session cookie
       response.set_cookie(
           "session_id",
           session_id,
           max_age=1800,  # 30 minutes
           httponly=True,
           secure=True,   # HTTPS only
           samesite="strict"
       )

       return response

   @app.post("/session-logout")
   def session_logout(request: Request):
       """Session-based logout"""
       session_id = request.cookies.get("session_id")

       if session_id:
           session_manager.destroy_session(session_id)

       response = JSONResponse({"message": "Logout successful"})
       response.delete_cookie("session_id")

       return response

REST API Patterns
-----------------

RESTful Resource Management
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Complete CRUD operations with validation:

.. code-block:: python

   from catzilla import BaseModel, Field, Path, Query
   from typing import Optional, List
   from datetime import datetime

   # Data models
   class TaskCreate(BaseModel):
       title: str = Field(..., min_length=1, max_length=200)
       description: Optional[str] = Field(None, max_length=1000)
       priority: int = Field(1, ge=1, le=5)
       due_date: Optional[str] = None

   class TaskUpdate(BaseModel):
       title: Optional[str] = Field(None, min_length=1, max_length=200)
       description: Optional[str] = Field(None, max_length=1000)
       priority: Optional[int] = Field(None, ge=1, le=5)
       due_date: Optional[str] = None
       completed: Optional[bool] = None

   class TaskResponse(BaseModel):
       id: int
       title: str
       description: Optional[str]
       priority: int
       due_date: Optional[str]
       completed: bool
       created_at: str
       updated_at: str

   # Mock database
   tasks_db = {}
   next_task_id = 1

   class TaskService:
       @staticmethod
       def create_task(task_data: TaskCreate) -> TaskResponse:
           """Create new task"""
           global next_task_id

           now = datetime.utcnow().isoformat()
           task = {
               "id": next_task_id,
               "title": task_data.title,
               "description": task_data.description,
               "priority": task_data.priority,
               "due_date": task_data.due_date,
               "completed": False,
               "created_at": now,
               "updated_at": now
           }

           tasks_db[next_task_id] = task
           next_task_id += 1

           return TaskResponse(**task)

       @staticmethod
       def get_task(task_id: int) -> Optional[TaskResponse]:
           """Get task by ID"""
           task = tasks_db.get(task_id)
           return TaskResponse(**task) if task else None

       @staticmethod
       def update_task(task_id: int, task_data: TaskUpdate) -> Optional[TaskResponse]:
           """Update existing task"""
           task = tasks_db.get(task_id)
           if not task:
               return None

           # Update fields
           update_data = {}
           if task_data.title is not None:
               update_data["title"] = task_data.title
           if task_data.description is not None:
               update_data["description"] = task_data.description
           if task_data.priority is not None:
               update_data["priority"] = task_data.priority
           if task_data.due_date is not None:
               update_data["due_date"] = task_data.due_date
           if task_data.completed is not None:
               update_data["completed"] = task_data.completed

           task.update(update_data)
           task["updated_at"] = datetime.utcnow().isoformat()

           return TaskResponse(**task)

       @staticmethod
       def delete_task(task_id: int) -> bool:
           """Delete task"""
           return tasks_db.pop(task_id, None) is not None

       @staticmethod
       def list_tasks(skip: int = 0, limit: int = 100, completed: Optional[bool] = None) -> List[TaskResponse]:
           """List tasks with pagination and filtering"""
           all_tasks = list(tasks_db.values())

           # Filter by completion status
           if completed is not None:
               all_tasks = [t for t in all_tasks if t["completed"] == completed]

           # Sort by created_at (newest first)
           all_tasks.sort(key=lambda x: x["created_at"], reverse=True)

           # Apply pagination
           paginated_tasks = all_tasks[skip:skip + limit]

           return [TaskResponse(**task) for task in paginated_tasks]

   # REST API endpoints
   @app.get("/api/tasks")
   def list_tasks(
       request: Request,
       skip: int = Query(0, ge=0, description="Number of tasks to skip"),
       limit: int = Query(10, ge=1, le=100, description="Number of tasks to return"),
       completed: Optional[bool] = Query(None, description="Filter by completion status")
   ):
       """List all tasks with pagination and filtering"""
       tasks = TaskService.list_tasks(skip=skip, limit=limit, completed=completed)

       return JSONResponse({
           "tasks": [{
               "id": task.id,
               "title": task.title,
               "description": task.description,
               "priority": task.priority,
               "due_date": task.due_date,
               "completed": task.completed,
               "created_at": task.created_at,
               "updated_at": task.updated_at
           } for task in tasks],
           "pagination": {
               "skip": skip,
               "limit": limit,
               "total": len(tasks_db),
               "returned": len(tasks)
           },
           "filters": {
               "completed": completed
           }
       })

   @app.post("/api/tasks")
   def create_task(request: Request, task: TaskCreate):
       """Create a new task"""
       try:
           new_task = TaskService.create_task(task)
           return JSONResponse(
               {"task": {
                   "id": new_task.id,
                   "title": new_task.title,
                   "description": new_task.description,
                   "priority": new_task.priority,
                   "due_date": new_task.due_date,
                   "completed": new_task.completed,
                   "created_at": new_task.created_at,
                   "updated_at": new_task.updated_at
               }, "message": "Task created successfully"},
               status_code=201
           )
       except Exception as e:
           return JSONResponse({"error": str(e)}, status_code=400)

   @app.get("/api/tasks/{task_id}")
   def get_task(request: Request, task_id: int = Path(..., ge=1, description="Task ID")):
       """Get a specific task by ID"""
       task = TaskService.get_task(task_id)

       if not task:
           return JSONResponse({"error": "Task not found"}, status_code=404)

       return JSONResponse({"task": {
           "id": task.id,
           "title": task.title,
           "description": task.description,
           "priority": task.priority,
           "due_date": task.due_date,
           "completed": task.completed,
           "created_at": task.created_at,
           "updated_at": task.updated_at
       }})

   @app.put("/api/tasks/{task_id}")
   def update_task(
       request: Request,
       task_update: TaskUpdate = None,
       task_id: int = Path(..., ge=1, description="Task ID")
   ):
       """Update an existing task"""
       updated_task = TaskService.update_task(task_id, task_update)

       if not updated_task:
           return JSONResponse({"error": "Task not found"}, status_code=404)

       return JSONResponse({
           "task": {
               "id": updated_task.id,
               "title": updated_task.title,
               "description": updated_task.description,
               "priority": updated_task.priority,
               "due_date": updated_task.due_date,
               "completed": updated_task.completed,
               "created_at": updated_task.created_at,
               "updated_at": updated_task.updated_at
           },
           "message": "Task updated successfully"
       })

   @app.delete("/api/tasks/{task_id}")
   def delete_task(request: Request, task_id: int = Path(..., ge=1, description="Task ID")):
       """Delete a task"""
       deleted = TaskService.delete_task(task_id)

       if not deleted:
           return JSONResponse({"error": "Task not found"}, status_code=404)

       return JSONResponse({"message": "Task deleted successfully"})

   # Bulk operations
   @app.post("/api/tasks/bulk")
   def bulk_create_tasks(request: Request, tasks: List[TaskCreate]):
       """Create multiple tasks"""
       if len(tasks) > 50:  # Limit bulk operations
           return JSONResponse({"error": "Maximum 50 tasks per bulk operation"}, status_code=400)

       created_tasks = []
       errors = []

       for i, task_data in enumerate(tasks):
           try:
               new_task = TaskService.create_task(task_data)
               created_tasks.append({
                   "id": new_task.id,
                   "title": new_task.title,
                   "description": new_task.description,
                   "priority": new_task.priority,
                   "due_date": new_task.due_date,
                   "completed": new_task.completed,
                   "created_at": new_task.created_at,
                   "updated_at": new_task.updated_at
               })
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

   @app.patch("/api/tasks/bulk/complete")
   def bulk_complete_tasks(request: Request, task_ids: List[int]):
       """Mark multiple tasks as completed"""
       updated_tasks = []
       not_found = []

       for task_id in task_ids:
           update_data = TaskUpdate(completed=True)
           updated_task = TaskService.update_task(task_id, update_data)

           if updated_task:
               updated_tasks.append({
                   "id": updated_task.id,
                   "title": updated_task.title,
                   "description": updated_task.description,
                   "priority": updated_task.priority,
                   "due_date": updated_task.due_date,
                   "completed": updated_task.completed,
                   "created_at": updated_task.created_at,
                   "updated_at": updated_task.updated_at
               })
           else:
               not_found.append(task_id)

       return JSONResponse({
           "updated_tasks": updated_tasks,
           "not_found": not_found,
           "summary": {
               "total_requested": len(task_ids),
               "updated": len(updated_tasks),
               "not_found": len(not_found)
           }
       })

API Versioning
~~~~~~~~~~~~~~

Implement API versioning strategies:

.. code-block:: python

   # URL path versioning
   @app.get("/api/v1/users/{user_id}")
   def get_user_v1(request: Request, user_id: int):
       """Version 1 of user API"""
       return JSONResponse({
           "id": user_id,
           "name": f"User {user_id}",
           "version": "1.0"
       })

   @app.get("/api/v2/users/{user_id}")
   def get_user_v2(request: Request, user_id: int):
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
   def get_user_versioned(request: Request, user_id: int):
       """Versioned user endpoint using headers"""
       version = get_api_version(request)

       if version == "v2":
           return get_user_v2(request, user_id)
       else:
           return get_user_v1(request, user_id)

   # Content negotiation versioning
   @app.get("/api/data/{item_id}")
   def get_data_with_content_negotiation(request: Request, item_id: int):
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
                   "type": "item",
                   "id": str(item_id),
                   "attributes": base_data,
                   "meta": {"version": "2.0"}
               }
           })
       else:
           # Version 1 format (default)
           return JSONResponse({
               **base_data,
               "version": "1.0"
           })

Error Handling Patterns
-----------------------

Comprehensive Error Handling
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Structured error responses and logging:

.. code-block:: python

   import logging
   import traceback
   from enum import Enum

   # Configure logging
   logging.basicConfig(level=logging.INFO)
   logger = logging.getLogger(__name__)

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

   @app.middleware()
   def error_handling_middleware(request: Request, call_next):
       """Global error handling middleware"""
       try:
           return call_next(request)

       except APIError as e:
           # Custom API errors
           logger.warning(f"API Error: {e.code.value} - {e.message}", extra={
               "error_code": e.code.value,
               "request_path": str(request.url),
               "request_method": request.method
           })

           return JSONResponse({
               "error": {
                   "code": e.code.value,
                   "message": e.message,
                   "details": e.details
               },
               "request_id": request.headers.get("X-Request-ID", "unknown")
           }, status_code=e.status_code)

       except ValidationError as e:
           # Validation errors
           logger.warning(f"Validation Error: {str(e)}")

           return JSONResponse({
               "error": {
                   "code": ErrorCode.VALIDATION_ERROR.value,
                   "message": "Validation failed",
                   "details": {"validation_errors": str(e)}
               }
           }, status_code=422)

       except Exception as e:
           # Unexpected errors
           error_id = str(uuid.uuid4())
           logger.error(f"Unexpected error [{error_id}]: {str(e)}", extra={
               "error_id": error_id,
               "traceback": traceback.format_exc(),
               "request_path": str(request.url)
           })

           return JSONResponse({
               "error": {
                   "code": ErrorCode.INTERNAL_ERROR.value,
                   "message": "An internal error occurred",
                   "error_id": error_id
               }
           }, status_code=500)

   # Usage examples
   @app.get("/api/protected-resource/{resource_id}")
   def get_protected_resource(request: Request, resource_id: int):
       """Example endpoint with comprehensive error handling"""

       # Simulate authentication check
       if not request.headers.get("Authorization"):
           raise APIError(
               ErrorCode.UNAUTHORIZED,
               "Authentication required",
               {"required_header": "Authorization"},
               status_code=401
           )

       # Simulate authorization check
       user_role = request.headers.get("X-User-Role", "user")
       if user_role != "admin" and resource_id > 100:
           raise APIError(
               ErrorCode.FORBIDDEN,
               "Insufficient permissions to access this resource",
               {"required_role": "admin", "user_role": user_role},
               status_code=403
           )

       # Simulate resource not found
       if resource_id > 1000:
           raise APIError(
               ErrorCode.NOT_FOUND,
               f"Resource {resource_id} not found",
               {"resource_id": resource_id},
               status_code=404
           )

       # Simulate successful response
       return JSONResponse({
           "resource": {
               "id": resource_id,
               "name": f"Resource {resource_id}",
               "access_level": "granted"
           }
       })

Rate Limiting and Throttling
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Implement rate limiting for API protection:

.. code-block:: python

   import time
   from collections import defaultdict

   class RateLimiter:
       def __init__(self):
           self.requests = defaultdict(list)
           self.limits = {
               "default": {"count": 100, "window": 3600},  # 100 requests per hour
               "premium": {"count": 1000, "window": 3600},  # 1000 requests per hour
               "admin": {"count": 10000, "window": 3600}    # 10000 requests per hour
           }

       def is_allowed(self, identifier: str, tier: str = "default") -> tuple[bool, dict]:
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
               "remaining": max(0, limit_config["count"] - current_count - (1 if allowed else 0)),
               "reset_time": window_start + limit_config["window"],
               "window_seconds": limit_config["window"]
           }

   rate_limiter = RateLimiter()

   def rate_limit_middleware(tier: str = "default"):
       """Rate limiting middleware factory"""
       def middleware(request: Request, call_next):
           # Identify client (could use IP, user ID, API key, etc.)
           client_id = request.client.host
           api_key = request.headers.get("X-API-Key")

           if api_key:
               client_id = f"api_key:{api_key}"

           # Check rate limit
           allowed, limit_info = rate_limiter.is_allowed(client_id, tier)

           if not allowed:
               return JSONResponse({
                   "error": {
                       "code": ErrorCode.RATE_LIMITED.value,
                       "message": "Rate limit exceeded",
                       "details": limit_info
                   }
               }, status_code=429, headers={
                   "X-RateLimit-Limit": str(limit_info["limit"]),
                   "X-RateLimit-Remaining": str(limit_info["remaining"]),
                   "X-RateLimit-Reset": str(int(limit_info["reset_time"])),
                   "Retry-After": str(limit_info["window_seconds"])
               })

           # Add rate limit headers to response
           response = call_next(request)
           response.headers.update({
               "X-RateLimit-Limit": str(limit_info["limit"]),
               "X-RateLimit-Remaining": str(limit_info["remaining"]),
               "X-RateLimit-Reset": str(int(limit_info["reset_time"]))
           })

           return response

       return middleware

   # Apply rate limiting to different endpoint groups
   @app.get("/api/public/data")
   @app.middleware([rate_limit_middleware("default")])
   def public_data_endpoint(request: Request):
       """Public endpoint with default rate limiting"""
       return JSONResponse({"data": "public information"})

   @app.get("/api/premium/analytics")
   @app.middleware([rate_limit_middleware("premium")])
   def premium_analytics_endpoint(request: Request):
       """Premium endpoint with higher rate limits"""
       return JSONResponse({"analytics": "premium data"})

Performance Monitoring
~~~~~~~~~~~~~~~~~~~~~~

Monitor API performance and health:

.. code-block:: python

   import psutil
   from collections import deque

   class PerformanceMonitor:
       def __init__(self, max_samples: int = 1000):
           self.request_times = deque(maxlen=max_samples)
           self.error_count = 0
           self.total_requests = 0
           self.start_time = time.time()

       def record_request(self, duration: float, status_code: int):
           """Record request metrics"""
           self.request_times.append(duration)
           self.total_requests += 1

           if status_code >= 400:
               self.error_count += 1

       def get_metrics(self) -> dict:
           """Get current performance metrics"""
           if not self.request_times:
               return {"error": "No requests recorded"}

           avg_response_time = sum(self.request_times) / len(self.request_times)
           uptime = time.time() - self.start_time

           # System metrics
           cpu_percent = psutil.cpu_percent()
           memory = psutil.virtual_memory()

           return {
               "performance": {
                   "avg_response_time_ms": round(avg_response_time * 1000, 2),
                   "min_response_time_ms": round(min(self.request_times) * 1000, 2),
                   "max_response_time_ms": round(max(self.request_times) * 1000, 2),
                   "total_requests": self.total_requests,
                   "error_rate_percent": round((self.error_count / self.total_requests) * 100, 2),
                   "requests_per_second": round(self.total_requests / uptime, 2)
               },
               "system": {
                   "cpu_percent": cpu_percent,
                   "memory_percent": memory.percent,
                   "memory_available_gb": round(memory.available / (1024**3), 2),
                   "uptime_seconds": round(uptime, 2)
               }
           }

   performance_monitor = PerformanceMonitor()

   @app.middleware()
   def performance_monitoring_middleware(request: Request, call_next):
       """Performance monitoring middleware"""
       start_time = time.time()

       response = call_next(request)

       duration = time.time() - start_time
       performance_monitor.record_request(duration, response.status_code)

       # Add performance headers
       response.headers["X-Response-Time"] = f"{duration:.4f}"

       return response

   @app.get("/api/health")
   def health_check(request: Request):
       """Comprehensive health check endpoint"""
       metrics = performance_monitor.get_metrics()

       # Determine health status
       health_status = "healthy"
       issues = []

       if "performance" in metrics:
           if metrics["performance"]["avg_response_time_ms"] > 1000:
               health_status = "degraded"
               issues.append("High average response time")

           if metrics["performance"]["error_rate_percent"] > 5:
               health_status = "unhealthy"
               issues.append("High error rate")

           if metrics["system"]["cpu_percent"] > 80:
               health_status = "degraded"
               issues.append("High CPU usage")

           if metrics["system"]["memory_percent"] > 85:
               health_status = "degraded"
               issues.append("High memory usage")

       return JSONResponse({
           "status": health_status,
           "timestamp": datetime.utcnow().isoformat(),
           "issues": issues,
           "metrics": metrics
       })

These real-world recipes provide production-ready patterns that you can adapt and extend for your specific use cases with Catzilla.
