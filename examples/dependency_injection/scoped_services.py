#!/usr/bin/env python3
"""
🔄 Catzilla DI Scoped Services Example

This example demonstrates Catzilla's revolutionary dependency injection system
with different service scopes (singleton, request, transient) using FastAPI-identical syntax.

Features demonstrated:
- Service registration with different scopes
- Singleton services (shared across all requests)
- Request-scoped services (new instance per request)
- Transient services (new instance every time)
- Service factories and configuration
- FastAPI-style Depends() syntax for automatic injection
- Clear demonstration of scope behavior through type hints
"""

import time
import uuid
from datetime import datetime
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

from catzilla import Catzilla, service, Depends, JSONResponse, Path
from catzilla.dependency_injection import set_default_container

# Initialize Catzilla with DI enabled
app = Catzilla(enable_di=True)
set_default_container(app.di_container)

print("🔄 Catzilla DI Scoped Services Example")
print("=" * 50)

# ============================================================================
# 1. SINGLETON SERVICES - Shared across all requests
# ============================================================================

@dataclass
class DatabaseConfig:
    """Database configuration (singleton)"""
    host: str = "localhost"
    port: int = 5432
    database: str = "catzilla_db"
    username: str = "admin"
    max_connections: int = 10

@service("db_config", scope="singleton")
def database_config() -> DatabaseConfig:
    """Database configuration factory"""
    print("📋 Database config created (singleton)")
    return DatabaseConfig()

@service("database", scope="singleton")
class DatabaseService:
    """Database service (singleton scope)"""

    def __init__(self, config: DatabaseConfig = Depends("db_config")):
        self.config = config
        self.connection_id = str(uuid.uuid4())[:8]
        self.query_count = 0
        self.connected_at = datetime.now()

        print(f"💾 Database service created (singleton) - Connection: {self.connection_id}")

    def execute_query(self, query: str) -> Dict[str, Any]:
        """Execute a database query"""
        self.query_count += 1
        return {
            "query": query,
            "connection_id": self.connection_id,
            "query_number": self.query_count,
            "executed_at": datetime.now().isoformat()
        }

    def get_stats(self) -> Dict[str, Any]:
        """Get database statistics"""
        return {
            "connection_id": self.connection_id,
            "total_queries": self.query_count,
            "uptime": (datetime.now() - self.connected_at).total_seconds(),
            "config": {
                "host": self.config.host,
                "database": self.config.database
            }
        }

@service("cache", scope="singleton")
class CacheService:
    """Cache service (singleton scope)"""

    def __init__(self):
        self.cache = {}
        self.hit_count = 0
        self.miss_count = 0
        self.instance_id = str(uuid.uuid4())[:8]

        print(f"🗄️  Cache service created (singleton) - Instance: {self.instance_id}")

    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        if key in self.cache:
            self.hit_count += 1
            return self.cache[key]
        else:
            self.miss_count += 1
            return None

    def set(self, key: str, value: Any, ttl: int = 300) -> None:
        """Set value in cache"""
        self.cache[key] = {
            "value": value,
            "stored_at": datetime.now().isoformat(),
            "ttl": ttl
        }

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        total = self.hit_count + self.miss_count
        hit_rate = (self.hit_count / total * 100) if total > 0 else 0

        return {
            "instance_id": self.instance_id,
            "hit_count": self.hit_count,
            "miss_count": self.miss_count,
            "hit_rate": f"{hit_rate:.1f}%",
            "cache_size": len(self.cache)
        }

# ============================================================================
# 2. REQUEST-SCOPED SERVICES - New instance per request
# ============================================================================

@service("user_session", scope="request")
class UserSession:
    """User session service (request scope)"""

    def __init__(self, cache_service: CacheService = Depends("cache")):
        self.session_id = str(uuid.uuid4())
        self.cache_service = cache_service
        self.created_at = datetime.now()
        self.actions = []

        print(f"👤 User session created (request-scoped) - Session: {self.session_id}")

    def get_user_data(self, user_id: str) -> Dict[str, Any]:
        """Get user data with session tracking"""
        self.actions.append(f"get_user_data:{user_id}")

        # Try cache first
        cached_data = self.cache_service.get(f"user:{user_id}")
        if cached_data:
            return cached_data["value"]

        # Simulate fetching from database
        user_data = {
            "user_id": user_id,
            "name": f"User {user_id}",
            "fetched_at": datetime.now().isoformat(),
            "session_id": self.session_id
        }

        # Cache the result
        self.cache_service.set(f"user:{user_id}", user_data)

        return user_data

    def get_session_info(self) -> Dict[str, Any]:
        """Get session information"""
        return {
            "session_id": self.session_id,
            "created_at": self.created_at.isoformat(),
            "actions_count": len(self.actions),
            "actions": self.actions,
            "duration": (datetime.now() - self.created_at).total_seconds()
        }

@service("request_logger", scope="request")
class RequestLogger:
    """Request logger service (request scope)"""

    def __init__(self):
        self.request_id = str(uuid.uuid4())[:8]
        self.start_time = datetime.now()
        self.logs = []

        print(f"📝 Request logger created (request-scoped) - Request: {self.request_id}")

    def log(self, message: str, level: str = "INFO") -> None:
        """Log a message with timestamp"""
        timestamp = (datetime.now() - self.start_time).total_seconds()
        entry = {
            "timestamp": timestamp,
            "level": level,
            "message": message,
            "request_id": self.request_id
        }
        self.logs.append(entry)

    def get_logs(self) -> List[Dict[str, Any]]:
        """Get all logs for this request"""
        return self.logs

    def get_request_info(self) -> Dict[str, Any]:
        """Get request information"""
        return {
            "request_id": self.request_id,
            "start_time": self.start_time.isoformat(),
            "duration": (datetime.now() - self.start_time).total_seconds(),
            "log_count": len(self.logs)
        }

# ============================================================================
# 3. TRANSIENT SERVICES - New instance every time
# ============================================================================

@service("analytics", scope="transient")
class AnalyticsService:
    """Analytics service (transient scope)"""

    def __init__(self):
        self.instance_id = str(uuid.uuid4())[:8]
        self.created_at = datetime.now()

        print(f"📊 Analytics service created (transient) - Instance: {self.instance_id}")

    def track_event(self, event_name: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Track an analytics event"""
        return {
            "event_name": event_name,
            "data": data,
            "instance_id": self.instance_id,
            "tracked_at": datetime.now().isoformat(),
            "created_at": self.created_at.isoformat()
        }

@service("temp_processor", scope="transient")
class TempProcessor:
    """Temporary processor service (transient scope)"""

    def __init__(self):
        self.instance_id = str(uuid.uuid4())[:8]
        self.created_at = datetime.now()

        print(f"⚡ Temp processor created (transient) - Instance: {self.instance_id}")

    def process_data(self, data: Any) -> Dict[str, Any]:
        """Process temporary data"""
        return {
            "processed_data": f"Processed: {data}",
            "processor_id": self.instance_id,
            "processed_at": datetime.now().isoformat(),
            "processing_time": (datetime.now() - self.created_at).total_seconds()
        }

# ============================================================================
# 4. ROUTE HANDLERS DEMONSTRATING SCOPED SERVICES WITH DEPENDS()
# ============================================================================

# NOTE: FastAPI-style Depends() syntax makes scope behavior clear:
#
# - Singleton services (database, cache): Same instance across ALL requests
# - Request-scoped services (session, logger): Same instance within ONE request
# - Transient services (analytics, processor): NEW instance every time injected
#
# Multiple Depends() of the same service within one route:
# - Singleton/Request: Returns the SAME instance
# - Transient: Returns DIFFERENT instances (analytics1 != analytics2)

@app.get("/")
def home(request):
    """Home page showing scoped services"""
    return JSONResponse({
        "message": "🔄 Catzilla DI Scoped Services Demo",
        "syntax": "FastAPI-identical Depends() for automatic injection",
        "scopes": {
            "singleton": "Shared across all requests (database, cache)",
            "request": "New instance per request (user_session, request_logger)",
            "transient": "New instance every time (analytics, temp_processor)"
        }
    })

@app.get("/api/user/{user_id}")
def get_user(request,
             user_id: str = Path(...),
             session: UserSession = Depends("user_session"),
             logger: RequestLogger = Depends("request_logger"),
             database: DatabaseService = Depends("database"),
             cache: CacheService = Depends("cache"),
             analytics1: AnalyticsService = Depends("analytics"),
             analytics2: AnalyticsService = Depends("analytics")):
    """Get user data - demonstrates request-scoped services"""

    logger.log(f"Fetching user {user_id}")

    # Get user data through session
    user_data = session.get_user_data(user_id)

    # Track analytics events
    analytics1.track_event("user_fetch", {"user_id": user_id})
    analytics2.track_event("user_view", {"user_id": user_id})

    # Execute database query
    db_result = database.execute_query(f"SELECT * FROM users WHERE id = '{user_id}'")

    logger.log(f"User {user_id} data retrieved")

    return JSONResponse({
        "user": user_data,
        "database_query": db_result,
        "session_info": session.get_session_info(),
        "request_logs": logger.get_logs(),
        "analytics": {
            "instance1": analytics1.instance_id,
            "instance2": analytics2.instance_id,
            "same_instance": analytics1.instance_id == analytics2.instance_id
        },
        "scope_demonstration": {
            "session_id": session.session_id,
            "logger_request_id": logger.request_id,
            "db_connection_id": database.connection_id,
            "cache_instance_id": cache.instance_id,
            "scope_notes": {
                "session_and_logger": "Same instance within this request (request-scoped)",
                "database_and_cache": "Same instance across ALL requests (singleton)",
                "analytics1_vs_analytics2": "Different instances - transient scope creates new each time"
            }
        }
    })

@app.get("/api/database/stats")
def get_database_stats(request,
                       database: DatabaseService = Depends("database"),
                       logger: RequestLogger = Depends("request_logger")):
    """Get database statistics - demonstrates singleton behavior"""

    logger.log("Database stats requested")

    stats = database.get_stats()

    return JSONResponse({
        "database_stats": stats,
        "request_info": logger.get_request_info(),
        "scope": "singleton - same instance across all requests"
    })

@app.get("/api/cache/stats")
def get_cache_stats(request,
                    cache: CacheService = Depends("cache"),
                    logger: RequestLogger = Depends("request_logger")):
    """Get cache statistics - demonstrates singleton behavior"""

    logger.log("Cache stats requested")

    stats = cache.get_stats()

    return JSONResponse({
        "cache_stats": stats,
        "request_info": logger.get_request_info(),
        "scope": "singleton - same instance across all requests"
    })

@app.get("/api/services/status")
def get_services_status(request,
                        session: UserSession = Depends("user_session"),
                        logger: RequestLogger = Depends("request_logger"),
                        database: DatabaseService = Depends("database"),
                        cache: CacheService = Depends("cache"),
                        analytics1: AnalyticsService = Depends("analytics"),
                        analytics2: AnalyticsService = Depends("analytics"),
                        processor1: TempProcessor = Depends("temp_processor"),
                        processor2: TempProcessor = Depends("temp_processor")):
    """Get status of all services - demonstrates scope behavior"""

    logger.log("Service status check")

    return JSONResponse({
        "services_status": {
            "singleton_services": {
                "database": {
                    "connection_id": database.connection_id,
                    "stats": database.get_stats()
                },
                "cache": {
                    "instance_id": cache.instance_id,
                    "stats": cache.get_stats()
                }
            },
            "request_scoped_services": {
                "user_session": {
                    "session_id": session.session_id,
                    "info": session.get_session_info()
                },
                "request_logger": {
                    "request_id": logger.request_id,
                    "info": logger.get_request_info()
                }
            },
            "transient_services": {
                "analytics": {
                    "instance1_id": analytics1.instance_id,
                    "instance2_id": analytics2.instance_id,
                    "same_instance": analytics1.instance_id == analytics2.instance_id
                },
                "temp_processor": {
                    "instance1_id": processor1.instance_id,
                    "instance2_id": processor2.instance_id,
                    "same_instance": processor1.instance_id == processor2.instance_id
                }
            }
        },
        "scope_explanation": {
            "singleton": "Same instance across all requests",
            "request": "Same instance within a request, new for each request",
            "transient": "New instance every time resolved"
        }
    })

@app.get("/health")
def health_check(request,
                 database: DatabaseService = Depends("database"),
                 cache: CacheService = Depends("cache"),
                 session: UserSession = Depends("user_session"),
                 logger: RequestLogger = Depends("request_logger"),
                 analytics: AnalyticsService = Depends("analytics")):
    """Health check endpoint showing all service scopes"""

    logger.log("Health check performed")

    return JSONResponse({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "services": {
            "singleton": {
                "database": database.get_stats(),
                "cache": cache.get_stats()
            },
            "request_scoped": {
                "user_session": session.get_session_info(),
                "request_logger": logger.get_request_info()
            },
            "transient": {
                "analytics": {
                    "instance_id": analytics.instance_id,
                    "created_at": analytics.created_at.isoformat()
                }
            }
        },
        "di_system": {
            "name": "Catzilla Revolutionary DI v0.2.0",
            "scopes_supported": ["singleton", "request", "transient"],
            "features": [
                "Fast C-backed resolution",
                "Automatic scope management",
                "Hierarchical containers",
                "Memory-optimized instances"
            ]
        }
    })

# ============================================================================
# 5. APPLICATION STARTUP
# ============================================================================

if __name__ == "__main__":
    print("\n🎯 Starting Catzilla DI Scoped Services Demo...")
    print("✨ FastAPI-identical Depends() syntax for seamless migration!")
    print("\nAvailable endpoints:")
    print("  GET  /                      - Home page")
    print("  GET  /api/user/{user_id}    - Get user (request-scoped demo)")
    print("  GET  /api/database/stats    - Database stats (singleton demo)")
    print("  GET  /api/cache/stats       - Cache stats (singleton demo)")
    print("  GET  /api/services/status   - All services status")
    print("  GET  /health                - Health check")

    print("\n🔄 Service Scopes with Depends():")
    print("  🔗 Singleton: Database, Cache (shared across requests)")
    print("  🔄 Request: UserSession, RequestLogger (per request)")
    print("  ⚡ Transient: Analytics, TempProcessor (new each time)")

    print("\n💡 Scope Behavior:")
    print("  • Same Depends() within route = same instance (singleton/request)")
    print("  • Same Depends() within route = different instance (transient)")
    print("  • Type hints show exactly what you're getting!")

    print(f"\n🚀 Server starting on http://localhost:8003")
    print("   Try: curl http://localhost:8003/api/user/alice")

    app.listen(8003)
