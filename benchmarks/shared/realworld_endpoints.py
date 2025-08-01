"""
Real-World Scenarios Benchmark Endpoints

Shared endpoint definitions for real-world application scenarios across all frameworks.
Includes complete application workflows like e-commerce, blog/CMS, user management,
file processing, and analytics.

Features:
- E-commerce product catalog and ordering
- Blog/CMS content management
- User authentication and profile management
- File upload and processing workflows
- Real-time analytics and dashboard
- Background task integration
"""

import json
import random
import time
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Any, Optional


def get_realworld_endpoints() -> Dict[str, Any]:
    """Get real-world scenario endpoint definitions"""
    return {
        "ecommerce": {
            "description": "E-commerce application scenarios",
            "endpoints": [
                {
                    "path": "/api/products",
                    "method": "GET",
                    "params": {
                        "page": [1, 2, 3],
                        "limit": [20, 50],
                        "category_id": [1, 2, 3, None],
                        "search": ["laptop", "phone", "book", None],
                        "sort_by": ["name", "price", "created_at", "popularity"],
                        "sort_order": ["asc", "desc"]
                    },
                    "weight": 3
                },
                {
                    "path": "/api/products/{product_id}",
                    "method": "GET",
                    "params": {
                        "product_id": list(range(1, 21))
                    },
                    "headers": {
                        "X-User-ID": [1, 2, 3, None]
                    },
                    "weight": 2
                },
                {
                    "path": "/api/orders",
                    "method": "POST",
                    "headers": {
                        "X-User-ID": [1, 2, 3, 4, 5],
                        "Content-Type": "application/json"
                    },
                    "body_generator": "generate_order_data",
                    "weight": 1
                }
            ]
        },
        "blog": {
            "description": "Blog/CMS scenarios",
            "endpoints": [
                {
                    "path": "/api/blog/posts",
                    "method": "GET",
                    "params": {
                        "page": [1, 2, 3],
                        "limit": [10, 20],
                        "status": ["published"],
                        "tag": ["tech", "business", "lifestyle", None],
                        "search": ["tutorial", "guide", "news", None]
                    },
                    "weight": 2
                },
                {
                    "path": "/api/blog/posts/{post_id}",
                    "method": "GET",
                    "params": {
                        "post_id": list(range(1, 11))
                    },
                    "weight": 2
                }
            ]
        },
        "analytics": {
            "description": "Analytics and tracking scenarios",
            "endpoints": [
                {
                    "path": "/api/analytics/dashboard",
                    "method": "GET",
                    "headers": {
                        "X-User-ID": [1]  # Admin only
                    },
                    "params": {
                        "date_from": [None, "2024-01-01"],
                        "date_to": [None, "2024-12-31"]
                    },
                    "weight": 1
                },
                {
                    "path": "/api/analytics/track",
                    "method": "POST",
                    "headers": {
                        "Content-Type": "application/json"
                    },
                    "body_generator": "generate_analytics_event",
                    "weight": 3
                }
            ]
        },
        "file_upload": {
            "description": "File upload scenarios",
            "endpoints": [
                {
                    "path": "/api/upload/product-image",
                    "method": "POST",
                    "headers": {
                        "X-User-ID": [1],  # Admin only
                        "Content-Type": "multipart/form-data"
                    },
                    "body_generator": "generate_file_upload_data",
                    "weight": 1
                }
            ]
        },
        "health": {
            "description": "Health check endpoint",
            "endpoints": [
                {
                    "path": "/health",
                    "method": "GET",
                    "weight": 1
                }
            ]
        }
    }


def generate_order_data() -> Dict[str, Any]:
    """Generate realistic order data for testing"""
    items = []
    num_items = random.randint(1, 5)

    for _ in range(num_items):
        items.append({
            "product_id": random.randint(1, 20),
            "quantity": random.randint(1, 3)
        })

    return {
        "user_id": random.randint(1, 5),
        "status": "pending",
        "total_amount": round(random.uniform(25.0, 500.0), 2),
        "shipping_address": {
            "street": f"{random.randint(100, 9999)} Main St",
            "city": random.choice(["New York", "Los Angeles", "Chicago", "Houston", "Phoenix"]),
            "state": random.choice(["NY", "CA", "IL", "TX", "AZ"]),
            "zip_code": f"{random.randint(10000, 99999)}",
            "country": "USA"
        },
        "billing_address": {
            "street": f"{random.randint(100, 9999)} Oak Ave",
            "city": random.choice(["Boston", "Seattle", "Denver", "Atlanta", "Miami"]),
            "state": random.choice(["MA", "WA", "CO", "GA", "FL"]),
            "zip_code": f"{random.randint(10000, 99999)}",
            "country": "USA"
        },
        "items": items,
        "payment_method": random.choice(["credit_card", "paypal", "bank_transfer"])
    }


def generate_analytics_event() -> Dict[str, Any]:
    """Generate analytics event data for testing"""
    event_types = ["page_view", "click", "purchase", "signup", "login"]
    pages = ["/", "/products", "/blog", "/about", "/contact", "/checkout"]

    return {
        "event_type": random.choice(event_types),
        "user_id": random.choice([None, 1, 2, 3, 4, 5]),
        "session_id": f"session_{random.randint(1000, 9999)}",
        "page_url": f"https://example.com{random.choice(pages)}",
        "referrer": random.choice([None, "https://google.com", "https://facebook.com"]),
        "user_agent": "Mozilla/5.0 (compatible; benchmark)",
        "ip_address": f"{random.randint(1, 255)}.{random.randint(1, 255)}.{random.randint(1, 255)}.{random.randint(1, 255)}",
        "properties": {
            "test_scenario": "real_world_benchmark",
            "timestamp": datetime.now().isoformat()
        }
    }


def generate_file_upload_data() -> Dict[str, Any]:
    """Generate file upload data for testing"""
    # This would typically be multipart form data
    # For benchmark purposes, we'll simulate the form fields
    return {
        "product_id": random.randint(1, 20),
        "alt_text": f"Product image {random.randint(1, 100)}",
        "file_info": {
            "filename": f"product_image_{random.randint(1, 1000)}.jpg",
            "content_type": "image/jpeg",
            "size": random.randint(50000, 2000000)  # 50KB to 2MB
        }
    }


def generate_blog_post_data() -> Dict[str, Any]:
    """Generate blog post data for testing"""
    titles = [
        "10 Tips for Better Web Performance",
        "Understanding Modern JavaScript Frameworks",
        "The Future of E-commerce Technology",
        "Building Scalable APIs with Python",
        "Database Optimization Strategies"
    ]

    tags = ["tech", "programming", "web-development", "performance", "tutorial"]

    return {
        "title": random.choice(titles),
        "slug": f"blog-post-{random.randint(1, 1000)}",
        "content": "This is a comprehensive blog post about technology. " * 50,
        "excerpt": "A brief excerpt of the blog post content.",
        "author_id": random.randint(1, 3),
        "status": "published",
        "tags": random.sample(tags, random.randint(1, 3)),
        "meta_description": "SEO-optimized meta description for the blog post."
    }


def generate_user_data() -> Dict[str, Any]:
    """Generate user registration data for testing"""
    usernames = ["techguru", "webdev", "designer", "analyst", "manager"]
    domains = ["gmail.com", "yahoo.com", "hotmail.com", "company.com"]
    first_names = ["John", "Jane", "Mike", "Sarah", "David", "Lisa"]
    last_names = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia"]

    username = f"{random.choice(usernames)}{random.randint(1, 999)}"
    first_name = random.choice(first_names)
    last_name = random.choice(last_names)

    return {
        "username": username,
        "email": f"{username}@{random.choice(domains)}",
        "first_name": first_name,
        "last_name": last_name,
        "is_active": True,
        "is_admin": False
    }


def generate_complex_search_data() -> Dict[str, Any]:
    """Generate complex search parameters for testing"""
    return {
        "query": random.choice([
            "laptop computer",
            "smartphone android",
            "running shoes nike",
            "coffee maker black",
            "wireless headphones"
        ]),
        "filters": {
            "category_id": random.choice([1, 2, 3, 4, 5, None]),
            "min_price": random.choice([None, 10, 50, 100]),
            "max_price": random.choice([None, 200, 500, 1000]),
            "brand": random.choice([None, "Brand1", "Brand2", "Brand3"]),
            "in_stock": random.choice([True, False, None])
        },
        "sort": {
            "field": random.choice(["price", "name", "created_at", "popularity"]),
            "order": random.choice(["asc", "desc"])
        },
        "pagination": {
            "page": random.randint(1, 5),
            "limit": random.choice([10, 20, 50])
        }
    }


def get_performance_test_scenarios() -> List[Dict[str, Any]]:
    """Get predefined performance test scenarios"""
    return [
        {
            "name": "product_browsing",
            "description": "Heavy product browsing with filtering and search",
            "duration": 30,
            "endpoints": [
                {"path": "/api/products", "weight": 5},
                {"path": "/api/products/{product_id}", "weight": 3}
            ]
        },
        {
            "name": "order_processing",
            "description": "Order creation and processing workflow",
            "duration": 30,
            "endpoints": [
                {"path": "/api/products", "weight": 2},
                {"path": "/api/products/{product_id}", "weight": 2},
                {"path": "/api/orders", "weight": 1}
            ]
        },
        {
            "name": "content_consumption",
            "description": "Blog content reading and interaction",
            "duration": 30,
            "endpoints": [
                {"path": "/api/blog/posts", "weight": 3},
                {"path": "/api/blog/posts/{post_id}", "weight": 2}
            ]
        },
        {
            "name": "analytics_heavy",
            "description": "Analytics tracking and dashboard access",
            "duration": 30,
            "endpoints": [
                {"path": "/api/analytics/track", "weight": 5},
                {"path": "/api/analytics/dashboard", "weight": 1}
            ]
        },
        {
            "name": "mixed_workload",
            "description": "Mixed real-world usage patterns",
            "duration": 60,
            "endpoints": [
                {"path": "/api/products", "weight": 4},
                {"path": "/api/products/{product_id}", "weight": 3},
                {"path": "/api/blog/posts", "weight": 2},
                {"path": "/api/blog/posts/{post_id}", "weight": 2},
                {"path": "/api/orders", "weight": 1},
                {"path": "/api/analytics/track", "weight": 3}
            ]
        }
    ]


def get_stress_test_patterns() -> List[Dict[str, Any]]:
    """Get stress test patterns for real-world scenarios"""
    return [
        {
            "name": "flash_sale",
            "description": "Simulates flash sale traffic spike",
            "pattern": "burst",
            "duration": 120,
            "concurrency_levels": [10, 50, 100, 200, 100, 50, 10],
            "endpoints": [
                {"path": "/api/products", "weight": 3},
                {"path": "/api/products/{product_id}", "weight": 4},
                {"path": "/api/orders", "weight": 2}
            ]
        },
        {
            "name": "content_viral",
            "description": "Simulates viral content traffic",
            "pattern": "gradual_increase",
            "duration": 180,
            "concurrency_levels": [5, 20, 50, 100, 150, 200, 250],
            "endpoints": [
                {"path": "/api/blog/posts", "weight": 2},
                {"path": "/api/blog/posts/{post_id}", "weight": 5}
            ]
        },
        {
            "name": "sustained_load",
            "description": "Sustained high load throughout day",
            "pattern": "constant",
            "duration": 300,
            "concurrency_levels": [100],
            "endpoints": [
                {"path": "/api/products", "weight": 3},
                {"path": "/api/products/{product_id}", "weight": 2},
                {"path": "/api/blog/posts", "weight": 2},
                {"path": "/api/orders", "weight": 1},
                {"path": "/api/analytics/track", "weight": 4}
            ]
        }
    ]


# Endpoint-specific data generators
ENDPOINT_GENERATORS = {
    "generate_order_data": generate_order_data,
    "generate_analytics_event": generate_analytics_event,
    "generate_file_upload_data": generate_file_upload_data,
    "generate_blog_post_data": generate_blog_post_data,
    "generate_user_data": generate_user_data,
    "generate_complex_search_data": generate_complex_search_data
}


def get_endpoint_generator(name: str):
    """Get data generator function by name"""
    return ENDPOINT_GENERATORS.get(name)


if __name__ == "__main__":
    # Test the endpoint definitions
    endpoints = get_realworld_endpoints()
    print("Real-world scenario endpoints:")
    for category, data in endpoints.items():
        print(f"\n{category.upper()}:")
        print(f"  Description: {data['description']}")
        for endpoint in data['endpoints']:
            print(f"  {endpoint['method']} {endpoint['path']} (weight: {endpoint['weight']})")

    print("\nSample data generators:")
    print("Order data:", json.dumps(generate_order_data(), indent=2, default=str))
    print("Analytics event:", json.dumps(generate_analytics_event(), indent=2, default=str))
