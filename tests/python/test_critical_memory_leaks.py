"""
🚨 CRITICAL PRIORITY 3: Memory Leak Detection Tests

Tests that MUST pass to ensure Catzilla doesn't have memory leaks in production:
1. Request/response lifecycle memory cleanup
2. DI container memory management
3. Long-running server memory stability
4. High-frequency request memory behavior
5. Large payload memory handling

These tests validate that Catzilla properly manages memory without leaks
that could cause production servers to crash from OOM conditions.
"""

import pytest
import time
import threading
import requests
import json
import subprocess
import sys
import os
import gc
import resource
from typing import Optional, Dict, Any, List
from unittest.mock import Mock, patch

# Import Catzilla components
try:
    from catzilla import Catzilla, service, Depends
    from catzilla.validation import BaseModel
    from catzilla.dependency_injection import AdvancedDIContainer
    from catzilla.types import Request, Response, JSONResponse
except ImportError:
    pytest.skip("Catzilla modules not available", allow_module_level=True)


class MemoryMonitor:
    """Helper class to monitor memory usage using resource module and subprocess"""

    def __init__(self, process_pid: Optional[int] = None):
        self.process_pid = process_pid
        self.initial_memory = self.get_memory_mb()
        self.peak_memory = self.initial_memory
        self.samples = [self.initial_memory]

    def get_memory_mb(self) -> float:
        """Get current memory usage in MB"""
        try:
            if self.process_pid:
                # Monitor external process using ps command
                try:
                    result = subprocess.run(
                        ['ps', '-p', str(self.process_pid), '-o', 'rss='],
                        capture_output=True, text=True, timeout=5
                    )
                    if result.returncode == 0 and result.stdout.strip():
                        # RSS is in KB on macOS, convert to MB
                        rss_kb = int(result.stdout.strip())
                        return rss_kb / 1024.0
                except (subprocess.TimeoutExpired, ValueError, subprocess.SubprocessError):
                    pass
                return 0.0
            else:
                # Monitor current process using resource module
                usage = resource.getrusage(resource.RUSAGE_SELF)
                # On macOS, ru_maxrss is in bytes, on Linux it's in KB
                # We'll assume bytes and convert to MB
                return usage.ru_maxrss / (1024 * 1024)
        except Exception:
            return 0.0

    def sample(self):
        """Take a memory sample"""
        current = self.get_memory_mb()
        self.samples.append(current)
        if current > self.peak_memory:
            self.peak_memory = current
        return current

    def get_stats(self) -> Dict[str, float]:
        """Get memory statistics"""
        if not self.samples:
            return {"initial": 0, "current": 0, "peak": 0, "growth": 0}

        current = self.samples[-1]
        growth = current - self.initial_memory

        return {
            "initial": self.initial_memory,
            "current": current,
            "peak": self.peak_memory,
            "growth": growth,
            "samples": len(self.samples)
        }


class TestCriticalMemoryLeaks:
    """Tests that MUST work for production memory safety"""

    def setup_method(self):
        """Setup for each test method"""
        import socket
        self.test_port = 9500  # Different port range for memory tests
        self.active_servers = []
        self.memory_monitors = []

    def teardown_method(self):
        """Cleanup after each test"""
        # Stop any remaining servers
        for server_info in self.active_servers:
            try:
                if 'process' in server_info and server_info['process']:
                    server_info['process'].terminate()
                    try:
                        server_info['process'].wait(timeout=3)
                    except subprocess.TimeoutExpired:
                        server_info['process'].kill()
                        server_info['process'].wait()

                    # Clean up script file
                    if 'script_path' in server_info:
                        try:
                            os.remove(server_info['script_path'])
                        except:
                            pass
            except:
                pass
        self.active_servers.clear()

        # Clean up memory monitors
        self.memory_monitors.clear()

        # Force garbage collection
        gc.collect()

        # Give extra time for cleanup and memory release
        time.sleep(2.0)

    def get_next_port(self) -> int:
        """Get next available test port with better conflict avoidance"""
        import socket
        import random
        import time

        # Use a wider range and add randomization to avoid conflicts
        # Use timestamp-based port range to ensure uniqueness across test runs
        timestamp_offset = int(time.time()) % 1000
        base_port = 9000 + timestamp_offset + random.randint(0, 100)

        for port in range(base_port, base_port + 500):  # Much wider search range
            try:
                # Test both TCP and check if anything is listening
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                sock.settimeout(1.0)
                result = sock.connect_ex(('localhost', port))
                sock.close()

                if result != 0:  # Port is not in use
                    # Double-check by trying to bind
                    try:
                        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                        sock.bind(('localhost', port))
                        sock.close()
                        self.test_port = port + 10  # Bigger gap to avoid conflicts
                        return port
                    except OSError:
                        continue
            except OSError:
                continue

        raise RuntimeError("No available ports found in range")

    def start_memory_test_server(self, app_code: str, port: int, timeout: float = 30.0) -> subprocess.Popen:
        """Start a test server for memory testing with robust startup"""
        script = f'''
import sys
import os
import time
import signal
sys.path.insert(0, "{os.path.dirname(os.path.dirname(os.path.dirname(__file__)))}")

from catzilla import Catzilla, service, Depends, JSONResponse
import time
import gc

{app_code}

def signal_handler(signum, frame):
    print("Memory test server shutting down gracefully...")
    sys.exit(0)

signal.signal(signal.SIGTERM, signal_handler)
signal.signal(signal.SIGINT, signal_handler)

if __name__ == "__main__":
    try:
        print(f"Starting memory test server on port {port}", flush=True)
        # Force garbage collection before starting
        gc.collect()
        # Add delay for proper initialization
        time.sleep(0.5)
        app.listen(port={port})
    except KeyboardInterrupt:
        print("Memory test server stopped by keyboard interrupt")
    except Exception as e:
        print(f"Memory test server error: {{e}}", flush=True)
        import traceback
        traceback.print_exc()
        sys.exit(1)
'''

        # Write script to temporary file with unique name
        script_path = f"/tmp/memory_test_server_{port}_{int(time.time())}.py"
        with open(script_path, 'w') as f:
            f.write(script)

        # Start subprocess
        process = subprocess.Popen([
            sys.executable, script_path
        ], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)

        # Track for cleanup
        self.active_servers.append({
            'process': process,
            'port': port,
            'script_path': script_path
        })

        # Wait for server to start with multiple health checks
        start_time = time.time()
        last_error = None
        health_checks_passed = 0
        required_health_checks = 2  # Reduced for faster tests

        while time.time() - start_time < timeout:
            if process.poll() is not None:
                output, _ = process.communicate()
                raise RuntimeError(f"Memory test server process died: {output}")

            try:
                response = requests.get(f"http://localhost:{port}/health", timeout=5)  # Increased timeout
                if response.status_code == 200:
                    health_checks_passed += 1
                    if health_checks_passed >= required_health_checks:
                        print(f"Memory test server started successfully on port {port}")
                        time.sleep(1.0)  # Additional stabilization time
                        return process
                    else:
                        time.sleep(0.5)  # Longer pause between checks
                else:
                    health_checks_passed = 0
                    time.sleep(0.5)
            except Exception as e:
                last_error = e
                health_checks_passed = 0
                time.sleep(1.0)  # Longer wait on error

        # Server failed to start
        try:
            process.terminate()
            output, _ = process.communicate(timeout=5)  # Increased timeout
        except:
            process.kill()
            output = "Process killed due to timeout"

        raise RuntimeError(f"Memory test server failed to start on port {port} within {timeout}s. Last error: {last_error}. Output: {output}")

    def test_request_response_memory_cleanup(self):
        """CRITICAL: Ensure request/response objects are properly cleaned up"""
        port = self.get_next_port()

        app_code = '''
from catzilla import Catzilla, JSONResponse
from catzilla.dependency_injection import set_default_container, clear_default_container
import gc

# Clear any existing default container
clear_default_container()
app = Catzilla(enable_di=True)
set_default_container(app.di_container)

# Counter to track requests
request_count = 0

@app.get("/health")
def health(request):
    return JSONResponse({"status": "ok"})

@app.get("/memory_test")
def memory_test(request):
    global request_count
    request_count += 1

    # Create some objects that should be cleaned up
    data = {
        "request_id": request_count,
        "large_data": "x" * 1000,  # 1KB of data
        "nested": {
            "level1": {"level2": {"level3": "data"}}
        },
        "list_data": list(range(100))
    }

    return JSONResponse(data)

@app.get("/gc_collect")
def gc_collect(request):
    # Force garbage collection
    collected = gc.collect()
    return JSONResponse({
        "collected": collected,
        "request_count": request_count
    })

@app.get("/stats")
def stats(request):
    return JSONResponse({
        "request_count": request_count,
        "gc_stats": {
            "counts": gc.get_counts(),
            "stats": [{"collections": s.collections, "collected": s.collected, "uncollectable": s.uncollectable} for s in gc.get_stats()]
        }
    })
'''

        # Start server
        process = self.start_memory_test_server(app_code, port)

        try:
            # Get initial memory baseline
            server_monitor = MemoryMonitor(process.pid)

            # Warm up with a few requests
            for _ in range(5):
                response = requests.get(f"http://localhost:{port}/memory_test", timeout=5)
                assert response.status_code == 200

            # Force garbage collection on server
            gc_response = requests.get(f"http://localhost:{port}/gc_collect", timeout=5)
            assert gc_response.status_code == 200

            # Wait for cleanup
            time.sleep(1)
            baseline_memory = server_monitor.sample()

            # Make many requests to test memory cleanup
            num_requests = 100
            for i in range(num_requests):
                response = requests.get(f"http://localhost:{port}/memory_test", timeout=5)
                assert response.status_code == 200

                # Sample memory every 10 requests
                if i % 10 == 0:
                    server_monitor.sample()

            # Force garbage collection again
            gc_response = requests.get(f"http://localhost:{port}/gc_collect", timeout=5)
            assert gc_response.status_code == 200
            gc_data = gc_response.json()
            print(f"GC collected {gc_data['collected']} objects after {gc_data['request_count']} requests")

            # Wait for cleanup and take final measurement
            time.sleep(2)
            final_memory = server_monitor.sample()

            # Get statistics
            stats = server_monitor.get_stats()
            print(f"Memory stats: {stats}")

            # Memory growth should be reasonable (< 50MB for 100 requests)
            memory_growth = final_memory - baseline_memory
            print(f"Memory growth: {memory_growth:.2f} MB for {num_requests} requests")

            # Check that memory didn't grow excessively
            max_acceptable_growth = 50.0  # 50MB
            assert memory_growth < max_acceptable_growth, f"Excessive memory growth: {memory_growth:.2f} MB"

            # Verify server is still responsive
            response = requests.get(f"http://localhost:{port}/health", timeout=5)
            assert response.status_code == 200

            print("✅ Request/response memory cleanup: PASSED")

        finally:
            process.terminate()
            try:
                process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()

    def test_di_container_memory_management(self):
        """CRITICAL: Ensure DI containers don't leak memory"""
        port = self.get_next_port()

        app_code = '''
from catzilla import Catzilla, service, Depends, JSONResponse
from catzilla.dependency_injection import set_default_container, clear_default_container
import gc

# Clear any existing default container
clear_default_container()
app = Catzilla(enable_di=True)
set_default_container(app.di_container)

@service("data_service")
class DataService:
    def __init__(self):
        self.data = {}
        self.access_count = 0

    def store_data(self, key: str, value: str):
        self.data[key] = value
        self.access_count += 1
        return len(self.data)

    def get_stats(self):
        return {
            "data_count": len(self.data),
            "access_count": self.access_count
        }

@service("temp_service")  # Service that creates temporary objects
class TempService:
    def __init__(self):
        self.temp_objects = []

    def create_temp_data(self, size: int = 1000):
        # Create temporary data that should be cleaned up
        temp_data = {
            "temp_id": len(self.temp_objects),
            "data": "x" * size,
            "nested": {"level": i for i in range(10)}
        }
        self.temp_objects.append(temp_data)

        # Keep only last 10 objects to prevent unbounded growth
        if len(self.temp_objects) > 10:
            self.temp_objects = self.temp_objects[-10:]

        return temp_data

@app.get("/health")
def health(request):
    return JSONResponse({"status": "ok"})

@app.get("/di_test")
def di_test(request,
           data_service: DataService = Depends("data_service"),
           temp_service: TempService = Depends("temp_service")):

    # Store some data
    data_count = data_service.store_data(f"key_{data_service.access_count}", f"value_{data_service.access_count}")

    # Create temporary data
    temp_data = temp_service.create_temp_data()

    return JSONResponse({
        "data_count": data_count,
        "temp_id": temp_data["temp_id"],
        "access_count": data_service.access_count
    })

@app.get("/di_stats")
def di_stats(request, data_service: DataService = Depends("data_service")):
    return JSONResponse(data_service.get_stats())

@app.get("/gc_collect")
def gc_collect(request):
    collected = gc.collect()
    return JSONResponse({"collected": collected})
'''

        # Start server
        process = self.start_memory_test_server(app_code, port)

        try:
            # Get initial memory baseline
            server_monitor = MemoryMonitor(process.pid)

            # Warm up
            for _ in range(5):
                response = requests.get(f"http://localhost:{port}/di_test", timeout=5)
                assert response.status_code == 200

            # Force GC and get baseline
            requests.get(f"http://localhost:{port}/gc_collect", timeout=5)
            time.sleep(1)
            baseline_memory = server_monitor.sample()

            # Make many DI requests
            num_requests = 200
            for i in range(num_requests):
                response = requests.get(f"http://localhost:{port}/di_test", timeout=5)
                assert response.status_code == 200

                if i % 20 == 0:
                    server_monitor.sample()

            # Check DI stats
            stats_response = requests.get(f"http://localhost:{port}/di_stats", timeout=5)
            assert stats_response.status_code == 200
            di_stats = stats_response.json()
            print(f"DI Stats: {di_stats}")

            # Force garbage collection
            gc_response = requests.get(f"http://localhost:{port}/gc_collect", timeout=5)
            gc_data = gc_response.json()
            print(f"GC collected {gc_data['collected']} objects")

            # Final memory measurement
            time.sleep(2)
            final_memory = server_monitor.sample()

            # Get statistics
            stats = server_monitor.get_stats()
            print(f"DI Memory stats: {stats}")

            # Memory growth should be reasonable for DI operations
            memory_growth = final_memory - baseline_memory
            print(f"DI Memory growth: {memory_growth:.2f} MB for {num_requests} DI requests")

            # DI should not cause excessive memory growth (< 30MB for 200 requests)
            max_acceptable_growth = 30.0
            assert memory_growth < max_acceptable_growth, f"Excessive DI memory growth: {memory_growth:.2f} MB"

            print("✅ DI container memory management: PASSED")

        finally:
            process.terminate()
            try:
                process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()

    def test_long_running_server_memory_stability(self):
        """CRITICAL: Ensure server memory is stable over time"""
        port = self.get_next_port()

        app_code = '''
from catzilla import Catzilla, service, Depends, JSONResponse
from catzilla.dependency_injection import set_default_container, clear_default_container
import time
import gc

clear_default_container()
app = Catzilla(enable_di=True)
set_default_container(app.di_container)

@service("session_manager")
class SessionManager:
    def __init__(self):
        self.sessions = {}
        self.session_count = 0

    def create_session(self):
        self.session_count += 1
        session_id = f"session_{self.session_count}"
        self.sessions[session_id] = {
            "created": time.time(),
            "data": {"user": f"user_{self.session_count}"}
        }

        # Clean up old sessions (keep only last 50)
        if len(self.sessions) > 50:
            oldest_sessions = sorted(self.sessions.items(), key=lambda x: x[1]["created"])
            for session_id, _ in oldest_sessions[:-50]:
                del self.sessions[session_id]

        return session_id

    def get_stats(self):
        return {
            "active_sessions": len(self.sessions),
            "total_created": self.session_count
        }

@app.get("/health")
def health(request):
    return JSONResponse({"status": "ok"})

@app.get("/session")
def create_session(request, manager: SessionManager = Depends("session_manager")):
    session_id = manager.create_session()
    return JSONResponse({"session_id": session_id})

@app.get("/session_stats")
def session_stats(request, manager: SessionManager = Depends("session_manager")):
    return JSONResponse(manager.get_stats())

@app.get("/gc_collect")
def gc_collect(request):
    collected = gc.collect()
    return JSONResponse({"collected": collected})
'''

        # Start server
        process = self.start_memory_test_server(app_code, port)

        try:
            # Monitor server memory over time
            server_monitor = MemoryMonitor(process.pid)

            # Get baseline
            baseline_memory = server_monitor.sample()
            print(f"Baseline memory: {baseline_memory:.2f} MB")

            # Run for multiple phases to simulate long-running behavior
            phases = [
                {"name": "Light Load", "requests": 50, "interval": 0.05},
                {"name": "Medium Load", "requests": 100, "interval": 0.02},
                {"name": "Heavy Load", "requests": 200, "interval": 0.01},
                {"name": "Cool Down", "requests": 50, "interval": 0.1}
            ]

            total_requests = 0

            for phase in phases:
                print(f"\n--- {phase['name']} Phase ---")
                phase_start_memory = server_monitor.sample()

                for i in range(phase["requests"]):
                    # Alternate between different endpoints
                    if i % 3 == 0:
                        endpoint = "/session"
                    elif i % 3 == 1:
                        endpoint = "/session_stats"
                    else:
                        endpoint = "/health"

                    response = requests.get(f"http://localhost:{port}{endpoint}", timeout=5)
                    assert response.status_code == 200

                    total_requests += 1

                    # Sample memory every 25 requests
                    if i % 25 == 0:
                        current_memory = server_monitor.sample()
                        print(f"  Request {total_requests}: {current_memory:.2f} MB")

                    time.sleep(phase["interval"])

                # Force GC between phases
                gc_response = requests.get(f"http://localhost:{port}/gc_collect", timeout=5)
                gc_data = gc_response.json()

                phase_end_memory = server_monitor.sample()
                phase_growth = phase_end_memory - phase_start_memory
                print(f"  Phase memory growth: {phase_growth:.2f} MB")
                print(f"  GC collected: {gc_data['collected']} objects")

                # Wait between phases
                time.sleep(1)

            # Final measurements
            time.sleep(2)
            final_memory = server_monitor.sample()

            # Get final stats
            stats_response = requests.get(f"http://localhost:{port}/session_stats", timeout=5)
            session_stats = stats_response.json()
            print(f"\nFinal session stats: {session_stats}")

            # Memory analysis
            stats = server_monitor.get_stats()
            print(f"\nMemory analysis:")
            print(f"  Initial: {stats['initial']:.2f} MB")
            print(f"  Final: {stats['current']:.2f} MB")
            print(f"  Peak: {stats['peak']:.2f} MB")
            print(f"  Total growth: {stats['growth']:.2f} MB")
            print(f"  Total requests: {total_requests}")

            # Validate memory stability
            # Growth should be reasonable for long-running server
            max_acceptable_growth = 100.0  # 100MB for extended operation
            assert stats['growth'] < max_acceptable_growth, f"Excessive memory growth: {stats['growth']:.2f} MB"

            # Peak should not be dramatically higher than final
            peak_ratio = stats['peak'] / stats['current'] if stats['current'] > 0 else 1
            assert peak_ratio < 2.0, f"Memory peak too high compared to final: {peak_ratio:.2f}x"

            print("✅ Long-running server memory stability: PASSED")

        finally:
            process.terminate()
            try:
                process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()

    def test_high_frequency_request_memory_behavior(self):
        """CRITICAL: Test memory behavior under high-frequency requests"""
        port = self.get_next_port()

        app_code = '''
from catzilla import Catzilla, JSONResponse
from catzilla.dependency_injection import set_default_container, clear_default_container
import time
import gc

clear_default_container()
app = Catzilla(enable_di=True)
set_default_container(app.di_container)

request_counter = 0

@app.get("/health")
def health(request):
    return JSONResponse({"status": "ok"})

@app.get("/fast")
def fast_endpoint(request):
    global request_counter
    request_counter += 1
    return JSONResponse({"count": request_counter})

@app.post("/fast_post")
def fast_post(request):
    global request_counter
    request_counter += 1
    try:
        data = request.json()
        return JSONResponse({"received": len(str(data)), "count": request_counter})
    except:
        return JSONResponse({"received": 0, "count": request_counter})

@app.get("/stats")
def stats(request):
    return JSONResponse({"total_requests": request_counter})
'''

        # Start server
        process = self.start_memory_test_server(app_code, port)

        try:
            server_monitor = MemoryMonitor(process.pid)

            # Baseline
            baseline_memory = server_monitor.sample()

            # High-frequency test
            print("Starting high-frequency request test...")

            # Reduce requests in CI environments to prevent overload
            num_requests = 300 if os.environ.get('CI') else 500  # Restored original values
            success_count = 0
            error_count = 0

            start_time = time.time()

            for i in range(num_requests):
                try:
                    # Increase timeout slightly for CI environments
                    request_timeout = 3 if os.environ.get('CI') else 2

                    if i % 2 == 0:
                        # GET request
                        response = requests.get(f"http://localhost:{port}/fast", timeout=request_timeout)
                    else:
                        # POST request with small payload
                        response = requests.post(
                            f"http://localhost:{port}/fast_post",
                            json={"test": f"data_{i}"},
                            timeout=request_timeout
                        )

                    if response.status_code == 200:
                        success_count += 1
                    else:
                        error_count += 1

                except Exception as e:
                    error_count += 1
                    if error_count > num_requests * 0.15:  # More than 15% errors (increased tolerance)
                        print(f"Too many errors ({error_count}/{i+1}), stopping at request {i}")
                        break

                # Sample memory every 50 requests
                if i % 50 == 0:
                    current_memory = server_monitor.sample()
                    print(f"Request {i}: {current_memory:.2f} MB, Success: {success_count}, Errors: {error_count}")

                # Add small delay every 100 requests to prevent overwhelming
                if os.environ.get('CI') and i > 0 and i % 100 == 0:
                    time.sleep(0.1)

            end_time = time.time()
            duration = end_time - start_time

            # Allow server to cool down after high-frequency requests
            print("Allowing server to process remaining requests...")
            time.sleep(3)

            # Get final stats with retry logic
            stats_response = None
            for attempt in range(3):
                try:
                    stats_response = requests.get(f"http://localhost:{port}/stats", timeout=15)
                    if stats_response.status_code == 200:
                        break
                except requests.exceptions.RequestException as e:
                    print(f"Stats request attempt {attempt + 1} failed: {e}")
                    if attempt < 2:  # Not the last attempt
                        time.sleep(2)

            if stats_response and stats_response.status_code == 200:
                server_stats = stats_response.json()
                print(f"Server processed {server_stats['total_requests']} requests")

            # Final memory measurement
            time.sleep(1)
            final_memory = server_monitor.sample()

            # Performance analysis
            requests_per_second = success_count / duration if duration > 0 else 0
            print(f"\nHigh-frequency test results:")
            print(f"  Requests: {success_count}/{num_requests} successful")
            print(f"  Duration: {duration:.2f}s")
            print(f"  Rate: {requests_per_second:.1f} req/s")
            print(f"  Memory growth: {final_memory - baseline_memory:.2f} MB")

            # Validate performance and memory - Restored original expectations after performance fix
            assert success_count >= num_requests * 0.9, f"Too many failed requests: {success_count}/{num_requests}"  # Restored to 90%
            assert requests_per_second > 50, f"Request rate too low: {requests_per_second:.1f} req/s"  # Restored to 50 req/s

            # Memory growth should be reasonable for high-frequency requests
            memory_growth = final_memory - baseline_memory
            max_acceptable_growth = 50.0  # 50MB for full request count
            assert memory_growth < max_acceptable_growth, f"Excessive memory growth: {memory_growth:.2f} MB"

            print("✅ High-frequency request memory behavior: PASSED")

        finally:
            process.terminate()
            try:
                process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()

    def test_large_payload_memory_handling(self):
        """CRITICAL: Ensure large payloads don't cause memory leaks"""
        port = self.get_next_port()

        app_code = '''
from catzilla import Catzilla, JSONResponse
from catzilla.dependency_injection import set_default_container, clear_default_container
import gc

clear_default_container()
app = Catzilla(enable_di=True)

large_request_count = 0

@app.get("/health")
def health(request):
    return JSONResponse({"status": "ok"})

@app.post("/large_payload")
def handle_large_payload(request):
    global large_request_count
    large_request_count += 1

    try:
        data = request.json()

        # Process the large payload
        payload_size = len(str(data))

        # Create a response that confirms processing but doesn't echo the full payload
        response_data = {
            "processed": True,
            "payload_size": payload_size,
            "request_count": large_request_count,
            "sample_keys": list(data.keys())[:5] if isinstance(data, dict) else []
        }

        return JSONResponse(response_data)

    except Exception as e:
        return JSONResponse({"error": str(e), "request_count": large_request_count})

@app.get("/large_response/{size}")
def large_response(request):
    try:
        size = int(request.path_params.get("size", 1000))
        # Limit size to prevent test from consuming too much memory
        size = min(size, 100000)  # Max 100KB

        data = {
            "large_data": "x" * size,
            "metadata": {
                "size": size,
                "timestamp": "2024-01-01",
                "chunks": [f"chunk_{i}" for i in range(min(10, size // 1000))]
            }
        }

        return JSONResponse(data)

    except Exception as e:
        return JSONResponse({"error": str(e)})

@app.get("/gc_collect")
def gc_collect(request):
    collected = gc.collect()
    return JSONResponse({"collected": collected})
'''

        # Start server
        process = self.start_memory_test_server(app_code, port)

        try:
            server_monitor = MemoryMonitor(process.pid)
            baseline_memory = server_monitor.sample()

            print("Testing large payload handling...")

            # Test various payload sizes
            payload_sizes = [1000, 5000, 10000, 25000, 50000]  # 1KB to 50KB

            for size in payload_sizes:
                print(f"\nTesting payload size: {size} bytes")

                # Create large payload
                large_data = {
                    "data": "x" * size,
                    "metadata": {
                        "size": size,
                        "chunks": [f"chunk_{i}" for i in range(10)]
                    },
                    "array_data": list(range(100))
                }

                # Test uploading large payload
                before_memory = server_monitor.sample()

                response = requests.post(
                    f"http://localhost:{port}/large_payload",
                    json=large_data,
                    timeout=10
                )

                assert response.status_code == 200
                response_data = response.json()
                print(f"  Processed payload of {response_data['payload_size']} bytes")

                # Test downloading large response
                response = requests.get(f"http://localhost:{port}/large_response/{size}", timeout=10)
                assert response.status_code == 200

                after_memory = server_monitor.sample()
                memory_delta = after_memory - before_memory
                print(f"  Memory delta for {size}B: {memory_delta:.2f} MB")

                # Force garbage collection
                gc_response = requests.get(f"http://localhost:{port}/gc_collect", timeout=5)
                gc_data = gc_response.json()

                after_gc_memory = server_monitor.sample()
                print(f"  Memory after GC: {after_gc_memory:.2f} MB (collected {gc_data['collected']} objects)")

                # Brief pause between tests
                time.sleep(0.5)

            # Final memory check
            time.sleep(2)
            final_memory = server_monitor.sample()

            # Memory analysis
            stats = server_monitor.get_stats()
            print(f"\nLarge payload memory analysis:")
            print(f"  Initial: {stats['initial']:.2f} MB")
            print(f"  Final: {stats['current']:.2f} MB")
            print(f"  Peak: {stats['peak']:.2f} MB")
            print(f"  Growth: {stats['growth']:.2f} MB")

            # Validate memory behavior
            # Growth should be reasonable even with large payloads
            max_acceptable_growth = 75.0  # 75MB for large payload tests
            assert stats['growth'] < max_acceptable_growth, f"Excessive memory growth: {stats['growth']:.2f} MB"

            # Server should still be responsive
            response = requests.get(f"http://localhost:{port}/health", timeout=5)
            assert response.status_code == 200

            print("✅ Large payload memory handling: PASSED")

        finally:
            process.terminate()
            try:
                process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()


if __name__ == "__main__":
    # Run memory leak tests individually for debugging
    test_memory = TestCriticalMemoryLeaks()
    test_memory.setup_method()

    try:
        print("🚀 Running Critical Memory Leak Detection Tests...")

        print("\n1. Testing request/response memory cleanup...")
        test_memory.test_request_response_memory_cleanup()

        print("\n2. Testing DI container memory management...")
        test_memory.test_di_container_memory_management()

        print("\n3. Testing long-running server memory stability...")
        test_memory.test_long_running_server_memory_stability()

        print("\n4. Testing high-frequency request memory behavior...")
        test_memory.test_high_frequency_request_memory_behavior()

        print("\n5. Testing large payload memory handling...")
        test_memory.test_large_payload_memory_handling()

        print("\n✅ All Critical Memory Leak Detection Tests PASSED!")

    except Exception as e:
        print(f"\n❌ Memory test failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        test_memory.teardown_method()
