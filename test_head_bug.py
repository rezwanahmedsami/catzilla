#!/usr/bin/env python3
"""
Test to isolate the HEAD method bug
"""

import sys
sys.path.insert(0, 'python')

from catzilla._catzilla import router_add_route, router_match

def test_head_bug():
    print("Testing HEAD method bug...")

    # First, test HEAD by itself
    print("\n1. Testing HEAD alone:")
    route_id = router_add_route('HEAD', '/head_test', 100)
    print(f"   Added HEAD route: {route_id}")

    match = router_match('HEAD', '/head_test')
    print(f"   HEAD match: {match}")

    # Now test GET alone
    print("\n2. Testing GET alone:")
    route_id = router_add_route('GET', '/get_test', 200)
    print(f"   Added GET route: {route_id}")

    match = router_match('GET', '/get_test')
    print(f"   GET match: {match}")

    # Now test if HEAD can match GET path
    print("\n3. Testing HEAD on GET path:")
    match = router_match('HEAD', '/get_test')
    print(f"   HEAD match on GET path: {match}")

    # Test if GET can match HEAD path
    print("\n4. Testing GET on HEAD path:")
    match = router_match('GET', '/head_test')
    print(f"   GET match on HEAD path: {match}")

    # Test mixed case
    print("\n5. Testing mixed case:")
    route_id = router_add_route('head', '/head_lower', 300)
    print(f"   Added 'head' route: {route_id}")

    match = router_match('head', '/head_lower')
    print(f"   'head' match: {match}")

    match = router_match('HEAD', '/head_lower')
    print(f"   'HEAD' match on 'head' route: {match}")

if __name__ == "__main__":
    test_head_bug()
