#!/usr/bin/env python3
"""
Example demonstrating the new use_jemalloc parameter in Catzilla v0.2.0

This example shows how to use the conditional runtime jemalloc support
with static linking and automatic fallback capabilities.
"""

from catzilla import Catzilla

def example_basic_usage():
    """Basic usage with automatic jemalloc detection"""
    print("=== Basic Usage Example ===")
    
    # Default behavior: use jemalloc if available, fallback to malloc if not
    app = Catzilla(use_jemalloc=True)
    
    print(f"Requested jemalloc: {app.use_jemalloc}")
    print(f"Actually using jemalloc: {app.has_jemalloc}")
    
    # Get detailed allocator information
    info = app.get_allocator_info()
    print(f"Current allocator: {info['current_allocator']}")
    print(f"Status: {info['status']}")
    
    @app.get("/")
    def home():
        return {"message": "Hello from Catzilla!", "allocator": info['current_allocator']}
    
    return app

def example_explicit_malloc():
    """Explicit malloc usage (disable jemalloc)"""
    print("\n=== Explicit Malloc Example ===")
    
    # Explicitly disable jemalloc (use standard malloc)
    app = Catzilla(use_jemalloc=False)
    
    print(f"Requested jemalloc: {app.use_jemalloc}")
    print(f"Actually using jemalloc: {app.has_jemalloc}")
    
    info = app.get_allocator_info()
    print(f"Current allocator: {info['current_allocator']}")
    
    @app.get("/malloc")
    def malloc_endpoint():
        return {"message": "Using standard malloc", "allocator": info['current_allocator']}
    
    return app

def example_conditional_setup():
    """Conditional setup based on jemalloc availability"""
    print("\n=== Conditional Setup Example ===")
    
    # Check availability before creating instance
    jemalloc_available = Catzilla.jemalloc_available()
    available_allocators = Catzilla.get_available_allocators()
    
    print(f"Jemalloc available: {jemalloc_available}")
    print(f"Available allocators: {available_allocators}")
    
    if jemalloc_available:
        # Use jemalloc with memory profiling for production
        app = Catzilla(
            use_jemalloc=True,
            memory_profiling=True,
            auto_memory_tuning=True,
            production=True
        )
        print("Created production instance with jemalloc + profiling")
    else:
        # Fallback configuration for environments without jemalloc
        app = Catzilla(
            use_jemalloc=False,
            memory_profiling=False,
            production=True
        )
        print("Created production instance with malloc (jemalloc not available)")
    
    @app.get("/status")
    def status():
        stats = app.get_memory_stats()
        return {
            "allocator": stats['allocator'],
            "jemalloc_available": stats['jemalloc_available'],
            "jemalloc_enabled": stats['jemalloc_enabled'],
            "memory_mb": stats.get('allocated_mb', 0)
        }
    
    return app

def example_memory_monitoring():
    """Example with advanced memory monitoring"""
    print("\n=== Memory Monitoring Example ===")
    
    # Enable all memory features if jemalloc is available
    app = Catzilla(
        use_jemalloc=True,
        memory_profiling=True,
        auto_memory_tuning=True,
        memory_stats_interval=30  # Check every 30 seconds
    )
    
    @app.get("/memory")
    def memory_stats():
        stats = app.get_memory_stats()
        return {
            "allocator_info": app.get_allocator_info(),
            "memory_stats": stats
        }
    
    @app.get("/allocators") 
    def allocators():
        return {
            "available": Catzilla.get_available_allocators(),
            "current": app.get_allocator_info()['current_allocator'],
            "build_supports_jemalloc": Catzilla.jemalloc_available()
        }
    
    return app

def main():
    """Run examples"""
    print("Catzilla v0.2.0 use_jemalloc Parameter Examples")
    print("=" * 60)
    
    # Run all examples
    app1 = example_basic_usage()
    app2 = example_explicit_malloc() 
    app3 = example_conditional_setup()
    app4 = example_memory_monitoring()
    
    print("\n" + "=" * 60)
    print("All examples completed!")
    print("To run a server, choose one of the apps and call app.run()")
    print("Example: app1.run(host='0.0.0.0', port=8000)")
    
    # Return the conditional setup app as the recommended approach
    return app3

if __name__ == "__main__":
    app = main()
    
    # Optionally run the server
    # app.run(host="0.0.0.0", port=8000)
