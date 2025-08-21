# Catzilla Basic Category Performance Report

## Test Configuration
- **Category**: basic
- **Duration**: 10s
- **Connections**: 100
- **Threads**: 4
- **Tool**: wrk
- **Date**: Thu Aug 21 05:41:15 UTC 2025

## Performance Results

| Framework | Endpoint | Requests/sec | Avg Latency | 99% Latency |
|-----------|----------|--------------|-------------|-------------|
| catzilla | basic_complex_json | 17360.10 | 5.92ms | 17.95ms |
| catzilla | basic_hello_world | 26431.91 | 4.05ms | 16.99ms |
| catzilla | basic_json_response | 20868.37 | 5.10ms | 21.86ms |
| catzilla | basic_path_params | 18689.69 | 5.59ms | 21.77ms |
| catzilla | basic_query_params | 13095.84 | 7.97ms | 25.87ms |
| django | basic_complex_json | 14714.80 | 6.71ms | 19.77ms |
| django | basic_hello_world | 15626.47 | 6.14ms | 20.52ms |
| django | basic_json_response | 15282.53 | 6.31ms | 18.82ms |
| django | basic_path_params | 14921.24 | 6.51ms | 18.01ms |
| django | basic_query_params | 13926.44 | 7.18ms | 19.08ms |
| fastapi | basic_complex_json | 4389.42 | 22.73ms | 40.02ms |
| fastapi | basic_hello_world | 6309.05 | 15.88ms | 33.40ms |
| fastapi | basic_json_response | 5656.60 | 17.66ms | 34.25ms |
| fastapi | basic_path_params | 5186.92 | 19.27ms | 35.95ms |
| fastapi | basic_query_params | 2767.89 | 35.99ms | 53.62ms |
| flask | basic_complex_json | 16427.06 | 5.89ms | 20.23ms |
| flask | basic_hello_world | 17435.09 | 5.32ms | 17.91ms |
| flask | basic_json_response | 17193.68 | 5.51ms | 17.85ms |
| flask | basic_path_params | 16823.57 | 5.64ms | 18.48ms |
| flask | basic_query_params | 16176.58 | 6.10ms | 22.24ms |

## Catzilla Performance Advantage

This report shows how Catzilla performs compared to other frameworks in the **basic** category.
