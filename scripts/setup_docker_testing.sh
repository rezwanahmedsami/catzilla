#!/bin/bash
# Catzilla Docker Testing Setup Script
# Sets up comprehensive cross-platform Docker testing environment

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/.." && pwd )"

echo -e "${BLUE}🚀 Catzilla Docker Testing Setup${NC}"
echo -e "${BLUE}================================${NC}"
echo ""

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check Docker requirements
check_docker_requirements() {
    echo -e "${YELLOW}🔍 Checking Docker requirements...${NC}"

    if ! command_exists docker; then
        echo -e "${RED}❌ Docker is not installed${NC}"
        echo "Please install Docker Desktop from: https://www.docker.com/products/docker-desktop"
        return 1
    fi

    if ! command_exists docker-compose; then
        echo -e "${RED}❌ Docker Compose is not installed${NC}"
        echo "Please install Docker Compose or use Docker Desktop which includes it"
        return 1
    fi

    # Check if Docker is running
    if ! docker info >/dev/null 2>&1; then
        echo -e "${RED}❌ Docker daemon is not running${NC}"
        echo "Please start Docker Desktop or the Docker daemon"
        return 1
    fi

    echo -e "${GREEN}✅ Docker and Docker Compose are available${NC}"

    # Check Docker version
    DOCKER_VERSION=$(docker --version | cut -d' ' -f3 | cut -d',' -f1)
    echo -e "${GREEN}  Docker version: ${DOCKER_VERSION}${NC}"

    COMPOSE_VERSION=$(docker-compose --version | cut -d' ' -f3 | cut -d',' -f1)
    echo -e "${GREEN}  Docker Compose version: ${COMPOSE_VERSION}${NC}"

    return 0
}

# Function to check available platforms
check_platform_support() {
    echo -e "${YELLOW}🌍 Checking platform support...${NC}"

    # Check if Windows containers are supported (on Windows/WSL)
    if docker system info 2>/dev/null | grep -q "OSType: linux"; then
        echo -e "${GREEN}✅ Linux containers supported${NC}"
        LINUX_SUPPORT=true
    else
        echo -e "${RED}❌ Linux containers not available${NC}"
        LINUX_SUPPORT=false
    fi

    # Windows container support is more complex to detect
    if [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "win32" ]] || [[ -n "${WSL_DISTRO_NAME:-}" ]]; then
        echo -e "${YELLOW}⚠️  Windows containers may be available${NC}"
        echo -e "${YELLOW}   Note: Requires Docker Desktop with Windows containers enabled${NC}"
        WINDOWS_SUPPORT=true
    else
        echo -e "${YELLOW}⚠️  Windows containers not available on this platform${NC}"
        WINDOWS_SUPPORT=false
    fi
}

# Function to build Docker images
build_docker_images() {
    echo -e "${YELLOW}🔨 Building Docker images...${NC}"
    cd "$PROJECT_ROOT"

    if [ "$LINUX_SUPPORT" = true ]; then
        echo -e "${GREEN}🐧 Building Linux testing image...${NC}"
        docker-compose -f docker/docker-compose.yml build catzilla-linux
        echo -e "${GREEN}🐧 Building Linux development image...${NC}"
        docker-compose -f docker/docker-compose.yml build catzilla-dev-linux
    fi

    if [ "$WINDOWS_SUPPORT" = true ]; then
        echo -e "${GREEN}🪟 Building Windows testing image...${NC}"
        echo -e "${YELLOW}   Note: This may take a while for the first build...${NC}"
        docker-compose -f docker/docker-compose.yml build catzilla-windows || {
            echo -e "${RED}❌ Windows image build failed${NC}"
            echo -e "${YELLOW}   This is normal if Windows containers are not enabled${NC}"
        }
        echo -e "${GREEN}🪟 Building Windows development image...${NC}"
        docker-compose -f docker/docker-compose.yml build catzilla-dev-windows || {
            echo -e "${RED}❌ Windows development image build failed${NC}"
            echo -e "${YELLOW}   This is normal if Windows containers are not enabled${NC}"
        }
    fi
}

# Function to test the setup
test_docker_setup() {
    echo -e "${YELLOW}🧪 Testing Docker setup...${NC}"
    cd "$PROJECT_ROOT"

    if [ "$LINUX_SUPPORT" = true ]; then
        echo -e "${GREEN}🐧 Testing Linux container...${NC}"
        if docker-compose -f docker/docker-compose.yml run --rm catzilla-linux python3 --version; then
            echo -e "${GREEN}✅ Linux container working${NC}"
        else
            echo -e "${RED}❌ Linux container test failed${NC}"
            return 1
        fi
    fi

    # Test Windows container only if build succeeded
    if [ "$WINDOWS_SUPPORT" = true ]; then
        echo -e "${GREEN}🪟 Testing Windows container (if available)...${NC}"
        if docker-compose -f docker/docker-compose.yml run --rm catzilla-windows python --version 2>/dev/null; then
            echo -e "${GREEN}✅ Windows container working${NC}"
        else
            echo -e "${YELLOW}⚠️  Windows container not available or failed${NC}"
        fi
    fi
}

# Function to create convenience scripts
create_convenience_scripts() {
    echo -e "${YELLOW}📝 Creating convenience scripts...${NC}"

    # Create quick test script
    cat > "$PROJECT_ROOT/scripts/test_docker_quick.sh" << 'EOF'
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
EOF
    chmod +x "$PROJECT_ROOT/scripts/test_docker_quick.sh"

    # Create full cross-platform test script
    cat > "$PROJECT_ROOT/scripts/test_docker_full.sh" << 'EOF'
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
EOF
    chmod +x "$PROJECT_ROOT/scripts/test_docker_full.sh"

    echo -e "${GREEN}✅ Convenience scripts created:${NC}"
    echo -e "${GREEN}   - scripts/test_docker_quick.sh${NC}"
    echo -e "${GREEN}   - scripts/test_docker_full.sh${NC}"
}

# Function to display usage instructions
display_usage_instructions() {
    echo ""
    echo -e "${BLUE}🎉 Docker Testing Setup Complete!${NC}"
    echo -e "${BLUE}===================================${NC}"
    echo ""
    echo -e "${GREEN}Available Commands:${NC}"
    echo ""
    echo -e "${YELLOW}Quick Testing:${NC}"
    echo "  ./scripts/run_tests.sh --docker linux      # Test on Linux only"
    echo "  ./scripts/test_docker_quick.sh             # Quick Linux test"
    echo ""
    echo -e "${YELLOW}Full Cross-Platform Testing:${NC}"
    echo "  ./scripts/run_tests.sh --docker all        # Test all platforms"
    echo "  ./scripts/run_tests.sh --docker windows    # Test Windows only"
    echo "  ./scripts/test_docker_full.sh              # Full test suite"
    echo ""
    echo -e "${YELLOW}Development:${NC}"
    echo "  ./docker/docker-dev.sh shell linux         # Interactive Linux shell"
    echo "  ./docker/docker-dev.sh shell windows       # Interactive Windows shell"
    echo "  ./docker/docker-dev.sh build all           # Rebuild images"
    echo ""
    echo -e "${YELLOW}Maintenance:${NC}"
    echo "  ./docker/docker-dev.sh clean               # Clean Docker resources"
    echo "  ./docker/docker-dev.sh logs linux          # View container logs"
    echo ""
    echo -e "${GREEN}💡 Pro Tips:${NC}"
    echo "  - Use Linux testing for fastest feedback"
    echo "  - Run full cross-platform tests before pushing"
    echo "  - Interactive shells great for debugging"
    echo "  - Clean up regularly to save disk space"
    echo ""
}

# Main execution
main() {
    # Check requirements
    if ! check_docker_requirements; then
        exit 1
    fi

    # Check platform support
    check_platform_support

    # Build images
    build_docker_images

    # Test setup
    test_docker_setup

    # Create convenience scripts
    create_convenience_scripts

    # Display usage instructions
    display_usage_instructions

    echo -e "${GREEN}🚀 Setup complete! Happy cross-platform testing! 🎯${NC}"
}

# Run main function
main "$@"
