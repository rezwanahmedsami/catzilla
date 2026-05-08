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
- **Date**: Fri May  8 14:17:30 +06 2026

## Performance Results

| Framework | Endpoint | Worker Mode | Workers | Requests/sec | Avg Latency | 99% Latency | Peak Memory |
|-----------|----------|-------------|---------|--------------|-------------|-------------|-------------|
| catzilla | basic_complex_json | multi | 10 | 141860.17 | 7.84ms | 51.21ms | 177.47MB |
| catzilla | basic_complex_json | single | 1 | 42865.50 | 2.42ms | 2.55ms | 28.03MB |
| catzilla | basic_hello_world | multi | 10 | 197946.62 | 6.27ms | 39.30ms | 308.44MB |
| catzilla | basic_hello_world | single | 1 | 76169.38 | 1.33ms | 1.42ms | 28.81MB |
| catzilla | basic_json_response | multi | 10 | 192597.28 | 5.66ms | 22.67ms | 308.55MB |
| catzilla | basic_json_response | single | 1 | 60562.15 | 1.74ms | 1.94ms | 28.83MB |
| catzilla | basic_path_params | multi | 10 | 175879.55 | 6.19ms | 36.05ms | 308.69MB |
| catzilla | basic_path_params | single | 1 | 51858.54 | 1.99ms | 2.05ms | 28.84MB |
| catzilla | basic_query_params | multi | 10 | 126099.79 | 8.24ms | 83.99ms | 248.72MB |
| catzilla | basic_query_params | single | 1 | 32044.11 | 3.31ms | 3.27ms | 28.09MB |
| django | basic_complex_json | multi | 10 | 5735.88 | 169.06ms | 258.98ms | 351.61MB |
| django | basic_complex_json | single | 1 | 2724.15 | 57.36ms | 826.71ms | 52.98MB |
| django | basic_hello_world | multi | 10 | 5607.75 | 171.90ms | 266.32ms | 346.02MB |
| django | basic_hello_world | single | 1 | 2854.41 | 52.43ms | 725.82ms | 52.78MB |
| django | basic_json_response | multi | 10 | 5601.73 | 172.54ms | 326.02ms | 348.47MB |
| django | basic_json_response | single | 1 | 2791.37 | 53.35ms | 737.28ms | 52.83MB |
| django | basic_path_params | multi | 10 | 5646.92 | 172.31ms | 320.71ms | 349.70MB |
| django | basic_path_params | single | 1 | 2709.17 | 55.43ms | 775.38ms | 52.86MB |
| django | basic_query_params | multi | 10 | 5686.92 | 170.32ms | 303.09ms | 350.78MB |
| django | basic_query_params | single | 1 | 2577.18 | 60.28ms | 854.14ms | 52.94MB |
| fastapi | basic_complex_json | multi | 10 | 33503.81 | 30.00ms | 69.48ms | 360.52MB |
| fastapi | basic_complex_json | single | 1 | 7518.15 | 13.29ms | 17.00ms | 32.14MB |
| fastapi | basic_hello_world | multi | 10 | 49098.41 | 20.95ms | 58.32ms | 341.05MB |
| fastapi | basic_hello_world | single | 1 | 10990.12 | 9.04ms | 10.41ms | 30.34MB |
| fastapi | basic_json_response | multi | 10 | 43766.03 | 23.92ms | 72.15ms | 348.50MB |
| fastapi | basic_json_response | single | 1 | 9722.76 | 10.24ms | 11.97ms | 31.23MB |
| fastapi | basic_path_params | multi | 10 | 40011.80 | 25.53ms | 68.33ms | 353.80MB |
| fastapi | basic_path_params | single | 1 | 9143.00 | 10.93ms | 13.81ms | 31.42MB |
| fastapi | basic_query_params | multi | 10 | 21546.97 | 47.07ms | 117.78ms | 358.12MB |
| fastapi | basic_query_params | single | 1 | 4627.60 | 21.57ms | 26.79ms | 32.12MB |
| flask | basic_complex_json | multi | 10 | 5564.92 | 174.82ms | 314.14ms | 290.08MB |
| flask | basic_complex_json | single | 1 | 2955.27 | 48.33ms | 637.93ms | 46.42MB |
| flask | basic_hello_world | multi | 10 | 5592.58 | 173.91ms | 279.62ms | 285.36MB |
| flask | basic_hello_world | single | 1 | 3086.90 | 46.85ms | 631.64ms | 46.23MB |
| flask | basic_json_response | multi | 10 | 5624.81 | 173.10ms | 270.58ms | 287.55MB |
| flask | basic_json_response | single | 1 | 3049.76 | 48.65ms | 679.85ms | 46.28MB |
| flask | basic_path_params | multi | 10 | 5671.62 | 173.35ms | 263.49ms | 288.50MB |
| flask | basic_path_params | single | 1 | 2998.81 | 48.68ms | 660.29ms | 46.33MB |
| flask | basic_query_params | multi | 10 | 5611.63 | 170.76ms | 304.17ms | 289.66MB |
| flask | basic_query_params | single | 1 | 2875.33 | 51.29ms | 700.14ms | 46.41MB |

## Catzilla Performance Advantage

This report shows how Catzilla performs compared to other frameworks in the **basic** category.
