# Catzilla Performance Benchmark Results

## Test Configuration
- **Duration**: 10s
- **Connections**: 100
- **Threads**: 4
- **Tool**: wrk
- **Date**: Tue Jul  8 14:15:07 +06 2025

## System Information

**Collection Time**: 2025-07-08T14:15:07.515785

### Operating System
- **System**: Darwin
- **Release**: 24.5.0
- **Version**: Darwin Kernel Version 24.5.0: Tue Apr 22 19:53:26 PDT 2025; root:xnu-11417.121.6~2/RELEASE_X86_64
- **Platform**: macOS-15.5-x86_64-i386-64bit
- **Machine**: x86_64

#### macOS Details
- **ProductName**: macOS
- **ProductVersion**: 15.5
- **BuildVersion**: 24F74

### CPU
- **Processor**: i386
- **Architecture**: 64bit
- **Logical Cores**: 8
- **Physical Cores**: 4
- **Model**: Quad-Core Intel Core i5
- **Speed**: 1.1 GHz
- **Current Frequency**: 1100 MHz
- **Max Frequency**: 1100 MHz

### Memory
- **Total RAM**: 8.0 GB
- **Available RAM**: 2.1 GB
- **Used RAM**: 4.41 GB (73.7%)
- **Total Swap**: 3.0 GB
- **Used Swap**: 52.6%

### Disk
- **Total Space**: 418.16 GB
- **Free Space**: 16.25 GB
- **Used Space**: 384.59 GB (92.0%)

### Python Environment
- **Python Version**: 3.10.11
- **Implementation**: cpython 3.10.11
- **Executable**: /Users/user/devwork/catzilla/venv/bin/python3

### System Load
- **1 minute**: 1.81
- **5 minutes**: 2.38
- **15 minutes**: 2.56
## Performance Results

| Framework | Endpoint | Requests/sec | Avg Latency | 99% Latency |
|-----------|----------|--------------|-------------|-------------|
| catzilla | complex_json | 11158.63 | 10.09ms | 19.79ms |
| catzilla | hello_world | 22414.34 | 4.82ms | 7.47ms |
| catzilla | json_response | 15810.79 | 7.86ms | 77.45ms |
| catzilla | path_params | 12919.70 | 10.13ms | 107.99ms |
| catzilla | query_params | 8669.24 | 14.22ms | 123.56ms |
| catzilla | query_validation | 9133.11 | 12.65ms | 54.94ms |
| catzilla | validate_product_model | 8338.30 | 14.60ms | 112.09ms |
| catzilla | validate_user_model | 8178.64 | 16.27ms | 166.06ms |
| django | complex_json | 0.40 | 2.59ms | 4.31ms |
| django | hello_world | 1172.77 | 84.77ms | 119.99ms |
| django | json_response | 0.40 | 3.77ms | 5.90ms |
| django | path_params | 677.24 | 147.49ms | 362.40ms |
| django | query_params | 1082.01 | 91.83ms | 110.47ms |
| fastapi | complex_json | 2374.22 | 42.02ms | 51.31ms |
| fastapi | hello_world | 3566.03 | 27.99ms | 33.76ms |
| fastapi | json_response | 3019.95 | 34.07ms | 107.39ms |
| fastapi | path_params | 2736.39 | 36.47ms | 43.73ms |
| fastapi | query_params | 1547.44 | 64.42ms | 75.10ms |
| flask | complex_json | 310.03 | 166.38ms | 525.90ms |
| flask | hello_world | 1193.43 | 84.50ms | 252.61ms |
| flask | json_response | 236.08 | 116.51ms | 168.49ms |
| flask | query_params | 837.29 | 112.85ms | 208.59ms |
