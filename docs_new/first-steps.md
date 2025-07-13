# First Steps with Catzilla

Congratulations on installing Catzilla! This guide will help you understand the core concepts and build your first meaningful application.

## Understanding Catzilla

Catzilla is designed around four core principles:

1. **Speed**: C-accelerated performance for maximum throughput
2. **Simplicity**: FastAPI-compatible API for easy adoption
3. **Safety**: Type-safe validation and dependency injection
4. **Scalability**: Built-in features for production deployment

## Core Concepts

### The Catzilla App

Every Catzilla application starts with creating an app instance:

```python
from catzilla import Catzilla

app = Catzilla()
```

This creates an application with:
- **C-accelerated router** for O(log n) route resolution
- **Auto-validation engine** compatible with Pydantic
- **Memory-optimized request handling** with jemalloc
- **Built-in documentation generation**

### Path Operations

Define API endpoints using decorators:

```python
@app.get("/items/{item_id}")
def read_item(request, item_id: int):
    return {"item_id": item_id}

@app.post("/items/")
def create_item(request, item: dict):
    return {"created": item}

@app.put("/items/{item_id}")
def update_item(request, item_id: int, item: dict):
    return {"item_id": item_id, "updated": item}

@app.delete("/items/{item_id}")
def delete_item(request, item_id: int):
    return {"item_id": item_id, "deleted": True}
```

### Request Validation

Catzilla provides ultra-fast validation using BaseModel:

```python
from catzilla.validation import BaseModel

class Item(BaseModel):
    name: str
    description: str | None = None
    price: float
    tax: float | None = None

@app.post("/items/")
def create_item(item: Item):
    return {"message": f"Created item: {item.name}", "item": item}
```

## Building Your First Real App

Let's build a simple todo API to demonstrate key concepts:

### 1. Define Data Models

```python
from catzilla import Catzilla
from catzilla.validation import BaseModel
from typing import List
import uuid
from datetime import datetime

app = Catzilla()

class TodoItem(BaseModel):
    id: str | None = None
    title: str
    description: str | None = None
    completed: bool = False
    created_at: datetime | None = None

class TodoCreate(BaseModel):
    title: str
    description: str | None = None

class TodoUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    completed: bool | None = None
```

### 2. Create In-Memory Storage

```python
# Simple in-memory storage
todos: List[TodoItem] = []

def find_todo(todo_id: str) -> TodoItem | None:
    for todo in todos:
        if todo.id == todo_id:
            return todo
    return None
```

### 3. Implement CRUD Operations

```python
@app.get("/todos")
def get_todos(request):
    """Get all todos"""
    return todos

@app.get("/todos/{todo_id}")
def get_todo(request, todo_id: str):
    """Get a specific todo"""
    todo = find_todo(todo_id)
    if not todo:
        raise HTTPException(status_code=404, detail="Todo not found")
    return todo

@app.post("/todos")
def create_todo(request, todo_data: TodoCreate):
    """Create a new todo"""
    todo = TodoItem(
        id=str(uuid.uuid4()),
        title=todo_data.title,
        description=todo_data.description,
        completed=False,
        created_at=datetime.now()
    )
    todos.append(todo)
    return todo

@app.put("/todos/{todo_id}")
def update_todo(request, todo_id: str, todo_data: TodoUpdate):
    """Update an existing todo"""
    todo = find_todo(todo_id)
    if not todo:
        raise HTTPException(status_code=404, detail="Todo not found")

    if todo_data.title is not None:
        todo.title = todo_data.title
    if todo_data.description is not None:
        todo.description = todo_data.description
    if todo_data.completed is not None:
        todo.completed = todo_data.completed

    return todo

@app.delete("/todos/{todo_id}")
def delete_todo(todo_id: str):
    """Delete a todo"""
    todo = find_todo(todo_id)
    if not todo:
        raise HTTPException(status_code=404, detail="Todo not found")

    todos.remove(todo)
    return {"message": "Todo deleted successfully"}
```

### 4. Add Root Endpoint

```python
@app.get("/")
def read_root():
    return {
        "message": "Welcome to Catzilla Todo API",
        "version": "1.0.0",
        "docs": "/docs",
        "total_todos": len(todos)
    }
```

### 5. Complete App

Here's the complete `todo_app.py`:

```python
from catzilla import Catzilla
from catzilla.validation import BaseModel
from catzilla.responses import HTTPException
from typing import List
import uuid
from datetime import datetime

app = Catzilla()

# Data Models
class TodoItem(BaseModel):
    id: str | None = None
    title: str
    description: str | None = None
    completed: bool = False
    created_at: datetime | None = None

class TodoCreate(BaseModel):
    title: str
    description: str | None = None

class TodoUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    completed: bool | None = None

# In-memory storage
todos: List[TodoItem] = []

def find_todo(todo_id: str) -> TodoItem | None:
    for todo in todos:
        if todo.id == todo_id:
            return todo
    return None

# API Endpoints
@app.get("/")
def read_root():
    return {
        "message": "Welcome to Catzilla Todo API",
        "version": "1.0.0",
        "docs": "/docs",
        "total_todos": len(todos)
    }

@app.get("/todos")
def get_todos(request):
    return todos

@app.get("/todos/{todo_id}")
def get_todo(request, todo_id: str):
    todo = find_todo(todo_id)
    if not todo:
        raise HTTPException(status_code=404, detail="Todo not found")
    return todo

@app.post("/todos")
def create_todo(request, todo_data: TodoCreate):
    todo = TodoItem(
        id=str(uuid.uuid4()),
        title=todo_data.title,
        description=todo_data.description,
        completed=False,
        created_at=datetime.now()
    )
    todos.append(todo)
    return todo

@app.put("/todos/{todo_id}")
def update_todo(request, todo_id: str, todo_data: TodoUpdate):
    todo = find_todo(todo_id)
    if not todo:
        raise HTTPException(status_code=404, detail="Todo not found")

    if todo_data.title is not None:
        todo.title = todo_data.title
    if todo_data.description is not None:
        todo.description = todo_data.description
    if todo_data.completed is not None:
        todo.completed = todo_data.completed

    return todo

@app.delete("/todos/{todo_id}")
def delete_todo(todo_id: str):
    todo = find_todo(todo_id)
    if not todo:
        raise HTTPException(status_code=404, detail="Todo not found")

    todos.remove(todo)
    return {"message": "Todo deleted successfully"}

if __name__ == "__main__":
    app.listen(host="0.0.0.0", port=8000)
```

## Test Your API

### 1. Run the App

```bash
python todo_app.py
```

### 2. Test with curl

```bash
# Get all todos
curl http://localhost:8000/todos

# Create a todo
curl -X POST http://localhost:8000/todos \
  -H "Content-Type: application/json" \
  -d '{"title": "Learn Catzilla", "description": "Build amazing APIs"}'

# Get specific todo (use ID from creation response)
curl http://localhost:8000/todos/{todo_id}

# Update todo
curl -X PUT http://localhost:8000/todos/{todo_id} \
  -H "Content-Type: application/json" \
  -d '{"completed": true}'

# Delete todo
curl -X DELETE http://localhost:8000/todos/{todo_id}
```

### 3. Interactive API Docs

Visit http://localhost:8000/docs to see the automatically generated interactive API documentation.

## Key Features You've Used

### ✅ Ultra-Fast Validation
Your data models are automatically compiled to C for 100x faster validation.

### ✅ Type Safety
Full type checking and auto-completion in your IDE.

### ✅ Automatic Documentation
Interactive API docs generated automatically.

### ✅ Memory Optimization
jemalloc provides 30% memory reduction compared to standard Python.

### ✅ C-Accelerated Routing
O(log n) route resolution for maximum performance.

## Next Steps

Now that you understand the basics, explore these advanced features:

### Immediate Next Steps
1. **[Tutorial](tutorial/index)** - Comprehensive step-by-step guide
2. **[Auto-Validation](validation/index)** - Master the validation system
3. **[Request & Response Handling](tutorial/request-response)** - Advanced patterns

### Advanced Features
1. **[Background Tasks](background-tasks/index)** - Async processing
2. **[Dependency Injection](dependency-injection/index)** - Organize your code
3. **[Middleware](middleware/index)** - Add custom functionality
4. **[Static Files](tutorial/static-files)** - Serve files efficiently

### Production Features
1. **[Performance Optimization](performance/index)** - Maximize speed
2. **[Deployment](deployment/index)** - Go to production
3. **[Monitoring](performance/monitoring)** - Track performance

## Performance Tips

For maximum performance in your applications:

```python
from catzilla import Catzilla

# Enable all performance features
app = Catzilla(
    enable_jemalloc=True,      # 30% memory reduction
    c_acceleration=True,        # C-speed routing
    router_type="c_accelerated" # Use C router
)
```

## Common Patterns

### Error Handling

```python
from catzilla.responses import HTTPException

@app.get("/items/{item_id}")
def get_item(item_id: int):
    if item_id < 1:
        raise HTTPException(
            status_code=400,
            detail="Item ID must be positive"
        )
    return {"item_id": item_id}
```

### Query Parameters

```python
@app.get("/items/")
def read_items(skip: int = 0, limit: int = 100):
    return {"skip": skip, "limit": limit}
```

### Request Body

```python
@app.post("/items/")
def create_item(item: Item, user_id: int):
    return {"item": item, "user_id": user_id}
```

Ready to dive deeper? Continue with the [Tutorial](tutorial/index) for a comprehensive guide to building production applications with Catzilla! 🚀
