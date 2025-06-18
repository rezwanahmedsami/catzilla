# 📋 Middleware Context Usage Guide

## Current Implementation

The Catzilla middleware system currently requires **manual initialization** of request context. The documentation has been updated to reflect the actual implementation.

## Correct Context Usage

### 1. **Manual Context Initialization**

```python
@app.middleware(priority=50, pre_route=True)
def auth_middleware(request):
    # REQUIRED: Initialize context manually
    if not hasattr(request, '_context'):
        request._context = {}

    # Now you can use context
    request._context['authenticated'] = True
    request._context['user_id'] = 'user123'
    return None
```

### 2. **Safe Context Access**

```python
@app.route('/api/data')
def get_data(request):
    # SAFE: Use getattr with default
    authenticated = getattr(request, '_context', {}).get('authenticated', False)
    user_id = getattr(request, '_context', {}).get('user_id', 'anonymous')

    return {
        "authenticated": authenticated,
        "user_id": user_id,
        "data": "some data"
    }
```

### 3. **Documentation vs Implementation**

❌ **Documentation Previously Showed** (INCORRECT):
```python
# This doesn't work - request.context doesn't exist by default
request.context['user'] = user_data
user = request.context.get('user')
```

✅ **Actual Implementation** (CORRECT):
```python
# This is what actually works
if not hasattr(request, '_context'):
    request._context = {}
request._context['user'] = user_data
user = getattr(request, '_context', {}).get('user')
```

## Updated Documentation

All middleware documentation files have been updated to reflect the correct usage:

- `docs/middleware.md` - Technical reference ✅
- `docs/middleware_user_guide.md` - User guide ✅
- `docs/middleware_guide.md` - Getting started guide ✅

## Examples

The working examples already use the correct pattern:

- `examples/middleware/main.py` - Production-style example ✅
- All per-route middleware examples ✅

## Summary

The middleware system works correctly, but requires:

1. **Manual context initialization** with `request._context = {}`
2. **Safe access** using `getattr(request, '_context', {}).get('key', default)`
3. **Proper error handling** when context might not exist

This ensures zero-allocation performance while providing middleware context sharing capabilities.
