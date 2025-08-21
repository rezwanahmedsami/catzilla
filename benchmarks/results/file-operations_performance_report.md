# Catzilla File-operations Category Performance Report

## Test Configuration
- **Category**: file-operations
- **Duration**: 10s
- **Connections**: 100
- **Threads**: 4
- **Tool**: wrk
- **Date**: Thu Aug 21 06:05:46 UTC 2025

## Performance Results

| Framework | Endpoint | Requests/sec | Avg Latency | 99% Latency |
|-----------|----------|--------------|-------------|-------------|
| catzilla | file-operations_binary_file_download | 35779.06 | 3.04ms | 16.60ms |
| catzilla | file-operations_data_streaming | 35191.42 | 3.05ms | 14.90ms |
| catzilla | file-operations_health_check | 21266.39 | 5.10ms | 21.70ms |
| catzilla | file-operations_large_file_upload | 34742.84 | 3.21ms | 17.54ms |
| catzilla | file-operations_medium_file_upload | 35053.24 | 3.15ms | 17.33ms |
| catzilla | file-operations_small_file_upload | 34758.80 | 3.16ms | 17.21ms |
| catzilla | file-operations_static_image_serve | 15283.55 | 6.83ms | 22.95ms |
| catzilla | file-operations_text_file_download | 34741.03 | 3.12ms | 15.10ms |
| django | file-operations_binary_file_download | 1748.03 | 56.91ms | 86.71ms |
| django | file-operations_data_streaming | 1766.73 | 56.23ms | 77.44ms |
| django | file-operations_health_check | 1888.85 | 52.55ms | 74.12ms |
| django | file-operations_large_file_upload | 1782.26 | 55.83ms | 76.87ms |
| django | file-operations_medium_file_upload | 1752.88 | 56.78ms | 79.08ms |
| django | file-operations_small_file_upload | 1815.31 | 54.82ms | 82.95ms |
| django | file-operations_static_image_serve | 1767.61 | 56.28ms | 78.30ms |
| django | file-operations_text_file_download | 1763.01 | 56.40ms | 78.03ms |
| fastapi | file-operations_binary_file_download | 5623.46 | 17.72ms | 35.20ms |
| fastapi | file-operations_data_streaming | 5511.39 | 18.14ms | 35.55ms |
| fastapi | file-operations_health_check | 5631.47 | 17.75ms | 34.88ms |
| fastapi | file-operations_large_file_upload | 5592.78 | 17.90ms | 35.66ms |
| fastapi | file-operations_medium_file_upload | 5446.68 | 18.50ms | 35.74ms |
| fastapi | file-operations_small_file_upload | 5492.39 | 18.41ms | 37.58ms |
| fastapi | file-operations_static_image_serve | 5416.66 | 18.52ms | 36.03ms |
| fastapi | file-operations_text_file_download | 5575.18 | 17.95ms | 35.40ms |
| flask | file-operations_binary_file_download | 16579.48 | 5.74ms | 17.43ms |
| flask | file-operations_data_streaming | 16368.71 | 5.79ms | 17.13ms |
| flask | file-operations_health_check | 17112.28 | 5.65ms | 21.68ms |
| flask | file-operations_large_file_upload | 16558.86 | 5.74ms | 16.41ms |
| flask | file-operations_medium_file_upload | 16706.59 | 5.75ms | 17.99ms |
| flask | file-operations_small_file_upload | 16749.61 | 5.70ms | 16.02ms |
| flask | file-operations_static_image_serve | 15333.55 | 6.47ms | 18.84ms |
| flask | file-operations_text_file_download | 16705.79 | 5.64ms | 17.22ms |

## Catzilla Performance Advantage

This report shows how Catzilla performs compared to other frameworks in the **file-operations** category.
