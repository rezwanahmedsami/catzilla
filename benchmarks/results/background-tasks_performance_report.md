# Catzilla Background-tasks Category Performance Report

## Test Configuration
- **Category**: background-tasks
- **Duration**: 10s
- **Connections**: 100
- **Threads**: 4
- **Tool**: wrk
- **Date**: Thu Aug 21 06:13:57 UTC 2025

## Performance Results

| Framework | Endpoint | Requests/sec | Avg Latency | 99% Latency |
|-----------|----------|--------------|-------------|-------------|
| catzilla | background-tasks_batch_processing | 32972.55 | 3.20ms | 13.89ms |
| catzilla | background-tasks_email_task | 32432.47 | 3.26ms | 14.56ms |
| catzilla | background-tasks_health_check | 19449.41 | 5.59ms | 23.19ms |
| catzilla | background-tasks_parallel_tasks | 32316.69 | 3.31ms | 15.24ms |
| catzilla | background-tasks_queue_processing | 32483.89 | 3.30ms | 15.00ms |
| catzilla | background-tasks_scheduled_task | 32614.44 | 3.21ms | 12.65ms |
| catzilla | background-tasks_simple_task | 32240.18 | 3.31ms | 15.54ms |
| django | background-tasks_batch_processing | 1829.16 | 54.30ms | 79.35ms |
| django | background-tasks_email_task | 1827.38 | 54.48ms | 83.23ms |
| django | background-tasks_health_check | 1943.95 | 51.24ms | 72.90ms |
| django | background-tasks_parallel_tasks | 1841.52 | 53.91ms | 75.59ms |
| django | background-tasks_queue_processing | 1840.35 | 54.10ms | 76.41ms |
| django | background-tasks_scheduled_task | 1834.34 | 54.26ms | 75.63ms |
| django | background-tasks_simple_task | 1885.42 | 52.82ms | 52.82ms |
| fastapi | background-tasks_batch_processing | 4661.54 | 21.42ms | 39.17ms |
| fastapi | background-tasks_email_task | 4672.68 | 21.41ms | 39.36ms |
| fastapi | background-tasks_health_check | 4294.22 | 23.47ms | 42.26ms |
| fastapi | background-tasks_parallel_tasks | 4749.06 | 21.03ms | 38.21ms |
| fastapi | background-tasks_queue_processing | 4713.11 | 21.11ms | 38.33ms |
| fastapi | background-tasks_scheduled_task | 4669.06 | 21.41ms | 38.69ms |
| fastapi | background-tasks_simple_task | 4654.22 | 21.45ms | 39.04ms |
| flask | background-tasks_batch_processing | 15567.91 | 6.43ms | 20.52ms |
| flask | background-tasks_email_task | 15807.99 | 6.30ms | 20.60ms |
| flask | background-tasks_health_check | 16024.07 | 6.17ms | 20.56ms |
| flask | background-tasks_parallel_tasks | 15306.10 | 6.60ms | 20.40ms |
| flask | background-tasks_queue_processing | 15397.53 | 6.51ms | 19.26ms |
| flask | background-tasks_scheduled_task | 15416.71 | 6.54ms | 20.60ms |
| flask | background-tasks_simple_task | 15857.13 | 6.39ms | 20.61ms |

## Catzilla Performance Advantage

This report shows how Catzilla performs compared to other frameworks in the **background-tasks** category.
