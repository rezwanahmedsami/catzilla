# Catzilla Middleware Category Performance Report

## Test Configuration
- **Category**: middleware
- **Duration**: 10s
- **Connections**: 100
- **Threads**: 4
- **Tool**: wrk
- **Date**: Thu Aug 21 06:44:47 UTC 2025

## Performance Results

| Framework | Endpoint | Requests/sec | Avg Latency | 99% Latency |
|-----------|----------|--------------|-------------|-------------|
| catzilla | middleware_auth_middleware | 19288.46 | 5.39ms | 19.25ms |
| catzilla | middleware_compression_middleware | 35346.85 | 3.03ms | 15.18ms |
| catzilla | middleware_cors_middleware | 34276.46 | 3.10ms | 13.96ms |
| catzilla | middleware_health_check | 20405.56 | 5.08ms | 17.84ms |
| catzilla | middleware_heavy_middleware | 19042.85 | 5.35ms | 14.32ms |
| catzilla | middleware_home | 21574.09 | 4.91ms | 18.27ms |
| catzilla | middleware_light_middleware | 19851.49 | 5.26ms | 16.83ms |
| catzilla | middleware_logging_middleware | 36114.11 | 2.92ms | 11.99ms |
| django | middleware_auth_middleware | 14891.62 | 6.60ms | 20.74ms |
| django | middleware_compression_middleware | 14666.55 | 6.79ms | 21.07ms |
| django | middleware_cors_middleware | 14520.99 | 6.90ms | 21.99ms |
| django | middleware_health_check | 15003.56 | 6.51ms | 19.32ms |
| django | middleware_heavy_middleware | 14966.16 | 6.55ms | 19.25ms |
| django | middleware_home | 15048.87 | 6.48ms | 18.22ms |
| django | middleware_light_middleware | 14946.07 | 6.60ms | 21.09ms |
| django | middleware_logging_middleware | 14556.78 | 6.89ms | 23.00ms |
| fastapi | middleware_auth_middleware | 1072.64 | 92.30ms | 127.25ms |
| fastapi | middleware_compression_middleware | 1086.04 | 91.32ms | 137.71ms |
| fastapi | middleware_cors_middleware | 1137.87 | 87.24ms | 87.24ms |
| fastapi | middleware_health_check | 1117.78 | 89.19ms | 110.36ms |
| fastapi | middleware_heavy_middleware | 1067.61 | 93.18ms | 131.25ms |
| fastapi | middleware_home | 1107.66 | 89.87ms | 111.21ms |
| fastapi | middleware_light_middleware | 1090.90 | 91.17ms | 116.39ms |
| fastapi | middleware_logging_middleware | 1122.17 | 87.98ms | 114.06ms |

## Catzilla Performance Advantage

This report shows how Catzilla performs compared to other frameworks in the **middleware** category.
