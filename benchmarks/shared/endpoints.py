#!/usr/bin/env python3
"""
Feature-Based Benchmark Endpoint Definitions

This module defines benchmark endpoints organized by feature categories.
Each category tests specific framework capabilities for fair performance comparisons.
"""

import json
import time
from typing import Dict, Any, List
from datetime import datetime

# ============================================================================
# SHARED TEST DATA
# ============================================================================

SAMPLE_USER = {
    "id": 123,
    "name": "John Doe",
    "email": "john@example.com",
    "active": True,
    "created_at": "2024-01-01T00:00:00Z"
}

SAMPLE_USERS = [
    {"id": i, "name": f"User {i}", "email": f"user{i}@example.com", "age": 25 + (i % 40)}
    for i in range(1, 101)
]

SAMPLE_POSTS = [
    {"id": i, "title": f"Post {i}", "content": f"Content for post {i}", "author_id": (i % 10) + 1}
    for i in range(1, 201)
]

SAMPLE_PRODUCTS = [
    {
        "id": i,
        "name": f"Product {i}",
        "price": 10.00 + (i * 5.99),
        "category": "electronics" if i % 2 == 0 else "books",
        "in_stock": i % 3 != 0
    }
    for i in range(1, 51)
]

# ============================================================================
# BASIC ENDPOINTS (Compatible with old system)
# ============================================================================

def get_basic_endpoints():
    """Basic HTTP benchmark endpoints (maintains compatibility with old system)"""
    return {
        "hello_world": {
            "method": "GET",
            "path": "/",
            "description": "Simple hello world response",
            "response": "Hello, World!",
            "content_type": "text/plain"
        },

        "json_response": {
            "method": "GET",
            "path": "/json",
            "description": "JSON serialization performance",
            "response": {"message": "Hello, World!", "timestamp": time.time()},
            "content_type": "application/json"
        },

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

# ============================================================================
# MIDDLEWARE BENCHMARK ENDPOINTS
# ============================================================================

def get_middleware_endpoints():
    """Middleware performance benchmark endpoints"""
    return {
        "auth_protected": {
            "method": "GET",
            "path": "/auth/protected",
            "description": "Endpoint protected by authentication middleware",
            "middleware": ["auth"],
            "response_template": lambda user_data: {
                "message": "Access granted",
                "user": user_data,
                "timestamp": time.time(),
                "middleware_applied": ["authentication"]
            }
        },

        "rate_limited": {
            "method": "GET",
            "path": "/rate-limited",
            "description": "Endpoint with rate limiting middleware",
            "middleware": ["rate_limit"],
            "response_template": lambda remaining: {
                "message": "Request processed",
                "rate_limit": {
                    "remaining": remaining,
                    "reset_time": time.time() + 3600
                },
                "timestamp": time.time()
            }
        },

        "multi_middleware": {
            "method": "POST",
            "path": "/admin/action",
            "description": "Endpoint with multiple middleware layers",
            "middleware": ["auth", "rate_limit", "admin"],
            "response_template": lambda user_data, rate_info: {
                "message": "Admin action completed",
                "user": user_data,
                "rate_limit": rate_info,
                "middleware_chain": ["auth", "rate_limit", "admin"],
                "timestamp": time.time()
            }
        },

        "cors_preflight": {
            "method": "OPTIONS",
            "path": "/api/cors",
            "description": "CORS preflight handling",
            "middleware": ["cors"],
            "response_template": lambda: {
                "cors_headers": {
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Methods": "GET,POST,PUT,DELETE",
                    "Access-Control-Allow-Headers": "Content-Type,Authorization"
                }
            }
        }
    }

# ============================================================================
# DEPENDENCY INJECTION BENCHMARK ENDPOINTS
# ============================================================================

def get_dependency_injection_endpoints():
    """Dependency injection performance benchmark endpoints"""
    return {
        "simple_injection": {
            "method": "GET",
            "path": "/di/simple",
            "description": "Simple service injection",
            "dependencies": ["user_service"],
            "response_template": lambda service_data: {
                "message": "Service injected successfully",
                "service": service_data,
                "injection_type": "simple",
                "timestamp": time.time()
            }
        },

        "nested_injection": {
            "method": "GET",
            "path": "/di/nested/{user_id}",
            "description": "Nested dependency injection with parameters",
            "dependencies": ["user_service", "post_service", "analytics_service"],
            "response_template": lambda user_id, user_data, posts, analytics: {
                "user_id": int(user_id),
                "user": user_data,
                "posts": posts,
                "analytics": analytics,
                "services_injected": 3,
                "timestamp": time.time()
            }
        },

        "scoped_services": {
            "method": "POST",
            "path": "/di/scoped",
            "description": "Request-scoped service injection",
            "dependencies": ["request_scoped_service", "singleton_service"],
            "response_template": lambda request_service, singleton_service: {
                "message": "Scoped services accessed",
                "request_service_id": request_service["id"],
                "singleton_service_id": singleton_service["id"],
                "scopes": ["request", "singleton"],
                "timestamp": time.time()
            }
        },

        "complex_graph": {
            "method": "GET",
            "path": "/di/complex",
            "description": "Complex dependency graph resolution",
            "dependencies": ["database_service", "cache_service", "notification_service", "analytics_service"],
            "response_template": lambda db, cache, notifications, analytics: {
                "message": "Complex dependency graph resolved",
                "services": {
                    "database": db,
                    "cache": cache,
                    "notifications": notifications,
                    "analytics": analytics
                },
                "resolution_depth": 4,
                "timestamp": time.time()
            }
        }
    }

# ============================================================================
# ASYNC OPERATIONS BENCHMARK ENDPOINTS
# ============================================================================

def get_async_endpoints():
    """Async operations benchmark endpoints"""
    return {
        "async_simple": {
            "method": "GET",
            "path": "/async/simple",
            "description": "Simple async endpoint",
            "async_ops": ["sleep_100ms"],
            "response_template": lambda: {
                "message": "Async operation completed",
                "operations": ["async_sleep"],
                "duration_ms": 100,
                "timestamp": time.time()
            }
        },

        "async_concurrent": {
            "method": "GET",
            "path": "/async/concurrent",
            "description": "Concurrent async operations",
            "async_ops": ["db_query", "api_call", "cache_lookup"],
            "response_template": lambda db_result, api_result, cache_result: {
                "message": "Concurrent operations completed",
                "results": {
                    "database": db_result,
                    "api": api_result,
                    "cache": cache_result
                },
                "concurrent_ops": 3,
                "timestamp": time.time()
            }
        },

        "async_database": {
            "method": "GET",
            "path": "/async/database/{user_id}",
            "description": "Async database operations",
            "async_ops": ["db_user_lookup", "db_posts_lookup", "db_relationships"],
            "response_template": lambda user_id, user, posts, relationships: {
                "user_id": int(user_id),
                "user": user,
                "posts": posts,
                "relationships": relationships,
                "db_queries": 3,
                "timestamp": time.time()
            }
        },

        "mixed_sync_async": {
            "method": "POST",
            "path": "/mixed/process",
            "description": "Mixed sync/async processing",
            "operations": ["sync_validation", "async_db_save", "sync_response"],
            "response_template": lambda validation_result, save_result: {
                "message": "Mixed processing completed",
                "validation": validation_result,
                "save_result": save_result,
                "processing_type": "hybrid",
                "timestamp": time.time()
            }
        }
    }

# ============================================================================
# DATABASE INTEGRATION BENCHMARK ENDPOINTS
# ============================================================================

def get_database_endpoints():
    """Database integration benchmark endpoints"""
    return {
        "db_user_crud": {
            "method": "GET",
            "path": "/db/users/{user_id}",
            "description": "Database user lookup with relationships",
            "db_ops": ["user_select", "posts_join", "comments_join"],
            "response_template": lambda user_id, user_with_relations: {
                "user": user_with_relations,
                "queries_executed": 1,  # optimized join
                "query_type": "left_join",
                "timestamp": time.time()
            }
        },

        "db_transaction": {
            "method": "POST",
            "path": "/db/transaction",
            "description": "Database transaction processing",
            "db_ops": ["begin_transaction", "insert_user", "insert_profile", "commit"],
            "response_template": lambda transaction_result: {
                "message": "Transaction completed",
                "result": transaction_result,
                "operations": ["create_user", "create_profile"],
                "transaction_id": f"txn_{int(time.time())}",
                "timestamp": time.time()
            }
        },

        "db_bulk_operations": {
            "method": "POST",
            "path": "/db/bulk",
            "description": "Bulk database operations",
            "db_ops": ["bulk_insert", "bulk_update"],
            "response_template": lambda inserted_count, updated_count: {
                "message": "Bulk operations completed",
                "inserted": inserted_count,
                "updated": updated_count,
                "total_operations": inserted_count + updated_count,
                "timestamp": time.time()
            }
        },

        "db_complex_query": {
            "method": "GET",
            "path": "/db/analytics",
            "description": "Complex analytical database query",
            "db_ops": ["aggregate_query", "subquery", "window_functions"],
            "response_template": lambda analytics_data: {
                "analytics": analytics_data,
                "query_complexity": "high",
                "aggregations": ["count", "sum", "avg"],
                "timestamp": time.time()
            }
        }
    }

# ============================================================================
# VALIDATION BENCHMARK ENDPOINTS
# ============================================================================

def get_validation_endpoints():
    """Auto-validation benchmark endpoints"""
    return {
        "simple_validation": {
            "method": "POST",
            "path": "/validate/simple",
            "description": "Simple model validation",
            "validation_fields": ["name", "email", "age"],
            "response_template": lambda validated_data: {
                "message": "Validation successful",
                "data": validated_data,
                "fields_validated": 3,
                "validation_engine": "auto",
                "timestamp": time.time()
            }
        },

        "complex_validation": {
            "method": "POST",
            "path": "/validate/complex",
            "description": "Complex nested model validation",
            "validation_fields": ["user", "profile", "preferences", "metadata"],
            "response_template": lambda validated_data: {
                "message": "Complex validation successful",
                "data": validated_data,
                "nested_objects": 3,
                "total_fields": 15,
                "validation_engine": "auto",
                "timestamp": time.time()
            }
        },

        "list_validation": {
            "method": "POST",
            "path": "/validate/list",
            "description": "List/array validation with constraints",
            "validation_fields": ["items", "metadata"],
            "response_template": lambda validated_data: {
                "message": "List validation successful",
                "data": validated_data,
                "list_items": len(validated_data.get("items", [])),
                "constraints_applied": ["min_items", "max_items", "item_type"],
                "timestamp": time.time()
            }
        },

        "custom_validators": {
            "method": "POST",
            "path": "/validate/custom",
            "description": "Custom validation rules",
            "validation_fields": ["email", "password", "phone"],
            "response_template": lambda validated_data: {
                "message": "Custom validation successful",
                "data": validated_data,
                "custom_rules": ["email_format", "password_strength", "phone_format"],
                "validation_engine": "auto",
                "timestamp": time.time()
            }
        }
    }

# ============================================================================
# UNIFIED ACCESS FUNCTIONS
# ============================================================================

def get_all_endpoints():
    """Get all benchmark endpoints organized by category"""
    return {
        "basic": get_basic_endpoints(),
        "middleware": get_middleware_endpoints(),
        "dependency_injection": get_dependency_injection_endpoints(),
        "async_operations": get_async_endpoints(),
        "database": get_database_endpoints(),
        "validation": get_validation_endpoints()
    }

def get_endpoints_by_category(category: str):
    """Get endpoints for a specific category"""
    all_endpoints = get_all_endpoints()
    return all_endpoints.get(category, {})

def get_benchmark_test_requests():
    """Get test requests for automated benchmarking (compatible with old system)"""
    basic_endpoints = get_basic_endpoints()

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

# Default test payload for POST requests (maintains compatibility)
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
    print("Feature-Based Benchmark Endpoints")
    print("=" * 50)

    all_endpoints = get_all_endpoints()
    for category, endpoints in all_endpoints.items():
        print(f"\n{category.upper()} CATEGORY:")
        for name, config in endpoints.items():
            print(f"  {name}: {config['method']} {config['path']}")

    print(f"\nTotal categories: {len(all_endpoints)}")
    total_endpoints = sum(len(endpoints) for endpoints in all_endpoints.values())
    print(f"Total endpoints: {total_endpoints}")
