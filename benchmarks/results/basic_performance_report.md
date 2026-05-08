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
- **Date**: Fri May  8 17:16:17 +06 2026

## Performance Results

| Framework | Endpoint | Worker Mode | Workers | Requests/sec | Avg Latency | 99% Latency | Peak Memory |
|-----------|----------|-------------|---------|--------------|-------------|-------------|-------------|
| catzilla | basic_complex_json | multi | 10 | 141860.17 | 7.84ms | 51.21ms | 177.47MB |
| catzilla | basic_complex_json | single | 1 | 41511.90 | 2.49ms | 2.57ms | 28.05MB |
| catzilla | basic_hello_world | multi | 10 | 197946.62 | 6.27ms | 39.30ms | 308.44MB |
| catzilla | basic_hello_world | single | 1 | 73849.34 | 1.38ms | 1.46ms | 28.78MB |
| catzilla | basic_json_response | multi | 10 | 192597.28 | 5.66ms | 22.67ms | 308.55MB |
| catzilla | basic_json_response | single | 1 | 58260.58 | 1.75ms | 2.16ms | 28.80MB |
| catzilla | basic_path_params | multi | 10 | 175879.55 | 6.19ms | 36.05ms | 308.69MB |
| catzilla | basic_path_params | single | 1 | 49706.91 | 2.08ms | 2.93ms | 28.81MB |
| catzilla | basic_query_params | multi | 10 | 126099.79 | 8.24ms | 83.99ms | 248.72MB |
| catzilla | basic_query_params | single | 1 | 30561.92 | 3.48ms | 7.87ms | 28.12MB |
| django | basic_complex_json | multi | 10 | 5735.88 | 169.06ms | 258.98ms | 351.61MB |
| django | basic_complex_json | single | 1 | 2727.78 | 55.10ms | 758.64ms | 53.73MB |
| django | basic_hello_world | multi | 10 | 5607.75 | 171.90ms | 266.32ms | 346.02MB |
| django | basic_hello_world | single | 1 | 2834.77 | 51.29ms | 690.45ms | 53.58MB |
| django | basic_json_response | multi | 10 | 5601.73 | 172.54ms | 326.02ms | 348.47MB |
| django | basic_json_response | single | 1 | 2777.89 | 56.25ms | 809.69ms | 53.61MB |
| django | basic_path_params | multi | 10 | 5646.92 | 172.31ms | 320.71ms | 349.70MB |
| django | basic_path_params | single | 1 | 2758.51 | 52.97ms | 716.95ms | 53.62MB |
| django | basic_query_params | multi | 10 | 5686.92 | 170.32ms | 303.09ms | 350.78MB |
| django | basic_query_params | single | 1 | 2618.86 | 59.22ms | 830.72ms | 53.72MB |
| fastapi | basic_complex_json | multi | 10 | 33503.81 | 30.00ms | 69.48ms | 360.52MB |
| fastapi | basic_complex_json | single | 1 | 7657.84 | 13.05ms | 13.56ms | 32.88MB |
| fastapi | basic_hello_world | multi | 10 | 49098.41 | 20.95ms | 58.32ms | 341.05MB |
| fastapi | basic_hello_world | single | 1 | 11131.23 | 8.94ms | 9.44ms | 31.33MB |
| fastapi | basic_json_response | multi | 10 | 43766.03 | 23.92ms | 72.15ms | 348.50MB |
| fastapi | basic_json_response | single | 1 | 9742.41 | 10.26ms | 12.51ms | 32.34MB |
| fastapi | basic_path_params | multi | 10 | 40011.80 | 25.53ms | 68.33ms | 353.80MB |
| fastapi | basic_path_params | single | 1 | 9168.65 | 10.83ms | 12.27ms | 32.42MB |
| fastapi | basic_query_params | multi | 10 | 21546.97 | 47.07ms | 117.78ms | 358.12MB |
| fastapi | basic_query_params | single | 1 | 4725.44 | 20.99ms | 22.04ms | 32.84MB |
| flask | basic_complex_json | multi | 10 | 5564.92 | 174.82ms | 314.14ms | 290.08MB |
| flask | basic_complex_json | single | 1 | 2900.97 | 49.79ms | 652.40ms | 47.69MB |
| flask | basic_hello_world | multi | 10 | 5592.58 | 173.91ms | 279.62ms | 285.36MB |
| flask | basic_hello_world | single | 1 | 3059.29 | 46.24ms | 605.43ms | 47.53MB |
| flask | basic_json_response | multi | 10 | 5624.81 | 173.10ms | 270.58ms | 287.55MB |
| flask | basic_json_response | single | 1 | 3011.35 | 47.93ms | 643.63ms | 47.56MB |
| flask | basic_path_params | multi | 10 | 5671.62 | 173.35ms | 263.49ms | 288.50MB |
| flask | basic_path_params | single | 1 | 2976.64 | 49.85ms | 693.52ms | 47.58MB |
| flask | basic_query_params | multi | 10 | 5611.63 | 170.76ms | 304.17ms | 289.66MB |
| flask | basic_query_params | single | 1 | 2839.05 | 54.12ms | 768.85ms | 47.62MB |

## Catzilla Performance Advantage

This report shows how Catzilla performs compared to other frameworks in the **basic** category.
