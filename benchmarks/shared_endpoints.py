#!/usr/bin/env python3
"""
Shared endpoint definitions for consistent benchmarking across frameworks.

This module defines the same endpoints that each framework server will implement
to ensure fair performance comparisons.
"""

import json
import time
from typing import Dict, Any

# Test data for consistent responses
SAMPLE_USER = {
    "id": 123,
    "name": "John Doe",
    "email": "john@example.com",
    "active": True,
    "created_at": "2024-01-01T00:00:00Z"
}

SAMPLE_USERS = [
    {"id": i, "name": f"User {i}", "email": f"user{i}@example.com"}
    for i in range(1, 101)
]

def get_benchmark_endpoints():
    """
    Returns a dictionary of endpoint definitions for benchmarking.
    Each endpoint tests different aspects of framework performance.
    """
    return {
        # Simple static response - tests basic request handling
        "hello_world": {
            "method": "GET",
            "path": "/",
            "description": "Simple hello world response",
            "response": "Hello, World!",
            "content_type": "text/plain"
        },

        # JSON serialization test
        "json_response": {
            "method": "GET",
            "path": "/json",
            "description": "JSON serialization performance",
            "response": {"message": "Hello, World!", "timestamp": time.time()},
            "content_type": "application/json"
        },

        # Path parameter extraction
        "user_by_id": {
            "method": "GET",
            "path": "/user/{id}",
            "description": "Path parameter extraction and JSON response",
            "response_template": lambda user_id: {
                "user_id": int(user_id),
                "name": f"User {user_id}",
                "email": f"user{user_id}@example.com",
                "profile_url": f"/user/{user_id}/profile"
            },
            "content_type": "application/json"
        },

        # JSON body parsing and echo
        "echo_json": {
            "method": "POST",
            "path": "/echo",
            "description": "JSON request parsing and echo response",
            "response_template": lambda data: {
                "echo": data,
                "received_at": time.time(),
                "size": len(json.dumps(data))
            },
            "content_type": "application/json"
        },

        # Query parameter handling
        "search_users": {
            "method": "GET",
            "path": "/users",
            "description": "Query parameter handling and filtering",
            "response_template": lambda limit=10, offset=0: {
                "users": SAMPLE_USERS[int(offset):int(offset)+int(limit)],
                "total": len(SAMPLE_USERS),
                "limit": int(limit),
                "offset": int(offset)
            },
            "content_type": "application/json"
        },

        # Complex JSON response
        "user_profile": {
            "method": "GET",
            "path": "/user/{id}/profile",
            "description": "Complex JSON response with nested data",
            "response_template": lambda user_id: {
                "user": {
                    "id": int(user_id),
                    "name": f"User {user_id}",
                    "email": f"user{user_id}@example.com",
                    "profile": {
                        "bio": f"This is user {user_id}'s biography",
                        "location": "San Francisco, CA",
                        "website": f"https://user{user_id}.example.com",
                        "social": {
                            "twitter": f"@user{user_id}",
                            "github": f"user{user_id}",
                            "linkedin": f"user{user_id}"
                        }
                    },
                    "stats": {
                        "posts": int(user_id) * 3,
                        "followers": int(user_id) * 10,
                        "following": int(user_id) * 5
                    }
                },
                "generated_at": time.time()
            },
            "content_type": "application/json"
        }
    }

def get_test_requests():
    """
    Returns a list of test requests for benchmarking.
    Each request targets a specific endpoint to test different performance aspects.
    """
    return [
        {
            "name": "hello_world",
            "method": "GET",
            "url": "/",
            "description": "Basic request handling"
        },
        {
            "name": "json_simple",
            "method": "GET",
            "url": "/json",
            "description": "JSON serialization"
        },
        {
            "name": "path_params",
            "method": "GET",
            "url": "/user/42",
            "description": "Path parameter extraction"
        },
        {
            "name": "json_echo",
            "method": "POST",
            "url": "/echo",
            "body": {"test": "data", "number": 42, "array": [1, 2, 3]},
            "description": "JSON request parsing"
        },
        {
            "name": "query_params",
            "method": "GET",
            "url": "/users?limit=20&offset=10",
            "description": "Query parameter handling"
        },
        {
            "name": "complex_json",
            "method": "GET",
            "url": "/user/123/profile",
            "description": "Complex JSON response"
        }
    ]

# Default test payload for POST requests
DEFAULT_JSON_PAYLOAD = {
    "message": "Hello from benchmark",
    "timestamp": time.time(),
    "data": {
        "nested": True,
        "values": [1, 2, 3, 4, 5],
        "metadata": {
            "framework": "test",
            "version": "1.0.0"
        }
    }
}

if __name__ == "__main__":
    print("Benchmark Endpoints Configuration")
    print("=" * 50)

    endpoints = get_benchmark_endpoints()
    for name, config in endpoints.items():
        print(f"\n{name.upper()}:")
        print(f"  Method: {config['method']}")
        print(f"  Path: {config['path']}")
        print(f"  Description: {config['description']}")

    print(f"\nTotal endpoints: {len(endpoints)}")

    requests = get_test_requests()
    print(f"\nTest requests: {len(requests)}")
    for req in requests:
        print(f"  {req['name']}: {req['method']} {req['url']}")
