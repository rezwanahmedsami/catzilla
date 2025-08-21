"""
Catzilla is a revolutionary web framework designed to push the boundaries of Python web development.
"""

from .app import Catzilla

# Backward compatibility alias
App = Catzilla

# Auto-validation system (FastAPI-style with 20x performance)
from .auto_validation import Form, Header, Path, Query, create_auto_validated_handler
from .cache_middleware import (
    ConditionalCacheMiddleware,
    SmartCacheMiddleware,
    create_api_cache_middleware,
    create_page_cache_middleware,
    create_static_cache_middleware,
)
from .decorators import Depends, auto_inject, depends, inject, scoped, service

# Revolutionary Dependency Injection System
from .dependency_injection import (
    DIContainer,
    DIContext,
    create_context,
    get_default_container,
    register_service,
    resolution_context,
    resolve_service,
    set_default_container,
)
from .factory import (
    ClassFactory,
    ConditionalFactory,
    ConfigurableFactory,
    FactoryConfig,
    FactoryRegistry,
    FunctionFactory,
    ServiceFactoryProtocol,
    SingletonFactory,
    create_class_factory,
    create_conditional_factory,
    create_configurable_factory,
    create_function_factory,
    factory,
    get_factory_registry,
)
from .integration import (
    DIMiddleware,
    DIRouteEnhancer,
    ValidationDIIntegration,
    create_di_app,
    di_depends,
    di_route,
)

# Memory management and optimization
from .memory import (
    disable_memory_profiling,
    enable_memory_profiling,
    get_allocator_info,
    get_memory_stats,
    is_jemalloc_available,
    is_jemalloc_enabled,
    memory_usage_mb,
    optimize_memory,
    reset_memory_stats,
)

# Middleware system
from .middleware import (
    DIMiddleware,
    MiddlewareMetrics,
    MiddlewareRequest,
    MiddlewareResponse,
    ZeroAllocMiddleware,
)
from .response import ResponseBuilder, response
from .router import RouterGroup
from .scope import (
    ScopeContext,
    ScopedDIContainer,
    ScopeManager,
    ScopeType,
    create_request_scope,
    create_session_scope,
    get_scope_manager,
    request_scope,
    scoped_service,
    session_scope,
)

# Revolutionary Smart Cache System (Multi-level C-accelerated caching)
# Revolutionary Smart Cache System
from .smart_cache import SmartCache, SmartCacheConfig, cached, get_cache, reset_cache

# Streaming and WebSocket support
from .streaming import StreamingResponse, StreamingWriter, stream_template
from .types import HTMLResponse, JSONResponse, Request, Response

# Revolutionary File Upload System (C-native, 10-100x faster)
from .uploads import CatzillaUploadFile, File, UploadManager, UploadPerformanceMonitor

# Alias for FastAPI compatibility
UploadFile = CatzillaUploadFile

# Ultra-fast validation engine
from .validation import (
    BaseModel,
    Field,
    ValidationError,
    get_performance_stats,
    reset_performance_stats,
)

__version__ = "0.2.0"

__all__ = [
    # Core framework
    "Catzilla",  # New primary class
    "App",  # Backward compatibility
    "Request",
    "Response",
    "JSONResponse",
    "HTMLResponse",
    "response",
    "ResponseBuilder",
    "Router",
    "RouterGroup",
    # Revolutionary Smart Cache System
    "SmartCache",
    "SmartCacheConfig",
    "cached",
    "get_cache",
    # Revolutionary File Upload System (C-native performance)
    "CatzillaUploadFile",
    "File",
    "UploadFile",
    "UploadManager",
    "UploadPerformanceMonitor",
    # Ultra-fast validation engine
    "BaseModel",
    "Field",
    "ValidationError",
    "IntField",
    "StringField",
    "FloatField",
    "BoolField",
    "ListField",
    "OptionalField",
    "get_performance_stats",
    "reset_performance_stats",
    # Memory management
    "get_memory_stats",
    "optimize_memory",
    "reset_memory_stats",
    "enable_memory_profiling",
    "disable_memory_profiling",
    "get_allocator_info",
    "memory_usage_mb",
    "is_jemalloc_available",
    "is_jemalloc_enabled",
    # Middleware system
    "ZeroAllocMiddleware",
    "MiddlewareRequest",
    "MiddlewareResponse",
    "DIMiddleware",
    "MiddlewareMetrics",
    # Auto-validation system (FastAPI-style)
    "Query",
    "Path",
    "Header",
    "Form",
    "create_auto_validated_handler",
    # Revolutionary Dependency Injection
    "DIContainer",
    "DIContext",
    "get_default_container",
    "set_default_container",
    "register_service",
    "resolve_service",
    "create_context",
    "resolution_context",
    # DI Decorators
    "service",
    "inject",
    "depends",
    "Depends",
    "auto_inject",
    "scoped",
    # DI Integration
    "DIMiddleware",
    "DIRouteEnhancer",
    "ValidationDIIntegration",
    "di_route",
    "create_di_app",
    "di_depends",
    # Scope Management
    "ScopeType",
    "ScopeManager",
    "ScopeContext",
    "get_scope_manager",
    "create_request_scope",
    "create_session_scope",
    "request_scope",
    "session_scope",
    "ScopedDIContainer",
    "scoped_service",
    # Revolutionary Smart Cache System
    "SmartCache",
    "SmartCacheConfig",
    "cached",
    "get_cache",
    "reset_cache",
    "SmartCacheMiddleware",
    "ConditionalCacheMiddleware",
    "create_api_cache_middleware",
    "create_static_cache_middleware",
    "create_page_cache_middleware",
    # Factory System
    "ServiceFactoryProtocol",
    "ClassFactory",
    "FunctionFactory",
    "ConditionalFactory",
    "SingletonFactory",
    "ConfigurableFactory",
    "FactoryRegistry",
    "FactoryConfig",
    "get_factory_registry",
    "factory",
    "create_class_factory",
    "create_function_factory",
    "create_conditional_factory",
    "create_configurable_factory",
]
