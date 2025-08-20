#!/usr/bin/env python3
"""
E2E Tests for Dependency Injection Functionality

Tests the DI server endpoints with real HTTP requests.
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
DI_SERVER_PORT = 8103
DI_SERVER_HOST = "127.0.0.1"

@pytest_asyncio.fixture(scope="module")
async def di_server():
    """Start and manage DI E2E test server"""
    server_manager = get_server_manager()

    # Start the DI server
    success = await server_manager.start_server("di", DI_SERVER_PORT, DI_SERVER_HOST)
    if not success:
        pytest.fail("Failed to start DI test server")

    yield server_manager.get_server_url("di")

    # Cleanup
    await server_manager.stop_server("di")

@pytest.mark.asyncio
async def test_di_health_check(di_server):
    """Test DI server health check"""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{di_server}/health")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "healthy"
        assert data["server"] == "di_e2e_test"
        assert "services" in data
        assert data["services"]["database"] == "active"
        assert data["services"]["greeting"] == "active"
        assert data["services"]["email"] == "active"

@pytest.mark.asyncio
async def test_di_home_info(di_server):
    """Test DI server info endpoint"""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{di_server}/")
        assert response.status_code == 200

        data = response.json()
        assert "Dependency Injection" in data["message"]
        assert "features" in data
        assert "endpoints" in data
        assert "services" in data

@pytest.mark.asyncio
async def test_database_service_get_users(di_server):
    """Test database service - get all users"""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{di_server}/di/users")
        assert response.status_code == 200

        data = response.json()
        assert "users" in data
        assert data["count"] >= 3  # Should have initial users
        assert data["service"] == "database"

        # Check user structure
        users = data["users"]
        assert len(users) >= 3
        for user in users:
            assert "id" in user
            assert "name" in user
            assert "email" in user

@pytest.mark.asyncio
async def test_database_service_get_user(di_server):
    """Test database service - get specific user"""
    async with httpx.AsyncClient() as client:
        # Get existing user
        response = await client.get(f"{di_server}/di/users/1")
        assert response.status_code == 200

        data = response.json()
        assert "user" in data
        assert data["user"]["id"] == 1
        assert data["service"] == "database"

        # Test non-existent user
        response = await client.get(f"{di_server}/di/users/999")
        assert response.status_code == 404

        data = response.json()
        assert "error" in data
        assert data["user_id"] == 999

@pytest.mark.asyncio
async def test_database_service_create_user(di_server):
    """Test database service - create new user"""
    async with httpx.AsyncClient() as client:
        new_user_data = {
            "name": "Test User",
            "email": "test@example.com"
        }

        response = await client.post(
            f"{di_server}/di/users",
            json=new_user_data
        )
        assert response.status_code == 201

        data = response.json()
        assert data["message"] == "User created successfully"
        assert "user" in data
        assert data["user"]["name"] == "Test User"
        assert data["user"]["email"] == "test@example.com"
        assert "id" in data["user"]
        assert data["service"] == "database"

@pytest.mark.asyncio
async def test_database_service_create_user_validation(di_server):
    """Test database service - create user validation"""
    async with httpx.AsyncClient() as client:
        # Missing name
        response = await client.post(
            f"{di_server}/di/users",
            json={"email": "test@example.com"}
        )
        assert response.status_code == 422  # Pydantic validation error

        # Missing email
        response = await client.post(
            f"{di_server}/di/users",
            json={"name": "Test User"}
        )
        assert response.status_code == 422  # Pydantic validation error

@pytest.mark.asyncio
async def test_greeting_service(di_server):
    """Test greeting service functionality"""
    async with httpx.AsyncClient() as client:
        # Test greeting
        response = await client.get(f"{di_server}/di/greet/Alice")
        assert response.status_code == 200

        data = response.json()
        assert "greeting" in data
        assert "Alice" in data["greeting"]
        assert "Catzilla DI testing" in data["greeting"]
        assert data["name"] == "Alice"
        assert data["service"] == "greeting"

        # Test farewell
        response = await client.get(f"{di_server}/di/farewell/Bob")
        assert response.status_code == 200

        data = response.json()
        assert "farewell" in data
        assert "Bob" in data["farewell"]
        assert "Goodbye" in data["farewell"]
        assert data["name"] == "Bob"
        assert data["service"] == "greeting"

@pytest.mark.asyncio
async def test_email_service(di_server):
    """Test email service functionality"""
    async with httpx.AsyncClient() as client:
        # Send email
        email_data = {
            "to": "test@example.com",
            "subject": "Test Email",
            "body": "This is a test email message."
        }

        response = await client.post(
            f"{di_server}/di/send-email",
            json=email_data
        )
        assert response.status_code == 201

        data = response.json()
        assert data["message"] == "Email sent successfully"
        assert "email" in data
        assert data["email"]["to"] == "test@example.com"
        assert data["email"]["subject"] == "Test Email"
        assert data["service"] == "email"

        # Get sent emails
        response = await client.get(f"{di_server}/di/emails")
        assert response.status_code == 200

        data = response.json()
        assert "emails" in data
        assert data["count"] >= 1
        assert data["service"] == "email"

@pytest.mark.asyncio
async def test_email_service_validation(di_server):
    """Test email service validation"""
    async with httpx.AsyncClient() as client:
        # Missing fields
        response = await client.post(
            f"{di_server}/di/send-email",
            json={"to": "test@example.com"}
        )
        assert response.status_code == 422  # Pydantic validation error

@pytest.mark.asyncio
async def test_services_status(di_server):
    """Test services status endpoint"""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{di_server}/di/services")
        assert response.status_code == 200

        data = response.json()
        assert "services" in data
        assert data["total_services"] == 3

        services = data["services"]
        assert "database" in services
        assert "greeting" in services
        assert "email" in services

        # Check service structure
        for service_name, service_data in services.items():
            assert service_data["status"] == "active"
            assert "created_at" in service_data

@pytest.mark.asyncio
async def test_multi_service_interaction(di_server):
    """Test interaction between multiple services"""
    async with httpx.AsyncClient() as client:
        welcome_data = {
            "name": "Multi Service User",
            "email": "multi@example.com"
        }

        response = await client.post(
            f"{di_server}/di/welcome-user",
            json=welcome_data
        )
        assert response.status_code == 201

        data = response.json()
        assert data["message"] == "User welcomed successfully"
        assert "user" in data
        assert "greeting" in data
        assert "email_sent" in data
        assert data["services_used"] == ["database", "greeting", "email"]

        # Verify user was created
        user = data["user"]
        assert user["name"] == "Multi Service User"
        assert user["email"] == "multi@example.com"

        # Verify greeting was generated
        greeting = data["greeting"]
        assert "Multi Service User" in greeting

        # Verify email was sent
        email_sent = data["email_sent"]
        assert email_sent["to"] == "multi@example.com"
        assert email_sent["subject"] == "Welcome to Catzilla!"

@pytest.mark.asyncio
async def test_concurrent_service_requests(di_server):
    """Test concurrent requests to different services"""
    async with httpx.AsyncClient() as client:
        # Create multiple tasks for different services
        tasks = []

        # Database tasks
        tasks.append(client.get(f"{di_server}/di/users"))
        tasks.append(client.get(f"{di_server}/di/users/1"))

        # Greeting tasks
        tasks.append(client.get(f"{di_server}/di/greet/User1"))
        tasks.append(client.get(f"{di_server}/di/greet/User2"))

        # Email tasks
        tasks.append(client.get(f"{di_server}/di/emails"))

        # Services status
        tasks.append(client.get(f"{di_server}/di/services"))

        # Execute concurrently
        responses = await asyncio.gather(*tasks)

        # All should succeed
        for response in responses:
            assert response.status_code == 200

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
