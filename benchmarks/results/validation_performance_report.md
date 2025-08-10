# Catzilla Uvalidation Category Performance Report

## Test Configuration
- **Category**: validation
- **Duration**: 10s
- **Connections**: 100
- **Threads**: 4
- **Tool**: wrk
- **Date**: Mon Aug 11 01:01:19 +06 2025

## Performance Results

| Framework | Endpoint | Requests/sec | Avg Latency | 99% Latency |
|-----------|----------|--------------|-------------|-------------|
| catzilla | validation_array_validation | 2657.82 | 63.54ms | 968.14ms |
| catzilla | validation_complex_validation | 5159.79 | 25.54ms | 307.79ms |
| catzilla | validation_health_check | 12166.68 | 9.49ms | 57.58ms |
| catzilla | validation_nested_validation | 5443.61 | 24.01ms | 244.01ms |
| catzilla | validation_performance_test | 1493.30 | 86.00ms | 990.17ms |
| catzilla | validation_simple_validation | 8307.68 | 17.28ms | 193.09ms |
| catzilla | validation_user_validation | 7161.75 | 17.27ms | 163.12ms |
| django | validation_array_validation | 562.08 | 49.30ms | 72.76ms |
| django | validation_complex_validation | 167.98 | 51.82ms | 99.27ms |
| django | validation_health_check | 922.40 | 108.09ms | 252.37ms |
| django | validation_nested_validation | 490.10 | 22.23ms | 72.88ms |
| django | validation_performance_test | 468.84 | 53.75ms | 91.10ms |
| django | validation_simple_validation | 0.99 | 3.35ms | 8.47ms |
| fastapi | validation_array_validation | 714.61 | 138.87ms | 158.68ms |
| fastapi | validation_complex_validation | 1306.21 | 76.16ms | 91.19ms |
| fastapi | validation_health_check | 2518.82 | 39.54ms | 50.53ms |
| fastapi | validation_nested_validation | 1361.48 | 74.23ms | 199.17ms |
| fastapi | validation_performance_test | 272.92 | 359.38ms | 415.53ms |
| fastapi | validation_simple_validation | 2162.64 | 46.11ms | 56.19ms |
| fastapi | validation_user_validation | 1766.39 | 56.46ms | 66.41ms |
| flask | validation_array_validation | 1663.23 | 47.79ms | 60.72ms |
| flask | validation_complex_validation | 1.10 | 4.82ms | 10.40ms |
| flask | validation_health_check | 1087.59 | 52.91ms | 73.76ms |
| flask | validation_nested_validation | 946.75 | 47.33ms | 63.82ms |
| flask | validation_performance_test | 4.06 | 6.82ms | 19.36ms |
| flask | validation_simple_validation | 0.69 | 2.71ms | 4.85ms |
| flask | validation_user_validation | 1660.15 | 39.15ms | 55.62ms |

## Catzilla Performance Advantage

This report shows how Catzilla performs compared to other frameworks in the **validation** category.
