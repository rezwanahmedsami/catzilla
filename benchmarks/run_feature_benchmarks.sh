#!/usr/bin/env zsh
# Catzilla Feature-Based Benchmark Runner
#
# This script runs comprehensive feature-based performance benchmarks comparing Catzilla
# against other popular Python web frameworks (FastAPI, Flask, Django).
#
# It maintains compatibility with the old benchmarking system while adding
# feature-specific testing capabilities.

set -e  # Exit on any error

# Configuration
BENCHMARK_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$BENCHMARK_DIR/.." && pwd)"
RESULTS_DIR="$BENCHMARK_DIR/results"
SERVERS_DIR="$BENCHMARK_DIR/servers"
SHARED_DIR="$BENCHMARK_DIR/shared"
TOOLS_DIR="$BENCHMARK_DIR/tools"
VENV_PATH="$PROJECT_ROOT/venv"

# Create results directory
mkdir -p "$RESULTS_DIR"

# Benchmark settings (same as old system)
DURATION="10s"          # Duration of each test
CONNECTIONS="100"       # Number of concurrent connections
THREADS="4"             # Number of threads to use
WARMUP_TIME="3s"        # Warmup duration

# Feature categories available for benchmarking
FEATURE_CATEGORIES=(
    "basic"
    "middleware"
    "dependency_injection"
    "async_operations"
    "database_integration"
    "validation"
    "file_operations"
    "background_tasks"
    "real_world_scenarios"
)

# Colors for output (same as old system)
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output (same as old system)
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

# Function to check if a port is in use (same as old system)
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        return 0  # Port is in use
    else
        return 1  # Port is free
    fi
}

# Function to wait for server to start (same as old system)
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

# Function to stop server by PID (same as old system)
stop_server() {
    local pid=$1
    local name=$2

    if [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then
        print_status "Stopping $name server (PID: $pid)..."
        kill -TERM "$pid" 2>/dev/null || true

        # Wait for graceful shutdown
        for i in {1..10}; do
            if ! kill -0 "$pid" 2>/dev/null; then
                print_success "$name server stopped gracefully"
                return 0
            fi
            sleep 1
        done

        # Force kill if necessary
        print_warning "Force killing $name server..."
        kill -KILL "$pid" 2>/dev/null || true
    fi
}

# Function to discover available servers for a feature category
discover_servers() {
    local feature_category=$1
    local feature_dir="$SERVERS_DIR/$feature_category"
    local servers=()

    if [ ! -d "$feature_dir" ]; then
        print_warning "Feature category '$feature_category' not found at $feature_dir"
        return 1
    fi

    # Look for server files in the feature directory
    for server_file in "$feature_dir"/*.py; do
        if [ -f "$server_file" ]; then
            local basename=$(basename "$server_file" .py)
            local framework_name=${basename%_*}  # Extract framework name (e.g., 'catzilla' from 'catzilla_middleware.py')
            servers+=("$framework_name:$server_file")
        fi
    done

    if [ ${#servers[@]} -eq 0 ]; then
        print_warning "No server files found in $feature_dir"
        return 1
    fi

    # Return the servers array
    printf '%s\n' "${servers[@]}"
    return 0
}

# Function to get server configuration (auto-assign ports)
get_server_config() {
    local framework=$1
    local base_port=$2

    # Auto-assign ports based on framework
    case "$framework" in
        "catzilla")
            echo "$base_port"
            ;;
        "fastapi")
            echo "$((base_port + 1))"
            ;;
        "flask")
            echo "$((base_port + 2))"
            ;;
        "django")
            echo "$((base_port + 3))"
            ;;
        "aiohttp")
            echo "$((base_port + 4))"
            ;;
        "tornado")
            echo "$((base_port + 5))"
            ;;
        *)
            echo "$((base_port + 10))"  # Default for unknown frameworks
            ;;
    esac
}

# Function to run benchmark for a specific endpoint (same core logic as old system)
run_benchmark() {
    local framework=$1
    local endpoint=$2
    local endpoint_name=$3
    local port=$4
    local method=${5:-"GET"}
    local post_data=${6:-""}
    local host="127.0.0.1"
    local url="http://$host:$port$endpoint"

    print_status "Benchmarking $framework - $endpoint_name ($endpoint)"

    # Warmup run (same as old system)
    print_status "Warming up $framework server..."
    if [ "$method" = "POST" ] && ([ -n "$post_data" ] || [[ "$endpoint_name" == *"validate"* ]]); then
        local warmup_payload
        if [[ "$endpoint_name" == *"product"* ]]; then
            warmup_payload='{"name": "High-Performance Widget", "price": 99.99, "category": "electronics", "description": "A widget designed for maximum performance", "in_stock": true, "variants": ["red", "blue", "green"]}'
        elif [[ "$endpoint_name" == *"user"* ]] || [[ "$endpoint_name" == *"validate"* ]]; then
            warmup_payload='{"id": 42, "name": "Alice Johnson", "email": "alice@example.com", "age": 28, "is_active": true, "tags": ["developer", "python", "performance"], "metadata": {"team": "backend", "level": "senior"}}'
        else
            warmup_payload='{"message": "Hello from benchmark", "timestamp": 1640995200, "data": {"nested": true, "values": [1, 2, 3, 4, 5]}}'
        fi

        # Create temporary Lua script for POST requests
        local lua_script="$RESULTS_DIR/temp_post.lua"
        cat > "$lua_script" << EOF
wrk.method = "POST"
wrk.body = '$warmup_payload'
wrk.headers["Content-Type"] = "application/json"
EOF

        wrk -t1 -c10 -d"$WARMUP_TIME" -s "$lua_script" "$url" >/dev/null 2>&1 || true
        rm -f "$lua_script"
    else
        wrk -t1 -c10 -d"$WARMUP_TIME" "$url" >/dev/null 2>&1 || true
    fi

    # Main benchmark (same core logic as old system)
    local result_file="$RESULTS_DIR/${framework}_${endpoint_name}.txt"
    local json_file="$RESULTS_DIR/${framework}_${endpoint_name}.json"

    print_status "Running main benchmark..."

    # Run wrk and capture output
    local wrk_success=false
    if [ "$method" = "POST" ] && ([ -n "$post_data" ] || [[ "$endpoint_name" == *"validate"* ]]); then
        # POST request with JSON body - choose appropriate payload
        local json_payload
        if [[ "$endpoint_name" == *"product"* ]]; then
            json_payload='{"name": "High-Performance Widget", "price": 99.99, "category": "electronics", "description": "A widget designed for maximum performance", "in_stock": true, "variants": ["red", "blue", "green"]}'
        elif [[ "$endpoint_name" == *"user"* ]] || [[ "$endpoint_name" == *"validate"* ]]; then
            json_payload='{"id": 42, "name": "Alice Johnson", "email": "alice@example.com", "age": 28, "is_active": true, "tags": ["developer", "python", "performance"], "metadata": {"team": "backend", "level": "senior"}}'
        else
            json_payload='{"message": "Hello from benchmark", "timestamp": 1640995200, "data": {"nested": true, "values": [1, 2, 3, 4, 5]}}'
        fi

        # Create temporary Lua script for POST requests
        local lua_script="$RESULTS_DIR/temp_${framework}_${endpoint_name}.lua"
        cat > "$lua_script" << EOF
wrk.method = "POST"
wrk.body = '$json_payload'
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

        # Extract key metrics and save as JSON (same as old system)
        local requests_per_sec=$(grep "Requests/sec:" "$result_file" | awk '{print $2}' | head -1)
        local avg_latency=$(grep "Latency" "$result_file" | awk '{print $2}' | head -1)
        local p99_latency=$(grep "99%" "$result_file" | awk '{print $2}' | head -1)
        local transfer_per_sec=$(grep "Transfer/sec:" "$result_file" | awk '{print $2}' | head -1)

        # Create JSON summary (same format as old system)
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
  "timestamp": "$(date -Iseconds)",
  "feature_category": "$CURRENT_FEATURE_CATEGORY"
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

# Function to start a server for a specific feature
start_feature_server() {
    local framework=$1
    local server_file=$2
    local port=$3

    print_status "Starting $framework server on port $port..."

    # Kill any existing process on this port
    if check_port "$port"; then
        print_warning "Port $port is in use, attempting to free it..."
        local existing_pid=$(lsof -ti:$port)
        if [ -n "$existing_pid" ]; then
            kill -TERM "$existing_pid" 2>/dev/null || true
            sleep 2
        fi
    fi

    # Start the server
    local server_pid
    if [[ "$server_file" == *"flask"* ]] && [[ "$server_file" == *"gunicorn"* ]]; then
        # Special handling for Flask with Gunicorn
        python3 "$server_file" --port "$port" --use-gunicorn &
        server_pid=$!
    else
        # Standard Python server
        python3 "$server_file" --port "$port" &
        server_pid=$!
    fi

    # Wait a moment for the server to start
    sleep 2

    # Verify the server started
    if ! kill -0 "$server_pid" 2>/dev/null; then
        print_error "Failed to start $framework server"
        return 1
    fi

    # Wait for server to become ready
    if wait_for_server "127.0.0.1" "$port" 30; then
        echo "$server_pid"  # Return the PID
        return 0
    else
        print_error "Server started but not responding on port $port"
        kill -TERM "$server_pid" 2>/dev/null || true
        return 1
    fi
}

# Function to run benchmarks for a specific feature category
run_feature_benchmarks() {
    local feature_category=$1
    local base_port=${2:-8000}

    export CURRENT_FEATURE_CATEGORY="$feature_category"

    print_status "Running benchmarks for feature category: $feature_category"

    # Discover available servers for this feature
    local servers_output
    if ! servers_output=$(discover_servers "$feature_category"); then
        print_error "No servers found for feature category: $feature_category"
        return 1
    fi

    # Convert output to array
    local servers=()
    while IFS= read -r line; do
        servers+=("$line")
    done <<< "$servers_output"

    print_status "Found ${#servers[@]} servers for $feature_category"

    # Load feature-specific endpoints
    local endpoints_file="$SERVERS_DIR/$feature_category/endpoints.json"
    local endpoints=()

    if [ -f "$endpoints_file" ]; then
        # Load custom endpoints for this feature
        print_status "Loading feature-specific endpoints from $endpoints_file"
        # Parse JSON file to get endpoints (simplified for now)
        endpoints=(
            "/:home:GET"
            "/health:health_check:GET"
            "/feature-test:feature_specific:GET"
        )
    else
        # Use default endpoints
        print_status "Using default endpoints for $feature_category"
        endpoints=(
            "/:hello_world:GET"
            "/health:health_check:GET"
            "/json:json_response:GET"
            "/user/42:path_params:GET"
        )
    fi

    # Start servers and run benchmarks
    local server_pids=()
    local current_port=$base_port

    for server_config in "${servers[@]}"; do
        local framework=${server_config%%:*}
        local server_file=${server_config#*:}
        local port=$(get_server_config "$framework" "$current_port")

        print_status "Processing $framework server..."

        # Start the server
        local server_pid
        if server_pid=$(start_feature_server "$framework" "$server_file" "$port"); then
            server_pids+=("$server_pid:$framework")

            # Run benchmarks for all endpoints
            for endpoint_config in "${endpoints[@]}"; do
                local endpoint_path=${endpoint_config%%:*}
                local endpoint_name=${endpoint_config#*:}
                endpoint_name=${endpoint_name%%:*}
                local method=${endpoint_config##*:}

                # Run the benchmark
                if ! run_benchmark "$framework" "$endpoint_path" "${feature_category}_${endpoint_name}" "$port" "$method"; then
                    print_warning "Benchmark failed for $framework:$endpoint_name"
                fi
            done

            # Stop the server
            stop_server "$server_pid" "$framework"
        else
            print_warning "Failed to start $framework server, skipping..."
        fi

        current_port=$((current_port + 10))  # Space out ports
    done

    # Cleanup any remaining servers
    for pid_info in "${server_pids[@]}"; do
        local pid=${pid_info%%:*}
        local name=${pid_info#*:}
        stop_server "$pid" "$name"
    done

    print_success "Completed benchmarks for feature category: $feature_category"
}

# Function to generate comprehensive report (same format as old system)
generate_report() {
    local report_file="$RESULTS_DIR/benchmark_summary.json"
    local timestamp=$(date -Iseconds)

    print_status "Generating comprehensive benchmark report..."

    # Collect system information
    local system_info_file="$RESULTS_DIR/system_info.json"
    if [ -f "$TOOLS_DIR/system_info.py" ]; then
        python3 "$TOOLS_DIR/system_info.py" --output "$system_info_file" --format json
    fi

    # Collect all individual results
    local results=()
    for json_file in "$RESULTS_DIR"/*.json; do
        if [[ "$json_file" != *"summary"* ]] && [[ "$json_file" != *"system_info"* ]]; then
            results+=("$json_file")
        fi
    done

    # Create summary report (same structure as old system)
    cat > "$report_file" << EOF
{
  "benchmark_run": {
    "timestamp": "$timestamp",
    "duration": "$DURATION",
    "connections": $CONNECTIONS,
    "threads": $THREADS,
    "total_tests": ${#results[@]}
  },
  "system_info_file": "system_info.json",
  "results": [
EOF

    # Add individual results
    local first=true
    for result_file in "${results[@]}"; do
        if [ "$first" = true ]; then
            first=false
        else
            echo "," >> "$report_file"
        fi
        cat "$result_file" >> "$report_file"
    done

    cat >> "$report_file" << EOF

  ]
}
EOF

    print_success "Report generated: $report_file"

    # Generate visualizations if possible
    if [ -f "$TOOLS_DIR/visualize_results.py" ]; then
        print_status "Generating performance charts..."
        python3 "$TOOLS_DIR/visualize_results.py" "$RESULTS_DIR" || print_warning "Chart generation failed"
    fi
}

# Main execution
main() {
    local feature_category=${1:-"all"}
    local base_port=${2:-8000}

    print_status "🚀 Catzilla Feature-Based Benchmark Runner"
    echo "=========================================="
    echo "Feature Category: $feature_category"
    echo "Base Port: $base_port"
    echo "Results Directory: $RESULTS_DIR"
    echo "Duration: $DURATION"
    echo "Connections: $CONNECTIONS"
    echo "Threads: $THREADS"
    echo ""

    # Clean results directory
    rm -rf "$RESULTS_DIR"/*.txt "$RESULTS_DIR"/*.json 2>/dev/null || true

    if [ "$feature_category" = "all" ]; then
        # Run all available feature categories
        print_status "Running benchmarks for all feature categories..."
        local current_base_port=$base_port

        for category in "${FEATURE_CATEGORIES[@]}"; do
            if [ -d "$SERVERS_DIR/$category" ]; then
                run_feature_benchmarks "$category" "$current_base_port"
                current_base_port=$((current_base_port + 100))  # Large port spacing between categories
            else
                print_warning "Skipping $category - directory not found"
            fi
        done
    else
        # Run specific feature category
        if [ -d "$SERVERS_DIR/$feature_category" ]; then
            run_feature_benchmarks "$feature_category" "$base_port"
        else
            print_error "Feature category '$feature_category' not found"
            echo "Available categories:"
            for category in "${FEATURE_CATEGORIES[@]}"; do
                if [ -d "$SERVERS_DIR/$category" ]; then
                    echo "  - $category"
                fi
            done
            exit 1
        fi
    fi

    # Generate final report
    generate_report

    print_success "🎉 Feature-based benchmarking completed!"
    print_status "Results available in: $RESULTS_DIR"
    print_status "Summary report: $RESULTS_DIR/benchmark_summary.json"
}

# Help function
show_help() {
    echo "Catzilla Feature-Based Benchmark Runner"
    echo ""
    echo "Usage: $0 [FEATURE_CATEGORY] [BASE_PORT]"
    echo ""
    echo "FEATURE_CATEGORY:"
    echo "  all                    - Run all available feature benchmarks (default)"
    echo "  basic                  - Basic HTTP benchmarks"
    echo "  middleware             - Middleware performance benchmarks"
    echo "  dependency_injection   - DI system benchmarks"
    echo "  async_operations       - Async/sync hybrid benchmarks"
    echo "  database_integration   - Database + ORM benchmarks"
    echo "  validation             - Auto-validation benchmarks"
    echo "  file_operations        - File upload/static serving benchmarks"
    echo "  background_tasks       - Background task benchmarks"
    echo "  real_world_scenarios   - Complete application benchmarks"
    echo ""
    echo "BASE_PORT:"
    echo "  Starting port number (default: 8000)"
    echo "  Frameworks will use sequential ports from this base"
    echo ""
    echo "Examples:"
    echo "  $0                           # Run all benchmarks"
    echo "  $0 middleware               # Run only middleware benchmarks"
    echo "  $0 basic 9000              # Run basic benchmarks starting from port 9000"
    echo ""
    echo "Environment:"
    echo "  DURATION='$DURATION'         # Benchmark duration"
    echo "  CONNECTIONS=$CONNECTIONS          # Concurrent connections"
    echo "  THREADS=$THREADS              # Number of threads"
}

# Check for help flag
if [ "$1" = "-h" ] || [ "$1" = "--help" ]; then
    show_help
    exit 0
fi

# Check dependencies
if ! command -v wrk >/dev/null 2>&1; then
    print_error "wrk is required but not installed. Please install wrk:"
    echo "  macOS: brew install wrk"
    echo "  Ubuntu: sudo apt-get install wrk"
    echo "  Or visit: https://github.com/wg/wrk"
    exit 1
fi

if ! command -v python3 >/dev/null 2>&1; then
    print_error "python3 is required but not installed"
    exit 1
fi

# Run main function
main "$@"
