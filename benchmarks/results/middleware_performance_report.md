# Catzilla Umiddleware Category Performance Report

## Test Configuration
- **Category**: middleware
- **Duration**: 10s
- **Connections**: 100
- **Threads**: 4
- **Tool**: wrk
- **Date**: Mon Aug 11 01:42:43 +06 2025

## Performance Results

| Framework | Endpoint | Requests/sec | Avg Latency | 99% Latency |
|-----------|----------|--------------|-------------|-------------|
| catzilla | middleware_auth_middleware | 187.29 | 234.91ms | 728.28ms |
| catzilla | middleware_compression_middleware | 11030.08 | 10.51ms | 37.74ms |
| catzilla | middleware_cors_middleware | 13108.46 | 9.79ms | 111.48ms |
| catzilla | middleware_health_check | 204.29 | 225.88ms | 720.36ms |
| catzilla | middleware_heavy_middleware | 198.49 | 221.02ms | 748.68ms |
| catzilla | middleware_home | 199.67 | 225.05ms | 715.58ms |
| catzilla | middleware_light_middleware | 211.80 | 219.24ms | 719.05ms |
| catzilla | middleware_logging_middleware | 10547.69 | 10.69ms | 48.11ms |
| django | middleware_health_check | 271.09 | 109.38ms | 305.93ms |
| django | middleware_heavy_middleware | 464.50 | 139.64ms | 384.22ms |
| django | middleware_home | 818.79 | 121.05ms | 247.90ms |
| django | middleware_light_middleware | 929.10 | 107.02ms | 211.49ms |

## Catzilla Performance Advantage

This report shows how Catzilla performs compared to other frameworks in the **middleware** category.
