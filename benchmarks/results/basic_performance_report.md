# Catzilla Ubasic Category Performance Report

## Test Configuration
- **Category**: basic
- **Duration**: 10s
- **Connections**: 100
- **Connections Per Worker**: 100
- **Requested Threads**: 4
- **Worker Mode**: single
- **Workers**: 1
- **Tool**: wrk
- **Date**: Sun May 10 14:02:24 +06 2026

## Performance Results

| Framework | Endpoint | Worker Mode | Workers | Requests/sec | Avg Latency | 99% Latency | Peak Memory |
|-----------|----------|-------------|---------|--------------|-------------|-------------|-------------|
| blacksheep | basic_complex_json | multi | 10 | 38909.41 | 40.64ms | 730.32ms | 55.59MB |
| blacksheep | basic_complex_json | single | 1 | 17503.63 | 5.68ms | 5.98ms | 46.77MB |
| blacksheep | basic_hello_world | multi | 10 | 53862.64 | 31.56ms | 617.55ms | 53.61MB |
| blacksheep | basic_hello_world | single | 1 | 20710.35 | 4.80ms | 5.09ms | 44.62MB |
| blacksheep | basic_json_response | multi | 10 | 47358.79 | 33.07ms | 598.85ms | 53.91MB |
| blacksheep | basic_json_response | single | 1 | 19305.54 | 5.16ms | 5.43ms | 44.91MB |
| blacksheep | basic_path_params | multi | 10 | 41920.79 | 40.34ms | 774.16ms | 53.91MB |
| blacksheep | basic_path_params | single | 1 | 18287.24 | 5.45ms | 7.71ms | 45.05MB |
| blacksheep | basic_query_params | multi | 10 | 29929.10 | 51.96ms | 886.80ms | 55.16MB |
| blacksheep | basic_query_params | single | 1 | 14985.52 | 6.65ms | 7.01ms | 45.94MB |
| catzilla | basic_complex_json | multi | 10 | 179539.51 | 5.83ms | 29.32ms | 339.62MB |
| catzilla | basic_complex_json | single | 1 | 53671.71 | 1.93ms | 2.09ms | 38.75MB |
| catzilla | basic_hello_world | multi | 10 | 202787.27 | 6.44ms | 60.58ms | 417.77MB |
| catzilla | basic_hello_world | single | 1 | 90332.12 | 1.13ms | 2.02ms | 38.59MB |
| catzilla | basic_json_response | multi | 10 | 193356.08 | 5.88ms | 28.01ms | 417.92MB |
| catzilla | basic_json_response | single | 1 | 72061.27 | 1.41ms | 1.55ms | 38.62MB |
| catzilla | basic_path_params | multi | 10 | 166612.83 | 6.93ms | 41.74ms | 418.11MB |
| catzilla | basic_path_params | single | 1 | 63354.59 | 1.62ms | 2.76ms | 38.62MB |
| catzilla | basic_query_params | multi | 10 | 142243.66 | 7.68ms | 89.60ms | 340.25MB |
| catzilla | basic_query_params | single | 1 | 38288.57 | 2.74ms | 4.81ms | 38.81MB |
| django | basic_complex_json | multi | 10 | 5567.32 | 172.73ms | 259.87ms | 352.05MB |
| django | basic_complex_json | single | 1 | 3539.96 | 31.94ms | 210.74ms | 75.44MB |
| django | basic_hello_world | multi | 10 | 5472.76 | 175.60ms | 293.80ms | 346.36MB |
| django | basic_hello_world | single | 1 | 3674.54 | 30.77ms | 203.03ms | 75.38MB |
| django | basic_json_response | multi | 10 | 5528.15 | 175.35ms | 277.00ms | 348.89MB |
| django | basic_json_response | single | 1 | 3614.40 | 31.37ms | 210.28ms | 75.38MB |
| django | basic_path_params | multi | 10 | 5553.92 | 178.95ms | 421.08ms | 350.12MB |
| django | basic_path_params | single | 1 | 3550.95 | 31.88ms | 211.71ms | 75.41MB |
| django | basic_query_params | multi | 10 | 5623.24 | 172.94ms | 250.24ms | 351.34MB |
| django | basic_query_params | single | 1 | 3435.35 | 33.17ms | 232.20ms | 75.44MB |
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
| flask | basic_complex_json | single | 1 | 3638.34 | 31.35ms | 222.50ms | 43.88MB |
| flask | basic_hello_world | multi | 10 | 5494.72 | 176.97ms | 284.54ms | 285.56MB |
| flask | basic_hello_world | single | 1 | 3788.66 | 29.65ms | 184.47ms | 72.23MB |
| flask | basic_json_response | multi | 10 | 5537.28 | 174.38ms | 269.80ms | 287.73MB |
| flask | basic_json_response | single | 1 | 3846.31 | 29.20ms | 181.36ms | 46.42MB |
| flask | basic_path_params | multi | 10 | 5449.18 | 177.13ms | 274.15ms | 288.75MB |
| flask | basic_path_params | single | 1 | 3733.64 | 30.37ms | 203.01ms | 43.83MB |
| flask | basic_query_params | multi | 10 | 5526.52 | 174.02ms | 289.53ms | 289.88MB |
| flask | basic_query_params | single | 1 | 3581.73 | 32.31ms | 246.97ms | 43.88MB |
| sanic | basic_complex_json | multi | 10 | 123708.53 | 9.96ms | 58.85ms | 321.42MB |
| sanic | basic_complex_json | single | 1 | 52130.11 | 1.98ms | 5.59ms | 34.06MB |
| sanic | basic_hello_world | multi | 10 | 166872.43 | 8.12ms | 49.52ms | 504.88MB |
| sanic | basic_hello_world | single | 1 | 76038.33 | 1.33ms | 2.67ms | 40.45MB |
| sanic | basic_json_response | multi | 10 | 103164.95 | 16.17ms | 116.42ms | 275.14MB |
| sanic | basic_json_response | single | 1 | 68338.93 | 1.48ms | 2.54ms | 40.48MB |
| sanic | basic_path_params | multi | 10 | 147732.39 | 7.89ms | 39.16ms | 279.56MB |
| sanic | basic_path_params | single | 1 | 60981.89 | 1.71ms | 5.12ms | 33.72MB |
| sanic | basic_query_params | multi | 10 | 107821.98 | 11.09ms | 57.68ms | 309.23MB |
| sanic | basic_query_params | single | 1 | 37078.58 | 3.00ms | 13.38ms | 34.00MB |

## Catzilla Performance Advantage

This report shows how Catzilla performs compared to other frameworks in the **basic** category.
