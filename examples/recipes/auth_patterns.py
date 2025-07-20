"""
Authentication & Authorization Example

This example demonstrates authentication and authorization patterns
using Catzilla framework.

Features demonstrated:
- JWT-based authentication
- Role-based access control (RBAC)
- Permission-based authorization
- API key authentication
- Rate limiting per user
- Secure password handling
- Session management
- Middleware-based auth
"""

from catzilla import Catzilla, Request, Response, JSONResponse
from catzilla.validation import BaseModel
from catzilla.middleware import ZeroAllocMiddleware
import json
try:
    import jwt
except ImportError:
    jwt = None
    print("Warning: PyJWT not installed. JWT functionality will be disabled.")
import hashlib
import hmac
import secrets
import time
from typing import Any, Dict, List, Optional, Union, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
import uuid
import base64

# Initialize Catzilla with security features
app = Catzilla(
    production=False,
    show_banner=True,
    log_requests=True
)

# Security configuration
AUTH_CONFIG = {
    "jwt_secret": "your-super-secret-jwt-key-change-in-production",
    "jwt_algorithm": "HS256",
    "jwt_expiry_hours": 24,
    "password_salt_rounds": 12,
    "max_login_attempts": 5,
    "lockout_duration_minutes": 15,
    "rate_limit_requests": 100,
    "rate_limit_window_minutes": 60
}

# User roles and permissions
class UserRole(str, Enum):
    ADMIN = "admin"
    MODERATOR = "moderator"
    USER = "user"
    READONLY = "readonly"

class Permission(str, Enum):
    READ_USERS = "read:users"
    WRITE_USERS = "write:users"
    DELETE_USERS = "delete:users"
    READ_POSTS = "read:posts"
    WRITE_POSTS = "write:posts"
    DELETE_POSTS = "delete:posts"
    ADMIN_PANEL = "admin:panel"
    MODERATE_CONTENT = "moderate:content"

# Role-permission mapping
ROLE_PERMISSIONS = {
    UserRole.ADMIN: [
        Permission.READ_USERS, Permission.WRITE_USERS, Permission.DELETE_USERS,
        Permission.READ_POSTS, Permission.WRITE_POSTS, Permission.DELETE_POSTS,
        Permission.ADMIN_PANEL, Permission.MODERATE_CONTENT
    ],
    UserRole.MODERATOR: [
        Permission.READ_USERS, Permission.READ_POSTS,
        Permission.WRITE_POSTS, Permission.MODERATE_CONTENT
    ],
    UserRole.USER: [
        Permission.READ_POSTS, Permission.WRITE_POSTS
    ],
    UserRole.READONLY: [
        Permission.READ_POSTS
    ]
}

# Data models
class LoginModel(BaseModel):
    """Login request model"""
    email: str
    password: str

class RegisterModel(BaseModel):
    """User registration model"""
    name: str
    email: str
    password: str
    role: UserRole = UserRole.USER

class ChangePasswordModel(BaseModel):
    """Change password model"""
    current_password: str
    new_password: str

# Database models
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
    api_key: Optional[str] = None
    created_at: datetime = None
    last_login: Optional[datetime] = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()

@dataclass
class AuthToken:
    user_id: str
    token: str
    expires_at: datetime
    created_at: datetime = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()

@dataclass
class RateLimitInfo:
    requests: int
    window_start: datetime

    def __post_init__(self):
        if self.window_start is None:
            self.window_start = datetime.now()

# In-memory storage
users_db: Dict[str, User] = {}
tokens_db: Dict[str, AuthToken] = {}
api_keys_db: Dict[str, str] = {}  # api_key -> user_id
rate_limits: Dict[str, RateLimitInfo] = {}

# Memory cache for sessions (simplified for demo)
session_cache = {}

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
    """Generate JWT token for user"""
    if jwt is None:
        # Simple fallback token for demo (not secure for production)
        payload = {
            'user_id': user.id,
            'email': user.email,
            'role': user.role.value,
            'permissions': [p.value for p in ROLE_PERMISSIONS.get(user.role, [])],
            'exp': (datetime.utcnow() + timedelta(hours=AUTH_CONFIG["jwt_expiry_hours"])).timestamp(),
            'iat': datetime.utcnow().timestamp()
        }
        import base64
        return base64.b64encode(json.dumps(payload).encode()).decode()

    payload = {
        'user_id': user.id,
        'email': user.email,
        'role': user.role.value,
        'permissions': [p.value for p in ROLE_PERMISSIONS.get(user.role, [])],
        'exp': datetime.utcnow() + timedelta(hours=AUTH_CONFIG["jwt_expiry_hours"]),
        'iat': datetime.utcnow()
    }
    return jwt.encode(payload, AUTH_CONFIG["jwt_secret"], algorithm=AUTH_CONFIG["jwt_algorithm"])

def verify_jwt(token: str) -> Optional[Dict[str, Any]]:
    """Verify and decode JWT token"""
    if jwt is None:
        # Simple fallback for demo
        try:
            import base64
            payload = json.loads(base64.b64decode(token.encode()).decode())
            # Check expiration
            if payload.get('exp') and payload['exp'] < datetime.utcnow().timestamp():
                return None
            return payload
        except:
            return None

    try:
        payload = jwt.decode(token, AUTH_CONFIG["jwt_secret"], algorithms=[AUTH_CONFIG["jwt_algorithm"]])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

def generate_api_key() -> str:
    """Generate secure API key"""
    return f"ck_{secrets.token_urlsafe(32)}"

def check_rate_limit(identifier: str) -> bool:
    """Check if request is within rate limit"""
    now = datetime.now()

    if identifier not in rate_limits:
        rate_limits[identifier] = RateLimitInfo(requests=1, window_start=now)
        return True

    rate_info = rate_limits[identifier]
    window_minutes = AUTH_CONFIG["rate_limit_window_minutes"]

    # Reset window if expired
    if now - rate_info.window_start > timedelta(minutes=window_minutes):
        rate_info.requests = 1
        rate_info.window_start = now
        return True

    # Check limit
    if rate_info.requests >= AUTH_CONFIG["rate_limit_requests"]:
        return False

    rate_info.requests += 1
    return True

def get_user_permissions(user: User) -> List[Permission]:
    """Get user permissions based on role"""
    return ROLE_PERMISSIONS.get(user.role, [])

def has_permission(user: User, permission: Permission) -> bool:
    """Check if user has specific permission"""
    return permission in get_user_permissions(user)

# Authentication middleware
@app.middleware(priority=20, pre_route=True, name="authentication")
def authentication_middleware(request: Request) -> Optional[Response]:
    """JWT and API key authentication middleware"""

    # Public paths that don't require auth
    public_paths = {'/', '/docs', '/health', '/auth/login', '/auth/register'}

    if request.path in public_paths:
        return None

    # Rate limiting check
    client_ip = request.headers.get('X-Forwarded-For', request.headers.get('X-Real-IP', 'unknown'))
    if not check_rate_limit(client_ip):
        return JSONResponse(
            {"error": "Rate limit exceeded", "retry_after": AUTH_CONFIG["rate_limit_window_minutes"] * 60},
            status_code=429,
            headers={"Retry-After": str(AUTH_CONFIG["rate_limit_window_minutes"] * 60)}
        )

    # Try JWT authentication first
    auth_header = request.headers.get('Authorization', '')
    if auth_header.startswith('Bearer '):
        token = auth_header[7:]
        payload = verify_jwt(token)
        if payload:
            user_id = payload['user_id']
            if user_id in users_db:
                user = users_db[user_id]
                if user.is_active:
                    # Attach user to request
                    if not hasattr(request, 'context'):
                        request.context = {}
                    request.context['user'] = user
                    request.context['auth_payload'] = payload
                    return None
                else:
                    return JSONResponse({"error": "Account deactivated"}, status_code=403)

        return JSONResponse({"error": "Invalid or expired token"}, status_code=401)

    # Try API key authentication
    api_key = request.headers.get('X-API-Key')
    if not api_key:
        api_key = request.query_params.get('api_key') if hasattr(request, 'query_params') else None

    if api_key:
        if api_key in api_keys_db:
            user_id = api_keys_db[api_key]
            if user_id in users_db:
                user = users_db[user_id]
                if user.is_active:
                    # Attach user to request
                    if not hasattr(request, 'context'):
                        request.context = {}
                    request.context['user'] = user
                    request.context['auth_type'] = 'api_key'
                    return None
                else:
                    return JSONResponse({"error": "Account deactivated"}, status_code=403)

        return JSONResponse({"error": "Invalid API key"}, status_code=401)

    # No authentication provided
    return JSONResponse({"error": "Authentication required"}, status_code=401)

# Authorization decorator
def require_permission(permission: Permission):
    """Decorator to require specific permission"""
    def decorator(func: Callable) -> Callable:
        def wrapper(request) -> Response:
            user = getattr(request, 'context', {}).get('user')
            if not user:
                return JSONResponse({"error": "Authentication required"}, status_code=401)

            if not has_permission(user, permission):
                return JSONResponse(
                    {"error": f"Permission '{permission.value}' required"},
                    status_code=403
                )

            return func(request)
        return wrapper
    return decorator

def require_role(role: UserRole):
    """Decorator to require specific role"""
    def decorator(func: Callable) -> Callable:
        def wrapper(request) -> Response:
            user = getattr(request, 'context', {}).get('user')
            if not user:
                return JSONResponse({"error": "Authentication required"}, status_code=401)

            if user.role != role:
                return JSONResponse(
                    {"error": f"Role '{role.value}' required"},
                    status_code=403
                )

            return func(request)
        return wrapper
    return decorator

@app.get("/")
def home(request) -> Response:
    """API documentation"""
    return JSONResponse({
        "message": "Catzilla Authentication & Authorization Example",
        "features": [
            "JWT-based authentication",
            "Role-based access control (RBAC)",
            "Permission-based authorization",
            "API key authentication",
            "Rate limiting per user",
            "Secure password handling",
            "Session management",
            "Middleware-based auth"
        ],
        "authentication": {
            "jwt": "Bearer token in Authorization header",
            "api_key": "X-API-Key header or api_key query parameter"
        },
        "roles": [role.value for role in UserRole],
        "permissions": [perm.value for perm in Permission],
        "endpoints": {
            "auth": {
                "register": "POST /auth/register",
                "login": "POST /auth/login",
                "logout": "POST /auth/logout",
                "refresh": "POST /auth/refresh",
                "change_password": "POST /auth/change-password",
                "profile": "GET /auth/profile"
            },
            "api_keys": {
                "generate": "POST /auth/api-keys",
                "list": "GET /auth/api-keys",
                "revoke": "DELETE /auth/api-keys/{key_id}"
            },
            "protected": {
                "users": "GET /api/users (read:users permission)",
                "admin": "GET /api/admin (admin role)",
                "moderate": "POST /api/moderate (moderate:content permission)"
            }
        }
    })

# Authentication endpoints
@app.post("/auth/register")
def register(request) -> Response:
    """Register new user"""
    try:
        user_data = RegisterModel(**request.json())

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
            role=user_data.role,
            api_key=generate_api_key()
        )

        users_db[user_id] = user
        api_keys_db[user.api_key] = user_id

        # Generate JWT token
        token = generate_jwt(user)

        return JSONResponse({
            "user": {
                "id": user.id,
                "name": user.name,
                "email": user.email,
                "role": user.role.value,
                "permissions": [p.value for p in get_user_permissions(user)]
            },
            "token": token,
            "api_key": user.api_key,
            "expires_in": AUTH_CONFIG["jwt_expiry_hours"] * 3600
        }, status_code=201)

    except ValueError as e:
        return JSONResponse({"error": "Validation failed", "details": str(e)}, status_code=400)
    except Exception as e:
        return JSONResponse({"error": "Internal server error", "details": str(e)}, status_code=500)

@app.post("/auth/login")
def login(request) -> Response:
    """Login user"""
    try:
        login_data = LoginModel(**request.json())

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
            # Increment login attempts
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
        user.last_login = datetime.now()

        # Generate JWT token
        token = generate_jwt(user)

        return JSONResponse({
            "user": {
                "id": user.id,
                "name": user.name,
                "email": user.email,
                "role": user.role.value,
                "permissions": [p.value for p in get_user_permissions(user)]
            },
            "token": token,
            "expires_in": AUTH_CONFIG["jwt_expiry_hours"] * 3600
        })

    except ValueError as e:
        return JSONResponse({"error": "Validation failed", "details": str(e)}, status_code=400)
    except Exception as e:
        return JSONResponse({"error": "Internal server error", "details": str(e)}, status_code=500)

@app.post("/auth/logout")
def logout(request) -> Response:
    """Logout user (invalidate token)"""
    # In a real application, you'd maintain a blacklist of invalidated tokens
    # For this example, we'll just return success
    return JSONResponse({"message": "Logged out successfully"})

@app.get("/auth/profile")
def get_profile(request) -> Response:
    """Get user profile"""
    user = getattr(request, 'context', {}).get('user')
    return JSONResponse({
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "role": user.role.value,
        "permissions": [p.value for p in get_user_permissions(user)],
        "is_active": user.is_active,
        "created_at": user.created_at.isoformat(),
        "last_login": user.last_login.isoformat() if user.last_login else None
    })

@app.post("/auth/change-password")
def change_password(request) -> Response:
    """Change user password"""
    try:
        password_data = ChangePasswordModel(**request.json())
        user = getattr(request, 'context', {}).get('user')

        # Verify current password
        if not verify_password(password_data.current_password, user.password_hash):
            return JSONResponse({"error": "Current password is incorrect"}, status_code=400)

        # Update password
        user.password_hash = hash_password(password_data.new_password)

        return JSONResponse({"message": "Password changed successfully"})

    except ValueError as e:
        return JSONResponse({"error": "Validation failed", "details": str(e)}, status_code=400)
    except Exception as e:
        return JSONResponse({"error": "Internal server error", "details": str(e)}, status_code=500)

# API Key management
@app.post("/auth/api-keys")
def generate_new_api_key(request) -> Response:
    """Generate new API key for user"""
    user = getattr(request, 'context', {}).get('user')

    # Revoke old API key
    if user.api_key and user.api_key in api_keys_db:
        del api_keys_db[user.api_key]

    # Generate new API key
    new_api_key = generate_api_key()
    user.api_key = new_api_key
    api_keys_db[new_api_key] = user.id

    return JSONResponse({
        "api_key": new_api_key,
        "created_at": datetime.now().isoformat(),
        "note": "Store this key securely. It won't be shown again."
    })

@app.get("/auth/api-keys")
def list_api_keys(request) -> Response:
    """List user's API key info (without showing the key)"""
    user = getattr(request, 'context', {}).get('user')

    if user.api_key:
        return JSONResponse({
            "api_key_exists": True,
            "key_prefix": user.api_key[:8] + "...",
            "created_at": user.created_at.isoformat()
        })
    else:
        return JSONResponse({"api_key_exists": False})

@app.delete("/auth/api-keys")
def revoke_api_key(request) -> Response:
    """Revoke user's API key"""
    user = getattr(request, 'context', {}).get('user')

    if user.api_key and user.api_key in api_keys_db:
        del api_keys_db[user.api_key]
        user.api_key = None
        return JSONResponse({"message": "API key revoked successfully"})
    else:
        return JSONResponse({"error": "No API key found"}, status_code=404)

# Protected endpoints demonstrating authorization
@app.get("/api/users")
@require_permission(Permission.READ_USERS)
def list_users(request) -> Response:
    """List all users - requires read:users permission"""
    users_list = []
    for user in users_db.values():
        users_list.append({
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "role": user.role.value,
            "is_active": user.is_active,
            "created_at": user.created_at.isoformat()
        })

    current_user = getattr(request, 'context', {}).get('user')
    return JSONResponse({
        "users": users_list,
        "total": len(users_list),
        "requester": {
            "id": current_user.id,
            "role": current_user.role.value
        }
    })

@app.get("/api/admin")
@require_role(UserRole.ADMIN)
def admin_panel(request) -> Response:
    """Admin panel - requires admin role"""
    current_user = getattr(request, 'context', {}).get('user')
    return JSONResponse({
        "message": "Welcome to admin panel",
        "system_stats": {
            "total_users": len(users_db),
            "active_users": sum(1 for u in users_db.values() if u.is_active),
            "total_tokens": len(tokens_db),
            "total_api_keys": len(api_keys_db)
        },
        "permissions": [p.value for p in get_user_permissions(current_user)]
    })

@app.post("/api/moderate")
@require_permission(Permission.MODERATE_CONTENT)
def moderate_content(request) -> Response:
    """Content moderation - requires moderate:content permission"""
    try:
        data = request.json()
        action = data.get("action", "review")
        content_id = data.get("content_id")

        current_user = getattr(request, 'context', {}).get('user')
        return JSONResponse({
            "message": f"Content {content_id} marked for {action}",
            "moderator": {
                "id": current_user.id,
                "name": current_user.name,
                "role": current_user.role.value
            },
            "timestamp": datetime.now().isoformat()
        })

    except Exception as e:
        return JSONResponse({"error": "Invalid request", "details": str(e)}, status_code=400)

@app.get("/health")
def health_check(request) -> Response:
    """Health check endpoint"""
    return JSONResponse({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "auth": {
            "total_users": len(users_db),
            "active_sessions": len(session_cache),
            "api_keys_issued": len(api_keys_db)
        }
    })

# Seed admin user for testing
def seed_admin_user():
    """Create default admin user for testing"""
    admin_email = "admin@example.com"

    # Check if admin already exists
    for user in users_db.values():
        if user.email == admin_email:
            return

    admin_id = str(uuid.uuid4())
    admin_password_hash = hash_password("admin123")
    admin_api_key = generate_api_key()

    admin_user = User(
        id=admin_id,
        name="System Admin",
        email=admin_email,
        password_hash=admin_password_hash,
        role=UserRole.ADMIN,
        api_key=admin_api_key
    )

    users_db[admin_id] = admin_user
    api_keys_db[admin_api_key] = admin_id

    print(f"🔐 Admin user created:")
    print(f"   Email: {admin_email}")
    print(f"   Password: admin123")
    print(f"   API Key: {admin_api_key}")

if __name__ == "__main__":
    print("🚨 Starting Catzilla Authentication & Authorization Example")
    print("📝 Available endpoints:")
    print("   GET    /                          - API documentation")
    print("   POST   /auth/register             - Register new user")
    print("   POST   /auth/login                - Login user")
    print("   POST   /auth/logout               - Logout user")
    print("   GET    /auth/profile              - Get user profile")
    print("   POST   /auth/change-password      - Change password")
    print("   POST   /auth/api-keys             - Generate API key")
    print("   GET    /auth/api-keys             - List API key info")
    print("   DELETE /auth/api-keys             - Revoke API key")
    print("   GET    /api/users                 - List users (requires permission)")
    print("   GET    /api/admin                 - Admin panel (requires admin role)")
    print("   POST   /api/moderate              - Moderate content (requires permission)")
    print("   GET    /health                    - Health check")
    print()
    print("🎨 Features demonstrated:")
    print("   • JWT-based authentication")
    print("   • Role-based access control (RBAC)")
    print("   • Permission-based authorization")
    print("   • API key authentication")
    print("   • Rate limiting per user")
    print("   • Secure password handling")
    print("   • Session management")
    print("   • Middleware-based auth")
    print()
    print("🧪 Try these examples:")
    print("   # Register a new user:")
    print("   curl -X POST -H 'Content-Type: application/json' \\")
    print("        -d '{\"name\":\"John Doe\",\"email\":\"john@example.com\",\"password\":\"password123\"}' \\")
    print("        http://localhost:8000/auth/register")
    print()
    print("   # Login:")
    print("   curl -X POST -H 'Content-Type: application/json' \\")
    print("        -d '{\"email\":\"admin@example.com\",\"password\":\"admin123\"}' \\")
    print("        http://localhost:8000/auth/login")
    print()
    print("   # Access protected endpoint with JWT:")
    print("   curl -H 'Authorization: Bearer YOUR_JWT_TOKEN' \\")
    print("        http://localhost:8000/api/users")
    print()
    print("   # Access with API key:")
    print("   curl -H 'X-API-Key: YOUR_API_KEY' \\")
    print("        http://localhost:8000/api/users")
    print()

    # Create admin user
    seed_admin_user()
    print()

    app.listen(host="0.0.0.0", port=8000)
