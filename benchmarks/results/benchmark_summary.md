# Catzilla Performance Benchmark Results

## Test Configuration
- **Duration**: 10s
- **Connections**: 100
- **Threads**: 4
- **Tool**: wrk
- **Date**: Sun May 25 18:07:42 BST 2025

## System Information

**Collection Time**: 2025-05-25T18:07:41.999568

### Operating System
- **System**: Linux
- **Release**: 4.18.0-513.9.1.el8_9.x86_64
- **Version**: #1 SMP Sat Dec 2 05:23:44 EST 2023
- **Platform**: Linux-4.18.0-513.9.1.el8_9.x86_64-x86_64-with-glibc2.2.5
- **Machine**: x86_64

#### Linux Distribution
- **NAME**: AlmaLinux
- **VERSION**: 8.10 (Cerulean Leopard)
- **ID**: almalinux
- **ID_LIKE**: rhel centos fedora
- **VERSION_ID**: 8.10

### CPU
- **Processor**: x86_64
- **Architecture**: 64bit
- **Logical Cores**: 8
- **Physical Cores**: 4
- **Model**: Intel(R) Xeon(R) CPU E3-1245 v5 @ 3.50GHz
- **Current Frequency**: 3538.27 MHz
- **Max Frequency**: 3900.0 MHz

### Memory
- **Total RAM**: 31.17 GB
- **Available RAM**: 9.1 GB
- **Used RAM**: 20.14 GB (70.8%)
- **Total Swap**: 1.0 GB
- **Used Swap**: 100.0%

### Disk
- **Total Space**: 1859.98 GB
- **Free Space**: 1760.17 GB
- **Used Space**: 99.81 GB (5.4%)

### Python Environment
- **Python Version**: 3.8.12
- **Implementation**: cpython 3.8.12
- **Executable**: /root/devwork/catzilla/venv/bin/python3

### System Load
- **1 minute**: 1.00
- **5 minutes**: 0.69
- **15 minutes**: 0.36
## Performance Results

| Framework | Endpoint | Requests/sec | Avg Latency | 99% Latency |
|-----------|----------|--------------|-------------|-------------|
| catzilla | complex_json | 14842.50 | 6.79ms | 9.70ms |
| catzilla | hello_world | 24758.50 | 4.07ms | 5.98ms |
| catzilla | json_response | 15753.65 | 6.38ms | 8.37ms |
| catzilla | path_params | 17589.58 | 5.68ms | 7.36ms |
| catzilla | query_params | 11144.58 | 8.95ms | 11.28ms |
| django | complex_json | 2161.83 | 46.00ms | 50.06ms |
| django | hello_world | 2338.89 | 42.56ms | 46.49ms |
| django | json_response | 2207.93 | 45.04ms | 52.15ms |
| django | path_params | 2219.09 | 44.82ms | 47.93ms |
| django | query_params | 1975.37 | 50.37ms | 55.36ms |
| fastapi | complex_json | 2007.83 | 49.63ms | 51.00ms |
| fastapi | hello_world | 2843.94 | 35.04ms | 36.02ms |
| fastapi | json_response | 2421.29 | 41.16ms | 43.74ms |
| fastapi | path_params | 2340.97 | 42.58ms | 43.98ms |
| fastapi | query_params | 1419.16 | 70.08ms | 71.84ms |
| flask | complex_json | 2520.75 | 39.47ms | 43.68ms |
| flask | hello_world | 2875.21 | 34.60ms | 38.87ms |
| flask | json_response | 2671.96 | 37.23ms | 43.31ms |
| flask | path_params | 2624.16 | 37.93ms | 41.89ms |
| flask | query_params | 2431.46 | 40.90ms | 47.22ms |
