# Catzilla Performance Benchmark Results

## Test Configuration
- **Duration**: 10s
- **Connections**: 100
- **Threads**: 4
- **Tool**: wrk
- **Date**: Sun Aug 10 17:24:03 +06 2025

## Performance Results

| Framework | Endpoint | Requests/sec | Avg Latency | 99% Latency |
|-----------|----------|--------------|-------------|-------------|
| catzilla
fastapi
flask
django |  |  |  |  |
| catzilla | basic_complex_json | 7810.99 | 18.89ms | 274.70ms |
| catzilla | basic_hello_world | 14801.21 | 8.77ms | 84.41ms |
| catzilla | basic_json_response | 11065.91 | 11.43ms | 118.40ms |
| catzilla | basic_path_params | 9653.17 | 17.73ms | 315.66ms |
| catzilla | basic_query_params | 6590.27 | 24.44ms | 382.17ms |
| catzilla | sqlalchemy-di_complex_db_operations | 12770.11 | 3.81ms | 7.29ms |
| catzilla | sqlalchemy-di_complex_di_chain | 12664.09 | 3.87ms | 7.78ms |
| catzilla | sqlalchemy-di_db_posts_list | 11771.53 | 6.68ms | 90.69ms |
| catzilla | sqlalchemy-di_db_user_detail | 13366.57 | 3.64ms | 6.90ms |
| catzilla | sqlalchemy-di_db_users_list | 14257.25 | 3.43ms | 6.47ms |
| catzilla | sqlalchemy-di_health_check | 943.16 | 71.12ms | 725.43ms |
| catzilla | sqlalchemy-di_simple_di | 16751.77 | 2.91ms | 5.23ms |
| catzilla | sqlalchemy-di_transient_di | 15327.43 | 3.19ms | 5.91ms |
| catzilla | validation_array_validation | 12999.58 | 9.26ms | 76.79ms |
| catzilla | validation_complex_validation | 12944.03 | 8.90ms | 47.90ms |
| catzilla | validation_health_check | 10964.44 | 12.28ms | 161.47ms |
| catzilla | validation_nested_validation | 10449.22 | 12.43ms | 120.61ms |
| catzilla | validation_performance_test | 11585.28 | 27.22ms | 569.42ms |
| catzilla | validation_simple_validation | 13431.67 | 11.13ms | 130.50ms |
| catzilla | validation_user_validation | 13698.74 | 11.53ms | 157.08ms |
|  |  |  |  |  |
| django | basic_complex_json | 842.15 | 118.01ms | 234.68ms |
| fastapi | basic_complex_json | 2091.87 | 47.61ms | 65.93ms |
| fastapi | basic_hello_world | 3282.63 | 30.21ms | 40.23ms |
| fastapi | basic_json_response | 2837.33 | 35.27ms | 66.24ms |
| fastapi | basic_path_params | 2466.21 | 40.44ms | 60.65ms |
| fastapi | basic_query_params | 1427.68 | 69.69ms | 97.47ms |
| fastapi | sqlalchemy-di_complex_db_operations | 2435.56 | 19.39ms | 28.49ms |
| fastapi | sqlalchemy-di_complex_di_chain | 2465.88 | 19.41ms | 26.89ms |
| fastapi | sqlalchemy-di_db_posts_list | 2471.84 | 19.11ms | 27.97ms |
| fastapi | sqlalchemy-di_db_user_detail | 2375.15 | 21.03ms | 86.68ms |
| fastapi | sqlalchemy-di_db_users_list | 2473.63 | 19.34ms | 29.30ms |
| fastapi | sqlalchemy-di_health_check | 482.63 | 98.11ms | 144.78ms |
| fastapi | sqlalchemy-di_simple_di | 2584.34 | 18.44ms | 27.11ms |
| fastapi | sqlalchemy-di_transient_di | 2401.14 | 19.62ms | 30.22ms |
| flask | basic_complex_json | 1130.77 | 88.73ms | 203.17ms |
| flask | basic_hello_world | 1107.04 | 90.18ms | 173.38ms |
| flask | basic_path_params | 0.00 | 0.00us | 0.00us |
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
