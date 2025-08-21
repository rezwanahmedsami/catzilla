#!/bin/bash

# Enhanced Feature-Based Benchmark Runner for Catzilla
# Comprehensive benchmarking across all feature categories including real-world scenarios

set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RESULTS_DIR="$SCRIPT_DIR/results"
PYTHON_CMD="${PYTHON_CMD:-python3}"
WRK_CMD="${WRK_CMD:-wrk}"

# Test parameters
THREADS="${THREADS:-4}"
CONNECTIONS="${CONNECTIONS:-100}"
DURATION="${DURATION:-30}"
TIMEOUT="${TIMEOUT:-10}"

# Categories to test (expanded with new categories)
CATEGORIES=("basic" "middleware" "dependency_injection" "async_operations" "validation" "file_operations" "background_tasks" "real_world_scenarios")
FRAMEWORKS=("catzilla" "fastapi" "flask" "django")

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Utility functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_dependencies() {
    log_info "Checking dependencies..."

    if ! command -v "$PYTHON_CMD" &> /dev/null; then
        log_error "Python not found. Please install Python 3.8+"
        exit 1
    fi

    if ! command -v "$WRK_CMD" &> /dev/null; then
        log_error "wrk not found. Please install wrk load testing tool"
        exit 1
    fi

    # Check for required Python packages
    log_info "Checking Python dependencies..."
    if ! $PYTHON_CMD -c "import fastapi, flask, django" 2>/dev/null; then
        log_warning "Some Python frameworks may not be installed. Install with:"
        log_warning "pip install fastapi flask django uvicorn"
    fi

    log_success "Dependencies check passed"
}

create_results_dir() {
    mkdir -p "$RESULTS_DIR"
    log_info "Results will be saved to: $RESULTS_DIR"
}

setup_test_environment() {
    log_info "Setting up test environment..."

    # Create uploads directory for file operations tests
    mkdir -p "$SCRIPT_DIR/uploads"

    # Create test files for file operations
    if [ ! -f "$SCRIPT_DIR/uploads/sample_file.txt" ]; then
        echo "This is a sample test file for benchmarking." > "$SCRIPT_DIR/uploads/sample_file.txt"
    fi

    log_success "Test environment ready"
}

run_single_category() {
    local category="$1"

    log_info "Running $category benchmarks..."

    # Adjust test duration for resource-intensive categories
    local test_duration="$DURATION"
    case $category in
        file_operations|background_tasks|real_world_scenarios)
            test_duration=$((DURATION * 2))  # Double duration for complex tests
            ;;
    esac

    $PYTHON_CMD "$SCRIPT_DIR/run_enhanced_benchmarks.py" \
        --category "$category" \
        --threads "$THREADS" \
        --connections "$CONNECTIONS" \
        --duration "$test_duration" \
        --timeout "$TIMEOUT" \
        --output-dir "$RESULTS_DIR"

    if [ $? -eq 0 ]; then
        log_success "$category benchmarks completed"
    else
        log_error "$category benchmarks failed"
        return 1
    fi
}

run_core_categories() {
    local core_categories=("basic" "middleware" "dependency_injection" "async_operations")

    log_info "Running core feature benchmarks"

    local failed_categories=()

    for category in "${core_categories[@]}"; do
        echo
        log_info "Starting $category category..."

        if run_single_category "$category"; then
            log_success "$category completed successfully"
        else
            log_error "$category failed"
            failed_categories+=("$category")
        fi
    done

    echo
    if [ ${#failed_categories[@]} -eq 0 ]; then
        log_success "Core categories completed successfully!"
    else
        log_warning "Some core categories failed: ${failed_categories[*]}"
    fi
}

run_advanced_categories() {
    local advanced_categories=("validation" "file_operations" "background_tasks" "real_world_scenarios")

    log_info "Running advanced feature benchmarks"

    local failed_categories=()

    for category in "${advanced_categories[@]}"; do
        echo
        log_info "Starting $category category..."

        if run_single_category "$category"; then
            log_success "$category completed successfully"
        else
            log_error "$category failed"
            failed_categories+=("$category")
        fi
    done

    echo
    if [ ${#failed_categories[@]} -eq 0 ]; then
        log_success "Advanced categories completed successfully!"
    else
        log_warning "Some advanced categories failed: ${failed_categories[*]}"
    fi
}

run_all_categories() {
    log_info "Running comprehensive feature-based benchmarks"
    log_info "Categories: ${CATEGORIES[*]}"
    log_info "Frameworks: ${FRAMEWORKS[*]}"
    log_info "Parameters: threads=$THREADS, connections=$CONNECTIONS, duration=${DURATION}s"

    local failed_categories=()

    for category in "${CATEGORIES[@]}"; do
        echo
        log_info "Starting $category category..."

        if run_single_category "$category"; then
            log_success "$category completed successfully"
        else
            log_error "$category failed"
            failed_categories+=("$category")
        fi
    done

    echo
    if [ ${#failed_categories[@]} -eq 0 ]; then
        log_success "All categories completed successfully!"
    else
        log_warning "Some categories failed: ${failed_categories[*]}"
    fi
}

generate_report() {
    log_info "Generating comprehensive performance report..."

    $PYTHON_CMD "$SCRIPT_DIR/run_enhanced_benchmarks.py" \
        --frameworks "${FRAMEWORKS[@]}" \
        --threads "$THREADS" \
        --connections "$CONNECTIONS" \
        --duration "$DURATION" \
        --timeout "$TIMEOUT" \
        --output-dir "$RESULTS_DIR" \
        --report

    if [ $? -eq 0 ]; then
        log_success "Performance report generated"

        # Find and display the latest report
        latest_report=$(find "$RESULTS_DIR" -name "performance_report_*.md" -type f -printf '%T@ %p\n' 2>/dev/null | sort -n | tail -1 | cut -d' ' -f2-)
        if [ -n "$latest_report" ]; then
            log_info "Latest report: $latest_report"
        fi
    else
        log_error "Failed to generate report"
    fi
}

run_quick_test() {
    log_info "Running quick validation test..."

    # Quick test with reduced parameters
    local quick_categories=("basic" "validation")
    local quick_duration=10
    local quick_connections=20

    for category in "${quick_categories[@]}"; do
        log_info "Quick test: $category"

        $PYTHON_CMD "$SCRIPT_DIR/run_enhanced_benchmarks.py" \
            --category "$category" \
            --threads 2 \
            --connections "$quick_connections" \
            --duration "$quick_duration" \
            --timeout 5 \
            --output-dir "$RESULTS_DIR"
    done

    log_success "Quick test completed"
}

show_usage() {
    echo "Enhanced Feature-Based Benchmark Runner for Catzilla"
    echo "Usage: $0 [OPTIONS] [COMMAND]"
    echo
    echo "Commands:"
    echo "  all                    Run all category benchmarks (default)"
    echo "  core                   Run core categories (basic, middleware, DI, async)"
    echo "  advanced               Run advanced categories (validation, files, tasks, real-world)"
    echo "  basic                  Run basic HTTP benchmarks"
    echo "  middleware             Run middleware benchmarks"
    echo "  dependency_injection   Run DI benchmarks"
    echo "  async_operations       Run async operation benchmarks"
    echo "  validation             Run validation engine benchmarks"
    echo "  file_operations        Run file upload/download benchmarks"
    echo "  background_tasks       Run background task processing benchmarks"
    echo "  real_world_scenarios   Run real-world application benchmarks"
    echo "  quick                  Run quick validation test"
    echo "  report                 Generate performance report only"
    echo
    echo "Options:"
    echo "  -h, --help             Show this help message"
    echo "  -t, --threads N        Number of threads (default: 4)"
    echo "  -c, --connections N    Number of connections (default: 100)"
    echo "  -d, --duration N       Test duration in seconds (default: 30)"
    echo "  -o, --output DIR       Output directory (default: results)"
    echo "  -f, --frameworks LIST  Frameworks to test (default: all)"
    echo
    echo "Environment variables:"
    echo "  PYTHON_CMD             Python command (default: python3)"
    echo "  WRK_CMD                wrk command (default: wrk)"
    echo "  THREADS                Number of threads"
    echo "  CONNECTIONS            Number of connections"
    echo "  DURATION               Test duration"
    echo
    echo "Examples:"
    echo "  $0                                    # Run all benchmarks"
    echo "  $0 core                               # Run core feature benchmarks"
    echo "  $0 advanced                           # Run advanced feature benchmarks"
    echo "  $0 real_world_scenarios               # Run real-world scenarios only"
    echo "  $0 -t 8 -c 200 -d 60 all             # Custom parameters"
    echo "  $0 -f catzilla fastapi validation    # Test specific frameworks and category"
    echo "  $0 quick                              # Quick validation test"
    echo "  $0 report                             # Generate report only"
}

main() {
    local command="all"

    # Parse command line arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            -h|--help)
                show_usage
                exit 0
                ;;
            -t|--threads)
                THREADS="$2"
                shift 2
                ;;
            -c|--connections)
                CONNECTIONS="$2"
                shift 2
                ;;
            -d|--duration)
                DURATION="$2"
                shift 2
                ;;
            -o|--output)
                RESULTS_DIR="$2"
                shift 2
                ;;
            -f|--frameworks)
                shift
                FRAMEWORKS=()
                while [[ $# -gt 0 && ! "$1" =~ ^- ]]; do
                    FRAMEWORKS+=("$1")
                    shift
                done
                ;;
            all|core|advanced|basic|middleware|dependency_injection|async_operations|validation|file_operations|background_tasks|real_world_scenarios|quick|report)
                command="$1"
                shift
                ;;
            *)
                log_error "Unknown option: $1"
                show_usage
                exit 1
                ;;
        esac
    done

    # Validate frameworks
    if [ ${#FRAMEWORKS[@]} -eq 0 ]; then
        FRAMEWORKS=("catzilla" "fastapi" "flask" "django")
    fi

    # Create results directory
    create_results_dir

    # Check dependencies
    check_dependencies

    # Setup test environment
    setup_test_environment

    # Execute command
    case $command in
        all)
            run_all_categories
            generate_report
            ;;
        core)
            run_core_categories
            ;;
        advanced)
            run_advanced_categories
            ;;
        basic|middleware|dependency_injection|async_operations|validation|file_operations|background_tasks|real_world_scenarios)
            run_single_category "$command"
            ;;
        quick)
            run_quick_test
            ;;
        report)
            generate_report
            ;;
        *)
            log_error "Unknown command: $command"
            show_usage
            exit 1
            ;;
    esac

    log_success "Benchmark run completed!"
    log_info "Results are available in: $RESULTS_DIR"
}

# Run main function
main "$@"
