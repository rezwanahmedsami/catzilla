import http.client
import json
import os
import socket
import subprocess
import sys
import tempfile
import textwrap
import time
from concurrent.futures import ThreadPoolExecutor

import psutil


def _find_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def _wait_for_server(port: int, timeout: float = 10.0) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=0.2):
                return
        except OSError:
            time.sleep(0.05)
    raise RuntimeError(f"server did not start on port {port}")


def _exercise_keepalive_endpoint(port: int, path: str, request_count: int) -> None:
    connection = http.client.HTTPConnection("127.0.0.1", port)
    try:
        for _ in range(request_count):
            connection.request("GET", path, headers={"Connection": "keep-alive"})
            response = connection.getresponse()
            response.read()
            assert response.status == 200
    finally:
        connection.close()


def _exercise_concurrent_endpoint(
    port: int, path: str, total_requests: int, workers: int
) -> None:
    requests_per_worker = total_requests // workers

    def _worker() -> None:
        connection = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
        try:
            for _ in range(requests_per_worker):
                connection.request("GET", path, headers={"Connection": "keep-alive"})
                response = connection.getresponse()
                response.read()
                assert response.status == 200
        finally:
            connection.close()

    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = [executor.submit(_worker) for _ in range(workers)]
        for future in futures:
            future.result()


def _get_json(port: int, path: str) -> dict:
    connection = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
    try:
        connection.request("GET", path)
        response = connection.getresponse()
        payload = response.read()
        assert response.status == 200
        return json.loads(payload)
    finally:
        connection.close()


def test_keepalive_requests_do_not_accumulate_request_memory():
    port = _find_free_port()
    server_code = textwrap.dedent(
        f'''
        from catzilla import Catzilla, Path

        app = Catzilla(
            use_jemalloc=False,
            memory_profiling=False,
            show_banner=False,
            log_requests=False,
            auto_validation=True,
        )


        @app.get("/")
        def home(request):
            return "Hello, World!"


        @app.get("/json")
        def json_response(request):
            return {{"message": "hello", "ok": True, "n": 1}}


        @app.get("/user/{{id}}")
        def user_by_id(request, id: int = Path(..., description="User ID")):
            return {{"id": id, "kind": "user"}}


        app.listen(host="127.0.0.1", port={port})
        '''
    )

    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as handle:
        handle.write(server_code)
        server_path = handle.name

    process = subprocess.Popen(
        [sys.executable, server_path],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    try:
        _wait_for_server(port)

        server_process = psutil.Process(process.pid)
        baseline_rss_mb = server_process.memory_info().rss / 1024 / 1024

        _exercise_keepalive_endpoint(port, "/", 600)
        _exercise_keepalive_endpoint(port, "/json", 600)
        _exercise_keepalive_endpoint(port, "/user/10", 600)

        time.sleep(0.3)
        final_rss_mb = server_process.memory_info().rss / 1024 / 1024
        growth_mb = final_rss_mb - baseline_rss_mb

        assert growth_mb < 5.0, (
            f"expected keep-alive memory growth to stay bounded, got {growth_mb:.2f} MB "
            f"(baseline={baseline_rss_mb:.2f} MB final={final_rss_mb:.2f} MB)"
        )
    finally:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)
        os.unlink(server_path)


def test_c_router_match_does_not_leak_python_objects_under_load():
    port = _find_free_port()
    server_code = textwrap.dedent(
        f'''
        import tracemalloc
        from catzilla import Catzilla, JSONResponse, Response

        tracemalloc.start(25)

        app = Catzilla(
            production=True,
            use_jemalloc=True,
            memory_profiling=False,
            show_banner=False,
            log_requests=False,
            enable_di=False,
            auto_validation=False,
        )

        plain_response = Response(status_code=200, content_type="text/plain", body="ok")


        @app.get("/")
        def home(request):
            return plain_response


        @app.get("/__memory_metrics")
        def memory_metrics(request):
            current, peak = tracemalloc.get_traced_memory()
            return JSONResponse({{"current_mb": current / (1024 * 1024), "peak_mb": peak / (1024 * 1024)}})


        app.listen(host="127.0.0.1", port={port})
        '''
    )

    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as handle:
        handle.write(server_code)
        server_path = handle.name

    process = subprocess.Popen(
        [sys.executable, server_path],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    try:
        _wait_for_server(port)

        baseline_metrics = _get_json(port, "/__memory_metrics")

        _exercise_concurrent_endpoint(port, "/", total_requests=4000, workers=20)
        time.sleep(0.3)

        final_metrics = _get_json(port, "/__memory_metrics")
        current_growth_mb = final_metrics["current_mb"] - baseline_metrics["current_mb"]

        assert current_growth_mb < 1.0, (
            "expected C router match bridge to keep traced Python memory bounded, "
            f"got growth of {current_growth_mb:.2f} MB "
            f"(baseline={baseline_metrics['current_mb']:.2f} MB final={final_metrics['current_mb']:.2f} MB)"
        )
    finally:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)
        os.unlink(server_path)