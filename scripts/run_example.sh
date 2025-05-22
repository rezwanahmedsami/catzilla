#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/.." && pwd )"

# Function to print usage
print_usage() {
    echo -e "${YELLOW}Usage: $0 <example_path>${NC}"
    echo "Example:"
    echo "  $0 examples/hello_world/main.py"
}

if [ $# -eq 0 ]; then
    print_usage
    exit 1
fi

# Set PYTHONPATH to include the python directory
export PYTHONPATH="$PROJECT_ROOT/python:$PYTHONPATH"

echo -e "${GREEN}Running example: $1${NC}"
python "$PROJECT_ROOT/$1" 