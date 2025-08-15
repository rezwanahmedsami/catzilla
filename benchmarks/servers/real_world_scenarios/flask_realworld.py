#!/usr/bin/env python3
"""
Flask Real-World Scenarios Benchmark Server

Complete real-world application scenarios using Flask with all common features.
Demonstrates typical web application patterns for performance comparison.

Features:
- E-commerce product catalog and ordering
- Blog/CMS content management
- User authentication and profiles
- File upload and processing
- Real-time analytics tracking
- Background task processing
"""

import os
import sys
import json
import time
import argparse
import uuid
import hashlib
from typing import Optional, List, Dict, Any, Union
from datetime import datetime, timedelta
from decimal import Decimal
import random
import threading
from concurrent.futures import ThreadPoolExecutor

# Import shared real-world endpoints
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'shared'))
from realworld_endpoints import get_realworld_endpoints

try:
    from flask import Flask, request, jsonify, send_file
    from werkzeug.utils import secure_filename
    import gunicorn.app.base
except ImportError:
    print("❌ Flask/Gunicorn not installed. Install with: pip install flask gunicorn")
    sys.exit(1)

# Initialize Flask app
app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file upload

# Get real-world endpoints configuration
endpoints_config = get_realworld_endpoints()

# =====================================================
# IN-MEMORY DATA STORES (for benchmarking)
# =====================================================

# Products data
PRODUCTS = [
    {
        "id": i,
        "name": f"Product {i}",
        "description": f"High-quality product {i} with excellent features",
        "price": round(random.uniform(10.00, 999.99), 2),
        "category_id": random.randint(1, 5),
        "category_name": random.choice(["Electronics", "Books", "Clothing", "Home", "Sports"]),
        "sku": f"SKU-{i:06d}",
        "stock_quantity": random.randint(0, 100),
        "rating": round(random.uniform(3.5, 5.0), 1),
        "reviews_count": random.randint(0, 500),
        "created_at": (datetime.now() - timedelta(days=random.randint(1, 365))).isoformat(),
        "updated_at": datetime.now().isoformat(),
        "is_featured": random.choice([True, False]),
        "images": [f"/static/images/product_{i}_{j}.jpg" for j in range(1, 4)],
        "tags": random.sample(["popular", "sale", "new", "trending", "bestseller"], k=random.randint(1, 3))
    }
    for i in range(1, 101)
]

# Blog posts data
BLOG_POSTS = [
    {
        "id": i,
        "title": f"Blog Post {i}: {random.choice(['Tutorial', 'Guide', 'News', 'Review'])}",
        "slug": f"blog-post-{i}",
        "content": f"This is the content of blog post {i}. " * 50,  # Realistic content length
        "excerpt": f"This is the excerpt for blog post {i}...",
        "author_id": random.randint(1, 10),
        "author_name": f"Author {random.randint(1, 10)}",
        "status": "published",
        "category": random.choice(["Tech", "Business", "Lifestyle", "Education"]),
        "tags": random.sample(["tutorial", "guide", "news", "tips", "howto"], k=random.randint(1, 3)),
        "created_at": (datetime.now() - timedelta(days=random.randint(1, 180))).isoformat(),
        "updated_at": datetime.now().isoformat(),
        "views_count": random.randint(100, 5000),
        "likes_count": random.randint(10, 500),
        "comments_count": random.randint(0, 50),
        "featured_image": f"/static/images/blog_{i}.jpg",
        "reading_time": random.randint(3, 15)
    }
    for i in range(1, 51)
]

# Users data
USERS = [
    {
        "id": i,
        "username": f"user{i}",
        "email": f"user{i}@example.com",
        "first_name": f"First{i}",
        "last_name": f"Last{i}",
        "is_active": True,
        "created_at": (datetime.now() - timedelta(days=random.randint(1, 365))).isoformat(),
        "last_login": datetime.now().isoformat(),
        "profile": {
            "bio": f"This is the bio for user {i}",
            "avatar": f"/static/avatars/user_{i}.jpg",
            "location": random.choice(["New York", "London", "Tokyo", "Paris", "Berlin"]),
            "website": f"https://user{i}.com"
        }
    }
    for i in range(1, 21)
]

# Analytics data store
ANALYTICS_EVENTS = []
ANALYTICS_STATS = {
    "total_page_views": 0,
    "unique_visitors": 0,
    "total_orders": 0,
    "revenue": 0.0
}

# Background task executor
executor = ThreadPoolExecutor(max_workers=4)

# =====================================================
# HELPER FUNCTIONS
# =====================================================

def simulate_database_query(duration_ms=5):
    """Simulate database query delay"""
    time.sleep(duration_ms / 1000.0)

def simulate_cache_lookup(hit_rate=0.8):
    """Simulate cache lookup with hit rate"""
    return random.random() < hit_rate

def track_analytics_event(event_type: str, user_id: Optional[int] = None, metadata: Dict = None):
    """Track analytics event in background"""
    def _track():
        event = {
            "id": str(uuid.uuid4()),
            "event_type": event_type,
            "user_id": user_id,
            "timestamp": datetime.now().isoformat(),
            "metadata": metadata or {}
        }
        ANALYTICS_EVENTS.append(event)
        ANALYTICS_STATS["total_page_views"] += 1

    executor.submit(_track)

# =====================================================
# FLASK ROUTES
# =====================================================

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint with system metrics"""
    return jsonify({
        "status": "healthy",
        "framework": "flask",
        "timestamp": time.time(),
        "version": "1.0.0",
        "environment": "benchmark",
        "metrics": {
            "total_products": len(PRODUCTS),
            "total_posts": len(BLOG_POSTS),
            "total_users": len(USERS),
            "analytics_events": len(ANALYTICS_EVENTS)
        }
    })

@app.route('/api/products', methods=['GET'])
def api_products():
    """Product listing with pagination, filtering, and search"""
    # Track page view
    track_analytics_event("product_list_view", metadata={"source": "api"})

    # Simulate cache lookup
    if simulate_cache_lookup():
        cache_time = 2  # Cache hit - faster response
    else:
        cache_time = 10  # Cache miss - slower response

    simulate_database_query(cache_time)

    # Get query parameters
    page = int(request.args.get("page", 1))
    limit = int(request.args.get("limit", 20))
    category_id = request.args.get("category_id")
    search = request.args.get("search")
    sort_by = request.args.get("sort_by", "created_at")
    sort_order = request.args.get("sort_order", "desc")

    # Filter products
    filtered_products = PRODUCTS.copy()

    if category_id:
        filtered_products = [p for p in filtered_products if p["category_id"] == int(category_id)]

    if search:
        search_lower = search.lower()
        filtered_products = [
            p for p in filtered_products
            if search_lower in p["name"].lower() or search_lower in p["description"].lower()
        ]

    # Sort products
    reverse = sort_order == "desc"
    if sort_by == "price":
        filtered_products.sort(key=lambda x: x["price"], reverse=reverse)
    elif sort_by == "name":
        filtered_products.sort(key=lambda x: x["name"], reverse=reverse)
    elif sort_by == "popularity":
        filtered_products.sort(key=lambda x: x["reviews_count"], reverse=reverse)
    else:  # created_at
        filtered_products.sort(key=lambda x: x["created_at"], reverse=reverse)

    # Pagination
    start_idx = (page - 1) * limit
    end_idx = start_idx + limit
    paginated_products = filtered_products[start_idx:end_idx]

    return jsonify({
        "products": paginated_products,
        "pagination": {
            "page": page,
            "limit": limit,
            "total": len(filtered_products),
            "total_pages": (len(filtered_products) + limit - 1) // limit,
            "has_next": end_idx < len(filtered_products),
            "has_prev": page > 1
        },
        "filters": {
            "category_id": category_id,
            "search": search,
            "sort_by": sort_by,
            "sort_order": sort_order
        }
    })

@app.route('/api/products/<int:product_id>', methods=['GET'])
def api_product_detail(product_id):
    """Get single product with view tracking"""
    # Track product view
    user_id = request.headers.get("X-User-ID")
    try:
        user_id_int = int(user_id) if user_id and user_id.isdigit() else None
    except (ValueError, AttributeError):
        user_id_int = None
    track_analytics_event("product_view", user_id=user_id_int,
                         metadata={"product_id": product_id})

    # Simulate database query
    simulate_database_query(8)

    try:
        product = next(p for p in PRODUCTS if p["id"] == product_id)

        # Add dynamic pricing and availability
        product_copy = product.copy()
        product_copy["current_price"] = product["price"] * random.uniform(0.9, 1.1)
        product_copy["is_available"] = product["stock_quantity"] > 0
        product_copy["estimated_delivery"] = (datetime.now() + timedelta(days=random.randint(1, 7))).isoformat()

        # Related products
        category_products = [p for p in PRODUCTS if p["category_id"] == product["category_id"] and p["id"] != product["id"]]
        related_products = random.sample(category_products, min(4, len(category_products)))

        return jsonify({
            "product": product_copy,
            "related_products": related_products,
            "metadata": {
                "viewed_at": datetime.now().isoformat(),
                "user_id": user_id
            }
        })
    except StopIteration:
        return jsonify({"error": "Product not found"}), 404

@app.route('/api/orders', methods=['POST'])
def api_orders():
    """Create new order with validation and processing"""
    try:
        data = request.get_json()
        user_id = request.headers.get("X-User-ID", 1)

        # Simulate order validation
        simulate_database_query(15)

        # Validate required fields
        required_fields = ["items", "shipping_address", "payment_method"]
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Missing required field: {field}"}), 400

        # Calculate order totals
        total_amount = 0
        order_items = []

        for item in data["items"]:
            try:
                product = next(p for p in PRODUCTS if p["id"] == item["product_id"])
                item_total = product["price"] * item["quantity"]
                total_amount += item_total

                order_items.append({
                    "product_id": item["product_id"],
                    "product_name": product["name"],
                    "quantity": item["quantity"],
                    "unit_price": product["price"],
                    "total_price": item_total
                })
            except StopIteration:
                return jsonify({"error": f"Product {item['product_id']} not found"}), 400

        # Create order
        order = {
            "id": random.randint(10000, 99999),
            "user_id": int(user_id),
            "status": "pending",
            "total_amount": round(total_amount, 2),
            "shipping_address": data["shipping_address"],
            "billing_address": data.get("billing_address", data["shipping_address"]),
            "payment_method": data["payment_method"],
            "items": order_items,
            "created_at": datetime.now().isoformat(),
            "estimated_delivery": (datetime.now() + timedelta(days=random.randint(3, 10))).isoformat()
        }

        # Track order event
        track_analytics_event("order_created", user_id=int(user_id),
                             metadata={"order_id": order["id"], "total_amount": total_amount})

        # Simulate background order processing
        def process_order():
            time.sleep(0.1)  # Simulate processing time
            ANALYTICS_STATS["total_orders"] += 1
            ANALYTICS_STATS["revenue"] += total_amount

        executor.submit(process_order)

        return jsonify({
            "order": order,
            "message": "Order created successfully",
            "estimated_processing_time": "2-5 minutes"
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route('/api/blog/posts', methods=['GET'])
def api_blog_posts():
    """Blog post listing with filtering"""
    # Track page view
    track_analytics_event("blog_list_view")

    # Simulate database query
    simulate_database_query(6)

    # Get query parameters
    page = int(request.args.get("page", 1))
    limit = int(request.args.get("limit", 10))
    status = request.args.get("status", "published")
    tag = request.args.get("tag")
    search = request.args.get("search")

    # Filter posts
    filtered_posts = [p for p in BLOG_POSTS if p["status"] == status]

    if tag:
        filtered_posts = [p for p in filtered_posts if tag in p["tags"]]

    if search:
        search_lower = search.lower()
        filtered_posts = [
            p for p in filtered_posts
            if search_lower in p["title"].lower() or search_lower in p["content"].lower()
        ]

    # Sort by created_at (newest first)
    filtered_posts.sort(key=lambda x: x["created_at"], reverse=True)

    # Pagination
    start_idx = (page - 1) * limit
    end_idx = start_idx + limit
    paginated_posts = filtered_posts[start_idx:end_idx]

    return jsonify({
        "posts": paginated_posts,
        "pagination": {
            "page": page,
            "limit": limit,
            "total": len(filtered_posts),
            "total_pages": (len(filtered_posts) + limit - 1) // limit
        },
        "filters": {
            "status": status,
            "tag": tag,
            "search": search
        }
    })

@app.route('/api/blog/posts/<int:post_id>', methods=['GET'])
def api_blog_post_detail(post_id):
    """Get single blog post with comments"""
    # Track post view
    track_analytics_event("blog_post_view", metadata={"post_id": post_id})

    # Simulate database query
    simulate_database_query(10)

    try:
        post = next(p for p in BLOG_POSTS if p["id"] == post_id)

        # Generate mock comments
        comments = [
            {
                "id": i,
                "author": f"Commenter {i}",
                "content": f"This is comment {i} on the post.",
                "created_at": (datetime.now() - timedelta(hours=random.randint(1, 72))).isoformat(),
                "likes": random.randint(0, 20)
            }
            for i in range(1, random.randint(3, 8))
        ]

        # Update view count
        post_copy = post.copy()
        post_copy["views_count"] += 1

        return jsonify({
            "post": post_copy,
            "comments": comments,
            "related_posts": random.sample(BLOG_POSTS, min(3, len(BLOG_POSTS)))
        })
    except StopIteration:
        return jsonify({"error": "Post not found"}), 404

@app.route('/api/analytics/dashboard', methods=['GET'])
def api_analytics_dashboard():
    """Analytics dashboard with real-time metrics"""
    user_id = request.headers.get("X-User-ID")
    if not user_id:
        return jsonify({"error": "User authentication required"}), 401

    # Simulate complex analytics query
    simulate_database_query(20)

    # Get date range
    date_from = request.args.get("date_from")
    date_to = request.args.get("date_to")

    # Generate analytics data
    analytics_data = {
        "overview": {
            "total_page_views": ANALYTICS_STATS["total_page_views"] + random.randint(1000, 5000),
            "unique_visitors": random.randint(500, 2000),
            "bounce_rate": round(random.uniform(30, 70), 2),
            "avg_session_duration": round(random.uniform(120, 300), 2)
        },
        "sales": {
            "total_orders": ANALYTICS_STATS["total_orders"] + random.randint(100, 500),
            "total_revenue": round(ANALYTICS_STATS["revenue"] + random.uniform(10000, 50000), 2),
            "avg_order_value": round(random.uniform(50, 200), 2),
            "conversion_rate": round(random.uniform(2, 8), 2)
        },
        "products": {
            "top_selling": random.sample(PRODUCTS, 5),
            "low_stock": [p for p in PRODUCTS if p["stock_quantity"] < 10][:5]
        },
        "traffic_sources": {
            "organic": random.randint(40, 60),
            "direct": random.randint(20, 35),
            "social": random.randint(10, 25),
            "referral": random.randint(5, 15)
        },
        "real_time": {
            "active_users": random.randint(10, 100),
            "current_sales": random.randint(0, 20),
            "server_load": round(random.uniform(10, 80), 2)
        }
    }

    return jsonify({
        "dashboard": analytics_data,
        "date_range": {
            "from": date_from or (datetime.now() - timedelta(days=30)).isoformat(),
            "to": date_to or datetime.now().isoformat()
        },
        "generated_at": datetime.now().isoformat()
    })

@app.route('/api/analytics/track', methods=['POST'])
def api_analytics_track():
    """Track analytics event"""
    try:
        data = request.get_json()

        # Validate required fields
        required_fields = ["event_type"]
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Missing required field: {field}"}), 400

        # Process event in background
        def process_event():
            event = {
                "id": str(uuid.uuid4()),
                "event_type": data["event_type"],
                "user_id": data.get("user_id"),
                "session_id": data.get("session_id"),
                "timestamp": datetime.now().isoformat(),
                "page_url": data.get("page_url"),
                "referrer": data.get("referrer"),
                "user_agent": data.get("user_agent"),
                "ip_address": data.get("ip_address"),
                "properties": data.get("properties", {})
            }
            ANALYTICS_EVENTS.append(event)
            ANALYTICS_STATS["total_page_views"] += 1

        executor.submit(process_event)

        return jsonify({
            "status": "success",
            "message": "Event tracked successfully",
            "event_id": str(uuid.uuid4())
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 400

class GunicornFlaskApplication(gunicorn.app.base.BaseApplication):
    """Custom Gunicorn application to run Flask with specific config"""

    def __init__(self, app, options=None):
        self.options = options or {}
        self.application = app
        super().__init__()

    def load_config(self):
        for key, value in self.options.items():
            if key in self.cfg.settings and value is not None:
                self.cfg.set(key.lower(), value)

    def load(self):
        return self.application

def main():
    """Start the Flask real-world benchmark server"""
    parser = argparse.ArgumentParser(description="Flask Real-World Scenarios Benchmark Server")
    parser.add_argument("--port", type=int, default=8083, help="Port to run server on")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind to")
    parser.add_argument("--workers", type=int, default=4, help="Number of worker processes")
    parser.add_argument("--use-gunicorn", action="store_true", default=True, help="Use Gunicorn (default)")
    args = parser.parse_args()

    print(f"🚀 Starting Flask real-world benchmark server on {args.host}:{args.port}")
    print("📊 Flask Real-World Features:")
    print("  🛒 E-commerce product catalog and ordering")
    print("  📝 Blog/CMS content management")
    print("  👥 User authentication and profiles")
    print("  📊 Real-time analytics tracking")
    print("  ⚡ Background task processing")
    print()
    print("Available endpoints:")
    print("  GET  /health                     - Health check with metrics")
    print("  GET  /api/products               - Product catalog with filtering")
    print("  GET  /api/products/{id}          - Product details with tracking")
    print("  POST /api/orders                 - Order creation and processing")
    print("  GET  /api/blog/posts             - Blog post listing")
    print("  GET  /api/blog/posts/{id}        - Blog post details with comments")
    print("  GET  /api/analytics/dashboard    - Analytics dashboard")
    print("  POST /api/analytics/track        - Event tracking")
    print()

    try:
        if args.use_gunicorn:
            # Production WSGI server
            options = {
                'bind': f'{args.host}:{args.port}',
                'workers': args.workers,
                'worker_class': 'sync',
                'timeout': 30,
                'keepalive': 2,
                'max_requests': 1000,
                'max_requests_jitter': 100,
                'disable_redirect_access_to_syslog': True,
                'capture_output': True,
                'enable_stdio_inheritance': True,
            }

            GunicornFlaskApplication(app, options).run()
        else:
            # Development server (not recommended for benchmarks)
            app.run(host=args.host, port=args.port, debug=False)

    except KeyboardInterrupt:
        print("\n👋 Flask real-world benchmark server stopped")

if __name__ == "__main__":
    main()
