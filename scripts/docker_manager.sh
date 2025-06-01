#!/bin/bash
# Advanced Docker Management Script for Catzilla
# Provides comprehensive Docker operations for cross-platform testing

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

print_usage() {
    echo -e "${BLUE}🐳 Catzilla Docker Management${NC}"
    echo -e "${BLUE}============================${NC}"
    echo ""
    echo "Usage: $0 [COMMAND] [OPTIONS]"
    echo ""
    echo -e "${YELLOW}Testing Commands:${NC}"
    echo "  test [linux|windows|all]     Run tests on specified platform(s)"
    echo "  quick                         Quick test on Linux only"
    echo "  ci                           Simulate full CI pipeline"
    echo ""
    echo -e "${YELLOW}Development Commands:${NC}"
    echo "  shell [linux|windows]        Interactive development shell"
    echo "  build [linux|windows|all]    Build Docker images"
    echo "  rebuild [linux|windows|all]  Force rebuild without cache"
    echo ""
    echo -e "${YELLOW}Maintenance Commands:${NC}"
    echo "  clean                         Clean containers and volumes"
    echo "  prune                         Prune Docker system (careful!)"
    echo "  logs [linux|windows]         View container logs"
    echo "  ps                            Show running containers"
    echo "  images                        Show Catzilla Docker images"
    echo ""
    echo -e "${YELLOW}Monitoring Commands:${NC}"
    echo "  stats                         Show container resource usage"
    echo "  health [linux|windows]       Check container health"
    echo "  benchmark [linux|windows|all] Run performance benchmarks"
    echo ""
    echo -e "${GREEN}Examples:${NC}"
    echo "  $0 test linux                # Test on Linux"
    echo "  $0 shell linux               # Interactive Linux shell"
    echo "  $0 ci                         # Full CI simulation"
    echo "  $0 clean                      # Clean up resources"
}

# Function to check Docker status
check_docker() {
    if ! command -v docker >/dev/null 2>&1; then
        echo -e "${RED}❌ Docker not found${NC}"
        exit 1
    fi

    if ! docker info >/dev/null 2>&1; then
        echo -e "${RED}❌ Docker daemon not running${NC}"
        exit 1
    fi
}

# Function to run tests
run_tests() {
    local platform=$1
    cd "$PROJECT_ROOT"

    echo -e "${CYAN}🧪 Running tests on platform: ${platform}${NC}"

    case "$platform" in
        "linux")
            echo -e "${GREEN}🐧 Testing on Linux...${NC}"
            docker-compose -f docker/docker-compose.yml run --rm catzilla-linux
            ;;
        "windows")
            echo -e "${GREEN}🪟 Testing on Windows...${NC}"
            docker-compose -f docker/docker-compose.yml run --rm catzilla-windows
            ;;
        "all"|"")
            echo -e "${GREEN}🌍 Testing on all platforms...${NC}"
            echo -e "${CYAN}Phase 1: Linux Testing${NC}"
            docker-compose -f docker/docker-compose.yml run --rm catzilla-linux
            echo ""
            echo -e "${CYAN}Phase 2: Windows Testing${NC}"
            docker-compose -f docker/docker-compose.yml run --rm catzilla-windows
            ;;
        *)
            echo -e "${RED}❌ Unknown platform: $platform${NC}"
            echo "Supported: linux, windows, all"
            exit 1
            ;;
    esac
}

# Function for quick testing
quick_test() {
    echo -e "${CYAN}⚡ Quick Test (Linux Only)${NC}"
    cd "$PROJECT_ROOT"
    docker-compose -f docker/docker-compose.yml run --rm catzilla-linux bash -c "
        echo '🚀 Quick Catzilla Test'
        echo '===================='

        # Quick build verification
        echo '🔨 Verifying build...'
        ./scripts/build.sh --quick || exit 1

        # Quick Python tests
        echo '🐍 Quick Python tests...'
        python -m pytest tests/python/test_basic_app.py -v || exit 1

        # Quick C tests
        echo '🔧 Quick C tests...'
        if [ -f build/test_router ]; then
            ./build/test_router || exit 1
        fi

        echo '✅ Quick test completed!'
    "
}

# Function to simulate CI pipeline
simulate_ci() {
    echo -e "${CYAN}🏗️  Simulating Full CI Pipeline${NC}"
    echo -e "${CYAN}===============================${NC}"

    cd "$PROJECT_ROOT"

    # Phase 1: Build verification
    echo -e "${YELLOW}Phase 1: Build Verification${NC}"
    docker-compose -f docker/docker-compose.yml run --rm catzilla-linux bash -c "
        ./scripts/build.sh || exit 1
        echo '✅ Build verification passed'
    "

    # Phase 2: Code quality checks
    echo -e "${YELLOW}Phase 2: Code Quality Checks${NC}"
    docker-compose -f docker/docker-compose.yml run --rm catzilla-linux bash -c "
        echo '🔍 Running linting...'
        python -m flake8 python/catzilla/ --count --select=E9,F63,F7,F82 --show-source --statistics || exit 1
        echo '🛡️  Running security checks...'
        python -m bandit -r python/catzilla/ -f json -o /dev/null || exit 1
        echo '✅ Code quality checks passed'
    "

    # Phase 3: Cross-platform testing
    echo -e "${YELLOW}Phase 3: Cross-Platform Testing${NC}"
    run_tests "all"

    # Phase 4: Performance verification
    echo -e "${YELLOW}Phase 4: Performance Verification${NC}"
    docker-compose -f docker/docker-compose.yml run --rm catzilla-linux bash -c "
        echo '⚡ Running performance verification...'
        python test_performance_verification.py || exit 1
        echo '✅ Performance verification passed'
    "

    echo -e "${GREEN}🎉 CI Pipeline Simulation Completed Successfully!${NC}"
}

# Function to open interactive shell
open_shell() {
    local platform=$1
    cd "$PROJECT_ROOT"

    case "$platform" in
        "linux")
            echo -e "${GREEN}🐧 Opening Linux development shell...${NC}"
            docker-compose -f docker/docker-compose.yml run --rm catzilla-dev-linux
            ;;
        "windows")
            echo -e "${GREEN}🪟 Opening Windows development shell...${NC}"
            docker-compose -f docker/docker-compose.yml run --rm catzilla-dev-windows
            ;;
        *)
            echo -e "${RED}❌ Unknown platform: $platform${NC}"
            echo "Supported: linux, windows"
            exit 1
            ;;
    esac
}

# Function to build images
build_images() {
    local platform=$1
    local no_cache=${2:-false}

    cd "$PROJECT_ROOT"

    local build_args=""
    if [ "$no_cache" = true ]; then
        build_args="--no-cache"
    fi

    case "$platform" in
        "linux")
            echo -e "${GREEN}🐧 Building Linux images...${NC}"
            docker-compose -f docker/docker-compose.yml build $build_args catzilla-linux catzilla-dev-linux
            ;;
        "windows")
            echo -e "${GREEN}🪟 Building Windows images...${NC}"
            docker-compose -f docker/docker-compose.yml build $build_args catzilla-windows catzilla-dev-windows
            ;;
        "all"|"")
            echo -e "${GREEN}🌍 Building all images...${NC}"
            docker-compose -f docker/docker-compose.yml build $build_args
            ;;
        *)
            echo -e "${RED}❌ Unknown platform: $platform${NC}"
            exit 1
            ;;
    esac
}

# Function to clean Docker resources
clean_docker() {
    cd "$PROJECT_ROOT"

    echo -e "${YELLOW}🧹 Cleaning Catzilla Docker resources...${NC}"

    # Stop and remove containers
    docker-compose -f docker/docker-compose.yml down --volumes --remove-orphans

    # Remove images
    echo -e "${YELLOW}Removing Catzilla images...${NC}"
    docker images | grep catzilla | awk '{print $3}' | xargs -r docker rmi -f

    # Remove build volumes
    echo -e "${YELLOW}Removing build volumes...${NC}"
    docker volume rm catzilla-linux-build catzilla-linux-logs catzilla-windows-build catzilla-windows-logs 2>/dev/null || true

    echo -e "${GREEN}✅ Cleanup completed${NC}"
}

# Function to prune Docker system
prune_docker() {
    echo -e "${RED}⚠️  WARNING: This will remove unused Docker resources system-wide${NC}"
    read -p "Are you sure? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        docker system prune -af --volumes
        echo -e "${GREEN}✅ Docker system pruned${NC}"
    else
        echo -e "${YELLOW}Operation cancelled${NC}"
    fi
}

# Function to show logs
show_logs() {
    local platform=$1
    cd "$PROJECT_ROOT"

    case "$platform" in
        "linux")
            docker-compose -f docker/docker-compose.yml logs catzilla-linux
            ;;
        "windows")
            docker-compose -f docker/docker-compose.yml logs catzilla-windows
            ;;
        *)
            docker-compose -f docker/docker-compose.yml logs
            ;;
    esac
}

# Function to show container stats
show_stats() {
    echo -e "${CYAN}📊 Container Resource Usage${NC}"
    docker stats --no-stream $(docker ps --filter "name=catzilla" --format "{{.Names}}" | tr '\n' ' ')
}

# Function to check health
check_health() {
    local platform=$1
    cd "$PROJECT_ROOT"

    case "$platform" in
        "linux")
            echo -e "${CYAN}🩺 Checking Linux container health...${NC}"
            docker-compose -f docker/docker-compose.yml run --rm catzilla-linux python3 -c "
import sys
print(f'Python: {sys.version}')
try:
    import catzilla
    print('✅ Catzilla import successful')
except Exception as e:
    print(f'❌ Catzilla import failed: {e}')
    sys.exit(1)
"
            ;;
        "windows")
            echo -e "${CYAN}🩺 Checking Windows container health...${NC}"
            docker-compose -f docker/docker-compose.yml run --rm catzilla-windows python -c "
import sys
print(f'Python: {sys.version}')
try:
    import catzilla
    print('✅ Catzilla import successful')
except Exception as e:
    print(f'❌ Catzilla import failed: {e}')
    sys.exit(1)
"
            ;;
        *)
            echo -e "${RED}❌ Please specify platform: linux or windows${NC}"
            exit 1
            ;;
    esac
}

# Function to run benchmarks
run_benchmarks() {
    local platform=$1
    cd "$PROJECT_ROOT"

    case "$platform" in
        "linux")
            echo -e "${CYAN}⚡ Running Linux benchmarks...${NC}"
            docker-compose -f docker/docker-compose.yml run --rm catzilla-linux bash -c "
                cd benchmarks
                python system_info.py
                ./run_all.sh
            "
            ;;
        "windows")
            echo -e "${CYAN}⚡ Running Windows benchmarks...${NC}"
            docker-compose -f docker/docker-compose.yml run --rm catzilla-windows cmd /c "
                cd benchmarks
                python system_info.py
                run_all.bat
            "
            ;;
        "all"|"")
            echo -e "${CYAN}⚡ Running benchmarks on all platforms...${NC}"
            run_benchmarks "linux"
            run_benchmarks "windows"
            ;;
        *)
            echo -e "${RED}❌ Unknown platform: $platform${NC}"
            exit 1
            ;;
    esac
}

# Main command handling
check_docker

case "$1" in
    test)
        run_tests "$2"
        ;;
    quick)
        quick_test
        ;;
    ci)
        simulate_ci
        ;;
    shell)
        open_shell "$2"
        ;;
    build)
        build_images "$2" false
        ;;
    rebuild)
        build_images "$2" true
        ;;
    clean)
        clean_docker
        ;;
    prune)
        prune_docker
        ;;
    logs)
        show_logs "$2"
        ;;
    ps)
        docker-compose -f "$PROJECT_ROOT/docker/docker-compose.yml" ps
        ;;
    images)
        docker images | grep -E "(REPOSITORY|catzilla)"
        ;;
    stats)
        show_stats
        ;;
    health)
        check_health "$2"
        ;;
    benchmark)
        run_benchmarks "$2"
        ;;
    ""|--help|-h)
        print_usage
        ;;
    *)
        echo -e "${RED}❌ Unknown command: $1${NC}"
        echo ""
        print_usage
        exit 1
        ;;
esac
