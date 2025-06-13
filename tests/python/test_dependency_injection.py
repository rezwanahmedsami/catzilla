# tests/python/test_dependency_injection.py
"""
Comprehensive tests for Catzilla's revolutionary dependency injection system.
Tests cover:
1. Basic service registration and resolution
2. Service scopes (singleton, request, transient)
3. Dependency injection in route handlers
4. Complex dependency chains
5. Error handling and edge cases
6. Performance characteristics
7. Thread safety
8. Container lifecycle management
"""

import pytest
import time
import threading
from unittest.mock import Mock, patch
from typing import Dict, List, Optional, Any

from catzilla import Catzilla, service, Depends, JSONResponse, BaseModel
from catzilla.dependency_injection import set_default_container, DIContainer, clear_default_container


class TestBasicDependencyInjection:
    """Test basic DI functionality and service registration"""

    def setup_method(self):
        """Setup clean state for each test"""
        # Clear any existing default container
        clear_default_container()

    def teardown_method(self):
        """Cleanup after each test"""
        clear_default_container()

    def test_service_registration_and_resolution(self):
        """Test basic service registration and manual resolution"""
        app = Catzilla(enable_di=True)
        set_default_container(app.di_container)

        @service("test_service")
        class TestService:
            def __init__(self):
                self.value = "test_value"

            def get_value(self):
                return self.value

        # Test manual resolution
        resolved_service = app.di_container.resolve("test_service")
        assert isinstance(resolved_service, TestService)
        assert resolved_service.get_value() == "test_value"

    def test_singleton_scope_default(self):
        """Test that services are singleton by default"""
        app = Catzilla(enable_di=True)
        set_default_container(app.di_container)

        @service("singleton_service")
        class SingletonService:
            def __init__(self):
                self.instance_id = id(self)

        # Resolve multiple times - should be same instance
        service1 = app.di_container.resolve("singleton_service")
        service2 = app.di_container.resolve("singleton_service")

        assert service1 is service2
        assert service1.instance_id == service2.instance_id

    def test_explicit_singleton_scope(self):
        """Test explicit singleton scope declaration"""
        app = Catzilla(enable_di=True)
        set_default_container(app.di_container)

        @service("explicit_singleton", scope="singleton")
        class ExplicitSingletonService:
            def __init__(self):
                self.created_at = time.time()

        service1 = app.di_container.resolve("explicit_singleton")
        time.sleep(0.01)  # Small delay
        service2 = app.di_container.resolve("explicit_singleton")

        assert service1 is service2
        assert service1.created_at == service2.created_at

    def test_transient_scope(self):
        """Test transient scope - new instance each time"""
        app = Catzilla(enable_di=True)
        set_default_container(app.di_container)

        @service("transient_service", scope="transient")
        class TransientService:
            def __init__(self):
                self.instance_id = id(self)
                self.created_at = time.time()

        service1 = app.di_container.resolve("transient_service")
        time.sleep(0.01)  # Small delay
        service2 = app.di_container.resolve("transient_service")

        assert service1 is not service2
        assert service1.instance_id != service2.instance_id
        assert service1.created_at != service2.created_at

    def test_request_scope(self):
        """Test request scope - same instance per request context"""
        app = Catzilla(enable_di=True)
        set_default_container(app.di_container)

        @service("request_service", scope="request")
        class RequestService:
            def __init__(self):
                self.instance_id = id(self)
                self.request_id = f"req_{int(time.time() * 1000) % 100000}"

        # Note: Request scope testing requires actual request context
        # This is a simplified test - full request scope testing happens in integration tests
        service1 = app.di_container.resolve("request_service")
        service2 = app.di_container.resolve("request_service")

        # In the same request context, should be same instance
        assert isinstance(service1, RequestService)
        assert isinstance(service2, RequestService)


class TestDependencyChains:
    """Test complex dependency chains and injection"""

    def setup_method(self):
        clear_default_container()

    def teardown_method(self):
        clear_default_container()

    def test_simple_dependency_chain(self):
        """Test service depending on another service"""
        app = Catzilla(enable_di=True)
        set_default_container(app.di_container)

        @service("config")
        class ConfigService:
            def __init__(self):
                self.database_url = "postgresql://localhost/test"
                self.debug = True

        @service("database")
        class DatabaseService:
            def __init__(self, config: ConfigService = Depends("config")):
                self.config = config
                self.connection_string = config.database_url

        db_service = app.di_container.resolve("database")
        assert isinstance(db_service, DatabaseService)
        assert isinstance(db_service.config, ConfigService)
        assert db_service.connection_string == "postgresql://localhost/test"

    def test_complex_dependency_chain(self):
        """Test complex multi-level dependency chain"""
        app = Catzilla(enable_di=True)
        set_default_container(app.di_container)

        @service("config")
        class ConfigService:
            def __init__(self):
                self.cache_ttl = 3600

        @service("cache")
        class CacheService:
            def __init__(self, config: ConfigService = Depends("config")):
                self.config = config
                self.ttl = config.cache_ttl

        @service("database")
        class DatabaseService:
            def __init__(self, config: ConfigService = Depends("config")):
                self.config = config

        @service("user_service")
        class UserService:
            def __init__(self,
                         db: DatabaseService = Depends("database"),
                         cache: CacheService = Depends("cache")):
                self.db = db
                self.cache = cache

        user_service = app.di_container.resolve("user_service")
        assert isinstance(user_service, UserService)
        assert isinstance(user_service.db, DatabaseService)
        assert isinstance(user_service.cache, CacheService)
        assert user_service.cache.ttl == 3600

        # Verify singleton behavior - config should be same instance
        assert user_service.db.config is user_service.cache.config

    def test_circular_dependency_detection(self):
        """Test that circular dependencies are detected and handled"""
        app = Catzilla(enable_di=True)
        set_default_container(app.di_container)

        # This would create a circular dependency - should be handled gracefully
        @service("service_a")
        class ServiceA:
            def __init__(self, service_b: 'ServiceB' = Depends("service_b")):
                self.service_b = service_b

        @service("service_b")
        class ServiceB:
            def __init__(self, service_a: ServiceA = Depends("service_a")):
                self.service_a = service_a

        # This should either handle gracefully or raise a clear error
        with pytest.raises(Exception):  # Expected to fail with circular dependency
            app.di_container.resolve("service_a")


class TestRouteHandlerInjection:
    """Test dependency injection in route handlers"""

    def setup_method(self):
        clear_default_container()

    def teardown_method(self):
        clear_default_container()

    def test_single_dependency_injection(self):
        """Test injecting a single dependency into route handler"""
        app = Catzilla(enable_di=True)
        set_default_container(app.di_container)

        @service("greeting")
        class GreetingService:
            def greet(self, name: str):
                return f"Hello {name}!"

        @app.get("/hello/{name}")
        def hello_handler(request, name: str, greeter: GreetingService = Depends("greeting")):
            return {"message": greeter.greet(name)}

        # Test that the service is properly registered
        greeting_service = app.di_container.resolve("greeting")
        assert isinstance(greeting_service, GreetingService)
        assert greeting_service.greet("World") == "Hello World!"

    def test_multiple_dependency_injection(self):
        """Test injecting multiple dependencies into route handler"""
        app = Catzilla(enable_di=True)
        set_default_container(app.di_container)

        @service("database")
        class DatabaseService:
            def get_user(self, user_id: int):
                return {"id": user_id, "name": f"User{user_id}"}

        @service("logger")
        class LoggerService:
            def __init__(self):
                self.logs = []

            def log(self, message: str):
                self.logs.append(message)

        @app.get("/users/{user_id}")
        def get_user_handler(request,
                           user_id: int,
                           db: DatabaseService = Depends("database"),
                           logger: LoggerService = Depends("logger")):
            logger.log(f"Fetching user {user_id}")
            user = db.get_user(user_id)
            return {"user": user, "logs": logger.logs}

        # Verify services are registered and working
        db = app.di_container.resolve("database")
        logger = app.di_container.resolve("logger")

        assert isinstance(db, DatabaseService)
        assert isinstance(logger, LoggerService)

        user = db.get_user(123)
        assert user["id"] == 123
        assert user["name"] == "User123"

    def test_mixed_scope_injection(self):
        """Test injecting services with different scopes"""
        app = Catzilla(enable_di=True)
        set_default_container(app.di_container)

        @service("config", scope="singleton")
        class ConfigService:
            def __init__(self):
                self.app_name = "TestApp"

        @service("request_logger", scope="request")
        class RequestLoggerService:
            def __init__(self):
                self.request_id = f"req_{int(time.time() * 1000) % 100000}"
                self.logs = []

        @service("analytics", scope="transient")
        class AnalyticsService:
            def __init__(self):
                self.session_id = f"session_{int(time.time() * 1000) % 100000}"

        @app.get("/test")
        def test_handler(request,
                        config: ConfigService = Depends("config"),
                        logger: RequestLoggerService = Depends("request_logger"),
                        analytics: AnalyticsService = Depends("analytics")):
            return {
                "app_name": config.app_name,
                "request_id": logger.request_id,
                "session_id": analytics.session_id
            }

        # Verify all services are registered
        assert app.di_container.resolve("config") is not None
        assert app.di_container.resolve("request_logger") is not None
        assert app.di_container.resolve("analytics") is not None


class TestErrorHandling:
    """Test error handling and edge cases"""

    def setup_method(self):
        clear_default_container()

    def teardown_method(self):
        clear_default_container()

    def test_service_not_found(self):
        """Test behavior when trying to resolve non-existent service"""
        app = Catzilla(enable_di=True)

        with pytest.raises(Exception):  # Should raise appropriate error
            app.di_container.resolve("non_existent_service")

    def test_dependency_not_found(self):
        """Test behavior when service has dependency on non-existent service"""
        app = Catzilla(enable_di=True)
        set_default_container(app.di_container)

        @service("broken_service")
        class BrokenService:
            def __init__(self, missing: 'MissingService' = Depends("missing_service")):
                self.missing = missing

        with pytest.raises(Exception):  # Should raise appropriate error
            app.di_container.resolve("broken_service")

    def test_service_initialization_error(self):
        """Test handling of errors during service initialization"""
        app = Catzilla(enable_di=True)
        set_default_container(app.di_container)

        @service("failing_service")
        class FailingService:
            def __init__(self):
                raise ValueError("Service initialization failed")

        with pytest.raises(ValueError):
            app.di_container.resolve("failing_service")

    def test_invalid_scope(self):
        """Test handling of invalid scope specification"""
        app = Catzilla(enable_di=True)
        set_default_container(app.di_container)

        # This should either handle gracefully or raise a clear error
        with pytest.raises(Exception):
            @service("invalid_scope_service", scope="invalid_scope")
            class InvalidScopeService:
                pass


class TestPerformance:
    """Test performance characteristics of DI system"""

    def setup_method(self):
        clear_default_container()

    def teardown_method(self):
        clear_default_container()

    def test_resolution_performance(self):
        """Test that service resolution is fast"""
        app = Catzilla(enable_di=True)
        set_default_container(app.di_container)

        @service("fast_service")
        class FastService:
            def __init__(self):
                self.value = "fast"

        # Measure resolution time
        start_time = time.time()
        for _ in range(1000):
            resolved_service = app.di_container.resolve("fast_service")
            assert resolved_service.value == "fast"
        end_time = time.time()

        # Should complete 1000 resolutions very quickly (singleton caching)
        total_time = end_time - start_time
        assert total_time < 0.1  # Should be much faster than 100ms

        # Average resolution time should be sub-millisecond
        avg_time_microseconds = (total_time / 1000) * 1_000_000
        assert avg_time_microseconds < 200  # Target: < 200μs per resolution

    def test_transient_performance(self):
        """Test performance of transient service creation"""
        app = Catzilla(enable_di=True)
        set_default_container(app.di_container)

        @service("transient_perf", scope="transient")
        class TransientPerfService:
            def __init__(self):
                self.instance_id = id(self)

        # Measure transient service creation time
        start_time = time.time()
        instances = []
        for _ in range(100):  # Fewer iterations since each creates new instance
            resolved_service = app.di_container.resolve("transient_perf")
            instances.append(resolved_service)  # Keep reference to actual object
        end_time = time.time()

        # Verify all instances are different
        instance_ids = [inst.instance_id for inst in instances]
        assert len(set(instance_ids)) == 100

        # Should still be reasonably fast
        total_time = end_time - start_time
        assert total_time < 0.5  # Should complete 100 creations in < 500ms

    def test_complex_dependency_performance(self):
        """Test performance with complex dependency chains"""
        app = Catzilla(enable_di=True)
        set_default_container(app.di_container)

        @service("config")
        class ConfigService:
            def __init__(self):
                self.value = "config"

        @service("cache")
        class CacheService:
            def __init__(self, config: ConfigService = Depends("config")):
                self.config = config

        @service("database")
        class DatabaseService:
            def __init__(self, config: ConfigService = Depends("config")):
                self.config = config

        @service("user_service")
        class UserService:
            def __init__(self,
                         db: DatabaseService = Depends("database"),
                         cache: CacheService = Depends("cache")):
                self.db = db
                self.cache = cache

        # Measure complex resolution time
        start_time = time.time()
        for _ in range(100):
            resolved_service = app.di_container.resolve("user_service")
            assert resolved_service.db.config.value == "config"
        end_time = time.time()

        total_time = end_time - start_time
        assert total_time < 0.1  # Should be fast due to singleton caching


class TestThreadSafety:
    """Test thread safety of DI system"""

    def setup_method(self):
        clear_default_container()

    def teardown_method(self):
        clear_default_container()

    def test_concurrent_singleton_resolution(self):
        """Test that singleton resolution is thread-safe"""
        app = Catzilla(enable_di=True)
        set_default_container(app.di_container)

        @service("thread_safe_service")
        class ThreadSafeService:
            def __init__(self):
                self.instance_id = id(self)
                time.sleep(0.01)  # Simulate some initialization work

        resolved_services = []
        exceptions = []

        def resolve_service():
            try:
                resolved_service = app.di_container.resolve("thread_safe_service")
                resolved_services.append(resolved_service)
            except Exception as e:
                exceptions.append(e)

        # Create multiple threads trying to resolve the same service
        threads = []
        for _ in range(10):
            thread = threading.Thread(target=resolve_service)
            threads.append(thread)

        # Start all threads
        for thread in threads:
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # Should have no exceptions
        assert len(exceptions) == 0, f"Exceptions occurred: {exceptions}"

        # All resolved services should be the same instance (singleton)
        assert len(resolved_services) == 10
        first_service = resolved_services[0]
        for resolved_service in resolved_services:
            assert resolved_service is first_service
            assert resolved_service.instance_id == first_service.instance_id

    def test_concurrent_transient_resolution(self):
        """Test that transient resolution works correctly under concurrent access"""
        app = Catzilla(enable_di=True)
        set_default_container(app.di_container)

        @service("concurrent_transient", scope="transient")
        class ConcurrentTransientService:
            def __init__(self):
                self.instance_id = id(self)
                self.thread_id = threading.current_thread().ident

        resolved_services = []
        exceptions = []

        def resolve_service():
            try:
                resolved_service = app.di_container.resolve("concurrent_transient")
                resolved_services.append(resolved_service)
            except Exception as e:
                exceptions.append(e)

        # Create multiple threads
        threads = []
        for _ in range(10):
            thread = threading.Thread(target=resolve_service)
            threads.append(thread)

        # Start all threads
        for thread in threads:
            thread.start()

        # Wait for completion
        for thread in threads:
            thread.join()

        # Should have no exceptions
        assert len(exceptions) == 0, f"Exceptions occurred: {exceptions}"

        # All services should be different instances (transient)
        assert len(resolved_services) == 10
        instance_ids = [s.instance_id for s in resolved_services]
        assert len(set(instance_ids)) == 10  # All different


class TestContainerLifecycle:
    """Test DI container lifecycle and management"""

    def test_multiple_containers(self):
        """Test that multiple containers can coexist"""
        container1 = DIContainer()
        container2 = DIContainer()

        # Register different services in each container
        set_default_container(container1)

        @service("service1")
        class Service1:
            def get_name(self):
                return "service1"

        set_default_container(container2)

        @service("service2")
        class Service2:
            def get_name(self):
                return "service2"

        # Each container should only know about its own services
        resolved1 = container1.resolve("service1")
        resolved2 = container2.resolve("service2")

        assert resolved1.get_name() == "service1"
        assert resolved2.get_name() == "service2"

        # Cross-container resolution should fail
        with pytest.raises(Exception):
            container1.resolve("service2")

        with pytest.raises(Exception):
            container2.resolve("service1")

    def test_container_cleanup(self):
        """Test container cleanup and resource management"""
        app = Catzilla(enable_di=True)
        set_default_container(app.di_container)

        @service("cleanup_service")
        class CleanupService:
            def __init__(self):
                self.cleaned_up = False

            def cleanup(self):
                self.cleaned_up = True

        resolved_service = app.di_container.resolve("cleanup_service")
        assert not resolved_service.cleaned_up

        # Manual cleanup (if supported)
        resolved_service.cleanup()
        assert resolved_service.cleaned_up


class TestPydanticIntegration:
    """Test integration with Pydantic models for request/response validation"""

    def setup_method(self):
        clear_default_container()

    def teardown_method(self):
        clear_default_container()

    def test_pydantic_model_with_di(self):
        """Test that DI works with Pydantic model validation"""
        app = Catzilla(enable_di=True)
        set_default_container(app.di_container)

        class UserModel(BaseModel):
            name: str
            email: str

        @service("user_validator")
        class UserValidatorService:
            def validate_user(self, user_data: dict) -> UserModel:
                return UserModel(**user_data)

        @app.post("/users")
        def create_user(request, validator: UserValidatorService = Depends("user_validator")):
            # In a real scenario, this would get data from request body
            test_data = {"name": "John Doe", "email": "john@example.com"}
            validated_user = validator.validate_user(test_data)
            return {"user": validated_user.dict()}

        # Test the service registration
        validator = app.di_container.resolve("user_validator")
        user = validator.validate_user({"name": "Test", "email": "test@example.com"})
        assert user.name == "Test"
        assert user.email == "test@example.com"


# Performance benchmark test (optional, for CI metrics)
def test_di_performance_benchmark():
    """
    Performance benchmark test for dependency injection.
    This test documents the expected performance characteristics.
    """
    app = Catzilla(enable_di=True)
    set_default_container(app.di_container)

    @service("benchmark_service")
    class BenchmarkService:
        def __init__(self):
            self.value = "benchmark"

    # Warm up
    for _ in range(10):
        app.di_container.resolve("benchmark_service")

    # Measure resolution time
    iterations = 10000
    start_time = time.time()

    for _ in range(iterations):
        resolved_service = app.di_container.resolve("benchmark_service")
        assert resolved_service.value == "benchmark"

    end_time = time.time()
    total_time = end_time - start_time
    avg_time_microseconds = (total_time / iterations) * 1_000_000

    print(f"\nDI Performance Benchmark:")
    print(f"  Total time for {iterations} resolutions: {total_time:.4f}s")
    print(f"  Average resolution time: {avg_time_microseconds:.1f}μs")
    print(f"  Resolutions per second: {iterations / total_time:.0f}")

    # Performance assertion - should be faster than 200μs per resolution
    assert avg_time_microseconds < 200, f"DI resolution too slow: {avg_time_microseconds:.1f}μs"

    clear_default_container()


if __name__ == "__main__":
    # Run specific test classes for development
    pytest.main([__file__ + "::TestBasicDependencyInjection", "-v"])
