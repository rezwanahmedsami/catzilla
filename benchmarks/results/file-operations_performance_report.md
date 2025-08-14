# Catzilla Ufile-operations Category Performance Report

## Test Configuration
- **Category**: file-operations
- **Duration**: 10s
- **Connections**: 100
- **Threads**: 4
- **Tool**: wrk
- **Date**: Thu Aug 14 14:59:44 +06 2025

## Performance Results

| Framework | Endpoint | Requests/sec | Avg Latency | 99% Latency |
|-----------|----------|--------------|-------------|-------------|
| catzilla | file-operations_binary_file_download | 13315.51 | 8.51ms | 16.70ms |
| catzilla | file-operations_data_streaming | 12875.33 | 9.92ms | 95.74ms |
| catzilla | file-operations_health_check | 12002.07 | 9.53ms | 45.11ms |
| catzilla | file-operations_large_file_upload | 8942.64 | 16.07ms | 164.54ms |
| catzilla | file-operations_medium_file_upload | 10664.51 | 11.75ms | 109.83ms |
| catzilla | file-operations_small_file_upload | 12112.70 | 10.56ms | 88.08ms |
| catzilla | file-operations_static_image_serve | 6438.09 | 20.70ms | 251.56ms |
| catzilla | file-operations_text_file_download | 13391.76 | 8.44ms | 16.34ms |
| django | file-operations_binary_file_download | 382.76 | 257.41ms | 342.06ms |
| django | file-operations_data_streaming | 377.15 | 258.77ms | 433.53ms |
| django | file-operations_health_check | 378.30 | 258.45ms | 443.61ms |
| django | file-operations_large_file_upload | 393.28 | 250.70ms | 330.28ms |
| django | file-operations_medium_file_upload | 377.32 | 261.47ms | 487.54ms |
| django | file-operations_small_file_upload | 349.27 | 282.69ms | 592.45ms |
| django | file-operations_static_image_serve | 364.45 | 269.60ms | 476.99ms |
| django | file-operations_text_file_download | 379.43 | 260.02ms | 415.57ms |
| fastapi | file-operations_binary_file_download | 2639.73 | 37.78ms | 49.73ms |
| fastapi | file-operations_data_streaming | 2468.80 | 41.46ms | 130.08ms |
| fastapi | file-operations_health_check | 3140.47 | 31.77ms | 40.13ms |
| fastapi | file-operations_large_file_upload | 2664.63 | 38.09ms | 112.90ms |
| fastapi | file-operations_medium_file_upload | 2865.38 | 34.92ms | 51.55ms |
| fastapi | file-operations_small_file_upload | 3015.98 | 33.10ms | 42.94ms |
| fastapi | file-operations_static_image_serve | 2533.63 | 39.35ms | 57.08ms |
| fastapi | file-operations_text_file_download | 2678.87 | 37.24ms | 46.47ms |
| flask | file-operations_binary_file_download | 774.98 | 130.71ms | 359.69ms |
| flask | file-operations_health_check | 835.94 | 119.69ms | 299.84ms |
| flask | file-operations_large_file_upload | 524.83 | 147.52ms | 422.50ms |
| flask | file-operations_medium_file_upload | 825.88 | 120.44ms | 249.95ms |
| flask | file-operations_small_file_upload | 283.82 | 106.34ms | 203.34ms |
| flask | file-operations_text_file_download | 201.45 | 154.19ms | 454.17ms |

## Catzilla Performance Advantage

This report shows how Catzilla performs compared to other frameworks in the **file-operations** category.
