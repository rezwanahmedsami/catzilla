# Catzilla Performance Benchmark Results

## Test Configuration
- **Duration**: 10s
- **Connections**: 100
- **Threads**: 4
- **Tool**: wrk
- **Date**: Mon Jun  2 03:00:37 +06 2025

## System Information

**Error**: System information collection failed

## Performance Results

| Framework | Endpoint | Requests/sec | Avg Latency | 99% Latency |
|-----------|----------|--------------|-------------|-------------|
| catzilla | complex_json | 14249.36 | 7.77ms | 17.67ms |
| catzilla | hello_world | 30985.31 | 3.41ms | 8.15ms |
| catzilla | json_response | 17676.85 | 6.18ms | 17.65ms |
| catzilla | path_params | 15454.02 | 8.35ms | 53.97ms |
| catzilla | query_params | 10082.42 | 12.14ms | 94.44ms |
| catzilla | query_validation | 11203.22 | 10.47ms | 50.05ms |
| catzilla | validate_product_model | 6950.62 | 17.72ms | 100.25ms |
| catzilla | validate_user_model | 10568.48 | 11.21ms | 66.29ms |
