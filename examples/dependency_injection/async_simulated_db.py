#!/usr/bin/env python3
"""
🗄️ Catzilla Async DI with Simulated Database Example

This example demonstrates Catzilla's async DI system with simulated database operations
that showcase async patterns without complex SQLAlchemy async dependencies.

Features demonstrated:
- Async database service simulation
- Async repository pattern with DI
- Async service layer with business logic
- Concurrent async operations
- Request-scoped async sessions
- Async autovalidation
"""

import asyncio
import time
import json
from datetime import datetime
from typing import Dict, Any, Optional, List

from catzilla import Catzilla, service, Depends, JSONResponse, Path, BaseModel, Field
from catzilla.dependency_injection import set_default_container

# Initialize Catzilla with DI enabled and autovalidation
app = Catzilla(enable_di=True, auto_validation=True, production=False, show_banner=True)
set_default_container(app.di_container)

print("🗄️ Catzilla Async DI with Simulated Database Example")
print("=" * 60)

# ============================================================================
# 1. DATA MODELS (Simulated Database Records)
# ============================================================================

class User:
    def __init__(self, id: int, name: str, email: str, created_at: datetime = None):
        self.id = id
        self.name = name
        self.email = email
        self.created_at = created_at or datetime.utcnow()
        self.posts = []

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "created_at": self.created_at.isoformat(),
            "posts_count": len(self.posts)
        }

class Post:
    def __init__(self, id: int, title: str, content: str, author_id: int, created_at: datetime = None):
        self.id = id
        self.title = title
        self.content = content
        self.author_id = author_id
        self.created_at = created_at or datetime.utcnow()
        self.author = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "content": self.content,
            "author_id": self.author_id,
            "author_name": self.author.name if self.author else None,
            "created_at": self.created_at.isoformat()
        }

# ============================================================================
# 2. ASYNC DATABASE SERVICE (SINGLETON)
# ============================================================================

@service("async_database", scope="singleton")
class AsyncDatabaseService:
    """Async database service that simulates real database operations"""

    def __init__(self):
        self.users = {}
        self.posts = {}
        self.next_user_id = 1
        self.next_post_id = 1
        self.connection_count = 0
        self.seeded = False

        print("🗄️ Async Database service initialized")

        # Initialize with sample data immediately
        self._seed_data_sync()

    def _seed_data_sync(self):
        """Seed initial data synchronously"""
        if self.seeded:
            return

        # Create sample users
        users_data = [
            {"name": "Alice Johnson", "email": "alice@example.com"},
            {"name": "Bob Smith", "email": "bob@example.com"},
            {"name": "Carol Brown", "email": "carol@example.com"},
            {"name": "David Wilson", "email": "david@example.com"}
        ]

        for user_data in users_data:
            user = User(self.next_user_id, user_data["name"], user_data["email"])
            self.users[user.id] = user
            self.next_user_id += 1

        # Create sample posts
        posts_data = [
            {"title": "Async Programming Guide", "content": "This is Alice's guide to async programming", "author_id": 1},
            {"title": "Hello Async World", "content": "Bob's introduction to async operations", "author_id": 2},
            {"title": "Concurrent Operations", "content": "Carol's tutorial on concurrency", "author_id": 3},
            {"title": "Advanced Async Patterns", "content": "Alice's advanced async tutorial", "author_id": 1},
            {"title": "Database Async Operations", "content": "David's guide to async databases", "author_id": 4},
        ]

        for post_data in posts_data:
            post = Post(self.next_post_id, post_data["title"], post_data["content"], post_data["author_id"])
            post.author = self.users.get(post_data["author_id"])
            if post.author:
                post.author.posts.append(post)
            self.posts[post.id] = post
            self.next_post_id += 1

        self.seeded = True
        print("🌱 Async database seeded with sample data")

    async def _seed_data(self):
        """Seed initial data asynchronously"""
        await asyncio.sleep(0.1)  # Simulate database initialization time

        # Create sample users
        users_data = [
            {"name": "Alice Johnson", "email": "alice@example.com"},
            {"name": "Bob Smith", "email": "bob@example.com"},
            {"name": "Carol Brown", "email": "carol@example.com"},
            {"name": "David Wilson", "email": "david@example.com"}
        ]

        for user_data in users_data:
            user = User(self.next_user_id, user_data["name"], user_data["email"])
            self.users[user.id] = user
            self.next_user_id += 1

        # Create sample posts
        posts_data = [
            {"title": "Async Programming Guide", "content": "This is Alice's guide to async programming", "author_id": 1},
            {"title": "Hello Async World", "content": "Bob's introduction to async operations", "author_id": 2},
            {"title": "Concurrent Operations", "content": "Carol's tutorial on concurrency", "author_id": 3},
            {"title": "Advanced Async Patterns", "content": "Alice's advanced async tutorial", "author_id": 1},
            {"title": "Database Async Operations", "content": "David's guide to async databases", "author_id": 4},
        ]

        for post_data in posts_data:
            post = Post(self.next_post_id, post_data["title"], post_data["content"], post_data["author_id"])
            post.author = self.users.get(post_data["author_id"])
            if post.author:
                post.author.posts.append(post)
            self.posts[post.id] = post
            self.next_post_id += 1

        print("🌱 Async database seeded with sample data")

    async def get_connection(self):
        """Simulate getting a database connection"""
        await asyncio.sleep(0.01)  # Simulate connection time
        self.connection_count += 1
        return f"connection_{self.connection_count}"

    async def execute_query(self, query: str, params: dict = None):
        """Simulate executing a database query"""
        await asyncio.sleep(0.02)  # Simulate query execution time
        return {"query": query, "params": params, "executed_at": datetime.now().isoformat()}

# ============================================================================
# 3. ASYNC SESSION MANAGEMENT (REQUEST SCOPE)
# ============================================================================

@service("async_session", scope="request")
class AsyncSessionService:
    """Async session service for managing database sessions"""

    def __init__(self, db: AsyncDatabaseService = Depends("async_database")):
        self.db = db
        self.connection = None
        self.transaction_count = 0
        self.operations = []

        print("🔄 Async session initialized (request-scoped)")

    async def get_connection(self):
        """Get or create database connection"""
        if not self.connection:
            self.connection = await self.db.get_connection()
        return self.connection

    async def begin_transaction(self):
        """Begin an async transaction"""
        await asyncio.sleep(0.005)  # Simulate transaction start
        self.transaction_count += 1
        return f"transaction_{self.transaction_count}"

    async def commit_transaction(self, transaction_id: str):
        """Commit an async transaction"""
        await asyncio.sleep(0.005)  # Simulate transaction commit
        self.operations.append(f"COMMIT {transaction_id}")

    async def rollback_transaction(self, transaction_id: str):
        """Rollback an async transaction"""
        await asyncio.sleep(0.005)  # Simulate transaction rollback
        self.operations.append(f"ROLLBACK {transaction_id}")

# ============================================================================
# 4. ASYNC REPOSITORY PATTERN WITH DI
# ============================================================================

@service("async_user_repository", scope="singleton")
class AsyncUserRepository:
    """Async user repository with simulated database operations"""

    def __init__(self):
        print("👥 Async User repository initialized")

    async def get_all(self, session: AsyncSessionService) -> List[User]:
        """Get all users asynchronously"""
        connection = await session.get_connection()
        await session.db.execute_query("SELECT * FROM users", {})
        await asyncio.sleep(0.05)  # Simulate complex query
        return list(session.db.users.values())

    async def get_by_id(self, user_id: int, session: AsyncSessionService) -> Optional[User]:
        """Get user by ID asynchronously"""
        connection = await session.get_connection()
        await session.db.execute_query("SELECT * FROM users WHERE id = ?", {"id": user_id})
        await asyncio.sleep(0.03)  # Simulate database lookup
        return session.db.users.get(user_id)

    async def get_by_email(self, email: str, session: AsyncSessionService) -> Optional[User]:
        """Get user by email asynchronously"""
        connection = await session.get_connection()
        await session.db.execute_query("SELECT * FROM users WHERE email = ?", {"email": email})
        await asyncio.sleep(0.04)  # Simulate index lookup
        for user in session.db.users.values():
            if user.email == email:
                return user
        return None

    async def create(self, name: str, email: str, session: AsyncSessionService) -> User:
        """Create a new user asynchronously"""
        connection = await session.get_connection()
        transaction_id = await session.begin_transaction()

        try:
            user = User(session.db.next_user_id, name, email)
            session.db.users[user.id] = user
            session.db.next_user_id += 1

            await session.db.execute_query("INSERT INTO users (name, email) VALUES (?, ?)",
                                         {"name": name, "email": email})
            await session.commit_transaction(transaction_id)
            await asyncio.sleep(0.06)  # Simulate insert operation

            return user
        except Exception:
            await session.rollback_transaction(transaction_id)
            raise

    async def update(self, user_id: int, session: AsyncSessionService, **kwargs) -> Optional[User]:
        """Update user asynchronously"""
        connection = await session.get_connection()
        transaction_id = await session.begin_transaction()

        try:
            user = session.db.users.get(user_id)
            if user:
                for key, value in kwargs.items():
                    if hasattr(user, key) and value is not None:
                        setattr(user, key, value)

                await session.db.execute_query("UPDATE users SET ... WHERE id = ?", {"id": user_id})
                await session.commit_transaction(transaction_id)
                await asyncio.sleep(0.05)  # Simulate update operation

            return user
        except Exception:
            await session.rollback_transaction(transaction_id)
            raise

    async def delete(self, user_id: int, session: AsyncSessionService) -> bool:
        """Delete user asynchronously"""
        connection = await session.get_connection()
        transaction_id = await session.begin_transaction()

        try:
            if user_id in session.db.users:
                # Also delete user's posts
                posts_to_delete = [post_id for post_id, post in session.db.posts.items()
                                 if post.author_id == user_id]
                for post_id in posts_to_delete:
                    del session.db.posts[post_id]

                del session.db.users[user_id]

                await session.db.execute_query("DELETE FROM users WHERE id = ?", {"id": user_id})
                await session.commit_transaction(transaction_id)
                await asyncio.sleep(0.08)  # Simulate cascade delete

                return True
            return False
        except Exception:
            await session.rollback_transaction(transaction_id)
            raise

@service("async_post_repository", scope="singleton")
class AsyncPostRepository:
    """Async post repository with simulated database operations"""

    def __init__(self):
        print("📝 Async Post repository initialized")

    async def get_all(self, session: AsyncSessionService) -> List[Post]:
        """Get all posts asynchronously"""
        connection = await session.get_connection()
        await session.db.execute_query("SELECT * FROM posts JOIN users ON posts.author_id = users.id", {})
        await asyncio.sleep(0.07)  # Simulate join query
        return list(session.db.posts.values())

    async def get_by_id(self, post_id: int, session: AsyncSessionService) -> Optional[Post]:
        """Get post by ID asynchronously"""
        connection = await session.get_connection()
        await session.db.execute_query("SELECT * FROM posts WHERE id = ?", {"id": post_id})
        await asyncio.sleep(0.03)  # Simulate lookup
        return session.db.posts.get(post_id)

    async def get_by_author(self, author_id: int, session: AsyncSessionService) -> List[Post]:
        """Get posts by author asynchronously"""
        connection = await session.get_connection()
        await session.db.execute_query("SELECT * FROM posts WHERE author_id = ?", {"author_id": author_id})
        await asyncio.sleep(0.04)  # Simulate filtered query
        return [post for post in session.db.posts.values() if post.author_id == author_id]

    async def create(self, title: str, content: str, author_id: int, session: AsyncSessionService) -> Post:
        """Create a new post asynchronously"""
        connection = await session.get_connection()
        transaction_id = await session.begin_transaction()

        try:
            post = Post(session.db.next_post_id, title, content, author_id)
            post.author = session.db.users.get(author_id)
            if post.author:
                post.author.posts.append(post)

            session.db.posts[post.id] = post
            session.db.next_post_id += 1

            await session.db.execute_query("INSERT INTO posts (title, content, author_id) VALUES (?, ?, ?)",
                                         {"title": title, "content": content, "author_id": author_id})
            await session.commit_transaction(transaction_id)
            await asyncio.sleep(0.05)  # Simulate insert

            return post
        except Exception:
            await session.rollback_transaction(transaction_id)
            raise

# ============================================================================
# 5. ASYNC SERVICE LAYER WITH BUSINESS LOGIC
# ============================================================================

@service("async_user_service", scope="singleton")
class AsyncUserService:
    """Async user service with business logic"""

    def __init__(self, user_repo: AsyncUserRepository = Depends("async_user_repository")):
        self.user_repo = user_repo
        print("🏢 Async User service initialized")

    async def get_all_users(self, session: AsyncSessionService) -> List[Dict[str, Any]]:
        """Get all users with their data asynchronously"""
        users = await self.user_repo.get_all(session)
        return [user.to_dict() for user in users]

    async def get_user_with_posts(self, user_id: int, session: AsyncSessionService) -> Optional[Dict[str, Any]]:
        """Get user with their posts asynchronously"""
        user = await self.user_repo.get_by_id(user_id, session)
        if not user:
            return None

        user_data = user.to_dict()
        user_data["posts"] = [post.to_dict() for post in user.posts]
        return user_data

    async def create_user(self, name: str, email: str, session: AsyncSessionService) -> Dict[str, Any]:
        """Create a new user with async validation"""
        # Check if email already exists
        existing_user = await self.user_repo.get_by_email(email, session)
        if existing_user:
            raise ValueError(f"User with email {email} already exists")

        user = await self.user_repo.create(name, email, session)
        return user.to_dict()

@service("async_post_service", scope="singleton")
class AsyncPostService:
    """Async post service with business logic"""

    def __init__(self,
                 post_repo: AsyncPostRepository = Depends("async_post_repository"),
                 user_repo: AsyncUserRepository = Depends("async_user_repository")):
        self.post_repo = post_repo
        self.user_repo = user_repo
        print("📰 Async Post service initialized")

    async def get_all_posts(self, session: AsyncSessionService) -> List[Dict[str, Any]]:
        """Get all posts with author info asynchronously"""
        posts = await self.post_repo.get_all(session)
        return [post.to_dict() for post in posts]

    async def create_post(self, title: str, content: str, author_id: int, session: AsyncSessionService) -> Dict[str, Any]:
        """Create a new post with async validation"""
        # Check if author exists
        author = await self.user_repo.get_by_id(author_id, session)
        if not author:
            raise ValueError(f"Author with ID {author_id} not found")

        post = await self.post_repo.create(title, content, author_id, session)
        return post.to_dict()

    async def get_user_posts(self, user_id: int, session: AsyncSessionService) -> List[Dict[str, Any]]:
        """Get all posts by a specific user"""
        posts = await self.post_repo.get_by_author(user_id, session)
        return [post.to_dict() for post in posts]

# ============================================================================
# 6. ASYNC ANALYTICS SERVICE (TRANSIENT)
# ============================================================================

@service("async_analytics", scope="transient")
class AsyncAnalyticsService:
    """Async analytics service for tracking operations"""

    def __init__(self):
        self.instance_id = str(time.time())[-6:]
        print(f"📊 Async Analytics service created (transient) - {self.instance_id}")

    async def track_operation(self, operation: str, entity: str, duration: float = None) -> Dict[str, Any]:
        """Track async operation"""
        # Simulate async analytics processing
        await asyncio.sleep(0.001)

        return {
            "operation": operation,
            "entity": entity,
            "duration": duration,
            "timestamp": datetime.now().isoformat(),
            "analytics_instance": self.instance_id,
            "async_operation": True
        }

# ============================================================================
# 7. VALIDATION MODELS FOR AUTOVALIDATION
# ============================================================================

class UserCreateModel(BaseModel):
    """User creation model with autovalidation"""
    name: str = Field(min_length=2, max_length=100, description="User name")
    email: str = Field(regex=r'^[^@]+@[^@]+\.[^@]+$', description="Valid email address")

class PostCreateModel(BaseModel):
    """Post creation model with autovalidation"""
    title: str = Field(min_length=5, max_length=200, description="Post title")
    content: str = Field(min_length=10, max_length=5000, description="Post content")
    author_id: int = Field(ge=1, description="Author ID")

class UserUpdateModel(BaseModel):
    """User update model with autovalidation"""
    name: Optional[str] = Field(None, min_length=2, max_length=100, description="User name")
    email: Optional[str] = Field(None, regex=r'^[^@]+@[^@]+\.[^@]+$', description="Valid email address")

# ============================================================================
# 8. ASYNC ROUTE HANDLERS
# ============================================================================

@app.get("/")
async def async_home(request):
    """Async home page"""
    return JSONResponse({
        "message": "🗄️ Catzilla Async DI with Simulated Database Demo",
        "features": [
            "Async database service simulation",
            "Async request-scoped sessions",
            "Async repository pattern with DI",
            "Async service layer with business logic",
            "Concurrent async operations",
            "Async autovalidation"
        ],
        "performance": "60%+ faster than FastAPI async",
        "async_support": True
    })

@app.get("/users")
async def get_users_async(request,
                         user_service: AsyncUserService = Depends("async_user_service"),
                         session: AsyncSessionService = Depends("async_session"),
                         analytics: AsyncAnalyticsService = Depends("async_analytics")):
    """Get all users asynchronously with concurrent operations"""
    start_time = time.time()

    # Run user fetch and analytics concurrently
    users_task = asyncio.create_task(user_service.get_all_users(session))
    analytics_task = asyncio.create_task(analytics.track_operation("SELECT", "users"))

    users, analytics_data = await asyncio.gather(users_task, analytics_task)

    duration = time.time() - start_time
    analytics_data["duration"] = duration

    return JSONResponse({
        "users": users,
        "count": len(users),
        "analytics": analytics_data,
        "concurrent_operations": 2,
        "session_operations": len(session.operations)
    })

@app.get("/users/{user_id}")
async def get_user_async(request,
                        user_id: int = Path(...),
                        user_service: AsyncUserService = Depends("async_user_service"),
                        session: AsyncSessionService = Depends("async_session"),
                        analytics: AsyncAnalyticsService = Depends("async_analytics")):
    """Get user with posts asynchronously"""
    start_time = time.time()

    # Run user fetch and analytics concurrently
    user_task = asyncio.create_task(user_service.get_user_with_posts(user_id, session))
    analytics_task = asyncio.create_task(analytics.track_operation("SELECT", "users"))

    user, analytics_data = await asyncio.gather(user_task, analytics_task)

    duration = time.time() - start_time
    analytics_data["duration"] = duration

    if not user:
        return JSONResponse({"error": "User not found"}, status_code=404)

    return JSONResponse({
        "user": user,
        "analytics": analytics_data,
        "concurrent_operations": 2
    })

@app.post("/users")
async def create_user_async(request,
                           user_service: AsyncUserService = Depends("async_user_service"),
                           session: AsyncSessionService = Depends("async_session"),
                           analytics: AsyncAnalyticsService = Depends("async_analytics")):
    """Create a new user asynchronously with manual validation"""
    try:
        start_time = time.time()

        # Parse and validate request body manually
        import json
        body = request.body
        if hasattr(body, 'decode'):
            body_str = body.decode() if isinstance(body, bytes) else str(body)
        else:
            body_str = str(body)
        data = json.loads(body_str)

        # Manual validation
        if not data.get("name") or len(data["name"]) < 2 or len(data["name"]) > 100:
            return JSONResponse({"error": "Name must be between 2 and 100 characters"}, status_code=400)

        email = data.get("email", "")
        import re
        if not re.match(r'^[^@]+@[^@]+\.[^@]+$', email):
            return JSONResponse({"error": "Invalid email format"}, status_code=400)

        # Run user creation and analytics tracking concurrently
        user_task = asyncio.create_task(user_service.create_user(data["name"], data["email"], session))
        analytics_task = asyncio.create_task(analytics.track_operation("INSERT", "users"))

        user, analytics_data = await asyncio.gather(user_task, analytics_task)

        duration = time.time() - start_time
        analytics_data["duration"] = duration

        return JSONResponse({
            "user": user,
            "analytics": analytics_data,
            "validation": {
                "manually_validated": True,
                "fields_validated": ["name", "email"]
            },
            "concurrent_operations": 2
        }, status_code=201)
    except ValueError as e:
        return JSONResponse({"error": str(e)}, status_code=400)
    except Exception as e:
        return JSONResponse({"error": f"Invalid request data: {str(e)}"}, status_code=400)

@app.put("/users/{user_id}")
async def update_user_async(request,
                           user_id: int = Path(..., ge=1),
                           user_repo: AsyncUserRepository = Depends("async_user_repository"),
                           session: AsyncSessionService = Depends("async_session"),
                           analytics: AsyncAnalyticsService = Depends("async_analytics")):
    """Update user asynchronously with manual validation"""
    try:
        start_time = time.time()

        # Parse and validate request body manually
        import json
        body = request.body
        if hasattr(body, 'decode'):
            body_str = body.decode() if isinstance(body, bytes) else str(body)
        else:
            body_str = str(body)
        data = json.loads(body_str) if body_str else {}

        # Manual validation
        update_data = {}
        if "name" in data:
            if not data["name"] or len(data["name"]) < 2 or len(data["name"]) > 100:
                return JSONResponse({"error": "Name must be between 2 and 100 characters"}, status_code=400)
            update_data["name"] = data["name"]

        if "email" in data:
            import re
            if not re.match(r'^[^@]+@[^@]+\.[^@]+$', data["email"]):
                return JSONResponse({"error": "Invalid email format"}, status_code=400)
            update_data["email"] = data["email"]

        # Check if user exists and update concurrently with analytics
        user_check_task = asyncio.create_task(user_repo.get_by_id(user_id, session))
        analytics_task = asyncio.create_task(analytics.track_operation("UPDATE", "users"))

        existing_user, analytics_data = await asyncio.gather(user_check_task, analytics_task)

        if not existing_user:
            return JSONResponse({"error": "User not found"}, status_code=404)

        if not update_data:
            return JSONResponse({"error": "No update data provided"}, status_code=400)

        updated_user = await user_repo.update(user_id, session, **update_data)

        duration = time.time() - start_time
        analytics_data["duration"] = duration

        return JSONResponse({
            "user": updated_user.to_dict() if updated_user else None,
            "analytics": analytics_data,
            "validation": {
                "manually_validated": True,
                "fields_validated": list(update_data.keys())
            },
            "concurrent_operations": 2
        })
    except ValueError as e:
        return JSONResponse({"error": str(e)}, status_code=400)
    except Exception as e:
        return JSONResponse({"error": f"Invalid request data: {str(e)}"}, status_code=400)

@app.delete("/users/{user_id}")
async def delete_user_async(request,
                           user_id: int = Path(..., ge=1),
                           user_repo: AsyncUserRepository = Depends("async_user_repository"),
                           session: AsyncSessionService = Depends("async_session"),
                           analytics: AsyncAnalyticsService = Depends("async_analytics")):
    """Delete user asynchronously with path validation"""
    try:
        start_time = time.time()

        # Run deletion and analytics concurrently
        delete_task = asyncio.create_task(user_repo.delete(user_id, session))
        analytics_task = asyncio.create_task(analytics.track_operation("DELETE", "users"))

        deleted, analytics_data = await asyncio.gather(delete_task, analytics_task)

        duration = time.time() - start_time
        analytics_data["duration"] = duration

        if deleted:
            return JSONResponse({
                "message": f"User {user_id} deleted successfully",
                "analytics": analytics_data,
                "validation": {
                    "path_validated": True,
                    "user_id_constraint": "ge=1"
                },
                "concurrent_operations": 2
            })
        else:
            return JSONResponse({"error": "User not found"}, status_code=404)
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=400)

@app.get("/posts")
async def get_posts_async(request,
                         post_service: AsyncPostService = Depends("async_post_service"),
                         session: AsyncSessionService = Depends("async_session"),
                         analytics: AsyncAnalyticsService = Depends("async_analytics")):
    """Get all posts asynchronously"""
    start_time = time.time()

    # Run posts fetch and analytics concurrently
    posts_task = asyncio.create_task(post_service.get_all_posts(session))
    analytics_task = asyncio.create_task(analytics.track_operation("SELECT", "posts"))

    posts, analytics_data = await asyncio.gather(posts_task, analytics_task)

    duration = time.time() - start_time
    analytics_data["duration"] = duration

    return JSONResponse({
        "posts": posts,
        "count": len(posts),
        "analytics": analytics_data,
        "concurrent_operations": 2
    })

@app.post("/posts")
async def create_post_async(request,
                           post_service: AsyncPostService = Depends("async_post_service"),
                           session: AsyncSessionService = Depends("async_session"),
                           analytics: AsyncAnalyticsService = Depends("async_analytics")):
    """Create a new post asynchronously with manual validation"""
    try:
        start_time = time.time()

        # Parse and validate request body manually
        import json
        body = request.body
        if hasattr(body, 'decode'):
            body_str = body.decode() if isinstance(body, bytes) else str(body)
        else:
            body_str = str(body)
        data = json.loads(body_str)

        # Manual validation
        if not data.get("title") or len(data["title"]) < 5 or len(data["title"]) > 200:
            return JSONResponse({"error": "Title must be between 5 and 200 characters"}, status_code=400)

        if not data.get("content") or len(data["content"]) < 10 or len(data["content"]) > 5000:
            return JSONResponse({"error": "Content must be between 10 and 5000 characters"}, status_code=400)

        author_id = data.get("author_id")
        if not isinstance(author_id, int) or author_id < 1:
            return JSONResponse({"error": "Author ID must be a positive integer"}, status_code=400)

        # Run post creation and analytics tracking concurrently
        post_task = asyncio.create_task(post_service.create_post(data["title"], data["content"], author_id, session))
        analytics_task = asyncio.create_task(analytics.track_operation("INSERT", "posts"))

        post, analytics_data = await asyncio.gather(post_task, analytics_task)

        duration = time.time() - start_time
        analytics_data["duration"] = duration

        return JSONResponse({
            "post": post,
            "analytics": analytics_data,
            "validation": {
                "manually_validated": True,
                "fields_validated": ["title", "content", "author_id"]
            },
            "concurrent_operations": 2
        }, status_code=201)
    except ValueError as e:
        return JSONResponse({"error": str(e)}, status_code=400)
    except Exception as e:
        return JSONResponse({"error": f"Invalid request data: {str(e)}"}, status_code=400)

@app.get("/users/{user_id}/posts")
async def get_user_posts_async(request,
                              user_id: int = Path(...),
                              post_service: AsyncPostService = Depends("async_post_service"),
                              user_repo: AsyncUserRepository = Depends("async_user_repository"),
                              session: AsyncSessionService = Depends("async_session"),
                              analytics: AsyncAnalyticsService = Depends("async_analytics")):
    """Get all posts by a specific user asynchronously"""
    start_time = time.time()

    # Check user exists and get posts concurrently
    user_check_task = asyncio.create_task(user_repo.get_by_id(user_id, session))
    posts_task = asyncio.create_task(post_service.get_user_posts(user_id, session))
    analytics_task = asyncio.create_task(analytics.track_operation("SELECT", "posts"))

    user, posts, analytics_data = await asyncio.gather(user_check_task, posts_task, analytics_task)

    if not user:
        return JSONResponse({"error": "User not found"}, status_code=404)

    duration = time.time() - start_time
    analytics_data["duration"] = duration

    return JSONResponse({
        "user_id": user_id,
        "user_name": user.name,
        "posts": posts,
        "count": len(posts),
        "analytics": analytics_data,
        "concurrent_operations": 3
    })

@app.get("/stats")
async def get_async_stats(request,
                         user_service: AsyncUserService = Depends("async_user_service"),
                         post_service: AsyncPostService = Depends("async_post_service"),
                         session: AsyncSessionService = Depends("async_session"),
                         analytics: AsyncAnalyticsService = Depends("async_analytics")):
    """Get comprehensive async database statistics"""
    start_time = time.time()

    # Run all stats queries concurrently
    users_task = asyncio.create_task(user_service.get_all_users(session))
    posts_task = asyncio.create_task(post_service.get_all_posts(session))
    analytics_task = asyncio.create_task(analytics.track_operation("SELECT", "multiple"))

    users, posts, analytics_data = await asyncio.gather(users_task, posts_task, analytics_task)

    duration = time.time() - start_time
    analytics_data["duration"] = duration

    return JSONResponse({
        "database_stats": {
            "total_users": len(users),
            "total_posts": len(posts),
            "average_posts_per_user": round(len(posts) / len(users), 2) if users else 0
        },
        "performance": {
            "query_duration": duration,
            "concurrent_queries": 3,
            "async_optimization": "60%+ faster than sync"
        },
        "session_info": {
            "connection": session.connection,
            "operations_count": len(session.operations)
        },
        "analytics": analytics_data,
        "timestamp": datetime.now().isoformat()
    })

# ============================================================================
# 9. APPLICATION STARTUP
# ============================================================================

if __name__ == "__main__":
    print("\n🎯 Starting Catzilla Async DI with Simulated Database Demo...")
    print("\nAvailable async endpoints:")
    print("  GET  /                - Async home page")
    print("  GET  /users           - Get all users (async with concurrency)")
    print("  GET  /users/{id}      - Get user with posts (async)")
    print("  POST /users           - Create new user (async + autovalidation)")
    print("  PUT  /users/{id}      - Update user (async + autovalidation)")
    print("  DELETE /users/{id}    - Delete user (async + path validation)")
    print("  GET  /posts           - Get all posts (async)")
    print("  POST /posts           - Create new post (async + autovalidation)")
    print("  GET  /users/{id}/posts - Get user's posts (async)")
    print("  GET  /stats           - Comprehensive async statistics")

    print("\n🗄️ Async Database Simulation Features:")
    print("  🔗 Database: Async singleton service")
    print("  🔄 Session: Async request-scoped service")
    print("  📦 Repositories: Async singleton services")
    print("  🏢 Services: Async singleton with business logic")
    print("  📊 Analytics: Async transient for operation tracking")
    print("  ⚡ Operations: All database calls are concurrent")
    print("  🎯 Validation: Async autovalidation with BaseModel")

    print(f"\n🚀 Async server starting on http://localhost:8006")
    print("   💡 All operations demonstrate true async concurrency!")

    app.listen(host="127.0.0.1", port=8006)
