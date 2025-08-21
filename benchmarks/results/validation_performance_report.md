# Catzilla Validation Category Performance Report

## Test Configuration
- **Category**: validation
- **Duration**: 10s
- **Connections**: 100
- **Threads**: 4
- **Tool**: wrk
- **Date**: Thu Aug 21 07:12:23 UTC 2025

## Performance Results

| Framework | Endpoint | Requests/sec | Avg Latency | 99% Latency |
|-----------|----------|--------------|-------------|-------------|
| catzilla | validation_array_validation | 6035.27 | 16.94ms | 33.54ms |
| catzilla | validation_complex_validation | 10629.90 | 9.61ms | 27.05ms |
| catzilla | validation_health_check | 22692.56 | 4.81ms | 21.71ms |
| catzilla | validation_nested_validation | 11205.46 | 9.07ms | 25.94ms |
| catzilla | validation_performance_test | 3346.07 | 30.09ms | 30.09ms |
| catzilla | validation_simple_validation | 17344.45 | 5.98ms | 22.47ms |
| catzilla | validation_user_validation | 14285.74 | 7.28ms | 24.05ms |
| django | validation_array_validation | 15182.54 | 6.32ms | 16.28ms |
| django | validation_complex_validation | 15071.00 | 6.44ms | 19.04ms |
| django | validation_health_check | 4858.83 | 20.52ms | 38.59ms |
| django | validation_nested_validation | 15313.29 | 6.30ms | 17.73ms |
| django | validation_performance_test | 14756.77 | 6.68ms | 20.14ms |
| django | validation_simple_validation | 15396.35 | 6.25ms | 18.72ms |
| django | validation_user_validation | 15333.41 | 6.27ms | 17.28ms |
| fastapi | validation_array_validation | 1597.56 | 62.30ms | 93.19ms |
| fastapi | validation_complex_validation | 2898.44 | 34.26ms | 52.15ms |
| fastapi | validation_health_check | 5377.46 | 18.58ms | 35.02ms |
| fastapi | validation_nested_validation | 3187.73 | 31.17ms | 48.26ms |
| fastapi | validation_performance_test | 612.04 | 161.69ms | 227.93ms |
| fastapi | validation_simple_validation | 4758.64 | 20.99ms | 38.21ms |
| fastapi | validation_user_validation | 4024.36 | 24.88ms | 42.56ms |
| flask | validation_array_validation | 15250.64 | 6.50ms | 17.47ms |
| flask | validation_complex_validation | 16464.79 | 5.82ms | 18.58ms |
| flask | validation_health_check | 17079.12 | 5.45ms | 16.52ms |
| flask | validation_nested_validation | 16430.52 | 5.79ms | 17.76ms |
| flask | validation_performance_test | 14644.97 | 6.88ms | 16.59ms |
| flask | validation_simple_validation | 16946.42 | 5.60ms | 19.67ms |
| flask | validation_user_validation | 16774.47 | 5.60ms | 16.33ms |

## Catzilla Performance Advantage

This report shows how Catzilla performs compared to other frameworks in the **validation** category.
