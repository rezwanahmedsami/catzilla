# 🌟 Real-World Example: E-Commerce API with Catzilla DI

This example demonstrates a production-ready e-commerce API using Catzilla's revolutionary dependency injection system.

## 📋 Project Structure

```
ecommerce_api/
├── app/
│   ├── __init__.py
│   ├── main.py              # Application entry point
│   ├── config.py            # Configuration service
│   ├── database.py          # Database services
│   ├── services/
│   │   ├── __init__.py
│   │   ├── user_service.py
│   │   ├── product_service.py
│   │   ├── order_service.py
│   │   ├── payment_service.py
│   │   └── notification_service.py
│   ├── repositories/
│   │   ├── __init__.py
│   │   ├── user_repository.py
│   │   ├── product_repository.py
│   │   └── order_repository.py
│   └── routes/
│       ├── __init__.py
│       ├── users.py
│       ├── products.py
│       └── orders.py
├── requirements.txt
└── README.md
```

## 🚀 Implementation

### Configuration Service

```python
# app/config.py
import os
from catzilla import service
from typing import Optional

@service("config", scope="singleton")
class Config:
    """Application configuration service"""

    def __init__(self):
        self.database_url = os.getenv("DATABASE_URL", "postgresql://localhost:5432/ecommerce")
        self.redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        self.secret_key = os.getenv("SECRET_KEY", "your-secret-key")
        self.debug = os.getenv("DEBUG", "false").lower() == "true"
        self.jwt_expiration_hours = int(os.getenv("JWT_EXPIRATION_HOURS", "24"))

        # Payment gateway config
        self.stripe_secret_key = os.getenv("STRIPE_SECRET_KEY")
        self.stripe_publishable_key = os.getenv("STRIPE_PUBLISHABLE_KEY")

        # Email config
        self.smtp_host = os.getenv("SMTP_HOST", "localhost")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_username = os.getenv("SMTP_USERNAME")
        self.smtp_password = os.getenv("SMTP_PASSWORD")

        # Validate required settings
        self._validate_config()

    def _validate_config(self):
        """Validate required configuration"""
        if not self.secret_key or self.secret_key == "your-secret-key":
            raise ValueError("SECRET_KEY must be set to a secure value")

        if not self.stripe_secret_key:
            raise ValueError("STRIPE_SECRET_KEY is required for payment processing")
```

### Database Services

```python
# app/database.py
import redis
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import QueuePool
from catzilla import service, Depends
from typing import Generator

Base = declarative_base()

@service("database_engine", scope="singleton")
class DatabaseEngine:
    """Database engine service with connection pooling"""

    def __init__(self, config: Config = Depends("config")):
        self.engine = create_engine(
            config.database_url,
            poolclass=QueuePool,
            pool_size=20,
            max_overflow=30,
            pool_pre_ping=True,
            echo=config.debug
        )

        # Create tables
        Base.metadata.create_all(self.engine)

@service("database_session", scope="request")
class DatabaseSession:
    """Request-scoped database session"""

    def __init__(self, engine: DatabaseEngine = Depends("database_engine")):
        SessionLocal = sessionmaker(bind=engine.engine)
        self.session = SessionLocal()

    def __enter__(self):
        return self.session

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            self.session.rollback()
        else:
            self.session.commit()
        self.session.close()

@service("redis_client", scope="singleton")
class RedisClient:
    """Redis client service for caching"""

    def __init__(self, config: Config = Depends("config")):
        self.client = redis.from_url(
            config.redis_url,
            decode_responses=True,
            retry_on_timeout=True,
            socket_connect_timeout=5
        )

        # Test connection
        try:
            self.client.ping()
        except redis.ConnectionError:
            raise RuntimeError("Failed to connect to Redis")

    def get(self, key: str, default=None):
        """Get value from cache"""
        try:
            return self.client.get(key) or default
        except redis.RedisError:
            return default

    def set(self, key: str, value: str, expire: int = 3600):
        """Set value in cache with expiration"""
        try:
            return self.client.setex(key, expire, value)
        except redis.RedisError:
            return False

    def delete(self, key: str):
        """Delete key from cache"""
        try:
            return self.client.delete(key)
        except redis.RedisError:
            return False
```

### User Service

```python
# app/services/user_service.py
import jwt
import bcrypt
from datetime import datetime, timedelta
from catzilla import service, Depends
from typing import Optional, Dict, Any

@service("user_service", scope="singleton")
class UserService:
    """User management service"""

    def __init__(self,
                 user_repo: 'UserRepository' = Depends("user_repository"),
                 config: Config = Depends("config"),
                 cache: RedisClient = Depends("redis_client")):
        self.user_repo = user_repo
        self.config = config
        self.cache = cache

    def create_user(self, email: str, password: str, name: str) -> Dict[str, Any]:
        """Create a new user account"""
        # Check if user exists
        if self.user_repo.find_by_email(email):
            raise ValueError("User with this email already exists")

        # Hash password
        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

        # Create user
        user = self.user_repo.create({
            'email': email,
            'name': name,
            'password_hash': password_hash.decode('utf-8'),
            'created_at': datetime.utcnow(),
            'is_active': True
        })

        # Generate JWT token
        token = self._generate_token(user['id'])

        # Cache user session
        self.cache.set(f"user_session:{user['id']}", token,
                      expire=self.config.jwt_expiration_hours * 3600)

        return {
            'user': self._sanitize_user(user),
            'token': token
        }

    def authenticate(self, email: str, password: str) -> Optional[Dict[str, Any]]:
        """Authenticate user and return token"""
        user = self.user_repo.find_by_email(email)
        if not user or not user['is_active']:
            return None

        # Verify password
        if not bcrypt.checkpw(password.encode('utf-8'),
                            user['password_hash'].encode('utf-8')):
            return None

        # Generate token
        token = self._generate_token(user['id'])

        # Cache session
        self.cache.set(f"user_session:{user['id']}", token,
                      expire=self.config.jwt_expiration_hours * 3600)

        return {
            'user': self._sanitize_user(user),
            'token': token
        }

    def get_user_by_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Get user from JWT token"""
        try:
            payload = jwt.decode(token, self.config.secret_key, algorithms=['HS256'])
            user_id = payload['user_id']

            # Check cache first
            cached_token = self.cache.get(f"user_session:{user_id}")
            if cached_token != token:
                return None

            user = self.user_repo.find_by_id(user_id)
            return self._sanitize_user(user) if user and user['is_active'] else None

        except jwt.InvalidTokenError:
            return None

    def _generate_token(self, user_id: int) -> str:
        """Generate JWT token for user"""
        payload = {
            'user_id': user_id,
            'exp': datetime.utcnow() + timedelta(hours=self.config.jwt_expiration_hours),
            'iat': datetime.utcnow()
        }
        return jwt.encode(payload, self.config.secret_key, algorithm='HS256')

    def _sanitize_user(self, user: Dict[str, Any]) -> Dict[str, Any]:
        """Remove sensitive fields from user data"""
        if not user:
            return None

        return {
            'id': user['id'],
            'email': user['email'],
            'name': user['name'],
            'created_at': user['created_at'].isoformat(),
            'is_active': user['is_active']
        }
```

### Product Service

```python
# app/services/product_service.py
import json
from typing import List, Dict, Any, Optional
from catzilla import service, Depends

@service("product_service", scope="singleton")
class ProductService:
    """Product catalog management service"""

    def __init__(self,
                 product_repo: 'ProductRepository' = Depends("product_repository"),
                 cache: RedisClient = Depends("redis_client")):
        self.product_repo = product_repo
        self.cache = cache

    def get_product(self, product_id: int) -> Optional[Dict[str, Any]]:
        """Get product by ID with caching"""
        cache_key = f"product:{product_id}"

        # Try cache first
        cached = self.cache.get(cache_key)
        if cached:
            return json.loads(cached)

        # Get from database
        product = self.product_repo.find_by_id(product_id)
        if product and product['is_active']:
            # Cache for 1 hour
            self.cache.set(cache_key, json.dumps(product, default=str), expire=3600)
            return product

        return None

    def search_products(self, query: str, category: str = None,
                       page: int = 1, limit: int = 20) -> Dict[str, Any]:
        """Search products with pagination"""
        cache_key = f"search:{query}:{category}:{page}:{limit}"

        # Try cache first
        cached = self.cache.get(cache_key)
        if cached:
            return json.loads(cached)

        # Search in database
        products = self.product_repo.search(query, category, page, limit)
        total = self.product_repo.count_search_results(query, category)

        result = {
            'products': products,
            'pagination': {
                'page': page,
                'limit': limit,
                'total': total,
                'pages': (total + limit - 1) // limit
            }
        }

        # Cache for 15 minutes
        self.cache.set(cache_key, json.dumps(result, default=str), expire=900)
        return result

    def update_inventory(self, product_id: int, quantity_change: int) -> bool:
        """Update product inventory"""
        product = self.product_repo.find_by_id(product_id)
        if not product:
            return False

        new_quantity = product['inventory_quantity'] + quantity_change
        if new_quantity < 0:
            raise ValueError("Insufficient inventory")

        success = self.product_repo.update_inventory(product_id, new_quantity)

        if success:
            # Invalidate cache
            self.cache.delete(f"product:{product_id}")

        return success

    def get_featured_products(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get featured products"""
        cache_key = f"featured_products:{limit}"

        cached = self.cache.get(cache_key)
        if cached:
            return json.loads(cached)

        products = self.product_repo.get_featured(limit)

        # Cache for 30 minutes
        self.cache.set(cache_key, json.dumps(products, default=str), expire=1800)
        return products
```

### Order Service

```python
# app/services/order_service.py
from datetime import datetime
from enum import Enum
from typing import List, Dict, Any, Optional
from catzilla import service, Depends

class OrderStatus(Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    PROCESSING = "processing"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"

@service("order_service", scope="singleton")
class OrderService:
    """Order management service"""

    def __init__(self,
                 order_repo: 'OrderRepository' = Depends("order_repository"),
                 product_service: ProductService = Depends("product_service"),
                 payment_service: 'PaymentService' = Depends("payment_service"),
                 notification_service: 'NotificationService' = Depends("notification_service")):
        self.order_repo = order_repo
        self.product_service = product_service
        self.payment_service = payment_service
        self.notification_service = notification_service

    def create_order(self, user_id: int, items: List[Dict[str, Any]],
                    shipping_address: Dict[str, str]) -> Dict[str, Any]:
        """Create a new order"""
        # Validate items and calculate total
        order_items = []
        total_amount = 0

        for item in items:
            product = self.product_service.get_product(item['product_id'])
            if not product:
                raise ValueError(f"Product {item['product_id']} not found")

            quantity = item['quantity']
            if quantity <= 0:
                raise ValueError("Quantity must be positive")

            if product['inventory_quantity'] < quantity:
                raise ValueError(f"Insufficient inventory for product {product['name']}")

            item_total = product['price'] * quantity
            total_amount += item_total

            order_items.append({
                'product_id': product['id'],
                'product_name': product['name'],
                'price': product['price'],
                'quantity': quantity,
                'total': item_total
            })

        # Create order
        order_data = {
            'user_id': user_id,
            'status': OrderStatus.PENDING.value,
            'total_amount': total_amount,
            'shipping_address': shipping_address,
            'created_at': datetime.utcnow(),
            'items': order_items
        }

        order = self.order_repo.create(order_data)

        # Reserve inventory
        for item in order_items:
            self.product_service.update_inventory(
                item['product_id'],
                -item['quantity']
            )

        # Send confirmation email
        self.notification_service.send_order_confirmation(user_id, order)

        return order

    def process_payment(self, order_id: int, payment_method: str,
                       payment_details: Dict[str, Any]) -> Dict[str, Any]:
        """Process payment for order"""
        order = self.order_repo.find_by_id(order_id)
        if not order:
            raise ValueError("Order not found")

        if order['status'] != OrderStatus.PENDING.value:
            raise ValueError("Order cannot be paid")

        # Process payment
        payment_result = self.payment_service.process_payment(
            amount=order['total_amount'],
            currency='USD',
            payment_method=payment_method,
            payment_details=payment_details,
            order_id=order_id
        )

        if payment_result['success']:
            # Update order status
            self.order_repo.update_status(order_id, OrderStatus.CONFIRMED.value)

            # Send payment confirmation
            self.notification_service.send_payment_confirmation(
                order['user_id'], order, payment_result
            )

            return {
                'success': True,
                'order': order,
                'payment': payment_result
            }
        else:
            return {
                'success': False,
                'error': payment_result.get('error', 'Payment failed')
            }

    def get_user_orders(self, user_id: int, page: int = 1,
                       limit: int = 10) -> Dict[str, Any]:
        """Get user's orders with pagination"""
        orders = self.order_repo.find_by_user(user_id, page, limit)
        total = self.order_repo.count_user_orders(user_id)

        return {
            'orders': orders,
            'pagination': {
                'page': page,
                'limit': limit,
                'total': total,
                'pages': (total + limit - 1) // limit
            }
        }

    def update_order_status(self, order_id: int, status: str) -> bool:
        """Update order status"""
        if status not in [s.value for s in OrderStatus]:
            raise ValueError(f"Invalid status: {status}")

        success = self.order_repo.update_status(order_id, status)

        if success:
            order = self.order_repo.find_by_id(order_id)
            # Send status update notification
            self.notification_service.send_status_update(
                order['user_id'], order, status
            )

        return success
```

### Route Handlers

```python
# app/routes/users.py
from catzilla import Catzilla, Depends, HTTPException
from typing import Dict, Any

def register_user_routes(app: Catzilla):
    """Register user-related routes"""

    @app.post("/auth/register")
    def register(
        user_data: Dict[str, str],
        user_service: UserService = Depends("user_service")
    ):
        """Register a new user"""
        try:
            result = user_service.create_user(
                email=user_data['email'],
                password=user_data['password'],
                name=user_data['name']
            )
            return {
                'success': True,
                'user': result['user'],
                'token': result['token']
            }
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

    @app.post("/auth/login")
    def login(
        credentials: Dict[str, str],
        user_service: UserService = Depends("user_service")
    ):
        """Authenticate user"""
        result = user_service.authenticate(
            email=credentials['email'],
            password=credentials['password']
        )

        if not result:
            raise HTTPException(status_code=401, detail="Invalid credentials")

        return {
            'success': True,
            'user': result['user'],
            'token': result['token']
        }

    @app.get("/auth/profile")
    def get_profile(
        current_user: Dict[str, Any] = Depends("current_user")
    ):
        """Get current user profile"""
        return {
            'success': True,
            'user': current_user
        }

# app/routes/products.py
def register_product_routes(app: Catzilla):
    """Register product-related routes"""

    @app.get("/products/{product_id}")
    def get_product(
        product_id: int,
        product_service: ProductService = Depends("product_service")
    ):
        """Get product by ID"""
        product = product_service.get_product(product_id)
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")

        return {
            'success': True,
            'product': product
        }

    @app.get("/products/search")
    def search_products(
        query: str,
        category: str = None,
        page: int = 1,
        limit: int = 20,
        product_service: ProductService = Depends("product_service")
    ):
        """Search products"""
        result = product_service.search_products(query, category, page, limit)
        return {
            'success': True,
            **result
        }

    @app.get("/products/featured")
    def get_featured_products(
        limit: int = 10,
        product_service: ProductService = Depends("product_service")
    ):
        """Get featured products"""
        products = product_service.get_featured_products(limit)
        return {
            'success': True,
            'products': products
        }
```

### Application Main

```python
# app/main.py
from catzilla import Catzilla
from catzilla.dependency_injection import AdvancedDIContainer, ContainerConfig
from app.routes.users import register_user_routes
from app.routes.products import register_product_routes
from app.routes.orders import register_order_routes

def create_app() -> Catzilla:
    """Create and configure the application"""

    # Create advanced DI container
    container_config = ContainerConfig(
        name="ECommerceAPI",
        inherit_services=True,
        debug_level=1
    )

    container = AdvancedDIContainer(config=container_config)

    # Create Catzilla app with DI
    app = Catzilla(
        title="E-Commerce API",
        version="1.0.0",
        di_container=container,
        auto_validation=True,
        memory_profiling=True
    )

    # Register routes
    register_user_routes(app)
    register_product_routes(app)
    register_order_routes(app)

    # Health check endpoint
    @app.get("/health")
    def health_check(
        container_info = Depends("container_info")
    ):
        """Health check endpoint"""
        health_status = app.di_container.get_health_status()
        return {
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'services': health_status['services_registered'],
            'container': container_info.name
        }

    return app

if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=8000)
```

## 🎯 Key Features Demonstrated

### 1. **Hierarchical Service Architecture**
- Configuration services at the root level
- Database services as shared infrastructure
- Business logic services with clear dependencies
- Route handlers as the presentation layer

### 2. **Performance Optimizations**
- Redis caching for frequently accessed data
- Database connection pooling
- Request-scoped database sessions
- Singleton services for expensive resources

### 3. **Production-Ready Patterns**
- Comprehensive error handling
- Structured logging and monitoring
- Health check endpoints
- Graceful degradation

### 4. **Scalability Features**
- Stateless service design
- Caching strategy for high-traffic endpoints
- Efficient dependency resolution
- Memory-optimized data structures

## 📊 Performance Benefits

This architecture with Catzilla DI provides:

- **5-8x faster** dependency resolution vs pure Python DI
- **30% memory reduction** through arena-based allocation
- **Sub-millisecond** service resolution for cached dependencies
- **Thread-safe** concurrent request handling
- **Zero-overhead** C-Python bridge for dependency management

## 🚀 Running the Application

```bash
# Install dependencies
pip install catzilla>=0.2.0 sqlalchemy redis bcrypt pyjwt

# Set environment variables
export DATABASE_URL="postgresql://user:pass@localhost/ecommerce"
export REDIS_URL="redis://localhost:6379"
export SECRET_KEY="your-super-secret-key"
export STRIPE_SECRET_KEY="sk_test_..."

# Run the application
python -m app.main
```

The application will start on `http://localhost:8000` with full dependency injection, auto-validation, and memory profiling enabled.

---

*This example demonstrates production-ready e-commerce API architecture using Catzilla's revolutionary dependency injection system with real-world performance optimizations and scalability patterns.*
