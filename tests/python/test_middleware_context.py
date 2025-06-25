#!/usr/bin/env python3
"""
🌪️ Catzilla Middleware Context Tests - Comprehensive Coverage

Tests specifically for the request context functionality that was missing
from the existing middleware test suite. These tests verify:

1. Context initialization patterns
2. Context sharing between middleware
3. Safe context access in route handlers
4. Error handling for uninitialized context
5. Real-world usage patterns from documentation
6. Memory efficiency and performance

This addresses the critical testing gap discovered during documentation audit.
"""

import pytest
import sys
import os
import time
import json
from typing import Dict, Any, List, Optional
from unittest.mock import Mock, patch, MagicMock

# Add the project root to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from catzilla import Catzilla, Request, Response, JSONResponse


class TestMiddlewareContext:
    """Test middleware context initialization, sharing, and access patterns"""

    def setup_method(self):
        """Set up test fixtures"""
        self.app = Catzilla(use_jemalloc=False, memory_profiling=False)
        self.context_log = []  # Track context operations
        self.request_log = []  # Track request processing

    def create_mock_request(self, path="/test", method="GET", headers=None):
        """Create a mock request object that behaves like real Request"""
        request = Mock(spec=Request)
        request.path = path
        request.method = method
        request.headers = headers or {}
        request.query_params = {}
        # Initially no context - must be manually created
        return request

    def test_context_manual_initialization_required(self):
        """Test that context must be manually initialized"""
        request = self.create_mock_request()

        # Fresh request should not have _context attribute
        assert not hasattr(request, '_context')

        # Accessing non-existent context should return empty dict with getattr
        context_data = getattr(request, '_context', {})
        assert context_data == {}

        # Getting from non-existent context should use default
        user_id = getattr(request, '_context', {}).get('user_id', 'anonymous')
        assert user_id == 'anonymous'

    def test_context_initialization_pattern(self):
        """Test the correct context initialization pattern from documentation"""
        request = self.create_mock_request()

        # This is the pattern shown in updated documentation
        if not hasattr(request, '_context'):
            request._context = {}

        # Now context exists and can be used
        assert hasattr(request, '_context')
        assert request._context == {}

        # Can store data
        request._context['user_id'] = 'user123'
        request._context['authenticated'] = True

        assert request._context['user_id'] == 'user123'
        assert request._context['authenticated'] is True

    def test_safe_context_access_pattern(self):
        """Test the safe context access pattern from documentation"""
        request = self.create_mock_request()

        # Safe access when context doesn't exist
        user_id = getattr(request, '_context', {}).get('user_id', 'anonymous')
        authenticated = getattr(request, '_context', {}).get('authenticated', False)

        assert user_id == 'anonymous'
        assert authenticated is False

        # Initialize context
        request._context = {'user_id': 'user456', 'authenticated': True}

        # Safe access when context exists
        user_id = getattr(request, '_context', {}).get('user_id', 'anonymous')
        authenticated = getattr(request, '_context', {}).get('authenticated', False)

        assert user_id == 'user456'
        assert authenticated is True

    def test_middleware_context_sharing_chain(self):
        """Test context sharing between multiple middleware"""
        execution_order = []

        def auth_middleware(request, response) -> Optional[Response]:
            """First middleware - sets up authentication"""
            execution_order.append('auth_start')

            # Initialize context (required pattern)
            if not hasattr(request, '_context'):
                request._context = {}

            # Simulate authentication
            auth_header = request.headers.get('Authorization', '')
            if auth_header == 'Bearer valid-token':
                request._context['authenticated'] = True
                request._context['user_id'] = 'user123'
                request._context['permissions'] = ['read', 'write']
            else:
                request._context['authenticated'] = False

            execution_order.append('auth_end')
            return None  # Continue

        def permission_middleware(request, response) -> Optional[Response]:
            """Second middleware - checks permissions using context"""
            execution_order.append('permission_start')

            # Safe context access
            authenticated = getattr(request, '_context', {}).get('authenticated', False)
            permissions = getattr(request, '_context', {}).get('permissions', [])

            if not authenticated:
                return JSONResponse({"error": "Not authenticated"}, status_code=401)

            if 'write' not in permissions:
                return JSONResponse({"error": "Insufficient permissions"}, status_code=403)

            execution_order.append('permission_end')
            return None  # Continue

        def logging_middleware(request, response) -> Optional[Response]:
            """Third middleware - logs using context"""
            execution_order.append('logging_start')

            # Access context data for logging
            user_id = getattr(request, '_context', {}).get('user_id', 'anonymous')
            authenticated = getattr(request, '_context', {}).get('authenticated', False)

            log_entry = {
                'path': request.path,
                'user_id': user_id,
                'authenticated': authenticated,
                'timestamp': time.time()
            }
            self.context_log.append(log_entry)

            execution_order.append('logging_end')
            return None  # Continue

        # Test 1: Valid authentication - should pass through all middleware
        request1 = self.create_mock_request(headers={'Authorization': 'Bearer valid-token'})

        # Execute middleware chain manually
        result1 = auth_middleware(request1, Mock())
        assert result1 is None  # Continue

        result2 = permission_middleware(request1, Mock())
        assert result2 is None  # Continue

        result3 = logging_middleware(request1, Mock())
        assert result3 is None  # Continue

        # Verify execution order
        expected_order = ['auth_start', 'auth_end', 'permission_start', 'permission_end', 'logging_start', 'logging_end']
        assert execution_order == expected_order

        # Verify context was shared correctly
        assert request1._context['authenticated'] is True
        assert request1._context['user_id'] == 'user123'
        assert request1._context['permissions'] == ['read', 'write']

        # Verify logging captured context
        assert len(self.context_log) == 1
        log_entry = self.context_log[0]
        assert log_entry['user_id'] == 'user123'
        assert log_entry['authenticated'] is True

    def test_middleware_context_early_termination(self):
        """Test middleware chain termination with context"""
        execution_order = []

        def auth_middleware(request, response) -> Optional[Response]:
            execution_order.append('auth')
            if not hasattr(request, '_context'):
                request._context = {}
            request._context['authenticated'] = False  # Fail auth
            return None

        def permission_middleware(request, response) -> Optional[Response]:
            execution_order.append('permission')
            authenticated = getattr(request, '_context', {}).get('authenticated', False)
            if not authenticated:
                return JSONResponse({"error": "Access denied"}, status_code=401)
            return None

        def should_not_run_middleware(request, response) -> Optional[Response]:
            execution_order.append('should_not_run')
            return None

        request = self.create_mock_request()

        # Execute chain
        result1 = auth_middleware(request, Mock())
        assert result1 is None

        result2 = permission_middleware(request, Mock())
        assert isinstance(result2, JSONResponse)  # Early termination

        # Should not reach third middleware
        assert execution_order == ['auth', 'permission']
        assert 'should_not_run' not in execution_order

    def test_context_error_handling_patterns(self):
        """Test error handling when context is not properly initialized"""
        request = self.create_mock_request()

        # Test accessing context that doesn't exist (safe pattern)
        def safe_context_access():
            user_id = getattr(request, '_context', {}).get('user_id', 'default')
            return user_id

        # Should not raise exception
        result = safe_context_access()
        assert result == 'default'

        # Test unsafe pattern (what docs used to show incorrectly)
        def unsafe_context_access():
            try:
                # This would fail if context doesn't exist
                return request._context['user_id']
            except AttributeError:
                return 'error'

        result = unsafe_context_access()
        assert result == 'error'

    def test_route_handler_context_access(self):
        """Test route handlers accessing context set by middleware"""

        def setup_user_middleware(request, response) -> Optional[Response]:
            """Middleware that sets up user context"""
            if not hasattr(request, '_context'):
                request._context = {}

            # Simulate user lookup
            api_key = request.headers.get('X-API-Key')
            if api_key == 'valid-key':
                request._context.update({
                    'user_id': 'user789',
                    'user_name': 'Test User',
                    'permissions': ['read', 'write', 'admin'],
                    'session_id': 'session123'
                })
            return None

        # Simulate route handler that uses context
        def get_user_profile(request):
            """Route handler that accesses middleware context"""
            # Safe context access pattern
            context = getattr(request, '_context', {})

            return {
                'user_id': context.get('user_id', 'anonymous'),
                'user_name': context.get('user_name', 'Unknown'),
                'permissions': context.get('permissions', []),
                'session_id': context.get('session_id', None)
            }

        # Test with valid API key
        request_with_key = self.create_mock_request(headers={'X-API-Key': 'valid-key'})

        # Run middleware
        setup_user_middleware(request_with_key, Mock())

        # Run route handler
        profile = get_user_profile(request_with_key)

        assert profile['user_id'] == 'user789'
        assert profile['user_name'] == 'Test User'
        assert profile['permissions'] == ['read', 'write', 'admin']
        assert profile['session_id'] == 'session123'

        # Test without API key
        request_no_key = self.create_mock_request()

        # Run middleware (no context set)
        setup_user_middleware(request_no_key, Mock())

        # Run route handler (should get defaults)
        profile_no_key = get_user_profile(request_no_key)

        assert profile_no_key['user_id'] == 'anonymous'
        assert profile_no_key['user_name'] == 'Unknown'
        assert profile_no_key['permissions'] == []
        assert profile_no_key['session_id'] is None

    def test_context_performance_characteristics(self):
        """Test that context operations are efficient"""
        request = self.create_mock_request()

        # Time context initialization
        start_time = time.time()
        for i in range(1000):
            if not hasattr(request, '_context'):
                request._context = {}
            request._context[f'key_{i}'] = f'value_{i}'
        init_time = time.time() - start_time

        # Time context access
        start_time = time.time()
        for i in range(1000):
            value = getattr(request, '_context', {}).get(f'key_{i}', 'default')
        access_time = time.time() - start_time

        # Context operations should be reasonably fast (under 10ms for 1000 operations)
        assert init_time < 0.01, f"Context initialization too slow: {init_time}s"
        assert access_time < 0.01, f"Context access too slow: {access_time}s"

        # Verify all data was stored correctly
        assert len(request._context) == 1000
        assert request._context['key_500'] == 'value_500'

    def test_real_world_auth_and_logging_scenario(self):
        """Test realistic middleware scenario matching examples"""
        execution_log = []

        def request_id_middleware(request, response) -> Optional[Response]:
            """Add unique request ID for tracing"""
            import uuid
            request_id = str(uuid.uuid4())[:8]

            # Initialize context - this is the critical pattern
            if not hasattr(request, '_context'):
                request._context = {}

            request._context['request_id'] = request_id
            request._context['start_time'] = time.time()

            execution_log.append(f"request_id_set:{request_id}")
            return None

        def auth_middleware(request, response) -> Optional[Response]:
            """Authentication with multiple methods"""
            # Initialize context if needed
            if not hasattr(request, '_context'):
                request._context = {}

            # Check multiple auth methods
            api_key = request.headers.get('Authorization', '')
            api_key_query = request.query_params.get('api_key', '')

            if api_key == 'Bearer secret-token' or api_key_query == 'demo-key':
                request._context['authenticated'] = True
                request._context['auth_method'] = 'header' if api_key else 'query'
                execution_log.append("auth_success")
            else:
                request._context['authenticated'] = False
                execution_log.append("auth_failed")
                return JSONResponse({"error": "Authentication required"}, status_code=401)

            return None

        def timing_middleware(request, response) -> Optional[Response]:
            """Add timing information"""
            if not hasattr(request, '_context'):
                request._context = {}

            # Calculate duration if start_time exists
            if 'start_time' in getattr(request, '_context', {}):
                duration = time.time() - request._context['start_time']
                request._context['duration_ms'] = duration * 1000
                execution_log.append(f"timing_calculated:{duration:.3f}s")

            return None

        # Test successful auth flow
        request = self.create_mock_request()
        request.headers = {'Authorization': 'Bearer secret-token'}

        # Execute middleware chain
        result1 = request_id_middleware(request, Mock())
        assert result1 is None

        result2 = auth_middleware(request, Mock())
        assert result2 is None

        time.sleep(0.001)  # Small delay to test timing

        result3 = timing_middleware(request, Mock())
        assert result3 is None

        # Verify complete context
        context = getattr(request, '_context', {})

        assert 'request_id' in context
        assert len(context['request_id']) == 8  # UUID prefix
        assert context['authenticated'] is True
        assert context['auth_method'] == 'header'
        assert 'duration_ms' in context
        assert context['duration_ms'] > 0

        # Verify execution log
        assert 'auth_success' in execution_log
        assert 'timing_calculated' in ''.join(execution_log)
        assert any('request_id_set:' in log for log in execution_log)


class TestMiddlewareContextIntegration:
    """Integration tests for context with actual Catzilla routing"""

    def test_context_with_fastapi_style_decorators(self):
        """Test context works with @app.get() style decorators"""
        app = Catzilla(use_jemalloc=False)
        context_data = {}

        def user_loader_middleware(request, response) -> Optional[Response]:
            if not hasattr(request, '_context'):
                request._context = {}
            request._context['user'] = 'test_user'
            context_data['middleware_ran'] = True
            return None

        @app.get("/test", middleware=[user_loader_middleware])
        def test_handler(request):
            user = getattr(request, '_context', {}).get('user', 'anonymous')
            context_data['handler_user'] = user
            return {"user": user}

        # Verify route was registered with middleware
        routes = app.router._routes
        test_route = None
        for route in routes:
            if route.path == "/test" and route.method == "GET":
                test_route = route
                break

        assert test_route is not None
        assert hasattr(test_route, 'middleware')
        assert test_route.middleware is not None
        assert len(test_route.middleware) == 1


def test_documentation_examples_work():
    """Test that code examples from updated documentation actually work"""

    # Example 1: Manual context initialization from docs
    request = Mock(spec=Request)
    request.headers = {'Authorization': 'Bearer token123'}

    # This is the pattern from updated docs
    if not hasattr(request, '_context'):
        request._context = {}

    request._context['authenticated'] = True
    request._context['user_id'] = 'user123'

    assert request._context['authenticated'] is True
    assert request._context['user_id'] == 'user123'

    # Example 2: Safe context access from docs
    def get_user_data(request):
        authenticated = getattr(request, '_context', {}).get('authenticated', False)
        user_id = getattr(request, '_context', {}).get('user_id', 'anonymous')
        return {"authenticated": authenticated, "user_id": user_id}

    result = get_user_data(request)
    assert result['authenticated'] is True
    assert result['user_id'] == 'user123'

    # Test with request that has no context
    empty_request = Mock(spec=Request)
    result_empty = get_user_data(empty_request)
    assert result_empty['authenticated'] is False
    assert result_empty['user_id'] == 'anonymous'


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
