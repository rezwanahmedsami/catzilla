# Catzilla Performance Benchmark Results

## Test Configuration
- **Duration**: 5s
- **Connections**: 50
- **Threads**: 4
- **Tool**: wrk
- **Date**: Sat Aug  2 17:08:21 +06 2025

## Performance Results

| Framework | Endpoint | Requests/sec | Avg Latency | 99% Latency |
|-----------|----------|--------------|-------------|-------------|
| catzilla
fastapi
flask
django |  |  |  |  |
| catzilla | sqlalchemy-di_complex_db_operations | 12770.11 | 3.81ms | 7.29ms |
| catzilla | sqlalchemy-di_complex_di_chain | 12664.09 | 3.87ms | 7.78ms |
| catzilla | sqlalchemy-di_db_posts_list | 11771.53 | 6.68ms | 90.69ms |
| catzilla | sqlalchemy-di_db_user_detail | 13366.57 | 3.64ms | 6.90ms |
| catzilla | sqlalchemy-di_db_users_list | 14257.25 | 3.43ms | 6.47ms |
| catzilla | sqlalchemy-di_health_check | 943.16 | 71.12ms | 725.43ms |
| catzilla | sqlalchemy-di_simple_di | 16751.77 | 2.91ms | 5.23ms |
| catzilla | sqlalchemy-di_transient_di | 15327.43 | 3.19ms | 5.91ms |
|  |  |  |  |  |
| fastapi | sqlalchemy-di_complex_db_operations | 2435.56 | 19.39ms | 28.49ms |
| fastapi | sqlalchemy-di_complex_di_chain | 2465.88 | 19.41ms | 26.89ms |
| fastapi | sqlalchemy-di_db_posts_list | 2471.84 | 19.11ms | 27.97ms |
| fastapi | sqlalchemy-di_db_user_detail | 2375.15 | 21.03ms | 86.68ms |
| fastapi | sqlalchemy-di_db_users_list | 2473.63 | 19.34ms | 29.30ms |
| fastapi | sqlalchemy-di_health_check | 482.63 | 98.11ms | 144.78ms |
| fastapi | sqlalchemy-di_simple_di | 2584.34 | 18.44ms | 27.11ms |
| fastapi | sqlalchemy-di_transient_di | 2401.14 | 19.62ms | 30.22ms |
| flask | sqlalchemy-di_complex_db_operations | 152.08 | 67.08ms | 92.64ms |
| flask | sqlalchemy-di_complex_di_chain | 864.07 | 55.03ms | 79.55ms |
| flask | sqlalchemy-di_db_posts_list | 732.08 | 64.96ms | 101.01ms |
| flask | sqlalchemy-di_db_user_detail | 746.80 | 67.05ms | 278.60ms |
| flask | sqlalchemy-di_db_users_list | 64.74 | 52.79ms | 72.47ms |
| flask | sqlalchemy-di_health_check | 316.20 | 150.69ms | 365.16ms |
| flask | sqlalchemy-di_simple_di | 749.23 | 63.50ms | 115.01ms |
| flask | sqlalchemy-di_transient_di | 741.84 | 64.09ms | 93.75ms |
| django |  |  |  |  |
| catzilla
fastapi
flask
django |  |  |  |  |
