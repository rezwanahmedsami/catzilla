#!/usr/bin/env python3
"""
🗄️ Catzilla DI with SQLAlchemy Example

This example demonstrates how to integrate Catzilla's DI system with SQLAlchemy
for database operations with proper dependency injection patterns.

Features demonstrated:
- SQLAlchemy engine registration as singleton
- Database session management with request scope
- Repository pattern with DI
- Service layer with database dependencies
- Transaction management
- Connection pooling
"""

import time
from datetime import datetime
from typing import Dict, Any, Optional, List
from contextlib import contextmanager

from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text, ForeignKey, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship, scoped_session
from sqlalchemy.pool import StaticPool

from catzilla import Catzilla, service, Depends, JSONResponse, Path, BaseModel, Field
from catzilla.dependency_injection import set_default_container

# Initialize Catzilla with DI enabled and autovalidation
app = Catzilla(enable_di=True, auto_validation=True)
set_default_container(app.di_container)

print("🗄️ Catzilla DI with SQLAlchemy Example")
print("=" * 50)

# ============================================================================
# 1. DATABASE MODELS AND SETUP
# ============================================================================

Base = declarative_base()

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    posts = relationship("Post", back_populates="author")

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

    author = relationship("User", back_populates="posts")

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
# 2. DATABASE CONFIGURATION AND ENGINE (SINGLETON)
# ============================================================================

@service("database_config", scope="singleton")
class DatabaseConfig:
    """Database configuration service"""

    def __init__(self):
        # Using SQLite for demo - in production use PostgreSQL, MySQL, etc.
        self.database_url = "sqlite:///catzilla_example.db"
        self.echo = True  # Enable SQL query logging
        self.pool_size = 10
        self.max_overflow = 20
        self.pool_timeout = 30

        print("📋 Database configuration initialized")

@service("database_engine", scope="singleton")
class DatabaseEngine:
    """SQLAlchemy engine service (singleton)"""

    def __init__(self, config: DatabaseConfig = Depends("database_config")):
        self.config = config

        # Create SQLAlchemy engine
        self.engine = create_engine(
            config.database_url,
            echo=config.echo,
            poolclass=StaticPool,  # For SQLite
            connect_args={"check_same_thread": False}  # For SQLite
        )

        # Create all tables
        Base.metadata.create_all(self.engine)

        # Create session factory
        self.SessionLocal = sessionmaker(
            bind=self.engine,
            autocommit=False,
            autoflush=False
        )

        print(f"🔧 Database engine created: {config.database_url}")

        # Seed some initial data
        self._seed_data()

    def _seed_data(self):
        """Seed initial data for demonstration"""
        session = self.SessionLocal()
        try:
            # Check if data already exists
            if session.query(User).count() == 0:
                # Create sample users
                users = [
                    User(name="Alice Johnson", email="alice@example.com"),
                    User(name="Bob Smith", email="bob@example.com"),
                    User(name="Carol Brown", email="carol@example.com"),
                ]

                for user in users:
                    session.add(user)

                session.commit()

                # Create sample posts
                posts = [
                    Post(title="First Post", content="This is Alice's first post", author_id=1),
                    Post(title="Hello World", content="Bob's introduction", author_id=2),
                    Post(title="Getting Started", content="Carol's guide", author_id=3),
                    Post(title="Advanced Topics", content="Alice's advanced tutorial", author_id=1),
                ]

                for post in posts:
                    session.add(post)

                session.commit()
                print("🌱 Sample data seeded successfully")
        finally:
            session.close()

# ============================================================================
# 3. DATABASE SESSION MANAGEMENT (REQUEST SCOPE)
# ============================================================================

@service("database_session", scope="request")
class DatabaseSession:
    """Database session service (request-scoped)"""

    def __init__(self, db_engine: DatabaseEngine = Depends("database_engine")):
        self.db_engine = db_engine
        self.session = db_engine.SessionLocal()
        self.transaction_count = 0

        print("🔄 Database session created (request-scoped)")

    def get_session(self) -> Session:
        """Get the SQLAlchemy session"""
        return self.session

    @contextmanager
    def transaction(self):
        """Context manager for database transactions"""
        try:
            self.transaction_count += 1
            yield self.session
            self.session.commit()
            print(f"✅ Transaction {self.transaction_count} committed")
        except Exception as e:
            self.session.rollback()
            print(f"❌ Transaction {self.transaction_count} rolled back: {e}")
            raise

    def close(self):
        """Close the database session"""
        self.session.close()
        print("🔒 Database session closed")

# ============================================================================
# 4. REPOSITORY PATTERN WITH DI
# ============================================================================

@service("user_repository", scope="singleton")
class UserRepository:
    """User repository with database operations"""

    def __init__(self):
        print("👥 User repository initialized")

    def get_all(self, db_session: DatabaseSession) -> List[User]:
        """Get all users"""
        return db_session.get_session().query(User).all()

    def get_by_id(self, user_id: int, db_session: DatabaseSession) -> Optional[User]:
        """Get user by ID"""
        return db_session.get_session().query(User).filter(User.id == user_id).first()

    def get_by_email(self, email: str, db_session: DatabaseSession) -> Optional[User]:
        """Get user by email"""
        return db_session.get_session().query(User).filter(User.email == email).first()

    def create(self, name: str, email: str, db_session: DatabaseSession) -> User:
        """Create a new user"""
        user = User(name=name, email=email)
        with db_session.transaction():
            db_session.get_session().add(user)
            db_session.get_session().flush()  # To get the ID
        return user

    def update(self, user_id: int, db_session, **kwargs):
        """Update user with validated data"""
        user = db_session.query(User).filter(User.id == user_id).first()
        if user:
            for key, value in kwargs.items():
                if value is not None and hasattr(user, key):
                    setattr(user, key, value)
            db_session.commit()
            return user
        return None

    def delete(self, user_id: int, db_session):
        """Delete user and return success status"""
        user = db_session.query(User).filter(User.id == user_id).first()
        if user:
            db_session.delete(user)
            db_session.commit()
            return True
        return False

@service("post_repository", scope="singleton")
class PostRepository:
    """Post repository with database operations"""

    def __init__(self):
        print("📝 Post repository initialized")

    def get_all(self, db_session: DatabaseSession) -> List[Post]:
        """Get all posts"""
        return db_session.get_session().query(Post).all()

    def get_by_id(self, post_id: int, db_session: DatabaseSession) -> Optional[Post]:
        """Get post by ID"""
        return db_session.get_session().query(Post).filter(Post.id == post_id).first()

    def get_by_author(self, author_id: int, db_session: DatabaseSession) -> List[Post]:
        """Get posts by author"""
        return db_session.get_session().query(Post).filter(Post.author_id == author_id).all()

    def create(self, title: str, content: str, author_id: int, db_session: DatabaseSession) -> Post:
        """Create a new post"""
        post = Post(title=title, content=content, author_id=author_id)
        with db_session.transaction():
            db_session.get_session().add(post)
            db_session.get_session().flush()
        return post

    def update(self, post_id: int, db_session, **kwargs):
        """Update post with validated data"""
        post = db_session.query(Post).filter(Post.id == post_id).first()
        if post:
            for key, value in kwargs.items():
                if value is not None and hasattr(post, key):
                    setattr(post, key, value)
            db_session.commit()
            return post
        return None

    def delete(self, post_id: int, db_session):
        """Delete post and return success status"""
        post = db_session.query(Post).filter(Post.id == post_id).first()
        if post:
            db_session.delete(post)
            db_session.commit()
            return True
        return False

# ============================================================================
# 5. SERVICE LAYER WITH BUSINESS LOGIC
# ============================================================================

@service("user_service", scope="singleton")
class UserService:
    """User service with business logic"""

    def __init__(self, user_repo: UserRepository = Depends("user_repository")):
        self.user_repo = user_repo
        print("🏢 User service initialized")

    def get_all_users(self, db_session: DatabaseSession) -> List[Dict[str, Any]]:
        """Get all users with their data"""
        users = self.user_repo.get_all(db_session)
        return [user.to_dict() for user in users]

    def get_user_with_posts(self, user_id: int, db_session: DatabaseSession) -> Optional[Dict[str, Any]]:
        """Get user with their posts"""
        user = self.user_repo.get_by_id(user_id, db_session)
        if not user:
            return None

        user_data = user.to_dict()
        user_data["posts"] = [post.to_dict() for post in user.posts]
        return user_data

    def create_user(self, name: str, email: str, db_session: DatabaseSession) -> Dict[str, Any]:
        """Create a new user with validation"""
        # Check if email already exists
        existing_user = self.user_repo.get_by_email(email, db_session)
        if existing_user:
            raise ValueError(f"User with email {email} already exists")

        user = self.user_repo.create(name, email, db_session)
        return user.to_dict()

@service("post_service", scope="singleton")
class PostService:
    """Post service with business logic"""

    def __init__(self,
                 post_repo: PostRepository = Depends("post_repository"),
                 user_repo: UserRepository = Depends("user_repository")):
        self.post_repo = post_repo
        self.user_repo = user_repo
        print("📰 Post service initialized")

    def get_all_posts(self, db_session: DatabaseSession) -> List[Dict[str, Any]]:
        """Get all posts with author info"""
        posts = self.post_repo.get_all(db_session)
        return [post.to_dict() for post in posts]

    def create_post(self, title: str, content: str, author_id: int, db_session: DatabaseSession) -> Dict[str, Any]:
        """Create a new post with validation"""
        # Check if author exists
        author = self.user_repo.get_by_id(author_id, db_session)
        if not author:
            raise ValueError(f"Author with ID {author_id} not found")

        post = self.post_repo.create(title, content, author_id, db_session)
        return post.to_dict()

# ============================================================================
# 6. ANALYTICS SERVICE (TRANSIENT)
# ============================================================================

@service("analytics", scope="transient")
class AnalyticsService:
    """Analytics service for tracking operations"""

    def __init__(self):
        self.instance_id = str(time.time())[-6:]
        print(f"📊 Analytics service created (transient) - {self.instance_id}")

    def track_database_operation(self, operation: str, table: str, duration: float = None) -> Dict[str, Any]:
        """Track database operation"""
        return {
            "operation": operation,
            "table": table,
            "duration": duration,
            "timestamp": datetime.now().isoformat(),
            "analytics_instance": self.instance_id
        }

# ============================================================================
# 1.5. VALIDATION MODELS FOR AUTOVALIDATION
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
# 7. ROUTE HANDLERS WITH DATABASE OPERATIONS
# ============================================================================

@app.get("/")
def home(request):
    """Home page"""
    return JSONResponse({
        "message": "🗄️ Catzilla DI with SQLAlchemy Demo",
        "features": [
            "SQLAlchemy engine as singleton service",
            "Request-scoped database sessions",
            "Repository pattern with DI",
            "Service layer with business logic",
            "Transaction management",
            "Connection pooling"
        ]
    })

@app.get("/users")
def get_users(request,
              user_service: UserService = Depends("user_service"),
              db_session: DatabaseSession = Depends("database_session"),
              analytics: AnalyticsService = Depends("analytics")):
    """Get all users"""
    start_time = time.time()
    users = user_service.get_all_users(db_session)
    duration = time.time() - start_time

    analytics_data = analytics.track_database_operation("SELECT", "users", duration)

    return JSONResponse({
        "users": users,
        "count": len(users),
        "analytics": analytics_data
    })

@app.get("/users/{user_id}")
def get_user(request,
             user_id: int = Path(...),
             user_service: UserService = Depends("user_service"),
             db_session: DatabaseSession = Depends("database_session"),
             analytics: AnalyticsService = Depends("analytics")):
    """Get user with posts"""
    start_time = time.time()
    user = user_service.get_user_with_posts(user_id, db_session)
    duration = time.time() - start_time

    if not user:
        return JSONResponse({"error": "User not found"}, status_code=404)

    analytics_data = analytics.track_database_operation("SELECT", "users", duration)

    return JSONResponse({
        "user": user,
        "analytics": analytics_data
    })

@app.post("/users")
def create_user(request,
                user_data: UserCreateModel,
                user_service: UserService = Depends("user_service"),
                db_session: DatabaseSession = Depends("database_session"),
                analytics: AnalyticsService = Depends("analytics")):
    """Create a new user with autovalidation"""
    try:
        start_time = time.time()
        user = user_service.create_user(user_data.name, user_data.email, db_session)
        duration = time.time() - start_time

        analytics_data = analytics.track_database_operation("INSERT", "users", duration)

        return JSONResponse({
            "user": user,
            "analytics": analytics_data,
            "validation": {
                "autovalidated": True,
                "fields_validated": ["name", "email"]
            }
        }, status_code=201)
    except ValueError as e:
        return JSONResponse({"error": str(e)}, status_code=400)

@app.put("/users/{user_id}")
def update_user(request,
                user_id: int = Path(..., ge=1),
                user_data: UserUpdateModel = None,
                user_service: UserService = Depends("user_service"),
                db_session: DatabaseSession = Depends("database_session"),
                analytics: AnalyticsService = Depends("analytics"),
                user_repo: UserRepository = Depends("user_repository")):
    """Update user with autovalidation"""
    try:
        start_time = time.time()

        # Check if user exists
        existing_user = user_repo.get_by_id(user_id, db_session)
        if not existing_user:
            return JSONResponse({"error": "User not found"}, status_code=404)

        # Update user with validated data
        updated_user = user_repo.update(
            user_id,
            db_session,
            name=user_data.name if user_data else None,
            email=user_data.email if user_data else None
        )

        duration = time.time() - start_time
        analytics_data = analytics.track_database_operation("UPDATE", "users", duration)

        return JSONResponse({
            "user": updated_user.to_dict() if updated_user else None,
            "analytics": analytics_data,
            "validation": {
                "autovalidated": True,
                "fields_validated": ["name", "email"] if user_data else []
            }
        })
    except ValueError as e:
        return JSONResponse({"error": str(e)}, status_code=400)

@app.get("/posts")
def get_posts(request,
              post_service: PostService = Depends("post_service"),
              db_session: DatabaseSession = Depends("database_session"),
              analytics: AnalyticsService = Depends("analytics")):
    """Get all posts"""
    start_time = time.time()
    posts = post_service.get_all_posts(db_session)
    duration = time.time() - start_time

    analytics_data = analytics.track_database_operation("SELECT", "posts", duration)

    return JSONResponse({
        "posts": posts,
        "count": len(posts),
        "analytics": analytics_data
    })

@app.post("/posts")
def create_post(request,
                post_data: PostCreateModel,
                post_service: PostService = Depends("post_service"),
                db_session: DatabaseSession = Depends("database_session"),
                analytics: AnalyticsService = Depends("analytics")):
    """Create a new post with autovalidation"""
    try:
        start_time = time.time()
        post = post_service.create_post(post_data.title, post_data.content, post_data.author_id, db_session)
        duration = time.time() - start_time

        analytics_data = analytics.track_database_operation("INSERT", "posts", duration)

        return JSONResponse({
            "post": post,
            "analytics": analytics_data,
            "validation": {
                "autovalidated": True,
                "fields_validated": ["title", "content", "author_id"]
            }
        }, status_code=201)
    except ValueError as e:
        return JSONResponse({"error": str(e)}, status_code=400)

@app.put("/posts/{post_id}")
def update_post(request,
                post_id: int = Path(..., ge=1),
                post_data: PostUpdateModel = None,
                post_service: PostService = Depends("post_service"),
                db_session: DatabaseSession = Depends("database_session"),
                analytics: AnalyticsService = Depends("analytics"),
                post_repo: PostRepository = Depends("post_repository")):
    """Update post with autovalidation"""
    try:
        start_time = time.time()

        # Check if post exists
        existing_post = post_repo.get_by_id(post_id, db_session)
        if not existing_post:
            return JSONResponse({"error": "Post not found"}, status_code=404)

        # Update post with validated data
        updated_post = post_repo.update(
            post_id,
            db_session,
            title=post_data.title if post_data else None,
            content=post_data.content if post_data else None
        )

        duration = time.time() - start_time
        analytics_data = analytics.track_database_operation("UPDATE", "posts", duration)

        return JSONResponse({
            "post": updated_post.to_dict() if updated_post else None,
            "analytics": analytics_data,
            "validation": {
                "autovalidated": True,
                "fields_validated": ["title", "content"] if post_data else []
            }
        })
    except ValueError as e:
        return JSONResponse({"error": str(e)}, status_code=400)

@app.delete("/users/{user_id}")
def delete_user(request,
                user_id: int = Path(..., ge=1),
                user_service: UserService = Depends("user_service"),
                db_session: DatabaseSession = Depends("database_session"),
                analytics: AnalyticsService = Depends("analytics"),
                user_repo: UserRepository = Depends("user_repository")):
    """Delete user with path validation"""
    try:
        start_time = time.time()
        deleted = user_repo.delete(user_id, db_session)
        duration = time.time() - start_time

        analytics_data = analytics.track_database_operation("DELETE", "users", duration)

        if deleted:
            return JSONResponse({
                "message": f"User {user_id} deleted successfully",
                "analytics": analytics_data,
                "validation": {
                    "path_validated": True,
                    "user_id_constraint": "ge=1"
                }
            })
        else:
            return JSONResponse({"error": "User not found"}, status_code=404)
    except ValueError as e:
        return JSONResponse({"error": str(e)}, status_code=400)

@app.delete("/posts/{post_id}")
def delete_post(request,
                post_id: int = Path(..., ge=1),
                post_service: PostService = Depends("post_service"),
                db_session: DatabaseSession = Depends("database_session"),
                analytics: AnalyticsService = Depends("analytics"),
                post_repo: PostRepository = Depends("post_repository")):
    """Delete post with path validation"""
    try:
        start_time = time.time()
        deleted = post_repo.delete(post_id, db_session)
        duration = time.time() - start_time

        analytics_data = analytics.track_database_operation("DELETE", "posts", duration)

        if deleted:
            return JSONResponse({
                "message": f"Post {post_id} deleted successfully",
                "analytics": analytics_data,
                "validation": {
                    "path_validated": True,
                    "post_id_constraint": "ge=1"
                }
            })
        else:
            return JSONResponse({"error": "Post not found"}, status_code=404)
    except ValueError as e:
        return JSONResponse({"error": str(e)}, status_code=400)

@app.get("/validation/examples")
def get_validation_examples(request):
    """Get example payloads for testing autovalidation"""
    return JSONResponse({
        "validation_info": {
            "autovalidation": "enabled",
            "framework": "Catzilla v0.2.0",
            "performance": "100x faster than Pydantic"
        },
        "examples": {
            "create_user_valid": {
                "name": "John Doe",
                "email": "john@example.com"
            },
            "create_user_invalid": {
                "name": "Jo",  # Too short (min_length=2)
                "email": "invalid-email"  # Invalid format
            },
            "create_post_valid": {
                "title": "My First Post",
                "content": "This is the content of my first post on this platform.",
                "author_id": 1
            },
            "create_post_invalid": {
                "title": "Hi",  # Too short (min_length=5)
                "content": "Short",  # Too short (min_length=10)
                "author_id": 0  # Below minimum (ge=1)
            },
            "update_user_valid": {
                "name": "Jane Smith",
                "email": "jane@example.com"
            },
            "update_post_valid": {
                "title": "Updated Post Title",
                "content": "This is the updated content of the post with proper length."
            }
        },
        "endpoints": {
            "create_user": "POST /users",
            "update_user": "PUT /users/{user_id}",
            "delete_user": "DELETE /users/{user_id}",
            "create_post": "POST /posts",
            "update_post": "PUT /posts/{post_id}",
            "delete_post": "DELETE /posts/{post_id}"
        }
    })

# ============================================================================
# 8. APPLICATION STARTUP
# ============================================================================

if __name__ == "__main__":
    print("\n🎯 Starting Catzilla DI with SQLAlchemy Demo...")
    print("\nAvailable endpoints:")
    print("  GET  /                - Home page")
    print("  GET  /users           - Get all users")
    print("  GET  /users/{id}      - Get user with posts")
    print("  POST /users           - Create new user")
    print("  PUT  /users/{id}      - Update user")
    print("  DELETE /users/{id}    - Delete user")
    print("  GET  /posts           - Get all posts")
    print("  POST /posts           - Create new post")
    print("  PUT  /posts/{id}      - Update post")
    print("  DELETE /posts/{id}    - Delete post")
    print("  GET  /database/stats  - Database statistics")
    print("  GET  /health          - Health check")

    print("\n🗄️ SQLAlchemy Integration:")
    print("  🔗 Engine: Singleton service")
    print("  🔄 Session: Request-scoped service")
    print("  📦 Repositories: Singleton services")
    print("  🏢 Services: Singleton with business logic")
    print("  📊 Analytics: Transient for operation tracking")

    print(f"\n🚀 Server starting on http://localhost:8004")
    print("   Try: curl http://localhost:8004/health")
    print("   Try: curl http://localhost:8004/users")

    app.listen(8004)
