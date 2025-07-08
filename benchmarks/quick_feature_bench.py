#!/usr/bin/env python3
"""
Feature Benchmark Runner

Quick benchmark of the new feature endpoints we added.
"""

import requests
import time
import json
import subprocess
import os
import signal

def start_server(framework, port, script):
    """Start a server process"""
    cmd = ['python', f'servers/{script}', '--port', str(port)]
    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        preexec_fn=os.setsid
    )

    # Wait for server to start
    time.sleep(3)

    # Test if server is responsive
    try:
        response = requests.get(f"http://127.0.0.1:{port}/health", timeout=5)
        if response.status_code == 200:
            print(f"✅ {framework} server started on port {port}")
            return process
        else:
            print(f"❌ {framework} server not responding")
            return None
    except:
        print(f"❌ Failed to start {framework} server")
        return None

def stop_server(process):
    """Stop a server process"""
    if process:
        try:
            os.killpg(os.getpgid(process.pid), signal.SIGTERM)
            process.wait(timeout=5)
        except:
            try:
                os.killpg(os.getpgid(process.pid), signal.SIGKILL)
            except:
                pass

def benchmark_endpoint(framework, port, endpoint, method='GET', data=None):
    """Simple benchmark of an endpoint"""
    url = f"http://127.0.0.1:{port}{endpoint}"
    times = []
    errors = 0

    # Warm up
    for _ in range(5):
        try:
            if method == 'GET':
                requests.get(url, timeout=5)
            else:
                requests.post(url, json=data, timeout=5)
        except:
            pass

    # Benchmark
    for _ in range(100):
        start_time = time.time()
        try:
            if method == 'GET':
                response = requests.get(url, timeout=5)
            else:
                response = requests.post(url, json=data, timeout=5)

            if response.status_code == 200:
                times.append(time.time() - start_time)
            else:
                errors += 1
        except:
            errors += 1

    if times:
        avg_time = sum(times) / len(times) * 1000  # Convert to ms
        rps = len(times) / sum(times) if sum(times) > 0 else 0
        return rps, avg_time, errors
    else:
        return 0, 0, errors

def main():
    """Run feature benchmarks"""
    frameworks = [
        ('catzilla', 8000, 'catzilla_server.py'),
        ('fastapi', 8001, 'fastapi_server.py'),
        ('flask', 8002, 'flask_server.py'),
        ('django', 8003, 'django_server.py')
    ]

    feature_endpoints = [
        ('routing_static', '/bench/routing/static', 'GET', None),
        ('routing_path', '/bench/routing/path/123', 'GET', None),
        ('validation_simple', '/bench/validation/simple', 'POST', {'id': 1, 'name': 'John', 'email': 'john@example.com'}),
        ('di_simple', '/bench/di/simple', 'GET', None),
        ('streaming_json', '/bench/streaming/json?count=10', 'GET', None)
    ]

    print("🚀 Feature Endpoint Benchmark")
    print("=" * 50)

    results = {}

    for framework, port, script in frameworks:
        print(f"\n📊 Testing {framework.upper()}...")

        # Start server
        process = start_server(framework, port, script)
        if not process:
            continue

        framework_results = {}

        try:
            for feature_name, endpoint, method, data in feature_endpoints:
                print(f"  Testing {feature_name}...", end=' ')
                rps, avg_time, errors = benchmark_endpoint(framework, port, endpoint, method, data)
                framework_results[feature_name] = {
                    'rps': round(rps, 2),
                    'avg_time_ms': round(avg_time, 2),
                    'errors': errors
                }
                print(f"{rps:.0f} req/s, {avg_time:.1f}ms avg")

        finally:
            stop_server(process)

        results[framework] = framework_results

    # Print summary
    print("\n" + "=" * 70)
    print("📊 FEATURE BENCHMARK SUMMARY")
    print("=" * 70)

    for feature_name, _, _, _ in feature_endpoints:
        print(f"\n🎯 {feature_name.replace('_', ' ').title()}:")
        feature_results = []
        for framework in ['catzilla', 'fastapi', 'flask', 'django']:
            if framework in results and feature_name in results[framework]:
                rps = results[framework][feature_name]['rps']
                feature_results.append((framework, rps))

        # Sort by RPS
        feature_results.sort(key=lambda x: x[1], reverse=True)

        medals = ['🥇', '🥈', '🥉', '  ']
        for i, (framework, rps) in enumerate(feature_results):
            medal = medals[i] if i < len(medals) else '  '
            print(f"  {medal} {framework.upper()}: {rps:.0f} req/s")

if __name__ == "__main__":
    main()
