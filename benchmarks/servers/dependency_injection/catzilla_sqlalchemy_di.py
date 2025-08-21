#!/usr/bin/env python3
"""
🗄️ Catzilla SQLAlchemy DI Benchmark Server

This server benchmarks Catzilla's DI system with real SQLAlchemy database operations.
Based on the sqlalchemy_example.py but optimized for performance benchmarking.

Features benchmarked:
- SQLAlchemy engine registration as singleton
- Database session management with request scope
- Repository pattern with DI
- Service layer with database dependencies
- Real database operations (CRUD)
- Transaction management
"""

import sys
import os
import time
from datetime import datetime
from typing import Dict, Any, Optional, List
from contextlib import contextmanager

# Add the catzilla package to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', 'python'))

from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship
from sqlalchemy.pool import StaticPool

from catzilla import Catzilla, service, Depends, JSONResponse, BaseModel, Path, Query
from catzilla.dependency_injection import set_default_container

# Initialize Catzilla with DI enabled for production performance
app = Catzilla(
    enable_di=True,
    production=True,
    use_jemalloc=True,
    auto_validation=False,  # Disabled for pure performance
    show_banner=False,
    log_requests=False
)

set_default_container(app.di_container)

print("🗄️ Catzilla SQLAlchemy DI Benchmark Server")

# ============================================================================
# 1. DATABASE MODELS
# ============================================================================

Base = declarative_base()

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    posts = relationship("Post", back_populates="author", lazy="select")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }

class Post(Base):
    __tablename__ = "posts"

    id = Column(Integer, primary_key=True)
    title = Column(String(200), nullable=False)
    content = Column(Text)
    author_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)

    author = relationship("User", back_populates="posts", lazy="select")

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
        # Using in-memory SQLite for consistent benchmarking
        self.database_url = "sqlite:///:memory:"
        self.echo = False  # Disable for performance
        self.pool_size = 10
        self.max_overflow = 20

@service("database_engine", scope="singleton")
class DatabaseEngine:
    """SQLAlchemy engine service (singleton)"""

    def __init__(self, config: DatabaseConfig = Depends("database_config")):
        self.config = config

        # Create SQLAlchemy engine optimized for performance
        self.engine = create_engine(
            config.database_url,
            echo=config.echo,
            poolclass=StaticPool,
            connect_args={"check_same_thread": False}
        )

        # Create all tables
        Base.metadata.create_all(self.engine)

        # Create session factory
        self.SessionLocal = sessionmaker(
            bind=self.engine,
            autocommit=False,
            autoflush=False
        )

        # Seed benchmark data
        self._seed_benchmark_data()

    def _seed_benchmark_data(self):
        """Seed data optimized for benchmarking"""
        session = self.SessionLocal()
        try:
            # Create 1000 users for realistic load testing
            users = []
            for i in range(1000):
                user = User(
                    name=f"User {i}",
                    email=f"user{i}@benchmark.com"
                )
                users.append(user)

            session.add_all(users)
            session.commit()

            # Create 5000 posts for realistic load testing
            posts = []
            for i in range(5000):
                post = Post(
                    title=f"Post Title {i}",
                    content=f"This is the content for post number {i}. " * 10,  # Realistic content size
                    author_id=(i % 1000) + 1  # Distribute posts among users
                )
                posts.append(post)

            session.add_all(posts)
            session.commit()

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

    def get_session(self) -> Session:
        """Get the SQLAlchemy session"""
        return self.session

    @contextmanager
    def transaction(self):
        """Context manager for database transactions"""
        try:
            yield self.session
            self.session.commit()
        except Exception:
            self.session.rollback()
            raise

    def close(self):
        """Close the database session"""
        self.session.close()

# ============================================================================
# 4. REPOSITORY PATTERN WITH DI
# ============================================================================

@service("user_repository", scope="singleton")
class UserRepository:
    """User repository with database operations"""

    def get_all(self, db_session: DatabaseSession, limit: int = 100) -> List[User]:
        """Get all users with limit for performance"""
        return db_session.get_session().query(User).limit(limit).all()

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
            db_session.get_session().flush()
        return user

    def update(self, user_id: int, db_session: DatabaseSession, **kwargs) -> Optional[User]:
        """Update user"""
        user = self.get_by_id(user_id, db_session)
        if user:
            for key, value in kwargs.items():
                if value is not None and hasattr(user, key):
                    setattr(user, key, value)
            with db_session.transaction():
                pass  # Changes are already tracked
            return user
        return None

    def delete(self, user_id: int, db_session: DatabaseSession) -> bool:
        """Delete user"""
        user = self.get_by_id(user_id, db_session)
        if user:
            with db_session.transaction():
                db_session.get_session().delete(user)
            return True
        return False

@service("post_repository", scope="singleton")
class PostRepository:
    """Post repository with database operations"""

    def get_all(self, db_session: DatabaseSession, limit: int = 100) -> List[Post]:
        """Get all posts with limit for performance"""
        return db_session.get_session().query(Post).limit(limit).all()

    def get_by_id(self, post_id: int, db_session: DatabaseSession) -> Optional[Post]:
        """Get post by ID"""
        return db_session.get_session().query(Post).filter(Post.id == post_id).first()

    def get_by_author(self, author_id: int, db_session: DatabaseSession, limit: int = 100) -> List[Post]:
        """Get posts by author with limit for performance"""
        return db_session.get_session().query(Post).filter(Post.author_id == author_id).limit(limit).all()

    def create(self, title: str, content: str, author_id: int, db_session: DatabaseSession) -> Post:
        """Create a new post"""
        post = Post(title=title, content=content, author_id=author_id)
        with db_session.transaction():
            db_session.get_session().add(post)
            db_session.get_session().flush()
        return post

    def update(self, post_id: int, db_session: DatabaseSession, **kwargs) -> Optional[Post]:
        """Update post"""
        post = self.get_by_id(post_id, db_session)
        if post:
            for key, value in kwargs.items():
                if value is not None and hasattr(post, key):
                    setattr(post, key, value)
            with db_session.transaction():
                pass  # Changes are already tracked
            return post
        return None

    def delete(self, post_id: int, db_session: DatabaseSession) -> bool:
        """Delete post"""
        post = self.get_by_id(post_id, db_session)
        if post:
            with db_session.transaction():
                db_session.get_session().delete(post)
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

    def get_all_users(self, db_session: DatabaseSession, limit: int = 100) -> List[Dict[str, Any]]:
        """Get all users with business logic"""
        users = self.user_repo.get_all(db_session, limit)
        return [user.to_dict() for user in users]

    def get_user_with_posts(self, user_id: int, db_session: DatabaseSession,
                           post_repo: PostRepository = Depends("post_repository")) -> Optional[Dict[str, Any]]:
        """Get user with their posts"""
        user = self.user_repo.get_by_id(user_id, db_session)
        if user:
            posts = post_repo.get_by_author(user_id, db_session, limit=10)
            user_dict = user.to_dict()
            user_dict["posts"] = [post.to_dict() for post in posts]
            user_dict["posts_count"] = len(posts)
            return user_dict
        return None

    def create_user(self, name: str, email: str, db_session: DatabaseSession) -> Dict[str, Any]:
        """Create user with business validation"""
        # Simple email validation
        if "@" not in email:
            raise ValueError("Invalid email format")

        # Check if email already exists
        existing_user = self.user_repo.get_by_email(email, db_session)
        if existing_user:
            raise ValueError("Email already exists")

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

    def get_all_posts(self, db_session: DatabaseSession, limit: int = 100) -> List[Dict[str, Any]]:
        """Get all posts with business logic"""
        posts = self.post_repo.get_all(db_session, limit)
        return [post.to_dict() for post in posts]

    def create_post(self, title: str, content: str, author_id: int, db_session: DatabaseSession) -> Dict[str, Any]:
        """Create post with business validation"""
        # Validate author exists
        author = self.user_repo.get_by_id(author_id, db_session)
        if not author:
            raise ValueError("Author not found")

        # Basic validation
        if len(title) < 5:
            raise ValueError("Title too short")
        if len(content) < 10:
            raise ValueError("Content too short")

        post = self.post_repo.create(title, content, author_id, db_session)
        return post.to_dict()

# ============================================================================
# 6. ANALYTICS SERVICE (TRANSIENT)
# ============================================================================

@service("analytics", scope="transient")
class AnalyticsService:
    """Analytics service for tracking operations"""

    def __init__(self):
        self.instance_id = time.time()

    def track_operation(self, operation: str, table: str, duration: float = None) -> Dict[str, Any]:
        """Track database operation for benchmarking"""
        return {
            "operation": operation,
            "table": table,
            "duration_ms": round(duration * 1000, 2) if duration else None,
            "timestamp": time.time(),
            "analytics_instance": self.instance_id
        }

# ============================================================================
# 7. BENCHMARK ENDPOINTS
# ============================================================================

@app.get("/")
def home(request):
    """Home endpoint - basic DI overhead test"""
    return JSONResponse({
        "message": "Catzilla SQLAlchemy DI Benchmark",
        "framework": "catzilla",
        "di_system": "enabled",
        "database": "sqlalchemy",
        "features": ["dependency_injection", "sqlalchemy", "repository_pattern", "services"]
    })

@app.get("/health")
def health_check(request,
                db_session: DatabaseSession = Depends("database_session")):
    """Health check with database connection test"""
    try:
        # Simple database query to test connection
        user_count = db_session.get_session().query(User).count()
        post_count = db_session.get_session().query(Post).count()

        return JSONResponse({
            "status": "healthy",
            "database": "connected",
            "data": {
                "users": user_count,
                "posts": post_count
            }
        })
    except Exception as e:
        return JSONResponse({
            "status": "unhealthy",
            "database": "disconnected",
            "error": str(e)
        }, status_code=500)

@app.get("/users")
def get_users(request,
              limit: int = Query(100, ge=1, le=1000),
              user_service: UserService = Depends("user_service"),
              db_session: DatabaseSession = Depends("database_session"),
              analytics: AnalyticsService = Depends("analytics")):
    """Get all users - tests singleton service DI with database operations"""
    start_time = time.time()
    users = user_service.get_all_users(db_session, limit)
    duration = time.time() - start_time

    analytics_data = analytics.track_operation("SELECT", "users", duration)

    return JSONResponse({
        "users": users,
        "count": len(users),
        "analytics": analytics_data
    })

@app.get("/users/{user_id}")
def get_user(request,
             user_id: int = Path(..., ge=1),
             user_service: UserService = Depends("user_service"),
             post_repo: PostRepository = Depends("post_repository"),
             db_session: DatabaseSession = Depends("database_session"),
             analytics: AnalyticsService = Depends("analytics")):
    """Get user with posts - tests complex DI chain with multiple repositories"""
    start_time = time.time()
    user = user_service.get_user_with_posts(user_id, db_session, post_repo)
    duration = time.time() - start_time

    if not user:
        return JSONResponse({"error": "User not found"}, status_code=404)

    analytics_data = analytics.track_operation("SELECT_JOIN", "users_posts", duration)

    return JSONResponse({
        "user": user,
        "analytics": analytics_data
    })

@app.get("/posts")
def get_posts(request,
              limit: int = Query(100, ge=1, le=1000),
              post_service: PostService = Depends("post_service"),
              db_session: DatabaseSession = Depends("database_session"),
              analytics: AnalyticsService = Depends("analytics")):
    """Get all posts - tests service layer DI with database operations"""
    start_time = time.time()
    posts = post_service.get_all_posts(db_session, limit)
    duration = time.time() - start_time

    analytics_data = analytics.track_operation("SELECT", "posts", duration)

    return JSONResponse({
        "posts": posts,
        "count": len(posts),
        "analytics": analytics_data
    })

@app.get("/posts/by-user/{user_id}")
def get_posts_by_user(request,
                     user_id: int = Path(..., ge=1),
                     limit: int = Query(100, ge=1, le=1000),
                     post_repo: PostRepository = Depends("post_repository"),
                     db_session: DatabaseSession = Depends("database_session"),
                     analytics: AnalyticsService = Depends("analytics")):
    """Get posts by user - tests repository DI with filtered queries"""
    start_time = time.time()
    posts = post_repo.get_by_author(user_id, db_session, limit)
    duration = time.time() - start_time

    analytics_data = analytics.track_operation("SELECT_FILTERED", "posts", duration)

    return JSONResponse({
        "posts": [post.to_dict() for post in posts],
        "count": len(posts),
        "user_id": user_id,
        "analytics": analytics_data
    })

@app.get("/analytics/transient-test")
def transient_analytics_test(request,
                           analytics1: AnalyticsService = Depends("analytics"),
                           analytics2: AnalyticsService = Depends("analytics"),
                           analytics3: AnalyticsService = Depends("analytics")):
    """Test transient service creation - each analytics should have different instance_id"""
    return JSONResponse({
        "message": "Transient service test",
        "analytics_instances": {
            "analytics1": analytics1.instance_id,
            "analytics2": analytics2.instance_id,
            "analytics3": analytics3.instance_id
        },
        "all_different": len({analytics1.instance_id, analytics2.instance_id, analytics3.instance_id}) == 3
    })

@app.get("/di-complex-chain")
def complex_di_chain_test(request,
                         user_service: UserService = Depends("user_service"),
                         post_service: PostService = Depends("post_service"),
                         user_repo: UserRepository = Depends("user_repository"),
                         post_repo: PostRepository = Depends("post_repository"),
                         db_session: DatabaseSession = Depends("database_session"),
                         analytics: AnalyticsService = Depends("analytics")):
    """Test complex DI chain with multiple services and repositories"""
    start_time = time.time()

    # Get some basic stats using all injected services
    user_count = len(user_service.get_all_users(db_session, limit=10))
    post_count = len(post_service.get_all_posts(db_session, limit=10))

    # Direct repository calls
    first_user = user_repo.get_by_id(1, db_session)
    first_post = post_repo.get_by_id(1, db_session)

    duration = time.time() - start_time
    analytics_data = analytics.track_operation("COMPLEX_CHAIN", "multiple", duration)

    return JSONResponse({
        "message": "Complex DI chain test completed",
        "data": {
            "user_count_sample": user_count,
            "post_count_sample": post_count,
            "first_user": first_user.to_dict() if first_user else None,
            "first_post": first_post.to_dict() if first_post else None
        },
        "analytics": analytics_data,
        "dependencies_injected": 6
    })

# Request cleanup
@app.middleware
def cleanup_middleware(request, response, call_next):
    """Middleware to ensure database sessions are cleaned up"""
    try:
        response = call_next(request)
        return response
    finally:
        # Clean up request-scoped services
        try:
            if hasattr(request, '_di_services') and 'database_session' in request._di_services:
                db_session = request._di_services['database_session']
                if hasattr(db_session, 'close'):
                    db_session.close()
        except:
            pass  # Ignore cleanup errors in benchmarks

# ============================================================================
# 8. APPLICATION STARTUP
# ============================================================================

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Catzilla SQLAlchemy DI Benchmark Server')
    parser.add_argument('--port', type=int, default=8000, help='Port to run the server on')
    args = parser.parse_args()

    print(f"\n🚀 Server starting on http://localhost:{args.port}")
    print("\nBenchmark endpoints:")
    print(f"  GET  http://localhost:{args.port}/                    - Home")
    print(f"  GET  http://localhost:{args.port}/health              - Health check with DB")
    print(f"  GET  http://localhost:{args.port}/users               - Get users (singleton service)")
    print(f"  GET  http://localhost:{args.port}/users/{{id}}          - Get user with posts (complex DI)")
    print(f"  GET  http://localhost:{args.port}/posts               - Get posts (service layer)")
    print(f"  GET  http://localhost:{args.port}/posts/by-user/{{id}}  - Get posts by user (repository)")
    print(f"  GET  http://localhost:{args.port}/analytics/transient-test - Transient service test")
    print(f"  GET  http://localhost:{args.port}/di-complex-chain    - Complex DI chain test")

    print(f"\n🗄️ SQLAlchemy Integration Features:")
    print(f"  🔗 Engine: Singleton service (1000 users, 5000 posts preloaded)")
    print(f"  🔄 Session: Request-scoped service with auto-cleanup")
    print(f"  📦 Repositories: Singleton services with CRUD operations")
    print(f"  🏢 Services: Business logic layer with validation")
    print(f"  📊 Analytics: Transient for operation tracking")

    app.listen(args.port)
