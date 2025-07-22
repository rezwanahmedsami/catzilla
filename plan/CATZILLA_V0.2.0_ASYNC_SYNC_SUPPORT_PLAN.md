# 🐱 Catzilla v0.2.0 Async/Sync Support Implementation Plan

**Focus**: Add both async and sync handler support to eliminate Python GIL blocking
**Timeline**: 2 weeks
**Goal**: True non-blocking execution at both C and Python levels

## 🎯 **CURRENT STATE ANALYSIS**

### ✅ **What We Have**
- C-native server with libuv (non-blocking I/O)
- Sync handlers only: `def handler(request):`
- C handles all I/O operations (no Python blocking)
- Performance: 21,947 RPS (259% faster than FastAPI)

### ❌ **What's Missing**
- Async handler support: `async def handler(request):`
- AsyncIO integration with libuv event loop
- Hybrid execution (both sync and async handlers in same app)

### 🧠 **The Core Problem**
```python
# Current: Only sync handlers (blocks Python thread during business logic)
@app.get("/users")
def get_users(request):
    # If this takes 100ms, it blocks the Python thread
    data = slow_database_query()  # 100ms blocking call
    return {"users": data}

# Target: Support async handlers (non-blocking Python execution)
@app.get("/users")
async def get_users(request):
    # This should not block the Python thread
    data = await async_database_query()  # 100ms non-blocking
    return {"users": data}
```

---

## 🎯 **IMPLEMENTATION PLAN**

### **Week 1: AsyncIO Bridge Infrastructure**

#### **Day 1-2: C-Python Async Bridge**
**File**: `src/python/async_bridge.c`
```c
// Core async bridge that connects libuv with Python asyncio
typedef struct {
    uv_async_t uv_async;
    PyObject* py_coroutine;
    PyObject* py_future;
    void* request_context;
} async_bridge_t;

// Bridge asyncio.Future to libuv async handle
int bridge_python_async(PyObject* coroutine, uv_loop_t* loop);

// Execute async handler in asyncio loop
void execute_async_handler(async_bridge_t* bridge);
```

#### **Day 3-4: Handler Detection System**
**File**: `python/catzilla/async_detector.py`
```python
import asyncio
import inspect

class AsyncHandlerDetector:
    """Detect if handler is sync or async and route appropriately"""

    @staticmethod
    def is_async_handler(handler) -> bool:
        return asyncio.iscoroutinefunction(handler)

    def wrap_handler(self, handler):
        if self.is_async_handler(handler):
            return self._wrap_async_handler(handler)
        else:
            return self._wrap_sync_handler(handler)
```

#### **Day 5: Request Routing Layer**
**File**: `python/catzilla/hybrid_executor.py`
```python
class HybridExecutor:
    """Route requests to sync or async handlers based on handler type"""

    def execute_handler(self, handler, request):
        if self.is_async_handler(handler):
            return self._execute_async(handler, request)
        else:
            return self._execute_sync(handler, request)
```

### **Week 2: Integration and Polish**

#### **Day 1-2: App Integration**
**Modify**: `python/catzilla/app.py`
```python
def listen(self, port: int = 8000, host: str = "0.0.0.0", enable_async: bool = True):
    """Start server with async/sync support"""
    if enable_async:
        # Initialize AsyncIO bridge
        self._init_async_bridge()

    # Start server (unchanged)
    self.server.listen(port, host)

def _handle_request(self, client, method, path, body, request_capsule):
    """Modified to handle both sync and async"""
    # Detect handler type and route appropriately
    if self.async_detector.is_async_handler(route.handler):
        return self._handle_async_request(...)
    else:
        return self._handle_sync_request(...)
```

#### **Day 3-4: Performance Optimization**
- Minimize async overhead for sync handlers
- Optimize C-Python bridge performance
- Add async handler caching

#### **Day 5: Testing and Validation**
- Create comprehensive test suite
- Benchmark async vs sync performance
- Validate both handler types work correctly

---

## 🏗️ **TECHNICAL ARCHITECTURE**

### **Hybrid Request Flow**
```
Client Request
     ↓
C Server (libuv) - handles I/O
     ↓
Python Router - detects handler type
     ↓
┌─────────────────┬─────────────────┐
│   Sync Handler  │  Async Handler  │
│                 │                 │
│ def handler()   │ async def hand  │
│ Direct call     │ AsyncIO bridge  │
│ Blocks thread   │ Non-blocking    │
└─────────────────┴─────────────────┘
     ↓                     ↓
Response sent back through C layer
```

### **AsyncIO Integration**
```python
# The bridge maintains compatibility with existing sync handlers
# while adding async support without breaking changes

# Existing sync handlers continue to work
@app.get("/sync")
def sync_handler(request):
    return {"message": "sync"}

# New async handlers are supported
@app.get("/async")
async def async_handler(request):
    await asyncio.sleep(0.1)  # Non-blocking
    return {"message": "async"}
```

---

## 🎯 **SUCCESS CRITERIA**

### **Week 1 Deliverable**
```python
# This basic async/sync detection must work:
app = Catzilla()

@app.get("/sync")
def sync_endpoint(request):
    return {"type": "sync"}

@app.get("/async")
async def async_endpoint(request):
    await asyncio.sleep(0.001)
    return {"type": "async"}

app.listen(enable_async=True)
# Both endpoints work correctly
```

### **Week 2 Deliverable**
```python
# Production-ready async/sync hybrid server:
app = Catzilla()

@app.get("/mixed")
async def mixed_handler(request):
    # Mix of async and sync operations
    sync_data = regular_function()
    async_data = await async_database_call()
    return {"sync": sync_data, "async": async_data}

# Performance target:
# - Sync handlers: Same performance as current (21,947 RPS)
# - Async handlers: 15,000+ RPS (acceptable overhead for non-blocking)
# - No regression in sync handler performance
```

---

## 🔧 **IMPLEMENTATION DETAILS**

### **Handler Registration**
```python
# Router automatically detects handler type during registration
def get(self, path: str, **kwargs):
    def decorator(handler):
        # Detect async vs sync during registration
        handler_type = "async" if asyncio.iscoroutinefunction(handler) else "sync"

        # Store handler with type metadata
        route = Route(
            method="GET",
            path=path,
            handler=handler,
            handler_type=handler_type,  # NEW
            **kwargs
        )
        return route
    return decorator
```

### **Request Execution**
```python
# Modified _handle_request method
def _handle_request(self, client, method, path, body, request_capsule):
    route, path_params, allowed_methods = self.router.match(method, base_path)

    if route.handler_type == "async":
        # Execute in asyncio bridge
        response = await self.async_executor.execute(route.handler, request)
    else:
        # Execute directly (current behavior)
        response = route.handler(request)

    # Send response (unchanged)
    response.send(client)
```

---

## ⚡ **PERFORMANCE EXPECTATIONS**

### **Current (Sync Only)**
- Sync handlers: 21,947 RPS
- I/O operations: Non-blocking (handled by C/libuv)
- Business logic: Blocking (Python thread waits)

### **Target (Hybrid Async/Sync)**
- Sync handlers: 21,947 RPS (no regression)
- Async handlers: 15,000+ RPS (70% of sync performance)
- Mixed workload: Async handlers don't block sync handlers

### **Benefits**
- **Sync handlers**: No change, continue to work exactly as before
- **Async handlers**: Can use `await` for database calls, API calls, etc.
- **True parallelism**: Multiple async handlers can execute concurrently
- **No GIL blocking**: Business logic becomes truly non-blocking

---

## 🚨 **CRITICAL DESIGN DECISIONS**

### **1. Backward Compatibility**
- All existing sync handlers continue to work unchanged
- No breaking changes to current API
- Performance regression is unacceptable

### **2. Optional Async**
```python
# Async support is opt-in
app.listen(enable_async=True)   # Enables async handlers
app.listen(enable_async=False)  # Pure sync mode (current behavior)
```

### **3. No AsyncIO Requirements for Sync Code**
```python
# Developers can still write pure sync code
@app.get("/simple")
def simple_handler(request):
    return {"message": "no async knowledge required"}
```

---

## 📝 **IMPLEMENTATION NOTES**

1. **Start Simple**: Basic async/sync detection first, optimization later
2. **Maintain C Performance**: All I/O still handled by C/libuv layer
3. **Minimize Overhead**: Async bridge only activates for async handlers
4. **Test Extensively**: Both handler types must work reliably
5. **Document Clearly**: Show developers when to use async vs sync

This plan focuses purely on adding async/sync support without complex multi-processing or other advanced features. The goal is to eliminate Python GIL blocking in business logic while maintaining Catzilla's core performance advantages.
