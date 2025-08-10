# Catzilla Ubasic Category Performance Report

## Test Configuration
- **Category**: basic
- **Duration**: 10s
- **Connections**: 100
- **Threads**: 4
- **Tool**: wrk
- **Date**: Sun Aug 10 17:32:23 +06 2025

## Performance Results

| Framework | Endpoint | Requests/sec | Avg Latency | 99% Latency |
|-----------|----------|--------------|-------------|-------------|
| catzilla | basic_complex_json | 7729.59 | 15.17ms | 97.27ms |
| catzilla | basic_hello_world | 14540.51 | 7.63ms | 10.30ms |
| catzilla | basic_json_response | 11874.04 | 9.61ms | 29.53ms |
| catzilla | basic_path_params | 9486.92 | 12.52ms | 83.97ms |
| catzilla | basic_query_params | 6577.34 | 19.02ms | 192.51ms |
| django | basic_complex_json | 842.15 | 118.01ms | 234.68ms |
| fastapi | basic_complex_json | 2091.87 | 47.61ms | 65.93ms |
| fastapi | basic_hello_world | 3282.63 | 30.21ms | 40.23ms |
| fastapi | basic_json_response | 2837.33 | 35.27ms | 66.24ms |
| fastapi | basic_path_params | 2466.21 | 40.44ms | 60.65ms |
| fastapi | basic_query_params | 1427.68 | 69.69ms | 97.47ms |
| flask | basic_complex_json | 1130.77 | 88.73ms | 203.17ms |
| flask | basic_hello_world | 1107.04 | 90.18ms | 173.38ms |
| flask | basic_path_params | 0.00 | 0.00us | 0.00us |

## Catzilla Performance Advantage

This report shows how Catzilla performs compared to other frameworks in the **basic** category.
