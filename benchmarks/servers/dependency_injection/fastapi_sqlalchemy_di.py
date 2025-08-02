#!/usr/bin/env python3
"""
🗄️ FastAPI SQLAlchemy DI Benchmark Server

This server benchmarks FastAPI's dependency injection with real SQLAlchemy database operations
for comparison with Catzilla's SQLAlchemy DI implementation.

Features benchmarked:
- SQLAlchemy engine registration with FastAPI dependencies
- Database session management
- Repository pattern with FastAPI DI
- Service layer with database dependencies
- Real database operations (CRUD)
"""

import time
from datetime import datetime
from typing import Dict, Any, Optional, List
from contextlib import contextmanager

try:
    from fastapi import FastAPI, Request, HTTPException, Depends, Path, Query
    from fastapi.responses import JSONResponse
    from pydantic import BaseModel
except ImportError:
    print("❌ FastAPI not installed. Install with: pip install fastapi uvicorn pydantic")
    import sys
    sys.exit(1)

from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship
from sqlalchemy.pool import StaticPool

# Initialize FastAPI
app = FastAPI(
    title="FastAPI SQLAlchemy DI Benchmark",
    docs_url=None,
    redoc_url=None
)

print("🗄️ FastAPI SQLAlchemy DI Benchmark Server")

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
# 2. DATABASE CONFIGURATION AND ENGINE
# ============================================================================

class DatabaseConfig:
    """Database configuration"""
    def __init__(self):
        # Using in-memory SQLite for consistent benchmarking
        self.database_url = "sqlite:///:memory:"
        self.echo = False  # Disable for performance

# Global configuration instance (singleton equivalent)
db_config = DatabaseConfig()

# Create SQLAlchemy engine
engine = create_engine(
    db_config.database_url,
    echo=db_config.echo,
    poolclass=StaticPool,
    connect_args={"check_same_thread": False}
)

# Create all tables
Base.metadata.create_all(engine)

# Create session factory
SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False
)

# Seed benchmark data
def seed_benchmark_data():
    """Seed data optimized for benchmarking"""
    session = SessionLocal()
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

# Initialize data
seed_benchmark_data()

# ============================================================================
# 3. DATABASE SESSION DEPENDENCY
# ============================================================================

def get_database_session() -> Session:
    """Get database session dependency"""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()

# ============================================================================
# 4. REPOSITORY PATTERN
# ============================================================================

class UserRepository:
    """User repository with database operations"""

    def get_all(self, db_session: Session, limit: int = 100) -> List[User]:
        """Get all users with limit for performance"""
        return db_session.query(User).limit(limit).all()

    def get_by_id(self, user_id: int, db_session: Session) -> Optional[User]:
        """Get user by ID"""
        return db_session.query(User).filter(User.id == user_id).first()

    def get_by_email(self, email: str, db_session: Session) -> Optional[User]:
        """Get user by email"""
        return db_session.query(User).filter(User.email == email).first()

    def create(self, name: str, email: str, db_session: Session) -> User:
        """Create a new user"""
        user = User(name=name, email=email)
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        return user

    def update(self, user_id: int, db_session: Session, **kwargs) -> Optional[User]:
        """Update user"""
        user = self.get_by_id(user_id, db_session)
        if user:
            for key, value in kwargs.items():
                if value is not None and hasattr(user, key):
                    setattr(user, key, value)
            db_session.commit()
            return user
        return None

    def delete(self, user_id: int, db_session: Session) -> bool:
        """Delete user"""
        user = self.get_by_id(user_id, db_session)
        if user:
            db_session.delete(user)
            db_session.commit()
            return True
        return False

class PostRepository:
    """Post repository with database operations"""

    def get_all(self, db_session: Session, limit: int = 100) -> List[Post]:
        """Get all posts with limit for performance"""
        return db_session.query(Post).limit(limit).all()

    def get_by_id(self, post_id: int, db_session: Session) -> Optional[Post]:
        """Get post by ID"""
        return db_session.query(Post).filter(Post.id == post_id).first()

    def get_by_author(self, author_id: int, db_session: Session, limit: int = 100) -> List[Post]:
        """Get posts by author with limit for performance"""
        return db_session.query(Post).filter(Post.author_id == author_id).limit(limit).all()

    def create(self, title: str, content: str, author_id: int, db_session: Session) -> Post:
        """Create a new post"""
        post = Post(title=title, content=content, author_id=author_id)
        db_session.add(post)
        db_session.commit()
        db_session.refresh(post)
        return post

    def update(self, post_id: int, db_session: Session, **kwargs) -> Optional[Post]:
        """Update post"""
        post = self.get_by_id(post_id, db_session)
        if post:
            for key, value in kwargs.items():
                if value is not None and hasattr(post, key):
                    setattr(post, key, value)
            db_session.commit()
            return post
        return None

    def delete(self, post_id: int, db_session: Session) -> bool:
        """Delete post"""
        post = self.get_by_id(post_id, db_session)
        if post:
            db_session.delete(post)
            db_session.commit()
            return True
        return False

# Repository instances (singleton equivalent)
user_repository = UserRepository()
post_repository = PostRepository()

# ============================================================================
# 5. SERVICE LAYER DEPENDENCIES
# ============================================================================

def get_user_repository() -> UserRepository:
    """Get user repository dependency"""
    return user_repository

def get_post_repository() -> PostRepository:
    """Get post repository dependency"""
    return post_repository

class UserService:
    """User service with business logic"""

    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo

    def get_all_users(self, db_session: Session, limit: int = 100) -> List[Dict[str, Any]]:
        """Get all users with business logic"""
        users = self.user_repo.get_all(db_session, limit)
        return [user.to_dict() for user in users]

    def get_user_with_posts(self, user_id: int, db_session: Session, post_repo: PostRepository) -> Optional[Dict[str, Any]]:
        """Get user with their posts"""
        user = self.user_repo.get_by_id(user_id, db_session)
        if user:
            posts = post_repo.get_by_author(user_id, db_session, limit=10)
            user_dict = user.to_dict()
            user_dict["posts"] = [post.to_dict() for post in posts]
            user_dict["posts_count"] = len(posts)
            return user_dict
        return None

    def create_user(self, name: str, email: str, db_session: Session) -> Dict[str, Any]:
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

class PostService:
    """Post service with business logic"""

    def __init__(self, post_repo: PostRepository, user_repo: UserRepository):
        self.post_repo = post_repo
        self.user_repo = user_repo

    def get_all_posts(self, db_session: Session, limit: int = 100) -> List[Dict[str, Any]]:
        """Get all posts with business logic"""
        posts = self.post_repo.get_all(db_session, limit)
        return [post.to_dict() for post in posts]

    def create_post(self, title: str, content: str, author_id: int, db_session: Session) -> Dict[str, Any]:
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

def get_user_service(user_repo: UserRepository = Depends(get_user_repository)) -> UserService:
    """Get user service dependency"""
    return UserService(user_repo)

def get_post_service(
    post_repo: PostRepository = Depends(get_post_repository),
    user_repo: UserRepository = Depends(get_user_repository)
) -> PostService:
    """Get post service dependency"""
    return PostService(post_repo, user_repo)

# ============================================================================
# 6. ANALYTICS SERVICE (NEW INSTANCE PER REQUEST)
# ============================================================================

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

def get_analytics_service() -> AnalyticsService:
    """Get analytics service dependency - new instance per request"""
    return AnalyticsService()

# ============================================================================
# 7. BENCHMARK ENDPOINTS
# ============================================================================

@app.get("/")
async def home():
    """Home endpoint - basic DI overhead test"""
    return {
        "message": "FastAPI SQLAlchemy DI Benchmark",
        "framework": "fastapi",
        "di_system": "depends",
        "database": "sqlalchemy",
        "features": ["dependency_injection", "sqlalchemy", "repository_pattern", "services"]
    }

@app.get("/health")
async def health_check(db_session: Session = Depends(get_database_session)):
    """Health check with database connection test"""
    try:
        # Simple database query to test connection
        user_count = db_session.query(User).count()
        post_count = db_session.query(Post).count()

        return {
            "status": "healthy",
            "database": "connected",
            "data": {
                "users": user_count,
                "posts": post_count
            }
        }
    except Exception as e:
        return JSONResponse({
            "status": "unhealthy",
            "database": "disconnected",
            "error": str(e)
        }, status_code=500)

@app.get("/users")
async def get_users(
    limit: int = Query(100, ge=1, le=1000),
    user_service: UserService = Depends(get_user_service),
    db_session: Session = Depends(get_database_session),
    analytics: AnalyticsService = Depends(get_analytics_service)
):
    """Get all users - tests service DI with database operations"""
    start_time = time.time()
    users = user_service.get_all_users(db_session, limit)
    duration = time.time() - start_time

    analytics_data = analytics.track_operation("SELECT", "users", duration)

    return {
        "users": users,
        "count": len(users),
        "analytics": analytics_data
    }

@app.get("/users/{user_id}")
async def get_user(
    user_id: int = Path(..., ge=1),
    user_service: UserService = Depends(get_user_service),
    post_repo: PostRepository = Depends(get_post_repository),
    db_session: Session = Depends(get_database_session),
    analytics: AnalyticsService = Depends(get_analytics_service)
):
    """Get user with posts - tests complex DI chain with multiple repositories"""
    start_time = time.time()
    user = user_service.get_user_with_posts(user_id, db_session, post_repo)
    duration = time.time() - start_time

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    analytics_data = analytics.track_operation("SELECT_JOIN", "users_posts", duration)

    return {
        "user": user,
        "analytics": analytics_data
    }

@app.get("/posts")
async def get_posts(
    limit: int = Query(100, ge=1, le=1000),
    post_service: PostService = Depends(get_post_service),
    db_session: Session = Depends(get_database_session),
    analytics: AnalyticsService = Depends(get_analytics_service)
):
    """Get all posts - tests service layer DI with database operations"""
    start_time = time.time()
    posts = post_service.get_all_posts(db_session, limit)
    duration = time.time() - start_time

    analytics_data = analytics.track_operation("SELECT", "posts", duration)

    return {
        "posts": posts,
        "count": len(posts),
        "analytics": analytics_data
    }

@app.get("/posts/by-user/{user_id}")
async def get_posts_by_user(
    user_id: int = Path(..., ge=1),
    limit: int = Query(100, ge=1, le=1000),
    post_repo: PostRepository = Depends(get_post_repository),
    db_session: Session = Depends(get_database_session),
    analytics: AnalyticsService = Depends(get_analytics_service)
):
    """Get posts by user - tests repository DI with filtered queries"""
    start_time = time.time()
    posts = post_repo.get_by_author(user_id, db_session, limit)
    duration = time.time() - start_time

    analytics_data = analytics.track_operation("SELECT_FILTERED", "posts", duration)

    return {
        "posts": [post.to_dict() for post in posts],
        "count": len(posts),
        "user_id": user_id,
        "analytics": analytics_data
    }

@app.get("/analytics/transient-test")
async def transient_analytics_test(
    analytics1: AnalyticsService = Depends(get_analytics_service),
    analytics2: AnalyticsService = Depends(get_analytics_service),
    analytics3: AnalyticsService = Depends(get_analytics_service)
):
    """Test multiple service instances - each analytics should have different instance_id"""
    return {
        "message": "Multiple service instances test",
        "analytics_instances": {
            "analytics1": analytics1.instance_id,
            "analytics2": analytics2.instance_id,
            "analytics3": analytics3.instance_id
        },
        "all_different": len({analytics1.instance_id, analytics2.instance_id, analytics3.instance_id}) == 3
    }

@app.get("/di-complex-chain")
async def complex_di_chain_test(
    user_service: UserService = Depends(get_user_service),
    post_service: PostService = Depends(get_post_service),
    user_repo: UserRepository = Depends(get_user_repository),
    post_repo: PostRepository = Depends(get_post_repository),
    db_session: Session = Depends(get_database_session),
    analytics: AnalyticsService = Depends(get_analytics_service)
):
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

    return {
        "message": "Complex DI chain test completed",
        "data": {
            "user_count_sample": user_count,
            "post_count_sample": post_count,
            "first_user": first_user.to_dict() if first_user else None,
            "first_post": first_post.to_dict() if first_post else None
        },
        "analytics": analytics_data,
        "dependencies_injected": 6
    }

# ============================================================================
# 8. APPLICATION STARTUP
# ============================================================================

if __name__ == "__main__":
    import argparse
    import uvicorn

    parser = argparse.ArgumentParser(description='FastAPI SQLAlchemy DI Benchmark Server')
    parser.add_argument('--port', type=int, default=8001, help='Port to run the server on')
    args = parser.parse_args()

    print(f"\n🚀 Server starting on http://localhost:{args.port}")
    print("\nBenchmark endpoints:")
    print(f"  GET  http://localhost:{args.port}/                    - Home")
    print(f"  GET  http://localhost:{args.port}/health              - Health check with DB")
    print(f"  GET  http://localhost:{args.port}/users               - Get users (service DI)")
    print(f"  GET  http://localhost:{args.port}/users/{{id}}          - Get user with posts (complex DI)")
    print(f"  GET  http://localhost:{args.port}/posts               - Get posts (service layer)")
    print(f"  GET  http://localhost:{args.port}/posts/by-user/{{id}}  - Get posts by user (repository)")
    print(f"  GET  http://localhost:{args.port}/analytics/transient-test - Multiple instances test")
    print(f"  GET  http://localhost:{args.port}/di-complex-chain    - Complex DI chain test")

    print(f"\n🗄️ SQLAlchemy Integration Features:")
    print(f"  🔗 Engine: Global instance (1000 users, 5000 posts preloaded)")
    print(f"  🔄 Session: Per-request dependency")
    print(f"  📦 Repositories: Singleton instances with CRUD operations")
    print(f"  🏢 Services: Dependency-injected business logic layer")
    print(f"  📊 Analytics: New instance per dependency call")

    uvicorn.run(app, host="0.0.0.0", port=args.port, log_level="warning")
