# Catzilla Ureal-world Category Performance Report

## Test Configuration
- **Category**: real-world
- **Duration**: 10s
- **Connections**: 100
- **Threads**: 4
- **Tool**: wrk
- **Date**: Sun Aug 17 21:23:58 +06 2025

## Performance Results

| Framework | Endpoint | Requests/sec | Avg Latency | 99% Latency |
|-----------|----------|--------------|-------------|-------------|
| catzilla | real-world_analytics_dashboard | 7311.78 | 16.84ms | 128.20ms |
| catzilla | real-world_analytics_tracking | 12719.55 | 8.72ms | 13.23ms |
| catzilla | real-world_blog_listing | 7942.33 | 15.30ms | 130.95ms |
| catzilla | real-world_blog_post_detail | 7845.48 | 14.78ms | 82.31ms |
| catzilla | real-world_health_check | 9278.97 | 12.20ms | 38.94ms |
| catzilla | real-world_order_processing | 12436.09 | 9.73ms | 80.16ms |
| catzilla | real-world_product_detail | 7528.94 | 16.77ms | 128.73ms |
| catzilla | real-world_product_search | 8068.41 | 15.06ms | 123.75ms |
| django | real-world_analytics_dashboard | 436.17 | 53.45ms | 153.04ms |
| django | real-world_analytics_tracking | 240.37 | 9.75ms | 66.78ms |
| django | real-world_blog_listing | 331.76 | 296.20ms | 318.03ms |
| django | real-world_blog_post_detail | 229.89 | 425.02ms | 551.54ms |
| django | real-world_health_check | 1096.31 | 56.42ms | 87.89ms |
| django | real-world_order_processing | 464.03 | 34.86ms | 71.37ms |
| django | real-world_product_detail | 304.19 | 322.99ms | 382.52ms |
| django | real-world_product_search | 0.70 | 7.33ms | 12.44ms |
| fastapi | real-world_analytics_dashboard | 1546.75 | 65.37ms | 170.20ms |
| fastapi | real-world_analytics_tracking | 2374.64 | 42.16ms | 93.59ms |
| fastapi | real-world_blog_listing | 1358.70 | 73.30ms | 123.79ms |
| fastapi | real-world_blog_post_detail | 1425.04 | 71.00ms | 190.20ms |
| fastapi | real-world_health_check | 2580.68 | 38.65ms | 49.99ms |
| fastapi | real-world_order_processing | 2419.50 | 41.28ms | 73.89ms |
| fastapi | real-world_product_detail | 1124.79 | 88.82ms | 198.52ms |
| fastapi | real-world_product_search | 1340.40 | 75.97ms | 213.03ms |
| flask | real-world_analytics_dashboard | 561.72 | 45.00ms | 72.30ms |
| flask | real-world_analytics_tracking | 284.79 | 12.42ms | 61.82ms |
| flask | real-world_blog_listing | 1.59 | 21.09ms | 37.34ms |
| flask | real-world_blog_post_detail | 229.79 | 424.68ms | 511.16ms |
| flask | real-world_health_check | 574.42 | 25.89ms | 63.30ms |
| flask | real-world_order_processing | 838.53 | 71.23ms | 260.36ms |
| flask | real-world_product_detail | 286.74 | 340.36ms | 523.17ms |
| flask | real-world_product_search | 103.23 | 148.01ms | 177.04ms |

## Catzilla Performance Advantage

This report shows how Catzilla performs compared to other frameworks in the **real-world** category.
