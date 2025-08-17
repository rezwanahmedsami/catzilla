# Catzilla Usqlalchemy-di Category Performance Report

## Test Configuration
- **Category**: sqlalchemy-di
- **Duration**: 10s
- **Connections**: 100
- **Threads**: 4
- **Tool**: wrk
- **Date**: Sun Aug 17 20:44:16 +06 2025

## Performance Results

| Framework | Endpoint | Requests/sec | Avg Latency | 99% Latency |
|-----------|----------|--------------|-------------|-------------|
| catzilla | sqlalchemy-di_complex_db_operations | 13346.14 | 8.58ms | 8.58ms |
| catzilla | sqlalchemy-di_complex_di_chain | 13839.62 | 7.96ms | 11.90ms |
| catzilla | sqlalchemy-di_db_posts_list | 14092.92 | 7.70ms | 11.22ms |
| catzilla | sqlalchemy-di_db_user_detail | 14308.89 | 7.72ms | 11.68ms |
| catzilla | sqlalchemy-di_db_users_list | 14429.21 | 8.40ms | 70.44ms |
| catzilla | sqlalchemy-di_health_check | 1059.34 | 104.14ms | 992.54ms |
| catzilla | sqlalchemy-di_simple_di | 17915.25 | 5.94ms | 8.27ms |
| catzilla | sqlalchemy-di_transient_di | 14901.48 | 8.00ms | 68.86ms |
| fastapi | sqlalchemy-di_complex_db_operations | 2335.82 | 43.39ms | 117.53ms |
| fastapi | sqlalchemy-di_complex_di_chain | 2416.54 | 41.26ms | 65.56ms |
| fastapi | sqlalchemy-di_db_posts_list | 2308.43 | 44.03ms | 126.79ms |
| fastapi | sqlalchemy-di_db_user_detail | 2393.85 | 41.64ms | 62.39ms |
| fastapi | sqlalchemy-di_db_users_list | 2417.82 | 41.26ms | 65.88ms |
| fastapi | sqlalchemy-di_health_check | 564.97 | 175.51ms | 253.99ms |
| fastapi | sqlalchemy-di_simple_di | 2353.17 | 43.76ms | 144.49ms |
| fastapi | sqlalchemy-di_transient_di | 2379.57 | 42.29ms | 93.08ms |
| flask | sqlalchemy-di_complex_db_operations | 4.67 | 13.38ms | 33.64ms |
| flask | sqlalchemy-di_complex_di_chain | 1655.56 | 44.74ms | 57.12ms |
| flask | sqlalchemy-di_db_posts_list | 954.85 | 51.62ms | 140.68ms |
| flask | sqlalchemy-di_db_user_detail | 0.89 | 5.43ms | 26.91ms |
| flask | sqlalchemy-di_db_users_list | 507.06 | 52.30ms | 76.09ms |
| flask | sqlalchemy-di_health_check | 855.60 | 115.82ms | 139.17ms |
| flask | sqlalchemy-di_simple_di | 18.54 | 30.66ms | 89.44ms |
| flask | sqlalchemy-di_transient_di | 494.42 | 30.42ms | 64.90ms |

## Catzilla Performance Advantage

This report shows how Catzilla performs compared to other frameworks in the **sqlalchemy-di** category.
