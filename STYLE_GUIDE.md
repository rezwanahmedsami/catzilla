# Catzilla Style Guide

This document contains the detailed C and Python code standards for Catzilla contributors.
See [CONTRIBUTING.md](CONTRIBUTING.md) for the overall contribution workflow.

## C Code Standards

### Formatting

- 4 spaces, no tabs
- Opening brace on the same line as the function signature
- One statement per line

```c
// ✅ Correct
int catzilla_router_add_route(catzilla_router_t *router,
                              const char *method,
                              const char *path,
                              request_handler_t handler) {
    if (!router || !method || !path || !handler) {
        return -1;
    }
    return 0;
}
```

### Naming Conventions

| Element | Convention | Example |
|---------|-----------|---------|
| Types | `catzilla_` prefix, `_t` suffix | `catzilla_route_t` |
| Public functions | `catzilla_module_action_target` | `catzilla_router_add_route` |
| Static functions | `module_action` | `router_find_route` |
| Constants | `UPPER_SNAKE_CASE` | `CATZILLA_MAX_PATH_LENGTH` |
| Variables | `snake_case` | `route_count` |

### Error Handling

- Validate all pointer inputs with NULL checks
- Return meaningful error codes (not just -1)
- Log errors with context
- Clean up allocated resources on failure

```c
int catzilla_router_add_route(catzilla_router_t *router,
                              const char *method,
                              const char *path,
                              request_handler_t handler) {
    if (!router) {
        LOG_ROUTER_ERROR("Router cannot be NULL");
        return CATZILLA_ERROR_INVALID_ARGUMENT;
    }
    if (!method || strlen(method) == 0) {
        LOG_ROUTER_ERROR("Method cannot be empty");
        return CATZILLA_ERROR_INVALID_ARGUMENT;
    }

    int result = internal_add_route(router, method, path, handler);
    if (result != 0) {
        LOG_ROUTER_ERROR("Failed to add route %s %s: error %d", method, path, result);
        return result;
    }
    return CATZILLA_SUCCESS;
}
```

### Memory Management

- Every `malloc`/`strdup` must have a corresponding `free`
- Check all allocation results for NULL
- Provide dedicated `_destroy`/`_cleanup` functions
- Use jemalloc arenas where appropriate (request, response, cache, static)

```c
catzilla_route_t* catzilla_route_create(const char *method, const char *path) {
    catzilla_route_t *route = malloc(sizeof(catzilla_route_t));
    if (!route) return NULL;

    route->method = strdup(method);
    route->path = strdup(path);
    route->handler = NULL;

    if (!route->method || !route->path) {
        catzilla_route_destroy(route);
        return NULL;
    }
    return route;
}

void catzilla_route_destroy(catzilla_route_t *route) {
    if (route) {
        free(route->method);
        free(route->path);
        free(route);
    }
}
```

### Performance

- Use trie-based structures for O(log n) route lookups, not linear search
- Reuse stack buffers in hot paths instead of malloc
- Pre-size arrays for known-small, fixed collections
- Cache frequently accessed values

### Security

- Validate all string lengths before copying (prevent buffer overflows)
- Reject path traversal sequences (`..`, `//`)
- Validate HTTP methods against an allowlist
- Never use `strcpy` — use bounded alternatives

## Python Code Standards

### Formatting

We use automated tools:
- **black** — code formatting (line length 88)
- **isort** — import sorting
- **flake8** — style and complexity
- **mypy** — type checking

Run before committing:
```bash
black python/catzilla/
isort python/catzilla/
flake8 python/catzilla/
mypy python/catzilla/
```

### Type Hints

All public APIs must have complete type hints:

```python
from typing import Any, Dict, List, Optional, Union

class RouterGroup:
    """A group of related routes with a common prefix."""

    def __init__(self, prefix: str, middleware: Optional[List] = None) -> None:
        if not prefix.startswith("/"):
            raise ValueError("Prefix must start with '/'")
        self._prefix = prefix.rstrip("/")
        self._routes: List[Dict[str, Any]] = []
        self._middleware = middleware or []

    def get(self, path: str) -> callable:
        """Register a GET route handler."""
        return self._add_route("GET", path)
```

### Docstrings

Use Google-style docstrings with Args, Returns, Raises, and Example sections for all public functions:

```python
def add_route(self, method: str, path: str, handler: callable) -> None:
    """Add a route to the router.

    Args:
        method: HTTP method (GET, POST, PUT, DELETE, etc.)
        path: URL path pattern with optional {param} placeholders
        handler: Function to handle matching requests

    Raises:
        ValueError: If method or path is invalid
        RouterError: If route conflicts with an existing route

    Example:
        >>> router.add_route("GET", "/users/{user_id}", get_user)
    """
```

### Error Handling

- Validate inputs at function boundaries
- Use specific exception types (not bare `Exception`)
- Preserve tracebacks with `raise ... from e`
- Check for required keys in dictionaries before access

### Performance

- Use C extension paths when available, with graceful Python fallback
- Pre-compile regex patterns when used for routing
- Leverage `__slots__` for memory efficiency in frequently-instantiated classes

## Code Quality Tools

### Pre-commit hooks

```bash
# Setup (one-time)
pip install pre-commit
pre-commit install

# Run all checks
pre-commit run --all-files
```

Our `.pre-commit-config.yaml`:
```yaml
repos:
  - repo: https://github.com/psf/black
    rev: 23.3.0
    hooks:
      - id: black
  - repo: https://github.com/pycqa/isort
    rev: 5.12.0
    hooks:
      - id: isort
  - repo: https://github.com/pycqa/flake8
    rev: 6.0.0
    hooks:
      - id: flake8
  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.3.0
    hooks:
      - id: mypy
```

### Tool configuration

From `pyproject.toml`:
```toml
[tool.black]
line-length = 88
target-version = ['py38', 'py39', 'py310', 'py311']

[tool.isort]
profile = "black"
multi_line_output = 3

[tool.mypy]
python_version = "3.8"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true

[tool.pytest.ini_options]
testpaths = ["tests/python"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
```

### Static analysis

```bash
black --check python/catzilla/
isort --check-only python/catzilla/
flake8 python/catzilla/
mypy python/catzilla/
```
```

