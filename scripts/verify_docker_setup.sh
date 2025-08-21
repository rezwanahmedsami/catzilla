#!/bin/bash
# Docker Testing Setup Verification
# Verifies that the Docker cross-platform testing setup is working correctly

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/.." && pwd )"

echo -e "${BLUE}🔍 Catzilla Docker Testing Setup Verification${NC}"
echo -e "${BLUE}=============================================${NC}"
echo ""

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check file exists and is executable
check_script() {
    local script_path=$1
    local script_name=$2

    if [ -f "$script_path" ] && [ -x "$script_path" ]; then
        echo -e "${GREEN}✅ $script_name${NC}"
        return 0
    else
        echo -e "${RED}❌ $script_name (missing or not executable)${NC}"
        return 1
    fi
}

# Check Docker prerequisites
echo -e "${YELLOW}🐳 Checking Docker Prerequisites${NC}"
echo "--------------------------------"

if command_exists docker; then
    echo -e "${GREEN}✅ Docker installed${NC}"
    DOCKER_VERSION=$(docker --version | cut -d' ' -f3 | cut -d',' -f1)
    echo -e "${CYAN}   Version: $DOCKER_VERSION${NC}"
else
    echo -e "${RED}❌ Docker not installed${NC}"
    echo "   Please install Docker Desktop: https://www.docker.com/products/docker-desktop"
    exit 1
fi

if command_exists docker-compose; then
    echo -e "${GREEN}✅ Docker Compose installed${NC}"
    COMPOSE_VERSION=$(docker-compose --version | cut -d' ' -f3 | cut -d',' -f1)
    echo -e "${CYAN}   Version: $COMPOSE_VERSION${NC}"
else
    echo -e "${RED}❌ Docker Compose not installed${NC}"
    exit 1
fi

if docker info >/dev/null 2>&1; then
    echo -e "${GREEN}✅ Docker daemon running${NC}"
else
    echo -e "${RED}❌ Docker daemon not running${NC}"
    echo "   Please start Docker Desktop"
    exit 1
fi

echo ""

# Check project structure
echo -e "${YELLOW}📁 Checking Project Structure${NC}"
echo "------------------------------"

cd "$PROJECT_ROOT"

if [ -f "docker/docker-compose.yml" ]; then
    echo -e "${GREEN}✅ docker-compose.yml${NC}"
else
    echo -e "${RED}❌ docker-compose.yml missing${NC}"
    exit 1
fi

if [ -f "docker/linux/Dockerfile" ]; then
    echo -e "${GREEN}✅ Linux Dockerfile${NC}"
else
    echo -e "${RED}❌ Linux Dockerfile missing${NC}"
    exit 1
fi

if [ -f "docker/windows/Dockerfile" ]; then
    echo -e "${GREEN}✅ Windows Dockerfile${NC}"
else
    echo -e "${RED}❌ Windows Dockerfile missing${NC}"
    exit 1
fi

if [ -f "docker/linux/test.sh" ] && [ -x "docker/linux/test.sh" ]; then
    echo -e "${GREEN}✅ Linux test script${NC}"
else
    echo -e "${RED}❌ Linux test script missing or not executable${NC}"
    exit 1
fi

if [ -f "docker/windows/test.bat" ]; then
    echo -e "${GREEN}✅ Windows test script${NC}"
else
    echo -e "${RED}❌ Windows test script missing${NC}"
    exit 1
fi

echo ""

# Check scripts
echo -e "${YELLOW}📜 Checking Docker Scripts${NC}"
echo "---------------------------"

SCRIPT_CHECKS=0
SCRIPT_TOTAL=0

check_script "$PROJECT_ROOT/scripts/setup_docker_testing.sh" "Setup script" && ((SCRIPT_CHECKS++))
((SCRIPT_TOTAL++))

check_script "$PROJECT_ROOT/scripts/docker_manager.sh" "Docker manager" && ((SCRIPT_CHECKS++))
((SCRIPT_TOTAL++))

check_script "$PROJECT_ROOT/scripts/docker_test_report.sh" "Test report generator" && ((SCRIPT_CHECKS++))
((SCRIPT_TOTAL++))

check_script "$PROJECT_ROOT/scripts/simulate_ci.sh" "CI simulator" && ((SCRIPT_CHECKS++))
((SCRIPT_TOTAL++))

check_script "$PROJECT_ROOT/scripts/run_tests.sh" "Main test runner" && ((SCRIPT_CHECKS++))
((SCRIPT_TOTAL++))

echo ""

# Check convenience scripts
if [ -f "$PROJECT_ROOT/scripts/test_docker_quick.sh" ]; then
    echo -e "${GREEN}✅ Quick test script${NC}"
else
    echo -e "${YELLOW}⚠️  Quick test script not found (will be created)${NC}"
fi

if [ -f "$PROJECT_ROOT/scripts/test_docker_full.sh" ]; then
    echo -e "${GREEN}✅ Full test script${NC}"
else
    echo -e "${YELLOW}⚠️  Full test script not found (will be created)${NC}"
fi

echo ""

# Test Docker Compose configuration
echo -e "${YELLOW}🔧 Testing Docker Compose Configuration${NC}"
echo "----------------------------------------"

if docker-compose -f docker/docker-compose.yml config >/dev/null 2>&1; then
    echo -e "${GREEN}✅ Docker Compose configuration valid${NC}"
else
    echo -e "${RED}❌ Docker Compose configuration invalid${NC}"
    docker-compose -f docker/docker-compose.yml config
    exit 1
fi

echo ""

# Test basic Docker functionality
echo -e "${YELLOW}🧪 Testing Basic Docker Functionality${NC}"
echo "--------------------------------------"

echo -e "${CYAN}Testing hello-world container...${NC}"
if docker run --rm hello-world >/dev/null 2>&1; then
    echo -e "${GREEN}✅ Docker container execution working${NC}"
else
    echo -e "${RED}❌ Docker container execution failed${NC}"
    exit 1
fi

echo ""

# Check if images exist
echo -e "${YELLOW}🖼️  Checking Catzilla Docker Images${NC}"
echo "-----------------------------------"

LINUX_IMAGE_EXISTS=false
WINDOWS_IMAGE_EXISTS=false

if docker images | grep -q "catzilla.*linux"; then
    echo -e "${GREEN}✅ Catzilla Linux image found${NC}"
    LINUX_IMAGE_EXISTS=true
else
    echo -e "${YELLOW}⚠️  Catzilla Linux image not found (will be built)${NC}"
fi

if docker images | grep -q "catzilla.*windows"; then
    echo -e "${GREEN}✅ Catzilla Windows image found${NC}"
    WINDOWS_IMAGE_EXISTS=true
else
    echo -e "${YELLOW}⚠️  Catzilla Windows image not found (will be built)${NC}"
fi

echo ""

# Summary
echo -e "${BLUE}📊 Verification Summary${NC}"
echo "======================"

echo -e "${CYAN}Scripts: $SCRIPT_CHECKS/$SCRIPT_TOTAL available${NC}"

if [ "$SCRIPT_CHECKS" -eq "$SCRIPT_TOTAL" ]; then
    echo -e "${GREEN}✅ All essential scripts available${NC}"
else
    echo -e "${YELLOW}⚠️  Some scripts missing - run setup_docker_testing.sh${NC}"
fi

if [ "$LINUX_IMAGE_EXISTS" = true ]; then
    echo -e "${GREEN}✅ Linux testing ready${NC}"
else
    echo -e "${YELLOW}⚠️  Linux image needs building${NC}"
fi

if [ "$WINDOWS_IMAGE_EXISTS" = true ]; then
    echo -e "${GREEN}✅ Windows testing ready${NC}"
else
    echo -e "${YELLOW}⚠️  Windows image needs building${NC}"
fi

echo ""

# Recommendations
echo -e "${BLUE}🎯 Next Steps${NC}"
echo "============="

if [ "$SCRIPT_CHECKS" -lt "$SCRIPT_TOTAL" ] || [ "$LINUX_IMAGE_EXISTS" = false ]; then
    echo -e "${YELLOW}1. Run setup script:${NC}"
    echo "   ./scripts/setup_docker_testing.sh"
    echo ""
fi

echo -e "${YELLOW}2. Test the setup:${NC}"
echo "   ./scripts/run_tests.sh --docker linux"
echo ""

echo -e "${YELLOW}3. Try the CI simulator:${NC}"
echo "   ./scripts/simulate_ci.sh --fast"
echo ""

echo -e "${YELLOW}4. Read the documentation:${NC}"
echo "   cat docker/README.md"
echo ""

# Overall status
if [ "$SCRIPT_CHECKS" -eq "$SCRIPT_TOTAL" ] && command_exists docker && docker info >/dev/null 2>&1; then
    echo -e "${GREEN}🎉 Docker testing setup verification PASSED!${NC}"
    echo -e "${GREEN}   Ready for cross-platform testing!${NC}"
    exit 0
else
    echo -e "${YELLOW}⚠️  Setup needs attention - follow the next steps above${NC}"
    exit 1
fi
