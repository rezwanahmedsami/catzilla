"""
Catzilla RouterGroup Example

This example demonstrates the RouterGroup functionality
for organizing routes with shared prefixes and metadata.
"""

from catzilla import Catzilla, Response, JSONResponse, HTMLResponse, RouterGroup

app = Catzilla(auto_validation=True, memory_profiling=False)

# Home page with RouterGroup demo
@app.get("/")
def home(request):
    return HTMLResponse("""
    <!DOCTYPE html>
    <html>
        <head>
            <title>Catzilla RouterGroup Example</title>
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
                .api-section {
                    margin: 20px 0;
                    padding: 20px;
                    border: 1px solid #e0e0e0;
                    border-radius: 4px;
                    background: #f9f9f9;
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
                    font-weight: bold;
                    padding: 2px 6px;
                    border-radius: 3px;
                    font-size: 12px;
                }
                .get { background: #d1ecf1; color: #0c5460; }
                .post { background: #d4edda; color: #155724; }
                .put { background: #fff3cd; color: #856404; }
                .delete { background: #f8d7da; color: #721c24; }
                code {
                    background: #f4f4f4;
                    padding: 2px 4px;
                    border-radius: 3px;
                }
            </style>
        </head>
        <body>
            <h1>🐱 Catzilla RouterGroup Example</h1>
            <p>This example demonstrates the RouterGroup functionality for organizing routes with shared prefixes.</p>

            <h2>Router Groups in this Example</h2>

            <div class="api-section">
                <h3>API v1 Group (/api/v1)</h3>
                <ul class="api-list">
                    <li><span class="method get">GET</span> <a href="/api/v1/status">/api/v1/status</a> - API status check</li>
                    <li><span class="method get">GET</span> <a href="/api/v1/info">/api/v1/info</a> - API information</li>
                </ul>
            </div>

            <div class="api-section">
                <h3>Users Group (/api/v1/users)</h3>
                <ul class="api-list">
                    <li><span class="method get">GET</span> <a href="/api/v1/users">/api/v1/users</a> - List all users</li>
                    <li><span class="method post">POST</span> <code>/api/v1/users</code> - Create a new user</li>
                    <li><span class="method get">GET</span> <a href="/api/v1/users/123">/api/v1/users/{user_id}</a> - Get user by ID</li>
                    <li><span class="method put">PUT</span> <code>/api/v1/users/{user_id}</code> - Update user</li>
                    <li><span class="method delete">DELETE</span> <code>/api/v1/users/{user_id}</code> - Delete user</li>
                </ul>
            </div>

            <div class="api-section">
                <h3>Posts Group (/api/v1/posts)</h3>
                <ul class="api-list">
                    <li><span class="method get">GET</span> <a href="/api/v1/posts">/api/v1/posts</a> - List all posts</li>
                    <li><span class="method post">POST</span> <code>/api/v1/posts</code> - Create a new post</li>
                    <li><span class="method get">GET</span> <a href="/api/v1/posts/456">/api/v1/posts/{post_id}</a> - Get post by ID</li>
                </ul>
            </div>

            <div class="api-section">
                <h3>Admin Group (/admin)</h3>
                <ul class="api-list">
                    <li><span class="method get">GET</span> <a href="/admin/dashboard">/admin/dashboard</a> - Admin dashboard</li>
                    <li><span class="method get">GET</span> <a href="/admin/stats">/admin/stats</a> - System statistics</li>
                </ul>
            </div>

            <h2>RouterGroup Features Demonstrated</h2>
            <ul>
                <li><strong>Shared Prefixes:</strong> Routes organized under common path prefixes</li>
                <li><strong>Tags and Metadata:</strong> Routes tagged for API organization and future OpenAPI support</li>
                <li><strong>Group Nesting:</strong> Users and posts groups included in API v1 group</li>
                <li><strong>Multiple Groups:</strong> Separate admin group with different prefix</li>
                <li><strong>Route Registration:</strong> All groups registered with <code>app.include_routes()</code></li>
            </ul>

            <h2>Source Code</h2>
            <p>Check out <code>examples/router_groups/main.py</code> to see how this is implemented!</p>
        </body>
    </html>
    """)

# Create API v1 group with shared prefix and metadata
api_v1_group = RouterGroup(
    prefix="/api/v1",
    tags=["api", "v1"],
    description="API version 1 endpoints",
    metadata={
        "version": "1.0.0",
        "documentation": "https://docs.example.com/api/v1"
    }
)

@api_v1_group.get("/status")
def api_status(request):
    """API status endpoint"""
    return JSONResponse({
        "status": "ok",
        "version": "1.0.0",
        "timestamp": "2024-01-01T00:00:00Z",
        "message": "API v1 is running"
    })

@api_v1_group.get("/info")
def api_info(request):
    """API information endpoint"""
    return JSONResponse({
        "api": {
            "name": "Catzilla API",
            "version": "1.0.0",
            "description": "Demonstration of RouterGroup functionality",
            "endpoints": {
                "users": "/api/v1/users",
                "posts": "/api/v1/posts",
                "status": "/api/v1/status"
            }
        },
        "server": {
            "framework": "Catzilla",
            "features": [
                "Dynamic routing",
                "Route groups",
                "Path parameters",
                "HTTP method decorators"
            ]
        }
    })

# Create Users group
users_group = RouterGroup(
    prefix="/users",
    tags=["users", "resources"],
    description="User management endpoints"
)

@users_group.get("/")
def list_users(request):
    """List all users"""
    return JSONResponse({
        "users": [
            {"id": 1, "name": "Alice Johnson", "email": "alice@example.com"},
            {"id": 2, "name": "Bob Smith", "email": "bob@example.com"},
            {"id": 3, "name": "Charlie Brown", "email": "charlie@example.com"}
        ],
        "total": 3,
        "page": 1,
        "per_page": 10
    })

@users_group.post("/")
def create_user(request):
    """Create a new user"""
    return JSONResponse({
        "message": "User created successfully",
        "user": {
            "id": 4,
            "name": "New User",
            "email": "newuser@example.com"
        }
    }, status_code=201)

@users_group.get("/{user_id}")
def get_user(request):
    """Get user by ID"""
    user_id = request.path_params.get("user_id")
    return JSONResponse({
        "user": {
            "id": int(user_id),
            "name": f"User {user_id}",
            "email": f"user{user_id}@example.com",
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:00:00Z"
        }
    })

@users_group.put("/{user_id}")
def update_user(request):
    """Update user by ID"""
    user_id = request.path_params.get("user_id")
    return JSONResponse({
        "message": f"User {user_id} updated successfully",
        "user": {
            "id": int(user_id),
            "name": f"Updated User {user_id}",
            "email": f"updated{user_id}@example.com"
        }
    })

@users_group.delete("/{user_id}")
def delete_user(request):
    """Delete user by ID"""
    user_id = request.path_params.get("user_id")
    return JSONResponse({
        "message": f"User {user_id} deleted successfully"
    })

# Create Posts group
posts_group = RouterGroup(
    prefix="/posts",
    tags=["posts", "content"],
    description="Post management endpoints"
)

@posts_group.get("/")
def list_posts(request):
    """List all posts"""
    return JSONResponse({
        "posts": [
            {
                "id": 1,
                "title": "Getting Started with Catzilla",
                "author_id": 1,
                "content": "Learn how to build web applications with Catzilla...",
                "created_at": "2024-01-01T00:00:00Z"
            },
            {
                "id": 2,
                "title": "Advanced Routing with RouterGroups",
                "author_id": 2,
                "content": "Explore the powerful RouterGroup functionality...",
                "created_at": "2024-01-02T00:00:00Z"
            }
        ],
        "total": 2,
        "page": 1,
        "per_page": 10
    })

@posts_group.post("/")
def create_post(request):
    """Create a new post"""
    return JSONResponse({
        "message": "Post created successfully",
        "post": {
            "id": 3,
            "title": "New Post",
            "author_id": 1,
            "content": "This is a new post created via the API",
            "created_at": "2024-01-03T00:00:00Z"
        }
    }, status_code=201)

@posts_group.get("/{post_id}")
def get_post(request):
    """Get post by ID"""
    post_id = request.path_params.get("post_id")
    return JSONResponse({
        "post": {
            "id": int(post_id),
            "title": f"Post {post_id}",
            "author_id": 1,
            "content": f"This is the content of post {post_id}...",
            "created_at": "2024-01-01T00:00:00Z",
            "tags": ["example", "demo"]
        }
    })

# Include users and posts groups in the API v1 group
api_v1_group.include_group(users_group)
api_v1_group.include_group(posts_group)

# Create Admin group (separate from API)
admin_group = RouterGroup(
    prefix="/admin",
    tags=["admin", "internal"],
    description="Administrative endpoints"
)

@admin_group.get("/dashboard")
def admin_dashboard(request):
    """Admin dashboard"""
    return JSONResponse({
        "dashboard": {
            "total_users": 3,
            "total_posts": 2,
            "server_uptime": "1 day, 2 hours, 30 minutes",
            "memory_usage": "45%",
            "cpu_usage": "12%"
        },
        "recent_activity": [
            {"action": "User created", "timestamp": "2024-01-03T10:30:00Z"},
            {"action": "Post published", "timestamp": "2024-01-03T09:15:00Z"},
            {"action": "User login", "timestamp": "2024-01-03T08:45:00Z"}
        ]
    })

@admin_group.get("/stats")
def admin_stats(request):
    """System statistics"""
    return JSONResponse({
        "statistics": {
            "requests": {
                "total": 1247,
                "today": 156,
                "errors": 3,
                "avg_response_time": "45ms"
            },
            "users": {
                "total": 3,
                "active": 2,
                "new_today": 0
            },
            "posts": {
                "total": 2,
                "published": 2,
                "draft": 0
            }
        },
        "system": {
            "version": "1.0.0",
            "uptime": "1 day, 2 hours, 30 minutes",
            "environment": "development"
        }
    })

# Include all groups in the main app
app.include_routes(api_v1_group)
app.include_routes(admin_group)

# Health check endpoint (not in any group)
@app.get("/health")
def health_check(request):
    """Health check endpoint"""
    return JSONResponse({
        "status": "healthy",
        "timestamp": "2024-01-01T00:00:00Z",
        "checks": {
            "database": "ok",
            "cache": "ok",
            "external_api": "ok"
        }
    })

if __name__ == "__main__":
    print("Starting Catzilla RouterGroup Example Server...")
    print("\nRoutes registered:")
    for route in app.routes():
        print(f"  {route['method']:6} {route['path']}")

    print(f"\nTotal routes: {len(app.routes())}")
    print("\nVisit http://localhost:8000 to see the demo!")

    app.listen(8000)
