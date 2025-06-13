"""
Catzilla Dependency Injection System - Python Bridge
High-performance dependency injection with C backend
"""

import ctypes
import inspect
import json
import os
import re
import threading
from contextlib import contextmanager
from dataclasses import dataclass, field
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
        # Validate scope
        valid_scopes = {"singleton", "transient", "scoped", "request"}
        if scope not in valid_scopes:
            raise ValueError(
                f"Invalid scope '{scope}'. Valid scopes are: {', '.join(valid_scopes)}"
            )

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
        # Import here to avoid circular imports
        from .decorators import Depends

        factory = registration.factory

        if inspect.isclass(factory):
            # Handle class constructor injection
            sig = inspect.signature(factory.__init__)
            params = {}

            for param_name, param in sig.parameters.items():
                if param_name == "self":
                    continue

                # Check if parameter has a Depends default value
                if param.default != inspect.Parameter.empty and isinstance(
                    param.default, Depends
                ):
                    service_name = param.default.service_name
                    if service_name in dependencies:
                        params[param_name] = dependencies[service_name]
                # Try to match parameter with dependency by name
                elif param_name in dependencies:
                    params[param_name] = dependencies[param_name]
                # Try to match by type annotation if parameter has no default
                elif (
                    param.default == inspect.Parameter.empty
                    and param.annotation != param.empty
                ):
                    for dep_name, dep_instance in dependencies.items():
                        if isinstance(dep_instance, param.annotation):
                            params[param_name] = dep_instance
                            break

            return factory(**params)

        elif callable(factory):
            # Handle function factory
            sig = inspect.signature(factory)
            params = {}

            for param_name, param in sig.parameters.items():
                # Check if parameter has a Depends default value
                if param.default != inspect.Parameter.empty and isinstance(
                    param.default, Depends
                ):
                    service_name = param.default.service_name
                    if service_name in dependencies:
                        params[param_name] = dependencies[service_name]
                # Try to match parameter with dependency by name
                elif param_name in dependencies:
                    params[param_name] = dependencies[param_name]

            return factory(**params)

        else:
            raise TypeError(
                f"Invalid factory type for service '{registration.name}': {type(factory)}"
            )

    def _analyze_dependencies(self, factory: ServiceFactory) -> List[str]:
        """Analyze factory function/class to discover dependencies"""
        # Import here to avoid circular imports
        from .decorators import Depends

        if inspect.isclass(factory):
            # Analyze constructor parameters
            try:
                sig = inspect.signature(factory.__init__)
                dependencies = []

                for param_name, param in sig.parameters.items():
                    if param_name == "self":
                        continue

                    # Skip *args and **kwargs parameters
                    if param.kind in (
                        inspect.Parameter.VAR_POSITIONAL,
                        inspect.Parameter.VAR_KEYWORD,
                    ):
                        continue

                    # Check if parameter has a Depends default value
                    if param.default != inspect.Parameter.empty:
                        if isinstance(param.default, Depends):
                            dependencies.append(param.default.service_name)
                        else:
                            # Parameter has default value, it's optional
                            continue
                    else:
                        # Use parameter name as dependency name by default
                        dependencies.append(param_name)

                return dependencies
            except (ValueError, TypeError):
                return []

        elif callable(factory):
            # Analyze function parameters
            try:
                sig = inspect.signature(factory)
                dependencies = []

                for param_name, param in sig.parameters.items():
                    # Skip *args and **kwargs parameters
                    if param.kind in (
                        inspect.Parameter.VAR_POSITIONAL,
                        inspect.Parameter.VAR_KEYWORD,
                    ):
                        continue

                    # Check if parameter has a Depends default value
                    if param.default != inspect.Parameter.empty:
                        if isinstance(param.default, Depends):
                            dependencies.append(param.default.service_name)
                        else:
                            # Parameter has default value, it's optional
                            continue
                    else:
                        # Use parameter name as dependency name by default
                        dependencies.append(param_name)

                return dependencies
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


# ============================================================================
# PHASE 5: PRODUCTION FEATURES - PYTHON BRIDGE
# ============================================================================


@dataclass
class ContainerConfig:
    """Configuration for hierarchical containers"""

    name: str = ""
    inherit_services: bool = True
    override_parent_services: bool = False
    isolation_level: int = 0  # 0=full sharing, 1=scoped isolation, 2=full isolation
    allowed_service_patterns: Optional[List[str]] = None
    denied_service_patterns: Optional[List[str]] = None


@dataclass
class FactoryConfig:
    """Advanced factory configuration"""

    factory_type: str = "simple"  # simple, builder, conditional, proxy, async
    description: str = ""
    builder_func: Optional[Callable] = None
    condition_func: Optional[Callable[[], bool]] = None
    alt_factory: Optional[Callable] = None
    destructor_func: Optional[Callable] = None
    auto_cleanup: bool = True


@dataclass
class ServiceConfig:
    """Configuration-based service registration"""

    service_name: str
    service_type: str
    scope: str = "singleton"
    factory_type: str = "simple"
    factory_description: str = ""
    dependencies: List[str] = field(default_factory=list)
    config_params: Dict[str, str] = field(default_factory=dict)
    enabled: bool = True
    priority: int = 0
    tags: List[str] = field(default_factory=list)


@dataclass
class ServiceInfo:
    """Service introspection information"""

    service_id: int
    service_name: str
    service_type: str
    scope: str
    dependencies: List[str] = field(default_factory=list)
    creation_count: int = 0
    last_access_time: int = 0
    total_resolution_time_ns: int = 0
    average_resolution_time_ns: int = 0
    instance_memory_size: int = 0
    metadata_memory_size: int = 0
    is_healthy: bool = True
    last_error: str = ""
    error_count: int = 0


@dataclass
class ContainerInfo:
    """Container introspection information"""

    container_id: int
    container_name: str
    parent_container_id: int = 0
    child_container_ids: List[int] = field(default_factory=list)
    services: List[ServiceInfo] = field(default_factory=list)
    total_memory_allocated: int = 0
    total_memory_used: int = 0
    memory_efficiency: float = 0.0
    is_healthy: bool = True
    health_issues: List[str] = field(default_factory=list)


class AdvancedDIContainer(DIContainer):
    """Extended DI container with Phase 5 production features"""

    def __init__(
        self,
        parent: Optional["AdvancedDIContainer"] = None,
        config: Optional[ContainerConfig] = None,
    ):
        super().__init__(parent)
        self._config = config or ContainerConfig()
        self._child_containers: List["AdvancedDIContainer"] = []
        self._debug_mode = False
        self._debug_level = 0

        if parent:
            parent._child_containers.append(self)

    # Hierarchical Container Management
    # ================================

    def create_child_container(
        self, config: Optional[ContainerConfig] = None
    ) -> "AdvancedDIContainer":
        """Create a child container with hierarchical configuration"""
        return AdvancedDIContainer(parent=self, config=config)

    def get_child_containers(self) -> List["AdvancedDIContainer"]:
        """Get list of child containers"""
        return self._child_containers.copy()

    def configure(self, config: ContainerConfig) -> None:
        """Update container configuration"""
        self._config = config

    def is_service_access_allowed(self, service_name: str) -> bool:
        """Check if service access is allowed by container policy"""
        if self._config.denied_service_patterns:
            for pattern in self._config.denied_service_patterns:
                if self._match_pattern(service_name, pattern):
                    return False

        if self._config.allowed_service_patterns:
            for pattern in self._config.allowed_service_patterns:
                if self._match_pattern(service_name, pattern):
                    return True
            return False

        return True

    def _match_pattern(self, service_name: str, pattern: str) -> bool:
        """Simple pattern matching (supports * wildcards)"""
        regex_pattern = pattern.replace("*", ".*")
        return bool(re.match(f"^{regex_pattern}$", service_name))

    # Advanced Factory Pattern Support
    # ================================

    def register_advanced_factory(
        self,
        name: str,
        factory_config: FactoryConfig,
        dependencies: Optional[List[str]] = None,
        factory_func: Optional[Callable] = None,
    ) -> int:
        """Register an advanced factory with complex configuration"""
        # Store factory configuration for later use
        if not hasattr(self, "_factory_configs"):
            self._factory_configs = {}
        self._factory_configs[name] = factory_config

        # Use provided factory function or the builder function from config
        factory = (
            factory_func
            if factory_func
            else (
                factory_config.builder_func
                if factory_config.builder_func
                else lambda: None
            )
        )
        return self.register(name, factory, "singleton", dependencies)

    def register_builder_factory(
        self,
        name: str,
        builder_func: Callable,
        factory_func: Callable,
        builder_config: Any = None,
        dependencies: Optional[List[str]] = None,
    ) -> int:
        """Register a builder pattern factory"""

        def builder_wrapper(*args, **kwargs):
            # First call the builder to get the config/dependencies
            built_args = builder_func()
            # Then call the factory with the built arguments
            if args:
                return factory_func(built_args, *args, **kwargs)
            else:
                return factory_func(built_args, **kwargs)

        config = FactoryConfig(
            factory_type="builder",
            builder_func=builder_func,
            description=f"Builder factory for {name}",
        )
        return self.register_advanced_factory(
            name, config, dependencies or [], builder_wrapper
        )

    def register_conditional_factory(
        self,
        name: str,
        condition_func: Callable[[], bool],
        primary_factory: Callable,
        fallback_factory: Callable,
        dependencies: Optional[List[str]] = None,
    ) -> int:
        """Register a conditional factory"""

        def conditional_wrapper(*args, **kwargs):
            if condition_func():
                return primary_factory(*args, **kwargs)
            else:
                return fallback_factory(*args, **kwargs)

        config = FactoryConfig(
            factory_type="conditional",
            condition_func=condition_func,
            alt_factory=fallback_factory,
            description=f"Conditional factory for {name}",
        )

        # Store factory configuration
        if not hasattr(self, "_factory_configs"):
            self._factory_configs = {}
        self._factory_configs[name] = config

        # Register the conditional wrapper
        return self.register(name, conditional_wrapper, "singleton", dependencies or [])

    # Configuration-Based Service Registration
    # ========================================

    def register_services_from_config(self, configs: List[ServiceConfig]) -> int:
        """Register services from configuration list"""
        success_count = 0

        for config in configs:
            if not config.enabled:
                continue

            try:
                # For now, just register with basic information
                # In full implementation, would create proper factories
                result = self.register(
                    config.service_name,
                    lambda: f"Service_{config.service_name}",  # Placeholder factory
                    config.scope,
                    config.dependencies,
                )
                if result == 0:
                    success_count += 1
            except Exception as e:
                print(f"Failed to register service '{config.service_name}': {e}")

        return success_count

    def load_config_from_json(self, json_config: str) -> int:
        """Load service configuration from JSON string"""
        try:
            data = json.loads(json_config)

            if not isinstance(data, dict) or "services" not in data:
                raise ValueError(
                    "Invalid JSON format: expected object with 'services' array"
                )

            configs = []
            for service_data in data["services"]:
                config = ServiceConfig(
                    service_name=service_data["service_name"],
                    service_type=service_data.get("service_type", "Unknown"),
                    scope=service_data.get("scope", "singleton"),
                    factory_type=service_data.get("factory_type", "simple"),
                    factory_description=service_data.get("factory_description", ""),
                    dependencies=service_data.get("dependencies", []),
                    config_params=service_data.get("config_params", {}),
                    enabled=service_data.get("enabled", True),
                    priority=service_data.get("priority", 0),
                    tags=service_data.get("tags", []),
                )
                configs.append(config)

            return self.register_services_from_config(configs)

        except (json.JSONDecodeError, KeyError, ValueError) as e:
            print(f"Failed to load config from JSON: {e}")
            return -1

    def load_config_from_file(self, config_file_path: str) -> int:
        """Load service configuration from file"""
        try:
            with open(config_file_path, "r") as f:
                json_config = f.read()
            return self.load_config_from_json(json_config)
        except IOError as e:
            print(f"Failed to read config file '{config_file_path}': {e}")
            return -1

    def export_config_to_json(self) -> str:
        """Export container configuration to JSON"""
        config_data = {
            "container_id": id(self),
            "container_name": self._config.name or f"Container_{id(self)}",
            "service_count": len(self._services),
            "services": [],
        }

        for name, registration in self._services.items():
            service_data = {
                "service_name": name,
                "service_type": (
                    registration.python_type.__name__
                    if registration.python_type
                    else "Unknown"
                ),
                "scope": registration.scope,
                "dependencies": registration.dependencies,
                "enabled": True,
            }
            config_data["services"].append(service_data)

        return json.dumps(config_data, indent=2)

    # Debugging and Introspection Tools
    # =================================

    def get_container_info(self) -> ContainerInfo:
        """Get comprehensive container information"""
        services = []
        for name, registration in self._services.items():
            service_info = ServiceInfo(
                service_id=id(registration),
                service_name=name,
                service_type=(
                    registration.python_type.__name__
                    if registration.python_type
                    else "Unknown"
                ),
                scope=registration.scope,
                dependencies=registration.dependencies,
                is_healthy=True,
            )
            services.append(service_info)

        return ContainerInfo(
            container_id=id(self),
            container_name=self._config.name or f"Container_{id(self)}",
            parent_container_id=id(self._parent) if self._parent else 0,
            child_container_ids=[id(child) for child in self._child_containers],
            services=services,
            is_healthy=True,
        )

    def get_service_info(self, service_name: str) -> Optional[ServiceInfo]:
        """Get detailed service information"""
        if service_name not in self._services:
            return None

        registration = self._services[service_name]
        return ServiceInfo(
            service_id=id(registration),
            service_name=service_name,
            service_type=(
                registration.python_type.__name__
                if registration.python_type
                else "Unknown"
            ),
            scope=registration.scope,
            dependencies=registration.dependencies,
            is_healthy=True,
        )

    def get_dependency_graph(self, format: str = "text") -> str:
        """Get dependency graph as string representation"""
        if format == "dot":
            lines = ["digraph DependencyGraph {"]
            for name, registration in self._services.items():
                lines.append(f'  "{name}";')
                for dep in registration.dependencies:
                    lines.append(f'  "{name}" -> "{dep}";')
            lines.append("}")
            return "\n".join(lines)

        elif format == "json":
            graph_data = {"container_id": id(self), "services": []}
            for name, registration in self._services.items():
                service_data = {"name": name, "dependencies": registration.dependencies}
                graph_data["services"].append(service_data)
            return json.dumps(graph_data, indent=2)

        else:  # text format
            lines = [f"Dependency Graph for Container {id(self)}:"]
            for name, registration in self._services.items():
                if registration.dependencies:
                    deps = ", ".join(registration.dependencies)
                    lines.append(f"  {name} -> [{deps}]")
                else:
                    lines.append(f"  {name} (no dependencies)")
            return "\n".join(lines)

    def analyze_dependencies(self) -> List[str]:
        """Analyze service dependencies for issues"""
        issues = []

        # Check for circular dependencies
        for name, registration in self._services.items():
            if name in registration.dependencies:
                issues.append(f"Service '{name}' depends on itself")

        # Check for missing dependencies
        for name, registration in self._services.items():
            for dep in registration.dependencies:
                if dep not in self._services and (
                    not self._parent or not self._parent.has_service(dep)
                ):
                    issues.append(
                        f"Service '{name}' depends on missing service '{dep}'"
                    )

        return issues

    def generate_performance_report(self) -> str:
        """Generate performance report"""
        lines = ["=== DI Container Performance Report ==="]
        lines.append(f"Container ID: {id(self)}")
        lines.append(f"Container Name: {self._config.name or 'Unnamed'}")
        lines.append(f"Total Services: {len(self._services)}")
        lines.append(f"Child Containers: {len(self._child_containers)}")

        if self._parent:
            lines.append(f"Parent Container: {id(self._parent)}")

        lines.append("")
        lines.append("Services:")
        for name, registration in self._services.items():
            lines.append(f"  - {name} ({registration.scope})")
            if registration.dependencies:
                lines.append(
                    f"    Dependencies: {', '.join(registration.dependencies)}"
                )

        return "\n".join(lines)

    def set_debug_mode(self, enabled: bool, debug_level: int = 1):
        """Enable/disable debug mode for container"""
        self._debug_mode = enabled
        self._debug_level = debug_level

        if enabled:
            print(f"Debug mode enabled for container {id(self)} (level {debug_level})")

    def get_resolution_trace(self, service_name: str) -> str:
        """Get service resolution trace"""
        if service_name not in self._services:
            return f"Service '{service_name}' not found"

        registration = self._services[service_name]
        lines = [f"Resolution trace for '{service_name}':"]
        lines.append(f"1. Service found in container {id(self)}")
        lines.append(
            f"2. Service type: {registration.python_type.__name__ if registration.python_type else 'Unknown'}"
        )
        lines.append(f"3. Service scope: {registration.scope}")
        lines.append(f"4. Dependencies: {registration.dependencies}")
        lines.append("5. Resolving dependencies...")

        for i, dep in enumerate(registration.dependencies, 6):
            lines.append(f"{i}. Resolving dependency '{dep}'")

        lines.append(f"{len(registration.dependencies) + 6}. Creating service instance")
        lines.append(f"{len(registration.dependencies) + 7}. Resolution complete")

        return "\n".join(lines)

    # Health Monitoring and Diagnostics
    # =================================

    def health_check(self, check_level: int = 0) -> int:
        """Perform health check on container"""
        health_score = 100

        # Basic checks
        if len(self._services) == 0:
            health_score -= 20

        # Check for dependency issues
        issues = self.analyze_dependencies()
        health_score -= len(issues) * 10

        # Detailed checks
        if check_level >= 1:
            # Check for unused services (services with no dependents)
            dependents = set()
            for registration in self._services.values():
                dependents.update(registration.dependencies)

            unused_count = len(self._services) - len(dependents)
            if unused_count > len(self._services) * 0.5:  # More than 50% unused
                health_score -= 15

        return max(0, health_score)

    def get_health_issues(self) -> List[str]:
        """Get health issues"""
        issues = []

        if len(self._services) == 0:
            issues.append("No services registered")

        issues.extend(self.analyze_dependencies())

        return issues


# Factory functions for Phase 5 features
# =======================================


def create_production_container(
    name: str = "", parent: Optional[AdvancedDIContainer] = None
) -> AdvancedDIContainer:
    """Create a production-ready DI container with advanced features"""
    config = ContainerConfig(name=name)
    return AdvancedDIContainer(parent=parent, config=config)


def load_container_from_config_file(
    config_file_path: str, parent: Optional[AdvancedDIContainer] = None
) -> AdvancedDIContainer:
    """Load a DI container from configuration file"""
    container = create_production_container(parent=parent)

    if container.load_config_from_file(config_file_path) == -1:
        raise ValueError(f"Failed to load configuration from {config_file_path}")

    return container


# Initialize the default container now that all classes are defined
_default_container = create_production_container("DefaultContainer")


# Enhanced convenience functions
def get_container_info() -> ContainerInfo:
    """Get information about the default container"""
    return _default_container.get_container_info()


def analyze_dependencies() -> List[str]:
    """Analyze dependencies in the default container"""
    return _default_container.analyze_dependencies()


def health_check(check_level: int = 0) -> int:
    """Perform health check on the default container"""
    return _default_container.health_check(check_level)


def export_config() -> str:
    """Export default container configuration to JSON"""
    return _default_container.export_config_to_json()


def get_default_container():
    """Get the default DI container"""
    return _default_container


def set_default_container(container) -> None:
    """Set the default DI container"""
    global _default_container
    _default_container = container


def clear_default_container() -> None:
    """Clear the default DI container (useful for testing)"""
    global _default_container
    _default_container = DIContainer()


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
