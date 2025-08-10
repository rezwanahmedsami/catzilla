# Catzilla Usqlalchemy-di Category Performance Report

## Test Configuration
- **Category**: sqlalchemy-di
- **Duration**: 10s
- **Connections**: 100
- **Threads**: 4
- **Tool**: wrk
- **Date**: Mon Aug 11 01:14:27 +06 2025

## Performance Results

| Framework | Endpoint | Requests/sec | Avg Latency | 99% Latency |
|-----------|----------|--------------|-------------|-------------|
| catzilla | sqlalchemy-di_complex_db_operations | 13277.21 | 9.87ms | 110.25ms |
| catzilla | sqlalchemy-di_complex_di_chain | 13717.58 | 8.02ms | 15.11ms |
| catzilla | sqlalchemy-di_db_posts_list | 13251.21 | 9.11ms | 85.93ms |
| catzilla | sqlalchemy-di_db_user_detail | 14257.14 | 7.56ms | 14.09ms |
| catzilla | sqlalchemy-di_db_users_list | 14922.16 | 7.35ms | 13.04ms |
| catzilla | sqlalchemy-di_health_check | 1061.84 | 100.79ms | 919.45ms |
| catzilla | sqlalchemy-di_simple_di | 17727.83 | 6.80ms | 64.66ms |
| catzilla | sqlalchemy-di_transient_di | 15207.82 | 8.59ms | 93.00ms |
| fastapi | sqlalchemy-di_complex_db_operations | 2880.18 | 34.64ms | 59.85ms |
| fastapi | sqlalchemy-di_complex_di_chain | 2918.84 | 34.22ms | 58.01ms |
| fastapi | sqlalchemy-di_db_posts_list | 2747.35 | 37.59ms | 138.52ms |
| fastapi | sqlalchemy-di_db_user_detail | 2933.75 | 34.02ms | 57.90ms |
| fastapi | sqlalchemy-di_db_users_list | 2929.40 | 34.10ms | 57.20ms |
| fastapi | sqlalchemy-di_health_check | 556.06 | 178.99ms | 405.41ms |
| fastapi | sqlalchemy-di_simple_di | 2832.13 | 36.51ms | 132.10ms |
| fastapi | sqlalchemy-di_transient_di | 2924.31 | 34.13ms | 57.48ms |
| flask | sqlalchemy-di_complex_db_operations | 1039.07 | 95.57ms | 137.64ms |
| flask | sqlalchemy-di_db_posts_list | 85.93 | 96.34ms | 163.56ms |
| flask | sqlalchemy-di_db_user_detail | 1014.72 | 97.74ms | 144.41ms |
| flask | sqlalchemy-di_db_users_list | 158.82 | 97.31ms | 150.10ms |
| flask | sqlalchemy-di_health_check | 376.02 | 261.95ms | 468.00ms |
| flask | sqlalchemy-di_simple_di | 827.07 | 108.15ms | 177.12ms |

## Catzilla Performance Advantage

This report shows how Catzilla performs compared to other frameworks in the **sqlalchemy-di** category.
