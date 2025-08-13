# Catzilla Umiddleware Category Performance Report

## Test Configuration
- **Category**: middleware
- **Duration**: 10s
- **Connections**: 100
- **Threads**: 4
- **Tool**: wrk
- **Date**: Wed Aug 13 23:49:56 +06 2025

## Performance Results

| Framework | Endpoint | Requests/sec | Avg Latency | 99% Latency |
|-----------|----------|--------------|-------------|-------------|
| catzilla | middleware_auth_middleware | 7040.52 | 17.78ms | 173.95ms |
| catzilla | middleware_compression_middleware | 10867.38 | 10.39ms | 10.39ms |
| catzilla | middleware_cors_middleware | 10144.21 | 12.29ms | 120.64ms |
| catzilla | middleware_health_check | 3165.09 | 36.92ms | 201.87ms |
| catzilla | middleware_heavy_middleware | 6284.37 | 23.86ms | 385.72ms |
| catzilla | middleware_home | 4594.22 | 35.27ms | 556.29ms |
| catzilla | middleware_light_middleware | 4885.07 | 28.02ms | 308.47ms |
| catzilla | middleware_logging_middleware | 10934.92 | 10.56ms | 44.27ms |
| django | middleware_auth_middleware | 419.39 | 17.99ms | 80.38ms |
| django | middleware_compression_middleware | 983.85 | 60.20ms | 78.88ms |
| django | middleware_cors_middleware | 695.93 | 63.61ms | 83.38ms |
| django | middleware_health_check | 18.07 | 31.54ms | 86.26ms |
| django | middleware_heavy_middleware | 11.64 | 2.34ms | 8.58ms |
| django | middleware_home | 1196.89 | 75.59ms | 175.82ms |
| django | middleware_light_middleware | 1569.15 | 63.15ms | 79.73ms |
| django | middleware_logging_middleware | 120.25 | 29.96ms | 84.02ms |
| fastapi | middleware_auth_middleware | 326.85 | 297.35ms | 505.83ms |
| fastapi | middleware_compression_middleware | 367.90 | 270.20ms | 387.29ms |
| fastapi | middleware_cors_middleware | 346.56 | 286.19ms | 483.96ms |
| fastapi | middleware_health_check | 348.37 | 285.18ms | 508.96ms |
| fastapi | middleware_heavy_middleware | 348.00 | 282.99ms | 337.03ms |
| fastapi | middleware_home | 356.53 | 275.36ms | 547.23ms |
| fastapi | middleware_light_middleware | 358.12 | 276.60ms | 350.87ms |
| fastapi | middleware_logging_middleware | 348.17 | 283.44ms | 457.62ms |
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
