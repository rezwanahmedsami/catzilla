#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/.." && pwd )"

# Note: Catzilla statically links jemalloc at build time
# No need for system jemalloc preloading

# Debug flags
DEBUG_C=0
DEBUG_PY=0
EXAMPLE_PATH=""

# Function to print usage
print_usage() {
    echo -e "${YELLOW}Usage: $0 [debug_options] <example_path>${NC}"
    echo ""
    echo -e "${BLUE}Debug Options:${NC}"
    echo -e "  ${CYAN}--debug${NC}     Enable both C and Python debug logging"
    echo -e "  ${CYAN}--debug_c${NC}   Enable C debug logging only"
    echo -e "  ${CYAN}--debug_py${NC}  Enable Python debug logging only"
    echo ""
    echo -e "${BLUE}Examples:${NC}"
    echo "  $0 examples/hello_world/main.py"
    echo "  $0 --debug examples/hello_world/main.py"
    echo "  $0 --debug_c examples/hello_world/main.py"
    echo "  $0 --debug_py examples/hello_world/main.py"
    echo ""
    echo -e "${BLUE}Debug Environment Variables:${NC}"
    echo -e "  ${CYAN}CATZILLA_C_DEBUG=1${NC}  - Shows C-level debugging (server, router, HTTP parsing)"
    echo -e "  ${CYAN}CATZILLA_DEBUG=1${NC}    - Shows Python-level debugging (types, app, request processing)"
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --debug)
            DEBUG_C=1
            DEBUG_PY=1
            shift
            ;;
        --debug_c)
            DEBUG_C=1
            shift
            ;;
        --debug_py)
            DEBUG_PY=1
            shift
            ;;
        -h|--help)
            print_usage
            exit 0
            ;;
        -*)
            echo -e "${RED}Error: Unknown option $1${NC}"
            print_usage
            exit 1
            ;;
        *)
            if [ -z "$EXAMPLE_PATH" ]; then
                EXAMPLE_PATH="$1"
            else
                echo -e "${RED}Error: Multiple example paths specified${NC}"
                print_usage
                exit 1
            fi
            shift
            ;;
    esac
done

# Check if example path is provided
if [ -z "$EXAMPLE_PATH" ]; then
    echo -e "${RED}Error: No example path specified${NC}"
    print_usage
    exit 1
fi

# Check if example file exists
if [ ! -f "$PROJECT_ROOT/$EXAMPLE_PATH" ]; then
    echo -e "${RED}Error: Example file not found: $PROJECT_ROOT/$EXAMPLE_PATH${NC}"
    exit 1
fi

# Set PYTHONPATH to include the python directory
export PYTHONPATH="$PROJECT_ROOT/python:$PYTHONPATH"

# Set debug environment variables
unset CATZILLA_C_DEBUG
unset CATZILLA_DEBUG

if [ $DEBUG_C -eq 1 ]; then
    export CATZILLA_C_DEBUG=1
fi

if [ $DEBUG_PY -eq 1 ]; then
    export CATZILLA_DEBUG=1
fi

# Print debug status
echo -e "${GREEN}🚀 Running Catzilla Example${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${CYAN}Example:${NC} $EXAMPLE_PATH"

if [ $DEBUG_C -eq 1 ] && [ $DEBUG_PY -eq 1 ]; then
    echo -e "${CYAN}Debug Mode:${NC} ${YELLOW}Full Debug${NC} (C + Python logging enabled)"
elif [ $DEBUG_C -eq 1 ]; then
    echo -e "${CYAN}Debug Mode:${NC} ${YELLOW}C Debug${NC} (C logging enabled)"
elif [ $DEBUG_PY -eq 1 ]; then
    echo -e "${CYAN}Debug Mode:${NC} ${YELLOW}Python Debug${NC} (Python logging enabled)"
else
    echo -e "${CYAN}Debug Mode:${NC} ${GREEN}Clean Output${NC} (End user mode)"
fi

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# Run the example
python "$PROJECT_ROOT/$EXAMPLE_PATH"
