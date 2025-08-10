#!/usr/bin/env python3
"""
🗄️ Flask SQLAlchemy DI Benchmark Server

This server benchmarks Flask with SQLAlchemy database operations using
a basic dependency injection pattern for comparison with Catzilla and FastAPI.

Features benchmarked:
- Flask-SQLAlchemy integration
- Application context for database sessions
- Repository pattern with Flask application context
- Service layer with database dependencies
- Real database operations (CRUD)
"""

import time
from datetime import datetime
from typing import Dict, Any, Optional, List
from functools import wraps

try:
    from flask import Flask, request, jsonify, g
except ImportError:
    print("❌ Flask not installed. Install with: pip install flask")
    import sys
    sys.exit(1)

from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship
from sqlalchemy.pool import StaticPool

# Initialize Flask
app = Flask(__name__)
app.config['JSON_SORT_KEYS'] = False

print("🗄️ Flask SQLAlchemy DI Benchmark Server")

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

# Global configuration instance
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
# 3. FLASK DATABASE SESSION MANAGEMENT
# ============================================================================

def get_db_session() -> Session:
    """Get database session from Flask g context"""
    if 'db_session' not in g:
        g.db_session = SessionLocal()
    return g.db_session

@app.teardown_appcontext
def close_db_session(error):
    """Close database session after request"""
    db_session = g.pop('db_session', None)
    if db_session is not None:
        db_session.close()

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
# 5. SERVICE LAYER
# ============================================================================

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

# Service instances (singleton equivalent)
user_service = UserService(user_repository)
post_service = PostService(post_repository, user_repository)

# ============================================================================
# 6. ANALYTICS SERVICE
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
    """Get analytics service - new instance per call"""
    return AnalyticsService()

# ============================================================================
# 7. BENCHMARK ENDPOINTS
# ============================================================================

@app.route("/")
def home():
    """Home endpoint - basic overhead test"""
    return jsonify({
        "message": "Flask SQLAlchemy DI Benchmark",
        "framework": "flask",
        "di_system": "application_context",
        "database": "sqlalchemy",
        "features": ["application_context", "sqlalchemy", "repository_pattern", "services"]
    })

@app.route("/health")
def health_check():
    """Health check with database connection test"""
    try:
        db_session = get_db_session()
        # Simple database query to test connection
        user_count = db_session.query(User).count()
        post_count = db_session.query(Post).count()

        return jsonify({
            "status": "healthy",
            "database": "connected",
            "data": {
                "users": user_count,
                "posts": post_count
            }
        })
    except Exception as e:
        return jsonify({
            "status": "unhealthy",
            "database": "disconnected",
            "error": str(e)
        }), 500

@app.route("/users")
def get_users():
    """Get all users - tests service with database operations"""
    try:
        limit = min(int(request.args.get('limit', 100)), 1000)
        db_session = get_db_session()
        analytics = get_analytics_service()

        start_time = time.time()
        users = user_service.get_all_users(db_session, limit)
        duration = time.time() - start_time

        analytics_data = analytics.track_operation("SELECT", "users", duration)

        return jsonify({
            "users": users,
            "count": len(users),
            "analytics": analytics_data
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/users/<int:user_id>")
def get_user(user_id):
    """Get user with posts - tests complex service operations"""
    try:
        if user_id < 1:
            return jsonify({"error": "Invalid user ID"}), 400

        db_session = get_db_session()
        analytics = get_analytics_service()

        start_time = time.time()
        user = user_service.get_user_with_posts(user_id, db_session, post_repository)
        duration = time.time() - start_time

        if not user:
            return jsonify({"error": "User not found"}), 404

        analytics_data = analytics.track_operation("SELECT_JOIN", "users_posts", duration)

        return jsonify({
            "user": user,
            "analytics": analytics_data
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/posts")
def get_posts():
    """Get all posts - tests service layer with database operations"""
    try:
        limit = min(int(request.args.get('limit', 100)), 1000)
        db_session = get_db_session()
        analytics = get_analytics_service()

        start_time = time.time()
        posts = post_service.get_all_posts(db_session, limit)
        duration = time.time() - start_time

        analytics_data = analytics.track_operation("SELECT", "posts", duration)

        return jsonify({
            "posts": posts,
            "count": len(posts),
            "analytics": analytics_data
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/posts/by-user/<int:user_id>")
def get_posts_by_user(user_id):
    """Get posts by user - tests repository with filtered queries"""
    try:
        if user_id < 1:
            return jsonify({"error": "Invalid user ID"}), 400

        limit = min(int(request.args.get('limit', 100)), 1000)
        db_session = get_db_session()
        analytics = get_analytics_service()

        start_time = time.time()
        posts = post_repository.get_by_author(user_id, db_session, limit)
        duration = time.time() - start_time

        analytics_data = analytics.track_operation("SELECT_FILTERED", "posts", duration)

        return jsonify({
            "posts": [post.to_dict() for post in posts],
            "count": len(posts),
            "user_id": user_id,
            "analytics": analytics_data
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/analytics/transient-test")
def transient_analytics_test():
    """Test multiple service instances - each analytics should have different instance_id"""
    analytics1 = get_analytics_service()
    analytics2 = get_analytics_service()
    analytics3 = get_analytics_service()

    return jsonify({
        "message": "Multiple service instances test",
        "analytics_instances": {
            "analytics1": analytics1.instance_id,
            "analytics2": analytics2.instance_id,
            "analytics3": analytics3.instance_id
        },
        "all_different": len({analytics1.instance_id, analytics2.instance_id, analytics3.instance_id}) == 3
    })

@app.route("/di-complex-chain")
def complex_di_chain_test():
    """Test complex service chain with multiple repositories"""
    try:
        db_session = get_db_session()
        analytics = get_analytics_service()

        start_time = time.time()

        # Get some basic stats using all services
        user_count = len(user_service.get_all_users(db_session, limit=10))
        post_count = len(post_service.get_all_posts(db_session, limit=10))

        # Direct repository calls
        first_user = user_repository.get_by_id(1, db_session)
        first_post = post_repository.get_by_id(1, db_session)

        duration = time.time() - start_time
        analytics_data = analytics.track_operation("COMPLEX_CHAIN", "multiple", duration)

        return jsonify({
            "message": "Complex service chain test completed",
            "data": {
                "user_count_sample": user_count,
                "post_count_sample": post_count,
                "first_user": first_user.to_dict() if first_user else None,
                "first_post": first_post.to_dict() if first_post else None
            },
            "analytics": analytics_data,
            "services_used": 6
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ============================================================================
# 8. APPLICATION STARTUP
# ============================================================================

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Flask SQLAlchemy DI Benchmark Server')
    parser.add_argument('--port', type=int, default=8002, help='Port to run the server on')
    args = parser.parse_args()

    print(f"\n🚀 Server starting on http://localhost:{args.port}")
    print("\nBenchmark endpoints:")
    print(f"  GET  http://localhost:{args.port}/                    - Home")
    print(f"  GET  http://localhost:{args.port}/health              - Health check with DB")
    print(f"  GET  http://localhost:{args.port}/users               - Get users (service layer)")
    print(f"  GET  http://localhost:{args.port}/users/{{id}}          - Get user with posts (complex services)")
    print(f"  GET  http://localhost:{args.port}/posts               - Get posts (service layer)")
    print(f"  GET  http://localhost:{args.port}/posts/by-user/{{id}}  - Get posts by user (repository)")
    print(f"  GET  http://localhost:{args.port}/analytics/transient-test - Multiple instances test")
    print(f"  GET  http://localhost:{args.port}/di-complex-chain    - Complex service chain test")

    print(f"\n🗄️ SQLAlchemy Integration Features:")
    print(f"  🔗 Engine: Global instance (1000 users, 5000 posts preloaded)")
    print(f"  🔄 Session: Flask application context (g)")
    print(f"  📦 Repositories: Singleton instances with CRUD operations")
    print(f"  🏢 Services: Application context-based business logic layer")
    print(f"  📊 Analytics: New instance per function call")

    app.run(host="0.0.0.0", port=args.port, debug=False, threaded=True)

# The app instance is already created at module level for WSGI servers like gunicorn
