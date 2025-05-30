"""
Catzilla Web Framework - The Python Framework That BREAKS THE RULES

Catzilla v0.2.0 Memory Revolution:
- 🚀 30% less memory usage with jemalloc
- ⚡ C-speed request processing
- 🎯 Zero-configuration optimization
- 📈 Gets faster over time
"""

from .app import App, Catzilla  # App is backward compatibility alias
from .response import ResponseBuilder, response
from .routing import Router, RouterGroup
from .types import HTMLResponse, JSONResponse, Request, Response

__version__ = "0.2.0"

__all__ = [
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
]
