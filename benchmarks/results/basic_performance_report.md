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
- **Date**: Sat May  9 12:32:12 +06 2026

## Performance Results

| Framework | Endpoint | Worker Mode | Workers | Requests/sec | Avg Latency | 99% Latency | Peak Memory |
|-----------|----------|-------------|---------|--------------|-------------|-------------|-------------|
| catzilla | basic_complex_json | multi | 10 | 167950.59 | 6.15ms | 34.76ms | 299.31MB |
| catzilla | basic_complex_json | single | 1 | 41648.68 | 2.49ms | 2.61ms | 27.86MB |
| catzilla | basic_hello_world | multi | 10 | 212425.71 | 5.25ms | 23.57ms | 305.75MB |
| catzilla | basic_hello_world | single | 1 | 72248.82 | 1.41ms | 1.47ms | 28.45MB |
| catzilla | basic_json_response | multi | 10 | 197326.26 | 5.45ms | 27.25ms | 305.94MB |
| catzilla | basic_json_response | single | 1 | 57767.06 | 1.78ms | 1.85ms | 28.48MB |
| catzilla | basic_path_params | multi | 10 | 184445.05 | 5.69ms | 29.97ms | 306.23MB |
| catzilla | basic_path_params | single | 1 | 49677.96 | 2.09ms | 2.13ms | 28.52MB |
| catzilla | basic_query_params | multi | 10 | 137966.43 | 7.61ms | 30.95ms | 300.44MB |
| catzilla | basic_query_params | single | 1 | 31707.18 | 3.33ms | 3.32ms | 27.97MB |
| django | basic_complex_json | multi | 10 | 5567.32 | 172.73ms | 259.87ms | 352.05MB |
| django | basic_complex_json | single | 1 | 2763.62 | 55.37ms | 790.54ms | 53.00MB |
| django | basic_hello_world | multi | 10 | 5472.76 | 175.60ms | 293.80ms | 346.36MB |
| django | basic_hello_world | single | 1 | 2866.30 | 51.90ms | 729.56ms | 52.84MB |
| django | basic_json_response | multi | 10 | 5528.15 | 175.35ms | 277.00ms | 348.89MB |
| django | basic_json_response | single | 1 | 2816.47 | 55.68ms | 810.52ms | 52.88MB |
| django | basic_path_params | multi | 10 | 5553.92 | 178.95ms | 421.08ms | 350.12MB |
| django | basic_path_params | single | 1 | 2805.55 | 57.38ms | 848.01ms | 52.91MB |
| django | basic_query_params | multi | 10 | 5623.24 | 172.94ms | 250.24ms | 351.34MB |
| django | basic_query_params | single | 1 | 2645.62 | 53.65ms | 663.78ms | 52.97MB |
| fastapi | basic_complex_json | multi | 10 | 38679.51 | 25.92ms | 25.92ms | 358.19MB |
| fastapi | basic_complex_json | single | 1 | 7680.47 | 13.01ms | 13.53ms | 32.03MB |
| fastapi | basic_hello_world | multi | 10 | 55121.89 | 18.21ms | 36.77ms | 340.67MB |
| fastapi | basic_hello_world | single | 1 | 11132.37 | 8.98ms | 9.54ms | 30.47MB |
| fastapi | basic_json_response | multi | 10 | 49678.09 | 20.40ms | 51.13ms | 346.56MB |
| fastapi | basic_json_response | single | 1 | 9869.86 | 10.13ms | 10.65ms | 31.45MB |
| fastapi | basic_path_params | multi | 10 | 45680.10 | 21.97ms | 47.52ms | 351.61MB |
| fastapi | basic_path_params | single | 1 | 9214.01 | 10.84ms | 11.34ms | 31.56MB |
| fastapi | basic_query_params | multi | 10 | 25289.59 | 39.78ms | 92.24ms | 356.52MB |
| fastapi | basic_query_params | single | 1 | 4786.11 | 20.72ms | 21.86ms | 32.00MB |
| flask | basic_complex_json | multi | 10 | 5432.29 | 186.95ms | 474.68ms | 291.47MB |
| flask | basic_complex_json | single | 1 | 2974.74 | 48.96ms | 670.39ms | 46.48MB |
| flask | basic_hello_world | multi | 10 | 5494.72 | 176.97ms | 284.54ms | 285.56MB |
| flask | basic_hello_world | single | 1 | 3093.59 | 45.41ms | 587.81ms | 46.39MB |
| flask | basic_json_response | multi | 10 | 5537.28 | 174.38ms | 269.80ms | 287.73MB |
| flask | basic_json_response | single | 1 | 3047.08 | 48.67ms | 671.90ms | 46.44MB |
| flask | basic_path_params | multi | 10 | 5449.18 | 177.13ms | 274.15ms | 288.75MB |
| flask | basic_path_params | single | 1 | 3013.40 | 47.79ms | 638.40ms | 46.45MB |
| flask | basic_query_params | multi | 10 | 5526.52 | 174.02ms | 289.53ms | 289.88MB |
| flask | basic_query_params | single | 1 | 2891.33 | 53.73ms | 776.82ms | 46.47MB |

## Catzilla Performance Advantage

This report shows how Catzilla performs compared to other frameworks in the **basic** category.
