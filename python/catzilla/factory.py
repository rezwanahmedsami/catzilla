"""
Catzilla DI Factory System
Advanced factory patterns for service creation and configuration
"""

import inspect
from abc import ABC, abstractmethod
from dataclasses import dataclass
from functools import partial
from typing import Any, Callable, Dict, List, Optional, Type, TypeVar, Union

from .dependency_injection import DIContainer, DIContext, ServiceFactory

T = TypeVar("T")


class ServiceFactoryProtocol(ABC):
    """Protocol for service factories"""

    @abstractmethod
    def create(
        self, dependencies: Dict[str, Any], context: Optional[DIContext] = None
    ) -> Any:
        """Create a service instance"""
        pass

    @abstractmethod
    def can_create(self, service_name: str) -> bool:
        """Check if this factory can create the specified service"""
        pass


@dataclass
class FactoryConfig:
    """Configuration for factory behavior"""

    lazy_loading: bool = True
    cache_instances: bool = False
    validate_dependencies: bool = True
    timeout_seconds: Optional[float] = None


class ClassFactory(ServiceFactoryProtocol):
    """Factory for creating instances from classes"""

    def __init__(self, target_class: Type[T], config: Optional[FactoryConfig] = None):
        self.target_class = target_class
        self.config = config or FactoryConfig()
        self._constructor_params = self._analyze_constructor()

    def create(
        self, dependencies: Dict[str, Any], context: Optional[DIContext] = None
    ) -> T:
        """Create class instance with dependency injection"""
        # Prepare constructor arguments
        constructor_args = {}

        for param_name, param_info in self._constructor_params.items():
            if param_name in dependencies:
                constructor_args[param_name] = dependencies[param_name]
            elif not param_info.get("has_default", False):
                # Check if dependency can be resolved by type
                param_type = param_info.get("type")
                if param_type:
                    for dep_name, dep_value in dependencies.items():
                        if isinstance(dep_value, param_type):
                            constructor_args[param_name] = dep_value
                            break
                    else:
                        raise ValueError(
                            f"Required dependency '{param_name}' not found for {self.target_class.__name__}"
                        )

        # Validate dependencies if configured
        if self.config.validate_dependencies:
            self._validate_dependencies(constructor_args)

        return self.target_class(**constructor_args)

    def can_create(self, service_name: str) -> bool:
        """Check if this factory can create the service"""
        return service_name == self.target_class.__name__.lower()

    def _analyze_constructor(self) -> Dict[str, Dict[str, Any]]:
        """Analyze constructor parameters"""
        params = {}

        try:
            sig = inspect.signature(self.target_class.__init__)
            for param_name, param in sig.parameters.items():
                if param_name == "self":
                    continue

                params[param_name] = {
                    "type": (
                        param.annotation if param.annotation != param.empty else None
                    ),
                    "has_default": param.default != param.empty,
                    "default": param.default if param.default != param.empty else None,
                }
        except (ValueError, TypeError):
            pass

        return params

    def _validate_dependencies(self, dependencies: Dict[str, Any]):
        """Validate that dependencies match expected types"""
        for param_name, param_info in self._constructor_params.items():
            if param_name in dependencies:
                expected_type = param_info.get("type")
                if expected_type and not isinstance(
                    dependencies[param_name], expected_type
                ):
                    actual_type = type(dependencies[param_name]).__name__
                    raise TypeError(
                        f"Dependency '{param_name}' expected type {expected_type.__name__}, got {actual_type}"
                    )


class FunctionFactory(ServiceFactoryProtocol):
    """Factory for creating instances using functions"""

    def __init__(self, factory_func: Callable, config: Optional[FactoryConfig] = None):
        self.factory_func = factory_func
        self.config = config or FactoryConfig()
        self._function_params = self._analyze_function()

    def create(
        self, dependencies: Dict[str, Any], context: Optional[DIContext] = None
    ) -> Any:
        """Create instance using factory function"""
        # Prepare function arguments
        func_args = {}

        for param_name, param_info in self._function_params.items():
            if param_name in dependencies:
                func_args[param_name] = dependencies[param_name]
            elif not param_info.get("has_default", False):
                raise ValueError(
                    f"Required dependency '{param_name}' not found for factory function"
                )

        # Validate dependencies if configured
        if self.config.validate_dependencies:
            self._validate_dependencies(func_args)

        return self.factory_func(**func_args)

    def can_create(self, service_name: str) -> bool:
        """Check if this factory can create the service"""
        return True  # Function factories are more flexible

    def _analyze_function(self) -> Dict[str, Dict[str, Any]]:
        """Analyze function parameters"""
        params = {}

        try:
            sig = inspect.signature(self.factory_func)
            for param_name, param in sig.parameters.items():
                params[param_name] = {
                    "type": (
                        param.annotation if param.annotation != param.empty else None
                    ),
                    "has_default": param.default != param.empty,
                    "default": param.default if param.default != param.empty else None,
                }
        except (ValueError, TypeError):
            pass

        return params

    def _validate_dependencies(self, dependencies: Dict[str, Any]):
        """Validate that dependencies match expected types"""
        for param_name, param_info in self._function_params.items():
            if param_name in dependencies:
                expected_type = param_info.get("type")
                if expected_type and not isinstance(
                    dependencies[param_name], expected_type
                ):
                    actual_type = type(dependencies[param_name]).__name__
                    raise TypeError(
                        f"Dependency '{param_name}' expected type {expected_type.__name__}, got {actual_type}"
                    )


class ConditionalFactory(ServiceFactoryProtocol):
    """Factory that chooses between multiple factories based on conditions"""

    def __init__(self, conditions: Dict[Callable, ServiceFactoryProtocol]):
        self.conditions = conditions

    def create(
        self, dependencies: Dict[str, Any], context: Optional[DIContext] = None
    ) -> Any:
        """Create instance using conditional logic"""
        for condition_func, factory in self.conditions.items():
            try:
                if condition_func(dependencies, context):
                    return factory.create(dependencies, context)
            except Exception:
                continue  # Try next condition

        raise RuntimeError("No factory condition matched for service creation")

    def can_create(self, service_name: str) -> bool:
        """Check if any of the conditional factories can create the service"""
        return any(
            factory.can_create(service_name) for factory in self.conditions.values()
        )


class SingletonFactory(ServiceFactoryProtocol):
    """Factory wrapper that ensures singleton behavior"""

    def __init__(self, wrapped_factory: ServiceFactoryProtocol):
        self.wrapped_factory = wrapped_factory
        self._instance = None
        self._created = False

    def create(
        self, dependencies: Dict[str, Any], context: Optional[DIContext] = None
    ) -> Any:
        """Create or return cached singleton instance"""
        if not self._created:
            self._instance = self.wrapped_factory.create(dependencies, context)
            self._created = True
        return self._instance

    def can_create(self, service_name: str) -> bool:
        """Check if wrapped factory can create the service"""
        return self.wrapped_factory.can_create(service_name)


class ConfigurableFactory(ServiceFactoryProtocol):
    """Factory that creates services with configuration injection"""

    def __init__(
        self, target_class: Type[T], config_provider: Callable[[], Dict[str, Any]]
    ):
        self.target_class = target_class
        self.config_provider = config_provider
        self.class_factory = ClassFactory(target_class)

    def create(
        self, dependencies: Dict[str, Any], context: Optional[DIContext] = None
    ) -> T:
        """Create instance with configuration injected"""
        # Get configuration
        config = self.config_provider()

        # Merge configuration with dependencies
        merged_deps = {**dependencies, **config}

        return self.class_factory.create(merged_deps, context)

    def can_create(self, service_name: str) -> bool:
        """Check if this factory can create the service"""
        return self.class_factory.can_create(service_name)


class FactoryRegistry:
    """Registry for managing multiple service factories"""

    def __init__(self):
        self._factories: Dict[str, ServiceFactoryProtocol] = {}
        self._default_factory: Optional[ServiceFactoryProtocol] = None

    def register_factory(self, service_name: str, factory: ServiceFactoryProtocol):
        """Register a factory for a specific service"""
        self._factories[service_name] = factory

    def register_class_factory(
        self,
        service_name: str,
        target_class: Type[T],
        config: Optional[FactoryConfig] = None,
    ):
        """Register a class factory"""
        factory = ClassFactory(target_class, config)
        self.register_factory(service_name, factory)

    def register_function_factory(
        self,
        service_name: str,
        factory_func: Callable,
        config: Optional[FactoryConfig] = None,
    ):
        """Register a function factory"""
        factory = FunctionFactory(factory_func, config)
        self.register_factory(service_name, factory)

    def register_singleton_factory(
        self, service_name: str, wrapped_factory: ServiceFactoryProtocol
    ):
        """Register a singleton factory wrapper"""
        factory = SingletonFactory(wrapped_factory)
        self.register_factory(service_name, factory)

    def set_default_factory(self, factory: ServiceFactoryProtocol):
        """Set a default factory for unregistered services"""
        self._default_factory = factory

    def get_factory(self, service_name: str) -> Optional[ServiceFactoryProtocol]:
        """Get a factory for a specific service"""
        if service_name in self._factories:
            return self._factories[service_name]

        # Check if default factory can handle this service
        if self._default_factory and self._default_factory.can_create(service_name):
            return self._default_factory

        return None

    def create_service(
        self,
        service_name: str,
        dependencies: Dict[str, Any],
        context: Optional[DIContext] = None,
    ) -> Any:
        """Create a service instance using the appropriate factory"""
        factory = self.get_factory(service_name)
        if not factory:
            raise ValueError(f"No factory registered for service '{service_name}'")

        return factory.create(dependencies, context)

    def list_factories(self) -> List[str]:
        """List all registered factory service names"""
        return list(self._factories.keys())


# Global factory registry
_global_factory_registry = FactoryRegistry()


def get_factory_registry() -> FactoryRegistry:
    """Get the global factory registry"""
    return _global_factory_registry


# Decorator for registering factories
def factory(
    service_name: str,
    factory_type: str = "class",
    config: Optional[FactoryConfig] = None,
):
    """
    Decorator to register a factory

    Args:
        service_name: Name of the service
        factory_type: Type of factory ('class', 'function', 'singleton')
        config: Factory configuration

    Usage:
        @factory("database", "class")
        class DatabaseService:
            pass

        @factory("cache", "function")
        def create_cache():
            return CacheService()
    """

    def decorator(target):
        registry = get_factory_registry()

        if factory_type == "class":
            registry.register_class_factory(service_name, target, config)
        elif factory_type == "function":
            registry.register_function_factory(service_name, target, config)
        elif factory_type == "singleton":
            base_factory = (
                ClassFactory(target, config)
                if inspect.isclass(target)
                else FunctionFactory(target, config)
            )
            registry.register_singleton_factory(service_name, base_factory)
        else:
            raise ValueError(f"Unknown factory type: {factory_type}")

        return target

    return decorator


# Helper functions for creating common factory patterns
def create_class_factory(target_class: Type[T], **kwargs) -> ClassFactory:
    """Create a class factory with optional configuration"""
    config = FactoryConfig(**kwargs) if kwargs else None
    return ClassFactory(target_class, config)


def create_function_factory(factory_func: Callable, **kwargs) -> FunctionFactory:
    """Create a function factory with optional configuration"""
    config = FactoryConfig(**kwargs) if kwargs else None
    return FunctionFactory(factory_func, config)


def create_conditional_factory(**conditions) -> ConditionalFactory:
    """
    Create a conditional factory

    Usage:
        factory = create_conditional_factory(
            lambda deps, ctx: deps.get('environment') == 'production': ProductionService,
            lambda deps, ctx: True: DevelopmentService  # Default
        )
    """
    return ConditionalFactory(conditions)


def create_configurable_factory(
    target_class: Type[T], config_provider: Callable[[], Dict[str, Any]]
) -> ConfigurableFactory:
    """Create a factory with configuration injection"""
    return ConfigurableFactory(target_class, config_provider)
