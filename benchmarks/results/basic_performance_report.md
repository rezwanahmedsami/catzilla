# Catzilla Ubasic Category Performance Report

## Test Configuration
- **Category**: basic
- **Duration**: 10s
- **Connections**: 1000
- **Connections Per Worker**: 100
- **Requested Threads**: 4
- **Worker Mode**: multi
- **Workers**: 10
- **Tool**: wrk
- **Date**: Mon May 11 01:15:41 +06 2026

## Performance Results

| Framework | Endpoint | Worker Mode | Workers | Requests/sec | Avg Latency | 99% Latency | Peak Memory |
|-----------|----------|-------------|---------|--------------|-------------|-------------|-------------|
| catzilla | basic_complex_json | multi | 10 | 149439.03 | 7.76ms | 79.45ms | 437.89MB |
| catzilla | basic_complex_json | single | 1 | 46664.26 | 2.24ms | 4.96ms | 20.70MB |
| catzilla | basic_hello_world | multi | 10 | 190612.49 | 6.72ms | 49.94ms | 439.12MB |
| catzilla | basic_hello_world | single | 1 | 82817.33 | 1.24ms | 2.65ms | 40.50MB |
| catzilla | basic_json_response | multi | 10 | 173013.52 | 6.86ms | 33.98ms | 439.19MB |
| catzilla | basic_json_response | single | 1 | 57034.76 | 1.82ms | 4.73ms | 30.67MB |
| catzilla | basic_path_params | multi | 10 | 161648.18 | 7.13ms | 45.79ms | 439.31MB |
| catzilla | basic_path_params | single | 1 | 57226.03 | 1.79ms | 4.21ms | 30.80MB |
| catzilla | basic_query_params | multi | 10 | 125273.92 | 8.99ms | 89.52ms | 439.89MB |
| catzilla | basic_query_params | single | 1 | 34912.04 | 3.01ms | 6.06ms | 31.19MB |
| django | basic_complex_json | multi | 10 | 9703.00 | 102.75ms | 229.10ms | 443.47MB |
| django | basic_complex_json | single | 1 | 3341.25 | 34.51ms | 260.86ms | 72.92MB |
| django | basic_hello_world | multi | 10 | 10254.09 | 100.26ms | 267.62ms | 439.69MB |
| django | basic_hello_world | single | 1 | 3492.81 | 32.48ms | 219.06ms | 72.84MB |
| django | basic_json_response | multi | 10 | 9978.15 | 100.07ms | 222.41ms | 441.62MB |
| django | basic_json_response | single | 1 | 3257.96 | 34.93ms | 241.76ms | 72.84MB |
| django | basic_path_params | multi | 10 | 9939.46 | 101.36ms | 253.72ms | 442.33MB |
| django | basic_path_params | single | 1 | 3393.82 | 33.76ms | 243.19ms | 72.86MB |
| django | basic_query_params | multi | 10 | 9758.83 | 102.11ms | 214.91ms | 442.98MB |
| django | basic_query_params | single | 1 | 3200.32 | 35.98ms | 265.38ms | 72.91MB |
| fastapi | basic_complex_json | multi | 10 | 61665.50 | 16.48ms | 46.50ms | 639.77MB |
| fastapi | basic_complex_json | single | 1 | 15644.21 | 6.60ms | 10.27ms | 58.31MB |
| fastapi | basic_hello_world | multi | 10 | 109212.14 | 9.75ms | 43.22ms | 632.44MB |
| fastapi | basic_hello_world | single | 1 | 35154.38 | 2.87ms | 4.07ms | 58.03MB |
| fastapi | basic_json_response | multi | 10 | 91218.34 | 11.72ms | 47.69ms | 634.16MB |
| fastapi | basic_json_response | single | 1 | 27476.80 | 3.68ms | 5.78ms | 58.09MB |
| fastapi | basic_path_params | multi | 10 | 75414.74 | 13.89ms | 46.34ms | 636.45MB |
| fastapi | basic_path_params | single | 1 | 19843.95 | 5.36ms | 12.85ms | 58.16MB |
| fastapi | basic_query_params | multi | 10 | 37063.89 | 27.32ms | 66.76ms | 638.03MB |
| fastapi | basic_query_params | single | 1 | 8134.66 | 13.04ms | 25.16ms | 58.28MB |
| flask | basic_complex_json | multi | 10 | 10105.51 | 98.31ms | 215.45ms | 428.89MB |
| flask | basic_complex_json | single | 1 | 3143.16 | 35.77ms | 226.98ms | 71.62MB |
| flask | basic_hello_world | multi | 10 | 10323.54 | 96.35ms | 203.48ms | 409.75MB |
| flask | basic_hello_world | single | 1 | 3577.52 | 31.57ms | 208.23ms | 67.83MB |
| flask | basic_json_response | multi | 10 | 10243.00 | 97.34ms | 211.87ms | 410.48MB |
| flask | basic_json_response | single | 1 | 3496.29 | 32.59ms | 224.76ms | 71.58MB |
| flask | basic_path_params | multi | 10 | 10199.23 | 97.45ms | 211.71ms | 422.64MB |
| flask | basic_path_params | single | 1 | 3512.00 | 32.20ms | 212.14ms | 71.58MB |
| flask | basic_query_params | multi | 10 | 9929.88 | 100.48ms | 221.18ms | 428.69MB |
| flask | basic_query_params | single | 1 | 3322.38 | 34.34ms | 242.27ms | 71.61MB |

## Catzilla Performance Advantage

This report shows how Catzilla performs compared to other frameworks in the **basic** category.
