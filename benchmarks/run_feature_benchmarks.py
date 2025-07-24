#!/usr/bin/env python3
"""
Feature-Based Benchmark Runner

Enhanced benchmark runner that supports both the old basic benchmarks
and new feature-specific benchmarks. Maintains compatibility with the
existing result format while adding feature categorization.
"""

import os
import sys
import json
import argparse
import subprocess
import time
import signal
import requests
from datetime import datetime
from typing import Dict, List, Any, Optional
import threading

# Colors for output
RED = '\033[0;31m'
GREEN = '\033[0;32m'
YELLOW = '\033[1;33m'
BLUE = '\033[0;34m'
PURPLE = '\033[0;35m'
CYAN = '\033[0;36m'
NC = '\033[0m'  # No Color

class FeatureBenchmarkRunner:
    """Enhanced benchmark runner for feature-based testing"""

    def __init__(self, benchmark_dir: str):
        self.benchmark_dir = benchmark_dir
        self.results_dir = os.path.join(benchmark_dir, "results")
        self.servers_dir = os.path.join(benchmark_dir, "servers")

        # Ensure results directory exists
        os.makedirs(self.results_dir, exist_ok=True)

        # Benchmark configuration
        self.duration = "10s"
        self.connections = 100
        self.threads = 4
        self.warmup_time = 3

        # Server processes
        self.processes = {}

        # Results storage
        self.results = []

        # Feature categories and their server configurations
        self.feature_categories = {
            "basic": {
                "servers": {
                    "catzilla": {"port": 8000, "script": "basic/catzilla_server.py"},
                    "fastapi": {"port": 8001, "script": "basic/fastapi_server.py"},
                    "flask": {"port": 8002, "script": "basic/flask_server.py"},
                    "django": {"port": 8003, "script": "basic/django_server.py"}
                },
                "endpoints": [
                    {"path": "/", "name": "hello_world", "method": "GET"},
                    {"path": "/json", "name": "json_response", "method": "GET"},
                    {"path": "/user/42", "name": "path_params", "method": "GET"},
                    {"path": "/users?limit=20&offset=10", "name": "query_params", "method": "GET"},
                    {"path": "/user/123/profile", "name": "complex_json", "method": "GET"}
                ]
            },
            "middleware": {
                "servers": {
                    "catzilla": {"port": 8010, "script": "middleware/catzilla_middleware.py"},
                    "fastapi": {"port": 8011, "script": "middleware/fastapi_middleware.py"},
                    "flask": {"port": 8012, "script": "middleware/flask_middleware.py"},
                    "django": {"port": 8013, "script": "middleware/django_middleware.py"}
                },
                "endpoints": [
                    {"path": "/auth/protected", "name": "auth_protected", "method": "GET", "headers": {"Authorization": "Bearer test-token"}},
                    {"path": "/rate-limited", "name": "rate_limited", "method": "GET"},
                    {"path": "/admin/action", "name": "multi_middleware", "method": "POST", "headers": {"Authorization": "Bearer admin-token"}}
                ]
            },
            "dependency_injection": {
                "servers": {
                    "catzilla": {"port": 8020, "script": "dependency_injection/catzilla_di.py"},
                    "fastapi": {"port": 8021, "script": "dependency_injection/fastapi_di.py"},
                    "django": {"port": 8023, "script": "dependency_injection/django_di.py"}
                },
                "endpoints": [
                    {"path": "/di/simple", "name": "simple_injection", "method": "GET"},
                    {"path": "/di/nested/42", "name": "nested_injection", "method": "GET"},
                    {"path": "/di/scoped", "name": "scoped_services", "method": "POST"},
                    {"path": "/di/complex", "name": "complex_graph", "method": "GET"}
                ]
            },
            "async_operations": {
                "servers": {
                    "catzilla": {"port": 8030, "script": "async_operations/catzilla_async.py"},
                    "fastapi": {"port": 8031, "script": "async_operations/fastapi_async.py"},
                    "aiohttp": {"port": 8032, "script": "async_operations/aiohttp_async.py"},
                    "tornado": {"port": 8033, "script": "async_operations/tornado_async.py"}
                },
                "endpoints": [
                    {"path": "/async/simple", "name": "async_simple", "method": "GET"},
                    {"path": "/async/concurrent", "name": "async_concurrent", "method": "GET"},
                    {"path": "/async/database/42", "name": "async_database", "method": "GET"},
                    {"path": "/mixed/process", "name": "mixed_sync_async", "method": "POST"}
                ]
            }
        }

    def print_status(self, message: str):
        print(f"{BLUE}[INFO]{NC} {message}")

    def print_success(self, message: str):
        print(f"{GREEN}[SUCCESS]{NC} {message}")

    def print_warning(self, message: str):
        print(f"{YELLOW}[WARNING]{NC} {message}")

    def print_error(self, message: str):
        print(f"{RED}[ERROR]{NC} {message}")

    def print_category(self, message: str):
        print(f"{PURPLE}[CATEGORY]{NC} {message}")

    def check_port(self, port: int) -> bool:
        """Check if a port is in use"""
        import socket
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            result = s.connect_ex(('127.0.0.1', port))
            return result == 0

    def wait_for_server(self, host: str, port: int, timeout: int = 30) -> bool:
        """Wait for server to start and respond to health check"""
        self.print_status(f"Waiting for server at {host}:{port} to start...")

        for i in range(timeout):
            try:
                response = requests.get(f"http://{host}:{port}/health", timeout=2)
                if response.status_code == 200:
                    self.print_success(f"Server at {host}:{port} is ready!")
                    return True
            except:
                pass
            time.sleep(1)

        self.print_error(f"Server at {host}:{port} failed to start within {timeout}s")
        return False

    def start_server(self, framework: str, config: Dict[str, Any], category: str) -> bool:
        """Start a framework server for a specific category"""
        script_path = os.path.join(self.servers_dir, config["script"])
        port = config["port"]

        # Kill any existing process on this port
        if self.check_port(port):
            self.print_warning(f"Port {port} is in use, attempting to free it...")
            os.system(f"lsof -ti:{port} | xargs kill -9 2>/dev/null")
            time.sleep(2)

        self.print_status(f"Starting {framework} server for {category} on port {port}...")

        try:
            # Start the server
            cmd = ['python3', script_path, '--port', str(port)]
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                preexec_fn=os.setsid
            )

            server_key = f"{category}_{framework}"
            self.processes[server_key] = process

            # Wait for server to start
            if self.wait_for_server("127.0.0.1", port):
                return True
            else:
                self.stop_server(server_key)
                return False

        except Exception as e:
            self.print_error(f"Failed to start {framework} server: {e}")
            return False

    def stop_server(self, server_key: str):
        """Stop a server process"""
        if server_key in self.processes:
            try:
                process = self.processes[server_key]
                os.killpg(os.getpgid(process.pid), signal.SIGTERM)
                process.wait(timeout=5)
            except:
                try:
                    os.killpg(os.getpgid(process.pid), signal.SIGKILL)
                except:
                    pass
            del self.processes[server_key]

    def run_wrk_benchmark(self, url: str, duration: str = None, connections: int = None, threads: int = None) -> Dict[str, Any]:
        """Run wrk benchmark and parse results"""
        duration = duration or self.duration
        connections = connections or self.connections
        threads = threads or self.threads

        cmd = [
            'wrk',
            '-t', str(threads),
            '-c', str(connections),
            '-d', duration,
            '--latency',
            url
        ]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            if result.returncode != 0:
                return {"error": f"wrk failed: {result.stderr}"}

            return self.parse_wrk_output(result.stdout)

        except subprocess.TimeoutExpired:
            return {"error": "wrk timed out"}
        except Exception as e:
            return {"error": f"wrk execution failed: {e}"}

    def parse_wrk_output(self, output: str) -> Dict[str, Any]:
        """Parse wrk output into structured data"""
        lines = output.strip().split('\n')
        results = {}

        for line in lines:
            line = line.strip()
            if 'Requests/sec:' in line:
                results['requests_per_sec'] = line.split(':')[1].strip()
            elif 'Transfer/sec:' in line:
                results['transfer_per_sec'] = line.split(':')[1].strip()
            elif 'Latency' in line and 'avg' in line:
                # Parse latency line: "Latency     4.98ms   5.12ms  19.25ms   94.32%"
                parts = line.split()
                if len(parts) >= 4:
                    results['avg_latency'] = parts[1]
                    results['p99_latency'] = parts[3] if len(parts) > 3 else parts[2]

        return results

    def benchmark_endpoint(self, framework: str, endpoint: Dict[str, Any], category: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Benchmark a single endpoint"""
        port = config["port"]
        url = f"http://127.0.0.1:{port}{endpoint['path']}"

        self.print_status(f"Benchmarking {framework} {endpoint['name']} endpoint...")

        # Warmup request
        try:
            requests.get(url, timeout=5)
        except:
            pass

        # Run benchmark
        results = self.run_wrk_benchmark(url)

        if "error" in results:
            self.print_error(f"Benchmark failed for {framework} {endpoint['name']}: {results['error']}")
            return None

        # Structure result data (compatible with old format)
        result = {
            "framework": framework,
            "category": category,
            "endpoint": endpoint["path"],
            "endpoint_name": endpoint["name"],
            "method": endpoint.get("method", "GET"),
            "duration": self.duration,
            "connections": self.connections,
            "threads": self.threads,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            **results
        }

        self.results.append(result)
        self.print_success(f"{framework} {endpoint['name']}: {results.get('requests_per_sec', 'N/A')} req/s")
        return result

    def benchmark_category(self, category: str, frameworks: List[str] = None) -> List[Dict[str, Any]]:
        """Benchmark all endpoints in a category"""
        if category not in self.feature_categories:
            self.print_error(f"Unknown category: {category}")
            return []

        category_config = self.feature_categories[category]
        frameworks = frameworks or list(category_config["servers"].keys())
        category_results = []

        self.print_category(f"Starting {category.upper()} benchmarks")
        print("=" * 60)

        # Start all servers for this category
        started_servers = {}
        for framework in frameworks:
            if framework in category_config["servers"]:
                server_config = category_config["servers"][framework]
                if self.start_server(framework, server_config, category):
                    started_servers[framework] = server_config
                else:
                    self.print_error(f"Failed to start {framework} server for {category}")

        if not started_servers:
            self.print_error(f"No servers started for {category} category")
            return []

        # Benchmark each endpoint for each framework
        for endpoint in category_config["endpoints"]:
            self.print_status(f"Testing endpoint: {endpoint['name']} ({endpoint['path']})")

            for framework, server_config in started_servers.items():
                result = self.benchmark_endpoint(framework, endpoint, category, server_config)
                if result:
                    category_results.append(result)

            print()  # Add spacing between endpoints

        # Stop all servers for this category
        for framework in started_servers.keys():
            self.stop_server(f"{category}_{framework}")

        self.print_success(f"Completed {category.upper()} benchmarks: {len(category_results)} results")
        return category_results

    def save_results(self):
        """Save benchmark results in the same format as old system"""
        timestamp = datetime.utcnow().isoformat() + "Z"

        # Create summary data structure (compatible with old format)
        summary = {
            "benchmark_info": {
                "timestamp": timestamp,
                "duration": self.duration,
                "connections": self.connections,
                "threads": self.threads,
                "tool": "wrk",
                "system": "feature_based"
            },
            "categories_tested": list(set(r["category"] for r in self.results)),
            "total_results": len(self.results),
            "results": self.results
        }

        # Save JSON summary
        summary_file = os.path.join(self.results_dir, "benchmark_summary.json")
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)

        # Save individual result files (compatible with old system)
        for result in self.results:
            filename = f"{result['framework']}_{result['endpoint_name']}.json"
            filepath = os.path.join(self.results_dir, filename)
            with open(filepath, 'w') as f:
                json.dump(result, f, indent=2)

        self.print_success(f"Results saved to {self.results_dir}")
        self.print_status(f"Summary file: {summary_file}")

    def cleanup(self):
        """Clean up any running processes"""
        for server_key in list(self.processes.keys()):
            self.stop_server(server_key)

    def run_benchmarks(self, categories: List[str] = None, frameworks: List[str] = None):
        """Run benchmarks for specified categories and frameworks"""
        categories = categories or ["basic"]  # Default to basic for compatibility

        self.print_status("Starting Feature-Based Benchmark Runner")
        print(f"{CYAN}Categories: {', '.join(categories)}{NC}")
        print(f"{CYAN}Duration: {self.duration}, Connections: {self.connections}, Threads: {self.threads}{NC}")
        print("=" * 80)

        try:
            for category in categories:
                category_results = self.benchmark_category(category, frameworks)
                self.results.extend(category_results)
                print()  # Add spacing between categories

            self.save_results()

            # Print final summary
            print(f"\n{GREEN}🎉 BENCHMARK COMPLETED!{NC}")
            print(f"Total results: {len(self.results)}")
            print(f"Categories tested: {len(set(r['category'] for r in self.results))}")
            print(f"Frameworks tested: {len(set(r['framework'] for r in self.results))}")

        except KeyboardInterrupt:
            self.print_warning("Benchmark interrupted by user")
        except Exception as e:
            self.print_error(f"Benchmark failed: {e}")
        finally:
            self.cleanup()

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Feature-Based Benchmark Runner')
    parser.add_argument('--categories', nargs='+', choices=['basic', 'middleware', 'dependency_injection', 'async_operations'],
                       default=['basic'], help='Categories to benchmark')
    parser.add_argument('--frameworks', nargs='+', help='Frameworks to test (default: all available)')
    parser.add_argument('--duration', default='10s', help='Test duration (default: 10s)')
    parser.add_argument('--connections', type=int, default=100, help='Concurrent connections (default: 100)')
    parser.add_argument('--threads', type=int, default=4, help='Number of threads (default: 4)')

    args = parser.parse_args()

    # Get benchmark directory
    benchmark_dir = os.path.dirname(os.path.abspath(__file__))

    # Create runner
    runner = FeatureBenchmarkRunner(benchmark_dir)
    runner.duration = args.duration
    runner.connections = args.connections
    runner.threads = args.threads

    # Run benchmarks
    runner.run_benchmarks(args.categories, args.frameworks)

if __name__ == "__main__":
    main()
