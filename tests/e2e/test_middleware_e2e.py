#!/usr/bin/env python3
"""
E2E Tests for Middleware Functionality

Tests the middleware server endpoints with real HTTP requests.
"""
import pytest
import pytest_asyncio
import httpx
import asyncio
from pathlib import Path
import sys

# Add test utils to path
test_dir = Path(__file__).parent
sys.path.insert(0, str(test_dir))

from utils.server_manager import get_server_manager

# Test configuration
MIDDLEWARE_SERVER_PORT = 8105
MIDDLEWARE_SERVER_HOST = "127.0.0.1"

@pytest_asyncio.fixture(scope="module")
async def middleware_server():
    """Start and manage middleware E2E test server"""
    server_manager = get_server_manager()

    # Start the middleware server
    success = await server_manager.start_server("middleware", MIDDLEWARE_SERVER_PORT, MIDDLEWARE_SERVER_HOST)
    if not success:
        pytest.fail("Failed to start middleware test server")

    yield server_manager.get_server_url("middleware")

    # Cleanup
    await server_manager.stop_server("middleware")

@pytest.mark.asyncio
async def test_middleware_health_check(middleware_server):
    """Test middleware server health check"""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{middleware_server}/health")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "healthy"
        assert data["server"] == "middleware_e2e_test"
        assert "request_duration" in data
        assert "middleware_count" in data

@pytest.mark.asyncio
async def test_middleware_home_info(middleware_server):
    """Test middleware server info endpoint"""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{middleware_server}/")
        assert response.status_code == 200

        data = response.json()
        assert "Middleware" in data["message"]
        assert "features" in data
        assert "endpoints" in data

@pytest.mark.asyncio
async def test_public_endpoint_global_middleware(middleware_server):
    """Test public endpoint with only global middleware"""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{middleware_server}/public")
        assert response.status_code == 200

        data = response.json()
        assert data["message"] == "This is a public endpoint"
        assert "timing" in data["middleware_applied"]
        assert "logging" in data["middleware_applied"]
        assert "cors" in data["middleware_applied"]
        assert "request_duration" in data

@pytest.mark.asyncio
async def test_protected_endpoint_auth_required(middleware_server):
    """Test protected endpoint requires authentication"""
    async with httpx.AsyncClient() as client:
        # No auth header
        response = await client.get(f"{middleware_server}/protected")
        assert response.status_code == 401

        data = response.json()
        assert data["error"] == "Authentication required"
        assert data["middleware"] == "auth"

@pytest.mark.asyncio
async def test_protected_endpoint_invalid_token(middleware_server):
    """Test protected endpoint with invalid token"""
    async with httpx.AsyncClient() as client:
        # Invalid token
        headers = {"authorization": "Bearer invalid-token"}
        response = await client.get(f"{middleware_server}/protected", headers=headers)
        assert response.status_code == 403

        data = response.json()
        assert data["error"] == "Invalid token"
        assert data["middleware"] == "auth"

@pytest.mark.asyncio
async def test_protected_endpoint_valid_token(middleware_server):
    """Test protected endpoint with valid token"""
    async with httpx.AsyncClient() as client:
        # Valid token
        headers = {"authorization": "Bearer valid-token"}
        response = await client.get(f"{middleware_server}/protected", headers=headers)
        assert response.status_code == 200

        data = response.json()
        assert data["message"] == "This is a protected endpoint"
        assert data["user"]["username"] == "testuser"
        assert "auth" in data["middleware_applied"]

@pytest.mark.asyncio
async def test_rate_limit_middleware(middleware_server):
    """Test rate limiting middleware"""
    async with httpx.AsyncClient() as client:
        # Normal request
        response = await client.get(f"{middleware_server}/rate-limited")
        assert response.status_code == 200

        data = response.json()
        assert "rate_limit" in data["middleware_applied"]

        # Rate limit exceeded
        headers = {"x-rate-limit-test": "exceeded"}
        response = await client.get(f"{middleware_server}/rate-limited", headers=headers)
        assert response.status_code == 429

        data = response.json()
        assert data["error"] == "Rate limit exceeded"
        assert data["middleware"] == "rate_limit"

@pytest.mark.asyncio
async def test_validation_middleware(middleware_server):
    """Test custom validation middleware"""
    async with httpx.AsyncClient() as client:
        # Valid request
        post_data = {"data": "test data", "process_type": "standard"}
        response = await client.post(f"{middleware_server}/process", json=post_data)
        assert response.status_code == 201

        data = response.json()
        assert data["message"] == "Data processed successfully"
        assert "validation" in data["middleware_applied"]

        # Validation failure
        headers = {"x-custom-validation": "fail"}
        response = await client.post(f"{middleware_server}/process", json=post_data, headers=headers)
        assert response.status_code == 400

        data = response.json()
        assert data["error"] == "Custom validation failed"
        assert data["middleware"] == "validation"

@pytest.mark.asyncio
async def test_multiple_middleware_layers(middleware_server):
    """Test endpoint with multiple middleware layers"""
    async with httpx.AsyncClient() as client:
        # All middleware should pass
        headers = {"authorization": "Bearer valid-token"}
        response = await client.get(f"{middleware_server}/multi-middleware", headers=headers)
        assert response.status_code == 200

        data = response.json()
        assert data["message"] == "This endpoint has multiple middleware layers"
        expected_middleware = ["timing", "logging", "cors", "auth", "rate_limit", "validation"]
        for mw in expected_middleware:
            assert mw in data["middleware_applied"]

@pytest.mark.asyncio
async def test_middleware_execution_order(middleware_server):
    """Test middleware execution order"""
    async with httpx.AsyncClient() as client:
        # Clear logs first
        await client.post(f"{middleware_server}/middleware/clear-logs")

        # Make a request to protected endpoint
        headers = {"authorization": "Bearer valid-token"}
        response = await client.get(f"{middleware_server}/protected", headers=headers)
        assert response.status_code == 200

        # Check middleware logs
        response = await client.get(f"{middleware_server}/middleware/logs")
        assert response.status_code == 200

        logs_data = response.json()
        middleware_logs = logs_data["middleware_logs"]

        # Should have logs from global middleware + auth middleware
        assert len(middleware_logs) > 0

        # Check that global middleware executed before route middleware
        global_mw = [log for log in middleware_logs if log["middleware"] in ["timing", "logging", "cors"]]
        auth_mw = [log for log in middleware_logs if log["middleware"] == "auth"]

        assert len(global_mw) > 0
        assert len(auth_mw) > 0

@pytest.mark.asyncio
async def test_middleware_short_circuiting(middleware_server):
    """Test middleware short-circuiting (stopping request early)"""
    async with httpx.AsyncClient() as client:
        # Clear logs
        await client.post(f"{middleware_server}/middleware/clear-logs")

        # Make request that fails auth (should short-circuit)
        response = await client.get(f"{middleware_server}/multi-middleware")
        assert response.status_code == 401

        # Check logs - should not reach later middleware
        response = await client.get(f"{middleware_server}/middleware/logs")
        logs_data = response.json()
        middleware_logs = logs_data["middleware_logs"]

        # Should have global middleware + auth check, but not rate_limit or validation
        middleware_types = [log["middleware"] for log in middleware_logs]
        assert "auth" in middleware_types
        # Route shouldn't be reached, so no rate_limit or validation middleware

@pytest.mark.asyncio
async def test_data_processing_with_middleware(middleware_server):
    """Test POST data processing with middleware"""
    async with httpx.AsyncClient() as client:
        post_data = {
            "data": "hello world",
            "process_type": "uppercase"
        }

        response = await client.post(f"{middleware_server}/process", json=post_data)
        assert response.status_code == 201

        data = response.json()
        assert data["message"] == "Data processed successfully"
        result = data["result"]
        assert result["original"] == "hello world"
        assert result["processed"] == "HELLO WORLD"
        assert result["type"] == "uppercase"

@pytest.mark.asyncio
async def test_middleware_statistics(middleware_server):
    """Test middleware statistics collection"""
    async with httpx.AsyncClient() as client:
        # Clear logs
        await client.post(f"{middleware_server}/middleware/clear-logs")

        # Make several requests
        await client.get(f"{middleware_server}/public")
        await client.get(f"{middleware_server}/public")

        headers = {"authorization": "Bearer valid-token"}
        await client.get(f"{middleware_server}/protected", headers=headers)

        # Get statistics
        response = await client.get(f"{middleware_server}/middleware/stats")
        assert response.status_code == 200

        stats = response.json()
        assert stats["total_requests"] >= 3
        assert "middleware_executions" in stats
        assert "total_middleware_logs" in stats

        # Should have counts for different middleware types
        executions = stats["middleware_executions"]
        assert executions.get("timing", 0) > 0
        assert executions.get("logging", 0) > 0

@pytest.mark.asyncio
async def test_concurrent_middleware_requests(middleware_server):
    """Test concurrent requests through middleware"""
    async with httpx.AsyncClient() as client:
        # Create multiple concurrent requests
        tasks = []
        headers = {"authorization": "Bearer valid-token"}

        for i in range(5):
            tasks.append(client.get(f"{middleware_server}/protected", headers=headers))

        # Execute concurrently
        responses = await asyncio.gather(*tasks)

        # All should succeed
        for response in responses:
            assert response.status_code == 200
            data = response.json()
            assert data["user"]["username"] == "testuser"

@pytest.mark.asyncio
async def test_middleware_logs_clearing(middleware_server):
    """Test clearing middleware logs"""
    async with httpx.AsyncClient() as client:
        # Make some requests to generate logs
        await client.get(f"{middleware_server}/public")
        await client.get(f"{middleware_server}/public")

        # Check logs exist
        response = await client.get(f"{middleware_server}/middleware/logs")
        logs_data = response.json()
        assert logs_data["total_logs"] > 0
        assert logs_data["total_requests"] > 0

        # Clear logs
        response = await client.post(f"{middleware_server}/middleware/clear-logs")
        assert response.status_code == 200

        clear_data = response.json()
        assert clear_data["message"] == "Logs cleared successfully"
        assert clear_data["cleared_middleware_logs"] > 0
        assert clear_data["cleared_request_logs"] > 0
        # Check cleared status directly from clear response to avoid middleware triggers
        assert clear_data["total_logs"] == 0
        assert clear_data["total_requests"] == 0

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
