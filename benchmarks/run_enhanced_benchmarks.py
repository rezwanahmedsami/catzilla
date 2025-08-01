#!/usr/bin/env python3
"""
Enhanced Feature-Based Benchmark Runner

Comprehensive benchmarking system for Catzilla, FastAPI, Flask, and Django
across multiple feature categories including real-world scenarios.

Features:
- Multiple benchmark categories (basic, middleware, DI, async, validation,
  file_operations, background_tasks, real_world_scenarios)
- Configurable test scenarios and load patterns
- Detailed performance metrics and comparison
- Results visualization and reporting
- Parallel framework testing
- Feature-specific benchmarks
"""

import os
import sys
import json
import time
import argparse
import subprocess
import threading
import queue
import signal
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
import concurrent.futures
import yaml

# Add shared modules to path
SCRIPT_DIR = Path(__file__).parent
SHARED_DIR = SCRIPT_DIR / "shared"
TOOLS_DIR = SCRIPT_DIR / "tools"
sys.path.insert(0, str(SHARED_DIR))
sys.path.insert(0, str(TOOLS_DIR))

# Import shared utilities
from benchmarks_config import (
    FRAMEWORKS, SERVER_CONFIGS, DEFAULT_TEST_PARAMS,
    get_framework_port, get_server_command
)

# Import system information collection
try:
    import os
    import sys
    # Add tools directory to path with absolute path
    tools_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'tools')
    if tools_dir not in sys.path:
        sys.path.insert(0, tools_dir)
    from system_info import collect_system_info, format_system_info_markdown
    print("System info module loaded successfully")
except ImportError as e:
    print(f"Warning: system_info module not found ({e}). System information will not be included in reports.")
    def collect_system_info():
        return {"error": "system_info module not available"}
    def format_system_info_markdown(info):
        return "## System Information\n\nSystem information not available."


class EnhancedBenchmarkRunner:
    """Enhanced benchmark runner with feature-based testing"""

    def __init__(self, output_dir: str = "results"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.servers = {}
        self.results = {}
        self.test_categories = [
            "basic",
            "middleware",
            "dependency_injection",
            "async_operations",
            "validation",
            "file_operations",
            "background_tasks",
            "real_world_scenarios"
        ]

    def discover_benchmark_categories(self) -> Dict[str, Dict]:
        """Discover available benchmark categories and their configurations"""
        categories = {}

        servers_dir = SCRIPT_DIR / "servers"
        for category_dir in servers_dir.iterdir():
            if category_dir.is_dir() and category_dir.name in self.test_categories:
                category_name = category_dir.name
                categories[category_name] = {
                    "name": category_name,
                    "path": category_dir,
                    "frameworks": [],
                    "endpoints": None
                }

                # Check for framework servers
                for framework in FRAMEWORKS:
                    server_file = None
                    for pattern in [f"{framework}_{category_name}.py", f"{framework}_server.py"]:
                        potential_file = category_dir / pattern
                        if potential_file.exists():
                            server_file = potential_file
                            break

                    if server_file:
                        categories[category_name]["frameworks"].append({
                            "name": framework,
                            "server_file": server_file,
                            "port": get_framework_port(framework, category_name)
                        })

                # Load endpoints configuration
                endpoints_file = category_dir / "endpoints.json"
                if endpoints_file.exists():
                    try:
                        with open(endpoints_file) as f:
                            categories[category_name]["endpoints"] = json.load(f)
                    except Exception as e:
                        print(f"Warning: Could not load endpoints for {category_name}: {e}")

        return categories

    def start_server(self, framework: str, category: str, server_file: Path, port: int) -> Optional[subprocess.Popen]:
        """Start a benchmark server"""
        try:
            cmd = [
                sys.executable, str(server_file),
                "--host", "127.0.0.1",
                "--port", str(port),
                "--workers", "1"
            ]

            print(f"Starting {framework} {category} server on port {port}")
            print(f"Command: {' '.join(cmd)}")

            # Start server with output capture
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=SCRIPT_DIR
            )

            # Wait a moment for server to start
            time.sleep(3)

            # Check if process is still running
            if process.poll() is not None:
                stdout, stderr = process.communicate()
                print(f"Failed to start {framework} {category} server:")
                print(f"stdout: {stdout}")
                print(f"stderr: {stderr}")
                return None

            return process

        except Exception as e:
            print(f"Error starting {framework} {category} server: {e}")
            return None

    def stop_server(self, process: subprocess.Popen):
        """Stop a benchmark server"""
        if process and process.poll() is None:
            try:
                process.terminate()
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()

    def run_wrk_benchmark(self, category: str, framework: str, port: int,
                         endpoints_config: Dict, test_params: Dict) -> Dict[str, Any]:
        """Run wrk benchmark for a specific endpoint"""
        results = {
            "framework": framework,
            "category": category,
            "timestamp": datetime.now().isoformat(),
            "test_params": test_params,
            "endpoints": {}
        }

        base_url = f"http://127.0.0.1:{port}"

        # Test each endpoint
        for endpoint in endpoints_config.get("endpoints", []):
            endpoint_path = endpoint["path"]
            method = endpoint.get("method", "GET")
            weight = endpoint.get("weight", 1)

            print(f"Testing {framework} {category}: {method} {endpoint_path}")

            # Build wrk command
            if method == "GET":
                url = f"{base_url}{endpoint_path}"
                # Replace path parameters with sample values
                if "{" in url:
                    path_params = endpoint.get("path_params", {})
                    for param, values in path_params.items():
                        if values:
                            sample_value = values[0] if isinstance(values, list) else values
                            url = url.replace(f"{{{param}}}", str(sample_value))

                wrk_cmd = [
                    "wrk",
                    "-t", str(test_params["threads"]),
                    "-c", str(test_params["connections"]),
                    "-d", f"{test_params['duration']}s",
                    "--timeout", f"{test_params['timeout']}s",
                    url
                ]
            else:
                # For POST requests, create a Lua script
                lua_script = self.create_wrk_lua_script(endpoint, base_url)
                lua_file = self.output_dir / f"{framework}_{category}_{endpoint_path.replace('/', '_')}.lua"

                with open(lua_file, 'w') as f:
                    f.write(lua_script)

                wrk_cmd = [
                    "wrk",
                    "-t", str(test_params["threads"]),
                    "-c", str(test_params["connections"]),
                    "-d", f"{test_params['duration']}s",
                    "--timeout", f"{test_params['timeout']}s",
                    "-s", str(lua_file),
                    base_url
                ]

            try:
                # Run wrk benchmark
                result = subprocess.run(
                    wrk_cmd,
                    capture_output=True,
                    text=True,
                    timeout=test_params["duration"] + 30
                )

                if result.returncode == 0:
                    endpoint_result = self.parse_wrk_output(result.stdout)
                    endpoint_result["method"] = method
                    endpoint_result["weight"] = weight
                    endpoint_result["cmd"] = " ".join(wrk_cmd)
                    results["endpoints"][endpoint_path] = endpoint_result
                else:
                    print(f"wrk failed for {endpoint_path}: {result.stderr}")
                    results["endpoints"][endpoint_path] = {
                        "error": result.stderr,
                        "method": method,
                        "weight": weight
                    }

            except subprocess.TimeoutExpired:
                print(f"wrk timeout for {endpoint_path}")
                results["endpoints"][endpoint_path] = {
                    "error": "timeout",
                    "method": method,
                    "weight": weight
                }

            # Small delay between tests
            time.sleep(1)

        return results

    def create_wrk_lua_script(self, endpoint: Dict, base_url: str) -> str:
        """Create a Lua script for wrk POST requests"""
        method = endpoint.get("method", "POST")
        path = endpoint["path"]
        body = endpoint.get("body", {})
        headers = endpoint.get("headers", {})

        lua_script = f'''
wrk.method = "{method}"
wrk.headers["Content-Type"] = "application/json"

'''

        # Add custom headers
        for header, value in headers.items():
            if isinstance(value, list):
                value = value[0]  # Use first value for simplicity
            lua_script += f'wrk.headers["{header}"] = "{value}"\n'

        lua_script += f'''
wrk.body = '{json.dumps(body)}'

request = function()
    local path = "{path}"
    -- Replace path parameters with sample values if needed
    return wrk.format(nil, path)
end
'''

        return lua_script

    def parse_wrk_output(self, output: str) -> Dict[str, Any]:
        """Parse wrk output into structured data"""
        lines = output.strip().split('\n')
        result = {}

        for line in lines:
            line = line.strip()

            # Parse requests per second
            if "Requests/sec:" in line:
                result["requests_per_second"] = float(line.split()[-1])

            # Parse transfer rate
            elif "Transfer/sec:" in line:
                transfer = line.split()[-1]
                result["transfer_per_second"] = transfer

            # Parse latency distribution
            elif "Latency" in line and "Distribution" not in line:
                parts = line.split()
                if len(parts) >= 4:
                    result["latency_avg"] = parts[1]
                    result["latency_stdev"] = parts[2]
                    result["latency_max"] = parts[3]

            # Parse request distribution
            elif line.startswith("50.000%"):
                result["latency_50p"] = line.split()[1]
            elif line.startswith("75.000%"):
                result["latency_75p"] = line.split()[1]
            elif line.startswith("90.000%"):
                result["latency_90p"] = line.split()[1]
            elif line.startswith("99.000%"):
                result["latency_99p"] = line.split()[1]

            # Parse total requests and errors
            elif "requests in" in line:
                parts = line.split()
                result["total_requests"] = int(parts[0])
                result["duration"] = parts[2].rstrip(',')
                if len(parts) > 4:
                    result["total_bytes"] = parts[4]

            elif "Socket errors:" in line:
                error_parts = line.split()
                result["socket_errors"] = {
                    "connect": int(error_parts[3].rstrip(',')),
                    "read": int(error_parts[5].rstrip(',')),
                    "write": int(error_parts[7].rstrip(',')),
                    "timeout": int(error_parts[9])
                }

        return result

    def run_category_benchmark(self, category: str, frameworks: List[str] = None,
                              test_params: Dict = None) -> Dict[str, Any]:
        """Run benchmark for a specific category"""
        if frameworks is None:
            frameworks = FRAMEWORKS

        if test_params is None:
            test_params = DEFAULT_TEST_PARAMS.copy()

        print(f"\n{'='*60}")
        print(f"Running {category} benchmarks")
        print(f"{'='*60}")

        categories = self.discover_benchmark_categories()
        if category not in categories:
            print(f"Category {category} not found")
            return {}

        category_config = categories[category]
        endpoints_config = category_config.get("endpoints", {})

        if not endpoints_config:
            print(f"No endpoints configuration found for {category}")
            return {}

        category_results = {
            "category": category,
            "timestamp": datetime.now().isoformat(),
            "test_params": test_params,
            "system_info": collect_system_info(),
            "frameworks": {}
        }

        # Start and test each framework
        for framework_info in category_config["frameworks"]:
            framework = framework_info["name"]
            if framework not in frameworks:
                continue

            server_file = framework_info["server_file"]
            port = framework_info["port"]

            print(f"\nTesting {framework} for {category}")

            # Start server
            process = self.start_server(framework, category, server_file, port)
            if not process:
                print(f"Failed to start {framework} server")
                continue

            try:
                # Wait for server to be ready
                time.sleep(5)

                # Run benchmarks
                results = self.run_wrk_benchmark(
                    category, framework, port, endpoints_config, test_params
                )
                category_results["frameworks"][framework] = results

            finally:
                # Stop server
                self.stop_server(process)
                time.sleep(2)

        # Save results with clean filename
        results_file = self.output_dir / f"{category}_results.json"
        with open(results_file, 'w') as f:
            json.dump(category_results, f, indent=2)

        print(f"Results saved to {results_file}")

        # Also save as benchmark_summary.json for the main category
        summary_file = self.output_dir / "benchmark_summary.json"
        with open(summary_file, 'w') as f:
            json.dump(category_results, f, indent=2)

        return category_results

    def run_all_benchmarks(self, frameworks: List[str] = None,
                          categories: List[str] = None,
                          test_params: Dict = None) -> Dict[str, Any]:
        """Run benchmarks for all categories"""
        if frameworks is None:
            frameworks = FRAMEWORKS

        if categories is None:
            categories = self.test_categories

        if test_params is None:
            test_params = DEFAULT_TEST_PARAMS.copy()

        print(f"Running comprehensive benchmarks")
        print(f"Frameworks: {', '.join(frameworks)}")
        print(f"Categories: {', '.join(categories)}")
        print(f"Test params: {test_params}")

        all_results = {
            "timestamp": datetime.now().isoformat(),
            "frameworks": frameworks,
            "categories": categories,
            "test_params": test_params,
            "system_info": collect_system_info(),
            "results": {}
        }

        # Run each category
        for category in categories:
            try:
                category_results = self.run_category_benchmark(
                    category, frameworks, test_params
                )
                all_results["results"][category] = category_results
            except Exception as e:
                print(f"Error running {category} benchmarks: {e}")
                all_results["results"][category] = {"error": str(e)}

        # Save comprehensive results with clean filename
        results_file = self.output_dir / "comprehensive_results.json"
        with open(results_file, 'w') as f:
            json.dump(all_results, f, indent=2)

        # Always save the main benchmark_summary.json
        summary_file = self.output_dir / "benchmark_summary.json"
        with open(summary_file, 'w') as f:
            json.dump(all_results, f, indent=2)

        print(f"\nComprehensive results saved to {results_file}")
        print(f"Benchmark summary saved to {summary_file}")
        return all_results

    def generate_performance_report(self, results: Dict[str, Any]) -> str:
        """Generate a performance comparison report with system information"""
        report = []
        report.append("# Catzilla Framework Benchmark Report")
        report.append(f"Generated: {results['timestamp']}")

        # Handle both single category and comprehensive results
        if "test_params" in results:
            report.append(f"Test Parameters: {results['test_params']}")
        report.append("")

        # Add system information
        if "system_info" in results:
            system_md = format_system_info_markdown(results["system_info"])
            report.append(system_md)
            report.append("")

        # Summary table
        report.append("## Performance Summary")
        report.append("")

        # Handle single category results (when running specific category)
        if "category" in results and "frameworks" in results:
            category = results["category"]
            report.append(f"### {category.title()} Category")
            report.append("")

            # Process endpoints for single category
            frameworks_data = results["frameworks"]
            if frameworks_data:
                # Get all endpoints from all frameworks
                all_endpoints = set()
                for fw_results in frameworks_data.values():
                    all_endpoints.update(fw_results.get("endpoints", {}).keys())

                for endpoint in sorted(all_endpoints):
                    report.append(f"#### Endpoint: {endpoint}")
                    report.append("")
                    report.append("| Framework | Requests/sec | Avg Latency | 99th Percentile |")
                    report.append("|-----------|--------------|-------------|-----------------|")

                    # Add data for each framework
                    for framework, framework_data in frameworks_data.items():
                        endpoint_results = framework_data.get("endpoints", {}).get(endpoint, {})
                        rps = endpoint_results.get("requests_per_second", "N/A")
                        avg_lat = endpoint_results.get("latency_avg", "N/A")
                        p99_lat = endpoint_results.get("latency_99p", "N/A")
                        report.append(f"| {framework} | {rps} | {avg_lat} | {p99_lat} |")

                    report.append("")

        # Handle comprehensive results (when running all categories)
        elif "results" in results:
            for category, category_results in results["results"].items():
                if "error" in category_results:
                    continue

                report.append(f"### {category.title()} Category")
                report.append("")

                frameworks_data = category_results.get("frameworks", {})
                if frameworks_data:
                    # Get all endpoints from all frameworks
                    all_endpoints = set()
                    for fw_results in frameworks_data.values():
                        all_endpoints.update(fw_results.get("endpoints", {}).keys())

                    for endpoint in sorted(all_endpoints):
                        report.append(f"#### Endpoint: {endpoint}")
                        report.append("")
                        report.append("| Framework | Requests/sec | Avg Latency | 99th Percentile |")
                        report.append("|-----------|--------------|-------------|-----------------|")

                        # Add data for each framework
                        for framework, framework_data in frameworks_data.items():
                            endpoint_results = framework_data.get("endpoints", {}).get(endpoint, {})
                            rps = endpoint_results.get("requests_per_second", "N/A")
                            avg_lat = endpoint_results.get("latency_avg", "N/A")
                            p99_lat = endpoint_results.get("latency_99p", "N/A")
                            report.append(f"| {framework} | {rps} | {avg_lat} | {p99_lat} |")

                        report.append("")

        return "\n".join(report)


def main():
    parser = argparse.ArgumentParser(description='Enhanced feature-based benchmark runner')
    parser.add_argument('--category', choices=[
        'basic', 'middleware', 'dependency_injection', 'async_operations',
        'validation', 'file_operations', 'background_tasks', 'real_world_scenarios'
    ], help='Run specific category benchmark')
    parser.add_argument('--frameworks', nargs='+', choices=FRAMEWORKS,
                       default=FRAMEWORKS, help='Frameworks to test')
    parser.add_argument('--threads', type=int, default=4, help='Number of threads for wrk')
    parser.add_argument('--connections', type=int, default=100, help='Number of connections for wrk')
    parser.add_argument('--duration', type=int, default=30, help='Test duration in seconds')
    parser.add_argument('--timeout', type=int, default=10, help='Request timeout in seconds')
    parser.add_argument('--output-dir', default='results', help='Output directory for results')
    parser.add_argument('--report', action='store_true', help='Generate performance report')

    args = parser.parse_args()

    # Create benchmark runner
    runner = EnhancedBenchmarkRunner(args.output_dir)

    # Set up test parameters
    test_params = {
        "threads": args.threads,
        "connections": args.connections,
        "duration": args.duration,
        "timeout": args.timeout
    }

    # Run benchmarks
    if args.category:
        results = runner.run_category_benchmark(
            args.category, args.frameworks, test_params
        )
    else:
        results = runner.run_all_benchmarks(
            args.frameworks, None, test_params
        )

    # Always generate performance report
    if "results" in results or "category" in results:
        report = runner.generate_performance_report(results)
        report_file = runner.output_dir / "benchmark_summary.md"
        with open(report_file, 'w') as f:
            f.write(report)
        print(f"Performance report saved to {report_file}")

    # Also generate additional detailed report if requested
    if args.report and ("results" in results or "category" in results):
        detailed_report_file = runner.output_dir / "performance_report_detailed.md"
        with open(detailed_report_file, 'w') as f:
            f.write(report)
        print(f"Detailed performance report saved to {detailed_report_file}")


if __name__ == "__main__":
    main()
