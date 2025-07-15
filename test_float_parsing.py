"""
Test float parsing issues in query parameters
"""
from catzilla import Catzilla, Request, Response, JSONResponse, Query
from typing import Optional

app = Catzilla(production=False, auto_validation=True)

@app.get("/test-float")
def test_float_parsing(
    request: Request,
    price: Optional[float] = Query(None, ge=0.0, description="Price filter"),
    discount: float = Query(0.0, ge=0.0, le=1.0, description="Discount rate")
) -> Response:
    """Test float parameter parsing"""
    return JSONResponse({
        "price": price,
        "price_type": type(price).__name__,
        "discount": discount,
        "discount_type": type(discount).__name__,
        "calculations": {
            "price_times_discount": price * discount if price else None,
            "final_price": price * (1 - discount) if price else None
        }
    })

if __name__ == "__main__":
    print("🧪 Testing float parsing issues")
    print("Try: curl 'http://localhost:8000/test-float?price=19.99&discount=0.15'")
    print("Try: curl 'http://localhost:8000/test-float?price=123.456&discount=0.1234'")
    app.listen(host="0.0.0.0", port=8000)
