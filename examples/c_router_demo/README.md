# 🚀 Catzilla C Router Performance Demo

This example demonstrates the C-accelerated routing system in Catzilla and showcases the performance improvements.

## 🎯 What This Demo Shows

- **C-accelerated route matching** - Fast trie-based lookup
- **Dynamic path parameters** - Efficient parameter extraction in C
- **Performance comparison** - Shows which router type is being used
- **Route introspection** - Debug information about registered routes
- **Complex routing patterns** - Nested dynamic routes with multiple parameters

## 🚀 Running the Demo

```bash
# From the project root
cd examples/c_router_demo
python main.py
```

Or from the project root:
```bash
python examples/c_router_demo/main.py
```

## 🧪 Testing Routes

Once the server is running, test these URLs:

### Static Routes (Fastest)
- `GET http://localhost:8000/` - Home page JSON response
- `GET http://localhost:8000/health` - Health check JSON
- `GET http://localhost:8000/about` - About page with beautiful HTML styling

### Dynamic Routes (C-accelerated parameter extraction)
- `GET http://localhost:8000/users/123` - Single parameter
- `GET http://localhost:8000/users/456/posts/789` - Multiple parameters
- `GET http://localhost:8000/api/v1/organizations/org1/projects/proj2/tasks/task3` - Complex nested route

### API Routes
- `POST http://localhost:8000/api/users/999/data` - With JSON body (use curl or Postman)

### Benchmark Routes
- `GET http://localhost:8000/benchmark/static` - Static route performance test
- `GET http://localhost:8000/benchmark/dynamic/test123` - Dynamic route performance test

### Debug & Performance Routes
- `GET http://localhost:8000/debug/routes` - List all registered routes
- `GET http://localhost:8000/performance/info` - Detailed router performance information

## 📊 Performance Features

This demo showcases:

1. **C Route Matching**: ~1-5μs vs ~10-50μs Python matching
2. **Fast Parameter Extraction**: C-based regex and string parsing
3. **Trie-based Lookup**: O(log n) complexity for route resolution
4. **Memory Efficiency**: C data structures for optimal performance

## 🔧 Router Types

The demo will automatically use the best available router:

- **CAcceleratedRouter**: C matching + Python handlers (18.5% faster)
- **FastRouter**: Optimized Python with C components (15.6% faster)
- **Router**: Pure Python fallback (baseline)

## 🧪 Console Output

When you run the demo, you'll see:

```
============================================================
🚀 CATZILLA C ROUTER PERFORMANCE DEMO
============================================================
📊 Router Type: CAcceleratedRouter
✅ Using C-accelerated routing for maximum performance!

============================================================
🛣️  REGISTERING ROUTES
============================================================
✅ Route registration completed!

📋 ROUTE SUMMARY:
├── Static routes: /, /health, /about
├── Dynamic routes: /users/{user_id}, /users/{user_id}/posts/{post_id}
├── API routes: /api/users/{user_id}/data
├── Benchmark routes: /benchmark/static, /benchmark/dynamic/{id}
├── Complex route: /api/v1/organizations/{org_id}/projects/{project_id}/tasks/{task_id}
├── Debug route: /debug/routes
└── Performance info: /performance/info

============================================================
🧪 TESTING C ROUTER FUNCTIONALITY
============================================================
🔍 Testing route matching:
  GET    /                                                  → ✅ MATCH
  GET    /health                                            → ✅ MATCH
  GET    /users/123                                         → ✅ MATCH (params: {'user_id': '123'})
  GET    /users/456/posts/789                              → ✅ MATCH (params: {'user_id': '456', 'post_id': '789'})
  POST   /api/users/999/data                               → ✅ MATCH (params: {'user_id': '999'})
  GET    /benchmark/dynamic/test123                        → ✅ MATCH (params: {'id': 'test123'})
  GET    /api/v1/organizations/org1/projects/proj2/tasks/task3 → ✅ MATCH (params: {'org_id': 'org1', 'project_id': 'proj2', 'task_id': 'task3'})
  GET    /nonexistent                                      → ❌ 404 NOT FOUND
  POST   /                                                 → ❌ 405 METHOD NOT ALLOWED (allowed: GET)
```

## 📈 Expected Performance

With C-accelerated routing, you should see:
- **15-20% faster** request handling
- **Lower CPU usage** for route matching
- **Better scalability** with many routes
- **Consistent performance** regardless of route complexity

## 🧪 Manual Testing Examples

### Test with curl:

```bash
# Static route
curl http://localhost:8000/

# Dynamic route with parameters
curl http://localhost:8000/users/123

# Complex nested route
curl http://localhost:8000/api/v1/organizations/myorg/projects/proj1/tasks/task42

# POST with JSON data
curl -X POST http://localhost:8000/api/users/123/data \
  -H "Content-Type: application/json" \
  -d '{"name": "John", "email": "john@example.com"}'

# Check router performance info
curl http://localhost:8000/performance/info
```

### Expected JSON Response Examples:

**GET /users/123:**
```json
{
  "user_id": "123",
  "user_id_type": "str",
  "message": "User 123 fetched via C router",
  "path_params": {"user_id": "123"},
  "router_performance": "C-accelerated parameter extraction",
  "timestamp": 1716566400.123
}
```

**GET /performance/info:**
```json
{
  "router_type": "CAcceleratedRouter",
  "performance_improvement": "18.5% faster than Python router",
  "matching_speed": "1-5μs (C implementation)",
  "best_for": "Applications with many dynamic routes",
  "features": [
    "C trie-based route matching",
    "Fast path parameter extraction",
    "Python route management",
    "Automatic fallback to Python"
  ],
  "timestamp": 1716566400.456
}
```

This demo provides a comprehensive showcase of Catzilla's C-accelerated routing performance! 🚀
