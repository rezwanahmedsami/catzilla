# Catzilla Performance Benchmark Results

## Test Configuration
- **Duration**: 10s
- **Connections**: 100
- **Threads**: 4
- **Tool**: wrk
- **Date**: Sat May 31 01:16:44 +06 2025

## System Information

**Error**: System information collection failed

## Performance Results

| Framework | Endpoint | Requests/sec | Avg Latency | 99% Latency |
|-----------|----------|--------------|-------------|-------------|
| catzilla | complex_json | 15551.51 | 7.30ms | 15.36ms |
| catzilla | hello_world | 30812.76 | 3.40ms | 4.69ms |
| catzilla | json_response | 22114.04 | 4.87ms | 6.91ms |
| catzilla | path_params | 18219.36 | 8.18ms | 118.12ms |
| catzilla | query_params | 11149.48 | 10.23ms | 10.23ms |
| django | complex_json | 759.15 | 133.95ms | 417.17ms |
| django | hello_world | 314.91 | 309.86ms | 648.94ms |
| django | json_response | 256.67 | 375.55ms | 764.29ms |
| django | path_params | 987.44 | 102.33ms | 298.69ms |
| django | query_params | 70.49 | 127.38ms | 185.46ms |
| fastapi | complex_json | 1703.07 | 58.51ms | 105.64ms |
| fastapi | hello_world | 1734.47 | 57.92ms | 130.68ms |
| fastapi | json_response | 1602.76 | 64.35ms | 226.20ms |
| fastapi | path_params | 1868.35 | 53.63ms | 116.06ms |
| fastapi | query_params | 946.06 | 107.00ms | 287.25ms |
| flask | complex_json | 472.78 | 209.32ms | 450.22ms |
| flask | hello_world | 1259.57 | 75.87ms | 95.93ms |
| flask | json_response | 542.91 | 157.11ms | 331.72ms |
| flask | path_params | 987.63 | 102.05ms | 267.05ms |
| flask | query_params | 613.58 | 161.38ms | 186.67ms |
