# Catzilla Uasync-operations Category Performance Report

## Test Configuration
- **Category**: async-operations
- **Duration**: 3s
- **Connections**: 100
- **Connections Per Worker**: 100
- **Requested Threads**: 4
- **Worker Mode**: single
- **Workers**: 1
- **Tool**: wrk
- **Date**: Fri May  8 16:35:42 +06 2026

## Performance Results

| Framework | Endpoint | Worker Mode | Workers | Requests/sec | Avg Latency | 99% Latency | Peak Memory |
|-----------|----------|-------------|---------|--------------|-------------|-------------|-------------|
| catzilla | async-operations_chain_async | single | 1 | 10875.82 | 8.97ms | 13.54ms | 28.41MB |
| catzilla | async-operations_fanout_async | single | 1 | 18310.07 | 5.67ms | 10.02ms | 28.42MB |
| catzilla | async-operations_raw_async | single | 1 | 29235.28 | 3.75ms | 12.77ms | 27.84MB |
| catzilla | async-operations_yield_once | single | 1 | 27830.06 | 3.68ms | 7.46ms | 28.09MB |
| django | async-operations_chain_async | single | 1 | 2066.76 | 4.84ms | 9.46ms | 36.22MB |
| django | async-operations_fanout_async | single | 1 | 2685.37 | 3.72ms | 7.81ms | 36.22MB |
| django | async-operations_raw_async | single | 1 | 2808.30 | 3.56ms | 7.76ms | 36.12MB |
| django | async-operations_yield_once | single | 1 | 2761.07 | 3.63ms | 7.81ms | 36.20MB |
| fastapi | async-operations_chain_async | single | 1 | 3839.31 | 2.60ms | 3.18ms | 29.77MB |
| fastapi | async-operations_fanout_async | single | 1 | 6091.01 | 1.65ms | 3.96ms | 29.77MB |
| fastapi | async-operations_raw_async | single | 1 | 6284.65 | 1.65ms | 5.51ms | 29.23MB |
| fastapi | async-operations_yield_once | single | 1 | 6461.69 | 1.55ms | 3.20ms | 29.58MB |

## Catzilla Performance Advantage

This report shows how Catzilla performs compared to other frameworks in the **async-operations** category.
