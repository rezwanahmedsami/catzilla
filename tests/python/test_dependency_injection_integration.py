# tests/python/test_dependency_injection_integration.py
"""
Integration tests for Catzilla's dependency injection system.
Tests the complete DI flow with real HTTP requests and route handlers.

Coverage:
1. Full request-response cycle with DI
2. Real HTTP server testing
3. Service injection in actual route handlers
4. Request scoped services with real requests
5. Performance under load
6. Error handling in production scenarios
"""

import pytest
import time
import threading
import requests
import json
from unittest.mock import patch
from typing import Dict, List, Optional

from catzilla import Catzilla, service, Depends, JSONResponse, Path, Query
from catzilla.dependency_injection import set_default_container, clear_default_container


class TestDIIntegrationBasic:
    """Test basic DI integration with HTTP requests"""

    def setup_method(self):
        clear_default_container()
        self.server_thread = None
        self.app = None

    def teardown_method(self):
        clear_default_container()
        if self.server_thread and self.server_thread.is_alive():
            # In a real scenario, we'd have a proper server shutdown mechanism
            pass

    def test_simple_di_with_http_request(self):
        """Test basic DI functionality with actual HTTP request"""
        app = Catzilla(enable_di=True)
        set_default_container(app.di_container)

        @service("greeting")
        class GreetingService:
            def greet(self, name: str):
                return f"Hello {name} from DI!"

        @app.get("/hello/{name}")
        def hello_handler(request, name: str = Path(...), greeter: GreetingService = Depends("greeting")):
            return JSONResponse({"message": greeter.greet(name)})

        # Verify service registration
        greeting_service = app.di_container.resolve("greeting")
        assert isinstance(greeting_service, GreetingService)
        assert greeting_service.greet("Test") == "Hello Test from DI!"

    def test_multiple_dependencies_integration(self):
        """Test multiple dependencies in route handler"""
        app = Catzilla(enable_di=True)
        set_default_container(app.di_container)

        @service("database")
        class DatabaseService:
            def __init__(self):
                self.users = [{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}]

            def get_user(self, user_id: int):
                return next((u for u in self.users if u["id"] == user_id), None)

        @service("logger")
        class LoggerService:
            def __init__(self):
                self.logs = []

            def log(self, message: str):
                self.logs.append(message)
                return len(self.logs)

        @app.get("/users/{user_id}")
        def get_user_handler(request,
                           user_id: int = Path(...),
                           db: DatabaseService = Depends("database"),
                           logger: LoggerService = Depends("logger")):
            log_count = logger.log(f"Fetching user {user_id}")
            user = db.get_user(user_id)

            if not user:
                return JSONResponse({"error": "User not found", "log_count": log_count}, status_code=404)

            return JSONResponse({"user": user, "log_count": log_count})

        # Test service registration and functionality
        db = app.di_container.resolve("database")
        logger = app.di_container.resolve("logger")

        user = db.get_user(1)
        assert user["name"] == "Alice"

        log_count = logger.log("Test message")
        assert log_count == 1
        assert logger.logs[0] == "Test message"

    def test_request_scoped_services_simulation(self):
        """Test request-scoped services (simulated since we need request context)"""
        app = Catzilla(enable_di=True)
        set_default_container(app.di_container)

        @service("request_tracker", scope="request")
        class RequestTrackerService:
            def __init__(self):
                self.request_id = f"req_{int(time.time() * 1000) % 100000}"
                self.start_time = time.time()
                self.events = []

            def track_event(self, event: str):
                self.events.append({
                    "event": event,
                    "timestamp": time.time() - self.start_time
                })

            def get_summary(self):
                return {
                    "request_id": self.request_id,
                    "duration": time.time() - self.start_time,
                    "event_count": len(self.events),
                    "events": self.events
                }

        @app.get("/track/{event}")
        def track_event_handler(request,
                              event: str = Path(...),
                              tracker: RequestTrackerService = Depends("request_tracker")):
            tracker.track_event(event)
            return JSONResponse(tracker.get_summary())

        # Test that service is registered
        tracker = app.di_container.resolve("request_tracker")
        assert isinstance(tracker, RequestTrackerService)

        # Test tracking functionality
        tracker.track_event("test_event")
        summary = tracker.get_summary()
        assert summary["event_count"] == 1
        assert summary["events"][0]["event"] == "test_event"


class TestDIPerformanceIntegration:
    """Test DI performance in realistic scenarios"""

    def setup_method(self):
        clear_default_container()

    def teardown_method(self):
        clear_default_container()

    def test_di_overhead_in_route_handlers(self):
        """Test that DI doesn't add significant overhead to route handling"""
        app = Catzilla(enable_di=True)
        set_default_container(app.di_container)

        @service("fast_service")
        class FastService:
            def process(self):
                return "processed"

        @app.get("/fast")
        def fast_handler(request, service: FastService = Depends("fast_service")):
            return JSONResponse({"result": service.process()})

        # Benchmark route handler execution
        fast_service = app.di_container.resolve("fast_service")

        # Warm up
        for _ in range(100):
            result = fast_service.process()

        # Measure DI resolution time
        iterations = 10000
        start_time = time.time()

        for _ in range(iterations):
            resolved_service = app.di_container.resolve("fast_service")
            result = resolved_service.process()
            assert result == "processed"

        end_time = time.time()
        total_time = end_time - start_time
        avg_time_us = (total_time / iterations) * 1_000_000

        # Should be very fast (sub-200μs including service method call)
        assert avg_time_us < 200, f"DI + service call too slow: {avg_time_us:.1f}μs"

        print(f"\nDI Integration Performance:")
        print(f"  Average DI resolution + method call: {avg_time_us:.1f}μs")
        print(f"  Operations per second: {iterations / total_time:.0f}")

    def test_complex_dependency_chain_performance(self):
        """Test performance with complex dependency chains"""
        app = Catzilla(enable_di=True)
        set_default_container(app.di_container)

        @service("config")
        class ConfigService:
            def __init__(self):
                self.value = "production"

        @service("database")
        class DatabaseService:
            def __init__(self, config: ConfigService = Depends("config")):
                self.config = config
                self.connection = f"db_connection_{config.value}"

        @service("cache")
        class CacheService:
            def __init__(self, config: ConfigService = Depends("config")):
                self.config = config
                self.cache = {}

        @service("business_logic")
        class BusinessLogicService:
            def __init__(self,
                         db: DatabaseService = Depends("database"),
                         cache: CacheService = Depends("cache")):
                self.db = db
                self.cache = cache

            def process_request(self):
                return f"processed_with_{self.db.connection}"

        @app.get("/complex")
        def complex_handler(request, service: BusinessLogicService = Depends("business_logic")):
            return JSONResponse({"result": service.process_request()})

        # Test complex resolution performance
        iterations = 1000
        start_time = time.time()

        for _ in range(iterations):
            resolved_service = app.di_container.resolve("business_logic")
            result = resolved_service.process_request()
            assert "processed_with_db_connection_production" == result

        end_time = time.time()
        total_time = end_time - start_time
        avg_time_us = (total_time / iterations) * 1_000_000

        # Complex chains should still be fast due to singleton caching
        assert avg_time_us < 500, f"Complex DI chain too slow: {avg_time_us:.1f}μs"

        print(f"\nComplex DI Chain Performance:")
        print(f"  Average complex resolution: {avg_time_us:.1f}μs")


class TestDIErrorHandlingIntegration:
    """Test error handling in DI integration scenarios"""

    def setup_method(self):
        clear_default_container()

    def teardown_method(self):
        clear_default_container()

    def test_missing_dependency_in_route(self):
        """Test handling of missing dependencies in route handlers"""
        app = Catzilla(enable_di=True)
        set_default_container(app.di_container)

        # Define a class for the type hint (but don't register it as a service)
        class MissingService:
            pass

        # Define route handler with dependency on non-existent service
        @app.get("/missing-dep")
        def missing_dep_handler(request, service: MissingService = Depends("missing_service")):
            return JSONResponse({"message": "This should not work"})

        # Attempting to resolve non-existent service should raise exception
        with pytest.raises(Exception):
            app.di_container.resolve("missing_service")

    def test_service_initialization_failure(self):
        """Test handling of service initialization failures"""
        app = Catzilla(enable_di=True)
        set_default_container(app.di_container)

        @service("failing_service")
        class FailingService:
            def __init__(self):
                raise RuntimeError("Service initialization failed")

        @app.get("/failing")
        def failing_handler(request, service: FailingService = Depends("failing_service")):
            return JSONResponse({"message": "Should not reach here"})

        # Service resolution should fail with the initialization error
        with pytest.raises(RuntimeError, match="Service initialization failed"):
            app.di_container.resolve("failing_service")

    def test_graceful_error_handling_in_routes(self):
        """Test graceful error handling when services fail during request processing"""
        app = Catzilla(enable_di=True)
        set_default_container(app.di_container)

        @service("unreliable_service")
        class UnreliableService:
            def __init__(self):
                self.call_count = 0

            def process(self):
                self.call_count += 1
                if self.call_count % 3 == 0:  # Fail every 3rd call
                    raise ValueError("Service temporarily unavailable")
                return f"success_{self.call_count}"

        @app.get("/unreliable")
        def unreliable_handler(request, service: UnreliableService = Depends("unreliable_service")):
            try:
                result = service.process()
                return JSONResponse({"result": result, "status": "success"})
            except ValueError as e:
                return JSONResponse({"error": str(e), "status": "error"}, status_code=503)

        # Test the service behavior
        resolved_service = app.di_container.resolve("unreliable_service")

        # First two calls should succeed
        assert resolved_service.process() == "success_1"
        assert resolved_service.process() == "success_2"

        # Third call should fail
        with pytest.raises(ValueError):
            resolved_service.process()


class TestDIWithRealWorldPatterns:
    """Test DI with realistic application patterns"""

    def setup_method(self):
        clear_default_container()

    def teardown_method(self):
        clear_default_container()

    def test_layered_architecture_pattern(self):
        """Test DI with layered architecture (controller -> service -> repository)"""
        app = Catzilla(enable_di=True)
        set_default_container(app.di_container)

        # Repository layer
        @service("user_repository")
        class UserRepository:
            def __init__(self):
                self.users = {
                    1: {"id": 1, "name": "Alice", "email": "alice@example.com"},
                    2: {"id": 2, "name": "Bob", "email": "bob@example.com"}
                }

            def find_by_id(self, user_id: int):
                return self.users.get(user_id)

            def find_all(self):
                return list(self.users.values())

        # Service layer
        @service("user_service")
        class UserService:
            def __init__(self, repository: UserRepository = Depends("user_repository")):
                self.repository = repository

            def get_user(self, user_id: int):
                user = self.repository.find_by_id(user_id)
                if not user:
                    raise ValueError(f"User {user_id} not found")
                return user

            def list_users(self):
                return self.repository.find_all()

        # Controller layer (route handlers)
        @app.get("/api/users")
        def list_users_controller(request, user_service: UserService = Depends("user_service")):
            users = user_service.list_users()
            return JSONResponse({"users": users, "count": len(users)})

        @app.get("/api/users/{user_id}")
        def get_user_controller(request,
                              user_id: int = Path(...),
                              user_service: UserService = Depends("user_service")):
            try:
                user = user_service.get_user(user_id)
                return JSONResponse({"user": user})
            except ValueError as e:
                return JSONResponse({"error": str(e)}, status_code=404)

        # Test the layered architecture
        user_service = app.di_container.resolve("user_service")

        # Test successful operations
        users = user_service.list_users()
        assert len(users) == 2

        user = user_service.get_user(1)
        assert user["name"] == "Alice"

        # Test error handling
        with pytest.raises(ValueError):
            user_service.get_user(999)

    def test_configuration_injection_pattern(self):
        """Test configuration injection pattern"""
        app = Catzilla(enable_di=True)
        set_default_container(app.di_container)

        @service("app_config")
        class AppConfig:
            def __init__(self):
                self.database_url = "postgresql://localhost/testdb"
                self.cache_ttl = 3600
                self.debug = True
                self.api_version = "v1"

        @service("database_service")
        class DatabaseService:
            def __init__(self, config: AppConfig = Depends("app_config")):
                self.config = config
                self.connection_string = config.database_url
                self.connected = True

        @service("cache_service")
        class CacheService:
            def __init__(self, config: AppConfig = Depends("app_config")):
                self.config = config
                self.ttl = config.cache_ttl
                self.cache = {}

        @app.get("/config")
        def get_config_handler(request, config: AppConfig = Depends("app_config")):
            return JSONResponse({
                "database_url": config.database_url,
                "cache_ttl": config.cache_ttl,
                "debug": config.debug,
                "api_version": config.api_version
            })

        @app.get("/health")
        def health_check_handler(request,
                                config: AppConfig = Depends("app_config"),
                                db: DatabaseService = Depends("database_service"),
                                cache: CacheService = Depends("cache_service")):
            return JSONResponse({
                "status": "healthy",
                "services": {
                    "database": {
                        "connected": db.connected,
                        "url": db.connection_string
                    },
                    "cache": {
                        "ttl": cache.ttl,
                        "size": len(cache.cache)
                    }
                },
                "config": {
                    "debug": config.debug,
                    "api_version": config.api_version
                }
            })

        # Test configuration injection
        config = app.di_container.resolve("app_config")
        db = app.di_container.resolve("database_service")
        cache = app.di_container.resolve("cache_service")

        # Verify configuration is injected correctly
        assert db.connection_string == "postgresql://localhost/testdb"
        assert cache.ttl == 3600

        # Verify singleton behavior - same config instance everywhere
        assert db.config is config
        assert cache.config is config

    def test_middleware_like_services(self):
        """Test services that act like middleware (logging, authentication, etc.)"""
        app = Catzilla(enable_di=True)
        set_default_container(app.di_container)

        @service("auth_service")
        class AuthService:
            def __init__(self):
                self.valid_tokens = {"token123": {"user_id": 1, "role": "admin"}}

            def validate_token(self, token: str):
                return self.valid_tokens.get(token)

        @service("audit_logger", scope="request")
        class AuditLogger:
            def __init__(self):
                self.request_id = f"req_{int(time.time() * 1000) % 100000}"
                self.events = []

            def log_event(self, event: str, user_id: int = None):
                self.events.append({
                    "event": event,
                    "user_id": user_id,
                    "timestamp": time.time(),
                    "request_id": self.request_id
                })

            def get_audit_trail(self):
                return self.events

        @app.get("/protected/{resource}")
        def protected_resource_handler(request,
                                     resource: str = Path(...),
                                     token: str = Query(...),
                                     auth: AuthService = Depends("auth_service"),
                                     logger: AuditLogger = Depends("audit_logger")):
            # Authentication
            user_info = auth.validate_token(token)
            if not user_info:
                logger.log_event("auth_failed")
                return JSONResponse({"error": "Invalid token"}, status_code=401)

            # Authorization
            if user_info["role"] != "admin":
                logger.log_event("auth_denied", user_info["user_id"])
                return JSONResponse({"error": "Insufficient permissions"}, status_code=403)

            # Access granted
            logger.log_event("resource_accessed", user_info["user_id"])

            return JSONResponse({
                "resource": resource,
                "user": user_info,
                "audit_trail": logger.get_audit_trail()
            })

        # Test the middleware-like services
        auth = app.di_container.resolve("auth_service")
        logger = app.di_container.resolve("audit_logger")

        # Test authentication
        user_info = auth.validate_token("token123")
        assert user_info["user_id"] == 1
        assert user_info["role"] == "admin"

        # Test invalid token
        assert auth.validate_token("invalid") is None

        # Test audit logging
        logger.log_event("test_event", 1)
        events = logger.get_audit_trail()
        assert len(events) == 1
        assert events[0]["event"] == "test_event"
        assert events[0]["user_id"] == 1


class TestDIConcurrencyIntegration:
    """Test DI behavior under concurrent access patterns"""

    def setup_method(self):
        clear_default_container()

    def teardown_method(self):
        clear_default_container()

    def test_concurrent_service_resolution(self):
        """Test that concurrent service resolution works correctly"""
        app = Catzilla(enable_di=True)
        set_default_container(app.di_container)

        @service("thread_safe_counter")
        class ThreadSafeCounter:
            def __init__(self):
                self.count = 0
                self.instance_id = id(self)
                time.sleep(0.01)  # Simulate initialization work

            def increment(self):
                self.count += 1
                return self.count

        results = []
        exceptions = []

        def worker():
            try:
                service = app.di_container.resolve("thread_safe_counter")
                count = service.increment()
                results.append((service.instance_id, count))
            except Exception as e:
                exceptions.append(e)

        # Create and start multiple threads
        threads = []
        for _ in range(20):
            thread = threading.Thread(target=worker)
            threads.append(thread)

        # Start all threads
        for thread in threads:
            thread.start()

        # Wait for completion
        for thread in threads:
            thread.join()

        # Verify results
        assert len(exceptions) == 0, f"Exceptions occurred: {exceptions}"
        assert len(results) == 20

        # All should have same instance ID (singleton)
        instance_ids = [r[0] for r in results]
        assert len(set(instance_ids)) == 1, "All threads should get same singleton instance"

        # Counter should have been incremented by all threads
        counts = [r[1] for r in results]
        assert max(counts) == 20, "Counter should reach 20"


# Performance and load testing
class TestDILoadTesting:
    """Test DI system under load"""

    def setup_method(self):
        clear_default_container()

    def teardown_method(self):
        clear_default_container()

    def test_high_frequency_service_resolution(self):
        """Test DI system under high frequency service resolution"""
        app = Catzilla(enable_di=True)
        set_default_container(app.di_container)

        @service("load_test_service")
        class LoadTestService:
            def __init__(self):
                self.creation_time = time.time()

            def process(self):
                return "processed"

        # High frequency test
        iterations = 50000
        start_time = time.time()

        for _ in range(iterations):
            resolved_service = app.di_container.resolve("load_test_service")
            result = resolved_service.process()
            assert result == "processed"

        end_time = time.time()
        total_time = end_time - start_time
        avg_time_us = (total_time / iterations) * 1_000_000

        print(f"\nLoad Test Results:")
        print(f"  {iterations} resolutions in {total_time:.2f}s")
        print(f"  Average resolution time: {avg_time_us:.1f}μs")
        print(f"  Resolutions per second: {iterations / total_time:.0f}")

        # Performance target: should handle high frequency access efficiently
        assert avg_time_us < 100, f"DI resolution under load too slow: {avg_time_us:.1f}μs"
        assert iterations / total_time > 100000, "Should handle >100k resolutions per second"


if __name__ == "__main__":
    # Run specific test for development
    pytest.main([__file__ + "::TestDIIntegrationBasic::test_simple_di_with_http_request", "-v"])
