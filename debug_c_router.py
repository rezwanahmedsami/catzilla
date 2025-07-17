#!/usr/bin/env python3
"""
Debug C router issue with HEAD method
"""

import sys
import os
sys.path.insert(0, 'python')

# Test the C extension directly
try:
    from catzilla._catzilla import router_add_route, router_match

    print("Testing C router HEAD method issue...")

    # Add GET route first
    result = router_add_route('GET', '/test', 1)
    print(f'Added GET route: {result}')

    # Add HEAD route
    result = router_add_route('HEAD', '/test', 2)
    print(f'Added HEAD route: {result}')

    # Add OPTIONS route
    result = router_add_route('OPTIONS', '/test', 3)
    print(f'Added OPTIONS route: {result}')

    # Try matching GET
    get_match = router_match('GET', '/test')
    print(f'GET match: {get_match}')

    # Try matching HEAD
    head_match = router_match('HEAD', '/test')
    print(f'HEAD match: {head_match}')

    # Try matching OPTIONS
    options_match = router_match('OPTIONS', '/test')
    print(f'OPTIONS match: {options_match}')

    print("\nLet's test different order...")

    # Try adding HEAD first
    result = router_add_route('HEAD', '/test2', 10)
    print(f'Added HEAD route to /test2: {result}')

    # Now match it
    head_match2 = router_match('HEAD', '/test2')
    print(f'HEAD match for /test2: {head_match2}')

    # Now add GET to same path
    result = router_add_route('GET', '/test2', 11)
    print(f'Added GET route to /test2: {result}')

    # Match HEAD again
    head_match3 = router_match('HEAD', '/test2')
    print(f'HEAD match for /test2 after GET: {head_match3}')

    # Match GET
    get_match2 = router_match('GET', '/test2')
    print(f'GET match for /test2: {get_match2}')

except ImportError as e:
    print(f'C extension not available: {e}')
    import traceback
    traceback.print_exc()
