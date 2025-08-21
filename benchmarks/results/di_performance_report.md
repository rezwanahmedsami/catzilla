# Catzilla Di Category Performance Report

## Test Configuration
- **Category**: di
- **Duration**: 10s
- **Connections**: 100
- **Threads**: 4
- **Tool**: wrk
- **Date**: Thu Aug 21 05:46:51 UTC 2025

## Performance Results

| Framework | Endpoint | Requests/sec | Avg Latency | 99% Latency |
|-----------|----------|--------------|-------------|-------------|
| catzilla | di_complex_di_chain | 35332.76 | 3.10ms | 15.59ms |
| catzilla | di_request_scoped_di | 35451.77 | 2.97ms | 12.41ms |
| catzilla | di_simple_di | 34721.43 | 3.23ms | 18.85ms |
| catzilla | di_singleton_di | 34947.44 | 3.10ms | 15.66ms |
| catzilla | di_transient_di | 34585.82 | 3.06ms | 14.17ms |
| django | di_complex_di_chain | 14585.52 | 6.85ms | 20.48ms |
| django | di_request_scoped_di | 15010.18 | 6.50ms | 18.56ms |
| django | di_simple_di | 15186.14 | 6.38ms | 19.35ms |
| django | di_singleton_di | 15080.14 | 6.41ms | 17.56ms |
| django | di_transient_di | 15221.91 | 6.38ms | 19.26ms |
| fastapi | di_complex_di_chain | 5669.73 | 17.61ms | 34.81ms |
| fastapi | di_request_scoped_di | 5695.35 | 17.53ms | 35.26ms |
| fastapi | di_simple_di | 5596.69 | 18.32ms | 50.78ms |
| fastapi | di_singleton_di | 5777.91 | 17.27ms | 34.57ms |
| fastapi | di_transient_di | 5783.88 | 17.29ms | 35.25ms |

## Catzilla Performance Advantage

This report shows how Catzilla performs compared to other frameworks in the **di** category.
