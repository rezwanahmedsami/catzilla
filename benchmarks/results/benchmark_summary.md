# Catzilla Performance Benchmark Results

## Test Configuration
- **Duration**: 5s
- **Connections**: 50
- **Threads**: 4
- **Tool**: wrk
- **Date**: Fri Aug  1 11:04:43 +06 2025

## Performance Results

| Framework | Endpoint | Requests/sec | Avg Latency | 99% Latency |
|-----------|----------|--------------|-------------|-------------|
| catzilla | complex_json | 7682.35 | 6.52ms | 12.70ms |
| catzilla | hello_world | 13371.91 | 4.05ms | 26.08ms |
| catzilla | json_response | 11089.68 | 4.44ms | 8.30ms |
| catzilla | path_params | 8999.50 | 5.48ms | 10.03ms |
| catzilla | query_params | 6318.87 | 7.96ms | 16.11ms |
