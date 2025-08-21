#!/bin/bash

# Catzilla Test Runner Script
# Uses distributed testing with pytest-xdist for process isolation and parallel execution
# This prevents cumulative memory effects and segfaults in C extension tests

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/.." && pwd )"

# Note: Catzilla statically links jemalloc at build time
# No need for system jemalloc preloading

# Function to print usage
print_usage() {
    echo -e "${YELLOW}🧪 Catzilla Test Runner${NC}"
    echo -e "${YELLOW}=====================${NC}"
    echo ""
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo -e "${CYAN}Standard Testing:${NC}"
    echo "  -h, --help            Show this help message"
    echo "  -a, --all             Run all tests (default)"
    echo "  -p, --python          Run only Python tests"
    echo "  -c, --c               Run only C tests"
    echo "  -e, --e2e             Run only E2E tests"
    echo "  -v, --verbose         Run tests with verbose output"
    echo ""
    echo -e "${CYAN}🐳 Docker Cross-Platform Testing:${NC}"
    echo "  --docker [PLATFORM]   Run tests in Docker container"
    echo "                        PLATFORM: linux, windows, windows-sim, all (default: all)"
    echo ""
    echo -e "${YELLOW}Platform Compatibility:${NC}"
    echo "  • linux: ✅ Supported on macOS, Linux, Windows"
    echo "  • windows: ⚠️  Requires Docker Desktop with Windows containers"
    echo "  • windows-sim: ✅ Windows simulation via Wine (Linux container)"
    echo "  • Use 'linux' or 'windows-sim' for reliable cross-platform testing"
    echo ""
    echo -e "${CYAN}Docker Examples:${NC}"
    echo "  $0 --docker           # Test on all platforms"
    echo "  $0 --docker linux     # Test on Ubuntu Linux"
    echo "  $0 --docker windows   # Test on Windows Server"
    echo ""
    echo -e "${CYAN}Quick Commands:${NC}"
    echo "  ./scripts/test_docker_quick.sh      # Quick Linux test"
    echo "  ./scripts/test_docker_full.sh       # Full cross-platform test"
    echo "  ./scripts/simulate_ci.sh --fast     # Simulate CI pipeline"
    echo ""
    echo -e "${CYAN}Docker Management:${NC}"
    echo "  ./scripts/docker_manager.sh shell linux    # Interactive shell"
    echo "  ./scripts/docker_manager.sh clean          # Clean containers"
    echo "  ./scripts/setup_docker_testing.sh          # Setup Docker testing"
    echo ""
    echo -e "${GREEN}💡 Pro Tips:${NC}"
    echo "  - Use '--docker linux' for fastest feedback"
    echo "  - Run '--docker all' before pushing to GitHub"
    echo "  - Use Docker for exact CI environment replication"
    echo "  - Docker saves CI costs by testing locally first"
}

# Function to check Docker platform support
check_docker_platform_support() {
    local platform=$1

    # Check Docker daemon OS type
    local docker_os=$(docker system info --format '{{.OSType}}' 2>/dev/null || echo "unknown")

    if [ "$platform" = "windows" ] && [ "$docker_os" != "windows" ]; then
        return 1
    fi

    return 0
}

# Function to run Docker tests
run_docker_tests() {
    local platform=$1

    echo -e "${YELLOW}🐳 Running tests in Docker containers...${NC}"

    # Ensure we're in the project root
    cd "$PROJECT_ROOT" || exit 1

    # Check if Docker is available
    if ! command -v docker &> /dev/null; then
        echo -e "${RED}❌ Docker is not installed or not in PATH${NC}"
        echo "Please install Docker to use this feature."
        return 1
    fi

    # Check if Docker Compose is available
    if ! command -v docker-compose &> /dev/null; then
        echo -e "${RED}❌ Docker Compose is not installed or not in PATH${NC}"
        echo "Please install Docker Compose to use this feature."
        return 1
    fi

    # Check Docker daemon status
    if ! docker info &> /dev/null; then
        echo -e "${RED}❌ Docker daemon is not running${NC}"
        echo "Please start Docker and try again."
        return 1
    fi

    # Get current host OS for better error messages
    local host_os=$(uname -s)
    local docker_os=$(docker system info --format '{{.OSType}}' 2>/dev/null || echo "unknown")

    case "$platform" in
        "linux")
            echo -e "${GREEN}🐧 Running tests on Linux (Ubuntu 22.04)...${NC}"
            docker-compose -f docker/docker-compose.yml build catzilla-linux
            docker-compose -f docker/docker-compose.yml run --rm catzilla-linux
            ;;
        "windows")
            if [ "$docker_os" != "windows" ]; then
                echo -e "${RED}❌ Windows containers are not supported on this Docker installation${NC}"
                echo -e "${YELLOW}Current Docker OS: $docker_os${NC}"
                echo -e "${YELLOW}Host OS: $host_os${NC}"
                echo ""
                echo -e "${YELLOW}To test Windows containers, you need:${NC}"
                if [ "$host_os" = "Darwin" ]; then
                    echo "  • Docker Desktop for Mac with Windows containers enabled"
                    echo "  • Or use a Windows machine/VM"
                elif [ "$host_os" = "Linux" ]; then
                    echo "  • A Windows machine or Windows VM"
                    echo "  • Docker Desktop for Windows"
                fi
                echo ""
                echo -e "${GREEN}💡 Alternatives:${NC}"
                echo "   ./scripts/run_tests.sh --docker linux      # Linux containers"
                echo "   ./scripts/run_tests.sh --docker windows-sim # Wine simulation"
                return 1
            fi
            echo -e "${GREEN}🪟 Running tests on Windows (Server 2022)...${NC}"
            docker-compose -f docker/docker-compose.yml build catzilla-windows
            docker-compose -f docker/docker-compose.yml run --rm catzilla-windows
            ;;
        "windows-sim")
            echo -e "${GREEN}🍷 Running tests on Windows Simulation (Wine)...${NC}"
            docker-compose -f docker/docker-compose.multiplatform.yml build catzilla-windows-sim
            docker-compose -f docker/docker-compose.multiplatform.yml run --rm catzilla-windows-sim
            ;;
        "all")
            echo -e "${GREEN}🌍 Running tests on all platforms...${NC}"
            echo ""
            echo -e "${GREEN}🐧 Testing Linux...${NC}"
            docker-compose -f docker/docker-compose.yml build catzilla-linux
            docker-compose -f docker/docker-compose.yml run --rm catzilla-linux

            echo ""
            if [ "$docker_os" = "windows" ]; then
                echo -e "${GREEN}🪟 Testing Windows...${NC}"
                docker-compose -f docker/docker-compose.yml build catzilla-windows
                docker-compose -f docker/docker-compose.yml run --rm catzilla-windows
            else
                echo -e "${YELLOW}⚠️  Skipping native Windows tests - using Wine simulation instead${NC}"
                echo -e "${GREEN}🍷 Testing Windows Simulation...${NC}"
                docker-compose -f docker/docker-compose.multiplatform.yml build catzilla-windows-sim
                docker-compose -f docker/docker-compose.multiplatform.yml run --rm catzilla-windows-sim
            fi
            ;;
        *)
            echo -e "${RED}❌ Unknown platform: $platform${NC}"
            echo "Supported platforms: linux, windows, windows-sim, all"
            return 1
            ;;
    esac
}
run_python_tests() {
    local verbose=$1
    echo -e "${YELLOW}Running Python tests with distributed execution...${NC}"

    # Set PYTHONPATH to include the python directory
    export PYTHONPATH="$PROJECT_ROOT/python:$PYTHONPATH"

    # Change to project root directory
    cd "$PROJECT_ROOT" || exit 1

    # Set up problem detection
    echo -e "${YELLOW}Setting up segfault detection...${NC}"
    export PYTHONFAULTHANDLER=1  # Enable Python fault handler

    # Detect the correct Python command
    PYTHON_CMD="python"
    if ! command -v python &> /dev/null; then
        if command -v python3 &> /dev/null; then
            PYTHON_CMD="python3"
        else
            echo -e "${RED}Error: Neither 'python' nor 'python3' command found!${NC}"
            return 1
        fi
    fi

    # Run pytest with distributed execution for process isolation and parallel testing
    echo -e "${YELLOW}Starting test execution...${NC}"
    if [ "$verbose" = true ]; then
        $PYTHON_CMD -m pytest tests/python/ -n auto --dist worksteal --tb=short -v
    else
        $PYTHON_CMD -m pytest tests/python/ -n auto --dist worksteal --tb=short
    fi

    local result=$?
    if [ $result -eq 0 ]; then
        echo -e "${GREEN}Python tests passed!${NC}"
    else
        echo -e "${RED}Python tests failed!${NC}"
        # Check for segfaults in test output
        if grep -q "Segmentation fault" .pytest_testlog 2>/dev/null; then
            echo -e "${RED}Segmentation faults detected in tests!${NC}"
            echo -e "${YELLOW}This may indicate memory management issues or test instability.${NC}"
        fi
        return 1
    fi
}

# Function to run E2E tests
run_e2e_tests() {
    local verbose=$1
    echo -e "${YELLOW}Running E2E tests...${NC}"

    # Set PYTHONPATH to include the python directory
    export PYTHONPATH="$PROJECT_ROOT/python:$PYTHONPATH"

    # Change to project root directory
    cd "$PROJECT_ROOT" || exit 1

    # Detect the correct Python command
    PYTHON_CMD="python"
    if ! command -v python &> /dev/null; then
        if command -v python3 &> /dev/null; then
            PYTHON_CMD="python3"
        else
            echo -e "${RED}Error: Neither 'python' nor 'python3' command found!${NC}"
            return 1
        fi
    fi

    # Run E2E tests with the specific pytest configuration
    echo -e "${YELLOW}Starting E2E test execution...${NC}"
    if [ "$verbose" = true ]; then
        $PYTHON_CMD -m pytest tests/e2e/ -c tests/e2e/pytest.ini --tb=short -v
    else
        $PYTHON_CMD -m pytest tests/e2e/ -c tests/e2e/pytest.ini --tb=short
    fi

    local result=$?
    if [ $result -eq 0 ]; then
        echo -e "${GREEN}E2E tests passed!${NC}"
    else
        echo -e "${RED}E2E tests failed!${NC}"
        return 1
    fi
}

# Function to run C tests
run_c_tests() {
    local verbose=$1
    echo -e "${YELLOW}Running C tests...${NC}"

    # Ensure build directory exists
    mkdir -p "$PROJECT_ROOT/build"

    # Build the project if needed
    cd "$PROJECT_ROOT" || exit 1
    cmake -S . -B build
    cmake --build build

    # List of C test executables to run
    local test_executables=("test_router" "test_advanced_router" "test_server_integration" "test_validation_engine" "test_dependency_injection" "test_middleware_minimal" "test_streaming")
    local all_passed=true

    # Run each C test executable
    for test_exe in "${test_executables[@]}"; do
        if [ -f "$PROJECT_ROOT/build/$test_exe" ]; then
            echo -e "${YELLOW}Running $test_exe...${NC}"

            if [ "$verbose" = true ]; then
                "$PROJECT_ROOT/build/$test_exe" -v
            else
                "$PROJECT_ROOT/build/$test_exe"
            fi

            local result=$?
            if [ $result -eq 0 ]; then
                echo -e "${GREEN}$test_exe passed!${NC}"
            else
                echo -e "${RED}$test_exe failed!${NC}"
                all_passed=false
            fi
        else
            echo -e "${RED}C test executable $test_exe not found!${NC}"
            all_passed=false
        fi
    done

    if [ "$all_passed" = true ]; then
        echo -e "${GREEN}All C tests passed!${NC}"
    else
        echo -e "${RED}Some C tests failed!${NC}"
        return 1
    fi
}

# Default values
run_all=true
run_python=false
run_c=false
run_e2e=false
verbose=false
docker_mode=false
docker_platform="all"

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            print_usage
            exit 0
            ;;
        -a|--all)
            run_all=true
            run_python=false
            run_c=false
            run_e2e=false
            shift
            ;;
        -p|--python)
            run_all=false
            run_python=true
            run_c=false
            run_e2e=false
            shift
            ;;
        -c|--c)
            run_all=false
            run_python=false
            run_c=true
            run_e2e=false
            shift
            ;;
        -e|--e2e)
            run_all=false
            run_python=false
            run_c=false
            run_e2e=true
            shift
            ;;
        -v|--verbose)
            verbose=true
            shift
            ;;
        --docker)
            docker_mode=true
            if [[ $# -gt 1 ]] && [[ $2 != -* ]]; then
                docker_platform="$2"
                shift 2
            else
                docker_platform="all"
                shift
            fi
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            print_usage
            exit 1
            ;;
    esac
done

# Handle Docker mode first
if [ "$docker_mode" = true ]; then
    run_docker_tests "$docker_platform"
    exit $?
fi

# Track overall success
success=true

# Run tests based on flags
if [ "$run_all" = true ]; then
    run_python_tests "$verbose" || success=false
    run_c_tests "$verbose" || success=false
    run_e2e_tests "$verbose" || success=false
elif [ "$run_python" = true ]; then
    run_python_tests "$verbose" || success=false
elif [ "$run_c" = true ]; then
    run_c_tests "$verbose" || success=false
elif [ "$run_e2e" = true ]; then
    run_e2e_tests "$verbose" || success=false
fi

# Exit with appropriate status
if [ "$success" = true ]; then
    echo -e "${GREEN}All requested tests passed!${NC}"
    exit 0
else
    echo -e "${RED}Some tests failed!${NC}"
    exit 1
fi
