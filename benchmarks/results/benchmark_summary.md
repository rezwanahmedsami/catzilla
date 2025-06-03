# Catzilla Performance Benchmark Results

## Test Configuration
- **Duration**: 10s
- **Connections**: 100
- **Threads**: 4
- **Tool**: wrk
- **Date**: Tue Jun  3 12:04:42 +06 2025

## System Information

**Collection Time**: 2025-06-03T12:04:42.838056

### Operating System
- **System**: Linux
- **Release**: 6.12.20-amd64
- **Version**: #1 SMP PREEMPT_DYNAMIC Kali 6.12.20-1kali1 (2025-03-26)
- **Platform**: Linux-6.12.20-amd64-x86_64-with-glibc2.41
- **Machine**: x86_64

#### Linux Distribution
- **NAME**: Kali GNU/Linux
- **VERSION_ID**: 2025.1
- **VERSION**: 2025.1
- **ID**: kali
- **ID_LIKE**: debian

### CPU
- **Processor**: 
- **Architecture**: 64bit
- **Logical Cores**: 8
- **Physical Cores**: 4
- **Model**: 11th Gen Intel(R) Core(TM) i5-11300H @ 3.10GHz
- **Current Frequency**: 2649.83 MHz
- **Max Frequency**: 4400.0 MHz

### Memory
- **Total RAM**: 7.54 GB
- **Available RAM**: 2.38 GB
- **Used RAM**: 4.08 GB (68.4%)
- **Total Swap**: 7.45 GB
- **Used Swap**: 10.9%

### Disk
- **Total Space**: 228.12 GB
- **Free Space**: 128.36 GB
- **Used Space**: 88.1 GB (38.6%)

### Python Environment
- **Python Version**: 3.11.8
- **Implementation**: cpython 3.11.8
- **Executable**: /home/rezwan/devwork/catzilla/venv/bin/python3

### System Load
- **1 minute**: 0.82
- **5 minutes**: 0.96
- **15 minutes**: 0.97
## Performance Results

| Framework | Endpoint | Requests/sec | Avg Latency | 99% Latency |
|-----------|----------|--------------|-------------|-------------|
| catzilla | complex_json | 35399.54 | 2.88ms | 3.53ms |
| catzilla | hello_world | 60519.47 | 1.69ms | 2.01ms |
| catzilla | json_response | 45874.48 | 2.20ms | 2.58ms |
| catzilla | path_params | 45477.02 | 2.22ms | 2.63ms |
| catzilla | query_params | 23522.66 | 4.43ms | 5.36ms |
| catzilla | query_validation | 26738.33 | 3.92ms | 5.85ms |
| catzilla | validate_product_model | 25093.43 | 4.14ms | 4.85ms |
| catzilla | validate_user_model | 24638.44 | 4.19ms | 4.82ms |
| django | complex_json | 4390.24 | 22.64ms | 25.61ms |
| django | hello_world | 4827.95 | 20.61ms | 23.09ms |
| django | json_response | 4551.99 | 21.85ms | 25.45ms |
| django | path_params | 4547.89 | 21.88ms | 24.00ms |
| django | query_params | 3975.90 | 25.01ms | 28.05ms |
| fastapi | complex_json | 4795.91 | 20.78ms | 24.63ms |
| fastapi | hello_world | 7228.22 | 13.76ms | 15.33ms |
| fastapi | json_response | 6455.49 | 15.45ms | 18.02ms |
| fastapi | path_params | 5660.86 | 17.59ms | 19.86ms |
| fastapi | query_params | 3002.46 | 33.10ms | 37.94ms |
| flask | complex_json | 5033.67 | 19.77ms | 22.07ms |
| flask | hello_world | 5698.33 | 17.44ms | 19.01ms |
| flask | json_response | 5394.48 | 18.46ms | 21.42ms |
| flask | path_params | 5255.20 | 18.95ms | 21.30ms |
| flask | query_params | 4653.36 | 21.34ms | 24.17ms |

