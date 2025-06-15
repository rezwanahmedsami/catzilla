"""
Hello World example using Catzilla's fluent response API.
Modern Catzilla v0.2.0 with Memory Revolution and auto-validation features.
"""

from catzilla import Catzilla, BaseModel
from catzilla.response import response

# Modern Catzilla v0.2.0 with Memory Revolution features
app = Catzilla(
    auto_validation=True,
    memory_profiling=False,  # Disable for stable production use
    use_jemalloc=True   # Enable memory optimization
)

# Auto-validation model for query parameters
class HelloQuery(BaseModel):
    name: str = "World"
    greeting: str = "Hello"

@app.get("/")
def hello(request):
    print("THis working very fine")
    return response.html("""
        <!DOCTYPE html>
        <html>
            <head>
                <title>Hello Catzilla</title>
                <style>
                    body {
                        font-family: Arial, sans-serif;
                        margin: 40px;
                        line-height: 1.6;
                    }
                </style>
            </head>
            <body>
                <h1>Hello, Catzilla!</h1>
                <p>Welcome to the fluent response API demo.</p>
                <ul>
                    <li><a href="/api/hello">JSON Response Example</a></li>
                    <li><a href="/text">Plain Text Example</a></li>
                </ul>
            </body>
        </html>
    """)

@app.get("/api/hello")
def hello_json(request):
    name = request.query_params.get("name", "World")
    return (response
        .status(200)
        .set_header("X-Powered-By", "Catzilla")
        .json({
            "message": f"Hello, {name}!",
            "timestamp": "2024-03-21T12:00:00Z"
        }))

@app.get("/text")
def hello_text(request):
    return (response
        .status(200)
        .set_header("X-Content-Type", "text/plain")
        .send("Hello, plain text!"))

if __name__ == "__main__":
    app.listen(8080)
