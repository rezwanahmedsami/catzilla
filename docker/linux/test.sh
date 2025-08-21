#!/bin/bash
set -e

echo "🐧 Testing Catzilla on Linux (Ubuntu 22.04)"
echo "============================================"
echo ""

# Display environment information
echo "📍 Environment Information:"
echo "  OS: $(cat /etc/os-release | grep PRETTY_NAME | cut -d'"' -f2)"
echo "  Python: $(python3 --version)"
echo "  CMake: $(cmake --version | head -n1)"
echo "  jemalloc: $(dpkg -l | grep jemalloc | head -n1 | awk '{print $2 " " $3}')"
echo ""

# Verify jemalloc preloading
echo "🔍 Verifying jemalloc configuration..."
if [ -n "$LD_PRELOAD" ]; then
    echo "✅ LD_PRELOAD configured: $LD_PRELOAD"
else
    echo "⚠️  Setting up jemalloc preload..."
    export LD_PRELOAD=/lib/x86_64-linux-gnu/libjemalloc.so.2:$LD_PRELOAD
fi

# Run jemalloc helper for additional verification
echo "📋 Running jemalloc detection..."
python3 scripts/jemalloc_helper.py --detect
echo ""

# Build the project (should already be built in Docker image)
echo "🔨 Verifying Catzilla build..."
if [ ! -f "build/_catzilla.so" ]; then
    echo "Building Catzilla..."
    ./scripts/build.sh
else
    echo "✅ Catzilla already built"
fi
echo ""

# Run comprehensive tests
echo "🧪 Running comprehensive test suite..."
echo "----------------------------------------"

# Run C tests first
echo "🔧 Running C tests..."
./scripts/run_tests.sh --c

# Run Python tests
echo "🐍 Running Python tests..."
./scripts/run_tests.sh --python

# Run cross-platform jemalloc verification
echo "🌍 Running cross-platform jemalloc tests..."
if [ -f "test_cross_platform_jemalloc.py" ]; then
    python3 test_cross_platform_jemalloc.py
else
    echo "ℹ️  Cross-platform jemalloc test not found, skipping..."
fi

# Run segfault verification tests
echo "🛡️  Running segfault prevention verification..."
if [ -f "scripts/verify_segfault_fix.py" ]; then
    python3 scripts/verify_segfault_fix.py
else
    echo "ℹ️  Segfault verification script not found, skipping..."
fi

# Run memory stress test
echo "🧠 Running memory stress test..."
python3 -c "
import gc
import catzilla
print('Testing memory management...')
for i in range(100):
    app = catzilla.Catzilla()
    app.add_route('GET', f'/test_{i}', lambda req: {'status': 'ok'})
    del app
    if i % 25 == 0:
        gc.collect()
        print(f'Memory test iteration {i}/100')
print('✅ Memory stress test completed')
"

# Performance smoke test
echo "⚡ Running performance smoke test..."
python3 -c "
import time
import catzilla

app = catzilla.Catzilla()
app.add_route('GET', '/', lambda req: {'message': 'Hello World'})

# Measure route matching performance
start = time.time()
for _ in range(10000):
    result = app._router.find_route('GET', '/')
end = time.time()

print(f'Route matching: {10000/(end-start):.0f} ops/sec')
print('✅ Performance smoke test completed')
"

echo ""
echo "✅ Linux tests completed successfully!"
echo "🎉 All systems operational on Ubuntu 22.04"
echo ""
echo "📊 Test Summary:"
echo "  - C tests: ✅"
echo "  - Python tests: ✅"
echo "  - Memory tests: ✅"
echo "  - Performance tests: ✅"
