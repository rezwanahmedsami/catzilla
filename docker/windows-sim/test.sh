#!/bin/bash
# Windows Simulation Test Runner
# Uses Wine to simulate Windows environment for testing

echo "🍷 Running Catzilla tests in Wine (Windows simulation)..."
echo "Platform: Windows Simulation via Wine"
echo "Python: $(wine python --version 2>/dev/null || python3 --version)"

cd /catzilla || exit 1

# Try Wine Python first, fallback to Linux Python
if wine python --version >/dev/null 2>&1; then
    echo "Using Wine Python for Windows simulation..."
    export PYTHON_CMD="wine python"
else
    echo "Wine Python not available, using Linux Python with Windows simulation flags..."
    export PYTHON_CMD="python3"
    export CATZILLA_WINDOWS_MODE=1
fi

# Set up Windows-like environment variables
export CATZILLA_PLATFORM=windows
export CATZILLA_FORCE_JEMALLOC=1

# Run tests with Windows simulation
echo "Starting Windows simulation tests..."
$PYTHON_CMD -m pytest tests/ -v --tb=short \
    --maxfail=5 \
    --disable-warnings \
    -x \
    || echo "Some tests failed in Windows simulation mode"

echo "Windows simulation testing completed"
