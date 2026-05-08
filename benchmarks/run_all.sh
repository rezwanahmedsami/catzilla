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

if [ -d "$PROJECT_ROOT/.venv" ]; then
    VENV_PATH="$PROJECT_ROOT/.venv"
elif [ -d "$PROJECT_ROOT/venv" ]; then
    VENV_PATH="$PROJECT_ROOT/venv"
else
    VENV_PATH="$PROJECT_ROOT/.venv"
fi

PYTHON_CMD="python3"
UVICORN_CMD="uvicorn"
GUNICORN_CMD="gunicorn"
GUNICORN_WSGI_FLAGS="--worker-class gthread --threads 8 --keep-alive 30 --timeout 120"

if [ -x "$VENV_PATH/bin/python" ]; then
    PYTHON_CMD="$VENV_PATH/bin/python"
fi
if [ -x "$VENV_PATH/bin/uvicorn" ]; then
    UVICORN_CMD="$VENV_PATH/bin/uvicorn"
fi
if [ -x "$VENV_PATH/bin/gunicorn" ]; then
    GUNICORN_CMD="$VENV_PATH/bin/gunicorn"
fi

# Create results directory
mkdir -p "$RESULTS_DIR"

# Benchmark settings
DURATION="10s"          # Duration of each test
CONNECTIONS="100"       # Total connections in single mode; per-worker connections in multi mode
CONNECTIONS_PER_WORKER="100"
THREADS="4"             # Number of threads to use
WARMUP_TIME="3s"        # Warmup duration
WORKER_MODE="single"    # HTTP worker mode for direct basic benchmarks
WORKERS="1"             # Number of HTTP worker processes in multi mode
WORKERS_EXPLICIT=false

BASIC_MULTI_CATZILLA_BACKEND_BASE_PORT="8100"
BASIC_MULTI_CATZILLA_MAX_WORKERS="16"

# Server configurations for basic benchmarks are generated dynamically by worker mode.
BASIC_SERVERS=()

# Server configurations for dependency injection benchmarks
DI_SERVERS=(
    "catzilla:8010:$PYTHON_CMD $SERVERS_DIR/dependency_injection/catzilla_di.py --port 8010"
    "fastapi:8011:$UVICORN_CMD benchmarks.servers.dependency_injection.fastapi_di:app --host 127.0.0.1 --port 8011"
    "django:8012:$GUNICORN_CMD --bind 127.0.0.1:8012 --workers 4 $GUNICORN_WSGI_FLAGS benchmarks.servers.dependency_injection.django_di:application"
)

# Server configurations for SQLAlchemy DI benchmarks
SQLALCHEMY_DI_SERVERS=(
    "catzilla:8020:$PYTHON_CMD $SERVERS_DIR/dependency_injection/catzilla_sqlalchemy_di.py --port 8020"
    "fastapi:8021:$UVICORN_CMD benchmarks.servers.dependency_injection.fastapi_sqlalchemy_di:app --host 127.0.0.1 --port 8021"
    "flask:8022:$GUNICORN_CMD --bind 127.0.0.1:8022 --workers 4 $GUNICORN_WSGI_FLAGS benchmarks.servers.dependency_injection.flask_sqlalchemy_di:app"
)

# Server configurations for middleware benchmarks
MIDDLEWARE_SERVERS=(
    "catzilla:8030:$PYTHON_CMD $SERVERS_DIR/middleware/catzilla_middleware.py --port 8030"
    "fastapi:8031:$UVICORN_CMD benchmarks.servers.middleware.fastapi_middleware:app --host 127.0.0.1 --port 8031"
    "flask:8033:$GUNICORN_CMD --bind 127.0.0.1:8033 --workers 4 $GUNICORN_WSGI_FLAGS benchmarks.servers.middleware.flask_middleware:app"
    "django:8032:$GUNICORN_CMD --bind 127.0.0.1:8032 --workers 4 $GUNICORN_WSGI_FLAGS benchmarks.servers.middleware.django_middleware:application"
)

# Server configurations for validation benchmarks
VALIDATION_SERVERS=(
    "catzilla:8040:$PYTHON_CMD $SERVERS_DIR/validation/catzilla_validation.py --port 8040"
    "fastapi:8041:$UVICORN_CMD benchmarks.servers.validation.fastapi_validation:app --host 127.0.0.1 --port 8041"
    "flask:8042:$GUNICORN_CMD --bind 127.0.0.1:8042 --workers 4 $GUNICORN_WSGI_FLAGS benchmarks.servers.validation.flask_validation:app"
    "django:8043:$GUNICORN_CMD --bind 127.0.0.1:8043 --workers 4 $GUNICORN_WSGI_FLAGS benchmarks.servers.validation.django_validation:application"
)

# Server configurations for file operations benchmarks
FILE_OPERATIONS_SERVERS=(
    "catzilla:8050:$PYTHON_CMD $SERVERS_DIR/file_operations/catzilla_file.py --port 8050"
    "fastapi:8051:$UVICORN_CMD benchmarks.servers.file_operations.fastapi_file:app --host 127.0.0.1 --port 8051"
    "flask:8052:$GUNICORN_CMD --bind 127.0.0.1:8052 --workers 4 $GUNICORN_WSGI_FLAGS benchmarks.servers.file_operations.flask_file:app"
    "django:8053:$GUNICORN_CMD --bind 127.0.0.1:8053 --workers 4 $GUNICORN_WSGI_FLAGS benchmarks.servers.file_operations.django_file:application"
)

# Server configurations for background tasks benchmarks
BACKGROUND_TASKS_SERVERS=(
    "catzilla:8060:$PYTHON_CMD $SERVERS_DIR/background_tasks/catzilla_tasks.py --port 8060"
    "fastapi:8061:$UVICORN_CMD benchmarks.servers.background_tasks.fastapi_tasks:app --host 127.0.0.1 --port 8061"
    "flask:8062:$GUNICORN_CMD --bind 127.0.0.1:8062 --workers 4 $GUNICORN_WSGI_FLAGS benchmarks.servers.background_tasks.flask_tasks:app"
    "django:8063:$GUNICORN_CMD --bind 127.0.0.1:8063 --workers 4 $GUNICORN_WSGI_FLAGS benchmarks.servers.background_tasks.django_tasks:application"
)

# Server configurations for real-world scenarios benchmarks
REAL_WORLD_SERVERS=(
    "catzilla:8080:$PYTHON_CMD $SERVERS_DIR/real_world_scenarios/catzilla_realworld.py --port 8080"
    "fastapi:8081:$UVICORN_CMD benchmarks.servers.real_world_scenarios.fastapi_realworld:app --host 127.0.0.1 --port 8081"
    "django:8082:$GUNICORN_CMD --bind 127.0.0.1:8082 --workers 4 $GUNICORN_WSGI_FLAGS benchmarks.servers.real_world_scenarios.django_realworld:application"
    "flask:8083:$GUNICORN_CMD --bind 127.0.0.1:8083 --workers 4 $GUNICORN_WSGI_FLAGS benchmarks.servers.real_world_scenarios.flask_realworld:app"
)

# Server configurations for async operations benchmarks
ASYNC_OPERATIONS_SERVERS=(
    "catzilla:8070:$PYTHON_CMD $SERVERS_DIR/async_operations/catzilla_async.py --port 8070"
    "fastapi:8071:$UVICORN_CMD benchmarks.servers.async_operations.fastapi_async:app --host 127.0.0.1 --port 8071"
    "django:8072:$UVICORN_CMD benchmarks.servers.async_operations.django_async:application --host 127.0.0.1 --port 8072"
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
    "/health:health_check"
    "/di/simple:simple_di"
    "/di/request:request_scoped_di"
    "/di/transient:transient_di"
    "/di/complex:complex_di_chain"
)

# Test endpoints for SQLAlchemy DI benchmarks
SQLALCHEMY_DI_ENDPOINTS=(
    "/health:health_check"
    "/users:db_users_list"
    "/users/1:db_user_detail"
    "/posts:db_posts_list"
    "/posts/by-user/1:db_posts_by_user"
    "/analytics/transient-test:transient_analytics"
    "/di-complex-chain:complex_di_chain"
)

# Test endpoints for middleware benchmarks
MIDDLEWARE_ENDPOINTS=(
    "/:home"
    "/health:health_check"
    "/middleware-light:light_middleware"
    "/middleware-heavy:heavy_middleware"
    "/middleware-auth:auth_middleware"
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
    "/files/list:file_listing"
)

# Test endpoints for background tasks benchmarks
BACKGROUND_TASKS_ENDPOINTS=(
    "/health:health_check"
    "/tasks:task_listing"
    "/queue/stats:queue_stats"
)

# Test endpoints for real-world scenarios benchmarks
REAL_WORLD_ENDPOINTS=(
    "/health:health_check"
    "/api/products:product_search"
    "/api/products/1:product_detail"
    "/api/blog/posts:blog_listing"
    "/api/blog/posts/1:blog_post_detail"
)

# Test endpoints for async operations benchmarks
ASYNC_OPERATIONS_ENDPOINTS=(
    "/async/raw:raw_async"
    "/async/yield-once:yield_once"
    "/async/fanout:fanout_async"
    "/async/chain/42:chain_async"
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

get_basic_server_configs() {
    local effective_workers=1
    if [ "$WORKER_MODE" = "multi" ]; then
        effective_workers=$WORKERS
    fi

    local catzilla_command="$PYTHON_CMD $SERVERS_DIR/basic/catzilla_server.py --host 127.0.0.1 --port 8000"
    local catzilla_port=8000
    if [ "$WORKER_MODE" = "multi" ]; then
        catzilla_port=$BASIC_MULTI_CATZILLA_BACKEND_BASE_PORT
        catzilla_command="$PYTHON_CMD $BENCHMARK_DIR/tools/multi_worker_proxy.py --host 127.0.0.1 --backend-base-port $BASIC_MULTI_CATZILLA_BACKEND_BASE_PORT --workers $WORKERS --worker-command '$PYTHON_CMD $SERVERS_DIR/basic/catzilla_server.py --host 127.0.0.1 --port {port}'"
    fi

    cat << EOF
catzilla:$catzilla_port:$catzilla_command
fastapi:8001:$UVICORN_CMD benchmarks.servers.basic.fastapi_server:app --host 127.0.0.1 --port 8001 --workers $effective_workers --no-access-log --log-level warning
flask:8002:$GUNICORN_CMD --bind 127.0.0.1:8002 --workers $effective_workers $GUNICORN_WSGI_FLAGS benchmarks.servers.basic.flask_server:app
django:8003:$GUNICORN_CMD --bind 127.0.0.1:8003 --workers $effective_workers $GUNICORN_WSGI_FLAGS benchmarks.servers.basic.django_server:application
EOF
}

get_server_configs_for_type() {
    local benchmark_type=$1
    case "$benchmark_type" in
        "basic") get_basic_server_configs ;;
        "di") printf "%s\n" "${DI_SERVERS[@]}" ;;
        "sqlalchemy-di") printf "%s\n" "${SQLALCHEMY_DI_SERVERS[@]}" ;;
        "middleware") printf "%s\n" "${MIDDLEWARE_SERVERS[@]}" ;;
        "validation") printf "%s\n" "${VALIDATION_SERVERS[@]}" ;;
        "async-operations") printf "%s\n" "${ASYNC_OPERATIONS_SERVERS[@]}" ;;
        "file-operations") printf "%s\n" "${FILE_OPERATIONS_SERVERS[@]}" ;;
        "background-tasks") printf "%s\n" "${BACKGROUND_TASKS_SERVERS[@]}" ;;
        "real-world") printf "%s\n" "${REAL_WORLD_SERVERS[@]}" ;;
        *) return 1 ;;
    esac
}

detect_default_worker_count() {
    local detected_workers=""

    if command -v nproc >/dev/null 2>&1; then
        detected_workers=$(nproc 2>/dev/null || true)
    elif command -v sysctl >/dev/null 2>&1; then
        detected_workers=$(sysctl -n hw.logicalcpu 2>/dev/null || true)
    elif command -v getconf >/dev/null 2>&1; then
        detected_workers=$(getconf _NPROCESSORS_ONLN 2>/dev/null || true)
    fi

    if ! [[ "$detected_workers" =~ ^[0-9]+$ ]] || [ "$detected_workers" -lt 2 ]; then
        detected_workers="2"
    fi

    echo "$detected_workers"
}

apply_connection_mode_settings() {
    if [ "$WORKER_MODE" = "multi" ]; then
        CONNECTIONS_PER_WORKER="$CONNECTIONS"
        CONNECTIONS="$((CONNECTIONS_PER_WORKER * WORKERS))"
    else
        CONNECTIONS_PER_WORKER="$CONNECTIONS"
    fi
}

format_connection_summary() {
    if [ "$WORKER_MODE" = "multi" ]; then
        echo "$CONNECTIONS total (${CONNECTIONS_PER_WORKER}/worker)"
    else
        echo "$CONNECTIONS"
    fi
}

format_requested_thread_summary() {
    if [ "$WORKER_MODE" = "multi" ]; then
        echo "$THREADS requested"
    else
        echo "$THREADS"
    fi
}

find_server_config() {
    local benchmark_type=$1
    local framework=$2
    local config=""
    local normalized_config=""

    while IFS= read -r config; do
        normalized_config="${config//$'\r'/}"
        normalized_config="${normalized_config#"${normalized_config%%[![:space:]]*}"}"

        if [ -n "$normalized_config" ] && [ "${normalized_config%%:*}" = "$framework" ]; then
            printf "%s\n" "$normalized_config"
            return 0
        fi
    done <<< "$(get_server_configs_for_type "$benchmark_type")"

    return 1
}

result_worker_suffix() {
    if [ "$WORKER_MODE" = "multi" ]; then
        echo "multi_${WORKERS}w"
    else
        echo "single_1w"
    fi
}

latency_to_ms() {
    local latency_value=$1
    if [ -z "$latency_value" ]; then
        echo "0"
        return
    fi

    local numeric=$(echo "$latency_value" | sed -E 's/^([0-9.]+).*/\1/')
    local unit=$(echo "$latency_value" | sed -E 's/^[0-9.]+([[:alpha:]]*).*/\1/' | tr '[:upper:]' '[:lower:]')

    case "$unit" in
        "us") awk -v value="$numeric" 'BEGIN { printf "%.6f", value / 1000 }' ;;
        "ms"|"") awk -v value="$numeric" 'BEGIN { printf "%.6f", value }' ;;
        "s") awk -v value="$numeric" 'BEGIN { printf "%.6f", value * 1000 }' ;;
        "m") awk -v value="$numeric" 'BEGIN { printf "%.6f", value * 60000 }' ;;
        *) echo "0" ;;
    esac
}

format_ms_latency() {
    local latency_ms=$1
    awk -v value="$latency_ms" 'BEGIN { printf "%.2fms", value + 0 }'
}

transfer_to_bytes_per_sec() {
    local transfer_value=$1
    if [ -z "$transfer_value" ]; then
        echo "0"
        return
    fi

    local numeric=$(echo "$transfer_value" | sed -E 's/^([0-9.]+).*/\1/')
    local unit=$(echo "$transfer_value" | sed -E 's/^[0-9.]+([[:alpha:]]*).*/\1/' | tr '[:lower:]' '[:upper:]')

    case "$unit" in
        "B"|"") awk -v value="$numeric" 'BEGIN { printf "%.6f", value }' ;;
        "KB") awk -v value="$numeric" 'BEGIN { printf "%.6f", value * 1024 }' ;;
        "MB") awk -v value="$numeric" 'BEGIN { printf "%.6f", value * 1024 * 1024 }' ;;
        "GB") awk -v value="$numeric" 'BEGIN { printf "%.6f", value * 1024 * 1024 * 1024 }' ;;
        *) echo "0" ;;
    esac
}

format_transfer_per_sec() {
    local bytes_per_sec=$1
    awk -v bytes="$bytes_per_sec" '
        BEGIN {
            value = bytes + 0
            unit = "B"
            if (value >= 1024 * 1024 * 1024) {
                value = value / (1024 * 1024 * 1024)
                unit = "GB"
            } else if (value >= 1024 * 1024) {
                value = value / (1024 * 1024)
                unit = "MB"
            } else if (value >= 1024) {
                value = value / 1024
                unit = "KB"
            }
            printf "%.2f%s", value, unit
        }
    '
}

sum_process_tree_rss_kb() {
    local root_pid=$1

    if [ -z "$root_pid" ] || ! kill -0 "$root_pid" 2>/dev/null; then
        echo "0"
        return
    fi

    local -a pending_pids
    local -a collected_pids
    local total_rss_kb=0
    local current_pid=""
    local child_pid=""
    local rss_kb=""

    pending_pids=("$root_pid")
    collected_pids=("$root_pid")

    while [ ${#pending_pids[@]} -gt 0 ]; do
        current_pid="${pending_pids[1]}"
        pending_pids=("${pending_pids[@]:1}")

        while IFS= read -r child_pid; do
            if [ -n "$child_pid" ]; then
                collected_pids+=("$child_pid")
                pending_pids+=("$child_pid")
            fi
        done < <(pgrep -P "$current_pid" 2>/dev/null || true)
    done

    for current_pid in "${collected_pids[@]}"; do
        rss_kb=$(ps -o rss= -p "$current_pid" 2>/dev/null | awk '{sum += $1} END {print sum + 0}')
        total_rss_kb=$((total_rss_kb + ${rss_kb:-0}))
    done

    echo "$total_rss_kb"
}

start_memory_monitor() {
    local root_pid=$1
    local output_file=$2
    local sample_interval="${3:-0.2}"

    (
        local peak_rss_kb=0
        local current_rss_kb=0

        while kill -0 "$root_pid" 2>/dev/null; do
            current_rss_kb=$(sum_process_tree_rss_kb "$root_pid")
            if [ "$current_rss_kb" -gt "$peak_rss_kb" ]; then
                peak_rss_kb="$current_rss_kb"
            fi
            sleep "$sample_interval"
        done

        echo "$peak_rss_kb" > "$output_file"
    ) &

    MEMORY_MONITOR_PID="$!"
}

stop_memory_monitor() {
    local monitor_pid=$1
    local output_file=$2
    local root_pid=$3
    local final_rss_kb="0"

    final_rss_kb=$(sum_process_tree_rss_kb "$root_pid")

    if [ -n "$monitor_pid" ] && kill -0 "$monitor_pid" 2>/dev/null; then
        kill -TERM "$monitor_pid" 2>/dev/null || true
        wait "$monitor_pid" 2>/dev/null || true
    fi

    if [ -f "$output_file" ]; then
        local peak_rss_kb=$(cat "$output_file" 2>/dev/null || echo "0")
        rm -f "$output_file"
        if [ "$final_rss_kb" -gt "$peak_rss_kb" ]; then
            echo "$final_rss_kb"
        else
            echo "$peak_rss_kb"
        fi
    else
        echo "$final_rss_kb"
    fi
}

format_memory_mb() {
    local rss_kb=$1
    awk -v value="$rss_kb" 'BEGIN { printf "%.2f", (value + 0) / 1024 }'
}

write_benchmark_json() {
    local json_file=$1
    local framework=$2
    local endpoint=$3
    local endpoint_name=$4
    local benchmark_type=$5
    local method=$6
    local requests_per_sec=$7
    local avg_latency=$8
    local p99_latency=$9
    local transfer_per_sec=${10}
    local requested_threads=${11:-$THREADS}
    local effective_threads=${12:-$requested_threads}
    local peak_memory_mb=${13:-0}

    cat > "$json_file" << EOF
{
  "framework": "$framework",
  "endpoint": "$endpoint",
  "endpoint_name": "$endpoint_name",
  "benchmark_type": "$benchmark_type",
  "method": "$method",
  "worker_mode": "$WORKER_MODE",
  "workers": $WORKERS,
  "duration": "$DURATION",
  "connections": $CONNECTIONS,
    "connections_per_worker": $CONNECTIONS_PER_WORKER,
    "threads": $effective_threads,
    "requested_threads": $requested_threads,
    "peak_memory_mb": $peak_memory_mb,
  "requests_per_sec": "${requests_per_sec:-0}",
  "avg_latency": "$avg_latency",
  "p99_latency": "$p99_latency",
  "transfer_per_sec": "$transfer_per_sec",
  "timestamp": "$(date -Iseconds)"
}
EOF
}

run_multiworker_catzilla_benchmark() {
    local endpoint=$1
    local endpoint_name=$2
    local method=$3
    local post_data=$4
    local benchmark_type=$5
    local worker_suffix=$(result_worker_suffix)
    local result_file="$RESULTS_DIR/catzilla_${endpoint_name}_${worker_suffix}.txt"
    local json_file="$RESULTS_DIR/catzilla_${endpoint_name}_${worker_suffix}.json"
    local server_pid=$(cat "$RESULTS_DIR/catzilla_server.pid" 2>/dev/null || echo "")
    local worker_connections=$CONNECTIONS_PER_WORKER
    local effective_threads=$THREADS
    local base_worker_threads=1
    local extra_worker_threads=0

    if [ "$worker_connections" -lt 1 ]; then
        worker_connections=1
    fi
    if [ "$effective_threads" -lt "$WORKERS" ]; then
        effective_threads=$WORKERS
    fi

    base_worker_threads=$(( effective_threads / WORKERS ))
    extra_worker_threads=$(( effective_threads % WORKERS ))

    local worker_ports=()
    for ((worker_index = 0; worker_index < WORKERS; worker_index++)); do
        worker_ports+=("$((BASIC_MULTI_CATZILLA_BACKEND_BASE_PORT + worker_index))")
    done

    for worker_port in "${worker_ports[@]}"; do
        local worker_url="http://127.0.0.1:${worker_port}${endpoint}"
        print_status "Warming up catzilla worker on port ${worker_port}..."
        if [ "$method" = "POST" ] && [ -n "$post_data" ]; then
            local warmup_lua="$RESULTS_DIR/temp_catzilla_${endpoint_name}_${worker_port}_warmup.lua"
            cat > "$warmup_lua" << EOF
wrk.method = "POST"
wrk.body = '$post_data'
wrk.headers["Content-Type"] = "application/json"
EOF
            wrk -t1 -c5 -d"$WARMUP_TIME" -s "$warmup_lua" "$worker_url" >/dev/null 2>&1 || true
            rm -f "$warmup_lua"
        else
            wrk -t1 -c5 -d"$WARMUP_TIME" "$worker_url" >/dev/null 2>&1 || true
        fi

        local preflight_status=$(/usr/bin/curl -s -o /dev/null -w "%{http_code}" "$worker_url")
        if [[ ! "$preflight_status" =~ ^2[0-9][0-9]$ ]]; then
            print_error "Skipping catzilla - $endpoint_name: worker on port $worker_port returned HTTP $preflight_status"
            return 1
        fi
    done

    print_status "Running aggregated multi-worker benchmark across ${WORKERS} catzilla worker processes..."
    print_status "Requested wrk threads: ${THREADS}; effective wrk threads: ${effective_threads}"

    local memory_stats_file="$RESULTS_DIR/catzilla_${endpoint_name}_${worker_suffix}.memory"
    local memory_monitor_pid=""
    local peak_memory_kb="0"
    local peak_memory_mb="0"

    if [ -n "$server_pid" ]; then
        start_memory_monitor "$server_pid" "$memory_stats_file"
        memory_monitor_pid="$MEMORY_MONITOR_PID"
    fi

    local worker_result_files=()
    local worker_pids=()
    local worker_lua_files=()
    local worker_index=0
    for worker_port in "${worker_ports[@]}"; do
        local worker_url="http://127.0.0.1:${worker_port}${endpoint}"
        local worker_result_file="$RESULTS_DIR/catzilla_${endpoint_name}_${worker_suffix}_${worker_port}.wrk.txt"
        local worker_threads=$base_worker_threads

        if [ "$worker_index" -lt "$extra_worker_threads" ]; then
            worker_threads=$((worker_threads + 1))
        fi

        worker_result_files+=("$worker_result_file")

        if [ "$method" = "POST" ] && [ -n "$post_data" ]; then
            local worker_lua="$RESULTS_DIR/temp_catzilla_${endpoint_name}_${worker_port}.lua"
            worker_lua_files+=("$worker_lua")
            cat > "$worker_lua" << EOF
wrk.method = "POST"
wrk.body = '$post_data'
wrk.headers["Content-Type"] = "application/json"
EOF
            wrk -t"$worker_threads" -c"$worker_connections" -d"$DURATION" --latency -s "$worker_lua" "$worker_url" > "$worker_result_file" 2>&1 &
        else
            wrk -t"$worker_threads" -c"$worker_connections" -d"$DURATION" --latency "$worker_url" > "$worker_result_file" 2>&1 &
        fi
        worker_pids+=("$!")
        worker_index=$((worker_index + 1))
    done

    local all_wrk_succeeded=true
    for worker_pid in "${worker_pids[@]}"; do
        if ! wait "$worker_pid"; then
            all_wrk_succeeded=false
        fi
    done

    if [ -n "$server_pid" ]; then
        peak_memory_kb=$(stop_memory_monitor "$memory_monitor_pid" "$memory_stats_file" "$server_pid")
        peak_memory_mb=$(format_memory_mb "$peak_memory_kb")
    fi

    for worker_lua in "${worker_lua_files[@]}"; do
        rm -f "$worker_lua"
    done

    if [ "$all_wrk_succeeded" = false ]; then
        print_error "One or more worker-local wrk processes failed for catzilla - $endpoint_name"
        return 1
    fi

    local total_rps=0
    local weighted_avg_latency_sum=0
    local max_p99_latency_ms=0
    local total_transfer_bytes=0

    for worker_result_file in "${worker_result_files[@]}"; do
        local invalid_responses=$(grep "Non-2xx or 3xx responses:" "$worker_result_file" | awk '{print $5}' | head -1)
        if [ -n "$invalid_responses" ] && [ "$invalid_responses" != "0" ]; then
            print_error "Benchmark produced $invalid_responses invalid responses in worker-local run: $worker_result_file"
            return 1
        fi

        local worker_rps=$(grep "Requests/sec:" "$worker_result_file" | awk '{print $2}' | head -1)
        local worker_avg_latency=$(grep "Latency" "$worker_result_file" | awk '{print $2}' | head -1)
        local worker_p99_latency=$(grep "99%" "$worker_result_file" | awk '{print $2}' | head -1)
        local worker_transfer=$(grep "Transfer/sec:" "$worker_result_file" | awk '{print $2}' | head -1)

        local worker_avg_latency_ms=$(latency_to_ms "$worker_avg_latency")
        local worker_p99_latency_ms=$(latency_to_ms "$worker_p99_latency")
        local worker_transfer_bytes=$(transfer_to_bytes_per_sec "$worker_transfer")

        total_rps=$(awk -v total="$total_rps" -v current="${worker_rps:-0}" 'BEGIN { printf "%.6f", total + current }')
        weighted_avg_latency_sum=$(awk -v total="$weighted_avg_latency_sum" -v latency="$worker_avg_latency_ms" -v current="${worker_rps:-0}" 'BEGIN { printf "%.6f", total + (latency * current) }')
        total_transfer_bytes=$(awk -v total="$total_transfer_bytes" -v current="$worker_transfer_bytes" 'BEGIN { printf "%.6f", total + current }')

        if awk -v current="$worker_p99_latency_ms" -v maximum="$max_p99_latency_ms" 'BEGIN { exit !(current > maximum) }'; then
            max_p99_latency_ms=$worker_p99_latency_ms
        fi
    done

    if awk -v total="$total_rps" 'BEGIN { exit !(total <= 0) }'; then
        print_error "Aggregated multi-worker benchmark produced zero requests/sec for catzilla - $endpoint_name"
        return 1
    fi

    local aggregate_avg_latency_ms=$(awk -v total="$weighted_avg_latency_sum" -v rps="$total_rps" 'BEGIN { printf "%.6f", total / rps }')
    local aggregate_avg_latency=$(format_ms_latency "$aggregate_avg_latency_ms")
    local aggregate_p99_latency=$(format_ms_latency "$max_p99_latency_ms")
    local aggregate_transfer=$(format_transfer_per_sec "$total_transfer_bytes")
    local total_rps_display=$(awk -v value="$total_rps" 'BEGIN { printf "%.2f", value }')

    cat > "$result_file" << EOF
Multi-worker aggregate benchmark for catzilla
Worker mode: $WORKER_MODE
Workers: $WORKERS
Requested Threads: $THREADS
Effective wrk Threads: $effective_threads
Endpoint: $endpoint
Requests/sec: $total_rps_display
Latency $aggregate_avg_latency
99% $aggregate_p99_latency
Transfer/sec: $aggregate_transfer
Peak Memory: ${peak_memory_mb}MB
EOF

    write_benchmark_json "$json_file" "catzilla" "$endpoint" "$endpoint_name" "$benchmark_type" "$method" "$total_rps_display" "$aggregate_avg_latency" "$aggregate_p99_latency" "$aggregate_transfer" "$THREADS" "$effective_threads" "$peak_memory_mb"

    print_success "Benchmark completed for catzilla - $endpoint_name"
    print_success "Results saved: $result_file, $json_file"
    echo "  Requests/sec: $total_rps_display"
    echo "  Avg Latency: $aggregate_avg_latency"
    echo "  99% Latency: $aggregate_p99_latency"
    echo "  Peak Memory: ${peak_memory_mb}MB"
    return 0
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
    local log_file="$RESULTS_DIR/${framework}_server.log"

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

    # Activate virtual environment if it exists
    if [ -f "$VENV_PATH/bin/activate" ]; then
        source "$VENV_PATH/bin/activate"
    fi

    # Start the server in its own session so benchmark-side shells and wrk
    # do not forward terminal signals into Gunicorn/Uvicorn worker trees.
    local server_pid=$(
        SERVER_LAUNCH_COMMAND="$command" \
        SERVER_LAUNCH_LOG="$log_file" \
        SERVER_LAUNCH_CWD="$PROJECT_ROOT" \
        "$PYTHON_CMD" - <<'PY'
import os
import subprocess

command = os.environ["SERVER_LAUNCH_COMMAND"]
log_path = os.environ["SERVER_LAUNCH_LOG"]
cwd = os.environ["SERVER_LAUNCH_CWD"]

with open(log_path, "wb") as handle:
    process = subprocess.Popen(
        command,
        cwd=cwd,
        shell=True,
        executable="/bin/zsh",
        stdin=subprocess.DEVNULL,
        stdout=handle,
        stderr=subprocess.STDOUT,
        start_new_session=True,
    )

print(process.pid)
PY
    )

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

    local server_config=""
    server_config=$(find_server_config "$benchmark_type" "$framework" || true)
    if [ -n "$server_config" ]; then
        port=$(echo "$server_config" | cut -d':' -f2)
    fi

    if [ -z "$port" ]; then
        print_error "Port not found for framework: $framework (type: $benchmark_type)"
        return 1
    fi

    local url="http://$host:$port$endpoint"

    print_status "Benchmarking $framework - $endpoint_name ($endpoint)"

    if [ "$framework" = "catzilla" ] && [ "$benchmark_type" = "basic" ] && [ "$WORKER_MODE" = "multi" ]; then
        run_multiworker_catzilla_benchmark "$endpoint" "$endpoint_name" "$method" "$post_data" "$benchmark_type"
        return $?
    fi

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

    local preflight_status=$(curl -s -o /dev/null -w "%{http_code}" "$url")
    if [[ ! "$preflight_status" =~ ^2[0-9][0-9]$ ]]; then
        print_error "Skipping $framework - $endpoint_name: preflight returned HTTP $preflight_status"
        return 1
    fi

    # Main benchmark
    local worker_suffix=$(result_worker_suffix)
    local result_file="$RESULTS_DIR/${framework}_${endpoint_name}_${worker_suffix}.txt"
    local json_file="$RESULTS_DIR/${framework}_${endpoint_name}_${worker_suffix}.json"
    local server_pid=$(cat "$RESULTS_DIR/${framework}_server.pid" 2>/dev/null || echo "")
    local memory_stats_file="$RESULTS_DIR/${framework}_${endpoint_name}_${worker_suffix}.memory"
    local memory_monitor_pid=""
    local peak_memory_kb="0"
    local peak_memory_mb="0"

    print_status "Running main benchmark..."

    if [ -n "$server_pid" ]; then
        start_memory_monitor "$server_pid" "$memory_stats_file"
        memory_monitor_pid="$MEMORY_MONITOR_PID"
    fi

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

    if [ -n "$server_pid" ]; then
        peak_memory_kb=$(stop_memory_monitor "$memory_monitor_pid" "$memory_stats_file" "$server_pid")
        peak_memory_mb=$(format_memory_mb "$peak_memory_kb")
    fi

    if [ "$wrk_success" = true ]; then
        local invalid_responses=$(grep "Non-2xx or 3xx responses:" "$result_file" | awk '{print $5}' | head -1)
        if [ -n "$invalid_responses" ] && [ "$invalid_responses" != "0" ]; then
            print_error "Benchmark produced $invalid_responses invalid responses for $framework - $endpoint_name"
            return 1
        fi

        print_success "Benchmark completed for $framework - $endpoint_name"

        # Extract key metrics and save as JSON
        local requests_per_sec=$(grep "Requests/sec:" "$result_file" | awk '{print $2}' | head -1)
        local avg_latency=$(grep "Latency" "$result_file" | awk '{print $2}' | head -1)
        local p99_latency=$(grep "99%" "$result_file" | awk '{print $2}' | head -1)
        local transfer_per_sec=$(grep "Transfer/sec:" "$result_file" | awk '{print $2}' | head -1)

            write_benchmark_json "$json_file" "$framework" "$endpoint" "$endpoint_name" "$benchmark_type" "$method" "${requests_per_sec:-0}" "$avg_latency" "$p99_latency" "$transfer_per_sec" "$THREADS" "$THREADS" "$peak_memory_mb"

        print_success "Results saved: $result_file, $json_file"
        echo "  Requests/sec: $requests_per_sec"
        echo "  Avg Latency: $avg_latency"
        echo "  99% Latency: $p99_latency"
            echo "  Peak Memory: ${peak_memory_mb}MB"

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
    local endpoints_array

    case "$benchmark_type" in
        "basic")
            endpoints_array=("${BASIC_ENDPOINTS[@]}")
            ;;
        "di")
            endpoints_array=("${DI_ENDPOINTS[@]}")
            ;;
        "sqlalchemy-di")
            endpoints_array=("${SQLALCHEMY_DI_ENDPOINTS[@]}")
            ;;
        "middleware")
            endpoints_array=("${MIDDLEWARE_ENDPOINTS[@]}")
            ;;
        "validation")
            endpoints_array=("${VALIDATION_ENDPOINTS[@]}")
            ;;
        "async-operations")
            endpoints_array=("${ASYNC_OPERATIONS_ENDPOINTS[@]}")
            ;;
        "file-operations")
            endpoints_array=("${FILE_OPERATIONS_ENDPOINTS[@]}")
            ;;
        "background-tasks")
            endpoints_array=("${BACKGROUND_TASKS_ENDPOINTS[@]}")
            ;;
        "real-world")
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

    server_config=$(find_server_config "$benchmark_type" "$framework" || true)
    if [ -n "$server_config" ]; then
        port=$(echo "$server_config" | cut -d':' -f2)
        command=$(echo "$server_config" | cut -d':' -f3-)
    fi

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
        "${(@f)$(get_server_configs_for_type basic)}"
        "${DI_SERVERS[@]}"
        "${SQLALCHEMY_DI_SERVERS[@]}"
        "${MIDDLEWARE_SERVERS[@]}"
        "${VALIDATION_SERVERS[@]}"
        "${ASYNC_OPERATIONS_SERVERS[@]}"
        "${FILE_OPERATIONS_SERVERS[@]}"
        "${BACKGROUND_TASKS_SERVERS[@]}"
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

    # Clean up any orphaned Catzilla multi-worker backend processes on benchmark-only ports.
    local catzilla_multi_port_end=$((BASIC_MULTI_CATZILLA_BACKEND_BASE_PORT + BASIC_MULTI_CATZILLA_MAX_WORKERS - 1))
    for port in $(seq "$BASIC_MULTI_CATZILLA_BACKEND_BASE_PORT" "$catzilla_multi_port_end"); do
        if check_port "$port"; then
            local existing_pid=$(lsof -Pi :$port -sTCP:LISTEN -t 2>/dev/null | head -1)
            if [ -n "$existing_pid" ]; then
                print_warning "Killing orphaned benchmark worker process $existing_pid using port $port"
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

# Function to clear individual benchmark result files
clear_benchmark_results() {
    print_header "🧹 Clearing Individual Benchmark Result Files"

    if [ ! -d "$RESULTS_DIR" ]; then
        print_warning "Results directory not found: $RESULTS_DIR"
        return 0
    fi

    # Count files to be deleted
    local json_count=$(find "$RESULTS_DIR" -name "*.json" -type f ! -name "benchmark_summary.json" 2>/dev/null | wc -l)
    local txt_count=$(find "$RESULTS_DIR" -name "*.txt" -type f 2>/dev/null | wc -l)
    local total_count=$((json_count + txt_count))

    if [ "$total_count" -eq 0 ]; then
        print_success "No individual benchmark result files found to clear"
        return 0
    fi

    print_status "Found $json_count JSON files and $txt_count TXT files to remove"
    print_status "Preserving benchmark_summary.json and analysis reports"

    # Remove individual JSON files (excluding benchmark_summary.json)
    if [ "$json_count" -gt 0 ]; then
        find "$RESULTS_DIR" -name "*.json" -type f ! -name "benchmark_summary.json" -delete 2>/dev/null || true
        print_success "Removed $json_count individual JSON result files"
    fi

    # Remove TXT files
    if [ "$txt_count" -gt 0 ]; then
        find "$RESULTS_DIR" -name "*.txt" -type f -delete 2>/dev/null || true
        print_success "Removed $txt_count TXT result files"
    fi

    print_success "✅ Individual benchmark result files cleared successfully!"
    print_status "Preserved files: benchmark_summary.json, *.md reports, *.png analysis"
}

# Function to generate summary report with framework-keyed structure
generate_summary() {
    local current_benchmark_type=${1:-$BENCHMARK_TYPE}  # Accept benchmark type as parameter
    print_status "Generating framework-keyed benchmark summary for $current_benchmark_type..."

    local summary_file="$RESULTS_DIR/benchmark_summary.json"
    local summary_md="$RESULTS_DIR/benchmark_summary.md"

    # Load existing summary or create new structure
    local existing_summary=""
    local should_create_new=true

    if [ -f "$summary_file" ] && [ -s "$summary_file" ]; then
        # File exists and is not empty
        existing_summary=$(cat "$summary_file" 2>/dev/null || echo "")
        if [ -n "$existing_summary" ] && echo "$existing_summary" | jq -e '.categories' >/dev/null 2>&1; then
            should_create_new=false
            print_status "Merging with existing benchmark summary..."
        else
            print_status "Existing summary file is invalid, creating new one..."
        fi
    else
        print_status "Creating new benchmark summary..."
    fi

    # Create new structure with framework-keyed organization
    local temp_file="/tmp/benchmark_summary_new.json"

    # Collect system information
    print_status "Collecting system information..."
    local system_info_json=""
    if [ -f "$BENCHMARK_DIR/tools/system_info.py" ]; then
        # Run system_info.py and capture output
        cd "$PROJECT_ROOT"  # Run from project root
        if [ -f "$VENV_PATH/bin/activate" ]; then
            source "$VENV_PATH/bin/activate"
        fi
        system_info_json=$(python3 "$BENCHMARK_DIR/tools/system_info.py" --format json 2>/dev/null || echo "{}")
        print_success "System information collected"
    else
        print_warning "system_info.py not found, skipping system information collection"
        system_info_json="{}"
    fi

    if [ "$should_create_new" = true ]; then
        # Create completely new structure
        cat > "$temp_file" << EOF
{
  "metadata": {
    "created": "$(date -Iseconds)",
    "last_updated": "$(date -Iseconds)",
    "version": "3.0",
    "description": "Catzilla Framework Transparent Benchmarking System - Framework Keyed"
  },
  "system_info": $system_info_json,
  "categories": {
    "$current_benchmark_type": {
      "last_run": "$(date -Iseconds)",
      "test_params": {
        "duration": "$DURATION",
        "connections": $CONNECTIONS,
        "connections_per_worker": $CONNECTIONS_PER_WORKER,
        "threads": $THREADS,
        "requested_threads": $THREADS,
                "worker_mode": "$WORKER_MODE",
                "workers": $WORKERS,
        "tool": "wrk"
      },
      "results": {
EOF
        # Add framework results for new file
        local frameworks=("catzilla" "fastapi" "flask" "django")
        local first_framework=true

        for framework in "${frameworks[@]}"; do
            if [ "$first_framework" = false ]; then
                echo "," >> "$temp_file"
            fi
            echo "        \"$framework\": [" >> "$temp_file"

            # Add new results for this framework
            local first_result=true
            for json_file in "$RESULTS_DIR"/*.json(N); do
                if [ -f "$json_file" ] && [[ "$json_file" != *"summary"* ]] && [[ "$json_file" == *"${framework}_${current_benchmark_type}_"* ]]; then
                    if [ "$first_result" = false ]; then
                        echo "," >> "$temp_file"
                    fi
                    cat "$json_file" | sed 's/^/          /' >> "$temp_file"
                    first_result=false
                fi
            done

            echo "" >> "$temp_file"
            echo "        ]" >> "$temp_file"
            first_framework=false
        done

        cat >> "$temp_file" << EOF
      }
    }
  }
}
EOF
    else
        # Merge with existing structure
        # Use jq to properly merge the data
        local new_category_data=""
        local frameworks=("catzilla" "fastapi" "flask" "django")

        # Build the new category data using jq
        local category_json=$(cat << EOF
{
  "last_run": "$(date -Iseconds)",
  "test_params": {
    "duration": "$DURATION",
    "connections": $CONNECTIONS,
        "connections_per_worker": $CONNECTIONS_PER_WORKER,
    "threads": $THREADS,
    "requested_threads": $THREADS,
        "worker_mode": "$WORKER_MODE",
        "workers": $WORKERS,
    "tool": "wrk"
  },
  "results": {
EOF
)

        echo "$category_json" > "$temp_file"

        local first_framework=true
        for framework in "${frameworks[@]}"; do
            if [ "$first_framework" = false ]; then
                echo "," >> "$temp_file"
            fi
            echo "    \"$framework\": [" >> "$temp_file"

            # Add new results for this framework if any exist
            local first_result=true
            local has_results=false
            for json_file in "$RESULTS_DIR"/*.json(N); do
                if [ -f "$json_file" ] && [[ "$json_file" != *"summary"* ]] && [[ "$json_file" == *"${framework}_${current_benchmark_type}_"* ]]; then
                    if [ "$first_result" = false ]; then
                        echo "," >> "$temp_file"
                    fi
                    cat "$json_file" | sed 's/^/      /' >> "$temp_file"
                    first_result=false
                    has_results=true
                fi
            done

            echo "" >> "$temp_file"
            echo "    ]" >> "$temp_file"
            first_framework=false
        done

        echo "  }" >> "$temp_file"
        echo "}" >> "$temp_file"

        # Now merge with existing summary using jq
        local final_temp="/tmp/benchmark_summary_final.json"
        echo "$existing_summary" | jq --argjson newcat "$(cat "$temp_file")" --argjson sysinfo "$system_info_json" \
            '.metadata.last_updated = "'$(date -Iseconds)'" | .system_info = $sysinfo | .categories."'$current_benchmark_type'" = $newcat' \
            > "$final_temp" 2>/dev/null

        if [ $? -eq 0 ] && [ -s "$final_temp" ]; then
            mv "$final_temp" "$temp_file"
        else
            print_warning "jq merge failed, falling back to simple replacement"
            # Fallback: create new structure with existing categories preserved manually
            echo "$existing_summary" | jq --argjson sysinfo "$system_info_json" '.metadata.last_updated = "'$(date -Iseconds)'" | .system_info = $sysinfo' > "$final_temp" 2>/dev/null
            if [ $? -eq 0 ]; then
                # Add the new category data
                local new_summary=$(cat "$final_temp")
                echo "$new_summary" | jq --argjson newcat "$(cat "$temp_file")" '.categories."'$current_benchmark_type'" = $newcat' > "$temp_file" 2>/dev/null || {
                    print_error "Failed to merge summary, creating backup"
                    cp "$summary_file" "${summary_file}.backup.$(date +%s)"
                    # Use the original file as fallback
                    cp "$summary_file" "$temp_file"
                }
            fi
            rm -f "$final_temp"
        fi
    fi

    # Move the temporary file to final location
    if [ -f "$temp_file" ] && [ -s "$temp_file" ]; then
        mv "$temp_file" "$summary_file"
        print_success "Framework-keyed benchmark summary saved to: $summary_file"
    else
        print_error "Failed to generate summary file"
        return 1
    fi

    # Create category-specific markdown
    generate_category_markdown_report "$current_benchmark_type"

    print_success "Category-specific reports generated"
}

# Function to generate category-specific markdown reports
generate_category_markdown_report() {
    local current_benchmark_type=${1:-$BENCHMARK_TYPE}  # Accept benchmark type as parameter
    local category_md="$RESULTS_DIR/${current_benchmark_type}_performance_report.md"

    cat > "$category_md" << EOF
# Catzilla $(echo ${current_benchmark_type} | sed 's/./\U&/') Category Performance Report

## Test Configuration
- **Category**: $current_benchmark_type
- **Duration**: $DURATION
- **Connections**: $CONNECTIONS
- **Connections Per Worker**: $CONNECTIONS_PER_WORKER
- **Requested Threads**: $THREADS
- **Worker Mode**: $WORKER_MODE
- **Workers**: $WORKERS
- **Tool**: wrk
- **Date**: $(date)

## Performance Results

| Framework | Endpoint | Worker Mode | Workers | Requests/sec | Avg Latency | 99% Latency | Peak Memory |
|-----------|----------|-------------|---------|--------------|-------------|-------------|-------------|
EOF

    # Parse JSON results to create table for current category
    for json_file in "$RESULTS_DIR"/*.json; do
        if [ -f "$json_file" ] && [[ "$json_file" != *"summary"* ]] && [[ "$json_file" == *"_${current_benchmark_type}_"* ]]; then
            local framework=$(grep '"framework"' "$json_file" | cut -d'"' -f4)
            local endpoint=$(grep '"endpoint_name"' "$json_file" | cut -d'"' -f4)
            local worker_mode=$(grep '"worker_mode"' "$json_file" | cut -d'"' -f4)
            local workers=$(grep '"workers"' "$json_file" | head -1 | awk -F': ' '{print $2}' | tr -d ',')
            local rps=$(grep '"requests_per_sec"' "$json_file" | cut -d'"' -f4)
            local avg_lat=$(grep '"avg_latency"' "$json_file" | cut -d'"' -f4)
            local p99_lat=$(grep '"p99_latency"' "$json_file" | cut -d'"' -f4)
            local peak_memory_mb=$(grep '"peak_memory_mb"' "$json_file" | head -1 | awk -F': ' '{print $2}' | tr -d ',')
            echo "| $framework | $endpoint | $worker_mode | $workers | $rps | $avg_lat | $p99_lat | ${peak_memory_mb}MB |" >> "$category_md"
        fi
    done

    echo "" >> "$category_md"
    echo "## Catzilla Performance Advantage" >> "$category_md"
    echo "" >> "$category_md"
    echo "This report shows how Catzilla performs compared to other frameworks in the **$current_benchmark_type** category." >> "$category_md"

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
    echo "  --connections NUM   Total connections in single mode, per-worker connections in multi mode (default: 100)"
    echo "  --threads NUM       Number of threads (default: 4)"
    echo "  --worker-mode MODE  HTTP worker mode for direct basic benchmarks: single or multi"
    echo "  --workers NUM       HTTP worker count for --worker-mode multi (default: auto logical CPU count)"
    echo "  --all              Run all available benchmark types"
    echo "  --clear            Clear individual benchmark result files (.json/.txt)"
    echo "  --help             Show this help message"
    echo ""
    echo "Direct Mode (wrk) Examples:"
    echo "  $0                                          # Run basic benchmarks"
    echo "  $0 --type di                               # Run dependency injection benchmarks"
    echo "  $0 --type sqlalchemy-di                    # Run SQLAlchemy DI benchmarks"
    echo "  $0 --type validation                       # Run validation engine benchmarks"
    echo "  $0 --type middleware                       # Run middleware benchmarks"
    echo "  $0 --framework catzilla --type validation  # Run Catzilla validation only"
    echo "  $0 --type basic --worker-mode single       # Basic benchmark in single-worker mode"
    echo "  $0 --type basic --worker-mode multi        # Basic benchmark in auto multi-worker mode"
    echo "  $0 --type basic --worker-mode multi --connections 200  # 200 connections sent to each worker"
    echo "  $0 --type basic --worker-mode multi --workers 4  # Basic benchmark in 4-worker mode"
    echo "  $0 --all                                   # Run ALL benchmark types"
    echo "  $0 --clear                                 # Clear individual result files"
    echo "  $0 --duration 30s --connections 200        # Custom settings"
    echo "  $0 --type async-operations                 # Run raw async operation benchmarks"
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
    echo "  async-operations   - Raw async handler operations"
    echo "  file-operations    - File upload/download/streaming"
    echo "  background-tasks   - Background task processing"
    echo "  real-world         - Real-world API scenarios"
    echo ""
    echo "Available feature categories (python mode):"
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
    # Define valid benchmark types
    local valid_types=("basic" "di" "sqlalchemy-di" "middleware" "validation" "async-operations" "file-operations" "background-tasks" "real-world")

    MODE="direct"  # Default to direct wrk mode
    BENCHMARK_TYPE="basic"  # Default benchmark type
    SELECTED_FRAMEWORK=""
    PYTHON_ARGS=""
    RUN_ALL_TYPES=false
    WORKERS_EXPLICIT=false

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
            --worker-mode)
                WORKER_MODE="$2"
                shift 2
                ;;
            --workers)
                WORKERS="$2"
                WORKERS_EXPLICIT=true
                shift 2
                ;;
            --all)
                RUN_ALL_TYPES=true
                shift
                ;;
            --clear)
                clear_benchmark_results
                exit 0
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

    if [ "$WORKER_MODE" != "single" ] && [ "$WORKER_MODE" != "multi" ]; then
        print_error "Invalid worker mode: $WORKER_MODE"
        print_error "Valid worker modes: single, multi"
        exit 1
    fi

    if ! [[ "$WORKERS" =~ ^[0-9]+$ ]] || [ "$WORKERS" -lt 1 ]; then
        print_error "Invalid workers value: $WORKERS"
        print_error "Workers must be a positive integer"
        exit 1
    fi

    if [ "$WORKER_MODE" = "single" ]; then
        WORKERS="1"
    elif [ "$WORKER_MODE" = "multi" ] && [ "$WORKERS_EXPLICIT" = false ]; then
        WORKERS="$(detect_default_worker_count)"
    fi

    apply_connection_mode_settings

    if [ "$MODE" = "python" ] && [ "$WORKER_MODE" = "multi" ]; then
        print_error "--worker-mode is currently supported only in direct mode"
        exit 1
    fi

    if [ "$MODE" = "direct" ] && [ "$WORKER_MODE" = "multi" ]; then
        if [ "$RUN_ALL_TYPES" = true ] || [ "$BENCHMARK_TYPE" != "basic" ]; then
            print_error "--worker-mode multi is currently supported only for direct basic benchmarks"
            exit 1
        fi
    fi
}

# Run direct wrk benchmarks (like benchmarks_old)
run_direct_benchmarks() {
    if [ "$RUN_ALL_TYPES" = true ]; then
        print_header "🚀 Direct wrk Benchmark Mode - ALL TYPES"
        local all_types=("basic" "di" "sqlalchemy-di" "middleware" "validation" "async-operations" "file-operations" "background-tasks" "real-world")
    else
        print_header "🚀 Direct wrk Benchmark Mode - $BENCHMARK_TYPE"
        local all_types=("$BENCHMARK_TYPE")
    fi

    echo "Duration: $DURATION, Connections: $(format_connection_summary), Threads: $(format_requested_thread_summary)"
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
                "async-operations")
                    frameworks_to_test=("catzilla" "fastapi" "django")  # Native async benchmark servers
                    ;;
                "file-operations")
                    frameworks_to_test=("catzilla" "fastapi" "flask" "django")  # All have file servers
                    ;;
                "background-tasks")
                    frameworks_to_test=("catzilla" "fastapi" "flask" "django")  # All have task servers
                    ;;
                "real-world")
                    frameworks_to_test=("catzilla" "fastapi" "django" "flask")  # These have real-world servers
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
                generate_summary "$benchmark_type"
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
    if [ "$RUN_ALL_TYPES" = true ]; then
        # For --all runs, generate summary for the last benchmark type
        generate_summary "${all_types[-1]}"
    else
        generate_summary "$BENCHMARK_TYPE"
    fi

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
    print_status "Duration: $DURATION, Connections: $(format_connection_summary), Threads: $(format_requested_thread_summary)"

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
    echo "Worker mode: $WORKER_MODE (${WORKERS} worker(s))"
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
