# 🔄 Migration Guide: FastAPI to Catzilla DI

## 📋 Overview

This guide helps you migrate from FastAPI's dependency injection system to Catzilla's revolutionary dependency injection. Catzilla's DI system provides 5-8x faster dependency resolution while maintaining familiar FastAPI-style APIs.

## 🔄 Quick Migration Reference

### Basic Dependency Declaration

**FastAPI:**
```python
from fastapi import FastAPI, Depends

def get_database():
    return DatabaseService()

def get_user_service(db: DatabaseService = Depends(get_database)):
    return UserService(db)

@app.get("/users/{user_id}")
def get_user(user_id: int,
            user_service: UserService = Depends(get_user_service)):
    return user_service.get_user(user_id)
```

**Catzilla:**
```python
from catzilla import Catzilla, service, Depends

@service("database", scope="singleton")
class DatabaseService:
    pass

@service("user_service", scope="singleton")
class UserService:
    def __init__(self, db: DatabaseService = Depends("database")):
        self.db = db

@app.get("/users/{user_id}")
def get_user(user_id: int,
            user_service: UserService = Depends("user_service")):
    return user_service.get_user(user_id)
```

### Scoped Dependencies

**FastAPI:**
```python
# Database session per request
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/users/")
def read_users(db: Session = Depends(get_db)):
    return db.query(User).all()
```

**Catzilla:**
```python
@service("database_session", scope="request")
class DatabaseSession:
    def __init__(self):
        self.session = SessionLocal()

    def __enter__(self):
        return self.session

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.session.close()

@app.get("/users/")
def read_users(db: DatabaseSession = Depends("database_session")):
    with db as session:
        return session.query(User).all()
```

## 📖 Step-by-Step Migration

### Step 1: Install Catzilla

```bash
pip install catzilla>=0.2.0
pip uninstall fastapi  # Optional: remove FastAPI
```

### Step 2: Update Imports

```python
# Before
from fastapi import FastAPI, Depends, HTTPException
from fastapi.responses import JSONResponse

# After
from catzilla import Catzilla, Depends, HTTPException, service
from catzilla.responses import JSONResponse
```

### Step 3: Convert Dependency Functions to Services

**FastAPI Pattern:**
```python
def get_settings():
    return Settings()

def get_database(settings: Settings = Depends(get_settings)):
    return Database(settings.database_url)

def get_user_service(db: Database = Depends(get_database)):
    return UserService(db)
```

**Catzilla Pattern:**
```python
@service("settings", scope="singleton")
class Settings:
    def __init__(self):
        self.database_url = "postgresql://..."

@service("database", scope="singleton")
class Database:
    def __init__(self, settings: Settings = Depends("settings")):
        self.connection = create_connection(settings.database_url)

@service("user_service", scope="singleton")
class UserService:
    def __init__(self, db: Database = Depends("database")):
        self.db = db
```

### Step 4: Update Route Handlers

**FastAPI:**
```python
@app.get("/users/{user_id}")
def get_user(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    user_service: UserService = Depends(get_user_service)
):
    return user_service.find_user(user_id, current_user, db)
```

**Catzilla:**
```python
@app.get("/users/{user_id}")
def get_user(
    user_id: int,
    current_user: User = Depends("current_user"),
    user_service: UserService = Depends("user_service")
):
    # Database session injected automatically into user_service
    return user_service.find_user(user_id, current_user)
```

## 🎯 Advanced Migration Patterns

### Sub-Dependencies

**FastAPI:**
```python
def get_token_header(x_token: str = Header()):
    if x_token != "fake-super-secret-token":
        raise HTTPException(status_code=400, detail="X-Token header invalid")
    return x_token

def get_query_token(token: str):
    return token

def get_token(
    x_token: str = Depends(get_token_header),
    token: str = Depends(get_query_token)
):
    return x_token or token

@app.get("/items/")
def read_items(token: str = Depends(get_token)):
    return {"token": token}
```

**Catzilla:**
```python
@service("token_validator", scope="request")
class TokenValidator:
    def __init__(self):
        self.x_token = None
        self.query_token = None

    def validate_header_token(self, x_token: str):
        if x_token != "fake-super-secret-token":
            raise HTTPException(status_code=400, detail="X-Token header invalid")
        self.x_token = x_token
        return x_token

    def get_final_token(self):
        return self.x_token or self.query_token

@app.get("/items/")
def read_items(validator: TokenValidator = Depends("token_validator")):
    token = validator.get_final_token()
    return {"token": token}
```

### Database Sessions with Context Managers

**FastAPI:**
```python
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

**Catzilla:**
```python
@service("database_session", scope="request")
class DatabaseSession:
    def __init__(self, config: DatabaseConfig = Depends("database_config")):
        self.session = SessionLocal(config.url)

    def __enter__(self):
        return self.session

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            self.session.rollback()
        else:
            self.session.commit()
        self.session.close()

# Usage in routes
@app.post("/users/")
def create_user(user: UserCreate, db_session: DatabaseSession = Depends("database_session")):
    with db_session as db:
        user = User(**user.dict())
        db.add(user)
        return user
```

## 🔧 Configuration Migration

### Settings and Configuration

**FastAPI:**
```python
from functools import lru_cache
from pydantic import BaseSettings

class Settings(BaseSettings):
    database_url: str = "postgresql://..."
    secret_key: str = "secret"

    class Config:
        env_file = ".env"

@lru_cache()
def get_settings():
    return Settings()

@app.get("/info")
def read_info(settings: Settings = Depends(get_settings)):
    return {"database_url": settings.database_url}
```

**Catzilla:**
```python
from catzilla.config import Config

@service("settings", scope="singleton")
class Settings(Config):
    def __init__(self):
        super().__init__()
        self.database_url: str = self.get_env("DATABASE_URL", "postgresql://...")
        self.secret_key: str = self.get_env("SECRET_KEY", "secret")

@app.get("/info")
def read_info(settings: Settings = Depends("settings")):
    return {"database_url": settings.database_url}
```

## 🚀 Performance Benefits

### Before and After Comparison

**FastAPI Dependency Resolution:**
```python
# Every request resolves the entire dependency chain
get_settings() -> get_database() -> get_user_service()
# ~45ms for complex dependency chains
```

**Catzilla Dependency Resolution:**
```python
# Singleton services resolved once, cached in C
# Only request-scoped services created per request
# ~6ms for same dependency chains (6.5x faster)
```

### Memory Usage

**FastAPI:**
- Function-based dependencies recreated each time
- No built-in caching mechanism
- Higher memory fragmentation

**Catzilla:**
- C-level caching with arena allocation
- 30% memory reduction through jemalloc optimization
- Efficient singleton management

## ⚠️ Migration Considerations

### Breaking Changes

1. **Dependency Functions → Service Classes**
   - Convert `def get_service()` to `@service class Service`
   - Constructor injection instead of function parameters

2. **Yield Dependencies → Context Managers**
   - FastAPI's `yield` becomes `__enter__/__exit__`
   - Better resource management and error handling

3. **Global State → Proper Scoping**
   - Replace `@lru_cache` with `@service(scope="singleton")`
   - Explicit scope management

### Compatibility Layers

For gradual migration, use compatibility helpers:

```python
from catzilla.compat import fastapi_to_catzilla

# Wrap existing FastAPI dependency functions
@fastapi_to_catzilla("legacy_database", scope="request")
def get_database():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Use in routes during migration
@app.get("/legacy-endpoint")
def legacy_handler(db = Depends("legacy_database")):
    return {"status": "working"}
```

## 🧪 Testing Migration

### Test Dependency Injection

**FastAPI:**
```python
def override_get_db():
    return MockDatabase()

app.dependency_overrides[get_db] = override_get_db
```

**Catzilla:**
```python
# Create test container
test_container = DIContainer()
test_container.register("database", MockDatabase, "singleton")

# Use test container in app
app.di_container = test_container
```

### Example Test Case

```python
import pytest
from catzilla.testing import TestClient, TestContainer

@pytest.fixture
def test_container():
    container = TestContainer()
    container.register("database", MockDatabase, "singleton")
    container.register("user_service", MockUserService, "singleton")
    return container

@pytest.fixture
def client(test_container):
    app.di_container = test_container
    return TestClient(app)

def test_get_user(client):
    response = client.get("/users/123")
    assert response.status_code == 200
    assert response.json()["user_id"] == 123
```

## 📈 Validation and Rollback

### Gradual Migration Strategy

1. **Phase 1: Setup Catzilla alongside FastAPI**
   ```python
   # Keep both systems running
   from fastapi import FastAPI as FastAPIApp
   from catzilla import Catzilla

   fastapi_app = FastAPIApp()  # Legacy routes
   catzilla_app = Catzilla()   # New routes
   ```

2. **Phase 2: Migrate route by route**
   ```python
   # Move one route at a time
   @catzilla_app.get("/users/{user_id}")  # New
   def get_user_v2(user_id: int, service = Depends("user_service")):
       pass

   @fastapi_app.get("/users/{user_id}/legacy")  # Keep old
   def get_user_v1(user_id: int, service = Depends(get_user_service)):
       pass
   ```

3. **Phase 3: Performance validation**
   ```python
   # Compare performance
   import time

   start = time.time()
   fastapi_response = fastapi_client.get("/users/123/legacy")
   fastapi_time = time.time() - start

   start = time.time()
   catzilla_response = catzilla_client.get("/users/123")
   catzilla_time = time.time() - start

   print(f"FastAPI: {fastapi_time:.3f}s")
   print(f"Catzilla: {catzilla_time:.3f}s")
   print(f"Speedup: {fastapi_time/catzilla_time:.1f}x")
   ```

## ✅ Migration Checklist

- [ ] Install Catzilla and update imports
- [ ] Convert dependency functions to service classes
- [ ] Update route handler signatures
- [ ] Replace `yield` dependencies with context managers
- [ ] Convert `@lru_cache` to `@service(scope="singleton")`
- [ ] Update configuration management
- [ ] Migrate test dependencies
- [ ] Performance test and validate
- [ ] Remove FastAPI dependencies

## 🆘 Common Migration Issues

### Issue 1: Dependency Not Found
```python
# Problem: Service name mismatch
@service("user_service")  # Registered as "user_service"
class UserService: pass

def handler(service = Depends("userservice")):  # Wrong name!
    pass

# Solution: Use consistent naming
SERVICE_NAMES = {
    "database": "database",
    "user_service": "user_service",
    "auth": "auth_service"
}
```

### Issue 2: Circular Dependencies
```python
# Problem: A -> B -> A
@service("service_a")
class ServiceA:
    def __init__(self, b = Depends("service_b")): pass

@service("service_b")
class ServiceB:
    def __init__(self, a = Depends("service_a")): pass

# Solution: Break the cycle
@service("service_a")
class ServiceA:
    def get_service_b(self):
        return container.resolve("service_b")
```

## 🔗 Additional Resources

- [Catzilla DI Performance Benchmarks](../benchmarks/dependency_injection.md)
- [FastAPI vs Catzilla Feature Comparison](./feature-comparison.md)
- [Production Migration Case Studies](./case-studies.md)

---

*This migration guide covers common patterns. For complex custom dependency injection scenarios, consult the full [Catzilla DI Documentation](./DEPENDENCY_INJECTION_GUIDE.md).*
