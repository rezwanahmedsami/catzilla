"""
E2E Server Manager

Manages test servers for E2E testing, adapted from benchmark server management.
Handles starting, stopping, and health checking of test servers.
"""
import asyncio
import os
import shutil
import subprocess
import sys
import time
import signal
import socket
from pathlib import Path
from typing import Dict, Optional, List
import httpx
import logging

logger = logging.getLogger(__name__)

class E2EServerManager:
    """Manages E2E test servers with lifecycle management"""

    def __init__(self, project_root: Optional[Path] = None):
        self.project_root = project_root or Path(__file__).parent.parent.parent.parent
        self.servers_dir = self.project_root / "tests" / "e2e" / "servers"
        self.running_servers: Dict[str, Dict] = {}
        self.venv_path = self.project_root / "venv"
        self.log_dir = self.project_root / "test-logs" / "e2e"
        self.log_dir.mkdir(parents=True, exist_ok=True)

    def get_python_executable(self) -> str:
        """Get Python executable from virtual environment if available"""
        candidates = []

        virtual_env = os.environ.get("VIRTUAL_ENV")
        if virtual_env:
            candidates.extend([
                Path(virtual_env) / "Scripts" / "python.exe",
                Path(virtual_env) / "bin" / "python",
            ])

        if self.venv_path.exists():
            candidates.extend([
                self.venv_path / "Scripts" / "python.exe",
                self.venv_path / "bin" / "python",
            ])

        candidates.append(Path(sys.executable))

        for candidate in candidates:
            if candidate and candidate.exists():
                return str(candidate)

        for command_name in ("python", "python3"):
            resolved = shutil.which(command_name)
            if resolved:
                return resolved

        return sys.executable

    def is_port_in_use(self, port: int) -> bool:
        """Check if a port is already in use using socket"""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            try:
                sock.bind(('127.0.0.1', port))
                return False  # Port is free
            except OSError:
                return True   # Port is in use

    async def wait_for_server_ready(self, host: str, port: int, timeout: int = 30, process: Optional[subprocess.Popen] = None) -> bool:
        """Wait for server to be ready by checking health endpoint"""
        url = f"http://{host}:{port}/health"

        async with httpx.AsyncClient() as client:
            for attempt in range(timeout):
                if process is not None and process.poll() is not None:
                    return False
                try:
                    response = await client.get(url, timeout=1.0)
                    if response.status_code == 200:
                        return True
                except (httpx.RequestError, httpx.TimeoutException):
                    pass
                await asyncio.sleep(1)

        return False

    async def start_server(
        self,
        server_name: str,
        port: int,
        host: str = "127.0.0.1",
        timeout: int = 30
    ) -> bool:
        """Start a test server"""

        # Check if server is already running
        if server_name in self.running_servers:
            if self.is_server_running(server_name):
                logger.warning(f"Server {server_name} is already running")
                return True
            stale_server = self.running_servers.pop(server_name)
            log_handle = stale_server.get("log_handle")
            if log_handle:
                log_handle.close()

        # Check if port is in use
        if self.is_port_in_use(port):
            logger.warning(f"Port {port} is in use, waiting...")
            await asyncio.sleep(3)  # Wait for port to be freed
            if self.is_port_in_use(port):
                logger.error(f"Port {port} is still in use")
                return False

        # Construct server path
        server_script = self.servers_dir / f"{server_name}_server.py"
        if not server_script.exists():
            logger.error(f"Server script not found: {server_script}")
            return False

        # Start server process
        python_exe = self.get_python_executable()
        cmd = [python_exe, str(server_script), "--host", host, "--port", str(port)]
        env = os.environ.copy()
        env.setdefault("PYTHONIOENCODING", "utf-8")
        env.setdefault("PYTHONUTF8", "1")

        python_path_entries = [str(self.project_root / "python"), str(self.project_root)]
        existing_pythonpath = env.get("PYTHONPATH")
        if existing_pythonpath:
            python_path_entries.append(existing_pythonpath)
        env["PYTHONPATH"] = os.pathsep.join(python_path_entries)

        log_path = self.log_dir / f"{server_name}_{port}.log"
        log_handle = open(log_path, "w", encoding="utf-8")

        try:
            logger.info(f"Starting {server_name} server on {host}:{port}")
            process = subprocess.Popen(
                cmd,
                cwd=self.project_root,
                stdout=log_handle,
                stderr=subprocess.STDOUT,
                env=env,
                text=True,
                encoding="utf-8",
                errors="replace",
                bufsize=1
            )

            # Wait for server to be ready
            if await self.wait_for_server_ready(host, port, timeout, process=process):
                self.running_servers[server_name] = {
                    "process": process,
                    "host": host,
                    "port": port,
                    "url": f"http://{host}:{port}",
                    "started_at": time.time(),
                    "log_path": str(log_path),
                    "log_handle": log_handle,
                }
                logger.info(f"✅ {server_name} server started successfully on {host}:{port}")
                return True
            else:
                # Server failed to start properly
                if process.poll() is None:
                    process.terminate()
                    try:
                        process.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        process.kill()

                # Get error output
                log_handle.flush()
                log_handle.close()
                output = log_path.read_text(encoding="utf-8", errors="replace") if log_path.exists() else ""
                logger.error(f"❌ {server_name} server failed to start")
                if output:
                    logger.error(f"Error output: {output.strip()}")

                return False

        except Exception as e:
            log_handle.close()
            logger.error(f"❌ Failed to start {server_name} server: {e}")
            return False

    async def stop_server(self, server_name: str) -> bool:
        """Stop a test server"""
        if server_name not in self.running_servers:
            logger.warning(f"Server {server_name} is not running")
            return True

        server_info = self.running_servers[server_name]
        process = server_info["process"]
        log_handle = server_info.get("log_handle")

        try:
            logger.info(f"Stopping {server_name} server...")

            # Graceful shutdown
            process.terminate()

            # Wait for graceful shutdown
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                # Force kill if necessary
                process.kill()
                process.wait(timeout=5)

            if log_handle:
                log_handle.close()

            del self.running_servers[server_name]
            logger.info(f"✅ {server_name} server stopped successfully")
            return True

        except Exception as e:
            if log_handle:
                log_handle.close()
            logger.error(f"❌ Failed to stop {server_name} server: {e}")
            return False

    async def stop_all_servers(self):
        """Stop all running servers"""
        logger.info("Stopping all E2E test servers...")

        for server_name in list(self.running_servers.keys()):
            await self.stop_server(server_name)

        logger.info("✅ All E2E test servers stopped")

    def get_server_url(self, server_name: str) -> Optional[str]:
        """Get the URL for a running server"""
        if server_name in self.running_servers:
            return self.running_servers[server_name]["url"]
        return None

    def is_server_running(self, server_name: str) -> bool:
        """Check if a server is currently running"""
        if server_name not in self.running_servers:
            return False

        process = self.running_servers[server_name]["process"]
        return process.poll() is None

    async def restart_server(self, server_name: str) -> bool:
        """Restart a server"""
        if server_name in self.running_servers:
            server_info = self.running_servers[server_name]
            host = server_info["host"]
            port = server_info["port"]

            await self.stop_server(server_name)
            await asyncio.sleep(2)  # Brief pause
            return await self.start_server(server_name, port, host)

        return False

    def get_running_servers(self) -> List[str]:
        """Get list of currently running server names"""
        return list(self.running_servers.keys())


# Singleton instance for global use
_server_manager: Optional[E2EServerManager] = None

def get_server_manager() -> E2EServerManager:
    """Get global server manager instance"""
    global _server_manager
    if _server_manager is None:
        _server_manager = E2EServerManager()
    return _server_manager
