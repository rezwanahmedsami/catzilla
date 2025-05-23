"""
Hello World example using Catzilla's fluent response API.
"""

from catzilla import App
from catzilla.response import response

app = App()

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
