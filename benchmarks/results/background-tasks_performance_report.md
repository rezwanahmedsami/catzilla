# Catzilla Ubackground-tasks Category Performance Report

## Test Configuration
- **Category**: background-tasks
- **Duration**: 10s
- **Connections**: 100
- **Threads**: 4
- **Tool**: wrk
- **Date**: Sat Aug 16 01:17:51 +06 2025

## Performance Results

| Framework | Endpoint | Requests/sec | Avg Latency | 99% Latency |
|-----------|----------|--------------|-------------|-------------|
| catzilla | background-tasks_batch_processing | 14330.03 | 7.97ms | 55.04ms |
| catzilla | background-tasks_email_task | 15657.49 | 6.82ms | 11.47ms |
| catzilla | background-tasks_health_check | 12443.01 | 10.78ms | 119.97ms |
| catzilla | background-tasks_parallel_tasks | 13482.18 | 8.13ms | 14.62ms |
| catzilla | background-tasks_queue_processing | 13995.23 | 8.02ms | 15.44ms |
| catzilla | background-tasks_scheduled_task | 14324.73 | 7.71ms | 13.94ms |
| catzilla | background-tasks_simple_task | 16767.85 | 6.56ms | 14.10ms |
| django | background-tasks_batch_processing | 428.03 | 230.50ms | 292.04ms |
| django | background-tasks_email_task | 455.75 | 216.49ms | 276.83ms |
| django | background-tasks_health_check | 605.19 | 163.43ms | 207.69ms |
| django | background-tasks_parallel_tasks | 404.40 | 243.96ms | 313.92ms |
| django | background-tasks_queue_processing | 387.98 | 254.06ms | 482.96ms |
| django | background-tasks_scheduled_task | 418.73 | 235.44ms | 302.01ms |
| django | background-tasks_simple_task | 480.36 | 205.70ms | 407.44ms |
| fastapi | background-tasks_batch_processing | 1298.32 | 76.62ms | 141.08ms |
| fastapi | background-tasks_email_task | 1215.52 | 83.72ms | 243.83ms |
| fastapi | background-tasks_health_check | 1277.76 | 79.05ms | 210.41ms |
| fastapi | background-tasks_parallel_tasks | 1135.31 | 88.83ms | 225.61ms |
| fastapi | background-tasks_queue_processing | 1243.09 | 80.95ms | 184.63ms |
| fastapi | background-tasks_scheduled_task | 1258.13 | 79.12ms | 153.62ms |
| fastapi | background-tasks_simple_task | 1406.26 | 71.25ms | 146.32ms |
| flask | background-tasks_batch_processing | 4.18 | 8.13ms | 27.27ms |
| flask | background-tasks_email_task | 1661.31 | 48.38ms | 127.30ms |
| flask | background-tasks_health_check | 1028.33 | 59.00ms | 116.29ms |
| flask | background-tasks_parallel_tasks | 2.78 | 26.85ms | 42.02ms |
| flask | background-tasks_queue_processing | 1660.69 | 46.87ms | 63.11ms |
| flask | background-tasks_simple_task | 0.90 | 11.33ms | 23.22ms |

## Catzilla Performance Advantage

This report shows how Catzilla performs compared to other frameworks in the **background-tasks** category.
