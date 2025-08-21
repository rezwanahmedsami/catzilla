# Catzilla Sqlalchemy-di Category Performance Report

## Test Configuration
- **Category**: sqlalchemy-di
- **Duration**: 10s
- **Connections**: 100
- **Threads**: 4
- **Tool**: wrk
- **Date**: Thu Aug 21 05:56:08 UTC 2025

## Performance Results

| Framework | Endpoint | Requests/sec | Avg Latency | 99% Latency |
|-----------|----------|--------------|-------------|-------------|
| catzilla | sqlalchemy-di_complex_db_operations | 36170.33 | 2.95ms | 13.21ms |
| catzilla | sqlalchemy-di_complex_di_chain | 35372.58 | 3.19ms | 18.81ms |
| catzilla | sqlalchemy-di_db_posts_list | 35713.69 | 3.09ms | 18.08ms |
| catzilla | sqlalchemy-di_db_user_detail | 35983.91 | 2.98ms | 14.73ms |
| catzilla | sqlalchemy-di_db_users_list | 34969.17 | 3.11ms | 16.14ms |
| catzilla | sqlalchemy-di_health_check | 1985.54 | 71.04ms | 914.36ms |
| catzilla | sqlalchemy-di_simple_di | 34646.11 | 3.22ms | 17.96ms |
| catzilla | sqlalchemy-di_transient_di | 34772.48 | 3.22ms | 15.77ms |
| fastapi | sqlalchemy-di_complex_db_operations | 5736.77 | 17.42ms | 33.69ms |
| fastapi | sqlalchemy-di_complex_di_chain | 5627.35 | 17.69ms | 34.89ms |
| fastapi | sqlalchemy-di_db_posts_list | 5747.94 | 17.38ms | 33.76ms |
| fastapi | sqlalchemy-di_db_user_detail | 5721.40 | 17.51ms | 34.48ms |
| fastapi | sqlalchemy-di_db_users_list | 5691.37 | 17.66ms | 35.35ms |
| fastapi | sqlalchemy-di_health_check | 1166.30 | 85.18ms | 130.32ms |
| fastapi | sqlalchemy-di_simple_di | 5765.49 | 17.33ms | 33.82ms |
| fastapi | sqlalchemy-di_transient_di | 5590.27 | 17.94ms | 35.27ms |
| flask | sqlalchemy-di_complex_db_operations | 14946.33 | 6.71ms | 17.77ms |
| flask | sqlalchemy-di_complex_di_chain | 15032.60 | 6.65ms | 14.79ms |
| flask | sqlalchemy-di_db_posts_list | 14948.34 | 6.72ms | 18.02ms |
| flask | sqlalchemy-di_db_user_detail | 15221.05 | 6.54ms | 17.89ms |
| flask | sqlalchemy-di_db_users_list | 15291.28 | 6.50ms | 18.30ms |
| flask | sqlalchemy-di_health_check | 5398.86 | 18.47ms | 36.89ms |
| flask | sqlalchemy-di_simple_di | 15446.14 | 6.42ms | 17.81ms |
| flask | sqlalchemy-di_transient_di | 15396.63 | 6.44ms | 17.66ms |

## Catzilla Performance Advantage

This report shows how Catzilla performs compared to other frameworks in the **sqlalchemy-di** category.
