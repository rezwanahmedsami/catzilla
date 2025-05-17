"""
Catzilla Hello World Example
"""

from catzilla import App, Response, JSONResponse, HTMLResponse

app = App()

@app.get("/")
def home(request):
    return HTMLResponse("""
    <!DOCTYPE html>
    <html>
        <head>
            <title>Catzilla Hello World</title>
            <style>
                body {
                    font-family: Arial, sans-serif;
                    margin: 40px;
                    line-height: 1.6;
                }
                h1 { color: #333; }
                a { color: #0066cc; }
            </style>
        </head>
        <body>
            <h1>Welcome to Catzilla!</h1>
            <p>A high-performance Python web framework with C core.</p>
            <ul>
                <li><a href="/hello">Hello Page</a></li>
                <li><a href="/api/info">API Info</a></li>
            </ul>
        </body>
    </html>
    """)

@app.get("/hello")
def hello(request):
    return HTMLResponse("<h1>Hello, World!</h1><p>This is Catzilla in action.</p>")

@app.get("/api/info")
def api_info(request):
    return JSONResponse({
        "name": "Catzilla",
        "version": "0.1.0",
        "description": "High-performance Python web framework with C core"
    })

# post("/api/echo")
@app.post("/api/echo")
def echo(request):
    data = request.body
    #  convert to json 
    if isinstance(data, bytes):
        data = data.decode('utf-8')
    #  convert to json
    try:
        import json
        data = json.loads(data)
    except json.JSONDecodeError:
        return JSONResponse({
            "error": "Invalid JSON data"
        }, status_code=400)
    return JSONResponse({
        "message": "Echoing back your data",
        "data": data
    })

# put("/api/update")
@app.put("/api/update")
def update(request):
    data = request.json()
    return JSONResponse({
        "message": "Data updated successfully",
        "data": data
    })

@app.delete("/api/delete")
def delete(request):
    data = request.json()
    return JSONResponse({
        "message": "Data deleted successfully",
        "data": data
    })

@app.patch("/api/patch")
def patch(request):
    data = request.json()
    return JSONResponse({
        "message": "Data patched successfully",
        "data": data
    })

if __name__ == "__main__":
    print("Starting Catzilla server on http://localhost:8000")
    app.listen(8080)