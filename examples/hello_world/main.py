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
                .demo-form {
                    margin: 20px 0;
                    padding: 20px;
                    border: 1px solid #ddd;
                    border-radius: 4px;
                }
            </style>
        </head>
        <body>
            <h1>Welcome to Catzilla!</h1>
            <p>A high-performance Python web framework with C core.</p>

            <div class="demo-form">
                <h2>Test Form Submission</h2>
                <form action="/demo/form" method="POST" enctype="application/x-www-form-urlencoded">
                    <p><input type="text" name="message" placeholder="Enter a message"></p>
                    <p><input type="submit" value="Submit Form"></p>
                </form>
            </div>

            <h2>API Endpoints:</h2>
            <ul>
                <li><a href="/hello">Hello Page</a></li>
                <li><a href="/api/info">API Info</a></li>
                <li><a href="/demo/request-info">Request Info Demo</a></li>
                <li><a href="/demo/query?name=catzilla&type=awesome">Query Params Demo</a></li>
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

@app.get("/demo/request-info")
def request_info(request):
    """Demonstrate all the new Request features"""
    return JSONResponse({
        "client_ip": request.client_ip,
        "content_type": request.content_type,
        "headers": request.headers,
        "query_params": request.query_params,
        "method": request.method,
        "path": request.path,
    })

@app.get("/demo/query")
def query_demo(request):
    """Demonstrate query parameter handling"""
    return JSONResponse({
        "message": "Query parameters received",
        "params": request.query_params
    })

@app.post("/demo/form")
def form_demo(request):
    """Demonstrate form data handling"""
    print(f"[DEBUG] Echo handler - body: {request.body}")
    form_data = request.form()
    return JSONResponse({
        "message": "Form data received",
        "form_data": form_data
    })

@app.post("/api/echo")
def echo(request):
    """Echo back JSON data with content type info"""
    # print body
    print(f"[DEBUG] Echo handler - body: {request.body}")
    # Get content type from request
    content_type = request.content_type
    print(f"[DEBUG] Echo handler - content type: {content_type}")

    # Get raw text first
    raw_text = request.text()
    print(f"[DEBUG] Echo handler - raw text: {raw_text}")

    # Try to parse JSON only if content type is application/json
    parsed_json = {}
    if content_type == "application/json":
        try:
            parsed_json = request.json()
            print(f"[DEBUG] Echo handler - parsed JSON: {parsed_json}")
        except Exception as e:
            print(f"[DEBUG] Echo handler - JSON parsing error: {e}")

    return JSONResponse({
        "message": "Echoing back your data",
        "content_type": content_type,
        "raw_text": raw_text,
        "parsed_json": parsed_json
    })

# Additional HTTP method handlers
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
