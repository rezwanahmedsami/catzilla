"""
Benchmark Configuration

Centralized configuration for framework benchmarking including
port assignments, server commands, and test parameters.
"""

import os
from typing import Dict, List, Any

# Supported frameworks
FRAMEWORKS = ["catzilla", "fastapi", "flask", "django"]

# Base port assignments for each framework
BASE_PORTS = {
    "catzilla": 8000,
    "fastapi": 8100,
    "flask": 8200,
    "django": 8300
}

# Port offsets for different categories
CATEGORY_OFFSETS = {
    "basic": 0,
    "middleware": 10,
    "dependency_injection": 20,
    "async_operations": 30,
    "validation": 40,
    "file_operations": 50,
    "background_tasks": 60,
    "real_world_scenarios": 70
}

# Server configuration for each framework
SERVER_CONFIGS = {
    "catzilla": {
        "command_template": "python {server_file} --host {host} --port {port} --workers {workers}",
        "startup_time": 3,
        "health_endpoint": "/health"
    },
    "fastapi": {
        "command_template": "python {server_file} --host {host} --port {port} --workers {workers}",
        "startup_time": 4,
        "health_endpoint": "/health"
    },
    "flask": {
        "command_template": "python {server_file} --host {host} --port {port}",
        "startup_time": 3,
        "health_endpoint": "/health"
    },
    "django": {
        "command_template": "python {server_file} --host {host} --port {port}",
        "startup_time": 5,
        "health_endpoint": "/health"
    }
}

# Default test parameters
DEFAULT_TEST_PARAMS = {
    "threads": 4,
    "connections": 100,
    "duration": 30,
    "timeout": 10
}

# Feature-specific test configurations
FEATURE_TEST_CONFIGS = {
    "basic": {
        "description": "Basic HTTP operations and routing",
        "test_duration": 30,
        "concurrent_users": [10, 25, 50, 100],
        "focus_metrics": ["requests_per_second", "latency_avg", "latency_99p"]
    },
    "middleware": {
        "description": "Middleware processing and request/response handling",
        "test_duration": 30,
        "concurrent_users": [10, 25, 50, 100],
        "focus_metrics": ["requests_per_second", "latency_avg", "middleware_overhead"]
    },
    "dependency_injection": {
        "description": "Dependency injection system performance",
        "test_duration": 30,
        "concurrent_users": [10, 25, 50],
        "focus_metrics": ["requests_per_second", "injection_time", "memory_usage"]
    },
    "async_operations": {
        "description": "Asynchronous operation handling",
        "test_duration": 45,
        "concurrent_users": [20, 50, 100, 200],
        "focus_metrics": ["requests_per_second", "async_latency", "throughput"]
    },
    "validation": {
        "description": "Data validation and serialization performance",
        "test_duration": 30,
        "concurrent_users": [10, 25, 50, 100],
        "focus_metrics": ["validation_speed", "error_handling", "memory_efficiency"]
    },
    "file_operations": {
        "description": "File upload, download, and processing",
        "test_duration": 60,
        "concurrent_users": [5, 10, 20, 50],
        "focus_metrics": ["throughput_mbps", "file_processing_time", "concurrent_uploads"]
    },
    "background_tasks": {
        "description": "Background task processing and scheduling",
        "test_duration": 60,
        "concurrent_users": [10, 20, 50, 100],
        "focus_metrics": ["task_throughput", "queue_efficiency", "task_latency"]
    },
    "real_world_scenarios": {
        "description": "Complete application scenarios",
        "test_duration": 90,
        "concurrent_users": [10, 25, 50, 100],
        "focus_metrics": ["end_to_end_performance", "feature_integration", "scalability"]
    }
}

# Load test patterns
LOAD_TEST_PATTERNS = {
    "constant": {
        "description": "Constant load throughout test",
        "pattern": "constant"
    },
    "ramp_up": {
        "description": "Gradual increase in load",
        "pattern": "linear_increase"
    },
    "spike": {
        "description": "Sudden load spikes",
        "pattern": "spike"
    },
    "burst": {
        "description": "Burst traffic patterns",
        "pattern": "burst"
    }
}

# Performance thresholds and expectations
PERFORMANCE_THRESHOLDS = {
    "catzilla": {
        "basic": {"min_rps": 10000, "max_latency_99p": "50ms"},
        "middleware": {"min_rps": 8000, "max_latency_99p": "75ms"},
        "validation": {"min_rps": 7000, "max_latency_99p": "100ms"},
        "file_operations": {"min_throughput_mbps": 100, "max_upload_time": "5s"},
        "background_tasks": {"min_task_throughput": 1000, "max_queue_time": "100ms"},
        "real_world_scenarios": {"min_rps": 5000, "max_latency_99p": "200ms"}
    },
    "fastapi": {
        "basic": {"min_rps": 8000, "max_latency_99p": "75ms"},
        "middleware": {"min_rps": 6000, "max_latency_99p": "100ms"},
        "validation": {"min_rps": 5000, "max_latency_99p": "150ms"},
        "file_operations": {"min_throughput_mbps": 80, "max_upload_time": "8s"},
        "background_tasks": {"min_task_throughput": 800, "max_queue_time": "200ms"},
        "real_world_scenarios": {"min_rps": 3000, "max_latency_99p": "300ms"}
    },
    "flask": {
        "basic": {"min_rps": 5000, "max_latency_99p": "100ms"},
        "middleware": {"min_rps": 3000, "max_latency_99p": "150ms"},
        "validation": {"min_rps": 2000, "max_latency_99p": "200ms"},
        "file_operations": {"min_throughput_mbps": 50, "max_upload_time": "10s"},
        "background_tasks": {"min_task_throughput": 500, "max_queue_time": "500ms"},
        "real_world_scenarios": {"min_rps": 1500, "max_latency_99p": "500ms"}
    },
    "django": {
        "basic": {"min_rps": 3000, "max_latency_99p": "150ms"},
        "middleware": {"min_rps": 2000, "max_latency_99p": "200ms"},
        "validation": {"min_rps": 1500, "max_latency_99p": "250ms"},
        "file_operations": {"min_throughput_mbps": 40, "max_upload_time": "12s"},
        "background_tasks": {"min_task_throughput": 400, "max_queue_time": "1s"},
        "real_world_scenarios": {"min_rps": 1000, "max_latency_99p": "800ms"}
    }
}

def get_framework_port(framework: str, category: str) -> int:
    """Get port number for a framework/category combination"""
    base_port = BASE_PORTS.get(framework, 8000)
    offset = CATEGORY_OFFSETS.get(category, 0)
    return base_port + offset

def get_server_command(framework: str, server_file: str, host: str = "127.0.0.1",
                      port: int = None, workers: int = 1) -> List[str]:
    """Generate server startup command"""
    config = SERVER_CONFIGS.get(framework, SERVER_CONFIGS["catzilla"])

    if port is None:
        port = BASE_PORTS.get(framework, 8000)

    template = config["command_template"]
    cmd_str = template.format(
        server_file=server_file,
        host=host,
        port=port,
        workers=workers
    )

    return cmd_str.split()

def get_test_config(category: str) -> Dict[str, Any]:
    """Get test configuration for a category"""
    return FEATURE_TEST_CONFIGS.get(category, {
        "description": f"{category} performance tests",
        "test_duration": 30,
        "concurrent_users": [10, 25, 50],
        "focus_metrics": ["requests_per_second", "latency_avg"]
    })

def get_performance_threshold(framework: str, category: str) -> Dict[str, Any]:
    """Get performance thresholds for framework/category"""
    framework_thresholds = PERFORMANCE_THRESHOLDS.get(framework, {})
    return framework_thresholds.get(category, {})

def validate_framework(framework: str) -> bool:
    """Validate if framework is supported"""
    return framework in FRAMEWORKS

def validate_category(category: str) -> bool:
    """Validate if category is supported"""
    return category in CATEGORY_OFFSETS

def get_all_categories() -> List[str]:
    """Get list of all supported benchmark categories"""
    return list(CATEGORY_OFFSETS.keys())

def get_category_description(category: str) -> str:
    """Get description for a benchmark category"""
    config = FEATURE_TEST_CONFIGS.get(category, {})
    return config.get("description", f"{category} performance tests")

# Environment-specific configurations
def get_env_config() -> Dict[str, Any]:
    """Get environment-specific configuration"""
    return {
        "python_executable": os.environ.get("PYTHON_EXECUTABLE", "python3"),
        "wrk_executable": os.environ.get("WRK_EXECUTABLE", "wrk"),
        "output_dir": os.environ.get("BENCHMARK_OUTPUT_DIR", "results"),
        "parallel_tests": os.environ.get("PARALLEL_TESTS", "false").lower() == "true",
        "verbose": os.environ.get("VERBOSE", "false").lower() == "true"
    }

# Benchmark result analysis configuration
ANALYSIS_CONFIG = {
    "key_metrics": [
        "requests_per_second",
        "latency_avg",
        "latency_99p",
        "total_requests",
        "transfer_per_second"
    ],
    "comparison_metrics": [
        "relative_performance",
        "scalability_factor",
        "efficiency_ratio"
    ],
    "report_sections": [
        "executive_summary",
        "framework_comparison",
        "category_analysis",
        "performance_insights",
        "recommendations"
    ]
}

if __name__ == "__main__":
    # Test configuration functions
    print("Supported frameworks:", FRAMEWORKS)
    print("Supported categories:", get_all_categories())
    print()

    for framework in FRAMEWORKS:
        for category in get_all_categories():
            port = get_framework_port(framework, category)
            print(f"{framework} {category}: port {port}")

    print()
    print("Test configurations:")
    for category in get_all_categories():
        config = get_test_config(category)
        print(f"{category}: {config['description']}")
