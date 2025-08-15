# Catzilla Ureal-world Category Performance Report

## Test Configuration
- **Category**: real-world
- **Duration**: 10s
- **Connections**: 100
- **Threads**: 4
- **Tool**: wrk
- **Date**: Sat Aug 16 03:03:05 +06 2025

## Performance Results

| Framework | Endpoint | Requests/sec | Avg Latency | 99% Latency |
|-----------|----------|--------------|-------------|-------------|
| catzilla | real-world_analytics_dashboard | 5322.75 | 23.60ms | 178.54ms |
| catzilla | real-world_analytics_tracking | 9309.27 | 12.52ms | 76.06ms |
| catzilla | real-world_blog_listing | 6407.98 | 20.34ms | 235.14ms |
| catzilla | real-world_blog_post_detail | 6158.35 | 21.21ms | 247.45ms |
| catzilla | real-world_health_check | 9913.78 | 11.98ms | 91.28ms |
| catzilla | real-world_order_processing | 9458.08 | 12.50ms | 92.60ms |
| catzilla | real-world_product_detail | 5178.21 | 24.30ms | 160.62ms |
| catzilla | real-world_product_search | 7977.00 | 14.67ms | 90.71ms |
| django | real-world_analytics_dashboard | 724.36 | 55.85ms | 73.94ms |
| django | real-world_analytics_tracking | 291.58 | 10.80ms | 72.40ms |
| django | real-world_blog_listing | 46.74 | 30.95ms | 189.37ms |
| django | real-world_blog_post_detail | 238.25 | 408.95ms | 531.61ms |
| django | real-world_health_check | 1010.94 | 51.31ms | 69.30ms |
| django | real-world_order_processing | 688.34 | 53.51ms | 70.38ms |
| django | real-world_product_detail | 280.49 | 349.21ms | 435.98ms |
| django | real-world_product_search | 0.30 | 10.61ms | 18.91ms |
| fastapi | real-world_analytics_dashboard | 1368.16 | 74.46ms | 204.60ms |
| fastapi | real-world_analytics_tracking | 2089.77 | 48.74ms | 146.24ms |
| fastapi | real-world_blog_listing | 1283.02 | 77.68ms | 139.41ms |
| fastapi | real-world_blog_post_detail | 1350.49 | 73.75ms | 135.65ms |
| fastapi | real-world_health_check | 2907.51 | 34.30ms | 44.48ms |
| fastapi | real-world_order_processing | 2200.24 | 46.57ms | 144.76ms |
| fastapi | real-world_product_detail | 1107.85 | 91.23ms | 250.64ms |
| fastapi | real-world_product_search | 1456.03 | 68.42ms | 109.14ms |
| flask | real-world_analytics_dashboard | 519.34 | 45.17ms | 117.22ms |
| flask | real-world_analytics_tracking | 264.35 | 14.27ms | 60.99ms |
| flask | real-world_blog_listing | 0.49 | 9.56ms | 10.66ms |
| flask | real-world_blog_post_detail | 232.65 | 420.50ms | 534.69ms |
| flask | real-world_health_check | 931.92 | 43.87ms | 72.24ms |
| flask | real-world_order_processing | 605.28 | 46.18ms | 60.68ms |
| flask | real-world_product_detail | 271.98 | 360.10ms | 393.61ms |
| flask | real-world_product_search | 0.70 | 9.58ms | 22.55ms |

## Catzilla Performance Advantage

This report shows how Catzilla performs compared to other frameworks in the **real-world** category.
