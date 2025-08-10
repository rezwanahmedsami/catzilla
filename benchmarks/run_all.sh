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
    "fastapi:8001:uvicorn benchmarks.servers.basic.fastapi_server:app --host 127.0.0.1 --port 8001"
    "flask:8002:gunicorn --bind 127.0.0.1:8002 --workers 4 --worker-class sync benchmarks.servers.basic.flask_server:app"
    "django:8003:gunicorn --bind 127.0.0.1:8003 --workers 4 --worker-class sync benchmarks.servers.basic.django_server:application"
)

# Server configurations for dependency injection benchmarks
DI_SERVERS=(
    "catzilla:8010:python3 $SERVERS_DIR/dependency_injection/catzilla_di.py --port 8010"
    "fastapi:8011:uvicorn benchmarks.servers.dependency_injection.fastapi_di:app --host 127.0.0.1 --port 8011"
    "django:8012:gunicorn --bind 127.0.0.1:8012 --workers 4 --worker-class sync benchmarks.servers.dependency_injection.django_di:application"
)

# Server configurations for SQLAlchemy DI benchmarks
SQLALCHEMY_DI_SERVERS=(
    "catzilla:8020:python3 $SERVERS_DIR/dependency_injection/catzilla_sqlalchemy_di.py --port 8020"
    "fastapi:8021:uvicorn benchmarks.servers.dependency_injection.fastapi_sqlalchemy_di:app --host 127.0.0.1 --port 8021"
    "flask:8022:gunicorn --bind 127.0.0.1:8022 --workers 4 --worker-class sync benchmarks.servers.dependency_injection.flask_sqlalchemy_di:app"
)

# Server configurations for middleware benchmarks
MIDDLEWARE_SERVERS=(
    "catzilla:8030:python3 $SERVERS_DIR/middleware/catzilla_middleware.py --port 8030"
    "fastapi:8031:uvicorn benchmarks.servers.middleware.fastapi_middleware:app --host 127.0.0.1 --port 8031"
    "django:8032:gunicorn --bind 127.0.0.1:8032 --workers 4 --worker-class sync benchmarks.servers.middleware.django_middleware:application"
)

# Server configurations for validation benchmarks
VALIDATION_SERVERS=(
    "catzilla:8040:python3 $SERVERS_DIR/validation/catzilla_validation.py --port 8040"
    "fastapi:8041:uvicorn benchmarks.servers.validation.fastapi_validation:app --host 127.0.0.1 --port 8041"
    "flask:8042:gunicorn --bind 127.0.0.1:8042 --workers 4 --worker-class sync benchmarks.servers.validation.flask_validation:app"
    "django:8043:gunicorn --bind 127.0.0.1:8043 --workers 4 --worker-class sync benchmarks.servers.validation.django_validation:application"
)

# Server configurations for file operations benchmarks
FILE_OPERATIONS_SERVERS=(
    "catzilla:8050:python3 $SERVERS_DIR/file_operations/catzilla_file.py --port 8050"
    "fastapi:8051:uvicorn benchmarks.servers.file_operations.fastapi_file:app --host 127.0.0.1 --port 8051"
    "flask:8052:gunicorn --bind 127.0.0.1:8052 --workers 4 --worker-class sync benchmarks.servers.file_operations.flask_file:app"
    "django:8053:gunicorn --bind 127.0.0.1:8053 --workers 4 --worker-class sync benchmarks.servers.file_operations.django_file:application"
)

# Server configurations for background tasks benchmarks
BACKGROUND_TASKS_SERVERS=(
    "catzilla:8060:python3 $SERVERS_DIR/background_tasks/catzilla_tasks.py --port 8060"
    "fastapi:8061:uvicorn benchmarks.servers.background_tasks.fastapi_tasks:app --host 127.0.0.1 --port 8061"
    "flask:8062:gunicorn --bind 127.0.0.1:8062 --workers 4 --worker-class sync benchmarks.servers.background_tasks.flask_tasks:app"
    "django:8063:gunicorn --bind 127.0.0.1:8063 --workers 4 --worker-class sync benchmarks.servers.background_tasks.django_tasks:application"
)

# Server configurations for async operations benchmarks
ASYNC_OPERATIONS_SERVERS=(
    "django:8070:gunicorn --bind 127.0.0.1:8070 --workers 4 --worker-class sync benchmarks.servers.async_operations.django_async:application"
)

# Server configurations for real-world scenarios benchmarks
REAL_WORLD_SERVERS=(
    "catzilla:8080:python3 $SERVERS_DIR/real_world_scenarios/catzilla_realworld.py --port 8080"
    "fastapi:8081:uvicorn benchmarks.servers.real_world_scenarios.fastapi_realworld:app --host 127.0.0.1 --port 8081"
)

# Test endpoints for basic benchmarks
BASIC_ENDPOINTS=(
    "/:hello_world"
    "/json:json_response"
    "/user/42:path_params"
    "/users?limit=20&offset=10:query_params"
    "/user/123/profile:complex_json"
)

# Test endpoints for dependency injection benchmarks
DI_ENDPOINTS=(
    "/di/simple:simple_di"
    "/di/transient:transient_di"
    "/di/singleton:singleton_di"
    "/di/request:request_scoped_di"
    "/di/complex:complex_di_chain"
)

# Test endpoints for SQLAlchemy DI benchmarks
SQLALCHEMY_DI_ENDPOINTS=(
    "/health:health_check"
    "/di/simple:simple_di"
    "/di/transient:transient_di"
    "/di/db/users:db_users_list"
    "/di/db/user/1:db_user_detail"
    "/di/db/posts:db_posts_list"
    "/di/db/complex:complex_db_operations"
    "/di/db/chain:complex_di_chain"
)

# Test endpoints for middleware benchmarks
MIDDLEWARE_ENDPOINTS=(
    "/:home"
    "/health:health_check"
    "/middleware-light:light_middleware"
    "/middleware-heavy:heavy_middleware"
    "/middleware-auth:auth_middleware"
    "/middleware-cors:cors_middleware"
    "/middleware-logging:logging_middleware"
    "/middleware-compression:compression_middleware"
)

# Test endpoints for validation benchmarks
VALIDATION_ENDPOINTS=(
    "/health:health_check"
    "/validation/simple:simple_validation"
    "/validation/user:user_validation"
    "/validation/nested:nested_validation"
    "/validation/complex:complex_validation"
    "/validation/array:array_validation"
    "/validation/performance:performance_test"
)

# Test endpoints for file operations benchmarks
FILE_OPERATIONS_ENDPOINTS=(
    "/health:health_check"
    "/upload/small:small_file_upload"
    "/upload/medium:medium_file_upload"
    "/upload/large:large_file_upload"
    "/download/text:text_file_download"
    "/download/binary:binary_file_download"
    "/static/image:static_image_serve"
    "/stream/data:data_streaming"
)

# Test endpoints for background tasks benchmarks
BACKGROUND_TASKS_ENDPOINTS=(
    "/health:health_check"
    "/task/simple:simple_task"
    "/task/email:email_task"
    "/task/batch:batch_processing"
    "/task/scheduled:scheduled_task"
    "/task/queue:queue_processing"
    "/task/parallel:parallel_tasks"
)

# Test endpoints for async operations benchmarks
ASYNC_OPERATIONS_ENDPOINTS=(
    "/health:health_check"
    "/async/simple:simple_async"
    "/async/db:async_database"
    "/async/http:async_http_client"
    "/async/concurrent:concurrent_operations"
)

# Test endpoints for real-world scenarios benchmarks
REAL_WORLD_ENDPOINTS=(
    "/health:health_check"
    "/api/users:user_crud"
    "/api/products:product_search"
    "/api/orders:order_processing"
    "/api/analytics:analytics_query"
    "/api/complex:complex_business_logic"
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

        # Wait for graceful shutdown with better monitoring
        local stopped=false
        for i in {1..10}; do  # Increased timeout to 10 seconds
            if ! kill -0 "$pid" 2>/dev/null; then
                stopped=true
                break
            fi
            sleep 1
        done

        # Force kill if necessary
        if [ "$stopped" = false ] && kill -0 "$pid" 2>/dev/null; then
            print_warning "Graceful shutdown failed. Force killing $name server..."
            kill -KILL "$pid" 2>/dev/null || true
            sleep 2  # Give it time to fully die
        fi

        # Verify the server is actually stopped
        if ! kill -0 "$pid" 2>/dev/null; then
            print_success "$name server stopped successfully (PID: $pid)"
        else
            print_error "Failed to stop $name server (PID: $pid)"
        fi
    else
        print_warning "Server PID $pid for $name is not running or invalid"
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
    local benchmark_type=${6:-"basic"}  # Add benchmark_type parameter

    # Extract port from appropriate server configuration based on benchmark type
    local servers_to_check=()
    case "$benchmark_type" in
        "basic") servers_to_check=("${BASIC_SERVERS[@]}") ;;
        "di") servers_to_check=("${DI_SERVERS[@]}") ;;
        "sqlalchemy-di") servers_to_check=("${SQLALCHEMY_DI_SERVERS[@]}") ;;
        "middleware") servers_to_check=("${MIDDLEWARE_SERVERS[@]}") ;;
        "validation") servers_to_check=("${VALIDATION_SERVERS[@]}") ;;
        "file-operations") servers_to_check=("${FILE_OPERATIONS_SERVERS[@]}") ;;
        "background-tasks") servers_to_check=("${BACKGROUND_TASKS_SERVERS[@]}") ;;
        "async-operations") servers_to_check=("${ASYNC_OPERATIONS_SERVERS[@]}") ;;
        "real-world") servers_to_check=("${REAL_WORLD_SERVERS[@]}") ;;
        *) servers_to_check=("${BASIC_SERVERS[@]}") ;;
    esac

    for server_config in "${servers_to_check[@]}"; do
        local server_name=${server_config%%:*}
        if [ "$server_name" = "$framework" ]; then
            port=$(echo "$server_config" | cut -d':' -f2)
            break
        fi
    done

    if [ -z "$port" ]; then
        print_error "Port not found for framework: $framework (type: $benchmark_type)"
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
  "benchmark_type": "$benchmark_type",
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
    local benchmark_type=${2:-"basic"}  # Default to basic benchmarks

    print_status "Starting $benchmark_type benchmark for $framework"
    echo "=================================================="

    # Select server configuration and endpoints based on benchmark type
    local servers_array
    local endpoints_array
    local port_offset

    case "$benchmark_type" in
        "basic")
            servers_array=("${BASIC_SERVERS[@]}")
            endpoints_array=("${BASIC_ENDPOINTS[@]}")
            ;;
        "di")
            servers_array=("${DI_SERVERS[@]}")
            endpoints_array=("${DI_ENDPOINTS[@]}")
            ;;
        "sqlalchemy-di")
            servers_array=("${SQLALCHEMY_DI_SERVERS[@]}")
            endpoints_array=("${SQLALCHEMY_DI_ENDPOINTS[@]}")
            ;;
        "middleware")
            servers_array=("${MIDDLEWARE_SERVERS[@]}")
            endpoints_array=("${MIDDLEWARE_ENDPOINTS[@]}")
            ;;
        "validation")
            servers_array=("${VALIDATION_SERVERS[@]}")
            endpoints_array=("${VALIDATION_ENDPOINTS[@]}")
            ;;
        "file-operations")
            servers_array=("${FILE_OPERATIONS_SERVERS[@]}")
            endpoints_array=("${FILE_OPERATIONS_ENDPOINTS[@]}")
            ;;
        "background-tasks")
            servers_array=("${BACKGROUND_TASKS_SERVERS[@]}")
            endpoints_array=("${BACKGROUND_TASKS_ENDPOINTS[@]}")
            ;;
        "async-operations")
            servers_array=("${ASYNC_OPERATIONS_SERVERS[@]}")
            endpoints_array=("${ASYNC_OPERATIONS_ENDPOINTS[@]}")
            ;;
        "real-world")
            servers_array=("${REAL_WORLD_SERVERS[@]}")
            endpoints_array=("${REAL_WORLD_ENDPOINTS[@]}")
            ;;
        *)
            print_error "Unknown benchmark type: $benchmark_type"
            return 1
            ;;
    esac

    # Extract server configuration
    local server_config=""
    local port=""
    local command=""

    for config in "${servers_array[@]}"; do
        local server_name=${config%%:*}
        if [ "$server_name" = "$framework" ]; then
            server_config="$config"
            port=$(echo "$config" | cut -d':' -f2)
            command=$(echo "$config" | cut -d':' -f3-)
            break
        fi
    done

    if [ -z "$server_config" ]; then
        print_error "Server configuration not found for $framework ($benchmark_type)"
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
    local framework_results_created=false

    for endpoint_config in "${endpoints_array[@]}"; do
        local endpoint=${endpoint_config%%:*}
        local endpoint_name=${endpoint_config#*:}

        if run_benchmark "$framework" "$endpoint" "${benchmark_type}_${endpoint_name}" "GET" "" "$benchmark_type"; then
            framework_results_created=true
        else
            all_passed=false
        fi

        sleep 2  # Brief pause between endpoints
    done

    # Stop the server
    if [ -n "$server_pid" ]; then
        stop_server "$server_pid" "$framework"
        rm -f "$RESULTS_DIR/${framework}_server.pid"

        # Additional cleanup: kill any remaining processes on the port
        if check_port "$port"; then
            print_warning "Port $port still in use after stopping server. Cleaning up remaining processes..."
            local remaining_pids=$(lsof -Pi :$port -sTCP:LISTEN -t 2>/dev/null)
            for remaining_pid in $remaining_pids; do
                if [ -n "$remaining_pid" ]; then
                    print_status "Killing remaining process $remaining_pid on port $port"
                    kill -TERM "$remaining_pid" 2>/dev/null || true
                    sleep 1
                    kill -KILL "$remaining_pid" 2>/dev/null || true
                fi
            done
        fi

        # Final verification and cleanup delay
        sleep 3
        if ! check_port "$port"; then
            print_success "$framework server and all child processes stopped (port $port is free)"
        else
            print_warning "$framework server cleanup completed but port $port may still be in use"
        fi
    fi

    if [ "$framework_results_created" = true ]; then
        print_success "Framework $framework benchmarks completed with some successful results"
        if [ "$all_passed" = false ]; then
            print_warning "Some endpoints failed for $framework, but successful results were preserved"
        fi
    else
        print_error "All $benchmark_type benchmarks failed for $framework - no results to save"
    fi

    echo ""
}

# Function to cleanup any running servers
cleanup_servers() {
    print_status "Cleaning up any running benchmark servers..."

    # List of all server configurations
    local all_servers=(
        "${BASIC_SERVERS[@]}"
        "${DI_SERVERS[@]}"
        "${SQLALCHEMY_DI_SERVERS[@]}"
        "${MIDDLEWARE_SERVERS[@]}"
        "${VALIDATION_SERVERS[@]}"
        "${FILE_OPERATIONS_SERVERS[@]}"
        "${BACKGROUND_TASKS_SERVERS[@]}"
        "${ASYNC_OPERATIONS_SERVERS[@]}"
        "${REAL_WORLD_SERVERS[@]}"
    )

    # Cleanup all servers
    for server_config in "${all_servers[@]}"; do
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

# Function to generate summary report with framework-keyed structure
generate_summary() {
    print_status "Generating framework-keyed benchmark summary..."

    local summary_file="$RESULTS_DIR/benchmark_summary.json"
    local summary_md="$RESULTS_DIR/benchmark_summary.md"

    # Load existing summary or create new structure
    local existing_summary=""
    if [ -f "$summary_file" ]; then
        existing_summary=$(cat "$summary_file")
    fi

    # Create new structure with framework-keyed organization
    local temp_file="/tmp/benchmark_summary_new.json"

    # Start building new summary
    cat > "$temp_file" << EOF
{
  "metadata": {
    "created": "$(date -Iseconds)",
    "last_updated": "$(date -Iseconds)",
    "version": "3.0",
    "description": "Catzilla Framework Transparent Benchmarking System - Framework Keyed"
  },
  "categories": {
EOF

    # Get existing categories (excluding current one) to preserve
    local other_categories=""
    if [ -n "$existing_summary" ] && echo "$existing_summary" | jq -e '.categories' >/dev/null 2>&1; then
        other_categories=$(echo "$existing_summary" | jq -r '.categories | keys[]' 2>/dev/null | grep -v "^$BENCHMARK_TYPE$" || true)
    fi

    # Add current benchmark type with framework-keyed structure
    echo "    \"$BENCHMARK_TYPE\": {" >> "$temp_file"
    echo "      \"last_run\": \"$(date -Iseconds)\"," >> "$temp_file"
    echo "      \"test_params\": {" >> "$temp_file"
    echo "        \"duration\": \"$DURATION\"," >> "$temp_file"
    echo "        \"connections\": $CONNECTIONS," >> "$temp_file"
    echo "        \"threads\": $THREADS," >> "$temp_file"
    echo "        \"tool\": \"wrk\"" >> "$temp_file"
    echo "      }," >> "$temp_file"
    echo "      \"results\": {" >> "$temp_file"

    # Initialize framework structure with existing data if available
    local frameworks=("catzilla" "fastapi" "flask" "django")
    local first_framework=true

    for framework in "${frameworks[@]}"; do
        if [ "$first_framework" = false ]; then
            echo "," >> "$temp_file"
        fi
        echo "        \"$framework\": [" >> "$temp_file"

        # Check if this framework has new results for current benchmark type
        local framework_has_new_results=false
        local first_result=true

        for json_file in "$RESULTS_DIR"/*.json; do
            if [ -f "$json_file" ] && [[ "$json_file" != *"summary"* ]] && [[ "$json_file" == *"_${BENCHMARK_TYPE}_"* ]]; then
                # Check if this JSON file is for the current framework
                local file_framework=$(grep '"framework"' "$json_file" 2>/dev/null | head -1 | cut -d'"' -f4 2>/dev/null || echo "")
                if [ "$file_framework" = "$framework" ]; then
                    if [ "$first_result" = false ]; then
                        echo "," >> "$temp_file"
                    fi
                    cat "$json_file" | sed 's/^/          /' >> "$temp_file"
                    first_result=false
                    framework_has_new_results=true
                fi
            fi
        done

        # If no new results for this framework, preserve existing data
        if [ "$framework_has_new_results" = false ] && [ -n "$existing_summary" ]; then
            local existing_framework_data=""
            if echo "$existing_summary" | jq -e ".categories.\"$BENCHMARK_TYPE\".results.\"$framework\"" >/dev/null 2>&1; then
                existing_framework_data=$(echo "$existing_summary" | jq -r ".categories.\"$BENCHMARK_TYPE\".results.\"$framework\"" 2>/dev/null)
                if [ "$existing_framework_data" != "[]" ] && [ "$existing_framework_data" != "null" ]; then
                    echo "$existing_framework_data" | jq -r '.[] | @json' 2>/dev/null | while IFS= read -r result; do
                        if [ "$first_result" = false ]; then
                            echo "," >> "$temp_file"
                        fi
                        echo "$result" | jq '.' | sed 's/^/          /' >> "$temp_file"
                        first_result=false
                    done 2>/dev/null || true
                fi
            fi
        fi

        echo "" >> "$temp_file"
        echo "        ]" >> "$temp_file"
        first_framework=false
    done

    echo "      }" >> "$temp_file"
    echo "    }" >> "$temp_file"

    # Add other existing categories
    if [ -n "$other_categories" ]; then
        for category in $other_categories; do
            echo "," >> "$temp_file"
            echo "    \"$category\": " >> "$temp_file"
            echo "$existing_summary" | jq ".categories.\"$category\"" | sed 's/^/    /' >> "$temp_file"
        done
    fi

    # Close the JSON structure
    echo "" >> "$temp_file"
    echo "  }" >> "$temp_file"
    echo "}" >> "$temp_file"

    # Move the temporary file to final location
    mv "$temp_file" "$summary_file"

    print_success "Framework-keyed benchmark summary saved to: $summary_file"

    # Create category-specific markdown
    generate_category_markdown_report

    print_success "Category-specific reports generated"
}

# Function to generate category-specific markdown reports
generate_category_markdown_report() {
    local category_md="$RESULTS_DIR/${BENCHMARK_TYPE}_performance_report.md"

    cat > "$category_md" << EOF
# Catzilla $(echo ${BENCHMARK_TYPE} | sed 's/./\U&/') Category Performance Report

## Test Configuration
- **Category**: $BENCHMARK_TYPE
- **Duration**: $DURATION
- **Connections**: $CONNECTIONS
- **Threads**: $THREADS
- **Tool**: wrk
- **Date**: $(date)

## Performance Results

| Framework | Endpoint | Requests/sec | Avg Latency | 99% Latency |
|-----------|----------|--------------|-------------|-------------|
EOF

    # Parse JSON results to create table for current category
    for json_file in "$RESULTS_DIR"/*.json; do
        if [ -f "$json_file" ] && [[ "$json_file" != *"summary"* ]] && [[ "$json_file" == *"_${BENCHMARK_TYPE}_"* ]]; then
            local framework=$(grep '"framework"' "$json_file" | cut -d'"' -f4)
            local endpoint=$(grep '"endpoint_name"' "$json_file" | cut -d'"' -f4)
            local rps=$(grep '"requests_per_sec"' "$json_file" | cut -d'"' -f4)
            local avg_lat=$(grep '"avg_latency"' "$json_file" | cut -d'"' -f4)
            local p99_lat=$(grep '"p99_latency"' "$json_file" | cut -d'"' -f4)
            echo "| $framework | $endpoint | $rps | $avg_lat | $p99_lat |" >> "$category_md"
        fi
    done

    echo "" >> "$category_md"
    echo "## Catzilla Performance Advantage" >> "$category_md"
    echo "" >> "$category_md"
    echo "This report shows how Catzilla performs compared to other frameworks in the **$BENCHMARK_TYPE** category." >> "$category_md"

    print_success "Category report saved to: $category_md"
}

# Function to cleanup any running servers
cleanup_servers() {
    print_status "Cleaning up any running benchmark servers..."

    # List of all server configurations
    local all_servers=(
        "${BASIC_SERVERS[@]}"
        "${DI_SERVERS[@]}"
        "${SQLALCHEMY_DI_SERVERS[@]}"
        "${MIDDLEWARE_SERVERS[@]}"
        "${VALIDATION_SERVERS[@]}"
        "${FILE_OPERATIONS_SERVERS[@]}"
        "${BACKGROUND_TASKS_SERVERS[@]}"
        "${ASYNC_OPERATIONS_SERVERS[@]}"
        "${REAL_WORLD_SERVERS[@]}"
    )

    # Cleanup all servers
    for server_config in "${all_servers[@]}"; do
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

# Show usage information
usage() {
    echo "Enhanced Catzilla Benchmark Runner"
    echo ""
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --mode MODE         Benchmark mode: 'direct' (wrk) or 'python' (feature-based)"
    echo "  --type TYPE         Benchmark type (see available types below)"
    echo "  --framework FRAMEWORK    Run specific framework only (catzilla,fastapi,flask,django)"
    echo "  --duration TIME     Test duration (default: 10s)"
    echo "  --connections NUM   Number of connections (default: 100)"
    echo "  --threads NUM       Number of threads (default: 4)"
    echo "  --all              Run all available benchmark types"
    echo "  --help             Show this help message"
    echo ""
    echo "Direct Mode (wrk) Examples:"
    echo "  $0                                          # Run basic benchmarks"
    echo "  $0 --type di                               # Run dependency injection benchmarks"
    echo "  $0 --type sqlalchemy-di                    # Run SQLAlchemy DI benchmarks"
    echo "  $0 --type validation                       # Run validation engine benchmarks"
    echo "  $0 --type middleware                       # Run middleware benchmarks"
    echo "  $0 --framework catzilla --type validation  # Run Catzilla validation only"
    echo "  $0 --all                                   # Run ALL benchmark types"
    echo "  $0 --duration 30s --connections 200        # Custom settings"
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
    echo ""
    echo "Available benchmark types (direct mode):"
    echo "  basic              - Basic HTTP operations (GET, POST, JSON)"
    echo "  di                 - Dependency injection overhead"
    echo "  sqlalchemy-di      - SQLAlchemy with dependency injection"
    echo "  middleware         - Middleware performance"
    echo "  validation         - Input validation engines"
    echo "  file-operations    - File upload/download/streaming"
    echo "  background-tasks   - Background task processing"
    echo "  async-operations   - Async/await operations"
    echo "  real-world         - Real-world API scenarios"
    echo ""
    echo "Available feature categories (python mode):"
    echo "  basic, middleware, dependency_injection, async_operations,"
    echo "  validation, file_operations, background_tasks, real_world_scenarios"
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
    BENCHMARK_TYPE="basic"  # Default benchmark type
    SELECTED_FRAMEWORK=""
    PYTHON_ARGS=""
    RUN_ALL_TYPES=false

    while [[ $# -gt 0 ]]; do
        case $1 in
            --mode)
                MODE="$2"
                shift 2
                ;;
            --type)
                BENCHMARK_TYPE="$2"
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
            --all)
                RUN_ALL_TYPES=true
                shift
                ;;
            --basic|--middleware|--di|--async|--validation|--file-ops|--bg-tasks|--real-world)
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

    # Validate benchmark type
    if [ -n "$BENCHMARK_TYPE" ]; then
        local valid_types=("basic" "di" "sqlalchemy-di" "middleware" "validation" "file-operations" "background-tasks" "async-operations" "real-world")
        local type_valid=false

        for valid_type in "${valid_types[@]}"; do
            if [ "$valid_type" = "$BENCHMARK_TYPE" ]; then
                type_valid=true
                break
            fi
        done

        if [ "$type_valid" = false ]; then
            print_error "Invalid benchmark type: $BENCHMARK_TYPE"
            print_error "Valid types: ${valid_types[*]}"
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
    if [ "$RUN_ALL_TYPES" = true ]; then
        print_header "🚀 Direct wrk Benchmark Mode - ALL TYPES"
        local all_types=("basic" "di" "sqlalchemy-di" "middleware" "validation" "file-operations" "background-tasks" "real-world")
    else
        print_header "🚀 Direct wrk Benchmark Mode - $BENCHMARK_TYPE"
        local all_types=("$BENCHMARK_TYPE")
    fi

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

    # Run benchmarks for each type
    for benchmark_type in "${all_types[@]}"; do
        print_header "Starting $benchmark_type benchmarks..."

        # Determine which frameworks to test based on benchmark type
        local frameworks_to_test
        if [ -n "$SELECTED_FRAMEWORK" ]; then
            frameworks_to_test=("$SELECTED_FRAMEWORK")
        else
            case "$benchmark_type" in
                "basic")
                    frameworks_to_test=("catzilla" "fastapi" "flask" "django")
                    ;;
                "di")
                    frameworks_to_test=("catzilla" "fastapi" "django")  # Only these have DI servers
                    ;;
                "sqlalchemy-di")
                    frameworks_to_test=("catzilla" "fastapi" "flask")  # These have SQLAlchemy DI servers
                    ;;
                "middleware")
                    frameworks_to_test=("catzilla" "fastapi" "django")  # These have middleware servers
                    ;;
                "validation")
                    frameworks_to_test=("catzilla" "fastapi" "flask" "django")  # All have validation servers
                    ;;
                "file-operations")
                    frameworks_to_test=("catzilla" "fastapi" "flask" "django")  # All have file servers
                    ;;
                "background-tasks")
                    frameworks_to_test=("catzilla" "fastapi" "flask" "django")  # All have task servers
                    ;;
                "async-operations")
                    frameworks_to_test=("django")  # Only Django async server available
                    ;;
                "real-world")
                    frameworks_to_test=("catzilla" "fastapi")  # These have real-world servers
                    ;;
                *)
                    frameworks_to_test=("catzilla" "fastapi" "flask" "django")
                    ;;
            esac
        fi

        print_status "Testing frameworks: ${frameworks_to_test[*]} (type: $benchmark_type)"
        echo ""

        # Run benchmarks for each framework
        for framework in "${frameworks_to_test[@]}"; do
            if benchmark_framework "$framework" "$benchmark_type"; then
                print_success "Successfully completed $framework benchmarks"
                # Generate summary after each successful framework to preserve results
                generate_summary
            else
                print_error "Failed to complete $framework benchmarks, but continuing with others..."
            fi
            sleep 3  # Pause between frameworks
        done

        if [ "$RUN_ALL_TYPES" = true ] && [ "$benchmark_type" != "${all_types[-1]}" ]; then
            print_status "Completed $benchmark_type benchmarks. Moving to next type..."
            echo ""
            sleep 5  # Longer pause between benchmark types
        fi
    done

    # Generate final summary
    generate_summary

    if [ "$RUN_ALL_TYPES" = true ]; then
        print_success "All benchmark types completed!"
    else
        print_success "All $BENCHMARK_TYPE benchmarks completed!"
    fi
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
