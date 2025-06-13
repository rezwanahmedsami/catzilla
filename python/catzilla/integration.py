"""
Catzilla DI Integration with Router and Validation Systems
Seamless integration of dependency injection with existing Catzilla features
"""

import inspect
from functools import wraps
from typing import Any, Callable, Dict, List, Optional, Union, get_type_hints

from .decorators import (
    _clear_current_context,
    _get_current_context,
    _set_current_context,
)
from .dependency_injection import DIContainer, DIContext, get_default_container


class DIMiddleware:
    """Middleware to integrate DI with Catzilla request handling"""

    def __init__(self, container: Optional[DIContainer] = None):
        self.container = container or get_default_container()

    def __call__(self, request_handler: Callable) -> Callable:
        """Apply DI middleware to a request handler"""

        @wraps(request_handler)
        def middleware_wrapper(*args, **kwargs):
            # Create DI context for this request
            with self.container.resolution_context() as context:
                _set_current_context(context)
                try:
                    # Check if handler is already DI-enhanced (skip double injection)
                    if hasattr(request_handler, "_catzilla_container"):
                        # Handler is already enhanced - just call it
                        return request_handler(*args, **kwargs)
                    elif hasattr(request_handler, "_catzilla_dependencies"):
                        return self._handle_with_di(
                            request_handler, context, *args, **kwargs
                        )
                    elif hasattr(request_handler, "_catzilla_auto_inject"):
                        return self._handle_auto_inject(
                            request_handler, context, *args, **kwargs
                        )
                    else:
                        # No DI needed, call handler normally
                        return request_handler(*args, **kwargs)
                finally:
                    _clear_current_context()

        return middleware_wrapper

    def _handle_with_di(self, handler: Callable, context: DIContext, *args, **kwargs):
        """Handle request with explicit dependency injection"""
        dependencies = getattr(handler, "_catzilla_dependencies", [])

        # Resolve dependencies
        resolved_deps = []
        for dep_name in dependencies:
            try:
                resolved_deps.append(self.container.resolve(dep_name, context))
            except Exception as e:
                raise RuntimeError(f"Failed to resolve dependency '{dep_name}': {e}")

        # Call handler with injected dependencies
        return handler(*args, *resolved_deps, **kwargs)

    def _handle_auto_inject(
        self, handler: Callable, context: DIContext, *args, **kwargs
    ):
        """Handle request with automatic dependency injection"""
        injectable_params = getattr(handler, "_catzilla_injectable_params", {})

        # Resolve and inject dependencies
        for param_name, service_name in injectable_params.items():
            if param_name not in kwargs:
                try:
                    kwargs[param_name] = self.container.resolve(service_name, context)
                except Exception as e:
                    raise RuntimeError(f"Failed to auto-inject '{param_name}': {e}")

        return handler(*args, **kwargs)


class DIRouteEnhancer:
    """Enhancer for Catzilla route decorators to support DI"""

    def __init__(self, container: Optional[DIContainer] = None):
        self.container = container or get_default_container()

    def enhance_route(
        self, route_func: Callable, dependencies: Optional[List[str]] = None
    ) -> Callable:
        """
        Enhance a route function with dependency injection support

        Args:
            route_func: Original route handler function
            dependencies: Optional list of dependency names to inject

        Returns:
            Enhanced route function with DI support
        """
        # Get function signature for parameter injection
        sig = inspect.signature(route_func)
        param_dependencies = {}  # param_name -> service_name mapping

        # Auto-discover dependencies if not provided
        if dependencies is None:
            dependencies = self._discover_dependencies(route_func)

        # Build parameter -> service mapping for Depends objects
        for param_name, param in sig.parameters.items():
            if hasattr(param.default, "service_name"):
                # This parameter has a Depends default value
                param_dependencies[param_name] = param.default.service_name
            elif param_name in self.container._services:
                # Try to match parameter name to service name
                param_dependencies[param_name] = param_name

        # Create DI-aware route handler
        @wraps(route_func)
        def di_route_handler(*args, **kwargs):
            # Get current DI context or create one
            context = _get_current_context(self.container)

            # Resolve dependencies and inject them into parameters
            for param_name, service_name in param_dependencies.items():
                if param_name not in kwargs:  # Don't override explicitly passed values
                    try:
                        resolved_service = self.container.resolve(service_name, context)
                        kwargs[param_name] = resolved_service
                    except Exception as e:
                        raise RuntimeError(
                            f"Failed to resolve dependency '{service_name}' for parameter '{param_name}': {e}"
                        )

            return route_func(*args, **kwargs)

        # Store DI metadata
        di_route_handler._catzilla_dependencies = dependencies
        di_route_handler._catzilla_param_dependencies = param_dependencies
        di_route_handler._catzilla_container = self.container
        di_route_handler._original_route_func = route_func

        return di_route_handler

    def _discover_dependencies(self, func: Callable) -> List[str]:
        """Auto-discover dependencies from function signature and type hints"""
        dependencies = []

        try:
            sig = inspect.signature(func)
            type_hints = get_type_hints(func)

            for param_name, param in sig.parameters.items():
                # Skip common route parameters
                if param_name in ["self", "request", "response", "path", "query"]:
                    continue

                # Check if parameter has a type hint that matches a registered service
                if param_name in type_hints:
                    param_type = type_hints[param_name]

                    # Try to find matching service by type or name
                    for service_name, registration in self.container._services.items():
                        if (
                            registration.python_type == param_type
                            or service_name == param_name
                            or service_name == param_name.lower()
                        ):
                            dependencies.append(service_name)
                            break

                # Check for explicit dependency annotation (Depends objects)
                elif hasattr(param.default, "service_name"):
                    # This is a Depends object
                    dependencies.append(param.default.service_name)

        except (ValueError, TypeError):
            pass

        return dependencies


def di_route(
    path: str,
    methods: List[str] = None,
    dependencies: List[str] = None,
    container: Optional[DIContainer] = None,
):
    """
    Route decorator with built-in dependency injection support

    Args:
        path: Route path pattern
        methods: HTTP methods (defaults to ['GET'])
        dependencies: List of service names to inject
        container: DI container to use

    Usage:
        @di_route("/users/{user_id}", dependencies=["database", "cache"])
        def get_user(user_id: int, database: DatabaseService, cache: CacheService):
            pass
    """

    def decorator(func: Callable) -> Callable:
        target_container = container or get_default_container()
        enhancer = DIRouteEnhancer(target_container)

        # Enhance function with DI
        enhanced_func = enhancer.enhance_route(func, dependencies)

        # Apply route decorator (this would integrate with Catzilla's router)
        # For now, just return the enhanced function
        enhanced_func._catzilla_route_path = path
        enhanced_func._catzilla_route_methods = methods or ["GET"]

        return enhanced_func

    return decorator


class ValidationDIIntegration:
    """Integration between DI system and Catzilla's validation system"""

    def __init__(self, container: Optional[DIContainer] = None):
        self.container = container or get_default_container()

    def validate_with_di(
        self, validator_service: str, data: Any, context: Optional[DIContext] = None
    ) -> Any:
        """
        Perform validation using a DI-registered validator service

        Args:
            validator_service: Name of the validator service
            data: Data to validate
            context: Optional DI context

        Returns:
            Validated data
        """
        validator = self.container.resolve(validator_service, context)

        if hasattr(validator, "validate"):
            return validator.validate(data)
        elif callable(validator):
            return validator(data)
        else:
            raise ValueError(f"Validator service '{validator_service}' is not callable")

    def create_validated_handler(
        self, handler: Callable, validators: Dict[str, str]
    ) -> Callable:
        """
        Create a handler with DI-based validation

        Args:
            handler: Original handler function
            validators: Dict mapping parameter names to validator service names

        Returns:
            Handler with validation applied
        """

        @wraps(handler)
        def validated_handler(*args, **kwargs):
            context = _get_current_context(self.container)

            # Apply validators to parameters
            for param_name, validator_service in validators.items():
                if param_name in kwargs:
                    try:
                        kwargs[param_name] = self.validate_with_di(
                            validator_service, kwargs[param_name], context
                        )
                    except Exception as e:
                        raise ValueError(f"Validation failed for '{param_name}': {e}")

            return handler(*args, **kwargs)

        return validated_handler


# Utility functions for integration
def create_di_app(container: Optional[DIContainer] = None):
    """
    Create a Catzilla app instance with DI integration

    Args:
        container: DI container to use (creates new one if None)

    Returns:
        Catzilla app with DI middleware applied
    """
    from catzilla import Catzilla  # Import here to avoid circular dependencies

    target_container = container or DIContainer()
    middleware = DIMiddleware(target_container)

    app = Catzilla()
    app.di_container = target_container
    app.di_middleware = middleware

    # Enhance route decorators
    original_get = app.get
    original_post = app.post
    original_put = app.put
    original_delete = app.delete

    def enhanced_route_decorator(original_decorator):
        def decorator(path: str, **kwargs):
            def route_wrapper(func: Callable) -> Callable:
                # Apply DI enhancement
                enhancer = DIRouteEnhancer(target_container)
                enhanced_func = enhancer.enhance_route(func)

                # Apply original route decorator
                return original_decorator(path, **kwargs)(enhanced_func)

            return route_wrapper

        return decorator

    app.get = enhanced_route_decorator(original_get)
    app.post = enhanced_route_decorator(original_post)
    app.put = enhanced_route_decorator(original_put)
    app.delete = enhanced_route_decorator(original_delete)

    return app


def di_depends(service_name: str, container: Optional[DIContainer] = None):
    """
    Create a dependency resolver for use with FastAPI-style parameter injection

    Args:
        service_name: Name of the service to resolve
        container: DI container to use

    Returns:
        Dependency resolver function
    """

    def resolver():
        target_container = container or get_default_container()
        context = _get_current_context(target_container)
        return target_container.resolve(service_name, context)

    resolver._catzilla_dependency_name = service_name
    resolver._catzilla_container = container

    return resolver


# Export commonly used integration functions
__all__ = [
    "DIMiddleware",
    "DIRouteEnhancer",
    "ValidationDIIntegration",
    "di_route",
    "create_di_app",
    "di_depends",
]
