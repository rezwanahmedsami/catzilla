#!/usr/bin/env zsh
# Enhanced Catzilla Benchmark Runner
#
# This script maintains compatibility with the old benchmarking system
# while supporting the new feature-based structure.

set -e  # Exit on any error

# Configuration
BENCHMARK_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$BENCHMARK_DIR/.." && pwd)"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_header() {
    echo -e "${PURPLE}$1${NC}"
}

# Check dependencies
check_dependencies() {
    print_status "Checking dependencies..."

    if ! command -v python3 &> /dev/null; then
        print_error "python3 is required but not installed"
        exit 1
    fi

    if ! command -v wrk &> /dev/null; then
        print_error "wrk is required but not installed"
        print_status "Install with: brew install wrk (macOS) or apt-get install wrk (Ubuntu)"
        exit 1
    fi

    print_success "All dependencies found"
}

# Collect system information
collect_system_info() {
    print_status "Collecting system information..."

    if [ -f "$BENCHMARK_DIR/tools/system_info.py" ]; then
        cd "$BENCHMARK_DIR"
        python3 tools/system_info.py --output results/system_info.json --format json
        print_success "System information collected"
    else
        print_warning "System info script not found, skipping..."
    fi
}

# Show usage information
usage() {
    echo "Enhanced Catzilla Benchmark Runner"
    echo ""
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --basic             Run basic HTTP benchmarks (default)"
    echo "  --middleware        Run middleware benchmarks"
    echo "  --di                Run dependency injection benchmarks"
    echo "  --async             Run async operations benchmarks"
    echo "  --all               Run all available benchmarks"
    echo "  --frameworks LIST   Comma-separated list of frameworks (catzilla,fastapi,flask,django)"
    echo "  --duration TIME     Test duration (default: 10s)"
    echo "  --connections NUM   Number of connections (default: 100)"
    echo "  --threads NUM       Number of threads (default: 4)"
    echo "  --help             Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0                                    # Run basic benchmarks"
    echo "  $0 --all                             # Run all benchmarks"
    echo "  $0 --middleware --frameworks catzilla,fastapi"
    echo "  $0 --basic --duration 30s --connections 200"
}

# Parse command line arguments
CATEGORIES=()
FRAMEWORKS=""
DURATION="10s"
CONNECTIONS="100"
THREADS="4"

while [[ $# -gt 0 ]]; do
    case $1 in
        --basic)
            CATEGORIES+=("basic")
            shift
            ;;
        --middleware)
            CATEGORIES+=("middleware")
            shift
            ;;
        --di)
            CATEGORIES+=("dependency_injection")
            shift
            ;;
        --async)
            CATEGORIES+=("async_operations")
            shift
            ;;
        --all)
            CATEGORIES=("basic" "middleware" "dependency_injection" "async_operations")
            shift
            ;;
        --frameworks)
            FRAMEWORKS="$2"
            shift 2
            ;;
        --duration)
            DURATION="$2"
            shift 2
            ;;
        --connections)
            CONNECTIONS="$2"
            shift 2
            ;;
        --threads)
            THREADS="$2"
            shift 2
            ;;
        --help)
            usage
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            usage
            exit 1
            ;;
    esac
done

# Default to basic if no categories specified
if [ ${#CATEGORIES[@]} -eq 0 ]; then
    CATEGORIES=("basic")
fi

# Main execution
main() {
    print_header "🚀 Enhanced Catzilla Benchmark Runner"
    echo "=" * 60

    # Check dependencies
    check_dependencies

    # Collect system info
    collect_system_info

    # Prepare arguments for Python runner
    PYTHON_ARGS="--categories ${CATEGORIES[*]} --duration $DURATION --connections $CONNECTIONS --threads $THREADS"

    if [ -n "$FRAMEWORKS" ]; then
        # Convert comma-separated list to space-separated for Python
        FRAMEWORKS_SPACE=$(echo "$FRAMEWORKS" | tr ',' ' ')
        PYTHON_ARGS="$PYTHON_ARGS --frameworks $FRAMEWORKS_SPACE"
    fi

    print_status "Running benchmarks with configuration:"
    print_status "  Categories: ${CATEGORIES[*]}"
    print_status "  Duration: $DURATION"
    print_status "  Connections: $CONNECTIONS"
    print_status "  Threads: $THREADS"
    [ -n "$FRAMEWORKS" ] && print_status "  Frameworks: $FRAMEWORKS"

    echo ""

    # Run the Python benchmark runner
    cd "$BENCHMARK_DIR"
    python3 run_feature_benchmarks.py $PYTHON_ARGS

    # Check if visualization script exists and run it
    if [ -f "$BENCHMARK_DIR/tools/visualize_results.py" ]; then
        print_status "Generating visualization..."
        python3 tools/visualize_results.py --input results/benchmark_summary.json --output results/
        print_success "Visualization generated in results/ directory"
    else
        print_warning "Visualization script not found, skipping..."
    fi

    print_success "Benchmark run completed!"
    print_status "Results are available in: $BENCHMARK_DIR/results/"
}

# Handle interrupts
trap 'print_warning "Benchmark interrupted by user"; exit 1' INT TERM

# Run main function
main "$@"
