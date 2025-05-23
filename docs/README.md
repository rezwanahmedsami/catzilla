# Catzilla Documentation

Welcome to the Catzilla documentation! Catzilla is a high-performance Python web framework with a C core, designed for simplicity and speed.

## Table of Contents

1. [Getting Started](./getting-started.md)
2. [Core Concepts](./core-concepts.md)
3. [Request Handling](./request-handling.md)
4. [Response Types](./response-types.md)
5. [Routing](./routing.md)
6. [Cookies and Headers](./cookies-and-headers.md)
7. [Examples](./examples.md)

## Quick Start

```python
from catzilla import App, JSONResponse

app = App()

@app.get("/hello")
def hello(request):
    return {"message": "Hello, World!"}

if __name__ == "__main__":
    app.listen(8080)
```

## Key Features

- **High Performance**: C core for handling HTTP requests
- **Simple API**: Intuitive routing and request handling
- **Flexible Responses**: Support for HTML, JSON, and custom responses
- **Type Conversion**: Automatic conversion of Python types to appropriate responses
- **Cookie Management**: Built-in cookie handling
- **Header Control**: Full control over HTTP headers
- **Status Codes**: Easy customization of HTTP status codes

## Framework Philosophy

Catzilla is designed with the following principles in mind:

1. **Speed First**: C core for maximum performance
2. **Developer Friendly**: Simple, intuitive API design
3. **Flexibility**: Support for various response types and use cases
4. **Stability**: Strong focus on testing and reliability

For detailed information about each feature, please refer to the specific documentation sections listed in the Table of Contents.
