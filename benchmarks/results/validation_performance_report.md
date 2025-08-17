# Catzilla Uvalidation Category Performance Report

## Test Configuration
- **Category**: validation
- **Duration**: 10s
- **Connections**: 100
- **Threads**: 4
- **Tool**: wrk
- **Date**: Sun Aug 17 21:39:40 +06 2025

## Performance Results

| Framework | Endpoint | Requests/sec | Avg Latency | 99% Latency |
|-----------|----------|--------------|-------------|-------------|
| catzilla | validation_array_validation | 2551.03 | 64.99ms | 976.14ms |
| catzilla | validation_complex_validation | 4620.01 | 29.90ms | 382.76ms |
| catzilla | validation_health_check | 6460.13 | 15.75ms | 24.07ms |
| catzilla | validation_nested_validation | 3383.64 | 52.07ms | 660.73ms |
| catzilla | validation_performance_test | 1512.42 | 86.93ms | 1.03s |
| catzilla | validation_simple_validation | 4856.21 | 27.28ms | 330.69ms |
| catzilla | validation_user_validation | 4150.46 | 35.07ms | 500.56ms |
| django | validation_array_validation | 626.54 | 43.87ms | 69.57ms |
| django | validation_complex_validation | 3.77 | 3.09ms | 25.32ms |
| django | validation_health_check | 0.00 | 0.00us | 0.00us |
| django | validation_nested_validation | 1648.43 | 41.23ms | 54.06ms |
| django | validation_performance_test | 833.59 | 48.37ms | 166.06ms |
| django | validation_simple_validation | 875.04 | 45.81ms | 61.42ms |
| django | validation_user_validation | 4.56 | 8.44ms | 22.04ms |
| fastapi | validation_array_validation | 683.29 | 145.16ms | 274.42ms |
| fastapi | validation_complex_validation | 1293.11 | 76.98ms | 90.85ms |
| fastapi | validation_health_check | 2592.79 | 38.46ms | 48.46ms |
| fastapi | validation_nested_validation | 1312.24 | 75.86ms | 117.88ms |
| fastapi | validation_performance_test | 276.48 | 354.61ms | 395.88ms |
| fastapi | validation_simple_validation | 1959.18 | 51.99ms | 152.46ms |
| fastapi | validation_user_validation | 1147.54 | 86.58ms | 175.90ms |
| flask | validation_array_validation | 1623.16 | 41.30ms | 56.39ms |
| flask | validation_complex_validation | 2.38 | 5.95ms | 27.39ms |
| flask | validation_health_check | 996.00 | 54.08ms | 126.66ms |
| flask | validation_nested_validation | 889.82 | 44.79ms | 63.36ms |
| flask | validation_performance_test | 952.26 | 47.04ms | 73.83ms |
| flask | validation_simple_validation | 0.30 | 2.03ms | 2.33ms |
| flask | validation_user_validation | 1627.19 | 40.47ms | 58.94ms |

## Catzilla Performance Advantage

This report shows how Catzilla performs compared to other frameworks in the **validation** category.
