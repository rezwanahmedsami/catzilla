#!/bin/bash
# Quick Docker testing script

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/.." && pwd )"

cd "$PROJECT_ROOT"

echo "🚀 Quick Docker Test"
echo "===================="

# Test Linux only (fastest)
echo "🐧 Testing on Linux..."
./scripts/run_tests.sh --docker linux

echo "✅ Quick test completed!"
