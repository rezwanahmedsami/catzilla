#!/usr/bin/env python3
"""
Simple Feature Endpoint Tester

Tests all feature endpoints across all frameworks to ensure they're working correctly.
This is a simple validation script before running the full benchmarks.
"""

import requests
import json
import time
import sys
from typing import Dict, List, Tuple

# Framework configurations
FRAMEWORKS = {
    "catzilla": {"base_url": "http://127.0.0.1:8000", "port": 8000},
    "fastapi": {"base_url": "http://127.0.0.1:8001", "port": 8001},
    "flask": {"base_url": "http://127.0.0.1:8002", "port": 8002},
    "django": {"base_url": "http://127.0.0.1:8003", "port": 8003}
}

# Test endpoints (method, endpoint, data)
TEST_ENDPOINTS = [
    # Basic endpoints
    ("GET", "/", None),
    ("GET", "/health", None),

    # Feature endpoints - Routing
    ("GET", "/bench/routing/static", None),
    ("GET", "/bench/routing/path/123", None),
    ("GET", "/bench/routing/path/electronics/456", None),
    ("GET", "/bench/routing/query?limit=10&offset=0&sort=name", None),

    # Feature endpoints - Validation
    ("POST", "/bench/validation/simple", {
        "id": 42,
        "name": "Alice Johnson",
        "email": "alice@example.com",
        "age": 28,
        "is_active": True
    }),
    ("POST", "/bench/validation/complex", {
        "id": 42,
        "name": "Alice Johnson",
        "email": "alice@example.com",
        "age": 28,
        "is_active": True,
        "tags": ["developer", "python"],
        "metadata": {"team": "backend"}
    }),
    ("POST", "/bench/validation/product", {
        "name": "Test Product",
        "price": 99.99,
        "category": "electronics",
        "description": "A test product",
        "in_stock": True
    }),
    ("GET", "/bench/validation/query?query=test&limit=10&offset=0&sort_by=created_at", None),

    # Feature endpoints - Dependency Injection
    ("GET", "/bench/di/simple", None),
    ("GET", "/bench/di/nested/123", None),

    # Feature endpoints - Background Tasks
    ("POST", "/bench/background/simple", {}),
    ("GET", "/bench/background/stats", None),

    # Feature endpoints - File Upload
    ("POST", "/bench/upload/simple", {}),
    ("GET", "/bench/upload/stats", None),

    # Feature endpoints - Streaming
    ("GET", "/bench/streaming/json?count=10", None),
    ("GET", "/bench/streaming/csv?count=5", None),
]

def test_endpoint(framework: str, base_url: str, method: str, endpoint: str, data: dict = None) -> Tuple[bool, str, float]:
    """Test a single endpoint and return success status, response info, and response time"""
    url = f"{base_url}{endpoint}"

    try:
        start_time = time.time()

        if method == "GET":
            response = requests.get(url, timeout=5)
        elif method == "POST":
            response = requests.post(url, json=data, timeout=5)
        else:
            return False, f"Unsupported method: {method}", 0

        response_time = (time.time() - start_time) * 1000  # Convert to ms

        if response.status_code == 200:
            # Try to parse JSON response to check if it's valid
            try:
                response_json = response.json()
                framework_in_response = response_json.get("framework", "unknown")
                return True, f"✅ {response.status_code} - Framework: {framework_in_response}", response_time
            except:
                # Non-JSON response (like CSV)
                content_type = response.headers.get('content-type', 'unknown')
                return True, f"✅ {response.status_code} - Content-Type: {content_type}", response_time
        else:
            return False, f"❌ {response.status_code} - {response.text[:100]}", response_time

    except requests.exceptions.ConnectionError:
        return False, f"❌ Connection failed - Server not running?", 0
    except requests.exceptions.Timeout:
        return False, f"❌ Request timeout", 0
    except Exception as e:
        return False, f"❌ Error: {str(e)}", 0

def check_server_health(framework: str, base_url: str) -> bool:
    """Check if server is healthy"""
    try:
        response = requests.get(f"{base_url}/health", timeout=3)
        return response.status_code == 200
    except:
        return False

def main():
    """Run feature endpoint tests"""
    print("🧪 Feature Endpoint Tester")
    print("=" * 50)

    results = {}

    # Test each framework
    for framework, config in FRAMEWORKS.items():
        print(f"\n🔧 Testing {framework.upper()} framework at {config['base_url']}")
        print("-" * 40)

        # Check if server is running
        if not check_server_health(framework, config['base_url']):
            print(f"⚠️  {framework} server is not running. Start it with:")
            print(f"   python3 benchmarks/servers/{framework}_server.py --port {config['port']}")
            results[framework] = {"status": "not_running", "endpoints": {}}
            continue

        # Test each endpoint
        framework_results = {"status": "running", "endpoints": {}}
        successful_tests = 0
        total_tests = len(TEST_ENDPOINTS)

        for method, endpoint, data in TEST_ENDPOINTS:
            success, message, response_time = test_endpoint(framework, config['base_url'], method, endpoint, data)

            endpoint_key = f"{method} {endpoint.split('?')[0]}"  # Remove query params for key
            framework_results["endpoints"][endpoint_key] = {
                "success": success,
                "message": message,
                "response_time_ms": response_time
            }

            if success:
                successful_tests += 1
                print(f"  {endpoint_key}: {message} ({response_time:.1f}ms)")
            else:
                print(f"  {endpoint_key}: {message}")

        # Summary for this framework
        success_rate = (successful_tests / total_tests) * 100
        framework_results["success_rate"] = success_rate
        framework_results["successful_tests"] = successful_tests
        framework_results["total_tests"] = total_tests

        print(f"\n  📊 {framework} Summary: {successful_tests}/{total_tests} tests passed ({success_rate:.1f}%)")

        results[framework] = framework_results

    # Overall summary
    print("\n" + "=" * 50)
    print("📈 OVERALL SUMMARY")
    print("=" * 50)

    running_frameworks = 0
    total_frameworks = len(FRAMEWORKS)

    for framework, result in results.items():
        status = result["status"]
        if status == "running":
            running_frameworks += 1
            success_rate = result["success_rate"]
            if success_rate == 100:
                status_icon = "🟢"
            elif success_rate >= 80:
                status_icon = "🟡"
            else:
                status_icon = "🔴"
            print(f"{status_icon} {framework.upper()}: {result['successful_tests']}/{result['total_tests']} endpoints working ({success_rate:.1f}%)")
        else:
            print(f"⚫ {framework.upper()}: Server not running")

    print(f"\n🚀 {running_frameworks}/{total_frameworks} frameworks are running")

    if running_frameworks == total_frameworks:
        print("\n✅ All frameworks are ready for benchmarking!")
        print("   Run: ./benchmarks/run_all.sh")
    else:
        print("\n⚠️  Start all servers before running benchmarks")
        print("   Catzilla: python3 benchmarks/servers/catzilla_server.py --port 8000")
        print("   FastAPI:  python3 benchmarks/servers/fastapi_server.py --port 8001")
        print("   Flask:    python3 benchmarks/servers/flask_server.py --port 8002 --use-gunicorn")
        print("   Django:   python3 benchmarks/servers/django_server.py --port 8003")

if __name__ == "__main__":
    main()
