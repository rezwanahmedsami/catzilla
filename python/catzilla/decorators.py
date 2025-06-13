"""
Catzilla Dependency Injection Decorators
FastAPI-style decorators for service registration and injection
"""

import inspect
from functools import wraps
from typing import Any, Callable, Dict, List, Optional, Type, TypeVar, Union

from .dependency_injection import (
    DIContainer,
    DIContext,
    ServiceFactory,
    ServiceRegistration,
    get_default_container,
    resolve_service,
)

T = TypeVar("T")


def service(
    name: Optional[str] = None,
    scope: str = "singleton",
    dependencies: Optional[List[str]] = None,
    container: Optional[DIContainer] = None,
):
    """
    Decorator to register a class or function as a service

    Args:
        name: Service name (defaults to class/function name)
        scope: Service lifecycle ('singleton', 'transient', 'scoped', 'request')
        dependencies: List of dependency service names (auto-discovered if None)
        container: DI container to register with (defaults to global container)

    Usage:
        @service()
        class DatabaseService:
            def __init__(self, config: ConfigService):
                pass

        @service("cache", scope="singleton")
        class CacheService:
            pass
    """

    def decorator(cls_or_func: ServiceFactory) -> ServiceFactory:
        service_name = name or getattr(cls_or_func, "__name__", str(cls_or_func))
        target_container = container or get_default_container()

        # Register the service
        result = target_container.register(
            name=service_name,
            factory=cls_or_func,
            scope=scope,
            dependencies=dependencies,
        )

        if result != 0:
            raise RuntimeError(f"Failed to register service '{service_name}'")

        # Add metadata to the class/function
        cls_or_func._catzilla_service_name = service_name
        cls_or_func._catzilla_scope = scope
        cls_or_func._catzilla_dependencies = dependencies or []
        cls_or_func._catzilla_container = target_container

        return cls_or_func

    return decorator


def inject(*dependency_names: str, container: Optional[DIContainer] = None):
    """
    Decorator to inject dependencies into a function

    Args:
        *dependency_names: Names of services to inject as arguments
        container: DI container to resolve from (defaults to global container)

    Usage:
        @inject("database", "cache")
        def process_user(user_id: int, database: DatabaseService, cache: CacheService):
            # Dependencies are automatically resolved and injected
            pass
    """

    def decorator(func: Callable) -> Callable:
        target_container = container or get_default_container()

        @wraps(func)
        def wrapper(*args, **kwargs):
            # Get or create resolution context
            context = _get_current_context(target_container)

            # Resolve dependencies using C backend
            resolved_deps = []
            for dep_name in dependency_names:
                try:
                    resolved_deps.append(target_container.resolve(dep_name, context))
                except Exception as e:
                    raise RuntimeError(
                        f"Failed to resolve dependency '{dep_name}': {e}"
                    )

            # Call original function with injected dependencies
            return func(*args, *resolved_deps, **kwargs)

        # Store dependency metadata
        wrapper._catzilla_dependencies = dependency_names
        wrapper._catzilla_container = target_container
        wrapper._original_func = func

        return wrapper

    return decorator


def depends(service_name: str, container: Optional[DIContainer] = None):
    """
    FastAPI-style dependency function for parameter injection

    Args:
        service_name: Name of the service to resolve
        container: DI container to resolve from (defaults to global container)

    Usage:
        def get_database() -> DatabaseService:
            return depends("database")

        @app.get("/users/{user_id}")
        def get_user(user_id: int, db: DatabaseService = get_database()):
            pass
    """

    def dependency_resolver():
        target_container = container or get_default_container()
        context = _get_current_context(target_container)
        return target_container.resolve(service_name, context)

    # Mark as dependency resolver
    dependency_resolver._catzilla_dependency_name = service_name
    dependency_resolver._catzilla_container = container

    return dependency_resolver


class Depends:
    """
    FastAPI-style Depends class for cleaner parameter injection

    Usage:
        @app.get("/users/{user_id}")
        def get_user(user_id: int,
                    db: DatabaseService = Depends("database"),
                    cache: CacheService = Depends("cache")):
            pass
    """

    def __init__(self, service_name: str, container: Optional[DIContainer] = None):
        self.service_name = service_name
        self.container = container or get_default_container()

    def __call__(self) -> Any:
        context = _get_current_context(self.container)
        return self.container.resolve(self.service_name, context)

    def __repr__(self):
        return f"Depends('{self.service_name}')"


def auto_inject(container: Optional[DIContainer] = None):
    """
    Decorator for automatic dependency injection based on type hints

    Args:
        container: DI container to resolve from (defaults to global container)

    Usage:
        @auto_inject()
        def process_user(user_id: int,
                        database: DatabaseService,  # Auto-injected
                        cache: CacheService):       # Auto-injected
            pass
    """

    def decorator(func: Callable) -> Callable:
        target_container = container or get_default_container()

        # Analyze function signature for type hints
        sig = inspect.signature(func)
        injectable_params = {}

        for param_name, param in sig.parameters.items():
            if param.annotation != param.empty:
                # Try to find service by type name
                type_name = getattr(param.annotation, "__name__", str(param.annotation))

                # Check if there's a registered service with this type
                for service_name, registration in target_container._services.items():
                    if (
                        registration.python_type == param.annotation
                        or registration.name == type_name.lower()
                        or registration.name == param_name
                    ):
                        injectable_params[param_name] = service_name
                        break

        @wraps(func)
        def wrapper(*args, **kwargs):
            # Get current context
            context = _get_current_context(target_container)

            # Resolve and inject dependencies
            for param_name, service_name in injectable_params.items():
                if param_name not in kwargs:
                    try:
                        kwargs[param_name] = target_container.resolve(
                            service_name, context
                        )
                    except Exception as e:
                        raise RuntimeError(
                            f"Failed to auto-inject '{param_name}' from service '{service_name}': {e}"
                        )

            return func(*args, **kwargs)

        # Store metadata
        wrapper._catzilla_auto_inject = True
        wrapper._catzilla_injectable_params = injectable_params
        wrapper._catzilla_container = target_container
        wrapper._original_func = func

        return wrapper

    return decorator


def scoped(scope_name: str = "request", container: Optional[DIContainer] = None):
    """
    Decorator to create a scoped context for a function

    Args:
        scope_name: Name of the scope
        container: DI container to use (defaults to global container)

    Usage:
        @scoped("request")
        @inject("database")
        def handle_request(request, database: DatabaseService):
            # Database service is request-scoped
            pass
    """

    def decorator(func: Callable) -> Callable:
        target_container = container or get_default_container()

        @wraps(func)
        def wrapper(*args, **kwargs):
            # Create new scope context
            with target_container.resolution_context() as context:
                # Store context in thread-local storage
                _set_current_context(context)
                try:
                    return func(*args, **kwargs)
                finally:
                    _clear_current_context()

        wrapper._catzilla_scoped = True
        wrapper._catzilla_scope_name = scope_name
        wrapper._catzilla_container = target_container
        wrapper._original_func = func

        return wrapper

    return decorator


# Thread-local storage for current DI context
import threading

_local = threading.local()


def _get_current_context(container: DIContainer) -> Optional[DIContext]:
    """Get the current DI context from thread-local storage"""
    context = getattr(_local, "di_context", None)
    if context is None:
        # Create a new context if none exists
        context = container.create_context()
        _local.di_context = context
    return context


def _set_current_context(context: DIContext):
    """Set the current DI context in thread-local storage"""
    _local.di_context = context


def _clear_current_context():
    """Clear the current DI context from thread-local storage"""
    if hasattr(_local, "di_context"):
        context = _local.di_context
        if context:
            context.cleanup()
        del _local.di_context


# Utility functions for dependency analysis
def get_service_dependencies(service_or_func: Any) -> List[str]:
    """Get dependency names for a service or function"""
    return getattr(service_or_func, "_catzilla_dependencies", [])


def is_service_registered(obj: Any) -> bool:
    """Check if an object is registered as a service"""
    return hasattr(obj, "_catzilla_service_name")


def get_service_name(obj: Any) -> Optional[str]:
    """Get the service name for a registered object"""
    return getattr(obj, "_catzilla_service_name", None)


def get_service_scope(obj: Any) -> Optional[str]:
    """Get the scope for a registered service"""
    return getattr(obj, "_catzilla_scope", None)
