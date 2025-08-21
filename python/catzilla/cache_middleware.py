"""
Catzilla Smart Cache Middleware
Automatic response caching with intelligent cache key generation
"""

import json
import time
from typing import Any, Callable, Dict, List, Optional, Set
from urllib.parse import parse_qs

from .smart_cache import SmartCache, SmartCacheConfig, get_cache
from .types import Request, Response


class SmartCacheMiddleware:
    """
    Intelligent response caching middleware that automatically caches responses
    based on configurable rules and generates smart cache keys.
    """

    def __init__(
        self,
        config: Optional[SmartCacheConfig] = None,
        cache_instance: Optional[SmartCache] = None,
        default_ttl: int = 3600,
        cache_methods: Optional[Set[str]] = None,
        cache_status_codes: Optional[Set[int]] = None,
        ignore_query_params: Optional[Set[str]] = None,
        cache_headers: Optional[Set[str]] = None,
        cache_private: bool = False,
        cache_authenticated: bool = False,
        exclude_paths: Optional[List[str]] = None,
        include_paths: Optional[List[str]] = None,
        cache_vary_headers: Optional[Set[str]] = None,
        custom_key_generator: Optional[Callable] = None,
    ):
        """
        Initialize Smart Cache Middleware

        Args:
            config: Cache configuration (if cache_instance not provided)
            cache_instance: Existing cache instance to use
            default_ttl: Default cache TTL in seconds
            cache_methods: HTTP methods to cache (default: GET, HEAD)
            cache_status_codes: Status codes to cache (default: 200, 301, 302, 404)
            ignore_query_params: Query parameters to ignore in cache key
            cache_headers: Headers to include in cache key
            cache_private: Whether to cache responses with private cache control
            cache_authenticated: Whether to cache authenticated requests
            exclude_paths: Paths to exclude from caching
            include_paths: Paths to include in caching (if set, only these are cached)
            cache_vary_headers: Headers that should vary the cache
            custom_key_generator: Custom function to generate cache keys
        """
        super().__init__()

        # Cache setup
        self.cache = cache_instance or get_cache(config)
        self.default_ttl = default_ttl

        # Caching rules
        self.cache_methods = cache_methods or {"GET", "HEAD"}
        self.cache_status_codes = cache_status_codes or {200, 301, 302, 404}
        self.ignore_query_params = ignore_query_params or {
            "_",
            "timestamp",
            "cache_buster",
        }
        self.cache_headers = cache_headers or {
            "accept",
            "accept-encoding",
            "accept-language",
        }
        self.cache_vary_headers = cache_vary_headers or set()

        # Behavior flags
        self.cache_private = cache_private
        self.cache_authenticated = cache_authenticated

        # Path filters
        self.exclude_paths = exclude_paths or []
        self.include_paths = include_paths

        # Custom key generator
        self.custom_key_generator = custom_key_generator

        # Statistics
        self.stats = {
            "cache_hits": 0,
            "cache_misses": 0,
            "cache_sets": 0,
            "cache_skips": 0,
            "total_requests": 0,
        }

    def _should_cache_request(self, request: Request) -> bool:
        """Determine if request should be cached"""
        # Check HTTP method
        if request.method not in self.cache_methods:
            return False

        # Check path filters
        path = request.url.path

        if self.include_paths:
            # If include_paths is set, only cache paths in the list
            if not any(
                path.startswith(include_path) for include_path in self.include_paths
            ):
                return False

        if self.exclude_paths:
            # Skip paths in exclude list
            if any(
                path.startswith(exclude_path) for exclude_path in self.exclude_paths
            ):
                return False

        # Check authentication
        if not self.cache_authenticated:
            auth_header = request.headers.get("authorization")
            if auth_header:
                return False

        # Check for no-cache directives
        cache_control = request.headers.get("cache-control", "").lower()
        if "no-cache" in cache_control or "no-store" in cache_control:
            return False

        return True

    def _should_cache_response(self, response: Response) -> bool:
        """Determine if response should be cached"""
        # Check status code
        if response.status_code not in self.cache_status_codes:
            return False

        # Check cache control headers
        cache_control = response.headers.get("cache-control", "").lower()

        if "no-cache" in cache_control or "no-store" in cache_control:
            return False

        if not self.cache_private and "private" in cache_control:
            return False

        # Check for vary: * (uncacheable)
        vary_header = response.headers.get("vary", "").lower()
        if vary_header == "*":
            return False

        return True

    def _normalize_query_string(self, query_string: str) -> str:
        """Normalize query string for cache key"""
        if not query_string:
            return ""

        # Parse query parameters
        params = parse_qs(query_string, keep_blank_values=True)

        # Remove ignored parameters
        for ignore_param in self.ignore_query_params:
            params.pop(ignore_param, None)

        # Sort parameters for consistent key generation
        normalized_params = []
        for key in sorted(params.keys()):
            for value in sorted(params[key]):
                normalized_params.append(f"{key}={value}")

        return "&".join(normalized_params)

    def _get_cache_headers(self, request: Request) -> Dict[str, str]:
        """Extract relevant headers for cache key"""
        headers = {}

        for header_name in self.cache_headers:
            header_value = request.headers.get(header_name)
            if header_value:
                headers[header_name] = header_value

        for header_name in self.cache_vary_headers:
            header_value = request.headers.get(header_name)
            if header_value:
                headers[header_name] = header_value

        return headers

    def _generate_cache_key(self, request: Request) -> str:
        """Generate cache key for request"""
        if self.custom_key_generator:
            return self.custom_key_generator(request)

        # Normalize query string
        normalized_query = self._normalize_query_string(request.url.query or "")

        # Get relevant headers
        cache_headers = self._get_cache_headers(request)

        # Generate key using cache system
        return self.cache.generate_key(
            method=request.method,
            path=request.url.path,
            query_string=normalized_query if normalized_query else None,
            headers=cache_headers,
        )

    def _get_cache_ttl(self, response: Response) -> int:
        """Extract TTL from response headers or use default"""
        cache_control = response.headers.get("cache-control", "")

        # Look for max-age directive
        for directive in cache_control.split(","):
            directive = directive.strip().lower()
            if directive.startswith("max-age="):
                try:
                    return int(directive.split("=")[1])
                except (ValueError, IndexError):
                    pass

        # Look for expires header
        expires = response.headers.get("expires")
        if expires:
            try:
                from email.utils import parsedate_to_datetime

                expires_time = parsedate_to_datetime(expires)
                ttl = int((expires_time.timestamp() - time.time()))
                if ttl > 0:
                    return ttl
            except (ValueError, TypeError):
                pass

        return self.default_ttl

    def _serialize_response(self, response: Response) -> bytes:
        """Serialize response for caching"""
        response_data = {
            "status_code": response.status_code,
            "headers": dict(response.headers),
            "body": (
                response.body.decode("utf-8")
                if isinstance(response.body, bytes)
                else response.body
            ),
            "media_type": getattr(response, "media_type", None),
            "cached_at": time.time(),
        }

        return json.dumps(response_data).encode("utf-8")

    def _deserialize_response(self, data: bytes) -> Response:
        """Deserialize cached response"""
        response_data = json.loads(data.decode("utf-8"))

        # Create response object
        response = Response(
            content=response_data["body"],
            status_code=response_data["status_code"],
            headers=response_data["headers"],
            media_type=response_data.get("media_type"),
        )

        # Add cache headers
        response.headers["x-cache"] = "HIT"
        response.headers["x-cache-time"] = str(
            int(time.time() - response_data["cached_at"])
        )

        return response

    async def process_request(self, request: Request) -> Optional[Response]:
        """Process incoming request - check cache for existing response"""
        self.stats["total_requests"] += 1

        # Check if we should cache this request
        if not self._should_cache_request(request):
            self.stats["cache_skips"] += 1
            return None

        # Generate cache key
        cache_key = self._generate_cache_key(request)

        # Try to get cached response
        cached_data, found = self.cache.get(cache_key)

        if found:
            self.stats["cache_hits"] += 1
            try:
                # Deserialize and return cached response
                response = self._deserialize_response(cached_data)
                return response
            except Exception:
                # Cache corruption, continue with normal request
                self.cache.delete(cache_key)

        self.stats["cache_misses"] += 1

        # Store cache key in request for use in process_response
        request.state.cache_key = cache_key

        return None

    async def process_response(self, request: Request, response: Response) -> Response:
        """Process response - cache if appropriate"""
        # Check if we have a cache key (request was cacheable)
        cache_key = getattr(request.state, "cache_key", None)
        if not cache_key:
            return response

        # Check if response should be cached
        if not self._should_cache_response(response):
            return response

        try:
            # Get TTL from response headers
            ttl = self._get_cache_ttl(response)

            # Serialize and cache response
            cached_data = self._serialize_response(response)
            success = self.cache.set(cache_key, cached_data, ttl)

            if success:
                self.stats["cache_sets"] += 1
                # Add cache headers
                response.headers["x-cache"] = "MISS"
                response.headers["x-cache-ttl"] = str(ttl)

        except Exception as e:
            # Don't fail the request if caching fails
            print(f"Cache error: {e}")

        return response

    def get_stats(self) -> Dict[str, Any]:
        """Get middleware statistics"""
        cache_stats = self.cache.get_stats()

        hit_ratio = 0.0
        if self.stats["total_requests"] > 0:
            hit_ratio = self.stats["cache_hits"] / self.stats["total_requests"]

        return {
            "middleware_stats": self.stats.copy(),
            "cache_stats": {
                "hits": cache_stats.hits,
                "misses": cache_stats.misses,
                "evictions": cache_stats.evictions,
                "memory_usage": cache_stats.memory_usage,
                "size": cache_stats.size,
                "capacity": cache_stats.capacity,
                "hit_ratio": cache_stats.hit_ratio,
                "tier_stats": cache_stats.tier_stats,
            },
            "overall_hit_ratio": hit_ratio,
            "cache_health": self.cache.health_check(),
        }

    def clear_cache(self):
        """Clear all cached responses"""
        self.cache.clear()
        self.stats = {key: 0 for key in self.stats}

    def warm_cache(self, urls: List[str], client=None):
        """Pre-warm cache with specific URLs"""
        # This would require making actual requests to warm the cache
        # Implementation depends on having access to test client
        pass


class ConditionalCacheMiddleware(SmartCacheMiddleware):
    """
    Cache middleware with conditional caching based on custom rules
    """

    def __init__(self, cache_rules: Dict[str, Dict[str, Any]], **kwargs):
        """
        Initialize with cache rules

        Args:
            cache_rules: Dict mapping path patterns to cache configurations
                Example:
                {
                    "/api/users/*": {"ttl": 300, "methods": ["GET"]},
                    "/api/posts/*": {"ttl": 600, "vary_headers": ["accept-language"]},
                    "/static/*": {"ttl": 86400, "status_codes": [200]},
                }
        """
        super().__init__(**kwargs)
        self.cache_rules = cache_rules

    def _get_rule_for_path(self, path: str) -> Optional[Dict[str, Any]]:
        """Get cache rule for specific path"""
        # Check for exact match first
        if path in self.cache_rules:
            return self.cache_rules[path]

        # Check for pattern matches
        for pattern, rule in self.cache_rules.items():
            if pattern.endswith("*"):
                prefix = pattern[:-1]
                if path.startswith(prefix):
                    return rule
            elif "*" in pattern:
                # Simple glob matching (could be enhanced)
                import fnmatch

                if fnmatch.fnmatch(path, pattern):
                    return rule

        return None

    def _should_cache_request(self, request: Request) -> bool:
        """Override to use path-specific rules"""
        # Get rule for this path
        rule = self._get_rule_for_path(request.url.path)
        if not rule:
            return super()._should_cache_request(request)

        # Check method against rule
        allowed_methods = rule.get("methods", self.cache_methods)
        if request.method not in allowed_methods:
            return False

        # Apply base checks
        return super()._should_cache_request(request)

    def _should_cache_response(self, response: Response) -> bool:
        """Override to use path-specific rules"""
        # Get rule for this path (stored in request state)
        request = getattr(response, "_request", None)
        if not request:
            return super()._should_cache_response(response)

        rule = self._get_rule_for_path(request.url.path)
        if not rule:
            return super()._should_cache_response(response)

        # Check status codes against rule
        allowed_status_codes = rule.get("status_codes", self.cache_status_codes)
        if response.status_code not in allowed_status_codes:
            return False

        # Apply base checks
        return super()._should_cache_response(response)

    def _get_cache_ttl(self, response: Response) -> int:
        """Override to use path-specific TTL"""
        request = getattr(response, "_request", None)
        if not request:
            return super()._get_cache_ttl(response)

        rule = self._get_rule_for_path(request.url.path)
        if rule and "ttl" in rule:
            return rule["ttl"]

        return super()._get_cache_ttl(response)


# Convenience functions for common cache configurations


def create_api_cache_middleware(ttl: int = 300, **kwargs) -> SmartCacheMiddleware:
    """Create cache middleware optimized for API responses"""
    return SmartCacheMiddleware(
        default_ttl=ttl,
        cache_methods={"GET", "HEAD"},
        cache_status_codes={200, 404},
        cache_headers={"accept", "accept-encoding"},
        cache_authenticated=False,
        **kwargs,
    )


def create_static_cache_middleware(ttl: int = 86400, **kwargs) -> SmartCacheMiddleware:
    """Create cache middleware optimized for static content"""
    return SmartCacheMiddleware(
        default_ttl=ttl,
        cache_methods={"GET", "HEAD"},
        cache_status_codes={200, 301, 302, 404},
        include_paths=["/static", "/assets", "/images", "/css", "/js"],
        cache_authenticated=True,
        **kwargs,
    )


def create_page_cache_middleware(ttl: int = 3600, **kwargs) -> SmartCacheMiddleware:
    """Create cache middleware optimized for HTML pages"""
    return SmartCacheMiddleware(
        default_ttl=ttl,
        cache_methods={"GET"},
        cache_status_codes={200},
        cache_headers={"accept", "accept-encoding", "accept-language"},
        cache_vary_headers={"accept-language"},
        cache_authenticated=False,
        **kwargs,
    )
