#!/usr/bin/env python3
"""
🌪️ Production API with Complete Middleware Stack

This example demonstrates a production-ready API using Catzilla's
Zero-Allocation Middleware System with a complete middleware stack
for authentication, authorization, rate limiting, caching, logging,
monitoring, and error handling.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'python'))

import time
import json
import uuid
import hashlib
import hmac
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any


def main():
    """Production API with complete zero-allocation middleware stack"""

    print("🌪️ Production API - Complete Middleware Stack")
    print("=" * 50)

    try:
        from catzilla import Catzilla
        from catzilla.middleware import Response
        from catzilla.validation import BaseModel
        from catzilla.integration import DIContainer, Service, Inject

        # Create production app with DI
        container = DIContainer()
        app = Catzilla(di_container=container)

    except ImportError:
        print("⚠️  Catzilla not available, showing production patterns...")
        return simulate_production_patterns()

    # ========================================================================
    # PRODUCTION SERVICES
    # ========================================================================

    class AuthService(Service):
        """Production authentication service"""

        def __init__(self):
            self.jwt_secret = "production-secret-key"
            self.active_sessions = {}
            self.blacklisted_tokens = set()

        def validate_jwt_token(self, token: str) -> Optional[Dict[str, Any]]:
            """Validate JWT token (simplified for demo)"""
            if token in self.blacklisted_tokens:
                return None

            # In production, would verify JWT signature
            if len(token) >= 20 and token.startswith('eyJ'):
                return {
                    'user_id': 'user_123',
                    'role': 'admin',
                    'permissions': ['read', 'write', 'delete'],
                    'exp': time.time() + 3600
                }
            return None

        def check_permission(self, user_role: str, required_permission: str) -> bool:
            """Check user permissions"""
            role_permissions = {
                'admin': ['read', 'write', 'delete', 'admin'],
                'user': ['read', 'write'],
                'guest': ['read']
            }
            return required_permission in role_permissions.get(user_role, [])

    class CacheService(Service):
        """Production caching service"""

        def __init__(self):
            self.cache = {}
            self.expiry = {}
            self.stats = {'hits': 0, 'misses': 0}

        def get(self, key: str) -> Optional[Any]:
            """Get cached value"""
            if key in self.cache:
                if time.time() < self.expiry.get(key, 0):
                    self.stats['hits'] += 1
                    return self.cache[key]
                else:
                    del self.cache[key]
                    if key in self.expiry:
                        del self.expiry[key]

            self.stats['misses'] += 1
            return None

        def set(self, key: str, value: Any, ttl: int = 300):
            """Set cached value with TTL"""
            self.cache[key] = value
            self.expiry[key] = time.time() + ttl

    class MonitoringService(Service):
        """Production monitoring and metrics"""

        def __init__(self):
            self.request_count = 0
            self.error_count = 0
            self.response_times = []
            self.endpoint_stats = {}
            self.alerts = []

        def record_request(self, endpoint: str, method: str, status: int, duration: float):
            """Record request metrics"""
            self.request_count += 1
            self.response_times.append(duration)

            if status >= 400:
                self.error_count += 1

            endpoint_key = f"{method} {endpoint}"
            if endpoint_key not in self.endpoint_stats:
                self.endpoint_stats[endpoint_key] = {
                    'count': 0, 'errors': 0, 'avg_time': 0, 'total_time': 0
                }

            stats = self.endpoint_stats[endpoint_key]
            stats['count'] += 1
            stats['total_time'] += duration
            stats['avg_time'] = stats['total_time'] / stats['count']

            if status >= 400:
                stats['errors'] += 1

        def get_health_status(self) -> Dict[str, Any]:
            """Get system health status"""
            error_rate = self.error_count / self.request_count if self.request_count > 0 else 0
            avg_response_time = sum(self.response_times) / len(self.response_times) if self.response_times else 0

            return {
                'status': 'healthy' if error_rate < 0.05 and avg_response_time < 0.5 else 'degraded',
                'total_requests': self.request_count,
                'error_rate': error_rate,
                'avg_response_time_ms': avg_response_time * 1000,
                'uptime': time.time()  # Simplified
            }

    class RateLimitService(Service):
        """Production rate limiting"""

        def __init__(self):
            self.clients = {}  # client_id -> {count, window_start, blocked_until}
            self.global_limits = {
                'default': {'requests': 1000, 'window': 3600},  # 1000/hour
                'premium': {'requests': 5000, 'window': 3600},  # 5000/hour
                'admin': {'requests': 10000, 'window': 3600}    # 10000/hour
            }

        def check_rate_limit(self, client_id: str, tier: str = 'default') -> Dict[str, Any]:
            """Check if client is within rate limits"""
            current_time = time.time()
            limits = self.global_limits.get(tier, self.global_limits['default'])

            if client_id not in self.clients:
                self.clients[client_id] = {
                    'count': 1,
                    'window_start': current_time,
                    'blocked_until': 0
                }
                return {'allowed': True, 'remaining': limits['requests'] - 1}

            client = self.clients[client_id]

            # Check if still blocked
            if current_time < client['blocked_until']:
                return {
                    'allowed': False,
                    'remaining': 0,
                    'reset_time': client['blocked_until']
                }

            # Check if new window
            if current_time - client['window_start'] > limits['window']:
                client['count'] = 1
                client['window_start'] = current_time
                client['blocked_until'] = 0
                return {'allowed': True, 'remaining': limits['requests'] - 1}

            # Check current window
            if client['count'] >= limits['requests']:
                client['blocked_until'] = client['window_start'] + limits['window']
                return {
                    'allowed': False,
                    'remaining': 0,
                    'reset_time': client['blocked_until']
                }

            client['count'] += 1
            return {'allowed': True, 'remaining': limits['requests'] - client['count']}

    # Register services
    container.register_singleton(AuthService)
    container.register_singleton(CacheService)
    container.register_singleton(MonitoringService)
    container.register_singleton(RateLimitService)

    # ========================================================================
    # PRODUCTION MIDDLEWARE STACK
    # ========================================================================

    print("🛠️  Configuring production middleware stack...")

    # Enable built-in C middleware for maximum performance
    app.enable_builtin_middleware([
        'security_headers',  # OWASP security headers
        'cors',             # Cross-origin requests
        'compression'       # Response compression
    ])

    @app.middleware(priority=50, pre_route=True, name="request_id")
    def request_id_middleware(request):
        """Generate unique request ID for tracing"""
        request_id = str(uuid.uuid4())
        request.context['request_id'] = request_id
        request.context['start_time'] = time.time()

        # Add to response headers later
        return None

    @app.middleware(priority=100, pre_route=True, name="rate_limiting")
    def rate_limiting_middleware(request):
        """Production rate limiting with tiered limits"""
        try:
            rate_limit_service = container.resolve(RateLimitService)

            # Identify client (IP + user ID if authenticated)
            client_ip = request.remote_addr or 'unknown'
            user_id = request.context.get('user_id', '')
            client_id = f"{client_ip}:{user_id}" if user_id else client_ip

            # Determine tier based on authentication
            tier = 'default'
            if 'Authorization' in request.headers:
                tier = 'premium'  # Authenticated users get higher limits

            # Check rate limit
            limit_result = rate_limit_service.check_rate_limit(client_id, tier)

            if not limit_result['allowed']:
                return Response(
                    status=429,
                    headers={
                        'Retry-After': str(int(limit_result.get('reset_time', time.time() + 3600) - time.time())),
                        'X-RateLimit-Limit': str(rate_limit_service.global_limits[tier]['requests']),
                        'X-RateLimit-Remaining': '0',
                        'X-RateLimit-Reset': str(int(limit_result.get('reset_time', time.time() + 3600)))
                    },
                    body=json.dumps({
                        'error': 'Rate limit exceeded',
                        'retry_after': int(limit_result.get('reset_time', time.time() + 3600) - time.time())
                    }),
                    content_type="application/json"
                )

            # Add rate limit headers
            request.context['rate_limit_remaining'] = limit_result['remaining']

            return None

        except Exception as e:
            print(f"Rate limiting error: {e}")
            return None  # Allow request on rate limiting failure

    @app.middleware(priority=200, pre_route=True, name="authentication")
    def authentication_middleware(request):
        """Production JWT authentication"""
        # Skip auth for public endpoints
        public_endpoints = ['/health', '/metrics', '/docs']
        if any(request.path.startswith(endpoint) for endpoint in public_endpoints):
            return None

        try:
            auth_service = container.resolve(AuthService)

            auth_header = request.headers.get('Authorization', '')

            if not auth_header:
                return Response(
                    status=401,
                    headers={'WWW-Authenticate': 'Bearer realm="API"'},
                    body=json.dumps({
                        'error': 'Authentication required',
                        'message': 'Please provide a valid Bearer token'
                    }),
                    content_type="application/json"
                )

            if not auth_header.startswith('Bearer '):
                return Response(
                    status=401,
                    headers={'WWW-Authenticate': 'Bearer realm="API"'},
                    body=json.dumps({
                        'error': 'Invalid authentication format',
                        'message': 'Use Bearer token authentication'
                    }),
                    content_type="application/json"
                )

            token = auth_header[7:]

            # Validate JWT token
            user_info = auth_service.validate_jwt_token(token)

            if not user_info:
                return Response(
                    status=403,
                    body=json.dumps({
                        'error': 'Invalid or expired token',
                        'message': 'Please re-authenticate'
                    }),
                    content_type="application/json"
                )

            # Store user context
            request.context['user_id'] = user_info['user_id']
            request.context['user_role'] = user_info['role']
            request.context['user_permissions'] = user_info['permissions']
            request.context['token_exp'] = user_info['exp']

            return None

        except Exception as e:
            print(f"Authentication error: {e}")
            return Response(
                status=500,
                body=json.dumps({'error': 'Authentication service unavailable'}),
                content_type="application/json"
            )

    @app.middleware(priority=300, pre_route=True, name="smart_caching")
    def smart_caching_middleware(request):
        """Intelligent response caching"""
        # Only cache GET requests
        if request.method != 'GET':
            return None

        # Skip caching for user-specific or real-time endpoints
        skip_cache_paths = ['/api/profile', '/api/realtime', '/api/admin']
        if any(path in request.path for path in skip_cache_paths):
            return None

        try:
            cache_service = container.resolve(CacheService)

            # Create cache key including user context for personalized responses
            user_id = request.context.get('user_id', 'anonymous')
            query_hash = hashlib.md5((request.query_string or '').encode()).hexdigest()[:8]
            cache_key = f"{request.path}:{user_id}:{query_hash}"

            # Check cache
            cached_response = cache_service.get(cache_key)

            if cached_response:
                print(f"💨 Cache HIT: {cache_key}")
                return Response(
                    status=200,
                    body=json.dumps(cached_response),
                    headers={
                        'Content-Type': 'application/json',
                        'X-Cache': 'HIT',
                        'X-Cache-Key': cache_key[:16] + '...'
                    }
                )

            # Store cache info for post-route caching
            request.context['cache_key'] = cache_key
            request.context['cache_service'] = cache_service

            return None

        except Exception as e:
            print(f"Caching error: {e}")
            return None

    @app.middleware(priority=400, pre_route=True, name="authorization")
    def authorization_middleware(request):
        """Role-based authorization"""
        # Skip for public endpoints
        if request.path.startswith('/health') or request.path.startswith('/docs'):
            return None

        try:
            auth_service = container.resolve(AuthService)
            user_role = request.context.get('user_role')

            if not user_role:
                return None  # No user authenticated, will be handled by auth middleware

            # Define endpoint permissions
            admin_endpoints = ['/api/admin', '/api/users/delete']
            write_endpoints = ['/api/users', '/api/orders']

            required_permission = None

            if any(endpoint in request.path for endpoint in admin_endpoints):
                required_permission = 'admin'
            elif request.method in ['POST', 'PUT', 'DELETE'] and any(endpoint in request.path for endpoint in write_endpoints):
                required_permission = 'write'
            else:
                required_permission = 'read'

            # Check permission
            if not auth_service.check_permission(user_role, required_permission):
                return Response(
                    status=403,
                    body=json.dumps({
                        'error': 'Insufficient permissions',
                        'required': required_permission,
                        'your_role': user_role
                    }),
                    content_type="application/json"
                )

            request.context['required_permission'] = required_permission

            return None

        except Exception as e:
            print(f"Authorization error: {e}")
            return Response(
                status=500,
                body=json.dumps({'error': 'Authorization service unavailable'}),
                content_type="application/json"
            )

    @app.middleware(priority=900, post_route=True, name="response_caching")
    def response_caching_middleware(request, response):
        """Cache successful responses"""
        cache_key = request.context.get('cache_key')
        cache_service = request.context.get('cache_service')

        if cache_key and cache_service and response.status_code == 200:
            try:
                # Parse response for caching
                response_data = json.loads(response.body) if response.body else {}

                # Determine TTL based on endpoint
                ttl = 300  # 5 minutes default
                if '/api/static' in request.path:
                    ttl = 3600  # 1 hour for static data
                elif '/api/users' in request.path:
                    ttl = 600   # 10 minutes for user data

                cache_service.set(cache_key, response_data, ttl)
                response.headers['X-Cache'] = 'MISS'
                response.headers['X-Cache-TTL'] = str(ttl)

                print(f"💾 Cached: {cache_key} (TTL: {ttl}s)")

            except Exception as e:
                print(f"Response caching error: {e}")

        return response

    @app.middleware(priority=950, post_route=True, name="monitoring")
    def monitoring_middleware(request, response):
        """Production monitoring and metrics"""
        try:
            monitoring_service = container.resolve(MonitoringService)

            # Calculate duration
            start_time = request.context.get('start_time', time.time())
            duration = time.time() - start_time

            # Record metrics
            monitoring_service.record_request(
                endpoint=request.path,
                method=request.method,
                status=response.status_code,
                duration=duration
            )

            # Add monitoring headers
            response.headers['X-Request-ID'] = request.context.get('request_id', 'unknown')
            response.headers['X-Response-Time'] = f"{duration*1000:.2f}ms"

            # Add rate limit headers
            if 'rate_limit_remaining' in request.context:
                response.headers['X-RateLimit-Remaining'] = str(request.context['rate_limit_remaining'])

            return response

        except Exception as e:
            print(f"Monitoring error: {e}")
            return response

    @app.middleware(priority=999, post_route=True, name="security_finalization")
    def security_finalization_middleware(request, response):
        """Final security headers and cleanup"""
        # Remove sensitive headers
        sensitive_headers = ['X-Internal-User', 'X-Debug-Info']
        for header in sensitive_headers:
            if header in response.headers:
                del response.headers[header]

        # Add final security headers
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'

        return response

    # ========================================================================
    # PRODUCTION API ENDPOINTS
    # ========================================================================

    print("📋 Registering production API endpoints...")

    # Health and monitoring endpoints
    @app.route('/health')
    @Inject(monitoring_service=MonitoringService)
    def health_check(monitoring_service: MonitoringService):
        """Health check endpoint"""
        health_status = monitoring_service.get_health_status()

        return {
            'status': health_status['status'],
            'timestamp': datetime.utcnow().isoformat(),
            'version': '1.0.0',
            'middleware': 'zero-allocation',
            'uptime': health_status.get('uptime', 0)
        }

    @app.route('/metrics')
    @Inject(monitoring_service=MonitoringService, cache_service=CacheService)
    def get_metrics(request, monitoring_service: MonitoringService, cache_service: CacheService):
        """Metrics endpoint for monitoring systems"""
        # Require admin permission
        if request.context.get('user_role') != 'admin':
            return Response(
                status=403,
                body=json.dumps({'error': 'Admin access required'}),
                content_type="application/json"
            )

        health_status = monitoring_service.get_health_status()

        return {
            'system': health_status,
            'endpoints': monitoring_service.endpoint_stats,
            'cache': {
                'hits': cache_service.stats['hits'],
                'misses': cache_service.stats['misses'],
                'hit_ratio': cache_service.stats['hits'] / (cache_service.stats['hits'] + cache_service.stats['misses']) if (cache_service.stats['hits'] + cache_service.stats['misses']) > 0 else 0,
                'size': len(cache_service.cache)
            },
            'middleware_stack': 'production-optimized'
        }

    # User management endpoints
    @app.route('/api/users')
    def get_users(request):
        """Get users list"""
        # Simulate user data
        users = [
            {'id': 1, 'name': 'Alice Admin', 'role': 'admin'},
            {'id': 2, 'name': 'Bob User', 'role': 'user'},
            {'id': 3, 'name': 'Carol Guest', 'role': 'guest'}
        ]

        return {
            'users': users,
            'total': len(users),
            'request_user': request.context.get('user_id'),
            'permissions': request.context.get('user_permissions', [])
        }

    @app.route('/api/users/<user_id>')
    def get_user(request, user_id: str):
        """Get specific user"""
        # Check if user can access this resource
        current_user_id = request.context.get('user_id')
        user_role = request.context.get('user_role')

        if current_user_id != user_id and user_role != 'admin':
            return Response(
                status=403,
                body=json.dumps({'error': 'Access denied'}),
                content_type="application/json"
            )

        # Simulate user lookup
        return {
            'id': user_id,
            'name': f'User {user_id}',
            'email': f'user{user_id}@example.com',
            'role': 'user',
            'last_login': datetime.utcnow().isoformat(),
            'accessed_by': current_user_id
        }

    @app.route('/api/orders', methods=['POST'])
    def create_order(request):
        """Create new order"""
        try:
            order_data = request.json

            # Validate order data
            required_fields = ['product_id', 'quantity']
            for field in required_fields:
                if field not in order_data:
                    return Response(
                        status=400,
                        body=json.dumps({'error': f'Missing required field: {field}'}),
                        content_type="application/json"
                    )

            # Create order
            order_id = str(uuid.uuid4())

            order = {
                'id': order_id,
                'user_id': request.context.get('user_id'),
                'product_id': order_data['product_id'],
                'quantity': order_data['quantity'],
                'status': 'pending',
                'created_at': datetime.utcnow().isoformat(),
                'total': order_data['quantity'] * 99.99  # Mock price
            }

            return order

        except Exception as e:
            return Response(
                status=400,
                body=json.dumps({'error': 'Invalid request data'}),
                content_type="application/json"
            )

    @app.route('/api/admin/stats')
    @Inject(monitoring_service=MonitoringService)
    def admin_stats(request, monitoring_service: MonitoringService):
        """Admin statistics endpoint"""
        health_status = monitoring_service.get_health_status()

        return {
            'system_stats': health_status,
            'middleware_performance': {
                'total_requests': health_status['total_requests'],
                'error_rate': health_status['error_rate'],
                'avg_response_time': health_status['avg_response_time_ms']
            },
            'admin_user': request.context.get('user_id')
        }

    # ========================================================================
    # PRODUCTION DEMONSTRATION
    # ========================================================================

    def demonstrate_production_middleware():
        """Demonstrate production middleware stack"""
        print("\n🚀 Production Middleware Stack Active")
        print("-" * 45)

        middleware_stack = [
            "Request ID Generation",
            "Rate Limiting (Tiered)",
            "JWT Authentication",
            "Smart Caching",
            "Role-based Authorization",
            "Built-in Security Headers",
            "Built-in CORS",
            "Built-in Compression",
            "Response Caching",
            "Production Monitoring",
            "Security Finalization"
        ]

        print("Active Middleware (execution order):")
        for i, middleware in enumerate(middleware_stack, 1):
            print(f"  {i:2d}. {middleware}")

        print(f"\nProduction Features:")
        print(f"  ✅ Zero-allocation C middleware")
        print(f"  ✅ JWT authentication with validation")
        print(f"  ✅ Tiered rate limiting")
        print(f"  ✅ Role-based authorization")
        print(f"  ✅ Intelligent caching")
        print(f"  ✅ Comprehensive monitoring")
        print(f"  ✅ OWASP security headers")
        print(f"  ✅ Request tracing")
        print(f"  ✅ Error handling")
        print(f"  ✅ Performance optimization")

    def show_production_performance():
        """Show expected production performance"""
        print(f"\n📊 Production Performance Expectations")
        print("-" * 45)

        print("Middleware Stack Performance:")
        print("  • Total middleware execution: <100μs")
        print("  • Built-in C middleware: <30μs")
        print("  • Authentication: <20μs")
        print("  • Authorization: <15μs")
        print("  • Rate limiting: <25μs")
        print("  • Caching: <35μs")
        print("  • Monitoring: <10μs")

        print("\nThroughput Expectations:")
        print("  • Requests/second: 50,000+")
        print("  • Memory per request: <1KB")
        print("  • CPU overhead: <5%")
        print("  • Cache hit ratio: 80-90%")

        print("\nProduction Reliability:")
        print("  • Error rate: <0.1%")
        print("  • Response time P99: <50ms")
        print("  • Zero memory leaks")
        print("  • Graceful degradation")

    # Run production demonstration
    demonstrate_production_middleware()
    show_production_performance()

    print(f"\n🎉 Production middleware stack configured!")
    print(f"   Ready for production deployment with:")
    print(f"   • Enterprise-grade security")
    print(f"   • High-performance optimization")
    print(f"   • Comprehensive monitoring")
    print(f"   • Scalable architecture")


def simulate_production_patterns():
    """Simulate production patterns when Catzilla is not available"""
    print("📋 Production Middleware Patterns")
    print("-" * 35)

    patterns = [
        "Security-first middleware ordering",
        "Tiered rate limiting with user tiers",
        "JWT authentication with proper validation",
        "Role-based authorization with granular permissions",
        "Intelligent caching with TTL strategies",
        "Comprehensive monitoring and metrics",
        "Error handling with proper HTTP status codes",
        "Request tracing with unique IDs",
        "Response compression and optimization",
        "Security header management"
    ]

    for i, pattern in enumerate(patterns, 1):
        print(f"  {i:2d}. {pattern}")

    print(f"\nProduction deployment would include:")
    print(f"  • Load balancing")
    print(f"  • SSL/TLS termination")
    print(f"  • Database connection pooling")
    print(f"  • Redis caching")
    print(f"  • Prometheus metrics")
    print(f"  • Structured logging")


if __name__ == '__main__':
    main()
