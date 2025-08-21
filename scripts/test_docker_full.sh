#!/bin/bash
# Full cross-platform Docker testing script

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/.." && pwd )"

cd "$PROJECT_ROOT"

echo "🌍 Full Cross-Platform Docker Test"
echo "=================================="

# Test all platforms
echo "Testing all platforms..."
./scripts/run_tests.sh --docker all

echo "✅ Full cross-platform test completed!"
