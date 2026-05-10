# Catzilla Umiddleware Category Performance Report

## Test Configuration
- **Category**: middleware
- **Duration**: 10s
- **Connections**: 100
- **Connections Per Worker**: 100
- **Requested Threads**: 4
- **Worker Mode**: single
- **Workers**: 1
- **Tool**: wrk
- **Date**: Sun May 10 13:12:57 +06 2026

## Performance Results

| Framework | Endpoint | Worker Mode | Workers | Requests/sec | Avg Latency | 99% Latency | Peak Memory |
|-----------|----------|-------------|---------|--------------|-------------|-------------|-------------|
| catzilla | middleware_auth_middleware | single | 1 | 60783.75 | 1.67ms | 2.76ms | 36.28MB |
| catzilla | middleware_health_check | single | 1 | 63639.48 | 1.62ms | 3.07ms | 36.27MB |
| catzilla | middleware_heavy_middleware | single | 1 | 55409.17 | 1.86ms | 3.54ms | 36.28MB |
| catzilla | middleware_home | single | 1 | 64677.71 | 1.58ms | 2.36ms | 36.22MB |
| catzilla | middleware_light_middleware | single | 1 | 61536.36 | 1.68ms | 3.02ms | 36.23MB |

## Catzilla Performance Advantage

This report shows how Catzilla performs compared to other frameworks in the **middleware** category.
