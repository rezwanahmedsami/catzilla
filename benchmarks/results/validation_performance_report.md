# Catzilla Uvalidation Category Performance Report

## Test Configuration
- **Category**: validation
- **Duration**: 10s
- **Connections**: 100
- **Threads**: 4
- **Tool**: wrk
- **Date**: Sat Aug 16 01:30:30 +06 2025

## Performance Results

| Framework | Endpoint | Requests/sec | Avg Latency | 99% Latency |
|-----------|----------|--------------|-------------|-------------|
| catzilla | validation_array_validation | 2037.23 | 80.58ms | 1.11s |
| catzilla | validation_complex_validation | 3818.78 | 34.06ms | 276.42ms |
| catzilla | validation_health_check | 11686.35 | 10.02ms | 72.19ms |
| catzilla | validation_nested_validation | 5262.26 | 22.90ms | 202.30ms |
| catzilla | validation_performance_test | 1228.19 | 96.54ms | 961.84ms |
| catzilla | validation_simple_validation | 8748.30 | 14.49ms | 139.27ms |
| catzilla | validation_user_validation | 6967.69 | 17.67ms | 134.95ms |
| django | validation_array_validation | 210.50 | 1.12ms | 9.89ms |
| django | validation_complex_validation | 172.96 | 45.97ms | 74.79ms |
| django | validation_health_check | 922.40 | 108.09ms | 252.37ms |
| django | validation_nested_validation | 785.17 | 45.01ms | 59.37ms |
| django | validation_performance_test | 726.10 | 49.70ms | 64.50ms |
| django | validation_simple_validation | 494.49 | 14.24ms | 75.00ms |
| django | validation_user_validation | 0.20 | 2.82ms | 4.64ms |
| fastapi | validation_array_validation | 566.95 | 176.11ms | 405.86ms |
| fastapi | validation_complex_validation | 1126.25 | 88.27ms | 160.70ms |
| fastapi | validation_health_check | 2101.04 | 48.81ms | 153.05ms |
| fastapi | validation_nested_validation | 1356.93 | 73.43ms | 105.12ms |
| fastapi | validation_performance_test | 251.93 | 389.08ms | 596.33ms |
| fastapi | validation_simple_validation | 1891.91 | 53.41ms | 137.43ms |
| fastapi | validation_user_validation | 1608.79 | 62.73ms | 164.86ms |
| flask | validation_array_validation | 1663.23 | 47.79ms | 60.72ms |
| flask | validation_complex_validation | 2.67 | 8.02ms | 19.95ms |
| flask | validation_health_check | 1029.88 | 52.81ms | 68.82ms |
| flask | validation_nested_validation | 972.19 | 52.48ms | 177.86ms |
| flask | validation_performance_test | 966.15 | 50.63ms | 67.15ms |
| flask | validation_simple_validation | 1.19 | 3.12ms | 6.51ms |
| flask | validation_user_validation | 1660.15 | 39.15ms | 55.62ms |

## Catzilla Performance Advantage

This report shows how Catzilla performs compared to other frameworks in the **validation** category.
