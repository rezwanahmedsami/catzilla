#!/usr/bin/env python3
"""Benchmark-only multi-worker launcher with an optional round-robin proxy."""

import argparse
import http.client
import signal
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import List, Tuple


EXCLUDED_RESPONSE_HEADERS = {
    "connection",
    "keep-alive",
    "proxy-authenticate",
    "proxy-authorization",
    "te",
    "trailers",
    "transfer-encoding",
    "upgrade",
}


class WorkerProxyLauncher:
    def __init__(self, args: argparse.Namespace):
        self.args = args
        self.backends: List[Tuple[str, int]] = [
            (args.host, args.backend_base_port + index)
            for index in range(args.workers)
        ]
        self.processes: List[subprocess.Popen] = []
        self._backend_index = 0
        self._backend_lock = threading.Lock()
        self.server = None

    def start(self) -> int:
        try:
            self._install_signal_handlers()
            self._start_workers()
            self._wait_for_backends()
            if self.args.proxy_port is not None:
                self._serve_proxy()
            else:
                self._run_launcher_only()
            return 0
        except KeyboardInterrupt:
            return 0
        except Exception as exc:  # pragma: no cover - startup failures are handled in shell validation
            print(f"❌ multi-worker launcher failed: {exc}", file=sys.stderr)
            return 1
        finally:
            self.stop()

    def stop(self) -> None:
        if self.server is not None:
            try:
                self.server.shutdown()
                self.server.server_close()
            except Exception:
                pass
            self.server = None

        for process in self.processes:
            if process.poll() is None:
                process.terminate()

        deadline = time.time() + 10
        for process in self.processes:
            if process.poll() is None:
                timeout = max(0.0, deadline - time.time())
                try:
                    process.wait(timeout=timeout)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=5)

    def _install_signal_handlers(self) -> None:
        def _handle_signal(signum, _frame):
            raise KeyboardInterrupt(signum)

        signal.signal(signal.SIGINT, _handle_signal)
        signal.signal(signal.SIGTERM, _handle_signal)

    def _start_workers(self) -> None:
        for index, (_host, port) in enumerate(self.backends):
            command = (
                self.args.worker_command
                .replace("{port}", str(port))
                .replace("{worker}", str(index))
            )
            process = subprocess.Popen(command, shell=True)
            self.processes.append(process)

    def _wait_for_backends(self) -> None:
        deadline = time.time() + self.args.startup_timeout

        for host, port in self.backends:
            health_url = f"http://{host}:{port}{self.args.health_path}"
            while time.time() < deadline:
                if any(process.poll() is not None for process in self.processes):
                    raise RuntimeError("a worker process exited before becoming ready")
                try:
                    with urllib.request.urlopen(health_url, timeout=1) as response:
                        if 200 <= response.status < 300:
                            break
                except (urllib.error.URLError, urllib.error.HTTPError):
                    time.sleep(0.2)
            else:
                raise RuntimeError(f"worker backend did not become ready: {health_url}")

    def _serve_proxy(self) -> None:
        launcher = self

        class ProxyHandler(BaseHTTPRequestHandler):
            protocol_version = "HTTP/1.1"

            def do_GET(self) -> None:  # noqa: N802
                self._proxy_request()

            def do_POST(self) -> None:  # noqa: N802
                self._proxy_request()

            def do_PUT(self) -> None:  # noqa: N802
                self._proxy_request()

            def do_PATCH(self) -> None:  # noqa: N802
                self._proxy_request()

            def do_DELETE(self) -> None:  # noqa: N802
                self._proxy_request()

            def do_HEAD(self) -> None:  # noqa: N802
                self._proxy_request()

            def do_OPTIONS(self) -> None:  # noqa: N802
                self._proxy_request()

            def log_message(self, _format: str, *_args) -> None:
                return

            def _proxy_request(self) -> None:
                backend_host, backend_port = launcher.next_backend()
                content_length = int(self.headers.get("Content-Length", "0") or "0")
                request_body = self.rfile.read(content_length) if content_length else None

                connection = http.client.HTTPConnection(backend_host, backend_port, timeout=30)
                try:
                    headers = {
                        key: value
                        for key, value in self.headers.items()
                        if key.lower() not in {"host", "connection"}
                    }
                    headers["Host"] = f"{backend_host}:{backend_port}"
                    connection.request(self.command, self.path, body=request_body, headers=headers)
                    response = connection.getresponse()
                    response_body = response.read()

                    self.send_response(response.status, response.reason)
                    sent_content_length = False
                    for header_name, header_value in response.getheaders():
                        header_name_lower = header_name.lower()
                        if header_name_lower in EXCLUDED_RESPONSE_HEADERS:
                            continue
                        if header_name_lower == "content-length":
                            sent_content_length = True
                        self.send_header(header_name, header_value)

                    if not sent_content_length:
                        self.send_header("Content-Length", str(len(response_body)))
                    self.end_headers()

                    if response_body and self.command != "HEAD":
                        self.wfile.write(response_body)
                except Exception as exc:  # pragma: no cover - network failures are runtime-only
                    error_body = f"proxy error: {exc}".encode("utf-8", errors="replace")
                    self.send_response(502, "Bad Gateway")
                    self.send_header("Content-Type", "text/plain")
                    self.send_header("Content-Length", str(len(error_body)))
                    self.end_headers()
                    if self.command != "HEAD":
                        self.wfile.write(error_body)
                finally:
                    connection.close()

        self.server = ThreadingHTTPServer((self.args.host, self.args.proxy_port), ProxyHandler)
        self.server.serve_forever()

    def _run_launcher_only(self) -> None:
        while True:
            if any(process.poll() is not None for process in self.processes):
                raise RuntimeError("a worker process exited while launcher-only mode was active")
            time.sleep(1)

    def next_backend(self) -> Tuple[str, int]:
        with self._backend_lock:
            backend = self.backends[self._backend_index]
            self._backend_index = (self._backend_index + 1) % len(self.backends)
            return backend


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Benchmark-only multi-worker launcher and optional proxy")
    parser.add_argument("--host", default="127.0.0.1", help="Host for proxy and backend workers")
    parser.add_argument("--proxy-port", type=int, help="Optional proxy port exposed to the benchmark runner")
    parser.add_argument("--backend-base-port", type=int, required=True, help="Base port for spawned worker processes")
    parser.add_argument("--workers", type=int, required=True, help="Number of backend worker processes")
    parser.add_argument("--worker-command", required=True, help="Shell command template for each worker. Use {port} and optionally {worker} placeholders")
    parser.add_argument("--health-path", default="/health", help="Health endpoint used to wait for backend readiness")
    parser.add_argument("--startup-timeout", type=int, default=30, help="Seconds to wait for all backends to become healthy")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    launcher = WorkerProxyLauncher(args)
    return launcher.start()


if __name__ == "__main__":
    raise SystemExit(main())