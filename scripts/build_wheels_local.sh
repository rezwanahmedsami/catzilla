#!/bin/bash
# Local wheel building script for Catzilla
# Usage: ./scripts/build_wheels_local.sh

set -e  # Exit on any error

echo "🏗️  Building Catzilla wheels locally..."

# Colors for pretty output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get current Python version
PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
echo -e "${BLUE}Using Python ${PYTHON_VERSION}${NC}"

# Clean previous builds
echo -e "${YELLOW}Cleaning previous builds...${NC}"
rm -rf build/ dist/ *.egg-info/ wheelhouse/
mkdir -p dist/

# Install build dependencies
echo -e "${YELLOW}Installing build dependencies...${NC}"
python3 -m pip install --upgrade pip setuptools wheel build

# Method 1: Standard wheel build (using your CMake setup.py)
echo -e "${BLUE}Method 1: Building wheel using standard Python build system...${NC}"
python3 -m build --wheel --sdist
echo -e "${GREEN}✅ Standard build completed${NC}"

# Show what was built
echo -e "${BLUE}Built packages:${NC}"
ls -la dist/

# Test the wheel
echo -e "${YELLOW}Testing wheel installation...${NC}"
WHEEL_FILE=$(ls dist/*.whl | head -1)
if [ -f "$WHEEL_FILE" ]; then
    echo -e "${BLUE}Installing: $(basename "$WHEEL_FILE")${NC}"
    python3 -m pip install "$WHEEL_FILE" --force-reinstall --no-deps

    # Test import
    echo -e "${YELLOW}Testing wheel functionality...${NC}"
    python3 -c "
from catzilla import App, JSONResponse
print('✅ Wheel import successful')
app = App()
@app.get('/')
def test(request):
    return JSONResponse({'status': 'ok', 'version': '0.1.0'})
print('✅ Wheel functionality test passed')
print('🎉 Local wheel build and test completed successfully!')
"
else
    echo -e "${RED}❌ No wheel file found${NC}"
    exit 1
fi

# Show final wheel details
echo -e "${BLUE}Final wheel details:${NC}"
python3 -m pip show catzilla
echo ""
echo -e "${GREEN}🎉 Local wheel building completed!${NC}"
echo -e "${BLUE}Wheel file: ${WHEEL_FILE}${NC}"

# Show wheel naming
WHEEL_NAME=$(basename "$WHEEL_FILE")
echo -e "${BLUE}Wheel naming: ${WHEEL_NAME}${NC}"
echo -e "${YELLOW}This wheel will install on:${NC}"
python3 -c "
import platform
import sys
print(f'  Python: {sys.version_info.major}.{sys.version_info.minor}')
print(f'  Platform: {platform.system()}')
print(f'  Architecture: {platform.machine()}')
"
