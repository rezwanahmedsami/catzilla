#!/usr/bin/env python3
"""
Debug C router - check what methods are actually being stored
"""

import sys
import os
sys.path.insert(0, 'python')

# Test the C extension directly
try:
    from catzilla._catzilla import router_add_route, router_match

    print("Adding HEAD route to /debug...")
    result = router_add_route('HEAD', '/debug', 1)
    print(f'Added HEAD route: {result}')

    print("\nMatching HEAD /debug...")
    head_match = router_match('HEAD', '/debug')
    print(f'HEAD match: {head_match}')

    print("\nMatching GET /debug...")
    get_match = router_match('GET', '/debug')
    print(f'GET match: {get_match}')

    print("\nTesting method normalization...")

    # Test if methods are being normalized
    result = router_add_route('head', '/debug2', 2)  # lowercase
    print(f'Added lowercase "head" route: {result}')

    head_match2 = router_match('HEAD', '/debug2')
    print(f'HEAD match for /debug2: {head_match2}')

    head_match3 = router_match('head', '/debug2')  # lowercase
    print(f'head match for /debug2: {head_match3}')

except ImportError as e:
    print(f'C extension not available: {e}')
    import traceback
    traceback.print_exc()
