"""
Catzilla Dependency Injection System - Python Bridge
High-performance dependency injection with C backend
"""

import ctypes
import inspect
import threading
from contextlib import contextmanager
from dataclasses import dataclass
from functools import wraps
from typing import Any, Callable, Dict, List, Optional, Type, TypeVar, Union

# Type hints
T = TypeVar("T")
ServiceFactory = Union[Type[T], Callable[..., T]]

# Load the C extension (will be implemented later)
try:
    import _catzilla

    _c_extension_available = True
except ImportError:
    _c_extension_available = False

    # Fallback mode for development
    class _MockCExtension:
        @staticmethod
        def di_container_create():
            return 1  # Mock container ID

        @staticmethod
        def di_container_set_parent(container, parent):
            return 0

        @staticmethod
        def di_register_service_python(
            container, name, type_name, scope, factory, deps
        ):
            return 0

        @staticmethod
        def di_resolve_service(container, name, context):
            return None  # Will call Python factory

        @staticmethod
        def di_create_context(container):
            return 2  # Mock context ID

        @staticmethod
        def di_cleanup_context(context):
            pass

    _catzilla = _MockCExtension()


@dataclass
class ServiceRegistration:
    """Metadata for a registered service"""

    name: str
    factory: ServiceFactory
    scope: str
    dependencies: List[str]
    python_type: Optional[Type] = None
    is_registered: bool = False


class DIContext:
    """Dependency resolution context for request-scoped services"""

    def __init__(self, container: "DIContainer"):
        self.container = container
        self._c_context = _catzilla.di_create_context(container._c_container)
        self._resolved_services: Dict[str, Any] = {}
        self._is_active = True

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cleanup()

    def cleanup(self):
        """Clean up request-scoped services"""
        if self._is_active:
            _catzilla.di_cleanup_context(self._c_context)
            self._resolved_services.clear()
            self._is_active = False


class DIContainer:
    """High-performance dependency injection container with C backend"""

    def __init__(self, parent: Optional["DIContainer"] = None):
        # Initialize C container
        self._c_container = _catzilla.di_container_create()
        if parent:
            _catzilla.di_container_set_parent(self._c_container, parent._c_container)

        # Python service registry (for metadata and fallback)
        self._services: Dict[str, ServiceRegistration] = {}
        self._factories: Dict[str, ServiceFactory] = {}
        self._parent = parent
        self._lock = threading.RLock()

        # Thread-local context storage
        self._local = threading.local()

    def register(
        self,
        name: str,
        factory: ServiceFactory,
        scope: str = "singleton",
        dependencies: Optional[List[str]] = None,
    ) -> int:
        """
        Register a service with the container

        Args:
            name: Service name/identifier
            factory: Factory function or class to create service instances
            scope: Service lifecycle ('singleton', 'transient', 'scoped', 'request')
            dependencies: List of dependency service names

        Returns:
            0 on success, -1 on failure
        """
        with self._lock:
            if name in self._services:
                raise ValueError(f"Service '{name}' is already registered")

            # Analyze factory for automatic dependency discovery
            if dependencies is None:
                dependencies = self._analyze_dependencies(factory)

            # Get type name
            type_name = getattr(factory, "__name__", str(type(factory)))

            # Register in C container for fast resolution
            result = _catzilla.di_register_service_python(
                self._c_container,
                name.encode("utf-8"),
                type_name.encode("utf-8"),
                scope.encode("utf-8"),
                factory,  # Pass Python object reference
                [dep.encode("utf-8") for dep in dependencies],
            )

            if result != 0:
                raise RuntimeError(f"Failed to register service '{name}' in C backend")

            # Store Python metadata
            registration = ServiceRegistration(
                name=name,
                factory=factory,
                scope=scope,
                dependencies=dependencies,
                python_type=factory if inspect.isclass(factory) else None,
                is_registered=True,
            )

            self._services[name] = registration
            self._factories[name] = factory

            return result

    def resolve(self, name: str, context: Optional[DIContext] = None) -> Any:
        """
        Resolve a service instance

        Args:
            name: Service name to resolve
            context: Optional DI context for request-scoped services

        Returns:
            Service instance
        """
        # Try C backend first for performance
        c_context = context._c_context if context else None
        c_result = _catzilla.di_resolve_service(
            self._c_container, name.encode("utf-8"), c_context
        )

        if c_result is not None:
            return c_result

        # Fallback to Python resolution
        return self._resolve_python(name, context)

    def _resolve_python(self, name: str, context: Optional[DIContext] = None) -> Any:
        """Python fallback for service resolution"""
        with self._lock:
            # Check if service is registered
            if name not in self._services:
                # Try parent container
                if self._parent:
                    return self._parent.resolve(name, context)
                raise ValueError(f"Service '{name}' not found")

            registration = self._services[name]

            # Check for circular dependencies
            if context and name in getattr(context, "_resolution_stack", set()):
                raise RuntimeError(f"Circular dependency detected for service '{name}'")

            # Handle singleton scope
            if registration.scope == "singleton" and hasattr(
                registration, "_cached_instance"
            ):
                return registration._cached_instance

            # Resolve dependencies
            resolved_deps = {}
            if registration.dependencies:
                # Track resolution stack
                if context:
                    if not hasattr(context, "_resolution_stack"):
                        context._resolution_stack = set()
                    context._resolution_stack.add(name)

                try:
                    for dep_name in registration.dependencies:
                        resolved_deps[dep_name] = self.resolve(dep_name, context)
                finally:
                    if context and hasattr(context, "_resolution_stack"):
                        context._resolution_stack.discard(name)

            # Create service instance
            instance = self._create_instance(registration, resolved_deps)

            # Cache singleton instances
            if registration.scope == "singleton":
                registration._cached_instance = instance

            return instance

    def _create_instance(
        self, registration: ServiceRegistration, dependencies: Dict[str, Any]
    ) -> Any:
        """Create a service instance using the factory"""
        factory = registration.factory

        if inspect.isclass(factory):
            # Handle class constructor injection
            if dependencies:
                # Use dependency injection
                sig = inspect.signature(factory.__init__)
                params = {}

                for param_name, param in sig.parameters.items():
                    if param_name == "self":
                        continue

                    # Try to match parameter with dependency
                    if param_name in dependencies:
                        params[param_name] = dependencies[param_name]
                    elif param.annotation != param.empty:
                        # Try to match by type annotation
                        for dep_name, dep_instance in dependencies.items():
                            if isinstance(dep_instance, param.annotation):
                                params[param_name] = dep_instance
                                break

                return factory(**params)
            else:
                return factory()

        elif callable(factory):
            # Handle function factory
            if dependencies:
                # Pass dependencies as arguments
                return factory(**dependencies)
            else:
                return factory()

        else:
            raise TypeError(
                f"Invalid factory type for service '{registration.name}': {type(factory)}"
            )

    def _analyze_dependencies(self, factory: ServiceFactory) -> List[str]:
        """Analyze factory function/class to discover dependencies"""
        if inspect.isclass(factory):
            # Analyze constructor parameters
            try:
                sig = inspect.signature(factory.__init__)
                dependencies = []

                for param_name, param in sig.parameters.items():
                    if param_name == "self":
                        continue

                    # Use parameter name as dependency name by default
                    # In a real implementation, this could be enhanced with
                    # type hints and custom annotations
                    dependencies.append(param_name)

                return dependencies
            except (ValueError, TypeError):
                return []

        elif callable(factory):
            # Analyze function parameters
            try:
                sig = inspect.signature(factory)
                return list(sig.parameters.keys())
            except (ValueError, TypeError):
                return []

        return []

    def create_context(self) -> DIContext:
        """Create a new dependency resolution context"""
        return DIContext(self)

    @contextmanager
    def resolution_context(self):
        """Context manager for automatic DI context lifecycle"""
        context = self.create_context()
        try:
            yield context
        finally:
            context.cleanup()

    def get_service_info(self, name: str) -> Optional[ServiceRegistration]:
        """Get metadata about a registered service"""
        return self._services.get(name)

    def list_services(self) -> List[str]:
        """List all registered service names"""
        services = list(self._services.keys())
        if self._parent:
            services.extend(self._parent.list_services())
        return sorted(set(services))


# Global default container
_default_container = DIContainer()


def get_default_container() -> DIContainer:
    """Get the global default DI container"""
    return _default_container


def set_default_container(container: DIContainer):
    """Set the global default DI container"""
    global _default_container
    _default_container = container


# Convenience functions for the default container
def register_service(
    name: str,
    factory: ServiceFactory,
    scope: str = "singleton",
    dependencies: Optional[List[str]] = None,
) -> int:
    """Register a service with the default container"""
    return _default_container.register(name, factory, scope, dependencies)


def resolve_service(name: str, context: Optional[DIContext] = None) -> Any:
    """Resolve a service from the default container"""
    return _default_container.resolve(name, context)


def create_context() -> DIContext:
    """Create a new DI context with the default container"""
    return _default_container.create_context()


@contextmanager
def resolution_context():
    """Context manager for automatic DI context with default container"""
    with _default_container.resolution_context() as context:
        yield context
