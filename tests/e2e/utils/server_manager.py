"""
E2E Server Manager

Manages test servers for E2E testing, adapted from benchmark server management.
Handles starting, stopping, and health checking of test servers.
"""
import asyncio
import subprocess
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

    def get_python_executable(self) -> str:
        """Get Python executable from virtual environment if available"""
        if self.venv_path.exists():
            venv_python = self.venv_path / "bin" / "python"
            if venv_python.exists():
                return str(venv_python)
        return "python3"

    def is_port_in_use(self, port: int) -> bool:
        """Check if a port is already in use using socket"""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            try:
                sock.bind(('127.0.0.1', port))
                return False  # Port is free
            except OSError:
                return True   # Port is in use

    async def wait_for_server_ready(self, host: str, port: int, timeout: int = 30) -> bool:
        """Wait for server to be ready by checking health endpoint"""
        url = f"http://{host}:{port}/health"

        async with httpx.AsyncClient() as client:
            for attempt in range(timeout):
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
            logger.warning(f"Server {server_name} is already running")
            return True

        # Check if port is in use
        if self.is_port_in_use(port):
            logger.warning(f"Port {port} is in use, waiting...")
            await asyncio.sleep(3)  # Wait for port to be freed

        # Construct server path
        server_script = self.servers_dir / f"{server_name}_server.py"
        if not server_script.exists():
            logger.error(f"Server script not found: {server_script}")
            return False

        # Start server process
        python_exe = self.get_python_executable()
        cmd = [python_exe, str(server_script), "--host", host, "--port", str(port)]

        try:
            logger.info(f"Starting {server_name} server on {host}:{port}")
            process = subprocess.Popen(
                cmd,
                cwd=self.project_root,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )

            # Wait for server to be ready
            if await self.wait_for_server_ready(host, port, timeout):
                self.running_servers[server_name] = {
                    "process": process,
                    "host": host,
                    "port": port,
                    "url": f"http://{host}:{port}",
                    "started_at": time.time()
                }
                logger.info(f"✅ {server_name} server started successfully on {host}:{port}")
                return True
            else:
                # Server failed to start properly
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()

                # Get error output
                stdout, stderr = process.communicate()
                logger.error(f"❌ {server_name} server failed to start")
                if stderr:
                    logger.error(f"Error output: {stderr.decode()}")

                return False

        except Exception as e:
            logger.error(f"❌ Failed to start {server_name} server: {e}")
            return False

    async def stop_server(self, server_name: str) -> bool:
        """Stop a test server"""
        if server_name not in self.running_servers:
            logger.warning(f"Server {server_name} is not running")
            return True

        server_info = self.running_servers[server_name]
        process = server_info["process"]

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

            del self.running_servers[server_name]
            logger.info(f"✅ {server_name} server stopped successfully")
            return True

        except Exception as e:
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
