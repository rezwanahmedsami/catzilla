# Catzilla Udi Category Performance Report

## Test Configuration
- **Category**: di
- **Duration**: 10s
- **Connections**: 100
- **Threads**: 4
- **Tool**: wrk
- **Date**: Sat Aug 16 02:02:03 +06 2025

## Performance Results

| Framework | Endpoint | Requests/sec | Avg Latency | 99% Latency |
|-----------|----------|--------------|-------------|-------------|
| catzilla | di_complex_di_chain | 11206.00 | 11.67ms | 112.07ms |
| catzilla | di_request_scoped_di | 12422.91 | 10.05ms | 99.61ms |
| catzilla | di_simple_di | 17681.88 | 6.40ms | 30.73ms |
| catzilla | di_singleton_di | 13804.00 | 8.02ms | 15.07ms |
| catzilla | di_transient_di | 15211.64 | 8.21ms | 80.25ms |
| catzilla | sqlalchemy-di_complex_di_chain | 13717.58 | 8.02ms | 15.11ms |
| django | di_complex_di_chain | 382.86 | 9.74ms | 79.71ms |
| django | di_request_scoped_di | 4.58 | 6.81ms | 22.46ms |
| django | di_simple_di | 960.14 | 42.75ms | 54.24ms |
| django | di_singleton_di | 1660.75 | 41.18ms | 55.19ms |
| django | di_transient_di | 0.89 | 2.97ms | 5.90ms |
| fastapi | di_complex_di_chain | 2580.27 | 38.65ms | 55.03ms |
| fastapi | di_request_scoped_di | 2656.40 | 37.55ms | 50.70ms |
| fastapi | di_simple_di | 3095.09 | 32.25ms | 42.21ms |
| fastapi | di_singleton_di | 2750.20 | 36.25ms | 49.76ms |
| fastapi | di_transient_di | 2806.23 | 36.03ms | 89.88ms |
| fastapi | sqlalchemy-di_complex_di_chain | 2918.84 | 34.22ms | 58.01ms |

## Catzilla Performance Advantage

This report shows how Catzilla performs compared to other frameworks in the **di** category.
