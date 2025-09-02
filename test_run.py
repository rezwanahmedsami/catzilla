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
