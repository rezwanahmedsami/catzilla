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
print("=" * 50)

# ============================================================================
# 1. ASYNC DATABASE MODELS AND SETUP
# ============================================================================

Base = declarative_base()

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    posts = relationship("Post", back_populates="author", lazy="selectin")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "posts_count": len(self.posts) if self.posts else 0
        }

class Post(Base):
    __tablename__ = "posts"

    id = Column(Integer, primary_key=True)
    title = Column(String(200), nullable=False)
    content = Column(Text)
    author_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)

    author = relationship("User", back_populates="posts", lazy="selectin")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "content": self.content,
            "author_id": self.author_id,
            "author_name": self.author.name if self.author else None,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }

# ============================================================================
# 2. ASYNC DATABASE CONFIGURATION AND ENGINE (SINGLETON)
# ============================================================================

@service("async_database_config", scope="singleton")
class AsyncDatabaseConfig:
    """Async database configuration service"""

    def __init__(self):
        # Using async SQLite for demo - in production use asyncpg for PostgreSQL
        self.database_url = "sqlite+aiosqlite:///catzilla_async_example.db"
        self.echo = True  # Enable SQL query logging
        self.pool_size = 10
        self.max_overflow = 20
        self.pool_timeout = 30

        print("📋 Async Database configuration initialized")

@service("async_database_engine", scope="singleton")
class AsyncDatabaseEngine:
    """Async SQLAlchemy engine service (singleton)"""

    def __init__(self, config: AsyncDatabaseConfig = Depends("async_database_config")):
        self.config = config

        # Create async SQLAlchemy engine
        self.engine = create_async_engine(
            config.database_url,
            echo=config.echo,
            poolclass=StaticPool,  # For SQLite
            connect_args={"check_same_thread": False}  # For SQLite
        )

        # Create async session factory
        self.AsyncSessionLocal = async_sessionmaker(
            bind=self.engine,
            class_=AsyncSession,
            autocommit=False,
            autoflush=False,
            expire_on_commit=False
        )

        print(f"🔧 Async Database engine created: {config.database_url}")

        # Initialize database
        asyncio.create_task(self._initialize_database())

    async def _initialize_database(self):
        """Initialize database and seed data"""
        try:
            # Create all tables
            async with self.engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)

            print("📋 Database tables created")

            # Seed data
            await self._seed_data()
        except Exception as e:
            print(f"❌ Database initialization error: {e}")

    async def _seed_data(self):
        """Seed initial data for demonstration"""
        async with self.AsyncSessionLocal() as session:
            try:
                # Check if data already exists
                result = await session.execute(select(User))
                if not result.scalars().first():
                    # Create sample users
                    users = [
                        User(name="Alice Johnson", email="alice@example.com"),
                        User(name="Bob Smith", email="bob@example.com"),
                        User(name="Carol Brown", email="carol@example.com"),
                        User(name="David Wilson", email="david@example.com")
                    ]

                    for user in users:
                        session.add(user)

                    await session.commit()

                    # Get user IDs after commit
                    result = await session.execute(select(User))
                    users_with_ids = result.scalars().all()

                    # Create sample posts
                    posts = [
                        Post(title="Async Programming Guide", content="This is Alice's guide to async programming", author_id=users_with_ids[0].id),
                        Post(title="Hello Async World", content="Bob's introduction to async operations", author_id=users_with_ids[1].id),
                        Post(title="Concurrent Operations", content="Carol's tutorial on concurrency", author_id=users_with_ids[2].id),
                        Post(title="Advanced Async Patterns", content="Alice's advanced async tutorial", author_id=users_with_ids[0].id),
                        Post(title="Database Async Operations", content="David's guide to async databases", author_id=users_with_ids[3].id),
                    ]

                    for post in posts:
                        session.add(post)

                    await session.commit()
                    print("🌱 Async sample data seeded successfully")
            except Exception as e:
                await session.rollback()
                print(f"❌ Error seeding data: {e}")

# ============================================================================
# 3. ASYNC DATABASE SESSION MANAGEMENT (REQUEST SCOPE)
# ============================================================================

@service("async_database_session", scope="request")
class AsyncDatabaseSession:
    """Async database session service (request-scoped)"""

    def __init__(self, db_engine: AsyncDatabaseEngine = Depends("async_database_engine")):
        self.db_engine = db_engine
        self.session = None
        self.transaction_count = 0

        print("🔄 Async Database session initialized (request-scoped)")

    async def get_session(self) -> AsyncSession:
        """Get the async SQLAlchemy session"""
        if self.session is None:
            self.session = self.db_engine.AsyncSessionLocal()
        return self.session

    @asynccontextmanager
    async def transaction(self):
        """Async context manager for database transactions"""
        session = await self.get_session()
        try:
            self.transaction_count += 1
            yield session
            await session.commit()
            print(f"✅ Async transaction {self.transaction_count} committed")
        except Exception as e:
            await session.rollback()
            print(f"❌ Async transaction {self.transaction_count} rolled back: {e}")
            raise

    async def close(self):
        """Close the async database session"""
        if self.session:
            await self.session.close()
            print("🔒 Async Database session closed")

# ============================================================================
# 4. ASYNC REPOSITORY PATTERN WITH DI
# ============================================================================

@service("async_user_repository", scope="singleton")
class AsyncUserRepository:
    """Async user repository with database operations"""

    def __init__(self):
        print("👥 Async User repository initialized")

    async def get_all(self, db_session: AsyncDatabaseSession) -> List[User]:
        """Get all users asynchronously"""
        session = await db_session.get_session()
        result = await session.execute(select(User).options(selectinload(User.posts)))
        return result.scalars().all()

    async def get_by_id(self, user_id: int, db_session: AsyncDatabaseSession) -> Optional[User]:
        """Get user by ID asynchronously"""
        session = await db_session.get_session()
        result = await session.execute(
            select(User).options(selectinload(User.posts)).where(User.id == user_id)
        )
        return result.scalars().first()

    async def get_by_email(self, email: str, db_session: AsyncDatabaseSession) -> Optional[User]:
        """Get user by email asynchronously"""
        session = await db_session.get_session()
        result = await session.execute(select(User).where(User.email == email))
        return result.scalars().first()

    async def create(self, name: str, email: str, db_session: AsyncDatabaseSession) -> User:
        """Create a new user asynchronously"""
        user = User(name=name, email=email)
        async with db_session.transaction() as session:
            session.add(user)
            await session.flush()  # To get the ID
        return user

    async def update(self, user_id: int, db_session: AsyncDatabaseSession, **kwargs) -> Optional[User]:
        """Update user asynchronously"""
        session = await db_session.get_session()
        async with db_session.transaction():
            result = await session.execute(
                update(User).where(User.id == user_id).values(**kwargs).returning(User)
            )
            updated_user = result.scalars().first()
            if updated_user:
                await session.refresh(updated_user)
            return updated_user

    async def delete(self, user_id: int, db_session: AsyncDatabaseSession) -> bool:
        """Delete user asynchronously"""
        session = await db_session.get_session()
        async with db_session.transaction():
            result = await session.execute(delete(User).where(User.id == user_id))
            return result.rowcount > 0

@service("async_post_repository", scope="singleton")
class AsyncPostRepository:
    """Async post repository with database operations"""

    def __init__(self):
        print("📝 Async Post repository initialized")

    async def get_all(self, db_session: AsyncDatabaseSession) -> List[Post]:
        """Get all posts asynchronously"""
        session = await db_session.get_session()
        result = await session.execute(select(Post).options(selectinload(Post.author)))
        return result.scalars().all()

    async def get_by_id(self, post_id: int, db_session: AsyncDatabaseSession) -> Optional[Post]:
        """Get post by ID asynchronously"""
        session = await db_session.get_session()
        result = await session.execute(
            select(Post).options(selectinload(Post.author)).where(Post.id == post_id)
        )
        return result.scalars().first()

    async def get_by_author(self, author_id: int, db_session: AsyncDatabaseSession) -> List[Post]:
        """Get posts by author asynchronously"""
        session = await db_session.get_session()
        result = await session.execute(
            select(Post).options(selectinload(Post.author)).where(Post.author_id == author_id)
        )
        return result.scalars().all()

    async def create(self, title: str, content: str, author_id: int, db_session: AsyncDatabaseSession) -> Post:
        """Create a new post asynchronously"""
        post = Post(title=title, content=content, author_id=author_id)
        async with db_session.transaction() as session:
            session.add(post)
            await session.flush()
        return post

    async def update(self, post_id: int, db_session: AsyncDatabaseSession, **kwargs) -> Optional[Post]:
        """Update post asynchronously"""
        session = await db_session.get_session()
        async with db_session.transaction():
            result = await session.execute(
                update(Post).where(Post.id == post_id).values(**kwargs).returning(Post)
            )
            updated_post = result.scalars().first()
            if updated_post:
                await session.refresh(updated_post, ["author"])
            return updated_post

    async def delete(self, post_id: int, db_session: AsyncDatabaseSession) -> bool:
        """Delete post asynchronously"""
        session = await db_session.get_session()
        async with db_session.transaction():
            result = await session.execute(delete(Post).where(Post.id == post_id))
            return result.rowcount > 0

# ============================================================================
# 5. ASYNC SERVICE LAYER WITH BUSINESS LOGIC
# ============================================================================

@service("async_user_service", scope="singleton")
class AsyncUserService:
    """Async user service with business logic"""

    def __init__(self, user_repo: AsyncUserRepository = Depends("async_user_repository")):
        self.user_repo = user_repo
        print("🏢 Async User service initialized")

    async def get_all_users(self, db_session: AsyncDatabaseSession) -> List[Dict[str, Any]]:
        """Get all users with their data asynchronously"""
        users = await self.user_repo.get_all(db_session)
        return [user.to_dict() for user in users]

    async def get_user_with_posts(self, user_id: int, db_session: AsyncDatabaseSession) -> Optional[Dict[str, Any]]:
        """Get user with their posts asynchronously"""
        user = await self.user_repo.get_by_id(user_id, db_session)
        if not user:
            return None

        user_data = user.to_dict()
        user_data["posts"] = [post.to_dict() for post in user.posts]
        return user_data

    async def create_user(self, name: str, email: str, db_session: AsyncDatabaseSession) -> Dict[str, Any]:
        """Create a new user with async validation"""
        # Check if email already exists
        existing_user = await self.user_repo.get_by_email(email, db_session)
        if existing_user:
            raise ValueError(f"User with email {email} already exists")

        user = await self.user_repo.create(name, email, db_session)
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

    async def get_all_posts(self, db_session: AsyncDatabaseSession) -> List[Dict[str, Any]]:
        """Get all posts with author info asynchronously"""
        posts = await self.post_repo.get_all(db_session)
        return [post.to_dict() for post in posts]

    async def create_post(self, title: str, content: str, author_id: int, db_session: AsyncDatabaseSession) -> Dict[str, Any]:
        """Create a new post with async validation"""
        # Check if author exists
        author = await self.user_repo.get_by_id(author_id, db_session)
        if not author:
            raise ValueError(f"Author with ID {author_id} not found")

        post = await self.post_repo.create(title, content, author_id, db_session)
        return post.to_dict()

    async def get_user_posts(self, user_id: int, db_session: AsyncDatabaseSession) -> List[Dict[str, Any]]:
        """Get all posts by a specific user"""
        posts = await self.post_repo.get_by_author(user_id, db_session)
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

    async def track_async_operation(self, operation: str, table: str, duration: float = None) -> Dict[str, Any]:
        """Track async database operation"""
        # Simulate async analytics processing
        await asyncio.sleep(0.001)

        return {
            "operation": operation,
            "table": table,
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

class PostUpdateModel(BaseModel):
    """Post update model with autovalidation"""
    title: Optional[str] = Field(None, min_length=5, max_length=200, description="Post title")
    content: Optional[str] = Field(None, min_length=10, max_length=5000, description="Post content")

# ============================================================================
# 8. ASYNC ROUTE HANDLERS WITH DATABASE OPERATIONS
# ============================================================================

@app.get("/")
async def async_home(request):
    """Async home page"""
    return JSONResponse({
        "message": "🗄️ Catzilla Async DI with SQLAlchemy Demo",
        "features": [
            "Async SQLAlchemy engine as singleton service",
            "Async request-scoped database sessions",
            "Async repository pattern with DI",
            "Async service layer with business logic",
            "Async transaction management",
            "Concurrent database operations"
        ],
        "performance": "60%+ faster than FastAPI async",
        "async_support": True
    })

@app.get("/users")
async def get_users_async(request,
                         user_service: AsyncUserService = Depends("async_user_service"),
                         db_session: AsyncDatabaseSession = Depends("async_database_session"),
                         analytics: AsyncAnalyticsService = Depends("async_analytics")):
    """Get all users asynchronously"""
    start_time = time.time()

    # Run user fetch and analytics concurrently
    users_task = asyncio.create_task(user_service.get_all_users(db_session))
    analytics_task = asyncio.create_task(analytics.track_async_operation("SELECT", "users"))

    users, analytics_data = await asyncio.gather(users_task, analytics_task)

    duration = time.time() - start_time
    analytics_data["duration"] = duration

    return JSONResponse({
        "users": users,
        "count": len(users),
        "analytics": analytics_data,
        "concurrent_operations": 2
    })

@app.get("/users/{user_id}")
async def get_user_async(request,
                        user_id: int = Path(...),
                        user_service: AsyncUserService = Depends("async_user_service"),
                        db_session: AsyncDatabaseSession = Depends("async_database_session"),
                        analytics: AsyncAnalyticsService = Depends("async_analytics")):
    """Get user with posts asynchronously"""
    start_time = time.time()

    # Run user fetch and analytics concurrently
    user_task = asyncio.create_task(user_service.get_user_with_posts(user_id, db_session))
    analytics_task = asyncio.create_task(analytics.track_async_operation("SELECT", "users"))

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
                           user_data: UserCreateModel,
                           user_service: AsyncUserService = Depends("async_user_service"),
                           db_session: AsyncDatabaseSession = Depends("async_database_session"),
                           analytics: AsyncAnalyticsService = Depends("async_analytics")):
    """Create a new user asynchronously with autovalidation"""
    try:
        start_time = time.time()

        # Run user creation and analytics tracking concurrently
        user_task = asyncio.create_task(user_service.create_user(user_data.name, user_data.email, db_session))
        analytics_task = asyncio.create_task(analytics.track_async_operation("INSERT", "users"))

        user, analytics_data = await asyncio.gather(user_task, analytics_task)

        duration = time.time() - start_time
        analytics_data["duration"] = duration

        return JSONResponse({
            "user": user,
            "analytics": analytics_data,
            "validation": {
                "autovalidated": True,
                "fields_validated": ["name", "email"]
            },
            "concurrent_operations": 2
        }, status_code=201)
    except ValueError as e:
        return JSONResponse({"error": str(e)}, status_code=400)

@app.put("/users/{user_id}")
async def update_user_async(request,
                           user_id: int = Path(..., ge=1),
                           user_data: UserUpdateModel = None,
                           user_repo: AsyncUserRepository = Depends("async_user_repository"),
                           db_session: AsyncDatabaseSession = Depends("async_database_session"),
                           analytics: AsyncAnalyticsService = Depends("async_analytics")):
    """Update user asynchronously with autovalidation"""
    try:
        start_time = time.time()

        # Check if user exists and update concurrently with analytics
        user_check_task = asyncio.create_task(user_repo.get_by_id(user_id, db_session))
        analytics_task = asyncio.create_task(analytics.track_async_operation("UPDATE", "users"))

        existing_user, analytics_data = await asyncio.gather(user_check_task, analytics_task)

        if not existing_user:
            return JSONResponse({"error": "User not found"}, status_code=404)

        # Update user with validated data
        update_data = {}
        if user_data and user_data.name is not None:
            update_data["name"] = user_data.name
        if user_data and user_data.email is not None:
            update_data["email"] = user_data.email

        if not update_data:
            return JSONResponse({"error": "No update data provided"}, status_code=400)

        updated_user = await user_repo.update(user_id, db_session, **update_data)

        duration = time.time() - start_time
        analytics_data["duration"] = duration

        return JSONResponse({
            "user": updated_user.to_dict() if updated_user else None,
            "analytics": analytics_data,
            "validation": {
                "autovalidated": True,
                "fields_validated": list(update_data.keys())
            },
            "concurrent_operations": 2
        })
    except ValueError as e:
        return JSONResponse({"error": str(e)}, status_code=400)

@app.delete("/users/{user_id}")
async def delete_user_async(request,
                           user_id: int = Path(..., ge=1),
                           user_repo: AsyncUserRepository = Depends("async_user_repository"),
                           db_session: AsyncDatabaseSession = Depends("async_database_session"),
                           analytics: AsyncAnalyticsService = Depends("async_analytics")):
    """Delete user asynchronously with path validation"""
    try:
        start_time = time.time()

        # Run deletion and analytics concurrently
        delete_task = asyncio.create_task(user_repo.delete(user_id, db_session))
        analytics_task = asyncio.create_task(analytics.track_async_operation("DELETE", "users"))

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
                         db_session: AsyncDatabaseSession = Depends("async_database_session"),
                         analytics: AsyncAnalyticsService = Depends("async_analytics")):
    """Get all posts asynchronously"""
    start_time = time.time()

    # Run posts fetch and analytics concurrently
    posts_task = asyncio.create_task(post_service.get_all_posts(db_session))
    analytics_task = asyncio.create_task(analytics.track_async_operation("SELECT", "posts"))

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
                           post_data: PostCreateModel,
                           post_service: AsyncPostService = Depends("async_post_service"),
                           db_session: AsyncDatabaseSession = Depends("async_database_session"),
                           analytics: AsyncAnalyticsService = Depends("async_analytics")):
    """Create a new post asynchronously with autovalidation"""
    try:
        start_time = time.time()

        # Run post creation and analytics tracking concurrently
        post_task = asyncio.create_task(post_service.create_post(post_data.title, post_data.content, post_data.author_id, db_session))
        analytics_task = asyncio.create_task(analytics.track_async_operation("INSERT", "posts"))

        post, analytics_data = await asyncio.gather(post_task, analytics_task)

        duration = time.time() - start_time
        analytics_data["duration"] = duration

        return JSONResponse({
            "post": post,
            "analytics": analytics_data,
            "validation": {
                "autovalidated": True,
                "fields_validated": ["title", "content", "author_id"]
            },
            "concurrent_operations": 2
        }, status_code=201)
    except ValueError as e:
        return JSONResponse({"error": str(e)}, status_code=400)

@app.get("/users/{user_id}/posts")
async def get_user_posts_async(request,
                              user_id: int = Path(...),
                              post_service: AsyncPostService = Depends("async_post_service"),
                              user_repo: AsyncUserRepository = Depends("async_user_repository"),
                              db_session: AsyncDatabaseSession = Depends("async_database_session"),
                              analytics: AsyncAnalyticsService = Depends("async_analytics")):
    """Get all posts by a specific user asynchronously"""
    start_time = time.time()

    # Check user exists and get posts concurrently
    user_check_task = asyncio.create_task(user_repo.get_by_id(user_id, db_session))
    posts_task = asyncio.create_task(post_service.get_user_posts(user_id, db_session))
    analytics_task = asyncio.create_task(analytics.track_async_operation("SELECT", "posts"))

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
                         db_session: AsyncDatabaseSession = Depends("async_database_session"),
                         analytics: AsyncAnalyticsService = Depends("async_analytics")):
    """Get comprehensive async database statistics"""
    start_time = time.time()

    # Run all stats queries concurrently
    users_task = asyncio.create_task(user_service.get_all_users(db_session))
    posts_task = asyncio.create_task(post_service.get_all_posts(db_session))
    analytics_task = asyncio.create_task(analytics.track_async_operation("SELECT", "multiple"))

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
        "analytics": analytics_data,
        "timestamp": datetime.now().isoformat()
    })

# ============================================================================
# 9. APPLICATION STARTUP
# ============================================================================

if __name__ == "__main__":
    print("\n🎯 Starting Catzilla Async DI with SQLAlchemy Demo...")
    print("\nAvailable async endpoints:")
    print("  GET  /                - Async home page")
    print("  GET  /users           - Get all users (async)")
    print("  GET  /users/{id}      - Get user with posts (async)")
    print("  POST /users           - Create new user (async)")
    print("  PUT  /users/{id}      - Update user (async)")
    print("  DELETE /users/{id}    - Delete user (async)")
    print("  GET  /posts           - Get all posts (async)")
    print("  POST /posts           - Create new post (async)")
    print("  GET  /users/{id}/posts - Get user's posts (async)")
    print("  GET  /stats           - Async database statistics")

    print("\n🗄️ Async SQLAlchemy Integration:")
    print("  🔗 Engine: Async singleton service")
    print("  🔄 Session: Async request-scoped service")
    print("  📦 Repositories: Async singleton services")
    print("  🏢 Services: Async singleton with business logic")
    print("  📊 Analytics: Async transient for operation tracking")
    print("  ⚡ Operations: All database calls are concurrent")

    print(f"\n🚀 Async server starting on http://localhost:8005")
    print("   Try: curl http://localhost:8005/")
    print("   Try: curl http://localhost:8005/users")

    app.listen(host="127.0.0.1", port=8005)
