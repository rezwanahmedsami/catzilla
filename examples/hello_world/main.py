"""
Catzilla Hello World Example with RouterGroup
Demonstrates how to organize routes using RouterGroup for better code structure.
"""

from catzilla import App, Response, JSONResponse, HTMLResponse, RouterGroup

app = App()

# Create router groups for different sections
api_router = RouterGroup(prefix="/api", tags=["api"])
demo_router = RouterGroup(prefix="/demo", tags=["demo"])
examples_router = RouterGroup(prefix="/examples", tags=["examples"])

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
                    max-width: 1200px;
                    margin: 0 auto;
                    padding: 20px;
                }
                h1 { color: #333; }
                h2 { color: #444; margin-top: 30px; }
                a { color: #0066cc; text-decoration: none; }
                a:hover { text-decoration: underline; }
                .demo-form {
                    margin: 20px 0;
                    padding: 20px;
                    border: 1px solid #ddd;
                    border-radius: 4px;
                    background: #f9f9f9;
                }
                .api-section {
                    margin: 20px 0;
                    padding: 20px;
                    border: 1px solid #e0e0e0;
                    border-radius: 4px;
                }
                .api-list {
                    list-style: none;
                    padding: 0;
                }
                .api-list li {
                    margin: 10px 0;
                    padding: 10px;
                    background: #fff;
                    border: 1px solid #eee;
                    border-radius: 4px;
                }
                .method {
                    display: inline-block;
                    padding: 3px 8px;
                    border-radius: 3px;
                    font-size: 0.8em;
                    font-weight: bold;
                    margin-right: 10px;
                }
                .get { background: #61affe; color: white; }
                .post { background: #49cc90; color: white; }
                .put { background: #fca130; color: white; }
                .delete { background: #f93e3e; color: white; }
                .patch { background: #50e3c2; color: white; }
                .examples-section {
                    margin-top: 30px;
                    padding: 20px;
                    background: #f8f9fa;
                    border-radius: 8px;
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

            <div class="api-section">
                <h2>API Endpoints</h2>
                <ul class="api-list">
                    <li><span class="method get">GET</span> <a href="/hello">Hello Page</a> - Simple HTML response</li>
                    <li><span class="method get">GET</span> <a href="/api/info">API Info</a> - Framework information</li>
                    <li><span class="method get">GET</span> <a href="/demo/request-info">Request Info Demo</a> - Shows request details</li>
                    <li><span class="method get">GET</span> <a href="/demo/query?name=catzilla&type=awesome">Query Params Demo</a> - URL parameter handling</li>
                    <li><span class="method post">POST</span> <code>/demo/form</code> - Form data handling</li>
                    <li><span class="method post">POST</span> <code>/api/echo</code> - Echo back request data</li>
                    <li><span class="method get">GET</span> <a href="/api/headers">Headers Demo</a> - Response header demo</li>
                    <li><span class="method get">GET</span> <a href="/api/cookies">Cookies Demo</a> - Cookie handling demo</li>
                    <li><span class="method get">GET</span> <a href="/api/status?code=404">Status Code Demo</a> - Custom status response</li>
                    <li><span class="method put">PUT</span> <code>/api/update</code> - Update endpoint</li>
                    <li><span class="method delete">DELETE</span> <code>/api/delete</code> - Delete endpoint</li>
                    <li><span class="method patch">PATCH</span> <code>/api/patch</code> - Patch endpoint</li>
                    <li><span class="method get">GET</span> <a href="/users/123">User Detail</a> - Path parameter example</li>
                </ul>
                <p><strong>Organization:</strong> This example demonstrates RouterGroup usage - routes are organized into logical groups (/api, /demo, /examples) for better code structure.</p>
            </div>

            <div class="examples-section">
                <h2>Quick Examples</h2>
                <ul class="api-list">
                    <li><span class="method get">GET</span> <a href="/examples/simple-html">Simple HTML</a> - Basic HTML string response</li>
                    <li><span class="method get">GET</span> <a href="/examples/simple-json">Simple JSON</a> - Basic dictionary/JSON response</li>
                    <li><span class="method get">GET</span> <a href="/examples/custom-status">Custom Status</a> - Response with custom status code</li>
                    <li><span class="method get">GET</span> <a href="/examples/json-with-headers">JSON with Headers</a> - JSON response with custom headers</li>
                    <li><span class="method get">GET</span> <a href="/examples/styled-html">Styled HTML</a> - HTML response with CSS styling</li>
                </ul>
            </div>
        </body>
    </html>
    """)

@app.get("/hello")
def hello(request):
    return HTMLResponse("<h1>Hello, World!</h1><p>This is Catzilla in action.</p>")

# API Routes - organized in api_router group
@api_router.get("/info")
def api_info(request):
    return JSONResponse({
        "name": "Catzilla",
        "version": "0.1.0",
        "description": "High-performance Python web framework with C core",
        "router_group": "api"
    })

@api_router.post("/echo")
def echo(request):
    """Echo back JSON data with content type info"""
    query_params = request.query_params
    print(f"[DEBUG-PY-FROM-EXAMPLE] Echo handler - query params: {query_params}")
    # print body
    print(f"[DEBUG-PY-FROM-EXAMPLE] Echo handler - body: {request.body}")
    # Get content type from request
    content_type = request.content_type
    print(f"[DEBUG-PY-FROM-EXAMPLE] Echo handler - content type: {content_type}")

    # Get raw text first
    raw_text = request.text()
    print(f"[DEBUG-PY-FROM-EXAMPLE] Echo handler - raw text: {raw_text}")

    # Try to parse JSON only if content type is application/json
    parsed_json = {}
    if content_type == "application/json":
        try:
            parsed_json = request.json()
            print(f"[DEBUG-PY-FROM-EXAMPLE] Echo handler - parsed JSON: {parsed_json}")
        except Exception as e:
            print(f"[DEBUG-PY-FROM-EXAMPLE] Echo handler - JSON parsing error: {e}")

    return JSONResponse({
        "message": "Echoing back your data",
        "content_type": content_type,
        "raw_text": raw_text,
        "parsed_json": parsed_json,
        "query_params": query_params,
        "router_group": "api"
    })

@api_router.put("/update")
def update(request):
    data = request.json()
    return JSONResponse({
        "message": "Data updated successfully",
        "data": data,
        "router_group": "api"
    })

@api_router.delete("/delete")
def delete(request):
    data = request.json()
    return JSONResponse({
        "message": "Data deleted successfully",
        "data": data,
        "router_group": "api"
    })

@api_router.patch("/patch")
def patch(request):
    data = request.json()
    return JSONResponse({
        "message": "Data patched successfully",
        "data": data,
        "router_group": "api"
    })

@api_router.get("/headers")
def headers_demo(request):
    """Demonstrate response headers"""
    return JSONResponse(
        {
            "message": "Custom headers demo",
            "your_headers": request.headers,
            "router_group": "api"
        },
        headers={
            "X-Custom-Header": "Custom Value",
            "X-Framework": "Catzilla",
            "X-Version": "0.1.0",
            "Access-Control-Allow-Origin": "*"
        }
    )

@api_router.get("/cookies")
def cookies_demo(request):
    """Demonstrate cookie handling"""
    response = JSONResponse({
        "message": "Cookie demo",
        "description": "Check your browser's cookies",
        "note": "All cookies should be visible now",
        "router_group": "api"
    })

    # Basic session cookie
    response.set_cookie(
        "session_demo",
        "abc123",
        max_age=3600,
        path="/"
    )

    # Persistent cookie
    response.set_cookie(
        "persistent_demo",
        "xyz789",
        expires="Sat, 24 May 2025 00:00:00 GMT",
        path="/"
    )

    # Secure cookie - only set secure flag if using HTTPS
    response.set_cookie(
        "secure_demo",
        "secure123",
        httponly=True,  # Remove secure flag since we're using HTTP
        path="/"
    )

    # Path-specific cookie
    response.set_cookie(
        "path_demo",
        "path123",
        path="/",  # Set to root path to ensure visibility
        max_age=3600
    )

    return response

@api_router.get("/status")
def status_demo(request):
    """Demonstrate different status codes"""
    # Extract status code from query params
    try:
        code = int(request.query_params.get("code", 400))
    except ValueError:
        code = 400

    return JSONResponse(
        {
            "message": f"Returning status code {code}",
            "description": "This is a status code demo",
            "router_group": "api"
        },
        status_code=code
    )

# api router with path parameters
@api_router.get("/users/{id}")
def api_user_detail(request):
    """Example of returning a user detail"""
    query_params = request.query_params
    return JSONResponse({
        "message": "User detail",
        "id": request.path_params["id"],
        "query_params": query_params,
        "note": "This route is registered in the api_router group"
    })

# Demo Routes - organized in demo_router group
@demo_router.get("/request-info")
def request_info(request):
    """Demonstrate all the new Request features"""
    return JSONResponse({
        "client_ip": request.client_ip,
        "content_type": request.content_type,
        "headers": request.headers,
        "query_params": request.query_params,
        "method": request.method,
        "path": request.path,
        "router_group": "demo"
    })

@demo_router.get("/query")
def query_demo(request):
    """Demonstrate query parameter handling"""
    return JSONResponse(
        {
            "message": "Query parameters received",
            "params": request.query_params,
            "router_group": "demo"
        },
        headers={
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*"  # Allow cross-origin requests
        }
    )

@demo_router.post("/form")
def form_demo(request):
    """Demonstrate form data handling"""
    print(f"[DEBUG-PY-FROM-EXAMPLE] Echo handler - body: {request.body}")
    content_type = request.content_type
    raw_text = request.text()
    form_data = request.form()
    query_params = request.query_params
    return JSONResponse({
        "message": "Form data received",
        "content_type": content_type,
        "raw_text": raw_text,
        "form_data": form_data,
        "query_params": query_params,
        "router_group": "demo"
    })

# Examples Routes - organized in examples_router group
@examples_router.get("/simple-html")
def simple_html(request):
    """Example of returning a simple HTML string"""
    return "<h1>Hello World</h1><p>This is a simple HTML response from the examples router group</p>"

@examples_router.get("/simple-json")
def simple_json(request):
    """Example of returning a simple dictionary"""
    return {
        "name": "sami",
        "role": "developer",
        "skills": ["python", "javascript", "c++"],
        "router_group": "examples"
    }

@examples_router.get("/custom-status")
def custom_status(request):
    """Example of returning with a custom status code"""
    return Response(
        status_code=201,
        body="Resource created successfully (from examples router group)",
        content_type="text/plain"
    )

@examples_router.get("/json-with-headers")
def json_with_headers(request):
    """Example of JSON response with custom headers"""
    return JSONResponse(
        {
            "message": "Success",
            "timestamp": "2024-03-21T12:00:00Z",
            "router_group": "examples"
        },
        headers={
            "X-Custom-Header": "Special Value",
            "X-Rate-Limit": "100"
        }
    )

@examples_router.get("/styled-html")
def styled_html(request):
    """Example of HTML response with CSS styling"""
    return HTMLResponse("""
        <!DOCTYPE html>
        <html>
            <head>
                <style>
                    body {
                        font-family: Arial, sans-serif;
                        margin: 40px;
                        background: #f0f0f0;
                    }
                    .card {
                        background: white;
                        padding: 20px;
                        border-radius: 8px;
                        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                    }
                    h1 { color: #2c3e50; }
                    .highlight { color: #e74c3c; }
                    .router-info { color: #27ae60; font-weight: bold; }
                </style>
            </head>
            <body>
                <div class="card">
                    <h1>Styled HTML Example</h1>
                    <p>This is a <span class="highlight">beautifully styled</span> HTML response.</p>
                    <p>It demonstrates how to return HTML with embedded CSS.</p>
                    <p class="router-info">Served by: examples RouterGroup</p>
                </div>
            </body>
        </html>
    """)

#  path param /users/{id} - direct on app to show mixed usage
@app.get("/users/{id}")
def user_detail(request):
    """Example of returning a user detail"""
    query_params = request.query_params
    return JSONResponse({
        "message": "User detail",
        "id": request.path_params["id"],
        "query_params": query_params,
        "note": "This route is registered directly on the app, not in a RouterGroup"
    })

# Include all router groups in the app
app.include_routes(api_router)
app.include_routes(demo_router)
app.include_routes(examples_router)

if __name__ == "__main__":
    print("[INFO-PY-FROM-EXAMPLE] Starting Catzilla server on http://localhost:8000")
    app.listen(8080)
