# Catzilla Ubasic Category Performance Report

## Test Configuration
- **Category**: basic
- **Duration**: 10s
- **Connections**: 100
- **Threads**: 4
- **Tool**: wrk
- **Date**: Sat Aug 16 02:15:27 +06 2025

## Performance Results

| Framework | Endpoint | Requests/sec | Avg Latency | 99% Latency |
|-----------|----------|--------------|-------------|-------------|
| catzilla | basic_complex_json | 7140.09 | 17.23ms | 126.54ms |
| catzilla | basic_hello_world | 12483.43 | 9.61ms | 80.41ms |
| catzilla | basic_json_response | 9404.73 | 13.43ms | 117.29ms |
| catzilla | basic_path_params | 8330.97 | 14.06ms | 87.11ms |
| catzilla | basic_query_params | 5642.72 | 20.73ms | 139.63ms |
| django | basic_complex_json | 433.86 | 1.33ms | 3.04ms |
| django | basic_hello_world | 1028.08 | 48.45ms | 67.96ms |
| django | basic_json_response | 1.29 | 4.40ms | 10.30ms |
| django | basic_path_params | 1664.19 | 49.36ms | 132.84ms |
| django | basic_query_params | 0.99 | 3.61ms | 8.71ms |
| fastapi | basic_complex_json | 1917.40 | 51.98ms | 67.30ms |
| fastapi | basic_hello_world | 2558.32 | 38.97ms | 53.08ms |
| fastapi | basic_json_response | 2304.81 | 43.26ms | 62.58ms |
| fastapi | basic_path_params | 2117.15 | 47.46ms | 111.54ms |
| fastapi | basic_query_params | 1281.65 | 78.59ms | 194.47ms |
| flask | basic_complex_json | 493.14 | 5.03ms | 59.27ms |
| flask | basic_hello_world | 1083.33 | 52.83ms | 66.56ms |
| flask | basic_json_response | 1.78 | 5.23ms | 17.42ms |
| flask | basic_path_params | 1612.88 | 47.77ms | 63.99ms |
| flask | basic_query_params | 0.89 | 9.45ms | 29.83ms |

## Catzilla Performance Advantage

This report shows how Catzilla performs compared to other frameworks in the **basic** category.
