# Catzilla Middleware Category Performance Report

## Test Configuration
- **Category**: middleware
- **Duration**: 10s
- **Connections**: 100
- **Threads**: 4
- **Tool**: wrk
- **Date**: Thu Aug 21 05:13:03 UTC 2025

## Performance Results

| Framework | Endpoint | Requests/sec | Avg Latency | 99% Latency |
|-----------|----------|--------------|-------------|-------------|
| catzilla | middleware_auth_middleware | 19279.74 | 5.47ms | 22.40ms |
| catzilla | middleware_compression_middleware | 35501.39 | 3.11ms | 18.08ms |
| catzilla | middleware_cors_middleware | 36191.91 | 2.99ms | 15.31ms |
| catzilla | middleware_health_check | 20584.69 | 5.00ms | 16.00ms |
| catzilla | middleware_heavy_middleware | 18719.39 | 5.58ms | 18.00ms |
| catzilla | middleware_home | 20205.14 | 5.13ms | 17.97ms |
| catzilla | middleware_light_middleware | 19316.86 | 5.40ms | 17.98ms |
| catzilla | middleware_logging_middleware | 36307.13 | 3.00ms | 15.54ms |
| django | middleware_auth_middleware | 14951.03 | 6.63ms | 22.65ms |
| django | middleware_compression_middleware | 14705.00 | 6.73ms | 20.08ms |
| django | middleware_cors_middleware | 14595.10 | 6.81ms | 20.53ms |
| django | middleware_health_check | 15070.40 | 6.46ms | 17.49ms |
| django | middleware_heavy_middleware | 15020.70 | 6.54ms | 20.96ms |
| django | middleware_home | 14973.02 | 6.55ms | 19.24ms |
| django | middleware_light_middleware | 15018.05 | 6.57ms | 22.58ms |
| django | middleware_logging_middleware | 14499.14 | 6.89ms | 22.70ms |
| fastapi | middleware_auth_middleware | 1067.40 | 93.34ms | 119.05ms |
| fastapi | middleware_compression_middleware | 1077.42 | 92.36ms | 118.19ms |
| fastapi | middleware_cors_middleware | 1097.88 | 90.55ms | 117.96ms |
| fastapi | middleware_health_check | 1117.48 | 88.55ms | 113.35ms |
| fastapi | middleware_heavy_middleware | 1055.08 | 93.98ms | 120.03ms |
| fastapi | middleware_home | 1117.91 | 88.89ms | 117.43ms |
| fastapi | middleware_light_middleware | 1086.57 | 91.52ms | 116.21ms |
| fastapi | middleware_logging_middleware | 1098.69 | 90.56ms | 133.31ms |

## Catzilla Performance Advantage

This report shows how Catzilla performs compared to other frameworks in the **middleware** category.
