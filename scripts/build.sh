#!/bin/bash
set -e  # Exit on error

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${YELLOW}🔨 Starting Catzilla development build...${NC}"

# 1. Build jemalloc if needed
echo -e "\n${GREEN}Step 1: Building jemalloc (if needed)...${NC}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
"${SCRIPT_DIR}/build_jemalloc.sh"
if [ $? -ne 0 ]; then
    echo -e "${YELLOW}⚠️  Warning: jemalloc build failed, continuing with system malloc${NC}"
fi

# 2. Clean previous builds
echo -e "\n${GREEN}Step 2: Cleaning previous builds...${NC}"
rm -rf build/ dist/ *.egg-info/
find . -name "*.so" -delete
find . -name "*.pyc" -delete
find . -name "__pycache__" -type d -exec rm -rf {} +

# 3. Create build directory
echo -e "\n${GREEN}Step 3: Creating build directory...${NC}"
mkdir -p build
cd build

# 4. Configure with CMake
echo -e "\n${GREEN}Step 4: Configuring with CMake...${NC}"
cmake .. \
    -DCMAKE_BUILD_TYPE=Debug \
    -DPython3_EXECUTABLE=$(which python3)

# 5. Build
echo -e "\n${GREEN}Step 5: Building...${NC}"
cmake --build . -j$(nproc 2>/dev/null || sysctl -n hw.ncpu)

# 6. Copy the built extension to the right place
echo -e "\n${GREEN}Step 6: Installing...${NC}"
cd ..

# Uninstall any existing version
python3 -m pip uninstall -y catzilla || true

# Install in development mode
python3 -m pip install -e .

echo -e "\n${GREEN}✅ Build complete!${NC}"
echo -e "${YELLOW}You can now run examples with: ./scripts/run_example.sh examples/hello_world/main.py${NC}"
