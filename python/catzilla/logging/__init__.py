"""
Catzilla Logging System (Legacy)

This module is maintained for backward compatibility.
New code should import from catzilla.ui instead.
"""

# Import from the new ui module for backward compatibility
from ..ui import (
    COLORS,
    BannerRenderer,
    ColorFormatter,
    DevLogger,
    ProductionLogger,
    RequestLogEntry,
    ServerInfoCollector,
    SystemInfoCollector,
)

__all__ = [
    "BannerRenderer",
    "ServerInfoCollector",
    "DevLogger",
    "ProductionLogger",
    "RequestLogEntry",
    "ColorFormatter",
    "COLORS",
    "SystemInfoCollector",
]
