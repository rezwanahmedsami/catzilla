"""
System information collectors for Catzilla startup banner.
Uses psutil for reliable system stats with C extension fallbacks.
"""

import os
import platform
import sys
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, Optional

try:
    import psutil

    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False


@dataclass
class ServerInfo:
    """Container for server information displayed in banner"""

    version: str
    host: str
    port: int
    protocol: str
    route_count: int
    worker_count: int
    prefork_enabled: bool
    prefork_processes: int
    jemalloc_enabled: bool
    cache_info: str
    profiling_enabled: bool
    profiling_interval: int
    pid: int
    memory_usage: str
    start_time: datetime
    mode: str
    debug_enabled: bool
    hot_reload_enabled: bool
    python_version: str
    platform_info: str


class SystemInfoCollector:
    """Collects system and runtime information using Catzilla's C extension"""

    @staticmethod
    def get_memory_usage() -> str:
        """Get current process memory usage using psutil or fallback methods"""
        # Try psutil first - most reliable
        if PSUTIL_AVAILABLE:
            try:
                process = psutil.Process()
                memory_mb = process.memory_info().rss / 1024 / 1024
                return f"{memory_mb:.1f} MB"
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass

        try:
            # Try to use Catzilla's C extension for memory stats
            from catzilla._catzilla import get_memory_stats

            stats = get_memory_stats()
            if stats and "rss" in stats:
                memory_mb = stats["rss"] / 1024 / 1024
                return f"{memory_mb:.1f} MB"
        except (ImportError, AttributeError, KeyError):
            pass

        try:
            # Fallback to reading /proc/self/status on Linux
            if platform.system() == "Linux":
                with open("/proc/self/status", "r") as f:
                    for line in f:
                        if line.startswith("VmRSS:"):
                            kb = int(line.split()[1])
                            mb = kb / 1024
                            return f"{mb:.1f} MB"
        except (FileNotFoundError, ValueError, IndexError):
            pass

        try:
            # Fallback to basic resource module
            import resource

            usage = resource.getrusage(resource.RUSAGE_SELF)
            # On macOS, ru_maxrss is in bytes, on Linux it's in KB
            if platform.system() == "Darwin":
                mb = usage.ru_maxrss / 1024 / 1024
            else:
                mb = usage.ru_maxrss / 1024
            return f"{mb:.1f} MB"
        except (ImportError, AttributeError):
            pass

        return "N/A"

    @staticmethod
    def get_cpu_usage() -> float:
        """Get current CPU usage percentage"""
        if PSUTIL_AVAILABLE:
            try:
                return psutil.cpu_percent(interval=0.1)
            except:
                pass
        return 0.0

    @staticmethod
    def get_python_version() -> str:
        """Get Python version string"""
        return f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"

    @staticmethod
    def get_platform_info() -> str:
        """Get platform information"""
        return f"{platform.system()} {platform.release()}"

    @staticmethod
    def check_jemalloc() -> bool:
        """Check if jemalloc is available and enabled using C extension"""
        try:
            # Try to use Catzilla's C extension
            from catzilla._catzilla import has_jemalloc

            return has_jemalloc()
        except (ImportError, AttributeError):
            try:
                # Fallback method - check if jemalloc symbols exist
                import _catzilla

                return hasattr(_catzilla, "jemalloc_stats") or hasattr(
                    _catzilla, "has_jemalloc"
                )
            except ImportError:
                return False

    @staticmethod
    def get_cache_info() -> str:
        """Get cache system information"""
        # This would be implemented based on actual cache system
        return "In-Memory"

    @staticmethod
    def get_worker_count() -> int:
        """Get recommended worker count based on CPU cores"""
        if PSUTIL_AVAILABLE:
            try:
                return psutil.cpu_count(logical=True) or 1
            except:
                pass
        return os.cpu_count() or 1


class ServerInfoCollector:
    """Collects server configuration and runtime information"""

    def __init__(self, app_instance):
        """Initialize with app instance to access configuration"""
        self.app = app_instance
        self.system_collector = SystemInfoCollector()

    def collect(self, host: str, port: int) -> ServerInfo:
        """Collect all server information"""

        # Determine protocol
        protocol = "https" if port == 443 or self._is_ssl_enabled() else "http"

        # Get route count
        route_count = self._get_route_count()

        # Collect all information
        return ServerInfo(
            version=self._get_version(),
            host=host,
            port=port,
            protocol=protocol,
            route_count=route_count,
            worker_count=self.system_collector.get_worker_count(),
            prefork_enabled=self._is_prefork_enabled(),
            prefork_processes=self._get_prefork_processes(),
            jemalloc_enabled=self._is_jemalloc_enabled(),
            cache_info=self.system_collector.get_cache_info(),
            profiling_enabled=self._is_profiling_enabled(),
            profiling_interval=self._get_profiling_interval(),
            pid=os.getpid(),
            memory_usage=self.system_collector.get_memory_usage(),
            start_time=datetime.now(),
            mode="development" if self.app.debug else "production",
            debug_enabled=self.app.debug,
            hot_reload_enabled=self._is_hot_reload_enabled(),
            python_version=self.system_collector.get_python_version(),
            platform_info=self.system_collector.get_platform_info(),
        )

    def _get_version(self) -> str:
        """Get Catzilla version"""
        try:
            # Try to get version from importlib.metadata (Python 3.8+)
            from importlib.metadata import version

            return version("catzilla")
        except ImportError:
            try:
                # Fallback for Python < 3.8
                import pkg_resources

                return pkg_resources.get_distribution("catzilla").version
            except:
                pass
        except Exception:
            pass

        return "0.1.0"  # Fallback version

    def _get_route_count(self) -> int:
        """Get total number of registered routes"""
        try:
            # Use the app's routes() method
            if hasattr(self.app, "routes"):
                routes = self.app.routes()
                return len(routes) if routes else 0
            # Fallback to router access
            elif hasattr(self.app, "router") and hasattr(self.app.router, "routes"):
                routes = self.app.router.routes()
                return len(routes) if routes else 0
            else:
                return 0
        except:
            return 0

    def _is_ssl_enabled(self) -> bool:
        """Check if SSL is enabled"""
        # This would check your SSL configuration
        return False

    def _is_prefork_enabled(self) -> bool:
        """Check if prefork is enabled"""
        # This would check your prefork configuration
        return False

    def _get_prefork_processes(self) -> int:
        """Get number of prefork processes"""
        # This would get the actual prefork process count
        return 0

    def _is_profiling_enabled(self) -> bool:
        """Check if profiling is enabled"""
        # Check for actual memory profiling configuration
        return getattr(self.app, "memory_profiling", False)

    def _get_profiling_interval(self) -> int:
        """Get profiling interval in seconds"""
        # Get the actual profiling interval from app config
        return getattr(self.app, "memory_stats_interval", 60)

    def _is_jemalloc_enabled(self) -> bool:
        """Check if jemalloc is actually enabled for this app instance"""
        # Check the app's jemalloc configuration
        if hasattr(self.app, "has_jemalloc"):
            return self.app.has_jemalloc
        elif hasattr(self.app, "use_jemalloc"):
            return self.app.use_jemalloc
        else:
            # Fallback to C extension check
            return self.system_collector.check_jemalloc()

    def _is_hot_reload_enabled(self) -> bool:
        """Check if hot reload is enabled"""
        # Catzilla doesn't currently have hot reload - this is a placeholder
        # In the future, this would check for file watching/auto-restart configuration
        return False
