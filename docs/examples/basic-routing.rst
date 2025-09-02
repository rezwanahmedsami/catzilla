Basic Routing Examples
======================

This page provides comprehensive examples of Catzilla's routing capabilities, from simple endpoints to advanced patterns. All examples are based on working code from the Catzilla examples repository.

Hello World
-----------

The simplest possible Catzilla application:

.. code-block:: python

   from catzilla import Catzilla, Request, Response, JSONResponse

   app = Catzilla(production=False, show_banner=True, log_requests=True)

   @app.get("/")
   def home(request: Request) -> Response:
       return JSONResponse({
           "message": "Hello, Catzilla!",
           "framework": "Catzilla v0.2.0",
           "performance": "High-performance web framework"
       })

   if __name__ == "__main__":
       app.listen(port=8000)

Async/Sync Hybrid Example
--------------------------

Catzilla's killer feature - seamlessly mixing async and sync handlers in one application:

.. code-block:: python

   from catzilla import Catzilla, Request, Response, JSONResponse
   import asyncio
   import time

   app = Catzilla(production=False, show_banner=True, log_requests=True)

   # Sync handler (perfect for CPU-bound tasks)
   @app.get("/sync")
   def sync_endpoint(request: Request) -> Response:
       """Runs in optimized thread pool"""
       start_time = time.time()

       # Simulate CPU-bound work
       result = sum(i * i for i in range(10000))

       return JSONResponse({
           "result": result,
           "handler_type": "sync",
           "execution": "thread_pool",
           "time": f"{time.time() - start_time:.3f}s"
       })

   # Async handler (perfect for I/O-bound tasks)
   @app.get("/async")
   async def async_endpoint(request: Request) -> Response:
       """Runs in event loop - non-blocking"""
       start_time = time.time()

       # Simulate async I/O
       await asyncio.sleep(0.1)

       return JSONResponse({
           "result": "async_completed",
           "handler_type": "async",
           "execution": "event_loop",
           "time": f"{time.time() - start_time:.3f}s"
       })

   if __name__ == "__main__":
       app.listen(port=8000)

URL Parameters with Auto-Validation
-----------------------------------

Catzilla provides powerful auto-validation for URL parameters using the ``Path()`` function:

.. code-block:: python

   from catzilla import Catzilla, Request, Response, JSONResponse, Path

   app = Catzilla(production=False, show_banner=True, log_requests=True)

   @app.get("/users/{user_id}")
   def get_user(request: Request, user_id: int = Path(description="User ID")) -> Response:
       return JSONResponse({
           "user_id": user_id,
           "type": type(user_id).__name__,
           "message": f"User {user_id} profile"
       })

   @app.get("/posts/{post_id}/comments/{comment_id}")
   def get_comment(
       request: Request,
       post_id: int = Path(description="Post ID"),
       comment_id: int = Path(description="Comment ID")
   ) -> Response:
       return JSONResponse({
           "post_id": post_id,
           "comment_id": comment_id,
           "message": f"Comment {comment_id} from post {post_id}"
       })

   if __name__ == "__main__":
       app.listen(port=8000)

Query Parameters with Auto-Validation
-------------------------------------

Catzilla provides automatic query parameter validation using the ``Query()`` function:

.. code-block:: python

   from catzilla import Catzilla, Request, Response, JSONResponse, Query
   from typing import Optional

   app = Catzilla(production=False, show_banner=True, log_requests=True)

   @app.get("/search")
   def search_items(
       request: Request,
       q: str = Query(description="Search query"),
       page: int = Query(default=1, description="Page number", ge=1),
       limit: int = Query(default=10, description="Items per page", ge=1, le=100),
       category: Optional[str] = Query(default=None, description="Filter by category")
   ) -> Response:
       return JSONResponse({
           "query": q,
           "page": page,
           "limit": limit,
           "category": category,
           "total_results": 42,
           "message": f"Search results for '{q}'"
       })

   @app.get("/users")
   def list_users(
       request: Request,
       active: bool = Query(default=True, description="Filter active users"),
       sort: str = Query(default="created", description="Sort field"),
       order: str = Query(default="desc", description="Sort order")
   ) -> Response:
       return JSONResponse({
           "filters": {
               "active": active,
               "sort": sort,
               "order": order
           },
           "users": [
               {"id": 1, "name": "Alice", "active": True},
               {"id": 2, "name": "Bob", "active": False}
           ]
       })

   if __name__ == "__main__":
       app.listen(port=8000)

Request Body Validation with BaseModel
--------------------------------------

Catzilla supports automatic request body validation using BaseModel:

.. code-block:: python

   from catzilla import Catzilla, Request, Response, JSONResponse, BaseModel, Field
   from typing import Optional

   app = Catzilla(production=False, show_banner=True, log_requests=True)

   class UserCreate(BaseModel):
       name: str = Field(min_length=2, max_length=50, description="User's full name")
       email: str = Field(description="User's email address")
       age: int = Field(ge=13, le=120, description="User's age")
       bio: Optional[str] = Field(default=None, max_length=200, description="User bio")

   class UserResponse(BaseModel):
       id: int
       name: str
       email: str
       age: int
       bio: Optional[str]
       created_at: str

   @app.post("/users")
   def create_user(request: Request, user_data: UserCreate) -> Response:
       # Auto-validation happens here
       new_user = UserResponse(
           id=123,
           name=user_data.name,
           email=user_data.email,
           age=user_data.age,
           bio=user_data.bio,
           created_at="2025-01-14T10:00:00Z"
       )

       return JSONResponse({
           "message": "User created successfully",
           "user": new_user.dict()
       })

   @app.put("/users/{user_id}")
   def update_user(
       request: Request,
       user_id: int,
       user_data: UserCreate
   ) -> Response:
       return JSONResponse({
           "message": f"User {user_id} updated",
           "updated_data": user_data.dict()
       })

   if __name__ == "__main__":
       app.listen(port=8000)

HTTP Methods
------------

Catzilla supports all standard HTTP methods with proper routing:

.. code-block:: python

   from catzilla import Catzilla, Request, Response, JSONResponse, BaseModel

   app = Catzilla(production=False, show_banner=True, log_requests=True)

   class ItemModel(BaseModel):
       name: str
       description: str
       price: float

   # GET - Read operations
   @app.get("/items")
   def get_items(request: Request) -> Response:
       return JSONResponse({
           "items": [
               {"id": 1, "name": "Item 1", "price": 10.99},
               {"id": 2, "name": "Item 2", "price": 15.50}
           ]
       })

   @app.get("/items/{item_id}")
   def get_item(request: Request, item_id: int) -> Response:
       return JSONResponse({
           "id": item_id,
           "name": f"Item {item_id}",
           "price": 12.99
       })

   # POST - Create operations
   @app.post("/items")
   def create_item(request: Request, item: ItemModel) -> Response:
       return JSONResponse({
           "message": "Item created",
           "item": item.dict(),
           "id": 123
       })

   # PUT - Update operations
   @app.put("/items/{item_id}")
   def update_item(request: Request, item_id: int, item: ItemModel) -> Response:
       return JSONResponse({
           "message": f"Item {item_id} updated",
           "item": item.dict()
       })

   # DELETE - Delete operations
   @app.delete("/items/{item_id}")
   def delete_item(request: Request, item_id: int) -> Response:
       return JSONResponse({
           "message": f"Item {item_id} deleted"
       })

   # PATCH - Partial updates
   @app.patch("/items/{item_id}")
   def patch_item(request: Request, item_id: int) -> Response:
       return JSONResponse({
           "message": f"Item {item_id} patched"
       })

   if __name__ == "__main__":
       app.listen(port=8000)

Header and Form Validation
--------------------------

Catzilla provides automatic validation for headers and form data:

.. code-block:: python

   from catzilla import Catzilla, Request, Response, JSONResponse, Header, Form, Query
   from typing import Optional

   app = Catzilla(production=False, show_banner=True, log_requests=True)

   @app.get("/secure-data")
   def get_secure_data(
       request: Request,
       authorization: str = Header(description="Bearer token"),
       user_agent: Optional[str] = Header(default=None, description="Client user agent"),
       api_key: Optional[str] = Query(default=None, description="API key")
   ) -> Response:
       return JSONResponse({
           "message": "Secure data accessed",
           "auth_method": "Bearer" if authorization.startswith("Bearer") else "Unknown",
           "user_agent": user_agent,
           "has_api_key": api_key is not None
       })

   @app.post("/form-data")
   def handle_form(
       request: Request,
       username: str = Form(description="Username"),
       email: str = Form(description="Email address"),
       age: int = Form(description="User age", ge=13),
       newsletter: bool = Form(default=False, description="Subscribe to newsletter")
   ) -> Response:
       return JSONResponse({
           "message": "Form data processed",
           "data": {
               "username": username,
               "email": email,
               "age": age,
               "newsletter": newsletter
           }
       })

   if __name__ == "__main__":
       app.listen(port=8000)

Advanced Routing Patterns
-------------------------

Combine multiple parameter types for complex routing scenarios:

.. code-block:: python

   from catzilla import Catzilla, Request, Response, JSONResponse, Path, Query, Header, BaseModel, Field
   from typing import Optional

   app = Catzilla(production=False, show_banner=True, log_requests=True)

   class SearchFilters(BaseModel):
       category: Optional[str] = Field(default=None, description="Category filter")
       tags: list[str] = Field(default=[], description="Tag filters")
       price_min: Optional[float] = Field(default=None, ge=0, description="Minimum price")
       price_max: Optional[float] = Field(default=None, ge=0, description="Maximum price")

   @app.get("/api/v1/users/{user_id}/orders/{order_id}")
   def get_user_order(
       request: Request,
       user_id: int = Path(description="User ID", ge=1),
       order_id: int = Path(description="Order ID", ge=1),
       include_items: bool = Query(default=False, description="Include order items"),
       authorization: str = Header(description="Authorization header"),
       x_request_id: Optional[str] = Header(default=None, description="Request tracking ID")
   ) -> Response:
       return JSONResponse({
           "user_id": user_id,
           "order_id": order_id,
           "include_items": include_items,
           "authorized": authorization.startswith("Bearer"),
           "request_id": x_request_id,
           "order": {
               "id": order_id,
               "user_id": user_id,
               "status": "completed",
               "total": 99.99,
               "items": ["Item 1", "Item 2"] if include_items else None
           }
       })

   @app.post("/api/v1/products/search")
   def advanced_search(
       request: Request,
       query: str = Query(description="Search query"),
       page: int = Query(default=1, ge=1, description="Page number"),
       limit: int = Query(default=20, ge=1, le=100, description="Results per page"),
       filters: SearchFilters,
       user_agent: Optional[str] = Header(default=None, description="User agent")
   ) -> Response:
       return JSONResponse({
           "search": {
               "query": query,
               "page": page,
               "limit": limit,
               "filters": filters.dict()
           },
           "results": [
               {"id": 1, "name": "Product 1", "price": 29.99},
               {"id": 2, "name": "Product 2", "price": 49.99}
           ],
           "pagination": {
               "page": page,
               "limit": limit,
               "total": 150,
               "pages": 8
           },
           "user_agent": user_agent
       })

   if __name__ == "__main__":
       app.listen(port=8000)

Error Handling Examples
-----------------------

Proper error handling patterns in Catzilla routing:

.. code-block:: python

   from catzilla import Catzilla, Request, Response, JSONResponse, Path

   app = Catzilla(production=False, show_banner=True, log_requests=True)

   # Sample data
   users = {
       1: {"id": 1, "name": "Alice", "email": "alice@example.com"},
       2: {"id": 2, "name": "Bob", "email": "bob@example.com"}
   }

   @app.get("/users/{user_id}")
   def get_user_with_validation(
       request: Request,
       user_id: int = Path(description="User ID", ge=1, le=1000000)
   ) -> Response:
       if user_id not in users:
           return JSONResponse(
               {"error": "User not found", "user_id": user_id},
               status_code=404
           )

       return JSONResponse({
           "user": users[user_id],
           "message": "User found successfully"
       })

   @app.delete("/users/{user_id}")
   def delete_user(
       request: Request,
       user_id: int = Path(description="User ID", ge=1)
   ) -> Response:
       if user_id not in users:
           return JSONResponse(
               {"error": "User not found"},
               status_code=404
           )

       deleted_user = users.pop(user_id)
       return JSONResponse({
           "message": "User deleted successfully",
           "deleted_user": deleted_user
       })

   # Division endpoint with error handling
   @app.get("/math/divide/{a}/{b}")
   def divide_numbers(
       request: Request,
       a: float = Path(description="Dividend"),
       b: float = Path(description="Divisor")
   ) -> Response:
       if b == 0:
           return JSONResponse(
               {"error": "Division by zero is not allowed"},
               status_code=400
           )

       result = a / b
       return JSONResponse({
           "dividend": a,
           "divisor": b,
           "result": result,
           "operation": "division"
       })

   if __name__ == "__main__":
       app.listen(port=8000)

Complete CRUD Example with Router Groups
----------------------------------------

A full CRUD (Create, Read, Update, Delete) API example using RouterGroup:

.. code-block:: python

   from catzilla import Catzilla, Request, Response, JSONResponse, RouterGroup, BaseModel, Field, Path, Query
   from typing import Optional

   app = Catzilla(production=False, show_banner=True, log_requests=True)

   # Data models
   class ProductCreate(BaseModel):
       name: str = Field(min_length=1, max_length=100, description="Product name")
       description: str = Field(max_length=500, description="Product description")
       price: float = Field(gt=0, description="Product price")
       category: str = Field(description="Product category")

   class ProductUpdate(BaseModel):
       name: Optional[str] = Field(default=None, min_length=1, max_length=100)
       description: Optional[str] = Field(default=None, max_length=500)
       price: Optional[float] = Field(default=None, gt=0)
       category: Optional[str] = Field(default=None)

   # In-memory storage
   products_db = {}
   next_product_id = 1

   # Create router group for products
   products_router = RouterGroup(prefix="/api/v1/products")

   @products_router.get("/")
   def list_products(
       request: Request,
       page: int = Query(default=1, ge=1, description="Page number"),
       limit: int = Query(default=10, ge=1, le=100, description="Items per page"),
       category: Optional[str] = Query(default=None, description="Filter by category")
   ) -> Response:
       # Filter products
       filtered_products = list(products_db.values())
       if category:
           filtered_products = [p for p in filtered_products if p["category"] == category]

       # Pagination
       start_idx = (page - 1) * limit
       end_idx = start_idx + limit
       page_products = filtered_products[start_idx:end_idx]

       return JSONResponse({
           "products": page_products,
           "pagination": {
               "page": page,
               "limit": limit,
               "total": len(filtered_products),
               "pages": (len(filtered_products) + limit - 1) // limit
           },
           "filter": {"category": category} if category else None
       })

   @products_router.post("/")
   def create_product(request: Request, product: ProductCreate) -> Response:
       global next_product_id

       new_product = {
           "id": next_product_id,
           "name": product.name,
           "description": product.description,
           "price": product.price,
           "category": product.category,
           "created_at": "2025-01-14T10:00:00Z",
           "updated_at": "2025-01-14T10:00:00Z"
       }

       products_db[next_product_id] = new_product
       next_product_id += 1

       return JSONResponse(new_product, status_code=201)

   @products_router.get("/{product_id}")
   def get_product(
       request: Request,
       product_id: int = Path(description="Product ID", ge=1)
   ) -> Response:
       if product_id not in products_db:
           return JSONResponse(
               {"error": "Product not found"},
               status_code=404
           )

       return JSONResponse({"product": products_db[product_id]})

   @products_router.put("/{product_id}")
   def update_product(
       request: Request,
       product: ProductUpdate,
       product_id: int = Path(description="Product ID", ge=1)
   ) -> Response:
       if product_id not in products_db:
           return JSONResponse(
               {"error": "Product not found"},
               status_code=404
           )

       existing_product = products_db[product_id]

       # Update fields
       if product.name is not None:
           existing_product["name"] = product.name
       if product.description is not None:
           existing_product["description"] = product.description
       if product.price is not None:
           existing_product["price"] = product.price
       if product.category is not None:
           existing_product["category"] = product.category

       existing_product["updated_at"] = "2025-01-14T10:30:00Z"

       return JSONResponse({"product": existing_product})

   @products_router.delete("/{product_id}")
   def delete_product(
       request: Request,
       product_id: int = Path(description="Product ID", ge=1)
   ) -> Response:
       if product_id not in products_db:
           return JSONResponse(
               {"error": "Product not found"},
               status_code=404
           )

       deleted_product = products_db.pop(product_id)
       return JSONResponse({
           "message": "Product deleted successfully",
           "deleted_product": deleted_product
       })

   # Register router group
   app.include_routes(products_router)

   # Root endpoint
   @app.get("/")
   def api_home(request: Request) -> Response:
       return JSONResponse({
           "message": "Catzilla CRUD API Example",
           "version": "0.2.0",
           "endpoints": {
               "products": "/api/v1/products",
               "create_product": "POST /api/v1/products",
               "get_product": "GET /api/v1/products/{id}",
               "update_product": "PUT /api/v1/products/{id}",
               "delete_product": "DELETE /api/v1/products/{id}"
           }
       })

   if __name__ == "__main__":
       app.listen(port=8000)

Performance Comparison Example
------------------------------

Demonstrate the performance benefits of Catzilla's async/sync hybrid approach:

.. code-block:: python

   from catzilla import Catzilla, Request, Response, JSONResponse
   import asyncio
   import time

   app = Catzilla(production=False, show_banner=True, log_requests=True)

   @app.get("/performance-test/sync")
   def sync_performance_test(request: Request) -> Response:
       """CPU-intensive task - perfect for sync handler"""
       start_time = time.time()

       # Simulate CPU-bound work
       result = sum(i * i for i in range(100000))

       execution_time = time.time() - start_time

       return JSONResponse({
           "handler_type": "sync",
           "execution_context": "thread_pool",
           "result": result,
           "execution_time": f"{execution_time:.4f}s",
           "optimal_for": "CPU-bound tasks"
       })

   @app.get("/performance-test/async")
   async def async_performance_test(request: Request) -> Response:
       """I/O-intensive task - perfect for async handler"""
       start_time = time.time()

       # Simulate multiple I/O operations
       tasks = [
           asyncio.sleep(0.1),  # Database query
           asyncio.sleep(0.05), # Cache lookup
           asyncio.sleep(0.08), # External API call
           asyncio.sleep(0.03)  # Log write
       ]

       await asyncio.gather(*tasks)
       execution_time = time.time() - start_time

       return JSONResponse({
           "handler_type": "async",
           "execution_context": "event_loop",
           "operations": len(tasks),
           "sequential_time_would_be": "0.26s",
           "actual_concurrent_time": f"{execution_time:.4f}s",
           "performance_gain": f"{((0.26 - execution_time) / 0.26 * 100):.1f}%",
           "optimal_for": "I/O-bound tasks"
       })

   @app.get("/performance-test/comparison")
   async def performance_comparison(request: Request) -> Response:
       """Compare both approaches side by side"""
       return JSONResponse({
           "framework": "Catzilla v0.2.0",
           "feature": "Async/Sync Hybrid Support",
           "benefits": {
               "sync_handlers": [
                   "Automatic thread pool execution",
                   "Perfect for CPU-bound tasks",
                   "No async/await overhead",
                   "Familiar programming model"
               ],
               "async_handlers": [
                   "Event loop execution",
                   "Perfect for I/O-bound tasks",
                   "High concurrency support",
                   "Non-blocking operations"
               ],
               "hybrid_approach": [
                   "Best of both worlds",
                   "Automatic handler detection",
                   "Optimal execution context",
                   "Maximum performance"
               ]
           },
           "recommendation": "Use sync for CPU tasks, async for I/O tasks"
       })

   if __name__ == "__main__":
       app.listen(port=8000)

Testing Your Catzilla Routes
----------------------------

Test your endpoints using curl or any HTTP client:

.. code-block:: bash

   # Basic endpoints
   curl http://localhost:8000/
   curl http://localhost:8000/sync
   curl http://localhost:8000/async

   # Path parameters with auto-validation
   curl http://localhost:8000/users/123
   curl http://localhost:8000/posts/456/comments/789

   # Query parameters with validation
   curl "http://localhost:8000/search?q=python&page=1&limit=5&category=tech"
   curl "http://localhost:8000/users?active=true&sort=name&order=asc"

   # POST with JSON body validation
   curl -X POST http://localhost:8000/users \
        -H "Content-Type: application/json" \
        -d '{
          "name": "John Doe",
          "email": "john@example.com",
          "age": 30,
          "bio": "Software developer"
        }'

   # Form data with validation
   curl -X POST http://localhost:8000/form-data \
        -d "username=johndoe&email=john@example.com&age=30&newsletter=true"

   # Headers validation
   curl http://localhost:8000/secure-data \
        -H "Authorization: Bearer token123" \
        -H "User-Agent: MyApp/1.0"

   # Advanced routing with RouterGroup
   curl http://localhost:8000/api/v1/products/
   curl -X POST http://localhost:8000/api/v1/products/ \
        -H "Content-Type: application/json" \
        -d '{
          "name": "Laptop",
          "description": "High-performance laptop",
          "price": 999.99,
          "category": "electronics"
        }'

   # Error handling examples
   curl http://localhost:8000/users/999999  # User not found
   curl http://localhost:8000/math/divide/10/0  # Division by zero

   # Performance testing
   curl http://localhost:8000/performance-test/sync
   curl http://localhost:8000/performance-test/async
   curl http://localhost:8000/performance-test/comparison

Summary
-------

This comprehensive guide demonstrates Catzilla's powerful routing capabilities:

**Key Features:**

- **Async/Sync Hybrid**: Mix sync and async handlers in one application
- **Auto-Validation**: Automatic parameter validation with ``Path()``, ``Query()``, ``Header()``, ``Form()``
- **Request Body Validation**: Use ``BaseModel`` for automatic JSON validation
- **RouterGroup**: Organize routes with prefixes and middleware
- **Error Handling**: Built-in validation errors and custom error responses
- **Performance**: Optimal execution contexts for different workload types

**Best Practices:**

- Use sync handlers for CPU-bound tasks
- Use async handlers for I/O-bound tasks
- Always include proper type hints and validation
- Use RouterGroup for organizing large APIs
- Handle errors gracefully with appropriate status codes
- Include complete imports and ``app.listen(port=8000)`` in examples

All examples are production-ready and can be copied directly into your Catzilla applications.

   # Health check
   curl http://localhost:8000/health

Key Features Demonstrated
-------------------------

1. **Async/Sync Hybrid**
   - Automatic handler type detection
   - Optimal execution context for each handler type
   - Performance benefits of concurrent async operations

2. **Auto-Validation**
   - BaseModel for request body validation
   - Path parameter validation with constraints
   - Query parameter validation with types and constraints

3. **C-Accelerated Performance**
   - Fast routing with O(log n) lookup
   - Optimized request/response handling
   - Exceptional performance with C-accelerated routing

4. **Developer-Friendly API**
   - Intuitive decorators and patterns
   - Comprehensive error handling
   - Easy migration from FastAPI

Next Steps
----------

What's Next?
------------

Now that you understand basic routing, explore these advanced topics:

- :doc:`../core-concepts/validation` - Learn about request/response validation with BaseModel
- :doc:`../core-concepts/dependency-injection` - Explore dependency injection patterns
- :doc:`../core-concepts/middleware` - Add middleware for authentication, logging, etc.
- :doc:`../guides/recipes` - Real-world application patterns
