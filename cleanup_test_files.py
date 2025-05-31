#!/usr/bin/env python3
"""
Cleanup script for temporary test files created during optional field development.
Keeps only the important test files and removes debug/temporary ones.
"""

import os
import shutil

# Files to keep (important for ongoing development/testing)
KEEP_FILES = {
    'test_final_verification.py',        # Final comprehensive test
    'test_performance_verification.py',  # Performance verification
    'test_optional_fields.py',          # Original comprehensive test
    'test_basic_app.py',                # Basic application test
    'test_validation.py',               # Core validation tests
}

# Files to remove (temporary/debug files from development)
REMOVE_FILES = {
    'test_debug_segfault.py',
    'test_ultra_minimal.py',
    'test_minimal.py',
    'test_minimal_optional.py',
    'test_creation_only.py',
    'test_exact_combo.py',
    'test_explicit_fields.py',
    'test_field_combinations.py',
    'test_validation_direct.py',
    'test_validation_simple.py',
    'test_type_hints_only.py',
    'test_comprehensive.py',
    'test_float_field.py',
    'test_bool_field.py',
    'test_jemalloc_integration.py',
    'test_memory_debug.py',
}

def cleanup_test_files():
    """Remove temporary test files created during development."""
    print("=== Cleaning up temporary test files ===")

    removed_count = 0
    kept_count = 0

    for filename in os.listdir('.'):
        if filename.startswith('test_') and filename.endswith('.py'):
            if filename in REMOVE_FILES:
                try:
                    os.remove(filename)
                    print(f"🗑️  Removed: {filename}")
                    removed_count += 1
                except OSError as e:
                    print(f"❌ Failed to remove {filename}: {e}")
            elif filename in KEEP_FILES:
                print(f"✅ Kept: {filename}")
                kept_count += 1
            else:
                print(f"🤔 Unknown test file (not in cleanup list): {filename}")

    print(f"\n📊 Cleanup Summary:")
    print(f"   • Files removed: {removed_count}")
    print(f"   • Files kept: {kept_count}")
    print(f"   • Important tests preserved for ongoing development")

if __name__ == '__main__':
    cleanup_test_files()
