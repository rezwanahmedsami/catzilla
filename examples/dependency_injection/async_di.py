#!/usr/bin/env python3
"""
🚀 Catzilla Async Dependency Injection Example

This demonstrates Catzilla's DI system with async handlers and FastAPI-identical syntax.
Perfect for developers migrating from FastAPI async apps or learning async DI patterns.

Features:
- FastAPI-identical async syntax with Depends()
- Async service methods for I/O operations
- Automatic async/sync service registration
- Mixed async/sync handlers with DI
- Async database operations simulation
- Zero boilerplate async setup

"""

import asyncio
import time
from datetime import datetime
from catzilla import Catzilla, service, Depends, Path
from catzilla.dependency_injection import set_default_container

# Create app with DI enabled
app = Catzilla(enable_di=True, production=False, show_banner=True)

# Set the app's container as default for service registration
set_default_container(app.di_container)

# ============================================================================
# ASYNC SERVICES - Real-world I/O Operations
# ============================================================================

@service("async_database")
class AsyncDatabaseService:
    """Async database service with simulated I/O operations"""

    def __init__(self):
        self.users = [
            {"id": 1, "name": "Alice", "email": "alice@example.com", "status": "active"},
            {"id": 2, "name": "Bob", "email": "bob@example.com", "status": "inactive"},
            {"id": 3, "name": "Carol", "email": "carol@example.com", "status": "active"},
            {"id": 4, "name": "David", "email": "david@example.com", "status": "pending"}
        ]
        print("💾 Async Database service initialized")

    async def get_users(self):
        """Simulate async database query"""
        await asyncio.sleep(0.1)  # Simulate network latency
        return self.users

    async def get_user(self, user_id: int):
        """Simulate async user lookup"""
        await asyncio.sleep(0.05)  # Simulate database query
        return next((u for u in self.users if u["id"] == user_id), None)

    async def search_users(self, status: str = None):
        """Simulate async user search with filtering"""
        await asyncio.sleep(0.08)  # Simulate complex query
        if status:
            return [u for u in self.users if u["status"] == status]
        return self.users

    async def get_user_count(self):
        """Simulate async aggregation query"""
        await asyncio.sleep(0.03)
        return len(self.users)

@service("async_notification")
class AsyncNotificationService:
    """Async notification service for external API calls"""

    def __init__(self):
        self.notifications = []
        print("📧 Async Notification service initialized")

    async def send_notification(self, user_id: int, message: str):
        """Simulate async external API call"""
        await asyncio.sleep(0.2)  # Simulate HTTP request to notification service

        notification = {
            "id": len(self.notifications) + 1,
            "user_id": user_id,
            "message": message,
            "sent_at": datetime.now().isoformat(),
            "status": "sent"
        }
        self.notifications.append(notification)
        return notification

    async def get_notifications(self, user_id: int = None):
        """Get notifications with async filtering"""
        await asyncio.sleep(0.05)
        if user_id:
            return [n for n in self.notifications if n["user_id"] == user_id]
        return self.notifications

@service("async_cache")
class AsyncCacheService:
    """Async cache service for Redis-like operations"""

    def __init__(self):
        self.cache = {}
        print("🗄️ Async Cache service initialized")

    async def get(self, key: str):
        """Simulate async cache lookup"""
        await asyncio.sleep(0.01)  # Simulate Redis latency
        return self.cache.get(key)

    async def set(self, key: str, value, ttl: int = 300):
        """Simulate async cache storage"""
        await asyncio.sleep(0.01)  # Simulate Redis write
        self.cache[key] = {
            "value": value,
            "expires_at": time.time() + ttl
        }

    async def clear_expired(self):
        """Simulate async cache cleanup"""
        await asyncio.sleep(0.02)
        current_time = time.time()
        expired_keys = [
            key for key, data in self.cache.items()
            if data["expires_at"] < current_time
        ]
        for key in expired_keys:
            del self.cache[key]
        return len(expired_keys)

@service("async_logger")
class AsyncLoggerService:
    """Async logging service with file I/O"""

    def __init__(self):
        self.logs = []
        print("📝 Async Logger service initialized")

    async def log(self, message: str, level: str = "INFO"):
        """Async logging with file write simulation"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "level": level,
            "message": message
        }
        self.logs.append(log_entry)

        # Simulate async file write
        await asyncio.sleep(0.01)

        return log_entry

    async def get_logs(self, level: str = None):
        """Get logs with async filtering"""
        await asyncio.sleep(0.01)
        if level:
            return [log for log in self.logs if log["level"] == level]
        return self.logs

    async def write_to_file(self, filename: str = "app.log"):
        """Simulate async file writing"""
        await asyncio.sleep(0.05)  # Simulate file I/O
        # In real implementation, you'd use aiofiles here
        return f"Wrote {len(self.logs)} logs to {filename}"

# ============================================================================
# MIXED SYNC SERVICES - Demonstrate compatibility
# ============================================================================

@service("metrics")
class MetricsService:
    """Sync metrics service - works with async handlers"""

    def __init__(self):
        self.requests = 0
        self.start_time = time.time()
        print("📊 Metrics service initialized")

    def increment_requests(self):
        self.requests += 1

    def get_metrics(self):
        uptime = time.time() - self.start_time
        return {
            "requests": self.requests,
            "uptime_seconds": round(uptime, 2),
            "requests_per_second": round(self.requests / uptime, 2) if uptime > 0 else 0
        }

# ============================================================================
# ASYNC ROUTES - FastAPI-Identical Async Syntax
# ============================================================================

@app.get("/")
async def async_home(request,
                     db: AsyncDatabaseService = Depends("async_database"),
                     logger: AsyncLoggerService = Depends("async_logger"),
                     metrics: MetricsService = Depends("metrics")):
    """Async home page with multiple DI services"""
    metrics.increment_requests()

    # Concurrent async operations
    user_count_task = asyncio.create_task(db.get_user_count())
    log_task = asyncio.create_task(logger.log("Home page accessed"))

    user_count, log_entry = await asyncio.gather(user_count_task, log_task)

    return {
        "message": "Welcome to Catzilla Async DI! 🚀",
        "di_system": "Catzilla v0.2.0 Async",
        "syntax": "FastAPI-identical async",
        "user_count": user_count,
        "performance": "60%+ faster than FastAPI",
        "log_id": log_entry["timestamp"]
    }

@app.get("/users")
async def get_users_async(request,
                         db: AsyncDatabaseService = Depends("async_database"),
                         cache: AsyncCacheService = Depends("async_cache"),
                         logger: AsyncLoggerService = Depends("async_logger"),
                         metrics: MetricsService = Depends("metrics")):
    """Async user listing with caching"""
    metrics.increment_requests()

    # Try cache first
    cached_users = await cache.get("all_users")
    if cached_users:
        await logger.log("Users served from cache")
        return {
            "users": cached_users["value"],
            "source": "cache",
            "count": len(cached_users["value"])
        }

    # Cache miss - fetch from database
    users = await db.get_users()
    await cache.set("all_users", users, ttl=60)  # Cache for 1 minute
    await logger.log(f"Fetched {len(users)} users from database")

    return {
        "users": users,
        "source": "database",
        "count": len(users),
        "cached": True
    }

@app.get("/users/{user_id}")
async def get_user_async(request,
                        user_id: int = Path(...),
                        db: AsyncDatabaseService = Depends("async_database"),
                        logger: AsyncLoggerService = Depends("async_logger"),
                        notification: AsyncNotificationService = Depends("async_notification")):
    """Async user lookup with notification"""

    # Concurrent operations
    user_task = asyncio.create_task(db.get_user(user_id))
    log_task = asyncio.create_task(logger.log(f"User {user_id} requested"))

    user, log_entry = await asyncio.gather(user_task, log_task)

    if not user:
        await logger.log(f"User {user_id} not found", "WARNING")
        return {"error": f"User {user_id} not found", "status": 404}

    # Send async notification (fire and forget)
    asyncio.create_task(
        notification.send_notification(
            user_id,
            f"Profile viewed at {datetime.now().strftime('%H:%M:%S')}"
        )
    )

    return {
        "user": user,
        "log_timestamp": log_entry["timestamp"],
        "notification": "queued"
    }

@app.get("/users/status/{status}")
async def search_users_by_status(request,
                                 status: str = Path(...),
                                 db: AsyncDatabaseService = Depends("async_database"),
                                 cache: AsyncCacheService = Depends("async_cache"),
                                 logger: AsyncLoggerService = Depends("async_logger")):
    """Async user search with smart caching"""

    cache_key = f"users_status_{status}"

    # Check cache and search concurrently
    cache_task = asyncio.create_task(cache.get(cache_key))
    search_task = asyncio.create_task(db.search_users(status))
    log_task = asyncio.create_task(logger.log(f"Searching users with status: {status}"))

    cached_result, users, log_entry = await asyncio.gather(
        cache_task, search_task, log_task
    )

    # Cache the result for future requests
    if not cached_result:
        await cache.set(cache_key, users, ttl=30)

    return {
        "users": users,
        "status_filter": status,
        "count": len(users),
        "from_cache": bool(cached_result),
        "search_timestamp": log_entry["timestamp"]
    }

@app.get("/notifications/{user_id}")
async def get_user_notifications(request,
                                user_id: int = Path(...),
                                notification: AsyncNotificationService = Depends("async_notification"),
                                logger: AsyncLoggerService = Depends("async_logger")):
    """Get user notifications asynchronously"""

    notifications_task = asyncio.create_task(notification.get_notifications(user_id))
    log_task = asyncio.create_task(logger.log(f"Fetching notifications for user {user_id}"))

    notifications, log_entry = await asyncio.gather(notifications_task, log_task)

    return {
        "user_id": user_id,
        "notifications": notifications,
        "count": len(notifications),
        "fetched_at": log_entry["timestamp"]
    }

@app.get("/stats")
async def get_system_stats(request,
                          db: AsyncDatabaseService = Depends("async_database"),
                          cache: AsyncCacheService = Depends("async_cache"),
                          logger: AsyncLoggerService = Depends("async_logger"),
                          metrics: MetricsService = Depends("metrics")):
    """Comprehensive async system statistics"""

    # Gather all stats concurrently
    user_count_task = asyncio.create_task(db.get_user_count())
    cache_cleanup_task = asyncio.create_task(cache.clear_expired())
    log_count_task = asyncio.create_task(logger.get_logs())

    user_count, expired_keys, logs = await asyncio.gather(
        user_count_task, cache_cleanup_task, log_count_task
    )

    sync_metrics = metrics.get_metrics()  # Sync call within async handler

    await logger.log("System stats requested")

    return {
        "database": {
            "total_users": user_count
        },
        "cache": {
            "expired_keys_cleaned": expired_keys
        },
        "logging": {
            "total_logs": len(logs),
            "error_logs": len([l for l in logs if l["level"] == "ERROR"])
        },
        "performance": sync_metrics,
        "async_operations": "All completed concurrently",
        "timestamp": datetime.now().isoformat()
    }

# ============================================================================
# MIXED SYNC/ASYNC ROUTES - Demonstrate Compatibility
# ============================================================================

@app.get("/sync-with-async-services")
def sync_handler_with_async_services(request,
                                    metrics: MetricsService = Depends("metrics"),
                                    cache: AsyncCacheService = Depends("async_cache")):
    """Sync handler using async services (via sync-calling-async pattern)"""
    metrics.increment_requests()

    # Use asyncio.run to call async service from sync handler
    async def get_cache_stats():
        await cache.clear_expired()
        return {"cache_operations": "completed"}

    cache_stats = asyncio.run(get_cache_stats())

    return {
        "handler_type": "sync",
        "services_used": ["sync_metrics", "async_cache"],
        "pattern": "sync-calling-async",
        "cache_stats": cache_stats,
        "metrics": metrics.get_metrics()
    }

# ============================================================================
# APPLICATION STARTUP
# ============================================================================

if __name__ == "__main__":
    print("\n🚀 Catzilla Async Dependency Injection Example")
    print("=" * 50)
    print("FastAPI-identical async syntax with 60%+ better performance!")
    print("\n🔥 Async Features:")
    print("  ✅ Async services with real I/O simulation")
    print("  ✅ Concurrent async operations")
    print("  ✅ Smart caching with async Redis-like operations")
    print("  ✅ Async logging and notifications")
    print("  ✅ Mixed sync/async service compatibility")

    print("\n🎯 Endpoints:")
    print("  GET /                          - Async home with concurrent operations")
    print("  GET /users                     - Async user listing with caching")
    print("  GET /users/{user_id}           - Async user lookup with notifications")
    print("  GET /users/status/{status}     - Async user search (active/inactive/pending)")
    print("  GET /notifications/{user_id}   - Get user notifications")
    print("  GET /stats                     - Comprehensive async system stats")
    print("  GET /sync-with-async-services  - Mixed sync/async pattern demo")

    print("\n🚀 Try these async examples:")
    print("  curl http://localhost:8000/")
    print("  curl http://localhost:8000/users")
    print("  curl http://localhost:8000/users/1")
    print("  curl http://localhost:8000/users/status/active")
    print("  curl http://localhost:8000/notifications/1")
    print("  curl http://localhost:8000/stats")

    print(f"\n🚀 Async server starting on http://localhost:8000")
    print("💡 All async operations run concurrently for maximum performance!")
    app.listen(host="127.0.0.1", port=8000)
