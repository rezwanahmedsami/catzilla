"""
Real E2E Tests for Validation Functionality

Tests actual HTTP requests against running Catzilla validation servers.
Mirrors examples/validation/ functionality with real server processes.
"""
import pytest
import pytest_asyncio
import httpx
import asyncio
from typing import Dict, Any

from tests.e2e.utils.server_manager import get_server_manager

# Test configuration
VALIDATION_SERVER_PORT = 8101
VALIDATION_SERVER_HOST = "127.0.0.1"

@pytest_asyncio.fixture(scope="module")
async def validation_server():
    """Start validation server for testing"""
    server_manager = get_server_manager()

    # Start the validation server
    success = await server_manager.start_server("validation", VALIDATION_SERVER_PORT, VALIDATION_SERVER_HOST)
    if not success:
        pytest.fail("Failed to start validation test server")

    yield server_manager.get_server_url("validation")

    # Cleanup
    await server_manager.stop_server("validation")

@pytest_asyncio.fixture
async def http_client():
    """HTTP client for making requests"""
    async with httpx.AsyncClient(timeout=10.0) as client:
        yield client

class TestE2EValidation:
    """Real E2E tests for validation functionality"""

    @pytest.mark.asyncio
    async def test_server_health_check(self, validation_server, http_client):
        """Test validation server health endpoint"""
        response = await http_client.get(f"{validation_server}/health")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "healthy"
        assert data["server"] == "validation_e2e_test"
        assert "timestamp" in data

    @pytest.mark.asyncio
    async def test_validation_server_info(self, validation_server, http_client):
        """Test validation server info endpoint"""
        response = await http_client.get(f"{validation_server}/")
        assert response.status_code == 200

        data = response.json()
        assert "Catzilla E2E Validation Test Server" in data["message"]
        assert "Model validation" in data["features"]
        assert "Field constraints" in data["features"]
        assert "Nested models" in data["features"]
        assert len(data["endpoints"]) >= 5

    @pytest.mark.asyncio
    async def test_simple_validation_success(self, validation_server, http_client):
        """Test simple model validation with valid data"""
        user_data = {
            "name": "John Doe",
            "email": "john.doe@example.com"
        }

        response = await http_client.post(
            f"{validation_server}/validation/simple",
            json=user_data
        )
        assert response.status_code == 201

        data = response.json()
        assert data["message"] == "Simple validation passed"
        assert data["validation"] == "success"
        assert data["user"]["name"] == user_data["name"]
        assert data["user"]["email"] == user_data["email"]

    @pytest.mark.asyncio
    async def test_simple_validation_failure(self, validation_server, http_client):
        """Test simple model validation with invalid data"""
        # Test name too short
        invalid_data = {
            "name": "J",  # Too short (min_length=2)
            "email": "john.doe@example.com"
        }

        response = await http_client.post(
            f"{validation_server}/validation/simple",
            json=invalid_data
        )
        assert response.status_code in [400, 422]  # Validation error

        # Test invalid email
        invalid_data = {
            "name": "John Doe",
            "email": "invalid-email"  # Invalid email format
        }

        response = await http_client.post(
            f"{validation_server}/validation/simple",
            json=invalid_data
        )
        assert response.status_code in [400, 422]  # Validation error

    @pytest.mark.asyncio
    async def test_complex_user_validation_success(self, validation_server, http_client):
        """Test complex user validation with valid data"""
        user_data = {
            "id": 12345,
            "username": "john_doe123",
            "email": "john.doe@example.com",
            "age": 25,
            "is_active": True,
            "bio": "Software developer passionate about Python"
        }

        response = await http_client.post(
            f"{validation_server}/validation/user",
            json=user_data
        )
        assert response.status_code == 201

        data = response.json()
        assert data["message"] == "User validation passed"
        assert data["validation"] == "success"
        assert data["user"]["id"] == user_data["id"]
        assert data["user"]["username"] == user_data["username"]
        assert data["user"]["email"] == user_data["email"]
        assert data["user"]["age"] == user_data["age"]
        assert data["user"]["is_active"] == user_data["is_active"]
        assert data["user"]["bio"] == user_data["bio"]

    @pytest.mark.asyncio
    async def test_complex_user_validation_failures(self, validation_server, http_client):
        """Test complex user validation with various invalid data"""
        # Test invalid ID (too low)
        invalid_data = {
            "id": 0,  # Below minimum (ge=1)
            "username": "john_doe",
            "email": "john@example.com",
            "age": 25
        }

        response = await http_client.post(
            f"{validation_server}/validation/user",
            json=invalid_data
        )
        assert response.status_code in [400, 422]

        # Test invalid username (special characters)
        invalid_data = {
            "id": 123,
            "username": "john@doe!",  # Invalid characters
            "email": "john@example.com",
            "age": 25
        }

        response = await http_client.post(
            f"{validation_server}/validation/user",
            json=invalid_data
        )
        assert response.status_code in [400, 422]

        # Test invalid age (too young)
        invalid_data = {
            "id": 123,
            "username": "john_doe",
            "email": "john@example.com",
            "age": 10  # Below minimum (ge=13)
        }

        response = await http_client.post(
            f"{validation_server}/validation/user",
            json=invalid_data
        )
        assert response.status_code in [400, 422]

    @pytest.mark.asyncio
    async def test_nested_model_validation_success(self, validation_server, http_client):
        """Test nested model validation with valid data"""
        user_data = {
            "name": "Jane Smith",
            "email": "jane.smith@example.com",
            "address": {
                "street": "123 Main Street",
                "city": "Anytown",
                "zipcode": "12345"
            }
        }

        response = await http_client.post(
            f"{validation_server}/validation/nested",
            json=user_data
        )
        assert response.status_code == 201

        data = response.json()
        assert data["message"] == "Nested validation passed"
        assert data["validation"] == "success"
        assert data["user"]["name"] == user_data["name"]
        assert data["user"]["email"] == user_data["email"]
        assert data["user"]["address"]["street"] == user_data["address"]["street"]
        assert data["user"]["address"]["city"] == user_data["address"]["city"]
        assert data["user"]["address"]["zipcode"] == user_data["address"]["zipcode"]

    @pytest.mark.asyncio
    async def test_nested_model_validation_failure(self, validation_server, http_client):
        """Test nested model validation with invalid data"""
        # Test invalid zipcode format
        invalid_data = {
            "name": "Jane Smith",
            "email": "jane.smith@example.com",
            "address": {
                "street": "123 Main Street",
                "city": "Anytown",
                "zipcode": "invalid"  # Invalid zipcode format
            }
        }

        response = await http_client.post(
            f"{validation_server}/validation/nested",
            json=invalid_data
        )
        assert response.status_code in [400, 422]

        # Test street too short
        invalid_data = {
            "name": "Jane Smith",
            "email": "jane.smith@example.com",
            "address": {
                "street": "123",  # Too short (min_length=5)
                "city": "Anytown",
                "zipcode": "12345"
            }
        }

        response = await http_client.post(
            f"{validation_server}/validation/nested",
            json=invalid_data
        )
        assert response.status_code in [400, 422]

    @pytest.mark.asyncio
    async def test_array_validation_success(self, validation_server, http_client):
        """Test array validation with valid data"""
        product_data = {
            "products": ["laptop", "mouse", "keyboard"],
            "category": "electronics"
        }

        response = await http_client.post(
            f"{validation_server}/validation/array",
            json=product_data
        )
        assert response.status_code == 201

        data = response.json()
        assert data["message"] == "Array validation passed"
        assert data["validation"] == "success"
        assert data["data"]["products"] == product_data["products"]
        assert data["data"]["category"] == product_data["category"]
        assert data["data"]["count"] == len(product_data["products"])

    @pytest.mark.asyncio
    async def test_array_validation_failure(self, validation_server, http_client):
        """Test array validation with invalid data"""
        # Test empty array (min_items=1)
        invalid_data = {
            "products": [],  # Empty array
            "category": "electronics"
        }

        response = await http_client.post(
            f"{validation_server}/validation/array",
            json=invalid_data
        )
        assert response.status_code in [400, 422]

        # Test too many items (max_items=10)
        invalid_data = {
            "products": [f"product{i}" for i in range(15)],  # Too many items
            "category": "electronics"
        }

        response = await http_client.post(
            f"{validation_server}/validation/array",
            json=invalid_data
        )
        assert response.status_code in [400, 422]

    @pytest.mark.asyncio
    async def test_query_parameter_validation_success(self, validation_server, http_client):
        """Test query parameter validation with valid data"""
        response = await http_client.get(
            f"{validation_server}/validation/query?name=JohnDoe&age=25&active=true"
        )
        assert response.status_code == 200

        data = response.json()
        assert data["message"] == "Query validation passed"
        assert data["validation"] == "success"
        assert data["query_params"]["name"] == "JohnDoe"
        assert data["query_params"]["age"] == 25
        assert data["query_params"]["active"] == True

    @pytest.mark.asyncio
    async def test_query_parameter_validation_failure(self, validation_server, http_client):
        """Test query parameter validation with invalid data"""
        # Test name too short
        response = await http_client.get(
            f"{validation_server}/validation/query?name=J&age=25"  # Name too short
        )
        assert response.status_code in [400, 422]

        # Test age out of range
        response = await http_client.get(
            f"{validation_server}/validation/query?name=John&age=200"  # Age too high
        )
        assert response.status_code in [400, 422]

    @pytest.mark.asyncio
    async def test_validation_comprehensive_workflow(self, validation_server, http_client):
        """Test comprehensive validation workflow"""
        # 1. Test simple validation
        simple_user = {"name": "Alice", "email": "alice@example.com"}
        response = await http_client.post(f"{validation_server}/validation/simple", json=simple_user)
        assert response.status_code == 201

        # 2. Test complex validation
        complex_user = {
            "id": 999,
            "username": "alice_dev",
            "email": "alice@example.com",
            "age": 30,
            "bio": "Full stack developer"
        }
        response = await http_client.post(f"{validation_server}/validation/user", json=complex_user)
        assert response.status_code == 201

        # 3. Test nested validation
        nested_user = {
            "name": "Alice Cooper",
            "email": "alice.cooper@example.com",
            "address": {
                "street": "456 Oak Avenue",
                "city": "Springfield",
                "zipcode": "67890"
            }
        }
        response = await http_client.post(f"{validation_server}/validation/nested", json=nested_user)
        assert response.status_code == 201

        # 4. Test array validation
        products = {
            "products": ["phone", "tablet", "headphones"],
            "category": "electronics"
        }
        response = await http_client.post(f"{validation_server}/validation/array", json=products)
        assert response.status_code == 201

        # 5. Test query validation
        response = await http_client.get(f"{validation_server}/validation/query?name=Alice&age=30&active=true")
        assert response.status_code == 200
