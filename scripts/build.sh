#!/bin/bash
set -e  # Exit on error

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${YELLOW}🔨 Starting Catzilla development build...${NC}"

# 1. Clean previous builds
echo -e "\n${GREEN}Cleaning previous builds...${NC}"
rm -rf build/ dist/ *.egg-info/
find . -name "*.so" -delete
find . -name "*.pyc" -delete
find . -name "__pycache__" -type d -exec rm -rf {} +

# 2. Create build directory
echo -e "\n${GREEN}Creating build directory...${NC}"
mkdir -p build
cd build

# 3. Configure with CMake
echo -e "\n${GREEN}Configuring with CMake...${NC}"
cmake .. \
    -DCMAKE_BUILD_TYPE=Debug \
    -DPython3_EXECUTABLE=$(which python3)

# 4. Build
echo -e "\n${GREEN}Building...${NC}"
cmake --build . -j$(nproc 2>/dev/null || sysctl -n hw.ncpu)

# 5. Copy the built extension to the right place
echo -e "\n${GREEN}Installing...${NC}"
cd ..

# Uninstall any existing version
python3 -m pip uninstall -y catzilla || true

# Install in development mode
python3 -m pip install -e .

echo -e "\n${GREEN}✅ Build complete!${NC}"
echo -e "${YELLOW}You can now run examples with: python3 examples/hello_world/main.py${NC}"
