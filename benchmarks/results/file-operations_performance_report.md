# Catzilla Ufile-operations Category Performance Report

## Test Configuration
- **Category**: file-operations
- **Duration**: 10s
- **Connections**: 100
- **Threads**: 4
- **Tool**: wrk
- **Date**: Sun Aug 17 21:07:15 +06 2025

## Performance Results

| Framework | Endpoint | Requests/sec | Avg Latency | 99% Latency |
|-----------|----------|--------------|-------------|-------------|
| catzilla | file-operations_binary_file_download | 14608.65 | 7.30ms | 11.19ms |
| catzilla | file-operations_data_streaming | 14258.77 | 7.66ms | 11.91ms |
| catzilla | file-operations_health_check | 12695.96 | 8.78ms | 14.96ms |
| catzilla | file-operations_large_file_upload | 15007.68 | 7.13ms | 11.13ms |
| catzilla | file-operations_medium_file_upload | 14578.28 | 7.82ms | 51.04ms |
| catzilla | file-operations_small_file_upload | 16668.76 | 6.44ms | 9.95ms |
| catzilla | file-operations_static_image_serve | 6743.31 | 18.45ms | 137.30ms |
| catzilla | file-operations_text_file_download | 14594.99 | 7.66ms | 11.49ms |
| django | file-operations_binary_file_download | 440.54 | 224.09ms | 257.51ms |
| django | file-operations_data_streaming | 403.26 | 244.29ms | 432.41ms |
| django | file-operations_health_check | 0.10 | 4.13ms | 4.13ms |
| django | file-operations_large_file_upload | 443.78 | 222.58ms | 389.12ms |
| django | file-operations_medium_file_upload | 492.33 | 200.67ms | 237.25ms |
| django | file-operations_small_file_upload | 606.32 | 163.11ms | 191.91ms |
| django | file-operations_static_image_serve | 433.44 | 227.71ms | 258.77ms |
| django | file-operations_text_file_download | 434.25 | 226.64ms | 355.71ms |
| fastapi | file-operations_binary_file_download | 2364.45 | 43.66ms | 144.02ms |
| fastapi | file-operations_data_streaming | 2491.55 | 39.79ms | 50.68ms |
| fastapi | file-operations_health_check | 2592.11 | 38.47ms | 48.05ms |
| fastapi | file-operations_large_file_upload | 2453.69 | 40.66ms | 57.49ms |
| fastapi | file-operations_medium_file_upload | 2428.29 | 41.14ms | 59.32ms |
| fastapi | file-operations_small_file_upload | 2374.31 | 42.53ms | 112.53ms |
| fastapi | file-operations_static_image_serve | 2399.68 | 41.57ms | 59.03ms |
| fastapi | file-operations_text_file_download | 2526.74 | 39.48ms | 50.29ms |
| flask | file-operations_binary_file_download | 836.63 | 41.41ms | 53.55ms |
| flask | file-operations_data_streaming | 1651.41 | 37.25ms | 49.67ms |
| flask | file-operations_health_check | 1037.70 | 52.57ms | 132.35ms |
| flask | file-operations_large_file_upload | 2.18 | 5.23ms | 21.75ms |
| flask | file-operations_medium_file_upload | 1662.92 | 42.95ms | 56.91ms |
| flask | file-operations_small_file_upload | 0.50 | 3.39ms | 4.42ms |
| flask | file-operations_static_image_serve | 0.49 | 2.30ms | 3.88ms |
| flask | file-operations_text_file_download | 0.10 | 8.13ms | 8.13ms |

## Catzilla Performance Advantage

This report shows how Catzilla performs compared to other frameworks in the **file-operations** category.
