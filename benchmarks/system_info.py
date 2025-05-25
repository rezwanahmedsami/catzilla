#!/usr/bin/env python3
"""
System Information Collection for Catzilla Benchmarks

This module collects comprehensive system information including:
- Operating System details
- CPU specifications
- Memory information
- Python environment details
- Network configuration

The collected information is used to provide context and authenticity
to benchmark results, ensuring reproducibility and credibility.
"""

import argparse
import json
import platform
import psutil
import sys
import socket
import subprocess
import os
from datetime import datetime
from typing import Dict, Any, Optional


def get_cpu_info() -> Dict[str, Any]:
    """Collect detailed CPU information."""
    cpu_info = {
        "processor": platform.processor(),
        "machine": platform.machine(),
        "architecture": platform.architecture()[0],
        "cpu_count_logical": psutil.cpu_count(logical=True),
        "cpu_count_physical": psutil.cpu_count(logical=False),
        "cpu_freq": {}
    }

    # Get CPU frequency information
    try:
        cpu_freq = psutil.cpu_freq()
        if cpu_freq:
            cpu_info["cpu_freq"] = {
                "current": round(cpu_freq.current, 2),
                "min": round(cpu_freq.min, 2) if cpu_freq.min else None,
                "max": round(cpu_freq.max, 2) if cpu_freq.max else None
            }
    except (AttributeError, NotImplementedError):
        cpu_info["cpu_freq"] = {"error": "CPU frequency information not available"}

    # Try to get more detailed CPU info on macOS and Linux
    try:
        if platform.system() == "Darwin":  # macOS
            # Get CPU model from system_profiler
            result = subprocess.run(
                ["system_profiler", "SPHardwareDataType"],
                capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0:
                for line in result.stdout.split('\n'):
                    if 'Processor Name:' in line:
                        cpu_info["model"] = line.split(':', 1)[1].strip()
                    elif 'Processor Speed:' in line:
                        cpu_info["speed"] = line.split(':', 1)[1].strip()
                    elif 'Number of Processors:' in line:
                        cpu_info["processors"] = line.split(':', 1)[1].strip()
                    elif 'Total Number of Cores:' in line:
                        cpu_info["total_cores"] = line.split(':', 1)[1].strip()

        elif platform.system() == "Linux":
            # Get CPU model from /proc/cpuinfo
            try:
                with open('/proc/cpuinfo', 'r') as f:
                    cpuinfo = f.read()
                    for line in cpuinfo.split('\n'):
                        if line.startswith('model name'):
                            cpu_info["model"] = line.split(':', 1)[1].strip()
                            break
            except (FileNotFoundError, PermissionError):
                pass

    except (subprocess.TimeoutExpired, subprocess.SubprocessError, FileNotFoundError):
        pass

    return cpu_info


def get_memory_info() -> Dict[str, Any]:
    """Collect detailed memory information."""
    memory = psutil.virtual_memory()
    swap = psutil.swap_memory()

    return {
        "total": memory.total,
        "available": memory.available,
        "used": memory.used,
        "free": memory.free,
        "percent_used": memory.percent,
        "total_gb": round(memory.total / (1024**3), 2),
        "available_gb": round(memory.available / (1024**3), 2),
        "used_gb": round(memory.used / (1024**3), 2),
        "swap": {
            "total": swap.total,
            "used": swap.used,
            "free": swap.free,
            "percent": swap.percent,
            "total_gb": round(swap.total / (1024**3), 2) if swap.total > 0 else 0
        }
    }


def get_disk_info() -> Dict[str, Any]:
    """Collect disk usage information."""
    try:
        # Get disk usage for the current directory (where benchmarks are running)
        current_path = os.getcwd()
        disk_usage = psutil.disk_usage(current_path)

        return {
            "path": current_path,
            "total": disk_usage.total,
            "used": disk_usage.used,
            "free": disk_usage.free,
            "total_gb": round(disk_usage.total / (1024**3), 2),
            "used_gb": round(disk_usage.used / (1024**3), 2),
            "free_gb": round(disk_usage.free / (1024**3), 2),
            "percent_used": round((disk_usage.used / disk_usage.total) * 100, 2)
        }
    except (OSError, AttributeError):
        return {"error": "Disk information not available"}


def get_network_info() -> Dict[str, Any]:
    """Collect network configuration information."""
    network_info = {
        "hostname": socket.gethostname(),
        "interfaces": {}
    }

    try:
        # Get network interfaces
        for interface_name, addresses in psutil.net_if_addrs().items():
            interface_info = []
            for addr in addresses:
                if addr.family == socket.AF_INET:  # IPv4
                    interface_info.append({
                        "family": "IPv4",
                        "address": addr.address,
                        "netmask": addr.netmask,
                        "broadcast": addr.broadcast
                    })
                elif addr.family == socket.AF_INET6:  # IPv6
                    interface_info.append({
                        "family": "IPv6",
                        "address": addr.address,
                        "netmask": addr.netmask
                    })

            if interface_info:
                network_info["interfaces"][interface_name] = interface_info

        # Get network statistics
        net_io = psutil.net_io_counters()
        if net_io:
            network_info["io_counters"] = {
                "bytes_sent": net_io.bytes_sent,
                "bytes_recv": net_io.bytes_recv,
                "packets_sent": net_io.packets_sent,
                "packets_recv": net_io.packets_recv
            }

    except (AttributeError, OSError):
        network_info["error"] = "Network information collection failed"

    return network_info


def get_python_info() -> Dict[str, Any]:
    """Collect Python environment information."""
    return {
        "version": sys.version,
        "version_info": {
            "major": sys.version_info.major,
            "minor": sys.version_info.minor,
            "micro": sys.version_info.micro,
            "releaselevel": sys.version_info.releaselevel,
            "serial": sys.version_info.serial
        },
        "executable": sys.executable,
        "platform": sys.platform,
        "implementation": {
            "name": sys.implementation.name,
            "version": f"{sys.implementation.version.major}.{sys.implementation.version.minor}.{sys.implementation.version.micro}"
        },
        "path": sys.path[:3]  # First few paths for context
    }


def get_os_info() -> Dict[str, Any]:
    """Collect operating system information."""
    os_info = {
        "system": platform.system(),
        "release": platform.release(),
        "version": platform.version(),
        "machine": platform.machine(),
        "processor": platform.processor(),
        "platform": platform.platform(),
        "node": platform.node()
    }

    # Add system-specific information
    try:
        if platform.system() == "Darwin":  # macOS
            result = subprocess.run(
                ["sw_vers"], capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0:
                macos_info = {}
                for line in result.stdout.strip().split('\n'):
                    if ':' in line:
                        key, value = line.split(':', 1)
                        macos_info[key.strip()] = value.strip()
                os_info["macos_details"] = macos_info

        elif platform.system() == "Linux":
            # Try to get distribution info
            try:
                with open('/etc/os-release', 'r') as f:
                    os_release = {}
                    for line in f:
                        if '=' in line:
                            key, value = line.strip().split('=', 1)
                            os_release[key] = value.strip('"')
                    os_info["linux_distribution"] = os_release
            except (FileNotFoundError, PermissionError):
                pass

    except (subprocess.TimeoutExpired, subprocess.SubprocessError, FileNotFoundError):
        pass

    return os_info


def get_process_info() -> Dict[str, Any]:
    """Collect current process information."""
    current_process = psutil.Process()

    return {
        "pid": current_process.pid,
        "ppid": current_process.ppid(),
        "name": current_process.name(),
        "cpu_percent": current_process.cpu_percent(),
        "memory_info": {
            "rss": current_process.memory_info().rss,
            "vms": current_process.memory_info().vms,
            "rss_mb": round(current_process.memory_info().rss / (1024**2), 2),
            "vms_mb": round(current_process.memory_info().vms / (1024**2), 2)
        },
        "create_time": current_process.create_time(),
        "cwd": current_process.cwd()
    }


def collect_system_info() -> Dict[str, Any]:
    """Collect comprehensive system information."""
    print("Collecting system information...", file=sys.stderr)

    system_info = {
        "collection_timestamp": datetime.now().isoformat(),
        "collection_utc": datetime.utcnow().isoformat() + "Z",
        "os": get_os_info(),
        "cpu": get_cpu_info(),
        "memory": get_memory_info(),
        "disk": get_disk_info(),
        "network": get_network_info(),
        "python": get_python_info(),
        "process": get_process_info()
    }

    # Add load averages on Unix systems
    try:
        if hasattr(os, 'getloadavg'):
            load_avg = os.getloadavg()
            system_info["load_average"] = {
                "1min": load_avg[0],
                "5min": load_avg[1],
                "15min": load_avg[2]
            }
    except (OSError, AttributeError):
        pass

    print("System information collection complete.", file=sys.stderr)
    return system_info


def format_system_info_markdown(system_info: Dict[str, Any]) -> str:
    """Format system information as Markdown for inclusion in reports."""
    md_lines = [
        "## System Information",
        "",
        f"**Collection Time**: {system_info['collection_timestamp']}",
        "",
        "### Operating System",
        f"- **System**: {system_info['os']['system']}",
        f"- **Release**: {system_info['os']['release']}",
        f"- **Version**: {system_info['os']['version']}",
        f"- **Platform**: {system_info['os']['platform']}",
        f"- **Machine**: {system_info['os']['machine']}",
    ]

    # Add macOS specific details
    if 'macos_details' in system_info['os']:
        md_lines.extend([
            "",
            "#### macOS Details",
        ])
        for key, value in system_info['os']['macos_details'].items():
            md_lines.append(f"- **{key}**: {value}")

    # Add Linux distribution details
    if 'linux_distribution' in system_info['os']:
        md_lines.extend([
            "",
            "#### Linux Distribution",
        ])
        for key, value in system_info['os']['linux_distribution'].items():
            if key in ['NAME', 'VERSION', 'ID', 'ID_LIKE', 'VERSION_ID']:
                md_lines.append(f"- **{key}**: {value}")

    # CPU Information
    cpu = system_info['cpu']
    md_lines.extend([
        "",
        "### CPU",
        f"- **Processor**: {cpu.get('processor', 'Unknown')}",
        f"- **Architecture**: {cpu.get('architecture', 'Unknown')}",
        f"- **Logical Cores**: {cpu.get('cpu_count_logical', 'Unknown')}",
        f"- **Physical Cores**: {cpu.get('cpu_count_physical', 'Unknown')}",
    ])

    if 'model' in cpu:
        md_lines.append(f"- **Model**: {cpu['model']}")
    if 'speed' in cpu:
        md_lines.append(f"- **Speed**: {cpu['speed']}")

    if cpu.get('cpu_freq') and 'current' in cpu['cpu_freq']:
        freq = cpu['cpu_freq']
        md_lines.append(f"- **Current Frequency**: {freq['current']} MHz")
        if freq.get('max'):
            md_lines.append(f"- **Max Frequency**: {freq['max']} MHz")

    # Memory Information
    memory = system_info['memory']
    md_lines.extend([
        "",
        "### Memory",
        f"- **Total RAM**: {memory['total_gb']} GB",
        f"- **Available RAM**: {memory['available_gb']} GB",
        f"- **Used RAM**: {memory['used_gb']} GB ({memory['percent_used']:.1f}%)",
    ])

    if memory['swap']['total_gb'] > 0:
        md_lines.extend([
            f"- **Total Swap**: {memory['swap']['total_gb']} GB",
            f"- **Used Swap**: {memory['swap']['percent']:.1f}%",
        ])

    # Disk Information
    if 'error' not in system_info['disk']:
        disk = system_info['disk']
        md_lines.extend([
            "",
            "### Disk",
            f"- **Total Space**: {disk['total_gb']} GB",
            f"- **Free Space**: {disk['free_gb']} GB",
            f"- **Used Space**: {disk['used_gb']} GB ({disk['percent_used']:.1f}%)",
        ])

    # Python Information
    python = system_info['python']
    md_lines.extend([
        "",
        "### Python Environment",
        f"- **Python Version**: {python['version_info']['major']}.{python['version_info']['minor']}.{python['version_info']['micro']}",
        f"- **Implementation**: {python['implementation']['name']} {python['implementation']['version']}",
        f"- **Executable**: {python['executable']}",
    ])

    # Load averages (Unix systems)
    if 'load_average' in system_info:
        load = system_info['load_average']
        md_lines.extend([
            "",
            "### System Load",
            f"- **1 minute**: {load['1min']:.2f}",
            f"- **5 minutes**: {load['5min']:.2f}",
            f"- **15 minutes**: {load['15min']:.2f}",
        ])

    return "\n".join(md_lines)


def main():
    """Main function to collect and output system information."""
    parser = argparse.ArgumentParser(
        description="Collect comprehensive system information for Catzilla benchmarks"
    )
    parser.add_argument(
        "--output", "-o",
        help="Output file path for JSON results"
    )
    parser.add_argument(
        "--format", "-f",
        choices=["json", "markdown"],
        default="json",
        help="Output format (default: json)"
    )
    parser.add_argument(
        "--pretty", "-p",
        action="store_true",
        help="Pretty print JSON output"
    )

    args = parser.parse_args()

    try:
        # Collect system information
        system_info = collect_system_info()

        if args.format == "json":
            # Output JSON
            if args.output:
                with open(args.output, 'w') as f:
                    if args.pretty:
                        json.dump(system_info, f, indent=2, default=str)
                    else:
                        json.dump(system_info, f, default=str)
                print(f"System information saved to: {args.output}", file=sys.stderr)
            else:
                if args.pretty:
                    print(json.dumps(system_info, indent=2, default=str))
                else:
                    print(json.dumps(system_info, default=str))

        elif args.format == "markdown":
            # Output Markdown
            markdown_output = format_system_info_markdown(system_info)
            if args.output:
                with open(args.output, 'w') as f:
                    f.write(markdown_output)
                print(f"System information saved to: {args.output}", file=sys.stderr)
            else:
                print(markdown_output)

        return 0

    except Exception as e:
        print(f"Error collecting system information: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
