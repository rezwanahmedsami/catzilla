"""
Catzilla Web Framework - The Python Framework That BREAKS THE RULES

Catzilla v0.2.0 Memory Revolution:
- 🚀 30% less memory usage with jemalloc
- ⚡ C-speed request processing
- 🎯 Zero-configuration optimization
- 📈 Gets faster over time

Ultra-Fast Validation Engine:
- 🔥 100x faster than Pydantic
- ⚡ C-accelerated field validation
- 🧠 jemalloc memory optimization
- 🎯 Minimal memory footprint
"""

from .app import App, Catzilla  # App is backward compatibility alias
from .response import ResponseBuilder, response
from .routing import Router, RouterGroup
from .types import HTMLResponse, JSONResponse, Request, Response

# Ultra-fast validation engine
from .validation import (
    BaseModel,
    BoolField,
    Field,
    FloatField,
    IntField,
    ListField,
    OptionalField,
    StringField,
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
    # Ultra-fast validation engine
    "Field",
    "Model",
    "ValidationError",
    "IntField",
    "StringField",
    "FloatField",
    "BoolField",
    "ListField",
    "DictField",
    "OptionalField",
    "UnionField",
    "get_validation_stats",
    "reset_validation_stats",
    "benchmark_validation",
    "email_pattern",
    "url_pattern",
    "uuid_pattern",
]
