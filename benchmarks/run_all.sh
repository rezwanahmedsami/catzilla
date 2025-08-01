#!/usr/bin/env zsh
# Enhanced Catzilla Benchmark Runner
#
# This script runs comprehensive performance benchmarks comparing Catzilla
# against other popular Python web frameworks (FastAPI, Flask, Django).
# It supports both direct wrk execution and Python-based testing.

set -e  # Exit on any error

# Configuration
BENCHMARK_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$BENCHMARK_DIR/.." && pwd)"
RESULTS_DIR="$BENCHMARK_DIR/results"
SERVERS_DIR="$BENCHMARK_DIR/servers"
VENV_PATH="$PROJECT_ROOT/venv"

# Create results directory
mkdir -p "$RESULTS_DIR"

# Benchmark settings
DURATION="10s"          # Duration of each test
CONNECTIONS="100"       # Number of concurrent connections
THREADS="4"             # Number of threads to use
WARMUP_TIME="3s"        # Warmup duration

# Server configurations for basic benchmarks
BASIC_SERVERS=(
    "catzilla:8000:python3 $SERVERS_DIR/basic/catzilla_server.py --port 8000"
    "fastapi:8001:python3 $SERVERS_DIR/basic/fastapi_server.py --port 8001"
    "flask:8002:python3 $SERVERS_DIR/basic/flask_server.py --port 8002"
    "django:8003:python3 $SERVERS_DIR/basic/django_server.py --port 8003"
)

# Test endpoints for basic benchmarks
BASIC_ENDPOINTS=(
    "/:hello_world"
    "/json:json_response"
    "/user/42:path_params"
    "/users?limit=20&offset=10:query_params"
    "/user/123/profile:complex_json"
)

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

# Function to check if a port is in use
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        return 0  # Port is in use
    else
        return 1  # Port is free
    fi
}

# Function to wait for server to start
wait_for_server() {
    local host=$1
    local port=$2
    local timeout=${3:-30}

    print_status "Waiting for server at $host:$port to start..."

    for i in $(seq 1 $timeout); do
        if curl -s "http://$host:$port/health" >/dev/null 2>&1; then
            print_success "Server at $host:$port is ready!"
            return 0
        fi
        sleep 1
    done

    print_error "Server at $host:$port failed to start within $timeout seconds"
    return 1
}

# Function to stop server by PID
stop_server() {
    local pid=$1
    local name=$2

    if [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then
        print_status "Stopping $name server (PID: $pid)..."
        kill -TERM "$pid" 2>/dev/null || true

        # Wait for graceful shutdown
        for i in {1..5}; do
            if ! kill -0 "$pid" 2>/dev/null; then
                break
            fi
            sleep 1
        done

        # Force kill if necessary
        if kill -0 "$pid" 2>/dev/null; then
            print_warning "Force killing $name server..."
            kill -KILL "$pid" 2>/dev/null || true
        fi
    fi
}

# Function to start a server
start_server() {
    local framework=$1
    local port=$2
    local command=$3

    print_status "Starting $framework server on port $port..."

    # Check if port is already in use
    if check_port "$port"; then
        print_warning "Port $port is already in use. Attempting to stop existing process..."
        local existing_pid=$(lsof -Pi :$port -sTCP:LISTEN -t 2>/dev/null | head -1)
        if [ -n "$existing_pid" ]; then
            kill -TERM "$existing_pid" 2>/dev/null || true
            sleep 2
        fi
    fi

    # Start the server in background
    cd "$PROJECT_ROOT"  # Run from project root

    # Activate virtual environment if it exists
    if [ -f "$VENV_PATH/bin/activate" ]; then
        source "$VENV_PATH/bin/activate"
    fi

    # Start server
    eval "$command" > "$RESULTS_DIR/${framework}_server.log" 2>&1 &
    local server_pid=$!

    # Wait for server to start
    if wait_for_server "127.0.0.1" "$port" 30; then
        echo "$server_pid" > "$RESULTS_DIR/${framework}_server.pid"
        print_success "$framework server started (PID: $server_pid)"
        return 0
    else
        stop_server "$server_pid" "$framework"
        print_error "Failed to start $framework server"
        return 1
    fi
}

# Function to run benchmark for a specific endpoint
run_benchmark() {
    local framework=$1
    local endpoint=$2
    local endpoint_name=$3
    local host="127.0.0.1"
    local port=""
    local method=${4:-"GET"}
    local post_data=${5:-""}

    # Extract port from server configuration
    for server_config in "${BASIC_SERVERS[@]}"; do
        local server_name=${server_config%%:*}
        if [ "$server_name" = "$framework" ]; then
            port=$(echo "$server_config" | cut -d':' -f2)
            break
        fi
    done

    if [ -z "$port" ]; then
        print_error "Port not found for framework: $framework"
        return 1
    fi

    local url="http://$host:$port$endpoint"

    print_status "Benchmarking $framework - $endpoint_name ($endpoint)"

    # Warmup run
    print_status "Warming up $framework server..."
    if [ "$method" = "POST" ] && [ -n "$post_data" ]; then
        # Create temporary Lua script for POST requests
        local lua_script="$RESULTS_DIR/temp_post.lua"
        cat > "$lua_script" << EOF
wrk.method = "POST"
wrk.body = '$post_data'
wrk.headers["Content-Type"] = "application/json"
EOF
        wrk -t1 -c10 -d"$WARMUP_TIME" -s "$lua_script" "$url" >/dev/null 2>&1 || true
        rm -f "$lua_script"
    else
        wrk -t1 -c10 -d"$WARMUP_TIME" "$url" >/dev/null 2>&1 || true
    fi

    # Main benchmark
    local result_file="$RESULTS_DIR/${framework}_${endpoint_name}.txt"
    local json_file="$RESULTS_DIR/${framework}_${endpoint_name}.json"

    print_status "Running main benchmark..."

    # Run wrk and capture output
    local wrk_success=false
    if [ "$method" = "POST" ] && [ -n "$post_data" ]; then
        # Create temporary Lua script for POST requests
        local lua_script="$RESULTS_DIR/temp_${framework}_${endpoint_name}.lua"
        cat > "$lua_script" << EOF
wrk.method = "POST"
wrk.body = '$post_data'
wrk.headers["Content-Type"] = "application/json"
EOF

        if wrk -t"$THREADS" -c"$CONNECTIONS" -d"$DURATION" --latency -s "$lua_script" "$url" > "$result_file" 2>&1; then
            wrk_success=true
        fi
        rm -f "$lua_script"
    else
        # GET request
        if wrk -t"$THREADS" -c"$CONNECTIONS" -d"$DURATION" --latency "$url" > "$result_file" 2>&1; then
            wrk_success=true
        fi
    fi

    if [ "$wrk_success" = true ]; then
        print_success "Benchmark completed for $framework - $endpoint_name"

        # Extract key metrics and save as JSON
        local requests_per_sec=$(grep "Requests/sec:" "$result_file" | awk '{print $2}' | head -1)
        local avg_latency=$(grep "Latency" "$result_file" | awk '{print $2}' | head -1)
        local p99_latency=$(grep "99%" "$result_file" | awk '{print $2}' | head -1)
        local transfer_per_sec=$(grep "Transfer/sec:" "$result_file" | awk '{print $2}' | head -1)

        # Create JSON summary
        cat > "$json_file" << EOF
{
  "framework": "$framework",
  "endpoint": "$endpoint",
  "endpoint_name": "$endpoint_name",
  "method": "$method",
  "duration": "$DURATION",
  "connections": $CONNECTIONS,
  "threads": $THREADS,
  "requests_per_sec": "${requests_per_sec:-0}",
  "avg_latency": "$avg_latency",
  "p99_latency": "$p99_latency",
  "transfer_per_sec": "$transfer_per_sec",
  "timestamp": "$(date -Iseconds)"
}
EOF

        print_success "Results saved: $result_file, $json_file"
        echo "  Requests/sec: $requests_per_sec"
        echo "  Avg Latency: $avg_latency"
        echo "  99% Latency: $p99_latency"

    else
        print_error "Benchmark failed for $framework - $endpoint_name"
        return 1
    fi
}

# Function to run benchmarks for a single framework
benchmark_framework() {
    local framework=$1

    print_status "Starting benchmark for $framework"
    echo "=================================================="

    # Extract server configuration
    local server_config=""
    local port=""
    local command=""

    for config in "${BASIC_SERVERS[@]}"; do
        local server_name=${config%%:*}
        if [ "$server_name" = "$framework" ]; then
            server_config="$config"
            port=$(echo "$config" | cut -d':' -f2)
            command=$(echo "$config" | cut -d':' -f3-)
            break
        fi
    done

    if [ -z "$server_config" ]; then
        print_error "Server configuration not found for $framework"
        return 1
    fi

    # Start the server
    if ! start_server "$framework" "$port" "$command"; then
        print_error "Skipping $framework due to server start failure"
        return 1
    fi

    # Get server PID for cleanup
    local server_pid=$(cat "$RESULTS_DIR/${framework}_server.pid" 2>/dev/null || echo "")

    # Run benchmarks for each endpoint
    local all_passed=true
    for endpoint_config in "${BASIC_ENDPOINTS[@]}"; do
        local endpoint=${endpoint_config%%:*}
        local endpoint_name=${endpoint_config#*:}

        if ! run_benchmark "$framework" "$endpoint" "$endpoint_name"; then
            all_passed=false
        fi

        sleep 2  # Brief pause between endpoints
    done

    # Stop the server
    if [ -n "$server_pid" ]; then
        stop_server "$server_pid" "$framework"
        rm -f "$RESULTS_DIR/${framework}_server.pid"
    fi

    if [ "$all_passed" = true ]; then
        print_success "All benchmarks completed for $framework"
    else
        print_warning "Some benchmarks failed for $framework"
    fi

    echo ""
}

# Function to cleanup any running servers
cleanup_servers() {
    print_status "Cleaning up any running benchmark servers..."

    for server_config in "${BASIC_SERVERS[@]}"; do
        local framework=${server_config%%:*}
        local port=$(echo "$server_config" | cut -d':' -f2)
        local pid_file="$RESULTS_DIR/${framework}_server.pid"

        if [ -f "$pid_file" ]; then
            local pid=$(cat "$pid_file")
            stop_server "$pid" "$framework"
            rm -f "$pid_file"
        fi

        # Also check for any processes using the port
        if check_port "$port"; then
            local existing_pid=$(lsof -Pi :$port -sTCP:LISTEN -t 2>/dev/null | head -1)
            if [ -n "$existing_pid" ]; then
                print_warning "Killing process $existing_pid using port $port"
                kill -TERM "$existing_pid" 2>/dev/null || true
                sleep 1
                kill -KILL "$existing_pid" 2>/dev/null || true
            fi
        fi
    done

    # Clean up temporary Lua scripts
    cleanup_lua_files
}

# Function to clean up temporary Lua scripts
cleanup_lua_files() {
    # Only clean up Lua files from results directory (temporary files)
    if [ -d "$RESULTS_DIR" ]; then
        local lua_count=$(find "$RESULTS_DIR" -name "*.lua" -type f 2>/dev/null | wc -l)
        if [ "$lua_count" -gt 0 ]; then
            print_status "Cleaning up $lua_count temporary Lua script(s) from results directory..."
            find "$RESULTS_DIR" -name "*.lua" -type f -delete 2>/dev/null || true
        fi
    fi
}

# Function to generate summary report
generate_summary() {
    print_status "Generating benchmark summary..."

    local summary_file="$RESULTS_DIR/benchmark_summary.json"
    local summary_md="$RESULTS_DIR/benchmark_summary.md"

    # Create JSON summary
    echo "{" > "$summary_file"
    echo "  \"benchmark_info\": {" >> "$summary_file"
    echo "    \"timestamp\": \"$(date -Iseconds)\"," >> "$summary_file"
    echo "    \"duration\": \"$DURATION\"," >> "$summary_file"
    echo "    \"connections\": $CONNECTIONS," >> "$summary_file"
    echo "    \"threads\": $THREADS," >> "$summary_file"
    echo "    \"tool\": \"wrk\"" >> "$summary_file"
    echo "  }," >> "$summary_file"
    echo "  \"results\": [" >> "$summary_file"

    # Collect all individual results
    local first=true
    for json_file in "$RESULTS_DIR"/*.json; do
        if [ -f "$json_file" ] && [[ "$json_file" != *"summary"* ]]; then
            if [ "$first" = false ]; then
                echo "," >> "$summary_file"
            fi
            cat "$json_file" | sed 's/^/    /' >> "$summary_file"
            first=false
        fi
    done

    echo "" >> "$summary_file"
    echo "  ]" >> "$summary_file"
    echo "}" >> "$summary_file"

    print_success "Benchmark summary saved to: $summary_file"

    # Create Markdown summary
    cat > "$summary_md" << EOF
# Catzilla Performance Benchmark Results

## Test Configuration
- **Duration**: $DURATION
- **Connections**: $CONNECTIONS
- **Threads**: $THREADS
- **Tool**: wrk
- **Date**: $(date)

## Performance Results

| Framework | Endpoint | Requests/sec | Avg Latency | 99% Latency |
|-----------|----------|--------------|-------------|-------------|
EOF

    # Parse JSON results to create table
    for json_file in "$RESULTS_DIR"/*.json; do
        if [ -f "$json_file" ] && [[ "$json_file" != *"summary"* ]]; then
            local framework=$(grep '"framework"' "$json_file" | cut -d'"' -f4)
            local endpoint=$(grep '"endpoint_name"' "$json_file" | cut -d'"' -f4)
            local rps=$(grep '"requests_per_sec"' "$json_file" | cut -d'"' -f4)
            local avg_lat=$(grep '"avg_latency"' "$json_file" | cut -d'"' -f4)
            local p99_lat=$(grep '"p99_latency"' "$json_file" | cut -d'"' -f4)
            echo "| $framework | $endpoint | $rps | $avg_lat | $p99_lat |" >> "$summary_md"
        fi
    done

    echo "" >> "$summary_md"
    print_success "Markdown summary saved to: $summary_md"
}

# Show usage information
usage() {
    echo "Enhanced Catzilla Benchmark Runner"
    echo ""
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --mode MODE         Benchmark mode: 'direct' (wrk) or 'python' (feature-based)"
    echo "  --framework FRAMEWORK    Run specific framework only (catzilla,fastapi,flask,django)"
    echo "  --duration TIME     Test duration (default: 10s)"
    echo "  --connections NUM   Number of connections (default: 100)"
    echo "  --threads NUM       Number of threads (default: 4)"
    echo "  --help             Show this help message"
    echo ""
    echo "Direct Mode (wrk) Examples:"
    echo "  $0                                    # Run all frameworks with wrk"
    echo "  $0 --framework catzilla              # Run Catzilla only"
    echo "  $0 --duration 30s --connections 200  # Custom settings"
    echo ""
    echo "Python Feature Mode Examples:"
    echo "  $0 --mode python --basic             # Run basic HTTP benchmarks"
    echo "  $0 --mode python --validation        # Run validation engine benchmarks"
    echo "  $0 --mode python --file-ops          # Run file operations benchmarks"
    echo "  $0 --mode python --bg-tasks          # Run background tasks benchmarks"
    echo "  $0 --mode python --real-world        # Run real-world scenarios"
    echo "  $0 --mode python --all               # Run all feature categories"
    echo ""
    echo "Available frameworks: catzilla, fastapi, flask, django"
    echo "Available feature categories: basic, middleware, dependency_injection, async_operations, validation, file_operations, background_tasks, real_world_scenarios"
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

# Parse command line arguments
parse_arguments() {
    MODE="direct"  # Default to direct wrk mode
    SELECTED_FRAMEWORK=""
    PYTHON_ARGS=""

    while [[ $# -gt 0 ]]; do
        case $1 in
            --mode)
                MODE="$2"
                shift 2
                ;;
            --framework)
                SELECTED_FRAMEWORK="$2"
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
            --basic|--middleware|--di|--async|--validation|--file-ops|--bg-tasks|--real-world|--all)
                MODE="python"
                PYTHON_ARGS="$PYTHON_ARGS $1"
                shift
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

    # Validate framework if specified
    if [ -n "$SELECTED_FRAMEWORK" ]; then
        local valid_frameworks=("catzilla" "fastapi" "flask" "django")
        local framework_valid=false

        for valid_fw in "${valid_frameworks[@]}"; do
            if [ "$valid_fw" = "$SELECTED_FRAMEWORK" ]; then
                framework_valid=true
                break
            fi
        done

        if [ "$framework_valid" = false ]; then
            print_error "Invalid framework: $SELECTED_FRAMEWORK"
            print_error "Valid frameworks: ${valid_frameworks[*]}"
            exit 1
        fi
    fi

    # Validate mode
    if [ "$MODE" != "direct" ] && [ "$MODE" != "python" ]; then
        print_error "Invalid mode: $MODE"
        print_error "Valid modes: direct, python"
        exit 1
    fi
}

# Run direct wrk benchmarks (like benchmarks_old)
run_direct_benchmarks() {
    print_header "🚀 Direct wrk Benchmark Mode"
    echo "Duration: $DURATION, Connections: $CONNECTIONS, Threads: $THREADS"
    echo "=========================================="

    # Activate virtual environment if it exists
    if [ -f "$VENV_PATH/bin/activate" ]; then
        print_status "Activating virtual environment..."
        source "$VENV_PATH/bin/activate"
        print_success "Virtual environment activated"
    else
        print_warning "Virtual environment not found at $VENV_PATH"
    fi

    # Trap to ensure cleanup on exit
    trap cleanup_servers EXIT

    # Clean up any existing servers
    cleanup_servers

    # Determine which frameworks to test
    local frameworks_to_test
    if [ -n "$SELECTED_FRAMEWORK" ]; then
        frameworks_to_test=("$SELECTED_FRAMEWORK")
    else
        frameworks_to_test=("catzilla" "fastapi" "flask" "django")
    fi

    print_status "Testing frameworks: ${frameworks_to_test[*]}"
    echo ""

    # Run benchmarks for each framework
    for framework in "${frameworks_to_test[@]}"; do
        benchmark_framework "$framework"
        sleep 3  # Pause between frameworks
    done

    # Generate summary
    generate_summary

    print_success "All benchmarks completed!"
    print_status "Results saved in: $RESULTS_DIR"
}

# Run Python feature-based benchmarks
run_python_benchmarks() {
    print_header "🚀 Python Feature-Based Benchmark Mode"

    # Prepare arguments for enhanced benchmark runner
    local enhanced_cmd="./run_enhanced_feature_benchmarks.sh"

    # Convert Python arguments to categories
    local categories=""
    if [ -n "$PYTHON_ARGS" ]; then
        # Remove leading/trailing whitespace from PYTHON_ARGS
        PYTHON_ARGS=$(echo "$PYTHON_ARGS" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')
        for arg in $PYTHON_ARGS; do
            case $arg in
                --basic) categories="${categories} basic" ;;
                --middleware) categories="${categories} middleware" ;;
                --di) categories="${categories} dependency_injection" ;;
                --async) categories="${categories} async_operations" ;;
                --validation) categories="${categories} validation" ;;
                --file-ops) categories="${categories} file_operations" ;;
                --bg-tasks) categories="${categories} background_tasks" ;;
                --real-world) categories="${categories} real_world_scenarios" ;;
                --all) categories="all" ;;
            esac
        done
        # Remove leading space
        categories=$(echo "$categories" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')
    else
        # Default to basic category
        categories="basic"
    fi

    print_status "Running enhanced benchmarks for categories: $categories"
    print_status "PYTHON_ARGS was: $PYTHON_ARGS"
    print_status "Duration: $DURATION, Connections: $CONNECTIONS, Threads: $THREADS"

    # Convert duration from "10s" format to just "10" for the enhanced script
    local duration_numeric=$(echo "$DURATION" | sed 's/s$//')

    # Set environment variables for the enhanced script
    export DURATION="$duration_numeric"
    export CONNECTIONS="$CONNECTIONS"
    export THREADS="$THREADS"

    # Run the enhanced benchmark runner
    cd "$BENCHMARK_DIR"

    if [ "$categories" = "all" ]; then
        eval "$enhanced_cmd all"
    else
        # Run each category separately
        for category in $categories; do
            print_status "Running $category benchmarks..."
            eval "$enhanced_cmd $category"
        done
    fi

    print_success "Enhanced benchmark completed!"
}

# Main execution
main() {
    # Parse command line arguments
    parse_arguments "$@"

    # Check dependencies
    check_dependencies

    print_header "🚀 Enhanced Catzilla Benchmark Runner"
    echo "Mode: $MODE"
    echo "=========================================="

    if [ "$MODE" = "direct" ]; then
        run_direct_benchmarks
    elif [ "$MODE" = "python" ]; then
        run_python_benchmarks
    else
        print_error "Invalid mode: $MODE"
        exit 1
    fi
}

# Handle interrupts
trap 'print_warning "Benchmark interrupted by user"; cleanup_servers; exit 1' INT TERM

# Run main function
main "$@"
