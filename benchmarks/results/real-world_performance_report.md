# Catzilla Real-world Category Performance Report

## Test Configuration
- **Category**: real-world
- **Duration**: 10s
- **Connections**: 100
- **Threads**: 4
- **Tool**: wrk
- **Date**: Thu Aug 21 06:24:47 UTC 2025

## Performance Results

| Framework | Endpoint | Requests/sec | Avg Latency | 99% Latency |
|-----------|----------|--------------|-------------|-------------|
| catzilla | real-world_analytics_dashboard | 16817.59 | 6.13ms | 20.76ms |
| catzilla | real-world_analytics_tracking | 30930.96 | 3.42ms | 15.40ms |
| catzilla | real-world_blog_listing | 17115.96 | 6.02ms | 19.13ms |
| catzilla | real-world_blog_post_detail | 16747.77 | 6.30ms | 22.84ms |
| catzilla | real-world_health_check | 19768.34 | 5.38ms | 23.05ms |
| catzilla | real-world_order_processing | 31964.99 | 3.26ms | 12.51ms |
| catzilla | real-world_product_detail | 17019.09 | 6.10ms | 20.58ms |
| catzilla | real-world_product_search | 17689.07 | 5.96ms | 22.02ms |
| django | real-world_analytics_dashboard | 14188.89 | 7.12ms | 21.10ms |
| django | real-world_analytics_tracking | 15070.36 | 6.50ms | 19.20ms |
| django | real-world_blog_listing | 603.19 | 164.04ms | 184.74ms |
| django | real-world_blog_post_detail | 375.09 | 262.34ms | 281.81ms |
| django | real-world_health_check | 15399.12 | 6.23ms | 18.96ms |
| django | real-world_order_processing | 15043.93 | 6.49ms | 19.16ms |
| django | real-world_product_detail | 462.78 | 213.23ms | 229.63ms |
| django | real-world_product_search | 952.74 | 104.14ms | 129.36ms |
| fastapi | real-world_analytics_dashboard | 3449.95 | 30.59ms | 93.55ms |
| fastapi | real-world_analytics_tracking | 5449.32 | 19.04ms | 65.14ms |
| fastapi | real-world_blog_listing | 2789.90 | 35.97ms | 82.84ms |
| fastapi | real-world_blog_post_detail | 3168.60 | 32.87ms | 93.07ms |
| fastapi | real-world_health_check | 5568.43 | 17.95ms | 35.37ms |
| fastapi | real-world_order_processing | 5442.92 | 18.62ms | 50.60ms |
| fastapi | real-world_product_detail | 2623.16 | 38.03ms | 69.01ms |
| fastapi | real-world_product_search | 2943.25 | 33.94ms | 65.94ms |
| flask | real-world_analytics_dashboard | 16807.86 | 5.62ms | 5.62ms |
| flask | real-world_analytics_tracking | 15198.45 | 6.57ms | 19.24ms |
| flask | real-world_blog_listing | 605.31 | 163.18ms | 191.35ms |
| flask | real-world_blog_post_detail | 376.62 | 261.57ms | 279.39ms |
| flask | real-world_health_check | 17005.58 | 5.58ms | 18.83ms |
| flask | real-world_order_processing | 15312.16 | 6.47ms | 17.71ms |
| flask | real-world_product_detail | 464.06 | 212.19ms | 243.92ms |
| flask | real-world_product_search | 951.15 | 104.49ms | 133.15ms |

## Catzilla Performance Advantage

This report shows how Catzilla performs compared to other frameworks in the **real-world** category.
