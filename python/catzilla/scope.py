"""
Catzilla DI Scope Management
Advanced scope handling for different service lifecycles
"""

import threading
import weakref
from contextlib import contextmanager
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set, Union

from .dependency_injection import DIContainer, DIContext


class ScopeType(Enum):
    """Service scope types"""

    SINGLETON = "singleton"
    TRANSIENT = "transient"
    SCOPED = "scoped"
    REQUEST = "request"
    SESSION = "session"
    THREAD = "thread"


@dataclass
class ScopeContext:
    """Context for a specific scope"""

    scope_id: str
    scope_type: ScopeType
    instances: Dict[str, Any] = field(default_factory=dict)
    cleanup_callbacks: Dict[str, Callable] = field(default_factory=dict)
    is_active: bool = True
    creation_time: float = field(default_factory=lambda: __import__("time").time())


class ScopeManager:
    """
    Advanced scope manager for controlling service lifecycles
    """

    def __init__(self):
        self._scopes: Dict[str, ScopeContext] = {}
        self._scope_stack: list = []  # Stack of active scopes
        self._thread_local = threading.local()
        self._lock = threading.RLock()

        # Weak references to track service instances
        self._singleton_instances: Dict[str, Any] = {}
        self._thread_instances: Dict[int, Dict[str, Any]] = {}

    def create_scope(
        self, scope_id: str, scope_type: Union[ScopeType, str]
    ) -> ScopeContext:
        """
        Create a new scope context

        Args:
            scope_id: Unique identifier for the scope
            scope_type: Type of scope to create

        Returns:
            New scope context
        """
        if isinstance(scope_type, str):
            scope_type = ScopeType(scope_type)

        with self._lock:
            if scope_id in self._scopes:
                raise ValueError(f"Scope '{scope_id}' already exists")

            scope_context = ScopeContext(scope_id=scope_id, scope_type=scope_type)

            self._scopes[scope_id] = scope_context
            return scope_context

    def get_scope(self, scope_id: str) -> Optional[ScopeContext]:
        """Get an existing scope context"""
        return self._scopes.get(scope_id)

    def activate_scope(self, scope_id: str):
        """Activate a scope (push to scope stack)"""
        with self._lock:
            if scope_id not in self._scopes:
                raise ValueError(f"Scope '{scope_id}' does not exist")

            # Get thread-local scope stack
            if not hasattr(self._thread_local, "scope_stack"):
                self._thread_local.scope_stack = []

            self._thread_local.scope_stack.append(scope_id)

    def deactivate_scope(self, scope_id: str):
        """Deactivate a scope (remove from scope stack)"""
        with self._lock:
            if hasattr(self._thread_local, "scope_stack"):
                try:
                    self._thread_local.scope_stack.remove(scope_id)
                except ValueError:
                    pass  # Scope not in stack

    def get_current_scope(self) -> Optional[ScopeContext]:
        """Get the currently active scope"""
        if (
            hasattr(self._thread_local, "scope_stack")
            and self._thread_local.scope_stack
        ):
            scope_id = self._thread_local.scope_stack[-1]
            return self._scopes.get(scope_id)
        return None

    def resolve_in_scope(
        self, service_name: str, factory: Callable, scope_type: Union[ScopeType, str]
    ) -> Any:
        """
        Resolve a service instance within the appropriate scope

        Args:
            service_name: Name of the service
            factory: Factory function to create the service
            scope_type: Scope type for the service

        Returns:
            Service instance
        """
        if isinstance(scope_type, str):
            scope_type = ScopeType(scope_type)

        if scope_type == ScopeType.SINGLETON:
            return self._resolve_singleton(service_name, factory)
        elif scope_type == ScopeType.TRANSIENT:
            return self._resolve_transient(service_name, factory)
        elif scope_type == ScopeType.THREAD:
            return self._resolve_thread_scoped(service_name, factory)
        elif scope_type == ScopeType.REQUEST:
            return self._resolve_request_scoped(service_name, factory)
        elif scope_type == ScopeType.SCOPED:
            return self._resolve_scoped(service_name, factory)
        else:
            raise ValueError(f"Unsupported scope type: {scope_type}")

    def _resolve_singleton(self, service_name: str, factory: Callable) -> Any:
        """Resolve a singleton service"""
        with self._lock:
            if service_name not in self._singleton_instances:
                instance = factory()
                self._singleton_instances[service_name] = instance

                # Register cleanup callback if the instance supports it
                if hasattr(instance, "cleanup") or hasattr(instance, "__del__"):
                    weakref.finalize(instance, self._cleanup_singleton, service_name)

            return self._singleton_instances[service_name]

    def _resolve_transient(self, service_name: str, factory: Callable) -> Any:
        """Resolve a transient service (always create new instance)"""
        return factory()

    def _resolve_thread_scoped(self, service_name: str, factory: Callable) -> Any:
        """Resolve a thread-scoped service"""
        thread_id = threading.current_thread().ident

        with self._lock:
            if thread_id not in self._thread_instances:
                self._thread_instances[thread_id] = {}

            thread_services = self._thread_instances[thread_id]

            if service_name not in thread_services:
                instance = factory()
                thread_services[service_name] = instance

                # Register cleanup when thread ends
                threading.current_thread()._catzilla_cleanup_callbacks = getattr(
                    threading.current_thread(), "_catzilla_cleanup_callbacks", []
                )
                threading.current_thread()._catzilla_cleanup_callbacks.append(
                    lambda: self._cleanup_thread_service(thread_id, service_name)
                )

            return thread_services[service_name]

    def _resolve_request_scoped(self, service_name: str, factory: Callable) -> Any:
        """Resolve a request-scoped service"""
        current_scope = self.get_current_scope()

        if not current_scope or current_scope.scope_type != ScopeType.REQUEST:
            # Create implicit request scope
            request_scope_id = (
                f"request_{threading.current_thread().ident}_{id(factory)}"
            )
            current_scope = self.create_scope(request_scope_id, ScopeType.REQUEST)
            self.activate_scope(request_scope_id)

        if service_name not in current_scope.instances:
            instance = factory()
            current_scope.instances[service_name] = instance

            # Register cleanup callback
            if hasattr(instance, "cleanup"):
                current_scope.cleanup_callbacks[service_name] = instance.cleanup

        return current_scope.instances[service_name]

    def _resolve_scoped(self, service_name: str, factory: Callable) -> Any:
        """Resolve a service in the current active scope"""
        current_scope = self.get_current_scope()

        if not current_scope:
            # Fall back to singleton behavior if no active scope
            return self._resolve_singleton(service_name, factory)

        if service_name not in current_scope.instances:
            instance = factory()
            current_scope.instances[service_name] = instance

            # Register cleanup callback
            if hasattr(instance, "cleanup"):
                current_scope.cleanup_callbacks[service_name] = instance.cleanup

        return current_scope.instances[service_name]

    def cleanup_scope(self, scope_id: str):
        """Clean up a specific scope and all its instances"""
        with self._lock:
            if scope_id not in self._scopes:
                return

            scope_context = self._scopes[scope_id]

            # Call cleanup callbacks
            for (
                service_name,
                cleanup_callback,
            ) in scope_context.cleanup_callbacks.items():
                try:
                    cleanup_callback()
                except Exception as e:
                    # Log error but continue cleanup
                    print(f"Error cleaning up service '{service_name}': {e}")

            # Clear instances
            scope_context.instances.clear()
            scope_context.cleanup_callbacks.clear()
            scope_context.is_active = False

            # Remove from active scopes
            self.deactivate_scope(scope_id)

            # Remove scope
            del self._scopes[scope_id]

    def cleanup_all_scopes(self):
        """Clean up all scopes"""
        scope_ids = list(self._scopes.keys())
        for scope_id in scope_ids:
            self.cleanup_scope(scope_id)

    def _cleanup_singleton(self, service_name: str):
        """Cleanup callback for singleton services"""
        with self._lock:
            if service_name in self._singleton_instances:
                del self._singleton_instances[service_name]

    def _cleanup_thread_service(self, thread_id: int, service_name: str):
        """Cleanup callback for thread-scoped services"""
        with self._lock:
            if thread_id in self._thread_instances:
                thread_services = self._thread_instances[thread_id]
                if service_name in thread_services:
                    del thread_services[service_name]

                # Remove thread entry if empty
                if not thread_services:
                    del self._thread_instances[thread_id]

    @contextmanager
    def scope_context(self, scope_id: str, scope_type: Union[ScopeType, str]):
        """
        Context manager for automatic scope lifecycle management

        Usage:
            with scope_manager.scope_context("request_123", ScopeType.REQUEST):
                # Services resolved here will be request-scoped
                service = container.resolve("database")
        """
        # Create and activate scope
        scope_context = self.create_scope(scope_id, scope_type)
        self.activate_scope(scope_id)

        try:
            yield scope_context
        finally:
            # Cleanup scope when exiting context
            self.cleanup_scope(scope_id)


# Global scope manager instance
_global_scope_manager = ScopeManager()


def get_scope_manager() -> ScopeManager:
    """Get the global scope manager instance"""
    return _global_scope_manager


def set_scope_manager(scope_manager: ScopeManager):
    """Set the global scope manager instance"""
    global _global_scope_manager
    _global_scope_manager = scope_manager


# Convenience functions
def create_request_scope(request_id: str) -> ScopeContext:
    """Create a new request scope"""
    return _global_scope_manager.create_scope(request_id, ScopeType.REQUEST)


def create_session_scope(session_id: str) -> ScopeContext:
    """Create a new session scope"""
    return _global_scope_manager.create_scope(session_id, ScopeType.SESSION)


@contextmanager
def request_scope(request_id: str):
    """Context manager for request scope"""
    with _global_scope_manager.scope_context(request_id, ScopeType.REQUEST) as scope:
        yield scope


@contextmanager
def session_scope(session_id: str):
    """Context manager for session scope"""
    with _global_scope_manager.scope_context(session_id, ScopeType.SESSION) as scope:
        yield scope


class ScopedDIContainer(DIContainer):
    """
    DI Container with enhanced scope management
    """

    def __init__(
        self,
        parent: Optional[DIContainer] = None,
        scope_manager: Optional[ScopeManager] = None,
    ):
        super().__init__(parent)
        self.scope_manager = scope_manager or get_scope_manager()

    def resolve(self, name: str, context: Optional[DIContext] = None) -> Any:
        """Enhanced resolve method with scope awareness"""
        registration = self._services.get(name)

        if registration and registration.scope in [scope.value for scope in ScopeType]:
            # Use scope manager for resolution
            def factory():
                return super(ScopedDIContainer, self)._resolve_python(name, context)

            return self.scope_manager.resolve_in_scope(
                name, factory, ScopeType(registration.scope)
            )

        # Fall back to default resolution
        return super().resolve(name, context)


# Enhanced decorator for scoped services
def scoped_service(
    scope_type: Union[ScopeType, str],
    name: Optional[str] = None,
    dependencies: Optional[List[str]] = None,
    container: Optional[DIContainer] = None,
):
    """
    Decorator for registering scoped services

    Args:
        scope_type: Scope type for the service
        name: Service name (defaults to class name)
        dependencies: List of dependencies
        container: DI container to use
    """
    from .decorators import service

    if isinstance(scope_type, ScopeType):
        scope_type = scope_type.value

    return service(
        name=name, scope=scope_type, dependencies=dependencies, container=container
    )
