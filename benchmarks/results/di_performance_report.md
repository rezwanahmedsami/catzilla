# Catzilla Udi Category Performance Report

## Test Configuration
- **Category**: di
- **Duration**: 10s
- **Connections**: 100
- **Threads**: 4
- **Tool**: wrk
- **Date**: Sun Aug 17 20:37:31 +06 2025

## Performance Results

| Framework | Endpoint | Requests/sec | Avg Latency | 99% Latency |
|-----------|----------|--------------|-------------|-------------|
| catzilla | di_complex_di_chain | 13571.29 | 8.59ms | 61.04ms |
| catzilla | di_request_scoped_di | 14808.92 | 7.26ms | 11.13ms |
| catzilla | di_simple_di | 17166.64 | 6.54ms | 33.36ms |
| catzilla | di_singleton_di | 14420.93 | 7.45ms | 15.51ms |
| catzilla | di_transient_di | 15725.93 | 6.82ms | 11.49ms |
| catzilla | sqlalchemy-di_complex_di_chain | 9671.26 | 14.44ms | 146.37ms |
| django | di_complex_di_chain | 1.29 | 6.94ms | 18.74ms |
| django | di_request_scoped_di | 0.60 | 2.99ms | 6.70ms |
| django | di_simple_di | 1091.05 | 58.63ms | 80.85ms |
| django | di_singleton_di | 1661.58 | 48.76ms | 61.99ms |
| django | di_transient_di | 1.09 | 5.11ms | 13.48ms |
| fastapi | di_complex_di_chain | 2446.13 | 40.79ms | 54.90ms |
| fastapi | di_request_scoped_di | 2433.76 | 40.96ms | 55.38ms |
| fastapi | di_simple_di | 2575.93 | 38.84ms | 55.97ms |
| fastapi | di_singleton_di | 2347.37 | 44.01ms | 154.93ms |
| fastapi | di_transient_di | 2535.67 | 39.29ms | 50.13ms |
| fastapi | sqlalchemy-di_complex_di_chain | 1813.77 | 55.54ms | 136.55ms |
| flask | sqlalchemy-di_complex_di_chain | 890.20 | 45.31ms | 68.91ms |

## Catzilla Performance Advantage

This report shows how Catzilla performs compared to other frameworks in the **di** category.
