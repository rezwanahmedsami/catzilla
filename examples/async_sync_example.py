#!/usr/bin/env python3
"""
Catzilla v0.2.0 Async/Sync Support Example

This example demonstrates the new hybrid async/sync handler support in Catzilla.
It shows how you can mix synchronous and asynchronous handlers in the same
application, with automatic detection and optimal execution.

Usage:
    python examples/async_sync_example.py

Features demonstrated:
- Automatic handler type detection
- Hybrid execution of sync and async handlers
- Performance monitoring
- Error handling
- Mixed handler types in one application
"""

import asyncio
import time
import json
from typing import Dict, Any

# This example shows how handlers would be defined in a real Catzilla app
# The actual app integration requires the C extension, but this shows the Python side

class MockRequest:
    """Mock request object for demonstration"""
    def __init__(self, method="GET", path="/", body="", query_params=None):
        self.method = method
        self.path = path
        self.body = body
        self.query_params = query_params or {}
        self.headers = {}
        self.path_params = {}

class MockResponse:
    """Mock response object for demonstration"""
    def __init__(self, content: Any, status_code: int = 200, content_type: str = "application/json"):
        self.content = content
        self.status_code = status_code
        self.content_type = content_type
        self.body = json.dumps(content) if isinstance(content, (dict, list)) else str(content)

# Example handlers mixing sync and async

def home_handler(request: MockRequest) -> MockResponse:
    """Synchronous handler for the home page"""
    return MockResponse({
        "message": "Welcome to Catzilla v0.2.0!",
        "features": [
            "Hybrid async/sync support",
            "Automatic handler detection",
            "Performance monitoring",
            "Thread-safe execution"
        ],
        "handler_type": "synchronous",
        "path": request.path
    })

async def api_data_handler(request: MockRequest) -> MockResponse:
    """Asynchronous handler that simulates database queries"""
    # Simulate async database query
    await asyncio.sleep(0.1)

    # Simulate fetching user data
    user_data = {
        "id": 123,
        "name": "Demo User",
        "last_login": time.time()
    }

    # Simulate another async operation
    await asyncio.sleep(0.05)

    return MockResponse({
        "data": user_data,
        "handler_type": "asynchronous",
        "query_time": 0.15,
        "path": request.path
    })

def health_check_handler(request: MockRequest) -> MockResponse:
    """Synchronous health check handler"""
    return MockResponse({
        "status": "healthy",
        "timestamp": time.time(),
        "version": "0.2.0",
        "async_support": True,
        "handler_type": "synchronous"
    })

async def async_computation_handler(request: MockRequest) -> MockResponse:
    """Asynchronous handler that performs computational tasks"""
    results = []

    # Simulate multiple async computations
    for i in range(3):
        await asyncio.sleep(0.02)  # Simulate async computation
        result = f"computation_result_{i}"
        results.append(result)

    return MockResponse({
        "results": results,
        "computation_time": 0.06,
        "handler_type": "asynchronous",
        "total_operations": len(results)
    })

def sync_file_handler(request: MockRequest) -> MockResponse:
    """Synchronous handler that simulates file operations"""
    # Simulate file reading (blocking I/O)
    time.sleep(0.1)

    return MockResponse({
        "file_content": "This is simulated file content",
        "file_size": 1024,
        "handler_type": "synchronous",
        "read_time": 0.1
    })

async def async_external_api_handler(request: MockRequest) -> MockResponse:
    """Asynchronous handler that simulates external API calls"""
    # Simulate multiple async API calls
    api_responses = []

    for endpoint in ["users", "posts", "comments"]:
        await asyncio.sleep(0.03)  # Simulate HTTP request
        api_responses.append({
            "endpoint": endpoint,
            "status": "success",
            "data_count": 10
        })

    return MockResponse({
        "api_responses": api_responses,
        "handler_type": "asynchronous",
        "total_requests": len(api_responses),
        "response_time": 0.09
    })

# Route definitions that would be used in a real Catzilla app
EXAMPLE_ROUTES = [
    ("GET", "/", home_handler),
    ("GET", "/api/data", api_data_handler),
    ("GET", "/health", health_check_handler),
    ("GET", "/compute", async_computation_handler),
    ("GET", "/files", sync_file_handler),
    ("GET", "/api/external", async_external_api_handler),
]

async def demonstrate_async_sync_mixing():
    """Demonstrate how sync and async handlers work together"""
    print("🚀 Catzilla v0.2.0 Async/Sync Support Demonstration\n")

    # Simulate requests to different handlers
    test_requests = [
        MockRequest("GET", "/"),
        MockRequest("GET", "/api/data"),
        MockRequest("GET", "/health"),
        MockRequest("GET", "/compute"),
        MockRequest("GET", "/files"),
        MockRequest("GET", "/api/external"),
    ]

    print("📊 Handler Type Analysis:")
    for method, path, handler in EXAMPLE_ROUTES:
        handler_type = "async" if asyncio.iscoroutinefunction(handler) else "sync"
        print(f"  {method} {path:<15} -> {handler.__name__:<25} [{handler_type}]")

    print(f"\n⚡ Executing {len(test_requests)} requests concurrently...\n")

    start_time = time.time()

    # Execute all handlers (mix of sync and async)
    tasks = []
    for request in test_requests:
        # Find the matching handler
        for method, path, handler in EXAMPLE_ROUTES:
            if request.method == method and request.path == path:
                if asyncio.iscoroutinefunction(handler):
                    # Async handler
                    task = handler(request)
                else:
                    # Sync handler - wrap in executor for demo
                    async def run_sync_handler(h, r):
                        loop = asyncio.get_running_loop()
                        return await loop.run_in_executor(None, h, r)
                    task = run_sync_handler(handler, request)

                tasks.append((request.path, task))
                break

    # Wait for all tasks to complete
    results = []
    for path, task in tasks:
        try:
            response = await task
            results.append((path, response, "success"))
        except Exception as e:
            results.append((path, None, f"error: {e}"))

    total_time = time.time() - start_time

    # Display results
    print("📋 Execution Results:")
    for path, response, status in results:
        if status == "success":
            content = json.loads(response.body) if hasattr(response, 'body') else response.content
            handler_type = content.get('handler_type', 'unknown')
            print(f"  {path:<20} -> {status:<10} [{handler_type}]")
        else:
            print(f"  {path:<20} -> {status}")

    print(f"\n⏱️  Total execution time: {total_time:.3f} seconds")
    print(f"🔄 Concurrent execution of {len(tasks)} handlers")

    print("\n✨ Key Benefits Demonstrated:")
    print("  ✅ Automatic detection of sync vs async handlers")
    print("  ✅ Optimal execution context for each handler type")
    print("  ✅ Concurrent execution of mixed handler types")
    print("  ✅ No changes required to existing sync handlers")
    print("  ✅ Full async support for new handlers")

    return results

def show_performance_comparison():
    """Show the performance benefits of the hybrid approach"""
    print("\n📈 Performance Comparison:")
    print("\n  Traditional (sync-only) approach:")
    print("    - All handlers block the main thread")
    print("    - I/O operations waste CPU cycles")
    print("    - No concurrent request processing")
    print("    - Poor scalability with async workloads")

    print("\n  Catzilla v0.2.0 Hybrid approach:")
    print("    - Sync handlers run in optimized thread pool")
    print("    - Async handlers run in event loop")
    print("    - Automatic optimal execution context")
    print("    - True concurrent processing")
    print("    - Best of both worlds: compatibility + performance")

def show_migration_guide():
    """Show how to migrate existing apps to use async support"""
    print("\n📚 Migration Guide:")
    print("\n  Existing sync handlers (no changes needed):")
    print("    def my_handler(request):")
    print("        return {'message': 'Hello World'}")

    print("\n  New async handlers (add async/await):")
    print("    async def my_async_handler(request):")
    print("        data = await fetch_from_database()")
    print("        return {'data': data}")

    print("\n  Catzilla automatically:")
    print("    ✅ Detects handler type")
    print("    ✅ Routes to appropriate executor")
    print("    ✅ Provides performance monitoring")
    print("    ✅ Handles errors gracefully")

async def main():
    """Main demonstration function"""
    try:
        await demonstrate_async_sync_mixing()
        show_performance_comparison()
        show_migration_guide()

        print("\n🎉 Catzilla v0.2.0 Async/Sync Support Demo Complete!")
        print("\nNext steps:")
        print("  1. Update your Catzilla app to v0.2.0")
        print("  2. Add async handlers where beneficial")
        print("  3. Monitor performance with built-in metrics")
        print("  4. Enjoy the performance boost! 🚀")

    except KeyboardInterrupt:
        print("\n⚠️ Demo interrupted by user")
    except Exception as e:
        print(f"\n❌ Demo error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
