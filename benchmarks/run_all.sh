#!/usr/bin/env zsh
# Catzilla Benchmark Runner
#
# This script runs comprehensive performance benchmarks comparing Catzilla
# against other popular Python web frameworks (FastAPI, Flask, Django).
#
# It starts each server, runs benchmarks using 'wrk', and collects results.

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

# Server configurations (using arrays instead of associative arrays for compatibility)
SERVERS=(
    "catzilla:8000:python3 $SERVERS_DIR/catzilla_server.py --port 8000"
    "fastapi:8001:python3 $SERVERS_DIR/fastapi_server.py --port 8001"
    "flask:8002:python3 $SERVERS_DIR/flask_server.py --port 8002 --use-gunicorn"
    "django:8003:python3 $SERVERS_DIR/django_server.py --port 8003"
)

# Test endpoints
ENDPOINTS=(
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

# Function to get server config by framework name
get_server_config() {
    local framework=$1
    for server_config in "${SERVERS[@]}"; do
        local name=${server_config%%:*}
        if [ "$name" = "$framework" ]; then
            echo "${server_config#*:}"
            return 0
        fi
    done
    return 1
}

# Function to run benchmark for a specific endpoint
run_benchmark() {
    local framework=$1
    local endpoint=$2
    local endpoint_name=$3
    local host="127.0.0.1"
    local server_config=$(get_server_config "$framework")
    local port=${server_config%%:*}
    local url="http://$host:$port$endpoint"

    print_status "Benchmarking $framework - $endpoint_name ($endpoint)"

    # Warmup run
    print_status "Warming up $framework server..."
    wrk -t1 -c10 -d"$WARMUP_TIME" "$url" >/dev/null 2>&1 || true

    # Main benchmark
    local result_file="$RESULTS_DIR/${framework}_${endpoint_name}.txt"
    local json_file="$RESULTS_DIR/${framework}_${endpoint_name}.json"

    print_status "Running main benchmark..."

    # Run wrk and capture output
    if wrk -t"$THREADS" -c"$CONNECTIONS" -d"$DURATION" --latency "$url" > "$result_file" 2>&1; then
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

# Function to start a server
start_server() {
    local framework=$1
    local server_config=$(get_server_config "$framework")
    local port=${server_config%%:*}
    local command=${server_config#*:}

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
    cd "$BENCHMARK_DIR/.."  # Run from project root
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

# Function to run benchmarks for a single framework
benchmark_framework() {
    local framework=$1

    print_status "Starting benchmark for $framework"
    echo "=================================================="

    # Start the server
    if ! start_server "$framework"; then
        print_error "Skipping $framework due to server start failure"
        return 1
    fi

    # Get server PID for cleanup
    local server_pid=$(cat "$RESULTS_DIR/${framework}_server.pid" 2>/dev/null || echo "")

    # Run benchmarks for each endpoint
    local all_passed=true
    for endpoint_config in "${ENDPOINTS[@]}"; do
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

    for server_config in "${SERVERS[@]}"; do
        local framework=${server_config%%:*}
        local config=${server_config#*:}
        local port=${config%%:*}
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
                print_warning "Force stopping process on port $port (PID: $existing_pid)"
                kill -KILL "$existing_pid" 2>/dev/null || true
            fi
        fi
    done
}

# Function to generate summary report
generate_summary() {
    print_status "Generating benchmark summary..."

    local summary_file="$RESULTS_DIR/benchmark_summary.json"
    local summary_md="$RESULTS_DIR/benchmark_summary.md"
    local system_info_file="$RESULTS_DIR/system_info.json"
    local system_info_md="$RESULTS_DIR/system_info.md"

    # Collect system information
    print_status "Collecting system information..."
    if python3 "$BENCHMARK_DIR/system_info.py" --output "$system_info_file"; then
        print_success "System information collected"

        # Also generate markdown format for easy inclusion in reports
        python3 "$BENCHMARK_DIR/system_info.py" --format markdown --output "$system_info_md"
    else
        print_warning "Failed to collect system information, continuing without it"
        echo '{"error": "System information collection failed"}' > "$system_info_file"
        echo "## System Information\n\n**Error**: System information collection failed" > "$system_info_md"
    fi

    # Create JSON summary
    echo "{" > "$summary_file"
    echo "  \"benchmark_info\": {" >> "$summary_file"
    echo "    \"timestamp\": \"$(date -Iseconds)\"," >> "$summary_file"
    echo "    \"duration\": \"$DURATION\"," >> "$summary_file"
    echo "    \"connections\": $CONNECTIONS," >> "$summary_file"
    echo "    \"threads\": $THREADS," >> "$summary_file"
    echo "    \"tool\": \"wrk\"" >> "$summary_file"
    echo "  }," >> "$summary_file"

    # Add system information to summary
    if [ -f "$system_info_file" ]; then
        echo "  \"system_info\": " >> "$summary_file"
        cat "$system_info_file" >> "$summary_file"
        echo "," >> "$summary_file"
    fi

    echo "  \"results\": [" >> "$summary_file"

    # Collect all individual results
    local first=true
    for json_file in "$RESULTS_DIR"/*.json; do
        if [ -f "$json_file" ] && [[ "$json_file" != *"summary"* ]] && [[ "$json_file" != *"system_info"* ]]; then
            if [ "$first" = true ]; then
                first=false
            else
                echo "," >> "$summary_file"
            fi
            cat "$json_file" | sed 's/^/    /' >> "$summary_file"
        fi
    done

    echo "" >> "$summary_file"
    echo "  ]" >> "$summary_file"
    echo "}" >> "$summary_file"

    print_success "Benchmark summary saved to: $summary_file"

    # Create Markdown summary
    cat > "$summary_md" << 'EOF'
# Catzilla Performance Benchmark Results

## Test Configuration
EOF
    echo "- **Duration**: $DURATION" >> "$summary_md"
    echo "- **Connections**: $CONNECTIONS" >> "$summary_md"
    echo "- **Threads**: $THREADS" >> "$summary_md"
    echo "- **Tool**: wrk" >> "$summary_md"
    echo "- **Date**: $(date)" >> "$summary_md"
    echo "" >> "$summary_md"

    # Add system information to markdown summary
    if [ -f "$system_info_md" ]; then
        cat "$system_info_md" >> "$summary_md"
        echo "" >> "$summary_md"
    fi

    # Add performance results table
    echo "## Performance Results" >> "$summary_md"
    echo "" >> "$summary_md"
    echo "| Framework | Endpoint | Requests/sec | Avg Latency | 99% Latency |" >> "$summary_md"
    echo "|-----------|----------|--------------|-------------|-------------|" >> "$summary_md"

    # Parse JSON results to create table
    for json_file in "$RESULTS_DIR"/*.json; do
        if [ -f "$json_file" ] && [[ "$json_file" != *"summary"* ]] && [[ "$json_file" != *"system_info"* ]]; then
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

# Main execution
main() {
    # Activate virtual environment if it exists
    if [ -f "$VENV_PATH/bin/activate" ]; then
        print_status "Activating virtual environment..."
        source "$VENV_PATH/bin/activate"
        print_success "Virtual environment activated"
    else
        print_warning "Virtual environment not found at $VENV_PATH"
    fi

    print_status "Starting Catzilla Performance Benchmarks"
    echo "=========================================="
    echo "Duration: $DURATION"
    echo "Connections: $CONNECTIONS"
    echo "Threads: $THREADS"
    echo "Results Directory: $RESULTS_DIR"
    echo ""

    # Trap to ensure cleanup on exit
    trap cleanup_servers EXIT

    # Clean up any existing servers
    cleanup_servers

    # Run benchmarks for each framework
    local frameworks_to_test=("catzilla" "fastapi" "flask" "django")

    for framework in "${frameworks_to_test[@]}"; do
        if ! benchmark_framework "$framework"; then
            print_warning "Benchmark failed for $framework, continuing with others..."
        fi
        sleep 3  # Pause between frameworks
    done

    # Generate summary
    generate_summary

    print_success "All benchmarks completed!"
    print_status "Results saved in: $RESULTS_DIR"
    print_status "To visualize results, run: python3 $BENCHMARK_DIR/visualize_results.py"
}

# Check if script is being run directly (works with both bash and zsh)
if [[ "${0}" == *"run_all.sh" ]]; then
    main "$@"
fi
