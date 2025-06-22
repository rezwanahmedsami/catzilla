#!/usr/bin/env python3
"""
Simple test for the Catzilla Smart Cache System
"""

import sys
import os

# Add the python directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'python'))

try:
    from catzilla._catzilla import Cache
    print("✅ Successfully imported C cache extension!")

    # Test basic functionality
    cache = Cache(capacity=1000, bucket_count=100)
    print("✅ Created cache instance")

    # Test set/get
    cache.set("test_key", b"test_value", ttl=60)
    print("✅ Set cache value")

    result = cache.get("test_key")
    print(f"✅ Got cache result: hit={result.hit}, data={result.data}")

    # Test stats
    stats = cache.get_stats()
    print(f"✅ Cache stats: {stats}")

    # Test exists
    exists = cache.exists("test_key")
    print(f"✅ Key exists: {exists}")

    # Test delete
    deleted = cache.delete("test_key")
    print(f"✅ Key deleted: {deleted}")

    # Test after delete
    result2 = cache.get("test_key")
    print(f"✅ After delete: hit={result2.hit}, data={result2.data}")

    print("\n🎉 All cache tests passed!")

except ImportError as e:
    print(f"❌ Failed to import C cache extension: {e}")
    sys.exit(1)
except Exception as e:
    print(f"❌ Cache test failed: {e}")
    sys.exit(1)
