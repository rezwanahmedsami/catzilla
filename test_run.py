from catzilla import Catzilla, JSONResponse, Header
import asyncio

app = Catzilla()

@app.get("/concurrent-demo")
async def concurrent_demo(request, request_id: str = Header("unknown", alias="X-Request-ID", description="Request ID for tracking")):
    """Show concurrent request handling"""

    # Simulate different I/O operations
    await asyncio.sleep(0.5)  # Each request sleeps independently

    return JSONResponse({
        "request_id": request_id,
        "message": "This request didn't block others!",
        "handler_type": "async"
    })

# Test with curl:
# curl -H "X-Request-ID: 1" http://localhost:8000/concurrent-demo &
# curl -H "X-Request-ID: 2" http://localhost:8000/concurrent-demo &
# curl -H "X-Request-ID: 3" http://localhost:8000/concurrent-demo &

if __name__ == "__main__":
    app.listen(port=8000)
