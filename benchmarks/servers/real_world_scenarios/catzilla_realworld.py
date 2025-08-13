#!/usr/bin/env python3
"""
Catzilla Real-World Scenarios Benchmark Server

Comprehensive real-world application scenarios using Catzilla's full feature set.
Tests complete application workflows combining multiple features.

Features:
- Complete REST API scenarios
- E-commerce application simulation
- Blog/CMS functionality
- User management system
- Real-time analytics dashboard
- File upload and processing workflows
- Background task integration
"""

import sys
import os
import json
import time
import argparse
import uuid
import hashlib
from typing import Optional, List, Dict, Any, Union
from datetime import datetime, timedelta
from decimal import Decimal
import random

# Add the catzilla package to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', 'python'))

from catzilla import (
    Catzilla, BaseModel, Field, BackgroundTask,
    JSONResponse, FileResponse, Response,
    Query, Path as PathParam, Header, Form, File, UploadFile,
    Depends
)

# Import shared real-world endpoints
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'shared'))
from realworld_endpoints import get_realworld_endpoints


# =====================================================
# REAL-WORLD DATA MODELS
# =====================================================

class User(BaseModel):
    """User model for authentication and profile management"""
    id: Optional[int] = None
    username: str = Field(min_length=3, max_length=20, regex=r'^[a-zA-Z0-9_]+$')
    email: str = Field(regex=r'^[^@]+@[^@]+\.[^@]+$')
    first_name: str = Field(min_length=1, max_length=50)
    last_name: str = Field(min_length=1, max_length=50)
    is_active: bool = True
    is_admin: bool = False
    created_at: Optional[datetime] = None
    last_login: Optional[datetime] = None

class Product(BaseModel):
    """E-commerce product model"""
    id: Optional[int] = None
    name: str = Field(min_length=1, max_length=200)
    description: str = Field(max_length=2000)
    price: Decimal = Field(ge=0.01, max_digits=10, decimal_places=2)
    category_id: int = Field(ge=1)
    brand: Optional[str] = Field(max_length=100)
    sku: str = Field(regex=r'^[A-Z0-9\-]+$')
    stock_quantity: int = Field(ge=0)
    is_featured: bool = False
    tags: List[str] = []
    images: List[str] = []
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class Order(BaseModel):
    """E-commerce order model"""
    id: Optional[int] = None
    user_id: int = Field(ge=1)
    status: str = Field(regex=r'^(pending|confirmed|processing|shipped|delivered|cancelled)$')
    total_amount: Decimal = Field(ge=0, max_digits=10, decimal_places=2)
    shipping_address: Dict[str, str]
    billing_address: Dict[str, str]
    items: List[Dict[str, Any]] = Field(min_items=1)
    payment_method: str = Field(regex=r'^(credit_card|paypal|bank_transfer)$')
    tracking_number: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class BlogPost(BaseModel):
    """Blog/CMS post model"""
    id: Optional[int] = None
    title: str = Field(min_length=1, max_length=200)
    slug: str = Field(regex=r'^[a-z0-9\-]+$')
    content: str = Field(min_length=1)
    excerpt: Optional[str] = Field(max_length=500)
    author_id: int = Field(ge=1)
    status: str = Field(regex=r'^(draft|published|archived)$')
    featured_image: Optional[str] = None
    tags: List[str] = []
    meta_description: Optional[str] = Field(max_length=160)
    view_count: int = Field(default=0, ge=0)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class Comment(BaseModel):
    """Blog comment model"""
    id: Optional[int] = None
    post_id: int = Field(ge=1)
    author_id: int = Field(ge=1)
    content: str = Field(min_length=1, max_length=1000)
    parent_id: Optional[int] = None
    is_approved: bool = False
    created_at: Optional[datetime] = None

class AnalyticsEvent(BaseModel):
    """Analytics event model"""
    id: Optional[str] = None
    event_type: str = Field(regex=r'^(page_view|click|purchase|signup|login)$')
    user_id: Optional[int] = None
    session_id: str
    page_url: str
    referrer: Optional[str] = None
    user_agent: str
    ip_address: str
    properties: Dict[str, Any] = {}
    timestamp: Optional[datetime] = None


def create_catzilla_realworld_server():
    """Create Catzilla server with real-world application scenarios"""

    app = Catzilla(
        production=True,
        use_jemalloc=True,           # Memory optimization
        auto_validation=True,        # Enable auto-validation
        memory_profiling=False,      # Disable for benchmarks
        auto_memory_tuning=True,     # Adaptive memory management
        show_banner=False,
        enable_background_tasks=True,  # Enable background processing
        enable_file_uploads=True,    # Enable file operations
        enable_di=True,             # Enable dependency injection
        max_upload_size=50 * 1024 * 1024  # 50MB uploads
    )

    # In-memory data storage (in production, this would be a database)
    data_store = {
        "users": {},
        "products": {},
        "orders": {},
        "blog_posts": {},
        "comments": {},
        "analytics_events": [],
        "sessions": {},
        "categories": {
            1: {"name": "Electronics", "slug": "electronics"},
            2: {"name": "Books", "slug": "books"},
            3: {"name": "Clothing", "slug": "clothing"},
            4: {"name": "Home & Garden", "slug": "home-garden"},
            5: {"name": "Sports", "slug": "sports"}
        }
    }

    # Create sample data
    create_sample_data(data_store)

    endpoints = get_realworld_endpoints()

    # ==========================================
    # DEPENDENCY INJECTION SETUP
    # ==========================================

    def get_current_user(user_id: int = Header(None, alias="X-User-ID")) -> Optional[User]:
        """Get current authenticated user"""
        if user_id and user_id in data_store["users"]:
            return User(**data_store["users"][user_id])
        return None

    def get_analytics_tracker():
        """Get analytics tracking service"""
        return AnalyticsTracker(data_store)

    app.register_dependency("current_user", get_current_user)
    app.register_dependency("analytics", get_analytics_tracker)

    # ==========================================
    # E-COMMERCE API SCENARIOS
    # ==========================================

    @app.get("/api/products")
    def list_products(
        request,
        page: int = Query(1, ge=1),
        limit: int = Query(20, ge=1, le=100),
        category_id: Optional[int] = Query(None),
        search: Optional[str] = Query(None),
        sort_by: str = Query("created_at", regex=r'^(name|price|created_at|popularity)$'),
        sort_order: str = Query("desc", regex=r'^(asc|desc)$'),
        analytics = Depends("analytics")
    ) -> Response:
        """Product listing with pagination, filtering, and search"""
        start_time = time.perf_counter()

        # Track page view
        analytics.track_event("page_view", {"page": "products", "filters": {
            "category_id": category_id, "search": search, "sort_by": sort_by
        }})

        products = list(data_store["products"].values())

        # Apply filters
        if category_id:
            products = [p for p in products if p.get("category_id") == category_id]

        if search:
            search_lower = search.lower()
            products = [p for p in products if
                       search_lower in p.get("name", "").lower() or
                       search_lower in p.get("description", "").lower()]

        # Apply sorting
        if sort_by == "name":
            products.sort(key=lambda x: x.get("name", ""))
        elif sort_by == "price":
            products.sort(key=lambda x: float(x.get("price", 0)))
        elif sort_by == "popularity":
            products.sort(key=lambda x: x.get("view_count", 0), reverse=True)
        else:  # created_at
            products.sort(key=lambda x: x.get("created_at", ""))

        if sort_order == "desc":
            products.reverse()

        # Pagination
        total_count = len(products)
        start_idx = (page - 1) * limit
        end_idx = start_idx + limit
        paginated_products = products[start_idx:end_idx]

        processing_time = (time.perf_counter() - start_time) * 1000

        return JSONResponse({
            "products": paginated_products,
            "pagination": {
                "page": page,
                "limit": limit,
                "total": total_count,
                "pages": (total_count + limit - 1) // limit
            },
            "filters": {
                "category_id": category_id,
                "search": search,
                "sort_by": sort_by,
                "sort_order": sort_order
            },
            "processing_time_ms": round(processing_time, 3),
            "framework": "catzilla"
        })

    @app.get("/api/products/{product_id}")
    def get_product(
        request,
        product_id: int = PathParam(...),
        current_user: Optional[User] = Depends("current_user"),
        analytics = Depends("analytics")
    ) -> Response:
        """Get single product with view tracking"""
        start_time = time.perf_counter()

        if product_id not in data_store["products"]:
            return JSONResponse({"error": "Product not found"}, status_code=404)

        product = data_store["products"][product_id]

        # Increment view count
        product["view_count"] = product.get("view_count", 0) + 1

        # Track product view
        analytics.track_event("product_view", {
            "product_id": product_id,
            "product_name": product.get("name"),
            "user_id": current_user.id if current_user else None
        })

        # Get related products
        category_id = product.get("category_id")
        related_products = [
            p for p in data_store["products"].values()
            if p.get("category_id") == category_id and p.get("id") != product_id
        ][:4]

        processing_time = (time.perf_counter() - start_time) * 1000

        return JSONResponse({
            "product": product,
            "related_products": related_products,
            "processing_time_ms": round(processing_time, 3),
            "framework": "catzilla"
        })

    @app.post("/api/orders")
    def create_order(
        request,
        order: Order,
        current_user: User = Depends("current_user"),
        analytics = Depends("analytics")
    ) -> Response:
        """Create new order with validation and processing"""
        start_time = time.perf_counter()

        if not current_user:
            return JSONResponse({"error": "Authentication required"}, status_code=401)

        # Generate order ID
        order_id = len(data_store["orders"]) + 1

        # Validate products and calculate total
        total_amount = Decimal('0')
        validated_items = []

        for item in order.items:
            product_id = item.get("product_id")
            quantity = item.get("quantity", 1)

            if product_id not in data_store["products"]:
                return JSONResponse({
                    "error": f"Product {product_id} not found"
                }, status_code=400)

            product = data_store["products"][product_id]

            if product.get("stock_quantity", 0) < quantity:
                return JSONResponse({
                    "error": f"Insufficient stock for product {product_id}"
                }, status_code=400)

            item_total = Decimal(str(product["price"])) * quantity
            total_amount += item_total

            validated_items.append({
                "product_id": product_id,
                "product_name": product["name"],
                "quantity": quantity,
                "unit_price": product["price"],
                "total_price": float(item_total)
            })

            # Update stock
            product["stock_quantity"] -= quantity

        # Create order
        order_data = {
            "id": order_id,
            "user_id": current_user.id,
            "status": "pending",
            "total_amount": float(total_amount),
            "shipping_address": order.shipping_address,
            "billing_address": order.billing_address,
            "items": validated_items,
            "payment_method": order.payment_method,
            "tracking_number": f"TRK{order_id:06d}",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }

        data_store["orders"][order_id] = order_data

        # Track purchase event
        analytics.track_event("purchase", {
            "order_id": order_id,
            "total_amount": float(total_amount),
            "item_count": len(validated_items),
            "user_id": current_user.id
        })

        # Schedule background tasks for order processing
        app.add_background_task(process_order_payment, order_id)
        app.add_background_task(send_order_confirmation_email, order_id, current_user.email)

        processing_time = (time.perf_counter() - start_time) * 1000

        return JSONResponse({
            "order_created": True,
            "order": order_data,
            "processing_time_ms": round(processing_time, 3),
            "framework": "catzilla"
        })

    # ==========================================
    # BLOG/CMS SCENARIOS
    # ==========================================

    @app.get("/api/blog/posts")
    def list_blog_posts(
        request,
        page: int = Query(1, ge=1),
        limit: int = Query(10, ge=1, le=50),
        status: str = Query("published"),
        tag: Optional[str] = Query(None),
        search: Optional[str] = Query(None),
        analytics = Depends("analytics")
    ) -> Response:
        """Blog post listing with filtering"""
        start_time = time.perf_counter()

        analytics.track_event("page_view", {"page": "blog", "filters": {
            "status": status, "tag": tag, "search": search
        }})

        posts = [p for p in data_store["blog_posts"].values() if p.get("status") == status]

        # Apply filters
        if tag:
            posts = [p for p in posts if tag in p.get("tags", [])]

        if search:
            search_lower = search.lower()
            posts = [p for p in posts if
                    search_lower in p.get("title", "").lower() or
                    search_lower in p.get("content", "").lower()]

        # Sort by created_at desc
        posts.sort(key=lambda x: x.get("created_at", ""), reverse=True)

        # Pagination
        total_count = len(posts)
        start_idx = (page - 1) * limit
        end_idx = start_idx + limit
        paginated_posts = posts[start_idx:end_idx]

        # Add author information
        for post in paginated_posts:
            author_id = post.get("author_id")
            if author_id and author_id in data_store["users"]:
                author = data_store["users"][author_id]
                post["author"] = {
                    "id": author["id"],
                    "username": author["username"],
                    "first_name": author["first_name"],
                    "last_name": author["last_name"]
                }

        processing_time = (time.perf_counter() - start_time) * 1000

        return JSONResponse({
            "posts": paginated_posts,
            "pagination": {
                "page": page,
                "limit": limit,
                "total": total_count,
                "pages": (total_count + limit - 1) // limit
            },
            "processing_time_ms": round(processing_time, 3),
            "framework": "catzilla"
        })

    @app.get("/api/blog/posts/{post_id}")
    def get_blog_post(
        request,
        post_id: int = PathParam(...),
        analytics = Depends("analytics")
    ) -> Response:
        """Get single blog post with comments"""
        start_time = time.perf_counter()

        if post_id not in data_store["blog_posts"]:
            return JSONResponse({"error": "Post not found"}, status_code=404)

        post = data_store["blog_posts"][post_id].copy()

        # Increment view count
        post["view_count"] = post.get("view_count", 0) + 1
        data_store["blog_posts"][post_id]["view_count"] = post["view_count"]

        # Get author information
        author_id = post.get("author_id")
        if author_id and author_id in data_store["users"]:
            author = data_store["users"][author_id]
            post["author"] = {
                "id": author["id"],
                "username": author["username"],
                "first_name": author["first_name"],
                "last_name": author["last_name"]
            }

        # Get comments
        comments = [c for c in data_store["comments"].values()
                   if c.get("post_id") == post_id and c.get("is_approved")]

        # Add author info to comments
        for comment in comments:
            comment_author_id = comment.get("author_id")
            if comment_author_id and comment_author_id in data_store["users"]:
                author = data_store["users"][comment_author_id]
                comment["author"] = {
                    "username": author["username"],
                    "first_name": author["first_name"],
                    "last_name": author["last_name"]
                }

        # Track post view
        analytics.track_event("blog_post_view", {
            "post_id": post_id,
            "post_title": post.get("title"),
            "view_count": post["view_count"]
        })

        processing_time = (time.perf_counter() - start_time) * 1000

        return JSONResponse({
            "post": post,
            "comments": comments,
            "processing_time_ms": round(processing_time, 3),
            "framework": "catzilla"
        })

    # ==========================================
    # FILE UPLOAD SCENARIOS
    # ==========================================

    @app.post("/api/upload/product-image")
    def upload_product_image(
        request,
        file: UploadFile = File(...),
        product_id: int = Form(...),
        alt_text: Optional[str] = Form(None),
        current_user: User = Depends("current_user")
    ) -> Response:
        """Upload product image with processing"""
        start_time = time.perf_counter()

        if not current_user or not current_user.is_admin:
            return JSONResponse({"error": "Admin access required"}, status_code=403)

        if product_id not in data_store["products"]:
            return JSONResponse({"error": "Product not found"}, status_code=404)

        # Validate file type
        allowed_types = ["image/jpeg", "image/png", "image/webp"]
        if file.content_type not in allowed_types:
            return JSONResponse({
                "error": f"Invalid file type. Allowed: {', '.join(allowed_types)}"
            }, status_code=400)

        # Process file
        content = file.file.read()
        file_size = len(content)

        # Generate filename
        file_extension = file.filename.split('.')[-1] if '.' in file.filename else 'jpg'
        new_filename = f"product_{product_id}_{int(time.time())}.{file_extension}"

        # Calculate checksum
        checksum = hashlib.md5(content).hexdigest()

        # Store image information
        image_info = {
            "filename": new_filename,
            "original_name": file.filename,
            "size": file_size,
            "content_type": file.content_type,
            "checksum": checksum,
            "alt_text": alt_text,
            "uploaded_by": current_user.id,
            "uploaded_at": datetime.now().isoformat()
        }

        # Add to product images
        product = data_store["products"][product_id]
        if "images" not in product:
            product["images"] = []
        product["images"].append(image_info)

        # Schedule background image processing
        app.add_background_task(process_product_image, new_filename, content)

        processing_time = (time.perf_counter() - start_time) * 1000

        return JSONResponse({
            "upload_successful": True,
            "image": image_info,
            "processing_time_ms": round(processing_time, 3),
            "background_processing": "scheduled",
            "framework": "catzilla"
        })

    # ==========================================
    # ANALYTICS DASHBOARD SCENARIOS
    # ==========================================

    @app.get("/api/analytics/dashboard")
    def get_analytics_dashboard(
        request,
        date_from: Optional[str] = Query(None),
        date_to: Optional[str] = Query(None),
        current_user: User = Depends("current_user")
    ) -> Response:
        """Analytics dashboard with real-time metrics"""
        start_time = time.perf_counter()

        if not current_user or not current_user.is_admin:
            return JSONResponse({"error": "Admin access required"}, status_code=403)

        # Calculate metrics
        metrics = calculate_dashboard_metrics(data_store, date_from, date_to)

        processing_time = (time.perf_counter() - start_time) * 1000

        return JSONResponse({
            "dashboard": metrics,
            "processing_time_ms": round(processing_time, 3),
            "framework": "catzilla"
        })

    @app.post("/api/analytics/track")
    def track_event(
        request,
        event: AnalyticsEvent,
        analytics = Depends("analytics")
    ) -> Response:
        """Track analytics event"""
        start_time = time.perf_counter()

        # Process event
        event_id = analytics.track_event(event.event_type, event.dict())

        processing_time = (time.perf_counter() - start_time) * 1000

        return JSONResponse({
            "event_tracked": True,
            "event_id": event_id,
            "processing_time_ms": round(processing_time, 3),
            "framework": "catzilla"
        })

    @app.get("/health")
    def health(request) -> Response:
        """Health check with system metrics"""
        return JSONResponse({
            "status": "healthy",
            "framework": "catzilla",
            "features": {
                "background_tasks": "enabled",
                "file_uploads": "enabled",
                "dependency_injection": "enabled",
                "memory_optimization": "jemalloc_enabled"
            },
            "data_counts": {
                "users": len(data_store["users"]),
                "products": len(data_store["products"]),
                "orders": len(data_store["orders"]),
                "blog_posts": len(data_store["blog_posts"]),
                "analytics_events": len(data_store["analytics_events"])
            }
        })

    return app


# =====================================================
# HELPER FUNCTIONS AND CLASSES
# =====================================================

class AnalyticsTracker:
    """Analytics tracking service"""

    def __init__(self, data_store):
        self.data_store = data_store

    def track_event(self, event_type: str, properties: Dict[str, Any]) -> str:
        """Track an analytics event"""
        event_id = str(uuid.uuid4())

        event_data = {
            "id": event_id,
            "event_type": event_type,
            "properties": properties,
            "timestamp": datetime.now().isoformat()
        }

        self.data_store["analytics_events"].append(event_data)
        return event_id

def process_order_payment(order_id: int):
    """Background task: Process order payment"""
    # Removed artificial delay for benchmarking  # Simulate payment processing
    print(f"Payment processed for order {order_id}")

def send_order_confirmation_email(order_id: int, email: str):
    """Background task: Send order confirmation email"""
    # Removed artificial delay for benchmarking  # Simulate email sending
    print(f"Confirmation email sent to {email} for order {order_id}")

def process_product_image(filename: str, content: bytes):
    """Background task: Process uploaded product image"""
    # Removed artificial delay for benchmarking  # Simulate image processing
    print(f"Image processed: {filename} ({len(content)} bytes)")

def calculate_dashboard_metrics(data_store: Dict, date_from: str, date_to: str) -> Dict[str, Any]:
    """Calculate analytics dashboard metrics"""
    return {
        "total_users": len(data_store["users"]),
        "total_products": len(data_store["products"]),
        "total_orders": len(data_store["orders"]),
        "total_blog_posts": len([p for p in data_store["blog_posts"].values() if p.get("status") == "published"]),
        "recent_orders": len([o for o in data_store["orders"].values()]),
        "revenue": sum(float(o.get("total_amount", 0)) for o in data_store["orders"].values()),
        "popular_products": sorted(
            data_store["products"].values(),
            key=lambda x: x.get("view_count", 0),
            reverse=True
        )[:5],
        "recent_events": data_store["analytics_events"][-10:] if data_store["analytics_events"] else []
    }

def create_sample_data(data_store: Dict):
    """Create sample data for testing"""
    # Create sample users
    for i in range(1, 11):
        user_data = {
            "id": i,
            "username": f"user{i}",
            "email": f"user{i}@example.com",
            "first_name": f"User",
            "last_name": f"{i}",
            "is_active": True,
            "is_admin": i == 1,
            "created_at": datetime.now().isoformat()
        }
        data_store["users"][i] = user_data

    # Create sample products
    for i in range(1, 21):
        product_data = {
            "id": i,
            "name": f"Product {i}",
            "description": f"This is a detailed description for product {i}",
            "price": round(random.uniform(10.0, 500.0), 2),
            "category_id": (i % 5) + 1,
            "brand": f"Brand{(i % 3) + 1}",
            "sku": f"PROD-{i:03d}",
            "stock_quantity": random.randint(0, 100),
            "is_featured": i <= 5,
            "tags": [f"tag{j}" for j in range(1, (i % 4) + 2)],
            "images": [],
            "view_count": random.randint(0, 1000),
            "created_at": datetime.now().isoformat()
        }
        data_store["products"][i] = product_data

    # Create sample blog posts
    for i in range(1, 11):
        post_data = {
            "id": i,
            "title": f"Blog Post {i}",
            "slug": f"blog-post-{i}",
            "content": f"This is the content for blog post {i}. " * 20,
            "excerpt": f"Excerpt for blog post {i}",
            "author_id": (i % 3) + 1,
            "status": "published",
            "tags": [f"blog", f"topic{i % 3}"],
            "view_count": random.randint(0, 500),
            "created_at": datetime.now().isoformat()
        }
        data_store["blog_posts"][i] = post_data


def main():
    parser = argparse.ArgumentParser(description='Catzilla real-world scenarios benchmark server')
    parser.add_argument('--host', default='127.0.0.1', help='Host to bind to')
    parser.add_argument('--port', type=int, default=8400, help='Port to bind to')
    parser.add_argument('--workers', type=int, default=1, help='Number of workers')

    args = parser.parse_args()

    app = create_catzilla_realworld_server()

    print(f"🚀 Starting Catzilla real-world scenarios benchmark server on {args.host}:{args.port}")
    print("Real-world scenario endpoints:")
    print("  GET  /api/products               - Product listing")
    print("  GET  /api/products/{id}          - Product details")
    print("  POST /api/orders                 - Create order")
    print("  GET  /api/blog/posts             - Blog post listing")
    print("  GET  /api/blog/posts/{id}        - Blog post details")
    print("  POST /api/upload/product-image   - Upload product image")
    print("  GET  /api/analytics/dashboard    - Analytics dashboard")
    print("  POST /api/analytics/track        - Track analytics event")
    print("  GET  /health                     - Health check")
    print()

    try:
        app.listen(args.port, args.host)
    except KeyboardInterrupt:
        print("\n👋 Catzilla real-world scenarios benchmark server stopped")


if __name__ == "__main__":
    main()
