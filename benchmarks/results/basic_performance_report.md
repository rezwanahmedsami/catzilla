# Catzilla Ubasic Category Performance Report

## Test Configuration
- **Category**: basic
- **Duration**: 2s
- **Connections**: 20
- **Threads**: 2
- **Tool**: wrk
- **Date**: Fri May  8 01:36:19 +06 2026

## Performance Results

| Framework | Endpoint | Requests/sec | Avg Latency | 99% Latency |
|-----------|----------|--------------|-------------|-------------|
| catzilla | basic_complex_json | 37409.31 | 554.50us | 1.56ms |
| catzilla | basic_hello_world | 60315.06 | 332.65us | 681.00us |
| catzilla | basic_json_response | 49608.23 | 427.45us | 1.43ms |
| catzilla | basic_path_params | 44213.38 | 453.50us | 0.89ms |
| catzilla | basic_query_params | 26527.10 | 781.19us | 2.12ms |
| fastapi | basic_complex_json | 6424.14 | 15.47ms | 16.67ms |
| fastapi | basic_hello_world | 8754.32 | 11.46ms | 16.75ms |
| fastapi | basic_json_response | 8037.99 | 12.43ms | 13.23ms |
| fastapi | basic_path_params | 7613.69 | 13.12ms | 13.56ms |
| fastapi | basic_query_params | 4043.03 | 24.61ms | 31.46ms |
| flask | basic_hello_world | 0.00 | 0.00us | 0.00us |

## Catzilla Performance Advantage

This report shows how Catzilla performs compared to other frameworks in the **basic** category.
