#!/usr/bin/env python3
"""
Comprehensive Feature Endpoint Test

Tests all feature endpoints across Catzilla, FastAPI, Flask, and Django
to ensure they are working correctly before running benchmarks.
"""

import requests
import json
import time
import subprocess
import signal
import os
from typing import Dict, List, Optional
import sys

# Color codes for output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

class FrameworkTester:
    """Tests all feature endpoints for each framework"""

    def __init__(self):
        self.frameworks = {
            'catzilla': {'port': 8000, 'script': 'servers/catzilla_server.py'},
            'fastapi': {'port': 8001, 'script': 'servers/fastapi_server.py'},
            'flask': {'port': 8002, 'script': 'servers/flask_server.py'},
            'django': {'port': 8003, 'script': 'servers/django_server.py'}
        }

        self.feature_endpoints = {
            'routing': [
                {'path': '/bench/routing/static', 'method': 'GET'},
                {'path': '/bench/routing/path/123', 'method': 'GET'},
                {'path': '/bench/routing/path/electronics/456', 'method': 'GET'},
                {'path': '/bench/routing/query?limit=20&offset=10&sort=price', 'method': 'GET'}
            ],
            'validation': [
                {
                    'path': '/bench/validation/simple',
                    'method': 'POST',
                    'data': {'id': 1, 'name': 'John Doe', 'email': 'john@example.com'}
                },
                {
                    'path': '/bench/validation/complex',
                    'method': 'POST',
                    'data': {'id': 2, 'name': 'Jane Doe', 'email': 'jane@example.com', 'age': 30, 'is_active': True}
                },
                {
                    'path': '/bench/validation/product',
                    'method': 'POST',
                    'data': {'name': 'Laptop', 'price': 999.99, 'category': 'Electronics', 'in_stock': True}
                },
                {'path': '/bench/validation/query?query=test&limit=10&offset=0&sort_by=name', 'method': 'GET'}
            ],
            'dependency_injection': [
                {'path': '/bench/di/simple', 'method': 'GET'},
                {'path': '/bench/di/nested/42', 'method': 'GET'}
            ],
            'background_tasks': [
                {'path': '/bench/background/simple', 'method': 'POST'},
                {'path': '/bench/background/stats', 'method': 'GET'}
            ],
            'file_upload': [
                {'path': '/bench/upload/simple', 'method': 'POST'},
                {'path': '/bench/upload/stats', 'method': 'GET'}
            ],
            'streaming': [
                {'path': '/bench/streaming/json?count=10', 'method': 'GET'},
                {'path': '/bench/streaming/csv?count=5', 'method': 'GET'}
            ]
        }

        self.processes = {}
        self.results = {}

    def start_server(self, framework: str) -> bool:
        """Start a framework server"""
        config = self.frameworks[framework]

        print(f"{BLUE}Starting {framework} server on port {config['port']}...{RESET}")

        try:
            # Kill any existing process on this port
            os.system(f"pkill -f {config['script']} > /dev/null 2>&1")
            time.sleep(1)

            # Start the server
            cmd = ['python', config['script'], '--port', str(config['port'])]
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                preexec_fn=os.setsid
            )

            self.processes[framework] = process

            # Wait for server to start
            time.sleep(3)

            # Test if server is responsive
            response = requests.get(f"http://127.0.0.1:{config['port']}/health", timeout=5)
            if response.status_code == 200:
                print(f"{GREEN}✅ {framework} server started successfully{RESET}")
                return True
            else:
                print(f"{RED}❌ {framework} server not responding{RESET}")
                return False

        except Exception as e:
            print(f"{RED}❌ Failed to start {framework} server: {e}{RESET}")
            return False

    def stop_server(self, framework: str):
        """Stop a framework server"""
        if framework in self.processes:
            try:
                os.killpg(os.getpgid(self.processes[framework].pid), signal.SIGTERM)
                self.processes[framework].wait(timeout=5)
            except:
                try:
                    os.killpg(os.getpgid(self.processes[framework].pid), signal.SIGKILL)
                except:
                    pass
            del self.processes[framework]

    def test_endpoint(self, framework: str, endpoint_config: Dict) -> Dict:
        """Test a single endpoint"""
        config = self.frameworks[framework]
        base_url = f"http://127.0.0.1:{config['port']}"
        url = base_url + endpoint_config['path']

        try:
            if endpoint_config['method'] == 'GET':
                response = requests.get(url, timeout=10)
            elif endpoint_config['method'] == 'POST':
                if 'data' in endpoint_config:
                    response = requests.post(url, json=endpoint_config['data'], timeout=10)
                else:
                    response = requests.post(url, timeout=10)

            return {
                'status_code': response.status_code,
                'success': response.status_code == 200,
                'response_time': response.elapsed.total_seconds(),
                'data': response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text[:100]
            }

        except Exception as e:
            return {
                'status_code': 0,
                'success': False,
                'response_time': 0,
                'error': str(e)
            }

    def test_framework(self, framework: str) -> Dict:
        """Test all endpoints for a framework"""
        print(f"\n{YELLOW}Testing {framework.upper()} framework{RESET}")
        print("=" * 50)

        if not self.start_server(framework):
            return {'success': False, 'error': 'Failed to start server'}

        framework_results = {}
        total_tests = 0
        passed_tests = 0

        try:
            for feature_name, endpoints in self.feature_endpoints.items():
                print(f"\n{BLUE}Testing {feature_name} endpoints:{RESET}")
                feature_results = []

                for endpoint_config in endpoints:
                    total_tests += 1
                    result = self.test_endpoint(framework, endpoint_config)

                    if result['success']:
                        print(f"  {GREEN}✅ {endpoint_config['method']} {endpoint_config['path']}{RESET}")
                        passed_tests += 1
                    else:
                        error_msg = result.get('error', f"Status: {result['status_code']}")
                        print(f"  {RED}❌ {endpoint_config['method']} {endpoint_config['path']} - {error_msg}{RESET}")

                    feature_results.append({
                        'endpoint': endpoint_config,
                        'result': result
                    })

                framework_results[feature_name] = feature_results

        finally:
            self.stop_server(framework)

        success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
        print(f"\n{YELLOW}Framework Summary: {passed_tests}/{total_tests} tests passed ({success_rate:.1f}%){RESET}")

        return {
            'success': success_rate == 100,
            'total_tests': total_tests,
            'passed_tests': passed_tests,
            'success_rate': success_rate,
            'features': framework_results
        }

    def run_all_tests(self):
        """Run tests for all frameworks"""
        print(f"{BLUE}🚀 Starting Comprehensive Feature Endpoint Tests{RESET}")
        print("=" * 60)

        overall_results = {}

        for framework in self.frameworks.keys():
            try:
                result = self.test_framework(framework)
                overall_results[framework] = result
            except KeyboardInterrupt:
                print(f"\n{YELLOW}Tests interrupted by user{RESET}")
                break
            except Exception as e:
                print(f"{RED}Error testing {framework}: {e}{RESET}")
                overall_results[framework] = {'success': False, 'error': str(e)}

        # Print overall summary
        print(f"\n{BLUE}📊 OVERALL TEST SUMMARY{RESET}")
        print("=" * 60)

        for framework, result in overall_results.items():
            if result.get('success'):
                print(f"{GREEN}✅ {framework.upper()}: {result['passed_tests']}/{result['total_tests']} tests passed{RESET}")
            else:
                print(f"{RED}❌ {framework.upper()}: FAILED - {result.get('error', 'Some tests failed')}{RESET}")

        # Cleanup any remaining processes
        for framework in self.frameworks.keys():
            self.stop_server(framework)

        return overall_results

def main():
    """Main test runner"""
    tester = FrameworkTester()

    try:
        results = tester.run_all_tests()

        # Check if all frameworks passed
        all_passed = all(result.get('success', False) for result in results.values())

        if all_passed:
            print(f"\n{GREEN}🎉 ALL TESTS PASSED! The benchmarking system is ready.{RESET}")
            sys.exit(0)
        else:
            print(f"\n{RED}⚠️  Some tests failed. Please check the results above.{RESET}")
            sys.exit(1)

    except KeyboardInterrupt:
        print(f"\n{YELLOW}Tests interrupted by user{RESET}")
        sys.exit(1)

if __name__ == "__main__":
    main()
