# Catzilla Ubasic Category Performance Report

## Test Configuration
- **Category**: basic
- **Duration**: 10s
- **Connections**: 100
- **Threads**: 4
- **Tool**: wrk
- **Date**: Fri May  8 00:43:52 +06 2026

## Performance Results

| Framework | Endpoint | Requests/sec | Avg Latency | 99% Latency |
|-----------|----------|--------------|-------------|-------------|
| catzilla | basic_complex_json | 40987.19 | 2.54ms | 2.54ms |
| catzilla | basic_hello_world | 63576.01 | 1.62ms | 3.34ms |
| catzilla | basic_json_response | 55365.83 | 1.86ms | 1.92ms |
| catzilla | basic_path_params | 47918.38 | 2.16ms | 2.20ms |
| catzilla | basic_query_params | 29070.69 | 3.67ms | 3.63ms |
| fastapi | basic_complex_json | 6424.14 | 15.47ms | 16.67ms |
| fastapi | basic_hello_world | 8754.32 | 11.46ms | 16.75ms |
| fastapi | basic_json_response | 8037.99 | 12.43ms | 13.23ms |
| fastapi | basic_path_params | 7613.69 | 13.12ms | 13.56ms |
| fastapi | basic_query_params | 4043.03 | 24.61ms | 31.46ms |
| flask | basic_hello_world | 0.00 | 0.00us | 0.00us |

## Catzilla Performance Advantage

This report shows how Catzilla performs compared to other frameworks in the **basic** category.
