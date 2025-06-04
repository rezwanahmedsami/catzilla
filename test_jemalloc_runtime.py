#!/usr/bin/env python3
"""
Test script for the new jemalloc runtime parameter functionality.

This script tests the static linking system and conditional runtime support
for jemalloc, verifying that the use_jemalloc parameter works correctly.
"""

import sys
import os

# Add the catzilla module to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'python'))

def test_jemalloc_availability():
    """Test static methods for jemalloc availability"""
    print("=== Testing Static Availability Methods ===")
    
    try:
        from catzilla.app import Catzilla
        
        # Test static method (can be called before instance creation)
        jemalloc_available = Catzilla.jemalloc_available()
        available_allocators = Catzilla.get_available_allocators()
        
        print(f"Jemalloc available (static check): {jemalloc_available}")
        print(f"Available allocators: {available_allocators}")
        
        return jemalloc_available
        
    except ImportError as e:
        print(f"Import error: {e}")
        return False

def test_catzilla_with_jemalloc():
    """Test Catzilla initialization with jemalloc enabled"""
    print("\n=== Testing Catzilla with use_jemalloc=True ===")
    
    try:
        from catzilla.app import Catzilla
        
        # Create Catzilla instance with jemalloc enabled
        app = Catzilla(use_jemalloc=True, memory_profiling=False)
        
        # Get allocator information
        allocator_info = app.get_allocator_info()
        print(f"Allocator info: {allocator_info}")
        
        # Get memory stats
        memory_stats = app.get_memory_stats()
        print(f"Memory stats: {memory_stats}")
        
        print(f"Successfully created Catzilla with jemalloc requested: {app.use_jemalloc}")
        print(f"Jemalloc actually enabled: {app.has_jemalloc}")
        
        return app
        
    except Exception as e:
        print(f"Error creating Catzilla with jemalloc: {e}")
        return None

def test_catzilla_without_jemalloc():
    """Test Catzilla initialization with jemalloc disabled"""
    print("\n=== Testing Catzilla with use_jemalloc=False ===")
    
    try:
        from catzilla.app import Catzilla
        
        # Create Catzilla instance with jemalloc disabled
        app = Catzilla(use_jemalloc=False, memory_profiling=False)
        
        # Get allocator information
        allocator_info = app.get_allocator_info()
        print(f"Allocator info: {allocator_info}")
        
        # Get memory stats
        memory_stats = app.get_memory_stats()
        print(f"Memory stats: {memory_stats}")
        
        print(f"Successfully created Catzilla with jemalloc disabled: {not app.use_jemalloc}")
        print(f"Using allocator: {allocator_info.get('current_allocator', 'unknown')}")
        
        return app
        
    except Exception as e:
        print(f"Error creating Catzilla without jemalloc: {e}")
        return None

def test_memory_functionality(app):
    """Test memory-related functionality"""
    if not app:
        return
        
    print(f"\n=== Testing Memory Functionality ===")
    
    try:
        # Test memory stats
        stats = app.get_memory_stats()
        print(f"Current allocator: {stats.get('allocator', 'unknown')}")
        print(f"Jemalloc available: {stats.get('jemalloc_available', False)}")
        print(f"Jemalloc enabled: {stats.get('jemalloc_enabled', False)}")
        
        if stats.get('jemalloc_enabled'):
            print(f"Memory allocated: {stats.get('allocated_mb', 0):.2f} MB")
            print(f"Memory fragmentation: {stats.get('fragmentation_percent', 0):.2f}%")
        
        # Test allocator info
        info = app.get_allocator_info()
        print(f"Runtime status: {info.get('status', 'unknown')}")
        
    except Exception as e:
        print(f"Error testing memory functionality: {e}")

def main():
    """Main test function"""
    print("Catzilla Jemalloc Runtime Parameter Test")
    print("=" * 50)
    
    # Test 1: Check availability before creating instances
    jemalloc_available = test_jemalloc_availability()
    
    # Test 2: Create Catzilla with jemalloc enabled
    app_with_jemalloc = test_catzilla_with_jemalloc()
    test_memory_functionality(app_with_jemalloc)
    
    # Test 3: Create Catzilla with jemalloc disabled
    app_without_jemalloc = test_catzilla_without_jemalloc()
    test_memory_functionality(app_without_jemalloc)
    
    # Summary
    print("\n=== Test Summary ===")
    print(f"Jemalloc build support: {jemalloc_available}")
    if app_with_jemalloc:
        print(f"Jemalloc runtime test: {'PASS' if app_with_jemalloc.has_jemalloc == jemalloc_available else 'FALLBACK'}")
    if app_without_jemalloc:
        print(f"Malloc runtime test: {'PASS' if not app_without_jemalloc.has_jemalloc else 'FAIL'}")
    
    print("\nTest completed!")

if __name__ == "__main__":
    main()
