# Catzilla Umiddleware Category Performance Report

## Test Configuration
- **Category**: middleware
- **Duration**: 10s
- **Connections**: 100
- **Threads**: 4
- **Tool**: wrk
- **Date**: Sun Aug 17 20:51:00 +06 2025

## Performance Results

| Framework | Endpoint | Requests/sec | Avg Latency | 99% Latency |
|-----------|----------|--------------|-------------|-------------|
| catzilla | middleware_auth_middleware | 8575.40 | 13.98ms | 95.45ms |
| catzilla | middleware_compression_middleware | 13056.76 | 9.63ms | 96.11ms |
| catzilla | middleware_cors_middleware | 14143.89 | 7.81ms | 12.06ms |
| catzilla | middleware_health_check | 10373.25 | 10.75ms | 16.98ms |
| catzilla | middleware_heavy_middleware | 8363.97 | 13.89ms | 80.38ms |
| catzilla | middleware_home | 11458.31 | 4.87ms | 14.95ms |
| catzilla | middleware_light_middleware | 9399.07 | 11.95ms | 11.95ms |
| catzilla | middleware_logging_middleware | 13976.50 | 7.85ms | 11.93ms |
| django | middleware_auth_middleware | 286.55 | 8.59ms | 103.99ms |
| django | middleware_compression_middleware | 1145.55 | 86.49ms | 103.04ms |
| django | middleware_cors_middleware | 967.37 | 88.15ms | 123.60ms |
| django | middleware_health_check | 0.50 | 6.54ms | 10.64ms |
| django | middleware_heavy_middleware | 191.49 | 99.23ms | 143.37ms |
| django | middleware_home | 1008.14 | 98.27ms | 118.41ms |
| django | middleware_light_middleware | 1156.18 | 85.68ms | 99.14ms |
| django | middleware_logging_middleware | 33.46 | 51.09ms | 121.26ms |
| fastapi | middleware_auth_middleware | 239.49 | 402.70ms | 488.75ms |
| fastapi | middleware_compression_middleware | 248.62 | 392.02ms | 459.63ms |
| fastapi | middleware_cors_middleware | 258.20 | 384.94ms | 477.92ms |
| fastapi | middleware_health_check | 455.08 | 218.17ms | 254.66ms |
| fastapi | middleware_heavy_middleware | 368.90 | 273.46ms | 617.08ms |
| fastapi | middleware_home | 448.35 | 221.75ms | 259.45ms |
| fastapi | middleware_light_middleware | 448.62 | 219.85ms | 273.18ms |
| fastapi | middleware_logging_middleware | 248.25 | 393.16ms | 462.47ms |
| flask | middleware_auth_middleware | 0.00 | 0.00us | 0.00us |
| flask | middleware_compression_middleware | 1579.07 | 55.57ms | 103.04ms |
| flask | middleware_cors_middleware | 970.32 | 53.28ms | 93.88ms |
| flask | middleware_health_check | 1.19 | 8.35ms | 28.73ms |
| flask | middleware_heavy_middleware | 3.59 | 5.44ms | 17.05ms |
| flask | middleware_home | 894.51 | 47.84ms | 141.71ms |
| flask | middleware_light_middleware | 1654.05 | 47.00ms | 63.32ms |
| flask | middleware_logging_middleware | 2.19 | 4.54ms | 11.75ms |

## Catzilla Performance Advantage

This report shows how Catzilla performs compared to other frameworks in the **middleware** category.
