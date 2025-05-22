#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/.." && pwd )"

# Function to print usage
print_usage() {
    echo -e "${YELLOW}Usage: $0 [OPTIONS]${NC}"
    echo "Options:"
    echo "  -h, --help     Show this help message"
    echo "  -a, --all      Run all tests (default)"
    echo "  -p, --python   Run only Python tests"
    echo "  -c, --c        Run only C tests"
    echo "  -v, --verbose  Run tests with verbose output"
}

# Function to run Python tests
run_python_tests() {
    local verbose=$1
    echo -e "${YELLOW}Running Python tests...${NC}"

    # Set PYTHONPATH to include the python directory
    export PYTHONPATH="$PROJECT_ROOT/python:$PYTHONPATH"

    # Run pytest with or without verbose flag
    if [ "$verbose" = true ]; then
        python -m pytest "$PROJECT_ROOT/tests/python" -v
    else
        python -m pytest "$PROJECT_ROOT/tests/python"
    fi

    local result=$?
    if [ $result -eq 0 ]; then
        echo -e "${GREEN}Python tests passed!${NC}"
    else
        echo -e "${RED}Python tests failed!${NC}"
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

    # Run the C tests
    if [ -f "$PROJECT_ROOT/build/test_router" ]; then
        if [ "$verbose" = true ]; then
            "$PROJECT_ROOT/build/test_router" -v
        else
            "$PROJECT_ROOT/build/test_router"
        fi

        local result=$?
        if [ $result -eq 0 ]; then
            echo -e "${GREEN}C tests passed!${NC}"
        else
            echo -e "${RED}C tests failed!${NC}"
            return 1
        fi
    else
        echo -e "${RED}C test executable not found!${NC}"
        return 1
    fi
}

# Default values
run_all=true
run_python=false
run_c=false
verbose=false

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
            shift
            ;;
        -p|--python)
            run_all=false
            run_python=true
            run_c=false
            shift
            ;;
        -c|--c)
            run_all=false
            run_python=false
            run_c=true
            shift
            ;;
        -v|--verbose)
            verbose=true
            shift
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            print_usage
            exit 1
            ;;
    esac
done

# Track overall success
success=true

# Run tests based on flags
if [ "$run_all" = true ]; then
    run_python_tests "$verbose" || success=false
    run_c_tests "$verbose" || success=false
elif [ "$run_python" = true ]; then
    run_python_tests "$verbose" || success=false
elif [ "$run_c" = true ]; then
    run_c_tests "$verbose" || success=false
fi

# Exit with appropriate status
if [ "$success" = true ]; then
    echo -e "${GREEN}All requested tests passed!${NC}"
    exit 0
else
    echo -e "${RED}Some tests failed!${NC}"
    exit 1
fi
