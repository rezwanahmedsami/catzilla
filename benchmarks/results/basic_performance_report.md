# Catzilla Ubasic Category Performance Report

## Test Configuration
- **Category**: basic
- **Duration**: 1s
- **Connections**: 100
- **Threads**: 4
- **Tool**: wrk
- **Date**: Thu Aug 21 11:30:17 +06 2025

## Performance Results

| Framework | Endpoint | Requests/sec | Avg Latency | 99% Latency |
|-----------|----------|--------------|-------------|-------------|
| catzilla | basic_complex_json | 9361.13 | 23.67ms | 305.37ms |
| catzilla | basic_hello_world | 14692.67 | 13.01ms | 185.58ms |
| catzilla | basic_json_response | 12303.06 | 16.54ms | 227.10ms |
| catzilla | basic_path_params | 8880.57 | 30.56ms | 268.90ms |
| catzilla | basic_query_params | 7166.67 | 40.01ms | 462.00ms |
| fastapi | basic_hello_world | 2964.48 | 33.81ms | 52.76ms |

## Catzilla Performance Advantage

This report shows how Catzilla performs compared to other frameworks in the **basic** category.
