# Catzilla Performance Benchmark Results

## Test Configuration
- **Duration**: 10s
- **Connections**: 100
- **Threads**: 4
- **Tool**: wrk
- **Date**: Tue Jul  8 11:20:38 UTC 2025

## System Information

**Collection Time**: 2025-07-08T11:20:38.449850

### Operating System
- **System**: Linux
- **Release**: 4.18.0-553.27.1.el8_10.x86_64
- **Version**: #1 SMP Tue Nov 5 04:50:16 EST 2024
- **Platform**: Linux-4.18.0-553.27.1.el8_10.x86_64-x86_64-with-glibc2.28
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
- **Logical Cores**: 16
- **Physical Cores**: 8
- **Model**: Intel(R) Xeon(R) E-2388G CPU @ 3.20GHz
- **Current Frequency**: 3112.49 MHz
- **Max Frequency**: 3201.0 MHz

### Memory
- **Total RAM**: 62.78 GB
- **Available RAM**: 41.42 GB
- **Used RAM**: 17.65 GB (34.0%)
- **Total Swap**: 1.0 GB
- **Used Swap**: 100.0%

### Disk
- **Total Space**: 474.58 GB
- **Free Space**: 324.74 GB
- **Used Space**: 149.84 GB (31.6%)

### Python Environment
- **Python Version**: 3.11.9
- **Implementation**: cpython 3.11.9
- **Executable**: /root/devwork/catzilla/venv/bin/python3

### System Load
- **1 minute**: 1.31
- **5 minutes**: 1.11
- **15 minutes**: 0.92
## Performance Results

| Framework | Endpoint | Requests/sec | Avg Latency | 99% Latency |
|-----------|----------|--------------|-------------|-------------|
| catzilla | complex_json | 21178.42 | 4.98ms | 19.25ms |
| catzilla | hello_world | 35678.50 | 2.97ms | 13.88ms |
| catzilla | json_response | 26723.18 | 3.86ms | 3.86ms |
| catzilla | path_params | 24734.27 | 4.15ms | 12.68ms |
| catzilla | query_params | 16250.90 | 6.25ms | 16.73ms |
| catzilla | query_validation | 18629.60 | 5.49ms | 16.84ms |
| catzilla | validate_product_model | 16327.53 | 6.32ms | 16.98ms |
| catzilla | validate_user_model | 16052.07 | 6.52ms | 22.76ms |
| django | complex_json | 4297.94 | 23.18ms | 40.55ms |
| django | hello_world | 4671.45 | 21.47ms | 40.02ms |
| django | json_response | 4474.05 | 22.31ms | 40.03ms |
| django | path_params | 4441.46 | 22.41ms | 40.17ms |
| django | query_params | 3951.70 | 25.26ms | 42.60ms |
| fastapi | complex_json | 5549.56 | 17.98ms | 35.35ms |
| fastapi | hello_world | 7979.18 | 12.65ms | 29.55ms |
| fastapi | json_response | 6937.52 | 14.40ms | 31.78ms |
| fastapi | path_params | 6547.91 | 15.35ms | 32.46ms |
| fastapi | query_params | 3515.07 | 28.38ms | 45.31ms |
| flask | complex_json | 4975.77 | 20.10ms | 37.34ms |
| flask | hello_world | 5558.25 | 17.93ms | 35.12ms |
| flask | json_response | 5378.57 | 18.51ms | 36.09ms |
| flask | path_params | 5129.00 | 19.43ms | 36.19ms |
| flask | query_params | 4816.61 | 20.72ms | 38.16ms |
