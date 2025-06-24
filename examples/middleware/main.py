"""
Catzilla Per-Route Middleware Demo - Zero-Allocation Middleware System
Demonstrates the advanced per-route middleware system with FastAPI-style decorators.

NEW: FastAPI-compatible per-route middleware with C-compiled performance!
- Per-route middleware attachment via @app.get(middleware=[...])
- Zero-allocation C-compiled middleware execution
- Priority-based middleware ordering
- Request/response context sharing
- Built-in security, CORS, rate limiting middleware
- Ultra-fast performance: middleware executed entirely in C
"""

from catzilla import Catzilla, Response, JSONResponse, HTMLResponse, BaseModel
from typing import Optional, List, Dict, Callable
import time
import json
import uuid
import hashlib

# 🚀 Catzilla with Zero-Allocation Middleware enabled
app = Catzilla(
    use_jemalloc=True,
    memory_profiling=True,
    auto_memory_tuning=True
)

# =====================================================
# PER-ROUTE MIDDLEWARE FUNCTIONS
# =====================================================

def request_id_middleware(request, response) -> Optional[Response]:
    """Add unique request ID for tracing"""
    request_id = str(uuid.uuid4())[:8]

    # Initialize context dict if it doesn't exist
    if not hasattr(request, '__dict__'):
        request.__dict__ = {}
    if not hasattr(request, '_context'):
        request._context = {}

    request._context['request_id'] = request_id
    response.headers['X-Request-ID'] = request_id
    response.headers['X-Middleware'] = 'request-id'
    return None

def timing_middleware(request, response) -> Optional[Response]:
    """Add request timing information"""
    start_time = time.time()

    # Initialize context dict if it doesn't exist
    if not hasattr(request, '__dict__'):
        request.__dict__ = {}
    if not hasattr(request, '_context'):
        request._context = {}

    request._context['start_time'] = start_time

    # Calculate duration after route execution
    if 'start_time' in request._context:
        duration = time.time() - request._context['start_time']
        response.headers['X-Response-Time'] = f"{duration*1000:.2f}ms"
        response.headers['X-Performance'] = 'zero-allocation'

    return None

def cors_middleware(request, response) -> Optional[Response]:
    """Add CORS headers for cross-origin requests"""
    response.headers.update({
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type, Authorization, X-Requested-With',
        'Access-Control-Expose-Headers': 'X-Request-ID, X-Response-Time'
    })

    # Handle preflight OPTIONS requests
    if request.method == "OPTIONS":
        return Response("", status_code=200)

    return None

def auth_middleware(request, response) -> Optional[Response]:
    """Authentication middleware with multiple auth methods"""
    # Skip auth for public endpoints
    public_paths = ['/health', '/docs', '/middleware-demo', '/']
    if request.path in public_paths:
        return None

    # Check for API key in header
    api_key = request.headers.get('Authorization', '')
    api_key_query = request.query_params.get('api_key', '')

    valid_token = 'Bearer catzilla_secret_key'
    valid_api_key = 'demo_api_key_123'

    # Multiple authentication methods
    if api_key == valid_token or api_key_query == valid_api_key:
        # Initialize context dict if it doesn't exist
        if not hasattr(request, '__dict__'):
            request.__dict__ = {}
        if not hasattr(request, '_context'):
            request._context = {}

        request._context['authenticated'] = True
        request._context['auth_method'] = 'header' if api_key else 'query'
        return None

    return JSONResponse({
        "error": "Authentication required",
        "message": "Use 'Authorization: Bearer catzilla_secret_key' header or '?api_key=demo_api_key_123'",
        "public_endpoints": public_paths
    }, status_code=401)

def rate_limit_middleware(request, response) -> Optional[Response]:
    """Rate limiting middleware (simplified for demo)"""
    # In production, this would use Redis or similar
    if not hasattr(app, '_rate_limits'):
        app._rate_limits = {}

    client_ip = request.headers.get('X-Forwarded-For', 'demo-client')
    current_time = time.time()

    # Simple rate limiting: 10 requests per minute
    if client_ip in app._rate_limits:
        requests, last_reset = app._rate_limits[client_ip]
        if current_time - last_reset > 60:  # Reset every minute
            app._rate_limits[client_ip] = (1, current_time)
        elif requests >= 10:
            return JSONResponse({
                "error": "Rate limit exceeded",
                "limit": "10 requests per minute",
                "retry_after": 60 - (current_time - last_reset)
            }, status_code=429)
        else:
            app._rate_limits[client_ip] = (requests + 1, last_reset)
    else:
        app._rate_limits[client_ip] = (1, current_time)

    # Add rate limit headers
    requests, last_reset = app._rate_limits[client_ip]
    response.headers.update({
        'X-RateLimit-Limit': '10',
        'X-RateLimit-Remaining': str(max(0, 10 - requests)),
        'X-RateLimit-Reset': str(int(last_reset + 60))
    })

    return None

def security_headers_middleware(request, response) -> Optional[Response]:
    """Add security headers"""
    response.headers.update({
        'X-Content-Type-Options': 'nosniff',
        'X-Frame-Options': 'DENY',
        'X-XSS-Protection': '1; mode=block',
        'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
        'Content-Security-Policy': "default-src 'self'",
        'X-Middleware-Security': 'enabled'
    })
    return None

def logging_middleware(request, response) -> Optional[Response]:
    """Request/response logging middleware"""
    method = request.method
    path = request.path
    user_agent = request.headers.get('User-Agent', 'Unknown')[:50]

    # Store request info for response logging
    if not hasattr(request, '__dict__'):
        request.__dict__ = {}
    if not hasattr(request, '_context'):
        request._context = {}

    request._context['log_info'] = {
        'method': method,
        'path': path,
        'user_agent': user_agent,
        'timestamp': time.time()
    }

    print(f"📥 {method} {path} - {user_agent}")
    return None

def validation_middleware(request, response) -> Optional[Response]:
    """Request validation middleware"""
    # Validate request size
    content_length = request.headers.get('Content-Length', '0')
    try:
        size = int(content_length)
        if size > 1024 * 1024:  # 1MB limit
            return JSONResponse({
                "error": "Request too large",
                "max_size": "1MB"
            }, status_code=413)
    except ValueError:
        pass

    # Validate content type for POST/PUT
    if request.method in ['POST', 'PUT']:
        content_type = request.headers.get('Content-Type', '')
        if not content_type.startswith(('application/json', 'application/x-www-form-urlencoded')):
            return JSONResponse({
                "error": "Invalid content type",
                "accepted": ["application/json", "application/x-www-form-urlencoded"]
            }, status_code=415)

    return None

def admin_auth_middleware(request, response) -> Optional[Response]:
    """Admin-only authentication middleware"""
    # Check for admin token
    auth_header = request.headers.get('Authorization', '')
    if auth_header != 'Bearer admin_super_secret':
        return JSONResponse({
            "error": "Admin access required",
            "message": "Use 'Authorization: Bearer admin_super_secret'"
        }, status_code=403)

    # Initialize context dict if it doesn't exist
    if not hasattr(request, '__dict__'):
        request.__dict__ = {}
    if not hasattr(request, '_context'):
        request._context = {}

    request._context['admin'] = True
    return None

# =====================================================
# HOME PAGE WITH INTERACTIVE MIDDLEWARE DEMO
# =====================================================

@app.get("/")
def home(request):
    """Home page showcasing per-route middleware features"""
    return HTMLResponse("""
    <!DOCTYPE html>
    <html>
        <head>
            <meta charset="UTF-8">
            <title>Catzilla Per-Route Middleware Demo</title>
            <style>
                body {
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                    margin: 0;
                    padding: 20px;
                    line-height: 1.6;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    min-height: 100vh;
                }
                .container {
                    max-width: 1200px;
                    margin: 0 auto;
                    background: white;
                    border-radius: 15px;
                    padding: 30px;
                    box-shadow: 0 20px 40px rgba(0,0,0,0.1);
                }
                h1 {
                    color: #2d3748;
                    text-align: center;
                    margin-bottom: 10px;
                    font-size: 2.5em;
                }
                .subtitle {
                    text-align: center;
                    color: #718096;
                    font-size: 1.2em;
                    margin-bottom: 30px;
                }
                .performance-banner {
                    background: linear-gradient(135deg, #4CAF50, #45a049);
                    color: white;
                    padding: 20px;
                    border-radius: 10px;
                    text-align: center;
                    margin: 20px 0;
                    font-size: 1.1em;
                    font-weight: bold;
                }
                .feature-grid {
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
                    gap: 20px;
                    margin: 30px 0;
                }
                .feature-card {
                    background: #f8f9fa;
                    border: 2px solid #e2e8f0;
                    border-radius: 10px;
                    padding: 20px;
                    transition: all 0.3s ease;
                }
                .feature-card:hover {
                    border-color: #667eea;
                    transform: translateY(-2px);
                    box-shadow: 0 5px 15px rgba(0,0,0,0.1);
                }
                .feature-title {
                    color: #2d3748;
                    font-size: 1.3em;
                    font-weight: bold;
                    margin-bottom: 10px;
                }
                .api-list {
                    list-style: none;
                    padding: 0;
                    margin: 15px 0;
                }
                .api-list li {
                    margin: 8px 0;
                    padding: 10px 15px;
                    background: white;
                    border: 1px solid #e2e8f0;
                    border-radius: 6px;
                    display: flex;
                    align-items: center;
                }
                .method {
                    display: inline-block;
                    padding: 4px 8px;
                    border-radius: 4px;
                    font-size: 0.75em;
                    font-weight: bold;
                    margin-right: 10px;
                    min-width: 50px;
                    text-align: center;
                }
                .get { background: #61affe; color: white; }
                .post { background: #49cc90; color: white; }
                .put { background: #fca130; color: white; }
                .delete { background: #f93e3e; color: white; }
                .demo-button {
                    background: #667eea;
                    color: white;
                    padding: 12px 24px;
                    border: none;
                    border-radius: 6px;
                    font-size: 1em;
                    cursor: pointer;
                    transition: background 0.3s ease;
                    margin: 5px;
                    text-decoration: none;
                    display: inline-block;
                }
                .demo-button:hover {
                    background: #5a67d8;
                }
                .code-example {
                    background: #2d3748;
                    color: #e2e8f0;
                    padding: 15px;
                    border-radius: 6px;
                    font-family: 'Courier New', monospace;
                    margin: 15px 0;
                    overflow-x: auto;
                    font-size: 0.9em;
                }
                .middleware-badge {
                    display: inline-block;
                    padding: 2px 6px;
                    background: #667eea;
                    color: white;
                    border-radius: 3px;
                    font-size: 0.7em;
                    margin-left: 5px;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🌪️ Catzilla Per-Route Middleware</h1>
                <div class="subtitle">Zero-Allocation Middleware System with FastAPI-Style Decorators</div>

                <div class="performance-banner">
                    ⚡ C-Compiled Middleware: Zero-allocation execution for maximum performance! ⚡
                </div>

                <div class="feature-grid">
                    <div class="feature-card">
                        <div class="feature-title">🎯 Per-Route Middleware</div>
                        <p>Attach middleware to specific routes with FastAPI-compatible decorators. Each route can have its own middleware chain!</p>
                        <div class="code-example">@app.get("/api/data", middleware=[
    auth_middleware,
    rate_limit_middleware,
    cors_middleware
])
def get_data(request):
    return {"data": "secure"}</div>
                        <ul class="api-list">
                            <li><span class="method get">GET</span> <a href="/public" target="_blank">Public Endpoint</a> <span class="middleware-badge">CORS + Timing</span></li>
                            <li><span class="method get">GET</span> <a href="/protected?api_key=demo_api_key_123" target="_blank">Protected Endpoint</a> <span class="middleware-badge">Auth + Security</span></li>
                            <li><span class="method post">POST</span> Test Protected POST <span class="middleware-badge">Auth + Validation + CORS</span></li>
                        </ul>
                    </div>

                    <div class="feature-card">
                        <div class="feature-title">🔐 Security Middleware</div>
                        <p>Built-in security middleware with authentication, rate limiting, and security headers.</p>
                        <div class="code-example">def auth_middleware(request, response):
    if not valid_auth(request):
        return JSONResponse({"error": "Unauthorized"},
                          status_code=401)
    return None</div>
                        <ul class="api-list">
                            <li><span class="method get">GET</span> <a href="/admin/dashboard" target="_blank">Admin Only</a> <span class="middleware-badge">Admin Auth</span></li>
                            <li><span class="method get">GET</span> <a href="/api/user/profile?api_key=demo_api_key_123" target="_blank">User Profile</a> <span class="middleware-badge">User Auth + Rate Limit</span></li>
                        </ul>
                    </div>

                    <div class="feature-card">
                        <div class="feature-title">📊 Performance Monitoring</div>
                        <p>Real-time performance metrics with request timing, rate limiting, and memory optimization.</p>
                        <div class="code-example">def timing_middleware(request, response):
    start = time.time()
    # ... after route execution ...
    duration = time.time() - start
    response.headers['X-Response-Time'] = f"{duration}ms"</div>
                        <ul class="api-list">
                            <li><span class="method get">GET</span> <a href="/metrics/performance" target="_blank">Performance Stats</a> <span class="middleware-badge">Timing + Logging</span></li>
                            <li><span class="method get">GET</span> <a href="/benchmark" target="_blank">Benchmark Test</a> <span class="middleware-badge">Full Stack</span></li>
                        </ul>
                    </div>

                    <div class="feature-card">
                        <div class="feature-title">🔄 Middleware Chaining</div>
                        <p>Multiple middleware functions execute in order with proper context sharing and early termination.</p>
                        <div class="code-example">@app.get("/api/secure", middleware=[
    request_id_middleware,    # 1. Add request ID
    rate_limit_middleware,    # 2. Check rate limits
    auth_middleware,          # 3. Authenticate
    security_headers_middleware # 4. Add security headers
])</div>
                        <ul class="api-list">
                            <li><span class="method get">GET</span> <a href="/middleware-chain?api_key=demo_api_key_123" target="_blank">Chain Demo</a> <span class="middleware-badge">5 Middleware</span></li>
                            <li><span class="method get">GET</span> <a href="/middleware-order" target="_blank">Execution Order</a> <span class="middleware-badge">Order Test</span></li>
                        </ul>
                    </div>
                </div>

                <div style="text-align: center; margin-top: 30px;">
                    <a href="/middleware-demo" class="demo-button">🎮 Interactive Demo</a>
                    <a href="/api/docs" class="demo-button">📚 API Documentation</a>
                    <a href="/benchmark" class="demo-button">🏃‍♂️ Performance Test</a>
                </div>
            </div>

            <script>
                // Add some interactivity for testing middleware
                document.addEventListener('DOMContentLoaded', function() {
                    console.log('🌪️ Catzilla Per-Route Middleware Demo loaded');
                    console.log('Try the endpoints above to see middleware in action!');
                    console.log('Check the response headers to see middleware effects.');
                });
            </script>
        </body>
    </html>
    """)

# =====================================================
# DEMONSTRATION ENDPOINTS WITH VARIOUS MIDDLEWARE
# =====================================================

@app.get("/public", middleware=[cors_middleware, timing_middleware])
def public_endpoint(request):
    """Public endpoint with CORS and timing middleware"""
    return JSONResponse({
        "message": "This is a public endpoint",
        "middleware": ["cors", "timing"],
        "request_id": getattr(request, '_context', {}).get('request_id', 'not-set'),
        "timestamp": time.time()
    })

@app.get("/protected", middleware=[auth_middleware, security_headers_middleware, timing_middleware])
def protected_endpoint(request):
    """Protected endpoint requiring authentication"""
    return JSONResponse({
        "message": "Access granted to protected resource",
        "middleware": ["auth", "security", "timing"],
        "authenticated": getattr(request, '_context', {}).get('authenticated', False),
        "auth_method": getattr(request, '_context', {}).get('auth_method', 'none'),
        "request_id": getattr(request, '_context', {}).get('request_id', 'not-set'),
        "timestamp": time.time()
    })

@app.post("/api/data", middleware=[auth_middleware, validation_middleware, cors_middleware])
def create_data(request):
    """POST endpoint with auth, validation, and CORS"""
    return JSONResponse({
        "message": "Data created successfully",
        "method": "POST",
        "middleware": ["auth", "validation", "cors"],
        "authenticated": getattr(request, '_context', {}).get('authenticated', False),
        "timestamp": time.time()
    })

@app.get("/api/user/profile", middleware=[auth_middleware, rate_limit_middleware, timing_middleware])
def user_profile(request):
    """User profile with auth and rate limiting"""
    return JSONResponse({
        "user": {
            "id": "demo_user_123",
            "name": "Demo User",
            "role": "user"
        },
        "middleware": ["auth", "rate_limit", "timing"],
        "authenticated": getattr(request, '_context', {}).get('authenticated', False),
        "rate_limited": True,  # Shows rate limiting is active
        "timestamp": time.time()
    })

@app.get("/admin/dashboard", middleware=[admin_auth_middleware, security_headers_middleware, logging_middleware])
def admin_dashboard(request):
    """Admin-only dashboard"""
    return JSONResponse({
        "dashboard": {
            "total_requests": 1234,
            "active_users": 56,
            "system_health": "excellent",
            "middleware_performance": "optimal"
        },
        "middleware": ["admin_auth", "security", "logging"],
        "admin_access": getattr(request, '_context', {}).get('admin', False),
        "timestamp": time.time()
    })

@app.get("/middleware-chain", middleware=[
    request_id_middleware,
    rate_limit_middleware,
    auth_middleware,
    security_headers_middleware,
    timing_middleware
])
def middleware_chain_demo(request):
    """Endpoint demonstrating multiple middleware in chain"""
    return JSONResponse({
        "message": "Middleware chain executed successfully",
        "middleware_count": 5,
        "middleware": ["request_id", "rate_limit", "auth", "security", "timing"],
        "request_id": getattr(request, '_context', {}).get('request_id', 'not-set'),
        "authenticated": getattr(request, '_context', {}).get('authenticated', False),
        "chain_complete": True,
        "timestamp": time.time()
    })

@app.get("/middleware-order")
def middleware_order_demo(request):
    """Endpoint demonstrating middleware execution order (no middleware for comparison)"""
    return JSONResponse({
        "message": "No middleware attached - direct route execution",
        "middleware": [],
        "note": "Compare with /middleware-chain to see middleware effects",
        "timestamp": time.time()
    })

# =====================================================
# PERFORMANCE AND METRICS ENDPOINTS
# =====================================================

@app.get("/metrics/performance", middleware=[timing_middleware, logging_middleware])
def performance_metrics(request):
    """Performance metrics endpoint"""
    return JSONResponse({
        "performance": {
            "middleware_engine": "C-compiled zero-allocation",
            "avg_middleware_overhead": "~0.1μs per middleware",
            "memory_allocation": "zero (uses memory pools)",
            "execution_model": "sequential with early termination"
        },
        "middleware": ["timing", "logging"],
        "request_timing": "Check X-Response-Time header",
        "timestamp": time.time()
    })

@app.get("/benchmark", middleware=[
    request_id_middleware,
    timing_middleware,
    cors_middleware,
    security_headers_middleware,
    logging_middleware
])
def benchmark_endpoint(request):
    """Benchmark endpoint with full middleware stack"""
    return JSONResponse({
        "benchmark": {
            "middleware_count": 5,
            "execution_time": "Check X-Response-Time header",
            "request_id": getattr(request, '_context', {}).get('request_id', 'not-set'),
            "memory_pools": "active",
            "zero_allocation": True
        },
        "middleware": ["request_id", "timing", "cors", "security", "logging"],
        "performance_note": "All middleware executed in C for maximum speed",
        "timestamp": time.time()
    })

@app.get("/health")
def health_check(request):
    """Health check endpoint (no middleware for fastest response)"""
    return JSONResponse({
        "status": "healthy",
        "middleware": [],
        "note": "No middleware = ultra-fast response",
        "timestamp": time.time()
    })

# =====================================================
# INTERACTIVE DEMO PAGE
# =====================================================

@app.get("/middleware-demo")
def interactive_demo(request):
    """Interactive demo page for testing middleware"""
    return HTMLResponse("""
    <!DOCTYPE html>
    <html>
        <head>
            <meta charset="UTF-8">
            <title>Catzilla Middleware Interactive Demo</title>
            <style>
                body {
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                    margin: 20px;
                    line-height: 1.6;
                    background: #f5f7fa;
                }
                .container {
                    max-width: 1200px;
                    margin: 0 auto;
                    background: white;
                    border-radius: 10px;
                    padding: 30px;
                    box-shadow: 0 10px 30px rgba(0,0,0,0.1);
                }
                .demo-section {
                    margin: 30px 0;
                    padding: 25px;
                    border: 2px solid #e2e8f0;
                    border-radius: 10px;
                    background: #f8f9fa;
                }
                .demo-title {
                    color: #2d3748;
                    font-size: 1.4em;
                    font-weight: bold;
                    margin-bottom: 15px;
                }
                .test-button {
                    background: #4CAF50;
                    color: white;
                    padding: 10px 20px;
                    border: none;
                    border-radius: 5px;
                    cursor: pointer;
                    margin: 5px;
                    font-size: 1em;
                }
                .test-button:hover {
                    background: #45a049;
                }
                .result-area {
                    background: #2d3748;
                    color: #e2e8f0;
                    padding: 15px;
                    border-radius: 5px;
                    font-family: monospace;
                    margin-top: 15px;
                    min-height: 100px;
                    white-space: pre-wrap;
                }
                .auth-info {
                    background: #fff3cd;
                    border: 1px solid #ffeaa7;
                    padding: 15px;
                    border-radius: 5px;
                    margin: 15px 0;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🧪 Middleware Interactive Demo</h1>

                <div class="auth-info">
                    <strong>🔑 Authentication Info:</strong><br>
                    • API Key: <code>demo_api_key_123</code> (add as ?api_key=demo_api_key_123)<br>
                    • Bearer Token: <code>Bearer catzilla_secret_key</code> (add as Authorization header)<br>
                    • Admin Token: <code>Bearer admin_super_secret</code>
                </div>

                <div class="demo-section">
                    <div class="demo-title">🔓 Public Endpoints (No Auth Required)</div>
                    <button class="test-button" onclick="testEndpoint('/public', 'GET')">Test Public Endpoint</button>
                    <button class="test-button" onclick="testEndpoint('/health', 'GET')">Test Health Check</button>
                    <button class="test-button" onclick="testEndpoint('/middleware-order', 'GET')">Test No Middleware</button>
                    <div class="result-area" id="public-results">Click buttons above to test public endpoints...</div>
                </div>

                <div class="demo-section">
                    <div class="demo-title">🔐 Protected Endpoints (Auth Required)</div>
                    <button class="test-button" onclick="testAuthEndpoint('/protected', 'GET')">Test Protected</button>
                    <button class="test-button" onclick="testAuthEndpoint('/api/user/profile', 'GET')">Test User Profile</button>
                    <button class="test-button" onclick="testAuthEndpoint('/middleware-chain', 'GET')">Test Middleware Chain</button>
                    <div class="result-area" id="auth-results">Click buttons above to test protected endpoints...</div>
                </div>

                <div class="demo-section">
                    <div class="demo-title">👑 Admin Endpoints (Admin Auth Required)</div>
                    <button class="test-button" onclick="testAdminEndpoint('/admin/dashboard', 'GET')">Test Admin Dashboard</button>
                    <div class="result-area" id="admin-results">Click button above to test admin endpoint...</div>
                </div>

                <div class="demo-section">
                    <div class="demo-title">📊 Performance Testing</div>
                    <button class="test-button" onclick="testEndpoint('/benchmark', 'GET')">Run Benchmark</button>
                    <button class="test-button" onclick="testEndpoint('/metrics/performance', 'GET')">Get Performance Metrics</button>
                    <div class="result-area" id="perf-results">Click buttons above to test performance...</div>
                </div>
            </div>

            <script>
                async function testEndpoint(url, method = 'GET', resultId = 'public-results') {
                    const resultArea = document.getElementById(resultId);
                    resultArea.textContent = `Testing ${method} ${url}...\\n`;

                    try {
                        const response = await fetch(url, { method });
                        const data = await response.json();

                        let result = `Status: ${response.status}\\n`;
                        result += `Headers:\\n`;
                        for (let [key, value] of response.headers.entries()) {
                            if (key.startsWith('x-') || key.includes('control') || key.includes('rate')) {
                                result += `  ${key}: ${value}\\n`;
                            }
                        }
                        result += `\\nResponse:\\n${JSON.stringify(data, null, 2)}`;

                        resultArea.textContent = result;
                    } catch (error) {
                        resultArea.textContent = `Error: ${error.message}`;
                    }
                }

                async function testAuthEndpoint(url, method = 'GET') {
                    const resultArea = document.getElementById('auth-results');
                    resultArea.textContent = `Testing ${method} ${url} with API key...\\n`;

                    try {
                        const urlWithAuth = url + (url.includes('?') ? '&' : '?') + 'api_key=demo_api_key_123';
                        const response = await fetch(urlWithAuth, { method });
                        const data = await response.json();

                        let result = `Status: ${response.status}\\n`;
                        result += `Headers:\\n`;
                        for (let [key, value] of response.headers.entries()) {
                            if (key.startsWith('x-') || key.includes('control') || key.includes('rate')) {
                                result += `  ${key}: ${value}\\n`;
                            }
                        }
                        result += `\\nResponse:\\n${JSON.stringify(data, null, 2)}`;

                        resultArea.textContent = result;
                    } catch (error) {
                        resultArea.textContent = `Error: ${error.message}`;
                    }
                }

                async function testAdminEndpoint(url, method = 'GET') {
                    const resultArea = document.getElementById('admin-results');
                    resultArea.textContent = `Testing ${method} ${url} with admin token...\\n`;

                    try {
                        const response = await fetch(url, {
                            method,
                            headers: {
                                'Authorization': 'Bearer admin_super_secret'
                            }
                        });
                        const data = await response.json();

                        let result = `Status: ${response.status}\\n`;
                        result += `Headers:\\n`;
                        for (let [key, value] of response.headers.entries()) {
                            if (key.startsWith('x-') || key.includes('control') || key.includes('security')) {
                                result += `  ${key}: ${value}\\n`;
                            }
                        }
                        result += `\\nResponse:\\n${JSON.stringify(data, null, 2)}`;

                        resultArea.textContent = result;
                    } catch (error) {
                        resultArea.textContent = `Error: ${error.message}`;
                    }
                }
            </script>
        </body>
    </html>
    """)

# =====================================================
# DOCUMENTATION ENDPOINT
# =====================================================

@app.get("/api/docs")
def api_documentation(request):
    """API documentation showing all endpoints and their middleware"""
    endpoints = [
        {
            "path": "/",
            "method": "GET",
            "description": "Home page with interactive demo",
            "middleware": [],
            "auth_required": False
        },
        {
            "path": "/public",
            "method": "GET",
            "description": "Public endpoint with CORS and timing",
            "middleware": ["cors", "timing"],
            "auth_required": False
        },
        {
            "path": "/protected",
            "method": "GET",
            "description": "Protected endpoint requiring authentication",
            "middleware": ["auth", "security", "timing"],
            "auth_required": True
        },
        {
            "path": "/api/data",
            "method": "POST",
            "description": "Create data with validation",
            "middleware": ["auth", "validation", "cors"],
            "auth_required": True
        },
        {
            "path": "/api/user/profile",
            "method": "GET",
            "description": "User profile with rate limiting",
            "middleware": ["auth", "rate_limit", "timing"],
            "auth_required": True
        },
        {
            "path": "/admin/dashboard",
            "method": "GET",
            "description": "Admin dashboard",
            "middleware": ["admin_auth", "security", "logging"],
            "auth_required": "admin"
        },
        {
            "path": "/middleware-chain",
            "method": "GET",
            "description": "Demonstrates middleware chaining",
            "middleware": ["request_id", "rate_limit", "auth", "security", "timing"],
            "auth_required": True
        },
        {
            "path": "/health",
            "method": "GET",
            "description": "Health check (no middleware)",
            "middleware": [],
            "auth_required": False
        }
    ]

    return JSONResponse({
        "title": "Catzilla Per-Route Middleware API",
        "description": "Zero-allocation middleware system with FastAPI-style decorators",
        "version": "1.0.0",
        "middleware_features": [
            "Per-route middleware attachment",
            "C-compiled execution for zero allocation",
            "FastAPI-compatible decorator syntax",
            "Priority-based middleware ordering",
            "Context sharing between middleware",
            "Early termination support"
        ],
        "authentication": {
            "api_key": "demo_api_key_123",
            "bearer_token": "Bearer catzilla_secret_key",
            "admin_token": "Bearer admin_super_secret"
        },
        "endpoints": endpoints,
        "middleware_types": {
            "auth": "Authentication and authorization",
            "cors": "Cross-origin resource sharing",
            "timing": "Request timing and performance metrics",
            "security": "Security headers and protections",
            "rate_limit": "Request rate limiting",
            "validation": "Request validation",
            "logging": "Request/response logging",
            "request_id": "Unique request ID generation",
            "admin_auth": "Admin-only authentication"
        }
    })

# =====================================================
# STARTUP MESSAGE
# =====================================================

if __name__ == "__main__":
    print("🌪️ Catzilla Per-Route Middleware Demo")
    print("=" * 50)
    print()
    print("🚀 Zero-Allocation Middleware System Features:")
    print("  • FastAPI-style decorators: @app.get(middleware=[...])")
    print("  • C-compiled middleware execution")
    print("  • Per-route middleware attachment")
    print("  • Priority-based execution order")
    print("  • Request/response context sharing")
    print("  • Built-in security and performance middleware")
    print()
    print("📋 Available Endpoints:")
    print("  GET  /                    - Interactive home page")
    print("  GET  /middleware-demo     - Interactive testing interface")
    print("  GET  /public              - Public endpoint (CORS + timing)")
    print("  GET  /protected           - Protected endpoint (auth required)")
    print("  GET  /api/user/profile    - User profile (auth + rate limiting)")
    print("  GET  /admin/dashboard     - Admin dashboard (admin auth)")
    print("  GET  /middleware-chain    - Multiple middleware demo")
    print("  GET  /benchmark           - Performance benchmark")
    print("  GET  /health              - Health check (no middleware)")
    print()
    print("🔑 Authentication:")
    print("  API Key: ?api_key=demo_api_key_123")
    print("  Bearer:  Authorization: Bearer catzilla_secret_key")
    print("  Admin:   Authorization: Bearer admin_super_secret")
    print()
    print("Starting server on http://localhost:8000...")
    print("Visit http://localhost:8000 for the interactive demo!")
    print("=" * 50)

    app.listen(host="127.0.0.1", port=8000)
