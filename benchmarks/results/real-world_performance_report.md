# Catzilla Ureal-world Category Performance Report

## Test Configuration
- **Category**: real-world
- **Duration**: 10s
- **Connections**: 100
- **Connections Per Worker**: 100
- **Requested Threads**: 4
- **Worker Mode**: single
- **Workers**: 1
- **Tool**: wrk
- **Date**: Sun May 10 13:24:52 +06 2026

## Performance Results

| Framework | Endpoint | Worker Mode | Workers | Requests/sec | Avg Latency | 99% Latency | Peak Memory |
|-----------|----------|-------------|---------|--------------|-------------|-------------|-------------|
| catzilla | real-world_blog_listing | single | 1 | 16351.58 | 7.04ms | 47.81ms | 544.11MB |
| catzilla | real-world_blog_post_detail | single | 1 | 35492.02 | 3.91ms | 55.07ms | 810.05MB |
| catzilla | real-world_health_check | single | 1 | 60285.99 | 1.72ms | 2.52ms | 38.77MB |
| catzilla | real-world_product_detail | single | 1 | 25619.67 | 4.30ms | 8.21ms | 380.72MB |
| catzilla | real-world_product_search | single | 1 | 16834.25 | 6.51ms | 17.13ms | 194.86MB |

## Catzilla Performance Advantage

This report shows how Catzilla performs compared to other frameworks in the **real-world** category.
