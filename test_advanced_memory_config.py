#!/usr/bin/env python3
"""
Test the new advanced memory configuration options in Catzilla v0.2.0
"""

import sys
import time
from catzilla import Catzilla

def test_basic_configuration():
    """Test basic memory configuration"""
    print("=== Testing Basic Memory Configuration ===")

    # Basic configuration (default)
    app1 = Catzilla()
    print(f"Basic app - jemalloc: {app1.has_jemalloc}")

    # Production with jemalloc disabled
    app2 = Catzilla(
        production=True,
        use_jemalloc=False
    )
    print(f"Production app (no jemalloc) - jemalloc: {app2.has_jemalloc}")
    print()

def test_advanced_configuration():
    """Test advanced memory configuration options"""
    print("=== Testing Advanced Memory Configuration ===")

    # Full memory revolution configuration
    app = Catzilla(
        production=False,
        use_jemalloc=True,           # 30% less memory usage
        memory_profiling=True,       # Real-time optimization
        auto_memory_tuning=True,     # Adaptive memory management
        memory_stats_interval=10     # Check every 10 seconds
    )

    print(f"Advanced app configuration:")
    print(f"  - Production mode: {app.production}")
    print(f"  - jemalloc enabled: {app.has_jemalloc}")
    print(f"  - Memory profiling: {app.memory_profiling}")
    print(f"  - Auto-tuning: {app.auto_memory_tuning}")
    print(f"  - Stats interval: {app.memory_stats_interval}s")

    # Test memory stats
    stats = app.get_memory_stats()
    print(f"\n📊 Memory Statistics:")
    for key, value in stats.items():
        if isinstance(value, float):
            print(f"  {key}: {value:.2f}")
        else:
            print(f"  {key}: {value}")

    # Test memory profile (if profiling enabled)
    if app.memory_profiling:
        print(f"\n🔍 Memory Profile:")
        profile = app.get_memory_profile()
        print(f"  Total checks: {profile.get('total_checks', 0)}")
        print(f"  Check interval: {profile.get('check_interval_seconds', 0)}s")
        print(f"  Auto-tuning: {profile.get('auto_tuning_enabled', False)}")

    return app

def test_memory_configurations():
    """Test different memory configuration combinations"""
    print("\n=== Testing Different Memory Configurations ===")

    configs = [
        {
            "name": "Minimal (Standard Memory)",
            "config": {"use_jemalloc": False}
        },
        {
            "name": "Basic jemalloc",
            "config": {"use_jemalloc": True, "memory_profiling": False}
        },
        {
            "name": "jemalloc + Profiling",
            "config": {"use_jemalloc": True, "memory_profiling": True, "auto_memory_tuning": False}
        },
        {
            "name": "Full Memory Revolution",
            "config": {
                "use_jemalloc": True,
                "memory_profiling": True,
                "auto_memory_tuning": True,
                "memory_stats_interval": 30
            }
        }
    ]

    for config_info in configs:
        print(f"\n🔧 {config_info['name']}:")
        app = Catzilla(**config_info['config'])
        stats = app.get_memory_stats()

        print(f"  jemalloc: {'✅' if stats.get('jemalloc_enabled') else '❌'}")
        print(f"  profiling: {'✅' if stats.get('profiling_enabled') else '❌'}")
        if stats.get('jemalloc_enabled'):
            print(f"  allocated: {stats.get('allocated_mb', 0):.2f} MB")
            print(f"  fragmentation: {stats.get('fragmentation_percent', 0):.1f}%")

def demonstrate_api_usage():
    """Demonstrate the new API usage patterns"""
    print("\n=== API Usage Examples ===")

    print("\n1. Development with full monitoring:")
    print("""
app = Catzilla(
    use_jemalloc=True,
    memory_profiling=True,
    auto_memory_tuning=True,
    memory_stats_interval=10
)
""")

    print("2. Production optimized:")
    print("""
app = Catzilla(
    production=True,
    use_jemalloc=True,
    memory_profiling=False,  # Disabled for production
    auto_memory_tuning=True
)
""")

    print("3. Testing/debugging with standard memory:")
    print("""
app = Catzilla(
    use_jemalloc=False,      # Use standard malloc for debugging
    memory_profiling=False
)
""")

def main():
    print("🚀 Catzilla v0.2.0 Advanced Memory Configuration Test")
    print("=" * 60)

    try:
        test_basic_configuration()
        app = test_advanced_configuration()
        test_memory_configurations()
        demonstrate_api_usage()

        print("\n✅ All memory configuration tests completed successfully!")

        # If we have an app with profiling, wait a bit to show profiling in action
        if hasattr(app, 'memory_profiling') and app.memory_profiling:
            print("\n⏱️  Waiting 15 seconds to demonstrate memory profiling...")
            time.sleep(15)

            # Show updated profile
            profile = app.get_memory_profile()
            print(f"\n📈 Updated Memory Profile:")
            print(f"  Total checks: {profile.get('total_checks', 0)}")
            if profile.get('stats_history'):
                latest = profile['stats_history'][-1]
                print(f"  Latest allocated: {latest.get('allocated_mb', 0):.2f} MB")
                print(f"  Latest fragmentation: {latest.get('fragmentation_percent', 0):.1f}%")

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
